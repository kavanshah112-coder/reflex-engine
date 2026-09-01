# -*- coding: utf-8 -*-
# origin: new for V1.5 -- packet -> relational substrate (PLAN section 4)
"""Indexes an information packet into the relational substrate without
flattening what distinguishes one story from another.

The brief's test (its section 4) is four sentences that a flat
representation cannot tell apart:

    John has 5 apples
    John gives 5 apples to Sarah
    Sarah gives John 5 apples
    John had 5 apples before giving Sarah 2

Every one contains John, 5, and apples. A representation keyed on
(entity, value, concept) collapses all four. What separates them is
POSSESSION vs TRANSFER, the DIRECTION of the transfer, and the ORDER of
events -- none of which the worker currently reports, because
`nlpw10.role_of` classifies a mention's role (input, historical,
negated, hypothetical) and its polarity and tense, and says nothing
about who gave what to whom.

So this module adds the one layer the packet lacks: a deterministic
transfer reader over the clause text, producing typed directed
relations. It reads only surface syntax -- a transfer verb, its
subject, and its recipient -- and where the syntax is not clear enough
it emits NO relation rather than a guessed one, because a wrong
direction is a wrong answer with a certificate attached and a missing
direction is an abstention.
"""
import re

from .rss import State

# Verbs that move a quantity from one holder to another. Deliberately
# short: every entry here licenses a directed edge, and a verb whose
# direction is not reliably recoverable from surface order does not
# belong in it.
TRANSFER = (r"\b(gave|gives|give|giving|handed|hands|handing|"
            r"passed|passes|passing|sent|sends|sending|sold|sells|"
            r"selling|lent|lends|lending|donated|donates|donating|"
            r"transferred|transfers|transferring|brought|brings|"
            r"bringing|paid|pays|paying)\b")
ACQUIRE = (r"\b(got|gets|received|receives|took|takes|bought|buys|"
           r"collected|collects|won|wins|found|finds)\b")
POSSESS = r"\b(has|have|had|owns|owned|holds|held|kept|keeps)\b"

TRANSFER_RE = re.compile(TRANSFER, re.I)
ACQUIRE_RE = re.compile(ACQUIRE, re.I)
POSSESS_RE = re.compile(POSSESS, re.I)

# "to Sarah" / "for Sarah" names the recipient explicitly.
TO_RE = re.compile(r"\b(?:to|for)\s+([A-Z][a-z]+)", re.U)
NAME_RE = re.compile(r"\b([A-Z][a-z]+)\b")

POSSESSION = "possession"
TRANSFER_REL = "transfer"
ACQUISITION = "acquisition"


def read_transfer(clause, subject_hint=None):
    """-> dict | None. Direction from surface syntax, or nothing.

    `subject_hint` supplies the subject for a subordinate clause that
    has none of its own. "John had 5 apples BEFORE GIVING Sarah 2" puts
    the giver in the main clause and the gift in the subordinate one;
    without inheritance the transfer has no source and is dropped,
    which is how the brief's fourth case lost its second event.

    Two English patterns carry the recipient:

        "<subj> gave <n> <thing> TO <recipient>"    prepositional
        "<subj> gave <recipient> <n> <thing>"       ditransitive

    In the ditransitive the indirect object comes FIRST, which is what
    separates "Sarah gives John 5 apples" (Sarah -> John) from "John
    gives 5 apples to Sarah" (John -> Sarah). Both contain the same
    three tokens in different order, and the order is the whole
    meaning.

    Returns None when subject or recipient cannot be identified. A
    transfer with an unknown end is not indexed as a transfer.
    """
    m = TRANSFER_RE.search(clause)
    if not m:
        return None
    before, after = clause[:m.start()], clause[m.end():]
    hit = NAME_RE.search(before)
    subj = hit.group(1) if hit else subject_hint
    if not subj:
        return None

    to = TO_RE.search(after)
    if to and to.group(1) != subj:
        return {"kind": TRANSFER_REL, "from": subj.lower(),
                "to": to.group(1).lower(), "pattern": "prepositional",
                "verb": m.group(0).lower()}

    # ditransitive: the first capitalised name after the verb, and
    # before any number, is the recipient.
    head = re.split(r"\d", after, 1)[0]
    rec = NAME_RE.search(head)
    if rec and rec.group(1) != subj:
        return {"kind": TRANSFER_REL, "from": subj.lower(),
                "to": rec.group(1).lower(), "pattern": "ditransitive",
                "verb": m.group(0).lower()}
    return None


def clause_kind(clause):
    if TRANSFER_RE.search(clause):
        return TRANSFER_REL
    if ACQUIRE_RE.search(clause):
        return ACQUISITION
    if POSSESS_RE.search(clause):
        return POSSESSION
    return None


