# V1.4 — The Relational State Substrate

**Reflex Engine, experiment V1.4 · INTERIM · 2026-09-01**

**The outcome ladder cannot be adjudicated yet, and this report does not
claim a rung.** Rung A requires H3 *and* (H4 or H5) *and* H9. H3 and H5
are measured and confirmed on the deterministic layers. **H9 — the
end-to-end energy advantage — is not measured at all**, and the model
arms that would produce relational states from real language have not
been run. Claiming A on a partial ladder is exactly the move the
pre-registration exists to prevent.

What follows is what was actually measured.

---

## 1. The result

Sealed adversarial suite, 600 cases, 10 semantic error classes, no model
in the loop. Every case carries a **correct** state and a **corrupt**
state over the same text, so each arm is scored twice.

| arm | detection | false positive |
|---|---|---|
| **C0** — V1.3's flat plan IR | **10.0%** | 0.0% |
| **C2** — substrate + semantic integrity | **100.0%** | 0.0% |

C0 catches exactly one class: `contradictory_relations`. It misses
incorrect grouping, entity mismatch, cross-entity contamination, wrong
scope, temporal inversion, duplicate entities, missing state
transitions and unresolved references — **because the flat IR discards
the material those errors are about.** Projecting a relational state
down to `quantities / plan / target / dismissed` throws away identity,
order, scope and context, and nothing downstream can ask about what is
no longer there.

Two deliberate generosities to C0, so its 10% is an upper bound rather
than a convenient number: `agreement` was handed the same IR twice and
always passes (with no model there is no second parse), and the
projection preserves the plan DAG, so groupings the flat IR *can*
express are expressed. Where C0 misses those, it misses because nothing
**checks** the grouping — not because the notation was too weak.

---

## 2. What this measures, and what it does not

**Measured:** whether the representation can *hold* the distinction, and
whether deterministic rules over it can *find* the error.

**Not measured:** whether a model can *produce* a faithful relational
state from real language. Both states in every case were constructed.

That boundary is the honest limit of this run and it is not a small
one. V1.3's coverage came from a model reading English; V1.4 has
replaced the representation that reading lands in, and has not yet
tested the reading. The bridge arms (llama-8B, haiku, sonnet, opus) are
built into the plan and unrun.

---

## 3. V1.3's specific failures, revisited

| V1.3 event | status in V1.4 |
|---|---|
| **W-1** "three times more" — identical wrong value from opus *and* sonnet, corroborator agreed each time | **Caught deterministically.** The phrase is in the frozen ambiguity set; it abstains with no model call. Cross-model corroboration could not have caught it — both families read it the same way — because ambiguity is a property of the phrase. |
| **W-4** non-integer under an integral target (3.222 trees, 15.5 days) | **Half caught.** Check 8 fires on `248/16 → 15.5 days`. It misses `29/9 → 3.222 trees` because *trees* did not reach the lexicon's frequency threshold. **The threshold was not lowered to fix this** — see §6. |
| **W-5** plan reuse, 7 served / 7 wrong | **Refused.** Reuse now gates on a semantic signature (resolved operators + the identities they act on), not surface text. The Mrs Hilt / cupcakes pair is refused. |
| **W-6** vacuous dismissal, plan stopped early | **Caught by `wrong_target`**, not by the detector written for it — see §5. |
| the `90 − (49 − 19)` grouping hazard | **Unrepresentable.** The second event's argument names the derived node, so there is no edge by which 19 could modify 49. Where V1.3 needed a check to catch it, the substrate makes it inexpressible. |

---

## 4. Reuse and semantic equivalence

Confusion matrix, both directions, because passing one by collapsing
the other is the obvious degenerate solution:

```
structurally similar / semantically DIFFERENT   refused   3 / 3
lexically different / semantically EQUIVALENT   accepted  3 / 3
                                                overall   6 / 6
```

`sold` ≡ `gave away` ≡ `lost` ≡ `used` (all deplete) are accepted as
equivalent. `gave away` vs `received` are refused as different despite
0.615 text similarity — near V1.3's 0.62 reuse threshold, which is the
point.

---

## 5. The false-positive column earned its place

**The first sealed run scored C2 at 100% detection and 90% false
positives.** A detector firing on nine correct states out of ten is
worthless, and only the paired design exposed it. This is V1.3's B10
repeating — non-degeneracy rejecting correct plans whose answer
coincided with an input — and it was caught this time by construction
rather than by luck.

Diagnosis found two different faults, which matters because they have
different remedies: four detectors were over-broad, and two of my own
"correct" states were not well-formed (an event with no resulting
node). Both were fixed **on a separate dev suite** (seed 9999); the
sealed suite was regenerated and run **once**. Superseded hash
`355803f5…`, current `b8921bfa…`.

