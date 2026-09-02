# -*- coding: utf-8 -*-
# origin: new for V1.6 -- the Q-100K workload builder (SPEC 6.1-6.3)
"""Builds the 100,000-query workload: programmatic in-domain items
across every taxonomy leaf, depth-laddered chains, narrative
distractors, and fact-committed slots for the bridge's foreign
phrasings.

Provenance rules (SPEC 6.4):
  * NO engine code is imported. Golds are computed HERE, with
    tools/gold_independent (the mpmath witness) as the evaluator, and
    every computed gold is verified by its own witness record before
    the item is admitted. Formula IDENTITY is shared with the pack
    (F = m*a is F = m*a); formula CODE is not.
  * Distractors come from GSM8K/ASDiv. Their golds are carried for
    the record but the only claim ever made on them is ESCALATION
    (SPEC 6). Distractor ids are DISJOINT across splits so no
    memorization path can leak acquisition text into SEAL.
  * Foreign slots: facts + gold fixed here; the text arrives later
    from bridge authors who see ONLY the fact sheet (merge_foreign16).

Determinism: seed 1600. Running twice produces identical output.

  python tools/build_q100k.py --out results/v16/data [--n 100000]
"""
import argparse
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "tools"))
import gold_independent as W  # noqa: E402

SEED = 1600

# ---------------------------------------------------------------------
# Tier A capability templates: phrasings driven by kinds.json nouns and
# units, golds by the cap's formula evaluated with the witness
# evaluator. Value ranges keep every formula well-conditioned.
# ---------------------------------------------------------------------
KINDS = json.loads((HERE / "packs" / "physics" / "kinds.json")
                   .read_text(encoding="utf-8"))
TAX = json.loads((HERE / "taxonomy.json").read_text(encoding="utf-8"))

# cap -> (formula over named inputs, [(input, kind, lo, hi, round)],
#         output noun, output unit, leaf)  -- formulas written here.
CAP_T = {
    "force_from_mass_accel": ("m * a",
                              [("m", "mass", 2, 2000, 0),
                               ("a", "accel", 0.5, 12, 1)],
                              "force", "N",
                              "physics/mechanics/dynamics_forces"),
    "kinetic_energy": ("0.5 * m * v**2",
                       [("m", "mass", 1, 500, 0),
                        ("v", "speed", 1, 60, 1)],
                       "kinetic energy", "J",
                       "physics/mechanics/energy_work"),
    "potential_energy": ("m * 9.8 * h",
                         [("m", "mass", 1, 300, 0),
                          ("h", "height", 1, 120, 1)],
                         "potential energy", "J",
                         "physics/mechanics/energy_work"),
    "work_from_force": ("f * d",
                        [("f", "force", 5, 900, 0),
                         ("d", "distance", 1, 80, 1)],
                        "work done", "J",
                        "physics/mechanics/energy_work"),
    "mass_from_density": ("rho * vol",
                          [("rho", "density", 500, 9000, 0),
                           ("vol", "volume", 0.1, 4, 2)],
                          "mass", "kg",
                          "physics/mechanics/mass_density_weight"),
    "current_from_vr": ("v / r",
                        [("v", "voltage", 3, 240, 0),
                         ("r", "resistance", 2, 600, 0)],
                        "current", "A",
                        "physics/electricity/dc_circuits"),
    "power_from_vi": ("v * i",
                      [("v", "voltage", 3, 240, 0),
                       ("i", "current", 0.1, 15, 1)],
                      "power", "W",
                      "physics/electricity/electrical_energy_power"),
    "charge_from_it": ("i * t",
                       [("i", "current", 0.1, 12, 1),
                        ("t", "time", 5, 600, 0)],
                       "charge", "C",
                       "physics/electricity/dc_circuits"),
    "heat_to_temp_rise": ("q / (m * c)",
                          [("q", "heat", 500, 90000, 0),
                           ("m", "mass", 0.5, 20, 1),
                           ("c", "specific_heat", 400, 4200, 0)],
                          "temperature rise", "K",
                          "physics/thermodynamics/heat_temperature"),
    "carnot_efficiency": ("1 - tc / th",
                          [("tc", "temp_cold", 250, 350, 0),
                           ("th", "temp_hot", 400, 900, 0)],
                          "Carnot efficiency", "",
                          "physics/thermodynamics/engines_efficiency"),
    "concentration_calc": ("n / vol",
                           [("n", "moles", 0.1, 6, 2),
                            ("vol", "volume", 0.2, 5, 2)],
                           "concentration", "mol/L",
                           "chemistry_quantitative/solution_stoichiometry"),
    "profit_calc": ("rev - cost",
                    [("rev", "revenue", 1000, 90000, 0),
                     ("cost", "cost", 500, 60000, 0)],
                    "profit", "$",
                    "quantitative_finance/profitability"),
    "revenue_calc": ("p * q",
                     [("p", "price", 2, 400, 0),
                      ("q", "quantity", 10, 5000, 0)],
                     "revenue", "$",
                     "quantitative_finance/cost_revenue"),
    "simple_interest": ("p * r * t / 100",
                        [("p", "principal", 500, 50000, 0),
                         ("r", "rate", 1, 12, 1),
                         ("t", "years", 1, 10, 0)],
                        "simple interest", "$",
                        "quantitative_finance/interest_growth"),
    "break_even": ("f / (p - u)",
                   [("f", "fixed_cost", 1000, 80000, 0),
                    ("p", "price", 20, 400, 0),
                    ("u", "unit_cost", 2, 19, 0)],
                   "break-even quantity", "units",
                   "quantitative_finance/cost_revenue"),
    "ltv_calc": ("arpu * life",
                 [("arpu", "arpu", 5, 200, 0),
                  ("life", "lifetime", 2, 48, 0)],
                 "customer lifetime value", "$",
                 "quantitative_finance/unit_economics"),
    "area_rect": ("l * w",
                  [("l", "length", 2, 90, 1),
                   ("w", "width", 1, 60, 1)],
                  "area", "m^2",
                  "mathematics/geometry_mensuration/area_perimeter"),
    "volume_box": ("l * w * h",
                   [("l", "length", 1, 20, 1),
                    ("w", "width", 1, 15, 1),
                    ("h", "height", 1, 10, 1)],
                   "volume", "m^3",
                   "mathematics/geometry_mensuration/volume_surface"),
    "mean_calc": (None, None, "mean", "",
                  "mathematics/statistics/descriptive"),
    "z_calc": ("(x - mu) / s",
               [("x", "value", 40, 160, 0),
                ("mu", "mean", 60, 140, 0),
                ("s", "std", 5, 25, 0)],
               "z-score", "",
               "mathematics/statistics/standardized_scores"),
}

