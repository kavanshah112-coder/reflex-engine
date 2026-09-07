# V1.9 SPEC — Reading Reflexes: a Live Loop That Cannot Admit What It Cannot Check

## Can an escalation-feedback loop admit readings of natural-language questions with ZERO genuine wrong admissions, and can an admitted reading serve a question phrased differently from its donor?

**STATUS: DRAFT v1 (2026-09-08) — §12 decisions OPEN for the user.
Freezes as tag `v1.9-plan` on the user's word. Designed from the S1
pre-study (branch `v1.9-reading`, tag `s1-plan`, `S1_SPEC.md`,
`bug_audit_s1.md`).** §7–§10 and the §11 risk register never change
after the first sealed run; amendments are dated blocks.

Built on V0.1–V1.8 and S1. No prior version, tag, snapshot, dataset,
report or log is modified. Full arc protocol: pre-registration,
hashed sealed set, dev/sealed discipline, bugs B-numbered with
superseded runs preserved, single-command reproduction, finalize with
tag + frozen snapshot (`.env` excluded) + report + memory. Bridge
only; no API spend; the live key in `.env` is never read.

---

## 1. What S1 measured, exactly

S1 ran the feedback loop offline against corpus golds: sonnet
proposed a READING (a plan over a question's numbers as positional
slots) for 1,800 GSM8K/ASDiv items; the engine bound, gated (G-P1..G-P5
with three reading-mode relaxations) and executed it; haiku (and
llama-3.1-8B locally) answered directly; AGREEMENT between the
engine's value and the answer was the admission signal.

| S1 number (SEALED 1,200, run once) | value |
|---|---|
| REACH — readings that pass the gates and execute | 66.3% (796) |
| READING-CORRECT (vs gold) | 97.5% |
| admitted by haiku agreement | 703 |
| FALSE-ADMIT by gold | **8 = 1.14%** (bar 0.5%: S1 OUTCOME E) |
| — of which corpus gold errors | 3 |
| — phrasing / format conventions | 2 |
| — integer-division semantics | 1 |
| — **genuine shared misreadings** | **2 = 0.28%** |
| haiku correct | 87.6% |
| correct readings rejected by disagreement | 81 |
| transfer refires at skeleton levels L0 / L1 / L2 | 0 / 0 / 0 |
| DEV: haiku ∧ llama agreement | 149 admitted, 1 "wrong" = a gold error, **0 genuine** |
| DEV: llama alone | 35.3% correct; 252 correct readings rejected |

Five learnings, each now a design rule:

1. **Agreement with one same-family answerer admits ~1 in 90 wrong by
   gold, ~1 in 350 wrong in truth.** Not enough for the arc's
   standard; the rest is the corpus's own errata and conventions.
2. **A second, independent-family answerer as a veto removed every
   genuine misread on DEV** (0 of 149), at the cost of admitting 149
   instead of 398. Precision is bought with reach; a weak model is
   worth more as a veto than as an answerer.
3. **The wrong classes have structure**: integer-context asks with
   non-integer results, ratio asks, percent-base conventions, and
   "around/half" geometry. Structural abstentions can be aimed at
   them, each with a positive control.
4. **Proposers computed.** Some executed their plans "to check they
   run"; one picked a plan because the given values were coprime.
   Isolation must be structural.
5. **Surface reuse is dead on natural text.** Not two of 1,200 real
   questions share a skeleton even with names, units, punctuation
   and stopwords removed. If readings are to compound, reuse must be
   structural — V1.8's binder problem restated for natural language.

---

## 2. Thesis

> A reading reflex is admitted only when the engine's execution of
> the reading agrees with TWO answerers of different model families
> and passes structural abstention rules aimed at the wrong classes
> S1 found; the proposer is isolated from execution; and reuse is
> keyed on STRUCTURE — the reading's plan signature and the
> question's cue signature — not on the surface skeleton. V1.9
> measures, offline and gold-graded, whether that loop admits zero
> genuine wrong readings, how much reach the veto costs, and whether
> structure-keyed reuse serves any real question its donor never saw
> without being wrong.

---

## 3. What is honestly unknown

