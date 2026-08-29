# Bug audit — V1.1

Two defects found AFTER first sealed results (the sim finals);
both handled under preserve-supersede-rerun. Originals preserved in
`results/expacq11/sim/superseded_W1c/`; the re-evaluation is
`refinals_v11.py`; verdicts in `refinals_verdict.json`.

**B1 — sealed-grading adapter refused text-served numeric answers.**
Numeric definition questions ("How many seconds in an hour?") served
by TEXT.qa reflexes return prose ("3600 seconds..."); the finals
grader passed strings to the numeric comparator, which returns
False, miscounting correct text serves as wrong answers (19 of the
original sim-final "wrong answers" were this). The stored `value`
rows were always faithful. Fix: analysis-side re-grade — numeric
truths served as text are graded by first-number extraction
(the v0.11 B1 precedent: the flag lied, not the data). The same rule
now also applies in-traffic so window metrics count text serves
consistently.

**B2 — ordinal vocabulary gap (LATENT ARC DEFECT, v0.8+ lineage).**
The reference regex matched ordinals first..fifth and 'last' while
the ORDINALS resolution table went to tenth. On fresh-seed sem
finals, "the kinetic energy of the tenth one" matched no reference,
fell through to a GLOBAL solve, consumed the first entity's facts
and returned EXACTLY the bind-trap answer (220,000 vs truth
200,174.5) — one wrong-fire, 1/76 = 1.3% (under the 2% gate; a
violation of the arc's zero standard). Every prior suite seed only
generated first..fifth/last asks, so five versions of sealed
batteries never exercised the gap: a seed-luck hole in a class
believed closed. Fix (W1c): ordinals extended to tenth in the
loader-built regex; the item now resolves entity E10 and answers
200,174.5 exactly. PARITY-PLUS battery re-run green after the fix.
DEEPER ISSUE LOGGED (violation_log, V1.2): an unresolved reference
over a multi-entity state should be treated as ambiguous (abstain),
never fall through to a GLOBAL first-facts solve — the ordinal fix
closes the instance, not the class.