NOUN = {
    "mass": ("mass", "kg"), "accel": ("acceleration", "m/s^2"),
    "speed": ("speed", "m/s"), "height": ("height", "m"),
    "force": ("force", "N"), "distance": ("distance", "m"),
    "density": ("density", "kg/m^3"), "volume": ("volume", "m^3"),
    "voltage": ("voltage", "V"), "resistance": ("resistance", "ohm"),
    "current": ("current", "A"), "time": ("time", "s"),
    "heat": ("heat energy", "J"),
    "specific_heat": ("specific heat capacity", "J/(kg*K)"),
    "temp_cold": ("cold reservoir temperature", "K"),
    "temp_hot": ("hot reservoir temperature", "K"),
    "moles": ("amount of solute", "mol"),
    "revenue": ("revenue", "$"), "cost": ("total cost", "$"),
    "price": ("price per unit", "$"), "quantity": ("units sold", ""),
    "principal": ("principal", "$"), "rate": ("annual rate", "%"),
    "years": ("time", "years"), "fixed_cost": ("fixed costs", "$"),
    "unit_cost": ("variable cost per unit", "$"),
    "arpu": ("average revenue per user per month", "$"),
    "lifetime": ("expected customer lifetime", "months"),
    "length": ("length", "m"), "width": ("width", "m"),
    "value": ("observed value", ""), "mean": ("mean", ""),
    "std": ("standard deviation", ""),
}

TIER_A_OPENERS = [
    "A {sys} has {facts}. What is the {out}?",
    "Given {facts}, find the {out}.",
    "{facts_cap}. Compute the {out}.",
    "{facts_cap}. What is the {out}?",
]
SYSTEMS = ["system", "setup", "device", "machine", "process", "sample",
           "circuit", "business", "product line", "object"]


def _fmt(v, nd):
    return ("%d" % round(v)) if nd == 0 else ("%.*f" % (nd, v))


def gen_tierA(rng, cap):
    formula, inputs, out_noun, out_unit, leaf = CAP_T[cap]
    if cap == "mean_calc":
        vals = [rng.randint(4, 96) for _ in range(rng.randint(4, 7))]
        gold = sum(vals) / len(vals)
        text = "The measured values are %s. What is the mean?" % (
            ", ".join(str(v) for v in vals))
        wit = {"check": "value", "claim_key": "claimed",
               "expected": gold}
        return text, gold, wit, [leaf]
    env, parts = {}, []
    for name, kind, lo, hi, nd in inputs:
        v = float(_fmt(rng.uniform(lo, hi), nd))
        env[name] = v
        noun, unit = NOUN[kind]
        # B28: the first build emitted "a acceleration" (dead article
        # logic); the broken article broke the engine's fact parse on
        # a slice of items and surfaced the unbound-quantity hazard.
        art = "an" if noun[0] in "aeiou" else "a"
        parts.append("%s %s %s" % (
            art, noun, "of %s %s" % (_fmt(v, nd), unit) if unit
            else "of %s" % _fmt(v, nd)))
    facts = ", ".join(parts)
    gold = float(W.evaluate(formula, env))
    tmpl = rng.choice(TIER_A_OPENERS)
    text = tmpl.format(sys=rng.choice(SYSTEMS), facts=facts,
                       facts_cap=facts[0].upper() + facts[1:],
                       out=out_noun)
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return text, gold, wit, [leaf]


