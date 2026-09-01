# V1.4 — The Relational State Substrate

**Reflex Engine, experiment V1.4 · OUTCOME D · 2026-09-01**

The substrate does what it was built to do. A model cannot feed it.

On a sealed 600-case adversarial suite the substrate catches every
seeded semantic error V1.3's representation could not see — 100%
against 10%, both at zero false positives. On 240 sealed real-language
items, driven by a model, it certifies **nothing at all**.

---

## 1. Verdict against the frozen ladder

| | condition | result |
|---|---|---|
| **F** | Tier A regressed, or C0 stops reproducing V1.3 | **not triggered** — verified |
| **D** | any sealed suite above its wrong-fire gate | **TRIGGERED** — C1/C2/C3 at 100% wrong-fire before B22 |
| **C** | substrate worse than C0 on semantic wrong-fire | not reached |
| **B** | H3 null at materially higher cost | not reached |
| **A** | H3 + (H4 or H5) + H9 | **unreachable** — H9 unmeasured, H3 unassessable at zero served |

**OUTCOME D.** Three sealed ablation arms served 17 answers on real
language and every one was wrong (§4). The defect was found and fixed
(B22); post-fix every arm serves zero and wrongs zero.

**The ladder has a gap, and saying so is part of the result.** After
the fix no rung fits: D no longer fires (nothing is served, so nothing
is wrong), C's literal condition fails (0% wrong-fire is not worse than
C0's 1.44%), B describes a tie that did not happen, and A needs
measurements that do not exist. The pre-registration never anticipated
a system that is **safe and inert**. D is reported because it fired on
a genuine sealed measurement during the run and because nothing above
it is reachable — not because the corrected system is unsafe.

---

## 2. The result that holds

Sealed adversarial suite, 600 cases, 10 semantic error classes, correct
and corrupt state for every case, no model in the loop.

| arm | detection | false positive |
|---|---|---|
| **C0** — V1.3's flat plan IR | **10.0%** | 0.0% |
| **C2** — substrate + integrity | **100.0%** | 0.0% |

C0 catches one class. It misses incorrect grouping, entity mismatch,
cross-entity contamination, wrong scope, temporal inversion, duplicate
entities, missing state transitions and unresolved references —
**because the flat IR discards the material those errors are about.**

Two deliberate generosities keep C0's 10% an upper bound rather than a
convenient number: `agreement` was handed the same IR twice and always
passes, and the projection preserves the plan DAG so groupings the flat
IR *can* express are expressed.

Your `90 − (49 − 19)` case is **unrepresentable** in the substrate: the
second event's argument names the derived node, so no edge lets 19
reach 49.

**Reuse and equivalence, 6/6.** All three structurally-similar /
semantically-different pairs refused — including V1.3's Mrs Hilt /
cupcakes failure — and all three lexically-different /
semantically-equivalent pairs accepted. `gave away` vs `received` is
refused at 0.615 text similarity, just under V1.3's 0.62 reuse
threshold.

---

## 3. The result that does not

240 sealed real-language items (S3, disjointness from all V1.3 usage
proved by id intersection), produced by haiku through the isolated
bridge.

| arm | served | correct | wrong | coverage |
|---|---|---|---|---|
| C1 substrate only | 0 | 0 | 0 | 0.0% |
| C2 + integrity | 0 | 0 | 0 | 0.0% |
| C3 + applicability | 0 | 0 | 0 | 0.0% |
| **C5 complete** | **0** | **0** | **0** | **0.0%** |

Where C5's coverage went:

```
agreement                             164   68.3%
integrity: wrong_target                42   17.5%
not_evaluable                          13    5.4%
integrity: missing_state_transition    10    4.2%
unknown_relation                        8    3.3%
integrity: entity_mismatch              1    0.4%
```

Against V1.3's flat IR on real language — 209 certified at 1.44% wrong
— this is a total collapse of coverage in exchange for the elimination
of wrong answers. **The bottleneck moved rather than lifted:** from
*checking* the reading to *producing* it.

---

## 4. Seventeen wrong answers, and whose fault they were

Before the fix, the arms served 17 answers and every one was wrong. Not
17 mistakes — one mistake, 17 times:

```
"I see 349 frogs. How many legs do they have?"    served 349
"18 cubes long ... it doubles her length"         served 18
"Mrs. Hilt read 2 books per day ... in one week"  served 2
```

Each is a state with no resolved relation, whose only terminal is a
stated given, executed and returned unchanged. The answer was the
question's own input.

**V1.3 caught this class.** `check_nondegenerate` has guarded it since
V1.3's own B4. I replaced the representation and did not re-derive what
the old one was protecting against.

> **A new representation inherits none of the old one's scar tissue.**
> Every guard the previous design accumulated has to be re-argued in
> the new terms, and the ones that get missed are exactly the ones
> nobody remembers needing.

Fixed (B22); pre-fix arms preserved under
`results/v14/arms/superseded_pre_B22/`.

---

## 5. A correction to my own analysis

Agreement dominates C5's abstentions at 68.3%, so the first question
was V1.3's D7 question: is the check rejecting equivalent readings over
naming?

A decomposition said yes for 5 of 27 resolved items — operators matched
while identity labels differed (`pigeons`/`pigeon`,
`seeds_per_watermelon`/`quantity`). Labels are free text a producer
chooses, so excluding them looked clearly right.

**Excluding them recovered nothing.** Failures went 19 → 20.

