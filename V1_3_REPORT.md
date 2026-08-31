# V1.3 — Reading Real Language Safely

**Reflex Engine, experiment V1.3 · OUTCOME D · 2026-08-31**

The engine answers questions written in ordinary English, and it does
so at a measured wrong-answer rate rather than a promised one. Its
best arm reads 69.7% of real language with three wrong answers in 209,
and a separate retrieval track certifies 289 answers with none wrong.

**And the pre-registered verdict is D, not A**, because the weakest
arm came in at 2.63% — above the 2% gate — on a single wrong answer in
38. The ladder was frozen before any sealed evaluation and puts D
above A. Section 2 explains why that reading is honoured rather than
argued around.

---

## 1. The question this version had to answer

V1.2 closed the generator universe and then hit a wall stated plainly
in its own report: on real user language — GSM8K, ASDiv, SciQ, frozen
and sealed — the engine abstained on **519 of 520** items. Coverage
was, to a rounding error, zero. Two acquisition loops run against
that residual produced **zero lift on both arms**. The diagnosis was
that the gap was not vocabulary but *arithmetic story composition*.

V1.3 acts on that diagnosis with one structural change, plus the two
extensions the user asked for:

> *"i want it to work with normal human language and also make it
> self generating and not just arithmetic"*

- **Normal human language** → the parse/verify split (§3).
- **Not just arithmetic** → provenance certification for retrieved
  facts, which involve no computation at all (§5).
- **Self-generating** → plan reflexes, minted from the engine's own
  verified solves (§6). This is the one that failed.

---

## 2. Verdict against the frozen ladder

The outcome ladder was fixed in `V1_3_SPEC.md` before any sealed
evaluation, with priority **F > D > C > B > A**.

| | condition | result |
|---|---|---|
| **F** | PARITY-PLUS broken by W1–W4 changes | **not triggered** — Tier A re-verified live |
| **D** | any sealed suite above the 2% gate, or Tier A regressed | **TRIGGERED** — haiku arm 1/38 = **2.63%** |
| **C** | L3 fails | not reached — D outranks |
| **B** | L3 + L9, L5 null *and* L7/L8 partial | not reached — D outranks |
| **A** | L3 + L9 + (L5 **or** L7/L8) | not reached — D outranks |

**OUTCOME D.** The haiku arm produced one wrong answer in 38 certified
= **2.63%**, above the pre-registered 2% gate.

### Why this is reported as D

Every other reading of the run says A. The strongest arm is at 1.44%,
the two clean arms combined are at 1.62%, the retrieval track is at
0.00%, and Tier A is intact. If the gate were applied to the
aggregate, or to the arm anyone would deploy, the version passes.

None of that is the pre-registration. The ladder says *"any sealed
suite or sweep above the 2% gate"*, with the explicit rider that **"a
safety regression outranks every coverage claim"**, and it fixes the
priority F > D > C > B > A so that D is tested before A. The haiku arm
is a sealed measurement and it is above the gate.

Choosing, after seeing the data, to read "suite" as excluding the arm
that failed — or to substitute the combined figure for the per-arm one
— would be exactly the move this arc pre-registers to prevent. The
verdict is D.

**What D means here, stated precisely:** it is one wrong answer on the
smallest and weakest arm, at n=38, where the 95% interval runs
[0.47%, 13.50%] and no honest claim can be made in either direction.
It is not evidence that the approach is unsafe, and it is not
dismissible either. It means the version did not demonstrate the
safety margin it set out to demonstrate, on every arm it measured.

The V1.3 wrong answer that produced it (ledger W-6) is a real defect
with a named cause, not a statistical accident: a needed quantity
discarded through the dismissal escape hatch with a circular reason.

---

## 3. The headline: real language, measured

Sealed 300-item sample drawn from GSM8K and ASDiv, disjoint from the
traffic pool. Unresolved items are scored as **abstentions**, never
dropped.

| arm | certified | correct | **wrong** | corroboration abstained | coverage | wrong-fire |
|---|---|---|---|---|---|---|
| sonnet | 209 | 206 | **3** | 12 | 69.7% | 1.44% |
| haiku | 38 | 37 | **1** | 142 | 12.7% | **2.63%** ← above gate |
| **clean combined** | **247** | **243** | **4** | 154 | — | **1.62%** |
| opus *(excluded, B9)* | 199 | 198 | 1 | 1 | 66.3% | 0.50% |

