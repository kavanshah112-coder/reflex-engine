# V1.9 bug audit (branch v1.9-reading)

Numbering continues the arc (B1–B36; S1 notes N1–N10 in bug_audit_s1.md).

## Note V1 — DEV A2 wrongs under one model (M-sonnet, 1,800; for the record, nothing tuned)

A2 admitted 948 of 1,260 executed readings; 5 disagree with gold:
- g0552 — "sales over $1000 get you an additional 10% commission":
  reading and sonnet apply 40% to the excess (900); gold applies 10%
  (450). Phrasing convention.
- g0590 — seats needed: reading counts invitees, friends, spouses
  (318); gold adds the host herself (319). **Genuine shared
  misreading** — the class the engine cannot see.
- g0768 — "twice as many … then 150 more": convention (S1 N5).
- g1048 — 21% per year depreciation: reading compounds (9,860.78),
  gold is linear on the original (7,400). Convention.
- g1309 — 430+750+300+700 = 2,180; gold 2,280. Gold error (S1 N5).
By class: 1 genuine, 3 conventions, 1 gold error. A2 by-gold rate
0.53%; genuine 0.11%. DEV is exposed data; the rules are frozen and
were not changed after reading this.

## Note V2 — proposer variance across bridge blocks (R12), sealed readings

Sonnet's sealed reading blocks returned null rates from 9/189
(batches 63–70, GSM8K-heavy) to 123/225 (batches 45–53, ASDiv
word-number and GCD/LCM heavy). Part is corpus mix; part is agent
variance in reading the constant rule — one agent treated "three/six/
ten" as unauthorised word-numbers although 3 and 6 are listed
constants. The prompt for the three later arms states the word→
constant mapping explicitly ("two"→2 … "six"→6, "a week"→7 …); the
sonnet blocks were not re-asked (readings are collected once). The
cost lands in REACH per corpus and is reported; no reading was
changed after the fact.

## Note V3 — SEALED A2 wrongs, M-sonnet (12 of 863; read after the run; nothing relabelled)

- **Gold errata / format (4):** a0375 (7 sets × 7 colours × 6 = 294;
  gold 42 = 7×6), a1332 (reading 2/5 = 0.4; corpus answer "5/2"),
  a1349 (perimeter 2·76 + 42 + 2·42 = 278; corpus formula treats 76
  as a perimeter, gold 90), g0454 (Marin and Nancy each 4/day × 30
  = 240; gold 150).
- **Rounding (4):** a1979, a1983, a1984, a1989 — means; reading exact
  (16.2857…), gold rounded to one decimal (16.3). R10 near-miss.
- **Unit convention (1):** a0175 (46 cents vs $0.46).
- **Interpretation conventions (2):** a1412 (does the father age
  during the 15 years: 45 vs 75), g0012 (break-even year 12 vs first
  earning year 13).
- **Genuine misreading (1):** g1035 — bottles every 3 ft on a 24 ft
  driveway, 5 s per gap: reading counts 8 gaps (40), gold 7 (35). A
  fencepost error the reading and the model's own answer shared.
By-gold FALSE-ADMIT 12/863 = 1.39%; GENUINE-WRONG 1 (0.12%).
SAFETY-GEN fails by one item; the letter follows.

## Note V4 — SEALED A2 wrongs, M-haiku (7 of 811)

