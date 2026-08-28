"""Typed quantity parser: text -> Quantity[] with semantic KINDS, plus
non-canonical unit conversion (logged as unit_conversion capability steps) and
asked-kind detection. Derived from the V0.2 binder machinery; the deltas are
kind assignment (mass vs just 'kg') and canonicalizing conversions.
"""
import re

from v3.ir import Quantity

_NUM = re.compile(r"(-?\d+(?:\.\d+)?)\s*([A-Za-zΩ°µ²³/()·^\.\*%]*)")

# (unit regex, kind, factor-to-canonical, canonical unit). Order matters.
UNIT_TABLE = [
    (r"m/s(?:²|\^2|\b2)", "accel", 1.0, "m/s^2"),
    (r"J/\(?kg", "spec_heat", 1.0, "J/(kg*K)"),
    (r"m/s", "speed", 1.0, "m/s"),
    (r"km/h", "speed", 1 / 3.6, "m/s"),
    (r"\bkJ\b", "energy", 1000.0, "J"),
    (r"\bJ\b|(?i:\bjoule)", "energy", 1.0, "J"),
    (r"\bkW\b", "power", 1000.0, "W"),
    (r"\bW\b|(?i:\bwatt)", "power", 1.0, "W"),
    (r"\bmA\b", "current", 0.001, "A"),
    (r"\bA\b|(?i:\bamp)", "current", 1.0, "A"),
    (r"\bkV\b", "voltage", 1000.0, "V"),
    (r"\bV\b|(?i:\bvolt)", "voltage", 1.0, "V"),
    (r"kΩ|(?i:\bkiloohm|\bkohm)", "resistance", 1000.0, "ohm"),
    (r"Ω|(?i:\bohm)", "resistance", 1.0, "ohm"),
    (r"\bC\b|(?i:\bcoulomb)", "charge", 1.0, "C"),
    (r"\bK\b|(?i:\bkelvin)", "temp", 1.0, "K"),
    (r"°C|(?i:\bdegree)", "temp", 1.0, "K"),   # diffs only; abs °C not used
    (r"\bkg\b|(?i:\bkilogram)", "mass", 1.0, "kg"),
    # grams: word form anywhere, single-letter 'g' only immediately after the
    # number (otherwise '(g = 9.8...)' constants match)
    (r"(?i:\bgram)|^\s?g\b", "mass", 0.001, "kg"),
    (r"\bN\b|(?i:\bnewton)", "force", 1.0, "N"),
    (r"(?i:\bhour|\bhr\b)", "time", 3600.0, "s"),
    (r"(?i:\bminute|\bmin\b)", "time", 60.0, "s"),
    (r"(?<!')\bs\b|(?i:\bsec|second)", "time", 1.0, "s"),
    (r"\bkm\b", "length", 1000.0, "m"),
    (r"\bcm\b", "length", 0.01, "m"),
    (r"\bm\b|(?i:\bmeter|\bmetre)", "length", 1.0, "m"),
    (r"%|(?i:\bpercent)", "efficiency", 0.01, ""),
]

_HEIGHT_KW = ["fall", "falls", "fell", "drop", "height", "high", "above",
              "raised", "lift", "lifts", "descend", "tall", "up ", "ledge",
              "cliff", "tumble", "slip", "waterfall", "hoist", "haul",
              "raise", "upward", "climb"]
_DIST_KW = ["drag", "push", "pull", "travel", "move", "across", "along",
            "distance", "slide", "displac"]
_HOT_KW = ["hot", "high", "source", "input"]
_COLD_KW = ["cold", "low", "sink", "reject"]
_DIFF_KW = ["rise", "increase", "change", "by", "warms", "difference"]

_EXCLUDED = {9.8}


