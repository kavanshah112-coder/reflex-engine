# -*- coding: utf-8 -*-
"""W2 unit tests: reflex_class casting, MEMORY.fact producer
(zero-disagreement + quorum + context), TEXT.qa producer
(consistency), injection/revert, engine memory-retry, gateway text
serving + functional-precedence."""
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from reflex.packs import loader                      # noqa: E402
loader.apply(HERE / "packs" / "physics")
from reflex import acquire as AQ                     # noqa: E402
from reflex.adapters.base import Completion, LLMAdapter  # noqa: E402
from reflex.engine import Engine                     # noqa: E402
from reflex.gateway import ReflexGateway             # noqa: E402


class StubLLM(LLMAdapter):
    name = "stub"

    def _complete(self, prompt, system, max_tokens):
        return Completion(text="stub escalation answer",
                          tokens_in=1, tokens_out=1)


def main():
    inj = AQ.Injector()
    store = AQ.CandidateStore(Path(tempfile.mktemp()))

    # ---- reflex_class casting
    cases = [
        ("new_cap", {"name": "x", "inputs": ["count"],
                     "output": "revenue", "expr": "count"},
         "FUNCTIONAL.finance"),
        ("new_cap", {"name": "x", "inputs": ["mass"],
                     "output": "temp_diff", "expr": "mass"},
         "FUNCTIONAL.thermodynamics"),
        ("lexicon_noun", {"kind": "speed", "noun": "clip"},
         "FUNCTIONAL.physics"),
        ("unit_index", {"unit": "x", "kind": "count"},
         "FUNCTIONAL.maths"),
        ("memory_fact", {"concept": "density", "value": 7800},
         "MEMORY.fact"),
        ("text_qa", {"key": "k", "answer": "a"}, "TEXT.qa"),
    ]
    for t, p, want in cases:
        got = AQ.classify_reflex(t, p, inj.W.KINDS9)
        assert got == want, (t, p, got, want)
    print("  reflex_class casting: 6/6")

    # ---- MEMORY.fact producer: quorum + zero-disagreement
    mt = AQ.MemoryFactTracker(k_min=3)
    for i in range(3):
        mt.observe(f"a steel slab q{i} density 7800",
                   [{"concept": "density", "value": 7800.0,
                     "unit": "kg/m^3"}])
    # conflicting observation for the same concept, overlapping ctx
    mt.observe("another steel part density 2700",
               [{"concept": "density", "value": 2700.0,
                 "unit": "kg/m^3"}])
    got = mt.harvest(store, inj.W.KINDS9)
    assert got == [], "disagreement in scope must block proposal"
    # disjoint context: aluminium 2700 x3, steel 7800 stays blocked
    mt2 = AQ.MemoryFactTracker(k_min=3)
    for q in ("a steel girder with density 7800 kg/m^3 spans it",
              "the steel ingot, density 7800, sits cooling",
              "some steel plating whose density is 7800 kg/m^3"):
        mt2.observe(q, [{"concept": "density", "value": 7800.0,
                         "unit": "kg/m^3"}])
    c = mt2.harvest(store, inj.W.KINDS9)
    assert len(c) == 1 and c[0]["payload"]["concept"] == "density"
    assert "steel" in c[0]["payload"]["context_tokens"]
    print("  MEMORY.fact producer: quorum + disagreement + context ok")

    # ---- gates + inject/revert for the new types
    g = AQ.Gauntlet(store, inj, lambda b, cand: {"wrong": 0,
                                                 "lift": 0})
    g.screen(c)
    assert c[0]["status"] == "PROBATION", c[0]["history"]
    assert c[0]["reflex_class"] == "MEMORY.fact"
    for _ in range(3):
        g.probation_round([])
    assert c[0]["status"] == "ACTIVE"
    assert loader.MEMORY_FACTS and \
        loader.MEMORY_FACTS[0]["concept"] == "density"
    print("  MEMORY.fact: gates -> probation -> ACTIVE, injected")

    # ---- engine memory-retry: density omitted from the query
    eng = Engine()
    r = eng.run_query("A steel block of volume 2 m^3 - what mass?",
                      "mem1")
    assert r.get("numeric_value") == 15600.0, \
        (r.get("numeric_value"), r.get("abstain_reason"))
    assert r.get("memory_used") == ["density"]
    # context NOT satisfied -> no injection, still abstains
    r2 = eng.run_query("A block of volume 2 m^3 - what mass?",
                       "mem2")
    assert r2.get("numeric_value") is None
    print("  engine MEMORY retry: fires on context, abstains without")

    # ---- TEXT.qa: producer consistency + gateway precedence
    tt = AQ.TextQATracker(k_min=3)
    for _ in range(3):
        tt.observe("What is Ohm's law?",
                   "Ohm's law: V = I * R (voltage equals current "
                   "times resistance).")
    tt.observe("What is Newton's first law?", "answer A")
    tt.observe("What is Newton's first law?", "answer B DIFFERENT")
    tt.observe("What is Newton's first law?", "answer A")
    tc = tt.harvest(store)
    keys = {c2["payload"]["key"] for c2 in tc}
    assert AQ.TextQATracker.norm_q("What is Ohm's law?") in keys
    assert len(tc) == 1, "inconsistent answers must never propose"
    g.screen(tc)
    for _ in range(3):
        g.probation_round([])
    assert tc[0]["status"] == "ACTIVE"
    gw = ReflexGateway(StubLLM(), engine=eng)
    a = gw.ask("What is Ohm's law?")
    assert a.status == "CERTIFIED_REFLEX" and "V = I * R" in a.value
    assert a.certificate.kind == "memory"
    assert a.certificate.detail["reflex_class"] == "TEXT.qa"
    # functional precedence: a computable query never hits TEXT.qa
    loader.TEXT_QA[AQ.TextQATracker.norm_q(
        "A crate weighs 40 kg and is lifted 5 m. How much "
        "potential energy does it gain?")] = {
        "answer": "SHOULD NEVER BE SERVED", "n_observations": 3}
    b = gw.ask("A crate weighs 40 kg and is lifted 5 m. How much "
               "potential energy does it gain?")
    assert b.status == "CERTIFIED_REFLEX" and b.value == 1960.0
    assert b.certificate.kind == "derivation"
    print("  TEXT.qa: consistency gate, serving, functional "
          "precedence ok")
    print("TYPED REFLEX TESTS PASS")


if __name__ == "__main__":
    main()