# ---------------------------------------------------------------------
# Unit conversion (pint golds, computed once here)
# ---------------------------------------------------------------------
try:
    import pint
    _UREG = pint.UnitRegistry()
except Exception:                                    # pragma: no cover
    _UREG = None

CONV = [
    ("km", "m", 0.5, 900, "mathematics-free", "units_conversion/simple_units"),
    ("m", "cm", 0.1, 50, "", "units_conversion/simple_units"),
    ("kg", "g", 0.05, 80, "", "units_conversion/simple_units"),
    ("hour", "minute", 0.25, 30, "", "units_conversion/simple_units"),
    ("mile", "km", 0.5, 500, "", "units_conversion/simple_units"),
    ("m/s", "km/h", 1, 90, "", "units_conversion/compound_rates"),
    ("km/h", "m/s", 5, 300, "", "units_conversion/compound_rates"),
    ("J", "kJ", 100, 90000, "", "units_conversion/simple_units"),
    ("L", "mL", 0.1, 40, "", "units_conversion/simple_units"),
]


def gen_conversion(rng):
    src, dst, lo, hi, _, leaf = CONV[rng.randrange(len(CONV))]
    v = round(rng.uniform(lo, hi), 2)
    gold = float((v * _UREG(src)).to(dst).magnitude)
    text = rng.choice([
        "Convert %s %s to %s." % (v, src, dst),
        "Express %s %s in %s." % (v, src, dst),
        "How many %s is %s %s?" % (dst, v, src),
        "%s %s equals how many %s?" % (v, src, dst),
    ])
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return text, gold, wit, [leaf]


# ---------------------------------------------------------------------
# Symbolic families (own-register phrasings; golds via witness-side
# construction -- NO sympy anywhere in this file)
# ---------------------------------------------------------------------
def _poly(rng, deg=None, var="x"):
    deg = deg or rng.randint(1, 4)
    terms = []
    for p in range(deg, -1, -1):
        c = rng.randint(-9, 9)
        if c == 0 and p == deg:
            c = rng.choice([1, 2, 3, -2])
        if c == 0:
            continue
        if p == 0:
            terms.append(str(c))
        elif p == 1:
            terms.append("%d*%s" % (c, var))
        else:
            terms.append("%d*%s**%d" % (c, var, p))
    e = " + ".join(terms).replace("+ -", "- ")
    return e or var


_FUNS = ["sin(x)", "cos(x)", "exp(x)", "log(x)", "sqrt(x)"]


def _fun_expr(rng):
    k = rng.random()
    if k < 0.35:
        return _poly(rng)
    if k < 0.6:
        return "%s*%s" % (_poly(rng, rng.randint(1, 2)),
                          rng.choice(_FUNS))
    if k < 0.8:
        return "%s + %s" % (_poly(rng, rng.randint(1, 3)),
                            rng.choice(_FUNS))
    return "%s(%s)" % (rng.choice(["sin", "cos", "exp"]),
                       _poly(rng, 1))


def _diff_gold(expr, order, at=None):
    """Numeric-witness gold: for expression answers the witness record
    IS the gold (graded by agreement at points); for at-points the
    gold is the finite-difference value."""
    needs_pos = "log" in expr or "sqrt" in expr
    window = (0.3, 1.9) if needs_pos else (-1.6, 1.6)
    if at is not None:
        want = float(W._fd(expr, "x", at, order, {}))
        return want, {"check": "derivative_at", "claim_key": "claimed",
                      "expr": expr, "var": "x", "order": order,
                      "point": at}
    return None, {"check": "derivative", "claim_key": "claimed_expr",
                  "expr": expr, "var": "x", "order": order,
                  "window": window}


def gen_diff(rng, order, at_point=False):
    expr = _fun_expr(rng)
    disp = expr.replace("**", "^").replace("*", "")
    ordw = {1: "", 2: "second ", 3: "third ", 4: "fourth "}[order]
    if at_point:
        at = float(rng.randint(1, 3)) if ("log" in expr or "sqrt" in
                                          expr) else float(
            rng.randint(-2, 3))
        gold, wit = _diff_gold(expr, order, at)
        text = rng.choice([
            "What is the %sderivative of %s at x = %g?" % (ordw, disp,
                                                           at),
            "Find the %sderivative of %s evaluated at x = %g." % (
                ordw, disp, at),
            "Compute the rate of change of %s at x = %g." % (disp, at)
            if order == 1 else
            "Evaluate the %sderivative of %s at x = %g." % (ordw, disp,
                                                            at),
        ])
        leaf = "mathematics/calculus/differentiation/evaluate_at_point"
        return text, gold, wit, [leaf]
    gold, wit = _diff_gold(expr, order)
    text = rng.choice([
        "Differentiate %s." % disp if order == 1 else
        "Differentiate %s twice." % disp if order == 2 else
        "Find the %sderivative of %s." % (ordw, disp),
        "Find the %sderivative of %s." % (ordw, disp),
        "What is the %sderivative of %s?" % (ordw, disp),
    ])
    leaf = {1: "mathematics/calculus/differentiation/first_derivative",
            2: "mathematics/calculus/differentiation/second_derivative",
            }.get(order,
                  "mathematics/calculus/differentiation/higher_order")
    return text, gold, wit, [leaf]


