# V1.4 — Relational State Substrate

**STATUS: DRAFT.** Not frozen. Section 17 lists the decisions needed
before this becomes the pre-registration. Nothing in §13–§15 may change
after the first sealed run.

---

## 1. What V1.3 established, and is preserved unchanged

These are standing facts. V1.4 does not re-litigate them, and no V1.4
result may quietly overwrite them.

1. **Parse/verify separation works.** Model reads, engine computes. Real-
   language coverage went from 0.2% (V1.2: 519/520 abstained) to 69.7%
   on the sonnet arm.
2. **It still produces wrong answers.** 209 certified, 3 wrong (1.44%);
   haiku 38 certified, 1 wrong (2.63%) — the breach that set OUTCOME D.
3. **Retrieved facts certify safely on provenance.** 289 served, 0 wrong
   across two corpora. The only track clearing the 2% gate *with
   confidence* (upper bound 1.31%).
4. **Plan reuse is unsafe.** 7 served, 7 wrong.
5. The canonical instance: a plan from *"Mrs. Hilt … 17 pages … read
   11"* (`sub`) bound positionally onto *"Janet bought 2 chocolate, 13
   vanilla and 2 strawberry cupcakes"* → served 11, truth 17.
6. **Strong models produce sophisticated but semantically inapplicable
   work.** `speed × time` is dimensionally impeccable and silent about
   round trips, segments, and frequency.
7. **Corroboration removes random error and leaves systematic error.**
   149 abstentions bought; every interpretive failure survived.
8. **INTERNAL VALIDITY ≠ SEMANTIC CORRECTNESS.** This is the sentence
   V1.4 exists to attack.
9. Dimensional correctness verifies structure, not meaning.
10. Semantic composition and semantic **applicability** are the
    remaining bottlenecks.

Also preserved: Tier A is unregressed (battery, 10,160 traps, 65 seeds,
vocabulary audit, invariants — all pass), the opus arm stays excluded
(B9), and no energy figure may be derived from bridge token counts (B7).

---

## 2. Architecture map — what actually exists today

Produced by inspection of the V1.3 tree before any design work.

### 2.1 Entry

`reflex/gateway.py` — `ReflexGateway.ask()` → `CERTIFIED_REFLEX` /
`LLM_ESCALATED` / `ABSTAINED`, each with a certificate. Hazards abstain
rather than escalate.

### 2.2 The TIER A path (self-parsed, deterministic, 0.000 wrong-fire)

```
query → v11.semparse11 → v11.integrity11 → v10.planner10
      → v10.pathman10  → v11.semrun11    → certificate
```

- **`v11/semstate11.py` (204 LOC) — the existing semantic state.**
  FACT records carrying `entity, concept, attribute, temporal, role,
  scope, polarity, value, unit, provenance, span, status, ambiguity,
  confidence, derived_from`. Identity key is the 6-tuple
  `(entity, concept, role, temporal, scope, polarity)`; same key +
  different value = CONFLICT. An **EntityGraph** carries aliases,
  ordinals, pronouns and comparatives ("the faster car" by argmax over
  certified facts). Statuses: `ASSERTED → CERTIFIED | AMBIGUOUS |
  CONFLICTED | QUARANTINED`, plus `DERIVED`. Only CERTIFIED is
  executable.
- **`v11/integrity11.py` (214 LOC)** — `certify()` + `check_invariants()`.
- **`v10/planner10.py` (126 LOC)** — goal-regression backward chaining
  with subgoal memoization, GAP-aware (emits `("<GAP>", kind)` pseudo-
  steps), deterministic with lexicographic tie-breaks.
- **`v10/pathman10.py` (156 LOC) — the Long Path Manager.** Keeps state
  across the whole plan, no re-parse between steps, routes typed gaps to
  the LLM, **never lets the LLM control the global path**.
