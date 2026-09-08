# V1.9 SPEC — Reading Reflexes: One Model, an Honest Engine

## Can an escalation-feedback loop with ONE model admit readings of natural-language questions with zero genuine wrong admissions — when the engine, not a second model, carries the honesty — and can an admitted reading serve a question phrased differently from its donor?

**STATUS: DRAFT v2 (2026-09-08) — §12 decisions OPEN for the user.
Freezes as tag `v1.9-plan` on the user's word. Designed from the S1
pre-study (branch `v1.9-reading`, tag `s1-plan`, `S1_SPEC.md`,
`bug_audit_s1.md`). Draft v1's second-model-family veto is withdrawn:
the architecture is one model that finds structure and an engine that
does everything else, and the safety must live in the engine.**
§7–§10 and the §11 risk register never change after the first sealed
run; amendments are dated blocks.

Built on V0.1–V1.8 and S1. No prior version, tag, snapshot, dataset,
report or log is modified. Full arc protocol: pre-registration,
hashed sealed set, dev/sealed discipline, bugs B-numbered with
superseded runs preserved, single-command reproduction, finalize with
tag + frozen snapshot (`.env` excluded) + report + memory. Bridge
only; no API spend; the live key in `.env` is never read.

---

## 1. What S1 measured, and what it means under one model

S1 (SEALED 1,200, run once): readings reach 66.3% of real GSM8K/ASDiv
items and are 97.5% correct; admission by agreement with a direct
answer admitted 703 and was wrong by gold 8 times (1.14%): 3 corpus
gold errors, 2 phrasing conventions, 1 integer-division semantics,
2 genuine shared misreadings (0.28%). Zero readings refired on any
other question at any skeleton abstraction level.

Draft v1 proposed a second model family as a veto. Withdrawn: the
reflex engine is ONE model structure. Re-reading the S1 wrongs under
that constraint, every genuine misread *dropped a stated quantity
that happened to be a word*: "thrice", "five times", "Chase and Rider
… they". The arc already has the rule for digits — B28 / G-P4:
**an unconsumed stated quantity is an incomplete read, and an
incomplete read never serves.** V1.9 extends it to words.

