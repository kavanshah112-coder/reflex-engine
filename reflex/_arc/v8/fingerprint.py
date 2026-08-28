# -*- coding: utf-8 -*-
"""V0.8 Structural Query Fingerprint (spec Section 6).

Converts a natural-language query into a normalized computational
representation:

    { quantities, kinds, target, target_candidates, relations, op_hints,
      signature, domain }

Design principles (registered in V08_PLAN + invention log H1/H2):
  * UNIT-FIRST: a number's kind comes from its unit/dimension wherever one
    exists — units generalize across arbitrary nouns/verbs (OOV-robust).
  * ROLE-FRAME second: money and bare lengths are disambiguated by
    structural role markers (per-X, to-<verb>, fixed/overhead, invest
    frames), not by enumerated noun lists.
  * NEVER override a specific kind produced by the frozen V0.4 parser
    (zero-regression rule, proven V0.6). Structural results may only
    (a) add quantities the base parser missed, (b) re-kind the generic
    kinds 'money' and 'distance', (c) resolve unit-context conflicts the
    base parser is known to get wrong ONLY via the thermal-pair rule
    below, which requires an explicit from..to thermal frame.
  * The fingerprint is pure recognition — no capability execution here.

All tables were designed from the capability registry + dev-distribution
phrasing conventions BEFORE any sealed dataset existed (Amendment A1).
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v3.ir import Quantity                       # noqa: E402
from v4.qparse4 import parse_quantities as pq4   # noqa: E402
from v4.qparse4 import asked_kind as ak4         # noqa: E402

NUM = r"(\d+(?:,\d{3})*(?:\.\d+)?)"

# ---------------------------------------------------------------- units
# (kind, regex, factor, note) — unit-first, noun-independent.
UNIT_TABLE = [
    ("mass", rf"{NUM}\s?(?:kg|kilograms?|kilos?)\b", 1.0, ""),
    ("mass", rf"{NUM}\s?(?:g|grams?)\b(?!/)", 1e-3, "g->kg"),
    ("mass", rf"{NUM}\s?(?:tonnes?|metric tons?|\bt\b)\b", 1e3, "t->kg"),
    ("speed", rf"{NUM}\s?(?:m/s|m s-1|meters? per second|metres? per second)",
     1.0, ""),
    ("speed", rf"{NUM}\s?(?:km/h|kph|kilometers? per hour)", 1 / 3.6,
     "km/h->m/s"),
    ("energy", rf"{NUM}\s?(?:kJ|kilojoules?)\b", 1e3, "kJ->J"),
    ("energy", rf"{NUM}\s?(?:MJ|megajoules?)\b", 1e6, "MJ->J"),
    ("energy", rf"{NUM}\s?(?:J\b|joules?)", 1.0, ""),
    ("energy", rf"{NUM}\s?(?:kWh|kilowatt.hours?)\b", 3.6e6, "kWh->J"),
    ("power", rf"{NUM}\s?(?:kW\b|kilowatts?)", 1e3, "kW->W"),
    ("power", rf"{NUM}\s?(?:W\b|watts?)", 1.0, ""),
    ("voltage", rf"{NUM}\s?(?:V\b|volts?)", 1.0, ""),
    ("current", rf"{NUM}\s?(?:A\b|amps?|amperes?)", 1.0, ""),
    ("resistance", rf"{NUM}\s?(?:ohms?|Ω)", 1.0, ""),
    ("charge", rf"{NUM}\s?(?:coulombs?)\b", 1.0, ""),
    ("time", rf"{NUM}\s?(?:seconds?|s\b|sec\b)", 1.0, ""),
    ("time", rf"{NUM}\s?(?:minutes?|min\b)", 60.0, "min->s"),
    ("time", rf"{NUM}\s?(?:hours?|hrs?\b|h\b)", 3600.0, "h->s"),
    ("years", rf"{NUM}\s?(?:years?|yr)\b", 1.0, ""),
    # coverage BEFORE area, both frame directions ('covers X m2 per liter'
    # is handled by the base parser; 'each liter covers X m2' is not)
    ("coverage_rate", rf"(?:liter|litre)[^.;]{{0,28}}covers?\s+{NUM}\s?"
     rf"(?:m²|m\^2|m2\b|square met\w*)", 1.0, ""),
    ("area", rf"{NUM}\s?(?:m²|m\^2|m2\b|square met\w*)", 1.0, ""),
    ("volume", rf"{NUM}\s?(?:m³|m\^3|m3\b|cubic met\w*)", 1.0, ""),
    ("density", rf"{NUM}\s?(?:kg/m³|kg/m\^3|kg/m3|kg per cubic)", 1.0, ""),
    ("liters", rf"{NUM}\s?(?:liters?|litres?|L\b)", 1.0, ""),
    ("force", rf"{NUM}\s?(?:N\b|newtons?)", 1.0, ""),
    ("length_m", rf"{NUM}\s?(?:m\b|meters?|metres?)", 1.0, ""),
    ("length_m", rf"{NUM}\s?(?:cm|centimet\w*)", 1e-2, "cm->m"),
    ("length_m", rf"{NUM}\s?(?:km|kilomet\w*)\b(?!/)", 1e3, "km->m"),
    ("temp_c", rf"{NUM}\s?(?:°C|° C|degrees?(?: C\b| Celsius)?|celsius)",
     1.0, ""),
]

# thermal frame: 'warms/heats/cools ... from X C to Y C' — reinterprets a
# C-pair (base parser: coulombs) as temperatures; requires the frame.
THERMAL_FRAME = re.compile(
    r"(?:heat\w*|warm\w*|cool\w*|temperat\w*|rais\w*|climbs?|rises?)",
    re.I)
FROMTO_C = re.compile(
    rf"from\s+{NUM}\s?(?:°C|C\b|degrees?)\s+(?:up\s+)?to\s+"
    rf"{NUM}\s?(?:°C|C\b|degrees?)", re.I)

# ------------------------------------------------------- length roles
LENGTH_ROLES = [
    ("height", r"tall|high\b|height|lift\w*|rais\w*|drop\w*|fall\w*|"
               r"above|elevat\w*|deep\b|hoist\w*|winch\w*"),
    ("length", r"long\b|length"),
    ("width", r"wide\b|width"),
    ("distance", r"travel\w*|mov\w*|push\w*|pull\w*|drag\w*|slid\w*|"
                 r"cover\w*|roll\w*|drives?\b|walks?\b|hauls?\b|tow\w*"),
]

# ------------------------------------------------------- money role frames
PER_UNIT_WORDS = {
    "kg": "price_per_kg", "kilogram": "price_per_kg", "kilo": "price_per_kg",
    "liter": "price_per_liter", "litre": "price_per_liter",
    "kwh": "price_per_kwh", "kilowatt-hour": "price_per_kwh",
    "kilowatt": "price_per_kwh",
}
MAKE_VERBS = (r"make|produce|manufactur\w*|build|craft|assembl\w*|brew|"
              r"grow|print|weld|cast|forge|stitch|carve|mold|bake|"
              r"fabricat\w*|bottle|pot\b|frame")
MONEY_GROUP = {"money", "price_per_unit", "unit_cost", "fixed_cost",
               "principal", "revenue", "cost_total", "cost_var",
               "sale_price", "price_per_kg", "price_per_liter",
               "price_per_kwh", "profit", "net_profit", "interest",
               "final_amount", "cost_eur"}
MONEY_FRAMES = [
    # ($ value already found; frame decides kind) — order = priority
    ("fixed_cost", r"fixed|overhead|rent\b|setup|base cost|standing"),
    ("profit", r"pockets?\b|clears?\b|rakes? in|nets?\b|profit of"),
    ("unit_cost", rf"(?:costs?|takes?|spends?)\s[^.;]{{0,24}}to\s"
                  rf"(?:{MAKE_VERBS})|each to\s|apiece to\s|"
                  rf"per (?:unit|item|piece) to\s|production cost|"
                  rf"cost per (?:unit|item|piece)|unit cost|to (?:{MAKE_VERBS})"),
    ("principal", r"invest\w*|deposit\w*|sav(?:es?|ings?)|principal|loan|"
                  r"stash\w*|put\w{0,4} (?:in|into)|account|grows|fund"),
    ("revenue", r"revenue|sales of|brings? in|takes? in"),
    ("cost_total", r"total cost|in total|altogether"),
    ("price_per_unit", r"each\b|apiece|per (?:unit|item|piece)|sells? for|"
                       r"sold (?:for|at)|is sold|sell\w* (?:them|these|each)|"
                       r"charg\w*|priced? at|asking|price of|goes for|"
                       r"go(?:es)? out the door|fetch\w*|commands?\b|"
                       r"retails? (?:at|for)"),
]

# ----------------------------------------------------------- count rule
UNIT_WORDS = set("""kg kilograms kilogram kilos g grams tonnes t m meters
metres cm km s seconds sec minutes min hours hrs h years yr J joules kJ
kilojoules MJ megajoules kWh W watts kW V volts A amps amperes ohms
liters litres L N newtons percent degrees celsius m² m³ dollars euros
usd eur coulombs""".lower().split())
COUNT_CTX = re.compile(r"sell|sold|make|made|produc|buy|bought|order|"
                       r"ship|manufactur|each|apiece|unit|batch|per\b|"
                       r"stock|craft|brew|grow|print|offer", re.I)
COUNT_PAT = re.compile(rf"{NUM}\s+([a-z]+)\b", re.I)

# ------------------------------------------------------- relation classes
RELATIONS = [
    ("motion", r"mov\w*|travel\w*|roll\w*|slid\w*|flies|fly\w*|drives?|"
               r"speeds?\b|velocit\w*|glides?|cruis\w*|zips?|races?"),
    ("lift", r"lift\w*|rais\w*|hoist\w*|drops?|fall\w*|elevat\w*|winch\w*|"
             r"tower|shelf|height|climb\w*"),
    ("thermal", r"heat\w*|warm\w*|cool\w*|temperat\w*|thermal|boil\w*|"
                r"stove|furnace|kettle|oven"),
    ("electrical", r"circuit|current|volt\w*|resist\w*|electr\w*|battery|"
                   r"appliance|heater|motor|bulb|charge\w*|amps?\b"),
    ("push", r"push\w*|pull\w*|drag\w*|tow\w*|force|friction|haul\w*"),
    ("commerce", r"sell\w*|sold|buy\w*|price|cost\w*|profit|revenue|"
                 r"margin|customer|shop|store|business|vendor|stall"),
    ("invest", r"invest\w*|interest|deposit\w*|account|principal|loan|"
               r"compound\w*|annual\w*|bank|fund|grows"),
    ("material", r"density|concrete|granite|steel|slab|block|beam|paint\w*|"
                 r"coat\w*|material|timber|marble|resin"),
    ("convert", r"euro|exchange|convert\w*|currency"),
    ("efficiency", r"efficien\w*|carnot|engine|reservoir"),
]

OP_HINTS = [
    ("compound", r"compound\w*|annually|each year .*(?:grows|increase)|"
                 r"per year compounded"),
    ("net", r"after.?tax|net\b"),
    ("discount", r"discount|% off|markdown|reduc\w* by"),
    ("breakeven", r"break.?even"),
    ("per", r"\bper\b|each\b|apiece"),
    ("total", r"total|altogether|combined|overall"),
    ("difference", r"warmer|hotter|cooler|rise\b|rises|increase\w*|"
                   r"change in|delta|gain\w*"),
]

# --------------------------------------------- question focus -> concept
# concept lexicon: surface phrase -> target kind (curated; may be merged
# with the V0.6 traffic-learned lexicon at recognizer level R5+)
FOCUS_LEX = [
    ("temp_diff", r"warmer|hotter|warming|temperature (?:rise|change|"
                  r"increase|climb)|rise in temperature|"
                  r"how much .*heat.* up|degrees? .*(?:rise|warm|gain)"),
    ("count_breakeven", r"break.?even"),
    ("net_profit", r"after.?tax profit|net profit|keep after tax|"
                   r"pocket after tax"),
    ("rate", r"margin|what percentage|what rate(?! of energy)|"
             r"what fraction"),
    ("final_amount", r"(?:worth|balance|value|grow to|amount) after|"
                     r"future value|end up with"),
    ("sale_price", r"sale price|discounted price|price after|final price|"
                   r"new price"),
    ("interest", r"interest|earn(?:ings)? (?:on|from)"),
    ("cost_eur", r"euros?\b|in eur\b"),
    ("energy", r"kinetic energy|potential energy|\benergy\b|work (?:is )?"
               r"(?:done|needed|required)|joules?|how much work"),
    ("power", r"\bpower\b|watts?|wattage|rate of energy "
              r"(?:draw|use|burn|consumption)|rate does .{0,16}burn"),
    ("voltage", r"voltage|volts?\b|potential difference"),
    ("current", r"current|amps?\b|amperes?"),
    ("resistance", r"resistance|ohms?"),
    ("charge", r"\bcharge\b|coulombs?"),
    ("efficiency", r"efficien\w*"),
    ("speed", r"speed|velocity|how fast"),
    ("force", r"\bforce\b|how hard|weigh\w*|weight"),
    ("height", r"how high|height|how far up|rise\b.*(?:m|meters)"),
    ("distance", r"how far\b|distance"),
    ("temp_diff", r"temperature"),
    ("mass", r"\bmass\b|how heavy|kilograms? (?:is|are|does)"),
    ("area", r"\barea\b"),
    ("volume", r"volume"),
    ("liters", r"liters?|litres?|how much paint"),
    ("count", r"how many"),
    ("profit", r"profit|earnings|left over|is cleared|do they clear"),
    ("revenue", r"revenue|total sales|take in|bring in"),
    ("time", r"how long|duration|seconds? (?:does|will|to)"),
    ("money", r"cost|spend|pay|much money|price\b|bill\b|charge for"),
]
QCLAUSE = re.compile(r"\b(?:how|what|find|compute|calculate|determine|"
                     r"work out|give)\b", re.I)

# nouns the concept layer KNOWS how to ask for; a question noun outside
# this set is evidence of an unrecognized concept -> inference must not
# fire (safety: never compute something other than what was asked)
KNOWN_FOCUS_NOUNS = set("""energy power voltage volts current resistance
charge efficiency speed velocity force weight height distance temperature
mass area volume liters litres paint profit revenue margin interest yield
balance cost costs price bill money earnings work wattage warming
kilograms joules watts amps ohms coulombs newtons euros degrees units
fraction percentage rate""".split())
FOCUS_NOUN_PAT = re.compile(
    r"(?:what|how much|how many)\s+(?:is\s+|are\s+)?(?:the\s+|its\s+|"
    r"a\s+)?([a-z]+(?:\s[a-z]+)?)", re.I)


def unknown_focus_noun(qseg, extra_words=()):
    """Return the unrecognized question noun, or None if the question
    noun is known / absent."""
    m = FOCUS_NOUN_PAT.search(qseg)
    if not m:
        return None
    words = [w for w in re.findall(r"[a-z]+", m.group(1).lower())
             if w not in STOP_FOCUS]
    if not words:
        return None
    known = KNOWN_FOCUS_NOUNS | set(extra_words)
    if any(w in known for w in words):
        return None
    return " ".join(words)


STOP_FOCUS = set("does do did will would can could of in on it that this "
                 "much many total final overall net".split())


def _mask(t, span):
    return t[:span[0]] + " " * (span[1] - span[0]) + t[span[1]:]


def structural_quantities(text):
    """Unit-first pass over the raw text. Returns list of dicts
    {kind, value, unit_note, span}. length_m/temp_c are provisional kinds
    resolved later by role/frame rules."""
    out = []
    work = text
    for kind, pat, factor, note in UNIT_TABLE:
        rx = re.compile(pat) if any(c.isupper() for c in pat) else \
            re.compile(pat, re.I)
        for m in list(rx.finditer(work)):
            val = float(m.group(1).replace(",", "")) * factor
            out.append({"kind": kind, "value": val, "note": note,
                        "span": m.span(), "raw": float(
                            m.group(1).replace(",", ""))})
            work = _mask(work, m.span())
    # money ($-sign or currency word: dimension-certain)
    for m in list(re.finditer(rf"\$\s?{NUM}|{NUM}\s?(?:dollars|usd)\b",
                              work, re.I)):
        g = m.group(1) or m.group(2)
        out.append({"kind": "money", "value": float(g.replace(",", "")),
                    "note": "", "span": m.span(), "raw": float(
                        g.replace(",", "")), "dollar_marked": True})
        work = _mask(work, m.span())
    # percent
    for m in list(re.finditer(rf"{NUM}\s?(?:%|percent)", work, re.I)):
        out.append({"kind": "percent",
                    "value": float(m.group(1).replace(",", "")) / 100,
                    "note": "%->fraction", "span": m.span(),
                    "raw": float(m.group(1).replace(",", ""))})
        work = _mask(work, m.span())
    # counts: number + plural token that is NOT a unit word
    for m in list(COUNT_PAT.finditer(work)):
        noun = m.group(2).lower()
        if noun in UNIT_WORDS or not noun.endswith("s") or len(noun) < 3:
            continue
        if COUNT_CTX.search(text):
            out.append({"kind": "count",
                        "value": float(m.group(1).replace(",", "")),
                        "note": f"count[{noun}]", "span": m.span(),
                        "raw": float(m.group(1).replace(",", ""))})
            work = _mask(work, m.span())
    return out, work


def resolve_roles(sq, text):
    """Resolve provisional kinds using role/frame rules."""
    low = text.lower()
    thermal = bool(THERMAL_FRAME.search(low))
    # thermal from-to pair
    ft = FROMTO_C.search(text)
    ft_vals = None
    if ft and thermal:
        ft_vals = (float(ft.group(1).replace(",", "")),
                   float(ft.group(2).replace(",", "")))
        # ensure the pair exists as temp quantities even when the unit was
        # a bare 'C' (which the unit table cannot claim: coulomb clash)
        have = {q["value"] for q in sq if q["kind"] == "temp_c"}
        for v in ft_vals:
            if v not in have:
                sq = sq + [{"kind": "temp_c", "value": v, "note": "bareC",
                            "span": ft.span(), "raw": v}]
    resolved = []
    for q in sq:
        k = q["kind"]
        if k == "length_m":
            # role words near the number decide height/length/width/distance
            lo = max(0, q["span"][0] - 60)
            ctx = low[lo:q["span"][1] + 60]
            kk = None
            for role, pat in LENGTH_ROLES:
                if re.search(pat, ctx, re.I):
                    kk = role
                    break
            if kk is None:
                for role, pat in LENGTH_ROLES:
                    if re.search(pat, low, re.I):
                        kk = role
                        break
            k = kk or "distance"
        elif k == "temp_c":
            if not thermal:
                continue  # a bare degree number without thermal frame:drop
            k = "temp_c"  # pair-resolved below
        elif k == "money":
            lo = max(0, q["span"][0] - 65)
            hi = q["span"][1] + 65
            seg = low[lo:hi]
            num_mid = q["span"][0] - lo
            # sentence-bound BOTH sides (v4 lesson: keywords must not leak
            # across '.' or ';')
            left = seg[:num_mid]
            cut = max(left.rfind("."), left.rfind(";"))
            if cut >= 0:
                seg = seg[cut + 1:]
                num_mid -= cut + 1
            right = seg[num_mid:]
            cuts = [i for i in (right.find("."), right.find(";")) if i >= 0]
            if cuts:
                seg = seg[:num_mid + min(cuts)]
            # per-X frame first (highest-precision structural marker)
            mm = re.search(r"per\s+([a-z-]+)|a\s+(kilogram|liter|litre)",
                           seg)
            kk = None
            if mm:
                w = (mm.group(1) or mm.group(2) or "").rstrip("s")
                kk = PER_UNIT_WORDS.get(w)
                if kk is None and w in ("unit", "item", "piece", "each"):
                    kk = "price_per_unit"
            hi_precision = kk is not None   # per-X frame
            if kk is None:
                # NEAREST frame wins (fine-bucketed distance, priority
                # only breaks exact-bucket ties)
                best = None  # (bucket, pri, dist, kind)
                for pri, (kind2, pat) in enumerate(MONEY_FRAMES):
                    for m2 in re.finditer(pat, seg, re.I):
                        mid = (m2.start() + m2.end()) / 2
                        dist = abs(mid - num_mid)
                        key = (int(dist // 6), pri, dist)
                        if best is None or key < best[:3]:
                            best = (*key, kind2)
                if best:
                    kk = best[3]
                    # frames precise enough to overrule the base parser:
                    # infinitive cost frames, profit verbs, sold-for
                    hi_precision = kk in ("unit_cost", "profit",
                                          "price_per_unit")
            k = kk or "money"
            q["hi_precision"] = bool(kk) and hi_precision
        elif k == "percent":
            near = low[max(0, q["span"][0] - 40):q["span"][1] + 35]
            k = ("rate_tax" if "tax" in near else
                 "rate_discount" if ("discount" in near or " off" in near)
                 else "rate")
        resolved.append({**q, "kind": k})
    # thermal pair -> temp_diff or hot/cold
    temps = [q for q in resolved if q["kind"] == "temp_c"]
    if ft_vals is not None and len(temps) >= 2:
        d = abs(ft_vals[1] - ft_vals[0])
        keep = [q for q in resolved if q["kind"] != "temp_c"]
        keep.append({"kind": "temp_diff", "value": d, "note": "from-to",
                     "span": temps[0]["span"], "raw": d})
        resolved = keep
    elif len(temps) == 1:
        temps[0]["kind"] = "temp_diff"
    elif len(temps) >= 2:
        # two temps without explicit from-to: hot/cold by magnitude
        a, b = temps[0], temps[1]
        hot, cold = (a, b) if a["value"] >= b["value"] else (b, a)
        hot["kind"], cold["kind"] = "temp_hot", "temp_cold"
        # carnot uses Kelvin; leave values as given (dev sets use K)
    return resolved


def question_focus(text, extra_lex=None):
    """Target-kind candidates from the question clause (ordered)."""
    segs = [s for s in re.split(r"[.?!]", text) if s.strip()]
    qseg = None
    for s in reversed(segs):
        if QCLAUSE.search(s) or s.strip().endswith("?"):
            qseg = s
            break
    if qseg is None:
        qseg = segs[-1] if segs else text
    low = qseg.lower()
    hits = []
    for kind, pat in FOCUS_LEX:
        m = re.search(pat, low)
        if m:
            hits.append((m.start(), m.end(), kind))
    for kind, pat in (extra_lex or []):
        m = re.search(pat, low)
        if m:
            hits.append((m.start(), m.end(), kind))
    # compound-noun head rule: when two matches OVERLAP ('profit margin'),
    # the head of an English noun compound is its LAST word — keep the
    # match with the later end, drop the earlier one
    drop = set()
    for i, (s1, e1, k1) in enumerate(hits):
        for j, (s2, e2, k2) in enumerate(hits):
            # overlap OR adjacency ('profit margin' = two adjacent
            # matches): the compound head is the LATER word
            if i != j and s2 < e1 + 2 and s1 < e2 + 2:
                if e1 < e2 or (e1 == e2 and s1 < s2):
                    drop.add(i)
    cands = [(s, k) for i, (s, e, k) in enumerate(hits) if i not in drop]
    # specific kinds outrank generic ones at any position ('how many
    # euros' asks for euros, not a count)
    generic = {"money", "count"}
    cands.sort(key=lambda sk: (1 if sk[1] in generic else 0, sk[0]))
    seen, out = set(), []
    for _, k in cands:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out, qseg


def fingerprint(text, extra_lex=None):
    """Full structural fingerprint. Merges base V0.4 parse (never
    overriding its specific kinds) with the structural pass."""
    base_qs, conv = pq4(text)
    base_ak = ak4(text)
    sq = resolve_roles(structural_quantities(text)[0], text)
    # merge: value-match against base quantities
    qs = [Quantity(kind=q.kind, value=q.value, unit=q.unit)
          for q in base_qs]
    used = set()
    adds, rekinds = [], []

    def _group(k):
        if k in MONEY_GROUP:
            return "money"
        if k in ("length", "width", "height", "distance", "length_m"):
            return "length"
        if k in ("temp_diff", "temp_hot", "temp_cold", "temp_c"):
            return "temp"
        return k

    for s in sq:
        # bind to the base quantity with matching VALUE, preferring
        # kind-identical, then group-compatible slots (a $3.0 price and
        # a 3 m width share a value — kind compatibility disambiguates)
        cands = []
        for j, q in enumerate(qs):
            if j in used:
                continue
            if (abs(q.value - s["value"]) < 1e-9 or
                    abs(q.value - s.get("raw", s["value"])) < 1e-9):
                compat = (0 if q.kind == s["kind"] else
                          1 if _group(q.kind) == _group(s["kind"]) else 2)
                cands.append((compat, j))
        bound = min(cands)[1] if cands else None
        if bound is None:
            qs.append(Quantity(kind=s["kind"], value=s["value"], unit=""))
            adds.append((s["kind"], s["value"]))
            used.add(len(qs) - 1)
        else:
            used.add(bound)
            generic_fix = (qs[bound].kind in ("money", "distance") and
                           s["kind"] not in ("money", "distance"))
            # narrow whitelisted structural corrections of known base-parser
            # systematic gaps (each requires a high-precision frame match)
            if (qs[bound].kind, s["kind"]) == ("area", "coverage_rate"):
                generic_fix = True
            # money-group INTERNAL override: an explicit structural frame
            # (per-X, to-<make-verb>, profit-verb, invest-frame) may
            # correct the base keyword guess WITHIN the money group only —
            # never across dimensional groups.
            money_fix = (qs[bound].kind in MONEY_GROUP and
                         s["kind"] in MONEY_GROUP and
                         s["kind"] != "money" and
                         s.get("hi_precision", False))
            # dimension-certainty: an explicit $-marked amount can never
            # be a count/mass/etc — the base parser mis-typed it
            if s.get("dollar_marked") and s["kind"] in MONEY_GROUP and \
                    qs[bound].kind not in MONEY_GROUP:
                money_fix = True
            if s["kind"] != qs[bound].kind and (generic_fix or money_fix):
                rekinds.append((qs[bound].kind, s["kind"], qs[bound].value))
                qs[bound] = Quantity(kind=s["kind"], value=qs[bound].value,
                                     unit=qs[bound].unit)
            # thermal-pair rule may override charge from bare 'C'
            elif qs[bound].kind == "charge" and s["kind"] in (
                    "temp_diff", "temp_hot", "temp_cold"):
                rekinds.append(("charge", s["kind"], qs[bound].value))
                qs[bound] = Quantity(kind=s["kind"], value=s["value"],
                                     unit="K")
    # drop exact-duplicate charge quantities replaced by a merged temp_diff
    kinds_now = [q.kind for q in qs]
    if "temp_diff" in kinds_now and kinds_now.count("charge") >= 1 and \
            THERMAL_FRAME.search(text.lower()) and FROMTO_C.search(text):
        qs = [q for q in qs if q.kind != "charge"]
    relations = [name for name, pat in RELATIONS
                 if re.search(pat, text, re.I)]
    hints = [name for name, pat in OP_HINTS if re.search(pat, text, re.I)]
    focus, qseg = question_focus(text, extra_lex)
    target = focus[0] if focus else base_ak
    kinds = sorted(q.kind for q in qs)
    sig = hashlib.sha256(json.dumps(
        [kinds, target or "?"]).encode()).hexdigest()[:16]
    return {"quantities": qs, "conversions": conv, "kinds": kinds,
            "base_ask": base_ak, "target": target,
            "target_candidates": focus, "relations": relations,
            "op_hints": hints, "signature": sig, "qseg": qseg,
            "adds": adds, "rekinds": rekinds}
