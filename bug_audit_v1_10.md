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
