# -*- coding: utf-8 -*-
# origin: new for V1.6 -- deterministic calculator-register parser (SPEC 5, H1)
"""Text -> structured symcore task, or None (escalate).

This module is the H1 measurement surface: it is the thing standing
between "the engine can compute second derivatives" and "the engine
serves a second-derivative question a person actually typed". It
handles CALCULATOR REGISTER -- imperative/interrogative math phrasing
("differentiate ...", "what is the integral of ... from 0 to 3",
"is 97 prime") -- and refuses story register entirely; stories are
out of scope by design and belong to the escalation path.

Rules of the house:
  * abstention is the default: no confident pattern -> None, never a
    guess. UNKNOWN > WRONG.
  * the parser produces a TASK; it never computes. Values come only
    from symcore16 behind the witness gate.
  * normalization is conservative: unicode math, caret powers, and
    implicit multiplication in unambiguous positions (digit before
    letter/paren). Anything still unparseable escalates downstream.
"""
import re

_SUP = {"²": "2", "³": "3", "⁴": "4"}

_FUNC_WORDS = ("sin", "cos", "tan", "exp", "log", "sqrt", "asin",
               "acos", "atan", "sinh", "cosh", "tanh", "pi")


def normalise_expr(s):
    """Conservative math-text -> witness-grammar expression string."""
    s = s.strip().strip(".?")
    s = s.replace("−", "-").replace("×", "*")
    s = s.replace("π", "pi").replace("√", "sqrt")
    for u, d in _SUP.items():
        s = re.sub(r"([A-Za-z0-9\)])%s" % u, r"\1**%s" % d, s)
    s = s.replace("^", "**")
    s = re.sub(r"\bln\b", "log", s)
    # 3x -> 3*x ; 2sin(x) -> 2*sin(x) ; 2(x+1) -> 2*(x+1)
    s = re.sub(r"(\d)\s*([A-Za-z\(])", r"\1*\2", s)
    # x(x+1) is ambiguous (function vs product) EXCEPT known functions;
    # allow known funcs, otherwise leave for sympify to accept/refuse.
    # )( -> )*(
    s = re.sub(r"\)\s*\(", r")*(", s)
    # collapse spaces
    s = re.sub(r"\s+", " ", s).strip()
    # "sqrt x" -> sqrt(x)
    s = re.sub(r"\b(sqrt|sin|cos|tan|exp|log)\s+([A-Za-z0-9]+)\b",
               r"\1(\2)", s)
    return s


_NUM = r"-?\d+(?:\.\d+)?"

_FUNC_RE = re.compile(r"\b(?:%s)\b" % "|".join(_FUNC_WORDS))


def _free_vars(*exprs):
    """Single-letter variables in normalized expressions, with function
    names removed as WORDS (never as characters: 'x' in 'exp' is not a
    variable sighting)."""
    s = " ".join(exprs)
    s = _FUNC_RE.sub(" ", s)
    return set(re.findall(r"\b([a-df-z])\b", s))

# ---------------------------------------------------------------- lib
# Each entry: (compiled pattern, builder(match) -> task dict | None).
# First confident match wins; patterns are ordered specific -> general.


def _expr_group(m, g="e"):
    return normalise_expr(m.group(g))


def _order_word(w):
    return {"first": 1, "second": 2, "third": 3, "fourth": 4,
            "1st": 1, "2nd": 2, "3rd": 3, "4th": 4,
            "twice": 2, "double": 2}.get(w.lower())


_RULES = []


def rule(pat, flags=re.I):
    def wrap(fn):
        _RULES.append((re.compile(pat, flags), fn))
        return fn
    return wrap


# --- differentiation ---------------------------------------------------
@rule(r"\b(?:find|compute|calculate|what is|give)?\s*(?:the)?\s*"
      r"(first|second|third|fourth|1st|2nd|3rd|4th)\s+derivative\s+of\s+"
      r"(?P<e>.+?)(?:\s+with respect to\s+(?P<v>[a-z]))?"
      r"(?:\s+(?:at|evaluated at)\s+(?P<v2>[a-z])\s*=\s*(?P<pt>%s))?\s*$"
      % _NUM)
def _d_nth(m):
    t = {"op": "differentiate", "expr": _expr_group(m),
         "var": (m.group("v") or m.group("v2") or "x"),
         "order": _order_word(m.group(1))}
    if m.group("pt"):
        t["at"] = float(m.group("pt"))
    return t


@rule(r"\bdifferentiate\s+(?P<e>.+?)\s+(twice|two times)"
      r"(?:\s+with respect to\s+(?P<v>[a-z]))?\s*$")
def _d_twice(m):
    return {"op": "differentiate", "expr": _expr_group(m),
            "var": m.group("v") or "x", "order": 2}


