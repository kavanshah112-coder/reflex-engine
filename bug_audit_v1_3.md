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

**B3 — dual-parse was vacuous by construction (caught before any
results; the smoke run was stopped mid-flight).** Decision (vi) of the
frozen spec makes every item parsed twice, with AGREEMENT as the first
of five checks and L10 devoted to whether disagreement is a useful
confidence signal. But the local adapter ran at temperature 0 with a
fixed seed, and the bridge adapter keys its cache on the prompt text —
so in both paths the "two independent parses" were byte-identical by
construction. Agreement would have passed 100% of the time, L10 would
have measured nothing, and the headline safety mechanism the user
specifically asked for would have been decorative.

Fixed on both paths: the local adapter now takes per-call `seed` and
`temperature` (verified: different seeds vary the output, the same
seed reproduces it exactly, so samples are independent AND the run
stays deterministic); the bridge adapter takes a `key_salt` that
participates in the cache key but is NEVER sent to the servicing
agent, so two identical prompts land in two slots answered
independently by two different agents.

Lesson, and it generalises past this project: a self-consistency check
is only as real as the independence of the samples it compares.
Nothing in the code would have failed, and every number would have
looked excellent.

**B4 — degenerate ("identity") plans certified as answers. Found on
the first real-language smoke, 20 items.** Six items certified; three
were wrong. Two of the three shared one shape:

    "Adam ran 25 miles more than Katie. Adam ran 35."
        plan: (25 - 35) + 35  ->  25      truth 10
    "Tuition costs $704 more than room and board; total $2,584."
        plan: (2584 - 704) + 704 -> 2584  truth 1644

The model builds a plausible multi-step plan that is algebraically the
IDENTITY and returns one of its own inputs. Every existing check
passed: both samples agreed (the error is systematic, not random),
every value appears in the text, every number is consumed, the plan
converges to one terminal, and the kinds are too generic
(`count`, `money`) for dimensional analysis to engage.

Fixed by a sixth check, `nondegenerate`, run last because it needs the
executed value: reject when the answer equals one of the inputs
exactly (for plans of >= 2 steps), when symbolic reduction collapses
the plan to a bare input, or when the result depends on only one
input. Re-scoring the smoke rows: certified 6 -> 4, wrong 3 -> 1.

**The third wrong answer is not catchable this way and is recorded as
an open class.** "Lillian builds 3 feeders and buys 3 others; each
attracts 20 birds" -> the plan computed `(3 + 20) * 20 = 460`
(truth 150). It is well-formed, non-degenerate, fully consumed, and
dimensionally legal because `count + count` is legal. Nothing
deterministic distinguishes it from a correct plan; catching it needs
a model-based verifier reading the plan against the story. This is the
same class as V1.2's gsm1120 and is the strongest argument yet that
the deterministic checks are necessary but not sufficient once a model
does the reading.
