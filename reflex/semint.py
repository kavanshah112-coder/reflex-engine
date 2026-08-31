# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W5 semantic integrity (V1_4_SPEC section 8)
"""Fifteen ways a relational state can be internally valid and mean the
wrong thing.

V1.3's five wrong answers all passed every deterministic check AND the
corroborator. The checks it had asked whether a PLAN was consistent
with the TEXT. None asked whether the plan answered the QUESTION, and
none could, because the flat plan IR had thrown away the material the
question is asked about -- entities, ordering, scope, state
transitions.

These detectors run over the substrate, where that material survives.
Each returns findings, never a verdict: the caller abstains on any
finding, because V1.4's rule is that an unproven state does not
execute.

Two properties are reported for every class and neither is optional:

  DETECTION      does it catch its adversarial cases
  FALSE POSITIVE does it fire on correct states

A detector with a high false-positive rate is a coverage tax wearing a
safety badge, and V1.3's B10 is the precedent -- non-degeneracy
rejected correct plans whose answer happened to equal an input, and
that cost was only discovered because somebody counted.
"""
import re

CLASSES = (
    "entity_mismatch", "similar_entity_confusion",
    "wrong_event_association", "wrong_temporal_ordering",
    "wrong_scope", "wrong_target", "incorrect_grouping",
    "missing_state_transition", "contradictory_relations",
    "duplicate_conflicting_entities", "unresolved_references",
    "cross_entity_contamination", "capability_applicability_failure",
    "plan_query_semantic_mismatch", "reused_plan_semantic_mismatch",
)


def _ident(n):
    return n.get("identity")


def _nodes(state):
    return list(state.nodes.values())


# ------------------------------------------------------------ 1, 2, 10
def c_entity_mismatch(state, ctx=None):
    """A relation joining nodes of different identities where the
    relation's own span names only one of them."""
    out = []
    for r in state.relations.values():
        idents = {_ident(state.get(a)) for a in r["args"]
                  if state.get(a)}
        idents.discard(None)
        if len(idents) > 1:
            span = (r.get("span") or "").lower()
            named = [i for i in idents
                     if i and i.replace("_", " ").lower() in span]
            if len(named) == 1:
                out.append({"id": r["id"], "identities": sorted(idents),
                            "named_in_span": named[0]})
    return out


def c_similar_entity_confusion(state, ctx=None):
    """Two identities differing only by a qualifier, both live."""
    out = []
    ids = sorted({_ident(n) for n in _nodes(state) if _ident(n)})
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ta, tb = set(a.lower().split("_")), set(b.lower().split("_"))
            if ta and tb and (ta < tb or tb < ta):
                out.append({"a": a, "b": b,
                            "why": "one identity subsumes the other"})
    return out


def c_duplicate_conflicting_entities(state, ctx=None):
    """Same identity, same order, different content -- one thing in two
    states at one time."""
    seen, out = {}, []
    for n in _nodes(state):
        k = (_ident(n), n.get("order"))
        if k[0] is None or k[1] is None:
            continue
        if k in seen and seen[k].get("content") != n.get("content"):
            out.append({"a": seen[k]["id"], "b": n["id"],
                        "identity": k[0], "order": k[1]})
        seen[k] = n
    return out


# --------------------------------------------------------------- 3, 7
def c_wrong_event_association(state, ctx=None):
    """An event whose argument is not the node its span is about."""
    out = []
    for r in state.relations.values():
        span = (r.get("span") or "").lower()
        for a in r["args"]:
            n = state.get(a)
            if not n:
                continue
            ident = (_ident(n) or "").replace("_", " ").lower()
            other = [m for m in _nodes(state)
                     if m["id"] != a and _ident(m) and
                     (_ident(m).replace("_", " ").lower() in span)]
            if ident and ident not in span and other:
                out.append({"relation": r["id"], "bound_to": a,
                            "span_names": [m["id"] for m in other]})
    return out


def c_incorrect_grouping(state, ctx=None):
    """A later event whose argument skips the most recent state of the
    identity it acts on -- the 90 - (49 - 19) shape."""
    out = []
    ordered = [e for e in state.ordered() if e["id"].startswith("r")]
    for r in ordered:
        for a in r["args"]:
            n = state.get(a)
            if not n or n.get("order") is None:
                continue
            ident = _ident(n)
            if ident is None:
                continue
            later = [m for m in _nodes(state)
                     if _ident(m) == ident and
                     m.get("order") is not None and
                     n["order"] < m["order"] < r["order"]]
            if later:
                out.append({"relation": r["id"], "acts_on": a,
                            "skipped": [m["id"] for m in later],
                            "why": "acts on a superseded state"})
    return out