Against V1.2's **0.2% coverage at zero wrong**, this is 69.7%
coverage at 1.44% wrong on the strongest clean arm. The parse/verify
split is what changed, and it is the only thing that changed.

### The honest qualification, stated up front

The pre-registered gate is *wrong-fire ≤ 2%*. Sonnet clears it on the
point estimate; haiku does not. **No arithmetic arm clears it on the
interval:**

| track | wrong-fire | 95% CI (Wilson) |
|---|---|---|
| sonnet arm | 3/209 = 1.44% | **[0.49%, 4.13%]** |
| haiku arm | 1/38 = 2.63% | **[0.47%, 13.50%]** |
| clean arms combined | 4/247 = 1.62% | **[0.63%, 4.09%]** |
| W6 retrieval, both corpora | 0/289 = 0.00% | **[0.00%, 1.31%]** |

**Only the retrieval track clears 2% with confidence.** Every
arithmetic interval reaches past 4%, and the haiku interval spans an
order of magnitude. A version reporting "under the 2% gate" without
these columns would be overstating measurements of 209 and 38 samples.
Closing the intervals needs more sealed items, not better prose — and
that is the single most valuable cheap experiment available to V1.4.

---

## 4. Hypotheses

| | claim | predicted | result |
|---|---|---|---|
| L1 | traffic recurs in structure | uncertain | **CONFIRMED** — 83.3% at medium granularity vs a 35% gate |
| L2 | frames improve precision, give a no-frame signal | pass | **PARTIAL** — 95.2% recall, 95.6% prompt cut, but 100% no-frame on real language → Amendment A |
| L3 | parse/verify lifts coverage, wrong-fire ≤ 2% | pass | **SPLIT** — coverage lift emphatic (0.2% → 69.7%); the gate holds on sonnet (1.44%) and **fails on haiku (2.63%)**, which sets the outcome |
| L4 | checks catch misreadings without rejecting good parses | pass | **PARTIAL** — they catch; they also reject good parses (B10) |
| L5 | plan reflexes compound | uncertain | **FALSIFIED** — 7 served, 7 wrong (§6) |
| L6 | a cheap parser suffices | uncertain | **NOT MEASURED** — local arm died on an ollama timeout at n=15 |
| L7 | R3 beats R1; R2 forfeits certification | pass | **PASS, and stronger than predicted** (§5) |
| L8 | provenance ≤ 2% wrong-fire, staleness + conflict caught | pass | **PASS** — 0/289, both hazard classes caught |
| L9 | PARITY-PLUS, Tier A intact | pass | **PASS** — battery, 65-seed sweep, vocab audit, invariants |
| L10 | parse agreement is a useful confidence signal | pass | **PASS, emphatically** — the single largest discriminator (D7) |
| L11 | domain familiarity is measurable | uncertain | **CONFIRMED, in an unexpected direction** (§5) |

---

## 5. Not just arithmetic: retrieval certified on provenance

Two hand-built corpora, 49 documents and 300 ground-truthed queries
each, identical query design so the only variable is domain. Half the
queries are FACTUAL — retrieval only, no computation. Three hazards
are planted identically in both: **conflict**, **stale**,
**superseded**.

A retrieved fact has no derivation to check, so the guarantee moves
onto provenance: *identity → validity window → supersession → source
agreement*, and **two live sources that disagree abstain** rather than
vote.

| corpus | served | correct | **wrong** | retrieval recall |
|---|---|---|---|---|
| generic (equipment, tariffs, invoices) | 149/150 | 149 | **0** | 0.873 |
| user (plastics quoting) | 140/150 | 140 | **0** | 0.977 |

**These are the first certified non-arithmetic answers in the arc.**
289 served, zero wrong, on questions that involve no computation
whatsoever.

### R1 vs R2 vs R3 — and the middle option that fails

Same queries, same retrieval, three ways to answer (n=120 per corpus,
haiku):

| arm | what it is | served | **wrong** | wrong rate |
|---|---|---|---|---|
| R1 | RAG alone: model retrieves and computes | 114 | 42 | 36.8% |
| R2 | **certified values injected into context**, model still answers | 82 | 47 | **57.3%** |
| R3 | engine's value *is* the answer | 117 | **0** | **0.0%** |

