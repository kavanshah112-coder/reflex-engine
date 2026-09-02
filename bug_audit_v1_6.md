# V1.6 bug audit

Numbering continues the arc (B1–B26 in prior audits). Superseded runs
are preserved; every fix is verified offline before a rerun.

## B27 — symbolic recursion blowup crashed the first dev run

**Found:** 2026-09-03, first baseline dev run (10k), background task
`bnaon8ogk` — preserved in the session task log.

**What happened:** an `integrate_def` item drove sympy into unbounded
recursion (`evalf` looping over an unevaluated nested `Derivative`,
974 frames) and the RecursionError propagated through
`symcore16.solve`, killing the whole run at item ~? (run died before
writing output).

**Why it matters:** the except-tuple in `solve()` listed arithmetic
failures but not `RecursionError`/`MemoryError`. An engine that
CRASHES on a query it should decline is the same defect family as
serving it — the refusal path existed and was not reachable.

**Fix (2 layers):** `symcore16.solve` catches `RecursionError` (and
`MemoryError`) and refuses with a named reason; `v16_run` wraps
`ask16` so any engine exception counts as `engine_error` + ESCALATED
and is logged, never a dead run and never a serve.

**Verified:** GATE-CTRL re-passes after the fix; the dev run
completes with `engine_errors` reported in the summary (see
`results/v16/baseline_dev_summary.json`).

## Probe findings (pre-counting, 2026-09-02) — fixed before any run

The 200-item probe (temp data, discarded) caught four defect classes
before any counting run; all four fixes are in the probe commit:

1. **Requested-unit mismatch** — "kinetic energy in kilojoules"
   served in J. Fix: gateway honors the asked unit via deterministic
   conversion or escalates.
2. **Concept specificity (gsm1120 class)** — "profit margin" served
   as profit ($ passes the dimensional gate). Fix: noun-evidence
   guard — an embedding or adjacent compound noun in the ask
   escalates.
3. **Parser overreach** — "Which is larger: the integral of …"
   matched the embedded integral mid-sentence. Fix: a match must own
   the question from the start (benign lead-ins only).
4. **Choice asks served numerically** — "Which energy is larger …"
   answered with a joule figure. Fix: CHOICE_ASK guard, comparisons
   are never answered by a number from Tier A.
