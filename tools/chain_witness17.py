# -*- coding: utf-8 -*-
# origin: new for V1.7 -- end-to-end chain witness (SPEC 4; mpmath only)
"""Replays a WHOLE plan on the mpmath side, no sympy anywhere.

Consumers:
  * build_q1m: computes golds (the witness IS the gold constructor,
    so no gold ever comes from engine code);
  * chainexec17: after the sympy-side executor produces a final
    value, this module re-derives it independently; disagreement
    beyond the depth-budgeted tolerance REFUSES the serve. One end
    check, not k stacked ones (SPEC Q1).

Tolerance budget: rel_tol(k) = 1e-6 * 3**(k-1), capped at 1e-3.
Numeric-differentiation steps widen it to 1e-3 flat (finite
differences carry O(h^2) noise; V1.6 precedent).

Ops implemented (mpmath/math only):
  evaluate, formula, scale, convert, derivative_at, integrate_def,
  limit, solve_pick (larger/smaller real root of a quadratic/linear,
  via mpmath.polyroots on extracted coefficients -- REFUSES on
  non-polynomial lhs), sum_finite, gcd, lcm, ncr, npr, is_prime,
  probability, compare.

POSITIVE CONTROL (B24): control_battery() -- seeded wrong finals
must all fail; sound chains must all pass.
"""
import math
import sys
from pathlib import Path

from mpmath import mp, mpf, polyroots, quad

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gold_independent as W  # noqa: E402  (mpmath witness core)

mp.dps = 30

try:
    import pint
    _UREG = pint.UnitRegistry()
except Exception:                                   # pragma: no cover
    _UREG = None


class ChainRefuse(Exception):
    pass


def rel_tol(k, has_fd=False):
    if has_fd:
        return 1e-3
    return min(1e-6 * (3 ** max(0, k - 1)), 1e-3)


def _poly_coeffs(expr, var="x", deg_max=3):
    """Extract polynomial coefficients numerically by sampling --
    stays sympy-free. Fits exact-degree polynomial via solve of a
    Vandermonde system in mpmath; refuses if residual is large."""
    pts = [mpf(p) for p in (-2, -1, 0, 1, 2)][:deg_max + 1]
    import mpmath
    A = mpmath.matrix([[p ** j for j in range(deg_max + 1)]
                       for p in pts])
    b = mpmath.matrix([W.evaluate(expr, {var: p}) for p in pts])
    c = mpmath.lu_solve(A, b)
    # verify at a fresh point
    x0 = mpf("0.7")
    fit = sum(c[j] * x0 ** j for j in range(deg_max + 1))
    if abs(fit - W.evaluate(expr, {var: x0})) > mpf("1e-9") * (
            1 + abs(fit)):
        raise ChainRefuse("lhs is not a low-degree polynomial")
    return [float(c[j]) for j in range(deg_max + 1)]


