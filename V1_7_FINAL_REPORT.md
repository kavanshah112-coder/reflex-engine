# V1.7 FINAL REPORT — Cohesive Multi-Reflex Chains at Million Scale

**Verdict: OUTCOME E** (frozen ladder §10, priority F>E>D>C>B>A).
SAFETY-1 was breached by two of the four per-model million arms
(R-haiku 0.80%, R-sonnet 0.63% wrong-fire vs the ≤0.5% bar) and
SAFETY-3 was breached by haiku's sealed plan arm (13 certified-wrong
plans). The ladder therefore says E — even though the deterministic
engine, all safety controls, and three of four planner campaigns ran
at **zero wrong**, and every non-safety criterion (COHESION,
PLAN-LIFT, TIMING, η, SCALE) passed. As in V1.3, the pre-registered
letter is strict while most aggregates are excellent; both are
reported here without adjustment.

Spec frozen at `v1.7-plan` (b87ff8f) before any sealed evaluation.
Q-1M (seed 1700, 1,000,000 items: 60.6% non-monotonous, 71.7%
multi-domain, 6,000 foreign-slot chains, 3,624 distractors) committed
in-repo with raw-byte hashes (`hashes_final_preseal.json`; seal
`4b83eb69…`); splits ACQ 200k / DEV 100k / SEAL 300k / REPLAY 400k.
Sealed splits ran once per pre-registered arm.

---

## 1. The question V1.7 asked

V1.6 proved single reflexes certify at scale. V1.7 asked: do they
**compose**? Three sub-questions, per the user's brief:

1. **Cohesion** — can the deterministic engine chain 2–6 reflexes
   through one another on questions that need all of them?
2. **Combined calculation** — do the four models (haiku, sonnet,
   opus, fable) produce *plans* — multi-reflex structures — that the
   gate + dual-implementation witness can certify?
3. **Time** — how long does each model take to find a multi-reflex
   structure, as a function of chain depth k?

## 2. Architecture (all new, V1.6 untouched)

- **Plan schema** (`planschema17`): DAG of typed nodes
  (`evaluate/formula/scale/convert/derivative_at/integrate_def/
  solve_pick/sum_finite/gcd/lcm/ncr/npr/is_prime/probability/
  compare`), `@nX` value refs, structure signatures for reuse.
- **Composer** (`composer17`): deterministic chain-visible text→plan.
- **Gate G-P1..4** (`plangate17`): schema/DAG; type+unit flow;
  ask-target (asked unit, CHOICE/GREATER asks); stated-number honesty
  by |magnitude| with an anti-value-smuggling STRUCTURAL whitelist.
- **Dual execution**: `chainexec17` (sympy side) certified only when
  `chain_witness17` (mpmath-only independent replay, depth-budgeted
  tolerance) confirms the final value. GATE-CTRL batteries (1 sound +
  8 wrong-plan classes; witness positive controls) passed 100% before
  any counting run.
- **Free-hand minting** (user decision D2): every model could propose
  parse, chain, and connector (unit-adapter) reflexes; all classes
  faced chained probation (≥3 end-witnessed correct, ≥2 distinct
  tuples, zero wrong).

## 3. COHESION — the deterministic result (PASS)

SEAL 300k, det arm, run once: **112,170 served / 0 wrong / 0
distractors served**; in-domain coverage 37.5%; **3+-step coverage
30.4% ≥ the 25% bar**. Depth reach: k2 66.1%, k3 42.5%, k4 27.0%,
k5 20.7%, k6 17.4%. The composer never served a partial answer
(B30/B31 class closed structurally: chain-marked text is out of the
single-step engine's domain, and a minted chain match must consume
the whole question).

## 4. The planning campaigns — 4,800 sealed plans, live-watched

Each model structured 1,200 sealed items (25-item batches, one
serial agent lane per model, one plan file per item written
immediately — file mtimes are the timing instrument; batch-first
items excluded as startup).