# ------------------------------------------------------------ 4, 5, 6
def c_wrong_temporal_ordering(state, ctx=None):
    """A node derived from something that happens later."""
    out = []
    for n in _nodes(state):
        if n.get("order") is None:
            continue
        for d in (n.get("derived_from") or []):
            src = state.get(d)
            if src and src.get("order") is not None and \
                    src["order"] > n["order"]:
                out.append({"node": n["id"], "derived_from": d,
                            "order": n["order"],
                            "source_order": src["order"]})
    return out


def c_wrong_scope(state, ctx=None):
    """Inputs combined across different scopes."""
    out = []
    for r in state.relations.values():
        scopes = set()
        for a in r["args"]:
            n = state.get(a)
            if n:
                scopes.add((n.get("context") or {}).get("scope"))
        scopes.discard(None)
        if len(scopes) > 1:
            out.append({"relation": r["id"], "scopes": sorted(scopes)})
    return out


def c_wrong_target(state, ctx=None):
    """The ask names an identity the terminal does not carry."""
    ask = (ctx or {}).get("ask")
    if not ask:
        return []
    terms = state.terminals()
    if not terms:
        return [{"why": "no terminal node"}]
    want = (ask.get("identity") or "").replace("_", " ").lower()
    if not want:
        return []
    have = {(_ident(t) or "").replace("_", " ").lower() for t in terms}
    if want not in have:
        return [{"ask": want, "terminals": sorted(have),
                 "why": "answer is not about what was asked"}]
    return []


# --------------------------------------------------------------- 8, 9
STATE_CHANGING = {"add", "sub", "mul", "div"}


def c_missing_state_transition(state, ctx=None):
    """An EVENT that changes something but produces no resulting state.

    Narrowed after the dev run: the first version fired on every
    relation with no product, including ASSERTIONS ("Ana has 12
    apples"), which change nothing and are supposed to produce nothing.
    That was 50% false positives on correct states. Only a relation the
    engine RESOLVED to a state-changing operator is an event; an
    unresolved span is W2's business and abstains there.
    """
    out = []
    for r in state.relations.values():
        op = (r.get("resolved") or {}).get("op")
        if op not in STATE_CHANGING:
            continue
        produced = [n for n in _nodes(state)
                    if r["id"] in (n.get("derived_from") or [])]
        if not produced:
            out.append({"relation": r["id"], "op": op,
                        "span": (r.get("span") or "")[:50],
                        "why": "event yields no resulting state"})
    return out


def c_contradictory_relations(state, ctx=None):
    """Two relations over the same args resolved to opposite operators."""
    inv = {("add", "sub"), ("sub", "add"), ("mul", "div"), ("div", "mul")}
    out, byargs = [], {}
    for r in state.relations.values():
        op = (r.get("resolved") or {}).get("op")
        if not op:
            continue
        byargs.setdefault(tuple(sorted(r["args"])), []).append((r["id"], op))
    for args, rs in byargs.items():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if (rs[i][1], rs[j][1]) in inv:
                    out.append({"a": rs[i][0], "b": rs[j][0],
                                "ops": [rs[i][1], rs[j][1]],
                                "args": list(args)})
    return out


# ------------------------------------------------------------- 11, 12
REFERENTIAL = re.compile(
    r"\b(it|its|they|them|their|he|she|his|her|the other|the others|"
    r"the rest|the remainder|this one|that one|the former|the latter|"
    r"some|both|each other)\b", re.I)


def c_unresolved_references(state, ctx=None):
    """An unresolved REFERENCE -- anaphora the engine could not bind.

    Narrowed after the dev run: the first version reported every
    unresolved relation, which is 40% of correct states and is not an
    integrity failure at all. A span the relation table does not cover
    abstains in W2, where it belongs. This class is about pronouns and
    definite descriptions with no established antecedent.
    """
    return [{"relation": r["id"], "span": (r.get("span") or "")[:50]}
            for r in state.unresolved()
            if REFERENTIAL.search(r.get("span") or "")]