Gold errata (3): a0375, a1349, g0454 (as above). Conventions (2):
a0185 (cents vs dollars), a2261 (whether the host counts: gold says
no here, though DEV g0590's gold said yes). Genuine (1): g0790 —
3/5 of 10 groups × 9 members × 2 shells = 108; reading dropped the
members per group (12). Haiku's readings are 89.4% correct vs
sonnet's 95.9%; the engine-only rule A1 admits 47 wrong of 852 for
haiku vs 29 of 882 for sonnet — the same-model answer is what carries
the small model to 7 (H9: scale monotone in reading quality; the
gates alone are not enough at any scale).

## Note V5 — SEALED A2 wrongs, M-opus (13 of 962)

Gold errata (3): a0375, a1349, g0454 (as V3). Gold format (3): a1332
(answer "5/2"), a1327 ("3/7" parsed as 3; reading 3/7 = 0.4286),
a1495 ("1/6" parsed as 1; reading 40/240 = 0.1667). Rounding (4):
a1979, a1983, a1984, a1989. Unit (1): a0175. Conventions (2): a1412
(father ages), g1161 (Abraham: "another 1/4 of his land" read against
the original 80 m² — 140 — where gold reads it against the remaining
40 — 170; the model's own answer shares the reading). Genuine (0).
Opus: READING-CORRECT 98.4%, G-P6 false-abstain 9.8%, GATE-COST
13.4%, A1 968/17 — the highest reading quality of the four arms; A2
13 wrong of which 10 are gold format/errata/rounding, 3 conventions.

## Note V6 — REUSE measured (nothing served): cue-keyed reuse is UNSAFE

`reader19v.py reuse` binds each SEALED item to the A2-admitted reading
of another item sharing its cue key (ask type, count, roles18 cues),
pure keys only, full gate stack, then grades by gold.

| arm | library | keys | pure | candidates | impure skipped | served | correct | WRONG |
|---|---|---|---|---|---|---|---|---|
| M-sonnet | 1,811 | 336 | 249 | 1,496 | 1,407 | 35 | 22 | **13** |
| M-haiku | 811 | 137 | 110 | 1,400 | 1,086 | 76 | 18 | **58** |
| M-opus | 962 | 182 | 134 | 1,449 | 1,383 | 40 | 22 | **18** |

REUSE-WRONG > 0 on every arm (37–76% of served). Two facts explain it:
(1) 94–95% of items with a candidate are on impure keys, as H6
predicted (CUE-PURITY on DEV 8.3%); (2) "pure" is vacuous for
singleton keys — a key with one reading has one signature by
definition, so the "pure" library is mostly keys with a single donor,
and the donor's structure says nothing about the recipient's
(`other|1|expr`, `count|2|unit:$,unit:$` fire the wrong plan).
The cue key does not determine the reading; ladder A is out; the
readings are one-phrasing reflexes. No item was ever served.

## Note V7 — SEALED A2 wrongs, M-fable (11 of 954); and the fable answer block relaunch

Gold errata (2): a1349, g0454. Rounding (4): a1979, a1983, a1984,
a1989. Unit (1): a0175. Conventions (3): a1412, g1161 (as V5), a2105
(florist: "2 lb for 9 days and then on the final day the normal
amount plus 4" — reading treats the final day as a tenth day, 24;
gold counts it among the nine, 22; the own answer agrees). Genuine
(1): g0796 — HR hires 20/month on 200, $4,000/employee/month, "total
paid after three months": reading pays the final workforce once
(260 × 4,000 = 1,040,000); gold sums three monthly payrolls
(220+240+260) × 4,000 = 2,880,000. The model's own answer shares the
misread (shared prior, R1). Fable: READING-CORRECT 97.6%, G-P6
false-abstain 9.4%, GATE-COST 13.6%, A1 962/18.

Process: fable answer batches 00–11 were reported written by the
first answer agent but were not on disk when the arm was reconciled
(the other 59 files were). The block was launched once more with the
same prompt before scoring; every file was then present, every
batch's id set matched its batch file, 0 "?" answers. No file was
overwritten; M-fable SEALED was scored once, after the recount.
Reuse (fable): library 954, pure keys 134, would-serve 38, WRONG 19
— the V6 finding on a fourth arm.

## Note V8 — The honesty gates bought nothing by gold on the large arms

A2 ⊆ A0 by construction. Wrongs removed by G-P6 + rules (A0 − A2):
sonnet 0 of 12, opus 0 of 13, fable 1 of 12 (g0814), haiku 12 of 19
(a1147, a1461, a1649…a1689 — a run of ASDiv items where haiku's
readings misuse word quantities). Cost: 13–17% of A0's admissions.
G-P6 kills / of which correct: 145/142, 108/108, 102/80, 105/102.
The filter that removes wrongs on every arm is agreement with the
model's own answer (A1 − A2: 17, 4, 40, 7). The gates were designed
from S1's sonnet/haiku pairing (where G-P6 removed 7 of 20); with
the same model in both roles, the wrongs that survive are shared
misreads and conventions that no lexical gate can see. Reported
prominently in the final report; nothing tuned after the sealed run.

## Note V9 — controls19v's S1-battery call rewrote results/v18/controls18.json

`reader19v.py controls` re-runs the V1.8 batteries as its
`s1_batteries` check; that call writes `results/v18/controls18.json`
and left it truncated (harvest_neg block dropped) in the working
tree. The file is a V1.8 artifact (tag v1.8-final); it was restored
from git before the V1.9 tag. No V1.9 number depends on it; the V1.9
control record is `results/v19/controls19v.json`.

## Note V10 — POST-HOC (after v1.9-final): "suggest, don't serve" reuse probe

`tools/reuse19_probe.py`. Not a sealed run; nothing served; no
threshold pre-registered. Every A2-admitted reading with the item's
cue key (impure keys included, ~187 candidates/item) is bound, gated
and executed; a candidate is ADMITTED only if its value agrees with
the model's OWN answer (P0), or agrees AND passes G-P6 + rules (P1).

| arm | P1 served / 1,764 | wrong by gold | of which already fresh-A2 wrongs | NEW ids | served where fresh reading was null/killed |
|---|---|---|---|---|---|
| sonnet | 688 | 8 (1.16%) | 4 (a0375, a1983, a1984, g0454) | a1460, a1477, a1481, a2268 | 91 |
| opus | 633 | 4 (0.63%) | 3 | a1481 | 58 |
| haiku | 612 | 3 (0.49%) | 3 | — | 69 |
| fable | 635 | 3 (0.47%) | 2 | a1481 | 60 |

P0 (no gates) serves ~150 more per arm with +1 wrong each, but 80–104
of those are ZERO-SLOT items (word-number questions) served by a
constant plan whose value happened to equal the own answer; P1 cuts
zero-slot serves to 8–13. Zero-slot candidates must be excluded by
construction in any spec (a constant is not a computation).

Every NEW wrong is a MULTI-ANSWER ask the proposer had declined
("how much did each cost", "how long are the pieces", "find the
present ages", "cases plus extra boxes"): the own answer gives one of
the two asked quantities, gold the other; a reused plan reproduces
it. Genuine misreads among the new wrongs: 0. A structural rule
S-MULTI (ask names two quantities) would remove all of them; it is
NOT applied here — it belongs on DEV in a later version.

Sonnet with a DEV-only library (948 readings, none from the sealed
set): P1 623 served / 6 wrong (0.96%) — the result does not depend on
cross-serving inside the sealed set.

Is the reused plan the RIGHT reading or a coincidence? On items where
the model's own fresh reading was A2-admitted, the reused plan has the
same bound signature 82.3% (sonnet), 93.4% (opus), 81.2% (haiku),
94.0% (fable) of the time; the different-plan serves were wrong 0/104,
0/38, 1/101, 0/34. So the served VALUE is as safe as fresh A2, but
~6–19% of reuse "hits" are a different computation that reproduces
the answer on these numbers — a reflex minted from such a hit would
be the wrong reading. Minting from reuse needs plan agreement with
a fresh reading (two-donor rule), not value agreement alone.

Reading: the binder CAN suggest; the own answer is the filter;
transfer exists at 35–39% of the sealed set with no proposer call,
at the fresh-A2 wrong rate. This is the V1.10 candidate.