**Q1 — zero genuine wrongs at what reach?** S1's dual-agreement result
is 0 of 149 on DEV. Sealed volume decides whether that is a rate or
luck.

**Q2 — does cue signature predict structure?** A phrasing-independent
key must map a new question to a reading. The candidate key is the
CUE SIGNATURE (roles18 cue per stated number, in order, plus the ask
type). Whether two questions with the same cue signature get the same
plan is unmeasured; S1's readings can measure it at no bridge cost.

**Q3 — transfer wrong-fire under structural reuse.** Positional
binding of a new question into a donor's plan is B32's whole family;
cue-signature equality is the guard. How often is it wrong?

**Q4 — gold errata.** Three of eight sealed "wrongs" in S1 were the
corpus's. A gold-graded loop needs a policy for disagreements where
two answerers and the engine agree against the gold: listed for
adjudication, never auto-relabelled; the frozen metric counts them.

**Q5 — llama throughput.** The 8B answerer ran at ~2 min per item on
this box in S1 (partial offload). An arm that cannot finish is
reported as such; no result is extrapolated.

---

## 4. Architecture

```
ITEM (natural-language question; gold hidden from every model)
  |
  +-- PROPOSER (bridge, sonnet; opus arm optional): READING = plan
  |     over slots {n0..nk} + structural constants. ISOLATION: the
  |     agent receives ONLY the batch file and may not run code;
  |     the batch carries the numbers already indexed so nothing
  |     needs computing; every plan is validated by reader19, not by
  |     the proposer. A reading whose plan depends on the specific
  |     values (detected by the CUE-PURITY check, §4.3) is a probation
  |     kill, not a serve.
  |
  +-- reader19.bind -> plangate18 (reading mode) -> chainexec17
  |     -> value v or ABSTAIN
  |
  +-- STRUCTURAL ABSTENTIONS (new, deterministic, each with a control):
  |     S-INT   count-type ask ("how many", "how much" with a counted
  |             noun) and v not an integer -> ABSTAIN
  |     S-RATIO ask contains "ratio of" -> ABSTAIN
  |     S-PCT   text contains "% higher/lower/more/less than" and the
  |             plan divides by (1 +/- p/100) or multiplies by
  |             (1 -/+ p/100) -> ABSTAIN (convention-ambiguous)
  |     S-GEOM  "around" a circular object with a diameter/radius
  |             stated -> ABSTAIN
  |     Each rule is measured for its false-abstain cost on DEV.
  |
  +-- ANSWERERS: haiku (bridge) AND llama-3.1-8B (local), one number
  |     each, never seeing the reading.
  |
  +-- ADMISSION RULES (all three graded; A2 is the version's rule):
  |     A0  haiku agrees                      (S1 baseline)
  |     A1  haiku AND llama agree
  |     A2  A1 + structural abstentions
  |
  +-- GRADING (offline): FALSE-ADMIT by gold, with the post-hoc
  |     classification reported beside it (gold errata / convention /
  |     integer / genuine).
  |
  +-- STRUCTURAL REUSE (measured, not served):
        key(item) = (cue signature, ask type, number count)
        For every admitted reading, other items with the same key:
        bind positionally -> gate -> witness -> value; grade vs gold.
        REUSE-SERVED, REUSE-WRONG per rule; CUE-PURITY on DEV (§4.3).
```

### 4.1 The reading reflex class (from S1, unchanged)

`{"plan": planschema17 plan over slots, "key": cue signature,
"donor": id, "proposer": model, "admission": "A2", "kind":
"reading"}`. No pattern, no roles18 role requirement, no value.

### 4.2 Cue signature

`roles18.analyze(text)` gives each stated number a cue (unit:$,
unit:%, factor, addend, threshold, bare, …). The cue signature is the
tuple of cues in order of appearance plus the ask type (count /
amount / ratio / bool / other, from a frozen regex table). It is a
fixed function of the text — no model.

### 4.3 CUE-PURITY (the Q2 measurement, no bridge cost)

Group DEV readings by key; purity = share of keys whose executable
readings all share one plan signature (`planschema17.signature`).
Keys with mixed signatures are UNSAFE keys: a reading indexed by such
a key would serve a different structure to a same-looking question.
Reuse is measured only on PURE keys; the purity itself is a primary
metric. A reading whose plan signature differs from every other
reading of its key on DEV is flagged "value-dependent or singular"
and never reused.

