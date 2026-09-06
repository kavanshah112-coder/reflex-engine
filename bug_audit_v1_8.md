# V1.8 bug audit

Numbering continues the arc (B1–B32 in prior audits). Superseded runs
preserved; fixes verified offline before reruns.

## B33 — haiku-13 was misdiagnosed in the B32 ledger: it is a FORMULA-SEMANTICS class, not dual-role

**Found:** 2026-09-06, building the haiku-13 positive control
(`tools/probe_b32_18.py`) before any V1.8 counting run. The B32 entry
(V1.7 audit) stated that "the same class explains haiku's 13 sealed
S-PLAN wrongs (a stated number serving two roles satisfies magnitude
honesty while a usage is dropped)". That sentence was written from the
replay-probe survivors, not from the 13 plans. Reading the 13:

- **12 of 13** carry the formula `p * r * t / 100 + p` — the AMOUNT
  (principal plus interest) — where the question asks for "the simple
  interest". Every stated number is consumed in its correct role
  (r=rate, t=years, factors and addends all bound), the end witness
  verifies the plan's own algebra, and the plan is wrong because
  nothing in G-P1..G-P4 knows what simple interest IS. Ids:
  q17_0243564, 0284700, 0296818, 0377177, 0443291, 0496536, 0503107,
  0580957, 0606249, 0832882, 0968553, 0972547.
- **1 of 13** (q17_0410663): the model differentiated `1x^3 - 1x^2`
  itself and emitted `derivative_at` of `3*x**2 - 2*x` — a second
  differentiation. The plan's expression literals 3 and 2 are
  whitelisted small ints under G-P4, and the stated coefficients 1, 1
  are "present" as `point: 1` and `order: 1` — magnitude honesty is
  satisfied by coincidence.

**Consequence for the frozen spec:** H2 predicted that usage
accounting (G-P4') kills 13/13. It kills the 13th (its EXPR literals
consume no stated number in their role) and CANNOT kill the 12 — their
usage is perfect. The haiku-13 battery is a GATE-CTRL positive
control; §9 says a control failure voids reuse serves until fixed.
The fix is not a tweak to usage accounting; it is a missing gate.

**Fix (SPEC AMENDMENT A1, recorded in V18_SPEC.md, dated):** G-P5,
certified formulas. A `formula` node's expr is producer-supplied
physics; V1.7 let it be free-form, which is a producer VALUE in
disguise one level up from V1.3's ban. G-P5 requires every formula
expr to be algebraically equivalent (sympy, symbol for symbol) to an
entry of a frozen certified table — the composer's own `FORM` table
(kinetic energy, potential energy, force, work, power, current, simple
interest) — and requires the question to NAME that kind at least as
many times as the plan uses it. `p * r * t / 100 + p` matches no
certified formula and dies. The 12 are G-P5's positive control; the
13th is G-P4''s.

**Cost, pre-registered honestly:** any fresh model plan using a
formula outside the table (a model-derived rearrangement, a kind not
in the table) now abstains. Reported as a G-P5 kill count per arm.

**Record correction:** the B32 ledger sentence stands as written in
`bug_audit_v1_7.md` (frozen); this entry supersedes its diagnosis of
haiku-13. The B32 mechanism list (donor-constant swap, role
misbinding) is unaffected — those were read from the replay wrongs
directly.

## B34 — sign-blind keyed-slot binding (caught by probation, before any counting run)

**Found:** 2026-09-06, harvest18 probation of the haiku dev+sealed
library on ACQ: 2 candidates revoked for a WRONG bound serve
(`haiku_full_0120` on q17_0670958, `haiku_full_0278` on q17_0855366).
Both questions end "Is the final value greater than **-216**?" /
"**-232**?".

**What happened:** roles18 tokens are MAGNITUDES with the sign kept
in the skeleton (`-#`) as structure. templateize matched the donor's
`compare.b = -216` to the token by magnitude and wrote an unsigned
marker; bind substituted the magnitude, so the served plan compared
against +216. The end witness verified the plan's own comparison; only
the ACQ gold disagreed. Had the two candidates survived, this would
have been a SAFETY-BIND wrong at sealed volume — the class Q3 called
"correct roles, wrong value" and could not name in advance.

