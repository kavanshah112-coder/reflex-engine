# V1.9 FINAL REPORT — Reading Reflexes with Escalation Feedback (branch v1.9-reading)

**Pre-registered outcome: E** on the frozen ladder (`V19_SPEC.md` §10, tag `v1.9-plan`).

## Headline

- **Primary arm (sonnet readings, haiku answers), SEALED 1,200, run once:** REACH 66.3% (796 executable readings), READING-CORRECT 97.5%, admitted by agreement 703, **FALSE-ADMIT 1.1% (8 of 703)**, READING-CORRECT among admitted 98.9%, haiku correct 87.6%, near-misses 1, disagree-but-correct 81.
- **llama arm:** not run to completion (see §5).
- **DEV 600 (for the record):** REACH 69.0%, READING-CORRECT 96.6%, FALSE-ADMIT 1.3% (5 of 398), haiku 95.3%.
- **Transfer:** L0 0 refire pairs / 0 served / 0 wrong; L1 0 / 0 / 0; L2 0 / 0 / 0 (skeletons: 1200 / 1200 / 1200 among 1,200).
- **GATE-CTRL:** PASS.

## 1. What was run

1,800 items sampled (seed 1900) from the frozen V1.3 corpora — 900 GSM8K test, 900 ASDiv — split DEV 600 / SEALED 1,200 by id hash and hashed before any bridge call. Golds never left `results/v19/data/`. For every item a *proposer* (sonnet, via bridge agents) emitted a READING: a plan over the question's numbers as positional slots `{n0}..{nk}` plus structural constants, no values, no arithmetic. The engine bound the item's own numbers, ran the plan through the V1.8 gate stack (G-P1..G-P5, with three reading-mode relaxations recorded in the spec) and the witness, and produced a value or an abstention. An *answerer* (haiku via bridge; llama-3.1-8B locally where it ran) answered each question directly with one number, never seeing the reading. AGREEMENT between the engine's value and the answer is the production-loop admission signal; offline it is graded against the corpus gold, which is the only way to learn how often agreement admits a wrong reading.

## 2. Results per arm

| arm | phase | n | executed (REACH) | reading correct | admitted | FALSE-ADMIT | admitted correct | answerer correct | disagree-but-correct | near-miss |
|---|---|---|---|---|---|---|---|---|---|---|
| R-sonnet-haiku | dev | 600 | 414 (69.0%) | 96.6% | 398 | **5 (1.3%)** | 98.7% | 95.3% | 7 | 3 |
| R-sonnet-haiku | sealed | 1200 | 796 (66.3%) | 97.5% | 703 | **8 (1.1%)** | 98.9% | 87.6% | 81 | 1 |

Per corpus (primary, sealed): gsm8k n=606 executed 453 correct 443 admitted 368 false-admit 4; asdiv n=594 executed 343 correct 333 admitted 335 false-admit 4.

Gate-kill anatomy (primary, sealed): `G-P3: choice/threshold ask; final is 'evaluate` ×25; `G-P4: stated quantity 1 unused` ×12; `G-P4: stated quantity 3 unused` ×10; `G-P4: stated quantity 2 unused` ×6; `G-P4: stated quantity 6 unused` ×5; `G-P4: stated quantity 10 unused` ×4; `G-P4: stated quantity 5 unused` ×4; `G-P4: stated quantity 18 unused` ×3; `G-P4: stated quantity 12 unused` ×3; `G-P4: stated quantity 8 unused` ×3.

## 3. What the false admits are

5 admitted readings disagree with the corpus gold (1.26% of 398):
- a0890 (ASDiv): reading and haiku 5; gold 6. 16−x = 2(11−x) gives
  x = 6, London then 5. The gold looks wrong.
- g1309 (GSM8K): reading and haiku 2,180; gold 2,280.
  430+750+300+700 = 2,180. The gold looks wrong.
- g0368: "three times more points than Sara, who scored 8" — reading
  3×8−14 = 10; gold takes "three times more" as 4× (32−14 = 18).
  Phrasing convention.
- g0768: "Ezra read twice as many as Ahmed … 300 … 150 more" —
  reading Ahmed = 150, total 600; gold recomputes Ahmed from 450
  (675). Phrasing convention.
- g0782: "Chase and Rider … ride thrice a day" — reading counts one
  rider (27); gold counts two (54). A genuine shared misreading:
  the V1.3 class, 1 of 398.
Per R6 the golds are not edited and the frozen FALSE-ADMIT counts
all five. The sealed run decides the letter; this note is the
anatomy the report must carry beside the number.

The sealed false admits are listed in `results/v19/R-sonnet-haiku_sealed_rows.json` (rows with `agree` true and `reading_correct` false) and classified in the ledger after the run; the frozen metric counts every one of them regardless of class.

## 4. Transfer

A reading serves only its donor's exact skeleton in V1.9; transfer was measured, not served. The counts above are the whole result: on natural text, even with names, units, punctuation and stopwords abstracted (L2), phrasings do not recur inside 1,200 items. Readings are one-phrasing reflexes on these corpora; compounding, if any, would have to come from the structure of the plan rather than the surface of the question — which is V1.8's binder problem restated for natural language.

## 5. The llama arm

ollama wedged during the DEV run (a single request exceeded 300 s at 0% GPU utilisation); after one server restart it answered in ~5 s. The arm is reported only to the extent it completed; see the summaries present in `results/v19/`.

## 6. Outcome on the frozen ladder

- SAFETY-FA ≤ 0.5%: **fail** (1.1%).
- REACH ≥ 30%: pass (66.3%).
- QUALITY ≥ 80%: pass (97.5%).
- FILTER: pass (98.9% admitted vs 97.5% executed).
- TRANSFER: no level served above L0 at zero wrong-fire (no refires at all).
- GATE-CTRL: PASS; SEALED-ONCE: every sealed arm run once.

**OUTCOME E.** Agreement-based admission is not safe enough as a production loop at this answerer: it admits wrong readings above the frozen bar. The anatomy (§3) says what the wrongs are; the report does not relabel them.

## 7. What V1.9 claims, and does not

It claims a working, gold-graded measurement of the escalation-feedback loop's admission signal on real questions — reach, quality and false-admit rate with their anatomy — and a new reflex class whose only content is which stated number goes where. It does not claim the loop is safe to run live (the letter says what the number says), does not claim transfer (there was none to measure), and does not relabel corpus golds it disagrees with.

## Reproduction
```
python tools/reader19.py prep ; python tools/reader19.py controls
# bridge: proposer/answerer agents write results/v19/bridge/{readings_<m>_<phase>/, answers_<m>_<phase>_NN.json}
python tools/answer19_llama.py --phase dev|sealed
python tools/reader19.py score --phase dev|sealed --proposer sonnet --answerer haiku|llama
```
