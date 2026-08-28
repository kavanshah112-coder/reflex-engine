# -*- coding: utf-8 -*-
"""V0.9 parser breeder (spec Sections 15-17).

Learns REPRESENTATION patterns from traffic, self-supervised:
an observation is recorded only when (a) the SQR passed the
deterministic validator and (b) the Path Manager completed the
computation to a final answer (no ground-truth labels are ever used).

Observation for each accepted USER_TEXT quantity:
    pattern  = context window around the number in the QUERY text,
               number replaced by <NUM>, lowercased
    concept  = validated concept
    unit     = surface unit
Target observations analogously from the question clause.

Deployment gates (V0.6 discipline):
    G1 structure: >= MIN_OBS observations, >= MIN_VALS distinct values,
       >= MIN_Q distinct queries, ZERO conflicting concepts for the
       same pattern (dominance: top concept must be unanimous),
       pattern must contain an anchor token (never a bare <NUM>).
    G2 replay: deterministic re-extraction on its own evidence
       reproduces every observation.
    G3 held-out: >= 98% agreement with validated-LLM concepts on a
       held-out traffic slice (evaluated at deployment time).

Deployed parser reflexes extract quantities BEFORE the LLM; when every
numeral in a query is covered and a target pattern fires, the LLM SQR
call is skipped entirely (the distillation payoff).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v9 import sqr9 as S9                     # noqa: E402

MIN_OBS, MIN_VALS, MIN_Q = 5, 3, 4
NUM_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE]-?\d+)?")


def _window(text, value, w=3):
    """Context pattern around the first occurrence of `value`."""
    for m in NUM_RE.finditer(text):
        try:
            v = float(m.group(0).replace(",", ""))
        except ValueError:
            continue
        if abs(v - value) < 1e-9:
            toks_l = re.findall(r"[^\s]+", text[:m.start()].lower())
            toks_r = re.findall(r"[^\s]+", text[m.end():].lower())
            pat = " ".join(toks_l[-w:]) + " <NUM> " + \
                " ".join(toks_r[:w])
            return re.sub(r"\d+(?:\.\d+)?", "#", pat).strip()
    return None


def _ask_pattern(text):
    segs = [s for s in re.split(r"[.?!]", text) if s.strip()]
    if not segs:
        return None
    ask = segs[-1].lower().strip()
    return re.sub(r"\d+(?:\.\d+)?", "#", ask)


class ParserBreeder:
    def __init__(self):
        self.obs = defaultdict(list)      # pattern -> [(concept, value,
        #                                    unit, query_id)]
        self.ask_obs = defaultdict(list)  # ask pattern -> [(kind, qid)]
        self.deployed = {}                # pattern -> {concept, unit}
        self.deployed_ask = {}            # ask pattern -> kind
        self.log = []

    # ------------------------------------------------------- learning
    def observe(self, query, query_id, validated_sqr, completed):
        if not completed:
            return
        for q in validated_sqr.get("quantities", []):
            if q.get("provenance") != "USER_TEXT" or \
                    q.get("value") is None:
                continue
            if q.get("concept") in (None, "UNKNOWN"):
                continue
            pat = _window(query, q["value"])
            if pat is None or "<NUM>" not in pat:
                continue
            self.obs[pat].append((q["concept"], q["value"],
                                  q.get("unit"), query_id,
                                  q.get("role"), query))
        tgt = (validated_sqr.get("target") or {}).get("concept")
        ap = _ask_pattern(query)
        if tgt and tgt != "UNKNOWN" and ap:
            self.ask_obs[ap].append((tgt, query_id))

    # ------------------------------------------------------ deployment
    def try_deploy(self, heldout=None):
        """Run gates over accumulated observations. heldout: list of
        (query, validated_sqr) pairs for G3."""
        new = []
        for pat, rows in self.obs.items():
            if pat in self.deployed:
                continue
            concepts = {r[0] for r in rows}
            roles = {r[4] for r in rows}
            if len(concepts) != 1 or roles - {"input"}:
                continue          # G1 dominance: unanimous, inputs only
            vals = {round(r[1], 9) for r in rows}
            qs = {r[3] for r in rows}
            if len(rows) < MIN_OBS or len(vals) < MIN_VALS or \
                    len(qs) < MIN_Q:
                continue
            anchor = [t for t in pat.split()
                      if t not in ("<NUM>", "#") and len(t) > 1]
            if not anchor:
                continue          # G1 anchor
            concept = next(iter(concepts))
            rx = self._regex_for(pat)
            if rx is None:
                continue
            # G2 replay: the regex must re-extract every observed value
            # from its own source query text
            if not all(any(abs(v - r[1]) < 1e-9
                           for v in self._extract_rx(rx, r[5]))
                       for r in rows):
                self.log.append({"pattern": pat, "gate": "G2",
                                 "deployed": False})
                continue
            # G3 held-out agreement
            if heldout:
                agree = tot = 0
                for hq, hsqr in heldout:
                    for v in self._extract_rx(rx, hq):
                        tot += 1
                        for g in hsqr.get("quantities", []):
                            if g.get("value") is not None and \
                                    abs(g["value"] - v) < 1e-9:
                                agree += (g.get("concept") == concept)
                                break
                if tot >= 3 and agree / tot < 0.98:
                    self.log.append({"pattern": pat, "gate": "G3",
                                     "agree": agree, "tot": tot,
                                     "deployed": False})
                    continue
            unit = rows[0][2]
            self.deployed[pat] = {"concept": concept, "unit": unit,
                                  "rx": rx.pattern, "n_obs": len(rows),
                                  "n_vals": len(vals),
                                  "n_queries": len(qs)}
            new.append(pat)
            self.log.append({"pattern": pat, "concept": concept,
                             "n_obs": len(rows), "deployed": True})
        for ap, rows in self.ask_obs.items():
            if ap in self.deployed_ask:
                continue
            kinds = {r[0] for r in rows}
            qs = {r[1] for r in rows}
            if len(kinds) == 1 and len(rows) >= MIN_OBS and \
                    len(qs) >= MIN_Q:
                self.deployed_ask[ap] = next(iter(kinds))
                new.append(f"ASK:{ap[:40]}")
        return new

    def _regex_for(self, pat):
        toks = pat.split()
        parts = []
        for t in toks:
            if t == "<NUM>":
                parts.append(r"(-?\d+(?:,\d{3})*(?:\.\d+)?)")
            else:
                parts.append(re.escape(t).replace("\\#", r"\d+(?:\.\d+)?"))
        try:
            return re.compile(r"\s+".join(parts), re.I)
        except re.error:
            return None

    def _extract_rx(self, rx, text):
        out = []
        for m in rx.finditer(text.lower()):
            try:
                out.append(float(m.group(1).replace(",", "")))
            except (ValueError, IndexError):
                pass
        return out

    # -------------------------------------------------------- runtime
    def extract(self, query):
        found = []
        for pat, spec in self.deployed.items():
            rx = re.compile(spec["rx"], re.I)
            for v in self._extract_rx(rx, query):
                found.append({"value": v, "concept": spec["concept"],
                              "unit": spec.get("unit"),
                              "pattern": pat})
        return found

    def covers(self, query, found):
        """Full coverage: every numeral in the query is extracted AND an
        ask pattern fires."""
        if not found:
            return False
        vals = {round(f["value"], 9) for f in found}
        for m in NUM_RE.finditer(query):
            try:
                v = round(float(m.group(0).replace(",", "")), 9)
            except ValueError:
                continue
            if v not in vals:
                return False
        return self._ask_kind(query) is not None

    def _ask_kind(self, query):
        ap = _ask_pattern(query)
        if ap in self.deployed_ask:
            return self.deployed_ask[ap]
        return None

    def assemble(self, query, query_id, found):
        qs = []
        for i, f in enumerate(found):
            qs.append({"qid": f"Q{i+1}", "entity": None,
                       "concept": f["concept"], "value": f["value"],
                       "unit": f.get("unit"), "role": "input",
                       "source_span": None, "provenance": "USER_TEXT",
                       "ambiguous": False, "_reflex": True})
        return {"query_id": query_id, "entities": [],
                "quantities": qs, "assumptions": [],
                "target": {"concept": self._ask_kind(query),
                           "entity": None, "unit": None, "span": ""},
                "ambiguity_flags": [], "_reflex_sqr": True}

    # ------------------------------------------------------ persistence
    def save(self, path):
        Path(path).write_text(json.dumps(
            {"deployed": self.deployed,
             "deployed_ask": self.deployed_ask,
             "log": self.log,
             "n_patterns_observed": len(self.obs)},
            indent=1), encoding="utf-8")

    @classmethod
    def load(cls, path):
        b = cls()
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        b.deployed = d["deployed"]
        b.deployed_ask = d["deployed_ask"]
        b.log = d.get("log", [])
        return b


# ------------------------------------------------------- pollution
def pollute_sqr(sqr, rng, mode):
    """Corrupt a validated SQR observation (Section 16 classes)."""
    import copy
    s = copy.deepcopy(sqr)
    qs = [q for q in s.get("quantities", [])
          if q.get("value") is not None]
    if not qs:
        return s
    q = rng.choice(qs)
    if mode == "wrong_quantity":
        q["value"] = q["value"] * rng.choice([10, 0.1, 3])
    elif mode == "wrong_unit":
        q["unit"] = rng.choice(["kg", "s", "$", "mol", "W"])
    elif mode == "wrong_concept":
        q["concept"] = rng.choice(["mass", "time", "revenue", "moles",
                                   "speed"])
    elif mode == "wrong_role":
        q["role"] = "input" if q.get("role") != "input" else \
            "distractor"
    elif mode == "wrong_entity":
        q["entity"] = "E9"
    elif mode == "wrong_target":
        s["target"] = {**(s.get("target") or {}),
                       "concept": rng.choice(["mass", "energy",
                                              "profit"])}
    return s
