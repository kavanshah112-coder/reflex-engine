# -*- coding: utf-8 -*-
"""V0.9 capability universe (spec Sections 8, 18, 24).

Two layers:
1. REAL: hand-authored, dimension-checked capabilities with genuine
   semantics across six domains (mechanics/thermal/electrical inherited
   from V0.8's registry, plus finance, engineering, chemistry,
   statistics, business). These carry natural-language surfaces and are
   used by the CPLX and XDOM benchmarks.
2. SYNTH: generated kind-graph registries (35/100/250/500/1000 caps)
   with NO language surface, used exclusively by the registry-scaling
   search experiment (Section 24).

Every kind carries a DIMENSION vector over base dimensions
(M kg, L m, T s, I A, K temp, N count, $ money) enabling principled
dimensional analysis (Section 20). Capabilities declare expressions
whose dimensional consistency is verified at module import.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ------------------------------------------------------- dimensions
DIMS = ("M", "L", "T", "I", "K", "N", "$")


def dim(**kw):
    return tuple(kw.get(d, 0) for d in DIMS)


D0 = dim()

# kind -> (dimension, canonical unit, surface noun phrases, unit surfaces)
KINDS9 = {
    # --- inherited physical kinds (V0.8-compatible names) ---
    "mass":         (dim(M=1), "kg", ["mass"], ["kg", "kilograms"]),
    "speed":        (dim(L=1, T=-1), "m/s", ["speed", "velocity"], ["m/s"]),
    "height":       (dim(L=1), "m", ["height", "thickness"], ["m", "metres"]),
    "distance":     (dim(L=1), "m", ["distance"], ["m"]),
    "length":       (dim(L=1), "m", ["length"], ["m"]),
    "width":        (dim(L=1), "m", ["width"], ["m"]),
    "area":         (dim(L=2), "m^2", ["area"], ["m^2", "square metres"]),
    "volume":       (dim(L=3), "m^3", ["volume"], ["m^3", "cubic metres"]),
    "density":      (dim(M=1, L=-3), "kg/m^3", ["density"], ["kg/m^3"]),
    "energy":       (dim(M=1, L=2, T=-2), "J", ["energy"], ["J", "joules"]),
    "power":        (dim(M=1, L=2, T=-3), "W", ["power"], ["W", "watts"]),
    "time":         (dim(T=1), "s", ["time", "duration"], ["s", "seconds"]),
    "force":        (dim(M=1, L=1, T=-2), "N", ["force", "weight"], ["N"]),
    "voltage":      (dim(M=1, L=2, T=-3, I=-1), "V", ["voltage"], ["V"]),
    "current":      (dim(I=1), "A", ["current"], ["A", "amps"]),
    "resistance":   (dim(M=1, L=2, T=-3, I=-2), "ohm", ["resistance"],
                     ["ohms"]),
    "charge":       (dim(I=1, T=1), "C", ["charge"], ["coulombs"]),
    "temp_diff":    (dim(K=1), "K", ["temperature rise", "warming", "temperature change", "temperature difference", "degrees warmer"],
                     ["K", "degrees"]),
    "temp_hot":     (dim(K=1), "K", ["hot reservoir temperature"], ["K"]),
    "temp_cold":    (dim(K=1), "K", ["cold reservoir temperature"], ["K"]),
    "spec_heat":    (dim(L=2, T=-2, K=-1), "J/kg/K", ["specific heat"],
                     ["J/kg/K"]),
    "efficiency":   (D0, "", ["efficiency"], []),
    "accel":        (dim(L=1, T=-2), "m/s^2", ["acceleration"], ["m/s^2"]),
    # --- finance (inherited) ---
    "count":        (dim(N=1), "units", ["quantity sold", "number of units", "batch"],
                     ["units"]),
    "price_per_unit": (dim(**{"$": 1, "N": -1}), "$/unit",
                       ["selling price"], ["$ each"]),
    "unit_cost":    (dim(**{"$": 1, "N": -1}), "$/unit",
                     ["production cost"], ["$ each"]),
    "fixed_cost":   (dim(**{"$": 1}), "$", ["fixed costs"], ["$"]),
    "revenue":      (dim(**{"$": 1}), "$", ["revenue"], ["$"]),
    "cost_var":     (dim(**{"$": 1}), "$", ["variable cost"], ["$"]),
    "cost_total":   (dim(**{"$": 1}), "$", ["total cost"], ["$"]),
    "profit":       (dim(**{"$": 1}), "$", ["profit"], ["$"]),
    "net_profit":   (dim(**{"$": 1}), "$", ["after-tax profit"], ["$"]),
    "rate":         (D0, "", ["rate", "margin"], ["%"]),
    "rate_tax":     (D0, "", ["tax rate"], ["%"]),
    "principal":    (dim(**{"$": 1}), "$", ["principal"], ["$"]),
    "interest":     (dim(**{"$": 1}), "$", ["interest"], ["$"]),
    "years":        (dim(T=1), "yr", ["term"], ["years"]),
    "final_amount": (dim(**{"$": 1}), "$", ["final balance"], ["$"]),
    "price_per_kg": (dim(**{"$": 1, "M": -1}), "$/kg",
                     ["price per kilogram"], ["$/kg"]),
    "price_per_kwh": (dim(**{"$": 1, "M": -1, "L": -2, "T": 2}), "$/kWh",
                      ["electricity tariff"], ["$/kWh"]),
    # --- chemistry (NEW domain) ---
    "molar_mass":   (dim(M=1, N=-1), "g/mol", ["molar mass"], ["g/mol"]),
    "moles":        (dim(N=1), "mol", ["amount of substance"], ["mol",
                                                                "moles"]),
    "concentration": (dim(N=1, L=-3), "mol/L", ["concentration",
                                                "molarity"], ["mol/L", "M"]),
    "solution_volume": (dim(L=3), "L", ["solution volume"], ["L",
                                                             "litres"]),
    "solute_mass":  (dim(M=1), "g", ["dissolved mass"], ["g", "grams"]),
    "dilution_factor": (D0, "", ["dilution factor"], []),
    "final_concentration": (dim(N=1, L=-3), "mol/L",
                            ["final concentration"], ["mol/L"]),
    "reaction_yield": (D0, "", ["reaction yield"], ["%"]),
    "product_moles": (dim(N=1), "mol", ["product amount"], ["mol"]),
    # --- statistics (NEW domain) ---
    "data_sum":     (D0, "", ["sum of the readings"], []),
    "data_count":   (D0, "", ["number of readings"], []),
    "mean":         (D0, "", ["mean", "average"], []),
    "sq_dev_sum":   (D0, "", ["sum of squared deviations"], []),
    "variance":     (D0, "", ["variance"], []),
    "std_dev":      (D0, "", ["standard deviation"], []),
    "obs_value":    (D0, "", ["observed value"], []),
    "z_score":      (D0, "", ["z-score", "standard score"], []),
    # --- business (NEW domain) ---
    "ad_spend":     (dim(**{"$": 1}), "$", ["marketing spend"], ["$"]),
    "new_customers": (dim(N=1), "", ["new customers"], ["customers"]),
    "cac":          (dim(**{"$": 1, "N": -1}), "$/cust",
                     ["customer acquisition cost"], ["$ per customer"]),
    "monthly_margin": (dim(**{"$": 1, "N": -1}), "$/cust/mo",
                       ["monthly margin per customer"], ["$"]),
    "churn_rate":   (D0, "", ["monthly churn"], ["%"]),
    "cust_lifetime": (D0, "", ["expected customer lifetime (months)"],
                      ["months"]),
    "ltv":          (dim(**{"$": 1, "N": -1}), "$/cust",
                     ["customer lifetime value"], ["$ per customer"]),
    "ltv_cac":      (D0, "", ["LTV to CAC ratio"], []),
    # --- glue kinds for long cross-domain chains (design-time) ---
    "cost_energy":  (dim(**{"$": 1}), "$", ["energy cost"], ["$"]),
    "cost_ops":     (dim(**{"$": 1}), "$", ["operating cost"], ["$"]),
    "ppu":          (dim(**{"$": 1, "N": -1}), "$/unit",
                     ["per-unit net profit", "profit per unit"], ["$ per unit"]),
}


def dim_of(kind):
    e = KINDS9.get(kind)
    return e[0] if e else None


# ---------------------------------------------------------- registry
# expr uses variables named by input kind (first occurrence); executor
# is shared with V0.8's mechanism at run time. 'dim_note' marks caps
# whose expression is intentionally NOT pure dimensional algebra
# (documented conversions).
CAPS9 = {
    # chemistry
    "moles_from_mass": {"inputs": ["solute_mass", "molar_mass"],
                        "output": "moles", "expr": "solute_mass / molar_mass",
                        "domain": "chemistry",
                        "equation": "n = m / M"},
    "concentration_calc": {"inputs": ["moles", "solution_volume"],
                           "output": "concentration",
                           "expr": "moles / solution_volume",
                           "domain": "chemistry", "equation": "C = n / V"},
    "dilute": {"inputs": ["concentration", "dilution_factor"],
               "output": "final_concentration",
               "expr": "concentration / dilution_factor",
               "domain": "chemistry", "equation": "C2 = C1 / f"},
    "yield_product": {"inputs": ["moles", "reaction_yield"],
                      "output": "product_moles",
                      "expr": "moles * reaction_yield",
                      "domain": "chemistry", "equation": "np = n * y"},
    # statistics
    "mean_calc": {"inputs": ["data_sum", "data_count"], "output": "mean",
                  "expr": "data_sum / data_count", "domain": "statistics",
                  "equation": "mu = S / n"},
    "variance_calc": {"inputs": ["sq_dev_sum", "data_count"],
                      "output": "variance",
                      "expr": "sq_dev_sum / data_count",
                      "domain": "statistics", "equation": "var = SS / n"},
    "std_calc": {"inputs": ["variance"], "output": "std_dev",
                 "expr": "variance ** 0.5", "domain": "statistics",
                 "equation": "sd = sqrt(var)"},
    "z_calc": {"inputs": ["obs_value", "mean", "std_dev"],
               "output": "z_score",
               "expr": "(obs_value - mean) / std_dev",
               "domain": "statistics", "equation": "z = (x-mu)/sd"},
    # business
    "cac_calc": {"inputs": ["ad_spend", "new_customers"], "output": "cac",
                 "expr": "ad_spend / new_customers", "domain": "business",
                 "equation": "CAC = spend / customers"},
    "lifetime_from_churn": {"inputs": ["churn_rate"],
                            "output": "cust_lifetime",
                            "expr": "1 / churn_rate", "domain": "business",
                            "equation": "L = 1 / churn"},
    "ltv_calc": {"inputs": ["monthly_margin", "cust_lifetime"],
                 "output": "ltv", "expr": "monthly_margin * cust_lifetime",
                 "domain": "business", "equation": "LTV = margin * L"},
    "ltv_cac_ratio": {"inputs": ["ltv", "cac"], "output": "ltv_cac",
                      "expr": "ltv / cac", "domain": "business",
                      "equation": "ratio = LTV / CAC"},
    # glue caps for long chains (design-time, pre-benchmark)
    "energy_cost": {"inputs": ["energy", "price_per_kwh"],
                    "output": "cost_energy",
                    "expr": "energy * price_per_kwh",
                    "domain": "finance", "equation": "Ce = E * tariff",
                    "dim_note": "tariff is $/J-equivalent after kWh "
                                "normalization in compile"},
    "operating_cost": {"inputs": ["cost_var", "cost_energy"],
                       "output": "cost_ops",
                       "expr": "cost_var + cost_energy",
                       "domain": "finance", "equation": "Co = Cv + Ce"},
    "total_cost9": {"inputs": ["fixed_cost", "cost_ops"],
                    "output": "cost_total",
                    "expr": "fixed_cost + cost_ops",
                    "domain": "finance", "equation": "C = F + Co"},
    "net_profit9": {"inputs": ["profit", "rate_tax"],
                    "output": "net_profit",
                    "expr": "profit * (1 - rate_tax)",
                    "domain": "finance", "equation": "Pn = P(1-t)"},
    "per_unit_profit": {"inputs": ["net_profit", "count"],
                        "output": "ppu",
                        "expr": "net_profit / count",
                        "domain": "finance", "equation": "ppu = Pn/n"},
}


def build_real_registry():
    """V0.8 frozen registry (33 caps + 2 bred) + the new domains."""
    from v6.bench6 import _registry_from_json
    reg = _registry_from_json(ROOT / "results/raw_v6/registry_gen5.json")
    for name, spec in CAPS9.items():
        assert name not in reg
        s = dict(spec)
        # compile expr to the v4 executor variable scheme (kind0 names)
        reg[name] = s
    return reg


def _exec_expr(spec, inputs):
    ns = {k: q.value for k, q in inputs.items()}
    # map kind-named variables directly
    try:
        v = eval(spec["expr"], {"__builtins__": {}, "math": math}, ns)
    except Exception as e:
        return None, False, f"exec9:{e}"
    if not (isinstance(v, (int, float)) and math.isfinite(v)):
        return None, False, "non-finite"
    return float(v), True, "ok"


def execute9(name, inputs, registry):
    """Executor covering both V0.8 caps (via v4) and V0.9 kind-named
    expressions."""
    spec = registry[name]
    if name in CAPS9:
        return _exec_expr(spec, inputs)
    from v4.registry_v4 import execute as ex4
    return ex4(name, inputs, registry=registry)


# ----------------------------------------------- dimensional checking
def expr_dimension(expr, reg_kinds=None):
    """Symbolic dimensional evaluation of a kind-named expression.
    Supports + - * / ** with numeric exponents. Returns dim tuple or
    None if inconsistent/unknown."""
    import ast

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Num):
            return D0
        if isinstance(node, ast.Constant):
            return D0 if isinstance(node.value, (int, float)) else None
        if isinstance(node, ast.Name):
            return dim_of(node.id)
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            if a is None or b is None:
                return None
            if isinstance(node.op, (ast.Add, ast.Sub)):
                return a if a == b else None
            if isinstance(node.op, ast.Mult):
                return tuple(x + y for x, y in zip(a, b))
            if isinstance(node.op, ast.Div):
                return tuple(x - y for x, y in zip(a, b))
            if isinstance(node.op, ast.Pow):
                if isinstance(node.right, ast.Constant) and \
                        isinstance(node.right.value, (int, float)):
                    p = node.right.value
                    return tuple(x * p for x in a)
                return None
            return None
        if isinstance(node, ast.UnaryOp):
            return ev(node.operand)
        return None
    try:
        return ev(ast.parse(expr, mode="eval"))
    except Exception:
        return None


def verify_caps_dimensions():
    """Import-time check: every CAPS9 expression is dimensionally
    consistent with its declared output."""
    bad = []
    for name, spec in CAPS9.items():
        d = expr_dimension(spec["expr"])
        want = dim_of(spec["output"])
        if d is None or d != want:
            bad.append((name, d, want))
    return bad


_BAD = verify_caps_dimensions()
assert not _BAD, f"dimensionally inconsistent caps: {_BAD}"


# -------------------------------------------- synthetic scaling layer
def synth_registry(n_caps, seed=900):
    """Kind-graph registry for search-scaling only (no NL surface).
    Kinds are layered; each cap consumes 1-3 kinds from earlier layers
    and produces a new kind. Deterministic per (n_caps, seed)."""
    rng = random.Random(seed + n_caps)
    kinds = [f"sk{i:04d}" for i in range(n_caps + 30)]
    reg = {}
    layer_of = {k: 0 for k in kinds[:30]}   # 30 source kinds
    next_kind = 30
    for i in range(n_caps):
        n_in = rng.choice([1, 2, 2, 3])
        pool = kinds[:next_kind]
        ins = rng.sample(pool, min(n_in, len(pool)))
        out = kinds[next_kind]
        layer_of[out] = max(layer_of[k] for k in ins) + 1
        next_kind += 1
        reg[f"scap{i:04d}"] = {"inputs": ins, "output": out,
                               "expr": "+".join(ins),
                               "domain": "synth",
                               "equation": "synthetic"}
    return reg


def registry_hash(reg):
    slim = {k: {"i": v["inputs"], "o": v["output"]}
            for k, v in sorted(reg.items())}
    return hashlib.sha256(json.dumps(slim, sort_keys=True)
                          .encode()).hexdigest()


if __name__ == "__main__":
    reg = build_real_registry()
    print("real registry:", len(reg), "caps; hash",
          registry_hash(reg)[:16])
    print("dims OK for", len(CAPS9), "new caps")
    for n in (100, 1000):
        sr = synth_registry(n)
        print("synth", n, registry_hash(sr)[:12])
