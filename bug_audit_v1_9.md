# V1.9 bug audit (branch v1.9-reading)

Numbering continues the arc (B1–B36 in prior audits).

## Note N4 — proposer node ids vs the frozen schema (format, canonicalised)

DEV first scoring: 339 of 600 readings gate-killed, 325 of them
`G-P1: nodes never reaching final` — the proposers named nodes `s1`,
`a1`, `t` and the frozen schema recognises references only as
`@n<digits>`, so every reference was invisible and every node
"unreachable". The prompt's example used `n1/n2` but did not state
the rule. Fix: `reader19.bind` renames ids to `n1..nK` in order and
rewrites every `@<old>` reference (A2's renaming, no semantics).
Pre-fix REACH 23.2% / post-fix 69.0%; the pre-fix summary is
superseded (committed in f9b4d70's parent state as the first score).
Not a reading error; recorded because a number changed.

## Note N5 — DEV false-admit anatomy (R6 in action; nothing relabelled)

5 admitted readings disagree with the corpus gold (1.26% of 398):
- a0890 (ASDiv): reading and haiku 5; gold 6. 16−x = 2(11−x) gives
  x = 6, London then 5. The gold looks wrong.
- g1309 (GSM8K): reading and haiku 2,180; gold 2,280.
  430+750+300+700 = 2,180. The gold looks wrong.
- g0368: "three times more points than Sara, who scored 8" — reading
  3×8−14 = 10; gold takes "three times more" as 4× (32−14 = 18).
  Phrasing convention.
- g0768: "Ezra read twice as many as Ahmed … 300 … 150 more" —
  reading Ahmed = 150, total 600; gold recomputes Ahmed from 450
  (675). Phrasing convention.
- g0782: "Chase and Rider … ride thrice a day" — reading counts one
  rider (27); gold counts two (54). A genuine shared misreading:
  the V1.3 class, 1 of 398.
Per R6 the golds are not edited and the frozen FALSE-ADMIT counts
all five. The sealed run decides the letter; this note is the
anatomy the report must carry beside the number.
