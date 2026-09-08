# V1.9 SPEC — Reading Reflexes: One Model, an Honest Engine

## Can an escalation-feedback loop built on ONE model admit readings of natural-language questions with zero genuine wrong admissions — the engine carrying the safety, the escalation's own answer serving as the probation value — and can an admitted reading serve a question phrased differently from its donor?

**STATUS: FROZEN (2026-09-08) — all §12 decisions RESOLVED by the
user as proposed, with one addition: four one-model arms (sonnet,
opus, haiku, fable), no local model anywhere. Tag `v1.9-plan`.** Designed from
the S1 pre-study (branch `v1.9-reading`, tag `s1-plan`, `S1_SPEC.md`,
`bug_audit_s1.md`). **Architecture constraint, fixed by the user: one
model.** The model that answered the escalation is the model that
proposes the reading; no second model, no second family, no
diagnostic arm with another model. §7–§10 and the §11 risk register
never change after the first sealed run; amendments are dated blocks.

Built on V0.1–V1.8 and S1. No prior version, tag, snapshot, dataset,
report or log is modified. Full arc protocol: pre-registration,
hashed sealed set, dev/sealed discipline, bugs B-numbered with
superseded runs preserved, single-command reproduction, finalize with
tag + frozen snapshot (`.env` excluded) + report + memory. Bridge
only; no API spend; the live key in `.env` is never read.

---

## 1. What S1 established

S1 ran the loop offline against corpus golds on 1,800 GSM8K/ASDiv
items (sonnet proposed readings; haiku answered; SEALED 1,200 scored
once). What carries into V1.9:

| S1 finding (SEALED unless noted) | number |
|---|---|
| readings that pass the gates and execute (REACH) | 66.3% |
| executed readings correct vs gold | 97.5% |
| admitted by agreement with a direct answer | 703 |
| wrong by gold among admitted | 8 = 1.14% (3 gold errata, 2 conventions, 1 integer semantics, **2 genuine misreads = 0.28%**) |
| correct readings rejected by disagreement | 81 |
| skeleton refires among 1,200 items, at three abstraction levels | 0 / 0 / 0 |

And the re-analysis that designs this version — the proven pipeline
(gate, witness, abstain) applied to S1's sealed readings with NO
agreement signal, then each engine-only addition, then the
escalation's own answer:

| stage | served | wrong |
|---|---|---|
| gates + witness (V1.8 stack, reading mode) | 796 | 20 (2.5%) |
| + G-P6 lexical honesty (word quantities, plural agents) | 671 | 13 (1.9%) |
| + four structural abstentions | 638 | 6 (0.94%) |
| + reading must reproduce the escalation's answer | 570 | **0** |

Every genuine misread S1 found dropped a stated quantity that was a
*word* ("thrice", "five times", "Chase and Rider … they") or fell in
one of four structural classes (integer count, ratio ask,
percent-base convention, "around" geometry). The six readings that
survive every engine-only rule are interpretive — the class V1.3
proved dimensional gates cannot see, and the class generator text
never contained. The escalation's answer closes them on this data.
It is not a second model: it is the value the user already received,
playing the role golds played in V1.0's probation and V1.8's harvest.

---

## 2. Thesis

> One model answers the escalation and, asked again, proposes a
> READING: a plan over the question's stated numbers, no values. The
> engine binds, gates and witnesses it, refuses any reading that
> leaves a stated quantity — digit or word — unconsumed, abstains on
> the four structural classes, and admits the reading only if its
> certified value reproduces the answer the same model already gave.
> V1.9 measures, against real golds at sealed volume, whether that
> loop admits zero genuine wrong readings, what reach the honesty
> costs, and whether structure — not surface — recurs enough for an
> admitted reading to serve a question it never saw.

---

## 3. What is honestly unknown

**Q1 — zero genuine wrongs, one model.** S1's zero was with haiku
answering sonnet's readings. With the same model in both roles the
prior is shared once more; the S1 re-analysis says the engine's rules
carry the load (0.94% before agreement), sealed volume says whether
"zero" is a rate.