### One detector retired as a negative result

`plan_query_semantic_mismatch` by unconsumed-givens **cannot work**, and
the reason is not fixable by tuning. A distractor is legitimately
unconsumed:

> *"Dev collected 11 shells and Elle collected 15. How many did Dev
> collect?"* — Elle's 15 **must** take no part in the answer.

No deterministic rule separates that from V1.3's W-6, where a *needed*
quantity was dropped. Telling them apart requires knowing which
quantities the question depends on, which is the semantic judgement the
version is trying to avoid asserting. The rule is disabled and kept in
the code as documentation; the W-6 shape is caught by `wrong_target`
instead, which compares the terminal's identity to the ask and needs no
notion of relevance.

---

## 6. Discipline notes

**A threshold that was not tuned.** Check 8 misses `29 trees` because
*trees* fell below `MIN_FREQ = 3` in the lexicon harvest. Lowering it
to 2 would very likely fix that case. `"29 trees"` is a **V1.3 sealed
item**, and tuning a method parameter against a known sealed answer is
tuning on the evaluation however innocuous the mechanism looks. The
threshold stands and check 8's hit rate is reported at whatever the
lexicon's coverage turns out to be.

**Tier A untouched.** The everyday-noun lexicon lives in a separate
V1.4-only pack and is never merged into `packs/physics`. Re-verified
after every change: battery, 65-seed sweep, vocabulary audit,
invariants — all pass. C0 reproduces V1.3 byte-for-byte (haiku 38/37/1,
sonnet 209/206/3, opus 199/198/1, retrieval 289/0). Rung F does not
fire.

---

## 7. Bugs (4, all pre-measurement)

- **B17** — one-letter unit aliases matched English words; `"16 vases a
  day"` derived *amperes*. Unit symbols now require numeric context.
- **B19** — `m` is claimed by both metres and molar, and `"60 m of
  rope"` returned *concentration* because a sorted list picked a
  winner. **This is V1.3's B8 in a new layer** — an ordering standing
  in for a conflict check. Colliding surfaces now abstain and name both
  claimants.
- **B18** — the physics lexicon has no everyday nouns, so derivation
  was UNKNOWN on nearly all real language and check 8 never fired: V1.3's
  D5 reproduced in a new place. Fixed with a separate lexicon harvested
  from **non-sealed** traffic.
- **B20** — a shell-mangled escape compiled a detector to match a
  backspace character. Valid regex, no error, clean result on every
  state, detection silently 0%.

### The recurrence worth naming

B20 is the fourth instance in two versions of one failure mode:

```
V1.3 B16   consumption went silent on all-word problems
V1.3 B8    supersession starved the conflict check of its input
V1.4 B19   a colliding surface resolved by sort order
V1.4 B20   a mangled escape produced an inert regex
```

**A green check that cannot go red.** Each was present in the code, ran
without error, and was structurally incapable of firing. B20 was caught
only because a class that should have detected 100% reported 0% and was
worth chasing — a plausible-looking 60% would have shipped.

Standing requirement adopted: **every detector needs a positive control
— a case it MUST fire on — running alongside the case it must not.**

---

## 8. What remains

Built and passing: W0 baseline lock · W1 substrate · W2 relation
resolution + frozen 14-entry ambiguity gate · W3 engine-derived kinds +
check 8 · W4 applicability overlay (4 of 58 capabilities conditioned) ·
W5 integrity (15 classes) · W7/W8 reuse and equivalence.

Not yet run, and each is required before the ladder can be adjudicated:

1. **Bridge arms** — llama-8B, haiku, sonnet, opus producing relational
   states from real language. This is the question §2 leaves open and
   the largest remaining cost (~2,400 items × 4 arms).
2. **H9, energy** — end-to-end on the local metered arm. V1.3's local
   arm ran 21 items in 4,409 s (210 s/item), which sizes an n=400 run at
   roughly 23 hours.
3. **C1/C3/C4/C5** — the full ablation; only C0 and C2 are measured.
4. **W6** — Path Manager rewiring over the substrate.
5. **W9** — long-horizon tractability (H10).
6. **S3** — the fresh human-language set.

---

## 9. The one-paragraph version

On a sealed 600-case suite the substrate catches every seeded semantic
error that V1.3's representation could not see — 100% against 10%, both
at zero false positives — and refuses the exact plan-reuse pair that
served V1.3 a wrong answer, while still accepting genuinely equivalent
rephrasings. That is a real result about the representation and a
bounded one: both states in every case were constructed, so it shows
the substrate can hold the distinction, not that a model can produce
it. The energy question is untouched. The ladder stays unadjudicated,
and the most useful thing found along the way was not a capability but
a pattern — four instances in two versions of a check that was present,
silent, and incapable of firing.
