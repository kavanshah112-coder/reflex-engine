# V1.4 SPEC — SEMANTIC COMPOSITION VIA A RELATIONAL STATE SUBSTRATE
## Open state · relations as stated · engine-derived types · capability applicability · semantic integrity

**STATUS: FROZEN 2026-09-01, tag `v1.4-plan`.** §17–§19 and the
AMENDMENT block never change after the first sealed run. The five §20
decisions are RESOLVED in the AMENDMENT at the end of this file.

Companion document: `V1_4_PLAN.md` holds the full V1.3 architecture map
(§2 there) and the research framing. This file is the implementable
specification: modules, data shapes, and per-package acceptance gates.

---

## 1. The thesis this version tests

V1.3 proved a separation and exposed a representation failure.

> **INTERNAL VALIDITY ≠ SEMANTIC CORRECTNESS.**
> The verifier sees a valid computation. The computation answers a
> different question than the one asked.

Five wrong answers, three classes, one shared signature: every
deterministic check passed *and* the corroborator agreed. The engine
could not tell that a well-formed plan was well-formed **for the wrong
reading**.

The architecture map (PLAN §2) found the cause is not an absent
capability but a bypassed one. Tier A carries entities, temporal
ordering, scope, polarity, provenance, a status lattice, a
goal-regression planner and a Long Path Manager, and runs at 0.000
wrong-fire over 10,160 traps. V1.3's model path used none of it: it
invented `quantities / plan / target / dismissed` and asked the model to
assert its own types.

But Tier A's state is relational **and closed** — a fixed 15-field
record, 77 fixed kinds, 58 capabilities of shape `{expr, inputs,
output}` with no applicability conditions. That closure is what buys the
0.000, and it is also why `speed × time` fires on a round trip.

**The thesis:** an *open* relational substrate — heterogeneous packets,
relations stored as stated, types derived by the engine — can carry real
language into deterministic execution and reduce semantically-wrong-
but-internally-valid answers, **without** losing the deterministic
guarantee and **without** destroying the end-to-end energy advantage.

**This is not assumed.** §18 rung C exists for "the substrate is worse",
and C0 is preserved executable so the comparison is direct.

---

## 2. Compute policy (DECISION i — open, §20)

V1.3 ran bridge-only. That cost the energy claim entirely (B7: servicing
agents fabricated token counts) and one arm's admissibility (B9: an agent
read the verifier).

Whatever is chosen, these are binding:

- **Servicing prompts forbid reading engine source.** The bridge is
  serviced from a directory that does not contain `reflex/`.
- **Token counts are measured or zero. Never estimated.** An arm that
  cannot measure reports calls and check outcomes, never energy.
- **At least one arm end-to-end metered on local hardware**, or the
  energy question is again reported unanswered (§16).
- Stub shapes rejected at ingest: empty, `{}`, `UNKNOWN`/`ERROR`/`N/A`,
  non-numeric answers to numeric prompts, and refusals whose reason names
  the agent rather than the problem (B11).
- Dual/independent samples are interleaved so twins never share a batch
  (B14).

---

## 3. W0 — Baseline lock and architecture freeze

**Purpose.** Guarantee the comparison is meaningful before anything is
built.

**Work.**
- Verify V1.3 integrity: tags `v1.0-final` … `v1.3-final` present, trees
  clean, `reflex-engine-v1.3-frozen` intact, `.env` absent from all
  snapshots.
- Re-run `python run_v1_3_experiment.py`; confirm it reproduces the
  published arm numbers from the frozen bridge cache
  (haiku 38/37/1, sonnet 209/206/3, retrieval 289/0).
- Take the immutable V1.4 starting snapshot.
- Freeze `C0` — the V1.3 path — behind an interface. **C0 source is not
  edited for the rest of V1.4.**

**Acceptance.** C0 reproduces V1.3 byte-for-byte. If it does not, §18
rung F fires immediately and V1.4 does not start.

---

## 4. W1 — The substrate (`reflex/rss.py`)

