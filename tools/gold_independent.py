# -*- coding: utf-8 -*-
# origin: new for V1.6 -- the independent numeric witness (SPEC 5.3, 6.4)
"""Numeric verification with NO sympy import, ever.

Two consumers, one contract:
  * dataset build: every stored gold is verified here before an item
    is admitted to Q-100K / S-SCI (golds are not the engine grading
    itself);
  * the engine gate: symcore16 submits every symbolic result here
    before certification (a result failing the witness is ESCALATED,
    never served).

The circularity this breaks: symcore16 is sympy-backed and the gold
constructor is sympy-backed, so a shared sympy bug could certify a
wrong answer against a wrong gold and call both right. This module's
only expression machinery is a ~40-line recursive-descent evaluator
over mpmath -- a different codebase, a different algorithm (finite
differences and quadrature instead of symbolic rules).

Expressions come from our own generator grammar:
  numbers, x (or declared vars), + - * / ** ( ),
  sin cos tan exp log sqrt asin acos atan sinh cosh tanh, pi, e
Anything else is a ValueError -- the witness refuses rather than
guesses (UNKNOWN > WRONG applies to instruments too).

Every check returns (ok: bool, detail: dict). Tolerances are relative
(1e-6 default) with an absolute floor for near-zero values.

POSITIVE CONTROL (B24): control_battery() feeds deliberately wrong
claims to every check and MUST see every one fail. Run it before any
counting run; a passing wrong claim voids the instrument.
"""
import math
import random

from mpmath import mp, mpf, quad, sin, cos, tan, exp, log, sqrt, \
    asin, acos, atan, sinh, cosh, tanh, pi, e, isnan, isinf

mp.dps = 30

_FUNCS = {"sin": sin, "cos": cos, "tan": tan, "exp": exp, "log": log,
          "sqrt": sqrt, "asin": asin, "acos": acos, "atan": atan,
          "sinh": sinh, "cosh": cosh, "tanh": tanh}
_CONSTS = {"pi": pi, "e": e}

REL_TOL = mpf("1e-6")
ABS_FLOOR = mpf("1e-9")


# ------------------------------------------------------------ tokenizer
def _tokens(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c.isdigit() or c == ".":
            j = i
            while j < n and (s[j].isdigit() or s[j] == "."):
                j += 1
            out.append(("num", s[i:j])); i = j
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (s[j].isalnum() or s[j] == "_"):
                j += 1
            out.append(("name", s[i:j])); i = j
        elif s.startswith("**", i):
            out.append(("op", "**")); i += 2
        elif c in "+-*/(),":
            out.append(("op", c)); i += 1
        elif c == "^":
            out.append(("op", "**")); i += 1
        else:
            raise ValueError("bad char %r in %r" % (c, s))
    out.append(("end", ""))
    return out


class _P(object):
    """number | name | name(expr) | (expr) with + - * / ** and unary -"""

    def __init__(self, s, env):
        self.t = _tokens(s)
        self.i = 0
        self.env = env

    def peek(self):
        return self.t[self.i]

    def eat(self, val=None):
        k, v = self.t[self.i]
        if val is not None and v != val:
            raise ValueError("expected %r got %r" % (val, v))
        self.i += 1
        return k, v

    def expr(self):
        v = self.term()
        while self.peek()[1] in ("+", "-"):
            _, op = self.eat()
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.factor()
        while self.peek()[1] in ("*", "/"):
            _, op = self.eat()
            r = self.factor()
            v = v * r if op == "*" else v / r
        return v

    def factor(self):
        if self.peek()[1] == "-":
            self.eat()
            return -self.factor()
        if self.peek()[1] == "+":
            self.eat()
            return self.factor()
        return self.power()

    def power(self):
        b = self.atom()
        if self.peek()[1] == "**":
            self.eat()
            return b ** self.factor()      # right-assoc, unary binds
        return b

    def atom(self):
        k, v = self.eat()
        if k == "num":
            return mpf(v)
        if k == "name":
            if self.peek()[1] == "(":
                if v not in _FUNCS:
                    raise ValueError("unknown function %r" % v)
                self.eat("(")
                arg = self.expr()
                self.eat(")")
                return _FUNCS[v](arg)
            if v in _CONSTS:
                return _CONSTS[v]
            if v in self.env:
                return mpf(self.env[v])
            raise ValueError("unknown name %r" % v)
        if v == "(":
            inner = self.expr()
            self.eat(")")
            return inner
        raise ValueError("unexpected token %r" % v)


def evaluate(expr, env=None):
    """Evaluate expr at env (dict of var -> number). Raises on refuse."""
    p = _P(expr, dict(env or {}))
    v = p.expr()
    if p.peek()[0] != "end":
        raise ValueError("trailing input in %r" % expr)
    if isnan(v) or isinf(v):
        raise ValueError("non-finite value")
    return v


def _close(a, b, rel=REL_TOL):
    a, b = mpf(a), mpf(b)
    if abs(b) < ABS_FLOOR:
        return abs(a - b) < mpf("1e-6")
    return abs(a - b) / abs(b) <= rel


def _samples(window, avoid, k, seed):
    rng = random.Random(seed)
    lo, hi = window
    pts, tries = [], 0
    while len(pts) < k and tries < 500:
        tries += 1
        x = lo + (hi - lo) * rng.random()
        if all(abs(x - a) > 0.05 for a in avoid):
            pts.append(x)
    if len(pts) < k:
        raise ValueError("cannot sample window %r" % (window,))
    return pts


# ------------------------------------------------------------- checks
def check_value(claimed, expected, rel=1e-6):
    ok = _close(claimed, expected, mpf(str(rel)))
    return ok, {"claimed": float(claimed), "expected": float(expected)}


def _fd(expr, var, x, order, env, h=mpf("1e-5")):
    """Central finite difference of `expr` in `var` at x, given order."""
    def f(t):
        d = dict(env); d[var] = t
        return evaluate(expr, d)
    x = mpf(x)
    if order == 0:
        return f(x)
    if order == 1:
        return (f(x + h) - f(x - h)) / (2 * h)
    if order == 2:
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)
    # higher order: recurse on first derivative numerically (wider h to
    # keep noise bounded at dps=30 this is safe to order 4)
    hh = h * 10
    return (_fd(expr, var, x + hh, order - 1, env, h)
            - _fd(expr, var, x - hh, order - 1, env, h)) / (2 * hh)


