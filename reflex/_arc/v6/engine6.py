# -*- coding: utf-8 -*-
"""V0.6 engine: staged recognition pipeline in front of the V0.5 partial
engine (spec Sections 4, 5, 29, 45).

Pipeline per query:
  R1  base typed parser (v4.qparse4) — unchanged, zero-regression anchor
  R2  deployed QPATs bind numbers R1 left unbound, or re-kind ONLY the
      generic kinds ('money', bare 'distance'); specific R1 kinds are
      never overridden
  R3  asked-kind: deployed APATs (verb-independent question shapes) may
      fill asked_kind only when R1 returns None or generic 'money';
      if APATs disagree/miss, deployed LEXEMES vote (verb semantics)
  then the V0.5 partial engine runs unchanged (planner, integrity gate,
  expression handoff, escalation).

Every record carries a full recognition trace for the spec-29 failure
taxonomy. All pattern/lexicon use is read-only here; learning happens
only in the breeder, deployment only through gates6.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
import v4.engines_v4 as E4              # noqa: E402
from v4.qparse4 import parse_quantities, asked_kind  # noqa: E402
from v3.ir import Quantity              # noqa: E402
from v5.engine5 import V5Engine         # noqa: E402
from v6.patterns import (number_contexts, question_abstraction,  # noqa
                         tokenize, _abstract_token)

ASKABLE = {"revenue", "profit", "money", "interest", "mass", "area",
           "volume", "count_breakeven", "cost_var", "final_amount",
           "sale_price", "net_profit", "net_interest", "rate", "power",
           "energy", "liters", "count", "speed", "distance", "force"}


class V6Engine(V5Engine):
    def __init__(self, pattern_registry=None, use_patterns=True,
                 use_lexicon=True, **kw):
        super().__init__(**kw)
        self.pr = pattern_registry
        self.use_patterns = use_patterns and pattern_registry is not None
        self.use_lexicon = use_lexicon and pattern_registry is not None
        self.name = "v6_" + kw.get("mode", "partial") + \
            ("" if self.use_patterns else "_nopat") + \
            ("" if self.use_lexicon else "_nolex")

    # ------------------------------------------------------------------
    def recognize(self, query):
        trace = {"r1_kinds": [], "qpat_hits": [], "apat_hit": None,
                 "lexeme_votes": [], "overrides": [], "added": []}
        qs, conv = parse_quantities(query)
        ak = asked_kind(query)
        trace["r1_kinds"] = [(q.kind, q.value) for q in qs]
        trace["r1_ask"] = ak
        if self.use_patterns:
            ncs = number_contexts(query)
            used = set()
            for nc in ncs:
                m = self.pr.match_number(nc)
                if not m:
                    continue
                bound = None
                for j, q in enumerate(qs):
                    if j not in used and abs(q.value - nc["value"]) < 1e-9:
                        bound = j
                        break
                if bound is not None:
                    used.add(bound)
                    if qs[bound].kind in ("money", "distance"):
                        trace["overrides"].append(
                            (qs[bound].kind, m["kind"], m["pattern"]))
                        qs[bound] = Quantity(kind=m["kind"],
                                             value=qs[bound].value,
                                             unit=qs[bound].unit)
                    # specific R1 kind: never overridden
                else:
                    trace["added"].append((m["kind"], nc["value"],
                                           m["pattern"]))
                    qs.append(Quantity(kind=m["kind"], value=nc["value"]))
                trace["qpat_hits"].append(m["pattern"])
        if ak in (None, "money"):
            new_ak = None
            if self.use_patterns:
                q_abs = question_abstraction(query)
                m = self.pr.match_ask(q_abs)
                if m:
                    new_ak = m["kind"]
                    trace["apat_hit"] = m["pattern"]
            if new_ak is None and self.use_lexicon:
                votes = {}
                for t in tokenize(query):
                    if _abstract_token(t) in ("<W>", "<NOUNS>"):
                        c = self.pr.lookup_lexeme(t)
                        if c and c in ASKABLE:
                            votes[c] = votes.get(c, 0) + 1
                            trace["lexeme_votes"].append((t, c))
                if len(votes) == 1:
                    new_ak = next(iter(votes))
                elif votes:
                    top = sorted(votes.items(), key=lambda kv: -kv[1])
                    if top[0][1] >= 2 * top[1][1]:
                        new_ak = top[0][0]
            if new_ak is not None:
                trace["ask_override"] = (ak, new_ak)
                ak = new_ak
        trace["final_kinds"] = [(q.kind, q.value) for q in qs]
        trace["final_ask"] = ak
        return qs, conv, ak, trace

    # ------------------------------------------------------------------
    def process(self, query, mode_llm="hybrid", query_id=None, log=True):
        qs, conv, ak, trace = self.recognize(query)
        # route the enriched recognition into the V4/V5 flow by patching
        # the module-level functions for the duration of this call
        orig_pq, orig_ak = E4.parse_quantities, E4.asked_kind
        import v5.engine5 as E5mod
        orig_pq5, orig_ak5 = E5mod.parse_quantities, E5mod.asked_kind

        def pq(_text):
            from dataclasses import replace
            return [replace(q) for q in qs], list(conv)

        def akf(_text):
            return ak
        E4.parse_quantities, E4.asked_kind = pq, akf
        E5mod.parse_quantities, E5mod.asked_kind = pq, akf
        try:
            rec = super().process(query, mode_llm=mode_llm,
                                  query_id=query_id, log=log)
        finally:
            E4.parse_quantities, E4.asked_kind = orig_pq, orig_ak
            E5mod.parse_quantities, E5mod.asked_kind = orig_pq5, orig_ak5
        rec["recognition"] = trace
        # GOAL-DIRECT RECOVERY (bug audit #3): the V4-lineage engine
        # answers directly only when the injected kind equals the asked
        # kind LITERALLY; for generic money asks a money-group injection
        # (cost_eur) fails resume and falls through to full LLM. When
        # that happened, the gate-validated handoff value IS the answer
        # the partial engine would have produced — prefer it over the
        # unvalidated free-text fallback. (Energy already spent on the
        # fallback call stays in the record — honest accounting.)
        if rec.get("status") == "llm_answer" and ak is not None:
            from v4.partial_planner import goal_kinds
            gks = set(goal_kinds(ak))
            for h in rec.get("handoffs", []):
                if h.get("accepted") and h.get("value") is not None \
                        and h.get("target_kind") in gks:
                    rec["answer_llm_fallback"] = rec.get("answer")
                    rec["numeric_value"] = h["value"]
                    rec["answer"] = (f"goal-direct handoff "
                                     f"[{h['target_kind']}] = "
                                     f"{h['value']:.4f}")
                    rec["status"] = "partial_answer"
                    rec["goal_direct_recovery"] = True
                    break
        return rec


def failure_stage(it, rec):
    """Spec-29 taxonomy for a graded-wrong or escalated record."""
    tr = rec.get("recognition") or {}
    if not tr.get("final_kinds"):
        return "1_pattern_recognition"        # nothing parsed at all
    if tr.get("final_ask") is None:
        return "2_concept_recognition"        # ask concept unresolved
    st = rec.get("status")
    if st == "reflex_answer" or st == "partial_answer":
        if rec.get("numeric_value") is not None:
            return "6_executor_or_binding"    # computed but wrong
    reason = rec.get("abstain_reason") or ""
    if reason.startswith("integrity"):
        return "7_validation_gate"
    if "no complete typed path" in reason or "gap" in reason:
        return "5_path_finding"
    if rec.get("escalated"):
        if rec.get("handoffs"):
            return "9_llm_handoff"
        return "9_llm_full"
    return "3_capability_retrieval"