### 4.4 Positive controls before any counting run (B24)

- S1's controls (gates, bind, agreement countable, skeleton levels).
- One control per structural rule: an item that must abstain and a
  near-identical item that must pass.
- Dual-agreement battery: reading wrong + haiku same wrong + llama
  different → NOT admitted; reading right + both agree → admitted.
- Cue-signature battery: two paraphrases with the same numbers and
  cues → same key; one differing cue → different key.
- Proposer-isolation battery: a batch file's schema carries no
  gold, no answer; the agent prompt is byte-identical across agents
  and forbids code; reader19 rejects any reading file that is not
  exactly `{"plan": …}`.

---

## 5. Datasets (frozen, hashed before any bridge call)

```
DEV       S1's 1,800 items (already exposed; golds, readings, haiku
          and llama answers exist) — every rule, control and purity
          number is developed here at zero bridge cost.
SEALED    the 1,824 corpus items S1 never sampled: GSM8K test 419 +
          ASDiv 1,405, hashed; readings (sonnet), haiku answers and
          llama answers collected once; scored once.
REUSE     SEALED items keyed against DEV+SEALED admitted readings
          (a reading never serves its own donor).
```

Golds live in `results/v19/data/` only; batch files carry
`{id, question, numbers}`.

---

## 6. Arms

| arm | proposer | answerers | admission | n |
|---|---|---|---|---|
| A0 | sonnet | haiku | haiku only | SEALED 1,824 |
| A1 | sonnet | haiku + llama | both | SEALED 1,824 |
| **A2 (primary)** | sonnet | haiku + llama | both + structural rules | SEALED 1,824 |
| A2-opus | opus | haiku + llama | both + rules | SEALED, only if bridge time allows |

The llama pass is the throughput risk (Q5): if it cannot complete on
SEALED, A1/A2 are reported on the completed prefix only and the
version says so on the first page.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| H1 | A2 admits ZERO genuine wrong readings on SEALED | predicted from S1 DEV (0 of 149); the version's crux |
| H2 | A2's FALSE-ADMIT by gold ≤ 0.5% (gold errata included) | uncertain — S1 sealed errata alone were 0.43% |
| H3 | the veto costs reach: A2 admits 35–45% of executed readings (S1: 149/414 = 36%) | predicted |
| H4 | structural rules remove the integer/ratio/percent/geometry classes with < 3% false abstention on DEV | plausible |
| H5 | CUE-PURITY on DEV < 70% — cue signatures do not determine structure on word problems | predicted (65–82% bare tokens) |
| H6 | structural reuse on pure keys serves > 0 sealed items and its wrong-fire is NOT zero | predicted — the B32 family on natural text |
| H7 | REACH stays ≥ 50% under the S1 tokenizer fixes (glued units, leading-dot decimals) | predicted |

---

## 8. Metrics (FROZEN)

Primary: per admission rule — admitted, FALSE-ADMIT by gold with
classification, GENUINE-WRONG count, READING-CORRECT among admitted,
reach cost (admitted/executed); CUE-PURITY on DEV; REUSE-SERVED and
REUSE-WRONG on SEALED per rule; false-abstain rate of each structural
rule on DEV. Secondary: REACH, READING-CORRECT, answerer accuracies,
disagree-but-correct, gate-kill anatomy, proposer format and
isolation violations, llama completion.

---

## 9. Thresholds (FROZEN)

```
GATE-CTRL     all §4.4 batteries pass before counting.
SAFETY-GEN    GENUINE-WRONG admissions under A2 on SEALED = 0
              (post-hoc classification of every by-gold wrong is
              published with the rows; one genuine wrong = E).
SAFETY-FA     FALSE-ADMIT by gold under A2 <= 0.5%.
REACH         >= 50% of SEALED executable.
VETO-COST     A2 admits >= 30% of executed readings.
RULES         each structural rule < 3% false abstention on DEV.
PURITY        CUE-PURITY on DEV reported; reuse measured on pure
              keys only.
REUSE-SAFE    REUSE-WRONG on SEALED under A2 keys = 0 for reuse to
              be declared servable at a later version; any wrong is
              reported as the B32-family rate on natural text.
SEALED-ONCE   readings, answers and scores on SEALED once.
```

