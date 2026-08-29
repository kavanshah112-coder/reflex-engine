# V1.1 SPEC — ENGINE-LAYER COVERAGE + TYPED REFLEXES + COMMERCIAL-SCALE SIMULATION

Status: FROZEN 2026-08-29, operationalizing the user directive:
engine-layer fixes then re-run the ablation; test the architecture on
Opus via the BRIDGE method (no API keys this version); run a longer
simulation to check efficiency at commercial scale with varied
topics; improve automatic reflex generation by TYPE-CASTING reflexes
(functional: maths / thermodynamics / physics / finance; memory and
text reflexes from repetitive concepts) with type-respective
validation gates. Work continues in reflex-engine (V1.0 preserved by
tag v1.0-final + byte-verified reflex-engine-frozen snapshot).
Sections 8–9 (hypotheses, outcomes) freeze at the plan commit, before
any V1.1 sealed item exists.

## 0. Non-negotiables (arc discipline, carried forward)

0.1 Never modify reflex-poc* repos/snapshots or reflex-engine-frozen.
    Verify all at finalization. `_arc/` stays byte-frozen (ORIGINS
    hashes): every V1.1 engine change lives in NEW files
    (reflex/engine_patches.py + engine wrapper), applied at load —
    the arc's auditable runtime-patch pattern.
0.2 Pre-registration: this spec + V1_1_PLAN parameters commit BEFORE
    any V1.1 sealed set is generated; generators commit before
    generation; sealed sets are touched once. Preserve-supersede-
    rerun for bugs after first results. Report negatives prominently.
0.3 Energy: V0.5 meter protocol for local metered runs. API models
    strictly calls/tokens — and in V1.1 ALL API-model work
    (haiku/sonnet/opus mining + any API servicing) goes through the
    DEFERRED-REPLAY BRIDGE (Agent-tool servicing, matching model),
    NOT direct API keys, per the user directive. The .env key is not
    used this version.
0.4 Finalize: tag v1.1-final, snapshot reflex-engine-v1.1-frozen
    (excluding .git and .env), report + PDF + artifact, ledger +
    logs, memory update, repro `python run_v1_1_experiment.py`.

## 1. W1 — Engine-layer fixes (the violation_log worklist, measured)

Fixes target the measured residual anatomy. Each is deterministic,
implemented in reflex/engine_patches.py (never editing _arc), with
unit tests, and is accepted only under the PARITY-PLUS gate:

  PARITY-PLUS: on the full V0.5–V0.11 battery + V1.0's sealed
  residual — (a) wrong-fire stays 0.000 everywhere; (b) NO item that
  was correct becomes incorrect or abstains (zero regressions);
  (c) every changed item is individually diffed and must be
  abstain→correct; (d) energy bound unchanged (≤ 0.61 J/q).

  F1 word-number vocabulary: dozen/half/couple/quarter forms
     ("a dozen", "half a", "a couple of", "one and a half") extended
     in mention extraction via patch.
  F2 hyphenated number-unit forms: digit-hyphen-unit ("2-tonne",
     "11-ohm") normalized before parse (digit-hyphen-letter only).
  F3 ask-focus correction, generalized from V1.0's acquired-kind
     override: when the base namer's target kind is already present
     as an input fact (asking-for-what-you-were-told) and exactly one
     OTHER kind noun (any kind, single-word included) appears in the
     ask clause, that kind becomes the target; plus pack target_verbs
     (currently dead data) wired into target recovery.
  F4 opportunistic small fixes ONLY if surfaced by F1–F3 test
     failures; each logged in violation_log.md.

Deliverable: W1 lift measured on V1.0's sealed residual (A0 re-run:
0.0% → X%) — the engine-fix contribution, cleanly attributed.

## 2. W2 — Typed reflex generation (the user's type-cast directive)