def check_derivative(expr, var, order, claimed_expr, window,
                     avoid=(), k=7, seed=160001, rel=1e-3):
    """claimed_expr(x_i) must match the order-th finite difference of
    expr at k sample points. rel is looser than value checks because
    finite differences carry O(h^2) noise."""
    pts = _samples(window, list(avoid), k, seed)
    for x in pts:
        want = _fd(expr, var, x, order, {})
        got = evaluate(claimed_expr, {var: x})
        if not _close(got, want, mpf(str(rel))):
            return False, {"at": float(x), "want": float(want),
                           "got": float(got)}
    return True, {"points": [float(p) for p in pts]}


def check_antiderivative(expr, var, claimed_F, window,
                         avoid=(), k=7, seed=160002, rel=1e-3):
    """d/dx claimed_F must equal expr at samples (constant drops out)."""
    return check_derivative(claimed_F, var, 1, expr, window,
                            avoid, k, seed, rel)


def check_definite_integral(expr, var, a, b, claimed, rel=1e-6):
    def f(t):
        return evaluate(expr, {var: t})
    want = quad(f, [mpf(a), mpf(b)])
    ok = _close(claimed, want, mpf(str(rel)))
    return ok, {"claimed": float(claimed), "quad": float(want)}


def check_solution(lhs, rhs, var, roots, env=None, rel=1e-6):
    """Every claimed root substituted into lhs == rhs must hold."""
    if not roots:
        return False, {"why": "no roots claimed"}
    for r in roots:
        d = dict(env or {}); d[var] = r
        L, R = evaluate(lhs, d), evaluate(rhs, d)
        if abs(R) < ABS_FLOOR:
            if abs(L) > mpf("1e-6"):
                return False, {"root": float(r), "lhs": float(L)}
        elif not _close(L, R, mpf(str(rel))):
            return False, {"root": float(r), "lhs": float(L),
                           "rhs": float(R)}
    return True, {"roots": [float(r) for r in roots]}