def _exec_node(node, env):
    op = node["op"]

    def val(key, default=None):
        v = node.get(key, default)
        if isinstance(v, str) and v.startswith("@"):
            return env[v[1:]]
        return v

    def expr_sub(key):
        """Expression slot with @refs replaced by numeric literals."""
        s = str(node[key])
        import re
        def rep(m):
            return repr(float(env[m.group(1)]))
        return re.sub(r"@(n\d+)\b", rep, s)

    if op in ("evaluate", "formula"):
        e = expr_sub("expr")
        environ = {}
        for k, v in node.items():
            if k in ("id", "op", "expr"):
                continue
            environ[k] = float(val(k))
        return float(W.evaluate(e, environ))
    if op == "scale":
        return float(val("value")) * float(val("by"))
    if op == "convert":
        if _UREG is None:
            raise ChainRefuse("no converter")
        return float((float(val("value")) * _UREG(node["from"]))
                     .to(node["to"]).magnitude)
    if op == "derivative_at":
        e = expr_sub("expr")
        return float(W._fd(e, node.get("var", "x"),
                           float(val("point")),
                           int(node.get("order", 1)), {}))
    if op == "integrate_def":
        e = expr_sub("expr")
        v = node.get("var", "x")
        return float(quad(lambda t: W.evaluate(e, {v: t}),
                          [float(val("a")), float(val("b"))]))
    if op == "limit":
        e = expr_sub("expr")
        pt = node["point"]
        seq = ([mpf(10) ** j for j in (4, 5, 6)] if pt in
               ("inf", "oo") else
               [mpf(pt) + mpf(10) ** -j for j in (4, 5, 6)])
        vals = [W.evaluate(e, {node.get("var", "x"): x}) for x in seq]
        if abs(vals[-1] - vals[-2]) > mpf("1e-3") * (1 +
                                                     abs(vals[-1])):
            raise ChainRefuse("limit not settling")
        return float(vals[-1])
    if op == "solve_pick":
        e = expr_sub("lhs")
        coeffs = _poly_coeffs(e, node.get("var", "x"))
        while coeffs and abs(coeffs[-1]) < 1e-12:
            coeffs.pop()
        if len(coeffs) < 2:
            raise ChainRefuse("degenerate equation")
        roots = polyroots(list(reversed(coeffs)))
        real = sorted(float(r.real) for r in roots
                      if abs(r.imag) < 1e-9)
        if not real:
            raise ChainRefuse("no real roots")
        return max(real) if node.get("pick", "larger") == "larger" \
            else min(real)
    if op == "sum_finite":
        e = str(node["expr"])
        v = node.get("var", "k")
        a, b = int(val("a")), int(val("b"))
        if b - a > 100000:
            raise ChainRefuse("sum too large")
        return float(sum(W.evaluate(e, {v: i})
                         for i in range(a, b + 1)))
    if op in ("gcd", "lcm"):
        a, b = int(val("a")), int(val("b"))
        g = math.gcd(a, b)
        return float(g if op == "gcd" else abs(a * b) // g)
    if op in ("ncr", "npr"):
        n, r = int(val("n")), int(val("r"))
        if r < 0 or r > n or n > 5000:
            raise ChainRefuse("bad n,r")
        return float(math.comb(n, r) if op == "ncr" else
                     math.perm(n, r))
    if op == "is_prime":
        n = int(val("n"))
        return float(n >= 2 and all(n % i for i in
                                    range(2, int(math.isqrt(n)) + 1)))
    if op == "probability":
        f, t = float(val("favorable")), float(val("total"))
        if t <= 0 or f < 0 or f > t:
            raise ChainRefuse("bad probability")
        return f / t
    if op == "compare":
        a, b = float(val("a")), float(val("b"))
        return 1.0 if a > b else (-1.0 if b > a else 0.0)
    raise ChainRefuse("unknown op %r" % op)


def replay(plan):
    """Execute the plan mpmath-side. -> (final_value, k, has_fd).
    Raises ChainRefuse when the chain cannot be replayed."""
    env = {}
    has_fd = False
    order = plan["nodes"]
    for node in order:
        try:
            env[node["id"]] = _exec_node(node, env)
        except (KeyError, ValueError, ZeroDivisionError,
                OverflowError) as exc:
            raise ChainRefuse("node %s: %s" % (node.get("id"), exc))
        if node["op"] == "derivative_at":
            has_fd = True
    fin = plan["final"]
    if fin not in env:
        raise ChainRefuse("final node missing")
    return float(env[fin]), len(order), has_fd


def check_final(plan, claimed):
    """The end-to-end gate: claimed final vs independent replay."""
    want, k, has_fd = replay(plan)
    tol = rel_tol(k, has_fd)
    ok = abs(claimed - want) <= max(tol * abs(want), 1e-9)
    return ok, {"want": want, "claimed": claimed, "k": k, "tol": tol}


# ---------------------------------------------------- positive control
def control_battery():
    sound = [
        # d3: root -> scale -> KE-formula
        ({"nodes": [
            {"id": "n1", "op": "solve_pick",
             "lhs": "x**2 - 5*x + 6", "pick": "larger"},
            {"id": "n2", "op": "scale", "value": "@n1", "by": 4},
            {"id": "n3", "op": "formula",
             "expr": "0.5 * m * v**2", "m": 10, "v": "@n2"}],
          "final": "n3"}, 0.5 * 10 * 144),
        # d4: integral -> convert -> compare branch
        ({"nodes": [
            {"id": "n1", "op": "integrate_def", "expr": "x**2",
             "a": 0, "b": 3},
            {"id": "n2", "op": "scale", "value": "@n1", "by": 1000},
            {"id": "n3", "op": "convert", "value": "@n2",
             "from": "J", "to": "kJ"},
            {"id": "n4", "op": "compare", "a": "@n3", "b": 8.0}],
          "final": "n4"}, 1.0),
        ({"nodes": [
            {"id": "n1", "op": "gcd", "a": 45, "b": 27},
            {"id": "n2", "op": "ncr", "n": 10, "r": 3},
            {"id": "n3", "op": "evaluate",
             "expr": "a + b", "a": "@n1", "b": "@n2"}],
          "final": "n3"}, 129.0),
        ({"nodes": [
            {"id": "n1", "op": "derivative_at", "expr": "x**3",
             "point": 2, "order": 1},
            {"id": "n2", "op": "convert", "value": "@n1",
             "from": "m/s", "to": "km/h"}],
          "final": "n2"}, 12 * 3.6),
    ]
    fails = []
    for plan, gold in sound:
        ok, d = check_final(plan, gold)
        if not ok:
            fails.append(("SOUND FAILED", plan["final"], d))
        okw, d2 = check_final(plan, gold * 1.5 + 7)
        if okw:
            fails.append(("WRONG PASSED", plan["final"], d2))
    # structural refusals must refuse
    try:
        replay({"nodes": [{"id": "n1", "op": "no_such"}],
                "final": "n1"})
        fails.append(("UNKNOWN OP EXECUTED",))
    except ChainRefuse:
        pass
    try:
        replay({"nodes": [{"id": "n1", "op": "solve_pick",
                           "lhs": "sin(x)/x"}], "final": "n1"})
        fails.append(("NON-POLY SOLVED",))
    except ChainRefuse:
        pass
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = control_battery()
    print("chain witness control battery:", "PASS" if ok else "FAIL")
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