- **`v11/semrun11.py` (236 LOC)** — entity-scoped execution (invariant
  I3: an entity-specific target consumes only that entity's facts +
  GLOBAL), temporal-delta targets, relational targets, selective
  redundancy on high-risk paths.
- **`packs/physics/`** — 77 kinds (dim vector, unit, nouns, aliases),
  58 capabilities as `{expr, inputs, output}`.

### 2.3 The TIER B path (model-parsed, new in V1.3)

```
query → reflex/parse_agent.py → reflex/planir.py → execute
```

- **`reflex/planir.py` (371 LOC)** — the flat plan IR:
  `quantities[] / plan[] / target / dismissed[]`, seven checks
  (agreement, structure, round-trip, consumption, scope, dimensional,
  non-degeneracy) plus corroboration, then direct evaluation.

### 2.4 The finding that reframes V1.4

**Tier B bypasses every relational structure the arc already owns.**

| capability | Tier A | Tier B (V1.3) |
|---|---|---|
| entity identity + graph | yes | **no** |
| temporal / event ordering | yes (`temporal`, `derived_from`) | **no** |
| scope, role, polarity | yes | **no** |
| status lattice + quarantine | yes | **no** |
| goal-regression planner | yes | **no** |
| Long Path Manager | yes | **no** |
| typed kinds from a pack | 77 kinds | model-asserted `count`/`money` |
| capability signatures | 58 typed caps | four hardcoded ops |
| wrong-fire | **0.000** / 10,160 traps | 1.44%–2.63% |

Every V1.3 semantic failure maps onto a structure that exists on the
Tier A side and was unavailable on the Tier B side:

- W-6 (Kaleb, served 15 for truth 3) — the plan stopped at "total
  tickets". Goal-regression *toward the ask* cannot stop early; it
  regresses from the target.
- The `90 − (49 − 19) = 60` grouping error — `temporal` +
  `derived_from` + state transitions exist in `semstate11`.
- W-5 (plan reuse) — entity graph and scope would gate the bind.
- W-4 (3.222 trees) — `kinds.json` carries the type; the model was asked
  to assert it instead.

So the honest problem statement is **not** "the engine has no relational
state". It is:

> **V1.3 built a second, poorer representation for the model-parsed path
> and routed real language through it.** The rich representation was
> right there and closed to model input.

### 2.5 But the existing state is not the answer either

`semstate11` is relational and **closed**: a fixed 15-field fact record,
a closed 77-kind universe, a closed 58-capability set, and capabilities
with `{expr, inputs, output}` and **no applicability conditions** — which
is exactly the `speed × time` hazard in §1.6.

**The V1.4 problem, precisely:** make the state *open and heterogeneous*
(packets, emergent relations, theory and retrieval alongside arithmetic)
**without losing the 0.000 wrong-fire that the closed version buys.**

---

## 3. Core question (frozen wording)

> Can a general relational state substrate — storing values, entities,
> relationships, ordering, context, provenance, constraints and state
> transitions **without forcing every query into a predefined semantic
> schema** — reduce semantically-wrong-but-internally-valid answers,
> while preserving the deterministic safety guarantees and the
> end-to-end energy advantage?

**This hypothesis is not assumed true.** §12's ablation is built so the
fixed representation and the substrate are compared directly, and §15
contains a rung for "the substrate performs worse".

---

## 4. The substrate (RSS)

`reflex/rss.py`. One general container. **The substrate stores; it does
not interpret.** Interpretation belongs to the Path Manager and the
integrity layer.

### 4.1 Design rule

> **Unlabelled ≠ unstructured.** No fixed semantic taxonomy. But every
> element carries machine-readable structural metadata, because
> determinism needs it.

A node carries *any* of the following, and is not required to carry all:

```
id            stable handle
content       number | string | packet | reference | null
span          verbatim source text  (round-trippable — the safety anchor)
role_hint     OPEN vocabulary, evidence-bearing, never a closed enum
relations     edges to other nodes, stored AS STATED (§4.3)
order         position / sequence index where the text implies one
context       scope, conditions, qualifiers
provenance    source, validity window, version   (V1.3 W6 machinery)
confidence    where a producer can honestly supply it
identity      entity handle into the entity graph
derived_from  causal ancestry for anything computed
```