**Fix:** a negative donor literal writes a signed marker
(`-$s3|threshold|0`); bind applies the sign. The skeleton guarantees
the question states the number with the same sign (a positive sibling
has skeleton `#`, not `-#`, and never matches). Expression operands
were never affected: their signs are characters in the expression
string. Control `sign` added to controls18 (donor with -216 -> sibling
with -300 binds b = -300 and serves the gold; the positive sibling
gets `no_skeleton`).

**Superseded runs:** the first probation ledgers
(`planlib18_haiku_all.json` with g3_wrong 2 and the dev/all ledgers
of every model) are superseded by the post-fix probation; the pre-fix
files are preserved under `results/v18/superseded_b34/`.

**Lesson (arc):** probation with golds is the only stage that can see
"the plan is right, the number is wrong"; the witness certifies the
plan the engine RAN. B34 is the reason §4.2's probation exists, and
the reason probation must never be skipped for harvest speed.

## Note N1 — harvest-negative battery refined (not a bug; recorded because a control changed)

The first `harvest_neg` run on the canonical union flagged 6 "leaks".
All 6 were plans V1.7's gate had KILLED (`asked in 'kJ'; final
carries None` — a missing unit annotation on a scale/evaluate node),
not witness-certified wrong plans; under A2 their derived-unit
canonical form equals a template certified through another donor of
the same question. The battery's claim is "no witness-certified WRONG
plan enters the library"; it now tests exactly that (gate True and
correct False), and reports gate-killed plans whose canonical form is
in the library as a separate count (evidence that those kills were
decorative, cf. B35). Nothing in the library changed.

## Note N2 — session restart interrupted ten in-flight runs (no output produced)

2026-09-06: the harness process exited while B-{haiku,sonnet,opus,
fable}-all on DEV-L, B-{haiku,sonnet,opus,fable}-dev on SEAL and
B-all-{dev,all} on SEAL were running. v18_run writes rows and
summaries only at the end of an arm, so none of the ten produced any
file; no result was observed. They were relaunched as first runs.
The run-once rule for SEAL is intact: no sealed number existed before
the relaunch.

## B36 — B30 residue: a foreign result-reference the chain marker does not see (inherited; the ONE wrong in V1.8's sealed-class runs)

**Found:** 2026-09-06, B-haiku-dev on REPLAY (run once): WRONG 1 of
193,623 served, path `v16:symcore16`, `WRONG_bind` 0. Item
q17_0568250 (foreign slot): "Calculate 9 × (5 + 2). With m = 57.0 and
this result as v, apply the formula 0.5 × m × v²." Served 63 (= 9×7,
sentence one); gold 113,116.5.

**What happened:** v18_run keeps V1.7's B30 routing verbatim: text is
chain-routed only if it matches the marker ("with this/that", "then",
"the result … multiply", ";") or has ≥3 sentences. "With m = 57.0 and
this result as v" matches none of it, so the text reached the V1.6
single-step engine, which parsed sentence one and served it — B30's
class on a phrasing the marker does not cover. The same item is wrong
by the same path in all four V1.7 million arms (the four
`v16:symcore16` rows of PROBE-B32) and will be in every V1.8
SEAL/REPLAY arm (identical code path). Sizing: 90,290 of Q-1M's chain
items never match the marker (two-sentence "Compute X. Multiply that
by N." chains); V1.6 abstains on all but this one.

**Status of the numbers:** sealed-class runs are run once; they
stand as found. The wrong is on the V1.6 path, not the binder —
SAFETY-BIND is intact; SAFETY-1 on REPLAY is 1/193,623 = 0.0005%
(bar ≤ 0.1%; expectation 0 not met, reported).

**Fix (offline-verified, in v18_run behind the default; `--routing17`
reproduces the sealed runs):** a second marker routes any text that
names "this/that/the result", binds a result "as <role>", or whose
second clause consumes "that/it/the result". Verified: the item now
routes to the chain path, the composer returns None (no grammar for
"×"), and it ESCALATES. 345 foreign chain items remain unrouted by
either marker (phrasings with no result-reference word at all, e.g.
"Multiply by m = 128.0 using the formula m * a"); V1.6 abstained on
all of them in 4M V1.7 evaluations. A DEV-L det18 rerun under the new
routing is the demonstration that the fix costs nothing (reported in
the final report if run).