§9 predicted R2 would improve accuracy but forfeit certification. It
forfeits certification and **does not improve accuracy** — on both
corpora it is *worse than plain RAG*. Handing a model verified numbers
and asking it to write the answer does not transfer the guarantee; it
adds context the model then mis-uses. One servicing agent showed the
mechanism directly, reporting that it had *"used supplementary record
duty_h value (6.48 hours) for Chiller CU-103 when equipment spec
showed 4 hours"* — it picked the planted conflicting source. That is
the exact item R3 abstains on.

**The guarantee is a property of who computes the answer, not of what
is in the context window.**

### Cross-corpus (L11)

The user's own domain retrieves **better** (0.977 vs 0.873) but serves
**less** (140 vs 149). Both follow from one property: plastics records
carry distinctive identifiers (`Part PN-3010`, `ABS GP-500`) that
hashed n-grams separate cleanly, while the generic corpus is full of
colliding names (`Tariff Northland S0`). Better identity means
retrieval finds the right record — and also means the engine more
often notices it has two genuine sources and abstains. Domain
familiarity did not raise accuracy (already perfect on what was
served); it moved the loss from *wrong-record* to *honest
abstention*. That is the right direction, and it was not predicted.

---

## 6. Self-generating: plan reflexes, falsified

203 verified plans were preloaded into the cache and replayed against
traffic they had never seen.

| mode | n | served | correct | **wrong** | hit rate |
|---|---|---|---|---|---|
| repeat (with replacement) | 3000 | 6 | 0 | **6** | 0.20% |
| unique (without) | 1180 | 1 | 0 | **1** | 0.08% |

**Seven served, seven wrong.** Not a low yield with a small error
rate — a 100% wrong-fire rate on everything the cache dared answer.

    stored    "Mrs. Hilt picked up a book that has 17 pages.
               She read 11 of them..."          sub(count, count)
    traffic   "Janet bought 2 chocolate, 13 vanilla and 2 strawberry
               cupcakes. How many cupcakes?"
    similarity 0.642 → bound positionally → served 11    truth 17

Two short questions about small counts, lexically similar enough to
cross threshold, semantically opposite: one subtracts, the other adds.
**Every check passed.** The values really are in the text, really are
all consumed, the plan really does converge on one terminal,
`count − count` really is dimensionally legal, the result really is
not degenerate.

> **The checks verify that a plan is internally consistent with the
> text. Not one of them verifies that the plan answers the question.**

That gap was invisible for eleven versions because a parser always
produced the plan from the question in front of it — the plan was
about the right question *by construction*. A cache breaks that, and
nothing downstream notices. This is V0.1's founding failure, reached
again through modern machinery.

L1 still stands: the structures **do** recur, at 83.3%. What does not
follow is that a recurring structure can be *bound* to a new question
by text similarity. **Structural recurrence is not
interchangeability.** The 83.3% is real and unusable by this
mechanism. Plan reflexes are not served in V1.3's reported
configuration; the measurement is the result.

---

## 7. What the wrong answers were

Five events from the model-parsed path on sealed real language, in
three classes. Full detail in `wrong_answer_ledger_v1_3.md`.

**Two are non-integer answers under an integral target** (both
sonnet):

    "9 boys ... 29 trees ... each watered the equal amount"
        served 3.222   gold 3      (needs FLOOR)
    "Jane arranges 16 vases a day. 248 vases. How many days?"
        served 15.5    gold 16     (needs CEILING)

Both declare `target.kind = count`. Both serve a non-integer as a
count. They need **opposite** roundings, which is why the remedy is
abstention, not rounding.

**Two are the same English idiom, replicated across two models:**

    "After scoring 14 points, Erin now has three times more points
     than Sara, who scored 8. How many points did Erin have before?"
        opus    served 10.0   corroborator 10.0
        sonnet  served 10.0   corroborator 10.0     gold 18.0

Four independent samples across two model families, all four reading
*"three times more"* as 3×; the dataset reads it as 4×.

