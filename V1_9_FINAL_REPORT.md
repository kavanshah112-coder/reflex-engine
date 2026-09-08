# V1.9 FINAL REPORT — One-Model Reading Reflexes with Escalation Feedback (branch v1.9-reading)

**Pre-registered outcome: E** on the frozen ladder (`V19_SPEC.md` §10, tag `v1.9-plan` @ 209bba7).

## Headline

- **Primary arm M-sonnet (sonnet answers AND proposes), SEALED 1,764 never-sampled items, run once:** REACH 61.1% (1077 executable readings), READING-CORRECT 95.9%, own answer correct 95.1%; A2 admitted 863, **FALSE-ADMIT by gold 12 (1.4%)**, of which **GENUINE 1** (g1035). SAFETY-GEN **fails by one item**.
- **M-opus:** REACH 63.4%, READING-CORRECT 98.4%, own answer 95.2%; A2 962 admitted / 13 wrong by gold (1.4%) / **0 genuine** (none).
- **M-haiku:** REACH 58.3%, READING-CORRECT 89.4%, own answer 95.0%; A2 811 admitted / 7 wrong by gold (0.9%) / **1 genuine** (g0790).
- **M-fable:** REACH 63.1%, READING-CORRECT 97.6%, own answer 95.2%; A2 954 admitted / 11 wrong by gold (1.1%) / **1 genuine** (g0796).
- **Negative, prominent:** the engine-side honesty gates (G-P6 + S-INT/RATIO/PCT/GEOM) removed 0/12, 0/13, 12/19, 1/12 of the by-gold wrongs that agreement alone (A0) would have admitted, while killing 17%, 13%, 13%, 13% of A0's admissions; every wrong they did remove was on haiku. G-P6 killed 145, 108, 102, 105 readings of which 142, 108, 80, 102 were correct. The filter that carries the safety is the model's own answer (A1→A2 removes 17, 4, 40, 7 wrongs).
- **Reuse (measured, never served):** M-sonnet 35 would-serve / **13 wrong**; M-opus 40 would-serve / **18 wrong**; M-haiku 76 would-serve / **58 wrong**; M-fable 38 would-serve / **19 wrong**. Cue-keyed reuse is unsafe on natural text; ladder A is out on every arm.
- **CUE-PURITY (DEV, sonnet):** 8.3% (7 pure of 84 keys with ≥2 readings; 206 singleton keys).
- **GATE-CTRL:** PASS (14 checks).

## 1. What was run

