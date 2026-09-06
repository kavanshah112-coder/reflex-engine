# V1.8 SPEC — Role-Aware Reuse

## Can a certified plan be served AGAIN, on a question it was not written for, without ever binding a number to the wrong role — and does a library that reuses safely compound?

**STATUS: FROZEN (2026-09-06) — all seven §12 decisions RESOLVED by
the user as proposed ("freeze n continue with proposed decisions").
Tag `v1.8-plan`.** §7–§10 and the §11 risk register never change
after this point; any later amendment is recorded as an AMENDMENT
block with its date and reason, never edited in place.

Built on V0.1–V1.7. No prior version, tag, snapshot, dataset, report
or log is modified. Full arc protocol applies: pre-registration,
hashed sealed sets (raw bytes, `-text` attr), dev/sealed splits, no
tuning on sealed results, bugs documented with superseded runs
preserved, single-command reproduction, finalize with tag + frozen
snapshot (`.env` excluded) + report MD/PDF + memory update. Bridge
only; no API spend; the live key in `.env` is never read by V1.8
code.

**The user's brief (2026-09-06), recorded in intent:** focus V1.8 on
the five generation problems V1.7 left open — minted reflexes do not
reuse safely (B32); connector minting was a null; minting needs
completed examples; the smallest model is shut out; growth per
mining dollar is modest and the library does not compound — and
write the spec with the known drawbacks of each proposed fix built
in, not discovered afterwards.

---

## 1. What V1.7 left exactly here

V1.7 (OUTCOME E, tag `v1.7-final` @ 819115d) proved the composition
half of the arc and broke on the reuse half:

- **Composition holds.** The deterministic composer served 112,170
  sealed chains at zero wrong (30.4% of 3+-step items; 17.4% at
  k=6). Sonnet / fable / opus planned 3,600 sealed chains with zero
  certified-wrong (93.2 / 94.8 / 95.8% certified). 4M evaluations,
  zero uncontained errors. Structure-finding 4.6–6.5 s median,
  +10–19% from k=3 to k=6.
