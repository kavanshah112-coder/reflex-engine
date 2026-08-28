"""V0.4 engines (Sections 3, 6, 13-17).

Modes:
  static          v2-lineage control: ONE capability, no chaining/handoff
  reflex          abstain at any gap (no LLM ever)
  aon             all-or-nothing: full-known reflex, else WHOLE query -> LLM.
                  This is simultaneously the strong-cascade control (Section
                  14) and the Section-38 baseline.
  partial         prefix -> structured LLM gap -> validate -> resume
  partial_unstruct  same but free-text LLM handoff (ablation, Section 39)
  partial_noverify  structured but validation disabled (ablation, Section 40)

gap_solver injection lets tests use an oracle; benchmarks use llm_bridge.
Parser-noise and executor-failure wrappers implement Sections 26-27.
"""
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401

from src.llm import ollama_client as llm            # noqa: E402
from v3.ir import Quantity                          # noqa: E402
from v4 import registry_v4 as R4                    # noqa: E402
from v4.qparse4 import parse_quantities, asked_kind  # noqa: E402
from v4.partial_planner import (plan_known, find_gap, forward_closure,  # noqa
                                goal_kinds)
from v4 import llm_bridge as bridge                 # noqa: E402


class NoiseModel:
    """Parser corruption (Section 26) + executor failure (Section 27)."""

    def __init__(self, parser_p=0.0, executor_p=0.0, seed=42):
        self.parser_p = parser_p
        self.executor_p = executor_p
        self.rng = random.Random(seed)

    def corrupt_quantities(self, qs):
        out = []
        for q in qs:
            r = self.rng.random()
            if r < self.parser_p:
                mode = self.rng.choice(["drop", "scale", "kind"])
                if mode == "drop":
                    continue
                if mode == "scale":
                    q = Quantity(kind=q.kind, value=q.value
                                 * self.rng.choice([0.1, 10]), unit=q.unit)
                else:
                    q = Quantity(kind=self.rng.choice(
                        ["mass", "money", "count", "rate"]),
                        value=q.value, unit=q.unit)
            out.append(q)
        return out

    def maybe_fail_executor(self, value):
        if self.rng.random() < self.executor_p:
            return value * self.rng.choice([0.5, 2.0, -1.0])
        return value


