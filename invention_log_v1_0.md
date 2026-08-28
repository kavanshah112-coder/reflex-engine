# Invention log — V1.0 (REFLEX ENGINE)

Hypotheses frozen in V1_PLAN.md at c7079fa (2026-08-28), before any
sealed set existed. Final statuses:

**H1 — integration parity. CONFIRMED.** All five ported sealed suites
reproduce the v0.11 champion rows with ZERO item-level diffs, twice
(vendored path and pack path), plus a third green run after the P3
engine-wrapper additions. cplx10 196/196 at zero LLM calls; invariants
8/8; energy 0.403 J/query ≤ the 0.61 bound.

**H2 — A1 ≈ A0 (breeder stays falsified). CONFIRMED, with a sharper
mechanism than predicted.** The breeder produced ZERO candidates in
5,000 residual queries: it aligns patterns against COMPLETED parses,
and the escalated-residual stream never completes. It is not weakly
unproductive on this stream; it is structurally inert.

**H3 — A2 > A0 (miner lifts certified coverage). FALSIFIED at the
pre-registered local scale; the ladder headline is judged on this
arm.** llama-8B mined 2,306 proposals, 132 went ACTIVE, and held-out
lift was exactly zero (validation flat 0/1000; sealed residual 0/500;
McNemar 0/0). SCALE REPLICATIONS (H12-lineage, reported alongside,
never swapped into the ladder): haiku +5.8pp (29/0, p≈3.7e-9),
sonnet +7.2pp (36/0, p≈0), sonnet>haiku 7/0 (p=0.016) — the channel
works and improves monotonically with miner scale; the falsification
is miner-scale-bounded, not architectural.

**H4 — A3 ≥ A2. CONFIRMED trivially (0 = 0), uninformative:** with
the breeder inert (H2), A3 degenerates to A2. The named interaction
could not be tested on this stream.

**H5 — gates necessary (K4 wrong-fire > gated + 5pp). FALSIFIED, and
the mechanism is a positive discovery: defense in depth.** With the
gauntlet disabled, ungated miner pools produced ZERO wrong-fire on
every sealed final — the runtime certification layer independently
contains the junk. The damage appears as LOST COVERAGE instead
(llama's ungated pool: sem 100→94.7%, adv 83.6→75.4%). The gauntlet
buys coverage protection and pack hygiene; certification buys the
safety floor even under reckless acquisition.

**H6 — wrong-fire 0.000 in ALL gated arms. CONFIRMED.** Six arms,
three sealed finals each, every checkpoint probe: not one wrong
execution anywhere. Coverage == accuracy on every arm that answered.

**H7 — break-even N ≤ 50 reuses. LETTER-PASS, SPIRIT-FAIL (reported
as MIXED).** Local miner: 22.6 kJ per ACTIVE reflex / 719 J avoided
= 31 reuses ≤ 50. But llama's ACTIVE reflexes are never reused (zero
lift → zero utilization), so the pass is hollow. The economically
real number is the sonnet replication's: ~720k tokens (≈ $3.5 at
current API list) for +7.2pp certified coverage — negligible against
the measured 1,910 J/query pure-LLM cost of the residual it retires.

**H8 — loop-close. CONFIRMED (demo traffic, labeled as such).** A
momentum kind + capability mined live from llama-8B out of a real
escalation, dimensionally gate-certified, probation-promoted, then
answering two paraphrases deterministically (14.0, 30.0) with full
certificates.

## Discoveries outside the pre-registered set

- **Escalated-residual composition** (item-level diagnosis, 30
  sampled): the frozen engine's misses are dominated by engine-layer
  gaps — word-number vocabulary ("a dozen"), hyphenated units
  ("2-tonne"), ask-focus mis-naming ("what current flows" targeted as
  resistance) — not missing domain mappings. This bounds what ANY
  shallow-candidate miner can do and is the concrete V1.1 worklist.
- **The composition hazard**: individually harmless candidates can
  collectively poison parsing (a mined kind aliased to "kg" made
  every "7 kg" ambiguous). Killed by alias-collision gates plus the
  regression clause in shadow confirmation (a wrong-answers-only
  check is blind to abstention damage).
- **Miner quality is prompt-coupled**: gap-directed prompts (the
  engine's own failure report included) cut proposal volume ~30% and
  produced the first gate-passing deep-layer candidates.
- **Frozen-engine scale check**: 45,000 fresh generated items, ZERO
  wrong answers during pool filtering (83.4% coverage, all misses
  abstentions).
