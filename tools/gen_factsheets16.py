# -*- coding: utf-8 -*-
# origin: new for V1.6 -- fact sheets for bridge authoring (SPEC 6.4)
"""Generates fact-first items: structured facts + gold + witness, and
a neutral BRIEF for a bridge author to phrase. The author sees ONLY
the brief -- never our generator text, grammar, parser, or modules
(V1.4 B9 discipline). Their text is merged back by merge_foreign16.

  python tools/gen_factsheets16.py --n 5400 --out results/v16/data/factsheets.json

Golds are computed here with the independent witness machinery and
verified by their own witness records, exactly as build_q100k does.
Seed 1601 (disjoint stream from the Q-100K generator's 1600).
"""
import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
import gold_independent as W  # noqa: E402

SEED = 1601


def _brief_tierA(facts, ask, unit):
    fs = "; ".join("%s = %s %s" % (n, v, u) if u else "%s = %s"
                   % (n, v) for n, v, u in facts)
    return ("Write ONE natural question, in plain calculator/exam "
            "register (NOT a story; no named people), that gives "
            "these facts and asks for the %s%s. Facts: %s"
            % (ask, " in %s" % unit if unit else "", fs))


def _mk(rng, idx):
    """One fact-first item across the op families."""
    k = rng.random()
    if k < 0.28:
        # tierA-style single formula
        fam = rng.choice([
            ("force", "N", [("mass", "kg", 2, 900, 0),
                            ("acceleration", "m/s^2", 0.5, 12, 1)],
             "m * a", ["m", "a"],
             ["physics/mechanics/dynamics_forces"]),
            ("kinetic energy", "J", [("mass", "kg", 1, 400, 0),
                                     ("speed", "m/s", 1, 50, 1)],
             "0.5 * m * v**2", ["m", "v"],
             ["physics/mechanics/energy_work"]),
            ("current", "A", [("voltage", "V", 3, 240, 0),
                              ("resistance", "ohm", 2, 500, 0)],
             "v / r", ["v", "r"],
             ["physics/electricity/dc_circuits"]),
            ("profit", "$", [("revenue", "$", 1000, 90000, 0),
                             ("total cost", "$", 500, 50000, 0)],
             "a - b", ["a", "b"],
             ["quantitative_finance/profitability"]),
            ("simple interest", "$",
             [("principal", "$", 500, 40000, 0),
              ("annual rate", "%", 1, 12, 1),
              ("time", "years", 1, 10, 0)],
             "p * r * t / 100", ["p", "r", "t"],
             ["quantitative_finance/interest_growth"]),
            ("area", "m^2", [("length", "m", 2, 80, 1),
                             ("width", "m", 1, 50, 1)],
             "l * w", ["l", "w"],
             ["mathematics/geometry_mensuration/area_perimeter"]),
        ])
        out, unit, spec, formula, names, leaves = fam
        facts, env = [], {}
        for (noun, u, lo, hi, nd), var in zip(spec, names):
            v = round(rng.uniform(lo, hi), nd)
            v = int(v) if nd == 0 else v
            facts.append((noun, v, u))
            env[var] = float(v)
        gold = float(W.evaluate(formula, env))
        return {"facts": [list(f) for f in facts], "ask": out,
                "ask_unit": unit,
                "brief": _brief_tierA(facts, out, unit),
                "gold": gold, "gold_type": "num",
                "witness": {"check": "value", "claim_key": "claimed",
                            "expected": gold},
                "leaves": leaves, "depth": 1}
    if k < 0.45:
        # differentiation (expr or at-point)
        c3, c2, c1 = (rng.randint(-6, 6) or 2, rng.randint(-9, 9),
                      rng.randint(-9, 9))
        expr = "%d*x**3 %+d*x**2 %+d*x" % (c3, c2, c1)
        order = rng.choice([1, 1, 2, 2, 3])
        if rng.random() < 0.5:
            at = float(rng.randint(-2, 3))
            gold = float(W._fd(expr, "x", at, order, {}))
            wit = {"check": "derivative_at", "claim_key": "claimed",
                   "expr": expr, "var": "x", "order": order,
                   "point": at}
            ordw = {1: "first", 2: "second", 3: "third"}[order]
            brief = ("Write ONE question in calculator/exam register "
                     "asking for the %s derivative of the function "
                     "%s evaluated at x = %g. Use any natural "
                     "mathematical phrasing (you may write powers "
                     "with ^)." % (ordw, expr.replace("**", "^"), at))
            return {"facts": [["function", expr, ""],
                              ["order", order, ""], ["point", at, ""]],
                    "ask": "%s derivative at point" % ordw,
                    "brief": brief, "gold": gold, "gold_type": "num",
                    "witness": wit,
                    "leaves": ["mathematics/calculus/differentiation/"
                               "evaluate_at_point"], "depth": 2}
        wit = {"check": "derivative", "claim_key": "claimed_expr",
               "expr": expr, "var": "x", "order": order,
               "window": (-1.6, 1.6)}
        ordw = {1: "first", 2: "second", 3: "third"}[order]
        leaf = {1: "first_derivative", 2: "second_derivative",
                3: "higher_order"}[order]
        brief = ("Write ONE question in calculator/exam register "
                 "asking for the %s derivative of %s. Powers may use "
                 "^." % (ordw, expr.replace("**", "^")))
        return {"facts": [["function", expr, ""], ["order", order, ""]],
                "ask": "%s derivative" % ordw, "brief": brief,
                "gold": None, "gold_type": "expr", "witness": wit,
                "leaves": ["mathematics/calculus/differentiation/%s"
                           % leaf], "depth": 1}
    if k < 0.57:
        # definite integral
        c2, c1 = rng.randint(1, 6), rng.randint(-9, 9)
        expr = "%d*x**2 %+d*x" % (c2, c1)
        a, b = sorted(rng.sample(range(0, 6), 2))
        from mpmath import quad
        gold = float(quad(lambda t: W.evaluate(expr, {"x": t}),
                          [a, b]))
        brief = ("Write ONE question in calculator/exam register "
                 "asking for the definite integral of %s from %d to "
                 "%d. Powers may use ^."
                 % (expr.replace("**", "^"), a, b))
        return {"facts": [["integrand", expr, ""], ["from", a, ""],
                          ["to", b, ""]],
                "ask": "definite integral", "brief": brief,
                "gold": gold, "gold_type": "num",
                "witness": {"check": "definite_integral",
                            "claim_key": "claimed", "expr": expr,
                            "var": "x", "a": a, "b": b},
                "leaves": ["mathematics/calculus/integration/definite"],
                "depth": 1}
    if k < 0.68:
        # quadratic solve
        r1, r2 = rng.sample(range(-6, 8), 2)
        bq, cq = -(r1 + r2), r1 * r2
        lhs = ("x**2 %+d*x %+d" % (bq, cq)).replace("+ -", "- ")
        gold = sorted([float(r1), float(r2)])
        brief = ("Write ONE question in calculator/exam register "
                 "asking to solve %s = 0. Powers may use ^."
                 % lhs.replace("**", "^"))
        return {"facts": [["equation", lhs + " = 0", ""]],
                "ask": "roots", "brief": brief, "gold": gold,
                "gold_type": "list",
                "witness": {"check": "solution", "claim_key": "roots",
                            "lhs": lhs, "rhs": "0", "var": "x"},
                "leaves": ["mathematics/algebra/"
                           "quadratic_polynomial_solve"], "depth": 1}
    if k < 0.78:
        # unit conversion
        import pint
        ureg = pint.UnitRegistry()
        src, dst, lo, hi = rng.choice([
            ("km", "m", 0.5, 900), ("kg", "g", 0.05, 80),
            ("m/s", "km/h", 1, 90), ("hour", "minute", 0.25, 30),
            ("J", "kJ", 200, 90000), ("mile", "km", 1, 400)])
        v = round(rng.uniform(lo, hi), 2)
        gold = float((v * ureg(src)).to(dst).magnitude)
        leaf = ("units_conversion/compound_rates" if "/" in src
                else "units_conversion/simple_units")
        brief = ("Write ONE question in calculator/exam register "
                 "asking to convert %s %s into %s." % (v, src, dst))
        return {"facts": [["value", v, src], ["target unit", dst, ""]],
                "ask": "conversion", "brief": brief, "gold": gold,
                "gold_type": "num",
                "witness": {"check": "value", "claim_key": "claimed",
                            "expected": gold},
                "leaves": [leaf], "depth": 1}
    if k < 0.86:
        # number theory / combinatorics
        import math
        if rng.random() < 0.5:
            a, b = rng.randint(12, 400), rng.randint(12, 400)
            op = rng.choice(["gcd", "lcm"])
            gold = float(math.gcd(a, b) if op == "gcd"
                         else abs(a * b) // math.gcd(a, b))
            brief = ("Write ONE question in calculator/exam register "
                     "asking for the %s of %d and %d."
                     % ("greatest common divisor" if op == "gcd"
                        else "least common multiple", a, b))
            return {"facts": [["a", a, ""], ["b", b, ""]], "ask": op,
                    "brief": brief, "gold": gold, "gold_type": "num",
                    "witness": {"check": "gcd_lcm",
                                "claim_key": "claimed", "kind": op,
                                "a": a, "b": b},
                    "leaves": ["mathematics/number_theory/gcd_lcm"],
                    "depth": 1}
        n = rng.randint(6, 30)
        r = rng.randint(2, 5)
        gold = float(math.comb(n, r))
        brief = ("Write ONE question in calculator/exam register "
                 "asking how many ways %d items can be chosen from "
                 "%d." % (r, n))
        return {"facts": [["n", n, ""], ["r", r, ""]],
                "ask": "combinations", "brief": brief, "gold": gold,
                "gold_type": "num",
                "witness": {"check": "int_fact", "claim_key": "claimed",
                            "kind": "ncr", "n": n, "r": r},
                "leaves": ["mathematics/combinatorics_probability/"
                           "permutations_combinations"], "depth": 1}
    if k < 0.93:
        # d2/d3 chain: KE in kJ, or speed conversion after derivative
        if rng.random() < 0.5:
            m, v = rng.randint(2, 400), rng.randint(2, 50)
            gold = 0.5 * m * v * v / 1000.0
            brief = ("Write ONE question in calculator/exam register: "
                     "a mass of %d kg moves at %d m/s; ask for its "
                     "kinetic energy expressed in kilojoules."
                     % (m, v))
            return {"facts": [["mass", m, "kg"], ["speed", v, "m/s"],
                              ["answer unit", "kJ", ""]],
                    "ask": "kinetic energy in kJ", "brief": brief,
                    "gold": gold, "gold_type": "num",
                    "witness": {"check": "value",
                                "claim_key": "claimed",
                                "expected": gold},
                    "leaves": ["physics/mechanics/energy_work",
                               "units_conversion/simple_units"],
                    "depth": 3, "nonmono": True}
        c2, c1 = rng.randint(1, 6), rng.randint(0, 9)
        t0 = float(rng.randint(1, 8))
        gold = float(((2 * c2 * t0 + c1) *
                      __import__("pint").UnitRegistry()("m/s"))
                     .to("km/h").magnitude)
        brief = ("Write ONE question in calculator/exam register: a "
                 "particle's position is s(t) = %dt^2 %+dt metres; "
                 "ask for its speed at t = %g seconds expressed in "
                 "km/h." % (c2, c1, t0))
        return {"facts": [["position law", "%d*t**2 %+d*t"
                           % (c2, c1), "m"], ["time", t0, "s"],
                          ["answer unit", "km/h", ""]],
                "ask": "speed in km/h", "brief": brief, "gold": gold,
                "gold_type": "num",
                "witness": {"check": "value", "claim_key": "claimed",
                            "expected": gold},
                "leaves": ["mathematics/calculus/differentiation/"
                           "evaluate_at_point",
                           "physics/mechanics/kinematics",
                           "units_conversion/compound_rates"],
                "depth": 3, "nonmono": True}
    # logic / sets
    if rng.random() < 0.5:
        A = sorted(rng.sample(range(1, 20), rng.randint(3, 6)))
        B = sorted(rng.sample(range(1, 20), rng.randint(3, 6)))
        kind = rng.choice(["union", "intersection", "difference"])
        want = {"union": set(A) | set(B),
                "intersection": set(A) & set(B),
                "difference": set(A) - set(B)}[kind]
        gold = len(want)
        brief = ("Write ONE question in calculator/exam register "
                 "asking how many elements are in the %s of the sets "
                 "{%s} and {%s}." % (kind, ", ".join(map(str, A)),
                                     ", ".join(map(str, B))))
        return {"facts": [["A", A, ""], ["B", B, ""],
                          ["operation", kind, ""]],
                "ask": "size of %s" % kind, "brief": brief,
                "gold": gold, "gold_type": "num",
                "witness": {"check": "set_op", "claim_key": "claimed",
                            "op": kind, "A": A, "B": B},
                "leaves": ["logic/set_operations"], "depth": 1}
    p, q = rng.random() < 0.5, rng.random() < 0.5
    expr = rng.choice(["p and not q", "not (p or q)", "p or not q"])
    env = {"p": p, "q": q}
    gold = bool(W._logic_eval(expr, env))
    brief = ("Write ONE question in calculator/exam register asking "
             "for the truth value of the expression '%s' when p is "
             "%s and q is %s." % (expr, str(p).lower(),
                                  str(q).lower()))
    return {"facts": [["expression", expr, ""], ["p", p, ""],
                      ["q", q, ""]],
            "ask": "truth value", "brief": brief, "gold": gold,
            "gold_type": "bool",
            "witness": {"check": "logic", "claim_key": "claimed",
                        "expr": expr, "env": env},
            "leaves": ["logic/propositional_evaluation"], "depth": 1}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5400)
    ap.add_argument("--out", default=str(HERE / "results" / "v16" /
                                         "data" / "factsheets.json"))
    a = ap.parse_args()
    rng = random.Random(SEED)
    sheets, rejects = [], 0
    while len(sheets) < a.n:
        try:
            s = _mk(rng, len(sheets))
        except (ValueError, ZeroDivisionError, OverflowError):
            rejects += 1
            continue
        # verify the stored gold against its own witness
        if s["gold_type"] not in ("expr",):
            claim = s["gold"]
            try:
                ok, _ = W.run_check(dict(s["witness"]), claim)
            except (ValueError, KeyError):
                ok = False
            if not ok:
                rejects += 1
                continue
        s["sheet_id"] = "fs16_%05d" % len(sheets)
        s.setdefault("nonmono", False)
        sheets.append(s)
    Path(a.out).write_text(json.dumps(sheets, indent=0),
                           encoding="utf-8")
    print(json.dumps({"sheets": len(sheets), "rejects": rejects,
                      "out": a.out}))


if __name__ == "__main__":
    main()