Absent fields are absent, not defaulted. **A field the producer did not
establish must never be filled with a plausible value** — that is
exactly how `kind: "count"` became noise in V1.3 (finding D5).

### 4.2 Who supplies what — the extended invariant

V1.3's invariant was *no LLM-supplied number enters certified state*.
V1.4 extends it to types and relations:

> **The model supplies SPANS and proposed structure.
> The engine DERIVES kinds, operators and applicability.
> Integrity validates; the model never writes certified state.**

This is the V0.8 I4 typed boundary (measured: all 60 resolver proposals
validator-rejected at haiku and sonnet scale) applied to semantics. A
model-asserted `kind` is unverifiable. A model-asserted **span** is
round-trippable against the source text, and the engine can derive the
kind from the span via `kinds.json` nouns/aliases.

### 4.3 Relations stored as stated

The single most important representational change.

```
V1.3:   mul(q_3, q_8)                      already committed to 3×
V1.4:   relation(Erin, Sara, span="three times more than")
```

The engine resolves relation phrases to operators in a **separate,
deterministic step**, against a relation table. Three outcomes:

- **resolved** — the phrase maps to exactly one operator; proceed;
- **ambiguous** — the phrase is in the pre-registered AMBIGUITY SET
  (§4.4); **abstain**;
- **unknown** — not in the table; **abstain** and log for the residual.

This is a deterministic, model-free fix for W-1, which V1.3 could not
touch. Cross-model corroboration would not have caught it: opus and
sonnet produced the identical wrong value on four independent samples,
so the misreading is model-invariant. Ambiguity is a property of the
*phrase*.

### 4.4 AMBIGUITY SET (frozen before any run)

```
"times more" / "times as many as" when the comparative base is implicit
"as much again"
"half again as many"
"more than X" where X is itself a derived quantity
bare "the other" / "the rest" with >1 candidate antecedent
"average" with no stated population
"each" where the distributee is ambiguous between two entities
```

Each entry needs a positive and a negative case in the adversarial suite
(§10). Adding to this list after a sealed run is forbidden.

### 4.5 Packets

The substrate is not arithmetic-only. A node's `content` may be a packet,
and packets are heterogeneous by design:

- **arithmetic** — quantities + entities + relations + events + ordering
- **theory** — concepts + properties + mechanisms + evidence
  (`temperature → kinetic energy → collision rate → reaction rate`)
