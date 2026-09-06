# -*- coding: utf-8 -*-
# origin: new for V1.8 -- G-P4' usage accounting over plangate17 (SPEC 4)
"""check(plan, question) -> (ok, transcript)

Runs plangate17.check UNCHANGED (G-P1..G-P4; V1.7 reproduces byte-
exact by calling plangate17 directly), then G-P4':

  every stated number, as a role-tagged TOKEN (roles18), must be
  consumed by exactly one literal occurrence of the plan whose slot
  role is compatible with the token's cue; and every non-structural
  literal occurrence must consume a token. A perfect matching between
  tokens and required literals -- or the plan dies.

This is what magnitude presence (G-P4) cannot see: '... over 6 years.
Multiply that by 6' states 6 twice in two roles; a plan that binds
t=6 and drops the factor has 6 'present' and passes G-P4, and served
13 certified-wrong sealed answers in V1.7 (haiku-13). Here the two
tokens need two literals, and the plan has one.

Literal classes:
  roled slot      (op,key) in roles18.SLOT_ROLE   -> REQUIRED, role R
  structural slot (op,key) in STRUCTURAL_SLOTS    -> ignored
  unknown slot    numeric, not in either table     -> UNROLLED: kill
  expr operand    number inside expr/lhs/rhs of an EXPR op, exponents
                  excluded                          -> REQUIRED, 'EXPR'
  formula expr    numbers inside a formula's expr   -> ignored
                  (physics constants: 0.5, 9.8, 100 ...)
  implicit rhs    solve_pick without rhs            -> OPTIONAL 0, 'rhs'
"""
from . import plangate17
from . import roles18 as R


def _literals(plan):
    """[(node_id, where, value, role, required)]"""
    out = []
    for n in plan.get("nodes", []):
        op = n.get("op")
        for k, v in n.items():
            if k in R.NON_SLOT_KEYS:
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            role = R.slot_role(op, k)
            if role == "STRUCTURAL":
                continue
            if role is None:
                out.append((n.get("id"), k, float(v), "UNROLLED", True))
                continue
            out.append((n.get("id"), k, float(v), role, True))
        if op in R.EXPR_OPS:
            for k in R.EXPR_KEYS:
                v = n.get(k)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    if k == "rhs":
                        out.append((n.get("id"), k, float(v), "rhs", True))
                    continue
                if isinstance(v, str):
                    for _s, _e, mag in R.expr_numbers(v):
                        out.append((n.get("id"), k, float(mag), "EXPR",
                                    True))
            if op == "solve_pick" and "rhs" not in n:
                out.append((n.get("id"), "rhs", 0.0, "rhs", False))
        elif op == "compare" and isinstance(n.get("b"), str) and \
                not n["b"].startswith("@"):
            for _s, _e, mag in R.expr_numbers(n["b"]):
                out.append((n.get("id"), "b", float(mag), "threshold",
                            True))
    return out