Every candidate (and every ACTIVE reflex + its certificate) carries a
reflex_class:

  FUNCTIONAL.<domain>   computational reflexes — the V1.0 types
                        (new_kind, new_cap, conversion, unit_index,
                        lexicon_noun, adj_map), domain-cast
                        deterministically from the output kind's
                        dimension vector + registry domain map:
                        maths (dimensionless/count), physics
                        (mechanics/electrical dims), thermodynamics
                        (temperature-bearing dims), finance (money-
                        bearing dims).
  MEMORY.fact           a recurring (concept, value, unit) constant
                        for a topic ("g = 9.8 m/s^2", "steel density
                        7800 kg/m^3") mined from REPEATED
                        observations in traffic; injected as a
                        GLOBAL certified constant usable by solves
                        whose query omits it.
  TEXT.qa               a recurring normalized question whose
                        escalation answers agree — served as a text
                        reflex with a memory certificate (the
                        certified semantic cache).

Type-respective gates (the user's "respective gate to validate"):
  FUNCTIONAL — the V1.0 gauntlet unchanged (conflict, redundancy,
    alias-collision, dimensional verification) + shadow probation.
  MEMORY.fact — cross-observation consistency (identical canonical
    value in >= K_MEM independent observations, zero disagreement),
    unit/dimension validity against the pack, no conflict with any
    derivable or pack value, then shadow probation (a wrong constant
    must show as wrong-fire/lost coverage).
  TEXT.qa — >= K_TXT independent escalations of the same normalized
    question with normalized-agreeing answers, topic tag attached,
    never overrides a FUNCTIONAL path (deterministic computation
    always outranks text recall), staleness field in the
    certificate.
Probation cadence and N=3/2-reset lifecycle carry over for all
classes.

## 3. W3 — V1.1 generators (pre-registered, committed pre-data)

  G1 residual stream v2: pool from the v0.11-recipe + OOF generators
     with fresh seeds, filtered by the W1-FIXED engine (the new
     frontier); splits val 1,000 / traffic 5,000 / sealed 500.
  G2 varied-topic commercial stream: 25,000 queries in the NATURAL
     mix (not residual-only) across mechanics, electrical,
     thermodynamics, finance, maths-style dimensionless items, plus
     two new families exercising the new reflex classes:
     fact-recall items (standard constants omitted from the query —
     answerable only via MEMORY.fact reflexes once acquired) and
     definition/lookup items with fixed ground-truth text (TEXT.qa).
     Family weights frozen in the plan; every item ground-truthed.
  G3 sealed finals for the commercial sim: 600 mixed (same weights,
     fresh seeds) + reuse of V1.1 sem/adv integrity finals recipe
     (fresh seeds).

## 4. W4 — Ablation re-run (same harness, new frontier)

Arms on G1, identical replay, ONLY producers differ; the ≤2% gate
(target 0) applies to every arm:
  B0 fixed-engine floor · B1 breeder · B2 miner llama-8B
  (pre-registered primary, judged in the ladder)
  Bridge scale replications (reported alongside, never substituted):
  B2-haiku · B2-sonnet · B2-opus — mining via the deferred-replay
  bridge: pass 1 enqueues, Agent-tool servicing (matching model,
  anti-fabrication instructions, split-file protocol for large
  batches), replay until 0 pending. Miner budget 500 calls/arm,
  every-10th-escalation sampling, unchanged.
Also carried: typed producers run in all mining arms (MEMORY/TEXT
candidates can arise from residual traffic where applicable).

## 5. W5 — Commercial-scale simulation (the efficiency question)

One long run on G2 (25,000 varied-topic queries) with the full
product configuration: W1-fixed engine + best-scale bridge miner
(sonnet, budget 300) + typed producers + gauntlet. Escalations are
COUNTED AND PRICED, not executed (the commercial model): local-LLM
J/query at the measured 1,910 J (residual mix) and API tokens at
list rates; engine-side energy from a metered 500-item sample
(exclusive). Checkpoints every 2,500: coverage, wrong-fire,
escalation rate, ACTIVE reflexes by class, cumulative cost.
Deliverables: the commercial curve (does coverage grow and cost/query
fall over a long varied workload?), workload projection at 10k/100k/
1M q/day, and the reflex-class breakdown of every acquired reflex.

## 6. Bridge protocol (W4/W5 API mining)

results/bridge_v11/<model>/req_*.json — enqueue on miss; servicing
via Agent tool with the matching model (haiku→haiku agents,
sonnet→sonnet, opus→opus), batches ≤40 requests/agent, responses
resp_<key>.json, no-stub verification before replay; replay passes
until 0 pending. All servicing agents receive anti-fabrication
instructions (answer ONLY from the prompt; JSON only). Calls/tokens
accounting from the bridge records.

## 7. V1_1_PLAN frozen parameters

K_MEM = 3 independent consistent observations · K_TXT = 3 ·
probation N=3 / 2 resets (unchanged) · miner budget 500 (ablation) /
300 (sim) · shadow pool i%7==3 (unchanged) · gate ≤2% target 0 ·
G2 family weights: mechanics .22, electrical .18, thermo .14,
finance .18, maths .10, fact-recall .10, definition .08 ·
seeds: G1 pool 8555/8556, shuffle 8557; G2 9555; finals 9666/9777 ·
PARITY-PLUS bounds as §1 · commercial metered sample n=500.

## 8. Hypotheses (frozen)

  J1 W1 fixes lift the V1.0 sealed residual by ≥15pp at wrong-fire 0
     (the anatomy said engine-layer gaps dominate). PREDICT pass.
  J2 Post-fix residual (G1) is harder for miners: B2-scale lifts
     shrink vs V1.0 unless MEMORY/TEXT classes open new ground.
     PREDICT uncertain — the interesting number.
  J3 Miner scale monotonicity extends to Opus (B2-opus ≥ B2-sonnet
     lift). PREDICT uncertain.
  J4 MEMORY.fact reflexes make fact-recall items answerable at
     wrong-fire 0 (G2 families). PREDICT pass.
  J5 TEXT.qa reflexes serve repeated definitions at wrong-fire 0 and
     never displace a FUNCTIONAL path. PREDICT pass.
  J6 Commercial sim: cost/query falls monotonically over 25k as
     acquisition + coverage compound; wrong-fire stays 0.000
     end-to-end. PREDICT pass.
  J7 Zero wrong-fire in every gated arm and the sim (the invariant).
     PREDICT pass.

## 9. Outcome ladder (frozen; priority F > D > C > B > A)

  A  J1 + J7 + (J4 & J5) + J6 — the typed engine grows coverage and
     commercial efficiency at zero safety cost.
  B  J1 + J7, but typed classes underdeliver (J4 or J5 fails):
     engine-layer fixes carry the version; typed acquisition returns
     redesigned.
  C  J1 fails the 15pp bar but J7 holds: fixes underperform the
     anatomy's promise; report per-fix attribution.
  D  ANY gated arm or the sim breaches the 2% gate — safety
     regression outranks everything.
  F  PARITY-PLUS violated (a regression or wrong-fire on the arc
     battery): the fixes broke the engine; nothing else counts.

## 10. Deliverables

Everything in §0.4 + per-fix attribution table + reflex-class census
+ the commercial curve + bridge servicing records. Questions the
report must answer: per-fix lift; what each miner scale adds at the
new frontier; the full list of MEMORY/TEXT reflexes acquired with
their gates' evidence; the commercial cost curve and its asymptote;
what still escalates after everything, and why.
