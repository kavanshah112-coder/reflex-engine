# V1.6 SPEC — The Verifier

## A zero-false-positive deterministic check over LLM answers

**STATUS: DRAFT for review. Freezes as tag `v1.6-plan`.**
§7–§10 never change after the first sealed run. §12 lists the decisions
needed before freezing.

Built on V0.1–V1.5. No prior version, tag, snapshot, dataset, report or
log is modified.

---

## 1. My V1.5 recommendation was wrong, and this spec starts by saying so

V1.5 closed by recommending an "abstention pivot": the engine stops
answering and instead reports what it cannot determine, on the argument
that a system knowing its own limits is worth deploying in front of one
that always answers.

The strongest form of that claim is **triage** — if the deterministic
verdict predicts when the LLM will be wrong, you route the risky
queries to a bigger model and save money without the engine answering
anything.

**It is false.** Tested on 601 direct-LLM answers already on disk from
V1.3, across sonnet, haiku and opus, on 300 sealed items:

```
packet verdict     LLM error rate      n
COMPLETE                 11.1%         81
everything else          12.5%        520
                    LIFT 1.12x
```

Eleven-point-one against twelve-point-five is noise. **The verdict
carries no usable signal about whether a model will fail.** The pivot
as I framed it is dead, and it died before this spec was written rather
than after a version was spent on it.

---

## 2. What survived the test, and is the actual thesis

The same data answers a different question. Not *"will the model fail?"*
asked **before**, but *"is this specific answer wrong?"* asked
**after**.

Three deterministic checks applied post-hoc to those 601 answers:

| check | fired | on wrong answers | on correct answers | precision |
|---|---|---|---|---|
| `non_integer_count` | 5 | **5** | **0** | **100%** |
| `negative` | 3 | **3** | **0** | **100%** |
| `magnitude_implausible` | 16 | 4 | 12 | 25% |

The first two caught **8 of 74 LLM errors (10.8%) with zero false flags
across 527 correct answers.** The third is noise and is excluded by the
admission rule in §4.

**The thesis:** a deterministic verifier can catch a measurable
fraction of LLM errors at zero cost to correct answers. It does not
answer, does not predict, and does not need to understand the query —
it needs only to notice that a specific answer cannot be right.

This is also the one thing this arc has always been good at. Tier A has
0.000 wrong-fire over 10,160 trap items across 65 seeds. Every version
since V1.3 has failed trying to make that machinery *produce* answers.
None has failed at *checking* them.

---

## 3. Why this is commercially different from every prior version

The economics invert. Previous versions had to answer a query to save
anything, so their ceiling was coverage — and coverage was 0.63%
(V1.5), 0% (V1.4), 69.7% at 1.44% wrong (V1.3).

A verifier's economics are:

```
cost    = flag_rate x retry_cost      (only flagged answers are re-run)
benefit = errors_caught
```

At the measured rates — 8 flags on 601 answers, all of them on wrong
ones — the cost is **1.3% extra model calls** to catch **10.8% of
errors**. There is no coverage requirement at all. The verifier is
useful at *any* recall above zero, provided the false-flag rate stays
at zero, because a flag that never costs a correct answer is free.

**The asymmetry is the whole product.** A false flag wastes one retry.
A missed error reaches the user. The design target is therefore not
recall-optimal; it is recall-maximal *subject to zero false flags*.

---

## 4. The admission rule (the core discipline)

> **A check is admitted only if it fires zero times on correct answers
> in the dev set, and it is re-measured on sealed data. Any check with a
> non-zero false-flag rate is reported and excluded.**

`magnitude_implausible` is the worked example: 25% precision, 12 false
flags, excluded. It would have added 4 caught errors and cost 12 correct
answers, and under §3's asymmetry that is a bad trade at any recall.

Every check additionally needs a **positive control** — a case it MUST
fire on — running beside the case it must not. Six instances across
V1.3–V1.4 of a check that could not go red (B8, B16, B19, B20, B22,
B24), and one instrument that read zero and reported it as a result.

---

## 5. Check inventory

Existing, already built and measured:

- `non_integer_count` — a non-integer answer under an integral target
  kind. V1.3 check 8. **100% precision on 601 answers.**
- `negative` — a negative count. **100% precision.**

Proposed for V1.6, each to be measured against the §4 rule:

- `not_in_text` — an answer that is neither a stated quantity nor
  derivable from stated quantities by one operation (the round-trip
  idea applied to an answer rather than a plan).
- `unit_mismatch` — the answer's implied unit conflicts with the target
  span's unit (V1.5 has both).
- `conflict_present` — the packet found a genuine same-key contradiction
  (V1.5 B26 rule). Suggestive at 25% LLM error on n=8; underpowered and
  must be re-measured.
- `superlative_arithmetic` — an optimisation/GCD question answered with
  a value that is not a divisor/multiple of the inputs.
- `exceeds_total` — a "remainder" answer larger than the largest stated
  quantity.
- `impossible_precision` — a whole-number domain answered to decimals.

Each is deterministic, needs no model, and costs microseconds.

---