@rule(r"\b(?:differentiate|derive)\s+(?P<e>.+?)"
      r"(?:\s+with respect to\s+(?P<v>[a-z]))?"
      r"(?:\s+(?:at|evaluated at)\s+(?P<v2>[a-z])\s*=\s*(?P<pt>%s))?\s*$"
      % _NUM)
def _d_plain(m):
    t = {"op": "differentiate", "expr": _expr_group(m),
         "var": (m.group("v") or m.group("v2") or "x"), "order": 1}
    if m.group("pt"):
        t["at"] = float(m.group("pt"))
    return t


@rule(r"\b(?:find|compute|calculate|what is|what's|give)?\s*(?:the)?\s*"
      r"derivative\s+of\s+(?P<e>.+?)"
      r"(?:\s+with respect to\s+(?P<v>[a-z]))?"
      r"(?:\s+(?:at|evaluated at)\s+(?P<v2>[a-z])\s*=\s*(?P<pt>%s))?\s*$"
      % _NUM)
def _d_of(m):
    t = {"op": "differentiate", "expr": _expr_group(m),
         "var": (m.group("v") or m.group("v2") or "x"), "order": 1}
    if m.group("pt"):
        t["at"] = float(m.group("pt"))
    return t


@rule(r"\bd\s*(?P<n>[2-4])?\s*/\s*d\s*(?P<v>[a-z])\s*(?:\^?\s*(?P=n))?"
      r"\s*(?:of|\[|\()?\s*(?P<e>[^\]\)]+?)[\]\)]?\s*$")
def _d_leibniz(m):
    return {"op": "differentiate", "expr": _expr_group(m),
            "var": m.group("v"),
            "order": int(m.group("n") or 1)}


@rule(r"\b(?:instantaneous\s+)?rate of change\s+of\s+(?P<e>.+?)\s+"
      r"(?:at|when)\s+(?P<v>[a-z])\s*=\s*(?P<pt>%s)\s*$" % _NUM)
def _d_rate(m):
    return {"op": "differentiate", "expr": _expr_group(m),
            "var": m.group("v"), "order": 1, "at": float(m.group("pt"))}


@rule(r"\bslope of (?:the )?(?:curve|graph|function)?\s*"
      r"(?:y\s*=\s*)?(?P<e>.+?)\s+(?:at|when)\s+"
      r"(?P<v>[a-z])\s*=\s*(?P<pt>%s)\s*$" % _NUM)
def _d_slope(m):
    return {"op": "differentiate", "expr": _expr_group(m),
            "var": m.group("v"), "order": 1, "at": float(m.group("pt"))}


# --- integration -------------------------------------------------------
@rule(r"\b(?:integrate|find the integral of|compute the integral of|"
      r"what is the integral of|evaluate the integral of)\s+(?P<e>.+?)\s+"
      r"from\s+(?P<a>%s)\s+to\s+(?P<b>%s)"
      r"(?:\s+with respect to\s+(?P<v>[a-z]))?\s*$" % (_NUM, _NUM))
def _int_def(m):
    return {"op": "integrate_def", "expr": _expr_group(m),
            "var": m.group("v") or "x",
            "a": float(m.group("a")), "b": float(m.group("b"))}


@rule(r"\bdefinite integral of\s+(?P<e>.+?)\s+"
      r"(?:on|over)\s*\[?\s*(?P<a>%s)\s*,\s*(?P<b>%s)\s*\]?\s*$"
      % (_NUM, _NUM))
def _int_def2(m):
    return {"op": "integrate_def", "expr": _expr_group(m), "var": "x",
            "a": float(m.group("a")), "b": float(m.group("b"))}


@rule(r"\b(?:integrate|antiderivative of|find the antiderivative of|"
      r"indefinite integral of|find the integral of)\s+(?P<e>.+?)"
      r"(?:\s+with respect to\s+(?P<v>[a-z]))?\s*$")
def _int_indef(m):
    return {"op": "integrate_indef", "expr": _expr_group(m),
            "var": m.group("v") or "x"}


# --- limits ------------------------------------------------------------
@rule(r"\b(?:find|compute|what is|evaluate)?\s*(?:the)?\s*limit of\s+"
      r"(?P<e>.+?)\s+as\s+(?P<v>[a-z])\s*"
      r"(?:approaches|->|→|goes to|tends to)\s*"
      r"(?P<pt>%s|infinity|∞|inf)\s*$" % _NUM)
def _lim(m):
    pt = m.group("pt").lower()
    if pt in ("infinity", "∞", "inf"):
        pt = "inf"
    else:
        pt = float(pt)
    return {"op": "limit", "expr": _expr_group(m), "var": m.group("v"),
            "point": pt}