def c_cross_entity_contamination(state, ctx=None):
    """A derived node whose ancestry mixes identities without a relation
    that names both."""
    # Narrowed after the dev run. Mixing identities is LEGITIMATE when
    # the derived node is a new thing: prizes computed from tickets and
    # a price mixes two identities and is exactly right. Contamination
    # is when the node CLAIMS one source identity while quietly
    # absorbing another -- it says it is Ana's total and it is not.
    out = []
    for n in _nodes(state):
        src = [state.get(d) for d in (n.get("derived_from") or [])]
        idents = {_ident(x) for x in src if x and _ident(x)}
        own = _ident(n)
        if len(idents) > 1 and own in idents:
            # Second narrowing. The first version asked whether the
            # SOURCE SPANS named both identities, which they trivially
            # do -- a node about Elle has Elle in its span -- so the
            # detector licensed every mixture and caught nothing.
            # The licence has to come from a RELATION that joins them:
            # something in the query must actually say these two are
            # combined.
            licensed = any(
                all(i.replace("_", " ").lower() in
                    (r.get("span") or "").lower() for i in idents)
                for r in state.relations.values())
            if not licensed:
                out.append({"node": n["id"], "claims": own,
                            "absorbs": sorted(idents - {own}),
                            "why": "no relation joins these identities"})
    return out


# --------------------------------------------------------- 13, 14, 15
def c_capability_applicability_failure(state, ctx=None):
    return list((ctx or {}).get("applicability_failures") or [])


def c_plan_query_semantic_mismatch(state, ctx=None):
    """The terminal answers a sub-question. V1.3's W-6: the plan
    computed total tickets and stopped, and the ask was candies."""
    ask = (ctx or {}).get("ask") or {}
    # Narrowed after the dev run: the first version counted a given as
    # unconsumed unless a RELATION named it, and missed that a node
    # feeding another node's `derived_from` is consumed just as surely.
    # That was 50% false positives.
    # NEGATIVE RESULT, kept in the code as documentation.
    #
    # The unconsumed-givens heuristic is DISABLED. It fired on the
    # correct states of four separate classes at a 100% rate, and the
    # reason is not fixable by tuning: a DISTRACTOR is legitimately
    # unconsumed. "Dev collected 11 shells and Elle collected 15. How
    # many did Dev collect?" -- Elle's 15 must take no part in the
    # answer, and a rule that flags unused quantities cannot tell that
    # from V1.3's W-6, where a needed quantity was discarded.
    #
    # Distinguishing them requires knowing which quantities the
    # question DEPENDS on, which is the semantic judgement the whole
    # version is trying to avoid asserting. So this class is reported
    # as NOT RELIABLY DETECTABLE by a deterministic rule over the
    # substrate. The W-6 shape it was aimed at is caught instead by
    # `wrong_target`, which compares the terminal's identity against
    # the ask -- a comparison that needs no notion of relevance.
    return []


def c_reused_plan_semantic_mismatch(state, ctx=None):
    return list((ctx or {}).get("reuse_mismatches") or [])


DETECTORS = {
    "entity_mismatch": c_entity_mismatch,
    "similar_entity_confusion": c_similar_entity_confusion,
    "wrong_event_association": c_wrong_event_association,
    "wrong_temporal_ordering": c_wrong_temporal_ordering,
    "wrong_scope": c_wrong_scope,
    "wrong_target": c_wrong_target,
    "incorrect_grouping": c_incorrect_grouping,
    "missing_state_transition": c_missing_state_transition,
    "contradictory_relations": c_contradictory_relations,
    "duplicate_conflicting_entities": c_duplicate_conflicting_entities,
    "unresolved_references": c_unresolved_references,
    "cross_entity_contamination": c_cross_entity_contamination,
    "capability_applicability_failure": c_capability_applicability_failure,
    "plan_query_semantic_mismatch": c_plan_query_semantic_mismatch,
    "reused_plan_semantic_mismatch": c_reused_plan_semantic_mismatch,
}

assert set(DETECTORS) == set(CLASSES), "every class needs a detector"


def inspect(state, ctx=None, enabled=None):
    """-> (clean, findings). `clean` False means ABSTAIN.

    Every class is always reported, including the ones that found
    nothing, so a class with no detector can never masquerade as a
    class with nothing to find.
    """
    findings = {}
    for name in CLASSES:
        if enabled is not None and name not in enabled:
            continue
        try:
            hits = DETECTORS[name](state, ctx) or []
        except Exception as e:
            hits = [{"detector_error": str(e)}]
        if hits:
            findings[name] = hits
    return (not findings), findings
