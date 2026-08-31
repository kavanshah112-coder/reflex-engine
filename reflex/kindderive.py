# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W3 engine-derived kinds (V1_4_SPEC section 6)
"""The engine derives types. The model no longer asserts them.

V1.3 asked the parse agent for a `kind` on every quantity and a `kind`
on the target. Finding D5 measured what came back: on real language the
model typed nearly everything `count` or `money`, most plans had 0-1 of
2 steps dimensionally verifiable, and one wrong answer certified with
ZERO verifiable steps. The arc's central safety mechanism -- dimensional
verification, built over eleven versions -- was idling, because the
labels feeding it were noise.

The cause is structural, not a modelling weakness: **a model-asserted
type is unverifiable.** Nothing in the query can contradict it. A
model-asserted SPAN is different -- it round-trips against the source
text -- so V1.4 moves the boundary:

    the producer says WHICH WORDS.  the engine says WHAT KIND.

Derivation is lexicon lookup over `kinds.json` (77 kinds, each with
nouns, aliases, unit and a dimension vector). UNKNOWN is a first-class
outcome and never defaults to `count`; defaulting is exactly how the
labels became vacuous.

INTEGRALITY is read off the pack rather than declared here. A kind
whose dimension vector is a pure count -- nonzero only in the count
slot -- denotes discrete things. That makes check 8 a property of the
pack, regenerable and auditable, instead of a hand-written list that
drifts.
"""
import json
import re
from pathlib import Path

UNKNOWN = "UNKNOWN"
DEFAULT_PACK = Path(__file__).resolve().parent.parent / "packs" / "physics"

_CACHE = {}


def _load(pack_dir=None):
    d = str(pack_dir or DEFAULT_PACK)
    if d in _CACHE:
        return _CACHE[d]
    kinds = json.loads((Path(d) / "kinds.json").read_text(
        encoding="utf-8"))

    # Longest surface form first: "number of units" must beat "units".
    surfaces = []
    for name, spec in kinds.items():
        forms = {name.replace("_", " ")}
        forms.update(n.lower() for n in (spec.get("nouns") or []))
        forms.update(a.lower() for a in (spec.get("aliases") or []))
        u = (spec.get("unit") or "").lower()
        if u:
            forms.add(u)
        for f in forms:
            f = f.strip()
            if f:
                surfaces.append((len(f), f, name))
    surfaces.sort(key=lambda t: (-t[0], t[1]))

    # B19. A surface form claimed by MORE THAN ONE kind cannot resolve.
    # "m" is metres and molar; first-match-wins picked whichever sorted
    # first, which is V1.3's B8 in a new place -- a conflict silently
    # settled by ordering rather than detected. Colliding forms are
    # recorded and refuse, exactly as two disagreeing provenance sources
    # do.
    claims = {}
    for _, form, name in surfaces:
        claims.setdefault(form, set()).add(name)
    colliding = {f for f, ks in claims.items() if len(ks) > 1}

    # Count dimension: the slot in which `count` is nonzero and every
    # other kind's non-count dimensions are zero. Derived, not assumed.
    cdim = None
    cspec = kinds.get("count", {}).get("dim")
    if cspec:
        nz = [i for i, v in enumerate(cspec) if v]
        if len(nz) == 1:
            cdim = nz[0]

    integral = set()
    if cdim is not None:
        for name, spec in kinds.items():
            dim = spec.get("dim") or []
            if len(dim) > cdim and dim[cdim] and \
                    all(v == 0 for i, v in enumerate(dim) if i != cdim):
                integral.add(name)

    # B18: everyday countable nouns, harvested from NON-SEALED traffic
    # (build_everyday_lexicon.py). Consulted only AFTER the physics
    # pack, and never merged into it -- that pack feeds Tier A.
    everyday, ev_kind = set(), "count"
    evf = Path(__file__).resolve().parent.parent / "packs" /         "everyday" / "count_nouns.json"
    if evf.exists():
        ev = json.loads(evf.read_text(encoding="utf-8"))
        ev_kind = ev.get("kind", "count")
        everyday = {w.lower() for w in ev.get("nouns", [])}

    _CACHE[d] = {"kinds": kinds, "surfaces": surfaces,
                 "integral": integral, "count_dim": cdim,
                 "colliding": colliding, "claims": claims,
                 "everyday": everyday, "everyday_kind": ev_kind}
    return _CACHE[d]