V1.9 asks whether ONE model — the same model that answers the escalated question — can propose a READING (a plan over the question's stated numbers as positional slots plus structural constants) that the engine admits with zero genuine wrong admissions, the engine carrying the safety. S1 (the pre-study, tag `s1-final`) had shown that agreement between an engine-computed reading and a *second* model's answer admits ~1.1% wrong by gold; the user ruled out a second model, so V1.9 replaces it with three engine-side gates plus the model's own answer: **G-P6 lexical honesty** (word quantities, plural named agents, cardinality matching), four **structural abstentions** (S-INT, S-RATIO, S-PCT, S-GEOM), and **A2 = engine gates + agreement with the model's own answer**. Two weaker rules are reported alongside: A0 (agreement only, S1's rule) and A1 (engine gates only, no agreement).

The sealed set is 1,764 GSM8K-test and ASDiv items never sampled by S1 (sha256 in `results/v19/data/`), in 71 batches of 25. Four arms, one model each, both roles: sonnet (primary), opus, haiku, fable. Every proposer and answerer ran as a bridge agent with Read/Write only, saw only the batch file (question text + numbers), never the golds, never the engine. Readings were bound, gated through the V1.8 stack in reading mode, executed by the witness, and graded against the corpus gold offline. DEV (S1's 1,800 items with sonnet's S1 readings and fresh sonnet answers) was used to set G-P6 and the rules before the sealed run; SEALED was scored once per arm.

## 2. Results per arm (SEALED 1,764, run once)

| arm | executed (REACH) | reading correct | own answer correct | G-P6 kills (false-abstain) | rule kills S-INT/RATIO/PCT/GEOM | GATE-COST | A0 adm/wrong | A1 adm/wrong | **A2 adm/wrong (FA)** | **genuine** | A2 rejected-but-correct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M-sonnet | 1077 (61.1%) | 95.9% | 95.1% | 145 (13.8%) | 14/32/11/0 | 18.1% | 1042/12 | 882/29 | **863/12 (1.4%)** | **1** | 182 |
| M-opus | 1118 (63.4%) | 98.4% | 95.2% | 108 (9.8%) | 3/32/11/0 | 13.4% | 1111/13 | 968/17 | **962/13 (1.4%)** | **0** | 151 |
| M-haiku | 1028 (58.3%) | 89.4% | 95.0% | 102 (8.7%) | 15/57/9/0 | 17.1% | 937/19 | 852/47 | **811/7 (0.9%)** | **1** | 115 |
| M-fable | 1114 (63.1%) | 97.6% | 95.2% | 105 (9.4%) | 9/32/11/0 | 13.6% | 1098/12 | 962/18 | **954/11 (1.1%)** | **1** | 144 |

DEV 1,800 (M-sonnet, for the record; used to set the gates): REACH 67.2%, READING-CORRECT 97.2%, own answer 95.3%, A0 1191/21, A1 960/11, A2 948/5 (0.5%), GATE-COST 20.7%, G-P6 false-abstain 15.5%.

Per corpus, M-sonnet: gsm8k n=419 executed 322 reading-correct 312 A2 admitted 221 wrong 3; asdiv n=1345 executed 755 reading-correct 721 A2 admitted 642 wrong 9.
Per corpus, M-opus: gsm8k n=419 executed 327 reading-correct 324 A2 admitted 256 wrong 2; asdiv n=1345 executed 791 reading-correct 776 A2 admitted 706 wrong 11.
Per corpus, M-haiku: gsm8k n=419 executed 244 reading-correct 200 A2 admitted 164 wrong 2; asdiv n=1345 executed 784 reading-correct 719 A2 admitted 647 wrong 5.
Per corpus, M-fable: gsm8k n=419 executed 325 reading-correct 319 A2 admitted 257 wrong 3; asdiv n=1345 executed 789 reading-correct 768 A2 admitted 697 wrong 8.

Three readings of the table. First, A1 versus A2: the engine's gates alone admit 29 (M-sonnet), 17 (M-opus), 47 (M-haiku), 18 (M-fable) wrong by gold; adding agreement with the model's own answer removes 17, 4, 40, 7 of them. The own answer is the filter that works, even though it shares the reading's prior. Second, A0 versus A2 (A2 is a subset of A0): the honesty gates removed **0 of 12 (M-sonnet), 0 of 13 (M-opus), 12 of 19 (M-haiku), 1 of 12 (M-fable)** of A0's by-gold wrongs while costing 17%, 13%, 13%, 13% of its admissions — on the three large models G-P6 and the structural rules bought nothing by gold on this corpus; they only earned their keep on haiku. Third, scale (H9): reading quality orders opus > fable > sonnet > haiku, and so does A1's wrong count; genuine counts are 1 (M-sonnet), 0 (M-opus), 1 (M-haiku), 1 (M-fable).

## 3. Every by-gold wrong under A2, classified after the run (nothing relabelled)

| arm | by gold | gold errata | gold format | rounding | unit conv. | convention | **GENUINE** | ids |
|---|---|---|---|---|---|---|---|---|
| M-sonnet | 12 | 3 | 1 | 4 | 1 | 2 | **1** | a0175 (unit convention), a0375 (gold errata), a1332 (gold format), a1349 (gold errata), a1412 (convention), a1979 (rounding), a1983 (rounding), a1984 (rounding), a1989 (rounding), g0012 (convention), g0454 (gold errata), g1035 (GENUINE) |
| M-opus | 13 | 3 | 3 | 4 | 1 | 2 | **0** | a0175 (unit convention), a0375 (gold errata), a1327 (gold format), a1332 (gold format), a1349 (gold errata), a1412 (convention), a1495 (gold format), a1979 (rounding), a1983 (rounding), a1984 (rounding), a1989 (rounding), g0454 (gold errata), g1161 (convention) |
| M-haiku | 7 | 3 | 0 | 0 | 2 | 1 | **1** | a0175 (unit convention), a0185 (unit convention), a0375 (gold errata), a1349 (gold errata), a2261 (convention), g0454 (gold errata), g0790 (GENUINE) |
| M-fable | 11 | 2 | 0 | 4 | 1 | 3 | **1** | a0175 (unit convention), a1349 (gold errata), a1412 (convention), a1979 (rounding), a1983 (rounding), a1984 (rounding), a1989 (rounding), a2105 (convention), g0454 (gold errata), g0796 (GENUINE), g1161 (convention) |

Classes. *Gold errata*: the corpus answer does not follow from the text (a0375 7×7×6 vs gold 7×6; a1349 a perimeter formula that contradicts the stated figure; g0454 two people × 4/day × 30 = 240 vs gold 150). *Gold format*: the corpus answer is a fraction the grader parses as its numerator ("5/2", "3/7", "1/6"); the reading's value is the fraction. *Rounding*: means given exact where gold rounds to one decimal. *Unit convention*: cents vs dollars. *Convention*: a defensible reading the corpus does not share (does the father age during the 15 years; break-even year vs first earning year; "another 1/4 of his land" against the original vs the remainder; whether the host counts; whether "the final day" is a tenth day). *GENUINE*: the reading is wrong and the model's own answer shares the error — g1035 (sonnet: bottles every 3 ft on 24 ft, 8 gaps vs 7), g0790 (haiku: dropped the members-per-group factor), g0796 (fable: paid the final workforce once instead of three monthly payrolls). Full rows: `results/v19/M-<arm>_sealed_rows.json`; ledger `bug_audit_v1_9.md` notes V3–V7.

## 4. What honesty costs, and what it buys

G-P6 kills almost only correct readings (kills / of which correct: 145/142, 108/108, 102/80, 105/102): on this corpus it is nearly a pure false-abstention gate, 13.8% (M-sonnet), 9.8% (M-opus), 8.7% (M-haiku), 9.4% (M-fable) of executed readings. The four structural rules stay under the 3% RULES bar each (S-RATIO is the largest at ~2.9%). GATE-COST (G-P6 + rules) is 18.1% (M-sonnet), 13.4% (M-opus), 17.1% (M-haiku), 13.6% (M-fable), inside the 30% bar. What it buys is in §2: on sonnet, opus and fable the gates removed no by-gold wrong that agreement would have admitted (fable: one); on haiku they removed 12 of 19. The engine-only rule A1 is worse than agreement-only A0 by gold on every arm. The safety in A2 comes from the own answer; the gates are a cost with a benefit only at the small scale.

## 5. Reuse: measured, never served

A reading admitted under A2 was keyed by its cue signature (ask type, number count, roles18 cues) and, on pure keys only, bound positionally to every other SEALED item with the same key, gated and executed, then graded. M-sonnet: 1496 items had a candidate, 1407 were on impure keys and skipped, 35 would have been served, **13 wrong**; M-opus: 1449 items had a candidate, 1383 were on impure keys and skipped, 40 would have been served, **18 wrong**; M-haiku: 1400 items had a candidate, 1086 were on impure keys and skipped, 76 would have been served, **58 wrong**; M-fable: 1452 items had a candidate, 1393 were on impure keys and skipped, 38 would have been served, **19 wrong**. H6 and H7 both held: the cue key does not determine the reading (CUE-PURITY 8.3% on DEV), and "pure" is vacuous on singleton keys, so the pure library is mostly single-donor keys whose structure says nothing about the recipient. This is B32 on natural text: positional replay onto a look-alike question fires wrong. Nothing was served; the readings are one-phrasing reflexes.

## 6. Bridge protocol and the record

Every model ran as an agent with Read and Write only: 8 reading blocks and 6 answer blocks per arm, batch files only, no golds, no engine, no code. Files were written once and never overwritten; per-block null counts were reconciled against the agents' own reports. Fable's answer batches 00–11 did not land on disk from the first launch and were collected by a second launch of the same block before scoring (ledger V7). No local model was used. No API spend outside the bridge.

## 7. Outcome on the frozen ladder

- GATE-CTRL: PASS.
- SAFETY-GEN (M-sonnet, A2, genuine wrong = 0): **fail** (1: g1035).
- SAFETY-FA ≤ 0.5% by gold: fail (1.4%, 12 of 863).
- REACH ≥ 50%: pass (61.1%).
- GATE-COST ≤ 30%: pass (18.1%).
- RULES < 3% each on DEV: pass (S-INT 0.4%, S-RATIO 2.7%, S-PCT 1.7%, S-GEOM 0.0%).
- REUSE-SAFE: fail (13 wrong of 35 would-serve); reuse stays measured.
- SEALED-ONCE: every arm's readings, answers and score produced once.

**OUTCOME E.** One model, an honest engine and its own answer still admitted a genuine misread on the primary arm — one item (g1035, a fencepost count) in 863 admissions. The rule says one genuine is E, and the report says E. The aggregates around it: 0.12% genuine on sonnet, 0 on opus, 1 on fable, 1 on haiku; by-gold rates 0.9–1.4% of which the majority are corpus errata, fraction formatting and rounding conventions; reuse wrong-fires on every arm.

## 8. Hypotheses

| hypothesis | result |
|---|---|
| H1 sonnet A2 genuine = 0 | FALSE (1: g1035) |
| H2 A2 FALSE-ADMIT ≤ 0.5% | FALSE (1.4%) |
| H3 A1 genuine > 0 | TRUE (A1 29 wrong by gold, ⊇ A2's genuine) |
| H4 A2 admits 60–80% of executed | FALSE (80.1%) |
| H5 each rule < 3% false abstention on DEV | TRUE |
| H6 CUE-PURITY < 70% | TRUE (8.3%) |
| H7 reuse serves > 0 and wrong-fire ≠ 0 | TRUE (13/35) |
| H8 REACH ≥ 50% | TRUE (61.1%) |
| H9 haiku genuine ≥ sonnet's, reach ≤ | TRUE (1 ≥ 1; 58.3% ≤ 61.1%) |

## 9. What V1.9 claims, and does not

It claims the first gold-graded measurement of a one-model escalation-feedback loop on real questions across four model scales: reach, reading quality, and the by-gold and genuine false-admission rates under three admission rules, with every wrong published and classified. It claims that the model's own answer, not the engine's honesty gates, is what removes wrong readings at sonnet/opus/fable scale, and that the gates matter only at haiku scale. It claims that cue-keyed reuse of readings is unsafe on natural text and was never served. It does not claim SAFETY-GEN (one genuine wrong on the primary arm), does not claim the loop is safe to run live, and does not relabel the corpus golds it disagrees with.

## Reproduction
```
git checkout v1.9-final
python tools/reader19v.py prep ; python tools/reader19v.py controls
# bridge agents (Read/Write only) fill results/v19/bridge/readings19_<m>_sealed/ and answers19_<m>_sealed_NN.json
python tools/reader19v.py score --phase dev --model sonnet
python tools/reader19v.py score --phase sealed --model sonnet|opus|haiku|fable   # once each
python tools/reader19v.py purity --model sonnet --phase dev
python tools/reader19v.py reuse --model <m>
```
