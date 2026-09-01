# -*- coding: utf-8 -*-
# origin: new for V1.5 -- typed LLM handoff (PLAN section 4, brief 6-7)
"""What the engine asks a model for, and what it will accept back.

The rule the whole design rests on: **the model names things, the
engine computes things.** A model that returns a number has authored
the answer, and every wrong answer in V1.3 came back through exactly
that door -- a plan that computed correctly over a reading nobody could
check.

So an escalation asks for the smallest missing FIELD, never for a
result. The packet already knows which field is missing (`verdict`), so
the request can be specific: name this quantity, name this target,
choose between these two readings, resolve this contradiction. The
reply is validated as a typed field and the engine does the arithmetic.

A note on economics, recorded in the plan as D-5 and repeated here
because it is easy to lose: this does NOT make the call cheaper. The
pure-LLM comparator already asks for a bare number at max_tokens=24,
which is the cheapest call available. Selective escalation saves energy
by AVOIDING calls, not by shrinking them. What it buys is safety: the
model's reply is a name the engine can check against the text, not a
value the engine would have to trust.
"""
import re

# What the engine will accept back, per escalation kind. Anything else
# is rejected -- including a correct-looking number, which is the one
# thing a model is most likely to volunteer.
CONTRACTS = {
    "name_these_quantities": {
        "asks": "which kind each listed quantity is",
        "returns": "kind name per quantity id",
        "rejects": ("a value", "a computed answer", "a kind absent "
                    "from the pack"),
    },
    "name_the_target": {
        "asks": "what the question is asking for",
        "returns": "a single kind name",
        "rejects": ("a value", "a computed answer"),
    },
    "concept_disambiguation": {
        "asks": "which of the listed candidate kinds applies",
        "returns": "one candidate, or ABSTAIN",
        "rejects": ("a kind outside the candidate list", "a value"),
    },
    "conflict_resolution": {
        "asks": "whether two quantities describe the same thing",
        "returns": "SAME or DIFFERENT, with the distinguishing span",
        "rejects": ("a value", "a merged quantity"),
    },
    "whole_query": {
        "asks": "the full structure (fallback only)",
        "returns": "a packet",
        "rejects": ("a computed answer",),
    },
}

NUMERIC = re.compile(r"^\s*-?\d[\d,]*(?:\.\d+)?\s*$")


class HandoffRejected(Exception):
    pass


def request(packet, unit):
    """Build the typed request. Carries only the unresolved region and
    the spans needed to resolve it -- never the whole query unless the
    packet is empty."""
    d = packet.get("verdict_detail") or {}
    req = {
        "step_id": "esc:%s" % unit,
        "kind": unit,
        "contract": CONTRACTS.get(unit, CONTRACTS["whole_query"]),
        "context": {},
        "source_spans": [],
        "authors_answer": False,
    }
    qs = {q["qid"]: q for q in packet.get("quantities") or []}
    if unit in ("name_these_quantities", "concept_disambiguation"):
        ids = d.get("quantities") or []
        req["context"]["quantities"] = [
            {"qid": i, "span": qs.get(i, {}).get("source_span"),
             "value": qs.get(i, {}).get("value"),
             "unit": qs.get(i, {}).get("unit"),
             "candidates": (d.get("candidates") or {}).get(i)}
            for i in ids]
        req["source_spans"] = [qs.get(i, {}).get("source_span")
                               for i in ids]
    elif unit == "name_the_target":
        req["context"]["ask_span"] = d.get("ask_span")
        req["context"]["known"] = d.get("known_quantities")
        req["source_spans"] = [d.get("ask_span")]
    elif unit == "conflict_resolution":
        req["context"]["conflicts"] = d.get("conflicts")
    else:
        req["context"]["query"] = packet.get("query")
    return req


def validate(request_, reply, known_kinds):
    """-> (accepted_fields, rejections).

    Every rejection reason from the brief's section 10 is checked here.
    A reply that is a bare number is refused whatever else is true: it
    means the model answered the question instead of naming the field.
    """
    rej = []
    out = {}
    kind = request_.get("kind")

    if isinstance(reply, str) and NUMERIC.match(reply or ""):
        return {}, [{"why": "model returned a VALUE, not a field",
                     "reply": reply[:40]}]
    if not isinstance(reply, dict):
        return {}, [{"why": "reply is not a typed object"}]
    if any(k in reply for k in ("answer", "result", "value")):
        rej.append({"why": "reply carries an answer field; the engine "
                           "computes values"})

    if kind in ("name_these_quantities", "concept_disambiguation"):
        asked = {q["qid"] for q in
                 (request_["context"].get("quantities") or [])}
        cand = {q["qid"]: (q.get("candidates") or [])
                for q in (request_["context"].get("quantities") or [])}
        for qid, k in (reply.get("kinds") or {}).items():
            if qid not in asked:
                rej.append({"qid": qid, "why": "not an asked quantity"})
            elif k not in known_kinds:
                rej.append({"qid": qid, "kind": k,
                            "why": "kind absent from the pack"})
            elif kind == "concept_disambiguation" and cand.get(qid) \
                    and k not in cand[qid]:
                rej.append({"qid": qid, "kind": k,
                            "why": "outside the candidate list"})
            else:
                out[qid] = k
    elif kind == "name_the_target":
        k = reply.get("target")
        if k not in known_kinds:
            rej.append({"kind": k, "why": "kind absent from the pack"})
        else:
            out["target"] = k
    elif kind == "conflict_resolution":
        v = reply.get("verdict")
        if v not in ("SAME", "DIFFERENT"):
            rej.append({"why": "verdict must be SAME or DIFFERENT"})
        else:
            out["conflict"] = v
    else:
        rej.append({"why": "no validator for this escalation kind"})

    return out, rej


def apply(packet, accepted, kind):
    """Write validated fields back into the packet. Only fields the
    validator accepted are written, and each records that it came from
    an escalation rather than from the text."""
    qs = {q["qid"]: q for q in packet.get("quantities") or []}
    for qid, k in accepted.items():
        if qid == "target":
            packet.setdefault("target", {})["concept"] = k
            packet["target"]["provenance"] = "LLM_ESCALATION"
            continue
        if qid in qs:
            qs[qid]["concept"] = k
            qs[qid]["status"] = "ok"
            qs[qid]["provenance"] = "LLM_ESCALATION"
            qs[qid]["confidence"] = "med"
    return packet
