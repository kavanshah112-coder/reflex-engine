# -*- coding: utf-8 -*-
# origin: new for V1.4 -- the producer side of the substrate
"""Asks a model for a relational state, and refuses to let it decide
anything.

The prompt is built around one asymmetry, which is the whole point of
V1.4's boundary:

    the producer says WHICH WORDS.  the engine says WHAT THEY MEAN.

So the model returns spans -- verbatim fragments of the query -- plus
the structure it sees over them: which quantity is which entity, what
order events happen in, which nodes an event acts on. It is never asked
for an operator, a kind, a unit, or an answer. Those are derived
(reflex/relations.py, reflex/kindderive.py) from material that
round-trips against the source text.

V1.3 asked for `{"op": "mul", "kind": "count"}` and got exactly what it
asked for: assertions nothing could check. Finding D5 measured the
result -- labels so uniformly `count`/`money` that the dimensional
gates idled, and one wrong answer certified with zero verifiable steps.
An operator asserted by a model is the reading already chosen; by the
time the engine sees `mul(3, 8)` the ambiguity in "three times more"
has been silently resolved and no check can recover that a choice was
made.
"""
import json
import re

SYSTEM = ("You extract structure from word problems. You never compute, "
          "never choose an arithmetic operation, and never label types. "
          "You only point at words and say how they relate.")

TEMPLATE = """Read this problem and describe its structure.

PROBLEM:
{query}

Return STRICT JSON only, no prose, in exactly this shape:
{{"nodes": [{{"span": "<VERBATIM words from the problem>", \
"content": <the number, or null>, "identity": "<short tag for WHAT \
this is about, e.g. apples, ana, price>", "order": <0,1,2... if the \
problem implies a sequence, else null>}}],
 "relations": [{{"span": "<VERBATIM words that say something HAPPENS \
or that two things RELATE>", "args": ["n1"], "order": <sequence \
position, or null>}}],
 "ask": {{"span": "<VERBATIM words of the question>", "identity": \
"<what the answer is about>"}}}}

RULES
1. Every "span" MUST be copied character-for-character from the \
problem. This is checked. If you cannot find the words, omit the item.
2. Do NOT write an operation. Not "add", not "subtract", not "+". \
Write the words the problem uses ("gave away 6", "bought 5 more").
3. Do NOT write a type, unit, or kind. Just the identity tag.
4. Do NOT compute or state the answer.
5. "args" lists the node ids the relation ACTS ON. Nodes are numbered \
n1, n2, n3... in the order you list them. If an event changes \
something that an earlier event already changed, point at the node \
produced by that earlier event, not the original.
6. If a quantity results FROM an event rather than being stated, give \
it "content": null and put the event's words in a relation.
7. If the problem cannot be described this way, return \
{{"nodes": [], "relations": [], "ask": {{}}, "refuse": "<why>"}}.
JSON only."""


def build_prompt(query):
    return TEMPLATE.format(query=query)


def extract_json(text):
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


def to_state(payload, query):
    """Build an rss.State from a producer payload, dropping anything
    that does not round-trip against the query.

    Dropping rather than repairing is deliberate. A span the model
    invented is evidence the reading is not anchored in the text, and
    silently correcting it would hide exactly the signal worth having.
    """
    from .rss import State
    st = State(query)
    if not isinstance(payload, dict):
        return st, {"why": "no payload"}
    dropped = []
    idmap = {}
    for i, n in enumerate(payload.get("nodes") or [], 1):
        if not isinstance(n, dict):
            continue
        span = (n.get("span") or "").strip()
        if not span or span.lower() not in query.lower():
            dropped.append({"kind": "node", "span": span[:50],
                            "why": "span not verbatim"})
            continue
        meta = {}
        if n.get("identity"):
            meta["identity"] = str(n["identity"]).strip().lower()
        if isinstance(n.get("order"), (int, float)):
            meta["order"] = n["order"]
        content = n.get("content")
        if isinstance(content, str):
            m = re.findall(r"-?\d[\d,]*(?:\.\d+)?", content)
            content = float(m[0].replace(",", "")) if m else None
        nid = st.add_node(span, content, **meta)
        idmap["n%d" % i] = nid
    for r in (payload.get("relations") or []):
        if not isinstance(r, dict):
            continue
        span = (r.get("span") or "").strip()
        if not span or span.lower() not in query.lower():
            dropped.append({"kind": "relation", "span": span[:50],
                            "why": "span not verbatim"})
            continue
        args = [idmap.get(a) for a in (r.get("args") or [])]
        args = [a for a in args if a]
        if not args:
            dropped.append({"kind": "relation", "span": span[:50],
                            "why": "no resolvable args"})
            continue
        meta = {}
        if isinstance(r.get("order"), (int, float)):
            meta["order"] = r["order"]
        st.add_relation(span, args, **meta)
    ask = payload.get("ask") or {}
    info = {"dropped": dropped,
            "ask": {"identity": str(ask.get("identity", "")).strip().lower(),
                    "span": ask.get("span", "")}}
    return st, info


def produce(adapter, query, variant=0, max_tokens=900):
    """One producer call. `variant` gives an independent sample."""
    kw = {"seed": 4000 + variant, "temperature": 0.6,
          "key_salt": "v14s%d" % variant}
    try:
        c = adapter.complete(build_prompt(query), system=SYSTEM,
                             max_tokens=max_tokens, **kw)
    except TypeError:
        c = adapter.complete(build_prompt(query), system=SYSTEM,
                             max_tokens=max_tokens)
    if getattr(c, "pending", False):
        return {"pending": True}
    payload = extract_json(c.text)
    return {"payload": payload,
            "refused": bool(payload and payload.get("refuse")),
            "tokens_in": getattr(c, "tokens_in", 0),
            "tokens_out": getattr(c, "tokens_out", 0)}