**Purpose.** One general container that stores what a query contains and
how its parts relate, without imposing meaning.

### 4.1 Node

Open record. Fields are present when established, **absent otherwise** —
never defaulted, never filled with a plausible value. (V1.3 D5: the
model filled `kind` because the schema demanded it, and the labels were
noise.)

```json
{
  "id": "n3",
  "content": 49,
  "span": "49 of them are bread rolls",
  "identity": "bread_rolls",
  "order": 1,
  "context": {"scope": "bakery", "polarity": "asserted"},
  "provenance": {"source": "USER_TEXT"},
  "confidence": "med",
  "derived_from": ["n1", "e2"],
  "role_hint": "part_of_total"
}
```

`role_hint` is an **open** vocabulary — evidence, never a gate. No check
may depend on it.

### 4.2 Relation

```json
{
  "id": "r1",
  "span": "three times more points than",
  "args": ["n_erin", "n_sara"],
  "order": 0,
  "resolved": null
}
```

`span` is verbatim and mandatory. `resolved` is written **only** by the
engine (W2), never by a producer.

### 4.3 Packet

`content` may be a packet. Packets are heterogeneous and are **not**
required to share fields:

| query type | packet carries |
|---|---|
| arithmetic | quantities · entities · relations · events · ordering |
| theory | concepts · properties · mechanisms · evidence |
| retrieval | entity · source · validity · provenance · supersession |
| mixed | linked substructures of the above |

Nesting: `packet → subpacket → relation → state transition`. The
retrieval packet is V1.3's W6 structure reused verbatim — deliberately,
because it is the only V1.3 track that cleared the gate with confidence
(0/289, upper bound 1.31%).

### 4.4 The extended invariant (binding on every later package)

> **Producers supply SPANS and proposed structure.
> The ENGINE derives kinds, operators and applicability.
> Integrity validates. No producer writes certified state.**

This is V0.8's I4 typed boundary applied to semantics. A model-asserted
type is unverifiable; a model-asserted **span** round-trips against the
source text.

### 4.5 API

```python
class State:
    def add_node(self, span, content=None, **meta) -> str
    def add_relation(self, span, args, **meta) -> str
    def get(self, nid) -> dict
    def neighbours(self, nid, kind=None) -> list
    def ordered(self) -> list            # by `order` where present
    def unresolved(self) -> list         # relations still unresolved
    def to_json(self) -> dict            # round-trippable, hashable
```

**Acceptance.** Round-trips to JSON byte-identically. Every node's
`span` is a verbatim substring of the source text (mechanically
checked). No field is auto-populated.

---

## 5. W2 — Relation resolution and the ambiguity gate

**Purpose.** The single largest representational change, and the
deterministic fix for the one class V1.3 could not touch.

```
V1.3:  mul(q3, q8)                            already committed to 3x
V1.4:  relation(span="three times more than")  resolved separately
```

`reflex/relations.py` resolves a relation span against a table, with
exactly three outcomes:

- **resolved** — the phrase maps to exactly one operator → proceed;
- **ambiguous** — the phrase matches the AMBIGUITY SET → **abstain**;
- **unknown** — not in the table → **abstain**, logged to the residual.

### 5.1 AMBIGUITY SET (FROZEN at freeze; never extended after a sealed run)

```
"times more" / "times as many" with an implicit comparative base
"as much again"
"half again as many"
"more than X" where X is itself derived
bare "the other" / "the rest" with >1 candidate antecedent
"average" with no stated population
"each" where the distributee is ambiguous between two entities
```

Each entry requires a positive and a negative case in S1 (§13).

**Why this is not solved by a second model.** W-1 produced the identical
wrong value from opus *and* sonnet across four independent samples.
Ambiguity is a property of the phrase, not of a model, so a deterministic
phrase gate catches what cross-model corroboration cannot.

**Acceptance.** Every AMBIGUITY SET entry abstains on its positive case
and does **not** abstain on its negative case. Unknown-relation rate is
reported, not hidden.

