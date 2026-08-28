# -*- coding: utf-8 -*-
"""V0.6 capability graph + path-finder variants (spec Sections 8-10, 30,
31).

Nodes = executable capabilities. Edges are TYPED CONTRACTS:
  derived edge  A -> B  iff  A.output in B.inputs      (registry-implied)
  direct edge   A -> B  bred by the link miner, carrying provenance,
                support, validation status, generation.

Path-finder variants (all measured; none assumed better — V0.5 measured
dependency-aware planning as n.s. NEGATIVE):
  P1 forward-only  the V0.4/V0.5 value planner (plan_known) — CONTROL
  P2 typed graph   backward kind-BFS over the capability graph to a
                   path SKETCH, then deterministic execution of the
                   sketch; falls back to P1 on sketch failure
  P3 direct-link   P2 but bred direct edges get priority (searched
                   first) — tests spec 31 (Physics->Derivation vs long
                   traversal)
  P5 static        single-capability lookup only (control)

Every variant reports: value, path, expansions (search effort), and
sketch validity — so search cost and answer quality are separable.
"""
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4                  # noqa: E402
from v4.partial_planner import plan_known, goal_kinds  # noqa: E402
from v3.ir import Quantity                        # noqa: E402


class CapGraph:
    def __init__(self, registry=None, direct_links=None):
        self.reg = registry if registry is not None else R4.REGISTRY
        self.direct = direct_links or []
        self._build()

    def _build(self):
        self.producers = defaultdict(list)   # kind -> [cap]
        self.derived_edges = []
        for name, spec in self.reg.items():
            if spec.get("transfer"):
                continue
            self.producers[spec["output"]].append(name)
        for a, sa in self.reg.items():
            if sa.get("transfer"):
                continue
            for b, sb in self.reg.items():
                if b == a or sb.get("transfer"):
                    continue
                if sa["output"] in sb["inputs"]:
                    self.derived_edges.append((a, b, sa["output"]))
        self.direct_by_dst = defaultdict(list)
        for e in self.direct:
            if e.get("status", "deployed") == "deployed":
                self.direct_by_dst[e["dst"]].append(e)

    def stats(self):
        return {"capabilities": len([1 for s in self.reg.values()
                                     if not s.get("transfer")]),
                "derived_edges": len(self.derived_edges),
                "direct_links": len(self.direct),
                "kinds": len(self.producers)}

    def save(self, path):
        Path(path).write_text(json.dumps(
            {"stats": self.stats(),
             "derived_edges": self.derived_edges,
             "direct_links": self.direct}, indent=1), encoding="utf-8")

    # ------------------------------------------------------------------
    def sketch_backward(self, have_kinds, goal, prefer_direct=False,
                        max_caps=12):
        """Backward BFS: which capabilities, in dependency order, derive
        `goal` from `have_kinds`? Returns (ordered caps, expansions) or
        (None, expansions)."""
        need = deque([goal])
        chosen = []
        satisfied = set(have_kinds)
        expansions = 0
        guard = 0
        while need and guard < 200:
            guard += 1
            k = need.popleft()
            if k in satisfied:
                continue
            prods = list(self.producers.get(k, []))
            if prefer_direct:
                boosted = [e["src"] for e in self.direct_by_dst.get(
                    "?", [])]
                direct_srcs = {e["src"] for cap in prods
                               for e in self.direct_by_dst.get(cap, [])}
                prods.sort(key=lambda c: (c not in direct_srcs,))
            if not prods:
                return None, expansions
            best = None
            for cap in prods:
                expansions += 1
                spec = self.reg[cap]
                missing = [i for i in spec["inputs"]
                           if i not in satisfied]
                producible = all(self.producers.get(i) or i in satisfied
                                 for i in spec["inputs"])
                if not producible:
                    continue
                if best is None or len(missing) < best[0]:
                    best = (len(missing), cap, missing)
            if best is None:
                return None, expansions
            _, cap, missing = best
            if cap in [c for c, _ in chosen]:
                return None, expansions       # cycle
            chosen.append((cap, k))
            satisfied.add(k)
            for mk in missing:
                need.append(mk)
            if len(chosen) > max_caps:
                return None, expansions
        # dependency order: repeatedly emit caps whose inputs are ready
        order = []
        ready = set(have_kinds)
        remaining = [c for c, _ in chosen]
        guard = 0
        while remaining and guard < 50:
            guard += 1
            for cap in list(remaining):
                if all(i in ready for i in self.reg[cap]["inputs"]):
                    order.append(cap)
                    ready.add(self.reg[cap]["output"])
                    remaining.remove(cap)
        if remaining:
            return None, expansions
        return order, expansions


def execute_sketch(order, qs, registry):
    """Deterministically execute a capability order; returns (value of
    the last step, ok)."""
    have = {}
    for q in qs:
        have.setdefault(q.kind, q.value)
    for cap in order:
        spec = registry[cap]
        if not all(k in have for k in spec["inputs"]):
            return None, False
        ins = {k: Quantity(kind=k, value=have[k])
               for k in spec["inputs"]}
        v, ok, _ = R4.execute(cap, ins, registry=registry)
        if not ok:
            return None, False
        have[spec["output"]] = v
    return (have[registry[order[-1]]["output"]], True) if order else \
        (None, False)


def pathfind(variant, qs, ak, registry, graph=None, priors=None):
    """Unified entry. Returns {ok, value, path, expansions, sketch_ok,
    variant}."""
    if variant == "P1":
        r = plan_known(qs, ak, priors=priors, registry=registry)
        return {"ok": r["ok"], "value": r.get("value"),
                "path": r.get("path", []),
                "expansions": r["stats"]["expansions"],
                "sketch_ok": None, "variant": "P1"}
    if variant == "P5":
        for name, spec in registry.items():
            if spec.get("transfer"):
                continue
            if spec["output"] in goal_kinds(ak) and \
                    all(any(q.kind == k for q in qs)
                        for k in spec["inputs"]):
                ins = {k: next(q for q in qs if q.kind == k)
                       for k in spec["inputs"]}
                v, ok, _ = R4.execute(name, ins, registry=registry)
                if ok:
                    return {"ok": True, "value": v, "path": [name],
                            "expansions": 1, "sketch_ok": None,
                            "variant": "P5"}
        return {"ok": False, "value": None, "path": [], "expansions": 1,
                "sketch_ok": None, "variant": "P5"}
    # P2 / P3
    g = graph or CapGraph(registry)
    have = {q.kind for q in qs}
    best = None
    total_exp = 0
    for goal in goal_kinds(ak):
        order, exp = g.sketch_backward(have, goal,
                                       prefer_direct=(variant == "P3"))
        total_exp += exp
        if order is not None:
            v, ok = execute_sketch(order, qs, registry)
            if ok:
                best = {"ok": True, "value": v, "path": order,
                        "expansions": total_exp, "sketch_ok": True,
                        "variant": variant}
                break
    if best:
        return best
    # sketch failed -> P1 fallback (recorded)
    r = plan_known(qs, ak, priors=priors, registry=registry)
    return {"ok": r["ok"], "value": r.get("value"),
            "path": r.get("path", []),
            "expansions": total_exp + r["stats"]["expansions"],
            "sketch_ok": False, "variant": variant + "+P1fallback"}
