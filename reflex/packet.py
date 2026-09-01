# -*- coding: utf-8 -*-
# origin: new for V1.5 -- information packet (V15_PLAN sections 2, 4)
"""The information packet, and an honest verdict on how complete it is.

The packet is NOT new work. `v10/nlpw10.parse()` has produced exactly
this structure since V0.10 -- entities with spans, quantities carrying
value, unit, concept, role, polarity, temporal context, source span,
provenance, confidence and a typed status, plus a target and ambiguity
flags -- and it computes nothing, invents nothing, and never emits a
derived value. V1.5 normalises that output and adds the one thing the
worker does not currently say out loud:

    IS THIS PACKET GOOD ENOUGH TO ANSWER FROM, AND IF NOT, WHY NOT.

That verdict is the whole economic pivot of the version. By the plan's
energy identity, saving is essentially equal to the fraction of queries
answered with no model call, so the exact question that decides V1.5 is
how often this function returns COMPLETE -- and, when it does not, WHICH
field is missing, because that is what the escalation gets to ask about
instead of re-asking the whole query.

Measured on 400 sealed real-language items before any of this was
written: COMPLETE 8.2%, target known 32.0%, all quantities named 19.0%,
at 6.4 ms per query. The verdicts below are the anatomy of the other
91.8%.
"""
import time

COMPLETE = "COMPLETE"
MISSING_TARGET = "MISSING_TARGET"
MISSING_CONCEPT = "MISSING_CONCEPT"
AMBIGUOUS = "AMBIGUOUS"
CONFLICTING = "CONFLICTING"
NO_QUANTITIES = "NO_QUANTITIES"

VERDICTS = (COMPLETE, MISSING_TARGET, MISSING_CONCEPT, AMBIGUOUS,
            CONFLICTING, NO_QUANTITIES)


def build(query, query_id=None, known=None, pack_dir=None):
    """query -> (packet, info). Deterministic. No model call.

    `packet` is the worker matrix plus a `verdict` block naming what is
    missing and, where possible, the smallest unit that would fix it.
    """
    from v10 import nlpw10
    t0 = time.perf_counter()
    matrix, winfo = nlpw10.parse(query, query_id, known)
    reground(matrix, pack_dir)
    verdict, detail = assess(matrix)
    packet = dict(matrix)
    packet["verdict"] = verdict
    packet["verdict_detail"] = detail
    packet["schema"] = "v15-packet/1"
    info = dict(winfo)
    info["verdict"] = verdict
    info["worker_ms"] = winfo.get("wall_ms")
    info["packet_ms"] = (time.perf_counter() - t0) * 1e3
    return packet, info


def reground(matrix, pack_dir=None):
    """B25. Replace every concept the worker could not EVIDENCE with
    UNKNOWN, and record what it had claimed.

    `nlpw10.name_concept` falls back to a token vote and then to a bare
    dimension match. On the generator universe those fallbacks almost
    never fire; on real language they fire constantly and return a
    confident wrong kind -- `payback_months` was assigned 131 times
    across 400 real queries, to snow depth, schoolchildren and
    touchdowns.

    That is worse than abstaining. An UNKNOWN quantity stops; a
    quantity called `payback_months` carries a dimension, so the
    dimensional gate engages, passes, and issues a certificate over
    nonsense.

    Regrounding demands the same evidence `kindderive` demands: a real
    noun, alias or unit present in the span, and abstention when two
    kinds claim the same surface. The worker's own naming is preserved
    in `claimed_concept` so the cost of this rule is measurable rather
    than merely asserted.
    """
    from . import kindderive as KD
    regrounded = 0
    for q in matrix.get("quantities") or []:
        claimed = q.get("concept")
        span = q.get("source_span") or ""
        unit = (q.get("unit") or "").strip()
        derived, why = KD.derive(("%s %s" % (span, unit)).strip(),
                                 pack_dir)
        q["claimed_concept"] = claimed
        q["evidence"] = why
        if derived == KD.UNKNOWN:
            if claimed not in (None, "UNKNOWN"):
                regrounded += 1
            q["concept"] = "UNKNOWN"
            q["status"] = "unknown_concept"
            q["confidence"] = "low"
        else:
            q["concept"] = derived
            if q.get("status") == "unknown_concept":
                q["status"] = "ok"
    tgt = matrix.get("target") or {}
    tclaim = tgt.get("concept")
    tderived, twhy = KD.derive(tgt.get("span") or "", pack_dir)
    tgt["claimed_concept"] = tclaim
    tgt["evidence"] = twhy
    tgt["concept"] = tderived if tderived != KD.UNKNOWN else "UNKNOWN"
    matrix["regrounded_quantities"] = regrounded
    return matrix


