# -*- coding: utf-8 -*-
# origin: new for V1.0 (public surface per V1_SPEC §3)
"""ReflexGateway — the single public entry point.

ask() pipeline: reflex engine (parse -> certify -> execute) first;
a certified answer returns CERTIFIED_REFLEX with a derivation
certificate. Otherwise the abstain reason is classified:

  coverage gap  (no_target, no_plan, delta_pair_missing,
                 relational_part_*)         -> LLM_ESCALATED
  integrity verdict (invariant_violation, redundancy_mismatch,
                 target_entity_ambiguous, or CONFLICTED/AMBIGUOUS
                 facts present)             -> ABSTAINED

The hazard->ABSTAINED rule is the product form of the arc's safety
result: a detected contradiction or ambiguity is never silently
handed to the LLM to guess at; the certificate says exactly what was
detected, and the caller can still choose to ask an LLM themselves.
"""
import time

from .adapters.base import LLMAdapter
from .answer import (ABSTAINED, CERTIFIED_REFLEX, LLM_ESCALATED, Answer,
                     Certificate, Cost)

ENGINE_VERSION = "1.0-p2"

HAZARD_REASONS = {"invariant_violation", "redundancy_mismatch",
                  "target_entity_ambiguous"}


class ReflexGateway:
    def __init__(self, llm: LLMAdapter, engine=None):
        """engine: reflex.engine.Engine, or None for pure-escalation
        (P1 skeleton behavior)."""
        self.llm = llm
        self.engine = engine
        self._n = {s: 0 for s in
                   (CERTIFIED_REFLEX, LLM_ESCALATED, ABSTAINED)}

    # ------------------------------------------------------ internals
    def _certificate_for_answer(self, rec):
        st = rec.get("_state")
        facts = []
        if st is not None:
            for f in st.facts:
                if f["status"] in ("CERTIFIED", "DERIVED"):
                    facts.append({
                        "fid": f["fid"], "entity": f.get("entity"),
                        "concept": f.get("concept"),
                        "value": f.get("value"),
                        "unit": f.get("unit"),
                        "status": f["status"],
                        "span": (f.get("span") or "")[:80]})
        return Certificate("derivation", {
            "engine": ENGINE_VERSION,
            "pack": getattr(self.engine, "pack_dir", None),
            "mode": rec.get("mode"),
            "facts": facts,
            "redundancy_checked": rec.get("redundancy_checked"),
            "invariant_violations":
                len(rec.get("invariant_violations") or []),
            "parse_ms": round(rec.get("parse_ms", 0), 3),
            "integrity_ms": round(rec.get("integrity_ms", 0), 3)})

    def _hazards(self, rec):
        st = rec.get("_state")
        out = []
        if st is not None:
            for f in st.facts:
                if f["status"] in ("CONFLICTED", "AMBIGUOUS"):
                    out.append({"fid": f["fid"],
                                "status": f["status"],
                                "concept": f.get("concept"),
                                "span": (f.get("span") or "")[:80]})
        return out

    # --------------------------------------------------------- public
    def ask(self, query: str, qid: str = None) -> Answer:
        t0 = time.perf_counter()
        qid = qid or f"q{int(t0 * 1e6) % 10**9}"
        rec = None
        if self.engine is not None:
            rec = self.engine.run_query(query, qid)
            if rec.get("status") == "pm_answer":
                ans = Answer(
                    value=rec.get("numeric_value"),
                    status=CERTIFIED_REFLEX,
                    certificate=self._certificate_for_answer(rec),
                    cost=Cost(llm_calls=0,
                              wall_ms=(time.perf_counter() - t0)
                              * 1000))
                self._n[ans.status] += 1
                return ans
            reason = rec.get("abstain_reason") or "no_answer"
            hazards = self._hazards(rec)
            if reason in HAZARD_REASONS or hazards:
                ans = Answer(
                    value=None, status=ABSTAINED,
                    certificate=Certificate("abstention", {
                        "engine": ENGINE_VERSION,
                        "reason": reason,
                        "hazards": hazards}),
                    cost=Cost(wall_ms=(time.perf_counter() - t0)
                              * 1000))
                self._n[ans.status] += 1
                return ans
        # V1.1 TEXT.qa: a certified text reflex for this normalized
        # question (consulted only AFTER the engine abstains, so a
        # functional path always outranks text recall)
        if rec is not None:
            from .packs.loader import TEXT_QA
            if TEXT_QA:
                from .acquire import TextQATracker
                hit = TEXT_QA.get(TextQATracker.norm_q(query))
                if hit:
                    ans = Answer(
                        value=hit["answer"],
                        status=CERTIFIED_REFLEX,
                        certificate=Certificate("memory", {
                            "engine": ENGINE_VERSION,
                            "reflex_class": "TEXT.qa",
                            "n_observations":
                                hit.get("n_observations"),
                            "note": "functional paths abstained; "
                                    "served from a consistency-"
                                    "gated text reflex"}),
                        cost=Cost(wall_ms=(time.perf_counter() - t0)
                                  * 1000))
                    self._n[ans.status] += 1
                    return ans
        # coverage gap (or no engine): escalate
        reason = (rec.get("abstain_reason") if rec else
                  "no certified path: engine not loaded")
        c = self.llm.complete(query)
        cost = Cost(llm_calls=1, tokens_in=c.tokens_in,
                    tokens_out=c.tokens_out,
                    wall_ms=(time.perf_counter() - t0) * 1000)
        ans = Answer(
            value=None if c.pending else c.text,
            status=LLM_ESCALATED,
            certificate=Certificate("escalation", {
                "engine": ENGINE_VERSION, "reason": reason,
                "llm": self.llm.name,
                **({"bridge_pending": c.request_id}
                   if c.pending else {})}),
            cost=cost)
        self._n[ans.status] += 1
        return ans

    def stats(self):
        return {"engine": ENGINE_VERSION, "counts": dict(self._n),
                "llm": self.llm.stats()}
