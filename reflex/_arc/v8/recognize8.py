# -*- coding: utf-8 -*-
"""V0.8 recognizer ladder R0..R7 (spec Section 5) + shared deterministic
solve harness.

Every recognizer maps text -> {quantities, target, fired, trace}. The
shared harness then runs the FROZEN typed planner/executor; recognition
quality is measured by what the deterministic layer can then do (coverage /
wrong-fire), plus label accuracy against the recognition benchmark.

Ladder decomposition (each rung isolates one mechanism):
  R0  V0.7 recognizer (V6Engine.recognize with the frozen R_v06 pattern
      registry) — control.
  R1  lexical: Jaccard nearest-exemplar over a dev-built bank.
  R2  embedding: MiniLM cosine nearest-exemplar.
  R3  R1 else R2.
  R4  structural fingerprint, structure-only focus (units in question,
      comparatives, how-ADJ forms). No concept wordlist, no exemplars.
  R5  R4 + concept graph (curated FOCUS_CONCEPT + V0.6 traffic-learned
      lexemes).
  R6  R5 + capability/path matching: unresolved targets are inferred by
      path feasibility over the capability index (unique feasible
      candidate rule + full-consumption rule).
  R7  R6 + calibrated abstention (conflict/uniqueness gates; thresholds
      set on DEV-VAL only).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v3.ir import Quantity                           # noqa: E402
from v4.qparse4 import parse_quantities as pq4       # noqa: E402
from v4.qparse4 import asked_kind as ak4             # noqa: E402
from v4.partial_planner import plan_known, _kind_closure  # noqa: E402
from v8 import fingerprint as FP                     # noqa: E402

STOP = set("""a an the of to in on at for and or is are was were be been has
have had do does did it its this that these those how what which who whom
whose when where why with by from as if then than so such much many more
most some any no not all each every per one two i you he she they we him
her them us my your his their our me""".split())


def content_tokens(text):
    return {t for t in re.findall(r"[a-z]+", text.lower())
            if t not in STOP and len(t) > 2}


def _inverse_pairs(registry):
    """Auto-detected inverse capability pairs: A,B are inverses iff
    output(A) in inputs(B) and output(B) in inputs(A). A path containing
    both computes a round trip (X -> Y -> X'), which is never the least
    mechanism for these tasks and is a classic wrong-fire source."""
    names = list(registry)
    pairs = set()
    for i, a in enumerate(names):
        sa = registry[a]
        for b in names[i + 1:]:
            sb = registry[b]
            if sa["output"] in sb["inputs"] and \
                    sb["output"] in sa["inputs"]:
                pairs.add(frozenset((a, b)))
    return pairs


_INV_CACHE = {}


def path_is_roundtrip(path, registry):
    key = id(registry)
    if key not in _INV_CACHE:
        _INV_CACHE[key] = _inverse_pairs(registry)
    pairs = _INV_CACHE[key]
    ps = set(path)
    return any(fs <= ps for fs in pairs)


def solve(qs, target, registry, priors=None, dup_kind_guard=False):
    """Deterministic solve through the frozen planner. Returns record.
    Rejects round-trip (inverse-pair) paths — structural validation.
    dup_kind_guard: also refuse paths that consume a kind the query
    supplies more than once (binding ambiguity the flat planner cannot
    resolve; the Path Manager handles these with clause binding)."""
    if target is None:
        return {"covered": False, "value": None, "path": [],
                "reason": "no_target"}
    r = plan_known(qs, target, registry=registry, priors=priors)
    if r["ok"]:
        path = [s["cap"] if isinstance(s, dict) else s for s in r["path"]]
        if path_is_roundtrip(path, registry):
            return {"covered": False, "value": None, "path": path,
                    "reason": "roundtrip_rejected", "stats": r.get("stats")}
        if dup_kind_guard:
            from collections import Counter
            dup = {k for k, c in Counter(q.kind for q in qs).items()
                   if c > 1}
            used = set()
            for name in path:
                used |= set(registry[name]["inputs"])
            if dup & used:
                return {"covered": False, "value": None, "path": path,
                        "reason": "dup_kind_ambiguity",
                        "stats": r.get("stats")}
        return {"covered": True, "value": r["value"], "path": path,
                "goal_kind": r.get("goal_kind"), "reason": "ok",
                "stats": r.get("stats")}
    return {"covered": False, "value": None, "path": [],
            "reason": "no_complete_path", "stats": r.get("stats")}


# ---------------------------------------------------------------- R0
class R0V7:
    name = "R0_v0.7"

    def __init__(self, engine):
        self.engine = engine   # a V6Engine with R_v06 patterns

    def recognize(self, text):
        qs, conv, ak, trace = self.engine.recognize(text)
        return {"quantities": qs, "target": ak,
                "trace": {"kind": "v7", **{k: trace[k] for k in
                                           ("final_kinds", "final_ask")}},
                "fired": ak is not None}


# ---------------------------------------------------------------- R1/R2
class R1Lexical:
    name = "R1_lexical"

    def __init__(self, bank, theta=0.5):
        self.bank = [(content_tokens(b["q"]), b) for b in bank]
        self.theta = theta

    def recognize(self, text):
        toks = content_tokens(text)
        best, bs = None, 0.0
        for btoks, b in self.bank:
            u = len(toks | btoks)
            s = len(toks & btoks) / u if u else 0.0
            if s > bs:
                bs, best = s, b
        qs, _ = pq4(text)
        if best is None or bs < self.theta:
            return {"quantities": qs, "target": None, "fired": False,
                    "trace": {"kind": "lex", "sim": bs}}
        return {"quantities": qs, "target": best["target"], "fired": True,
                "trace": {"kind": "lex", "sim": bs,
                          "exemplar": best["q"][:60]}}


class R2Embed:
    name = "R2_embed"
    _model = None

    @classmethod
    def model(cls):
        if cls._model is None:
            import pandas  # noqa: F401 (import-order workaround)
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2")
        return cls._model

    def __init__(self, bank, theta=0.6):
        import numpy as np
        self.bank = bank
        self.theta = theta
        m = self.model()
        self.emb = m.encode([b["q"] for b in bank],
                            normalize_embeddings=True)
        self.np = np

    def recognize(self, text):
        v = self.model().encode([text], normalize_embeddings=True)[0]
        sims = self.emb @ v
        i = int(self.np.argmax(sims))
        bs = float(sims[i])
        qs, _ = pq4(text)
        if bs < self.theta:
            return {"quantities": qs, "target": None, "fired": False,
                    "trace": {"kind": "emb", "sim": bs}}
        b = self.bank[i]
        return {"quantities": qs, "target": b["target"], "fired": True,
                "trace": {"kind": "emb", "sim": bs,
                          "exemplar": b["q"][:60]}}


class R3LexEmbed:
    name = "R3_lex+embed"

    def __init__(self, r1, r2):
        self.r1, self.r2 = r1, r2

    def recognize(self, text):
        r = self.r1.recognize(text)
        if r["fired"]:
            return {**r, "trace": {**r["trace"], "via": "R1"}}
        r = self.r2.recognize(text)
        return {**r, "trace": {**r["trace"], "via": "R2"}}


# ---------------------------------------------------------------- R4/R5
# structure-only focus: unit mentions + comparatives + how-ADJ (no concept
# wordlist). Kept apart from FP.FOCUS_LEX for the ladder decomposition.
FOCUS_STRUCT = [
    ("energy", r"joules?\b|\bkj\b|kilojoules?|kwh\b"),
    ("power", r"watts?\b|\bkw\b"),
    ("voltage", r"volts?\b"),
    ("current", r"amps?\b|amperes?"),
    ("resistance", r"ohms?"),
    ("charge", r"coulombs?"),
    ("temp_diff", r"warmer|hotter|cooler|degrees?\b"),
    ("speed", r"how fast|m/s\b"),
    ("mass", r"how heavy|kilograms?\b|\bkg\b"),
    ("height", r"how high"),
    ("distance", r"how far"),
    ("time", r"how long|seconds?\b"),
    ("cost_eur", r"euros?\b"),
    ("liters", r"liters?\b|litres?\b"),
    ("area", r"square met\w*|m²"),
    ("force", r"newtons?\b|how hard"),
    ("count", r"how many"),
    ("money", r"how much money"),
]


class R4Struct:
    name = "R4_structural"

    def __init__(self, focus=None):
        self.focus = focus  # None -> structure-only

    def recognize(self, text):
        f = FP.fingerprint(text, extra_lex=None)
        if self.focus == "concept":
            target = f["target"]
            cands = f["target_candidates"]
        else:
            cands, _ = FP.question_focus(text, extra_lex=None)
            # restrict to STRUCT patterns only
            struct_hits = []
            segs = f["qseg"].lower()
            for kind, pat in FOCUS_STRUCT:
                m = re.search(pat, segs)
                if m:
                    struct_hits.append((m.start(), kind))
            generic = {"money", "count"}
            struct_hits.sort(key=lambda sk: (1 if sk[1] in generic else 0,
                                             sk[0]))
            cands = []
            for _, k in struct_hits:
                if k not in cands:
                    cands.append(k)
            target = cands[0] if cands else f["base_ask"]
        return {"quantities": f["quantities"], "target": target,
                "fired": target is not None, "fp": f,
                "target_candidates": cands,
                "trace": {"kind": self.name, "rekinds": f["rekinds"],
                          "adds": f["adds"]}}


def v6_lexeme_lex(pattern_registry, askable):
    """Turn the V0.6 traffic-learned lexeme lexicon into extra focus
    patterns (surface word -> concept), concepts filtered to askable."""
    out = []
    lex = getattr(pattern_registry, "lexemes", None) or {}
    for word, entry in lex.items():
        c = entry.get("concept") if isinstance(entry, dict) else entry
        if c in askable and re.fullmatch(r"[a-z-]+", word or ""):
            out.append((c, rf"\b{re.escape(word)}\w*"))
    return out


class R5Concept(R4Struct):
    name = "R5_concept"

    def __init__(self, extra_lex=None):
        super().__init__(focus="concept")
        self.extra = extra_lex or []

    def recognize(self, text):
        f = FP.fingerprint(text, extra_lex=self.extra)
        return {"quantities": f["quantities"], "target": f["target"],
                "fired": f["target"] is not None, "fp": f,
                "target_candidates": f["target_candidates"],
                "trace": {"kind": self.name, "rekinds": f["rekinds"]}}


# ---------------------------------------------------------------- R6/R7
class R6Path(R5Concept):
    name = "R6_path"

    def __init__(self, registry, extra_lex=None):
        super().__init__(extra_lex)
        self.registry = registry

    def recognize(self, text):
        r = super().recognize(text)
        qs = r["quantities"]
        have = {q.kind for q in qs}
        reach = _kind_closure(have, self.registry)
        cands = r.get("target_candidates") or []
        t = r["target"]
        trace = dict(r["trace"], kind=self.name)
        # unknown-focus-noun guard: the question names a concept the
        # concept layer does not know (cands empty) — the base parser's
        # keyword fallback is untrustworthy there; abstain outright
        if not cands:
            unk = FP.unknown_focus_noun((r.get("fp") or {}).get("qseg", ""))
            if unk:
                trace["unknown_focus_noun"] = unk
                return {**r, "target": None, "fired": False,
                        "trace": trace, "abstained": True}
        # 1) keep the first focus candidate that is actually reachable
        feas = [k for k in cands if k in reach or k == "money"]
        if feas:
            if t not in feas:
                trace["path_switch"] = (t, feas[0])
                t = feas[0]
        elif t is not None and t not in reach and t != "money":
            # the question NAMED a target we cannot reach: honest answer
            # is abstain/escalate — never compute something else instead
            trace["named_target_unreachable"] = t
            return {**r, "target": t, "fired": False, "trace": trace,
                    "abstained": True}
        # 2) no target at all: infer by unique full-consumption path —
        # but ONLY if the question has no unrecognized focus noun (a
        # question noun outside the concept vocabulary means an
        # unrecognized concept, e.g. 'momentum': must not fire)
        if t is None:
            unk = FP.unknown_focus_noun(
                (r.get("fp") or {}).get("qseg", ""),
                extra_words=[w for _, w in []])
            if unk:
                trace["unknown_focus_noun"] = unk
                return {**r, "target": None, "fired": False,
                        "trace": trace, "abstained": True}
            t = self._infer_target(qs, reach, trace)
        return {**r, "target": t, "fired": t is not None, "trace": trace}

    def _infer_target(self, qs, reach, trace):
        """Unique-capability inference: which outputs can a complete path
        reach that CONSUMES EVERY parsed quantity? Unique -> adopt."""
        have = [q.kind for q in qs]
        outs = []
        for name, spec in self.registry.items():
            if spec.get("transfer"):
                continue
            if all(k in reach for k in spec["inputs"]) and \
                    any(k in have for k in spec["inputs"]):
                outs.append(spec["output"])
        # candidate outputs reachable by a complete path that consumes
        # EVERY parsed quantity (planner reports input coverage directly).
        # Round-trip chains (A->B->A') can fake full coverage, so apply a
        # minimal-mechanism rule: adopt only a UNIQUE SHORTEST full-
        # coverage explanation.
        full = {}
        for out in dict.fromkeys(outs):
            r = plan_known(qs, out, registry=self.registry)
            if r["ok"] and r.get("coverage", 0.0) >= 0.999:
                full[out] = len(r["path"])
        trace["inferred_candidates"] = sorted(full)[:6]
        if full:
            best = min(full.values())
            mins = [o for o, ln in full.items() if ln == best]
            if len(mins) == 1:
                trace["inferred_target"] = mins[0]
                return mins[0]
        return None


class R7Full(R6Path):
    name = "R7_full"
    dup_guard = True

    def __init__(self, registry, extra_lex=None, max_alts=1):
        super().__init__(registry, extra_lex)
        self.max_alts = max_alts   # calibrated on DEV-VAL only

    def recognize(self, text):
        r = super().recognize(text)
        if not r["fired"]:
            return r
        qs, t = r["quantities"], r["target"]
        trace = dict(r["trace"], kind=self.name)
        # conflict gate: multiple DISTINCT reachable focus candidates that
        # produce DIFFERENT numeric answers -> abstain
        cands = [k for k in (r.get("target_candidates") or [])[:3]
                 if k != t]
        alts = []
        for k in cands:
            s = solve(qs, k, self.registry)
            if s["covered"]:
                alts.append((k, s["value"]))
        main = solve(qs, t, self.registry)
        if main["covered"] and alts:
            diff = [k for k, v in alts
                    if abs(v - main["value"]) > 2e-2 *
                    max(1e-9, abs(main["value"]))]
            if len(diff) > self.max_alts - 1 and diff:
                trace["conflict_abstain"] = [t] + diff
                return {**r, "target": t, "fired": False, "trace": trace,
                        "abstained": True}
        return {**r, "trace": trace}
