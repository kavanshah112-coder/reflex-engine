# -*- coding: utf-8 -*-
# origin: new for V1.4 -- W1 relational state substrate (V1_4_SPEC section 4)
"""The substrate stores what a query contains and how its parts relate.
It does not decide what any of it means.

V1.3 asked a model to fill `quantities / plan / target / dismissed`, and
measured the consequence: on real language the model typed nearly
everything `count` or `money` because the schema demanded a type, and
those labels carried no information (finding D5). One wrong answer
certified with zero dimensionally-verifiable steps. The schema
manufactured structure that was not in the reading.

So the rule here is narrow and load-bearing:

    A FIELD THAT WAS NOT ESTABLISHED IS ABSENT.

Not defaulted, not guessed, not filled with the most likely value. A
missing `order` means the text did not imply one; it does not mean
zero. Downstream checks are written to treat absence as "unknown, do
not proceed" rather than as a value, which is what turns an open record
into a safety property instead of a liability.

Unlabelled is not unstructured. Every element may carry machine-readable
metadata -- identity, order, context, provenance, derivation, relations
-- because determinism needs it. What is refused is a fixed SEMANTIC
TAXONOMY: no closed enum of roles, no mandatory `kind`, no requirement
that two packets share fields.

The one mandatory field is `span`, and it is mandatory because it is the
safety anchor. A span is verbatim source text, so it round-trips: the
engine can check that a producer did not invent it. Everything a
producer asserts is therefore checkable against the query, and
everything the engine derives (kinds, operators, applicability) is
derived from checkable material. That is V0.8's I4 typed boundary
carried onto semantics.
"""
import hashlib
import json

# Fields the engine reads structurally. Listing them is NOT a schema --
# a node may carry any other key a producer finds useful, and none of
# these is required. They are named so that checks can be written
# against a stable vocabulary rather than against guesses.
STRUCTURAL = ("content", "span", "identity", "order", "context",
              "provenance", "confidence", "derived_from", "role_hint",
              "packet")

# Written by the ENGINE only. A producer that sets one of these is
# rejected: it would be asserting an interpretation, which is exactly
# the boundary V1.4 exists to hold.
ENGINE_ONLY = ("resolved", "kind", "applicable", "certified")


class ProducerViolation(Exception):
    """A producer tried to write a field only the engine may write."""