class V4Engine:
    def __init__(self, mode="partial", concept=None, max_handoffs=1,
                 max_depth=6, registry=None, noise=None,
                 gap_solver=None, experience_log=None):
        self.mode = mode
        self.concept = concept          # ConceptNodes-like or None
        self.max_handoffs = max_handoffs
        self.max_depth = max_depth
        self.registry = registry if registry is not None else R4.REGISTRY
        self.noise = noise or NoiseModel()
        self.gap_solver = gap_solver    # (query, state, kind, existing)->rec
        self.experience_log = experience_log
        self.name = f"v4_{mode}"

    def _priors(self, query):
        if self.concept is None:
            return {}, 0.0, 0.0
        rec = self.concept.recognize(query)
        return rec["priors"], rec["ood_score"], rec["flops"]

    def _full_llm(self, record, query):
        out = llm.generate(query)
        record["llm_calls"] = record.get("llm_calls", 0) + 1
        record["llm_tokens"] = record.get("llm_tokens", 0) + \
            out["prompt_tokens"] + out["gen_tokens"]
        record["llm_flops"] = record.get("llm_flops", 0) + out["flops_est"]
        record["answer"] = out["text"]
        record["status"] = "llm_answer"

    def process(self, query, mode_llm="hybrid", query_id=None, log=True):
        """mode_llm: 'hybrid' allows LLM; 'pure' never calls it."""
        t0 = time.perf_counter()
        rec = {"query_id": query_id, "engine": self.name, "mode": self.mode,
               "status": None, "answer": None, "numeric_value": None,
               "reflex_ops": 0, "llm_ops": 0, "llm_calls": 0,
               "llm_tokens": 0, "llm_flops": 0.0, "reflex_flops": 0.0,
               "handoffs": [], "path": [], "escalated": False,
               "abstain_reason": None, "registry_version": "v0"}
        qs, conv = parse_quantities(query)
        qs = self.noise.corrupt_quantities(qs)
        ak = asked_kind(query)
        priors, ood, cflops = self._priors(query)
        rec["reflex_flops"] += cflops
        rec["ood_score"] = ood
        rec["asked_kind"] = ak
        if ood >= 0.5 or ak is None or not qs:
            rec["abstain_reason"] = ("ood" if ood >= 0.5
                                     else "no asked kind or quantities")
            if mode_llm == "hybrid":
                rec["escalated"] = True
                self._full_llm(rec, query)
            else:
                rec["status"] = "ABSTAIN"
            rec["total_ms"] = (time.perf_counter() - t0) * 1000
            return rec

        # context guards: capabilities excluded by query semantics the type
        # system cannot see (e.g. simple_interest on 'compound' queries)
        low = query.lower()
        reg_eff = {k: v for k, v in self.registry.items()
                   if not any(w in low for w in v.get("context_exclude", []))}
        rec["context_excluded"] = sorted(set(self.registry) - set(reg_eff))

        if self.mode == "static":
            # v2-lineage control: ONE capability, no chaining, no handoff —
            # same registry/parser/concept net as every other v4 system
            cands = []
            for name, spec in reg_eff.items():
                if spec.get("transfer"):
                    continue
                if spec["output"] in goal_kinds(ak) and \
                        all(any(q.kind == k for q in qs)
                            for k in spec["inputs"]):
                    cands.append((priors.get(name, 0.0), name))
            if cands:
                _, name = max(cands)
                spec = reg_eff[name]
                inputs = {k: next(q for q in qs if q.kind == k)
                          for k in spec["inputs"]}
                v, ok, _ = R4.execute(name, inputs, registry=reg_eff)
                rec["reflex_flops"] += 50
                if ok:
                    val = self.noise.maybe_fail_executor(v)
                    rec["path"] = [name]
                    rec["reflex_ops"] = 1
                    rec["numeric_value"] = val
                    rec["answer"] = f"static {name} = {val:.4f}"
                    rec["status"] = "reflex_answer"
                    rec["total_ms"] = (time.perf_counter() - t0) * 1000
                    return rec
            rec["abstain_reason"] = "static: no single bindable capability"
            if mode_llm == "hybrid":
                rec["escalated"] = True
                self._full_llm(rec, query)
            else:
                rec["status"] = "ABSTAIN"
            rec["total_ms"] = (time.perf_counter() - t0) * 1000
            return rec

        # 1) full known-path attempt
        r = plan_known(qs, ak, priors=priors, max_depth=self.max_depth,
                       registry=reg_eff)
        rec["reflex_flops"] += r["stats"]["executor_calls"] * 50
        suspect = False
        suspect_cands = []
        if r["ok"] and r.get("coverage", 1.0) < 0.999:
            # SUSPECT complete path: parsed quantities left unused. If a
            # fuller path could be built through a missing capability input,
            # this path likely answers the wrong (simpler) question.
            suspect_cands = find_gap(qs, ak, priors=priors,
                                     max_depth=self.max_depth,
                                     registry=reg_eff, suspect_mode=True)
            suspect = bool(suspect_cands)
            rec["suspect_path"] = suspect
        if r["ok"] and not suspect:
            val = self.noise.maybe_fail_executor(r["value"])
            rec["path"] = r["path"]
            rec["reflex_ops"] = len(r["path"])
            rec["numeric_value"] = val
            rec["answer"] = f"reflex path {r['path']} = {val:.4f}"
            rec["status"] = "reflex_answer"
            rec["executor_noise_applied"] = val != r["value"]
            rec["total_ms"] = (time.perf_counter() - t0) * 1000
            return rec

        if self.mode == "reflex" or mode_llm == "pure":
            rec["abstain_reason"] = "gap in registry (no complete typed path)"
            rec["status"] = "ABSTAIN"
            rec["total_ms"] = (time.perf_counter() - t0) * 1000
            return rec
        if self.mode == "aon":
            rec["escalated"] = True
            rec["abstain_reason"] = "aon: incomplete path -> full LLM"
            self._full_llm(rec, query)
            rec["total_ms"] = (time.perf_counter() - t0) * 1000
            return rec

        # 2) partial: prefix closure (context for gap detection + the LLM),
        # then gap handoffs (multi-candidate). Resume planning always restarts
        # from PRIMITIVES (query quantities + accepted LLM injections) — the
        # closure state would trip redundant-production pruning on the goal.
        state, prefix = forward_closure(qs, priors=priors,
                                        registry=reg_eff)
        injections = []
        rec["prefix_path"] = prefix
        rec["reflex_ops"] += len(prefix)
        # default structured solver is the v3 EXPRESSION handoff — chosen on
        # VALIDATION (v1 value / v2 value+work / v3 expression: 25/26/29 of
        # 35); v1 remains benchmarked as the *_handv1 ablation records
        solver = self.gap_solver or (
            bridge.solve_gap_unstructured if self.mode == "partial_unstruct"
            else bridge.solve_gap_structured_v3)
        for h in range(self.max_handoffs):
            cands = find_gap(state, ak, priors=priors,
                             max_depth=self.max_depth,
                             registry=reg_eff)
            if not cands and h == 0 and suspect_cands:
                cands = suspect_cands
            if not cands:
                break
            injected = None
            for gap in cands[:3]:      # try up to 3 gap candidates
                existing = {q.kind: q.value for q in state}
                srec = solver(query, [q for q in state if not q.consumed],
                              gap["kind"], existing)
                # state snapshot at handoff time: the breeder mines
                # (available kinds -> injected kind) numeric relations
                srec["state_at_handoff"] = {
                    q.kind: q.value for q in state if not q.consumed}
                rec["handoffs"].append(srec)
                rec["llm_calls"] += 1
                rec["llm_ops"] += 1
                rec["llm_tokens"] += srec.get("prompt_tokens", 0) + \
                    srec.get("gen_tokens", 0)
                rec["llm_flops"] += srec.get("flops_est", 0)
                accepted = (srec["accepted"]
                            or self.mode == "partial_noverify")
                if accepted and srec["value"] is not None:
                    injected = (gap["kind"], srec["value"])
                    break
            if injected is None:
                break
            if injected[0] == ak:
                # the LLM produced the exact asked kind: answer directly
                val = self.noise.maybe_fail_executor(injected[1])
                rec["path"] = prefix + [f"LLM[{injected[0]}]"]
                rec["numeric_value"] = val
                rec["answer"] = f"partial path {rec['path']} = {val:.4f}"
                rec["status"] = "partial_answer"
                rec["escalated"] = True
                rec["total_ms"] = (time.perf_counter() - t0) * 1000
                return rec
            q_inj = Quantity(kind=injected[0], value=injected[1],
                             source="llm")
            injections.append(q_inj)
            state = list(state) + [q_inj]
            r2 = plan_known(list(qs) + list(injections), ak, priors=priors,
                            max_depth=self.max_depth, registry=reg_eff,
                            must_use=tuple(q.kind for q in injections))
            rec["reflex_flops"] += r2["stats"]["executor_calls"] * 50
            if r2["ok"]:
                val = self.noise.maybe_fail_executor(r2["value"])
                rec["path"] = prefix + [f"LLM[{injected[0]}]"] + r2["path"]
                rec["reflex_ops"] += len(r2["path"])
                rec["numeric_value"] = val
                rec["answer"] = f"partial path {rec['path']} = {val:.4f}"
                rec["status"] = "partial_answer"
                rec["escalated"] = True   # LLM was used (as component)
                rec["total_ms"] = (time.perf_counter() - t0) * 1000
                return rec
        # handoffs exhausted / failed -> fall back
        rec["abstain_reason"] = "gap handoff failed"
        rec["escalated"] = True
        self._full_llm(rec, query)
        rec["total_ms"] = (time.perf_counter() - t0) * 1000
        return rec
