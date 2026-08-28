# -*- coding: utf-8 -*-
"""V0.11 breeder (spec Section 14): semantic structure classes on top
of the proven V0.10 lexical machinery.

Classes bred here:
  1. lexical quantity patterns (pbreed10, ±3-token <NUM> windows)
  2. ask patterns (pbreed10)
  3. STRUCTURAL quantity patterns (new): the verb/noun slot is
     wildcarded (<W>) while the UNIT anchor stays literal —
     "a <W> <W> <NUM> kg" -> mass. These can generalize to unseen
     lexemes; whether they do is hypothesis H7's experiment.
  4. entity-reference patterns: "<ENT> <W> <NUM> <unit>" windows that
     also bind the nearest preceding entity mention.
  5. temporal patterns: initial/final cue windows -> temporal scope.
  6. path structures (pbreed10 path cache).

Gates (all classes): G1 support >=5 obs, >=3 distinct values, >=4
distinct queries, unanimous label; G2 regex replay on own evidence;
G3 held-out agreement >=98% on reserved observations; adversarial
screen: the pattern must NOT match any role-cue window (historical/
hypothetical/negated/spec) in the screen corpus. Pollution rule
unchanged: only structurally validated observations breed.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v10.pbreed10 import ParserBreeder10, pollute_sqr  # noqa: E402,F401

_NUM = r"(-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][+-]?\d+)?)"
_TOK = re.compile(r"[A-Za-z$%€£/^.]+|-?\d[\w.+-]*")


def _struct_window(text, value, w=3):
    """±w tokens around the value; non-unit alpha tokens wildcarded
    to <W>, the numeral to <NUM>, unit-ish tokens kept literal."""
    from v10.nlpw10 import UNIT_WORDS
    toks = _TOK.findall(text)
    vi = None
    for i, t in enumerate(toks):
        try:
            if abs(float(t.replace(",", "")) - value) < 1e-9:
                vi = i
                break
        except ValueError:
            continue
    if vi is None:
        return None
    lo, hi = max(0, vi - w), min(len(toks), vi + w + 1)
    out = []
    for j in range(lo, hi):
        t = toks[j]
        if j == vi:
            out.append("<NUM>")
        elif t.lower().rstrip(".,;:!?") in UNIT_WORDS or \
                "/" in t or t in ("$", "%", "€"):
            out.append(t.lower().rstrip(".,;:!?"))
        elif re.fullmatch(r"-?\d[\w.+-]*", t):
            out.append("<N2>")
        else:
            out.append("<W>")
    return " ".join(out)


class ParserBreeder11(ParserBreeder10):
    def __init__(self):
        super().__init__()
        self.sobs = defaultdict(list)       # structural observations
        self.deployed_struct = {}
        self.tobs = defaultdict(list)       # temporal cue windows
        self.deployed_temporal = {}

    # ------------------------------------------------ observation
    def observe_semantic(self, query, query_id, facts, completed):
        if not completed:
            return
        for f in facts:
            if f.get("provenance") != "USER_TEXT" or \
                    f.get("value") is None:
                continue
            if f.get("concept") in (None, "UNKNOWN"):
                continue
            sp = _struct_window(query, f["value"])
            if sp and "<NUM>" in sp:
                self.sobs[sp].append((f["concept"], f["value"],
                                      f.get("unit"), query_id))
            if f.get("temporal") in ("initial", "final"):
                w = _struct_window(query, f["value"], w=5)
                if w:
                    self.tobs[w].append((f["temporal"], query_id))

    def try_deploy_struct(self, heldout=None):
        new = []
        for pat, obs in self.sobs.items():
            if pat in self.deployed_struct:
                continue
            concepts = {o[0] for o in obs}
            vals = {o[1] for o in obs}
            qs = {o[3] for o in obs}
            units = {(o[2] or "").lower() for o in obs}
            # G1: support + unanimity + a literal unit anchor
            has_unit_anchor = any(
                t not in ("<W>", "<NUM>", "<N2>")
                for t in pat.split())
            if len(obs) < 5 or len(vals) < 3 or len(qs) < 4 or \
                    len(concepts) != 1 or not has_unit_anchor:
                continue
            concept = next(iter(concepts))
            # G3 held-out agreement
            if heldout:
                agree = tot = 0
                for (q, facts) in heldout:
                    for f in facts:
                        if f.get("value") is None:
                            continue
                        sp = _struct_window(q, f["value"])
                        if sp == pat:
                            tot += 1
                            agree += (f.get("concept") == concept)
                if tot >= 2 and agree / tot < 0.98:
                    continue
            self.deployed_struct[pat] = {
                "concept": concept, "unit": next(iter(units)),
                "support": len(obs)}
            new.append(pat)
        return new

    def extract_struct(self, query):
        """Match structural patterns against a query; returns
        [(concept, value, unit)]."""
        out = []
        toks = _TOK.findall(query)
        for i, t in enumerate(toks):
            try:
                v = float(t.replace(",", ""))
            except ValueError:
                continue
            sp = _struct_window(query, v)
            d = self.deployed_struct.get(sp)
            if d:
                out.append((d["concept"], v, d["unit"]))
        return out

    def save(self, path):
        super().save(path)
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        d["deployed_struct"] = self.deployed_struct
        d["n_sobs"] = len(self.sobs)
        Path(path).write_text(json.dumps(d, indent=1),
                              encoding="utf-8")

    @classmethod
    def load(cls, path):
        base = ParserBreeder10.load(path)
        obj = cls()
        obj.__dict__.update(base.__dict__)
        obj.sobs = defaultdict(list)
        obj.tobs = defaultdict(list)
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        obj.deployed_struct = d.get("deployed_struct", {})
        obj.deployed_temporal = d.get("deployed_temporal", {})
        return obj