def check_limit(expr, var, point, claimed, side="both", rel=1e-4):
    """Numeric approach: f at point +/- 10^-k must trend to claimed."""
    seqs = []
    if side in ("both", "left"):
        seqs.append([mpf(point) - mpf(10) ** -j for j in (4, 5, 6)])
    if side in ("both", "right"):
        seqs.append([mpf(point) + mpf(10) ** -j for j in (4, 5, 6)])
    if str(point) in ("inf", "oo"):
        seqs = [[mpf(10) ** j for j in (4, 5, 6)]]
    for seq in seqs:
        vals = [evaluate(expr, {var: x}) for x in seq]
        if not _close(vals[-1], claimed, mpf(str(rel))):
            return False, {"approach": float(seq[-1]),
                           "value": float(vals[-1]),
                           "claimed": float(claimed)}
    return True, {"claimed": float(claimed)}


def check_gcd_lcm(kind, a, b, claimed):
    want = math.gcd(int(a), int(b)) if kind == "gcd" \
        else abs(int(a) * int(b)) // math.gcd(int(a), int(b))
    return int(claimed) == want, {"want": want, "claimed": int(claimed)}


def check_derivative_at(expr, var, order, point, claimed, rel=1e-3):
    """claimed must match the order-th finite difference at one point."""
    want = _fd(expr, var, point, order, {})
    ok = _close(claimed, want, mpf(str(rel)))
    return ok, {"want": float(want), "claimed": float(claimed)}


def check_finite_sum(expr, var, a, b, claimed, rel=1e-6):
    """Iterative summation over integers a..b, no closed form used."""
    a, b = int(a), int(b)
    if b - a > 100000:
        raise ValueError("sum range too large for witness")
    total = mpf(0)
    for n in range(a, b + 1):
        total += evaluate(expr, {var: n})
    ok = _close(claimed, total, mpf(str(rel)))
    return ok, {"want": float(total), "claimed": float(claimed)}


def check_int_fact(kind, n, r=None, claimed=None):
    """Integer facts by direct iteration: is_prime (trial division),
    nCr / nPr (multiplicative loops), factorial."""
    n = int(n)
    if kind == "is_prime":
        if n < 2:
            want = False
        else:
            want = all(n % d for d in range(2, int(math.isqrt(n)) + 1))
        return bool(claimed) == want, {"want": want}
    r = int(r)
    if kind == "npr":
        want = 1
        for i in range(n, n - r, -1):
            want *= i
    elif kind == "ncr":
        want = 1
        for i in range(1, r + 1):
            want = want * (n - r + i) // i
    else:
        raise ValueError("unknown int fact %r" % kind)
    return int(claimed) == want, {"want": want, "claimed": int(claimed)}


def _logic_eval(s, env):
    """Independent propositional evaluator: and/or/not/parens/vars.
    Recursive descent, lowest precedence first (or < and < not)."""
    toks = []
    for raw in s.replace("(", " ( ").replace(")", " ) ").split():
        toks.append(raw.lower())
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def eat():
        t = toks[pos[0]]; pos[0] += 1; return t

    def p_or():
        v = p_and()
        while peek() == "or":
            eat(); v = p_and() or v
        return v

    def p_and():
        v = p_not()
        while peek() == "and":
            eat()
            r = p_not()
            v = v and r
        return v

    def p_not():
        if peek() == "not":
            eat(); return not p_not()
        return p_atom()

    def p_atom():
        t = eat()
        if t == "(":
            v = p_or()
            assert eat() == ")"
            return v
        if t in ("true", "1"):
            return True
        if t in ("false", "0"):
            return False
        if t in env:
            return bool(env[t])
        raise ValueError("unknown prop %r" % t)

    v = p_or()
    if peek() is not None:
        raise ValueError("trailing logic input")
    return v


def check_logic(expr, env, claimed):
    want = _logic_eval(expr, {k.lower(): v for k, v in env.items()})
    return bool(claimed) == want, {"want": want, "claimed": bool(claimed)}


def check_set_op(op, A, B, claimed):
    """Set results by plain python sets; claimed is a sorted list or a
    size, matched against rec['result_type'] implicitly by type."""
    A, B = set(A), set(B)
    want = {"union": A | B, "intersection": A & B,
            "difference": A - B, "symmetric_difference": A ^ B}[op]
    if isinstance(claimed, (int, float)) and not isinstance(claimed, bool):
        return int(claimed) == len(want), {"want_size": len(want)}
    return sorted(claimed) == sorted(want), {"want": sorted(want)}


CHECKS = {
    "value": check_value,
    "derivative": check_derivative,
    "derivative_at": check_derivative_at,
    "antiderivative": check_antiderivative,
    "definite_integral": check_definite_integral,
    "solution": check_solution,
    "limit": check_limit,
    "gcd_lcm": check_gcd_lcm,
    "finite_sum": check_finite_sum,
    "int_fact": check_int_fact,
    "logic": check_logic,
    "set_op": check_set_op,
}