def parse_quantities(text):
    """Returns (quantities, conversions). Conversion steps are logged so the
    unit_conversion capability appears in the executed path."""
    out, conversions = [], []
    prev_end = 0
    temps = []
    for m in _NUM.finditer(text):
        val = float(m.group(1))
        if val in _EXCLUDED:
            prev_end = m.end(1)
            continue
        tail = text[m.end(1):m.end(1) + 14]
        nd = re.search(r"\d", tail)
        if nd:
            tail = tail[:nd.start()]
        elif (len(tail) == 14 and len(text) > m.end(1) + 14
              and text[m.end(1) + 14].isalpha()):
            tail = re.sub(r"[A-Za-z]+$", "", tail)
        kind, factor, cunit = None, 1.0, ""
        for pat, k, f, cu in UNIT_TABLE:
            if re.search(pat, tail):
                kind, factor, cunit = k, f, cu
                break
        if kind is None:
            prev_end = m.end(1)
            continue
        ctx = text[max(prev_end, m.start(1) - 45):m.start(1)].lower()
        ctx_after = text[m.end(1):m.end(1) + 30].lower()
        # length disambiguation may look at the whole preceding clause: the
        # binary height-vs-distance call needs verbs that often sit before an
        # earlier number ("lifts a 36 kg load 5 m")
        ctx_wide = text[max(0, m.start(1) - 90):m.start(1)].lower()
        cval = val * factor
        if factor != 1.0:
            conversions.append(f"unit_conversion[{m.group(2) or tail.strip()}"
                               f"->{cunit}]")
        if kind == "length":
            kind = ("height" if any(k in ctx_wide or k in ctx_after
                                    for k in _HEIGHT_KW) else
                    "distance" if any(k in ctx_wide or k in ctx_after
                                      for k in _DIST_KW) else "distance")
        if kind == "temp":
            if any(k in ctx for k in _DIFF_KW) or "°c" in tail.lower():
                kind = "temp_diff"
            else:
                temps.append((len(out), cval, ctx))
        out.append(Quantity(kind=kind, value=cval, unit=cunit))
        prev_end = m.end(1)
    # resolve absolute temperature pairs into hot/cold
    if len(temps) >= 2:
        (i1, v1, c1), (i2, v2, c2) = temps[0], temps[1]
        hot_first = (v1 >= v2)
        if any(k in c1 for k in _COLD_KW) and not any(k in c1 for k in _HOT_KW):
            hot_first = False
        if any(k in c1 for k in _HOT_KW):
            hot_first = True
        out[i1].kind = "temp_hot" if hot_first else "temp_cold"
        out[i2].kind = "temp_cold" if hot_first else "temp_hot"
    elif len(temps) == 1:
        i1, v1, c1 = temps[0]
        out[i1].kind = "temp_diff"  # single temperature in our tasks = a delta
    return out, conversions


_ASK = [
    ("temp_diff", r"temperature|Δt\b|delta t|how hot|how warm|hotter|warmer"),
    ("height", r"height|how high|how far up|lift"),
    ("speed", r"speed|velocity|how fast"),
    ("efficiency", r"efficiency"),
    ("charge", r"\bcharge\b"),
    ("current", r"current"),
    ("voltage", r"voltage|potential difference|\bemf\b"),
    ("resistance", r"resistance"),
    ("power", r"\bpower\b|\bp\b"),
    ("force", r"\bforce\b"),
    ("time", r"how long|\btime\b|duration"),
    ("distance", r"how far|distance"),
    ("energy", r"energy|\bwork\b(?!\s+out)|\bheat\b|joule|\bke\b|\bpe\b"),
]
_QVERB = re.compile(r"\b(what|find|calculate|determine|compute|how)\b", re.I)


def asked_kind(text):
    segs = [s for s in re.split(r"[.?!]", text) if s.strip()]
    for t in ([segs[-1]] if segs else []) + [text]:
        low = t.lower()
        m = _QVERB.search(low)
        region = low[m.start():] if m else low
        best = None
        for kind, pat in _ASK:
            mm = re.search(pat, region)
            if mm and (best is None or mm.start() < best[0]):
                best = (mm.start(), kind)
        if best:
            kind = best[1]
            # rate modifier: 'heat per second' etc. is a POWER question
            if kind == "energy" and re.search(
                    r"per second|each second|per unit time", region):
                kind = "power"
            return kind
    # last resort: first kind keyword anywhere in the text
    low = text.lower()
    best = None
    for kind, pat in _ASK:
        mm = re.search(pat, low)
        if mm and (best is None or mm.start() < best[0]):
            best = (mm.start(), kind)
    return best[1] if best else None