def index(packet, query):
    """packet -> (rss.State, report).

    Nodes carry the quantity and everything that distinguishes it:
    identity, clause order, role, polarity, temporal context, unit,
    derived kind, verbatim span, provenance. Relations carry direction.
    """
    st = State(query)
    rep = {"nodes": 0, "transfers": 0, "possessions": 0,
           "acquisitions": 0, "undirected": 0}

    clauses, bounds = _clauses(query, with_bounds=True)
    qid_to_node = {}
    low = query.lower()
    for q in packet.get("quantities") or []:
        span = q.get("source_span") or ""
        if span and span.lower() not in low:
            continue                      # never index an unverifiable span
        # Clause index is re-derived against THIS module's segmentation
        # by locating the span in the query. The packet's own `clause`
        # field indexes nlpw10's segmentation, which splits only on
        # sentence punctuation; using it here silently attached both
        # events of "John had 5 apples before giving Sarah 2" to clause
        # 0, leaving the transfer clause with no quantities and the
        # transfer therefore unindexed.
        off = q.get("char_start")
        if not isinstance(off, int):
            off = low.find(span.lower()) if span else -1
        ci = _clause_at(off, bounds, q.get("clause"))
        ctext = clauses[ci] if isinstance(ci, int) and ci < len(clauses) \
            else query
        meta = {
            "identity": q.get("entity"),
            "order": ci if isinstance(ci, int) else None,
            "context": {"role": q.get("role"),
                        "polarity": q.get("polarity"),
                        "time_context": q.get("time_context"),
                        "clause_kind": clause_kind(ctext)},
            "provenance": {"source": q.get("provenance", "USER_TEXT"),
                           "qid": q.get("qid")},
            "confidence": q.get("confidence"),
            "role_hint": q.get("concept"),
            "unit": q.get("unit") or None,
        }
        nid = st.add_node(span, q.get("value"), **meta)
        qid_to_node[q.get("qid")] = nid
        rep["nodes"] += 1

    # one directed relation per clause that moves something
    last_subject = None
    for ci, ctext in enumerate(clauses):
        nodes_here = [n for n in st.nodes.values()
                      if n.get("order") == ci]
        if not nodes_here:
            continue
        t = read_transfer(ctext, subject_hint=last_subject)
        kind = clause_kind(ctext)
        here = NAME_RE.search(ctext)
        if here:
            last_subject = here.group(1)
        span = ctext.strip()
        if span.lower() not in query.lower():
            continue
        if t:
            st.add_relation(span, [n["id"] for n in nodes_here],
                            order=ci,
                            direction={"from": t["from"], "to": t["to"],
                                       "pattern": t["pattern"]},
                            relation_kind=TRANSFER_REL)
            rep["transfers"] += 1
        elif kind in (POSSESSION, ACQUISITION):
            st.add_relation(span, [n["id"] for n in nodes_here],
                            order=ci, relation_kind=kind)
            rep[kind + "s" if kind == POSSESSION else "acquisitions"] \
                = rep.get(kind + "s" if kind == POSSESSION
                          else "acquisitions", 0) + 1
        elif kind == TRANSFER_REL:
            # a transfer verb whose direction could not be read. Record
            # it as undirected rather than inventing an orientation.
            st.add_relation(span, [n["id"] for n in nodes_here],
                            order=ci, relation_kind="undirected")
            rep["undirected"] += 1

    tgt = packet.get("target") or {}
    rep["target"] = {"concept": tgt.get("concept"),
                     "span": tgt.get("span")}
    rep["spans_ok"], rep["span_problems"] = st.verify_spans()
    return st, rep


def signature(state):
    """What makes two indexed stories the SAME story.

    Direction is part of it. "John gives Sarah 5" and "Sarah gives John
    5" differ here even though every value, entity and concept matches,
    which is the property the brief's four-way test is asking for.
    """
    sig = []
    for r in sorted(state.relations.values(),
                    key=lambda x: (x.get("order") or 0, x["id"])):
        d = r.get("direction") or {}
        sig.append((r.get("relation_kind"),
                    d.get("from"), d.get("to"), len(r["args"])))
    return tuple(sig)


# A temporal subordinator starts a SECOND event inside one sentence.
# "John had 5 apples BEFORE giving Sarah 2" is a possession and a
# transfer, and splitting only on sentence punctuation reports it as
# one event -- which loses the transfer entirely and makes the answer
# unreachable. Ordering is the point of the brief's fourth case.
SUBORD_RE = re.compile(
    r"\s+(?=(?:before|after|then|once|when|until|and then|"
    r"having)\b)", re.I)


def _clause_at(offset, bounds, fallback=None):
    """Which clause contains this character offset."""
    if offset is not None and offset >= 0:
        for i, (a, b) in enumerate(bounds):
            if a <= offset < b:
                return i
    return fallback


def _clauses(text, with_bounds=False):
    """Sentence split, then temporal-subordinator split, with the
    character bounds of every piece so quantities can be attached to
    the clause that actually contains them."""
    segs, pos = [], 0
    for m in re.finditer(r"[.?!]", text):
        if text[pos:m.end()].strip():
            segs.append((pos, m.end()))
        pos = m.end()
    if text[pos:].strip():
        segs.append((pos, len(text)))
    segs = segs or [(0, len(text))]

    out, bounds = [], []
    for a, b in segs:
        seg = text[a:b]
        cuts = [a] + [a + m.start() for m in SUBORD_RE.finditer(seg)] \
            + [b]
        cuts = sorted(set(cuts))
        made = False
        for x, y in zip(cuts, cuts[1:]):
            if text[x:y].strip():
                out.append(text[x:y])
                bounds.append((x, y))
                made = True
        if not made:
            out.append(seg)
            bounds.append((a, b))
    return (out, bounds) if with_bounds else out
