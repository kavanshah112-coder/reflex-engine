# V1.7 SPEC — Composition at Scale

## A million-query workload of multi-reflex questions: do certified reflexes compose, and how long does a model take to find the structure?

**STATUS: DRAFT v2 — all seven §11 decisions RESOLVED by the user
(2026-09-03: free-hand minting incl. connector reflexes; in-repo
storage; rest as proposed). Ready to freeze as tag `v1.7-plan` on
the user's word.** §7–§10 never change after the first sealed run.

Built on V0.1–V1.6. No prior version, tag, snapshot, dataset, report
or log is modified. Full arc protocol applies: pre-registration,
hashed sealed sets (raw bytes, `-text` attr), dev/sealed splits, no
tuning on sealed results, bugs documented with superseded runs
preserved, single-command reproduction, finalize with tag + frozen
snapshot (`.env` excluded) + report MD/PDF + memory update.

**The user's brief (2026-09-03), recorded verbatim in intent:** run
~1,000,000 queries on each model arm; the queries cover complex
questions where MORE than one or two reflexes must be used; test the
reflexes' cohesiveness and combined calculation; and measure how much
time an LLM takes to figure out and implement a multi-reflex
structure.

---

## 1. What V1.6 left exactly here

V1.6 sealed the single- and short-chain regime: 55.5% foreign
coverage, 70.4% mixed, **zero wrong-fire over 118k+ serves**, and a
271-reflex library whose minting quality improved monotonically with
model scale. Its depth curve ended the version with a shape, not a
decay: **d3 chains 99.7% served, d4+ 0% — by guard.** Every d4 item
escalated because nothing in the system could compose three or more
certified steps and a final operation; the engine refused rather than
guessed, which is correct and is also the boundary V1.7 attacks.

Two prior results stand as the hazard and the hope:

- **The hazard — V1.3 plan reflexes: 7 served, 7 wrong.** "Checks
  verify a plan matches the TEXT, never that it answers the
  QUESTION." A plan is producer-supplied STRUCTURE, and structure is
  exactly what the dimensional gates cannot see (gsm1120's lesson at
  a higher level). Any V1.7 design in which a model proposes the
  composition must answer this head-on.
- **The hope — V1.6's inversion of V1.1:** when producers propose
  *procedures* and an independent witness checks every output, model
  fluency became coverage instead of wrongness. V1.7 extends the same
  bet one level up: let producers propose *compositions of
  procedures*, gate the composition, witness every step AND the end.

In-regime constants carry forward unchanged (21 mJ/serve V1.2,
64.9 J/call V1.4; identity: saving ≈ served share). The model matrix
is haiku / sonnet / opus / fable via isolated bridge, no local model,
no new energy claims (B7).

---

## 2. Thesis

> Certified reflexes are not just individually safe — they COMPOSE.
> A workload of million-query scale whose items need 3–6 reflexes
> chained through intermediate values can be served three ways, in
> strictly decreasing determinism: (i) the engine composes the chain
> itself; (ii) a model proposes the chain ONCE and the engine
> executes, gates, and witnesses every step and the end; (iii) full
> escalation. V1.7 measures how far (i) and (ii) reach, whether
> independently-minted reflexes cohere when chained, and what a
> model's structure-finding costs in time across four scales.