## 6. Architecture

```
QUERY ──> LLM ──> ANSWER
  │                 │
  └──> PACKET ──────┤     nlpw10 + V1.5 packet, 6 ms, no model
       (V1.5)       │
                    v
              VERIFIER (V1.6)
                    │
         ┌──────────┴──────────┐
         │                     │
      CLEAN                  FLAGGED
         │                     │
      deliver            retry / escalate
                         / surface to user
```

The verifier never rewrites an answer and never supplies one. It emits
a flag with the check that fired and the span that justifies it, so a
flag is auditable rather than a score.

Reuses without modification: `nlpw10`, `reflex/packet.py`,
`reflex/kindderive.py`, `reflex/relations.py`, `v5/energy.py`. New code
is one module, `reflex/verify16.py`, plus its check battery.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| V1 | a deterministic check suite catches ≥10% of LLM errors at a zero false-flag rate | **pass** — 10.8% already measured on dev |
| V2 | the suite generalises: sealed false-flag rate stays at zero | **uncertain** — V1.5's guards held on dev and broke on sealed |
| V3 | recall rises with suite size without breaking V2 | uncertain |
| V4 | flagged answers are materially more likely to be wrong than base rate | pass |
| V5 | a retry on flagged answers converts caught errors into correct answers | uncertain |
| V6 | the verifier's cost is negligible against one model call | **pass** — 6 ms vs 64.9 J |
| V7 | recall holds across model scale (llama, haiku, sonnet, opus) | uncertain — stronger models may fail differently |
| V8 | the packet VERDICT does not predict LLM failure | **already FALSIFIED as a predictor — recorded, not re-tested** |

---

## 8. Metrics (FROZEN)

**Primary: recall of LLM errors at a zero false-flag rate.**

Secondary: precision · per-check firing rate and precision · flag rate
(the retry bill) · verifier latency and energy · recall by model · recall
by error class · net accuracy after retry.

Reported per check, never only in aggregate. A suite number hides which
check is carrying it and which is dead weight.

---

## 9. Thresholds (FROZEN)

```
SAFETY     false-flag rate on sealed correct answers = 0.
           A single false flag on a correct answer voids the check that
           produced it. The suite is reported without it and re-run.
RECALL     >= 10% of LLM errors caught on sealed data.
COST       flag rate <= 5% of answers (the retry bill).
POWER      no zero-false-flag claim without the Wilson upper bound
           reported alongside; at n correct answers the upper bound on
           a zero count is ~3/n, and that bound is the claim.
```

---

## 10. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  Tier A regressed, or V1.3/V1.4/V1.5 stop reproducing.
E  the suite false-flags on sealed correct answers and no
   zero-false-flag subset reaches 10% recall.
D  zero false flags but recall below 10%: real and too small to matter.
C  works on weak models only; recall collapses on sonnet/opus.
B  recall >= 10% at zero false flags on one model, not across scale.
A  recall >= 10% at zero false flags across all four model scales,
   flag rate <= 5%.
```

---

## 11. Datasets

```
D-dev     the 601 V1.3 direct-LLM answers (300 sealed V1.3 items,
          3 models). ALREADY ANALYSED for this purpose and therefore
          CONTAMINATED -- dev only, never an evaluation result.
D-sealed  fresh LLM answers on S3-sealed (800 items, V1.5 hash
          3c1eed86...), collected per model through the bridge.
          NOT YET COLLECTED and not inspected.
S8        adversarial answers: correct answers engineered to look
          suspect, to measure false flags where they are most likely.
```

**Corpus honesty:** the real-language pool is exhausted. 3,625 items
total; V1.3–V1.5 consumed all but a handful. D-sealed reuses S3-sealed
ITEMS but with **fresh model answers**, which is legitimate because the
unit of evaluation is an answer, not an item — but the items' golds
have been seen by this project, and that is recorded rather than
glossed.

---

## 12. Open decisions — needed before freezing

1. **Is zero false flags the right bar**, or should it be "≤0.5% with
   the cost stated"? Zero is clean and may be unreachable at useful
   recall.
2. **Which models for D-sealed.** Full four-model matrix is ~3,200
   bridge answers. Propose: haiku + sonnet at 800 each, opus at 400,
   llama metered locally at 800.
3. **Retry policy for V5** — same model, or escalate to a larger one?
   The second is the commercially interesting version and costs more to
   test.
4. **Check budget** — admit all six proposed checks, or the three most
   principled and measure the rest as candidates?

---

## 13. What this version is honestly worth

It is a smaller claim than any version since V1.0. It does not answer
questions, does not save energy by avoiding model calls, and does not
make the model better. It catches some errors for free.

That is worth doing precisely because it is the first claim in six
versions that the measured evidence *supports before the work starts*
rather than after it fails. V1.3 through V1.5 each began with a thesis
that measurement dismantled. This one begins with a measurement that
survived a falsification attempt aimed directly at it.

The version's job is to find out whether it survives sealed data too —
and V1.5's guards, which held at 0% on dev and broke to 40% on sealed,
are the reason that is a real question rather than a formality.
