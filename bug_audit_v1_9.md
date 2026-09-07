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

## Note N6 — slot tokenizer gaps (REACH cost, frozen with prep)

`reader19.numbers_of` did not expose numbers glued to a unit ("15kg",
"750kg", "300g", "18mph") or decimals without a leading digit
("$.20", ".15"); those items had empty or partial slot maps and the
proposers could only abstain (nulls citing them: g0617, g0627, g0672,
g0043, g0109, g0359, g1215, g1269, g0792). The tokenizer is frozen
with the hashed sample; the cost lands in REACH and is reported, not
patched after the fact.

## Note N7 — proposer self-execution (observed, not a leak)

Several proposer agents evaluated their plans against the batch slot
values "to check they run" before writing them. No gold or answer
file was opened (they had none in their file list), so nothing
leaked; but a proposer that executes its own plan is computing, which
the prompt forbade. The readings stand as written; the behaviour is
recorded because a live loop would want to prevent it structurally
(the proposer should not have an interpreter).

## Note N8 — SEALED false-admit anatomy (8 of 703; the frozen metric counts all eight)

Read after the run; nothing relabelled.
- **Gold errata (3):** a1410 (father = 3×sum; after 5 years 2×sum
  → father 45, gold 15 is the children's sum — and the reading's
  plan `{n0}*3*3` is spurious, right by coincidence); g0749 (12
  groups needed, 6 formed → 6 more; gold 3); g0823 (Sasha 14 + (10−6)
  = 18; gold 14).
- **Convention / format (2):** a1678 (ratio 72:40 — reading 1.8, gold
  9 = the first term of 9:5); g0119 ("30% higher" — reading divides
  by 1.3, gold multiplies by 0.7).
- **Integer semantics (1):** a2266 (45 Starbursts among 18 friends —
  reading 2.5, gold 2 with the remainder eaten by Sean).
- **Genuine shared misreadings (2):** a1505 (walking "around" a
  circular lake = half the circumference; reading and haiku used the
  full circumference); g0894 (mowing multiples 1+3+5 of $6 ignored by
  both).
Shared-prior wrongs are therefore 2 of 703 (0.28%); integer-semantics
and convention cases 3 (0.43%); gold errata 3 (0.43%). The frozen
FALSE-ADMIT is 8/703 = 1.14% and the letter follows it. The
production-loop implication is in the report: agreement admits the
corpus's own mistakes and its conventions as readily as the model's.
