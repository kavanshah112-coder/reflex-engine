# -*- coding: utf-8 -*-
"""V0.11 semantic state (spec Sections 3-7).

FACT record: [entity, concept, attribute, temporal, role] +
value/unit/provenance/span/status/ambiguity/confidence/derived_from.
Identity key (experimental, benchmarked): (entity, concept, role,
temporal, scope, polarity). Same key + different value = CONFLICT;
different temporal (initial/final) or different entity = VALID.

EntityGraph: explicit entity identity with aliases, ordinals,
pronouns, and comparative references ("the faster car" resolved by
argmax over certified facts). Facts attach to entities; an
entity-specific Reflex may never consume another entity's fact.

Statuses: ASSERTED -> (integrity) -> CERTIFIED | AMBIGUOUS |
CONFLICTED | QUARANTINED; DERIVED for execution products.
Only CERTIFIED facts are executable.
"""
import itertools

STATUSES = ("ASSERTED", "DERIVED", "AMBIGUOUS", "CONFLICTED",
            "QUARANTINED", "CERTIFIED")

# comparative adjective -> (concept, direction)  [+1 = argmax]
COMPARATIVES = {
    "faster": ("speed", 1), "slower": ("speed", -1),
    "heavier": ("mass", 1), "lighter": ("mass", -1),
    "taller": ("height", 1), "shorter": ("height", -1),
    "longer": ("length", 1), "larger": ("volume", 1),
    "smaller": ("volume", -1), "bigger": ("mass", 1),
    "denser": ("density", 1), "hotter": ("temp_diff", 1),
    "pricier": ("price_per_unit", 1),
    "cheaper": ("price_per_unit", -1),
    "stronger": ("voltage", 1), "wider": ("width", 1),
    "deeper": ("height", 1),
    # superlatives
    "fastest": ("speed", 1), "slowest": ("speed", -1),
    "heaviest": ("mass", 1), "lightest": ("mass", -1),
    "tallest": ("height", 1), "longest": ("length", 1),
    "largest": ("volume", 1), "smallest": ("volume", -1),
    "biggest": ("mass", 1), "densest": ("density", 1),
    "cheapest": ("price_per_unit", -1),
    "priciest": ("price_per_unit", 1),
}
ORDINALS = {"first": 0, "second": 1, "third": 2, "fourth": 3,
            "fifth": 4, "sixth": 5, "seventh": 6, "eighth": 7,
            "ninth": 8, "tenth": 9, "last": -1}


def make_fact(entity, concept, value, unit="", role="input",
              temporal="none", scope="none", polarity="asserted",
              attribute="", provenance="USER_TEXT", span="",
              confidence="med", derived_from=None, fid=None):
    return {"fid": fid, "entity": entity, "concept": concept,
            "attribute": attribute, "temporal": temporal,
            "role": role, "scope": scope, "polarity": polarity,
            "value": value, "unit": unit, "provenance": provenance,
            "span": span, "status": "ASSERTED",
            "ambiguity": [], "confidence": confidence,
            "derived_from": derived_from or []}


def identity_key(f):
    return (f.get("entity"), f.get("concept"), f.get("role"),
            f.get("temporal"), f.get("scope"), f.get("polarity"))


class EntityGraph:
    def __init__(self):
        self.entities = {}          # eid -> {name, aliases, order}
        self._n = 0

    def add(self, name, aliases=()):
        # reuse on exact name/alias match
        low = name.strip().lower()
        for eid, e in self.entities.items():
            if low == e["name"].lower() or \
                    low in {a.lower() for a in e["aliases"]}:
                return eid
        eid = f"E{self._n + 1}"
        self._n += 1
        self.entities[eid] = {"name": name.strip(),
                              "aliases": list(aliases),
                              "order": self._n - 1}
        return eid

    def alias(self, eid, name):
        if eid in self.entities and name not in \
                self.entities[eid]["aliases"]:
            self.entities[eid]["aliases"].append(name)

    def by_order(self, idx):
        ordered = sorted(self.entities, key=lambda e:
                         self.entities[e]["order"])
        if not ordered:
            return None
        try:
            return ordered[idx]
        except IndexError:
            return None

    def resolve(self, ref, facts=None, last_mentioned=None):
        """Resolve a textual reference to (eid or None, candidates).
        ref forms: exact name/alias, 'the first/second/... one',
        pronoun ('it'), comparative ('the faster car')."""
        r = (ref or "").strip().lower()
        r = r.removeprefix("the ").strip()
        # exact / alias
        for eid, e in self.entities.items():
            if r == e["name"].lower() or \
                    r in {a.lower() for a in e["aliases"]}:
                return eid, [eid]
        # ordinal
        for w, idx in ORDINALS.items():
            if r.startswith(w):
                eid = self.by_order(idx)
                return eid, [eid] if eid else []
        # comparative over certified facts
        toks = r.split()
        for t in toks:
            if t in COMPARATIVES and facts is not None:
                concept, sign = COMPARATIVES[t]
                cands = [(f["entity"], f["value"]) for f in facts
                         if f.get("concept") == concept
                         and f.get("status") in ("CERTIFIED",
                                                 "ASSERTED")
                         and f.get("entity") in self.entities
                         and f.get("value") is not None]
                if len({e for e, _ in cands}) >= 2:
                    best = max(cands, key=lambda x: sign * x[1])
                    return best[0], sorted({e for e, _ in cands})
                return None, sorted({e for e, _ in cands})
        # pronoun / definite singular
        if r in ("it", "its", "one", "this", "that") or not r:
            if len(self.entities) == 1:
                only = next(iter(self.entities))
                return only, [only]
            # >1 entity: a bare pronoun is genuinely ambiguous (the
            # pronoun-trap class) — never guess by recency
            return None, sorted(self.entities)
        # partial-noun match ('tank' when Tank A / Tank B exist)
        hits = [eid for eid, e in self.entities.items()
                if r in e["name"].lower()
                or any(r in a.lower() for a in e["aliases"])]
        if len(hits) == 1:
            return hits[0], hits
        if hits:
            return None, sorted(hits)
        # unmatched definite hypernym ('the container') with
        # entities present: ALL entities are candidates
        if self.entities:
            return None, sorted(self.entities)
        return None, []


class SemanticState:
    def __init__(self):
        self.facts = []
        self.graph = EntityGraph()
        self.relations = []          # {a, rel, b, span}
        self._fid = itertools.count(1)

    def add(self, **kw):
        f = make_fact(**kw)
        f["fid"] = f"F{next(self._fid)}"
        self.facts.append(f)
        return f

    def add_relation(self, a, rel, b, span=""):
        self.relations.append({"a": a, "rel": rel, "b": b,
                               "span": span})

    def by_key(self):
        out = {}
        for f in self.facts:
            out.setdefault(identity_key(f), []).append(f)
        return out

    def certified(self, entity=None, include_global=True):
        out = []
        for f in self.facts:
            if f["status"] != "CERTIFIED":
                continue
            if entity is None:
                out.append(f)
            elif f["entity"] == entity or \
                    (include_global and f["entity"] in (None,
                                                        "GLOBAL")):
                out.append(f)
        return out

    def dependents_of(self, fid):
        """Transitive closure of facts derived from fid."""
        out, frontier = set(), {fid}
        while frontier:
            nxt = set()
            for f in self.facts:
                if f["fid"] in out:
                    continue
                if set(f.get("derived_from") or []) & frontier:
                    out.add(f["fid"])
                    nxt.add(f["fid"])
            frontier = nxt
        return out
