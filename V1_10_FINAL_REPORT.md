# V1.10 Final Report — Suggest, Don't Serve

Branch v1.10-suggest; spec frozen as v1.10-plan before any bridge call; W-400K hashed before any run; SEAL and REPLAY scored once per arm. **Pre-registered outcome: E** (SAFETY-GEN fails: 3 genuine A2S wrongs on M-sonnet SEAL; SAFETY-CHAIN fails (P1-P3 model-free wrong on a sealed pass: sonnet/replay=1, opus/replay=1, haiku/replay=1, fable/replay=1, det/replay=1)).

## Headline
**OUTCOME E, by the letter, on two bars.** (1) SAFETY-GEN: the suggestion rule A2S (the library suggests a reading on the item's cue key; the engine executes it; it is served only if it agrees with the model's own answer) served 410 items on M-sonnet SEAL and was wrong by gold on 10; after post-hoc classification 7 are corpus errata or SVAMP conventions and **3 are GENUINE** (w10_T3_003280, w10_T3_006604, w10_T3_006914): the model's own answer was wrong, a library plan reproduced the same wrong number, and the engine served it. The V10 post-hoc prediction ("0 new genuine") does not survive a sealed run: agreement between an impure library and an impure answer is not a proof. (2) SAFETY-CHAIN: the deterministic exact path, which is model-free, served w10_P1_030692 ("mass 11 kg, acceleration 11.0 m/s^2, what is the force") as 107.8 N on REPLAY on every arm (B41: a stored P1 plan computed weight m*g instead of m*a; the cue key does not separate the two) - one certified wrong in 33k model-free serves; B42 is a second exact wrong on a T3 unit item (1500 for 2 km/h) that the ladder does not count because T3 is not a P tier. SEAL itself had zero exact wrongs on every arm (33-35k serves each).

**What held.** Exact path 0 wrong on SEAL, 4 arms, 133,450 serves; opus A2S 335 served / 0 wrong on SEAL; fable 316 / 2 (1 genuine); SAFETY-PC 0 on every arm; RULES < 0.5% false abstention; KC (key consensus, served only in shadow) 0 wrong on fable SEAL (7 served) but 1/1 on haiku SEAL and 1/3 on fable REPLAY - consensus of impure keys is impure (H9 holds as predicted). Reach: REACH-S (strict, E-SAMPLE) is 24.2 / 17.6 / 12.0 / 17.2% on sonnet / opus / haiku / fable, below the 30% bar; the marginal figure (items the fresh reading did not serve either) is 47 / 38 / 15 / 36%. T2 is the tier suggestion serves (47-63%); T3 (GSM8K-train) 6-19%; T4 and P4 essentially 0. **Tokens: the thesis is inverted.** With the engine in front the model still answers 62-65% of queries (answer-only ratio 62-65% > 50%), and because every non-exact item also needs a reading proposal that costs 2-4x an answer, full-accounting tokens/query is 197-324% of LLM-only. The engine saves tokens only where it serves exactly, and that share (35-38%) was already V1.8's.

**Principal negative.** The V1.10 thesis - "the library can be reused safely if the model's own answer filters it" - is falsified at scale in the direction V1.9 warned about: the filter is the model's answer, so the filter's error rate is the model's error rate on the items it gets wrong, and a large library contains a plan for almost every wrong number (sonnet: 10 wrong / 410; haiku: 9 / 283 with 6 genuine, because haiku's own answers are right only 73% of the time on the sample). Suggestion transfers the model's mistakes into certified answers at 0.6-3.2% per arm; the only arm at zero (opus) is the one whose own answers were right 98.7% of the time. A2S is therefore not safer than fresh A2 (H1 fails on sonnet and haiku); it is the same mechanism with a different reading source.

## 1. What was run
- W-400K: 387062 items (tier quotas in the spec; N4 in the ledger). Splits acq 154653 / dev 38475 / seal 96847 / replay 97087 by sha1(id).
- Arms: M-sonnet, M-opus, M-haiku, M-fable (one model per arm for answers, readings and authoring QC) and D (deterministic engine only). Engine identical across arms.
- Bridge: Read/Write-only agents on batch files without golds; harness-reported usage logged per agent (never self-report).
What was run, in order. (1) Spec frozen (v1.10-plan @ 20731e3). (2) W-400K built and hashed (HASHES.json: source corpora, sampled items, post-authoring and post-QC files, SEAL and REPLAY sample ids). (3) ACQ, non-authored tiers, one pass per model arm with the E-SAMPLE bridge (answers + readings); library minted by PLAN-AGREEMENT (lib_<arm>_acq1). (4) T4/P4 authored by the four models (haiku, sonnet, opus, fable; 8,000 stories), QC'd by a different model on every SEAL/REPLAY item (QC reject = never scored, N17), then a second ACQ pass on the authored tiers (lib_<arm>_acq2). (5) DEV, two passes (dev1 non-authored, dev2 authored): Z-SLOT and S-MULTI false-abstention measured; no further rule added (the echo-donor hypothesis was tested and rejected on DEV, N23). (6) SEAL: answers (122 batches x 4 models), readings (all tiers, slots or chain language), then ONE engine pass per arm with lib_<arm>_acq2 frozen. (7) REPLAY (the second sealed sample): same protocol, ONE pass per arm. (8) Token instrument from harness-reported usage (usage.jsonl, 400+ rows). Every bridge agent got batch files only: no golds, no engine, no code; Read/Write tools only. Two rate-limit outages and one per-model limit interrupted the bridge waves; every interrupted agent was relaunched with "skip if exists" and partial files were kept (N10, N13, N20, N32).

## 2. Results per arm on SEAL (run once)
### M-sonnet — SEAL n=92392, sampled 3042, 76.20 ms/query
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 20149 | 127 / 0 | 77 / 0 | 77 / 0 | 0 / 0 | 200 / 0 | 19822 | 100.0% | 0.4% |
| T2 | 20011 | 1139 / 0 | 112 / 0 | 112 / 0 | 0 / 0 | 238 / 0 | 18634 | 100.0% | 0.6% |
| T3 | 1876 | 0 / 0 | 116 / 4 | 119 / 6 | 0 / 0 | 439 / 9 | 1430 | 96.2% | 7.5% |
| T3p | 242 | 0 / 0 | 88 / 6 | 88 / 6 | 0 / 0 | 130 / 5 | 75 | 95.9% | 54.0% |
| T4 | 1372 (+400 author-excluded) | 0 / 0 | 17 / 0 | 17 / 0 | 0 / 0 | 151 / 3 | 1220 | 97.8% | 1.4% |
| P1 | 19907 | 17510 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 24 / 0 | 2373 | 97.0% | 0.0% |
| P2 | 15062 | 11795 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 34 / 0 | 3233 | 100.0% | 0.0% |
| P3 | 10083 | 2531 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 154 / 0 | 7398 | 99.2% | 0.0% |
| P4 | 974 (+201 author-excluded) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 47 / 0 | 927 | 98.4% | 0.0% |
| PC | 279 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 279 | 97.6% | 0.0% |
| D | 1836 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1836 | — | 0.0% |
| **all** | 91791 | 33102 / 0 | 410 / 10 | 413 / 12 | 0 / 0 | 1417 / 17 | 57227 | 97.9% | — |