The commercial identity gains a term: a type-(ii) serve costs ONE
structuring call amortized over every repeat of that structure
(V1.0's amortization lesson), so

```
E_system ≈ f_esc×E_llm + f_plan×(E_llm/η + k×E_engine) + f_det×k×E_engine
    η = plan reuse factor (structures recur; V1.3 W0: 83.3% structural
        recurrence on real traffic at medium granularity)
```

---

## 3. What is honestly unknown — the version's core questions

**Q1 — cohesiveness.** V1.6's reflexes were admitted ALONE, each
witnessed on its own leaf. Nothing says reflex A's output is what
reflex B needs: units drift (A yields m/s, B expects km/h), types
drift (a root list into a scalar slot), precision drifts (numeric
witness tolerances compound over k steps). **Does a library of 271
independently-minted procedures behave as ONE calculator when
chained?** Compounding tolerance is a real hazard: k chained 1e-6
relative checks do not guarantee an end-to-end 1e-6.

**Q2 — who finds the structure?** The engine's deterministic composer
can chain only what it can parse into a DAG. The unknown is the gap
between "the engine sees the chain" and "a model sees the chain":
V1.6's d2 sat at 50% because chains hide in clause structure. When a
model bridges that gap by emitting a STRUCTURED PLAN, does the
plan-level gate hold where V1.3's plan reflexes failed — or does
"plan matches text, not question" return at scale?

**Q3 — time-to-structure.** How long does each model scale take to
read a multi-reflex question and emit a valid executable plan, and
does that time grow with chain depth k? Measured comparatively
across the four scales through an identical bridge harness.

**Q4 — million-scale stability.** 118k serves at zero wrong-fire is
not 4M. At 1M×4 arms, one-in-a-million defect classes (B27-family
crashes, tolerance edge cases, regex pathologies in 271 patterns)
get their first honest chance to fire.

---

## 4. Architecture

```
QUERY
  |
  v  gateway16 (V1.6, unchanged: Tier A + sciparse + reflexes)
  |            serves what it already serves
  |
  +-- composer17 (NEW, deterministic): parses "chain-visible" text
  |     into a PLAN DAG itself; executes below
  |
  +-- planner sample only (bridge, per model): model reads the query
  |     and emits a PLAN in the frozen plan schema -- it computes
  |     NOTHING and its plan carries no values (V1.3 lesson: values
  |     from producers are banned; STRUCTURE is quarantined until
  |     gated)
  |
  v  PLAN GATE (NEW, deterministic; the V1.3 answer):
  |    G-P1 schema: every node is a known op/reflex; DAG, no cycles
  |    G-P2 type/unit flow: every edge type-checks and unit-checks
  |         through the taxonomy (kind/dimension of each output
  |         matches the consuming slot; conversions inserted only
  |         from the certified conversion table)
  |    G-P3 ask-target match: the terminal node's kind/unit must
  |         match what the QUESTION asks (the anti-gsm1120 check:
  |         a plan ending in joules cannot serve a percent ask)
  |    G-P4 completeness: every stated quantity is consumed or
  |         explicitly declared irrelevant by the gate (B28 rule
  |         lifted to plan level: an ignored stated number kills
  |         the plan)
  |
  v  EXECUTOR: each node runs through symcore16/Tier A behind the
  |    per-step witness; END-TO-END witness re-derives the final
  |    value on the mpmath side through the whole chain with
  |    tolerance budgeted for depth k (Q1's compounding answered by
  |    construction: the end check is one check, not k stacked)
  |
  +-- CERTIFIED (chain certificate: every node, every witness, the
  |    plan hash, the gate transcript)
  +-- else ESCALATED untouched
```

New code: `reflex/composer17.py` (deterministic chain parser),
`reflex/plangate17.py` (G-P1..4 + chain certificate),
`reflex/chainexec17.py` (DAG execution + end-to-end witness),
`reflex/connector17.py` (the new reflex class below),
`tools/build_q1m.py`, `tools/planner17.py` (bridge plan collection +
timing). Reused untouched: all of V1.6, its 271-reflex library as
the STARTING library, taxonomy, witness, gauntlet machinery.

### 4.1 Phase L' — free-hand minting, including CONNECTOR reflexes
(user decision, 2026-09-03)

Each model gets a free hand on the ACQ residual stream to mint, per
the V1.6 discipline (isolated bridge, same residuals for every
model, everything laddered), THREE classes:

1. **parse reflexes** — the V1.6 class, unchanged (pattern → task);
2. **chain reflexes** — a pattern mapping text to a multi-step PLAN
   in the frozen plan schema (structure only, no values), gated by
   the full plan gate G-P1..4 before probation;
3. **connector reflexes** — the new class: a bridge that CONNECTS
   two pre-existing reflexes so queries needing their combination
   certify. Schema:

   ```
   {"name": ..., "from": <taxonomy leaf or op whose output it
    consumes>, "to": <op/reflex slot it feeds>, "adapter":
    <template expr over the upstream value, e.g. "($v)/1000" or a
    certified-conversion reference>, "when": <optional trigger
    words>}
   ```

   A connector carries NO answer and NO parse of its own — it is
   pure plumbing, and its adapter expression executes through the
   witness like any other computation. Placement is by evidence:
   its from/to endpoints must exist and type/unit-check through
   G-P2, or it is index-killed.

Gauntlet for all three classes: G1 schema (constant tasks and
memorization banned as before), G2 evidence-based placement, G3
shadow probation — for chain and connector reflexes probation runs
on CHAINED items and requires ≥3 end-to-end-witnessed correct
serves on ≥2 distinct operand tuples with ZERO wrong. The per-model
creation ledger (proposed / killed-by-gate / admitted, per class)
remains a primary deliverable, now with a connector column — the
cohesiveness question made constructive: where the library fails to
compose, can a model mint the missing joint, safely?

**Positive controls before any counting run (B24):** the plan gate
gets a battery of deliberately wrong plans that MUST all die — right
values/wrong ask (gsm1120-shaped), unit-flow breaks, cyclic DAGs,
plans ignoring a stated quantity, plans smuggling a literal value.
The end-to-end witness gets seeded wrong finals that MUST all fail.

---

## 5. Datasets

```
Q-1M        1,000,000 items, composition-first generator (seed
            1700): every in-domain item is a DAG of 2-6 reflex-level
            steps over the 47-leaf taxonomy, ≥60% needing 3+ steps
            (the brief's "more than one or two"), ≥40% multi-domain,
            ≥50% non-monotonic step sequences, plus 2% narrative
            distractors (corpora reuse, escalation-only claim) and a
            foreign-phrased overlay (bridge-authored around fact
            sheets, ~6k). Golds computed step-by-step by the
            INDEPENDENT witness constructor with end-to-end
            verification at build. Stored as JSONL under
            `results/v17/data/` and committed there with raw-byte
            hashes and `-text` attr (user decision: the repo has no
            remote, clone bloat is not a concern; the folder is the
            record).
            Splits (adjusted because free-hand minting needs its own
            stream that is neither dev-tuned nor sealed):
            ACQ 200k (minting residuals) / DEV 100k / SEAL 300k /
            REPLAY 400k (evaluated, never tuned on), distractors
            disjoint across all four.
S-PLAN      the planner sample: 600 DEV + 1,200 SEALED items drawn
            from Q-1M's 3+-step stratum (same items for every model;
            no model receives foreign items it authored), used for
            the bridge planning runs and the time-to-structure
            measurement.
```

The 1M×4 claim: each ARM (deterministic modes per model-library —
but the library is the frozen union, so deterministic arms are
identical across models) — the per-MODEL 1M runs are the plan-mode
arms: model-planned serving evaluated on the full million via PLAN
REUSE (a plan collected on S-PLAN generalizes to every item sharing
its structure signature; V1.3's 83.3% recurrence made testable).
Each model's plan library replays over the same 1M workload: that is
"1,000,000 queries on each model" at bridge budgets that fit.

---

## 6. Time-to-structure (the brief's timing question, made honest)

Per model, per S-PLAN item: wall-clock from prompt-ready to
valid-plan-received through an IDENTICAL bridge harness, plus
plan-token count, plus attempts (invalid plans are re-asked once;
both timed). Reported as:

- median / p90 seconds per scale, split by chain depth k=2..6;
- structure-finding success: % of items yielding a gate-PASSING plan;
- time per ADMITTED plan (failures amortize into the cost).

**Frozen caveat (B7's sibling):** bridge wall-clock includes harness
overhead; numbers are COMPARATIVE across scales measured in the same
harness within the same session window, never absolute latency
claims, and token counts are reported alongside as the
harness-independent proxy.

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| V1 | independently-minted reflexes compose: deterministic chain serving reaches a usable share of 3+-step items at zero wrong-fire | uncertain — Q1 is open; tolerance compounding and unit drift are real |
| V2 | the end-to-end witness catches every seeded wrong final (control) and blocks real drift | must pass its control or no chain serve counts |
| V3 | the plan gate holds where V1.3 fell: ZERO certified-wrong from model plans (the plan-level gsm1120 stays shut) | **the version's safety crux — V1.3 precedent says this is where it breaks** |
| V4 | model-planned serving lifts 3+-step coverage over the deterministic composer on sealed data | uncertain |
| V5 | plan quality and structure-finding success rise with model scale (V1.6's monotonicity, one level up) | predicted from V1.6 |
| V6 | time-to-structure rises with chain depth k and falls with scale | plausible; measured, both halves |
| V7 | plans REUSE: structure signatures recur enough that S-PLAN plans cover a large share of the 1M workload (η >> 1) | predicted from V1.3 W0 (83.3% recurrence) |
| V8 | million-scale stability: zero engine crashes, zero SAFETY breaches over 4M+ evaluations | pass — B27 family is contained; first honest test at this scale |
| V9 | CONNECTOR minting works: models identify missing joints between existing reflexes and mint adapters that lift chain coverage at zero minted wrong-fire | **the constructive half of Q1 — new class, no precedent; V1.6's monotone-quality result suggests yes at higher scales** |

---

## 8. Metrics (FROZEN)

**Primary: (a) 3+-step sealed coverage and wrong-fire per serving
mode (deterministic / plan-replay per model) — SEAL 300k and the
full-1M replay; (b) plan-gate outcomes per model (proposed / G-P1..4
kills / admitted / certified-correct / certified-WRONG — the last
must be zero); (c) time-to-structure distributions per model per
depth (§6); (d) plan-reuse factor η per model.**

Secondary: cohesiveness autopsy (unit-drift kills, type kills,
tolerance kills at G-P2 and the end witness, per pair of reflex
families); depth curve d2–d6 per mode; distractor escalation (zero
certified, in-stream); identity-projected saving with the η term;
serve latency at chain depth; per-check gate transcript stats.

---

## 9. Thresholds (FROZEN)

```
SAFETY-1    wrong-fire on ALL served answers, every arm, every set
            <= 0.5%; target and expectation 0. An unaddressed or
            gate-transcript-less chain certificate counts WRONG.
SAFETY-2    zero certified narrative items (in-stream distractors).
SAFETY-3    zero certified-WRONG answers from MODEL-PROPOSED plans
            (one = the V1.3 class is open at plan level; that arm
            fails regardless of its coverage).
SAFETY-4    zero wrong-fire attributable to any V1.7-minted reflex
            of ANY class (parse / chain / connector) on sealed data
            — V1.6's SAFETY-3 standard extended; one traced wrong
            revokes the reflex AND is reported; >=3 from one
            model's library fails that arm.
GATE-CTRL   plan-gate + end-witness control batteries pass 100%
            before any counting run; a control failure voids all
            chain serves until fixed and rerun.
COHESION    deterministic 3+-step sealed coverage >= 25% (the
            composer sees the chain and the library holds together),
            at SAFETY-1.
PLAN-LIFT   best plan arm adds >= +10pp over deterministic on the
            3+-step sealed stratum at SAFETY-3, else model planning
            is reported as not paying.
TIMING      complete §6 distributions for all four scales on >= 90%
            of S-PLAN sealed items (a measurement threshold, not a
            speed bar — no speed number is pre-judged).
SCALE       4M+ total evaluations complete with zero uncontained
            engine errors (contained B27-style refusals reported).
```

---

## 10. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  Tier A / V1.6 stop reproducing, or a GATE-CTRL battery cannot
   pass.
E  SAFETY-1, SAFETY-2 or SAFETY-3 fails — composition is unsafe, or
   the V1.3 plan class reopened.
D  safe but incoherent: deterministic 3+-step coverage < 10% — the
   library does not compose and the version's premise fails.
C  COHESION met but PLAN-LIFT fails on every scale: reflexes
   compose deterministically, model structuring adds nothing;
   report the timing study and the deterministic result honestly.
B  COHESION + PLAN-LIFT met, but TIMING or SCALE incomplete, or
   plan reuse η < 2 (plans do not amortize; the economics term
   dies while the safety result stands).
A  COHESION >= 25%, PLAN-LIFT >= +10pp on >= 2 scales at SAFETY-3
   zero, SAFETY-4 zero across all minted classes, full timing
   distributions on all 4 scales, η >= 2 on >= 2 scales, SCALE
   clean.
```

---

## 11. Decisions — RESOLVED by the user (2026-09-03)

1. **Q-1M splits** — as proposed, ADJUSTED for decision 2: minting
   needs its own untainted stream, so ACQ 200k is carved from the
   replay mass. Final: **ACQ 200k / DEV 100k / SEAL 300k /
   REPLAY 400k.**
2. **Minting: FREE HAND, all four models** (user-directed). Each
   model may mint parse reflexes, chain reflexes, and the new
   **connector reflexes** — adapters that join two pre-existing
   reflexes so combined queries certify (§4.1). Same isolation,
   same gauntlet discipline, chained probation for chain/connector
   classes, SAFETY-4 gate, per-class creation ledger.
3. **S-PLAN** — 600 dev / 1,200 sealed per model, as proposed.
4. **Plan schema breadth** — full: symcore ops + the reflex library
   (V1.6's 271 + V1.7 admissions) + Tier A caps, as proposed.
5. **Depth mix** — k=2:20 / k=3:30 / k=4:25 / k=5:15 / k=6:10;
   ≥40% multi-domain; ≥50% non-monotone, as proposed.
6. **Plan retries** — 1 re-ask, both attempts timed, as proposed.
7. **Storage** — Q-1M lives IN the repo under `results/v17/data/`
   (user-directed: no remote, size is not a concern). Raw-byte
   hashes still recorded before any sealed run; `-text` attr set.

---

## 12. What this version honestly claims, and does not

It does not re-litigate reading language, and it does not mint new
parsing. It claims the next structural thing: **that a library of
individually-certified procedures behaves as one calculator when
questions require three, four, six of them in sequence — that a
model can find the structure the engine cannot see, without ever
being trusted for a value — and that the finding cost is a measured,
scale-dependent number.** If the plan gate cannot keep model
structure honest, rung E says the V1.3 class is still open and the
next version knows exactly what it is about. If reflexes simply do
not compose, rung D says the library is a collection, not a
calculator — a result worth exactly as much as its opposite.

Either way, at 4M+ evaluations, "zero wrong-fire" stops being a
promising streak and becomes the load-bearing claim of the whole
arc — or it breaks, and the break is the finding.
