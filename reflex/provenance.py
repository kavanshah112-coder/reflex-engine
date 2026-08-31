# -*- coding: utf-8 -*-
# origin: new for V1.3 -- W6 provenance certification (SPEC section 9)
"""Certification for answers that are RETRIEVED rather than derived.

Every version of this arc has certified on derivation: a value is
trustworthy because the engine computed it from checked inputs under
checked dimensions. A retrieved fact has no derivation to check --
the number was simply written down by someone -- so the guarantee has
to come from somewhere else, and section 9 puts it on PROVENANCE:

  identity      which document, which version
  validity      is that document inside its stated validity window
  supersession  is a later version of the same record present
  agreement     do the surviving live records concur

The rule that makes this a certification rather than a lookup is the
last one: **two live sources that disagree produce an abstention, not
a majority vote and not a newest-wins tiebreak.** A conflict means the
corpus itself is wrong, and no retrieval policy can repair that from
the inside. This mirrors the arc's oldest invariant -- when the engine
cannot establish a value it declines to serve one -- and it is the
reason a FACTUAL answer can carry a certificate at all.

Values are read from document TEXT, never from any structured field
the corpus generator happened to leave behind, because a real
deployment has only the text.
"""
import re

LABEL_KEYS = {
    "rated power": "power_kw",
    "nominal duty": "duty_h",
    "drive efficiency": "efficiency",
    "energy rate": "rate",
    "standing charge": "standing",
    "quantity": "qty",
    "unit price": "unit_price",
    "service interval": "interval_h",
    "labour rate": "labour",
    "density": "density",
    "resin price": "price_kg",
    "mould shrinkage": "shrinkage",
    "hourly rate": "rate_h",
    "setup allowance": "setup_h",
    "clamping force": "tonnage",
    "shot weight per part": "weight_g",
    "cavities in tool": "cavities",
    "cycle time": "cycle_s",
    "runner weight per shot": "runner_g",
    "parts per carton": "per_carton",
    "freight cost": "freight_kg",
}

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def read_facts(text):
    """Parse `Label: value` lines out of a document. Returns
    {canonical_key: float}. Unrecognised labels are ignored rather
    than guessed at -- an unparsed line costs coverage, a
    mis-parsed one costs correctness."""
    out = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        label, _, rhs = line.partition(":")
        lab = label.strip().lower()
        key = LABEL_KEYS.get(lab)
        if key is None and lab in LABEL_KEYS.values():
            key = lab                      # hazard docs write raw keys
        if key is None:
            continue
        m = NUM.search(rhs)
        if not m:
            continue
        try:
            out[key] = float(m.group(0).replace(",", ""))
        except ValueError:
            continue
    return out


def _live(doc, asof):
    return doc["valid_from"] <= asof <= doc["valid_to"]


def base_title(d):
    return d["title"].split(" (")[0]


def resolve(docs, key, asof="2026-08-31", subject=None):
    """Certify one retrieved fact, or refuse.

    -> {"ok": True, "value": v, "provenance": {...}}
       {"ok": False, "why": "...", ...}

    `subject` is the record the question is ABOUT. It matters more
    than it looks. Forty material sheets each carry a `density`, so a
    resolver that considers every retrieved document holding the
    requested KEY sees forty disagreeing sources and abstains on
    everything -- which is what the first W6 run did, on all 150
    factual queries. Identity is therefore the FIRST provenance
    question, not an optimisation: establish which record is being
    asked about, and only then ask whether the sources for THAT
    record agree. When identity cannot be established the answer is
    still an abstention, but for an honest reason.
    """
    if subject:
        scoped = [d for d in docs if base_title(d) == subject]
        if not scoped:
            return {"ok": False, "why": "subject_not_retrieved",
                    "subject": subject}
        docs = scoped
    seen = []
    for d in docs:
        vals = read_facts(d["text"])
        if key in vals:
            seen.append((d, vals[key]))
    if not seen:
        return {"ok": False, "why": "fact_not_found_in_retrieved_docs"}

    quarantined = [(d, v) for d, v in seen if not _live(d, asof)]
    live = [(d, v) for d, v in seen if _live(d, asof)]
    if not live:
        return {"ok": False, "why": "all_sources_outside_validity",
                "quarantined": [d["id"] for d, _ in quarantined]}

    # Supersession keeps every record at the HIGHEST version, not one
    # of them. Keeping a single winner per title silently resolved
    # disagreement by document ORDER: two live version-1 records for
    # the same fact would collapse to whichever the retriever happened
    # to return first, and the conflict check downstream then had one
    # value to look at and nothing to object to. That is how B8's
    # wrong-certified answers were produced -- the conflict detector
    # was intact and simply never given both values.
    top = {}
    for d, v in live:
        t = base_title(d)
        top[t] = max(top.get(t, d["version"]), d["version"])
    surviving = [(d, v) for d, v in live
                 if d["version"] == top[base_title(d)]]

    vals = {round(v, 6) for _, v in surviving}
    if len(vals) > 1:
        return {"ok": False, "why": "sources_conflict",
                "values": sorted(vals),
                "sources": [d["id"] for d, _ in surviving]}

    d, v = surviving[0]
    return {"ok": True, "value": v,
            "provenance": {"source": d["id"], "title": d["title"],
                           "version": d["version"],
                           "valid_from": d["valid_from"],
                           "valid_to": d["valid_to"],
                           "asof": asof,
                           "superseded_versions":
                               len(live) - len(surviving),
                           "quarantined_sources":
                               [q["id"] for q, _ in quarantined]}}