def derive(span, pack_dir=None):
    """span -> (kind, why). Returns (UNKNOWN, reason) when the span
    carries no recognised noun, alias or unit. UNKNOWN never falls back
    to a plausible kind."""
    P = _load(pack_dir)
    s = re.sub(r"\s+", " ", (span or "").strip().lower())
    if not s:
        return UNKNOWN, "empty_span"
    for _, form, name in P["surfaces"]:
        if len(form) <= 2:
            # B17: a one- or two-character form is a UNIT SYMBOL, not a
            # word. Matching it as a word turned the English article "a"
            # into amperes on "16 vases a day". Unit symbols only count
            # in numeric context.
            pat = r"\d\s*%s(?![a-z])" % re.escape(form)
        else:
            pat = r"(?<![a-z])%s(?![a-z])" % re.escape(form)
        if re.search(pat, s):
            if form in P["colliding"]:
                return UNKNOWN, ("ambiguous surface %r claimed by %s"
                                 % (form,
                                    ",".join(sorted(P["claims"][form]))))
            return name, "matched %r" % form
    for w in re.findall(r"[a-z]{3,}", s):
        if w in P["everyday"]:
            return P["everyday_kind"], "everyday countable %r" % w
    return UNKNOWN, "no noun/alias/unit in span"


def is_integral(kind, pack_dir=None):
    """True when the kind denotes discrete things, read off the pack's
    dimension vectors."""
    return kind in _load(pack_dir)["integral"]


def integral_kinds(pack_dir=None):
    return sorted(_load(pack_dir)["integral"])


# ---------------------------------------------------------------- ck 8
def check_target_integrality(target_kind, value, tol=1e-9,
                             pack_dir=None):
    """CHECK 8 -- pre-registered in V1_4_SPEC section 6.1.

    If the target's derived kind is integral, a non-integer result
    ABSTAINS. It never rounds.

    Rounding is not available, and V1.3 is why. Its two instances
    needed OPPOSITE roundings:

        "9 boys ... 29 trees ... each watered the equal amount"
            29/9 = 3.222   gold 3     (floors)
        "Jane arranges 16 vases a day, 248 vases, how many days?"
            248/16 = 15.5  gold 16    (ceilings)

    Nothing in either plan says which way the world goes. The engine
    knows the answer is not a whole number and does not know what to do
    about it, so it declines -- which is the only honest move and the
    one the arc has made since V0.3.

    -> (ok, detail)
    """
    if target_kind in (None, UNKNOWN):
        return True, {"skipped": "target kind unknown"}
    if not is_integral(target_kind, pack_dir):
        return True, {"skipped": "kind not integral",
                      "kind": target_kind}
    try:
        v = float(value)
    except (TypeError, ValueError):
        return True, {"skipped": "value not numeric"}
    if abs(v - round(v)) <= tol:
        return True, {"kind": target_kind, "value": v}
    return False, {"why": "non_integer_under_integral_kind",
                   "kind": target_kind, "value": v,
                   "note": "abstain, never round: floor and ceiling are "
                           "both attested in V1.3"}


def derive_state(state, pack_dir=None):
    """Derive a kind for every node in an rss.State, engine-side.
    Returns a coverage report -- the UNKNOWN rate is a headline W3
    number, not a footnote."""
    rep = {"derived": 0, "unknown": 0, "by_kind": {}}
    for nid, n in sorted(state.nodes.items()):
        kind, why = derive(n.get("span", ""), pack_dir)
        state.set_kind(nid, kind, why)
        if kind == UNKNOWN:
            rep["unknown"] += 1
        else:
            rep["derived"] += 1
            rep["by_kind"][kind] = rep["by_kind"].get(kind, 0) + 1
    tot = rep["derived"] + rep["unknown"]
    rep["unknown_rate"] = round(rep["unknown"] / tot, 4) if tot else None
    return rep
