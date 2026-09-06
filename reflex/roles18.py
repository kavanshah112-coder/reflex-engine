# -*- coding: utf-8 -*-
# origin: new for V1.8 -- deterministic role resolution (SPEC 4, 4.1)
"""Every stated number in a question gets a ROLE, by a fixed function
of the text and nothing else: no model is called here (SPEC 4.1, risk
R3). The binder and the usage-accounting gate G-P4' both read roles
from this module, so a role means one thing everywhere.

    analyze(text) -> Roles
        .steps     the question's clauses (composer17's splitter)
        .skeleton  the text with every stated number's digits -> '#'
                   (signs and unit exponents kept: structure, not
                   value)
        .tokens    [Token] one per stated number, in text order
        .unique    tokens minus benign repeats (same value, same UNIT
                   cue, same clause counts once -- R4)

A Token carries (step, cue, value, ordinal, raw, dup). Cues:
    unit:<u>   number adjacent to a unit word (kg, %, years, $, ...)
    at         'at x = N'            range_lo/range_hi  'from A to B',
    factor     'multiply ... by N'                       'for k = A to B'
    addend     'add N to', 'subtract N from', 'increase ... by N'
    threshold  'greater than N', 'exceeds N', ...
    choose_n/choose_r   'N choose R'
    pair_a/pair_b       'gcd of A and B'
    rhs        '... = N' closing an equation clause
    expr       a coefficient/operand inside an expression clause
    bare       unresolved -- the cue grammar cannot read this number

ordinal = position among tokens with the same (step, cue), so a slot
marker '$s<step>|<cue>|<ordinal>' names exactly one number of a
question whose skeleton matches the donor's.

SLOT_ROLE maps every planschema17 literal slot the four V1.7 models
used (6,757 admitted plans, all conventional) to the cue it may bind;
a slot outside the table is UNROLLED and the plan abstains.
"""
import re
from collections import namedtuple

from .composer17 import _steps as _composer_steps
from .gateway16 import _VALUE_NUM

Token = namedtuple("Token", "step cue value ord raw dup pos")

_NUM = r"(-?\d+(?:\.\d+)?)"

UNIT_CANON = {
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "g": "g", "gram": "g", "grams": "g",
    "m/s^2": "m/s^2", "m/s²": "m/s^2",
    "m/s": "m/s", "km/h": "km/h", "kph": "km/h",
    "kn": "kN", "kj": "kJ", "kilojoule": "kJ", "kilojoules": "kJ",
    "j": "J", "joule": "J", "joules": "J",
    "n": "N", "newton": "N", "newtons": "N",
    "v": "V", "volt": "V", "volts": "V",
    "a": "A", "amp": "A", "amps": "A", "ampere": "A", "amperes": "A",
    "w": "W", "watt": "W", "watts": "W",
    "ohm": "ohm", "ohms": "ohm", "ω": "ohm",
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "km": "km", "cm": "cm",
    "s": "s", "sec": "s", "second": "s", "seconds": "s",
    "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours",
    "minute": "minutes", "minutes": "minutes", "min": "minutes",
    "%": "%", "percent": "%",
    "year": "years", "years": "years", "yr": "years", "yrs": "years",
    "dollar": "$", "dollars": "$", "usd": "$",
}
_UNIT_ALT = "|".join(re.escape(u) for u in
                     sorted(UNIT_CANON, key=len, reverse=True))
_UNIT_AFTER = re.compile(r"%s\s*(?P<u>%s)(?![\w/^])" % (_NUM, _UNIT_ALT),
                         re.I)
_DOLLAR_BEFORE = re.compile(r"\$\s*%s" % _NUM)