Measured on S1's own rows (crude prototype, no tuning; §4.3 is the
frozen form): a lexical-honesty gate kills 5 of the 8 sealed by-gold
wrongs — the genuine "thrice / five times" misread and all three
gold-errata cases — and 104 of 786 correct readings (13.2%). The
three sealed survivors are exactly the three structural classes S1
named (geometry "around", ratio ask, integer division). The DEV
plural-agents misread survives the prototype only because its factor
2 coincides with "twice"; the cardinality form (one word, one literal
occurrence — G-P4′'s matching) closes it.

Measured on S1 SEALED with NO agreement signal — the proven pipeline
(gate, witness, abstain) alone — and then each engine-only addition:

| stage | served | wrong |
|---|---|---|
| gates + witness (V1.8 stack, reading mode) | 796 | 20 (2.5%) |
| + G-P6 lexical honesty | 671 | 13 (1.9%) |
| + structural abstentions | 638 | 6 (0.94%) |
| + reading reproduces the escalation's own answer | 570 | **0** |

The six survivors of every engine-only rule are interpretive
misreads — the class V1.3 proved dimensional and honesty gates cannot
see, and the class generator text never contained. The escalation's
own answer is not a second model: it is the value the user already
received, playing the role golds played in V1.0's probation and
V1.8's harvest. The proven pipeline always probated against a value;
on a live escalation this is the only value there is.

So the one-model design is: **the escalation's own answer is the
probation value; the engine's honesty gates and structural
abstentions are the safety.** No second model.

---

## 2. Thesis

> With one model proposing readings and the same escalation's answer
> as the only agreement signal, an engine that refuses any reading
> which leaves a stated quantity — digit OR word — unconsumed, and
> abstains on the four structural classes S1 found, admits zero
> genuine wrong readings at a measured reach cost. Reuse is keyed on
> structure, not surface, and is measured before it is ever served.

---

## 3. What is honestly unknown

**Q1 — zero genuine wrongs at what reach?** The prototype's 13%
reach cost is on unconsumed *irrelevant* words ("four years later").
The frozen gate may cost more or less; sealed volume decides whether
"zero genuine" is a rate.

**Q2 — same-model agreement's residual value.** With the gates
carrying safety, does agreement with the escalation's answer still
filter anything (S1: admitted-correct 98.9% vs executed 97.5%)? A
measured secondary, not a requirement.

**Q3 — does cue signature predict structure?** The phrasing-
independent reuse key is the CUE SIGNATURE (roles18 cue per stated
number, in order, plus ask type). Its purity is measurable on S1's
readings at no bridge cost.

**Q4 — transfer wrong-fire under structural reuse.** Positional
binding of a same-key question into a donor's plan is the B32 family;
measured, never served.

**Q5 — gold errata.** Three of eight S1 wrongs were the corpus's. The
frozen by-gold metric counts them; the genuine count is the crux;
nothing is relabelled.

---

## 4. Architecture

```
ITEM (natural-language question; gold hidden from the model)
  |
  +-- PROPOSER (bridge, sonnet; opus arm optional): READING = plan
  |     over slots {n0..nk} + structural constants. ISOLATION: the
  |     agent receives only the batch file (numbers pre-indexed),
  |     may not run code; reader19 validates every file.
  |
  +-- reader19.bind -> plangate18 (reading mode) -> G-P6 (new)
  |     -> structural abstentions (new) -> chainexec17 -> value v,
  |     or ABSTAIN with the gate's reason.
  |
  +-- ANSWER: the escalation's own direct answer (same model family
  |     as the proposer; in S1, haiku). Free in production: it is
  |     the answer the user got.
  |
  +-- ADMISSION (graded; A2 is the version's rule):
  |     A0  agreement only                          (S1 baseline)
  |     A1  G-P6 + structural abstentions, no agreement
  |     A2  A1 + agreement
  |
  +-- GRADING (offline): FALSE-ADMIT by gold with classification;
  |     GENUINE-WRONG count; reach cost per gate and rule.
  |
  +-- STRUCTURAL REUSE (measured, not served): key = (cue signature,
        ask type, number count); CUE-PURITY on DEV; REUSE-SERVED /
        REUSE-WRONG on SEALED.
```

### 4.1 The reading reflex class (S1, unchanged)

`{"plan": planschema17 plan over slots, "key": cue signature, "donor":
id, "proposer": model, "admission": "A2", "kind": "reading"}`.

### 4.2 Cue signature (Q3)

`roles18.analyze(text)` cue per stated number, in order, plus the ask
type (count / amount / ratio / bool / other, frozen regex table). A
fixed function of the text.

### 4.3 G-P6 — lexical honesty (the version's gate)

Stated quantities are digits AND words. A frozen table maps quantity
words to values: number words one…twenty, thirty…ninety, hundred,
thousand; "dozen" 12; "half" 0.5, "quarter" 0.25, "third" 1/3;
"twice"/"double(d)" 2, "thrice"/"triple(d)" 3; "<word> times" as
its number. PLURAL-AGENT: two capitalised names joined by "and" with
a later "they / both / together / altogether" counts as a stated 2.
Rule: every word-quantity token must be matched to a DISTINCT literal
occurrence in the plan (magnitude equality; a slot whose digits
equal the word's value also counts), by the same bipartite matching
G-P4′ uses for digits; an unmatched token kills the reading. Digit
tokens keep G-P4 / G-P4′ as they are. Ordinals ("first", "second"),
"one" and "a" are not quantities. False-abstain cost on DEV is a
reported metric, never tuned away on SEALED.

### 4.4 Structural abstentions (from the S1 anatomy)

- **S-INT**: count-type ask ("how many …") and v not an integer →
  ABSTAIN.
- **S-RATIO**: ask contains "ratio" → ABSTAIN.
- **S-PCT**: "N% (higher|lower|more|less) than" or "N times more
  than" in the text → ABSTAIN (base / multiplier convention
  ambiguous).
- **S-GEOM**: "around" with a stated diameter/radius or "circular" →
  ABSTAIN.
Each rule: one abstaining control, one passing near-twin, and its
false-abstain rate on DEV.

### 4.5 Positive controls before any counting run (B24)

S1's controls; G-P6 battery (the S1 "thrice/five times" reading must
die; the S1 plural-agents reading must die under cardinality; a
reading consuming every word must pass; "four years later" with an
irrelevant "four" must die — the cost is deliberate and visible);
one control pair per structural rule; cue-signature battery
(paraphrase pair → same key; one cue changed → different key);
proposer-isolation battery (reader19 rejects any file not exactly
`{"plan": …}`; agent prompt byte-identical; no code).