### M-opus — SEAL n=92392, sampled 3042, 63.39 ms/query
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 20149 | 0 / 0 | 37 / 0 | 37 / 0 | 0 / 0 | 200 / 0 | 19949 | 100.0% | 0.2% |
| T2 | 20011 | 1355 / 0 | 138 / 0 | 138 / 0 | 0 / 0 | 234 / 0 | 18422 | 100.0% | 0.7% |
| T3 | 1876 | 0 / 0 | 82 / 0 | 84 / 1 | 0 / 0 | 448 / 5 | 1424 | 97.7% | 5.4% |
| T3p | 242 | 0 / 0 | 66 / 0 | 66 / 0 | 0 / 0 | 127 / 2 | 99 | 98.3% | 40.0% |
| T4 | 1411 (+361 author-excluded) | 0 / 0 | 12 / 0 | 12 / 0 | 0 / 0 | 131 / 1 | 1280 | 99.3% | 0.9% |
| P1 | 19907 | 17510 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 22 / 0 | 2375 | 97.5% | 0.0% |
| P2 | 15062 | 11795 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 34 / 0 | 3233 | 98.8% | 0.0% |
| P3 | 10083 | 2532 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 162 / 0 | 7389 | 99.6% | 0.0% |
| P4 | 933 (+242 author-excluded) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 46 / 0 | 887 | 97.9% | 0.0% |
| PC | 279 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 279 | 98.8% | 0.0% |
| D | 1836 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1836 | — | 0.0% |
| **all** | 91789 | 33192 / 0 | 335 / 0 | 337 / 1 | 0 / 0 | 1404 / 8 | 57173 | 98.7% | — |

### M-haiku — SEAL n=92392, sampled 3042, 40.25 ms/query
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 20149 | 0 / 0 | 33 / 0 | 33 / 0 | 0 / 0 | 200 / 0 | 19949 | 100.0% | 0.2% |
| T2 | 20011 | 1271 / 0 | 147 / 1 | 168 / 1 | 0 / 0 | 68 / 0 | 18582 | 98.4% | 0.8% |
| T3 | 1876 | 0 / 0 | 34 / 3 | 52 / 3 | 1 / 1 | 120 / 1 | 1736 | 82.7% | 1.9% |
| T3p | 242 | 0 / 0 | 67 / 5 | 68 / 5 | 0 / 0 | 107 / 4 | 110 | 94.2% | 37.9% |
| T4 | 1050 (+722 author-excluded) | 0 / 0 | 2 / 0 | 2 / 0 | 0 / 0 | 19 / 1 | 1031 | 41.0% | 0.2% |
| P1 | 19907 | 17457 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 6 / 0 | 2444 | 53.5% | 0.0% |
| P2 | 15062 | 10903 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 2 / 0 | 4157 | 19.6% | 0.0% |
| P3 | 10083 | 2504 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 8 / 0 | 7571 | 46.4% | 0.0% |
| P4 | 641 (+534 author-excluded) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 641 | 86.0% | 0.0% |
| PC | 279 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 279 | 96.8% | 0.0% |
| D | 1836 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1836 | — | 0.0% |
| **all** | 91136 | 32135 / 0 | 283 / 9 | 323 / 9 | 1 / 1 | 530 / 6 | 58336 | 72.8% | — |

### M-fable — SEAL n=92392, sampled 3042, 58.45 ms/query
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 20149 | 127 / 0 | 50 / 0 | 50 / 0 | 0 / 0 | 200 / 0 | 19822 | 100.0% | 0.3% |
| T2 | 20011 | 3057 / 0 | 115 / 0 | 115 / 0 | 7 / 0 | 215 / 0 | 16739 | 100.0% | 0.7% |
| T3 | 1876 | 0 / 0 | 85 / 1 | 86 / 2 | 0 / 0 | 440 / 6 | 1430 | 97.3% | 5.6% |
| T3p | 242 | 0 / 0 | 60 / 1 | 60 / 1 | 0 / 0 | 129 / 2 | 100 | 97.9% | 37.5% |
| T4 | 1483 (+289 author-excluded) | 0 / 0 | 6 / 0 | 6 / 0 | 0 / 0 | 141 / 0 | 1342 | 99.7% | 0.4% |
| P1 | 19907 | 17510 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 22 / 0 | 2375 | 96.0% | 0.0% |
| P2 | 15062 | 11795 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 34 / 0 | 3233 | 98.8% | 0.0% |
| P3 | 10083 | 2532 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 162 / 0 | 7389 | 99.6% | 0.0% |
| P4 | 977 (+198 author-excluded) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 60 / 0 | 917 | 97.1% | 0.0% |
| PC | 279 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 279 | 98.8% | 0.0% |
| D | 1836 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1836 | — | 0.0% |
| **all** | 91905 | 35021 / 0 | 316 / 2 | 317 / 3 | 7 / 0 | 1403 / 8 | 55462 | 98.4% | — |

### D (engine only) — SEAL n=92392
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 20149 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 20149 | — | 0.0% |
| T2 | 20011 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 20011 | — | 0.0% |
| T3 | 1876 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1876 | — | 0.0% |
| T3p | 242 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 242 | — | 0.0% |
| T4 | 1772 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1772 | — | 0.0% |
| P1 | 19907 | 17269 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 2638 | — | 0.0% |
| P2 | 15062 | 10171 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 4891 | — | 0.0% |
| P3 | 10083 | 2501 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 7582 | — | 0.0% |
| P4 | 1175 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1175 | — | 0.0% |
| PC | 279 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 279 | — | 0.0% |
| D | 1836 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 1836 | — | 0.0% |
| **all** | 92392 | 29941 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 62451 | — | — |

Per arm on SEAL (92,392 items; E-SAMPLE 3,042 answered per arm): sonnet exact 33,102 / 0 wrong, A2S 410 / 10, fresh A2 1,417 / 17, KC 0 served; opus exact 33,192 / 0, A2S 335 / 0, A2 1,404 / 8, KC 0; haiku exact 32,135 / 0, A2S 283 / 9, A2 530 / 6, KC 1 / 1; fable exact 35,021 / 0, A2S 316 / 2, A2 1,403 / 8, KC 7 / 0. A0S (suggestion without the own-answer filter) served 413 / 337 / 323 / 317 with 12 / 1 / 9 / 3 wrong: the own-answer filter removed 2 of sonnet's 12 and 1 of opus's 1 - a fraction of the by-gold wrongs, not the class. Own answers were correct on 97.9 / 98.7 / 72.8 / 98.4% of the answered sample, and the A2S wrong rate tracks that number (opus 0.0%, fable 0.6%, sonnet 2.4%, haiku 3.2%). The D arm (engine only, no model) served 29,941 exact on SEAL at 0 wrong. Every model arm reproduces D's exact-path behaviour (the exact path does not depend on the arm), which is the SEALED-ONCE consistency check.