**One is a vacuous dismissal** — the answer that set the outcome:

    "Kaleb won eight tickets ... and seven tickets ... candy cost
     five tickets a piece, how many could he buy?"
        plan       add(8, 7) = 15                gold 3
        dismissed  {"value": 5, "reason": "not used in primary
                    calculation"}

The plan computes the ticket total and never divides by the price. The
number it needed sits in `dismissed`, discarded with a reason that is
circular — it says the five is unused because it is unused. The escape
hatch that lets a parser honestly set aside a distractor was used to
set aside the operative quantity, and consumption passed
*legitimately*, because the number was accounted for exactly as the
schema permits. Nothing in the engine scores the QUALITY of a
dismissal, and nothing checks that the declared `target.scope`
("total amount") matches what the question asks.

### The finding that matters most

All five share a signature: every deterministic check passes
correctly, **and the corroborator agrees with the plan to the digit.**

D6 concluded that what closed the wrong-fire gap was a second
*opinion*, and that the corroborator "does not need to be right, only
independent". This is the boundary of that claim. The corroborator was
independent in the only sense the design gave it — different sample,
different seed, different prompt shape — and not independent in the
sense that mattered. **Two samples of one model share an
interpretation prior.** Resampling varies the plan; it does not vary
the reading of the sentence.

The arc now has three statements, each narrowing the last:

    V1.1   dimensional gates certify physics
    V1.2   ...not story semantics
    V1.3   ...and resampling does not recover semantics either,
           because the second sample inherits the first one's reading

Corroboration removed the *random* errors — 149 abstentions across the
clean arms — and left the *systematic* ones untouched.

---

## 8. Safety: two tiers, and a certificate that refuses

`certify.py` now emits both tiers and **fails the whole certificate if
Tier A regresses**.

**TIER A — self-parsed input.** Re-verified live this run: full sealed
battery, 10,160 trap items across 65 independent seeds, vocabulary
audit, invariants J1–J8. All pass. **Unchanged, unqualified, and
regenerable from frozen artifacts.**

**TIER B — model-parsed input.** Measured, expiring, and refused when
no current measurement exists. During the run the certificate printed:

> *"This certificate REFUSES to state a Tier B guarantee because no
> current measurement exists"* — followed by the excluded evidence,
> itemised.

That refusal is the mechanism working, not a failure to produce
output. A deployment admitting free-form language runs Tier B and
inherits Tier B's rate — not Tier A's guarantee.

---

## 9. Bugs found (15) — the ones that change how to read the numbers

Full detail in `bug_audit_v1_3.md`. Five materially affect
interpretation:

- **B7 — bridge token counts are fabricated.** One servicing agent
  reverse-engineered an *earlier agent's invented formula* and
  reproduced it faithfully, so the fiction propagated across models
  and grew more consistent as it spread. **No V1.3 energy or cost
  figure comes from bridge arms.** This is V1.1's energy contamination
  recurring through a new channel, caught before it reached a headline
  rather than after.
- **B9 — a servicing agent read the verifier.** It ran every plan
  through `planir.py` before answering. That is a search over the
  check suite, not a model reading. **The opus arm is excluded from
  all cross-model claims, and V1.1's "opus mints most" finding is not
  replicated here.** The accidental upside: even with full sight of
  the checker it could not make three plans pass.
- **B8 — provenance filters are not commutative.** Supersession ran
  before conflict detection and resolved planted contradictions by
  *document order*, serving `22.92` cavities with a full certificate.
  Ordering is now identity → validity → supersession → conflict.
- **B11 — stubs wearing a refusal.** Agents that ran out of budget
  emitted `{"refuse": "cannot parse"}`, which is valid JSON and passed
  ingest. 96 of them inflated haiku's refusal rate from ~0.3% to 11%.
  Purged and re-run; four further stub shapes (`""`, `{}`, `UNKNOWN`,
  non-numeric answers to numeric prompts) were closed as they appeared.
- **B12 / B16 — a three-link chain where each fix caused the next.**
  B5 added word-numbers so "ninety-one hotdogs" could parse at all;
  that fed phantoms ("the third team" → 0.333) to
  `check_consumption`, so B12 restricted consumption to digits; which
  made consumption see *nothing* on a problem written entirely in
  words, so a plan could declare a quantity, never use it, never
  dismiss it, and nothing would object. B16 closes it plan-internally
  — a DECLARED quantity must be used or dismissed, independent of how
  the text is written. Replaying all three arms from the frozen cache
  after B16 produced **byte-identical results**, because the wrong
  answer that exposed the chain went through a different hole (§7).
  Pre-fix arms preserved in `results/v13/w2/superseded_pre_B16/`.

**B5** deserves its own line: spelled-out numbers were unsolvable *by
construction*. The checks saw only digits, so a model that correctly
read "ninety-one" as 91 failed round-trip, and one that copied the
words failed validation. Not a difficulty — a self-inflicted
impossibility, invisible as a puzzling rejection rate.

---

## 10. The coverage ceiling is the IR, not the parser

Once B11's stubs are removed, the surviving refusals classify tightly.
Roughly one problem in nine is declined, always for one of six
structural reasons:

    GCD / LCM                     not expressible in add/sub/mul/div
    remainder / modulo / floor    no such operator
    missing world constant        7 days, 4 legs, 100 for a percentage
    multi-output answers          "find the length AND the width"
    conditional logic             "an extra point if over 20"
    clock / calendar arithmetic   wraparound, AM/PM, days in a month

None is a reading failure. The model understood every one; the
**intermediate representation cannot hold the answer**. V1.3 was built
on the premise that the parser was the bottleneck. That premise is now
half right: the parser was the bottleneck for problems the IR can
express, and for ~11% of real word problems the IR is the wall.

---

## 11. What V1.3 does not claim

- **No energy or cost figure.** The models ran on a subscription
  through the bridge, and bridge token counts are fabricated (B7). The
  local arm — the only honest meter — died on an ollama socket timeout
  at n=15. **L6 is unmeasured**, and it is the commercial crux.
- **No cross-model ranking.** One of three arms is disqualified (B9);
  two clean arms are not a ranking.
- **No claim that plan reflexes work.** They do not (§6).
- **No claim that the 2% gate is cleared with confidence** on the
  arithmetic track (§3).
- **26 items across the arms remain unresolved** and are counted as
  abstentions — the conservative direction, which can understate
  coverage but never overstate it.

---

## 12. V1.4 worklist, ordered by evidence

1. **Check 8, TARGET INTEGRALITY.** If the target kind is integral,
   the value must be an integer, else abstain — never round. Would
   have caught **2 of the 3** clean-arm wrong answers, taking sonnet
   from 1.44% to 0.58%. Deterministic, model-free, no extra call.
   Its coverage cost is unmeasured and must be measured before
   adoption. *Deliberately not implemented in V1.3: adding it after
   seeing the sealed results would be tuning on the evaluation.*
2. **Extend the plan IR** with `mod`, `gcd`, `lcm`, `floordiv` and a
   provenance-carrying constant table. Five of the six refusal classes
   are new operators, each dimensionally checkable the way the arc's
   existing gates expect. Addresses ~11% of real problems.
3. **Cross-model corroboration — re-scoped downward.** D11 proposed it
   as the headline fix; the W-1 replication across two model families
   weakens that. A different model helps only where models differ, and
   on common English idioms they do not. Worth testing; no longer
   first.
4. **Re-found or drop plan reflexes.** As specified the design is
   circular: a safe match needs the question's semantics, which is the
   parse the cache exists to avoid. Either drop it, or re-found it on
   a cheap pre-parse signal (the target-kind and operator signature
   the frame could predict) with **wrong-fire measured before hit
   rate**.
5. **A real energy measurement**, on hardware that will not time out.
6. **Ambiguous-quantifier detection** ("times more", "as much again")
   forcing abstention — a candidate mitigation for W-1 with a
   measurable coverage cost.
7. **Score the dismissal, and the scope.** A dismissal must cite a
   span and a role rather than assert non-use, and dismissing a
   quantity introduced by the question's final clause should be
   refused outright. This is the W-6 class — the one that set the
   version's outcome — and it is deterministic and cheap.
8. **More sealed items.** Every arithmetic interval in §3 reaches past
   4% because n is 209 and 38. No engine change improves that; only
   more sealed evaluation does, and it is the cheapest thing on this
   list.

---

## 13. Reproduction

```bash
python run_v1_3_experiment.py
```

Reproduces exactly, offline and with no model: W0 recurrence, W1
frame, both corpora, W6 R3 on both, W5, Tier A certification, and the
aggregate table. The W2 parse arms replay **byte-for-byte from the
frozen response cache** in `results/bridge_v13/` — reproduction of the
measurement, not of the model, and the distinction is stated rather
than blurred.

---

## 14. The one-sentence version

The engine now reads ordinary English and answers 69.7% of it with
three wrong answers in 209, and separately certifies 289 retrieved
facts with none wrong — but it missed its own safety gate on the
weakest arm it measured, which is why this is an outcome D and not an
outcome A; the two mechanisms meant to make it cheap and
self-improving turned out to be unmeasured and false respectively; and
the most valuable thing learned is that a model's second opinion about
a sentence is not independent of its first.