---

## 10. Outcome ladder (FROZEN; F > E > D > C > B > A)

```
F  a control battery cannot pass, or S1/V1.8 stop reproducing.
E  SAFETY-GEN fails: the dual-veto loop still admits a genuine
   misread — agreement, even independent, is not a safe admission
   signal; report the case.
D  SAFETY-GEN holds but REACH < 30% or VETO-COST < 15%: safe and
   inert — the veto eats the reach.
C  SAFETY-GEN, REACH, VETO-COST hold but SAFETY-FA fails on gold
   errata alone: the loop is safe in truth and the corpus is not;
   report both numbers.
B  all safety and reach bars hold; reuse measured; REUSE-WRONG > 0
   or REUSE-SERVED = 0: readings are safe one-phrasing reflexes.
A  B plus REUSE-SERVED > 0 at REUSE-WRONG = 0 on pure keys —
   structure-keyed reuse on natural text without a wrong answer.
```

---

## 11. Risk register (FROZEN with §7–§10)

```
R1  Two Claude-family answerers would share a prior; llama is the
    veto precisely because it is weak and foreign. Detect: A0 vs A1
    genuine-wrong counts. Mitigate: llama is mandatory for A2.
R2  llama throughput (~2 min/item in S1). Detect: completion count.
    Mitigate: run it first and continuously; report prefix if short.
R3  Gold errata dominate by-gold wrongs. Detect: classification of
    every wrong published. Mitigate: SAFETY-GEN is the crux, SAFETY-
    FA stays as the objective number; nothing relabelled.
R4  Structural rules over-abstain. Detect: false-abstain on DEV per
    rule. Mitigate: a rule above 3% is reported and kept (frozen).
R5  Proposer computes / value-dependent readings. Detect: isolation
    battery; CUE-PURITY singular flags; agent transcripts sampled.
    Mitigate: no-code instruction + reader19 validation; a singular
    reading is never reused.
R6  Cue signatures are mostly "bare" on word problems -> purity is
    low and reuse is measured on a small pure subset. Detect: PURITY,
    pure-key count. Mitigate: none; that is H5.
R7  Positional binding on a same-key question is the B32 family.
    Detect: REUSE-WRONG. Mitigate: nothing served in V1.9.
R8  Tokenizer gaps (S1 N6) cost reach. Detect: null-reading reasons.
    Mitigate: glued units and leading-dot decimals fixed BEFORE the
    sealed batches are written; frozen with the hash.
R9  DEV is fully exposed (S1 sealed items included). Detect: all
    tuning on DEV, SEALED untouched by any model until the run.
    Mitigate: SEALED = never-sampled corpus items only.
R10 Agreement tolerance masks rounding (near-miss). Detect: near-
    miss ledger. Mitigate: reported.
```

---

## 12. Decisions — OPEN for the user

1. **SEALED = the 1,824 never-sampled corpus items** (all of them),
   as proposed; or a 1,200 subsample to shorten the llama pass.
2. **llama as mandatory veto** for the primary arm, as proposed; or
   opus as the second answerer (same family — R1 says no).
3. **Structural rules S-INT / S-RATIO / S-PCT / S-GEOM**, as listed;
   the user may add or strike rules before freeze.
4. **Reuse measured, never served** in V1.9, as proposed.
5. **opus proposer arm** conditional on bridge time, as proposed.
6. **Tokenizer fixes** (glued units, leading-dot decimals) applied
   before the sealed batches are written, as proposed.
7. **Ladder** as §10; in particular rung C for "safe in truth, wrong
   by errata".

---

## 13. What this version claims, and does not

It claims a live-loop admission rule — dual independent agreement
plus structural abstention — measured against real golds for genuine
wrong admissions at sealed volume, and the first measurement of
whether a reading can be keyed on structure rather than surface. It
does not claim the loop is production-ready (the letter says what the
sealed number says), does not serve any reused reading, and does not
relabel a gold it disagrees with.
