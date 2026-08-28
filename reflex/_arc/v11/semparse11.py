# -*- coding: utf-8 -*-
"""V0.11 semantic parser (spec Section 13): language -> semantic
packets (facts with entity identity + temporal scope), built on the
V0.10 worker's extraction machinery (mention extraction, unit-index
naming, role cues) plus:

- explicit entity mentions ("Car A", "the blue tank", "pump 2"),
  per-clause subject entities, alias accumulation;
- reference resolution (pronouns, ordinals, comparatives) via the
  EntityGraph — comparatives resolve AFTER facts exist;
- temporal scoping: initial/final PAIRS become temporal facts (the
  V0.10 behavior of discarding past-cue values is kept only for
  LONE historical mentions — the H2 experiment);
- relations ("connected to", "feeds", "inside") recorded explicitly.

The parser does NOT solve anything.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from v10.nlpw10 import (extract_mentions, name_concept,   # noqa: E402
                        role_of, segment_clauses, KINDS9)
from v11.semstate11 import SemanticState, ORDINALS        # noqa: E402

# entity mention patterns
ENT_RE = re.compile(
    r"\b(?:(car|tank|pump|truck|block|slab|crate|beaker|battery|"
    r"motor|coil|piston|drone|cart|boiler|reactor|vat|silo|wheel|"
    r"press|kiln|generator|fan|lorry|sled|trolley|barge|probe|"
    r"sensor)\s+([A-Z]|[0-9]+)\b|"
    r"the\s+(red|blue|green|black|white|old|new|left|right|big|"
    r"small|heavy|light)\s+(car|tank|pump|truck|block|slab|crate|"
    r"beaker|battery|motor|coil|piston|drone|cart|boiler|reactor|"
    r"vat|silo|wheel|press|kiln|generator|fan|lorry|sled|trolley|"
    r"barge|probe|sensor))\b", re.I)
REF_RE = re.compile(
    r"\b(?:the\s+(first|second|third|fourth|fifth|last)\s+(?:one|"
    r"car|tank|pump|truck|block|slab|crate|beaker|battery|motor|"
    r"coil|piston|drone|cart|boiler|reactor|vat|silo|wheel|press|"
    r"kiln|generator|fan|lorry|sled|trolley|barge|probe|sensor)|"
    r"the\s+(faster|slower|heavier|lighter|taller|shorter|longer|"
    r"larger|smaller|bigger|denser|cheaper|pricier|wider|deeper|"
    r"fastest|slowest|heaviest|lightest|tallest|longest|largest|"
    r"smallest|biggest|densest|cheapest|priciest)\s+"
    r"\w+|(it|its)|"
    r"the\s+(car|tank|pump|truck|block|slab|crate|beaker|battery|"
    r"motor|coil|piston|drone|cart|boiler|reactor|vat|silo|wheel|"
    r"press|kiln|generator|fan|lorry|sled|trolley|barge|probe|"
    r"sensor|container|vessel|machine|device|vehicle|object|item)"
    r"(?!\s+[A-Z0-9]\b))\b", re.I)
INITIAL_RE = re.compile(
    r"\b(initial(?:ly)?|at first|originally|start(?:s|ed)? (?:at|"
    r"with)|began (?:at|with)|before\b)", re.I)
FINAL_RE = re.compile(
    r"\b(final(?:ly)?|ends? (?:at|up (?:at|with))|ended (?:at|"
    r"with)|afterwards?|in the end|settle[sd]? at|drops? to|"
    r"rises? to|becomes?|now (?:reads|holds|weighs|measures))\b",
    re.I)
REL_RE = re.compile(
    r"\b(feeds|drives|connected to|inside|on top of|linked to|"
    r"powers|drains into)\b", re.I)


def _entity_mentions(text, graph):
    """Register explicit entities in order of first mention;
    returns list of (eid, start, end)."""
    out = []
    for m in ENT_RE.finditer(text):
        if m.group(1):
            name = f"{m.group(1).capitalize()} {m.group(2).upper()}"
        else:
            name = f"the {m.group(3).lower()} {m.group(4).lower()}"
        eid = graph.add(name)
        out.append((eid, m.start(), m.end()))
    return out


def parse(query, query_id=None, known=None):
    """query -> (SemanticState, info). Facts carry entity ids where
    resolvable, candidate lists where ambiguous."""
    known = known or set(KINDS9)
    st = SemanticState()
    clauses = segment_clauses(query)
    ents = _entity_mentions(query, st.graph)
    mentions, _cl = extract_mentions(query)
    # scientific-notation correction: v10's regex drops '+' exponents
    sci = {}
    from v10.nlpw10 import _unit_after
    for sm in re.finditer(r"(\d+(?:\.\d+)?)[eE]([+-]?\d+)", query):
        sci[sm.start(1)] = (float(sm.group(0).replace("E", "e")),
                            sm.end())
    fixed = []
    skip_next = False
    for j, m in enumerate(mentions):
        if skip_next:
            skip_next = False
            continue
        key = m["start"] + (1 if query[m["start"]:m["start"] + 1]
                            in "$€£" else 0)
        if key in sci:
            sci[m["start"]] = sci[key]
        if m["start"] in sci:
            sv, send = sci[m["start"]]
            u2 = _unit_after(query, send)
            if (m.get("unit") or "").startswith("$"):
                u2 = m["unit"]        # keep money prefix unit
            m = dict(m, value=sv, unit=u2, end=send)
            # drop the orphaned exponent mention that follows
            if j + 1 < len(mentions) and                     mentions[j + 1]["start"] <= send + 1:
                skip_next = True
        fixed.append(m)
    mentions = fixed
    last_ent = None
    deferred = []            # comparative references resolved later
    for i, m in enumerate(mentions):
        ct = clauses[m["clause"]][0]
        cstart = clauses[m["clause"]][1]
        role, pol, tc = role_of(ct, ct, center=m["start"] - cstart)
        concept, cands, how = name_concept(
            m["unit"], m["span"], known, clause=ct,
            rel=m["start"] - cstart)
        # entity attribution: nearest PRECEDING explicit entity in
        # the same clause, else a reference expression, else the
        # clause-level default
        eid, amb = None, []
        cend = cstart + len(ct)
        best = None
        for (e, s, _ee) in ents:
            if cstart <= s <= m["start"]:
                if best is None or s > best[1]:
                    best = (e, s)
        ref = None
        for rm in REF_RE.finditer(ct):
            if cstart + rm.start() <= m["start"]:
                ref = rm
        if ref is not None and (best is None or
                                cstart + ref.start() > best[1]):
            rtext = ref.group(0)
            low = rtext.lower()
            if any(w in low for w in
                   ("faster", "slower", "heavier", "lighter",
                    "taller", "shorter", "longer", "larger",
                    "smaller", "bigger", "denser", "cheaper",
                    "pricier", "wider", "deeper", "fastest",
                    "slowest", "heaviest", "lightest", "tallest",
                    "longest", "largest", "smallest", "biggest",
                    "densest", "cheapest", "priciest")):
                deferred.append((len(st.facts), rtext))
                eid = None
            else:
                eid, amb = st.graph.resolve(rtext,
                                            last_mentioned=last_ent)
        elif best is not None:
            eid = best[0]
        elif len(st.graph.entities) == 1:
            # single entity: attribute ONLY if this clause's subject
            # is (or refers to) that entity — a clause with its own
            # distinct subject ('the wind blows at...') stays GLOBAL
            only = next(iter(st.graph.entities))
            ename = st.graph.entities[only]["name"].lower()
            subj = re.findall(r"[a-z]+", ct.lower()[:40])
            _STOP = {"the", "a", "an", "of", "old", "new"}
            etoks = set(re.findall(r"[a-z]+", ename)) - _STOP
            ref_here = REF_RE.search(ct)
            ref_before = ref_here is not None and \
                cstart + ref_here.start() <= m["start"]
            if (set(subj[:6]) & etoks) or ref_before or \
                    (ENT_RE.search(ct) is not None):
                eid = only
            else:
                eid = "GLOBAL"
        elif st.graph.entities:
            # cross-clause continuation: the prior clause's entity,
            # but only when THIS clause introduces neither an entity
            # nor a reference expression
            if last_ent and ENT_RE.search(ct) is None and \
                    REF_RE.search(ct) is None:
                eid = last_ent
            else:
                amb = sorted(st.graph.entities)
        if eid:
            last_ent = eid
        # temporal scope
        w0 = max(cstart, m["start"] - 50)
        window = query[w0:m["end"] + 20]
        temporal = "none"
        if INITIAL_RE.search(window):
            temporal = "initial"
        elif FINAL_RE.search(window):
            temporal = "final"
        if temporal != "none" and role == "historical":
            role = "input"       # temporal pair semantics; validated
        f = st.add(entity=eid or ("GLOBAL" if not
                                  st.graph.entities else None),
                   concept=concept, value=m["value"],
                   unit=m["unit"], role=role, temporal=temporal,
                   polarity=pol, span=m["span"],
                   provenance="USER_TEXT",
                   confidence="high" if how.startswith("unit")
                   else "med")
        if f["entity"] is None:
            f["ambiguity"] = amb
    # deferred comparative resolution (facts now exist)
    for fidx, rtext in deferred:
        f = st.facts[fidx]
        eid, cands = st.graph.resolve(rtext, facts=st.facts)
        if eid:
            f["entity"] = eid
        else:
            f["entity"] = None
            f["ambiguity"] = cands
    # lone-historical demotion: an initial-cue fact with no same-key
    # final counterpart for the same entity+concept stays historical
    pairs = {}
    for f in st.facts:
        pairs.setdefault((f["entity"], f["concept"]), []).append(f)
    for (_e, _c), group in pairs.items():
        temps = {f["temporal"] for f in group}
        if "initial" in temps and "final" not in temps and \
                len(group) == 1:
            group[0]["role"] = "historical"
            group[0]["temporal"] = "none"
    # relations
    for rm in REL_RE.finditer(query):
        st.add_relation("?", rm.group(1).lower(), "?",
                        span=query[max(0, rm.start() - 30):
                                   rm.end() + 30])
    # target: concept via V0.10 logic + entity via reference
    segs = [s for s in re.split(r"[.?!]", query) if s.strip()]
    ask = segs[-1].strip() if segs else query
    from v10.nlpw10 import parse as p10
    m10, _ = p10(query, query_id)
    t_concept = m10["target"]["concept"]
    if t_concept in (None, "UNKNOWN"):
        _VERB_TGT = {"weigh": "mass", "weighs": "mass",
                     "cost": "cost_total", "take": "revenue",
                     "revenue": "revenue", "current": "current",
                     "concentration": "concentration",
                     "energy": "energy", "power": "power",
                     "mass": "mass", "profit": "profit"}
        for w in re.findall(r"[a-z]+", ask.lower()):
            if w in _VERB_TGT and _VERB_TGT[w] in known:
                t_concept = _VERB_TGT[w]
                break
    t_entity, t_cands = None, []
    em = ENT_RE.search(ask)
    if em:
        nm = (f"{em.group(1).capitalize()} {em.group(2).upper()}"
              if em.group(1) else
              f"the {em.group(3).lower()} {em.group(4).lower()}")
        t_entity, t_cands = st.graph.resolve(nm, facts=st.facts)
    else:
        rm = REF_RE.search(ask)
        if rm:
            t_entity, t_cands = st.graph.resolve(
                rm.group(0), facts=st.facts,
                last_mentioned=last_ent)
        elif len(st.graph.entities) == 1:
            t_entity = next(iter(st.graph.entities))
    info = {"n_facts": len(st.facts),
            "n_entities": len(st.graph.entities),
            "target_concept": t_concept,
            "target_entity": t_entity,
            "target_candidates": t_cands}
    return st, info