def gen_int_def(rng):
    expr = _poly(rng, rng.randint(1, 3))
    a, b = sorted(rng.sample(range(0, 6), 2))
    disp = expr.replace("**", "^").replace("*", "")
    from mpmath import quad
    gold = float(quad(lambda t: W.evaluate(expr, {"x": t}), [a, b]))
    text = rng.choice([
        "Integrate %s from %d to %d." % (disp, a, b),
        "What is the integral of %s from %d to %d?" % (disp, a, b),
        "Evaluate the definite integral of %s on [%d, %d]." % (disp,
                                                               a, b),
    ])
    wit = {"check": "definite_integral", "claim_key": "claimed",
           "expr": expr, "var": "x", "a": a, "b": b}
    return text, gold, wit, ["mathematics/calculus/integration/definite"]


def gen_int_indef(rng):
    expr = rng.choice(["cos(x)", "sin(x)", "exp(x)",
                       _poly(rng, rng.randint(1, 3))])
    disp = expr.replace("**", "^").replace("*", "")
    text = rng.choice([
        "Find the antiderivative of %s." % disp,
        "Integrate %s." % disp,
        "What is the indefinite integral of %s?" % disp,
    ])
    wit = {"check": "antiderivative", "claim_key": "claimed_F",
           "expr": expr, "var": "x", "window": (0.3, 1.6)}
    return text, None, wit, [
        "mathematics/calculus/integration/indefinite"]


def gen_limit(rng):
    kind = rng.random()
    if kind < 0.4:
        expr, pt, gold = "sin(%d*x)/x" % rng.randint(1, 5), 0.0, None
        gold = float(re.match(r"sin\((\d)", expr).group(1))
        text = "What is the limit of sin(%dx)/x as x approaches 0?" % \
            int(gold)
        wit = {"check": "limit", "claim_key": "claimed", "expr": expr,
               "var": "x", "point": 0}
        return text, gold, wit, [
            "mathematics/calculus/limits/finite_point"]
    if kind < 0.75:
        a, b = rng.randint(1, 9), rng.randint(1, 9)
        c, d = rng.randint(1, 9), rng.randint(1, 9)
        expr = "(%d*x + %d)/(%d*x + %d)" % (a, b, c, d)
        gold = a / c
        text = "Find the limit of (%dx + %d)/(%dx + %d) as x " \
            "approaches infinity." % (a, b, c, d)
        wit = {"check": "limit", "claim_key": "claimed", "expr": expr,
               "var": "x", "point": "inf"}
        return text, gold, wit, [
            "mathematics/calculus/limits/at_infinity"]
    p = float(rng.randint(1, 4))
    expr = _poly(rng, 2)
    gold = float(W.evaluate(expr, {"x": p}))
    disp = expr.replace("**", "^").replace("*", "")
    text = "What is the limit of %s as x approaches %g?" % (disp, p)
    wit = {"check": "limit", "claim_key": "claimed", "expr": expr,
           "var": "x", "point": p}
    return text, gold, wit, ["mathematics/calculus/limits/finite_point"]


def gen_solve(rng):
    if rng.random() < 0.5:
        r1, r2 = rng.sample(range(-6, 8), 2)
        b, c = -(r1 + r2), r1 * r2
        lhs = "x**2 %+d*x %+d" % (b, c) if b else "x**2 %+d" % c
        lhs = lhs.replace("+0*x ", "").replace("+ -", "- ")
        disp = lhs.replace("**", "^").replace("*", "")
        gold = sorted([float(r1), float(r2)])
        text = rng.choice([
            "Solve %s = 0." % disp,
            "Find the roots of %s = 0." % disp,
            "What are the solutions of %s = 0?" % disp,
        ])
        wit = {"check": "solution", "claim_key": "roots", "lhs": lhs,
               "rhs": "0", "var": "x"}
        return text, gold, wit, [
            "mathematics/algebra/quadratic_polynomial_solve"]
    a = rng.randint(2, 12)
    x0 = rng.randint(-9, 15)
    b = rng.randint(-20, 20)
    cst = a * x0 + b
    lhs, rhs = "%d*x %+d" % (a, b), str(cst)
    disp = lhs.replace("*", "")
    gold = [float(x0)]
    text = rng.choice([
        "Solve %s = %s." % (disp, rhs),
        "Solve for x: %s = %s" % (disp, rhs),
        "Find x such that %s = %s." % (disp, rhs),
    ])
    wit = {"check": "solution", "claim_key": "roots", "lhs": lhs,
           "rhs": rhs, "var": "x"}
    return text, gold, wit, ["mathematics/algebra/linear_solve"]