## 3. Every by-gold wrong on SEAL, classified after the run (nothing relabelled)
| arm | rule | id | tier | value | gold | class |
|---|---|---|---|---|---|---|
| sonnet | A2 | w10_T3_000167 | T3 | 19200.0 | 1920 | CORPUS |
| sonnet | A2S | w10_T3_000700 | T3 | 300.0 | 3 | CORPUS |
| sonnet | A2 | w10_T3_000700 | T3 | 300.0 | 3 | CORPUS |
| sonnet | A2 | w10_T3_001777 | T3 | 60.0 | 90 | INTERP |
| sonnet | A2 | w10_T3_001958 | T3 | 30.0 | 40 | CORPUS |
| sonnet | A2S | w10_T3_003280 | T3 | 13.0 | 11 | GENUINE |
| sonnet | A2 | w10_T3_003280 | T3 | 13.0 | 11 | GENUINE |
| sonnet | A2 | w10_T3_004437 | T3 | 480.0 | 400 | INTERP |
| sonnet | A2 | w10_T3_005496 | T3 | 11.0 | 12 | CORPUS |
| sonnet | A2S | w10_T3_006604 | T3 | 441.0 | 378 | GENUINE |
| sonnet | A2 | w10_T3_006604 | T3 | 441.0 | 378 | GENUINE |
| sonnet | A2 | w10_T3_006832 | T3 | 500.0 | 250 | CORPUS |
| sonnet | A2S | w10_T3_006914 | T3 | 80.0 | 65 | GENUINE |
| sonnet | A2S | w10_T3p_000049 | T3p | 415.0 | 266 | CORPUS |
| sonnet | A2S | w10_T3p_000206 | T3p | 18.0 | 11 | CORPUS |
| sonnet | A2 | w10_T3p_000206 | T3p | 18.0 | 11 | CORPUS |
| sonnet | A2S | w10_T3p_000334 | T3p | 26.0 | 16 | CORPUS |
| sonnet | A2S | w10_T3p_000638 | T3p | 0.0 | 10 | CORPUS |
| sonnet | A2S | w10_T3p_000679 | T3p | 5.0 | 1 | CORPUS |
| sonnet | A2 | w10_T3p_000679 | T3p | 5.0 | 1 | CORPUS |
| sonnet | A2 | w10_T3p_000792 | T3p | 18.0 | 15 | CORPUS |
| sonnet | A2 | w10_T3p_000906 | T3p | 86.0 | 156 | CORPUS |
| sonnet | A2S | w10_T3p_000985 | T3p | 6.0 | 8 | CORPUS |
| sonnet | A2 | w10_T3p_000985 | T3p | 6.0 | 8 | CORPUS |
| sonnet | A2 | w10_T4_001576 | T4 | 84.0 | 34 | INTERP |
| sonnet | A2 | w10_T4_002658 | T4 | 19167.0 | 19159 | INTERP |
| sonnet | A2 | w10_T4_014073 | T4 | 2859.0 | 2163 | CORPUS |
| opus | A2 | w10_T3_000167 | T3 | 19200.0 | 1920 | CORPUS |
| opus | A2 | w10_T3_000869 | T3 | 0.0 | 3 | CORPUS |
| opus | A2 | w10_T3_001777 | T3 | 60.0 | 90 | INTERP |
| opus | A2 | w10_T3_005496 | T3 | 11.0 | 12 | CORPUS |
| opus | A2 | w10_T3_006832 | T3 | 500.0 | 250 | CORPUS |
| opus | A2 | w10_T3p_000679 | T3p | 5.0 | 1 | CORPUS |
| opus | A2 | w10_T3p_000906 | T3p | 86.0 | 156 | CORPUS |
| opus | A2 | w10_T4_014073 | T4 | 2859.0 | 2163 | CORPUS |
| haiku | A2S | w10_T2_049262 | T2 | 8.0 | 10 | GENUINE |
| haiku | A2S | w10_T3_000114 | T3 | 14.0 | 15 | GENUINE |
| haiku | A2S | w10_T3_001527 | T3 | 15.0 | 21 | GENUINE |
| haiku | A2 | w10_T3_005075 | T3 | 225.0 | 230 | GENUINE |
| haiku | A2S | w10_T3_005207 | T3 | 12.0 | 16 | GENUINE |
| haiku | A2S | w10_T3p_000206 | T3p | 18.0 | 11 | CORPUS |
| haiku | A2 | w10_T3p_000206 | T3p | 18.0 | 11 | CORPUS |
| haiku | A2S | w10_T3p_000512 | T3p | 132.0 | 20 | CORPUS |
| haiku | A2S | w10_T3p_000638 | T3p | 0.0 | 10 | CORPUS |
| haiku | A2 | w10_T3p_000679 | T3p | 5.0 | 1 | CORPUS |
| haiku | A2 | w10_T3p_000792 | T3p | 18.0 | 15 | CORPUS |
| haiku | A2S | w10_T3p_000810 | T3p | 5.0 | 21 | GENUINE |
| haiku | A2 | w10_T3p_000906 | T3p | 86.0 | 156 | CORPUS |
| haiku | A2S | w10_T3p_000985 | T3p | 3.0 | 8 | GENUINE |
| haiku | A2 | w10_T4_006199 | T4 | 353.0 | 179 | GENUINE |
| fable | A2 | w10_T3_000167 | T3 | 19200.0 | 1920 | CORPUS |
| fable | A2 | w10_T3_000700 | T3 | 300.0 | 3 | CORPUS |
| fable | A2 | w10_T3_001958 | T3 | 30.0 | 40 | CORPUS |
| fable | A2 | w10_T3_005496 | T3 | 11.0 | 12 | CORPUS |
| fable | A2 | w10_T3_006832 | T3 | 500.0 | 250 | CORPUS |
| fable | A2S | w10_T3_006914 | T3 | 80.0 | 65 | GENUINE |
| fable | A2 | w10_T3_007444 | T3 | 140.0 | 280 | CORPUS |
| fable | A2S | w10_T3p_000638 | T3p | 0.0 | 10 | CORPUS |
| fable | A2 | w10_T3p_000679 | T3p | 5.0 | 1 | CORPUS |
| fable | A2 | w10_T3p_000906 | T3p | 86.0 | 156 | CORPUS |

Classes (nothing relabelled; golds are the corpus's). GENUINE on SEAL under A2S: sonnet 3 (Jonah's fish 003280: the two eaters were removed, own 13 vs 11; the cannoneers 006604: 'none of the cannoneers were women' makes them men, own 441 vs 378; Billy's videos 006914: four full lists plus five, own 80 vs 65), haiku 6 (arithmetic slips on T2/T3/T3'), fable 1 (006914 again), opus 0. Every GENUINE is a reading error of the model that a library plan happened to reproduce: the served number is the model's own wrong number. CORPUS on SEAL (the served value is right by the text; the gold is an erratum or a corpus convention): the GSM8K-train errata 000167 (19,200 vs 1920), 001958 (speed 3/4 -> time 4/3), 005496 (11 vs 12), 006832 (500 vs 250), 007444 (140 vs 280), the unit answer 000700 (300 cents vs $3), the SVAMP 'N more pages of biology' convention (000206, 000334, 000792, 000985), and perturbed-SVAMP items whose gold does not follow from the text (000049, 000512, 000638, 000679, 000906). INTERP (both readings defensible): 001777, 004437, and the haiku-authored T4 asks 001576, 002658 whose gold treats a stated quantity as a distractor. One authored gold (014073) does not follow from its own story and passed QC (N36). REPLAY reproduces the classes: A2S wrongs on REPLAY are 3 / 3 / 2 / 3 (sonnet / opus / haiku / fable), all CORPUS except one haiku GENUINE (T4_002045); the two exact-path wrongs B41 and B42 appear on every arm because the exact path is model-free.

