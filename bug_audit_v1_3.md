# Bug audit — V1.3

Opened at plan freeze (tag `v1.3-plan`, 4e8b507). Arc protocol:

- Every defect found is recorded here, whether it was caught before or
  after first results.
- A defect found AFTER first sealed results triggers
  **preserve-supersede-rerun**: the original outputs are moved to a
  `superseded_<tag>/` directory and kept, the fix is made, the
  affected arms are re-run, and both readings stand in the record.
- Fixes that the PARITY-PLUS battery rejects are recorded as
  *attempted and reverted*, with the mechanism that rejected them —
  V1.2's reverted unparsed-quantity guard is the precedent.
- Nothing is deleted. Nothing is quietly re-run.

Invoked so far in the arc: 4 times (V0.11 B2/B3, V1.1 B1/B2).

## Findings

(none yet)
