# -*- coding: utf-8 -*-
# origin: new for V1.7 -- deterministic chain parser (SPEC 4)
"""Sequential chain text -> plan, or None (escalate / hand to the
planner sample).

Handles CHAIN-VISIBLE register: imperative steps separated by
sentence or 'then' boundaries, each step one of the step grammars
below, intermediate results referenced as "that/the result/it".
The composer never computes; it emits a plan for chainexec17, which
runs it behind the plan gate and the end-to-end witness.

Abstention is the default (UNKNOWN > WRONG): any step sentence that
matches no step grammar aborts the whole parse -- a half-understood
chain is an incomplete read (B28 at chain level).
"""
import re

from .sciparse16 import normalise_expr

_NUM = r"-?\d+(?:\.\d+)?"
_RESULT = r"(?:that(?: result| value| number)?|the result|it|this)"

_SPLIT = re.compile(
    r"(?<=[.;])\s+|\s*[.;]\s*$|,?\s*(?:and\s+)?then\s+", re.I)


def _steps(text):
    parts = [p.strip(" .;") for p in _SPLIT.split(text.strip())
             if p and p.strip(" .;")]
    return parts


_STEP_RULES = []


def rule(pat):
    def wrap(fn):
        _STEP_RULES.append((re.compile(pat, re.I), fn))
        return fn
    return wrap


# Each builder returns a node dict WITHOUT id; "@prev" marks the
# running value and is rewritten to the actual node ref afterwards.
@rule(r"^(?:start with|take|find|compute)?\s*the\s+"
      r"(?P<pick>larger|smaller)\s+(?:real\s+)?root of\s+"
      r"(?P<l>[^=]+?)\s*=\s*(?P<r>.+)$")
def _s_root(m):
    return {"op": "solve_pick", "lhs": normalise_expr(m.group("l")),
            "rhs": normalise_expr(m.group("r")),
            "pick": m.group("pick").lower()}


@rule(r"^(?:start with|take|find|compute)?\s*the\s+"
      r"(?P<ow>first|second|third)\s+derivative of\s+(?P<e>.+?)\s+"
      r"at\s+(?P<v>[a-z])\s*=\s*(?P<pt>%s)$" % _NUM)
def _s_deriv(m):
    return {"op": "derivative_at", "expr": normalise_expr(m.group("e")),
            "var": m.group("v"),
            "order": {"first": 1, "second": 2, "third": 3}[
                m.group("ow").lower()],
            "point": float(m.group("pt"))}


@rule(r"^(?:start with|take|find|compute)?\s*the\s+integral of\s+"
      r"(?P<e>.+?)\s+from\s+(?P<a>%s)\s+to\s+(?P<b>%s)$"
      % (_NUM, _NUM))
def _s_int(m):
    return {"op": "integrate_def", "expr": normalise_expr(m.group("e")),
            "a": float(m.group("a")), "b": float(m.group("b"))}


@rule(r"^(?:start with|take|find|compute)?\s*the\s+"
      r"(?P<k>gcd|greatest common divisor|lcm|least common multiple)"
      r"\s+of\s+(?P<a>\d+)\s+and\s+(?P<b>\d+)$")
def _s_gcd(m):
    op = "gcd" if m.group("k").lower().startswith(("g", "gr")) \
        else "lcm"
    return {"op": op, "a": int(m.group("a")), "b": int(m.group("b"))}


@rule(r"^(?:start with|take|compute)?\s*(?P<n>\d+)\s+choose\s+"
      r"(?P<r>\d+)$")
def _s_ncr(m):
    return {"op": "ncr", "n": int(m.group("n")), "r": int(m.group("r"))}


@rule(r"^(?:start with|take|compute)?\s*the sum of\s+(?P<e>.+?)\s+"
      r"for\s+(?P<v>[a-z])\s*=\s*(?P<a>\d+)\s+to\s+(?P<b>\d+)$")
def _s_sum(m):
    return {"op": "sum_finite", "expr": normalise_expr(m.group("e")),
            "var": m.group("v"), "a": int(m.group("a")),
            "b": int(m.group("b"))}


@rule(r"^(?:start with|take|compute)?\s*(?P<e>[-0-9(][^a-df-z=]*)$")
def _s_eval(m):
    return {"op": "evaluate", "expr": normalise_expr(m.group("e"))}


@rule(r"^multiply\s+%s\s+by\s+(?P<f>%s)$" % (_RESULT, _NUM))
def _s_mul(m):
    return {"op": "scale", "value": "@prev", "by": float(m.group("f"))}


@rule(r"^divide\s+%s\s+by\s+(?P<f>%s)$" % (_RESULT, _NUM))
def _s_div(m):
    f = float(m.group("f"))
    if f == 0:
        return None
    return {"op": "scale", "value": "@prev", "by": 1.0 / f}


@rule(r"^(?:add\s+(?P<a>%s)\s+to\s+%s|increase\s+%s\s+by\s+"
      r"(?P<a2>%s))$" % (_NUM, _RESULT, _RESULT, _NUM))
def _s_add(m):
    a = m.group("a") or m.group("a2")
    return {"op": "evaluate", "expr": "@prev + %s" % a}


