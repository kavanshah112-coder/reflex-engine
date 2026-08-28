# -*- coding: utf-8 -*-
"""V0.8 Path Manager (spec Sections 13-20, 34).

State machine per query:
  recognize (R7) -> QUERY_INDEX -> path (memo | typed search) ->
  stepwise execution: Reflex where the capability is AVAILABLE, indexed
  LLM step where it is missing -> typed validation -> state update ->
  next step -> final.

P-levels (Section 23 ablation):
  P1  static single-capability selection only (no multi-step search)
  P2  typed forward path search + clause binding, deterministic routing;
      capability gaps ESCALATE the whole query (no step delegation)
  P3  P2 + Path/Query Index memoization + missing steps delegated to the
      LLM as I5 typed-expression steps (deterministic routing)
  P4  P3 but the LLM ROUTES each step (follows LLM choice; no typed
      state in its context; step solves at I3 raw-value)
  P5  P4 + typed state in routing/step context (steps at I4)
  P6  full: indexed LLM supervision with DETERMINISTIC ROUTE VALIDATION
      (LLM proposes, router verifies executability + path membership;
      invalid proposals overridden), steps at I5, full validation
Pure mode: use_llm=False — gaps and unrecognized queries abstain.

Every transition is logged: query_id, path_id, step_id, input state,
executor, output state, provenance, validation, next step (Section 34).
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v4.partial_planner import find_gap                  # noqa: E402
from v4.registry_v4 import execute as exec4              # noqa: E402
from v3.ir import Quantity                               # noqa: E402
from v8.pathindex import (PathIndex, QueryIndex, kind_path_search,  # noqa
                          path_code, build_links, tag_clauses)
from v8 import llmstep as LS                             # noqa: E402


class PathManager:
    def __init__(self, registry, recognizer, plevel=6, ilevel=5,
                 use_llm=True, use_links=True, validate=True,
                 available=None, pindex=None, qindex=None):
        self.registry = registry
        self.rec = recognizer
        self.plevel = plevel
        self.ilevel = ilevel
        self.use_llm = use_llm
        self.use_links = use_links
        self.validate = validate
        self.avail = set(available) if available is not None \
            else set(registry)
        self.avail_reg = {n: s for n, s in registry.items()
                          if n in self.avail}
        self.links = build_links(self.avail_reg)
        self.pi = pindex if pindex is not None else PathIndex()
        self.qi = qindex if qindex is not None else QueryIndex()

    # ------------------------------------------------------------ helpers
    def _llm_full(self, rec, query):
        if not self.use_llm:
            rec["status"] = "abstain"
            rec["abstain_reason"] = rec.get("abstain_reason",
                                            "pure_mode_no_llm")
            return rec
        out = LS.call_full(query)
        rec["llm_calls"].append(out)
        rec["full_llm_calls"] += 1
        rec["status"] = "llm_answer" if out["accepted"] else "llm_failed"
        rec["numeric_value"] = out["value"]
        return rec

    def _bind(self, kind, state, anchor_clauses):
        """Pick the state entry to consume for `kind`: prefer PRODUCED
        entries (chain outputs), then unconsumed query entries with the
        smallest clause distance to the step's other inputs; allow
        consumed reuse as last resort."""
        cands = [s for s in state if s["kind"] == kind]
        if not cands:
            return None
        produced = [s for s in cands if s["provenance"] != "query"
                    and not s["consumed"]]
        if produced:
            return produced[-1]
        fresh = [s for s in cands if not s["consumed"]]
        pool = fresh if fresh else cands
        if anchor_clauses and len(pool) > 1:
            def dist(s):
                if s["clause"] < 0:
                    return 99
                return min(abs(s["clause"] - a) for a in anchor_clauses)
            pool = sorted(pool, key=dist)
        return pool[0]

    def _exec_step(self, name, state, qid, pid, step_id, transitions):
        spec = self.registry[name]
        bound = {}
        anchors = []
        # two-pass binding: rarest kinds first so the anchor set grows
        order = sorted(spec["inputs"],
                       key=lambda k: sum(1 for s in state
                                         if s["kind"] == k))
        for k in order:
            s = self._bind(k, state, anchors)
            if s is None:
                return None, k
            bound[k] = s
            if s["clause"] >= 0:
                anchors.append(s["clause"])
        inputs = {k: Quantity(kind=k, value=s["value"])
                  for k, s in bound.items()}
        v, ok, why = exec4(name, inputs, registry=self.registry)
        if not ok:
            transitions.append({
                "query_id": qid, "path_id": pid, "step_id": step_id,
                "cap": name, "executor": "reflex", "ok": False,
                "why": why})
            return None, f"exec_fail:{why}"
        for s in bound.values():
            s["consumed"] = True
        new = {"kind": spec["output"], "value": v, "clause": -1,
               "provenance": f"{qid}/{pid}/STEP-{step_id}",
               "consumed": False, "by": name}
        state.append(new)
        transitions.append({
            "query_id": qid, "path_id": pid, "step_id": step_id,
            "cap": name, "executor": "reflex",
            "inputs": {k: s["value"] for k, s in bound.items()},
            "output": {spec["output"]: v},
            "provenance": new["provenance"], "validation": "PASS",
            "ok": True})
        return v, None

    def _llm_step(self, need_kind, state, ctx, rec, transitions):
        """Missing-step delegation with indexed prompt + typed
        validation; returns value or None."""
        if not self.use_llm:
            return None
        ilevel = self.ilevel
        # full current typed state, one entry per kind: prefer the
        # unconsumed entry (for duplicate kinds, the not-yet-used value
        # is the step-relevant one); consumption bookkeeping steers
        # reflex binding, it must not hide information from the LLM
        by_kind = {}
        for s in state:
            cur = by_kind.get(s["kind"])
            if cur is None or (cur["consumed"] and not s["consumed"]):
                by_kind[s["kind"]] = s
        ctx = dict(ctx, need_kind=need_kind,
                   state=[{"kind": s["kind"], "value": s["value"],
                           "provenance": s["provenance"]}
                          for s in by_kind.values()])
        out = LS.call_step(ilevel, ctx)
        rec["llm_calls"].append(out)
        rec["step_llm_calls"] += 1
        accepted = out["accepted"]
        if not self.validate:
            # ablation L: accept ANY parseable numeric regardless of gates
            if not accepted and out.get("value") is None:
                import re as _re
                m = _re.search(r"-?\d+(?:\.\d+)?", out.get("raw", ""))
                if m:
                    out["value"] = float(m.group(0))
                    accepted = True
            elif out.get("value") is not None:
                accepted = True
        if not accepted or out.get("value") is None:
            transitions.append({
                "query_id": ctx.get("query_id"),
                "path_id": ctx.get("path_id"),
                "step_id": ctx.get("step_id"), "cap": f"<LLM:{need_kind}>",
                "executor": "llm", "ok": False,
                "validation": ";".join(out.get("validation") or []) or
                "FAIL"})
            return None
        new = {"kind": need_kind, "value": out["value"], "clause": -1,
               "provenance": f"{ctx.get('query_id')}/"
                             f"{ctx.get('path_id')}/"
                             f"STEP-{ctx.get('step_id')}",
               "consumed": False, "by": "llm_step"}
        state.append(new)
        transitions.append({
            "query_id": ctx.get("query_id"), "path_id": ctx.get("path_id"),
            "step_id": ctx.get("step_id"), "cap": f"<LLM:{need_kind}>",
            "executor": "llm",
            "handoff": out.get("handoff_kind"),
            "expression": out.get("expression"),
            "output": {need_kind: out["value"]},
            "provenance": new["provenance"],
            "validation": "PASS" if self.validate else "UNGATED",
            "ok": True})
        return out["value"]

    # ------------------------------------------------------------ process
    def process(self, query, query_id=None, truth_path=None):
        t0 = time.perf_counter()
        rec = {"query_id": query_id, "query": query, "llm_calls": [],
               "full_llm_calls": 0, "step_llm_calls": 0,
               "route_llm_calls": 0, "transitions": [],
               "status": None, "numeric_value": None, "path": None,
               "path_hit": False, "search_expansions": 0,
               "route_events": []}
        r = self.rec.recognize(query)
        rec["recognized"] = bool(r["fired"])
        rec["target"] = r.get("target")
        if not r["fired"]:
            rec["abstain_reason"] = "recognition_abstain"
            out = self._llm_full(rec, query)
            out["t_ms"] = (time.perf_counter() - t0) * 1e3
            return out
        qs = r["quantities"]
        target = r["target"]
        kinds = [q.kind for q in qs]
        sig = (r.get("fp") or {}).get("signature") or \
            path_code(kinds, [], target)
        qid = self.qi.new(query, sig, target, qid_hint=query_id)
        rec["qid"] = qid
        clauses = tag_clauses(query, qs)
        state = [{"kind": q.kind, "value": q.value, "clause": c,
                  "provenance": "query", "consumed": False}
                 for q, c in zip(qs, clauses)]

        # ---- path acquisition
        steps, pid = None, None
        goal = target
        if self.plevel >= 3:
            code = self.qi.memo_get(sig)
            if code:
                prec = self.pi.lookup(code)
                if prec and set(prec["input_kinds"]) <= set(kinds):
                    steps = list(prec["steps"])
                    pid = prec["path_id"]
                    goal = prec["output_kind"]
                    rec["path_hit"] = True
        if steps is None:
            if self.plevel == 1:
                # static: one capability, directly
                steps = None
                for name, spec in self.avail_reg.items():
                    if spec["output"] == target and \
                            all(k in kinds for k in spec["inputs"]):
                        steps = [name]
                        break
                st = {"expansions": len(self.avail_reg)}
            else:
                steps, st = kind_path_search(
                    kinds, target, self.avail_reg,
                    use_links=self.use_links, links=self.links)
                if steps and target == "money":
                    goal = self.registry[steps[-1]]["output"]
            rec["search_expansions"] = (st or {}).get("expansions", 0)
            if steps:
                prec = self.pi.register(kinds, steps, goal,
                                        validated=False)
                pid = prec["path_id"]
                if self.plevel >= 3:
                    self.qi.memo_put(sig, prec["code"])

        # ---- capability gap? (Section 15)
        gap_kind = None
        goals = {target}
        if target == "money":
            from v4.partial_planner import MONEY_GROUP as MG
            goals = set(MG)
        if steps is None and self.plevel >= 2:
            cands = find_gap(qs, target, registry=self.avail_reg)
            # goal-direct gaps LAST: a mid-chain gap gives the LLM the
            # smallest possible step (find_gap philosophy)
            cands = ([c for c in cands if c["kind"] not in goals] +
                     [c for c in cands if c["kind"] in goals])
            for c in cands[:4]:
                if c["kind"] in goals:
                    if target == "money":
                        # generic money ask: a goal-direct gap would let
                        # the system invent WHICH money quantity to
                        # produce — unsafe; escalate instead
                        continue
                    # goal-direct gap: reflex prefix (forward enrichment)
                    # + LLM final step
                    gap_kind = c["kind"]
                    steps = []
                    goal = c["kind"]
                    break
                trial, st2 = kind_path_search(
                    kinds + [c["kind"]], target, self.avail_reg,
                    use_links=self.use_links, links=self.links)
                rec["search_expansions"] += (st2 or {}).get(
                    "expansions", 0)
                if trial is not None:
                    gap_kind = c["kind"]
                    steps = trial
                    break
            if gap_kind and (self.plevel < 3 or not self.use_llm):
                # P2: no step delegation — escalate whole query
                rec["abstain_reason"] = f"gap_{gap_kind}_no_delegation"
                out = self._llm_full(rec, query)
                out["t_ms"] = (time.perf_counter() - t0) * 1e3
                return out
            if gap_kind:
                pid = f"GAP-{gap_kind}"
        if steps is None:
            rec["abstain_reason"] = "no_path"
            out = self._llm_full(rec, query)
            out["t_ms"] = (time.perf_counter() - t0) * 1e3
            return out

        # ---- stepwise execution (Section 34 state machine)
        rec["path"] = list(steps)
        rec["gap_kind"] = gap_kind
        n_steps = len(steps) + (1 if gap_kind else 0)
        plan = list(steps)
        completed = []
        step_id = 0
        value = None
        guard = 0
        # forward enrichment before ANY gap step (find_gap philosophy:
        # the LLM solves the SIMPLEST missing transformation; reflex
        # consumes the leftovers first). Safe since the LLM prompt now
        # carries the full typed state regardless of consumption.
        # Rule: caps consuming >= 2 fresh QUERY kinds, or a chain
        # continuation (>=1 produced + >=1 fresh input).
        if gap_kind:
            enriched = True
            enrich_rounds = 0
            while enriched and enrich_rounds < 6:
                enriched = False
                enrich_rounds += 1
                have_k = {s["kind"] for s in state}
                for name, spec in sorted(self.avail_reg.items()):
                    if spec.get("transfer") or spec["output"] in have_k:
                        continue
                    fresh = {s["kind"] for s in state
                             if not s["consumed"] and
                             s["provenance"] == "query"}
                    produced = {s["kind"] for s in state
                                if not s["consumed"] and
                                s["provenance"] != "query"}
                    if not all(k in have_k for k in spec["inputs"]):
                        continue
                    nf = len(set(spec["inputs"]) & fresh)
                    np_ = len(set(spec["inputs"]) & produced)
                    # >=2 fresh query kinds, or a chain continuation
                    # (>=1 produced + >=1 fresh)
                    if not (nf >= 2 or (nf >= 1 and np_ >= 1)):
                        continue
                    # never consume a CONSUMABLE produced kind (energy):
                    # that destroys prior work the LLM step likely needs
                    # (speed_from_energy trap)
                    from v3.ir import CONSUMABLE_KINDS
                    if set(spec["inputs"]) & CONSUMABLE_KINDS & produced:
                        continue
                    # output must be consumable by SOMETHING in the full
                    # registry — dead-end outputs (count_breakeven) only
                    # pollute the LLM's state
                    if not any(spec["output"] in s2["inputs"]
                               for s2 in self.registry.values()):
                        continue
                    step_id += 1
                    v, err = self._exec_step(name, state, qid, pid,
                                             step_id, rec["transitions"])
                    if err is None:
                        completed.append({"step": step_id, "cap": name,
                                          "by": "reflex"})
                        if name in plan:
                            plan.remove(name)
                        enriched = True
                        break
                    step_id -= 1
        # goal-direct gap with empty plan: the LLM step IS the final step
        if gap_kind and not plan:
            ctx = {"query_id": qid, "query": query, "target": goal,
                   "input_kinds": kinds, "path_id": pid,
                   "step_id": step_id + 1, "n_steps": step_id + 1,
                   "completed": completed, "next_caps": []}
            v = self._llm_step(gap_kind, state, ctx, rec,
                               rec["transitions"])
            if v is not None:
                value = v
                gap_kind = None
                completed.append({"step": step_id + 1,
                                  "cap": f"<LLM:{goal}>", "by": "llm"})
            else:
                rec["abstain_reason"] = f"llm_step_failed_{gap_kind}"
        while plan and guard < 2 * n_steps + 4:
            guard += 1
            step_id += 1
            # executable next steps
            have = {s["kind"] for s in state if not s["consumed"]} | \
                {s["kind"] for s in state}
            exec_ok = [n for n in plan
                       if all(k in {s['kind'] for s in state}
                              for k in self.registry[n]["inputs"])]
            det_next = plan[0] if plan[0] in exec_ok else \
                (exec_ok[0] if exec_ok else None)
            chosen = det_next
            # LLM routing (Sections 16/20) for P4/P5/P6
            if self.plevel >= 4 and self.use_llm and len(plan) > 1:
                ctx = {"query_id": qid, "query": query, "target": goal,
                       "input_kinds": kinds, "path_id": pid,
                       "step_id": step_id, "n_steps": n_steps,
                       "completed": completed,
                       "need_kind": "-", "route_options":
                       sorted(set(plan)),
                       "state": ([{"kind": s["kind"], "value": s["value"],
                                   "provenance": s["provenance"]}
                                  for s in state]
                                 if self.plevel >= 5 else [])}
                ro = LS.call_route(ctx)
                rec["llm_calls"].append(ro)
                rec["route_llm_calls"] += 1
                proposal = ro.get("next")
                valid = proposal in plan and proposal in exec_ok
                rec["route_events"].append(
                    {"step": step_id, "proposal": proposal,
                     "det": det_next, "valid": bool(valid),
                     "agree": proposal == det_next})
                if self.plevel == 4 or self.plevel == 5:
                    chosen = proposal if proposal in plan else None
                    if chosen is None:
                        rec["abstain_reason"] = "llm_route_invalid"
                        break
                else:  # P6: deterministic validation overrides
                    chosen = proposal if valid else det_next
            if chosen is None:
                # maybe the gap step is due
                if gap_kind:
                    need = gap_kind
                    ctx = {"query_id": qid, "query": query,
                           "target": goal, "input_kinds": kinds,
                           "path_id": pid, "step_id": step_id,
                           "n_steps": n_steps, "completed": completed,
                           "next_caps": [
                               f"{n}({', '.join(self.registry[n]['inputs'])}"
                               f") -> {self.registry[n]['output']}"
                               for n in plan[:1]]}
                    v = self._llm_step(need, state, ctx, rec,
                                       rec["transitions"])
                    if v is None:
                        rec["abstain_reason"] = f"llm_step_failed_{need}"
                        break
                    completed.append({"step": step_id,
                                      "cap": f"<LLM:{need}>",
                                      "by": "llm"})
                    gap_kind = None
                    continue
                rec["abstain_reason"] = "no_executable_step"
                break
            v, err = self._exec_step(chosen, state, qid, pid, step_id,
                                     rec["transitions"])
            if err is not None and gap_kind and err == gap_kind:
                # the missing input is the gap kind: LLM step now
                step_id -= 1
                ctx = {"query_id": qid, "query": query, "target": goal,
                       "input_kinds": kinds, "path_id": pid,
                       "step_id": step_id + 1, "n_steps": n_steps,
                       "completed": completed,
                       "next_caps": [
                           f"{chosen}({', '.join(self.registry[chosen]['inputs'])}"
                           f") -> {self.registry[chosen]['output']}"]}
                vv = self._llm_step(gap_kind, state, ctx, rec,
                                    rec["transitions"])
                if vv is None:
                    rec["abstain_reason"] = \
                        f"llm_step_failed_{gap_kind}"
                    break
                completed.append({"step": step_id + 1,
                                  "cap": f"<LLM:{gap_kind}>",
                                  "by": "llm"})
                gap_kind = None
                step_id += 1
                continue
            if err is not None:
                rec["abstain_reason"] = f"step_error_{chosen}:{err}"
                break
            completed.append({"step": step_id, "cap": chosen,
                              "by": "reflex"})
            plan.remove(chosen)
            value = v
        if value is not None and not plan:
            rec["status"] = "pm_answer"
            rec["numeric_value"] = value
            rec["completed"] = completed
            if pid and not str(pid).startswith("GAP") and \
                    self.plevel >= 3:
                prec = self.pi.by_code.get(
                    path_code(sorted(set(kinds)), rec["path"], goal))
            self.qi.records[qid]["final_result"] = value
        elif rec["status"] is None:
            out = self._llm_full(rec, query)
            out["t_ms"] = (time.perf_counter() - t0) * 1e3
            return out
        rec["t_ms"] = (time.perf_counter() - t0) * 1e3
        return rec