| model  | certified | rate  | gate-killed | exec-refused | **SAFETY-3 wrong** |
|--------|-----------|-------|-------------|--------------|--------------------|
| haiku  | 1,077     | 89.8% | 81          | 29           | **13**             |
| sonnet | 1,118     | 93.2% | 66          | 16           | 0                  |
| fable  | 1,138     | 94.8% | 62          | 0            | 0                  |
| opus   | 1,150     | 95.8% | 50          | 0            | 0                  |

Dev (600/model) had shown **zero** wrongs for all four — haiku's 13
appeared only at sealed scale. Mechanism: a stated number serving two
roles ("multiply by 7 … at 7% per year") satisfies |magnitude|
honesty while a usage is dropped; role-blind honesty is the blind
spot (§7). Per frozen SAFETY-3, one wrong fails the arm: haiku's
plan arm is disqualified regardless of coverage.

### Timing (the user's third question)

Median seconds to find and write a chain structure, by depth
(p90 in parentheses); n = 1,151/1,200 measured per model (95.9% ≥
the 90% TIMING threshold):

| model  | k3          | k4          | k5          | k6          |
|--------|-------------|-------------|-------------|-------------|
| sonnet | 4.60 (5.58) | 4.74 (5.66) | 4.89 (6.12) | 5.10 (6.23) |
| haiku  | 4.74 (6.14) | 4.91 (6.71) | 5.05 (7.13) | 5.29 (7.31) |
| opus   | 5.43 (6.47) | 5.67 (6.88) | 6.04 (7.47) | 6.45 (8.02) |
| fable  | 5.59 (6.37) | 5.79 (6.53) | 6.07 (6.72) | 6.31 (7.40) |

Two findings. (1) Structure-finding time is **nearly flat in depth**:
a 6-step chain costs only ~10–19% more than a 3-step one (+0.5–1.0s)
— models grasp the whole chain in one read; depth is not re-derived
step by step. (2) **Speed anti-correlates with safety**: the fastest
planner (sonnet/haiku ≈4.6–4.7s) includes the only unsafe one; the
slowest (opus 5.4–6.5s) is the most accurate at zero wrong.

## 5. The four million-item arms (R-\<model\>: det + that model's
minted reflexes + its dev plan templates, over all 1M items)

4,000,000 evaluations, **zero uncontained engine errors** (SCALE
met). Sealed split (300k) per arm:

| arm      | coverage | wrong | wrong-fire | SAFETY-1 | error per template serve |
|----------|----------|-------|------------|----------|--------------------------|
| R-haiku  | 39.2%    | 937   | 0.80%      | **FAIL** | 18.7%                    |
| R-sonnet | 44.6%    | 840   | 0.63%      | **FAIL** | 4.0%                     |
| R-fable  | 47.2%    | 542   | 0.38%      | pass     | 1.9%                     |
| R-opus   | 48.8%    | 357   | 0.24%      | pass     | 1.06%                    |

Every wrong in every arm traces to a **dev plan template** replayed
by positional regex (path `mint:chain:<model>_plan_*`); the
composer's own serves inside the same runs were at zero wrong. Both
coverage and template hygiene are **monotone in scale** — V1.1's
scale inversion stays falsified one layer up: bigger models write
templates that are simultaneously more general (more serves) and
cleaner (fewer wrongs per serve).

## 6. PLAN-LIFT and η

Det 3+-step sealed coverage is 30.4% (72,793 of 239,299). The sealed
S-PLAN pools were drawn uniformly from det's 166,506 3+-step
escalations, so certified rate × residual share estimates the plan
arms' stratum coverage at SAFETY-3 zero:

- sonnet: 30.4% → ~95.2% (**+64.8pp**)
- fable: 30.4% → ~96.4% (**+66.0pp**)
- opus: 30.4% → ~97.1% (**+66.7pp**)
- haiku: disqualified (SAFETY-3).

PLAN-LIFT ≥ +10pp met on three scales. η (serves per admitted
library entry on the 400k replay mass): haiku 12.5, sonnet 48.2,
fable 65.7, opus 74.9 — all ≥2, with the caveat that those serves
carry the B32 wrong-fire above.

## 7. B32 — the version's principal negative discovery