---

## 5. Datasets (frozen, hashed before any bridge call)

```
DEV      S1's 1,800 items (exposed; readings and haiku answers exist)
         — gates, rules, controls, purity at zero bridge cost.
SEALED   the corpus items S1 never sampled: GSM8K test 419 + ASDiv
         1,405 = 1,824 (or a 1,200 hashed subsample, §12); readings
         and haiku answers collected once, scored once. Tokenizer
         fixes (glued units, leading-dot decimals; S1 note N6)
         applied before the batches are written.
REUSE    SEALED keyed against DEV+SEALED readings admitted under A2;
         a reading never serves its own donor.
```

---

## 6. Arms

| arm | proposer | answer | admission | n |
|---|---|---|---|---|
| A0 | sonnet | haiku | agreement only | SEALED |
| A1 | sonnet | — | G-P6 + rules | SEALED |
| **A2 (primary)** | sonnet | haiku | G-P6 + rules + agreement | SEALED |
| A2-opus | opus | haiku | as A2 | SEALED, if bridge time allows |
| D-llama | sonnet | llama-3.1-8B (local) | diagnostic only, on whatever prefix completes | not an architecture arm |

The llama row is a diagnostic of R1 (how much a foreign veto would
have added), explicitly outside the one-model architecture; it is
reported, never used for admission.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| H1 | A2 admits ZERO genuine wrong readings on SEALED | the crux; predicted from the S1 re-analysis (every genuine misread dropped a word-quantity or hit a structural class) |
| H2 | A2's FALSE-ADMIT by gold ≤ 0.5% | uncertain — S1's errata alone were 0.43%, and G-P6 killed all three errata cases only by luck of their wording |
| H3 | G-P6's false-abstain cost on DEV is 10–20% of executed readings | predicted from the prototype (13.2%) |
| H4 | each structural rule < 3% false abstention on DEV | plausible |
| H5 | agreement adds little once the gates hold: A1 and A2 GENUINE-WRONG both 0; A2 admits ≥ 85% of A1 | predicted |
| H6 | CUE-PURITY on DEV < 70% | predicted (65–82% bare tokens) |
| H7 | structural reuse on pure keys serves > 0 sealed items and its wrong-fire is NOT zero | predicted — B32 on natural text |
| H8 | REACH ≥ 50% after tokenizer fixes and before G-P6 | predicted |

---

## 8. Metrics (FROZEN)

Primary: per admission rule — admitted, FALSE-ADMIT by gold with
classification, GENUINE-WRONG, READING-CORRECT among admitted, reach
cost; G-P6 kills and false-abstain rate; per-rule false-abstain
rates; CUE-PURITY; REUSE-SERVED / REUSE-WRONG. Secondary: REACH,
READING-CORRECT, answer accuracy, disagree-but-correct, gate-kill
anatomy, isolation violations, D-llama prefix numbers.

---

## 9. Thresholds (FROZEN)