@rule(r"^subtract\s+(?P<a>%s)\s+from\s+%s$" % (_NUM, _RESULT))
def _s_sub(m):
    return {"op": "evaluate", "expr": "@prev - %s" % m.group("a")}


@rule(r"^(?:express|convert)\s+%s\s+(?:in|to)\s+(?P<u>[\w/^-]+)"
      r"(?:\s+from\s+(?P<f>[\w/^-]+))?$" % _RESULT)
def _s_conv(m):
    if not m.group("f"):
        return None            # unknown source unit -> abstain
    return {"op": "convert", "value": "@prev", "from": m.group("f"),
            "to": m.group("u")}


@rule(r"^using\s+%s\s+as the\s+(?P<role>speed|mass|force|distance|"
      r"height|voltage|current|resistance|principal|revenue|price)"
      r"(?:\s+in\s+(?P<ru>[\w/^-]+))?\s*(?:of|for|with|and)?\s*"
      r"(?P<rest>.*)$" % _RESULT)
def _s_use(m):
    """'Using that as the speed in m/s of a 10 kg mass, find the
    kinetic energy [in kJ]' -- a formula step with the running value
    bound to a role and remaining facts parsed from the rest."""
    role = m.group("role").lower()
    rest = m.group("rest") or ""
    facts = dict(re.findall(
        r"(\d+(?:\.\d+)?)\s*(kg|m/s|m|n|v|ohm|s|years?|%|\$)",
        rest, re.I))
    want = re.search(
        r"(kinetic energy|potential energy|force|work|power|current|"
        r"simple interest|profit)", rest, re.I)
    if not want:
        return None
    kind = want.group(1).lower()
    unit_m = re.search(r"\bin\s+(kj|j|n|w|km/h|m/s)\b", rest, re.I)
    FORM = {
        "kinetic energy": ("0.5 * m * v**2",
                           {"m": "kg", "v": "speed"}, "J"),
        "potential energy": ("m * 9.8 * h",
                             {"m": "kg", "h": "height"}, "J"),
        "force": ("m * a", {"m": "kg", "a": "accel"}, "N"),
        "work": ("f * d", {"f": "force", "d": "m"}, "J"),
        "power": ("v * i", {"v": "voltage", "i": "current"}, "W"),
        "current": ("v / r", {"v": "voltage", "r": "ohm"}, "A"),
    }
    if kind not in FORM:
        return None
    expr, slots, base_unit = FORM[kind]
    node = {"op": "formula", "expr": expr, "unit": base_unit}
    ROLE2SLOT = {"speed": "v", "mass": "m", "force": "f",
                 "height": "h", "distance": "d", "voltage": "v",
                 "current": "i", "resistance": "r"}
    slot = ROLE2SLOT.get(role)
    if slot is None or slot not in expr:
        return None
    node[slot] = "@prev"
    # bind remaining slots from stated facts by unit
    inv = {u.lower(): num for num, u in
           re.findall(r"(\d+(?:\.\d+)?)\s*(kg|m/s|m|N|V|ohm|s)\b",
                      rest)}
    for s in re.findall(r"\b([a-z])\b",
                        expr.replace("**", " ").replace("*", " ")
                        .replace("/", " ")):
        if s in node or not s.isalpha():
            continue
        for unit, num in inv.items():
            node[s] = float(num)
            break
        else:
            return None        # unbound slot -> abstain
    _ = facts
    if unit_m and unit_m.group(1).lower() in ("kj", "km/h"):
        node["_post_convert"] = (base_unit,
                                 {"kj": "kJ", "km/h": "km/h"}[
                                     unit_m.group(1).lower()])
    return node


def parse_chain(text):
    """-> plan dict or None."""
    parts = _steps(text)
    if len(parts) < 2:
        return None
    nodes = []
    for p in parts:
        node = None
        for rx, fn in _STEP_RULES:
            m = rx.match(p)
            if m:
                try:
                    node = fn(m)
                except (ValueError, KeyError):
                    node = None
                if node is not None:
                    break
        if node is None:
            return None        # one unread step aborts the chain
        prev = "n%d" % len(nodes)
        conv = node.pop("_post_convert", None)
        nid = "n%d" % (len(nodes) + 1)
        node = {("id" if k == "id" else k):
                (v.replace("@prev", "@" + prev)
                 if isinstance(v, str) and "@prev" in v else v)
                for k, v in node.items()}
        node["id"] = nid
        nodes.append(node)
        if conv:
            cid = "n%d" % (len(nodes) + 1)
            nodes.append({"id": cid, "op": "convert",
                          "value": "@" + nid, "from": conv[0],
                          "to": conv[1]})
    if len(nodes) < 2:
        return None
    return {"nodes": nodes, "final": nodes[-1]["id"]}


if __name__ == "__main__":
    DEMO = [
        "Take the larger root of x^2 - 5x + 6 = 0. Multiply that by "
        "4. Using that as the speed in m/s of a 10 kg mass, find "
        "the kinetic energy in kJ.",
        "Compute the gcd of 45 and 27. Multiply the result by 10. "
        "Add 5 to that.",
        "Find the integral of x^2 from 0 to 3, then multiply the "
        "result by 1000. Express it in kJ from J.",
    ]
    import json
    for q in DEMO:
        p = parse_chain(q)
        print("---", q[:60])
        print(json.dumps(p, indent=1) if p else "None")
