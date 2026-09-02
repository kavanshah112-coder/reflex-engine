# -*- coding: utf-8 -*-
# origin: new for V1.6 -- the symbolic core behind symcore16 leaves (SPEC 5.3)
"""Executes structured scientific tasks deterministically (sympy) and
refuses to certify anything the independent witness cannot confirm.

Contract:
    solve(task) -> (result, certificate) | (None, refusal)

  * task is a STRUCTURED record (op + operands). Text-to-task lives in
    sciparse16; this module never sees natural language.
  * every certified result carries {"witness": {...}} -- the numeric
    cross-check that passed (mpmath, tools/gold_independent, no sympy).
    A result the witness rejects or cannot check is REFUSED (escalate),
    never served. UNKNOWN > WRONG.
  * certificates carry the taxonomy leaf so the gateway can stamp the
    address (SPEC 5.1: a certificate that cannot name its path is a
    SAFETY-1 wrong-fire).

GATE-CTRL (SPEC 9): solve(task, sabotage=True) deliberately corrupts
the symbolic result before the gate. The engine-level control battery
requires 100% of sabotaged results to be REFUSED. B24: instruments and
gates get positive controls before any counting run.
"""
import sys
from pathlib import Path

import sympy as sp

_TOOLS = str(Path(__file__).resolve().parent.parent / "tools")
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
import gold_independent as W  # noqa: E402  (mpmath witness, no sympy)

X = sp.Symbol("x")

_ALLOWED_FUNCS = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                  "exp": sp.exp, "log": sp.log, "sqrt": sp.sqrt,
                  "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
                  "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
                  "pi": sp.pi, "e": sp.E}


def _parse(expr, var="x"):
    """Parse into sympy under the generator grammar only."""
    local = dict(_ALLOWED_FUNCS)
    local[var] = sp.Symbol(var)
    try:
        e = sp.sympify(expr, locals=local, rational=True, evaluate=True)
    except (sp.SympifyError, SyntaxError, TypeError) as exc:
        raise ValueError("unparseable: %s" % exc)
    bad = [str(s) for s in e.free_symbols if str(s) != var]
    if bad:
        raise ValueError("free symbols beyond %s: %s" % (var, bad))
    return e


def _expr_str(e):
    """Render sympy back into the witness grammar."""
    return sp.sstr(e).replace("E", "e") if e is sp.E else sp.sstr(e)


def _window_for(expr, var="x"):
    """A sample window avoiding the expression's obvious singularities.
    log/sqrt push the window positive; denominator roots and tan poles
    inside the window go to `avoid`. If a window cannot be made safe,
    raise -- the task is refused, not guessed."""
    e = _parse(expr, var)
    lo, hi = (-2.0, 2.0)
    s = str(e)
    if "log" in s or "sqrt" in s:
        lo = 0.3
    if "tan" in s or "atan" not in s and "tan(" in s:
        lo, hi = (-1.2, 1.2) if lo < 0 else (0.3, 1.2)
    avoid = []
    den = sp.denom(sp.together(e))
    if den != 1:
        try:
            for r in sp.solve(sp.Eq(den, 0), sp.Symbol(var)):
                if r.is_real:
                    fr = float(r)
                    if lo - 0.5 <= fr <= hi + 0.5:
                        avoid.append(fr)
        except Exception:
            raise ValueError("cannot bound singularities")
    if lo >= hi:
        raise ValueError("no safe window")
    return (lo, hi), avoid


def _refuse(why, **kw):
    d = {"why": why}
    d.update(kw)
    return None, d


def _sabotage_num(v):
    return v + 1 if v not in (None,) else v


class Refused(Exception):
    pass


def _gate(check, **kw):
    """Run a witness check; a failing or erroring witness refuses."""
    try:
        ok, detail = W.CHECKS[check](**kw)
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise Refused("witness cannot check: %s" % exc)
    if not ok:
        raise Refused("witness rejected: %s" % detail)
    return {"check": check, "detail": detail}