**Q2 — the reach cost of honesty.** The prototype abstained on 20% of
executable readings, mostly on irrelevant word-quantities ("four
years later"). The frozen gate may cost more.

**Q3 — does structure recur?** Surface never did. The candidate key
is the CUE SIGNATURE (roles18 cue per stated number, in order, plus
ask type). Whether two questions with the same key get the same plan
— CUE-PURITY — is measurable on S1's readings before any bridge call.

**Q4 — transfer wrong-fire.** Positional binding of a same-key
question into a donor's plan is the B32 family; measured, never
served.

**Q5 — gold errata.** Three of eight S1 wrongs were the corpus's; the
by-gold metric counts them, the genuine count is the crux, nothing is
relabelled.

---

## 4. Architecture (one model)

```
ESCALATION: question Q; model M answers directly -> a (the user's answer)
  |
  +-- asynchronously, the SAME model M proposes READING(Q):
  |     a planschema17 plan over slots {n0..nk} (Q's stated numbers
  |     in order) + structural constants; no values, no arithmetic.
  |     ISOLATION: M receives only {id, question, numbers}; may not
  |     run code; reader19 validates the file; a reading that is not
  |     exactly {"plan": ...} is a format failure.
  |
  +-- ENGINE: reader19.bind -> plangate18 (reading mode: G-P1..G-P5,
  |     G-P4' usage matching) -> G-P6 lexical honesty (new) ->
  |     structural abstentions (new) -> chainexec17 (per-step +
  |     end witness) -> certified value v, or ABSTAIN with reason.
  |
  +-- PROBATION VALUE: a. ADMIT iff |v - a| <= max(1e-4|a|, 1e-6).
  |     (In production a is free: it is what the user got.)
  |
  +-- LIBRARY: admitted READING keyed by (cue signature, ask type,
  |     number count). Serving on a later question with the same key
  |     = bind positionally + full gate + G-P6 + rules + witness;
  |     MEASURED in V1.9, never served.
  |
  +-- GRADING (offline only): every stage vs corpus gold.
```

Admission rules, all graded on the same items; **A2 is the version's
rule**:

- **A0** agreement only (S1's rule, for continuity)
- **A1** G-P6 + structural abstentions, no agreement (engine alone)
- **A2** A1 + agreement with the escalation's answer

### 4.1 The reading reflex class

`{"plan": …, "key": cue signature, "donor": id, "model": M,
"admission": "A2", "kind": "reading"}`. No pattern, no value, no
role requirement from roles18 (bare tokens expected).

### 4.2 G-P6 — lexical honesty

Stated quantities are digits AND words. Frozen word table: number
words one…twenty, thirty…ninety, hundred, thousand; "dozen" 12;
"half" 0.5, "quarter" 0.25, "third" 1/3; "twice"/"double(d)" 2,
"thrice"/"triple(d)" 3; "<number-word> times" as its number.
PLURAL-AGENT: two capitalised names joined by "and" with a later
"they / both / together / altogether" is a stated 2. Rule: every
word-quantity token must match a DISTINCT literal occurrence in the
plan (magnitude; a slot whose digits equal the word's value counts),
by the bipartite matching G-P4′ already uses — one token, one
literal; an unmatched token kills the reading. "one", "a", ordinals
and "first/second/last" are not quantities. Digit tokens keep G-P4 /
G-P4′ unchanged.

### 4.3 Structural abstentions

- **S-INT** — count ask ("how many …") and v not an integer → ABSTAIN
- **S-RATIO** — "ratio" in the ask → ABSTAIN
- **S-PCT** — "N% (higher|lower|more|less) than" or "N times more
  than" → ABSTAIN (base convention ambiguous)
- **S-GEOM** — "around" with a circle/diameter/radius stated → ABSTAIN

Each rule: one abstaining control, one passing near-twin, and its
false-abstain rate on DEV, reported.

### 4.4 Cue signature and CUE-PURITY

Key(Q) = (roles18 cue per stated number in order, ask type from a
frozen regex table, number count) — a fixed function of the text.
CUE-PURITY on DEV = share of keys whose executed readings all share
one `planschema17.signature`. Reuse is measured on PURE keys only; a
reading whose signature differs from every other reading of its key
is flagged singular (possibly value-dependent) and never reused.

### 4.5 Positive controls before any counting run (B24)

S1's batteries; G-P6 battery (S1's "thrice / five times" reading must
die; S1's "Chase and Rider" reading must die under cardinality; a
reading consuming every word must pass; an irrelevant "four years
later" must die — the cost is deliberate and visible); one control
pair per structural rule; cue-signature battery (paraphrase pair →
same key, one cue changed → different key); isolation battery
(batch schema carries no gold or answer; agent prompt byte-identical;
any file not exactly `{"plan": …}` rejected).

---

## 5. Datasets (frozen, hashed before any bridge call)

```
DEV      S1's 1,800 items (readings by sonnet exist; golds exist).
         New for V1.9: DEV answers by the SAME model as the proposer
         (sonnet), one bridge pass. Gates, rules, controls and
         purity are developed here.
SEALED   the corpus items S1 never sampled — GSM8K test 419 + ASDiv
         1,405 = 1,824 (or a hashed 1,200 subsample, §12) — hashed;
         tokenizer fixes (glued units "15kg", leading-dot decimals
         "$.20"; S1 note N6) applied before the batches are written.
         Per arm: readings and answers by ONE model, collected once,
         scored once.
REUSE    SEALED keyed against DEV+SEALED readings admitted under A2;
         a reading never serves its own donor.
```

Golds live in `results/v19/data/` only; batch files carry
`{id, question, numbers}`.

---

## 6. Arms (one model per arm, both roles)

| arm | model (answers AND proposes) | n |
|---|---|---|
| **M-sonnet (primary)** | sonnet | DEV 1,800 answers; SEALED readings + answers |
| M-opus | opus | SEALED readings + answers |
| M-haiku | haiku | SEALED readings + answers — the scale question (does the small model read safely under this engine?) |
| M-fable | fable | SEALED readings + answers |

All four arms run (user decision, 2026-09-08); no local model is
used for anything.

No cross-model pairing anywhere. S1's sonnet/haiku rows remain as the
pre-study record and are not re-scored as a V1.9 arm.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| H1 | M-sonnet under A2 admits ZERO genuine wrong readings on SEALED | the crux; S1 re-analysis says yes; the shared prior says maybe |
| H2 | A2's by-gold FALSE-ADMIT ≤ 0.5% | uncertain — S1's errata alone were 0.43% |
| H3 | engine-only A1 is not enough: A1 GENUINE-WRONG > 0 on SEALED | predicted (S1: 6 of 638 by gold) |
| H4 | honesty costs reach: A2 admits 60–80% of executed readings | predicted from the prototype (570/796 = 72%) |
| H5 | each structural rule < 3% false abstention on DEV | plausible |
| H6 | CUE-PURITY on DEV < 70% — structure is not determined by cues on word problems | predicted (65–82% bare tokens) |
| H7 | reuse on pure keys serves > 0 sealed items and its wrong-fire is NOT zero | predicted — B32 on natural text |
| H8 | REACH ≥ 50% before honesty, after tokenizer fixes | predicted (S1 66%) |
| H9 | scale is monotone: if M-haiku runs, its genuine-wrong count ≥ sonnet's and its reach ≤ | predicted from V1.6–V1.8 |

---

## 8. Metrics (FROZEN)

Primary, per arm and admission rule: admitted; FALSE-ADMIT by gold
with post-hoc classification (gold errata / convention / integer /
genuine) and every wrong's row published; GENUINE-WRONG; READING-
CORRECT among admitted; admitted ÷ executed. G-P6 and per-rule
kill counts and false-abstain rates on DEV. CUE-PURITY; pure-key
count; REUSE-SERVED / REUSE-WRONG on SEALED. Secondary: REACH,
READING-CORRECT, answer accuracy of M, disagree-but-correct, near-
miss ledger, gate-kill anatomy, format and isolation violations.

---

## 9. Thresholds (FROZEN)

```
GATE-CTRL     every §4.5 battery passes before counting.
SAFETY-GEN    GENUINE-WRONG admissions under A2 (M-sonnet, SEALED)
              = 0. Every by-gold wrong published with its class; one
              genuine = E.
SAFETY-FA     FALSE-ADMIT by gold under A2 <= 0.5%.
REACH         >= 50% of SEALED executable before G-P6.
GATE-COST     G-P6 + rules abstain <= 30% of executed readings.
RULES         each structural rule < 3% false abstention on DEV.
PURITY        reported; reuse measured on pure keys only.
REUSE-SAFE    REUSE-WRONG = 0 on SEALED for reuse to be declared
              servable in a later version; otherwise the rate is the
              B32-family number on natural text.
SEALED-ONCE   readings, answers and scores on SEALED once per arm.
```

---

## 10. Outcome ladder (FROZEN; F > E > D > C > B > A)

```
F  a control battery cannot pass, or S1 / V1.8 stop reproducing.
E  SAFETY-GEN fails: one model, an honest engine and its own answer
   still admitted a genuine misread — report the case and its class.
D  SAFETY-GEN holds but REACH < 30% or GATE-COST > 30%: safe and
   inert; honesty ate the reach.
C  SAFETY-GEN, REACH, GATE-COST hold but SAFETY-FA fails on gold
   errata alone: safe in truth, wrong by the corpus; both numbers.
B  all safety and reach bars hold; reuse measured; REUSE-WRONG > 0
   or REUSE-SERVED = 0: readings are safe one-phrasing reflexes.
A  B plus REUSE-SERVED > 0 at REUSE-WRONG = 0 on pure keys —
   structure-keyed reuse on natural text without a wrong answer.
```

---

## 11. Risk register (FROZEN with §7–§10)

```
R1  Shared prior, twice: the same model reads and answers. A misread
    that consumes every quantity and hits no structural class agrees
    with itself. Detect: SAFETY-GEN; A1 vs A2. Mitigate: none in V1.9
    — it is the thing measured; rung E exists for it.
R2  G-P6 over-abstains on irrelevant word-quantities. Detect: false-
    abstain on DEV. Mitigate: none; the cost is the honesty rule's
    (GATE-COST, rung D).
R3  Word-table gaps ("a couple", "half a dozen", "a score"). Detect:
    residual by-gold wrongs' anatomy. Mitigate: table frozen; gaps
    become the next list.
R4  Gold errata dominate by-gold wrongs. Detect: classification
    published. Mitigate: SAFETY-GEN is the crux; nothing relabelled.
R5  Proposer computes / value-dependent readings (S1 N7). Detect:
    isolation battery; singular-key flags; agent transcripts sampled.
    Mitigate: no-code prompt, numbers pre-indexed, reader19 validation;
    singular readings never reused.
R6  Cue signatures mostly "bare" on word problems -> low purity,
    small pure subset. Detect: PURITY. Mitigate: none (H6).
R7  Positional binding on same-key questions is the B32 family.
    Detect: REUSE-WRONG. Mitigate: nothing served.
R8  Tokenizer gaps. Mitigate: fixed before batches; frozen by hash.
R9  DEV fully exposed (S1 sealed items included). Mitigate: SEALED =
    never-sampled corpus items only; no model sees them before the
    run.
R10 Agreement tolerance masks rounding. Detect: near-miss ledger.
R11 Answer parsing ("$18" vs "18"; "18 dollars"). Detect: parse
    failures counted; unparsable = no agreement.
R12 Bridge-agent variance (format failures, partial writes). Detect:
    format-failure count; one re-ask allowed, both attempts recorded.
```

---

## 12. Decisions — RESOLVED by the user (2026-09-08, all as proposed; arms = sonnet, opus, haiku, fable; no ollama)

1. **SEALED size**: all 1,824 never-sampled items (proposed), or a
   hashed 1,200 subsample.
2. **G-P6 word table** as §4.2 — add or strike entries.
3. **Structural rules** S-INT / S-RATIO / S-PCT / S-GEOM as §4.3.
4. **Reuse measured, never served** in V1.9 (proposed).
5. **Additional arms** M-opus and M-haiku if bridge time allows
   (proposed), or M-sonnet only.
6. **DEV answers by sonnet** (one new bridge pass over 1,800 items)
   so DEV is one-model too (proposed); or reuse S1's haiku answers on
   DEV and accept a cross-model DEV.
7. **Ladder** as §10, in particular rung C for "safe in truth, wrong
   by errata".

---

## 13. What this version claims, and does not

It claims a one-model escalation-feedback loop whose safety is the
engine's honesty about every stated quantity, digit or word, plus
four structural abstentions, with the escalation's own answer as the
probation value — measured against real golds for genuine wrong
admissions at sealed volume — and the first measurement of
structure-keyed reuse on natural text. It adds no second model,
serves no reused reading, and relabels no gold it disagrees with.
