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

## B28 — quarantined input ignored; weight served as force (dev run 1)

**Found:** 2026-09-03, first completed dev baseline (10k): 10 wrong
of 4,550 served — all ten the same class. Superseded run preserved
under `results/v16/superseded_dev_run1/`.

**What happened:** builder templates emitted "a acceleration" (dead
article-selection code — `if False` short-circuit always chose "a").
On that slice the engine still PARSED the acceleration (concept
`accel`, value, unit all correct) but assigned it status
**QUARANTINED** — and then served `weight_from_mass` (m·g = mass ×
9.8) as "the force", ignoring a quarantined fact of exactly the input
the asked formula needs. Example: mass 1562, accel 7.0 → served
15307.6 (= 1562 × 9.8), gold 10934 (= 1562 × 7).

**Why it matters:** the dimensional gate cannot catch it (weight is a
force). It is the V1.2 gsm1120 family again — certified, semantically
wrong — arising this time from PARTIAL READS: any phrasing the fact
reader half-parses can trigger it, so foreign phrasings would have
hit it on sealed data.

**Fix (2 parts, both V1.6-layer; frozen Tier A untouched):**
1. `gateway16._unbound_stated_quantity`: a numeric quantity stated in
   the text that no CERTIFIED/DERIVED fact carries escalates the
   query — quarantined counts as UNREAD, because the engine saw the
   value and decided not to trust it. An incomplete read never
   serves. (First guard version counted quarantined facts as bound
   and did not fire; fixed by filtering on status.)
2. `build_q100k` article logic repaired ("an acceleration"); dataset
   regenerated and re-hashed BEFORE any seal run (the seal split had
   never been evaluated; prior hashes were recorded as pre-freeze in
   `hashes_prefreeze.json` and both generations are preserved).

**Verified:** all ten wrong-fire texts now ESCALATED (incomplete
read); healthy force/weight items still serve; dev rerun reported in
`results/v16/baseline_dev_summary.json`.

## B29 — requested-unit guard was end-anchored; foreign phrasing walks past it

**Found:** 2026-09-03, first post-merge runs. S-SCI-dev: 6 wrong of
134 served (4.48%); ACQ: 19 wrong of 26,600 (0.071%) — every single
one the same class: *"Calculate, in kilojoules, the kinetic energy of
a 206 kg mass moving at 32 m/s"* served in JOULES (1000× off).

**Why:** the probe-era guard matched "in <unit>" only at the END of
the question. My own generator always puts it there; human-register
authors put it mid-sentence. The guard existed for exactly this
hazard and the phrasing walked around it — a miniature of the whole
H1 lesson: the guard covered its own grammar, not the domain.

**Fix:** requested unit matched anywhere in the ask; two DIFFERENT
requested units = ambiguous = escalate. Verified on all six S-SCI
phrasings (now served, converted, unit-stamped kJ) with plain-J asks
unaffected. Superseded runs preserved under
`results/v16/superseded_premerge_guard/` before rerun.

Also noted: 5 engine-error containments (B27 machinery working as
designed) on foreign texts, all escalated; reasons now logged per row.

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
