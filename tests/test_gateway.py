# -*- coding: utf-8 -*-
"""Gateway product-surface test: certified answer with certificate,
coverage escalation to the plugged LLM, hazard abstention."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from reflex import (ABSTAINED, CERTIFIED_REFLEX,        # noqa: E402
                    LLM_ESCALATED, ReflexGateway)
from reflex.adapters.ollama import OllamaAdapter         # noqa: E402
from reflex.engine import Engine                         # noqa: E402


def main():
    gw = ReflexGateway(OllamaAdapter(), engine=Engine())

    # 1. covered physics query -> certified, zero LLM calls
    a = gw.ask("A crate weighs 40 kg and is lifted 5 m. "
               "How much potential energy does it gain?")
    assert a.status == CERTIFIED_REFLEX, (a.status,
                                          a.certificate.detail)
    assert abs(a.value - 40 * 9.8 * 5) < 1e-6, a.value
    assert a.cost.llm_calls == 0
    d = a.certificate.detail
    assert d["mode"] in ("entity_scoped", "global")
    assert d["facts"], "certificate must carry consumed facts"
    print(f"  certified: {a.value} J, {len(d['facts'])} facts, "
          f"parse {d['parse_ms']}ms  OK")

    # 2. out-of-domain query -> escalated to the plugged LLM
    b = gw.ask("What is the capital of France? "
               "Answer in one word.")
    assert b.status == LLM_ESCALATED, b.status
    assert b.value and "paris" in b.value.lower(), b.value[:80]
    assert b.cost.llm_calls == 1
    print(f"  escalated: reason={b.certificate.detail['reason']!r}, "
          f"llm={b.certificate.detail['llm']}  OK")

    # 3. contradiction trap -> ABSTAINED with hazard certificate
    c = gw.ask("Tank A holds 2000 kg of water. Tank A holds 2000 g "
               "of water. What is the mass of water in Tank A in kg?")
    assert c.status == ABSTAINED, (c.status, c.value,
                                   c.certificate.detail)
    hz = c.certificate.detail["hazards"]
    assert any(h["status"] == "CONFLICTED" for h in hz), hz
    print(f"  abstained: {len(hz)} hazard facts "
          f"(reason={c.certificate.detail['reason']!r})  OK")

    s = gw.stats()
    assert s["counts"][CERTIFIED_REFLEX] == 1
    assert s["counts"][LLM_ESCALATED] == 1
    assert s["counts"][ABSTAINED] == 1
    print("GATEWAY CHECKPOINT PASS")


if __name__ == "__main__":
    main()
