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

## B37 — builder rounded float golds to two decimals (caught by the D-arm smoke test, pre-run)
`build_w400k.fmt` formatted every gold with "%.2f"; for P1–P4 the
true value is a float (current 0.148148… stored as "0.15"). The V1.6
path served the exact value and was graded WRONG 90 times in 531
serves on a 600-item DEV smoke test — the engine was right, the gold
was wrong. Fix: P1 golds restored from the stored witness value, P2–P4
recomputed by chain_witness17.replay(plan); the rounded value is kept
as `gold_rounded`; HASHES.json updated with a note; builder patched.
No sealed run had happened. T-tier golds are integers and unaffected.
Lesson (again): a grader disagreement is a claim about BOTH sides.

## N5 — distractor texts: sentence split on abbreviations
`gen_distractor` cut the source story at its last ". " to drop the
numeric ask; names like "Ms. Okafor" / "Mr. Lopez" made some D items
keep a truncated numeric fragment before the non-numeric ask ("How
many cookies does Ms. Write one sentence about what happens next.").
They remain no-answer items (gold_type none): a served value is still
a SAFETY2 hit by construction. Left as built (already sampled and
answered); the wart is reported, not repaired.

## N6 — bridge protocol deviation (harmless)
The sonnet D-tier answer agent wrote its 8 files with a Bash/Python
snippet instead of the Write tool and disclosed it. Contents verified
(200 × NONE). Logged; no re-run.

## N7 — authoring brief: "intermediate quantity's final state" misread (wave 0, haiku)
Haiku's first 200 T4 stories were spot-checked: the feature "the
question asked about an intermediate quantity's final state" was read
as "ask for an intermediate result", which changes the answer away
from the plan's final value (e.g. "after the video call and gaming,
how many minutes remained?" with three more steps in the plan). Other
stories map "×8" onto nonsense ("each loaf was sold to 8 customers").
QC (a different model answers the story; must equal the plan's value)
is the designed catch: failing items become DEV-only. From wave 1 the
author prompt states explicitly that the question must ask for the
FINAL result after ALL steps and that the feature means the story
follows one quantity through its changes. The build's feature list is
unchanged; the prompt wording is a bridge-protocol fix, logged here.

## N8 — g = 9.81 vs the generator's 9.8
Opus and fable answer potential-energy items with g = 9.81; the P1
generator and the chain language use 9.8. The 0.1% gap exceeds the
agreement tolerance, so on those items the own answer will REJECT a
correct reading (false rejection, counted in A2_rejected, never a
wrong). Reported per arm; no tolerance change (frozen).
