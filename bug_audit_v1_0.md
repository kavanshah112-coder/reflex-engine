# Bug audit — V1.0

No defect was found AFTER first sealed results in any arm; nothing
required the preserve-supersede-rerun protocol this version. All
findings below occurred pre-sealed (build/demo phase) or are
cosmetic, and are recorded for completeness.

**B1 (pre-experiment, demo phase): shadow evaluation was blind to
coverage regression.** The original shadow check counted only new
WRONG answers, so candidates that degraded parsing into ABSTENTIONS
confirmed cleanly and went ACTIVE (the "brick_mass aliased kg"
composition hazard: 44 harmless-but-poisonous candidates, "7 kg"
made ambiguous). Fixed before any experiment data existed:
alias/unit-collision + redundancy static gates, and shadow
confirmation now requires zero lost coverage. The probation numbers
frozen in V1_PLAN (N=3, 2 resets) were unchanged.

**B2 (pre-experiment): demo transcript KeyError** on second-pass
gate history ('gate' vs 'gate_with_deps') — crashed the demo script
after mining; script fix only, no data affected.

**B3 (pre-data, recorded as Amendment 1 in expgen_v1.py): generator
pool undersized.** The frozen 6,500-residual requirement met the
loud-failure assert at the measured 83.4% pool coverage; pool
enlarged 20,500 -> 45,000 BEFORE any split file was written. Seeds,
filter, and split sizes unchanged.

**Cosmetic (recorded, unfixed by design during the run):**
- Duplicate ACTIVE payloads: identical proposals mined from
  different queries each pass probation independently (injection is
  idempotent, so behavior is unaffected; wasteful). Dedup-at-gate is
  V1.1 work.
- Dead unit-index entries: candidates like unit "V" pass gates as
  novel keys but runtime lookups lowercase to the already-indexed
  "v", so the entry is unreachable (harmless).
- K4's "62/38 unique proposals applied" counts unique payloads after
  exact-JSON dedup of the miner's heavy repetition; the full row
  counts (2,306 / 1,014) are in the arm stores.

**Engine-freeze amendments (see violation_log.md):** two
engine-wrapper additions were made AFTER the v1.0-parity tag but
BEFORE EXP-ACQ dataset generation (acquired-kind target recovery;
wrong-target override). Both are gated to acquired kinds — they
cannot fire on base-pack traffic — and the full parity battery was
re-run green after each. Without them, new_kind candidates could
never become answer targets, which would have rigged EXP-ACQ against
the miner for a reason unrelated to acquisition quality.