## 4. Reach: what the suggestion serves that the fresh reading could not
| arm | REACH-S (T3+T3', bar 30%) | T1 | T2 | T4 | P4 | A2S wrong / served | A0S wrong / served |
|---|---|---|---|---|---|---|---|
| sonnet | 24.2% | 38.5% | 47.1% | 5.4% | 0.0% | 10 / 410 | 12 / 413 |
| opus | 17.6% | 18.5% | 59.0% | 3.9% | 0.0% | 0 / 335 | 1 / 337 |
| haiku | 12.0% | 16.5% | 62.6% | 0.9% | 0.0% | 9 / 283 | 9 / 323 |
| fable | 17.2% | 25.0% | 53.5% | 1.7% | 0.0% | 2 / 316 | 3 / 317 |

SUGGEST-REACH is measured on the E-SAMPLE (the model answered only sampled items; un-sampled items escalate by construction). Strict = share of sampled items the exact path did not serve that the suggestion served; marginal = share of those the fresh reading did not serve either. Strict REACH-S over T3+T3' is 24.2 / 17.6 / 12.0 / 17.2% (bar 30%): the bar fails on every arm. By tier, suggestion is a T2 mechanism (47-63%): two-to-three-step narratives with a small set of cue keys are what the library has plans for. On GSM8K-train (T3) it serves 6-19%, on SVAMP (T3') 25-36%, on authored T4 0.9-5.4% and on P4 exactly 0 on every arm: the authored tiers were written by the four models as 4-6 step stories with distractors, and the library's cue keys do not fire on them. H4 fails (T1 and T3 below 30%; T4/P4 below 15% holds trivially). H10 holds: haiku has more genuine wrongs (6 vs 3) and less reach (12.0 vs 24.2%) than sonnet - scale monotone in both directions, as in every version since V1.6.

## 5. Physics: chains model-free, stories by reading
| arm | P1 served / wrong | P2 served / wrong | P3 served / wrong | P4 A2S / wrong | P4 fresh A2 / wrong | PC certified |
|---|---|---|---|---|---|---|
| sonnet | 17510 / 0 | 11795 / 0 | 2531 / 0 | 0 / 0 | 47 / 0 | 0 |
| opus | 17510 / 0 | 11795 / 0 | 2532 / 0 | 0 / 0 | 46 / 0 | 0 |
| haiku | 17457 / 0 | 10903 / 0 | 2504 / 0 | 0 / 0 | 0 / 0 | 0 |
| fable | 17510 / 0 | 11795 / 0 | 2532 / 0 | 0 / 0 | 60 / 0 | 0 |
| D | 17269 / 0 | 10171 / 0 | 2501 / 0 | 0 / 0 | 0 / 0 | 0 |

Physics chains P1-P3 are served by the model-free exact path (V1.7/V1.8 role skeletons): on SEAL 86.7% of P1, 67.5% of P2 and 24.8% of P3 certified at 0 wrong; on REPLAY the same shares with the one B41 wrong on P1. H5's 90% bar fails on coverage (P3 chains of 5-6 nodes need plans the library does not have; the ~255 P-plans per arm come from P1/P2 donors) but holds on safety on SEAL. P4 (authored physics stories): fresh readings reached 4.8 / 4.9 / 0.0 / 6.1% of scorable items with 0 wrong on every arm (H6 holds on both halves); the readings were the bottleneck - the gates killed most P4 plans (fresh_gate_kill 82-152 per tier) and haiku's P4 SEAL block was all-null by its own agent's script (N32). PC (SciQ concept items, 279 on SEAL): 0 certified on every arm (H7 and SAFETY-PC hold); the model answered 242-250 of 250 sampled correctly and every one escalated.

## 6. Tokens (harness-reported, marginal over the empty-batch baseline)
| model | role | split | agents | items | raw tokens/item | marginal tokens/item |
|---|---|---|---|---|---|---|
| fable | answer | acq | 17 | 3600 | 455.8 | 178 |
| fable | answer | acq+dev | 2 | 600 | 502.4 | 307 |
| fable | answer | ctl_empty | 1 | 0 | None | — |
| fable | answer | dev | 4 | 1039 | 381.5 | 155 |
| fable | answer | replay | 4 | 1064 | 422.1 | 201 |
| fable | answer | seal | 9 | 3042 | 363.2 | 189 |
| fable | author | - | 3 | 425 | 1310.7 | 896 |
| fable | author | all | 7 | 1400 | 1198.2 | 904 |
| fable | qc | - | 10 | 3567 | 402.1 | 237 |
| fable | reading | acq | 17 | 2950 | 1009.8 | 671 |
| fable | reading | acq+dev | 1 | 175 | 1151.1 | 815 |
| fable | reading | dev | 6 | 1019 | 1007.7 | 662 |
| fable | reading | replay | 5 | 900 | 1028.8 | 702 |
| fable | reading | seal | 11 | 2366 | 1038.2 | 765 |
| haiku | answer | acq | 18 | 3700 | 422.7 | 194 |
| haiku | answer | acq+dev | 2 | 600 | 352.5 | 196 |
| haiku | answer | ctl_empty | 1 | 0 | None | — |
| haiku | answer | dev | 4 | 1044 | 345.7 | 166 |
| haiku | answer | replay | 4 | 812 | 415.8 | 184 |
| haiku | answer | seal | 10 | 3042 | 348.4 | 194 |
| haiku | author | - | 1 | 128 | 984.6 | 617 |
| haiku | author | all | 31 | 6104 | 733.5 | 495 |
| haiku | qc | - | 4 | 1255 | 469.2 | 319 |
| haiku | reading | acq | 18 | 3325 | 747.5 | 493 |
| haiku | reading | acq+dev | 1 | 200 | 669.8 | 435 |
| haiku | reading | dev | 7 | 1069 | 831.8 | 524 |
| haiku | reading | replay | 5 | 900 | 746.6 | 485 |
| haiku | reading | seal | 13 | 2661 | 621.6 | 392 |
| opus | answer | acq | 18 | 3700 | 467.9 | 183 |
| opus | answer | acq+dev | 2 | 600 | 498.5 | 304 |
| opus | answer | ctl_empty | 1 | 0 | None | — |
| opus | answer | dev | 4 | 1039 | 387.8 | 163 |
| opus | answer | replay | 4 | 1164 | 395.4 | 194 |
| opus | answer | seal | 9 | 3042 | 369.3 | 196 |
| opus | author | - | 3 | 600 | 997.1 | 705 |
| opus | author | all | 8 | 1600 | 1209.8 | 917 |
| opus | qc | - | 5 | 1403 | 521.7 | 313 |
| opus | reading | acq | 18 | 3171 | 1084.1 | 752 |
| opus | reading | acq+dev | 1 | 190 | 1226.7 | 919 |
| opus | reading | dev | 6 | 1003 | 1081.2 | 731 |
| opus | reading | replay | 5 | 900 | 1066.7 | 742 |
| opus | reading | seal | 11 | 2376 | 1038.8 | 768 |
| sonnet | answer | acq | 17 | 3525 | 548.4 | 237 |
| sonnet | answer | acq+dev | 2 | 600 | 709.4 | 494 |
| sonnet | answer | ctl_empty | 1 | 0 | None | — |
| sonnet | answer | ctl_full | 1 | 25 | 2637.3 | 56 |
| sonnet | answer | dev | 4 | 1044 | 445.6 | 198 |
| sonnet | answer | replay | 4 | 814 | 565.3 | 248 |
| sonnet | answer | seal | 12 | 4092 | 436.0 | 247 |
| sonnet | author | - | 3 | 575 | 1143.9 | 807 |
| sonnet | author | all | 10 | 1700 | 1440.3 | 1061 |
| sonnet | qc | - | 5 | 1518 | 627.3 | 415 |
| sonnet | reading | acq | 18 | 3049 | 1203.2 | 822 |
| sonnet | reading | acq+dev | 1 | 200 | 1380.8 | 1058 |
| sonnet | reading | dev | 6 | 994 | 1175.9 | 786 |
| sonnet | reading | replay | 5 | 900 | 1190.3 | 832 |
| sonnet | reading | seal | 11 | 1853 | 1383.6 | 1001 |