- **Reuse breaks.** Every one of the 8,842 wrong answers in the four
  million-item arms (haiku 3,069 / sonnet 2,768 / fable 1,762 /
  opus 1,243) came from `planlib17` positional template replay —
  never from the composer, never from a fresh plan on the three
  larger models. B32 names three mechanisms of one family:
  donor-constant swap (the STRUCTURAL whitelist blind spot), role
  misbinding (all numbers present, roles swapped), and dropped
  dual-role usage (haiku's 13 certified-wrong sealed plans, which
  G-P4's magnitude-presence check cannot see). The
  `--strictreplay` literal-presence probe closed only the first
  (0.73% → 0.46% dev wrong-fire; 9 role-misbinding survivors).
- **Generation otherwise works.** Chain-reflex minting: sonnet 37 /
  opus 60 / fable 52 admitted (union 149), zero sealed wrongs
  traced to any admitted reflex after B31; haiku 0. Connector
  minting: zero survivors on every model. Every coverage point in
  the arc from V1.0 to V1.7 was bought by a mining run; no evidence
  yet that the library compounds.

The one sentence V1.7 ends on, from the B32 ledger entry: *"Safe
reuse must bind by ROLE, which is what the composer does — and the
composer served 112,170 sealed chains at zero wrong."*
`composer17._s_use` already binds by role cue ("using X as the
speed") and by unit ("bind remaining slots from stated facts by
unit"), deterministically. V1.8 lifts that mechanism from the
composer's own chains to the reuse of every certified plan.

In-regime constants carry forward unchanged; no new energy claim is
made until §6's instrument passes its positive control.

---

## 2. Thesis

> The three generation problems that matter — unsafe reuse (B32),
> minting from completed examples only, and a non-compounding
> library — are ONE problem seen three ways. A witness-certified
> plan IS a completed example of a question the composer could not
> do; serving it again safely IS role-aware reuse; and safe reuse IS
> the only mechanism by which a library compounds without a mining
> run per coverage point. V1.8 builds one component, a deterministic
> role-aware binder, and measures whether the three problems close
> together — or whether the coverage cost of binding honestly
> collapses the economics the reuse was meant to deliver.

The identity gains its honest form. V1.7 wrote
`E_system ≈ f_esc×E_llm + f_plan×(E_llm/η + k×E_engine) + f_det×k×E_engine`
with η measured 12.5–74.9. V1.8 states that η was measured over
UNSAFE reuse; the η that matters is the one at zero binder wrongs,
and it may be much smaller. The version's economics are reported at
that η, not V1.7's.

---

## 3. What is honestly unknown — the version's core questions

**Q1 — coverage cost of honesty.** Strict role binding abstains on
any ambiguity. If many questions carry two numbers of the same
dimension, the binder abstains on all of them. The question is not
whether role-aware reuse is safer — the composer already shows it is
— but what fraction of V1.7's template-served volume survives when
every bind must be unique. The answer may be half. That is reported
as a curve, not hidden in a threshold.

**Q2 — is role inference deterministic enough?** Deciding that "12"
is a rate and "5" is a time from the surrounding text is a reading
problem, and V1.3–V1.5 showed that model readings of one text
disagree with each other ~3/4 of the time. V1.8 answers by fiat and
then measures the cost: the binder contains NO model call; a role is
a (dimension, unit-or-cue, consumer-slot) triple resolved only by
unit adjacency and the composer's own cue grammar. What that grammar
cannot resolve, it abstains on. Q2 is therefore Q1 in different
clothes: how much does a purely deterministic binder leave on the
table?

**Q3 — a fourth B32 mechanism.** The three mechanisms are the three
the 8,842 wrongs showed. A role-aware binder is designed against
those three. A mechanism absent from the probe corpus (correct roles,
wrong ORDER in a non-commutative op; correct roles, wrong node for a
number that legitimately fits two nodes) would pass the positive
control and still fire. V1.8 pre-registers where it would show up
(sealed volume; the §11 ledger-injection cannot see it) and does not
claim its absence.

**Q4 — does harvest generalize honestly?** Turning one certified
plan into a template asserts that the plan's structure fits every
question sharing its signature. The plan was certified for ONE
binding; the template is a claim about a family. B32 is exactly what
happens when that claim is wrong. Harvest produces templates faster,
and under an imperfect binder that means wrongs faster.

**Q5 — compounding, or the generator's redundancy?** Q-1M is
generator-produced and structurally repetitive by construction. A
compounding ratio of 5 on Q-1M may be 1.2 on real questions. The
ratio is reported twice — raw, and on a signature-deduplicated
stream — and the synthetic caveat is carried into every claim.

---

## 4. Architecture

```
QUERY (chain-routed text; V1.6 path untouched, B30 routing kept)
  |
  +-- composer17 (V1.7, unchanged) ---- serves what it already serves
  |
  +-- binder18 (NEW, deterministic, NO model call)
  |     1. signature lookup: candidate templates whose
  |        planschema17.signature matches the question's
  |        role-slot signature (NOT a surface regex)
  |     2. role resolution: every stated number in the question
  |        gets a ROLE = (dimension from its unit or cue, usage
  |        count from the composer's cue grammar); a number with
  |        no resolvable dimension and no cue is UNRESOLVED
  |     3. bind: every template slot must take EXACTLY ONE
  |        stated number whose role matches the slot's role;
  |        zero candidates -> abstain; two candidates -> abstain;
  |        any UNRESOLVED stated number -> abstain (B28 at
  |        binding level: an unplaced number is a wrong plan)
  |     4. multiplicity rule: if >1 template binds, serve only if
  |        the bound plans are identical after binding; else
  |        abstain and count "template collision"
  |     5. the bound plan goes through plangate17 (with G-P4'
  |        below) + chainexec17 + chain_witness17 EXACTLY as a
  |        fresh plan would. Reuse saves structure-finding, never
  |        certification.
  |
  +-- plangate17 G-P4' (EXTENDED): stated-number honesty becomes
  |     usage accounting. For every stated number, the composer's
  |     cue grammar yields a semantic usage count u(s) (a number
  |     re-mentioned beside the same unit within the same clause
  |     counts once); the plan must consume s exactly u(s) times
  |     by |magnitude| AND role. The STRUCTURAL whitelist remains
  |     an exemption for literals the plan INTRODUCES, never for
  |     binding (the B32 rule from the ledger, made structural).
  |
  +-- planner sample (bridge, as V1.7): fresh plans on items the
  |     composer and binder both abstain on; gated by G-P1..3 +
  |     G-P4'; the source of new templates
  |
  +-- harvest18 (NEW, offline): certified plan -> role-slot
  |     template -> gauntlet -> library (§4.2)
  |
  +-- else ESCALATED untouched
```

New code: `reflex/roles18.py` (role resolution from unit adjacency +
the composer's cue grammar, shared by binder and gate),
`reflex/binder18.py` (steps 1–5), `plangate17` extended in place with
G-P4' behind a flag (V1.7 behaviour reproducible byte-exact with the
flag off), `tools/harvest18.py`, `tools/gapclass18.py` (§4.3),
`v18_run.py`. Reused untouched: composer17, chainexec17,
chain_witness17, mint17's gauntlet, the V1.6 stack, the V1.7 plan
archive.

### 4.1 The binder is deterministic — a rule, not a preference

No model is called inside binder18, roles18 or G-P4'. This is the
answer to Q2 and the mitigation of §11 R3: a component whose
correctness is semantic and whose errors corroboration cannot see
(V1.3) is admitted into the safety path only if its behaviour is a
fixed function of the text. What the fixed function cannot resolve,
it abstains on. The haiku binding arm (§4.4) is the ONLY place a
model touches binding, and it is a measured arm, never merged.

### 4.2 harvest18 — plan-to-template with the two-donor rule

Input: the V1.7 plan archive (`results/v17/v17_plan_archive.zip`,
4,800 raw plans; `plans_<m>_{dev,sealed}.json` scored) plus every
V1.8 fresh certified plan. Only plans that were witness-certified
CORRECT against gold are eligible; certified-wrong and gate-killed
plans are the §4.5 negative battery.

Pipeline per plan: replace each bound literal with a role slot
(roles18 on the donor question) → `planschema17.signature` →
candidate template. Admission requires:

- **Two-donor rule (Q4):** a template enters probation only when ≥2
  certified plans from DISTINCT donor questions produce the same
  signature AND the same role assignment. One plan is an example;
  two agreeing plans are a claim about a family. Single-donor
  templates are recorded, never served.
- **Probation** in the V1.7 gauntlet form on the ACQ stream (golds
  exist there): ≥3 end-to-end-witnessed correct serves on ≥3
  distinct operand tuples, zero wrong, one strike revokes.
- **Sub-chain harvest**: a certified k-step plan yields its
  contiguous sub-plans (k=2..k−1) as candidates. Each sub-template
  is subject to the SAME two-donor rule and its OWN probation —
  a sub-chain that isolates a cancelling error (V1.2's gsm1120
  class) must fail on its own tuples (§11 R7).

Library growth is a primary deliverable per class (full-chain /
sub-chain), per donor model, with a collision count (§11 R8).

### 4.3 gapclass18 — connectors, re-posed as measured gaps

V1.7's connector null is not re-run. Instead, every escalation on
DEV-L is classified by the composer's own failure reason: (a)
structure gap — the composer found no DAG; (b) adapter gap — a DAG
exists but one edge fails G-P2 type/unit flow for want of a
conversion edge; (c) binding gap — binder18 abstained (with its
reason: zero candidates / two candidates / unresolved / collision);
(d) other. Shares are reported first.

Adapter minting runs ONLY if adapter gaps are ≥10% of escalations.
Then, per missing edge (ranked by frequency), the bridge model is
asked for exactly that edge with a unit/dimension derivation the
witness checks. Admission requires shadow probation over the FULL
DEV-L stream with zero wrong AND zero lost coverage — the V1.0
composition-hazard rule (§11 R5): one new edge changes which paths
exist for every question, not just the gap it was mined for. If
adapter gaps are <10%, connectors are closed as a null with a
measured reason, and no adapter is minted.

### 4.4 haiku binding arm — the V1.3 test at binding level

haiku is never asked to find structure in V1.8. On the items where
binder18 abstains for reason "two candidates", haiku is asked ONLY
to choose the binding, and the chosen plan goes through the full
gate + witness. This arm is evaluated separately and its serves are
NEVER merged into the served library or the compounding ratio. It
answers one question: is a cheap model safe as a slot-filler when
the witness recomputes values? The pre-registered risk (§11 R9) is
that a dimensionally consistent misbinding passes the witness —
binding is composition, and the guarantee belongs to whoever
composes (V1.3). If deterministic binding already covers what haiku
adds, haiku is reported REDUNDANT, which is a clean result.

### 4.5 Positive and negative controls before any counting run (B24)

- **B32 probe corpus**: every wrong row of the eight
  `R-<model>_{acq,dev,seal,replay}_wrong.json` files (8,842 serves,
  question + template + wrong answer + gold). binder18 must, on
  every one, either abstain or serve the gold. One served wrong
  voids the version's binder until fixed and rerun.
- **haiku-13 corpus**: the 13 certified-wrong sealed S-PLAN serves;
  G-P4' must kill every plan.
- **Order battery (Q3)**: hand-built plans with correct roles and
  swapped operand order on every non-commutative op (sub, div,
  pow, convert from/to); must all die at G-P4' or the witness.
- **Benign-repeat battery (§11 R4)**: questions that re-mention a
  number beside the same unit ("the 40 kg crate — yes, 40 kg");
  roles18 must count one usage, and the plan must PASS.
- **Harvest negative battery**: every certified-wrong and
  gate-killed V1.7 plan pushed through harvest18; none may reach
  probation.
- **Instrument control (§6)**: the energy meter must read
  non-zero on a known load before any joule is reported.

---

## 5. Datasets

```
Q-1M        REUSED as frozen (results/v17/data/, hashes as recorded).
            ACQ 200k / DEV 100k / SEAL 300k / REPLAY 400k, same
            splits, same distractors. SEAL and REPLAY are run ONCE
            for V1.8's arms.
DEV-L       NEW: 400k items, same generator, seed 1800, same depth
            mix and overlays, built and hashed BEFORE any V1.8
            serving code exists; hash-checked disjoint from SEAL
            and REPLAY item-by-item. The sealed-shaped dev set that
            V1.7's 600-item S-PLAN dev could not be (0 of 4 arms
            showed a wrong; sealed exposed 13 — a ~0.15% chance dev
            would have caught them). Safety metrics on dev are
            reported from DEV-L only.
DEV-L-INJ   DEV-L plus the §4.5 probe corpora injected in-stream
            (B30 / B31 / B32 / haiku-13), labelled, used in EVERY
            dev run. This catches only known classes (§11 R11) and
            is described that way.
PROBE-B32   the 8,842-row corpus above, frozen and hashed.
S-PLAN      V1.7's 600 dev / 1,200 sealed planner items, reused for
            the haiku binding arm and for fresh plans; no new
            planner sample.
REAL-DIAG   DIAGNOSTIC ONLY, no threshold: the frozen V1.3 corpora
            (GSM8K / ASDiv / SciQ slices, hashes as recorded) run
            through binder18 + composer to report the compounding
            ratio on non-synthetic text beside Q-1M's (Q5).
```

Signature deduplication for Q5: a stream in which each
`planschema17.signature` of the gold DAG is kept once, drawn from
REPLAY, hashed; the compounding ratio is reported on it alongside
the raw stream.

---

## 6. Energy (scoped, instrumented, or not claimed)

Measured on the lean scientific configuration only: composer17 +
binder18 + gate + witness, no parser-era pipeline. Batch-metered as
in V1.2 with three rules from §11 R12–R13:

- the meter must pass a positive control (a fixed CPU load reads
  within 20% of its known draw) before and after each batch;
- Ventorah's Docker workers are production and are never stopped;
  measurements are taken in windows where the fleet is idle by its
  own `/status`, with a 60 s idle baseline subtracted and the
  baseline's variance carried into the reported CI;
- two numbers are reported, never one: J per certified served
  answer, and J per QUESTION on the sealed stream with the measured
  bridge planning cost amortized at the ZERO-WRONG η — the number a
  reader will compare to LLM inference whether we like it or not.

If the positive control fails or the idle window cannot be found in
the session, no energy number is reported and the ladder's ENERGY
item reads "not measured", not "small".

---

## 7. Hypotheses (FROZEN on freeze)

| | claim | prediction |
|---|---|---|
| H1 | binder18 closes the B32 family: zero served-wrong on PROBE-B32 (8,842) and zero binder-attributed certified-wrong on SEAL + REPLAY | **the version's safety crux**; predicted yes for the three known mechanisms; Q3's fourth mechanism is the unknown |
| H2 | G-P4' closes the dual-role class: the haiku-13 corpus dies 13/13; haiku's fresh-plan certified-wrong on sealed S-PLAN = 0 | predicted yes; a few % of haiku plans move to abstain |
| H3 | the coverage cost of honesty is real but not collapsing: role-aware reuse retains ≥60% of V1.7's template-served volume per arm | **uncertain — Q1; could be half** |
| H4 | harvest18 turns the archive into a library: ≥300 role-aware templates admitted under the two-donor rule at zero probation wrongs | plausible from 3,406 certified sealed + ~1,700 dev plans; unique-signature count unknown |
| H5 | the library compounds: compounding ratio (certified library serves ÷ plans purchased) ≥5 raw and ≥2 on the deduplicated stream for ≥2 scales | uncertain; the dedup number is the one that counts |
| H6 | adapter gaps are a minority of escalations (<10%) — V1.7's connector null had a good reason | predicted; measured either way |
| H7 | haiku as slot-filler is either unsafe (≥1 certified wrong) or redundant (adds <1pp over deterministic binding) — not a third thing | predicted from V1.3 + V1.7 |
| H8 | DEV-L at 400k exposes at least one wrong mode S-PLAN dev could not (M1's premise) | predicted; if DEV-L shows zero and SEAL shows some, M1 has failed too |
| H9 | the lean configuration's energy is measurable with a passing instrument control, and J/question at zero-wrong η is within one order of magnitude of J/certified serve | uncertain — depends on η at zero wrong |

---

## 8. Metrics (FROZEN)

**Primary: (a) served-wrong count on PROBE-B32 (must be 0) and
binder-attributed certified-wrong on SEAL and REPLAY per arm (must be
0); (b) coverage retention = role-aware template serves ÷ V1.7
positional template serves on the SAME sealed items, per arm, with
the abstain-reason breakdown (zero candidates / two candidates /
unresolved / collision); (c) harvest ledger: plans in → single-donor
recorded → two-donor probation → admitted / revoked, per class and
donor model; (d) compounding ratio, raw and deduplicated, as a curve
over the stream; (e) gap-class shares on DEV-L.**

Secondary: G-P4' abstain reasons on fresh plans; benign-repeat
false-abstain rate (from the battery and a 1k hand-audited DEV-L
sample); template collision rate; haiku binding arm wrong / lift;
adapter arm (if run) recovered share at zero lost coverage; REAL-DIAG
compounding ratio; energy per §6; every V1.7 secondary metric
re-reported so nothing regresses silently.

---

## 9. Thresholds (FROZEN)

```
SAFETY-B32  zero served-wrong on PROBE-B32 (8,842 rows) — a control,
            not a result; fails the version until fixed and rerun.
SAFETY-1    wrong-fire on ALL served answers, every arm, every set
            <= 0.1%; target and expectation 0. (V1.7's 0.5% bar was
            met by no reuse arm; V1.8's bar is the composer's
            standard, because reuse now claims the composer's
            mechanism.)
SAFETY-2    zero certified narrative items (in-stream distractors).
SAFETY-BIND zero certified-WRONG answers attributable to binder18 on
            SEAL or REPLAY. One = the B32 family is not closed and
            the version is E regardless of every other number.
SAFETY-3    zero certified-WRONG from MODEL-PROPOSED fresh plans
            under G-P4' (V1.7's SAFETY-3, now including haiku).
SAFETY-4    zero wrong-fire attributable to any harvested template
            or minted adapter on sealed data; one traced wrong
            revokes it AND is reported.
GATE-CTRL   every §4.5 battery passes 100% before any counting run;
            a control failure voids all reuse serves until rerun.
RETAIN      coverage retention >= 60% per arm on >= 2 scales.
            40-60% = partial (reported at rung C). < 40% on every
            scale = collapse (rung D).
HARVEST     >= 300 role-aware templates admitted (union) at zero
            probation wrongs.
COMPOUND    compounding ratio >= 5 raw AND >= 2 deduplicated on
            >= 2 scales, with SAFETY-BIND at zero. A raw pass with a
            dedup fail is reported as "the generator's redundancy,
            not the library's" and does not count.
GAP         gap-class shares reported on DEV-L (a measurement
            threshold). If adapter share >= 10% and the arm runs:
            recover >= 25% of adapter-gap escalations at zero wrong
            and zero lost coverage, else honest null.
DEVVOL      DEV-L 400k run for every arm before its sealed run,
            with DEV-L-INJ; no sealed run without it.
ENERGY      instrument control passed both sides of every batch;
            both §6 numbers reported with CI — or "not measured".
```

Where thresholds pull against each other, **safety wins by
construction** (§11 R10): COMPOUND and RETAIN are computed only over
serves that satisfy SAFETY-BIND; the binder's matching rules (§4
steps 1–4) are frozen at `v1.8-plan` and may not be loosened to lift
a ratio.

---

## 10. Outcome ladder (FROZEN; priority F > E > D > C > B > A)

```
F  V1.7 / V1.6 / Tier A stop reproducing byte-exact with G-P4' off,
   or a GATE-CTRL battery cannot pass, or PROBE-B32 cannot be
   reconstructed from the committed wrong files.
E  SAFETY-1, SAFETY-2, SAFETY-BIND or SAFETY-3 fails — role-aware
   reuse is not safe, or the dual-role class is still open.
D  safe but collapsed: RETAIN < 40% on every scale AND HARVEST
   fails — honest binding leaves too little to reuse; the library
   is a lookup table and the amortization term dies. Report the
   abstain-reason anatomy as the finding.
C  safe, RETAIN >= 40% on >= 2 scales, but COMPOUND fails
   (dedup ratio < 2 everywhere) or HARVEST fails — reuse works and
   does not compound; every coverage point still costs a mining
   run. Report the curve.
B  SAFETY all zero, RETAIN >= 60% on >= 2 scales, HARVEST met,
   COMPOUND met on >= 2 scales — but ENERGY not measured, or GAP /
   haiku arms incomplete, or DEVVOL skipped for any arm.
A  everything in B, plus ENERGY reported with passing controls,
   GAP answered either way (measured shares; adapter arm run or
   closed by the 10% rule), haiku arm reported as unsafe /
   redundant / neither with numbers, and H8 answered.
```

---

## 11. Risk register (FROZEN with §7–§10) — each fix's known drawback, its detector, and what we do about it

Each row is a drawback identified BEFORE the run. A drawback that
fires is a result, not a bug; it is reported under its R-number.

```
R1   Coverage collapse from strict binding (P1).
     Detect: RETAIN per arm + abstain-reason breakdown.
     Mitigate: none by loosening — the matching rules are frozen.
     Rung D exists for this. The curve is the deliverable.
R2   New representation inherits no scar tissue (P1; V1.4/B22).
     Detect: DEV-L-INJ carries every ledgered wrong class; the V1.7
     secondary metrics are all re-reported.
     Mitigate: G-P4' is additive behind a flag; every V1.7 gate
     stays in the path; nothing is replaced, only extended.
R3   Role inference is a reading problem (P1; V1.3-V1.5).
     Detect: binder18 contains no model call — verified by a test
     that the bridge module is not importable from it.
     Mitigate: by construction (§4.1). The cost is R1.
R4   False abstention on benign repeats (P1b).
     Detect: benign-repeat battery + 1k hand-audited DEV-L sample
     with the false-abstain rate reported.
     Mitigate: same-unit-same-clause dedup in roles18; if the
     audited rate > 5%, reported as a G-P4' defect, not tuned away
     on sealed.
R5   Composition hazard from adapter edges (P2; V1.0).
     Detect: shadow probation over the FULL DEV-L stream per edge
     with a zero-lost-coverage rule.
     Mitigate: the 10% rule means the arm may never run; if it
     runs, one edge at a time, full re-run each.
R6   Gap misclassification (P2).
     Detect: 500-item hand audit of gapclass18 labels on DEV-L,
     agreement reported.
     Mitigate: adapter minting keyed to audited share, not raw.
R7   Silent generalization in harvest; sub-chain multiplies error
     (P3; V1.2 gsm1120).
     Detect: two-donor rule + per-template probation on ACQ golds;
     harvest negative battery.
     Mitigate: single-donor templates never serve; sub-templates
     get their own probation on their own tuples.
R8   Library explosion / multiple matches (P3).
     Detect: template collision count; signature-lookup latency
     reported at library size.
     Mitigate: the multiplicity rule (identical bound plans serve,
     differing ones abstain); no ranking heuristic — a ranking
     would be a hidden model.
R9   Cheap model in the safety path (P4; V1.3 "the guarantee
     belongs to whoever composes").
     Detect: haiku arm evaluated alone, never merged.
     Mitigate: the arm's wrongs count under SAFETY-3 for haiku
     only; the served library is untouched by it.
R10  Goodhart on the compounding ratio (P5).
     Detect: COMPOUND is computed only over SAFETY-BIND-clean
     serves; binder rules frozen at v1.8-plan.
     Mitigate: safety wins by construction (§9).
R11  Synthetic inflation of compounding (P5; Q5).
     Detect: deduplicated-stream ratio + REAL-DIAG.
     Mitigate: the dedup ratio is the one thresholded; every
     compounding claim carries the synthetic caveat.
R12  Dev/sealed contamination pressure at 400k dev (M1; V1.5
     disclosure).
     Detect: DEV-L built with its own seed and hash-checked
     item-disjoint from SEAL/REPLAY before any V1.8 code runs.
     Mitigate: structural separation; no sealed run without DEVVOL.
R13  Known-wrong injection catches only known wrongs (M1).
     Detect: H8 — DEV-L must find something S-PLAN dev could not,
     or M1's premise is reported as failed.
     Mitigate: none; stated as a limit.
R14  Energy instrument validity on a shared box (M2; B24).
     Detect: positive control both sides of every batch; idle
     baseline subtraction with variance in the CI.
     Mitigate: "not measured" is an allowed and honest outcome.
R15  Scoped energy claim read as an end-to-end claim (M2).
     Detect: two numbers always reported (§6).
     Mitigate: J/question at zero-wrong η is printed beside
     J/certified serve in every table that shows either.
R16  Systemic: the binder's correctness is semantic, which the arc
     has never certified deterministically (V1.2: "dimensional
     gates certify physics, not story semantics").
     Detect: SAFETY-BIND at sealed volume; Q3 stays open.
     Mitigate: abstain on every ambiguity; any binder wrong is E.
     If the binder cannot be made deterministic at usable
     coverage, V1.8 says so at rung D and the next version knows
     what it is about.
```

---

## 12. Decisions — RESOLVED by the user (2026-09-06, all as proposed)

1. **DEV-L 400k** — built by `tools/build_devl18.py` from V1.7's
   frozen generator (`build_q1m.gen_item`, untouched) with seed
   1800; programmatic items only plus the Q-1M ACQ/DEV distractor
   items (already disjoint from SEAL/REPLAY; the corpus has no
   unused supply); every generated text hash-checked against the
   SEAL+REPLAY text set and rejected on collision (count in the
   manifest); no foreign-slot overlay (bridge-authored in V1.7,
   not re-authored here — recorded as a DEV-L limitation). Raw-byte
   SHA-256 recorded before any V1.8 serving code exists.
2. **RETAIN band** — 60% pass / 40–60% partial / <40% collapse.
3. **Adapter arm gating** — the 10%-of-escalations rule.
4. **haiku binding arm** — run as a measured, never-merged arm.
5. **REAL-DIAG** — run the frozen V1.3 corpora as a no-threshold
   diagnostic.
6. **Energy window** — fleet-idle windows with baseline subtraction
   and instrument controls; "not measured" allowed.
7. **V1.7 logs** — the per-item logs of all four million arms
   (`results/v17/R-<model>_{acq,dev,seal,replay}.jsonl`, none of
   which had been committed — not only fable's) and the strict
   probe log are committed in the freeze commit, so PROBE-B32 and
   the per-item retention denominator are reconstructible from the
   repo alone. Finding recorded here: `R-*_wrong.json` rows carry
   text truncated to 140 characters, so PROBE-B32 is rebuilt by
   joining wrong-row ids to the committed Q-1M items and template
   names to `stack_<model>.json`.

**Implementation note (frozen with the spec):** G-P4' is delivered
as `reflex/plangate18.check`, which calls `plangate17.check`
unchanged and then applies usage accounting — V1.7's gate stays
byte-identical and the "flag off" reproduction is simply the V1.7
call path. Role resolution for both the binder and G-P4' lives in
`reflex/roles18.py`; slot roles are a fixed table over the
planschema17 slot conventions the four models actually used in all
6,757 admitted V1.7 plans (`formula.m/r/t`, `scale.by`,
`derivative_at.point`, `integrate_def.a/b`, `sum_finite.a/b`,
`ncr.n/r`, `gcd|lcm.a/b`, `compare.b`); a plan slot outside the
table is UNROLLED and the plan abstains.

---

## 13. What this version honestly claims, and does not

It does not re-open reading language, and it does not mint new
parsing. It claims the next structural thing: **that a certified
plan can be served again on a question it was not written for,
binding every number by role and never by position, at the
composer's standard of zero wrong — and that when reuse is safe, the
library begins to pay for itself.** If the binder cannot bind
honestly without abstaining on most of what V1.7 reused, rung D says
the amortization term is dead and names the abstain reasons that
killed it. If reuse is safe but the deduplicated ratio stays near
one, rung C says every coverage point still has to be bought. If a
fourth B32 mechanism fires at sealed volume, rung E says the family
is larger than three and the ledger gets its next entry.

The 8,842 wrong answers are the version's positive control. A binder
that lets one of them through is not a binder.

---

## AMENDMENT A1 (2026-09-06, before any counting run) — gate G-P5, certified formulas

**Reason (B33, `bug_audit_v1_8.md`):** building the haiku-13 positive
control showed that 12 of the 13 certified-wrong haiku plans carry the
formula `p * r * t / 100 + p` (the amount) for a "simple interest"
ask, with every stated number consumed in its correct role; the 13th
pre-differentiated its expression. The B32 ledger's diagnosis of
haiku-13 as a dual-role class was written without reading the plans
and is superseded. H2 as frozen ("G-P4' kills 13/13") is therefore
unachievable for 12 of 13 by usage accounting, and a GATE-CTRL battery
that cannot pass is rung F.

**Amendment:** the plan gate gains **G-P5 — certified formulas**: a
`formula` node's expr must be algebraically equivalent, symbol for
symbol, to an entry of the frozen certified-formula table (the
composer's `FORM` table: kinetic energy, potential energy, force,
work, power, current, simple interest), and the question must name
that kind at least as many times as the plan uses it. A free-form
formula is producer-supplied physics — a value in disguise one level
above V1.3's ban — and abstains.

**Frozen consequences:** H2 now reads "G-P4' + G-P5 kill haiku-13
13/13; haiku's fresh-plan certified-wrong on sealed S-PLAN = 0". The
G-P5 kill count per arm is a reported metric (a fresh plan with an
uncertified formula abstains — the coverage cost is measured, not
hidden). §4.5's haiku-13 battery is split: 12 rows are G-P5's positive
control, 1 row is G-P4''s. Nothing in §9/§10 changes. Risk register
row **R17**: the certified table is small (7 kinds); any question
whose physics is outside it escalates — detect: G-P5 kill share;
mitigate: none in V1.8, the table is frozen with this amendment.
