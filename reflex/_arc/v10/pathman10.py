# -*- coding: utf-8 -*-
"""V0.10 Long Path Manager (spec Sections 11-13).

Path acquisition: planner10 goal-regression (depth wall removed —
autopsy-proven). Execution: the battle-tested V0.8 machinery
(_bind/_exec_step/_llm_step) driven by a v10 loop that keeps state
across the whole plan (incremental — no re-parse between steps),
executes ("<GAP>", kind) pseudo-steps as targeted typed LLM calls,
and never lets the LLM control the global path.

Escalation cases (Section 6) are decided by budget10 BEFORE this
manager runs; here only case-D (missing capability step) and case-E
(execution failure -> escalate/abstain) apply.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v8 import pathman as PM8                    # noqa: E402
from v8 import llmstep as LS                     # noqa: E402
from v10 import planner10 as PL10                # noqa: E402


class _NullRec:
    name = "null"

    def recognize(self, text):
        return {"fired": False, "quantities": [], "target": None}


class LongPathManager:
    def __init__(self, registry, use_llm=True, validate=True,
                 available=None, max_gaps=1):
        self.registry = registry
        self.avail = set(available) if available is not None \
            else set(registry)
        self.avail_reg = {n: s for n, s in registry.items()
                          if n in self.avail}
        self.use_llm = use_llm
        self.validate = validate
        self.max_gaps = max_gaps
        # V0.8 execution machinery host (its search is never used)
        self.pm8 = PM8.PathManager(registry, _NullRec(), plevel=3,
                                   ilevel=5, use_llm=use_llm,
                                   validate=validate)

    def run(self, state, target, query, query_id, chain_mode="chain"):
        """state: list of {kind,value,clause,provenance,consumed}
        (from compile_state). chain_mode: 'direct' = single-capability
        only (system C); 'chain' = full planner (D+).
        Returns a record like PM8.process()."""
        t0 = time.perf_counter()
        rec = {"query_id": query_id, "llm_calls": [],
               "full_llm_calls": 0, "step_llm_calls": 0,
               "transitions": [], "status": None,
               "numeric_value": None, "path": None,
               "plan_stats": None, "reflex_steps": 0,
               "llm_steps_exec": 0, "gap_steps": 0,
               "path_completed": False}
        kinds = [s["kind"] for s in state]
        if not kinds or not target or target == "UNKNOWN":
            rec["abstain_reason"] = "empty_state_or_target"
            rec["status"] = "abstain"
            rec["t_ms"] = (time.perf_counter() - t0) * 1e3
            return rec
        if chain_mode == "direct":
            steps = None
            for name in sorted(self.avail_reg):
                spec = self.avail_reg[name]
                if spec.get("transfer"):
                    continue
                if spec["output"] == target and \
                        all(k in kinds for k in spec["inputs"]):
                    steps = (name,)
                    break
            stats = {"expansions": len(self.avail_reg), "gaps": 0}
            if steps is None:
                rec["abstain_reason"] = "no_direct_capability"
                rec["status"] = "abstain"
                rec["t_ms"] = (time.perf_counter() - t0) * 1e3
                return rec
        else:
            steps, stats = PL10.plan(
                kinds, target, self.avail_reg,
                max_gaps=self.max_gaps if self.use_llm else 0,
                allow_gaps=self.use_llm)
            if steps is None:
                rec["abstain_reason"] = "no_plan"
                rec["status"] = "abstain"
                rec["t_ms"] = (time.perf_counter() - t0) * 1e3
                return rec
        rec["plan_stats"] = stats
        rec["path"] = [s if not isinstance(s, tuple) else
                       f"<GAP:{s[1]}>" for s in steps]
        goal = stats.get("goal", target)
        n_steps = len(steps)
        value, completed = None, []
        for i, s in enumerate(steps):
            step_id = i + 1
            if isinstance(s, tuple):            # ("<GAP>", kind)
                need = s[1]
                if not self.use_llm:
                    rec["abstain_reason"] = f"gap_{need}_pure_mode"
                    break
                ctx = {"query_id": query_id, "query": query,
                       "target": goal, "input_kinds": kinds,
                       "path_id": f"V10-{query_id}",
                       "step_id": step_id, "n_steps": n_steps,
                       "completed": completed, "next_caps": [
                           f"{n}({', '.join(self.registry[n]['inputs'])})"
                           f" -> {self.registry[n]['output']}"
                           for n in steps[i + 1:i + 2]
                           if not isinstance(n, tuple)]}
                v = self.pm8._llm_step(need, state, ctx, rec,
                                       rec["transitions"])
                if v is None:
                    rec["abstain_reason"] = f"llm_step_failed_{need}"
                    break
                rec["gap_steps"] += 1
                rec["llm_steps_exec"] += 1
                completed.append({"step": step_id,
                                  "cap": f"<LLM:{need}>", "by": "llm"})
                value = v
                continue
            v, err = self.pm8._exec_step(s, state, query_id,
                                         f"V10-{query_id}", step_id,
                                         rec["transitions"])
            if err is not None:
                rec["abstain_reason"] = f"step_error_{s}:{err}"
                break
            rec["reflex_steps"] += 1
            completed.append({"step": step_id, "cap": s,
                              "by": "reflex"})
            value = v
        else:
            rec["path_completed"] = True
        rec["completed"] = completed
        if rec["path_completed"] and value is not None:
            rec["status"] = "pm_answer"
            rec["numeric_value"] = value
        elif rec["status"] is None:
            rec["status"] = "abstain"
        rec["t_ms"] = (time.perf_counter() - t0) * 1e3
        return rec

    def llm_full(self, rec, query):
        """Case-E escalation / cascade fallback: counted full solve."""
        out = LS.call_full(query)
        rec["llm_calls"].append(out)
        rec["full_llm_calls"] += 1
        rec["status"] = "llm_answer" if out["accepted"] else \
            "llm_failed"
        rec["numeric_value"] = out["value"]
        return rec
