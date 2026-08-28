"""V0.5 dependency-aware gap planner (Section 19).

V0.4's find_gap is forward-only: it proposes any kind whose injection makes
the goal types-reachable. The V0.4 core experiment showed interior unknowns
(KNOWN -> UNKNOWN -> KNOWN suffix) are the weakest regime (40% vs 60%
direct LLM, n=10).

Mechanism added here (registry-structural only, nothing tuned on any
evaluation split):

  FORWARD  reachable = kind_closure(state)
  BACKWARD demanded  = demand_closure(goal): kinds that can feed any
           capability chain ending in the goal, with a BFS distance
           (0 = the goal itself).
  GAP      candidates = demanded  \\  reachable, filtered to kinds whose
           injection completes a typed path (same criterion as V0.4),
           ranked by (consumes_unused, demand_distance).
  CONTRACT for the chosen kind K, the handoff carries:
             consumers: known capabilities that will CONSUME K on a demand
                        path, with their typed signatures ("net_profit will
                        feed margin_net(net_profit, revenue) -> rate")
             unused_available: parsed kinds no known capability consumes —
                        the missing transformation most likely involves
                        them.
           Both are derived from the registry + parsed state alone.
  MULTI    if no single kind unlocks the goal, kind PAIRS are tried
           (V0.4 recommendation: multi-kind gap detection).

The V0.4 forward-only planner remains available as the ablation
(Section 29-H).
"""
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import v4  # noqa: F401,E402
from v4.partial_planner import (_kind_closure, goal_kinds)  # noqa: E402
from v4 import registry_v4 as R4  # noqa: E402


def demand_closure(goals, reg):
    """kind -> BFS distance to the goal through capability inputs."""
    dist = {g: 0 for g in goals}
    frontier = deque(goals)
    while frontier:
        k = frontier.popleft()
        for spec in reg.values():
            if spec.get("transfer"):
                continue
            if spec["output"] == k:
                for i in spec["inputs"]:
                    if i not in dist:
                        dist[i] = dist[k] + 1
                        frontier.append(i)
    return dist


def _contract_for(K, base, have, reg, goals, demand):
    consumers = []
    for name, spec in reg.items():
        if spec.get("transfer") or K not in spec["inputs"]:
            continue
        if spec["output"] not in demand and spec["output"] not in goals:
            continue
        others = [i for i in spec["inputs"] if i != K]
        if all(o in base | {K} for o in others):
            consumers.append({
                "cap": name,
                "signature": f"{spec['output']} = "
                             f"{name}({', '.join(spec['inputs'])})"})
    used_by_known = set()
    for spec in reg.values():
        if not spec.get("transfer") and \
                all(k in base for k in spec["inputs"]):
            used_by_known |= set(spec["inputs"])
    unused = sorted(have - used_by_known)
    return {"consumers": consumers[:3], "unused_available": unused}


def find_gap_dep(qs, asked, priors=None, max_depth=6, registry=None,
                 suspect_mode=False):
    """Dependency-aware candidates. Same return shape as V0.4 find_gap,
    plus each candidate carries a 'contract' dict."""
    reg = registry if registry is not None else R4.REGISTRY
    have = {q.kind for q in qs}
    goals = set(goal_kinds(asked))
    base = _kind_closure(have, reg)
    demand = demand_closure(goals, reg)

    if suspect_mode:
        cands = []
        for name, spec in reg.items():
            if spec.get("transfer") or spec["output"] not in goals:
                continue
            missing = [k for k in spec["inputs"] if k not in base]
            if len(missing) == 1:
                K = missing[0]
                cands.append({"kind": K, "residual_len": 1,
                              "consumes_unused": True, "via": name,
                              "demand_distance": demand.get(K, 99),
                              "contract": _contract_for(
                                  K, base, have, reg, goals, demand)})
        seen, out = set(), []
        for c in sorted(cands, key=lambda c: c["demand_distance"]):
            if c["kind"] not in seen:
                seen.add(c["kind"])
                out.append(c)
        return out

    if base & goals:
        return []
    used_by_known = set()
    for spec in reg.values():
        if not spec.get("transfer") and \
                all(k in base for k in spec["inputs"]):
            used_by_known |= set(spec["inputs"])
    unused = have - used_by_known
    cands = []
    demanded_missing = [k for k in demand if k not in base]
    for K in sorted(demanded_missing):
        reach = _kind_closure(have | {K}, reg)
        if not (reach & goals):
            continue
        consumes_unused = any(
            K in spec["inputs"] and unused & set(spec["inputs"])
            for spec in reg.values())
        cands.append({"kind": K,
                      "residual_len": 0 if K in goals else 1,
                      "consumes_unused": consumes_unused,
                      "demand_distance": demand.get(K, 99),
                      "contract": _contract_for(K, base, have, reg, goals,
                                                demand)})
    cands.sort(key=lambda c: (-c["consumes_unused"], c["demand_distance"],
                              c["residual_len"]))
    if cands:
        return cands
    # multi-kind fallback: pairs of demanded-missing kinds
    pairs = []
    dm = demanded_missing[:12]
    for i, K1 in enumerate(dm):
        for K2 in dm[i + 1:]:
            reach = _kind_closure(have | {K1, K2}, reg)
            if reach & goals:
                d = min(demand.get(K1, 99), demand.get(K2, 99))
                pairs.append(({"kind": K1, "pair": K2,
                               "residual_len": 2, "consumes_unused": False,
                               "demand_distance": d,
                               "contract": _contract_for(
                                   K1, base, have, reg, goals, demand)}))
    pairs.sort(key=lambda c: c["demand_distance"])
    return pairs