def gen_eval(rng):
    expr = "%d*(%d %+d)**2 %+d" % (rng.randint(2, 9), rng.randint(2, 9),
                                   rng.randint(-5, 9),
                                   rng.randint(-20, 20))
    gold = float(W.evaluate(expr, {}))
    disp = expr.replace("**", "^")
    text = rng.choice(["What is %s?" % disp, "Evaluate %s." % disp,
                       "Compute %s." % disp])
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return text, gold, wit, [
        "mathematics/arithmetic/expression_evaluation"]


def gen_sum(rng):
    expr = rng.choice(["k", "k**2", "2*k - 1", "k**3"])
    n = rng.randint(5, 60)
    gold = float(sum(W.evaluate(expr, {"k": i})
                     for i in range(1, n + 1)))
    disp = expr.replace("**", "^").replace("*", "")
    text = rng.choice([
        "What is the sum of %s for k = 1 to %d?" % (disp, n),
        "Sum of %s from k = 1 to %d." % (disp, n),
    ])
    wit = {"check": "finite_sum", "claim_key": "claimed", "expr": expr,
           "var": "k", "a": 1, "b": n}
    return text, gold, wit, ["mathematics/sequences_series/finite_sum"]


def gen_seq(rng):
    a0, d, n = rng.randint(1, 20), rng.randint(2, 12), rng.randint(5, 40)
    if rng.random() < 0.5:
        gold = float(a0 + (n - 1) * d)
        text = "An arithmetic sequence starts at %d with common " \
            "difference %d. What is term %d?" % (a0, d, n)
    else:
        r, n = rng.randint(2, 4), rng.randint(3, 12)
        gold = float(a0 * r ** (n - 1))
        text = "A geometric sequence starts at %d with ratio %d. " \
            "What is term %d?" % (a0, r, n)
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return text, gold, wit, [
        "mathematics/sequences_series/arithmetic_geometric"]


