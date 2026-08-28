# -*- coding: utf-8 -*-
# origin: new for V1.0 — P2b-1 engine/pack separation (V1_SPEC §4)
"""Domain-pack loader: reconstructs every domain table from a pack
directory and injects it into the engine IN PLACE (the arc-established
runtime-patch pattern; the vendored files stay byte-frozen).

For the physics pack this must be behaviorally identical to
lexpatch11.apply() on the hardcoded tables — verified by
tests/test_pack_equality.py (structure dumps in twin subprocesses)
and by the E0 parity battery run through the pack path.

Engine-inline domain residue (NOT yet pack-driven; each is an E1
violation-log candidate, listed in packs/physics/README.md):
  - v4 base registry compiled members (`pre`/`fn` functions)
  - integrity11.certify inner `_canon` conflict-canonicalization table
    and the chem-frame concept list; `_unit_in_span` alias table
  - semparse11 function-local literals: the deferred-comparative word
    tuple and the `_VERB_TGT` ask-verb map
  - v9/sqr9 normalize_concept fallback vocabulary (U9.KINDS9)
"""
import json
import re
import sys
from pathlib import Path

_ARC = Path(__file__).resolve().parents[1] / "_arc"
if str(_ARC) not in sys.path:
    sys.path.insert(0, str(_ARC))

_APPLIED = None

# acquisition-time canonical-conversion rules (reflex/acquire.py
# appends here for `conversion` candidates; consulted after the pack's
# base rules)
EXTRA_CANONICAL = []

# authoritative unit-index extras: the pack's own extras plus ACTIVE
# acquired unit_index entries. Injector._rebuild_units re-applies
# exactly this dict after any fresh index build.
UNIT_INDEX_EXTRAS = {}


def _load(pack_dir):
    p = Path(pack_dir)
    out = {}
    for name in ("manifest", "kinds", "caps", "lexicon",
                 "conversions"):
        out[name] = json.loads((p / f"{name}.json").read_text(
            encoding="utf-8"))
    return out


def _ent_re(nouns, adjs):
    n = "|".join(nouns)
    a = "|".join(adjs)
    return re.compile(
        rf"\b(?:({n})\s+([A-Z]|[0-9]+)\b|"
        rf"the\s+({a})\s+({n}))\b", re.I)


def _ref_re(nouns, comparatives, hypernyms):
    n = "|".join(nouns)
    c = "|".join(comparatives)
    h = "|".join(nouns + hypernyms)
    return re.compile(
        rf"\b(?:the\s+(first|second|third|fourth|fifth|last)\s+(?:one|"
        rf"{n})|"
        rf"the\s+({c})\s+"
        rf"\w+|(it|its)|"
        rf"the\s+({h})"
        rf"(?!\s+[A-Z0-9]\b))\b", re.I)


# the REF_RE comparative alternation is its own frozen list (a strict
# subset of COMPARATIVES keys in the arc)
REF_COMPARATIVES = [
    "faster", "slower", "heavier", "lighter", "taller", "shorter",
    "longer", "larger", "smaller", "bigger", "denser", "cheaper",
    "pricier", "wider", "deeper", "fastest", "slowest", "heaviest",
    "lightest", "tallest", "longest", "largest", "smallest",
    "biggest", "densest", "cheapest", "priciest"]


def _make_to_canonical(conv, kinds_obj):
    rules = conv["canonical_rules"]
    pr = conv["percent_rule"]

    def _to_canonical(f):
        v = f["value"]
        u = (f.get("unit") or "").strip().lower().rstrip(".,;:!?")
        k = f["concept"]
        for r in list(rules) + EXTRA_CANONICAL:
            if r["concept"] != k:
                continue
            if r.get("special") == "kwh_contains":
                hit = ("kwh" in u) or u in ("$", "")
            else:
                hit = u in r["units"]
            if hit:
                return (v * r["factor"] if r["op"] == "mul"
                        else v / r["factor"])
        if u in pr["units"] and abs(v) > pr["min_abs"]:
            if k in kinds_obj and all(
                    d == 0 for d in kinds_obj[k][0]):
                return v / pr["factor"]
        return v

    return _to_canonical


