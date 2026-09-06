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