---

## 6. W3 — Engine-derived kinds (`reflex/kindderive.py`)

**Purpose.** Remove the model's ability to assert a type.

Input: a node's `span`. Output: a kind from `packs/*/kinds.json`
(77 kinds: dim vector, unit, nouns, aliases) or `UNKNOWN`.

- Derivation is by lexicon lookup over the span's nouns and units.
- `UNKNOWN` is a first-class outcome and does **not** default to `count`.
- **Integrality** is a property of the derived kind, not of a model
  assertion. This is V1.3's proposed check 8, pre-registered here rather
  than added after seeing sealed results.

### 6.1 Check 8 — TARGET INTEGRALITY (pre-registered)

If the target's derived kind is integral, a non-integer result
**abstains — never rounds.** V1.3's two instances needed *opposite*
roundings (3.222 trees floors, 15.5 days ceilings), which is precisely
why rounding is not a remedy.

**Pre-registered expectation:** would have caught 2 of 3 clean-arm wrong
answers in V1.3, taking sonnet 1.44% → 0.58%. **Its coverage cost is
unmeasured and is a required output of this package**, not an
afterthought.

**Acceptance.** Kind-derivation accuracy reported against a hand-labelled
sample; `UNKNOWN` rate reported; check 8's coverage cost reported as a
number before any claim rests on it.

---

## 7. W4 — Capability applicability (`packs/*/caps.json` v2)

**Purpose.** Stop dimensionally-correct, semantically-inapplicable
execution.

Extend the capability record from `{expr, inputs, output}` with an
optional `applicability`: preconditions **on relational state**, not on
types.

```json
{
  "spec": {"expr": "speed * time", "inputs": ["speed","time"],
           "output": "distance"},
  "applicability": [
    {"require": "target_relates_to", "arg": "distance"},
    {"require": "same_segment", "args": ["speed","time"]},
    {"require": "segment_identified"},
    {"forbid":  "unresolved_relation", "arg": "return_trip"},
    {"forbid":  "unresolved_relation", "arg": "repetition"},
    {"forbid":  "conflicting_relation", "arg": "journey_state"}
  ]
}
```

Semantics: a condition must be **established**, not merely
un-contradicted. If it cannot be: **do not execute** — abstain or
escalate.

> A capability that is mathematically correct and semantically
> inapplicable is not safe.

Capabilities without authored conditions retain V1.3 behaviour; ablation
C3 measures exactly what the conditions buy.

**Acceptance.** Every authored condition has an adversarial case that
trips it. Conditions are versioned in the pack and hashed.

---

## 8. W5 — Semantic integrity (`reflex/semint.py`)

Runs over the substrate. Detects at minimum:

```
 1 entity mismatch                 9 contradictory relations
 2 similar-entity confusion       10 duplicate/conflicting entities
 3 wrong event association        11 unresolved references
 4 wrong temporal ordering        12 cross-entity quantity contamination
 5 wrong scope                    13 capability applicability failure
 6 wrong target                   14 plan/query semantic mismatch
 7 incorrect grouping             15 reused-plan semantic mismatch
 8 missing state transition
```

Each class gets its own adversarial cases in S1 and its own detection
rate in the report. **A class with no detector is reported as undetected,
never omitted.**

### 8.1 The grouping hazard, by construction

*"90 people start. 49 leave, then 19 leave. How many remain?"*

```
n1  content=90              identity=population   order=0
e1  relation=leave  qty=49  affects=n1            order=1
s1  derived_from=[n1,e1]    content=41
e2  relation=leave  qty=19  affects=s1            order=2
s2  derived_from=[s1,e2]    content=22
ask target=population  at_order=last
```

`90 − (49 − 19) = 60` is **unrepresentable**: `e2` affects `s1`, and no
edge lets 19 modify 49. Where V1.3 needed a check to catch the
mis-grouping, the substrate makes it inexpressible.

**This is the mechanism claim of the version, and H3 is where it is
measured rather than asserted.**

