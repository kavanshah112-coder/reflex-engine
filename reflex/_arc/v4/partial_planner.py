"""Partial-path planning (Sections 15-16): compute the largest safe reflex
prefix, detect the typed GAP (which single kind, if provided, unlocks a path
to the goal), hand that subproblem to the LLM, validate, inject, resume.

Gap detection is STRUCTURAL, not confidence-based (Section 16): a kind K is a
gap candidate iff hypothetically adding K lets the typed planner complete the
path. The residual plan computed with a dummy value gives the resume structure;
the real LLM value replaces the dummy and everything re-executes.
"""
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import v4  # noqa: F401

from v3 import capabilities as C3       # noqa: E402
from v3 import planner as P3            # noqa: E402
from v3.ir import Quantity, KINDS       # noqa: E402
from v4 import registry_v4 as R4        # noqa: E402

MONEY_GROUP = ["money", "cost_var", "cost_total", "profit", "net_profit",
               "revenue", "interest", "cost_eur", "final_amount",
               "sale_price"]


@contextmanager
def use_registry(reg):
    """Point the frozen V0.3 planner at the V0.4 registry + executor."""
    old_reg, old_exec = C3.REGISTRY, C3.execute
    C3.REGISTRY = reg
    C3.execute = lambda name, inputs: R4.execute(name, inputs, registry=reg)
    try:
        yield
    finally:
        C3.REGISTRY, C3.execute = old_reg, old_exec


def goal_kinds(asked):
    if asked == "money":
        return MONEY_GROUP
    return [asked]


def plan_known(qs, asked, priors=None, max_depth=6, registry=None,
               must_use=()):
    from v4 import planner4 as P4
    reg = registry if registry is not None else R4.REGISTRY
    # types-only reachability pre-filter: never run the value planner toward a
    # goal kind that is not even kind-reachable (fail fast)
    reach = _kind_closure({q.kind for q in qs}, reg)
    ex = lambda name, inputs: R4.execute(name, inputs, registry=reg)  # noqa
    for g in goal_kinds(asked):
        if g not in reach:
            continue
        r = P4.plan(qs, g, reg, ex, priors=priors, max_depth=max_depth,
                    must_use=must_use)
        if r["ok"]:
            r["goal_kind"] = g
            return r
    return {"ok": False, "path": [], "value": None,
            "stats": {"expansions": 0, "executor_calls": 0,
                      "max_branching": 0},
            "goal_kind": asked}


def _kind_closure(kinds, reg):
    """Types-only reachability: which kinds become derivable from `kinds`."""
    have = set(kinds)
    changed = True
    while changed:
        changed = False
        for spec in reg.values():
            if spec.get("transfer"):
                continue
            if spec["output"] not in have and \
                    all(k in have for k in spec["inputs"]):
                have.add(spec["output"])
                changed = True
    return have


def find_gap(qs, asked, priors=None, max_depth=6, registry=None,
             suspect_mode=False):
    """Which single kind unlocks the goal? TYPES-ONLY reachability closure
    per candidate (fast); the real planner runs after injection.

    suspect_mode: the goal is already reachable but query quantities are
    unused — propose the missing inputs of known-but-inapplicable
    capabilities instead (e.g. margin_net's unproducible net_profit), so a
    FULLER path can be built through a handoff."""
    reg = registry if registry is not None else R4.REGISTRY
    have = {q.kind for q in qs}
    goals = set(goal_kinds(asked))
    base = _kind_closure(have, reg)
    if suspect_mode:
        # only capabilities that DIRECTLY produce a goal kind qualify — the
        # goal is already reachable, so reachability alone discriminates
        # nothing; we want the fuller path ending in the goal
        cands = []
        for name, spec in reg.items():
            if spec.get("transfer") or spec["output"] not in goals:
                continue
            missing = [k for k in spec["inputs"] if k not in base]
            if len(missing) == 1:
                cands.append({"kind": missing[0], "residual_len": 1,
                              "consumes_unused": True, "via": name})
        # dedupe by kind
        seen, out = set(), []
        for c in cands:
            if c["kind"] not in seen:
                seen.add(c["kind"])
                out.append(c)
        return out
    if base & goals:
        return []          # goal already reachable; no gap
    # candidates: kinds consumed by some capability, or the goal itself
    cand_kinds = {k for spec in reg.values() for k in spec["inputs"]} | goals
    # ranking: prefer gaps whose injected kind is consumed ALONGSIDE query
    # kinds that no known path uses yet (the LLM should solve the SIMPLEST
    # missing transformation, letting reflex consume the leftovers), then
    # goal-direct gaps
    used_by_known = set()
    for spec in reg.values():
        if all(k in base for k in spec["inputs"]):
            used_by_known |= set(spec["inputs"])
    unused = have - used_by_known
    cands = []
    for K in sorted(cand_kinds - base):
        reach = _kind_closure(have | {K}, reg)
        if reach & goals:
            consumes_unused = any(
                K in spec["inputs"] and unused & set(spec["inputs"])
                for spec in reg.values())
            cands.append({"kind": K,
                          "residual_len": 0 if K in goals else 1,
                          "consumes_unused": consumes_unused})
    cands.sort(key=lambda c: (-c["consumes_unused"], c["residual_len"]))
    return cands


def forward_closure(qs, priors=None, max_steps=None, registry=None):
    """Largest safe computable prefix: greedily apply applicable capabilities
    (highest prior first), each at most once, until nothing applies. Runs to
    EXHAUSTION by default — a step cap once made a physics detour (mass ->
    weight -> potential energy) starve the money chain that the gap actually
    needed. Skips capabilities whose output kind is already present
    (no-redundant-production, mirroring planner4)."""
    reg = registry if registry is not None else R4.REGISTRY
    from dataclasses import replace
    state = [replace(q) for q in qs]
    path = []
    for _ in range(max_steps if max_steps is not None else len(reg)):
        have = {}
        for q in state:
            if not q.consumed:
                have.setdefault(q.kind, q)
        apps = []
        for name, spec in reg.items():
            if spec.get("transfer") or name in path:
                continue
            if spec["output"] in have:
                continue
            if all(k in have for k in spec["inputs"]):
                apps.append(((priors or {}).get(name, 0.5), name))
        if not apps:
            break
        _, name = max(apps)
        spec = reg[name]
        inputs = {k: have[k] for k in spec["inputs"]}
        v, ok, _ = R4.execute(name, inputs, registry=reg)
        if not ok:
            break
        for k in spec["inputs"]:
            if k in ("energy",):
                inputs[k].consumed = True
        state.append(Quantity(kind=spec["output"], value=v, source=name))
        path.append(name)
    return state, path
