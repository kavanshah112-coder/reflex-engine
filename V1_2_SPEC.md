# V1.2 SPEC — SAFETY CERTIFICATION + REAL-LANGUAGE COVERAGE + ENERGY

Status: FROZEN 2026-08-29, issued by the user ("go with the
recommendation given and generate new 1.2 spec then start
experiment"), with the user's addition: a THEORY track of real
theoretical/conceptual queries in the corpus. Supersedes
V1_2_SPEC_DRAFT.md (kept for provenance). All five draft open
questions are resolved below. Arc discipline unchanged (V1_1_SPEC
§0); V1.1 is preserved at tag v1.1-final + snapshot
reflex-engine-v1.1-frozen and is RE-VERIFIED before any V1.2 work.

## Resolved parameters (frozen)

  CORPUS (W2): FULL track = GSM8K test + ASDiv mix, n=1,000
    (unfiltered honest floor). UNITS track = units-bearing subset of
    the same corpora, n≥300 (deterministic filter: item text
    contains a unit token mappable to the pack's kind space).
    THEORY track (user addition) = 300 real human-written
    theoretical/conceptual science questions from SciQ (fallback if
    unavailable: a hand-frozen, hashed set of 100 textbook-style
    conceptual questions, provenance recorded) — graded against the
    dataset's answer key; the engine is EXPECTED to abstain (no
    derivation path); the tracks test (a) the safety boundary on
    conceptual language and (b) whether TEXT.qa acquisition can
    serve repeated theory questions from bridge answers at K=3.
    A user-supplied real query log remains an open invitation; none
    exists at freeze. All corpus files downloaded once, SHA-256
    hashed, licenses recorded, then FROZEN; splits: traffic vs
    sealed disjoint [sealed: FULL 300, UNITS 120, THEORY 100;
    traffic: the remainder].
  SEED SWEEP (W1.3): sem + adv + NEW reference-trap family
    (unresolved refs, ordinals first..tenth+beyond-vocabulary
    forms, multi-entity hypernyms) x 20 seeds each; parser suites
    x 5 seeds. Certification metric: wrong-fire across the ENTIRE
    sweep (target 0.000; ≤2% floor).
  ENERGY (W3): blended target certified-serve < 1.0 J/query on the
    g2 commercial mix (V0.5 protocol, 3 independent metered runs,
    variance reported); per-class breakdown (det/memory/text/
    abstain) reported WITHOUT bars; cold-start measured once; idle
    out of scope this version.
  BRIDGE (W2.3): sonnet primary miner/answerer, budget 300 calls;
    opus replication arm, budget 300. No API keys — deferred-replay
    bridge with matching-model agent servicing only.
  CERTIFICATE (W1.4): yes — `certify.py` regenerates the machine
    safety case AND emits a one-page external certificate summary
    (claims, complete wrong-fire history, re-verification command).

## W1 — Safety certification

W1.1 Ambiguity-by-default guard: with ≥2 entities holding facts of
  the to-be-consumed kinds and an absent/unresolved ask reference,
  the engine abstains (hazard, competing bindings in the
  certificate); never a GLOBAL first-facts solve. PARITY-PLUS gated;
  legitimately-global battery items itemized.
W1.2 Vocabulary-completeness audit: machine test that every
  resolution table is reachable by its gate (ORDINALS/COMPARATIVES/
  cue lexicons/unit tables/pack lexicon); every gap fixed under
  PARITY-PLUS and logged; the audit joins the permanent test suite.
W1.3 Seed-sweep certification per the frozen parameters.
W1.4 `certify.py`: invariants J1–J8, audit, full parity battery
  results, sweep ledger, complete wrong-fire history (B2 included),
  one-page external certificate. Deterministic regeneration.

## W2 — Real-language coverage

W2.1 Corpus acquisition per frozen parameters (download once, hash,
  freeze; licenses recorded in the provenance manifest).
W2.2 Zero-shot: frozen v1.2 engine (post-W1, post-W3 — the shipping
  engine) on all three sealed tracks, once: coverage / abstention /
  wrong-fire. Pre-registered honesty: FULL and THEORY coverage may
  be near zero; the claim under test is that the safety boundary
  transfers — abstain, don't guess.
W2.3 Acquisition loop on the real-language traffic splits (typed
  producers + gauntlet + bridge per frozen budgets), validation
  probes, sealed finals once. McNemar vs the frozen floor per track.

## W3 — Energy

W3.1 Phase/class profile of the 1.93 J figure (measured, before any
  optimization).
W3.2 Profile-directed optimizations (parse/state reuse, planner
  memoization across retry targets, early-exit, out-of-universe
  abstention fast-path), each PARITY-PLUS gated.
W3.3 Evidence pack: 3 metered runs + variance, per-class J/query,
  cold-start, refreshed commercial model incl. real-language mix and
  API token accounting.

## Hypotheses (FROZEN)

  K1 B2-class guard: wrong-fire 0.000 across the full seed sweep,
     PARITY-PLUS held.                                PREDICT pass
  K2 Vocabulary audit closes every table/gate mismatch (count
     reported; zero found would itself be news).      PREDICT ≥1 found
  K3 Real-language zero-shot: gate holds on ALL THREE tracks
     (wrong-fire ≤2%, target 0), abstention carrying the safety.
                                                      PREDICT uncertain — THE test
  K4 Coverage numbers on FULL/UNITS/THEORY reported without bars
     (measurement-first).                             —
  K5 Typed acquisition lifts UNITS-track coverage vs the frozen
     floor (McNemar significant) at wrong-fire 0; THEORY-track
     TEXT.qa serves reported.                         PREDICT uncertain
  K6 Certified-serve < 1.0 J/query post-optimization; evidence pack
     delivered.                                       PREDICT pass
  K7 certify.py regenerates the safety case + certificate
     deterministically.                               PREDICT pass

## Outcome ladder (FROZEN; priority F > D > C > B > A)

  A  K1 + K3 + K6 + K7 and K5 significant on UNITS: certified-safe,
     cheaper, learning on real human language.
  B  K1 + K3 + K6 + K7, K5 null: safety + economics transfer to real
     language; acquisition remains in-universe-bound (the honest
     negative).
  C  K3 holds, K6 misses: safety transfers; economics continues.
  D  Any sealed suite or sweep above the 2% gate.
  F  PARITY-PLUS broken.

## Deliverables

certify.py + machine case + one-page certificate · frozen corpora w/
hashes+licenses · zero-shot + loop results w/ sealed finals · energy
evidence pack · logs (invention/bug/violation) · v1.2-final tag +
snapshot (no .env) + report + PDF + artifact + memory ·
run_v1_2_experiment.py.