# --- solving -----------------------------------------------------------
@rule(r"\b(?:solve|find (?:all )?(?:real )?(?:the )?"
      r"(?:solutions?|roots?|zeros?) (?:of|to|for))\s*:?\s*"
      r"(?P<l>[^=]+?)\s*=\s*(?P<r>[^=]+?)"
      r"(?:\s+for\s+(?P<v>[a-z]))?\s*$")
def _solve(m):
    lhs = normalise_expr(m.group("l"))
    rhs = normalise_expr(m.group("r"))
    var = m.group("v")
    if not var:
        letters = _free_vars(lhs, rhs)
        if len(letters) != 1:
            return None
        var = letters.pop()
    deg2 = "**2" in lhs + rhs or "**3" in lhs + rhs
    return {"op": "solve_poly" if deg2 else "solve_linear",
            "lhs": lhs, "rhs": rhs, "var": var}


@rule(r"\b(?:solve for|find)\s+(?P<v>[a-z])\b[^:]*?:?\s+"
      r"(?P<l>[^=]+?)\s*=\s*(?P<r>[^=]+?)\s*$")
def _solve2(m):
    lhs = normalise_expr(m.group("l"))
    rhs = normalise_expr(m.group("r"))
    deg2 = "**2" in lhs + rhs or "**3" in lhs + rhs
    return {"op": "solve_poly" if deg2 else "solve_linear",
            "lhs": lhs, "rhs": rhs, "var": m.group("v")}


# --- sums / sequences --------------------------------------------------
@rule(r"\b(?:sum|total) of\s+(?P<e>.+?)\s+"
      r"(?:for|from)\s+(?P<v>[a-z])\s*=\s*(?P<a>-?\d+)\s+to\s+"
      r"(?P<b>-?\d+)\s*$")
def _sum(m):
    return {"op": "sum_finite", "expr": _expr_group(m),
            "var": m.group("v"), "a": int(m.group("a")),
            "b": int(m.group("b"))}


@rule(r"\bsum of the first\s+(?P<n>\d+)\s+"
      r"(?P<what>positive integers|natural numbers|integers|squares|"
      r"cubes|odd numbers|even numbers)\s*$")
def _sum_first(m):
    n = int(m.group("n"))
    what = m.group("what")
    expr = {"positive integers": "k", "natural numbers": "k",
            "integers": "k", "squares": "k**2", "cubes": "k**3",
            "odd numbers": "2*k - 1", "even numbers": "2*k"}[what]
    return {"op": "sum_finite", "expr": expr, "var": "k", "a": 1, "b": n}


# --- number theory -----------------------------------------------------
@rule(r"\b(?:gcd|greatest common (?:divisor|factor)|gcf|hcf)"
      r"(?:\s+of)?\s*\(?\s*(?P<a>\d+)\s*(?:,|and)\s*(?P<b>\d+)\s*\)?\s*$")
def _gcd(m):
    return {"op": "gcd", "a": int(m.group("a")), "b": int(m.group("b"))}


@rule(r"\b(?:lcm|least common multiple|lowest common multiple)"
      r"(?:\s+of)?\s*\(?\s*(?P<a>\d+)\s*(?:,|and)\s*(?P<b>\d+)\s*\)?\s*$")
def _lcm(m):
    return {"op": "lcm", "a": int(m.group("a")), "b": int(m.group("b"))}


@rule(r"\bis\s+(?P<n>\d+)\s+(?:a\s+)?prime(?:\s+number)?\s*\??\s*$")
def _prime(m):
    return {"op": "is_prime", "n": int(m.group("n"))}


# --- combinatorics -----------------------------------------------------
@rule(r"\b(?P<n>\d+)\s*choose\s*(?P<r>\d+)\s*$")
def _choose(m):
    return {"op": "ncr", "n": int(m.group("n")), "r": int(m.group("r"))}


@rule(r"\bhow many ways .*(?:choose|select|pick)\s+(?P<r>\d+)\s+"
      r"(?:items?|objects?|people|elements?)?\s*"
      r"(?:from|out of)\s+(?P<n>\d+)\b.*$")
def _choose2(m):
    return {"op": "ncr", "n": int(m.group("n")), "r": int(m.group("r"))}


@rule(r"\b(?:number of\s+)?(?P<k>combinations|permutations)\s+of\s+"
      r"(?P<n>\d+)\s+(?:items?|objects?|things|elements?)\s+"
      r"taken\s+(?P<r>\d+)(?:\s+at a time)?\s*$")
def _perm(m):
    op = "ncr" if m.group("k").lower().startswith("c") else "npr"
    return {"op": op, "n": int(m.group("n")), "r": int(m.group("r"))}