class State:
    """An open relational state over one query.

    Nodes hold content (a number, a string, a packet, a reference, or
    nothing yet). Relations hold an edge and the VERBATIM PHRASE that
    asserted it -- never a resolved operator. Resolution is a separate,
    deterministic step (reflex/relations.py) so that an ambiguous phrase
    can abstain instead of silently committing to one reading.
    """

    def __init__(self, source_text=""):
        self.source = source_text or ""
        self._lower = self.source.lower()
        self.nodes = {}
        self.relations = {}
        self._n = 0
        self._r = 0

    # ------------------------------------------------------ producing
    def add_node(self, span, content=None, **meta):
        self._reject_engine_fields(meta)
        self._n += 1
        nid = "n%d" % self._n
        rec = {"id": nid, "span": span}
        if content is not None:
            rec["content"] = content
        for k, v in meta.items():
            if v is not None:            # absence is meaningful
                rec[k] = v
        self.nodes[nid] = rec
        return nid

    def add_relation(self, span, args, **meta):
        """`span` is the phrase that asserted the relation, verbatim.
        No operator is accepted here -- see the module docstring."""
        self._reject_engine_fields(meta)
        self._r += 1
        rid = "r%d" % self._r
        rec = {"id": rid, "span": span, "args": list(args)}
        for k, v in meta.items():
            if v is not None:
                rec[k] = v
        self.relations[rid] = rec
        return rid

    @staticmethod
    def _reject_engine_fields(meta):
        bad = sorted(k for k in meta if k in ENGINE_ONLY)
        if bad:
            raise ProducerViolation(
                "producer may not set engine-only field(s): %s"
                % ", ".join(bad))

    # ------------------------------------------------- engine writing
    def resolve_relation(self, rid, operator, why=""):
        """Engine-only. Records how a relation phrase was read."""
        self.relations[rid]["resolved"] = {"op": operator, "why": why}

    def set_kind(self, nid, kind, why=""):
        """Engine-only. Derived from the span, never asserted."""
        self.nodes[nid]["kind"] = {"kind": kind, "why": why}

    # ------------------------------------------------------- reading
    def get(self, eid):
        return self.nodes.get(eid) or self.relations.get(eid)

    def neighbours(self, nid, via=None):
        """Nodes reachable from `nid` through relations, optionally
        only through relations whose resolved operator is `via`."""
        out = []
        for r in self.relations.values():
            if nid not in r["args"]:
                continue
            if via is not None and \
                    (r.get("resolved") or {}).get("op") != via:
                continue
            out.extend(a for a in r["args"] if a != nid)
        return out

    def ordered(self):
        """Nodes and relations that carry an explicit order, sorted.
        Elements WITHOUT an order are omitted -- they are unordered,
        which is a different claim from being first."""
        items = [e for e in
                 list(self.nodes.values()) + list(self.relations.values())
                 if isinstance(e.get("order"), (int, float))]
        return sorted(items, key=lambda e: (e["order"], e["id"]))

    def unordered(self):
        return [e for e in
                list(self.nodes.values()) + list(self.relations.values())
                if not isinstance(e.get("order"), (int, float))]

    def unresolved(self):
        """Relations the engine has not resolved. Any non-empty result
        is a reason to abstain, not a reason to guess."""
        return [r for r in self.relations.values()
                if not r.get("resolved")]

    def roots(self):
        """Nodes not derived from anything -- the query's givens."""
        return [n for n in self.nodes.values() if not n.get("derived_from")]

    def terminals(self):
        """Nodes nothing else derives from."""
        used = {d for n in self.nodes.values()
                for d in (n.get("derived_from") or [])}
        return [n for n in self.nodes.values() if n["id"] not in used]

    # -------------------------------------------------- verification
    def verify_spans(self):
        """Every span must be verbatim source text.

        This is the check that makes a producer's output evidence
        rather than assertion. A span that is not in the query was
        invented, and anything derived from it is unsafe regardless of
        how well-formed the rest of the state looks.
        """
        bad = []
        for e in list(self.nodes.values()) + list(self.relations.values()):
            sp = (e.get("span") or "").strip()
            if not sp:
                bad.append({"id": e["id"], "why": "empty_span"})
            elif sp.lower() not in self._lower:
                bad.append({"id": e["id"], "why": "span_not_in_source",
                            "span": sp[:60]})
        return (not bad), bad

    def verify_refs(self):
        """Relation args and derived_from must name existing elements."""
        bad = []
        for r in self.relations.values():
            for a in r["args"]:
                if a not in self.nodes:
                    bad.append({"id": r["id"], "why": "dangling_arg",
                                "ref": a})
        for n in self.nodes.values():
            for d in (n.get("derived_from") or []):
                if d not in self.nodes and d not in self.relations:
                    bad.append({"id": n["id"], "why": "dangling_derivation",
                                "ref": d})
        return (not bad), bad

    # ------------------------------------------------------ transport
    def to_json(self):
        return {"source": self.source,
                "nodes": [self.nodes[k] for k in
                          sorted(self.nodes, key=_numkey)],
                "relations": [self.relations[k] for k in
                              sorted(self.relations, key=_numkey)]}

    @classmethod
    def from_json(cls, d):
        st = cls(d.get("source", ""))
        for n in d.get("nodes", []):
            st.nodes[n["id"]] = dict(n)
            st._n = max(st._n, _numkey(n["id"]))
        for r in d.get("relations", []):
            st.relations[r["id"]] = dict(r)
            st._r = max(st._r, _numkey(r["id"]))
        return st

    def digest(self):
        """Stable hash of the state, for provenance and dedup."""
        blob = json.dumps(self.to_json(), sort_keys=True,
                          separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def stats(self):
        return {"nodes": len(self.nodes),
                "relations": len(self.relations),
                "unresolved": len(self.unresolved()),
                "ordered": len(self.ordered()),
                "unordered": len(self.unordered()),
                "with_identity": sum(1 for n in self.nodes.values()
                                     if n.get("identity")),
                "derived": sum(1 for n in self.nodes.values()
                               if n.get("derived_from"))}


def _numkey(eid):
    try:
        return int(eid[1:])
    except (ValueError, IndexError):
        return 0