def solve(task, sabotage=False):
    """Execute one structured task. Returns (result, certificate) or
    (None, refusal). `sabotage` corrupts the symbolic result pre-gate
    (GATE-CTRL only; never set in a counting run)."""
    op = task.get("op")
    leaf = task.get("leaf")
    if not leaf:
        return _refuse("task carries no taxonomy leaf")
    try:
        if op == "differentiate":
            e = _parse(task["expr"], task.get("var", "x"))
            v = sp.Symbol(task.get("var", "x"))
            order = int(task.get("order", 1))
            if order < 1 or order > 4:
                return _refuse("unsupported order")
            d = sp.diff(e, v, order)
            if sabotage:
                d = d + v
            window, avoid = _window_for(task["expr"], str(v))
            if "at" in task and task["at"] is not None:
                val = d.subs(v, sp.nsimplify(task["at"]))
                val = float(sp.N(val))
                if sabotage:
                    val = _sabotage_num(val)
                wit = _gate("derivative_at", expr=task["expr"],
                            var=str(v), order=order,
                            point=float(task["at"]), claimed=val)
                return val, {"leaf": leaf, "op": op, "witness": wit}
            wit = _gate("derivative", expr=task["expr"], var=str(v),
                        order=order, claimed_expr=_expr_str(d),
                        window=window, avoid=avoid)
            return _expr_str(d), {"leaf": leaf, "op": op, "witness": wit}

        if op == "integrate_def":
            e = _parse(task["expr"], task.get("var", "x"))
            v = sp.Symbol(task.get("var", "x"))
            a, b = float(task["a"]), float(task["b"])
            val = sp.integrate(e, (v, a, b))
            if val.has(sp.Integral):
                return _refuse("no closed evaluation")
            val = float(sp.N(val))
            if sabotage:
                val = _sabotage_num(val)
            wit = _gate("definite_integral", expr=task["expr"],
                        var=str(v), a=a, b=b, claimed=val)
            scale = task.get("scale")
            if scale is not None:
                # chain step: exact scalar on a witness-passed value
                val = float(scale) * val
                wit = dict(wit)
                wit["chain"] = "scaled by %g after witness" % scale
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "integrate_indef":
            e = _parse(task["expr"], task.get("var", "x"))
            v = sp.Symbol(task.get("var", "x"))
            F = sp.integrate(e, v)
            if F.has(sp.Integral):
                return _refuse("no closed antiderivative")
            if sabotage:
                F = F * 2
            window, avoid = _window_for(task["expr"], str(v))
            wit = _gate("antiderivative", expr=task["expr"], var=str(v),
                        claimed_F=_expr_str(F), window=window,
                        avoid=avoid)
            return _expr_str(F) + " + C", {"leaf": leaf, "op": op,
                                           "witness": wit}

        if op == "limit":
            e = _parse(task["expr"], task.get("var", "x"))
            v = sp.Symbol(task.get("var", "x"))
            pt = task["point"]
            target = sp.oo if pt in ("inf", "oo") else sp.nsimplify(pt)
            val = sp.limit(e, v, target)
            if not val.is_finite:
                return _refuse("non-finite limit")
            val = float(sp.N(val))
            if sabotage:
                val = _sabotage_num(val)
            wit = _gate("limit", expr=task["expr"], var=str(v),
                        point=("inf" if pt in ("inf", "oo") else
                               float(pt)), claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op in ("solve_linear", "solve_poly"):
            v = sp.Symbol(task.get("var", "x"))
            L = _parse(task["lhs"], str(v))
            R = _parse(task["rhs"], str(v))
            roots = sp.solve(sp.Eq(L, R), v)
            real = [float(sp.N(r)) for r in roots
                    if getattr(r, "is_real", False)]
            if not real:
                return _refuse("no real roots found")
            if sabotage:
                real = [r + 1 for r in real]
            wit = _gate("solution", lhs="(%s) - (%s)" % (task["lhs"],
                                                         task["rhs"]),
                        rhs="0", var=str(v), roots=sorted(real))
            pick = task.get("pick")
            if pick:
                # chain step: choosing "the larger root" presumes the
                # root set is COMPLETE; membership was witnessed above
                # but completeness only holds when the count matches
                # the degree, so anything but exactly 2 roots refuses.
                if len(real) != 2:
                    return _refuse("pick needs a complete 2-root set")
                r0 = max(real) if pick == "larger" else min(real)
                val = float(task.get("post_mul", 1)) * r0 + \
                    float(task.get("post_add", 0))
                wit = dict(wit)
                wit["chain"] = "%s root -> affine after witness" % pick
                return val, {"leaf": leaf, "op": op, "witness": wit}
            return sorted(real), {"leaf": leaf, "op": op, "witness": wit}

        if op == "evaluate":
            env = {k: float(vv) for k, vv in
                   (task.get("env") or {}).items()}
            local = dict(_ALLOWED_FUNCS)
            for k in env:
                local[k] = sp.Symbol(k)
            e = sp.sympify(task["expr"], locals=local, rational=True)
            extra = [str(s) for s in e.free_symbols if str(s) not in env]
            if extra:
                return _refuse("unbound variables", vars=extra)
            val = float(sp.N(e.subs({sp.Symbol(k): sp.nsimplify(vv)
                                     for k, vv in env.items()})))
            if sabotage:
                val = _sabotage_num(val)
            wit = _gate("value", claimed=val,
                        expected=float(W.evaluate(task["expr"], env)))
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "sum_finite":
            v = sp.Symbol(task.get("var", "n"))
            e = _parse(task["expr"], str(v))
            a, b = int(task["a"]), int(task["b"])
            if b < a or b - a > 100000:
                return _refuse("bad sum range")
            val = float(sp.N(sp.summation(e, (v, a, b))))
            if sabotage:
                val = _sabotage_num(val)
            wit = _gate("finite_sum", expr=task["expr"], var=str(v),
                        a=a, b=b, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op in ("gcd", "lcm"):
            a, b = int(task["a"]), int(task["b"])
            val = int(sp.gcd(a, b)) if op == "gcd" else int(sp.lcm(a, b))
            if sabotage:
                val += 1
            wit = _gate("gcd_lcm", kind=op, a=a, b=b, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "is_prime":
            n = int(task["n"])
            val = bool(sp.isprime(n))
            if sabotage:
                val = not val
            wit = _gate("int_fact", kind="is_prime", n=n, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op in ("ncr", "npr"):
            n, r = int(task["n"]), int(task["r"])
            if r < 0 or r > n or n > 5000:
                return _refuse("bad n,r")
            val = int(sp.binomial(n, r)) if op == "ncr" \
                else int(sp.factorial(n) / sp.factorial(n - r))
            if sabotage:
                val += 1
            wit = _gate("int_fact", kind=op, n=n, r=r, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "probability":
            f, t = float(task["favorable"]), float(task["total"])
            if t <= 0 or f < 0 or f > t:
                return _refuse("bad probability operands")
            val = f / t
            if sabotage:
                val = min(1.0, val + 0.1)
            wit = _gate("value", claimed=val, expected=f / t)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "logic_eval":
            env = {k: bool(v) for k, v in (task.get("env") or {}).items()}
            try:
                want = W._logic_eval(task["expr"], {k.lower(): v
                                                   for k, v in env.items()})
            except (ValueError, AssertionError) as exc:
                return _refuse("unparseable logic: %s" % exc)
            val = bool(want)
            if sabotage:
                val = not val
            wit = _gate("logic", expr=task["expr"], env=env, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "set_op":
            A, B = list(task["A"]), list(task["B"])
            kind = task["kind"]
            want = {"union": set(A) | set(B),
                    "intersection": set(A) & set(B),
                    "difference": set(A) - set(B),
                    "symmetric_difference": set(A) ^ set(B)}.get(kind)
            if want is None:
                return _refuse("unknown set op")
            if task.get("result") == "size":
                val = len(want)
                if sabotage:
                    val += 1
            else:
                val = sorted(want)
                if sabotage:
                    val = val + [999999]
            wit = _gate("set_op", op=kind, A=A, B=B, claimed=val)
            return val, {"leaf": leaf, "op": op, "witness": wit}

        if op == "compare":
            env = {k: float(v) for k, v in (task.get("env") or {}).items()}
            va = float(W.evaluate(task["a_expr"], env))
            vb = float(W.evaluate(task["b_expr"], env))
            val = "a" if va > vb else ("b" if vb > va else "equal")
            if sabotage:
                val = {"a": "b", "b": "a", "equal": "a"}[val]
            # the witness IS the computation here; re-check by value
            wit = _gate("value",
                        claimed={"a": 1.0, "b": -1.0, "equal": 0.0}[val],
                        expected=(1.0 if va > vb else
                                  (-1.0 if vb > va else 0.0)))
            return val, {"leaf": leaf, "op": op, "witness": wit,
                         "a": va, "b": vb}

        return _refuse("unsupported op", op=op)

    except Refused as r:
        return _refuse(str(r))
    except (ValueError, KeyError, TypeError, ZeroDivisionError,
            OverflowError) as exc:
        return _refuse("cannot execute: %s" % exc)


# ------------------------------------------------- engine gate control
CONTROL_TASKS = [
    {"op": "differentiate", "leaf": "mathematics/calculus/differentiation/first_derivative",
     "expr": "x**3*sin(x)", "var": "x", "order": 1},
    {"op": "differentiate", "leaf": "mathematics/calculus/differentiation/second_derivative",
     "expr": "exp(x)*cos(x)", "var": "x", "order": 2},
    {"op": "differentiate", "leaf": "mathematics/calculus/differentiation/evaluate_at_point",
     "expr": "x**2 + 3*x", "var": "x", "order": 1, "at": 2.0},
    {"op": "integrate_def", "leaf": "mathematics/calculus/integration/definite",
     "expr": "x**2", "var": "x", "a": 0, "b": 3},
    {"op": "integrate_indef", "leaf": "mathematics/calculus/integration/indefinite",
     "expr": "cos(x)", "var": "x"},
    {"op": "limit", "leaf": "mathematics/calculus/limits/finite_point",
     "expr": "sin(x)/x", "var": "x", "point": 0},
    {"op": "solve_poly", "leaf": "mathematics/algebra/quadratic_polynomial_solve",
     "lhs": "x**2 - 5*x + 6", "rhs": "0", "var": "x"},
    {"op": "evaluate", "leaf": "mathematics/arithmetic/expression_evaluation",
     "expr": "3*a + b**2", "env": {"a": 2.0, "b": 3.0}},
    {"op": "sum_finite", "leaf": "mathematics/sequences_series/finite_sum",
     "expr": "n**2", "var": "n", "a": 1, "b": 10},
    {"op": "gcd", "leaf": "mathematics/number_theory/gcd_lcm", "a": 45, "b": 27},
    {"op": "is_prime", "leaf": "mathematics/number_theory/divisibility_primes", "n": 97},
    {"op": "ncr", "leaf": "mathematics/combinatorics_probability/permutations_combinations",
     "n": 10, "r": 3},
    {"op": "probability", "leaf": "mathematics/combinatorics_probability/basic_probability",
     "favorable": 3, "total": 8},
    {"op": "logic_eval", "leaf": "logic/propositional_evaluation",
     "expr": "p and not q", "env": {"p": True, "q": False}},
    {"op": "set_op", "leaf": "logic/set_operations", "kind": "intersection",
     "A": [1, 2, 3, 4], "B": [3, 4, 5], "result": "size"},
    {"op": "compare", "leaf": "logic/comparison_ordering",
     "a_expr": "2**10", "b_expr": "10**3", "env": {}},
]


def gate_control():
    """GATE-CTRL: every control task must (a) certify when honest and
    (b) be REFUSED when sabotaged. Returns (ok, failures)."""
    fails = []
    for t in CONTROL_TASKS:
        val, cert = solve(t)
        if val is None:
            fails.append(("HONEST REFUSED", t["op"], cert))
            continue
        if "witness" not in cert or cert.get("leaf") != t["leaf"]:
            fails.append(("CERT MALFORMED", t["op"], cert))
        sval, scert = solve(t, sabotage=True)
        if sval is not None:
            fails.append(("SABOTAGE SERVED", t["op"], sval))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = gate_control()
    print("symcore GATE-CTRL: %s (%d control tasks, honest certify + "
          "sabotage refuse)" % ("PASS" if ok else "FAIL",
                                len(CONTROL_TASKS)))
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
