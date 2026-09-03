# -*- coding: utf-8 -*-
# origin: new for V1.7 -- engine-side DAG execution + end gate (SPEC 4)
"""Executes a plan with the ENGINE's machinery (symcore16 / certified
conversions), then refuses to certify unless the independent chain
witness re-derives the same final.

    run(plan, sabotage=False) -> (value, cert) | (None, refusal)

Per-node execution is the sympy side; the mpmath side never sees the
engine's intermediates -- it replays the plan from its literals. The
disagreement tolerance is depth-budgeted (chain_witness17.rel_tol).

GATE-CTRL: run(plan, sabotage=True) corrupts the engine's final
before the end gate; the control battery requires 100% refusal.
"""
import re
import sys
from pathlib import Path

from . import planschema17 as PS
from . import symcore16

_TOOLS = str(Path(__file__).resolve().parent.parent / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import chain_witness17 as CW  # noqa: E402

try:
    import pint
    _UREG = pint.UnitRegistry()
except Exception:                                   # pragma: no cover
    _UREG = None

# plan ops -> symcore task ops (engine side); "evaluate" is handled
# with "formula" (extra slots become the env)
_SYM_OPS = {"integrate_def", "limit", "sum_finite",
            "gcd", "lcm", "ncr", "npr", "is_prime", "probability"}


def _refuse(why, **kw):
    d = {"why": why}
    d.update(kw)
    return None, d


def _subst(node, env):
    """Resolve @refs into literals for the engine side."""
    out = {}
    for k, v in node.items():
        if k == "id":
            continue
        if PS.is_ref(v):
            out[k] = env[v[1:]]
        elif isinstance(v, str) and "@" in v:
            out[k] = re.sub(r"@(n\d+)\b",
                            lambda m: repr(float(env[m.group(1)])), v)
        else:
            out[k] = v
    return out


def _exec_engine(node, env):
    """One node, engine side. Returns value or raises ValueError."""
    n = _subst(node, env)
    op = n.pop("op")
    if op == "scale":
        return float(n["value"]) * float(n["by"])
    if op == "convert":
        if _UREG is None:
            raise ValueError("no converter")
        return float((float(n["value"]) * _UREG(n["from"]))
                     .to(n["to"]).magnitude)
    if op == "compare":
        a, b = float(n["a"]), float(n["b"])
        return 1.0 if a > b else (-1.0 if b > a else 0.0)
    if op == "derivative_at":
        task = {"op": "differentiate", "expr": n["expr"],
                "var": n.get("var", "x"),
                "order": int(n.get("order", 1)),
                "at": float(n["point"]),
                "leaf": "mathematics/calculus/differentiation/"
                        "evaluate_at_point"}
        val, cert = symcore16.solve(task)
        if val is None:
            raise ValueError("step refused: %s" % cert.get("why"))
        return float(val)
    if op == "solve_pick":
        task = {"op": "solve_poly", "lhs": n["lhs"],
                "rhs": n.get("rhs", "0"), "var": n.get("var", "x"),
                "leaf": "mathematics/algebra/"
                        "quadratic_polynomial_solve"}
        val, cert = symcore16.solve(task)
        if val is None:
            raise ValueError("step refused: %s" % cert.get("why"))
        roots = val if isinstance(val, list) else [val]
        return float(max(roots) if n.get("pick", "larger") ==
                     "larger" else min(roots))
    if op in ("formula", "evaluate"):
        env2 = {k: float(v) for k, v in n.items()
                if k not in ("expr",)}
        task = {"op": "evaluate", "expr": n["expr"], "env": env2,
                "leaf": "mathematics/arithmetic/expression_evaluation"}
        val, cert = symcore16.solve(task)
        if val is None:
            raise ValueError("step refused: %s" % cert.get("why"))
        return float(val)
    if op in _SYM_OPS:
        task = dict(n)
        task["op"] = op
        from . import taxonomy16
        leaf = taxonomy16.place_symbolic(task)
        if leaf is None:
            raise ValueError("unplaceable step %r" % op)
        task["leaf"] = leaf
        val, cert = symcore16.solve(task)
        if val is None:
            raise ValueError("step refused: %s" % cert.get("why"))
        if isinstance(val, bool):
            return 1.0 if val else 0.0
        if isinstance(val, list):
            raise ValueError("list output needs solve_pick")
        return float(val)
    raise ValueError("unknown op %r" % op)


def run(plan, sabotage=False):
    env = {}
    steps = []
    try:
        for node in plan["nodes"]:
            v = _exec_engine(node, env)
            env[node["id"]] = v
            steps.append({"id": node["id"], "op": node["op"],
                          "value": v})
        final = float(env[plan["final"]])
    except (ValueError, KeyError, TypeError, ZeroDivisionError,
            OverflowError, RecursionError) as exc:
        return _refuse("chain execution refused: %s" % exc)
    if sabotage:
        final = final * 1.5 + 7
    try:
        ok, detail = CW.check_final(plan, final)
    except CW.ChainRefuse as exc:
        return _refuse("end witness cannot replay: %s" % exc)
    if not ok:
        return _refuse("end witness rejected", **detail)
    return final, {"steps": steps, "end_witness": detail,
                   "signature": PS.signature(plan)}


def gate_control():
    """Every sound control plan certifies; every sabotage refuses."""
    plans = [p for p, _g in CW.control_battery.__defaults__ or []] \
        if False else None
    # reuse the witness battery's sound plans directly
    sound = [
        {"nodes": [
            {"id": "n1", "op": "solve_pick",
             "lhs": "x**2 - 5*x + 6", "pick": "larger"},
            {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
            {"id": "n3", "op": "formula",
             "expr": "0.5 * m * v**2", "m": 10, "v": "@n2"}],
         "final": "n3"},
        {"nodes": [
            {"id": "n1", "op": "integrate_def", "expr": "x**2",
             "a": 0, "b": 3},
            {"id": "n2", "op": "scale", "value": "@n1", "by": 1000},
            {"id": "n3", "op": "convert", "value": "@n2",
             "from": "J", "to": "kJ"},
            {"id": "n4", "op": "compare", "a": "@n3", "b": 8.0}],
         "final": "n4"},
        {"nodes": [
            {"id": "n1", "op": "gcd", "a": 45, "b": 27},
            {"id": "n2", "op": "ncr", "n": 10, "r": 3},
            {"id": "n3", "op": "evaluate", "expr": "a + b",
             "a": "@n1", "b": "@n2"}],
         "final": "n3"},
        {"nodes": [
            {"id": "n1", "op": "derivative_at", "expr": "x**3",
             "point": 2, "order": 1},
            {"id": "n2", "op": "convert", "value": "@n1",
             "from": "m/s", "to": "km/h"}],
         "final": "n2"},
    ]
    fails = []
    for p in sound:
        v, cert = run(p)
        if v is None:
            fails.append(("SOUND REFUSED", p["final"], cert))
        sv, scert = run(p, sabotage=True)
        if sv is not None:
            fails.append(("SABOTAGE SERVED", p["final"], sv))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = gate_control()
    print("chainexec GATE-CTRL:", "PASS" if ok else "FAIL",
          "(4 chains, honest certify + sabotage refuse)")
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
