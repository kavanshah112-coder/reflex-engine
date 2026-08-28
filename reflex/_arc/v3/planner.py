"""Dynamic capability planner (Section 18): typed forward chaining.

State = typed quantities available (parsed + produced). A capability is
APPLICABLE when every input kind is present (bindability). Best-first search
expands applicable capabilities, scored by neural capability priors (from
concept nodes) x type-goal heuristics; stops when the asked kind is produced.
No chain is stored anywhere — every path is constructed at query time from
typed compatibility. Instrumented: expansions, branching, executor calls.
"""
import heapq
import itertools

from v3 import capabilities as C
from v3.ir import Quantity, PlanState, CONSUMABLE_KINDS

MAX_DEPTH_DEFAULT = 4


def plan(quantities, goal_kind, priors=None, max_depth=MAX_DEPTH_DEFAULT,
         beam=24):
    """Best-first typed forward search.

    quantities: list[Quantity] parsed from the query.
    goal_kind: kind the question asks for.
    priors: dict capability_name -> relevance in [0,1] (neural; default 0.5).
    Returns dict with best result + search stats.
    """
    priors = priors or {}
    stats = {"expansions": 0, "executor_calls": 0, "max_branching": 0,
             "states_seen": 0}
    s0 = PlanState()
    for q in quantities:
        s0.add(q)
    if s0.has(goal_kind) and goal_kind not in ("energy",):
        # asked quantity literally given (degenerate); still allow search to
        # produce it properly, but record the trivial option
        pass

    counter = itertools.count()
    n_query = max(1, len(quantities))
    # priority: -score, path length, tiebreak counter
    heap = [(-1.0, 0, next(counter), s0, 1.0)]
    goal_candidates = []
    seen_paths = set()
    while heap and len(goal_candidates) < 5:
        neg, depth, _, state, score = heapq.heappop(heap)
        stats["states_seen"] += 1
        if state.has(goal_kind) and state.path:
            # the goal must be PRODUCED by the path, not merely present in the
            # query (inputs bind query-first; the goal scans newest-first)
            produced = next((q for q in reversed(state.quantities[goal_kind])
                             if q.source != "query"), None)
            if produced is not None:
                # DANGLING-INTERMEDIATE CHECK: every non-final step's output
                # must be consumed by a later step (a plan that computes the
                # Carnot efficiency and then ignores it is invalid dataflow)
                sources_used = {s for step in state.step_sources
                                for s in step.values()}
                dangling = any(
                    name not in sources_used
                    for name in state.path[:-1])
                if dangling:
                    continue
                # input coverage: how many of the query's quantities does this
                # plan actually consume? A plan that ignores supplied givens
                # (e.g. lifting with raw heat while the reservoir temperatures
                # go unused) is suspect — prefer maximal utilization.
                used_kinds = set()
                for name in state.path:
                    used_kinds |= set(C.REGISTRY[name]["inputs"])
                coverage = sum(1 for q in quantities
                               if q.kind in used_kinds) / n_query
                goal_candidates.append(
                    {"state": state, "score": score, "coverage": coverage,
                     "value": produced.value, "quantity": produced})
                continue
        if depth >= max_depth:
            continue
        applicable = []
        for name, spec in C.REGISTRY.items():
            if spec.get("transfer"):
                continue
            if name in state.path:  # no capability repetition in one path
                continue
            if all(state.has(k) for k in spec["inputs"]):
                applicable.append(name)
        stats["max_branching"] = max(stats["max_branching"], len(applicable))
        for name in applicable:
            spec = C.REGISTRY[name]
            inputs = {k: state.get(k) for k in spec["inputs"]}
            value, ok, reason = C.execute(name, inputs)
            stats["executor_calls"] += 1
            if not ok:
                continue
            ns = state.clone()
            # resource-linear consumption: energy inputs are used up (no
            # double-counting a Joule); parameters (mass, temps, c) reusable
            for k in spec["inputs"]:
                if k in CONSUMABLE_KINDS:
                    ns.get(k).consumed = True
            ns.add(Quantity(kind=spec["output"], value=value, source=name))
            ns.path = state.path + [name]
            ns.step_sources = state.step_sources + [
                {k: inputs[k].source for k in spec["inputs"]}]
            key = tuple(ns.path)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            stats["expansions"] += 1
            prior = priors.get(name, 0.5)
            # heuristic: does this capability's output move toward the goal?
            out_kind = spec["output"]
            toward = 1.0 if out_kind == goal_kind else \
                (0.7 if C.caps_consuming(out_kind) else 0.4)
            nscore = score * (0.35 + 0.65 * prior) * toward
            heapq.heappush(heap, (-nscore, depth + 1, next(counter), ns,
                                  nscore))
        if len(heap) > beam:
            heap = heapq.nsmallest(beam, heap)
            heapq.heapify(heap)
    if not goal_candidates:
        return {"ok": False, "reason": "no typed path to goal",
                "stats": stats, "path": [], "value": None, "score": 0.0,
                "coverage": 0.0, "n_alternatives": 0}
    best = max(goal_candidates,
               key=lambda c: (round(c["coverage"], 3), c["score"]))
    st = best["state"]
    return {"ok": True, "path": st.path, "value": best["value"],
            "score": best["score"], "coverage": best["coverage"],
            "n_alternatives": len(goal_candidates),
            "conversions": st.conversions, "stats": stats}


def render_path(path, conversions):
    """Human/GT-comparable path: conversions first, conservation markers where
    energy crosses between capabilities of different domains."""
    out = list(conversions)
    prev_domain = None
    for name in path:
        d = C.REGISTRY[name]["domain"]
        if (prev_domain is not None and d != prev_domain
                and C.REGISTRY[name]["inputs"][0] == "energy"):
            out.append("energy_conservation")
        out.append(name)
        prev_domain = d
    return out


def alternate_value(quantities, goal_kind, exclude_path, priors=None,
                    max_depth=MAX_DEPTH_DEFAULT):
    """Second-opinion: best path that differs from exclude_path (risk feature:
    alternative-path agreement)."""
    priors = dict(priors or {})
    for name in exclude_path:
        priors[name] = min(priors.get(name, 0.5), 0.05)
    r = plan(quantities, goal_kind, priors=priors, max_depth=max_depth)
    if r["ok"] and r["path"] != list(exclude_path):
        return r["value"], r["path"]
    return None, None