# keyword cues, tried in order on tokens not claimed by a unit
_KEYWORD_CUES = [
    (re.compile(r"\bat\s+[a-z]\s*=\s*%s" % _NUM, re.I), ["at"]),
    (re.compile(r"\bfor\s+[a-z]\s*=\s*%s\s+to\s+%s" % (_NUM, _NUM),
                re.I), ["range_lo", "range_hi"]),
    (re.compile(r"\bfrom\s+%s\s+to\s+%s" % (_NUM, _NUM), re.I),
     ["range_lo", "range_hi"]),
    (re.compile(r"%s\s+choose\s+%s" % (_NUM, _NUM), re.I),
     ["choose_n", "choose_r"]),
    (re.compile(r"\b(?:gcd|lcm|greatest common divisor|least common "
                r"multiple|highest common factor|hcf)\s+of\s+%s\s+and"
                r"\s+%s" % (_NUM, _NUM), re.I), ["pair_a", "pair_b"]),
    (re.compile(r"\b(?:greater|larger|bigger|more|less|smaller|fewer|"
                r"lower|higher)\s+than\s+%s" % _NUM, re.I),
     ["threshold"]),
    (re.compile(r"\b(?:exceeds?|at\s+least|at\s+most|below|above)\s+%s"
                % _NUM, re.I), ["threshold"]),
    (re.compile(r"\b(?:add|plus)\s+%s" % _NUM, re.I), ["addend"]),
    (re.compile(r"\bsubtract\s+%s" % _NUM, re.I), ["addend"]),
    (re.compile(r"\bminus\s+%s" % _NUM, re.I), ["addend"]),
    (re.compile(r"\b(?:increas|decreas|reduc|rais)\w*\b[^.;]*?\bby\s+%s"
                % _NUM, re.I), ["addend"]),
    (re.compile(r"\b(?:multipl|divid|scal)\w*\b[^.;]*?\bby\s+%s" % _NUM,
                re.I), ["factor"]),
    (re.compile(r"=\s*%s\s*$" % _NUM), ["rhs"]),
]
_EXPR_CTX = re.compile(r"\b(?:root|derivative|integral|sum|limit)\s+of\b"
                       r"|\d\s*\(|[a-z]\^|\*\*|\^|\*|\d\s*[a-z]\b", re.I)

# ---------------------------------------------------------------------
# plan-side slot roles (frozen table, SPEC 12 implementation note)
SLOT_ROLE = {
    ("formula", "m"): "unit:kg", ("formula", "r"): "unit:%",
    ("formula", "t"): "unit:years", ("formula", "a"): "unit:m/s^2",
    ("formula", "v"): "unit:m/s", ("formula", "h"): "unit:m",
    ("formula", "d"): "unit:m", ("formula", "p"): "unit:$",
    ("formula", "f"): "unit:N", ("formula", "i"): "unit:A",
    ("scale", "by"): "factor",
    ("derivative_at", "point"): "at",
    ("integrate_def", "a"): "range_lo", ("integrate_def", "b"): "range_hi",
    ("sum_finite", "a"): "range_lo", ("sum_finite", "b"): "range_hi",
    ("ncr", "n"): "choose_n", ("ncr", "r"): "choose_r",
    ("npr", "n"): "choose_n", ("npr", "r"): "choose_r",
    ("gcd", "a"): "pair_a", ("gcd", "b"): "pair_b",
    ("lcm", "a"): "pair_a", ("lcm", "b"): "pair_b",
    ("compare", "b"): "threshold",
    ("solve_pick", "rhs"): "rhs",
}
# slots whose literal is word-derived, never a stated number
STRUCTURAL_SLOTS = {("derivative_at", "order")}
# ops whose expr-like strings carry operands that must be stated
EXPR_OPS = {"evaluate", "solve_pick", "derivative_at", "integrate_def",
            "sum_finite", "limit"}
EXPR_KEYS = ("expr", "lhs", "rhs")
EXPR_TOKEN_CUES = {"expr", "addend", "rhs"}
NON_SLOT_KEYS = {"id", "op", "from", "to", "var", "pick", "unit",
                 "order", "expr", "lhs", "rhs"}

# numbers inside a plan expression, exponents excluded ('x**2', 'x^2')
_EXPR_NUM = re.compile(r"(?<!\*\*)(?<!\^)(?<![\w.])(\d+(?:\.\d+)?)")


def expr_numbers(s):
    """[(start, end, magnitude_str)] of operand numbers in a plan
    expression string, exponents excluded."""
    return [(m.start(1), m.end(1), m.group(1)) for m in
            _EXPR_NUM.finditer(s)]


class Roles(object):
    __slots__ = ("text", "steps", "skeleton", "tokens", "unique")

    def __init__(self, text, steps, skeleton, tokens, unique):
        self.text, self.steps, self.skeleton = text, steps, skeleton
        self.tokens, self.unique = tokens, unique

    def bare(self):
        return [t for t in self.unique if t.cue == "bare"]

    def find(self, step, cue, ordinal):
        for t in self.unique:
            if t.step == step and t.cue == cue and t.ord == ordinal:
                return t
        return None


