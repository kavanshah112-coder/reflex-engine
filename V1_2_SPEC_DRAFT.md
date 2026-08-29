# V1.2 SPEC — SAFETY CERTIFICATION + REAL-LANGUAGE COVERAGE + ENERGY
## (DRAFT for review — NOT frozen; no work begins until issued)

Status: DRAFT authored 2026-08-29 from the user directive: safety
certification · real-language coverage · energy measurement ·
retry-chain cost reduction (1.93 → sub-1 J/query) · out-of-universe
truth ("the generator universe is closed; the next coverage number
must come from real user language"). Numeric parameters marked
[PLAN] freeze at plan commit. Arc discipline carries forward
unchanged (§0 of V1_1_SPEC: priors untouchable, _arc byte-frozen,
pre-registration before data, preserve-supersede-rerun, negatives
prominent, PDF+artifact+snapshot at finalization).

---

## W1 — SAFETY CERTIFICATION

The B2 lesson ("seed luck is not coverage — only vocabulary-complete
gates are") becomes a workstream with three parts and a deliverable
artifact.

**W1.1 Close the B2 class, not the instance.** Ambiguity-by-default
guard at the engine layer: when the state holds ≥2 entities carrying
facts of the kinds a solve would consume, and the ask's entity
reference is ABSENT or UNRESOLVED, the engine abstains as
`target_entity_ambiguous` (a hazard, surfaced by the gateway as
ABSTAINED with the competing bindings in the certificate) — it never
falls through to a GLOBAL first-facts solve. Design constraints:
  - fires only when competing per-entity bindings actually exist for
    the consumed kinds (single-entity and genuinely-global states are
    untouched);
  - acceptance under PARITY-PLUS (zero regressions on the full
    battery) — any battery item that legitimately global-solves with
    multiple incidental entities must still pass, itemized.

**W1.2 Vocabulary-completeness audit (the anti-seed-luck test).**
A static, machine-checked consistency battery: every resolution
table must be fully reachable by the gate/regex that feeds it —
ORDINALS vs the reference regex (the B2 gap, now a permanent test),
COMPARATIVES vs the comparative alternation, cue lexicons vs their
patterns, unit tables vs capture classes, pack lexicon vs the
worker's matchers. Every found gap is fixed under PARITY-PLUS and
individually logged. The audit joins the test suite forever.

**W1.3 Seed-sweep certification.** Trap-class suites (sem/adv
recipes + a new unresolved-reference/beyond-fifth-ordinal trap
family) generated across [PLAN: ~20] independent seeds, evaluated
once each: the certification claim is wrong-fire across the whole
sweep, not one lucky seed. Target 0.000; the ≤2% gate is the floor.

**Deliverable: the Safety Certification Artifact** — a
machine-regenerable safety case (`python certify.py`): invariants
J1–J8, the vocabulary audit, the full parity battery, the seed-sweep
ledger, and the complete wrong-fire history with the B2 event and
its supersede trail. This is the auditable document the
commercialization story sells.

## W2 — REAL-LANGUAGE COVERAGE (out-of-universe truth)

The generator universe is closed; V1.2 measures the engine against
HUMAN-written problems for the first time.

**W2.1 Corpus.** Real, human-authored word-problem corpora with
ground-truth answers, downloaded once, hashed, frozen (candidates,
final choice at plan freeze: GSM8K test split, SVAMP, ASDiv — all
permissively licensed, all real human phrasing). Two pre-registered
tracks, both reported:
  - FULL track: an unfiltered slice [PLAN: n≈1,000] — the honest
    floor; many items lie entirely outside the engine's dimensional
    universe and SHOULD abstain.
  - UNITS track: the subset whose quantities/asks carry physical or
    monetary units mappable to the pack's kind space [PLAN: n≈300+]
    — the engine's design domain, where coverage is a fair question.
An optional third source: any real query log the user supplies.

**W2.2 Zero-shot measurement.** The frozen v1.1-final engine on both
tracks, once: coverage, abstention, and above all WRONG-FIRE. The
pre-registered expectation is honest: coverage will be LOW (possibly
single digits on FULL) — the claim under test is that the safety
boundary transfers to language the engine has never seen: it must
abstain, not guess.

**W2.3 The real-language acquisition loop.** The product
configuration (typed producers + gauntlet + bridge miner
[PLAN: sonnet primary, opus replication]) over a real-language
traffic split disjoint from the sealed slices; validation probes;
sealed real-language final evaluated once. The question V1.1 could
not ask: does typed acquisition lift coverage on REAL human phrasing
at wrong-fire zero? McNemar vs the frozen floor.

## W3 — ENERGY MEASUREMENT + RETRY-CHAIN COST

**W3.1 Profile first.** A per-phase cost breakdown of the 1.93
J/query commercial figure (parse, certify, primary solve, F3 retry
solves, memory retries, per serve-class det/memory/text/abstain) —
measured, not guessed, before optimizing.

**W3.2 Optimize the retry chain.** Candidate mechanisms (chosen by
the profile, all PARITY-PLUS-gated): parse/state reuse across retry
phases; planner-result memoization across alternative targets;
early-exit when no alternative target or applicable memory exists;
abstention fast-path for out-of-universe inputs (W2 makes this path
hot). Target [PLAN]: certified-serve cost < 1.0 J/query on the g2
commercial mix, re-metered under the V0.5 protocol.

**W3.3 Energy measurement as evidence, not a footnote.** Three
independent metered runs (variance reported); per-class J/query;
cold-start; the commercial workload model re-fit with the measured
numbers and the real-language mix; API-side token accounting for the
acquisition loop. The deliverable is an energy section that a
skeptical reviewer could re-run.

## W4 — Hypotheses (freeze at plan commit; drafts)

  K1 The B2-class guard yields wrong-fire 0.000 across the full
     seed-sweep, with PARITY-PLUS held.               PREDICT pass
  K2 The vocabulary audit finds and closes every table/gate mismatch
     (count reported; zero would itself be news).     PREDICT ≥1 found
  K3 Real-language zero-shot: the gate holds on FULL and UNITS
     tracks (wrong-fire ≤2%, target 0) with abstention doing the
     safety work.                                     PREDICT uncertain — THE test
  K4 Real-language coverage numbers reported WITHOUT a pre-set bar
     (measurement-first; bars on safety only).        —
  K5 Typed acquisition lifts UNITS-track coverage vs the frozen
     floor (McNemar significant) at wrong-fire 0.     PREDICT uncertain
  K6 Certified-serve cost < 1.0 J/query post-optimization, energy
     evidence pack delivered.                         PREDICT pass
  K7 `certify.py` regenerates the full safety case deterministically. PREDICT pass

## W5 — Outcome ladder (draft; freezes at plan commit)

  A  K1 + K3 + K6 + K7, and K5 shows significant real-language lift:
     certified-safe, cheaper, and learning on real human language.
  B  K1 + K3 + K6 + K7, K5 null: the safety and economics story
     stands on real language; acquisition remains in-universe-bound
     (reported as the version's honest negative).
  C  K3 holds but K6 misses the energy target: safety transfers,
     economics work continues.
  D  ANY wrong-fire above the 2% gate on any sealed suite or sweep —
     safety regression outranks everything.
  F  PARITY-PLUS broken by W1/W3 changes: nothing else counts.
  Priority F > D > C > B > A.

## Deliverables

Safety Certification Artifact (`certify.py` + its report) · frozen
real-language corpora with hashes and licenses recorded · zero-shot
+ acquisition-loop results with sealed finals · energy evidence pack
· per-fix and per-audit-finding logs · v1.2-final tag + snapshot +
report + PDF + artifact · `run_v1_2_experiment.py`.

## Open questions for review (decide before freeze)

1. Corpus selection and slice sizes (GSM8K/SVAMP/ASDiv mix; how much
   FULL vs UNITS; include a user-supplied log?).
2. Seed-sweep width (20 seeds proposed) and whether the sweep
   includes parser suites or trap suites only.
3. The energy target (sub-1.0 J/query proposed) and whether idle/
   cold-start accounting belongs in scope.
4. Bridge budget for the real-language acquisition loop (sonnet
   primary + opus replication proposed).
5. Whether "safety certification" should also produce an external-
   facing one-page certificate summary (the commercial artifact) in
   addition to the machine-checkable case.
