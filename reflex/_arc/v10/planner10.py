# -*- coding: utf-8 -*-
"""V0.10 long-path planner (Section 11): goal-regression backward
chaining with subgoal memoization, replacing kind_path_search's
horizon-limited forward BFS (the proven V0.9 depth wall — see
results/raw_v10/depth_autopsy.json).

Properties (measured in the autopsy):
- exact-linear expansions in plan length (25 exp @ depth 25);
- correct DAG merges (branching chains share sub-plans);
- GAP-AWARE: when a subgoal kind has no producer, the planner emits a
  ("<GAP>", kind) pseudo-step instead of failing — the unknown budget
  routes exactly that typed step to the LLM (case D). Plans are ranked
  by (fewest gaps, shortest length, lexicographic).

Deterministic: no randomness, lexicographic tie-breaks.
"""
import time

MONEY_GROUP = None


def _money_group():
    global MONEY_GROUP
    if MONEY_GROUP is None:
        try:
            from v4.partial_planner import MONEY_GROUP as MG
            MONEY_GROUP = set(MG)
        except Exception:
            MONEY_GROUP = set()
    return MONEY_GROUP


def plan(kinds, target, registry, max_depth=64, max_gaps=1,
         allow_gaps=True):
    """Returns (steps, stats). steps is a tuple of capability names,
    with ("<GAP>", kind) tuples for missing capabilities (at most
    max_gaps). None if no plan within limits. Ordered executably."""
    t0 = time.perf_counter()
    have = set(kinds)
    stats = {"expansions": 0, "gaps": 0, "memo_hits": 0}
    producers = {}
    for name in sorted(registry):
        spec = registry[name]
        if spec.get("transfer"):
            continue
        producers.setdefault(spec["output"], []).append(name)
    memo = {}

    def solve(kind, stack):
        """Returns (steps_tuple, n_gaps) or None. steps executable in
        order; gap pseudo-steps included."""
        if kind in have:
            return ((), 0)
        if kind in memo:
            stats["memo_hits"] += 1
            return memo[kind]
        if kind in stack or len(stack) > max_depth:
            return None          # cycle/depth — do NOT memoize
        best = None
        for name in producers.get(kind, []):
            stats["expansions"] += 1
            steps, gaps, ok = (), 0, True
            for k in registry[name]["inputs"]:
                sub = solve(k, stack | {kind})
                if sub is None:
                    ok = False
                    break
                ss, gg = sub
                for s in ss:
                    if s not in steps:
                        steps += (s,)
                gaps += gg
            if ok:
                cand = (steps + (name,), gaps)
                if best is None or (cand[1], len(cand[0]), cand[0]) < \
                        (best[1], len(best[0]), best[0]):
                    best = cand
        if best is None and allow_gaps:
            best = ((("<GAP>", kind),), 1)
        if best is not None and best[1] > max_gaps:
            best = None
        # memoize successes AND producer-exhausted failures (stack-free)
        if best is not None or not producers.get(kind):
            memo[kind] = best
        return best

    goals = [target]
    if target == "money" and _money_group():
        goals = sorted(_money_group())
    result = None
    for g in goals:
        r = solve(g, frozenset())
        if r is not None and (result is None or
                              (r[1], len(r[0])) <
                              (result[1], len(result[0]))):
            result = r
            stats["goal"] = g
    stats["wall_ms"] = (time.perf_counter() - t0) * 1e3
    if result is None:
        return None, stats
    steps, gaps = result
    # dedup while preserving order (shared sub-plans merge)
    seen, ordered = set(), []
    for s in steps:
        key = s if isinstance(s, tuple) else ("cap", s)
        if key not in seen:
            seen.add(key)
            ordered.append(s)
    stats["gaps"] = gaps
    stats["plan_len"] = len(ordered)
    return tuple(ordered), stats


def verify_executable(steps, kinds, registry):
    """Deterministic order check: every step's inputs available when
    reached (gap steps produce their kind)."""
    have = set(kinds)
    for s in steps:
        if isinstance(s, tuple):          # ("<GAP>", kind)
            have.add(s[1])
            continue
        spec = registry[s]
        if not all(k in have for k in spec["inputs"]):
            return False
        have.add(spec["output"])
    return True
