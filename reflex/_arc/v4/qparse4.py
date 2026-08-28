"""V0.4 typed parser: finance/engineering pre-pass (money-kind keyword
disambiguation, %, years, counts, areas, densities, fx) + masked delegation to
the frozen V0.3 physics parser. Extended asked-kind detection."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import v4.registry_v4  # noqa: F401,E402  (installs NEW_KINDS into ir3)

from v3.ir import Quantity                     # noqa: E402
from v3 import qparse as q3                    # noqa: E402

_MONEY = re.compile(r"\$\s?(\d+(?:,\d{3})*(?:\.\d+)?)")
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s?(?:%|percent)")
_NUM_UNIT = [
    ("years", re.compile(r"(\d+(?:\.\d+)?)\s?(?:years?|yr)\b", re.I)),
    ("count", re.compile(r"(\d+(?:,\d{3})*)\s?(?:units?|items?|widgets?|"
                         r"pieces?|lamps?|chairs?|shirts?|products?|goods|"
                         r"boxes)\b", re.I)),
    # coverage BEFORE area: 'covers 15 m² per liter' is a rate, not an area
    ("coverage_rate", re.compile(r"cover\w*\s+(\d+(?:\.\d+)?)\s?(?:m²|m\^2|"
                                 r"square met\w*)[^.]{0,16}per lit", re.I)),
    ("area", re.compile(r"(\d+(?:\.\d+)?)\s?(?:m²|m\^2|square met)", re.I)),
    ("volume", re.compile(r"(\d+(?:\.\d+)?)\s?(?:m³|m\^3|cubic met)", re.I)),
    ("density", re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s?kg/m", re.I)),
    ("liters", re.compile(r"(\d+(?:\.\d+)?)\s?(?:liters?|litres?|L\b) of",
                          re.I)),
    ("fx_rate", re.compile(r"(?:exchange rate of|1 dollar (?:is|=)|= )\s?"
                           r"(\d+(?:\.\d+)?)\s?euro", re.I)),
]
_MONEY_KIND = [
    ("price_per_kg", ["per kg", "per kilogram", "a kilogram"]),
    ("price_per_liter", ["per liter", "per litre", "a liter"]),
    ("price_per_kwh", ["per kwh", "per kilowatt"]),
    # specific markers OUTRANK the production/price groups on near-ties:
    # in "$5 each to produce, $5936 fixed costs" both 'to produce' and
    # 'fixed' land in the same distance bucket around $5936
    ("fixed_cost", ["fixed"]),
    ("principal", ["invest", "deposit", "principal", "loan", "saves",
                   "savings of", "grows"]),
    ("revenue", ["revenue"]),
    ("cost_total", ["total cost"]),
    ("unit_cost", ["to make", "to produce", "to manufacture",
                   "cost per unit", "costs per unit", "unit cost",
                   "each to"]),
    ("price_per_unit", ["each", "per unit", "sells for", "sell for",
                        "charges", "price of", "apiece", "sale price",
                        "selling price", "priced at"]),
]
_RATE_CTX = ["tax", "discount", "interest", "margin", "rate", "grow",
             "growth", "off"]
_THICK = re.compile(r"(\d+(?:\.\d+)?)\s?(?:m|cm)\s+thick", re.I)


def _mask(text, span):
    return text[:span[0]] + " " * (span[1] - span[0]) + text[span[1]:]


def parse_quantities(text):
    out, conversions = [], []
    work = text
    # thickness -> height (before physics pass would call it distance)
    m = _THICK.search(work)
    if m:
        v = float(m.group(1))
        if "cm" in m.group(0):
            v /= 100
            conversions.append("unit_conversion[cm->m]")
        out.append(Quantity(kind="height", value=v, unit="m"))
        work = _mask(work, m.span())
    for kind, pat in _NUM_UNIT:
        for m in list(pat.finditer(work)):
            out.append(Quantity(kind=kind,
                                value=float(m.group(1).replace(",", "")),
                                unit=""))
            work = _mask(work, m.span())
    for m in list(_PCT.finditer(work)):
        ctx = work[max(0, m.start() - 55):m.end() + 40].lower()
        if any(k in ctx for k in _RATE_CTX):
            # subkind by nearest context: tax vs discount vs generic rate
            near = work[max(0, m.start() - 30):m.end() + 25].lower()
            kind = ("rate_tax" if "tax" in near else
                    "rate_discount" if ("discount" in near or " off" in near)
                    else "rate")
            out.append(Quantity(kind=kind, value=float(m.group(1)) / 100,
                                unit=""))
            conversions.append("unit_conversion[%->fraction]")
            work = _mask(work, m.span())
    for m in list(_MONEY.finditer(work)):
        val = float(m.group(1).replace(",", ""))
        lo, hi = max(0, m.start() - 55), m.end() + 55
        # sentence-bound context: keywords must not leak across '.' or ';'
        seg = work[lo:hi]
        left = seg[:m.start() - lo]
        cut = max(left.rfind("."), left.rfind(";"))
        if cut >= 0:
            lo = lo + cut + 1
        right = work[m.end():hi]
        cut2 = min([i for i in (right.find("."), right.find(";"))
                    if i >= 0] or [len(right)])
        hi = m.end() + cut2
        ctx = work[lo:hi].lower()
        # NEAREST keyword wins (not list order): '$4785' next to 'total cost'
        # must not be claimed by a distant 'revenue'
        # distance-BUCKETED nearest keyword: near-ties resolve by priority so
        # '$9 each to produce' binds unit_cost, not price ('each' adjacent)
        best = None  # (dist_bucket, priority, dist, kind)
        num_mid = m.start() - lo
        for pri, (k, kws) in enumerate(_MONEY_KIND):
            for w in kws:
                j = ctx.find(w)
                while j >= 0:
                    dist = abs(j + len(w) / 2 - num_mid)
                    key = (int(dist // 10), pri, dist)
                    if best is None or key < best[:3]:
                        best = (*key, k)
                    j = ctx.find(w, j + 1)
        kind = best[3] if best else "money"
        out.append(Quantity(kind=kind, value=val, unit="$"))
        work = _mask(work, m.span())
    # length/width from remaining "X m long / X m in length"
    for kind, kw in [("length", r"long|length"), ("width", r"wide|width")]:
        pat = re.compile(rf"(\d+(?:\.\d+)?)\s?m\s+(?:in\s+)?(?:{kw})", re.I)
        for m in list(pat.finditer(work)):
            out.append(Quantity(kind=kind, value=float(m.group(1)),
                                unit="m"))
            work = _mask(work, m.span())
    # physics pass on the masked remainder
    phys, conv3 = q3.parse_quantities(work)
    out.extend(phys)
    conversions.extend(conv3)
    return out, conversions


_ASK4 = [
    ("rate", r"after.?tax margin|\bmargin\b|what percentage|what rate"),
    ("net_interest", r"after.?tax interest"),
    ("sale_price", r"sale price|final price|price after"),
    ("net_profit", r"after.?tax profit|net profit|after.?tax\b"),
    ("profit", r"\bprofit\b"),
    ("revenue", r"revenue"),
    ("interest", r"\binterest\b|how much.*earn"),
    ("count_breakeven", r"break.?even"),
    ("count", r"how many units|how many .*(sell|make)"),
    ("liters", r"how (?:much|many) (?:paint|liters|litres)|"
               r"needed in liters"),
    ("cost_var", r"cost of (?:the )?(?:paint|material|electricity|energy)"),
    ("money", r"total cost|how much (?:money|will it cost|does it cost)|"
              r"\bcost\b|spend|worth"),
    ("area", r"\barea\b"),
    ("mass", r"\bmass\b|how heavy"),
] + [(k, p) for k, p in q3._ASK]   # physics asks compete positionally too


def asked_kind(text):
    low_all = text.lower()
    segs = [s for s in re.split(r"[.?!]", text) if s.strip()]
    for t in ([segs[-1]] if segs else []) + [text]:
        low = t.lower()
        # euro override: any euro mention in the question means cost_eur
        if "euro" in low:
            return "cost_eur"
        # 'worth/balance after N years' asks for the FUTURE VALUE, not a
        # generic money amount ('how much money' would win positionally)
        if re.search(r"(?:worth|balance) after", low):
            return "final_amount"
        # break-even questions ask for the hypothetical break-even quantity,
        # not a sales count ('how many units' would win positionally)
        if re.search(r"break.?even", low):
            return "count_breakeven"
        m = q3._QVERB.search(low)
        region = low[m.start():] if m else low
        best = None
        for kind, pat in _ASK4:
            mm = re.search(pat, region)
            if mm and (best is None or mm.start() < best[0]):
                best = (mm.start(), kind)
        if best:
            return best[1]
    if "euro" in low_all:
        return "cost_eur"
    return q3.asked_kind(text)