```
GATE-CTRL     all §4.5 batteries pass before counting.
SAFETY-GEN    GENUINE-WRONG admissions under A2 on SEALED = 0 (every
              by-gold wrong published with its classification and
              row; one genuine = E).
SAFETY-FA     FALSE-ADMIT by gold under A2 <= 0.5%.
REACH         >= 50% of SEALED executable before G-P6.
GATE-COST     G-P6 + rules abstain <= 25% of executed readings on
              SEALED (else safe-and-inert, rung D).
RULES         each structural rule < 3% false abstention on DEV.
PURITY        reported; reuse measured on pure keys only.
REUSE-SAFE    REUSE-WRONG = 0 on SEALED for reuse to be declared
              servable later; any wrong reported as the rate.
SEALED-ONCE   readings, answers, scores on SEALED once.
```

---

## 10. Outcome ladder (FROZEN; F > E > D > C > B > A)

```
F  a control battery cannot pass, or S1/V1.8 stop reproducing.
E  SAFETY-GEN fails: the honest engine still admitted a genuine
   misread with one model — report the case and its class.
D  SAFETY-GEN holds but REACH < 30% or GATE-COST > 25%: safe and
   inert.
C  SAFETY-GEN, REACH, GATE-COST hold but SAFETY-FA fails on gold
   errata alone: safe in truth, wrong by the corpus; both numbers.
B  all safety and reach bars hold; reuse measured; REUSE-WRONG > 0
   or REUSE-SERVED = 0: safe one-phrasing reflexes.
A  B plus REUSE-SERVED > 0 at REUSE-WRONG = 0 on pure keys.
```

---

## 11. Risk register (FROZEN with §7–§10)

```
R1  One model, one prior: a misread that consumes every word and
    hits no structural class is invisible to this engine. Detect:
    SAFETY-GEN. Mitigate: none in V1.9 — it is the thing measured;
    D-llama reports what a foreign veto would have added, as a
    diagnostic only.
R2  G-P6 over-abstains on irrelevant word-quantities ("four years
    later"). Detect: false-abstain on DEV. Mitigate: none; the cost
    is the honesty rule's, reported (GATE-COST rung D exists).
R3  Word table gaps ("a couple", "a score", "half a dozen"). Detect:
    residual by-gold wrongs' anatomy. Mitigate: table frozen with
    the spec; gaps become the next version's list.
R4  Gold errata dominate by-gold wrongs. Detect: classification
    published. Mitigate: SAFETY-GEN is the crux; nothing relabelled.
R5  Proposer computes / value-dependent readings. Detect: isolation
    battery; singular-key flags. Mitigate: no code; validation;
    singular readings never reused.
R6  Cue signatures mostly "bare" -> low purity, small pure subset.
    Detect: PURITY. Mitigate: none (H6).
R7  Positional binding on same-key questions is the B32 family.
    Detect: REUSE-WRONG. Mitigate: nothing served.
R8  Tokenizer gaps. Mitigate: fixed before batches; frozen by hash.
R9  DEV fully exposed. Mitigate: SEALED = never-sampled items only.
R10 Agreement tolerance masks rounding. Detect: near-miss ledger.
R11 The escalation answer as agreement signal is the same model's
    prior twice (reading + answer). Detect: A1 vs A2. Mitigate: the
    design does not rely on it (H5).
```

---

## 12. Decisions — OPEN for the user

1. SEALED = all 1,824 never-sampled items, or a 1,200 hashed
   subsample (the llama diagnostic is the only throughput concern;
   the primary arm needs sonnet + haiku only).
2. G-P6 word table as §4.3; add or strike entries before freeze.
3. Structural rules S-INT / S-RATIO / S-PCT / S-GEOM as §4.4.
4. Reuse measured, never served, in V1.9.
5. opus proposer arm if bridge time allows.
6. D-llama diagnostic on whatever prefix completes, outside the
   architecture; or drop it entirely.
7. Ladder as §10.

---

## 13. What this version claims, and does not

It claims a one-model escalation-feedback loop whose safety is the
engine's honesty about every stated quantity, digit or word, plus
four structural abstentions — measured against real golds for
genuine wrong admissions at sealed volume — and the first measurement
of structure-keyed reuse on natural text. It does not add a second
model, does not serve any reused reading, and does not relabel a gold
it disagrees with.