def run_check(rec, claimed):
    """Dispatch a stored witness record against a claimed answer.
    rec: {"check": <name>, ...kwargs}; claimed replaces the record's
    claim slot named by rec["claim_key"]."""
    rec = dict(rec)
    name = rec.pop("check")
    key = rec.pop("claim_key")
    rec[key] = claimed
    return CHECKS[name](**rec)


# ---------------------------------------------------- positive control
def control_battery():
    """Deliberately wrong claims. EVERY entry must FAIL its check.
    Returns (ok, failures) where ok means the instrument is alive."""
    wrong = [
        ("value", dict(claimed=2.0, expected=3.0)),
        ("value", dict(claimed=100.0001, expected=100.0, rel=1e-9)),
        ("derivative", dict(expr="x**3", var="x", order=1,
                            claimed_expr="3*x", window=(0.5, 2.0))),
        ("derivative", dict(expr="sin(x)", var="x", order=2,
                            claimed_expr="sin(x)", window=(0.2, 1.4))),
        ("antiderivative", dict(expr="cos(x)", var="x",
                                claimed_F="cos(x)", window=(0.2, 1.4))),
        ("definite_integral", dict(expr="x**2", var="x", a=0, b=3,
                                   claimed=8.0)),
        ("solution", dict(lhs="x**2 - 5*x + 6", rhs="0", var="x",
                          roots=[2, 4])),
        ("limit", dict(expr="sin(x)/x", var="x", point=0, claimed=0.5)),
        ("gcd_lcm", dict(kind="gcd", a=45, b=27, claimed=3)),
        ("derivative_at", dict(expr="x**2", var="x", order=1, point=3,
                               claimed=5.0)),
        ("finite_sum", dict(expr="n", var="n", a=1, b=100,
                            claimed=5049.0)),
        ("int_fact", dict(kind="is_prime", n=91, claimed=True)),
        ("int_fact", dict(kind="ncr", n=10, r=3, claimed=110)),
        ("logic", dict(expr="p and not q", env={"p": True, "q": False},
                       claimed=False)),
        ("set_op", dict(op="intersection", A=[1, 2, 3], B=[2, 3, 4],
                        claimed=[1, 2, 3])),
    ]
    right = [
        ("value", dict(claimed=3.0, expected=3.0)),
        ("derivative", dict(expr="x**3", var="x", order=1,
                            claimed_expr="3*x**2", window=(0.5, 2.0))),
        ("derivative", dict(expr="sin(x)", var="x", order=2,
                            claimed_expr="-sin(x)", window=(0.2, 1.4))),
        ("antiderivative", dict(expr="cos(x)", var="x",
                                claimed_F="sin(x)", window=(0.2, 1.4))),
        ("definite_integral", dict(expr="x**2", var="x", a=0, b=3,
                                   claimed=9.0)),
        ("solution", dict(lhs="x**2 - 5*x + 6", rhs="0", var="x",
                          roots=[2, 3])),
        ("limit", dict(expr="sin(x)/x", var="x", point=0, claimed=1.0)),
        ("gcd_lcm", dict(kind="gcd", a=45, b=27, claimed=9)),
        ("derivative_at", dict(expr="x**2", var="x", order=1, point=3,
                               claimed=6.0)),
        ("finite_sum", dict(expr="n", var="n", a=1, b=100,
                            claimed=5050.0)),
        ("int_fact", dict(kind="is_prime", n=97, claimed=True)),
        ("int_fact", dict(kind="ncr", n=10, r=3, claimed=120)),
        ("logic", dict(expr="p and not q", env={"p": True, "q": False},
                       claimed=True)),
        ("set_op", dict(op="intersection", A=[1, 2, 3], B=[2, 3, 4],
                        claimed=[2, 3])),
    ]
    fails = []
    for name, kw in wrong:
        ok, d = CHECKS[name](**kw)
        if ok:
            fails.append(("WRONG-CLAIM PASSED", name, kw, d))
    for name, kw in right:
        ok, d = CHECKS[name](**kw)
        if not ok:
            fails.append(("RIGHT-CLAIM FAILED", name, kw, d))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = control_battery()
    print("witness control battery:", "PASS" if ok else "FAIL")
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