def assess(matrix):
    """-> (verdict, detail).

    Ordered so the FIRST thing wrong is the thing reported. A packet
    with a conflict and a missing target is a conflict: resolving the
    target would not make it answerable, and reporting the cheaper
    problem would send the escalation after the wrong thing.
    """
    qs = matrix.get("quantities") or []
    tgt = (matrix.get("target") or {}).get("concept")

    if not qs:
        return NO_QUANTITIES, {
            "why": "no numeric mention extracted",
            "escalate": "whole_query"}

    # CONFLICTING before anything else: same entity, same concept, same
    # temporal context, different values. This is the V0.11 identity key
    # minus the fields the worker does not set, and it is the one class
    # that must never be silently resolved.
    # A genuine conflict is the text ASSERTING TWICE and disagreeing,
    # which takes two separate assertions -- so two clauses. Two numbers
    # inside ONE clause are a list or a compound, never a contradiction:
    #
    #   "Seven red apples and two green apples"   two things
    #   "12 packs of cookies and 16 packs of noodles"  two things
    #   "It lasts 1 hour and 30 minutes"          one compound duration
    #   "arrives at 8:30"                         one clock time
    #
    # Without the clause requirement this rule fired on 90 of 400 real
    # packets and 81 of those were `count` quantities co-ordinated in a
    # single clause -- a 100% false-positive class that would have been
    # reported as the corpus contradicting itself.
    seen, conflicts = {}, []
    for q in qs:
        key = (q.get("entity"), q.get("concept"), q.get("time_context"),
               q.get("polarity"))
        if q.get("concept") in (None, "UNKNOWN"):
            continue
        prev = seen.get(key)
        if prev and prev["value"] != q.get("value") \
                and prev["clause"] != q.get("clause"):
            conflicts.append({"a": prev["qid"], "b": q["qid"],
                              "concept": q.get("concept"),
                              "values": [prev["value"], q.get("value")],
                              "clauses": [prev["clause"],
                                          q.get("clause")]})
        elif not prev:
            seen[key] = {"qid": q["qid"], "value": q.get("value"),
                         "clause": q.get("clause")}
    if conflicts:
        return CONFLICTING, {"conflicts": conflicts,
                             "escalate": "conflict_resolution"}

    ambiguous = [q["qid"] for q in qs
                 if q.get("status") == "ambiguous_concept"]
    if ambiguous:
        return AMBIGUOUS, {
            "quantities": ambiguous,
            "candidates": {q["qid"]: q.get("candidates")
                           for q in qs if q["qid"] in ambiguous},
            "escalate": "concept_disambiguation"}

    unknown = [q["qid"] for q in qs
               if q.get("status") == "unknown_concept"
               or q.get("concept") in (None, "UNKNOWN")]
    if unknown:
        return MISSING_CONCEPT, {
            "quantities": unknown,
            "spans": {q["qid"]: q.get("source_span")
                      for q in qs if q["qid"] in unknown},
            "escalate": "name_these_quantities"}

    if not tgt or tgt == "UNKNOWN":
        return MISSING_TARGET, {
            "ask_span": (matrix.get("target") or {}).get("span"),
            "known_quantities": [
                {"qid": q["qid"], "concept": q.get("concept"),
                 "value": q.get("value"), "unit": q.get("unit")}
                for q in qs],
            "escalate": "name_the_target"}

    return COMPLETE, {"quantities": len(qs), "target": tgt}


def escalation_unit(packet):
    """The SMALLEST unresolved unit, per brief section 6.

    Returns a dict naming what to ask about and the context needed to
    ask it -- never the whole query unless the packet is empty.

    The plan's D-5 records what this does and does not buy: it does NOT
    make the call cheaper, because the pure-LLM comparator already asks
    for a bare number at max_tokens=24. What it buys is that the model
    is asked to NAME something rather than to ANSWER something, so its
    reply is a typed field the engine validates instead of a number the
    engine would have to trust.
    """
    v = packet.get("verdict")
    d = packet.get("verdict_detail") or {}
    return {"verdict": v, "unit": d.get("escalate", "whole_query"),
            "detail": d,
            "authors_answer": False}