def gen_numtheory(rng):
    k = rng.random()
    if k < 0.4:
        a, b = rng.randint(12, 400), rng.randint(12, 400)
        op = rng.choice(["gcd", "lcm"])
        import math
        gold = float(math.gcd(a, b) if op == "gcd" else
                     abs(a * b) // math.gcd(a, b))
        name = {"gcd": rng.choice(["gcd", "greatest common divisor"]),
                "lcm": rng.choice(["lcm", "least common multiple"])}[op]
        text = "What is the %s of %d and %d?" % (name, a, b)
        wit = {"check": "gcd_lcm", "claim_key": "claimed", "kind": op,
               "a": a, "b": b}
        return text, gold, wit, ["mathematics/number_theory/gcd_lcm"]
    n = rng.randint(20, 2000)
    import math
    gold = n >= 2 and all(n % i for i in
                          range(2, int(math.isqrt(n)) + 1))
    text = rng.choice(["Is %d prime?" % n,
                       "Is %d a prime number?" % n])
    wit = {"check": "int_fact", "claim_key": "claimed",
           "kind": "is_prime", "n": n}
    return text, bool(gold), wit, [
        "mathematics/number_theory/divisibility_primes"]


def gen_comb(rng):
    n = rng.randint(5, 30)
    r = rng.randint(2, min(6, n - 1))
    if rng.random() < 0.6:
        import math
        gold = float(math.comb(n, r))
        text = rng.choice([
            "%d choose %d" % (n, r),
            "How many combinations of %d items taken %d at a time?"
            % (n, r)])
        wit = {"check": "int_fact", "claim_key": "claimed",
               "kind": "ncr", "n": n, "r": r}
        return text, gold, wit, [
            "mathematics/combinatorics_probability/"
            "permutations_combinations"]
    f, t = rng.randint(1, 7), rng.randint(8, 40)
    gold = f / t
    text = "What is the probability of an outcome with %d " \
        "favourable cases out of %d equally likely cases?" % (f, t)
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return text, gold, wit, [
        "mathematics/combinatorics_probability/basic_probability"]


def gen_logic(rng):
    p, q, r = (rng.random() < 0.5 for _ in range(3))
    expr = rng.choice(["p and not q", "p or (q and r)",
                       "not (p or q)", "(p and q) or not r",
                       "not p and (q or r)"])
    env = {"p": p, "q": q, "r": r}
    used = {v for v in "pqr" if v in expr}
    env = {k: v for k, v in env.items() if k in used}
    gold = W._logic_eval(expr, env)
    envs = " and ".join("%s is %s" % (k, str(v).lower())
                        for k, v in sorted(env.items()))
    text = "Evaluate %s where %s." % (expr, envs)
    wit = {"check": "logic", "claim_key": "claimed", "expr": expr,
           "env": env}
    return text, bool(gold), wit, ["logic/propositional_evaluation"]


def gen_set(rng):
    A = sorted(rng.sample(range(1, 20), rng.randint(3, 6)))
    B = sorted(rng.sample(range(1, 20), rng.randint(3, 6)))
    kind = rng.choice(["union", "intersection", "difference"])
    want = {"union": set(A) | set(B), "intersection": set(A) & set(B),
            "difference": set(A) - set(B)}[kind]
    if rng.random() < 0.5:
        gold = sorted(want)
        text = "What is the %s of {%s} and {%s}?" % (
            kind, ", ".join(map(str, A)), ", ".join(map(str, B)))
    else:
        gold = len(want)
        text = "How many elements are in the %s of {%s} and {%s}?" % (
            kind, ", ".join(map(str, A)), ", ".join(map(str, B)))
    wit = {"check": "set_op", "claim_key": "claimed", "op": kind,
           "A": A, "B": B}
    return text, gold, wit, ["logic/set_operations"]


def gen_compare(rng):
    a = "%d**%d" % (rng.randint(2, 9), rng.randint(2, 6))
    b = "%d**%d" % (rng.randint(2, 9), rng.randint(2, 6))
    va, vb = float(W.evaluate(a, {})), float(W.evaluate(b, {}))
    if va == vb:
        return gen_compare(rng)
    gold = a.replace("**", "^") if va > vb else b.replace("**", "^")
    text = "Which is larger, %s or %s?" % (a.replace("**", "^"),
                                           b.replace("**", "^"))
    wit = {"check": "value", "claim_key": "claimed",
           "expected": 1.0 if va > vb else -1.0}
    return text, gold, wit, ["logic/comparison_ordering"]


D1_FAMILIES = (
    [lambda r, c=c: gen_tierA(r, c) for c in CAP_T] +
    [gen_conversion] * 4 +
    [lambda r: gen_diff(r, 1), lambda r: gen_diff(r, 2),
     lambda r: gen_diff(r, rng_order_hi(r)),
     lambda r: gen_diff(r, 1, at_point=True),
     lambda r: gen_diff(r, 2, at_point=True),
     gen_int_def, gen_int_indef, gen_limit, gen_solve, gen_eval,
     gen_sum, gen_seq, gen_numtheory, gen_comb, gen_logic, gen_set,
     gen_compare] * 2
)


def rng_order_hi(rng):
    return rng.choice([3, 4])


# ---------------------------------------------------------------------
# Depth chains (SPEC 6.3). Gold composed step-by-step HERE, with
# every step witness-checkable. `nonmono` = consecutive steps differ
# in operation type; multi-area = >= 2 top-level domains.
# ---------------------------------------------------------------------
def gen_d2(rng):
    k = rng.random()
    if k < 0.3:   # derivative then evaluate (calculus chain)
        expr = _poly(rng, rng.randint(2, 4))
        at = float(rng.randint(-2, 3))
        gold = float(W._fd(expr, "x", at, 2, {}))
        disp = expr.replace("**", "^").replace("*", "")
        text = "Differentiate %s twice and evaluate the result at " \
            "x = %g." % (disp, at)
        wit = {"check": "derivative_at", "claim_key": "claimed",
               "expr": expr, "var": "x", "order": 2, "point": at}
        return (text, gold, wit,
                ["mathematics/calculus/differentiation/second_derivative",
                 "mathematics/calculus/differentiation/evaluate_at_point"],
                True)
    if k < 0.55:  # integral then scale (calculus + arithmetic)
        expr = _poly(rng, rng.randint(1, 3))
        a, b = sorted(rng.sample(range(0, 5), 2))
        m = rng.randint(2, 9)
        from mpmath import quad
        base = float(quad(lambda t: W.evaluate(expr, {"x": t}), [a, b]))
        gold = m * base
        disp = expr.replace("**", "^").replace("*", "")
        text = "Integrate %s from %d to %d, then multiply the " \
            "result by %d." % (disp, a, b, m)
        wit = {"check": "value", "claim_key": "claimed",
               "expected": gold}
        return (text, gold, wit,
                ["mathematics/calculus/integration/definite",
                 "mathematics/arithmetic/expression_evaluation"], True)
    if k < 0.8:   # solve then substitute (algebra chain)
        r1, r2 = rng.sample(range(1, 9), 2)
        b, c = -(r1 + r2), r1 * r2
        lhs = ("x**2 %+d*x %+d" % (b, c)).replace("+ -", "- ")
        big = float(max(r1, r2))
        m2, a2 = rng.randint(2, 7), rng.randint(1, 15)
        gold = m2 * big + a2
        disp = lhs.replace("**", "^").replace("*", "")
        text = "Find the larger root of %s = 0, then compute %d " \
            "times that root plus %d." % (disp, m2, a2)
        wit = {"check": "value", "claim_key": "claimed",
               "expected": gold}
        return (text, gold, wit,
                ["mathematics/algebra/quadratic_polynomial_solve",
                 "mathematics/arithmetic/expression_evaluation"], True)
    # gcd then primality (number theory, monotone-ish pair)
    import math
    a, b = rng.randint(20, 300), rng.randint(20, 300)
    g = math.gcd(a, b)
    gold = g >= 2 and all(g % i for i in
                          range(2, int(math.isqrt(g)) + 1))
    text = "Is the greatest common divisor of %d and %d prime?" % (a, b)
    wit = {"check": "int_fact", "claim_key": "claimed",
           "kind": "is_prime", "n": g}
    return (text, bool(gold), wit,
            ["mathematics/number_theory/gcd_lcm",
             "mathematics/number_theory/divisibility_primes"], False)


def gen_d3(rng):
    k = rng.random()
    if k < 0.35:  # kinematics derivative -> unit conversion
        c2, c1 = rng.randint(1, 6), rng.randint(0, 9)
        t0 = float(rng.randint(1, 8))
        v_ms = 2 * c2 * t0 + c1                # d/dt (c2 t^2 + c1 t)
        gold = float((v_ms * _UREG("m/s")).to("km/h").magnitude)
        text = "A particle's position is s(t) = %dt^2 %+dt metres. " \
            "Find its speed at t = %g seconds, in km/h." % (c2, c1, t0)
        wit = {"check": "value", "claim_key": "claimed",
               "expected": gold}
        return (text, gold, wit,
                ["mathematics/calculus/differentiation/evaluate_at_point",
                 "physics/mechanics/kinematics",
                 "units_conversion/compound_rates"], True)
    if k < 0.65:  # KE -> kJ conversion (physics + units)
        m = rng.randint(2, 400)
        v = rng.randint(2, 50)
        gold = 0.5 * m * v * v / 1000.0
        text = "A body of mass %d kg moves at %d m/s. What is its " \
            "kinetic energy in kilojoules?" % (m, v)
        wit = {"check": "value", "claim_key": "claimed",
               "expected": gold}
        return (text, gold, wit,
                ["physics/mechanics/energy_work",
                 "units_conversion/simple_units"], True)
    # finance chain: revenue, cost -> profit -> margin %
    p, q = rng.randint(5, 300), rng.randint(20, 3000)
    cost = rng.randint(1, max(2, p * q * 3 // 4))
    rev = p * q
    gold = (rev - cost) / rev * 100.0
    text = "A product sells %d units at $%d each with total costs " \
        "of $%d. What is the profit margin in percent?" % (q, p, cost)
    wit = {"check": "value", "claim_key": "claimed", "expected": gold}
    return (text, gold, wit,
            ["quantitative_finance/cost_revenue",
             "quantitative_finance/profitability"], True)


def gen_d4(rng):
    k = rng.random()
    if k < 0.5:   # integral vs sum comparison (calculus+series+logic)
        n = rng.randint(3, 12)
        from mpmath import quad
        i_val = float(quad(lambda t: W.evaluate("x**2", {"x": t}),
                           [0, n]))
        s_val = float(sum(i * i for i in range(1, n + 1)))
        gold = "sum" if s_val > i_val else "integral"
        text = "Which is larger: the integral of x^2 from 0 to %d, " \
            "or the sum of k^2 for k = 1 to %d?" % (n, n)
        wit = {"check": "value", "claim_key": "claimed",
               "expected": 1.0 if s_val > i_val else -1.0}
        return (text, gold, wit,
                ["mathematics/calculus/integration/definite",
                 "mathematics/sequences_series/finite_sum",
                 "logic/comparison_ordering"], True)
    # physics vs physics comparison via energies (mech+thermo+logic)
    m, v = rng.randint(2, 200), rng.randint(2, 40)
    ke = 0.5 * m * v * v
    q, mm, c = rng.randint(1, 50) * 100, rng.randint(1, 10), 4200
    dT = q / (mm * c)
    m2, h = rng.randint(2, 200), rng.randint(1, 100)
    pe = m2 * 9.8 * h
    gold = "kinetic" if ke > pe else "potential"
    text = "A mass of %d kg moves at %d m/s; another mass of %d kg " \
        "sits %d m high. Which energy is larger, the kinetic energy " \
        "of the first or the potential energy of the second?" % (
            m, v, m2, h)
    wit = {"check": "value", "claim_key": "claimed",
           "expected": 1.0 if ke > pe else -1.0}
    _ = dT
    return (text, gold, wit,
            ["physics/mechanics/energy_work",
             "physics/mechanics/energy_work",
             "logic/comparison_ordering"], True)


# ---------------------------------------------------------------------
# Distractors (narrative; claim = ESCALATION only)
# ---------------------------------------------------------------------
def load_distractors():
    out = []
    p = HERE / "corpora" / "gsm8k_test.jsonl"
    for i, line in enumerate(p.read_text(encoding="utf-8")
                             .splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        ans = d["answer"].split("####")[-1].strip().replace(",", "")
        out.append({"src": "gsm8k", "sid": "g%04d" % i,
                    "text": d["question"], "gold": ans})
    x = ET.parse(HERE / "corpora" / "asdiv.xml").getroot()
    for i, pr in enumerate(x.iter("Problem")):
        body = (pr.findtext("Body") or "").strip()
        q = (pr.findtext("Question") or "").strip()
        a = (pr.findtext("Answer") or "").strip()
        if body and q:
            out.append({"src": "asdiv", "sid": "a%04d" % i,
                        "text": ("%s %s" % (body, q)).strip(),
                        "gold": a})
    return out


# ---------------------------------------------------------------------
def verify_item(it):
    """Every programmatic item's stored gold must pass its own witness
    record (golds are not trusted, they are checked)."""
    wit = it["witness"]
    gold = it["gold"]
    if wit["check"] == "derivative" or (wit["check"] ==
                                        "antiderivative"):
        return True   # expression golds: the record itself grades
    claim = gold
    if it["gold_type"] == "choice":
        claim = wit["expected"]      # comparisons: sign convention
    ok, _ = W.run_check(wit, claim)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100000)
    ap.add_argument("--out", default=str(HERE / "results" / "v16" /
                                         "data"))
    a = ap.parse_args()
    rng = random.Random(SEED)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    distr = load_distractors()
    rng.shuffle(distr)
    n_total = a.n
    n_dist = min(len(distr), round(n_total * 0.036))
    n_foreign = round(n_total * 0.03) if n_total >= 10000 else 0
    n_prog = n_total - n_dist - n_foreign

    # depth mix over programmatic+foreign (distractors carry none)
    items = []
    fails = 0
    depth_of = {1: 0.40, 2: 0.30, 3: 0.20, 4: 0.10}
    quota = {d: round((n_prog + n_foreign) * f)
             for d, f in depth_of.items()}
    made = {d: 0 for d in quota}
    idx = 0
    while sum(made.values()) < sum(quota.values()):
        d = next(k for k in (1, 2, 3, 4) if made[k] < quota[k])
        try:
            if d == 1:
                fam = D1_FAMILIES[rng.randrange(len(D1_FAMILIES))]
                text, gold, wit, leaves = fam(rng)
                nonmono = False
            elif d == 2:
                text, gold, wit, leaves, nonmono = gen_d2(rng)
            elif d == 3:
                text, gold, wit, leaves, nonmono = gen_d3(rng)
            else:
                text, gold, wit, leaves, nonmono = gen_d4(rng)
        except (ValueError, ZeroDivisionError, OverflowError,
                RecursionError):
            fails += 1
            if fails > 5000:
                raise RuntimeError("generator failing too often")
            continue
        gt = ("bool" if isinstance(gold, bool) else
              "list" if isinstance(gold, list) else
              "choice" if isinstance(gold, str) else
              "expr" if gold is None else "num")
        it = {"id": "q16_%06d" % idx, "text": text, "gold": gold,
              "gold_type": gt, "witness": wit, "leaves": leaves,
              "depth": d, "nonmono": bool(nonmono if d > 1 else False),
              "register": "own", "distractor": False}
        if not verify_item(it):
            fails += 1
            continue
        items.append(it)
        made[d] += 1
        idx += 1

    # mark foreign slots (facts+gold fixed; text will be REPLACED by a
    # bridge author who sees only the fact sheet)
    fslots = rng.sample(range(len(items)), n_foreign)
    for i in fslots:
        items[i]["register"] = "foreign_slot"

    for j, d in enumerate(distr[:n_dist]):
        items.append({"id": "q16_dist_%04d" % j, "text": d["text"],
                      "gold": d["gold"], "gold_type": "num",
                      "witness": None, "leaves": [], "depth": None,
                      "nonmono": False, "register": "corpus",
                      "distractor": True, "src": d["src"]})

    rng.shuffle(items)
    # splits with DISJOINT distractors by construction (single pass)
    n = len(items)
    acq, dev, seal = (items[:int(n * 0.6)],
                      items[int(n * 0.6):int(n * 0.7)],
                      items[int(n * 0.7):])
    manifest = {"seed": SEED, "n": n, "programmatic": n_prog,
                "foreign_slots": n_foreign, "distractors": n_dist,
                "generator_rejects": fails,
                "depth_quota": quota,
                "splits": {"acq": len(acq), "dev": len(dev),
                           "seal": len(seal)}}
    for name, part in (("acq", acq), ("dev", dev), ("seal", seal)):
        (out / ("q100k_%s.json" % name)).write_text(
            json.dumps(part, indent=0), encoding="utf-8")
    (out / "q100k_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