def apply(pack_dir):
    """Inject the pack into the engine. Idempotent per pack."""
    global _APPLIED
    pack_dir = str(Path(pack_dir).resolve())
    if _APPLIED == pack_dir:
        return
    if _APPLIED is not None:
        raise RuntimeError(f"another pack already loaded: {_APPLIED}")
    P = _load(pack_dir)

    import v10.nlpw10 as W
    import v10.universe10 as U10
    import v9.universe9 as U9
    import v11.semstate11 as SS
    import v11.semparse11 as SP
    import v11.semrun11 as SR
    from v4 import registry_v4 as R4

    # ---- kinds (KINDS10 object is shared with integrity11)
    kinds = {k: (tuple(v["dim"]), v["unit"], list(v["nouns"]),
                 list(v["aliases"]))
             for k, v in P["kinds"].items()}
    U10.KINDS10.clear()
    U10.KINDS10.update(kinds)
    # worker view (module-global; semparse11 holds the same instance)
    W.KINDS9.clear()
    W.KINDS9.update(kinds)

    # ---- worker lexicon
    lex = P["lexicon"]
    W._EXTRA_NOUNS.clear()
    W._EXTRA_NOUNS.update({k: list(v) for k, v in
                           lex["extra_nouns"].items()})
    W._ADJ.clear()
    W._ADJ.update(lex["adj"])
    W.UNIT_WORDS.clear()
    W.UNIT_WORDS.update(lex["unit_words"])
    W._CONV.clear()
    W._CONV.update({u: (b, f) for u, (b, f) in
                    P["conversions"]["mention_conv"].items()})
    idx = W._build_unit_index()
    W._UNIT_IDX.clear()
    W._UNIT_IDX.update(idx)
    UNIT_INDEX_EXTRAS.clear()
    UNIT_INDEX_EXTRAS.update({u: list(ks) for u, ks in
                              lex["unit_index_extra"].items()})
    for u, ks in UNIT_INDEX_EXTRAS.items():
        W._UNIT_IDX.setdefault(u, list(ks))

    # ---- comparatives (shared instance with semrun's import)
    SS.COMPARATIVES.clear()
    SS.COMPARATIVES.update({k: tuple(v) for k, v in
                            lex["comparatives"].items()})

    # ---- parser entity/reference regexes
    SP.ENT_RE = _ent_re(lex["entity_nouns"],
                        lex["entity_adjectives"])
    SP.REF_RE = _ref_re(lex["entity_nouns"], REF_COMPARATIVES,
                        lex["ref_hypernyms"])

    # ---- phrase_name patch (v11 behavior, sale verbs from pack)
    if not getattr(W.phrase_name, "_pack_patched", False):
        _orig_pn = W.phrase_name
        sale_verbs = tuple(lex["sale_verbs"])

        def _pn_pack(clause, rel, known, unit=""):
            cl = clause.lower()
            words = re.findall(r"[a-z0-9.^/$%]+", cl)
            off, widx = 0, len(words) - 1
            for i, w in enumerate(words):
                j = cl.find(w, off)
                if j <= rel < j + len(w) or j > rel:
                    widx = i
                    break
                off = j + len(w)
            nxt = [w.rstrip(".,;:!?")
                   for w in words[widx + 1:widx + 3]]
            prv = [w.rstrip(".,;:!?")
                   for w in words[max(0, widx - 3):widx]]
            u = (unit or "").strip().lower()
            money_u = u.startswith("$") or u in ("dollars", "dollar")
            if money_u and "price_per_unit" in W.KINDS9:
                if (nxt and nxt[0] in ("each", "apiece")) or \
                        any(w.startswith(sale_verbs)
                            for w in prv + nxt):
                    return "price_per_unit", ["price_per_unit"]
            return _orig_pn(clause, rel, known, unit=unit)

        _pn_pack._pack_patched = True
        W.phrase_name = _pn_pack

    # ---- registry: engine base UNION pack caps (v6 semantics);
    # compiled members re-attach from the engine base
    caps9, caps10 = {}, {}
    newreg = dict(R4.REGISTRY)
    for name, c in P["caps"].items():
        if name not in newreg:
            newreg[name] = dict(c["spec"])
        if c["family"] == "caps9":
            caps9[name] = dict(c["spec"])
        elif c["family"] == "caps10":
            caps10[name] = dict(c["spec"])
    U9.CAPS9.clear()
    U9.CAPS9.update(caps9)
    U10.CAPS10_EXTRA.clear()
    U10.CAPS10_EXTRA.update(caps10)
    SR.REG11.clear()
    SR.REG11.update(newreg)

    # ---- canonical conversion (execution adapter)
    SR._to_canonical = _make_to_canonical(P["conversions"],
                                          U10.KINDS10)

    _APPLIED = pack_dir

    # ---- acquired overlay: ACTIVE candidates from past acquisition
    # runs (authorship-tagged; applied via the same injector so a
    # fresh process reproduces the acquired state)
    acq = Path(pack_dir) / "acquired.json"
    if acq.exists():
        from .. import acquire as AQ
        inj = AQ.Injector()
        for c in json.loads(acq.read_text(encoding="utf-8")):
            if c["type"] == "template_struct":
                continue      # applied by load_breeder's caller
            inj.apply(c)


def load_breeder(pack_dir):
    from v11.pbreed11 import ParserBreeder11
    p = Path(pack_dir) / "breeder_struct.json"
    if p.exists():
        return ParserBreeder11.load(p)
    return ParserBreeder11()