- **retrieval** — entity + source + validity + provenance + supersession
  (V1.3's W6 structure, reused verbatim)
- **mixed** — linked substructures of the above

Nesting is `packet → subpacket → relation → state transition`. **No
requirement that packets share fields.** Building the general container
on the retrieval packet is deliberate: that is the only V1.3 track that
cleared the gate with confidence.

### 4.6 Worked example (the §1 grouping hazard)

*"90 people start. 49 leave, then 19 leave. How many remain?"*

```
n1  content=90  span="90 people start"   identity=population  order=0
e1  relation=leave  quantity=49  affects=n1  order=1
s1  derived_from=[n1,e1]  content=41
e2  relation=leave  quantity=19  affects=s1  order=2
s2  derived_from=[s1,e2]  content=22
ask target=population  at_order=last
```

`90 − (49 − 19) = 60` is not merely wrong here — it is **unrepresentable**:
`e2` affects `s1`, not `e1`, and there is no edge that would let 19
modify 49. Where V1.3 needed a check to *catch* the mis-grouping, the
substrate makes it inexpressible. That is the mechanism V1.4 is testing,
and §13 H3 is where it gets measured rather than asserted.

---

## 5. Capability applicability

Extend `caps.json` from `{expr, inputs, output}` to add optional
`applicability` — **preconditions on relational state**, not on types.

```
capability:  distance = speed × time
requires:
  - target relates to distance
  - speed and time belong to the SAME travel segment
  - the applicable segment is identified
  - no unresolved return-trip relation
  - no unresolved repetition/frequency relation
  - no conflicting journey-state relation
```

If a condition cannot be **established** (not merely "is not
contradicted"): **do not execute.** Abstain or escalate.

> A capability that is mathematically correct and semantically
> inapplicable is not safe.

Conditions are authored per capability, versioned in the pack, and each
one needs an adversarial case that trips it. Capabilities without
authored conditions keep V1.3 behaviour, and the ablation (C3) measures
exactly what the conditions buy.

---

## 6. Semantic integrity layer

`reflex/semint.py`, running over the substrate, detecting at minimum:

```
 1 entity mismatch                9 contradictory relations
 2 similar-entity confusion      10 duplicate/conflicting entities
 3 wrong event association       11 unresolved references
 4 wrong temporal ordering       12 cross-entity quantity contamination
 5 wrong scope                   13 capability applicability failure
 6 wrong target                  14 plan/query semantic mismatch
 7 incorrect grouping            15 reused-plan semantic mismatch
 8 missing state transition
```

Each class needs its own adversarial cases and its own detection rate in
the report. A class with no detector is reported as undetected rather
than omitted.

---

## 7. Path Manager integration

`pathman10` already keeps state across a plan and refuses to let the LLM
control the global path. V1.4 rewires it to run over the substrate and to
check applicability before each step:

```
what must happen → which capability can do it → what state it consumes
→ what state it produces → what relations must remain true
→ what preconditions must hold → what passes to the next step
```

The `("<GAP>", kind)` pseudo-step already routes typed gaps to the LLM;
that channel is retained and is the only place a model touches a step.
**The LLM never overrides a deterministic gate.**

---

## 8. Plan reuse, reworked

> **similarity ≠ applicability**

A stored plan may execute only if the new query's relational state
satisfies the plan's recorded semantic preconditions: same relevant
entity relations, same target semantics, compatible event structure,
compatible ordering, compatible constraints, compatible scope.

Explicitly insufficient, alone or combined: similar wording, similar
quantities, similar structure, similar embeddings.

Otherwise abstain. V1.3's mechanism scored 7/7 wrong; the pre-registered
bar for re-admitting plan reuse is in §14.

---

## 9. Semantic equivalence test

A dedicated suite, and the sharpest single test of the whole hypothesis:

- **structurally similar / semantically different** — must be
  distinguished (the Mrs. Hilt ↔ cupcakes pair is case 1);
- **structurally different / semantically equivalent** — must be
  recognised as the same.

Reported as a confusion matrix, not a single accuracy number. Passing one
direction by collapsing the other is the obvious degenerate solution and
the matrix exposes it.

---

## 10. Datasets

All generated, hashed, and **sealed before any tuning**. No dataset in
this section may be inspected answer-side before its run.

**S1 — fresh adversarial semantic suite.** multi-entity; repeated
entities; temporal ordering; multi-stage state change; nested operations;
contradictions; implicit relations; ambiguous references; pronouns;
"more/less than"; "times as many"; "remaining"; "total"; "average";
"rate"; "frequency"; round trips; repeated cycles; multiple segments;
causal; theoretical; theory+calculation; retrieval+reasoning; numerical
distractors; **structurally-similar/semantically-different pairs**;
**semantically-equivalent/lexically-different pairs**. Explicitly
targeted at breaking: dimensional-only validation, structural similarity,
plan reuse, capability applicability, entity binding, state transitions.

**S2 — real language, retained.** The V1.3 GSM8K/ASDiv sealed sample,
unchanged, for direct comparability.

**S3 — fresh human language.** Colloquial, incomplete sentences, implicit
relations, unusual word order, synonyms, pronouns, multi-entity
reference, natural numerical description, theory, mixed reasoning.

**S4 — long-horizon generated workload.** For §11.

**S5 — retrieval.** V1.3's two corpora, unchanged, plus multi-document
relational cases.

---

## 11. Long-horizon / tractability

Do not assume the substrate stays efficient. Measure, over a substantial
generated workload: state growth, state compression, relation count, path
length, reflex coverage, LLM escalation, false certifications, integrity
failures.

Watch specifically for: combinatorial explosion, memory growth, lookup
degradation, relation ambiguity, stale state, duplicate state,
conflicting state. H10 is falsified if any of these grows
super-linearly in query complexity.

---

## 12. Ablations

```
C0   V1.3 control — flat plan IR, unchanged           (the baseline)
C1   substrate only
C2   substrate + semantic integrity
C3   substrate + capability applicability
C4   substrate + Path Manager
C5   complete V1.4 system
```

Paired comparisons: fixed schema vs substrate · structural similarity vs
relational equivalence · dimensional validation vs semantic
applicability · plan reuse on vs off.

C0 must remain **executable and byte-identical** for the life of V1.4.
The substrate goes in behind a clean interface; the V1.3 path is not
edited to accommodate it.

---

## 13. Hypotheses (to be FROZEN)

| | hypothesis | prediction |
|---|---|---|
| H1 | a general relational substrate improves semantic composition over the fixed representation | uncertain |
| H2 | it reduces wrong entity binding | uncertain |
| H3 | it reduces structurally-valid-but-semantically-wrong computation | uncertain — **the headline** |
| H4 | capability applicability conditions reduce semantic wrong-fire | pass |
| H5 | semantic integrity improves safety without unacceptable coverage loss | uncertain |
| H6 | the substrate makes safe plan reuse possible | uncertain — V1.3 says 7/7 wrong |
| H7 | it improves Path Manager orchestration | uncertain |
| H8 | it improves real-language coverage | uncertain |
| H9 | it preserves the end-to-end energy advantage | uncertain — **the commercial crux** |
| H10 | it stays tractable as complexity and path depth grow | uncertain |

Statuses come from measured data only.

---

## 14. Metrics, thresholds, and statistical power

### 14.1 Measured everywhere

coverage · correct coverage · **wrong-fire** · abstention ·
semantic-conflict detection rate · plan-reuse safety · path completion ·
LLM calls/query · reflex calls/query · latency · **J/query** ·
**J/correct answer**.

### 14.2 Energy accounting — the boundary is the point

V1.3 made **no** energy claim, because bridge token counts were
fabricated (B7). V1.4 must not repeat that, and must not hide semantic
work outside the boundary.

Report, for pure LLM and for the reflex architecture:

```
J/query · J/correct · LLM calls/query · % solved without LLM
% of energy in: parsing · semantic interpretation · Path Manager
                reflex execution · verification · fallback
```

**Rules.** Every model call inside the boundary, including the semantic
worker. No estimated token counts, ever — measured or zero. Bridge arms
may report calls and check outcomes but **never** energy. At least one
arm must run on locally-metered hardware end to end, or the energy
question is reported unanswered again.

### 14.3 Statistical power — pre-registered n

V1.3's intervals were too wide to settle anything: sonnet 1.44%
[0.49, 4.13], haiku 2.63% [0.47, 13.50]. **No engine change fixes that.**

- To certify wrong-fire **≤ 2% with 95% confidence at an observed 0**:
  n ≥ **200** certified answers (rule of three: 3/200 = 1.5%).
- To certify **≤ 2%** at a true rate near **1.4%**: n ≈ **1,500**
  certified answers.

So V1.4 pre-registers its sealed size to the claim it intends to make. If
the target is "near-zero wrong-fire", n ≥ 200 per arm suffices and is
cheap. If the target is "under 2% at a nonzero rate", the run must be
~1,500 per arm or the claim must not be made. **Choose before running.**

### 14.4 Model scale

llama-8B · Haiku · Sonnet, all three, on locally-metered hardware where
possible. Opus only under a clean pre-registered protocol — V1.3's opus
arm was disqualified because its servicing agent read the verifier (B9).
**Servicing prompts must forbid reading engine source, and the bridge
should be serviced from a directory that does not contain it.**

---

## 15. Outcome ladder (to be FROZEN)

Priority **F > D > C > B > A**, tested in that order.

```
F  Tier A regressed, or C0 no longer reproduces V1.3's published numbers.
   A broken baseline invalidates every comparison.

D  Any sealed suite above its pre-registered wrong-fire gate.
   A safety regression outranks every coverage and energy claim.

C  The substrate performs WORSE than C0 on semantic wrong-fire.
   Report it as the headline. This rung exists because the hypothesis
   is not assumed true.

B  H3 null: the substrate neither reduces nor increases semantic
   wrong-fire, at materially higher cost. A more expensive tie.

A  H3 confirmed AND (H4 or H5) AND H9 holds: semantic coverage rises,
   deterministic safety is preserved, and the end-to-end energy
   advantage survives.
```

**A requires all three.** Coverage rising on its own is not success —
V1.3's D verdict came from a coverage arm, not a coverage failure.

---

## 16. Discipline (carried forward, non-negotiable)

- **Version preservation.** Verify V1.3 integrity and all prior tags
  before starting; immutable V1.4 starting snapshot; V0.1 → V1.3 stay
  untouched.
- **Pre-registration.** This file frozen and tagged `v1.4-plan` before
  any sealed evaluation. §13–§15 never change after data.
- **Bug discipline.** Log it, identify when it entered, preserve
  superseded results, rewind to a registry-consistent boundary, re-run
  affected measurements, never silently overwrite history.
- **No tuning on sealed sets.** V1.3 declined to add its own best fix
  (target integrality) for exactly this reason; that check is
  pre-registered here instead.
- **Convergence rule.** Bounded servicing rounds; unresolved items score
  as ABSTENTIONS. Post-seal work is quarantined, never ingested.
- **Do not manufacture a positive outcome.** If the substrate is worse,
  rung C says so.

---

## 17. Open decisions — needed before this can be frozen

1. **Sealed size (§14.3).** Target "near-zero" at n ≈ 200/arm, or "under
   2%" at n ≈ 1,500/arm? This is the largest cost driver in the version
   and it determines what may be claimed.
2. **Energy hardware.** An end-to-end metered run needs a local model on
   this machine. V1.3's ollama arm managed n=22 at ~5 min/item before
   timing out. Accept a small metered arm, or defer the energy claim
   again?
3. **Bridge vs API.** Bridge again (no spend, slow, needs the B9/B11
   hardening), or a small metered API budget for the arms that carry the
   energy claim?
4. **Scope.** §4–§8 is a large build — substrate, applicability
   conditions on 58 capabilities, 15 integrity classes, Path Manager
   rewiring, reworked reuse. A first cut could take C0/C1/C2 only and
   defer C3/C4 to V1.5. Full scope, or staged?
5. **Ambiguity set (§4.4).** Frozen as listed, or extended first? It
   cannot be extended after a sealed run.

---

## 18. Execution order

1. Architecture map ✔ (§2 — done, and it changed the framing)
2. Freeze this plan; tag `v1.4-plan`; immutable starting snapshot
3. Build the substrate behind a clean interface — **C0 stays executable**
4. Semantic integrity layer; capability applicability conditions
5. Build S1/S3/S4; hash and seal
6. Run C0–C5 across all model classes
7. Analyse; plots; report; certificate; energy analysis
8. Tag `v1.4-final`; frozen snapshot; reproduction command

---

## 19. The question this version answers

Not *"can the system understand more?"* but:

> **Can the system represent enough of the meaning of a query that
> deterministic reflex computation safely replaces expensive LLM
> reasoning in real workloads?**