**Acceptance.** Per-class detection rate; false-positive rate on
correct states reported alongside — a detector that fires on good states
is a coverage tax, not safety.

---

## 9. W6 — Path Manager over the substrate

`v10/pathman10.py` already keeps state across a plan, re-parses nothing
between steps, routes typed `("<GAP>", kind)` steps to the LLM, and never
lets the LLM control the global path. V1.4 rewires it to run over the
substrate and to check applicability before each step:

```
what must happen → which capability can do it → what state it consumes
→ what state it produces → what relations must remain true
→ what preconditions must hold → what passes to the next step
```

Goal-regression from the **ask** is what prevents V1.3's W-6 failure: a
plan that computes "total tickets" and stops cannot satisfy a regression
whose goal is "candies purchasable".

**Binding.** The LLM never overrides a deterministic gate. The typed-gap
channel is the only place a model touches a step.

**Acceptance.** Path completion rate; steps refused by applicability;
zero cases of a model-supplied value entering certified state
(mechanically asserted, as in V0.8 I4).

---

## 10. W7 — Plan reuse, reworked

> **similarity ≠ applicability**

V1.3's mechanism scored **7 served / 7 wrong**. Re-admission requires a
stored plan to record its semantic preconditions, and a candidate query's
relational state to satisfy them: same relevant entity relations, same
target semantics, compatible event structure, compatible ordering,
compatible constraints, compatible scope.

**Explicitly insufficient, alone or in combination:** similar wording,
similar quantities, similar structure, similar embeddings.

**Acceptance gate (pre-registered).** Plan reuse is reported as usable
only at **zero wrong-fire on S1's reuse-trap block** *and* a hit rate
above 5%. Below either, it is reported as retired again — the honest
outcome, and the one V1.3 reached.

---

## 11. W8 — Semantic equivalence

The sharpest single test of the thesis. Two directions, reported as a
**confusion matrix**, never as one accuracy number:

- **structurally similar / semantically different** must be
  distinguished — the Mrs. Hilt ↔ cupcakes pair is case 1;
- **structurally different / semantically equivalent** must be
  recognised as the same.

The matrix exists because passing one direction by collapsing the other
is the obvious degenerate solution.

---

## 12. W9 — Long-horizon tractability

Do not assume the substrate stays efficient. Over S4, measure: state
growth, state compression, relation count, path length, reflex coverage,
LLM escalation, false certifications, integrity failures.

Watch for: combinatorial explosion, memory growth, lookup degradation,
relation ambiguity, stale state, duplicate state, conflicting state.

**H10 is falsified if any of these grows super-linearly in query
complexity.**

---

## 13. Datasets

All generated, **hashed, and sealed before any tuning**. No sealed set is
inspected answer-side before its run.

| | set | contents |
|---|---|---|
| **S1** | fresh adversarial semantic suite | multi-entity · repeated entities · temporal ordering · multi-stage state change · nested ops · contradictions · implicit relations · ambiguous references · pronouns · more/less than · times as many · remaining · total · average · rate · frequency · round trips · repeated cycles · multiple segments · causal · theoretical · theory+calculation · retrieval+reasoning · numerical distractors · **structurally-similar/semantically-different pairs** · **semantically-equivalent/lexically-different pairs** |
| **S2** | real language, retained | V1.3's GSM8K/ASDiv sealed sample, unchanged, for direct comparability |
| **S3** | fresh human language | colloquial · incomplete sentences · implicit relations · unusual word order · synonyms · pronouns · multi-entity reference · natural numerical description · theory · mixed |
| **S4** | long-horizon workload | generated, for W9 |
| **S5** | retrieval | V1.3's two corpora unchanged + multi-document relational cases |

S1 must contain blocks explicitly built to break: dimensional-only
validation · structural similarity · plan reuse · capability
applicability · entity binding · state transitions.

---

## 14. Ablation matrix

