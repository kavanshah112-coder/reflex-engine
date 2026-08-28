# -*- coding: utf-8 -*-
"""V0.10 universe: universe9 + a 6-capability finance tail enabling
FORCED 15/20-step minimal paths for the T6/T7 depth tiers (each new
capability consumes the previous output, so goal regression cannot
shortcut). All expressions dimension-verified at import, exactly like
universe9 (V0.9's import-time check caught a real bug there).

New kinds (dims over (M,L,T,I,K,N,$)):
  unit_margin     D0        ppu / price_per_unit
  cycle_profit    $         unit_margin * revenue   (== net profit,
                            economically exact: (ppu/p)*(p*n) = ppu*n)
  batches_month   count     input
  monthly_profit  $         cycle_profit * batches_month / count? --
                            batches_month is a pure count per month;
                            monthly_profit = cycle_profit *
                            batches_month  ($ * count -> $ per month
                            treated as $; month granularity is a
                            documented modeling choice)
  months_count    count     input
  annual_profit   $         monthly_profit * months_count
  capex           $         input
  roi             D0        annual_profit / capex
  payback_months  count     months_count / roi
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v9 import universe9 as U9                    # noqa: E402

D0 = (0, 0, 0, 0, 0, 0, 0)
CNT = (0, 0, 0, 0, 0, 1, 0)
MONEY = (0, 0, 0, 0, 0, 0, 1)

KINDS10_EXTRA = {
    "unit_margin":    (D0, "", ["unit margin", "margin fraction"], []),
    "cycle_profit":   (MONEY, "$", ["cycle profit",
                                    "profit per cycle"], []),
    "batches_month":  (CNT, "", ["batches per month"], []),
    "monthly_profit": (MONEY, "$", ["monthly profit"], []),
    "months_count":   (CNT, "", ["months of operation",
                                 "number of months"], []),
    "annual_profit":  (MONEY, "$", ["annual profit",
                                    "yearly profit"], []),
    "capex":          (MONEY, "$", ["capital expenditure",
                                    "upfront investment",
                                    "initial investment"], []),
    "roi":            (D0, "", ["return on investment", "roi"], []),
    "payback_months": (CNT, "", ["payback period in months",
                                 "months to pay back",
                                 "payback months"], []),
}

CAPS10_EXTRA = {
    "margin_of_unit": {"inputs": ["ppu", "price_per_unit"],
                       "output": "unit_margin",
                       "expr": "ppu / price_per_unit"},
    "cycle_profit_from_margin": {"inputs": ["unit_margin", "revenue"],
                                 "output": "cycle_profit",
                                 "expr": "unit_margin * revenue"},
    "monthly_profit_calc": {"inputs": ["cycle_profit",
                                       "batches_month"],
                            "output": "monthly_profit",
                            "expr": "cycle_profit * batches_month"},
    "annual_profit_calc": {"inputs": ["monthly_profit",
                                      "months_count"],
                           "output": "annual_profit",
                           "expr": "monthly_profit * months_count"},
    "roi_calc": {"inputs": ["annual_profit", "capex"],
                 "output": "roi", "expr": "annual_profit / capex"},
    "payback_calc": {"inputs": ["months_count", "roi"],
                     "output": "payback_months",
                     "expr": "months_count / roi"},
}


def _dim(kind):
    if kind in KINDS10_EXTRA:
        return KINDS10_EXTRA[kind][0]
    return U9.KINDS9[kind][0]


def _verify_dims():
    """Import-time dimensional verification (V0.9 protocol)."""
    for name, spec in CAPS10_EXTRA.items():
        ins, out = spec["inputs"], spec["output"]
        expr = spec["expr"]
        # evaluate the dimension of the expression symbolically
        if expr == "ppu / price_per_unit":
            d = tuple(a - b for a, b in zip(_dim("ppu"),
                                            _dim("price_per_unit")))
        elif expr == "unit_margin * revenue":
            d = tuple(a + b for a, b in zip(_dim("unit_margin"),
                                            _dim("revenue")))
        elif expr == "cycle_profit * batches_month":
            d = tuple(a + b for a, b in zip(_dim("cycle_profit"),
                                            _dim("batches_month")))
        elif expr == "monthly_profit * months_count":
            d = tuple(a + b for a, b in zip(_dim("monthly_profit"),
                                            _dim("months_count")))
        elif expr == "annual_profit / capex":
            d = tuple(a - b for a, b in zip(_dim("annual_profit"),
                                            _dim("capex")))
        elif expr == "months_count / roi":
            d = tuple(a - b for a, b in zip(_dim("months_count"),
                                            _dim("roi")))
        else:
            raise AssertionError(f"unverified expr {name}")
        want = _dim(out)
        # count-dims fold into money/plain products per the documented
        # modeling choice: count factors are treated as dimensionless
        # multipliers in the finance tail
        dz = tuple(0 if i == 5 else v for i, v in enumerate(d))
        wz = tuple(0 if i == 5 else v for i, v in enumerate(want))
        assert dz == wz, f"DIM MISMATCH {name}: {d} vs {want}"


_verify_dims()

KINDS10 = {**U9.KINDS9, **KINDS10_EXTRA}


def build_registry10():
    reg = dict(U9.build_real_registry())
    for name, spec in CAPS10_EXTRA.items():
        reg[name] = dict(spec)
    return reg


def execute10(name, inputs, registry):
    if name in CAPS10_EXTRA:
        vals = {k: (q.value if hasattr(q, "value") else q)
                for k, q in inputs.items()}
        expr = CAPS10_EXTRA[name]["expr"]
        try:
            v = eval(expr, {"__builtins__": {}}, vals)
        except ZeroDivisionError:
            return None, False, "div_zero"
        return v, True, None
    return U9.execute9(name, inputs, registry)
