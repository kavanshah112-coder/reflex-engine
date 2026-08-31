# Bug audit — V1.3

Opened at plan freeze (tag `v1.3-plan`, 4e8b507). Arc protocol:

- Every defect found is recorded here, whether it was caught before or
  after first results.
- A defect found AFTER first results triggers
  **preserve-supersede-rerun**: the original outputs are moved to a
  `superseded_<tag>/` directory and kept, the fix is made, the
  affected work is re-run, and both readings stand in the record.
- Fixes that the PARITY-PLUS battery rejects are recorded as
  *attempted and reverted*, with the mechanism that rejected them —
  V1.2's reverted unparsed-quantity guard is the precedent.
- Nothing is deleted. Nothing is quietly re-run.

Protocol invocations in the arc: 5 (V0.11 B2/B3, V1.1 B1/B2, V1.3 B1).

## Findings

**B1 — the `fine` recurrence signature was degenerate (found at the
first W0 run; supersede invoked).** `fine` returned exactly the same
partition as `medium` (359 distinct structures, identical coverage)
because the literal/derived marker it added was fully determined by
the unit class already in `medium` — the two levels could never
differ. A three-granularity measurement was really a two-granularity
one, and the "lower bound on reuse" was not a lower bound at all.
Fixed by giving `fine` real discrimination: a derived operand now
carries **dataflow linkage** — which earlier step produced it, as a
relative offset, or `nested` for an in-expression sub-result — so a
linear chain (a→b→c) is distinguished from a tree (a,b→c). Original
outputs preserved in `results/v13/superseded_B1/`.

*Incident during the fix, recorded because it is the dangerous
class:* the first fix was applied by a patch script whose match
string did not match the file exactly. It **failed silently and
partially** — the emission code updated while the function it read
from did not — which swapped the meanings of `medium` and `fine` and
caused the W0 gate to be evaluated against the wrong metric (it still
printed PASS, at 97.5%). Caught by noticing that `medium` had *fewer*
distinct structures than `coarse`-adjacent expectations and that the
level ordering was inverted. Re-applied as an exact edit and
re-verified. Lesson: a silently half-applied patch is worse than a
failed one, because the run still succeeds and still prints a verdict.

**B2 — ASDiv reference formulas were being mangled rather than
parsed.** ASDiv's `Formula` field carries parenthetical unit
annotations (`2*60 (min/hour) + 34 (min) = 154 (min); ...`),
semicolon-separated multi-clause solutions, and fully algebraic
statements (`x:The larger number; x-y=70; x=6y`). The original code
stripped every non-arithmetic character and parsed whatever remained,
which for some items produced a *structurally wrong but syntactically
valid* signature. Fixed: annotations stripped, clauses split, and any
clause that is algebraic or word-bearing is **refused rather than
mangled**.

Consequence, reported rather than buried: the stricter parser lowered
the parsed count from 784 to 726 of 944 numeric items. The earlier,
higher count was partly bogus. 218 items (213 ASDiv, 5 GSM8K) remain
structurally unmeasurable from their own reference solutions.

*Standing limitation this creates:* W0's recurrence figures describe
77% of numeric traffic. The unmeasured 23% skews toward algebraic and
multi-clause problems, which are plausibly *less* repetitive than
average — so 83.3% should be read as an upper-leaning estimate, and
the report must say so.
