# Reflex Engine — Safety Certificate (one page)

**Engine:** reflex-engine, V1.2 line · **Generated:** 2026-08-29 12:15:46 · **Verdict: CERTIFIED**

## What this engine guarantees
1. **It answers only what it can certify.** Every answer carries a
   machine-readable certificate (derivation facts, integrity checks,
   reflex provenance). Everything else is an explicit abstention or a
   labeled escalation — never a guess.
2. **Detected hazards abstain.** Contradictions, ambiguous bindings,
   and unresolved references over multi-entity states return the
   hazard, not an answer.
3. **Acquired knowledge passes typed gates** (dimensional
   verification, consistency quorums, shadow probation) before it can
   ever answer, and every acquired reflex records its authorship.

## The evidence (machine-regenerable: `python certify.py --full`)
- Invariants J1–J8: machine-checked pass.
- Vocabulary-completeness audit: all resolution tables reachable by
  their gates (2 historical gaps found and closed; documented
  exceptions listed with reasons).
- Full sealed battery (V0.5–V1.1 lineage, 1,634+ items): wrong-fire
  0.000, zero regressions vs the certified champion.
- Seed-sweep: 10160 adversarial/trap items across
  65 independent generation seeds: wrong-fire 0.000.

## The complete wrong-fire history (nothing excused)
One event in the engine line's sealed history: a latent
ordinal-vocabulary gap produced one mis-bound answer (1/76, 1.3%) on
a fresh-seed suite in V1.1. It was found by the sealed evaluation,
fixed, re-verified, and its entire CLASS is now closed by an
ambiguity-by-default guard plus a permanent vocabulary audit and the
65-seed sweep above. Lesson institutionalized: seed luck is not
coverage — only vocabulary-complete gates are.

## How to re-verify
`python certify.py --full` regenerates every check above from source
on the frozen artifacts. `python run_v1_2_experiment.py` reproduces
the version's numbers.
