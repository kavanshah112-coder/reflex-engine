# V1_PLAN — frozen pre-registration for V1.0 (REFLEX ENGINE)

FROZEN at first commit of this repo, 2026-08-28, before any sealed set
exists and before any experiment arm runs. Authority: V1_SPEC.md
(frozen same date). Nothing in this file changes after data. Sealed-set
GENERATOR CODE does not exist yet; it must be committed (hash recorded
in the provenance manifest) BEFORE any sealed item is generated, and no
sealed set may be regenerated after first evaluation.

## 1. Frozen numeric parameters

- PROBATION: a candidate is promoted to ACTIVE after N_probation = 3
  consecutive shadow confirmations with zero shadow wrong-fire; any
  shadow failure resets the count; 2 resets = permanent rejection.
- TRAFFIC (EXP-ACQ primary stream): 5,000 recorded queries drawn from
  the escalated-residual families (uncovered parse11 quadrants + OOF
  families + fresh generation from those family definitions), recorded
  ONCE and replayed identically to every arm.
- CHECKPOINTS: after queries 100 / 250 / 500 / 1,000 / 2,500 / 5,000.
- HELD-OUT VALIDATION: n = 1,000, generated and frozen BEFORE the
  traffic stream is recorded; probed at every checkpoint; never used
  for tuning, shadow evaluation, or candidate selection.
- SHADOW SETS: drawn only from a held-back dev split of REAL recorded
  traffic (never miner-generated paraphrases).
- SEALED FINALS: semantic ~80 + adversarial ~120 + parser ~500 per the
  V0.11 recipe, generated after plan freeze from the pre-registered
  generators, evaluated once per arm at the end.
- GATE (all arms): wrong-fire ≤ 2.0%, target 0.000. gate_rate =
  (wrong answers on answer-expected items + any answer on
  abstain-expected items) / n  — exactly V0.11 analyze11.
- H5 pollution margin: K4 (no gates) wrong-fire must exceed gated A2
  by > 5.0pp for H5 to be confirmed.
- H7 break-even threshold: minted-reflex break-even N ≤ 50 reuses,
  priced at 719 J/query avoided (V0.10 measured pure-LLM baseline)
  and API tokens at published rates for API-authored candidates.
- PARITY TOLERANCES (E0): wrong-execution 0.000 exact on every ported
  sealed suite; cplx10 196/196 exact at zero LLM calls; parse11 sealed
  ≥ 83.2% (84.2 − 1.0pp) and OOF ≥ 66.8% (68.3 − 1.5pp) with every
  regressed item individually diffed and explained (unexplained ⇒
  parity failure); J/query ≤ 0.61 (0.53 × 1.15) on the regression set;
  invariants J1–J8 8/8.
- ENERGY: V0.5 PowerMeter protocol; calibrate_ambient(20); cache-cold;
  metered arms run exclusively; LLM_JQ = 719.0 for workload math; API
  models never on the joule axis.
- STATS: McNemar exact (two-sided) on shared sealed items; bootstrap
  95% CI, n=10,000 resamples, seed=1 (this repo's fixed seed).

## 2. Arms (identical frozen engine at tag v1.0-parity; identical
gauntlet; identical replayed stream; ONLY enabled producers differ)

  A0 frozen pack (no acquisition)      — attribution baseline
  A1 BREEDER only (deterministic induction, V0.6/V0.10/V0.11 lineage)
  A2 MINER only (LLM-authored deep-layer candidates)
  A3 BREEDER + MINER

Controls: K1 v0.11-C10 champion via compat shim (own process, ported
suites); K2 V1 engine integrity OFF; K3 pure LLM on the ablation's
sealed suites (local metered; haiku/sonnet calls-only); K4 MINER with
gauntlet DISABLED (dev + sealed).

## 3. Hypotheses and predictions (frozen; from V1_SPEC §10)

  H1 parity holds ............................ PREDICT pass
  H2 A1 ≈ A0 held-out lift (breeder stays falsified) . PREDICT ≈0 lift
     (if A1 > A0 materially: mechanism autopsy REQUIRED before any
     reporting of it as a win)
  H3 A2 > A0 (miner lifts certified coverage) . PREDICT uncertain (THE BET)
  H4 A3 ≥ A2; surplus attributable to the named interaction
     (miner-expanded surface regularities → breeder specialization)
     .......................................... PREDICT small positive
  H5 K4 wrong-fire > gated A2 + 5pp ........... PREDICT pass
  H6 wrong-fire 0.000 in ALL gated arms ....... PREDICT pass
  H7 break-even N ≤ 50 reuses ................. PREDICT pass
  H8 loop-close demonstrated .................. PREDICT pass

## 4. Outcome ladder (frozen; the ONLY headline vocabulary)

  A  parity + H3 + H6 + H7      — engine grows certified coverage from
                                  any plugged-in LLM at commercial cost
  B  parity + H3, H7 fails      — acquisition works, economics doesn't yet
  C  parity + H3 falsified      — integrated certified engine stands;
                                  acquisition returns redesigned (A1/A3
                                  reported with equal prominence)
  D  parity + ANY gated arm > 2% gate — safety regression; outranks all
                                  coverage claims
  F  parity fails               — nothing else may be claimed
  Priority on mixed results: F > D > C > B > A.

## 5. Discipline reminders binding this run

Verify V0.1–V0.11 preservation before work (done at this commit; see
provenance_manifest.json). Engine freezes at tag v1.0-parity for all
arms. Preserve-supersede-rerun for any bug after first results. Shadow
sets never from miner paraphrases. Prototype demos are "demo traffic"
only; headlines come from sealed runs. Report negatives prominently.