TOKENS/QUERY with the engine in front vs LLM-only, extrapolated to SEAL (bar: full accounting <= 50% on the primary arm):

| arm | SEAL n | exact served | non-exact share | answer marginal tok/item | reading marginal tok/item | ratio (answer-only) | ratio (full: answer + reading) | non-exact share on T4+P4 |
|---|---|---|---|---|---|---|---|---|
| sonnet | 92392 | 33102 | 64.2% | 247 | 1001 | 64% | 324% | 100.0% |
| opus | 92392 | 33192 | 64.1% | 196 | 768 | 64% | 315% | 100.0% |
| haiku | 92392 | 32135 | 65.2% | 194 | 392 | 65% | 197% | 100.0% |
| fable | 92392 | 35021 | 62.1% | 189 | 765 | 62% | 313% | 100.0% |

Marginal tokens per item are harness-reported totals minus the empty-batch baseline per agent (N3: sonnet 64,522; opus 58,488; haiku 47,005; fable 58,748), which is 70-95% of every agent's total. An answer costs 189-247 marginal tokens per item; a reading proposal 392-1,001 (slots on T tiers, chains on P tiers). With the engine in front the exact path serves 35-38% of SEAL and the model must answer the other 62-65% (its own answer is the A2S filter and the escalation answer), so the answer-only ratio is 62-65% of LLM-only - above the 50% bar on every arm; on T4+P4 it is 100% (the exact path served nothing there). Counting the reading proposal every non-exact item needs, the full ratio is 324 / 315 / 197 / 313%: the reading pipeline costs 2-3x what answering costs. TOKENS fails and H8 fails; the measured-sample numbers are in the table above, the extrapolation uses the exact-served count of the whole split (a count, not a sample statistic). The V1.10 economy is negative unless readings are amortised across repeated traffic, which W-400K does not contain (every item is seen once).

## 7. DEV: rules and their cost
### M-sonnet — DEV n=37303
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 7938 | 47 / 0 | 42 / 0 | 42 / 0 | 0 / 0 | 100 / 0 | 7791 | 100.0% | 0.5% |
| T2 | 7948 | 787 / 0 | 44 / 0 | 44 / 0 | 0 / 0 | 90 / 0 | 7071 | 100.0% | 0.6% |
| T3 | 730 | 0 / 0 | 54 / 0 | 54 / 0 | 0 / 0 | 229 / 3 | 497 | 97.7% | 9.8% |
| T3p | 94 | 0 / 0 | 33 / 1 | 33 / 1 | 0 / 0 | 55 / 0 | 31 | 97.9% | 51.6% |
| T4 | 982 | 0 / 0 | 3 / 0 | 3 / 0 | 0 / 0 | 47 / 0 | 679 | 96.2% | 0.4% |
| P1 | 7976 | 7040 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 7 / 0 | 929 | 96.0% | 0.0% |
| P2 | 6028 | 4656 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 16 / 0 | 1356 | 100.0% | 0.0% |
| P3 | 3905 | 956 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 63 / 0 | 2886 | 99.0% | 0.0% |
| P4 | 811 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 17 / 0 | 491 | 96.6% | 0.0% |
| PC | 95 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 95 | 95.8% | 0.0% |
| D | 796 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 796 | — | 0.0% |
| **all** | 37303 | 13486 / 0 | 176 / 1 | 176 / 1 | 0 / 0 | 624 / 3 | 22622 | 97.9% | — |

### M-opus — DEV n=37303
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 7938 | 0 / 0 | 24 / 0 | 24 / 0 | 0 / 0 | 100 / 0 | 7838 | 100.0% | 0.3% |
| T2 | 7948 | 561 / 0 | 66 / 0 | 66 / 0 | 0 / 0 | 95 / 0 | 7292 | 100.0% | 0.9% |
| T3 | 730 | 0 / 0 | 46 / 0 | 47 / 0 | 0 / 0 | 233 / 3 | 493 | 97.7% | 8.5% |
| T3p | 94 | 0 / 0 | 28 / 0 | 28 / 0 | 0 / 0 | 56 / 0 | 34 | 98.9% | 45.2% |
| T4 | 982 | 0 / 0 | 3 / 0 | 3 / 0 | 0 / 0 | 52 / 1 | 675 | 99.0% | 0.4% |
| P1 | 7976 | 7040 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 9 / 0 | 927 | 91.0% | 0.0% |
| P2 | 6028 | 4656 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 16 / 0 | 1356 | 100.0% | 0.0% |
| P3 | 3905 | 956 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 63 / 0 | 2886 | 100.0% | 0.0% |
| P4 | 811 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 13 / 0 | 495 | 97.7% | 0.0% |
| PC | 95 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 95 | 98.9% | 0.0% |
| D | 796 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 796 | — | 0.0% |
| **all** | 37303 | 13213 / 0 | 167 / 0 | 168 / 0 | 0 / 0 | 637 / 4 | 22887 | 98.2% | — |

### M-haiku — DEV n=37303
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 7938 | 0 / 0 | 22 / 0 | 22 / 0 | 0 / 0 | 100 / 0 | 7838 | 100.0% | 0.3% |
| T2 | 7948 | 858 / 0 | 49 / 0 | 68 / 0 | 0 / 0 | 68 / 0 | 7022 | 100.0% | 0.7% |
| T3 | 730 | 0 / 0 | 19 / 0 | 33 / 0 | 0 / 0 | 117 / 0 | 612 | 85.0% | 3.0% |
| T3p | 94 | 0 / 0 | 26 / 4 | 26 / 4 | 0 / 0 | 50 / 0 | 38 | 90.4% | 40.6% |
| T4 | 982 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 6 / 0 | 721 | 27.6% | 0.0% |
| P1 | 7976 | 7013 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 963 | 60.0% | 0.0% |
| P2 | 6028 | 4341 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 8 / 0 | 1679 | 29.0% | 0.0% |
| P3 | 3905 | 952 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 17 / 0 | 2936 | 24.0% | 0.0% |
| P4 | 811 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 508 | 1.1% | 0.0% |
| PC | 95 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 95 | 96.8% | 0.0% |
| D | 796 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 796 | — | 0.0% |
| **all** | 37303 | 13164 / 0 | 116 / 4 | 149 / 4 | 0 / 0 | 366 / 0 | 23208 | 65.6% | — |