def steps_of(text):
    return [p.strip(" .;?") for p in _composer_steps(text)
            if p.strip(" .;?")]


def skeleton_of(text):
    def rep(m):
        s = m.group(1)
        return ("-#" if s.startswith("-") else "#")
    return _VALUE_NUM.sub(rep, text).strip()


def _tokens_in_step(si, step):
    nums = [(m.start(1), m.end(1), m.group(1))
            for m in _VALUE_NUM.finditer(step)]
    if not nums:
        return []
    claimed = {}
    # 1. unit cues
    for m in _UNIT_AFTER.finditer(step):
        claimed.setdefault(m.start(1), "unit:" +
                           UNIT_CANON[m.group("u").lower()])
    for m in _DOLLAR_BEFORE.finditer(step):
        claimed.setdefault(m.start(1), "unit:$")
    # 2. keyword cues in order; first cue wins a number
    for rx, cues in _KEYWORD_CUES:
        for m in rx.finditer(step):
            for gi, cue in enumerate(cues, start=1):
                claimed.setdefault(m.start(gi), cue)
    # 3. expression context for the rest
    is_expr = bool(_EXPR_CTX.search(step))
    toks = []
    counts = {}
    for st, en, raw in nums:
        cue = claimed.get(st)
        if cue is None:
            cue = "expr" if is_expr else "bare"
        mag = raw.lstrip("-")
        val = float(mag)
        k = (cue,)
        counts[k] = counts.get(k, 0)
        toks.append([si, cue, val, counts[k], mag, False, st])
        counts[k] += 1
    # benign repeats: same value beside the same UNIT in one clause
    seen = set()
    for t in toks:
        if t[1].startswith("unit:"):
            key = (t[1], t[2])
            if key in seen:
                t[5] = True
            seen.add(key)
    # re-number ordinals over non-dup tokens only
    counts = {}
    out = []
    for t in toks:
        if t[5]:
            out.append(Token(t[0], t[1], t[2], -1, t[4], True, t[6]))
            continue
        c = counts.get(t[1], 0)
        counts[t[1]] = c + 1
        out.append(Token(t[0], t[1], t[2], c, t[4], False, t[6]))
    return out


def analyze(text):
    steps = steps_of(text)
    tokens = []
    for si, s in enumerate(steps):
        tokens.extend(_tokens_in_step(si, s))
    unique = [t for t in tokens if not t.dup]
    return Roles(text, steps, skeleton_of(text), tokens, unique)


def slot_role(op, key):
    """-> cue string, 'STRUCTURAL', or None (unrolled)."""
    if (op, key) in STRUCTURAL_SLOTS:
        return "STRUCTURAL"
    return SLOT_ROLE.get((op, key))


def compatible(cue, role):
    """May a token with `cue` fill a slot whose role is `role`?
    'bare' tokens are the cue grammar's blind spot: they may fill any
    slot (magnitude-only, V1.7's level), and the transcript says so."""
    if cue == "bare":
        return True
    if role == "EXPR":
        return cue in EXPR_TOKEN_CUES
    return cue == role


if __name__ == "__main__":
    import json
    DEMO = [
        "Take the first derivative of 1x^3 -3x^2 at x = 4. Using that "
        "as a principal in dollars, find the simple interest at 2% "
        "per year over 6 years.",
        "Compute 2(6 + 3). Using that as a principal in dollars, find "
        "the simple interest at 2% per year over 6 years. Multiply "
        "that by 3, in $.",
        "Compute the lcm of 162 and 373. Multiply the result by 6. Is "
        "the final value greater than 1812.78?",
        "Find the integral of 2x^2 + 3x from 0 to 3. Using that as the "
        "speed in m/s of a 10 kg mass, find the kinetic energy. "
        "Express the result in kJ from J.",
        "Compute the sum of 2k - 1 for k = 1 to 25. Subtract 7 from "
        "that. Multiply that by 3.",
        "A 40 kg crate -- yes, 40 kg -- moves at 3 m/s; find its "
        "kinetic energy.",
    ]
    for q in DEMO:
        r = analyze(q)
        print("---", r.skeleton)
        for t in r.tokens:
            print("   ", json.dumps(t._asdict()))
