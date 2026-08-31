# -*- coding: utf-8 -*-
# origin: new for V1.3 — W2 NLP parse agent (V1_3_SPEC §5)
"""The model reads; it never computes.

The agent receives a query plus (when available) a frame that narrows
the kind vocabulary, and returns a typed plan: quantities lifted
verbatim from the text, an ordered arithmetic DAG over them, a target,
and an explicit list of numbers it decided are not needed. The engine
evaluates. Any number the model writes as a RESULT is a contract
violation and is rejected by planir.validate/execute, which only ever
reads `value` fields of quantities that also appear in the text.
"""
import json
import re

from . import planir

SYSTEM = (
    "You convert word problems into a typed plan for a deterministic "
    "engine. You never compute anything yourself."
)

TEMPLATE = """Convert this problem into a typed plan. Do NOT solve it.

PROBLEM:
{query}

{frame_block}
Return STRICT JSON only, no prose, in exactly this shape:
{{"quantities": [{{"id": "q1", "value": <number copied from the \
problem>, "unit": "<unit token from the problem, or empty>", \
"kind": "<kind name>", "span": "<the words it came from>"}}],
 "plan": [{{"op": "add|sub|mul|div", "args": ["q1", "q2"], \
"out": "s1", "note": "<what this step means>"}}],
 "target": {{"kind": "<kind name>", "scope": "<what the question \
finally asks for, in your words>"}},
 "dismissed": [{{"value": <number>, "reason": "<why this number is \
not needed>"}}]}}

RULES
1. Every `value` must be a number that literally appears in the \
problem text. Never invent, never round, never compute.
2. `plan` steps reference earlier ids (`q*` quantities or `s*` step \
outputs). The LAST step's output is the answer.
3. EVERY number in the problem must either be used by a step or \
listed in `dismissed` with a reason. This is checked.
4. Use kind names from the list above when one fits; otherwise use \
"count" for plain quantities, "money" for currency.
5. If the problem cannot be expressed this way, return \
{{"quantities": [], "plan": [], "target": {{}}, \
"dismissed": [], "refuse": "<why>"}}.
JSON only."""


def build_prompt(query, frame=None):
    if frame and frame.get("kinds"):
        lines = "\n".join(f"  {k}" for k in frame["kinds"])
        ex = ""
        for e in (frame.get("examples") or [])[:2]:
            ex += f"  e.g. \"{e['q'][:90]}\" uses {e['kinds'][:4]}\n"
        block = (f"KIND VOCABULARY (prefer these):\n{lines}\n"
                 f"{ex}\n")
    else:
        block = ("KIND VOCABULARY: none matched — this problem is "
                 "outside the engine's usual domain. Use \"count\" "
                 "and \"money\" freely and describe the target in "
                 "your own words.\n\n")
    return TEMPLATE.format(query=query, frame_block=block)


def extract_json(text):
    """First balanced JSON object in the reply."""
    if not text:
        return None
    depth = start = 0
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except Exception:
                    continue
    return None


def parse_once(adapter, query, frame=None, max_tokens=900,
               variant=0):
    """`variant` selects an independent sample of the SAME prompt:
    a different sampling seed locally, a different bridge cache slot
    remotely. Without it both parses are identical and the agreement
    check means nothing."""
    kw = {}
    if variant:
        kw["seed"] = 1000 + variant
        kw["temperature"] = 0.6
        kw["key_salt"] = f"v{variant}"
    else:
        kw["seed"] = 1000
        kw["temperature"] = 0.6
        kw["key_salt"] = "v0"
    try:
        c = adapter.complete(build_prompt(query, frame),
                             system=SYSTEM, max_tokens=max_tokens,
                             **kw)
    except TypeError:
        c = adapter.complete(build_prompt(query, frame),
                             system=SYSTEM, max_tokens=max_tokens)
    if getattr(c, "pending", False):
        return {"pending": True, "request_id": c.request_id}
    ir = extract_json(c.text)
    return {"ir": ir, "tokens_in": c.tokens_in,
            "tokens_out": c.tokens_out,
            "refused": bool(ir and ir.get("refuse"))}