### M-fable — DEV n=37303
| tier | n | exact served / wrong | A2S served / wrong | A0S served / wrong | KC served / wrong | fresh A2 / wrong | escalated | own correct | reach (A2S of non-exact) |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 7938 | 47 / 0 | 29 / 0 | 29 / 0 | 0 / 0 | 100 / 0 | 7791 | 100.0% | 0.4% |
| T2 | 7948 | 641 / 0 | 60 / 0 | 60 / 0 | 2 / 0 | 94 / 0 | 7213 | 100.0% | 0.8% |
| T3 | 730 | 0 / 0 | 43 / 0 | 44 / 0 | 0 / 0 | 232 / 2 | 495 | 98.3% | 8.0% |
| T3p | 94 | 0 / 0 | 29 / 0 | 29 / 0 | 0 / 0 | 56 / 0 | 35 | 98.9% | 45.3% |
| T4 | 982 | 0 / 0 | 2 / 0 | 2 / 0 | 0 / 0 | 46 / 0 | 680 | 99.0% | 0.3% |
| P1 | 7976 | 7040 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 9 / 0 | 927 | 91.0% | 0.0% |
| P2 | 6028 | 4656 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 16 / 0 | 1356 | 100.0% | 0.0% |
| P3 | 3905 | 956 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 62 / 0 | 2887 | 99.0% | 0.0% |
| P4 | 811 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 20 / 0 | 488 | 100.0% | 0.0% |
| PC | 95 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 95 | 98.9% | 0.0% |
| D | 796 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 796 | — | 0.0% |
| **all** | 37303 | 13340 / 0 | 163 / 0 | 164 / 0 | 2 / 0 | 635 / 2 | 22763 | 98.5% | — |


RULES on DEV (false abstention of a rule = sampled DEV T-tier items the rule blocked on which the un-blocked suggestion would have served the gold, over all sampled items; bar < 3%):

| arm | sampled | Z-SLOT blocked | Z-SLOT false abst. | S-MULTI blocked | S-MULTI would serve (correct/wrong) | S-MULTI false abst. |
|---|---|---|---|---|---|---|
| sonnet | 744 | 5 | 0.0% | 10 | 3 (3/0) | 0.4% |
| opus | 744 | 5 | 0.0% | 10 | 1 (1/0) | 0.1% |
| haiku | 744 | 5 | 0.0% | 10 | 0 (0/0) | 0.0% |
| fable | 744 | 5 | 0.0% | 10 | 1 (1/0) | 0.1% |

