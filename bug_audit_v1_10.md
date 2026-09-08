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

## B38 — P-tier fresh readings gated by the wrong gate (caught on the ACQ P1 test, pre-sealed)
`fresh_P` passed model-proposed chain plans (literal values) through
plangate18, whose G-P4′ expects role-slot templates and killed 20 of
22 with "unrolled numeric slot". Literal plans are the V1.7 plan
language and are gated by plangate17 (G-P1..G-P5): all 20 pass it.
Fixed before any DEV/SEAL run; the suggest path for P tiers still uses
binder18 + plangate18 on templates, unchanged.

## N9 — an author agent delegated to sub-agents
The sonnet T4 wave-0 author wrote batches 000–002 and 007 itself and
spawned its own sub-agents for 003–006, then stopped before they
reported. Files present at check: 000, 001, 002, 007. The model that
wrote 003–006 (if they arrive) is the sub-agent's model, which the
harness defaults to the parent's; recorded as sonnet with this
caveat. Missing batches are relaunched in a later wave. Usage for the
sub-agents is not visible to the token log (their tokens are not in
the parent's figure) — flagged for the TOKENS metric: authoring
tokens are a dataset-construction cost and are not part of
TOKENS/QUERY, so the metric is unaffected.

## B39 — grader dropped exponents (found on the D-arm ACQ baseline, pre-sealed)
Full-precision golds are stored with repr(); a true-zero chain result
replays as 1.8e-19 and `S1.parse_answer` reads "1.8" (its regex has no
exponent). 32 of the baseline's 33 "wrongs" were exact-zero serves
graded against 1.8. Fix: engine110 parses golds and own answers with
float() first, S1.parse_answer as fallback. S1 itself is frozen and
untouched. Baseline re-run after the fix.

## B40 — the V1.6 minted library fired on a word problem (D-arm ACQ baseline, pre-sealed)
GSM8K-train "Tim sleeps 6 hours per day for 5 days a week and 10 hours
a day for the other 2. How much total sleep?" — ask16 escalated, then
`acquire16.apply_library` served 360 via reflex16:sonnet:
conv_hour_to_minute (gold 50). A B32-class lexical replay from a
library minted for the scientific domain. Fix: the library is consulted
only when the reader found a unit-cued quantity in the question. One
item in 3,024 T3; DEV/ACQ are tuning splits, so the fix is in scope;
the sealed run inherits it. The D-arm baseline before the fix:
ACQ 142,653 non-authored items, 48,171 exact serves, 1 genuine wrong
(this item), P1 27,913/0, P2 16,240/0 true, P3 4,017/0 true, T1/T2/T3′
0 served, PC 0 served, D 0 served.

**B40b.** The unit-cue gate did not stop the Tim item (its key carries
`unit:hours`); the rerun baseline (`base2`) served it again — the ONLY
wrong in 47,866 exact serves over 142,653 ACQ items. The V1.6 library
contributes 6,932 P1 serves and 1 T3 serve in ACQ. Gate changed to the
ask type: the library is consulted only for `other`/`ratio` asks
(every P1–P3 item; 364 of 3,024 T3 items remain eligible) and never
for `count`/`amount` story asks. Baseline re-run as `base3`.

## N10 — session rate limit (2026-09-08 ~19:30 IST, reset 20:30): 20 bridge agents terminated mid-job
Every running agent died with HTTP 429. Files already written were
kept; partial JSON files (haiku P4 032, 055, 056, 057 unparseable;
haiku P4 007, 029–031 and haiku T4 024, 048, 065–070 with missing ids)
are treated as absent and re-authored — the only case in the arc where
a bridge file is overwritten, and only because it is not valid data.
Tokens of the killed agents are not in `usage.jsonl` (the harness
reports usage only on completion); TOKENS/QUERY is computed from
completed jobs only. Reconciliation (`author_*` vs `authored_*`,
`ansq_*` vs `ans_*`, `readq_*` vs `read_*/reading_*.json`) drives
every relaunch; nothing is launched twice for an id that already has a
file.

**Cut decision (spec §11.2 cut order, applied now):** authoring
throughput is ~8 batches per 17 min per large-model agent; 600 batches
remained. P4 authoring stops at what exists (≈5,100 of 10,000 items,
above the 4k cut); T4 continues to 8,000 items (320 batches) and stops.
Unauthored T4/P4 items have no text and are simply absent from every
split; the effective workload is reported with the realised sizes.

**Baseline after B39/B40b (`base3`):** ACQ 142,653 non-authored items,
48,170 exact serves, 0 wrong, 0 PC served, 0 distractor served.

## N11 — haiku over-nulled one reading block
Haiku's T3 28–31 + T3′ 0–3 reading block returned 164 nulls of 200
(other models: 0 nulls on the same T3′ batches) and wrote the files
with 28 tool calls, i.e. in bulk. The readings are the proposer's
output and stand as collected — a second pass would be a second sample
of the proposer, which the one-reading-per-item protocol forbids. The
effect is a lower haiku fresh-reach on those items; reported per tier.
