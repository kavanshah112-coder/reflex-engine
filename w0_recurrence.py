# -*- coding: utf-8 -*-
# origin: new for V1.3 — W0 structural recurrence (V1_3_SPEC §3)
"""Measures whether real traffic RECURS in solution structure, at
three granularities, at zero model cost.

Source of truth is the corpus's OWN reference solution, never our
engine's reading: GSM8K carries inline <<a op b=c>> calculator
annotations, ASDiv carries a Formula field. Both are parsed with
`ast` and walked in evaluation order.

  coarse  operator sequence only                (upper bound on reuse)
  medium  operators + operand unit classes      (the gated metric)
  fine    medium + literal/derived dataflow     (lower bound)

Runs on the TRAFFIC POOL ONLY — sealed splits are never inspected, so
no sealed item informs any design decision.

Gate (V1_3_SPEC §3): at MEDIUM, top 200 structures must cover >= 35%
of items, else W5's compounding claim leaves the ladder.

  python w0_recurrence.py
"""
import ast
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "results" / "v13" / "data"
OUT = HERE / "results" / "v13"
TOP_N, GATE = 200, 0.35

OPS = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul",
       ast.Div: "div", ast.Pow: "pow", ast.USub: "neg"}

UNIT_MAP = [
    (r"\$|dollars?|cents?|usd", "money"),
    (r"kgs?|kilograms?|grams?|tonnes?|pounds?|lbs?|ounces?", "mass"),
    (r"km/h|kph|mph|m/s", "speed"),
    (r"kms?|metres?|meters?|miles?|feet|foot|inches|inch|yards?|cm|mm",
     "length"),
    (r"hours?|hrs?|minutes?|mins?|seconds?|secs?|days?|weeks?|"
     r"months?|years?", "time"),
    (r"litres?|liters?|ml|gallons?|quarts?", "volume"),
    (r"kwh|kw|watts?|joules?|volts?|amps?|ohms?", "physical"),
    (r"%|percent", "percent"),
]
UNIT_RE = [(re.compile(p, re.I), c) for p, c in UNIT_MAP]


def unit_class(text, value):
    """Class of the unit token following `value` in `text`."""
    for lit in {f"{value:g}", str(int(value))
                if float(value).is_integer() else f"{value:g}"}:
        for m in re.finditer(re.escape(lit), text):
            tail = text[m.end():m.end() + 18]
            head = text[max(0, m.start() - 2):m.start()]
            if "$" in head:
                return "money"
            for rx, cls in UNIT_RE:
                if rx.search(tail):
                    return cls
            return "count"
    return "unseen"


def walk(node, q, prior, steps):
    """Post-order walk; emits (op, [operand classes]) per BinOp."""
    if isinstance(node, ast.BinOp):
        lc = walk(node.left, q, prior, steps)
        rc = walk(node.right, q, prior, steps)
        op = OPS.get(type(node.op), "op")
        steps.append((op, [lc, rc]))
        return ("der", "der")
    if isinstance(node, ast.UnaryOp):
        return walk(node.operand, q, prior, steps)
    if isinstance(node, ast.Constant) and \
            isinstance(node.value, (int, float)):
        v = float(node.value)
        if any(abs(v - p) < 1e-9 for p in prior):
            return ("der", "derived")
        return ("lit", unit_class(q, v))
    return ("lit", "unknown")


def signatures(item):
    """-> (coarse, medium, fine) or None if unparseable."""
    q, src = item["q"], item.get("source")
    exprs, prior = [], []
    if src == "gsm8k":
        for m in re.finditer(r"<<([^=<>]+)=([^<>]*)>>",
                             item.get("solution") or ""):
            exprs.append((m.group(1), m.group(2)))
    else:
        f = (item.get("solution") or "").split("=")[0]
        if f.strip():
            exprs.append((f, ""))
    if not exprs:
        return None
    all_steps = []
    for lhs, rhs in exprs:
        clean = lhs.replace(",", "").replace("x", "*").strip()
        clean = re.sub(r"[^0-9\.\+\-\*/\(\)\s]", "", clean)
        try:
            tree = ast.parse(clean, mode="eval")
        except Exception:
            return None
        steps = []
        try:
            walk(tree.body, q, prior, steps)
        except Exception:
            return None
        all_steps.extend(steps)
        try:
            prior.append(float(rhs.replace(",", "")))
        except Exception:
            pass
    if not all_steps:
        return None
    coarse = "|".join(op for op, _ in all_steps)
    medium = "|".join(f"{op}({','.join(c for _, c in ops)})"
                      for op, ops in all_steps)
    fine = "|".join(
        f"{op}({','.join(f'{k}:{c}' for k, c in ops)})"
        for op, ops in all_steps)
    return coarse, medium, fine


def curve(counter, n_items):
    """Cumulative coverage by rank."""
    out, run = [], 0
    for i, (_sig, c) in enumerate(counter.most_common(), 1):
        run += c
        out.append({"rank": i, "cum_coverage": run / n_items})
    return out


def main():
    pool = json.loads((DATA / "v13_traffic_pool.json")
                      .read_text(encoding="utf-8"))
    numeric = [x for x in pool if x.get("answer") is not None]
    cs, ms, fs = Counter(), Counter(), Counter()
    parsed = failed = 0
    for it in numeric:
        sig = signatures(it)
        if sig is None:
            failed += 1
            continue
        parsed += 1
        cs[sig[0]] += 1
        ms[sig[1]] += 1
        fs[sig[2]] += 1
    res = {"pool_n": len(pool), "numeric_n": len(numeric),
           "parsed": parsed, "unparseable": failed,
           "levels": {}}
    for name, ctr in (("coarse", cs), ("medium", ms), ("fine", fs)):
        cur = curve(ctr, parsed)
        top = cur[min(TOP_N, len(cur)) - 1]["cum_coverage"] \
            if cur else 0.0
        res["levels"][name] = {
            "distinct": len(ctr),
            f"top{TOP_N}_coverage": round(top, 4),
            "top10": [{"sig": s, "n": c} for s, c in
                      ctr.most_common(10)],
            "curve": cur[:TOP_N]}
        print(f"{name:7s}: {len(ctr):5d} distinct structures, "
              f"top{TOP_N} covers {top:.1%}")
    med = res["levels"]["medium"][f"top{TOP_N}_coverage"]
    res["gate"] = {"metric": "medium", "threshold": GATE,
                   "value": med, "passed": med >= GATE}
    (OUT / "w0_recurrence.json").write_text(
        json.dumps(res, indent=1), encoding="utf-8")
    print(f"parsed {parsed}/{len(numeric)} numeric items "
          f"({failed} unparseable, reported not dropped)")
    print(f"W0 GATE (medium top{TOP_N} >= {GATE:.0%}): "
          f"{'PASS' if med >= GATE else 'FAIL'} at {med:.1%}")


if __name__ == "__main__":
    main()