DEV (37,303 items per arm; dev1 + dev2 merged). A2S served 176 / 1 wrong (sonnet), 167 / 0 (opus), 116 / 4 (haiku), 163 / 0 (fable). Z-SLOT and S-MULTI false abstention on DEV were below the 3% RULES bar on every arm (rules110.json, measured post hoc, N35); the KC shadow served 3 on sonnet with 3 wrong at DEV, so KC was never promoted. The one DEV-set decision was to add NO new rule: the only wrong-class hypothesis raised on DEV (echo donors: a suggestion whose plan simply repeats the item's own numbers) had zero instances among A2S serves (N23), so nothing was added and nothing was tuned on DEV after dev1 except the QC step for authored items (N17), which is a workload rule, not an engine rule.

## 8. Acquisition and REPLAY
- M-sonnet ACQ: library T=1325 P=255 probated=44; A2S served 472 / wrong 4; curve 40k:0, 60k:0, 80k:13, 100k:89, 120k:172, 140k:299
- M-opus ACQ: library T=918 P=253 probated=43; A2S served 433 / wrong 1; curve 40k:0, 60k:0, 80k:5, 100k:35, 120k:136, 140k:288
- M-haiku ACQ: library T=458 P=104 probated=22; A2S served 338 / wrong 7; curve 40k:0, 60k:0, 80k:4, 100k:32, 120k:114, 140k:246
- M-fable ACQ: library T=808 P=254 probated=44; A2S served 413 / wrong 4; curve 40k:0, 60k:0, 80k:7, 100k:48, 120k:147, 140k:287

Every by-gold wrong on REPLAY (classified after the run):

| arm | rule | id | tier | value | gold | class |
|---|---|---|---|---|---|---|
| sonnet | exact | w10_P1_030692 | P1 | 107.80000000000001 | 121.0 | unclassified |
| sonnet | A2 | w10_T3_000356 | T3 | 64.0 | 66 | CORPUS |
| sonnet | A2 | w10_T3_000424 | T3 | 6825.0 | 750 | INTERP |
| sonnet | exact | w10_T3_002293 | T3 | 1500.0 | 2 | unclassified |
| sonnet | A2S | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| sonnet | A2 | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| sonnet | A2 | w10_T3_005051 | T3 | 2600.0 | 1600 | INTERP |
| sonnet | A2S | w10_T3p_000034 | T3p | 3.0 | 1 | CORPUS |
| sonnet | A2S | w10_T3p_000729 | T3p | 10.0 | 13 | CORPUS |
| sonnet | A2 | w10_T4_002700 | T4 | 1119.0 | 1110 | INTERP |
| opus | exact | w10_P1_030692 | P1 | 107.80000000000001 | 121.0 | unclassified |
| opus | A2 | w10_T3_000356 | T3 | 64.0 | 66 | CORPUS |
| opus | A2 | w10_T3_000424 | T3 | 6825.0 | 750 | INTERP |
| opus | exact | w10_T3_002293 | T3 | 1500.0 | 2 | unclassified |
| opus | A2S | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| opus | A2 | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| opus | A2S | w10_T3p_000034 | T3p | 3.0 | 1 | CORPUS |
| opus | A2S | w10_T3p_000729 | T3p | 10.0 | 13 | CORPUS |
| opus | A2 | w10_T4_002700 | T4 | 1119.0 | 1110 | INTERP |
| haiku | exact | w10_P1_030692 | P1 | 107.80000000000001 | 121.0 | unclassified |
| haiku | exact | w10_T3_002293 | T3 | 1500.0 | 2 | unclassified |
| haiku | A2 | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| haiku | A2S | w10_T3p_000729 | T3p | 10.0 | 13 | CORPUS |
| haiku | A2S | w10_T4_002045 | T4 | 239.0 | 388 | GENUINE |
| fable | exact | w10_P1_030692 | P1 | 107.80000000000001 | 121.0 | unclassified |
| fable | A2 | w10_T3_000356 | T3 | 64.0 | 66 | CORPUS |
| fable | A2 | w10_T3_000424 | T3 | 6825.0 | 750 | INTERP |
| fable | exact | w10_T3_002293 | T3 | 1500.0 | 2 | unclassified |
| fable | A2S | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| fable | A2 | w10_T3_002338 | T3 | 25.0 | 30 | CORPUS |
| fable | A2S | w10_T3p_000034 | T3p | 3.0 | 1 | CORPUS |
| fable | A2S | w10_T3p_000729 | T3p | 10.0 | 13 | CORPUS |

- M-sonnet REPLAY: A2S served 118 / wrong 3; exact 32959 / wrong 2; escalated 58491 of 92516
- M-opus REPLAY: A2S served 96 / wrong 3; exact 33089 / wrong 2; escalated 58320 of 92516
- M-haiku REPLAY: A2S served 72 / wrong 2; exact 32259 / wrong 2; escalated 58699 of 92516
- M-fable REPLAY: A2S served 92 / wrong 3; exact 34112 / wrong 2; escalated 57441 of 92516

ACQ (148,009 items per arm; base + acq2 merged). The exact path serves ~51k items per arm at zero wrong on every arm (the V1.8 machinery). Suggestion under A2S served 472 (sonnet, 4 wrong), 433 (opus, 1), 338 (haiku, 7), 413 (fable, 4); fresh A2 readings admitted 1,650-1,900 per arm with 10-12 wrong by gold. The library after acq2 holds ~1,325 T-plans and ~255 P-plans per arm (probation removes plans that disagree once). The acquisition curve (checkpoints every 20k, fig. 3) is concave and non-flat on every arm: A2S serves are 0 at 40k and 60k, 13 at 80k, 89 at 100k, 172 at 120k, 299 at 140k on sonnet - the library needs the T3/T3' tiers (positions 80k+) before it has anything to suggest on real text (H12 holds).

## 9. Controls
| control | result |
|---|---|
| v19_batteries | True |
| Z-SLOT | True |
| S-MULTI_pos | True |
| S-MULTI_pos2 | True |
| S-MULTI_neg | True |
| suggest_serves_on_agreement | True |
| suggest_refuses_on_disagreement | True |
| KC_needs_3 | True |
| PC_not_served | True |
| G6_rule_haiku | True |
| G6_reported_sonnet | True |
| pass | True |

## 10. Hypotheses
| | claim | verdict | evidence |
|---|---|---|---|
| H1 | A2S wrong by gold <= fresh A2's rate on every arm | **FAILS** | sonnet A2S 2.44% vs A2 1.20%; opus A2S 0.00% vs A2 0.57%; haiku A2S 3.18% vs A2 1.13%; fable A2S 0.63% vs A2 0.57% |
| H2 | GENUINE wrong under A2S = 0 on M-sonnet SEAL | **FAILS** | genuine: w10_T3_003280, w10_T3_006604, w10_T3_006914 |
| H3 | Z-SLOT + S-MULTI cost < 3% false abstention on DEV | **HOLDS (cost)** | sonnet S-MULTI 0.4%, Z-SLOT 0.0%; opus S-MULTI 0.1%, Z-SLOT 0.0%; haiku S-MULTI 0.0%, Z-SLOT 0.0%; fable S-MULTI 0.1%, Z-SLOT 0.0% |
| H4 | SUGGEST-REACH >= 30% on T1-T3, falling with tier; T4 and P4 < 15% (strict, E-SAMPLE) | **FAILS** | sonnet: T1 38.5%, T2 47.1%, T3 19.3%, T3p 36.4%, T4 5.4%, P4 0.0%; opus: T1 18.5%, T2 59.0%, T3 13.7%, T3p 27.3%, T4 3.9%, P4 0.0%; haiku: T1 16.5%, T2 62.6%, T3 5.7%, T3p 27.7%, T4 0.9%, P4 0.0%; fable: T1 25.0%, T2 53.5%, T3 14.2%, T3p 24.8%, T4 1.7%, P4 0.0% |
| H5 | P1-P3 certified >= 90% at zero wrong, model-free | **FAILS** | D/seal P1 86.7% (0 wrong); D/seal P2 67.5% (0 wrong); D/seal P3 24.8% (0 wrong); D/replay P1 87.2% (1 wrong); D/replay P2 67.5% (0 wrong); D/replay P3 25.6% (0 wrong) |
| H6 | P4: fresh reading reach < 50%; every P4 wrong traces to reading, never to formula | **HOLDS (reach)** | sonnet P4 fresh A2 47 / 974 scorable (4.8%), 0 wrong; opus P4 fresh A2 46 / 933 scorable (4.9%), 0 wrong; haiku P4 fresh A2 0 / 641 scorable (0.0%), 0 wrong; fable P4 fresh A2 60 / 977 scorable (6.1%), 0 wrong |
| H7 | PC concept items: 0 certified on every arm | **HOLDS** | sonnet 0, opus 0, haiku 0, fable 0 |
| H8 | engine-in-front TOKENS/QUERY <= 50% of LLM-only overall, > 80% on T4/P4 | **FAILS** | sonnet answer-only 64%, full 324%, T4+P4 100%; opus answer-only 64%, full 315%, T4+P4 100%; haiku answer-only 65%, full 197%, T4+P4 100%; fable answer-only 62%, full 313%, T4+P4 100% |
| H9 | KC serves > 0 on SEAL with KC-WRONG > 0 | **HOLDS** | sonnet 0 served / 0 wrong, opus 0 served / 0 wrong, haiku 1 served / 1 wrong, fable 7 served / 0 wrong |
| H10 | scale monotone: haiku >= sonnet in genuine A2S wrongs, <= in REACH-S | **HOLDS** | genuine sonnet 3 / haiku 6; REACH-S sonnet 24.2% / haiku 12.0% |
| H11 | value-right/reading-wrong hits are 5-20% of A2S serves; PLAN-AGREEMENT minting excludes them | **FAILS (share outside 5-20%)** | sonnet 143 / 365 (39.2%); opus 174 / 315 (55.2%); haiku 58 / 148 (39.2%); fable 187 / 297 (63.0%) |
| H12 | acquisition curve (A2S serves vs ACQ position) non-flat | **HOLDS (non-flat)** | sonnet [0, 0, 13, 89, 172, 299]; opus [0, 0, 5, 35, 136, 288]; haiku [0, 0, 4, 32, 114, 246]; fable [0, 0, 7, 48, 147, 287] |

Commentary. H1 fails where it matters (sonnet 2.4% vs 1.2%, haiku 3.2% vs 1.1%): suggested readings are wrong by gold MORE often than fresh ones on the two arms with the most wrong own answers, because a suggested plan is admitted on agreement with the answer alone while a fresh reading also passes the gates on its own structure. H2 (the crux) fails by three items. H3 holds on cost; whether the two rules remove 'every V10-class wrong' cannot be shown, since the V10 classes were defined on V1.9's items - on SEAL no wrong is an echo donor (N23) and none is a slot-less item. H4, H5 (coverage), H8, H11 fail; H6, H7, H9, H10, H12 hold. H11's measured share of value-right/plan-different hits among A2S serves that also had an admitted fresh reading is 39-63%, far above the predicted 5-20%: two different plans reach the same number on most items (commutations, reorderings, a distractor added and subtracted), and PLAN-AGREEMENT minting kept every one of them out of the library as a new donor (they were counted, not minted).

## 11. Outcome on the frozen ladder
Outcome **E**: SAFETY-GEN fails: 3 genuine A2S wrongs on M-sonnet SEAL; SAFETY-CHAIN fails (P1-P3 model-free wrong on a sealed pass: sonnet/replay=1, opus/replay=1, haiku/replay=1, fable/replay=1, det/replay=1)
Ladder applied to the letter (F > E > D > C > B > A). F: no - GATE-CTRL passes (controls110.json, 11 batteries incl. the V1.9 set, Z-SLOT, S-MULTI positive and negative, suggest-on-agreement, refuse-on-disagreement, KC-needs-3, PC-not-served, G-P6 per arm) and the V1.9 numbers reproduce on the burned set. E: yes - SAFETY-GEN fails (3 genuine on M-sonnet SEAL) and SAFETY-CHAIN fails (B41: one model-free P1 wrong on REPLAY, every arm; SEAL alone would pass it). Had E not fired, D would (REACH-S 12-24% < 30% on every arm); had D not fired, C would (SAFETY-FA 2.4 / 3.2% on sonnet / haiku; TOKENS 62-65% answer-only, 197-324% full). B/A were never reachable: KC served 0 on sonnet and opus SEAL and was wrong on haiku (1/1) and fable REPLAY (1/3). Every bar except SAFETY-PC, RULES and SEALED-ONCE fails on at least one arm; opus alone passes SAFETY-GEN, SAFETY-FA and KC on SEAL (with KC untestable at 0 served).

## 12. What V1.10 claims, and does not
What V1.10 establishes. (1) Suggest-don't-serve with an own-answer filter is NOT a safety mechanism: at 400k scale it serves the model's wrong answers at the model's wrong-answer rate on the reachable items (0.0-3.2% by arm), and the sealed genuine count on the primary arm is 3, not 0. The only configuration at zero (opus) is the one with the fewest wrong answers to begin with. (2) The model-free exact path remains the only zero-wrong mechanism: 133,450 serves on SEAL at 0 wrong across four arms, plus 29,941 on the D arm; its one REPLAY wrong (B41) is a library plan that conflated weight and force under one cue key - a V1.8-class role error, fixable by dimension-checking the plan against the ask (V1.11 work). (3) Reach of suggestion on real text is 12-24% strict and is a T2 phenomenon; on authored multi-step stories and physics stories it is 0-5%. (4) The token economy of a reading-proposing pipeline is negative on single-pass traffic: 2-3x LLM-only. (5) Scale is monotone: more capable arms have fewer genuine wrongs (haiku 6, sonnet 3, fable 1, opus 0). (6) Instruments: RULES measured post hoc at < 0.5%; the KC shadow records no item identity (N35); one haiku reading file was malformed and mapped to FORMAT (N34); haiku authored one QC-passing gold that does not follow from its story (N36). Not claimed: any energy or latency number (none measured this version); any statement about un-sampled items beyond the exact path (the model saw 3.3% of SEAL).

## 13. Ledger (bug_audit_v1_10.md)
- N1 — P3 generator constraint relaxed at build
- N2 — Tooling: heredoc backslashes
- N3 — Token instrument positive control (procedural)
- N4 — W-400K built: 387,062 items
- B37 — builder rounded float golds to two decimals (caught by the D-arm smoke test, pre-run)
- N5 — distractor texts: sentence split on abbreviations
- N6 — bridge protocol deviation (harmless)
- N7 — authoring brief: "intermediate quantity's final state" misread (wave 0, haiku)
- N8 — g = 9.81 vs the generator's 9.8
- B38 — P-tier fresh readings gated by the wrong gate (caught on the ACQ P1 test, pre-sealed)
- N9 — an author agent delegated to sub-agents
- B39 — grader dropped exponents (found on the D-arm ACQ baseline, pre-sealed)
- B40 — the V1.6 minted library fired on a word problem (D-arm ACQ baseline, pre-sealed)
- N10 — session rate limit (2026-09-08 ~19:30 IST, reset 20:30): 20 bridge agents terminated mid-job
- N11 — haiku over-nulled one reading block
- N12 — ACQ arm passes on the non-authored tiers (`<arm>_acq_base`, lib_<arm>_acq1.json)
- N13 — Fable model limit (2026-09-08 ~22:30 IST) and one stray file
- N14 — haiku wrote six reading files for ids that exist in no batch
- N15 — authored stories merged; QC restricted to the scored set; hashes re-recorded
- N16 — a sonnet DEV reading agent reports having "run a slot-substitution check"
- N17 — QC applied; QC-rejected items are not scored on any split (engine change before any sealed run)
- N18 — haiku over-nulled the ACQ T4 9–17 reading block (as N11)
- N19 — sonnet P4 answer files written under rotated names (renamed, not rewritten)
- N20 — second session limit (2026-09-09 ~23:20 IST, reset 03:00): 14 reading agents killed
- N21 — M-sonnet ACQ pass and the three DEV passes (acq1 libraries)
- N22 — M-haiku ACQ pass on the authored tiers (acq2)
- N23 — M-haiku DEV pass on the authored tiers (dev2, acq2 library)
- N24 — M-fable ACQ pass on the authored tiers (acq2)
- N25 — M-fable DEV pass on the authored tiers (dev2)
- N26 — one reading file rewritten by its own proposer (content identical)
- N27 — M-opus ACQ pass on the authored tiers (acq2)
- N28 — M-sonnet ACQ pass on the authored tiers (acq2) and M-opus DEV (dev2)
- N29 — M-sonnet DEV (dev2) and SEAL answer coverage
- N30 — proposer memorisation caveat on GSM8K-train items
- N31 — haiku over-nulls on SEAL (same class as N11/N18)
- N32 — third session limit (2026-09-10 ~04:05 IST, reset 08:00) and a haiku agent that wiped its own output directory
- D-arm sealed passes (engine only, once each): SEAL 0 wrong, REPLAY 2 wrong
- B41 — V1.6 tier-A physics binds by value: equal mass and acceleration collapse to the weight template (sealed wrong, REPLAY P1)
- B42 — V1.6 conversion reflex fires on a rate ask (sealed wrong, REPLAY T3)
- N33 — haiku REPLAY answer files short by one or two ids
- N34 — one malformed haiku REPLAY reading file
- N35 — RULES measured post hoc; KC shadow wrong not identifiable
- B43 - GENUINE A2S wrongs on M-sonnet SEAL (SAFETY-GEN fails)
- N36 - B41/B42 reproduce on every arm; one authored gold wrong past QC
- Close of ledger for V1.10

## Reproduction
```
python tools/build_w400k.py                      # W-400K + HASHES.json (already built; hashes must match)
python tools/engine110.py controls               # controls110.json pass=true
python tools/engine110.py run --arm <arm> --split seal --tag seal --lib-in results/v110/lib_<arm>_acq2.json
python tools/engine110.py tokens                 # tokens110.json from bridge/usage.jsonl
python tools/report110.py                        # this report
```
