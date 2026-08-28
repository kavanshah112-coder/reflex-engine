"""V0.4 registry: V0.3 physics capabilities (imported unchanged) + finance +
engineering domains, with versioning and hashing (Sections 43-44).

UNKNOWN_SPECS are used ONLY by the dataset generator to build ground truth.
They are asserted ABSENT from the registry (Section 8). Several REGISTRY
capabilities consume kinds that only unknowns produce (net_profit, sale_price,
liters, final_amount) — real downstream tools around a genuine gap.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v3.capabilities import REGISTRY as PHYS  # noqa: E402  (frozen V0.3)
from v3.capabilities import execute as _EX3_ORIGINAL  # noqa: E402
from v3 import ir as ir3                      # noqa: E402

# extend the kind system
NEW_KINDS = {
    "count": "units", "count_breakeven": "units", "rate": "", "years": "yr",
    "price_per_unit": "$/unit", "unit_cost": "$/unit",
    "fixed_cost": "$", "revenue": "$", "cost_var": "$", "cost_total": "$",
    "profit": "$", "net_profit": "$", "sale_price": "$/unit",
    "principal": "$", "interest": "$", "final_amount": "$",
    "length": "m", "width": "m", "area": "m^2", "density": "kg/m^3",
    "rate_tax": "", "rate_discount": "", "net_interest": "$",
    "price_per_kg": "$/kg", "liters": "L", "price_per_liter": "$/L",
    "coverage_rate": "m^2/L", "fx_rate": "", "cost_eur": "EUR",
    "price_per_kwh": "$/kWh", "money": "$",
}
ir3.KINDS.update(NEW_KINDS)

FIN_ENG = {
    # ---- finance ----
    "revenue_calc": {"inputs": ["price_per_unit", "count"],
                     "output": "revenue", "equation": "R = p*n",
                     "expr": "p0 * c0", "domain": "finance"},
    "variable_cost": {"inputs": ["unit_cost", "count"], "output": "cost_var",
                      "equation": "Cv = u*n", "expr": "u0 * c0",
                      "domain": "finance"},
    "total_cost": {"inputs": ["fixed_cost", "cost_var"],
                   "output": "cost_total", "equation": "C = F + Cv",
                   "expr": "f0 + c0", "domain": "finance"},
    "profit_calc": {"inputs": ["revenue", "cost_total"], "output": "profit",
                    "equation": "P = R - C", "expr": "r0 - c0",
                    "domain": "finance"},
    "margin_calc": {"inputs": ["profit", "revenue"], "output": "rate",
                    "equation": "m = P/R", "expr": "p0 / r0",
                    "domain": "finance",
                    "pre": lambda s: s["r0"] != 0},
    "margin_net": {"inputs": ["net_profit", "revenue"], "output": "rate",
                   "equation": "m = Pn/R", "expr": "n0 / r0",
                   "domain": "finance", "pre": lambda s: s["r0"] != 0},
    "simple_interest": {"inputs": ["principal", "rate", "years"],
                        "output": "interest", "equation": "I = P*r*t",
                        "expr": "p0 * r0 * y0", "domain": "finance",
                        # context guard: same input KINDS as compound growth,
                        # but the semantics differ — a capability may declare
                        # query-context exclusions (documented mechanism; the
                        # type system alone cannot see 'compound')
                        "context_exclude": ["compound"]},
    "interest_from_final": {"inputs": ["final_amount", "principal"],
                            "output": "interest", "equation": "I = A - P",
                            "expr": "f0 - p0", "domain": "finance"},
    "revenue_sale": {"inputs": ["sale_price", "count"], "output": "revenue",
                     "equation": "R = ps*n", "expr": "s0 * c0",
                     "domain": "finance"},
    # break-even output is its OWN kind: it is a hypothetical quantity, not
    # the actual units sold — typing it 'count' let the planner manufacture a
    # missing sales count and emit profit=0 on adversarial no-count items
    "break_even": {"inputs": ["fixed_cost", "price_per_unit", "unit_cost"],
                   "output": "count_breakeven", "equation": "n = F/(p-u)",
                   "expr": "f0 / (p0 - u0)", "domain": "finance",
                   "pre": lambda s: s["p0"] > s["u0"]},
    # ---- engineering / geometry ----
    "area_rect": {"inputs": ["length", "width"], "output": "area",
                  "equation": "A = l*w", "expr": "l0 * w0",
                  "domain": "engineering"},
    "volume_box": {"inputs": ["area", "height"], "output": "volume",
                   "equation": "V = A*h", "expr": "a0 * h0",
                   "domain": "engineering"},
    "mass_from_density": {"inputs": ["density", "volume"], "output": "mass",
                          "equation": "m = rho*V", "expr": "d0 * v0",
                          "domain": "engineering"},
    "material_cost": {"inputs": ["price_per_kg", "mass"],
                      "output": "cost_var", "equation": "Cv = pk*m",
                      "expr": "p0 * m0", "domain": "engineering"},
    "weight_from_mass": {"inputs": ["mass"], "output": "force",
                         "equation": "W = m*g", "expr": "m0 * 9.8",
                         "domain": "engineering"},
    "paint_cost": {"inputs": ["liters", "price_per_liter"],
                   "output": "cost_var", "equation": "C = L*pl",
                   "expr": "l0 * p0", "domain": "engineering"},
}

REGISTRY = {**PHYS, **FIN_ENG}

# variable naming for the shared executor (extends V0.3's scheme)
_KV = {"count": "c", "rate": "r", "years": "y", "price_per_unit": "p",
       "unit_cost": "u", "fixed_cost": "f", "revenue": "r",
       "cost_var": "c", "cost_total": "c", "profit": "p", "net_profit": "n",
       "sale_price": "s", "principal": "p", "interest": "i",
       "final_amount": "f", "length": "l", "width": "w", "area": "a",
       "density": "d", "price_per_kg": "p", "liters": "l",
       "price_per_liter": "p", "coverage_rate": "cv", "fx_rate": "x",
       "cost_eur": "e", "price_per_kwh": "p", "money": "m",
       # physics kinds consumed by engineering capabilities
       "mass": "m", "height": "h", "volume": "v", "energy": "e",
       "rate_tax": "r", "rate_discount": "r"}

# UNKNOWN capabilities: generator-only ground truth. NEVER in REGISTRY.
UNKNOWN_SPECS = {
    "tax_net": {"inputs": ["profit", "rate_tax"], "output": "net_profit",
                "truth": lambda s: s["profit"] * (1 - s["rate_tax"]),
                "nl": "after-tax profit = profit x (1 - tax rate)"},
    "discount_price": {"inputs": ["price_per_unit", "rate_discount"],
                       "output": "sale_price",
                       "truth": lambda s: s["price_per_unit"]
                       * (1 - s["rate_discount"]),
                       "nl": "sale price = price x (1 - discount)"},
    "paint_needed": {"inputs": ["area", "coverage_rate"], "output": "liters",
                     "truth": lambda s: s["area"] / s["coverage_rate"],
                     "nl": "liters = area / coverage per liter"},
    "compound_growth": {"inputs": ["principal", "rate", "years"],
                        "output": "final_amount",
                        "truth": lambda s: s["principal"]
                        * (1 + s["rate"]) ** s["years"],
                        "nl": "A = P (1+r)^t"},
    "kwh_cost": {"inputs": ["energy", "price_per_kwh"], "output": "cost_var",
                 "truth": lambda s: s["energy"] / 3.6e6
                 * s["price_per_kwh"],
                 "nl": "cost = (J / 3.6e6 kWh) x price per kWh"},
    "currency_convert": {"inputs": ["cost_total", "fx_rate"],
                         "output": "cost_eur",
                         "truth": lambda s: s["cost_total"] * s["fx_rate"],
                         "nl": "EUR = USD x fx rate"},
}

for u in UNKNOWN_SPECS:
    assert u not in REGISTRY, f"unknown capability leaked into registry: {u}"


def registry_hash(reg=None):
    reg = reg if reg is not None else REGISTRY
    spec = {k: {"inputs": v["inputs"], "output": v["output"],
                "equation": v["equation"]} for k, v in sorted(reg.items())}
    return hashlib.sha256(json.dumps(spec, sort_keys=True)
                          .encode()).hexdigest()


def save_registry(path, reg=None, version="v0"):
    reg = reg if reg is not None else REGISTRY
    doc = {"version": version, "hash": registry_hash(reg),
           "capabilities": {k: {"inputs": v["inputs"], "output": v["output"],
                                "equation": v["equation"],
                                "domain": v["domain"]}
                            for k, v in sorted(reg.items())}}
    Path(path).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc["hash"]


def execute(name, inputs, registry=None):
    """Shared deterministic executor for physics + new capabilities."""
    reg = registry if registry is not None else REGISTRY
    spec = reg[name]
    if name in PHYS:
        return _EX3_ORIGINAL(name, inputs)  # bound pre-patch; no recursion
    ns = {"math": math}
    counts = {}
    for kind in spec["inputs"]:
        base = _KV.get(kind, kind[:2])
        i = counts.get(base, 0)
        counts[base] = i + 1
        ns[f"{base}{i}"] = inputs[kind].value
    pre = spec.get("pre")
    if pre is not None:
        try:
            if not pre(ns):
                return None, False, f"precondition failed for {name}"
        except Exception as e:
            return None, False, f"precondition error: {e}"
    try:
        v = eval(spec["expr"], {"__builtins__": {}, "math": math}, ns)
    except Exception as e:
        return None, False, f"executor error: {e}"
    if not (isinstance(v, (int, float)) and math.isfinite(v)):
        return None, False, "non-finite"
    return float(v), True, "ok"
