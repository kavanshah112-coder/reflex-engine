# -*- coding: utf-8 -*-
# origin: new for V1.3 — W5 plan reflexes (V1_3_SPEC §8)
"""Plan reflexes: reuse a VERIFIED plan shape on a new query without
parsing it again.

The economic claim in §8 is "served by cached plans at ZERO parse
cost", and that constrains the design: matching must happen on the
TEXT, before any model call. A cache keyed on the plan signature
would require parsing first and would save nothing that matters.

So a plan reflex is  (text pattern) -> (plan schema with slots):
  - retrieval by hashed n-grams over past VERIFIED solves (the same
    machinery as the frame — V0.2 lineage, no model, no embedder);
  - binding by position: the new query's numbers fill the schema's
    slots in order of appearance;
  - and then every downstream check still runs. A bound plan is a
    CANDIDATE, never an answer: round-trip, consumption, scope,
    non-degeneracy and corroboration all apply exactly as they do to
    a freshly parsed plan.

That last point is what makes positional binding safe enough to try.
Binding numbers from a merely-similar question into a stored shape is
precisely how a cache produces confident nonsense (V0.1's founding
failure), so the cache is given no authority the parser does not
have.
"""
import re

from .frame import cosine, features

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def numbers_in(text):
    out = []
    for m in NUM_RE.finditer(text):
        try:
            out.append(float(m.group(0).replace(",", "")))
        except ValueError:
            continue
    return out


def signature(ir):
    """Structural signature of a verified plan: the operator sequence
    plus each operand's kind, with derived operands marked. Mirrors
    W0's `medium` granularity so the two measurements are comparable."""
    kind_of = {q["id"]: (q.get("kind") or "unknown")
               for q in ir.get("quantities", [])}
    parts = []
    for s in ir.get("plan", []):
        cls = []
        for arg in s["args"]:
            cls.append(kind_of.get(arg, "derived"))
        parts.append(f"{s['op']}({','.join(cls)})")
    return "|".join(parts)


def schema_of(ir, text):
    """Turn a verified plan into a reusable schema: the step DAG kept
    verbatim, quantities reduced to ORDER-OF-APPEARANCE slots."""
    nums = numbers_in(text)
    slots = []
    for q in ir["quantities"]:
        v = float(q["value"])
        idx = next((i for i, n in enumerate(nums)
                    if abs(n - v) < 1e-9), None)
        slots.append({"id": q["id"], "slot": idx,
                      "unit": q.get("unit", ""),
                      "kind": q.get("kind")})
    return {"slots": slots,
            "plan": [{"op": s["op"], "args": s["args"],
                      "out": s["out"]} for s in ir["plan"]],
            "target": ir.get("target", {}),
            "n_numbers": len(nums)}


class PlanCache:
    """Text-retrieved, slot-bound plan reflexes."""

    def __init__(self, threshold=0.62, min_conf=2):
        self.rows = []        # {vec, q, schema, sig, hits}
        self.threshold = threshold
        self.min_conf = min_conf
        self.pending = {}     # sig -> confirmations before activation

    # ------------------------------------------------------ minting
    def observe(self, text, ir):
        """A verified solve. A schema activates only after `min_conf`
        independent confirmations of the same signature (the arc's
        probation pattern, cheapened: no shadow batch is needed
        because every served plan is still fully checked)."""
        sig = signature(ir)
        self.pending[sig] = self.pending.get(sig, 0) + 1
        if self.pending[sig] < self.min_conf:
            return False
        if any(r["sig"] == sig and cosine(features(text), r["vec"])
               > 0.95 for r in self.rows):
            return False
        self.rows.append({"vec": features(text), "q": text[:160],
                          "schema": schema_of(ir, text), "sig": sig,
                          "hits": 0})
        return True

    # ------------------------------------------------------ serving
    def match(self, text):
        """-> (bound_ir, score, sig) or None. No model call."""
        if not self.rows:
            return None
        v = features(text)
        best, bs = None, 0.0
        for r in self.rows:
            s = cosine(v, r["vec"])
            if s > bs:
                best, bs = r, s
        if best is None or bs < self.threshold:
            return None
        nums = numbers_in(text)
        sch = best["schema"]
        if len(nums) != sch["n_numbers"]:
            return None            # different arity: refuse to bind
        qs = []
        for sl in sch["slots"]:
            if sl["slot"] is None or sl["slot"] >= len(nums):
                return None
            qs.append({"id": sl["id"], "value": nums[sl["slot"]],
                       "unit": sl["unit"], "kind": sl["kind"]})
        ir = {"quantities": qs,
              "plan": [dict(s) for s in sch["plan"]],
              "target": dict(sch["target"]), "dismissed": [],
              "_from_cache": True}
        best["hits"] += 1
        return ir, bs, best["sig"]

    def stats(self):
        return {"schemas": len(self.rows),
                "pending_signatures": len(self.pending),
                "total_hits": sum(r["hits"] for r in self.rows),
                "top": sorted(
                    ({"sig": r["sig"], "hits": r["hits"],
                      "q": r["q"][:70]} for r in self.rows),
                    key=lambda x: -x["hits"])[:10]}