def _match(tokens, lits):
    """Maximum bipartite matching tokens -> literal occurrences.
    Returns (assignment dict token_idx -> lit_idx)."""
    adj = []
    for t in tokens:
        row = []
        for j, (_n, _k, val, role, _req) in enumerate(lits):
            if role == "UNROLLED":
                continue
            if abs(abs(val) - t.value) < 1e-9 and \
                    R.compatible(t.cue, role):
                row.append(j)
        adj.append(row)
    match_l = {}

    def try_t(i, seen):
        for j in adj[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in match_l or try_t(match_l[j], seen):
                match_l[j] = i
                return True
        return False
    for i in range(len(tokens)):
        try_t(i, set())
    return {i: j for j, i in match_l.items()}


def usage_check(plan, question, roles=None):
    """G-P4' alone. -> (ok, why, info)"""
    roles = roles or R.analyze(question)
    lits = _literals(plan)
    for _n, k, v, role, _r in lits:
        if role == "UNROLLED":
            return False, "G-P4': unrolled numeric slot %s=%g" % (k, v), {}
    toks = roles.unique
    asg = _match(toks, lits)
    info = {"tokens": len(toks), "bare": len(roles.bare()),
            "literals": len(lits)}
    for i, t in enumerate(toks):
        if i not in asg:
            return False, ("G-P4': stated %s (%s, clause %d) has no "
                           "literal in its role" % (t.raw, t.cue, t.step)
                           ), info
    used = set(asg.values())
    for j, (nid, k, v, role, req) in enumerate(lits):
        if req and j not in used:
            return False, ("G-P4': literal %g in %s.%s consumes no "
                           "stated number of role %s" % (v, nid, k, role)
                           ), info
    return True, None, info


# ---------------------------------------------------------------------
# G-P5 -- certified formulas (SPEC AMENDMENT A1, 2026-09-06; B33)
# A formula node's expr is producer-supplied PHYSICS, and V1.7 let it
# be free-form: 12 of haiku's 13 certified-wrong sealed plans wrote
# 'p * r * t / 100 + p' (the amount) for 'simple interest'. Every
# number was consumed, the witness verified the plan's own algebra,
# and nothing in the gate knew what simple interest IS. The composer
# does (composer17.FORM); this gate makes that table binding: a
# formula expr must be algebraically equivalent to a certified formula
# whose KIND the question names, symbol for symbol.
CERTIFIED_FORMULAS = {
    "kinetic energy": ("0.5 * m * v**2", "J"),
    "potential energy": ("m * 9.8 * h", "J"),
    "force": ("m * a", "N"),
    "work": ("f * d", "J"),
    "power": ("v * i", "W"),
    "current": ("v / r", "A"),
    "simple interest": ("p * r * t / 100", "$"),
}
_FORMULA_CACHE = {}


def _equiv(expr, canon):
    key = (expr, canon)
    if key in _FORMULA_CACHE:
        return _FORMULA_CACHE[key]
    try:
        import sympy
        from sympy.parsing.sympy_parser import parse_expr
        a = parse_expr(expr.replace("^", "**"))
        b = parse_expr(canon)
        ok = sympy.simplify(a - b) == 0
    except Exception:            # noqa: BLE001  (unparseable = not certified)
        ok = False
    _FORMULA_CACHE[key] = ok
    return ok


def formula_check(plan, question):
    """-> (ok, why). Each formula node must match a certified kind the
    question names; kinds named fewer times than used are a kill."""
    ql = question.lower()
    used = {}
    for n in plan.get("nodes", []):
        if n.get("op") != "formula":
            continue
        expr = n.get("expr") or ""
        kind = None
        for k, (canon, _u) in CERTIFIED_FORMULAS.items():
            if _equiv(expr, canon):
                kind = k
                break
        if kind is None:
            return False, ("G-P5: formula %r is not a certified "
                           "formula" % expr)
        used[kind] = used.get(kind, 0) + 1
    for kind, cnt in used.items():
        named = ql.count(kind)
        if named < cnt:
            return False, ("G-P5: %d %s formula node(s) but the question "
                           "names it %d time(s)" % (cnt, kind, named))
    return True, None


def check(plan, question, roles=None):
    ok, t = plangate17.check(plan, question)
    if not ok:
        return ok, t
    t = [x for x in t if x.get("gate") != "ALL"]
    ok2, why, info = usage_check(plan, question, roles)
    if not ok2:
        t.append({"gate": "G-P4'", "kill": why})
        return False, t
    t.append({"gate": "G-P4'", "pass": True, **info})
    ok5, why5 = formula_check(plan, question)
    if not ok5:
        t.append({"gate": "G-P5", "kill": why5})
        return False, t
    t.append({"gate": "G-P5", "pass": True})
    t.append({"gate": "ALL", "pass": True})
    return True, t


# ---------------------------------------------------- positive controls
def control_battery():
    """V1.7's battery must still hold through this gate; plus the
    dual-role, order and benign-repeat classes (SPEC 4.5)."""
    fails = []
    ok17, f17 = plangate17.control_battery()
    if not ok17:
        fails.append(("V1.7 BATTERY", f17))
    q_dual = ("Compute 12 choose 2. Using that as a principal in "
              "dollars, find the simple interest at 5% per year over "
              "6 years. Multiply that by 6, in $.")
    sound = {"nodes": [
        {"id": "n1", "op": "ncr", "n": 12, "r": 2},
        {"id": "n2", "op": "formula", "expr": "p * r * t / 100",
         "p": "@n1", "r": 5, "t": 6, "unit": "$"},
        {"id": "n3", "op": "scale", "value": "@n2", "by": 6,
         "unit": "$"}], "final": "n3"}
    dropped = {"nodes": sound["nodes"][:2], "final": "n2"}
    swapped = {"nodes": [
        {"id": "n1", "op": "ncr", "n": 12, "r": 2},
        {"id": "n2", "op": "formula", "expr": "p * r * t / 100",
         "p": "@n1", "r": 6, "t": 5, "unit": "$"},
        {"id": "n3", "op": "scale", "value": "@n2", "by": 6,
         "unit": "$"}], "final": "n3"}
    # R4: a re-mention beside the same unit within ONE clause counts
    # once; across clauses it is a second stated quantity (frozen rule)
    q_rep = ("A 40 kg crate -- yes, 40 kg -- moving at 3 m/s, find its "
             "kinetic energy.")
    q_rep_plan = {"nodes": [
        {"id": "n1", "op": "formula", "expr": "0.5 * m * v**2",
         "m": 40, "v": 3, "unit": "J"}], "final": "n1"}
    q_order = "Compute the lcm of 45 and 27. Subtract 7 from that."
    order_ok = {"nodes": [
        {"id": "n1", "op": "lcm", "a": 45, "b": 27},
        {"id": "n2", "op": "evaluate", "expr": "@n1 - 7"}], "final": "n2"}
    q_coef = ("Compute 2(6 + 3). Using that as a principal in dollars, "
              "find the simple interest at 2% per year over 6 years.")
    coef_sound = {"nodes": [
        {"id": "n1", "op": "evaluate", "expr": "2*(6 + 3)"},
        {"id": "n2", "op": "formula", "expr": "p * r * t / 100",
         "p": "@n1", "r": 2, "t": 6, "unit": "$"}], "final": "n2"}
    coef_smuggle = {"nodes": [
        {"id": "n1", "op": "evaluate", "expr": "2*(6 + 3)"},
        {"id": "n2", "op": "formula", "expr": "p * 2 * t / 100",
         "p": "@n1", "t": 6, "unit": "$"}], "final": "n2"}
    # B33 classes: the amount-for-interest formula (12 of haiku-13) and
    # the pre-differentiated expression (the 13th)
    amount = {"nodes": [
        {"id": "n1", "op": "ncr", "n": 12, "r": 2},
        {"id": "n2", "op": "formula", "expr": "p * r * t / 100 + p",
         "p": "@n1", "r": 5, "t": 6, "unit": "$"},
        {"id": "n3", "op": "scale", "value": "@n2", "by": 6,
         "unit": "$"}], "final": "n3"}
    q_pre = ("Compute the first derivative of 1x^3 -1x^2 at x = 1. "
             "Using that as the speed in m/s of a 31 kg mass, find the "
             "kinetic energy. Express the result in kJ from J, in kJ.")
    pre_diff = {"nodes": [
        {"id": "n1", "op": "derivative_at", "expr": "3*x**2 - 2*x",
         "point": 1, "order": 1},
        {"id": "n2", "op": "formula", "expr": "0.5 * m * v**2", "m": 31,
         "v": "@n1", "unit": "J"},
        {"id": "n3", "op": "convert", "value": "@n2", "from": "J",
         "to": "kJ"}], "final": "n3"}
    pre_sound = {"nodes": [
        {"id": "n1", "op": "derivative_at", "expr": "1*x**3 - 1*x**2",
         "point": 1, "order": 1},
        {"id": "n2", "op": "formula", "expr": "0.5 * m * v**2", "m": 31,
         "v": "@n1", "unit": "J"},
        {"id": "n3", "op": "convert", "value": "@n2", "from": "J",
         "to": "kJ"}], "final": "n3"}
    cases = [
        ("sound dual-role plan", sound, q_dual, True),
        ("amount for interest (B33, 12 of haiku-13)", amount, q_dual,
         False),
        ("pre-differentiated expression (B33, the 13th)", pre_diff,
         q_pre, False),
        ("derivative plan sound", pre_sound, q_pre, True),
        ("dropped dual-role usage (haiku-13 class)", dropped, q_dual,
         False),
        ("rate/years swapped (B32 role misbinding)", swapped, q_dual,
         False),
        ("benign repeat counts once", q_rep_plan, q_rep, True),
        ("sound subtraction", order_ok, q_order, True),
        ("coefficient plan sound", coef_sound, q_coef, True),
        ("rate hard-coded in formula expr (whitelist smuggle)",
         coef_smuggle, q_coef, False),
    ]
    for name, plan, q, want in cases:
        ok, t = check(plan, q)
        if ok != want:
            fails.append(("PASSED" if ok else "KILLED", name, t[-1]))
    return (not fails), fails


if __name__ == "__main__":
    ok, fails = control_battery()
    print("G-P4' control battery:", "PASS" if ok else "FAIL")
    for f in fails:
        print(" ", f)
    raise SystemExit(0 if ok else 1)