The decomposition was wrong. It compared *flattened* identity lists, so
a sample that split a story into more relations appeared as a naming
difference:

```
A = [seeds_per_watermelon, watermelons]   2 relations
B = [quantity, quantity, seeds, seeds]    4 relations
```

That is structural disagreement wearing the costume of a vocabulary
disagreement. **Two samples of one model produce structurally different
relational states for the same problem in roughly three quarters of
resolved cases.**

The wrong reading was the comfortable one — it would have turned a hard
finding about producer instability into a tidy comparison bug. Only the
fix failing caught it.

---

## 6. Hypotheses

| | claim | result |
|---|---|---|
| H1 | substrate improves semantic composition over the fixed representation | **CONFIRMED on the representation, FALSIFIED end-to-end** |
| H2 | reduces wrong entity binding | **CONFIRMED** — 100% detection, 0% FP |
| H3 | reduces structurally-valid-but-semantically-wrong computation | **CONFIRMED deterministically; UNASSESSABLE on the model path** (zero served) |
| H4 | applicability conditions reduce semantic wrong-fire | **NOT EXERCISED** — 4 of 58 capabilities conditioned; C3 = C1 on every item |
| H5 | integrity improves safety without unacceptable coverage loss | **HALF CONFIRMED** — safety yes; the coverage loss is total, so "unacceptable" is answered against it |
| H6 | safe plan reuse becomes possible | **CONFIRMED on the confusion matrix**, 6/6 |
| H7 | improves Path Manager orchestration | **NOT RUN** (W6 deferred) |
| H8 | improves real-language coverage | **FALSIFIED** — 69.7% (V1.3) → 0.0% |
| H9 | preserves the end-to-end energy advantage | **NOT MEASURED** — local metered arm still running at report time |
| H10 | stays tractable as complexity grows | **NOT RUN** (W9 deferred) |

---

## 7. Bugs (7)

- **B17** one-letter unit aliases matched English words — `"16 vases a day"` derived *amperes*.
- **B18** the physics lexicon has no everyday nouns, so derivation was UNKNOWN on nearly all real language and check 8 never fired — V1.3's D5 in a new place. Fixed with a separate lexicon harvested from **non-sealed** traffic.
- **B19** `m` is claimed by metres *and* molar; `"60 m of rope"` returned *concentration* because sort order picked a winner. **V1.3's B8 in a new layer.**
- **B20** a shell-mangled escape compiled a detector to match a backspace character — valid regex, no error, silently 0% detection.
- **B21** the inherited V1.3 stub filter discarded every valid V1.4 payload (it demanded `quantities`/`plan`, V1.4 sends `nodes`/`relations`).
- **B22** the substrate executor shipped without non-degeneracy — §4.
- **B23** a payload with the right keys and no content is still a stub. One agent wrote 59 of 60 as `{"nodes": [], "relations": []}` and called it "the foundational output file"; B21 had just widened the key check, so it passed. 121 purged. **Each fix to a stub filter teaches the next stub what to look like.**

### The recurrence, now at five

```
V1.3 B16   consumption went silent on all-word problems
V1.3 B8    supersession starved the conflict check of its input
V1.4 B19   a colliding surface resolved by sort order
V1.4 B20   a mangled escape produced an inert regex
V1.4 B22   a guard that simply was not carried across a rewrite
```

**A green check that cannot go red.** Standing requirement adopted:
every detector needs a positive control — a case it MUST fire on —
running alongside the case it must not.

---

## 8. What this version establishes

1. **The representation was never the hard part.** Moving from a flat
   plan IR to a relational substrate takes semantic-error detection
   from 10% to 100% at no false-positive cost. That is real and it is
   cheap.
2. **Producing the representation is the hard part.** Three quarters of
   dual samples disagree structurally; a fifth of surviving states
   answer a different question than the one asked. Neither is a
   checking problem.
3. **The gates work exactly as designed, and that is the problem.**
   Every abstention in §3 is defensible in isolation. Together they
   refuse everything.
4. **V1.3's flat IR is still the only configuration that has ever
   answered real language at scale** — 209 certified, 1.44% wrong. V1.4
   is safer and useless; V1.3 is useful and imperfect. Nothing yet is
   both.

---

## 9. What V1.4 does not claim

- **No energy figure.** The metered local arm was still running at
  report time (n=60 reflex + n=60 pure-LLM on identical items,
  ~200 s/item). H9 is unmeasured for the second version running, and it
  remains the commercial crux.
- **No cross-model comparison.** Only the haiku arm ran; sonnet, opus
  and llama-8B are unrun, so D-vi's architecture-and-reflex comparison
  is not delivered.
- **No applicability result.** 4 of 58 capabilities carry conditions
  and none fired on S3; C3 is identical to C1 on every item.
- **No Path Manager or tractability result** (W6, W9 deferred).

---

## 10. The one-paragraph version

V1.4 replaced the representation and the bottleneck moved with it. The
substrate holds every distinction the flat IR could not — 100% versus
10% semantic-error detection at zero false positives, the `90 −
(49 − 19)` hazard made unrepresentable rather than merely caught, and
V1.3's plan-reuse failure correctly refused — but on real language a
model cannot produce states the substrate will accept, and the
complete system certified nothing at all on 240 sealed items. The
outcome is D, fired by seventeen wrong answers that turned out to be a
guard I failed to carry across the rewrite; and the most useful thing
learned is that a new representation inherits none of the old one's
scar tissue.