```
C0   V1.3 control — flat plan IR, unchanged, byte-identical
C1   substrate only
C2   substrate + semantic integrity
C3   substrate + capability applicability
C4   substrate + Path Manager
C5   complete V1.4 system
```

Paired comparisons: fixed schema vs substrate · structural similarity vs
relational equivalence · dimensional validation vs semantic
applicability · plan reuse on vs off.

---

## 15. Metrics

Measured for every arm and every ablation:

```
coverage · correct coverage · WRONG-FIRE · abstention
semantic-conflict detection rate (per class) · plan-reuse safety
path completion · LLM calls/query · reflex calls/query · latency
J/query · J/correct answer
```

Wrong-fire is reported **whether or not it is zero**, per class, per set,
per arm, with Wilson intervals.

---

## 16. Energy accounting — the boundary is the claim

V1.3 made **no** energy claim (B7). V1.4 must not repeat that, and must
not hide semantic work outside the boundary.

For pure LLM and for the reflex architecture:

```
J/query · J/correct · LLM calls/query · % solved without LLM
% of energy in: parsing · semantic interpretation · Path Manager
                reflex execution · verification · fallback
```

**Rules.** Every model call is inside the boundary, the semantic worker
included. No estimated tokens, ever. Bridge arms may report calls and
check outcomes but never energy. Comparison is against pure LLM **at
equivalent task difficulty**.

### 16.1 Statistical power — pre-registered n (DECISION ii, §20)

V1.3's intervals settled nothing: sonnet 1.44% [0.49, 4.13], haiku 2.63%
[0.47, 13.50]. **No engine change fixes that; only n does.**

- to certify wrong-fire **≤ 2%** at an observed **0**: n ≥ **200**
  certified answers per arm (rule of three);
- to certify **≤ 2%** at a true rate near **1.4%**: n ≈ **1,500** per
  arm.

**The sealed size is chosen before running, and it determines what may be
claimed.** A claim the chosen n cannot support is not made.

---

## 17. Hypotheses (FROZEN on freeze)

| | hypothesis | prediction |
|---|---|---|
| H1 | a general relational substrate improves semantic composition over the fixed representation | uncertain |
| H2 | it reduces wrong entity binding | uncertain |
| H3 | it reduces structurally-valid-but-semantically-wrong computation | uncertain — **THE headline** |
| H4 | capability applicability conditions reduce semantic wrong-fire | pass |
| H5 | semantic integrity improves safety without unacceptable coverage loss | uncertain |
| H6 | the substrate makes safe plan reuse possible | uncertain — V1.3 says 7/7 wrong |
| H7 | it improves Path Manager orchestration | uncertain |
| H8 | it improves real-language coverage | uncertain |
| H9 | it preserves the end-to-end energy advantage | uncertain — **the commercial crux** |
| H10 | it stays tractable as complexity and path depth grow | uncertain |

Statuses are determined from measured data only.

---

## 18. Outcome ladder (FROZEN; priority F > D > C > B > A)

```
F  Tier A regressed, or C0 no longer reproduces V1.3's published
   numbers. A broken baseline invalidates every comparison.

D  Any sealed suite above its pre-registered wrong-fire gate.
   A safety regression outranks every coverage and energy claim.

C  The substrate performs WORSE than C0 on semantic wrong-fire.
   Reported as the headline. This rung exists because the thesis is
   not assumed true.

B  H3 null — the substrate neither reduces nor increases semantic
   wrong-fire, at materially higher cost. A more expensive tie.

A  H3 confirmed AND (H4 or H5) AND H9 holds.
```

**A requires all three.** Rising coverage alone is not success: V1.3's D
verdict came from a coverage arm, not a coverage failure.

---

## 19. Discipline (carried forward, non-negotiable)

- **Version preservation.** V0.1 → V1.3 untouched; all prior tags and
  snapshots verified before start; immutable V1.4 starting snapshot.
- **Pre-registration.** This file tagged `v1.4-plan` before any sealed
  evaluation. §17–§19 never change after data. Amendments append, are
  dated, and state what forced them (V1.3 Amendments A and B are the
  precedent).