@rule(r"\bprobability of .*?(?P<f>\d+)\s+favou?rable"
      r".*?(?:out of|in|of)\s+(?P<t>\d+)\b.*$")
def _prob(m):
    return {"op": "probability", "favorable": int(m.group("f")),
            "total": int(m.group("t"))}


# --- logic / sets / comparison ----------------------------------------
@rule(r"\b(?:evaluate|what is the truth value of|is)\s+"
      r"(?P<e>[a-z](?:[a-z\s]|and|or|not|\(|\))*?)\s+"
      r"(?:where|given|if|when)\s+(?P<env>.+?)\s*\??\s*$")
def _logic(m):
    env = {}
    for part in re.split(r",|\band\b(?=\s+[a-z]\s+is)", m.group("env")):
        mm = re.search(r"([a-z])\s+is\s+(true|false)", part, re.I)
        if mm:
            env[mm.group(1)] = mm.group(2).lower() == "true"
    if not env:
        return None
    return {"op": "logic_eval", "expr": m.group("e").strip(),
            "env": env}


def _setlist(s):
    return [int(x) for x in re.findall(r"-?\d+", s)]


@rule(r"\b(?:find|what is|compute|give)?\s*(?:the)?\s*"
      r"(?P<k>union|intersection|difference|symmetric difference)\s+of\s+"
      r"\{(?P<A>[^}]*)\}\s+and\s+\{(?P<B>[^}]*)\}\s*\??\s*$")
def _set(m):
    return {"op": "set_op",
            "kind": m.group("k").lower().replace(" ", "_"),
            "A": _setlist(m.group("A")), "B": _setlist(m.group("B"))}


@rule(r"\bhow many elements .*"
      r"(?P<k>union|intersection|difference)\s+of\s+"
      r"\{(?P<A>[^}]*)\}\s+and\s+\{(?P<B>[^}]*)\}\s*\??\s*$")
def _setsize(m):
    return {"op": "set_op", "kind": m.group("k").lower(),
            "A": _setlist(m.group("A")), "B": _setlist(m.group("B")),
            "result": "size"}


@rule(r"\bwhich is (?:larger|bigger|greater|smaller|less)\s*[,:]?\s+"
      r"(?P<a>.+?)\s+or\s+(?P<b>.+?)\s*\??\s*$")
def _cmp(m):
    a = normalise_expr(m.group("a"))
    b = normalise_expr(m.group("b"))
    if _free_vars(a, b):
        return None            # unbound variables -> escalate
    return {"op": "compare", "a_expr": a, "b_expr": b, "env": {}}


# --- plain evaluation (LAST: the most general) -------------------------
@rule(r"\b(?:evaluate|compute|calculate|what is|what's)\s+"
      r"(?P<e>[-0-9\(][^=]*?)\s*"
      r"(?:\s+(?:when|where|with|given|for)\s+(?P<env>.+?))?\s*\??\s*$")
def _eval(m):
    expr = _expr_group(m)
    env = {}
    if m.group("env"):
        for part in re.split(r",|\band\b", m.group("env")):
            mm = re.search(r"([a-z])\s*(?:=|is)\s*(%s)" % _NUM, part)
            if mm:
                env[mm.group(1)] = float(mm.group(2))
    free = _free_vars(expr) - set(env)
    if free:
        return None            # unbound variables -> escalate
    return {"op": "evaluate", "expr": expr, "env": env}


def parse(text):
    """-> structured task or None. Deterministic; never computes."""
    s = re.sub(r"\s+", " ", (text or "")).strip()
    s = re.sub(r"[?.!\s]+$", "", s)      # trailing punctuation is noise
    if not s:
        return None
    for pat, fn in _RULES:
        m = pat.search(s)
        if m:
            try:
                t = fn(m)
            except (ValueError, KeyError):
                t = None
            if t is not None:
                return t
    return None


if __name__ == "__main__":
    DEMO = [
        "Differentiate x^3 * sin(x)",
        "find the second derivative of exp(x)*cos(x)",
        "What is the derivative of x^2 + 3x at x = 2?",
        "integrate x^2 from 0 to 3",
        "antiderivative of cos(x)",
        "limit of sin(x)/x as x approaches 0",
        "solve x^2 - 5x + 6 = 0",
        "what is 3*(4+2)^2",
        "sum of k^2 for k = 1 to 10",
        "gcd of 45 and 27",
        "is 97 prime?",
        "10 choose 3",
        "union of {1,2,3} and {3,4}",
        "which is larger, 2^10 or 10^3?",
        "A waiter had 47 customers and 41 left",   # story -> None
    ]
    for q in DEMO:
        print("%-55s -> %s" % (q[:55], parse(q)))
