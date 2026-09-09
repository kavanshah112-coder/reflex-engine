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

## N12 — ACQ arm passes on the non-authored tiers (`<arm>_acq_base`, lib_<arm>_acq1.json)
Opus / haiku / fable run over 142,653 ACQ items (3,100 sampled per arm)
seeded with the V1.9 A2 library; sonnet running. Exact path 51,353 /
50,811 / 51,588 serves at 0 wrong (up from the D-arm 48,170 by the
P-templates minted from fresh chain readings: 250 / 102 / 251). A2S
served 426 / 337 / 406 with 1 / 7 / 4 wrong by gold; every A2S wrong
equals the model's own answer by construction (A2S = agreement), and
on ACQ they are dominated by SVAMP items whose gold is itself
contestable (T3′ 000717 "second chapter" gold 13, 000497 "$4, 99 bars
at $3" gold 1, 000844 "21 roses, threw away 34") plus haiku own-answer
errors (T3 006976 arithmetic-series, 007019). Classification is done
after SEAL; nothing here is relabelled. KC (shadow) served 0 / 0 / 10
with 0 / 0 / 1 wrong — consistent with H9. Haiku's own answers on the
physics tiers are weak (P1 210/300, P2 133/300, P3 123/300), so its
fresh A2 on P-tiers is small; the model-free chain path is unaffected
(0 wrong). Acquisition curve (A2S cumulative at 40k…140k): opus
0/0/5/35/136/288, haiku 0/0/4/32/114/246, fable 0/0/7/48/147/287 —
zero for the first 60k because the id order walks D, P1–P3, PC before
T1; the curve is reported against the T-tier position in the report.

## N13 — Fable model limit (2026-09-08 ~22:30 IST) and one stray file
Two fable T4 authoring agents (w04 033–040, w05 041–048) died with
HTTP 429 (per-model Fable limit, not the session limit of N10). Files
033–038 were complete and kept; 039–048 relaunched 2026-09-09 as two
5-batch jobs (user: "when limit comes back automatically start").
A haiku authoring agent wrote `authored_T4_haiku_141.json` to
`<repo>/bridge/` instead of `results/v110/bridge/` (20 ids, of which
17 duplicate the correctly-placed file and 3 are ids that do not exist
in the request); moved to `results/v110/bridge/stray_authored_T4_haiku_141.json`,
not merged.

## N14 — haiku wrote six reading files for ids that exist in no batch
`read_haiku_dev/` holds 900 files against 894 DEV batch ids: six
files (`w10_T3p_000001…000004`, `w10_T3p_001559`, …) name ids that
appear in no `readq_dev_*` batch (the T3′ DEV sample has 94 items, so
haiku's last block "completed 25" by inventing ids). The engine loads
readings by the item id it is scoring, so invented ids are never
read; the files are kept, not deleted, and counted here. Sonnet, opus
and fable: 0 extra ids.

## N15 — authored stories merged; QC restricted to the scored set; hashes re-recorded
`author_merge110 stories` merged 7,881 T4 and 5,277 P4 stories (28
ids skipped as already present from the redo files); the four workload
files were verified against HASHES.json immediately before the merge
(all MATCH) and re-hashed after it (`HASHES.json["post_authoring"]`).
The unrestricted QC set would have been 529 batches (13,158 items);
under the spec amendment's budget clause QC is restricted to every
authored item in SEAL and REPLAY plus the E-SAMPLE authored items of
ACQ and DEV: 7,745 items, 314 batches (`author_merge110 qcbatches`;
the 529 unrestricted `qcq_*` files it replaced were engine-generated
inputs, not bridge outputs). Un-QC'd ACQ/DEV authored items keep
`qc="pending"` and are scored by the engine paths only. QC model map:
sonnet→opus, opus→sonnet, haiku→fable, fable→haiku. The fable w04b
authoring agent rewrote its own 039/040 files once before finishing
(word-form step values corrected to digits) — its own in-progress
output, not established data.

## N16 — a sonnet DEV reading agent reports having "run a slot-substitution check"
The sonnet T3 0–7 DEV reading agent reported that its 193 non-null
plans "parse and evaluate cleanly under a slot-substitution check I
ran against the stated numbers" — i.e. it executed its own plans
(against the Read/Write-only instruction, cf. N6). It had no golds,
so the check cannot have tuned readings toward the answer; it can
only have removed syntactically broken plans, which the engine would
have nulled anyway. The readings stand as collected; reported here.

## N17 — QC applied; QC-rejected items are not scored on any split (engine change before any sealed run)
`author_merge110 qc` over 314 batches (7,745 items): T4 4,265 pass /
290 reject; P4 2,834 pass / 356 reject; 536 rejected SEAL/REPLAY items
moved to dev (`split_original` kept). Rejects by author: haiku T4
259 of 2,058 QC'd (12.6%), haiku P4 255 of 1,509 (16.9%); sonnet 2 /
5, opus 16 / 5, fable 13 / 91 (fable P4 91 of 548 — the fable-authored
P4 stories carry narrated intermediates that the QC model (haiku)
answered from). QC models reported the dominant reject mechanisms:
haiku-authored stories that (a) narrate a wrong intermediate value
("the derivative … yields 11" when it is 10) or (b) ask for an
intermediate state (the wave-0 misreading of the feature, N7), and a
handful of truncated or self-contradictory texts. Post-QC SEAL holds
T4 1,772 / P4 1,175 authored items, REPLAY T4 1,887 / P4 1,175, all
QC-passed. `engine110.run` now skips items with `qc == "reject"` on
every split (counted as `qc_rejected` per tier) — ACQ/DEV rejects
were previously scorable against a disputed gold; SEAL/REPLAY had
none left. This is an engine change made before any sealed run and
after the D-arm baselines, which contain no authored items. Files
re-hashed as `HASHES.json["post_qc"]`; the ACQ/DEV T4/P4 E-SAMPLE
(500/400 and 150/150) was drawn after QC.

## N18 — haiku over-nulled the ACQ T4 9–17 reading block (as N11)
Haiku's T4 batches 009–017 (225 items) came back 213 null / 12 plans (and its T4 018–019 + DEV T4 block 134 null / 66 plans, 53 tool calls),
written with 23 tool calls (bulk, i.e. not one Write per file — the
N6 class of instruction breach). The other three models' T4 blocks
are reported when they land. As in N11 the readings stand as
collected (one reading per item, never re-sampled); the effect is a
lower haiku fresh reach on T4, reported per tier.

## N19 — sonnet P4 answer files written under rotated names (renamed, not rewritten)
The sonnet "acq P4 12–15 + dev P4" answer agent wrote seven files
whose contents belonged to the NEXT batch in its list (the answers
for `ansq_dev_P4_000` landed in `ans_sonnet_acq_P4_015.json`, …, the
answers for `ansq_acq_P4_015` in `ans_sonnet_dev_P4_005.json`): every
id→answer pair is internally consistent (each file holds exactly the
25 ids of one batch), only the file name was off by one. Because the
engine loads answers per split by file name, the mislabelled files
would have dropped 25 ACQ ids and 25 DEV ids. Fix: the seven files
were renamed to the batch whose ids they contain (a pure rotation; no
content changed, nothing overwritten), verified id-exact afterwards.
A second sonnet answer agent (T4 12–19 + dev T4) reported catching
and correcting the same class of slip on its own before writing.

## N20 — second session limit (2026-09-09 ~23:20 IST, reset 03:00): 14 reading agents killed
The session usage limit terminated every running sonnet/opus/fable
T4/P4 reading agent mid-job (haiku's completed). Files already
written are kept; the same jobs are relaunched with the same prompts
("skip if the file exists"), as in N10. Tokens of killed agents are
not in usage.jsonl. Haiku's bulk-written blocks left 25 ACQ P4 and 25
DEV T4 ids without a file (its reports claimed full coverage); those
two blocks are re-issued with skip-if-exists.

## N21 — M-sonnet ACQ pass and the three DEV passes (acq1 libraries)
Sonnet ACQ (142,653): exact 51,169 / 0 wrong; A2S 466 / 4 wrong (all
T3′ = SVAMP items whose own answer equals the served value: 000497,
000595, 000717, 000849); fresh A2 1,650 / 10 wrong (T3, all own-answer
agreements on GSM8K items with contestable golds or own errors); KC
served 3 / 3 WRONG (H9's prediction, on the primary arm); library T
1,144 / P 251 / probated 44. Curve 0/0/13/89/172/299.
DEV (35,510 non-authored items, dev1 tag, acq1 library, sonnet
running): haiku exact 13,164 / 0, A2S 116 / 4 wrong (T3′, own-answer
errors: 000301, 000491, 000753, 000997); opus 13,213 / 0, A2S 164 / 0;
fable 13,340 / 0, A2S 161 / 0, KC 2 / 0. PC certified 0 on all;
distractor served 0. Post-hoc check for "echo" donors (plans without
an arithmetic operator, which would agree with any own answer that
restates a stated number): none exist among the suggested serves on
any arm — no rule added from DEV; Z-SLOT/S-MULTI stand as frozen.

## N22 — M-haiku ACQ pass on the authored tiers (acq2)
5,356 ACQ T4/P4 items (4,000 sampled; 88 QC-rejected skipped): exact
path 0 serves (no deterministic path exists for authored prose, as
designed); fresh A2 admitted 65 / 0 wrong (T4 45, P4 20); A2S served 1
/ 0 wrong (T4); A0S 2 / 1 wrong (the agreement-only rule, reported).
Haiku's own answers on T4 are 287/465 correct and on P4 255/347, so
the own-answer filter admits little. P4 readings: 103 in a
non-chain format, 206 killed by plangate17, 7 refused at execution,
31 executed (30 right) — the reach on authored physics stories is
low, as H6 predicted, and every P4 wrong-by-gold count is 0. Library
T 458 / P 104 after the pass (lib_haiku_acq2).

## N23 — M-haiku DEV pass on the authored tiers (dev2, acq2 library)
1,793 DEV T4/P4 items (558 QC-rejected skipped — DEV now holds the
536 rejects moved out of SEAL/REPLAY): exact 0, A2S 0, fresh A2 6 / 0
wrong (T4), P4 readings 83 non-chain format + 5 gate kills, 0
executed. Haiku's own DEV answers are poor here (T4 29/105, P4 1/88
by gold at the engine's tolerance; its ACQ P4 answers were 255/347),
which is why almost nothing is admitted — a bridge-quality fact about
the haiku answerer on this block, reported, not repaired. All answer
files were re-verified id-exact against their batches (no rotation of
the N19 kind on any model).

## N24 — M-fable ACQ pass on the authored tiers (acq2)
5,356 ACQ T4/P4 items (4,000 sampled): fresh A2 admitted 274 / 2
wrong by gold (T4 197/2, P4 77/0); A2S served 7 / 0 wrong; own
answers 802/812 correct. Both A2 wrongs (T4 007181, 014572) are
haiku-authored stories whose "unit change stated in words" feature
was rendered as an ask in the converted unit ("in minutes", "in
hours") while the gold is the raw operation chain — the model's own
answer and the executed reading agree with each other and disagree
with the gold; on SEAL such items fall in the post-hoc class
"convention / authoring artefact". plangate17 kills 232 T4 and 268
P4 fresh readings (the authored stories carry restated intermediates
that the gate reads as unrolled literals). Library T 808 / P 254.

## N25 — M-fable DEV pass on the authored tiers (dev2)
1,793 DEV T4/P4 items (558 QC-rejected skipped): fresh A2 admitted 66
/ 0 wrong (T4 46, P4 20); A2S 2 / 0; own answers 192/193. No rule
change from DEV on any arm so far (haiku, fable on T4/P4; haiku,
opus, fable on the non-authored tiers): Z-SLOT and S-MULTI stand as
frozen and plangate17 remains the P-reading gate.

## N26 — one reading file rewritten by its own proposer (content identical)
The relaunched sonnet P4 8–15 reading agent reported overwriting
`read_sonnet_acq/reading_w10_P4_000584.json` before noticing it
existed. The committed first version (commit 5ef98163) and the
rewritten file are byte-for-byte the same plan, so the one-reading-
per-item rule is intact; recorded because it is the only overwrite
of a bridge output in V1.10. Opus's relaunched T4 9–17 agent
composed the word-multipliers "eight"/"nine" from listed constants
(`*2*4`, `*3*3`) on four items instead of nulling as instructed;
those readings stand (the engine's gates judge them), reported here.

## N27 — M-opus ACQ pass on the authored tiers (acq2)
5,356 ACQ T4/P4 items: fresh A2 admitted 284 / 2 wrong (T4 208/2, P4
76/0); A2S 7 / 0; own answers 799/812. The two A2 wrongs (T4 013526
"both lost 57 marbles" — per-player vs combined; 014572 — the
"in hours" ask over a minute chain, the same item fable missed) are
haiku-authored ambiguities where the model's own answer and the
executed reading agree with each other and not with the raw chain
gold. Library T 918 / P 253 (lib_opus_acq2).

## N28 — M-sonnet ACQ pass on the authored tiers (acq2) and M-opus DEV (dev2)
Sonnet ACQ T4/P4 (5,356): fresh A2 admitted 261 / 4 wrong (T4 201/4,
P4 60/0); A2S 6 / 0; own 790/812. The four T4 wrongs are all
haiku-authored ambiguity or unit-tail items (003171 "needed for the
expansion" total-vs-increment; 004488 "5 for every lantern still
hanging" add-vs-become; 007181 and 014572 the minute/hour asks seen
on the other arms); in each the own answer equals the executed
reading. Library T 1,325 / P 255 (lib_sonnet_acq2).
Opus DEV T4/P4 (1,793): fresh A2 65 / 1 wrong (T4 002567 "all 8
batches delivered to a partner" — remaining-vs-no-op), A2S 3 / 0, own
190/193. Across the four arms the authored-tier wrongs are the same
handful of haiku-authored ambiguities; no engine rule is added — the
wrongs are the model's own readings of an ambiguous story, exactly
the class the version was designed to expose.

## N29 — M-sonnet DEV (dev2) and SEAL answer coverage
Sonnet DEV T4/P4 (1,793): fresh A2 64 / 0 wrong, A2S 3 / 0, own
186/193. With that, every arm has completed ACQ and DEV on the
authored tiers with no engine rule added (RULES: no DEV-set rule
beyond the frozen Z-SLOT/S-MULTI; their DEV cost is computed in the
report from the rows).
SEAL answer coverage after the first wave: opus and fable complete
(122/122 batches, ids exact); sonnet P4 009–011 and haiku P4 007–011
still running; haiku's P3+D agent wrote only P3 000–003 + D 000–003
of its 14 batches (reported "14 files") — P3 004–009 re-issued as a
fill job; haiku `T3_020` holds 24 of its 25 ids plus one invented id
(kept as written; the one unanswered item simply has no own answer
on the haiku arm).

## N30 — proposer memorisation caveat on GSM8K-train items
The sonnet SEAL T2/T3 reading agent reported that it "cross-checked
several of the harder T3 problems against their well-known canonical
answers" — i.e. it recognised GSM8K-train items and their published
answers from pre-training. No gold was shown to any agent, but T3 is
the public GSM8K training split, so a reading proposer can anchor a
plan on a remembered answer; T3′ (SVAMP), T4 and P4 do not have this
property. Reported as a caveat on the T3 reading-quality numbers of
every arm (it is a contamination fact about the corpus, not a
protocol breach); the authored tiers are the clean test of reading.

## N31 — haiku over-nulls on SEAL (same class as N11/N18)
Haiku's SEAL reading blocks came back with far more nulls than the
other three proposers on the same batches: P1+P2 0–1 (all 50 P2
items null, "need full symbolic parsing"), T3 12–21 64/250 null,
T3′ block 68/250, T3p+T4 0–7 63/242, T4 8–15 18/200, T2/T3 block
54/250 written in bulk with 21 tool calls; its T3 2–11 block was
delegated to a sub-agent (N9 class). Sonnet/opus/fable on the same
batches: 0–25 nulls per 250. Readings stand as collected (one reading
per item, never re-sampled); the effect is a lower haiku fresh reach
on SEAL, reported per tier, and is itself a scale finding (H10).
