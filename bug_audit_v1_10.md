# V1.10 ledger (branch v1.10-suggest; spec frozen v1.10-plan)

## N1 — P3 generator constraint relaxed at build
The V1.7 chain generator never places two physics steps in one chain
(unit state after a physics mid blocks a second). P3 was specified as
"≥2 physics leaves"; that stratum is empty by construction. P3 = k 5–6,
≥1 physics step, ≥2 domains, non-monotonic (acceptance ~29%). Logged
before any run; spec §5.1 text stands with this note.

## N2 — Tooling: heredoc backslashes
Two attempts to write the S-MULTI regex through a bash heredoc lost
every `\b` (the shell ate the backslashes; the file carried backspace
characters). Rewritten with explicit chr(92). Controls: S-MULTI_pos,
_pos2, _neg all pass; `controls110.json` pass=true.

## N3 — Token instrument positive control (procedural)
Two sonnet answer agents on `ansq_ctl_full.json` (25 trivial items)
and `ansq_ctl_empty.json` (0 items); harness-reported usage of both is
logged in `bridge/usage.jsonl`. The instrument passes if empty < full
and both are non-zero. (B7/B24: never the agent's self-report.)

**N3 result (calibration, before any run):** sonnet full batch of 25
trivial items = 65,932 harness tokens; empty batch = 64,522. The
instrument passes (empty < full, both non-zero) and shows that the
harness-reported figure is ~98% fixed agent overhead (system prompt,
tool definitions). TOKENS/QUERY is therefore defined as MARGINAL
tokens: (batch tokens − the model's empty-batch baseline) ÷ items,
with the raw figure reported beside it. Empty-batch baselines are
collected per model (sonnet 64,522; opus/haiku/fable below). This is
an instrument definition fixed before the sealed run, not a tuning.

## N4 — W-400K built: 387,062 items
Tier quotas met exactly (T1/T2 80k, T4 20k, P1 80k, P2 60k, P3 40k,
P4 10k) plus corpora (T3 7,473; T3′ 1,000; PC 1,000) and a 2%
distractor overlay (7,589) = 387,062, i.e. "≈400k" in the spec is
387k. Rejects: T2 5,207 (unsolvable draws), P2 124,001, P3 92,890
(generator constraints), P4 23,682. Splits acq 154,653 / dev 38,475 /
seal 96,847 / replay 97,087. Hashes in `results/v110/data/HASHES.json`.
Authoring requests: 1,200 batches of 25 (800 T4, 400 P4), author model
by id hash. Build wall time ~25 min.
