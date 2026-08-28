# reflex-engine (V1.0)

The integrated reflex architecture: distillation of the reflex-poc
research arc V0.1–V0.11 into one engine that plugs into any LLM,
generates reflexes from live escalations, and certifies them before
they can ever answer.

- Authority: `V1_SPEC.md` (frozen 2026-08-28) + `V1_PLAN.md`
  (frozen pre-registration: parameters, hypotheses, outcome ladder).
- Public surface: `ReflexGateway(llm).ask(query) -> Answer(value,
  status, certificate, cost)` with status `CERTIFIED_REFLEX |
  LLM_ESCALATED | ABSTAINED`.
- Adapters: `reflex/adapters/` — ollama (local llama3.1:8b, metered),
  openai-compatible endpoints, anthropic via the deferred-replay
  bridge (no direct API keys in this environment).
- Build phases: P1 skeleton (done) → P2 port + parity battery →
  P3 acquisition (breeder + miner, one gauntlet) → P4 demo + EXP-ACQ
  ablation A0–A3.

Prior versions live in `Downloads/reflex-poc*` and are never modified;
every ported file records its origin in a header comment.

Run the current checkpoint: `python tests/test_p1_skeleton.py`
(needs local ollama for the live adapter checks).