- **No tuning on sealed sets.** V1.3 declined to add its own best fix for
  this reason; that fix is pre-registered here as W3 §6.1 instead.
- **Bug discipline.** Log it, identify when it entered, preserve
  superseded results under `superseded_<tag>/`, rewind to a
  registry-consistent boundary, re-run affected measurements, never
  silently overwrite history.
- **Convergence rule.** Bounded servicing rounds; unresolved items score
  as ABSTENTIONS; post-seal work is quarantined, never ingested.
- **Do not manufacture a positive outcome.** Rung C is real.

---

## 20. Open decisions — required before freezing

1. **Sealed size (§16.1).** "Near-zero" at n ≈ 200/arm, or "under 2%" at
   n ≈ 1,500/arm? Largest cost driver; determines what may be claimed.
2. **Energy hardware (§16).** V1.3's local arm managed n=22 at ~5 min/item
   before timing out. Accept a small metered arm, or defer the energy
   claim again?
3. **Compute policy (§2).** Bridge again (no spend, slow, needs B9/B11
   hardening), or a metered API budget for the arms carrying the energy
   claim?
4. **Scope.** Full W1–W9, or a staged first cut (W0–W5 + C0/C1/C2) with
   applicability and Path Manager deferred to V1.5?
5. **Ambiguity set (§5.1).** Frozen as listed, or extended first? It
   cannot be extended after a sealed run.

---

## 21. Deliverables

Substrate · relation resolver + ambiguity gate · kind derivation +
check 8 · capability applicability (pack v2) · semantic integrity layer
(15 classes) · Path Manager over the substrate · reworked plan reuse ·
semantic-equivalence confusion matrix · S1/S3/S4 generated, hashed and
sealed · ablation C0–C5 across llama-8B / Haiku / Sonnet · end-to-end
energy analysis with the boundary stated · plots · logs (invention /
bug / wrong-answer ledger) · two-tier certificate · `v1.4-final` tag +
frozen snapshot + report + PDF + artifact + memory ·
`run_v1_4_experiment.py`.

---

## 22. The question this version answers

Not *"can the system understand more?"* but:

> **Can the system represent enough of the meaning of a query that
> deterministic reflex computation safely replaces expensive LLM
> reasoning in real workloads?**


---

# AMENDMENT — decisions resolved, 2026-09-01, BEFORE any sealed run

## D-i · Compute policy: BRIDGE, hardened (§2)

Bridge again, no API spend. Binding hardening, all of it enforced in
code rather than in prompt wording alone:

- the bridge is serviced from a directory that does **not** contain
  `reflex/`, so a servicing agent cannot read the verifier even if it
  tries (B9 made the opus arm inadmissible in V1.3);
- servicing prompts forbid reading engine source explicitly;
- token counts are **zero or measured, never estimated** (B7);
- ingest rejects every known stub shape: empty, `{}`, `UNKNOWN` /
  `ERROR` / `N/A` / `ABSTAIN`, non-numeric answers to numeric prompts,
  and refusals whose reason names the agent rather than the problem
  (B11);
- dual samples are interleaved so twins never share a batch (B14).

## D-ii · Sealed size: 2,400 items — and a decision RULE, not a fixed n

**My n ≈ 1,500 figure in the draft was wrong** and is corrected here
before it could enter a pre-registration. It came from a plain normal
approximation; recomputed with the Wilson interval the arc actually
reports:

    observed wrong-fire   certified n needed for upper bound < 2%
        1.4%                    2,025
        0.9%                      600
        0.5%                      375
        0.0%                      200

The required n therefore depends on the rate achieved — which is the
very thing V1.4 is trying to change. Fixing n at 1,500 would
pre-commit to a number that clears the gate only if the substrate
works.

**Resolved.** The SEALED SET is fixed at **2,400 items**; the CLAIM is
governed by a rule:

> An arm may state "wrong-fire ≤ 2%" only if its Wilson 95% **upper
> bound** is below 2%, at whatever n that arm reached. Otherwise it
> reports the point estimate and the interval and makes no gate claim.

Corpus capacity is the binding constraint and is stated rather than
discovered: GSM8K test (1,319) + ASDiv (2,306) = 3,625 real-language
items total, of which V1.3 consumed ~1,780. So the 2,400 splits:

    S1  generated adversarial semantic suite   1,200   (pool unlimited)
    S3  fresh real language, disjoint from all
        V1.3 usage                             1,200   (pool allows it)
    S2  V1.3's 300-item sealed sample, retained unchanged for direct
        comparability (reported separately, never pooled into the above)

Projected certified counts at V1.3 coverage rates, stated in advance so
nobody is surprised later:

    sonnet          ~1,672    can clear 2% if the rate falls below ~1.1%
    opus            ~1,591    same
    llama-8B local  ~  763    can clear if the rate falls below ~0.8%
    haiku           ~  304    can clear only at ~0.5% or below

**Haiku cannot reach a 2,000-scale n at any budget** — at 12.7%
coverage it would need ~16,000 items and the corpus holds 3,625. This
is a property of the arm, not of the funding, and it is recorded now so
that haiku's interval is read as expected rather than as a shortfall.

## D-iii · Energy: measured on the local arm, longer run

The energy claim rests on the **local ollama arm**, metered end to end,
run long. V1.3's local arm reached n=22 before a socket timeout; the
timeout is already raised to 600 s and the arm is budgeted for a
multi-hour run at n ≥ 400.

Accounting boundary unchanged and binding: every model call inside it,
semantic worker included; bridge arms may report calls and check
outcomes but **never** energy; comparison against pure LLM at equivalent
task difficulty.

## D-iv · Scope: FULL W1–W9. Nothing skipped.

All nine packages and the complete C0–C5 ablation. The staged option in
the draft is withdrawn.

## D-v · AMBIGUITY SET extended (FROZEN as of this amendment)

Original seven retained, plus seven more, each grounded in a V1.3
observation:

```
 8  percentage with no stated base ("50% more", "60% of")
       - V1.3 refusal class: the 100 is never in the text
 9  bare multiplier with implicit base ("half", "twice", "double",
    "triple") - V1.3 extracted "half" as 0.5 where 2 was needed
10  "remaining" / "left" after >=2 depletion events with no anchor
       - which remainder is being asked for
11  "between X and Y" - inclusive vs exclusive boundary
12  "up to" / "at least" / "no more than" - a BOUND stated where a
    VALUE is expected
13  comparative against an unstated population ("above average",
    "faster than usual")
14  "per" / "a piece" / "each" where the distributee is ambiguous
    between two entities  (extends entry 7)
```

Every entry needs a positive and a negative case in S1. **This set is
now frozen and may not be extended after the first sealed run.**

## D-vi · Opus included, and a cross-model architecture comparison

Opus runs as a first-class arm under the D-i hardening, which is what
made it inadmissible in V1.3. Beyond wrong-fire and coverage, V1.4
reports a **cross-model comparison of the relational state itself** —
newly possible because the state is now inspectable rather than a flat
plan:

    RELATIONAL STATE QUALITY   nodes/query, relations/query, span
                               fidelity, entity-graph completeness,
                               order coverage, unresolved-relation rate
    REFLEX BEHAVIOUR           reflexes used/query, reflexes minted,
                               applicability refusals, path length,
                               path completion, gap-step rate
    SEMANTIC ERROR PROFILE     per-class detection and per-class escape,
                               by model

Arms: **llama-8B · haiku · sonnet · opus**, identical sealed sets,
identical substrate. V1.1's "opus mints most" claim is treated as
UNREPLICATED and is re-tested here from scratch, not assumed.

## What did not change

§17 hypotheses, §18 ladder (rung C — "the substrate is worse" — still
sits above B and A), and §19 discipline are unchanged and are frozen
with this amendment.
