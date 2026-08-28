"""Generic symbolic derivation engine (sympy).

The neural part of the derivation node decides WHAT to derive (spec id, or a parsed
equation set); this engine performs the actual symbolic work: eliminate intermediate
variables, solve for the requested symbol, and emit human-readable steps.

Parsing uses an explicit symbol namespace — bare sympify() would interpret
Q (Query), E (e), C, N, I, S, beta, gamma... as sympy builtins.
"""
import re

import sympy as sp

_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_FUNCS = {"sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
          "log": sp.log, "exp": sp.exp, "pi": sp.pi}


def make_ns(*texts):
    """Symbol namespace for all identifiers appearing in the given strings."""
    ns = dict(_FUNCS)
    for t in texts:
        for name in _IDENT.findall(t):
            if name not in ns and name != "Eq":
                ns[name] = sp.Symbol(name, positive=True)
    return ns


def parse_expr(s, ns):
    return sp.sympify(s, locals=ns)


def parse_eq(s, ns):
    """Parse 'lhs = rhs' or 'Eq(lhs, rhs)' into a sympy Eq."""
    s = s.strip()
    if s.startswith("Eq(") and s.endswith(")"):
        inner = s[3:-1]
        # split on the top-level comma
        depth, split_at = 0, None
        for i, ch in enumerate(inner):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "," and depth == 0:
                split_at = i
                break
        lhs, rhs = inner[:split_at], inner[split_at + 1:]
    else:
        lhs, rhs = s.split("=", 1)
    return sp.Eq(parse_expr(lhs, ns), parse_expr(rhs, ns))


class DerivationResult:
    def __init__(self, ok, final_eq=None, steps=None, error=None):
        self.ok = ok
        self.final_eq = final_eq          # sympy Eq
        self.steps = steps or []          # list of human-readable strings
        self.error = error

    def to_dict(self):
        return {"ok": self.ok,
                "final": str(self.final_eq) if self.final_eq is not None else None,
                "steps": self.steps, "error": self.error}


def derive(given_eqs, eliminate, solve_for, ns, positive_root=False):
    """Eliminate `eliminate` symbols from `given_eqs`, then solve for `solve_for`.

    Returns DerivationResult. Purely generic — works for any consistent algebraic
    system sympy can solve; fails honestly otherwise.
    """
    steps = [f"Given: {', '.join(sp.sstr(e) for e in given_eqs)}"]
    try:
        eqs = list(given_eqs)
        for sym_name in eliminate:
            sym = ns[sym_name]
            # find an equation to solve for this symbol
            src = next((e for e in eqs if sym in e.free_symbols), None)
            if src is None:
                return DerivationResult(False,
                                        error=f"cannot eliminate {sym_name}: absent")
            sols = sp.solve(src, sym)
            if not sols:
                return DerivationResult(False,
                                        error=f"cannot solve for {sym_name}")
            sol = sols[-1] if positive_root else sols[0]
            steps.append(f"From {sp.sstr(src)}: {sym_name} = {sp.sstr(sol)}")
            eqs = [sp.Eq(e.lhs.subs(sym, sol), e.rhs.subs(sym, sol)).simplify()
                   if isinstance(e, sp.Eq) else e
                   for e in eqs if e is not src]
            eqs = [e for e in eqs if e is not sp.true]
            steps.append("Substitute into the remaining equations: "
                         + ", ".join(sp.sstr(e) for e in eqs))
        target_sym = ns[solve_for]
        combined = [e for e in eqs if target_sym in e.free_symbols]
        if not combined:
            return DerivationResult(False, error=f"no equation contains {solve_for}")
        sols = sp.solve(combined, target_sym, dict=True)
        if not sols:
            return DerivationResult(False, error=f"cannot solve for {solve_for}")
        expr = sols[-1][target_sym] if positive_root else sols[0][target_sym]
        expr = sp.simplify(expr)
        final = sp.Eq(target_sym, expr)
        steps.append(f"Solve for {solve_for}: {sp.sstr(final)}")
        return DerivationResult(True, final_eq=final, steps=steps)
    except Exception as e:  # honest failure, not a crash
        return DerivationResult(False, error=f"{type(e).__name__}: {e}")


def relations_equivalent(eq_a, eq_b):
    """True if two relations are algebraically equivalent (up to rearrangement/scale)."""
    try:
        da = sp.simplify(eq_a.lhs - eq_a.rhs)
        db = sp.simplify(eq_b.lhs - eq_b.rhs)
        if da == 0 or db == 0:
            return bool(da == 0 and db == 0)
        if sp.simplify(da - db) == 0 or sp.simplify(da + db) == 0:
            return True
        ratio = sp.simplify(da / db)
        return ratio.is_constant() is True and ratio != 0
    except Exception:
        return False


def verify_against_target(final_eq, target_str, ns):
    target = parse_eq(target_str, ns)
    if relations_equivalent(final_eq, target):
        return True
    # also accept solved-for-lhs equivalence (e.g. v = sqrt(...) vs v**2 = ...)
    try:
        lhs_sym = (final_eq.lhs if final_eq.lhs.is_Symbol else
                   target.lhs if target.lhs.is_Symbol else None)
        if lhs_sym is not None:
            sa = sp.solve(final_eq, lhs_sym)
            sb = sp.solve(target, lhs_sym)
            for a in sa:
                for b in sb:
                    if sp.simplify(a - b) == 0:
                        return True
    except Exception:
        pass
    return False