def dual_parse(adapter, query, frame=None):
    """Two independent parses (V1_3_SPEC decision vi). Disagreement
    is a measured confidence signal, not a coin flip."""
    a = parse_once(adapter, query, frame, variant=0)
    b = parse_once(adapter, query, frame, variant=1)
    return a, b


CORROB_TEMPLATE = ("Solve this problem. Reply with ONLY the final "
                   "number, no words, no units.

PROBLEM: {q}")
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def corroborate(adapter, query, seed=2000):
    """An INDEPENDENT solve, used only as a veto (V1_3_SPEC
    Amendment B). Never a source of the answer: the engine's
    plan-computed value stays authoritative, and a disagreement
    abstains. The corroborator does not need to be right, only
    independent."""
    try:
        c = adapter.complete(CORROB_TEMPLATE.format(q=query),
                             max_tokens=24, seed=seed,
                             temperature=0.3, key_salt="corrob")
    except TypeError:
        c = adapter.complete(CORROB_TEMPLATE.format(q=query),
                             max_tokens=24)
    if getattr(c, "pending", False):
        return None, True
    m = _NUM.findall((c.text or "").replace(",", ""))
    try:
        return (float(m[-1]) if m else None), False
    except ValueError:
        return None, False


def solve(adapter, query, frame, kinds, retry=True,
          corroboration=True):
    """Full W2->W4 path for one item. Returns a record; `value` is
    None unless every check passed and the ENGINE computed it."""
    rec = {"out_of_frame": frame is None, "checks": None,
           "value": None, "status": None, "tokens": 0}
    a, b = dual_parse(adapter, query, frame)
    if a.get("pending") or b.get("pending"):
        rec["status"] = "pending"
        return rec
    rec["tokens"] = (a.get("tokens_in", 0) + a.get("tokens_out", 0)
                     + b.get("tokens_in", 0) + b.get("tokens_out", 0))
    if a.get("refused") or b.get("refused"):
        rec["status"] = "model_refused"
        return rec
    ok, report = planir.verify(a.get("ir"), b.get("ir"), query, kinds)
    rec["checks"] = report
    if not ok and retry:
        failed = next((k for k, v in report.items()
                       if isinstance(v, dict) and not v.get("ok")),
                      "unknown")
        hint = (f"\n\nA previous attempt failed the {failed} check. "
                f"Detail: {json.dumps(report.get(failed))[:200]}. "
                f"Fix exactly that and return JSON only.")
        c = adapter.complete(build_prompt(query, frame) + hint,
                             system=SYSTEM, max_tokens=900)
        if not getattr(c, "pending", False):
            rec["tokens"] += c.tokens_in + c.tokens_out
            ir2 = extract_json(c.text)
            ok2, report2 = planir.verify(ir2, ir2, query, kinds)
            if ok2:
                ok, report = ok2, report2
                rec["checks"] = report
                rec["retried"] = True
                a = {"ir": ir2}
    if not ok:
        rec["status"] = "verification_failed"
        return rec
    value, trace = planir.execute(a["ir"])
    if value is None:
        rec["status"] = "execution_failed"
        rec["exec_error"] = trace
        return rec
    if corroboration:
        cval, pending = corroborate(adapter, query)
        rec["corroboration"] = cval
        if pending:
            rec["status"] = "pending"
            return rec
        agree = (cval is not None and
                 abs(cval - value) <= 2e-2 * max(1e-9, abs(value)))
        rec["checks"]["corroboration"] = {
            "ok": agree, "independent_value": cval,
            "plan_value": value}
        if not agree:
            rec["status"] = "corroboration_mismatch"
            return rec
    rec["value"] = value
    rec["trace"] = trace
    rec["ir"] = a["ir"]
    rec["status"] = "certified"
    return rec