**Positional plan replay is structurally unsafe.** Templatized plans
(question numbers → regex groups, plan literals kept when
whitelist-small) served wrong answers three ways, all one family:

1. **Donor-constant swap**: a template's whitelist-small literals
   (rates 2–7%, small multipliers) differ from the matched question's
   — G-P4's |magnitude| honesty cannot see it because the whitelist
   exempts exactly those numbers.
2. **Role misbinding**: groups bind numbers that all appear in the
   question — in the wrong roles (rate↔years↔multiplier swaps).
3. **Dropped dual-role usage** (haiku's 13 plan wrongs): one stated
   number used in two roles lets a plan that drops a usage pass.

A `--strictreplay` fix (every bound slot value must be stated in the
question) was verified on dev: it closes subset 1 (wrong-fire 0.73%
→ 0.46% on a 5k probe) but **cannot** close 2 or 3 — no
literal-presence filter sees roles. The composer is role-aware and
served 112,170 sealed chains at zero wrong. **Safe plan reuse must
bind by role, not position — that is V1.8's problem statement.**

## 8. Minting and connectors

Admitted chain reflexes: haiku 0, sonnet 37, opus 60 (0 wrong-kills
in its gauntlet — opus end-anchored every pattern unprompted), fable
52; union 149. Connector reflexes: proposed by all models, all inert
— the composer already performs final-unit conversion, so the class
had nothing to repair (an honest null: free-hand invention found no
gap where the user hypothesized one). B31 (a minted chain serving
the prefix of a longer chain) was caught in dev, fixed structurally
in gauntlet AND serving path, and never recurred.

## 9. Safety ledger

- SAFETY-1: det arm 0.000 everywhere; R-fable/R-opus under bar;
  **R-haiku 0.80% and R-sonnet 0.63% breach** → outcome E trigger.
- SAFETY-2: **zero** distractors served, all arms, all 4M items.
- SAFETY-3: sonnet/fable/opus sealed plan arms **zero**;
  **haiku 13** → its plan arm fails.
- SAFETY-4: breached by replay-template entries (all wrongs traced,
  ≥3 per failing library).
- GATE-CTRL: all batteries passed before counting; zero uncontained
  engine errors in 4M evaluations (B27 containment held).

Bugs this version: B30 (V1.6 parser served step one of a foreign
chain — routed chain text past the V1.6 path), B31 (minted prefix
serve — whole-question consumption), B32 (replay role-misbinding —
characterized, partially fixed, structurally assigned to V1.8). All
superseded runs preserved (`results/v17/premerge/`,
`superseded_b30/`); every wrong row committed.

## 10. What V1.7 established

1. **Composition is real and safe deterministically**: 30.4% of
   3+-step sealed questions solved end-to-end by chaining certified
   reflexes, zero wrong in 412k+ det serves across the arc's runs.
2. **Models find chain structure fast and mostly safely**: ~4.6–6.5s
   per chain, near-flat in depth; sonnet/fable/opus certified
   93–96% of sealed chains at zero wrong through the gate+witness.
3. **The unsafe layer is reuse, not planning**: every wrong in 4M
   evaluations came from positional template replay or role-blind
   honesty — never from the composer, never from a fresh certified
   plan by the three larger models.
4. **Scale helps everywhere measured**: coverage, template hygiene,
   plan accuracy, and gauntlet discipline all improve monotonically
   from haiku to opus.

## 11. Repro

```
python tools/build_q1m.py                     # data (seed 1700)
python v17_run.py --split seal --arm det      # COHESION (run-once)
python v17_run.py --split <s> --arm R-<m> --mintlib results/v17/stack_<m>.json
python tools/planner17.py score --model <m> --phase sealed
python v17_run.py --split dev --arm R-haiku-strict --mintlib \
  results/v17/stack_haiku.json --strictreplay --limit 5000 --tag probe
```

Environment: Windows 11, Python 3.12, sympy/mpmath/pint pinned as
V1.6. Timing = harness-observed plan-file mtime deltas (B7: no
bridge-reported timing used). Model access via bridge agents only.
