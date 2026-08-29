# -*- coding: utf-8 -*-
# origin: new for V1.0 — pack-driven engine core (V1_SPEC §3)
"""The integrated reflex engine: pack-driven C10-configuration
pipeline (parse -> breeder augmentation -> certify -> execute), the
exact champion recipe from v11/run11.run_control, with every domain
table supplied by a domain pack instead of hardcoded state.

boot() once per process (one pack per process — the in-place
injection pattern the arc always used).
"""
import sys
import time
from pathlib import Path

_ARC = Path(__file__).resolve().parent / "_arc"
if str(_ARC) not in sys.path:
    sys.path.insert(0, str(_ARC))

from .packs import loader                                  # noqa: E402

DEFAULT_PACK = Path(__file__).resolve().parents[1] / "packs" / \
    "physics"


class Engine:
    def __init__(self, pack_dir=DEFAULT_PACK, resolver=None,
                 redundancy=True, use_breeder=True):
        loader.apply(pack_dir)
        from v11.semparse11 import parse as _parse
        from v11.integrity11 import certify as _certify
        from v11.semrun11 import run as _run
        self._parse, self._certify, self._run = (_parse, _certify,
                                                 _run)
        self.breeder = (loader.load_breeder(pack_dir)
                        if use_breeder else None)
        if self.breeder is not None:
            import json as _json
            acq = Path(pack_dir) / "acquired.json"
            if acq.exists():
                for c in _json.loads(acq.read_text(
                        encoding="utf-8")):
                    if c["type"] == "template_struct":
                        self.breeder.deployed_struct[
                            c["payload"]["key"]] = \
                            c["payload"]["spec"]
        self.resolver = resolver
        self.redundancy = redundancy
        self.pack_dir = str(pack_dir)

    def run_query(self, query, qid, available=None):
        """One query through the full pipeline. Returns the v11-style
        record + parse artifacts (facts/state for certificates)."""
        from . import engine_patches as EP
        t0 = time.perf_counter()
        query, _norm = EP.normalize_query(query)     # F1+F2 (V1.1)
        rec = {"query_id": qid, "llm_calls": [],
               "reflex_parse": False, "normalized": _norm}
        tp = time.perf_counter()
        st, info = self._parse(query, qid)
        rec["parse_ms"] = (time.perf_counter() - tp) * 1e3
        if self.breeder is not None:
            extra = self.breeder.extract_struct(query)
            known_unknown = [f for f in st.facts
                             if f["concept"] in (None, "UNKNOWN")]
            for (c, v, u) in extra:
                for f in known_unknown:
                    if f["value"] is not None and \
                            abs(f["value"] - v) < 1e-9:
                        f["concept"] = c
                        rec["reflex_parse"] = True
        # acquired-kind target recovery: the vendored target-namer
        # cannot see single-word nouns of kinds added after pack load
        # (tc_hits requires multiword phrases; the v9 fallback tables
        # are import-frozen). Fires ONLY for acquired kinds and ONLY
        # when the target is unknown, so base-pack behavior and E0
        # parity are untouched by construction.
        import re as _re
        from .packs.loader import BASE_KINDS
        import v10.universe10 as _U10
        acquired = {k: _U10.KINDS10[k] for k in _U10.KINDS10
                    if k not in BASE_KINDS}
        if acquired:
            segs = [s for s in _re.split(r"[.?!]", query)
                    if s.strip()]
            askl = (segs[-1] if segs else query).lower()
            toks = set(_re.findall(r"[a-z_]+", askl))
            hits = []
            for k, spec in acquired.items():
                nouns = [k] + [n.lower() for n in (spec[2] or [])]
                for n in nouns:
                    if (" " in n and n in askl) or n in toks:
                        hits.append(k)
                        break
            tgt = info.get("target_concept")
            if len(set(hits)) == 1:
                if tgt in (None, "UNKNOWN"):
                    info["target_concept"] = hits[0]
                else:
                    # wrong-target override: the base namer picked a
                    # kind whose value is ALREADY a given input (the
                    # 'asking for what you were told' signal the arc
                    # treats as suspicious) while an acquired kind's
                    # noun literally appears in the ask
                    have = {f["concept"] for f in st.facts
                            if f.get("value") is not None}
                    if tgt in have:
                        info["target_concept"] = hits[0]
        # W1.1b (V1.2): appositive alias resolution — "Truck A — the
        # freight hauler —" registers the alias, facts whose spans
        # carry the alias re-attribute to its entity, and an ask
        # naming the alias resolves. Replaces the correct-by-luck
        # global guesses the guard rightly refuses.
        if st.graph.entities:
            import re as _re
            for eid, e in list(st.graph.entities.items()):
                nm = _re.escape(e["name"])
                for m in _re.finditer(
                        rf"{nm}\s*[,–—-]+\s*(the\s+"
                        rf"[a-z][a-z ]{{2,30}}?)\s*[,–—-]",
                        query, _re.I):
                    ph = m.group(1).strip()
                    # only a TRUE alias: if the phrase already
                    # resolves (it is an entity-pattern name of its
                    # own, e.g. "the red car"), the vendored binding
                    # machinery owns it — registering it here would
                    # split the entity (sem alias class regression,
                    # caught by the battery)
                    already, _c = st.graph.resolve(ph)
                    if already is None:
                        st.graph.alias(eid, ph)
            alias_map = {}
            for eid, e in st.graph.entities.items():
                for a2 in e["aliases"]:
                    alias_map[a2.lower()] = eid
            if alias_map:
                for f in st.facts:
                    sp = (f.get("span") or "").lower()
                    for a2, eid in alias_map.items():
                        if a2 in sp and f.get("entity") != eid:
                            f["entity"] = eid
                            f["ambiguity"] = []
                            break
                if info.get("target_entity") is None:
                    segs2 = [s for s in _re.split(r"[.?!]", query)
                             if s.strip()]
                    ask2 = (segs2[-1] if segs2 else query).lower()
                    hits2 = {eid for a2, eid in alias_map.items()
                             if a2 in ask2}
                    if len(hits2) == 1:
                        info["target_entity"] = next(iter(hits2))
        ti = time.perf_counter()
        self._certify(st)
        rec["integrity_ms"] = (time.perf_counter() - ti) * 1e3
        r = self._run(st, info, query, qid, use_llm=False,
                      resolver=self.resolver,
                      redundancy=self.redundancy, avail=available)
        # F3 (V1.1): retry-after-abstain with an alternative target.
        # Only coverage-type abstentions retry, so no answered item
        # and no integrity verdict can ever change.
        if r.get("status") != "pm_answer" and \
                r.get("abstain_reason") in EP._RETRYABLE:
            from .packs.loader import MEMORY_FACTS, TARGET_VERBS
            import re as _re
            import v10.nlpw10 as _W
            in_concepts = {f["concept"] for f in st.facts
                           if f.get("value") is not None}
            alts = EP.alt_targets(
                query, info.get("target_concept"),
                _W.KINDS9, TARGET_VERBS, in_concepts)

            def _try(tgt):
                info2 = dict(info, target_concept=tgt)
                rr = self._run(st, info2, query, qid,
                               use_llm=False,
                               resolver=self.resolver,
                               redundancy=self.redundancy,
                               avail=available)
                return (rr, info2) if rr.get("status") == \
                    "pm_answer" else None

            hit = None
            for alt in alts:                    # phase 1: F3 alts
                hit = _try(alt)
                if hit:
                    rec["target_retry"] = alt
                    break
            if hit is None and MEMORY_FACTS:
                # phase 2 (V1.1 MEMORY.fact): inject applicable
                # certified constants (context satisfied, concept not
                # explicitly given), then retry original + alt targets
                qtok = set(_re.findall(r"[a-z]+", query.lower()))
                added = []
                for mf in MEMORY_FACTS:
                    if mf["concept"] in in_concepts:
                        continue
                    if set(mf.get("context_tokens") or []) <= qtok:
                        f = st.add(entity="GLOBAL",
                                   concept=mf["concept"],
                                   value=mf["value"],
                                   unit=mf.get("unit", ""),
                                   role="input",
                                   provenance="MEMORY",
                                   span=f"[memory:{mf['concept']}]")
                        f["status"] = "CERTIFIED"
                        added.append(mf["concept"])
                if added:
                    targets = [info.get("target_concept")] + alts
                    for tgt in dict.fromkeys(
                            t for t in targets
                            if t not in (None, "UNKNOWN")):
                        hit = _try(tgt)
                        if hit:
                            rec["memory_used"] = added
                            if tgt != info.get("target_concept"):
                                rec["target_retry"] = tgt
                            break
            if hit:
                r, info = hit
        # W1.1 (V1.2): ambiguity-by-default guard. A GLOBAL solve
        # over a state where >=2 entities hold competing facts of the
        # same kinds is a binding guess, not an answer (bug_audit_v1_1
        # B2's class): convert to a hazard abstention carrying the
        # competing bindings. Single-entity and genuinely-global
        # states are untouched; relational asks route through
        # relational modes and never reach here.
        if r.get("status") == "pm_answer" and \
                r.get("mode") == "global":
            import re as _re2
            _segs = [s for s in _re2.split(r"[.?!]", query)
                     if s.strip()]
            _ask = (_segs[-1] if _segs else query)
            if not EP.ASK_REF_RE.search(_ask):
                per_ent = None      # kind-only ask: legitimately
                #                     global; guard stays silent
            else:
                per_ent = {}
        else:
            per_ent = None
        if per_ent is not None:
            for f in st.facts:
                e = f.get("entity")
                if e in (None, "GLOBAL"):
                    continue
                if f.get("value") is not None and \
                        f.get("concept") not in (None, "UNKNOWN"):
                    per_ent.setdefault(e, set()).add(f["concept"])
            if len(per_ent) >= 2:
                kinds_seen = {}
                competing = set()
                for e, ks in per_ent.items():
                    for k in ks:
                        if k in kinds_seen and kinds_seen[k] != e:
                            competing.add(k)
                        kinds_seen.setdefault(k, e)
                if competing:
                    r = dict(r, status="abstain",
                             numeric_value=None,
                             abstain_reason="target_entity_ambiguous")
                    rec["guard_fired"] = {
                        "competing_kinds": sorted(competing),
                        "entities": sorted(per_ent)}
        rec.update({k: r.get(k) for k in
                    ("status", "numeric_value", "abstain_reason",
                     "mode", "resolver_used", "redundancy_checked",
                     "invariant_violations")})
        rec["llm_calls"] = r.get("llm_calls", [])
        rec["t_ms"] = (time.perf_counter() - t0) * 1e3
        rec["_state"] = st
        rec["_info"] = info
        return rec
