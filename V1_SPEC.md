# V1.0 SPEC — REFLEX ENGINE
## Integrated prototype (plugs into any LLM) + the acquisition ablation A0–A3

Status: FROZEN 2026-08-28 — issued by the user ("ok freeze this and
start v1"). This document is the authority for V1.0. Sections 10–11 are
frozen now, before any sealed evaluation, and never change after data.
Numeric parameters left open here are frozen in V1_PLAN.md at plan commit.

---

## 0. Non-negotiables (arc discipline, unchanged)

0.1 Before ANY work: verify v0.1–v0.11 tags, clean prior trees, every
    `-frozen` snapshot byte-identical; record in the provenance manifest.
    Never modify any prior repo or snapshot.
0.2 New repo: `Downloads/reflex-engine` (fresh git; a distillation, not a
    merge — prior code copied in file-by-file with origin recorded in
    file headers).
0.3 Plan freeze: `V1_PLAN.md` (outcome ladder + gates + predictions)
    committed and hash-recorded BEFORE generating any sealed set or
    starting any experiment arm. No tuning on sealed sets, ever.
0.4 Preserve-supersede-rerun for bugs found after first results.
    `invention_log_v1_0.md` (H1–H8), `bug_audit_v1_0.md`. Report
    negatives prominently.
0.5 Energy: V0.5 PowerMeter protocol (ambient-calibrated, cache-cold,
    metered arms exclusive). API models: calls/tokens only, never on the
    joule axis. Local model: llama3.1:8b (ollama digest 46e0c10c039e).
0.6 Finalize: tag `v1.0-final`, snapshot `reflex-engine-frozen`
    byte-identical, final report + PDF + web artifact, ledger update,
    `python run_v1_0_experiment.py` (hash-gated, resumable).
0.7 Discipline split: prototype demos earn the phrase "works on demo
    traffic" ONLY. Headline claims come exclusively from the sealed
    ablation (Section 8) and the parity battery (Section 7).

## 1. Purpose

Build ONE system that (a) integrates every surviving layer of the
V0.1–V0.11 arc behind a single gateway, (b) plugs into any LLM through
adapters, (c) generates reflexes from live escalations, and (d) certifies
them before they can ever answer. Then answer the acquisition question
the arc left open, as a four-arm ablation:

  Which acquisition channel actually grows certified coverage —
  the deterministic breeder (A1), the LLM miner (A2), both (A3) —
  against a frozen-pack control (A0), at what cost, under the
  unchanged ≤2% wrong-fire gate?

## 2. Deferred (explicitly NOT in V1.0)

Domain-pack onboarding study (human-vs-LLM authored packs from a brief)
and provenance-certified knowledge reflexes: both move to V1.1, running
ON this prototype. Grammar/structural parser learning and escalation-
triage economics: V1.2+. Real-traffic pilot: whenever a production log
exists. Any capability work not in this spec is a violation.

## 3. Architecture contract

Public surface (the product shape):

    gateway.ask(query) -> Answer(value, status, certificate, cost)
        status ∈ CERTIFIED_REFLEX | LLM_ESCALATED | ABSTAINED
    certificate = machine-readable provenance: which reflex/path/facts/
        checks fired, or which LLM answered and why it was escalated.

Modules (port origin in parentheses; every cross-layer call typed; the
ONLY path into execution is CERTIFIED state — V0.11 invariants carried
verbatim as J1–J8, machine-checked):

  gateway.py      public API + CLI; optional localhost HTTP front.
  adapters/       uniform complete() + call/token metering:
                  ollama.py (llama3.1:8b), anthropic.py (haiku/sonnet),
                  openai_compat.py (generic). Engine is model-agnostic
                  (V0.10 manager-independence result).
  recognition.py  hashed n-gram router + OOD gate + error predictor
                  (V0.2 lineage). NO embedder on the hot path.
  semstate.py,
  entity.py       fact store: 6-field identity keys, entity graph,
                  temporal scopes, statuses ASSERTED..CERTIFIED (V0.11).
  parse.py        parser + unit/dimension-driven naming (V0.10 worker +
                  V0.11 patches, merged properly for the first time).
  integrity.py    certification: DERIVATION strategy = v0.11's 12 checks
                  verbatim; fact-local quarantine + dependency closure;
                  PROVENANCE strategy = stub interface only (V1.1).
  worker.py,
  planner.py,
  paths.py        deterministic worker, goal-regression planner, path
                  cache w/ paraphrase+revalued reuse (V0.10; includes
                  the FULL B3 conversion table; completeness of unit
                  tables machine-checked at pack load).
  escalate.py     manager protocol, SQR for out-of-family, resolver
                  proposals ALWAYS behind the deterministic validator —
                  the LLM never writes certified state (V0.9/V0.11 I4).
  packs/          declarative versioned pack schema + loader; physics
                  extracted from engine code as the first pack; packs
                  never contain engine code. Authorship metadata per
                  entry (HUMAN | BREEDER | MINER model+prompt+tokens).
  acquire.py      the acquisition subsystem (Section 5).
  meter.py        PowerMeter port + token accounting.
  trace.py        certificates on every answer.
  tests/          invariant tests + the frozen parity battery (Sec. 7).
  demo.py         live loop: query stream in, running tally of
                  reflex-answered vs escalated vs abstained, tokens and
                  joules saved, newly minted reflexes with certificates.

Deleted (with the result that killed each): MiniLM embedder (V0.2:
hashed ≈ minilm at 1/200,000 cost; 99.9% of reflex FLOPs); neural
reflex nodes (superseded by compiled deterministic paths); raw-value
interfaces I0–I3 (V0.8: 36–39% vs 95.4%); distance-threshold gating
(V0.1). NOTE: token-window breeding is NOT deleted this time — it is
arm A1 of the ablation, retained precisely so its twice-falsified lift
is retested inside the integrated engine under identical conditions.

## 4. Pack contract (condensed)

A pack is a declarative, versioned, frozen, diffable artifact: lexicon;
entity/concept ontology; units/dimensions/FULL conversion tables;
templates/grammar fragments; worker capability definitions; adversarial
seed classes; manifest (version, hash, per-entry authorship, gate
certificates). Rationale (recorded so the decision is auditable): the
integrity engine certifies only inspectable declarative content, never
latent LLM knowledge (I4's proposer/validator split made durable);
artifacts are auditable and diffable (B3 was caught against V0.9's
table); gates only protect content that passes through them into a
frozen artifact (V0.6); the pack is the unit of ownership, rollback,
and LLM-free edge deployment; LLM-in-the-hot-path reimports the cost
the arc removed.

## 5. Acquisition subsystem: two producers, ONE gauntlet

Both channels emit candidates into the SAME typed candidate interface
and the SAME certification pipeline. The arms of the ablation differ
ONLY in which producers are enabled.

5.1 Producers.
    BREEDER (A1 lineage: V0.6/V0.10/V0.11): deterministic induction
    over traffic logs — token-window and structural-alignment patterns.
    Near-zero cost. Prior measured result: pollution-proof filtering,
    zero held-out lift (H7 falsified twice) — retained for retest.
    MINER (new, the H3 bet): on escalation, prompts the SAME plugged-in
    LLM to emit STRUCTURED candidates as JSON, never free text:
    lexicon entries, concept definitions, unit conversions, template
    fragments. Deep-layer content — the layer where all real coverage
    gains in the arc actually came from (V0.11 mechanism finding).
    Cost metered per candidate (calls/tokens).
5.2 The gauntlet (shared, ported, proven): deterministic gate battery
    (V0.6 lineage: type/dimension consistency, conflict-against-pack,
    unit-table closure, syntax) → shadow evaluation → PROBATION status
    in the pack → promotion to ACTIVE only after N consistent shadow
    confirmations (N frozen in V1_PLAN.md). Nothing answers a live
    query until ACTIVE. Rejected candidates are logged, never deleted.
5.3 Shadow-eval integrity rule: shadow sets are drawn from held-back
    REAL traffic (dev split) only — never from miner-generated
    paraphrases. The LLM must not grade its own homework.
5.4 Every candidate carries authorship metadata; the pack remains a
    fully auditable artifact at all times.

## 6. Build phases (each ends at a working checkpoint)

  P1 SKELETON   gateway + adapters; everything escalates; end-to-end
                from hour one. Checkpoint: ask() answers via all three
                adapters with metering.
  P2 THE PORT   all Section-3 layers; physics pack extracted from
                engine code; parity battery GREEN (Section 7).
                Checkpoint: tag `v1.0-parity`. Engine freezes here for
                all experiment arms.
  P3 ACQUISITION breeder + miner behind the one candidate interface;
                gauntlet; probation lifecycle. Checkpoint: the
                LOOP-CLOSE demo — one reflex mined from a live LLM
                escalation, gate-certified, promoted, and answering a
                paraphrased repeat deterministically with a full
                certificate.
  P4 DEMO+EXP   demo.py; then the ablation (Section 8) as the first
                experiment ON the prototype.

Prototype acceptance (deliberately narrow): parity battery green + one
loop-close demonstration. Everything beyond is experiment phase.

## 7. E0 — Parity battery (the gate; everything stops on failure)

Port ALL sealed suites V0.5–V0.11 unchanged (byte-copied, hashes
recorded): cplx10 regression 196, sem11 76, adv11 122, parse11 1000 +
oof 240, v0.8 recognition, v0.9 EXT, inject/corruption suites. The V1
engine with the ported physics pack must reproduce:
  - wrong-execution 0.000 on every sealed suite (exact)
  - cplx10 196/196 at zero LLM calls (exact)
  - parse11 sealed ≥ 84.2%−1.0pp; oof ≥ 68.3%−1.5pp (allowance ONLY
    for pack-schema normalization; every regressed item individually
    diffed and explained; unexplained regressions = parity failure)
  - J/query ≤ 0.53 × 1.15 on the regression set (meter variance)
  - invariants J1–J8: 8/8
Parity failure = OUTCOME F; nothing else may be claimed.

## 8. EXP-ACQ — the acquisition ablation (the V1.0 experiment)

8.1 Arms (identical frozen engine, identical gauntlet, identical
    recorded traffic; the ONLY difference is enabled producers):
      A0  frozen pack, no acquisition (attribution baseline; also
          controls for path-cache warming)
      A1  BREEDER only
      A2  MINER only
      A3  BREEDER + MINER (complementarity test)
8.2 Traffic. Primary stream: the ESCALATED RESIDUAL — queries of the
    kind the parity-frozen engine cannot cover (drawn from the
    uncovered parse11 quadrants / OOF families and fresh generation
    from those families), i.e. the 15.8% that is 99.7% of residual
    energy. One recorded stream (~5k queries, size frozen in
    V1_PLAN.md), replayed identically to every arm.
    Secondary (exploratory, NOT outcome-gating): bootstrap a thin new
    domain from a near-empty pack on a small stream; report
    qualitatively.
8.3 Measurement (V0.11 recipe): frozen held-out validation set probed
    at checkpoints → a learning curve per arm; sealed suites (semantic
    + adversarial + parser, generated after plan freeze from
    pre-registered generators) for final numbers; per-quadrant
    breakdown.
8.4 The gate applies to EVERY arm: wrong-fire ≤2% (target 0.000),
    gate_rate defined exactly as V0.11 analyze (wrong answers on
    answer-expected + any answer on abstain-expected, over n). An arm
    that lifts coverage by polluting the pack LOSES regardless of lift.
8.5 Cost axis (mandatory, or the comparison is rigged): per-arm
    acquisition cost (breeder ≈ free; miner tokens priced at API
    rates + metered joules for local), lift-per-cost, and BREAK-EVEN:
    reuses N after which a minted reflex repays its minting cost at
    719 J/query avoided. Report N.
8.6 Per-arm bookkeeping: candidates proposed / gate-rejected /
    probation-failed / activated; activated-reflex utilization on
    held-out; worst rejected candidates shown in the report.

## 9. Controls, statistics, energy

  K1 v0.11 C10 champion via compat shim (own process) on ported suites
     — prior-generation baseline for parity context.
  K2 V1 engine, integrity OFF — what certification buys post-integration.
  K3 pure LLM on the ablation's sealed suites (local metered;
     haiku/sonnet calls-only).
  K4 MINER with gauntlet DISABLED (activation without certification),
     dev + sealed — measures pollution: what the gates buy (expected
     to be the scary chart; pre-registered H5).
McNemar paired across arms on shared sealed items; bootstrap 95% CIs
(fixed seed); learning curves with exact counts. Energy per Section
0.5; workload projection updated with post-acquisition coverage mix
(LLM_JQ = 719.0 carried from V0.10).

## 10. Hypotheses + pre-registered predictions (frozen at plan commit)

  H1 Integration parity holds (Section 7).                PREDICT: pass
  H2 A1 ≈ A0 on held-out lift — the twice-falsified breeder stays
     falsified inside the integrated engine.              PREDICT: ≈0 lift
     (If A1 > A0 materially, the surprise itself demands a mechanism
     autopsy before it is reported as a win.)
  H3 A2 > A0: LLM-mined deep-layer candidates survive gates AND lift
     held-out coverage. THE OPEN BET.                     PREDICT: uncertain
  H4 A3 ≥ A2, with any surplus explained by one named interaction:
     miner-expanded lexicon/templates create new surface regularities
     the breeder can then specialize.                     PREDICT: small +
  H5 K4 (no gates) wrong-fire exceeds gated A2 by >5pp — gates are
     necessary, not decorative, for LLM authorship.       PREDICT: pass
  H6 Wrong-fire 0.000 in ALL gated arms (shared gauntlet). PREDICT: pass
  H7 Miner break-even N is small enough to matter commercially
     (pre-register threshold: N ≤ 50 reuses).             PREDICT: pass
  H8 Loop-close: at least one mined reflex answers a held-out
     paraphrase deterministically with a full certificate. PREDICT: pass

## 11. Outcome ladder (pre-registered; the ONLY headline vocabulary)

  A  Parity + H3 confirmed + H6 (all arms clean) + H7: the engine
     grows certified coverage from any plugged-in LLM at commercial
     cost. (First new capability result since V0.11.)
  B  Parity + H3 confirmed but H7 fails (lift is real, too expensive):
     acquisition works; economics needs the V1.2 triage work.
  C  Parity + H3 falsified (miner candidates don't survive gates or
     don't lift): the prototype stands as an integrated certified
     engine; acquisition returns redesigned. A1/A3 results reported
     with equal prominence either way.
  D  Parity + any gated arm breaches the 2% gate: the gauntlet does
     not transfer to live acquisition — a safety regression that
     outranks all coverage claims.
  F  Parity fails: integration not achieved; nothing else counts.
  Priority on mixed results: F > D > C > B > A.

## 12. Deliverables

`V1_PLAN.md` (frozen pre-seal) · reflex-engine package + physics pack ·
frozen parity battery with hashes · recorded traffic stream + replay
harness · `results/v1.0_final_report.md` (+ PDF + artifact) ·
hypothesis ledger V0.1→V1.0 · invention/bug logs · loop-close demo
recording (transcript) · provenance manifest · tag `v1.0-final` ·
snapshot `reflex-engine-frozen` · `python run_v1_0_experiment.py`.

## 13. Questions the final report must answer

 1. Did every arc headline survive integration? (item-level diffs)
 2. What was hiding in engine code that pack extraction exposed?
 3. The four learning curves, on one plot, with the gate line.
 4. What did the miner propose, what fraction survived the gauntlet,
    and what did the rejects look like? (worst examples shown)
 5. Did the breeder stay falsified inside the new engine (H2)?
 6. Is A3's surplus over A2 real, and is the named interaction the
    mechanism (H4)?
 7. What did K4 serve without gates? (the pollution chart)
 8. Break-even N per minted reflex, and the updated workload
    projection with post-acquisition coverage.
 9. Did any gated arm ever wrong-fire, even once? Show the item(s).
10. The loop-close transcript: escalation → candidate → certificate →
    deterministic answer to a paraphrase.
11. What died in this spec that the data says should return?
12. The one sentence a customer may be told about what this engine
    guarantees, supported only by sealed measurements.
