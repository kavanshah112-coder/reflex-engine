# -*- coding: utf-8 -*-
"""P1 checkpoint: ask() end-to-end through all three adapters with
metering. Live adapters (ollama, openai_compat->ollama) need the local
ollama server; the bridge test exercises enqueue/replay without a
network."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reflex import LLM_ESCALATED, ReflexGateway          # noqa: E402
from reflex.adapters.anthropic_bridge import \
    AnthropicBridgeAdapter                                # noqa: E402
from reflex.adapters.ollama import OllamaAdapter          # noqa: E402
from reflex.adapters.openai_compat import \
    OpenAICompatAdapter                                   # noqa: E402


def check_live(adapter, tag):
    gw = ReflexGateway(adapter)
    a = gw.ask("What is 6 times 7? Answer with just the number.")
    assert a.status == LLM_ESCALATED, a.status
    assert a.value and "42" in a.value, (tag, a.value[:120])
    assert a.cost.llm_calls == 1
    assert a.cost.tokens_out > 0, (tag, "no token metering")
    assert a.certificate.kind == "escalation"
    s = gw.stats()
    assert s["llm"]["calls"] == 1
    print(f"  {tag}: ok ({a.cost.tokens_out} tok out, "
          f"{a.cost.wall_ms:.0f} ms)")


def check_bridge(tmp):
    ad = AnthropicBridgeAdapter(model="claude-haiku-4-5",
                                bridge_dir=tmp)
    gw = ReflexGateway(ad)
    a = gw.ask("bridge smoke question")
    assert a.status == LLM_ESCALATED and a.value is None
    k = a.certificate.detail["bridge_pending"]
    assert k in ad.pending()
    # simulate servicing, then replay must return the stored text
    (Path(tmp) / f"resp_{k}.json").write_text(
        json.dumps({"text": "serviced", "tokens_in": 3,
                    "tokens_out": 1}), encoding="utf-8")
    b = gw.ask("bridge smoke question")
    assert b.value == "serviced" and not ad.pending()
    print("  anthropic_bridge: ok (enqueue -> service -> replay)")


if __name__ == "__main__":
    print("P1 skeleton checks:")
    check_live(OllamaAdapter(), "ollama")
    check_live(OpenAICompatAdapter(), "openai_compat->ollama/v1")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        check_bridge(td)
    print("P1 CHECKPOINT PASS")
