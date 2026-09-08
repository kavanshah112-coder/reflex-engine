# V1.9 bug audit (branch v1.9-reading)

Numbering continues the arc (B1–B36; S1 notes N1–N10 in bug_audit_s1.md).

## Note V1 — DEV A2 wrongs under one model (M-sonnet, 1,800; for the record, nothing tuned)

A2 admitted 948 of 1,260 executed readings; 5 disagree with gold:
- g0552 — "sales over $1000 get you an additional 10% commission":
  reading and sonnet apply 40% to the excess (900); gold applies 10%
  (450). Phrasing convention.
- g0590 — seats needed: reading counts invitees, friends, spouses
  (318); gold adds the host herself (319). **Genuine shared
  misreading** — the class the engine cannot see.
- g0768 — "twice as many … then 150 more": convention (S1 N5).
- g1048 — 21% per year depreciation: reading compounds (9,860.78),
  gold is linear on the original (7,400). Convention.
- g1309 — 430+750+300+700 = 2,180; gold 2,280. Gold error (S1 N5).
By class: 1 genuine, 3 conventions, 1 gold error. A2 by-gold rate
0.53%; genuine 0.11%. DEV is exposed data; the rules are frozen and
were not changed after reading this.

## Note V2 — proposer variance across bridge blocks (R12), sealed readings

Sonnet's sealed reading blocks returned null rates from 9/189
(batches 63–70, GSM8K-heavy) to 123/225 (batches 45–53, ASDiv
word-number and GCD/LCM heavy). Part is corpus mix; part is agent
variance in reading the constant rule — one agent treated "three/six/
ten" as unauthorised word-numbers although 3 and 6 are listed
constants. The prompt for the three later arms states the word→
constant mapping explicitly ("two"→2 … "six"→6, "a week"→7 …); the
sonnet blocks were not re-asked (readings are collected once). The
cost lands in REACH per corpus and is reported; no reading was
changed after the fact.

## Note V3 — SEALED A2 wrongs, M-sonnet (12 of 863; read after the run; nothing relabelled)

- **Gold errata / format (4):** a0375 (7 sets × 7 colours × 6 = 294;
  gold 42 = 7×6), a1332 (reading 2/5 = 0.4; corpus answer "5/2"),
  a1349 (perimeter 2·76 + 42 + 2·42 = 278; corpus formula treats 76
  as a perimeter, gold 90), g0454 (Marin and Nancy each 4/day × 30
  = 240; gold 150).
- **Rounding (4):** a1979, a1983, a1984, a1989 — means; reading exact
  (16.2857…), gold rounded to one decimal (16.3). R10 near-miss.
- **Unit convention (1):** a0175 (46 cents vs $0.46).
- **Interpretation conventions (2):** a1412 (does the father age
  during the 15 years: 45 vs 75), g0012 (break-even year 12 vs first
  earning year 13).
- **Genuine misreading (1):** g1035 — bottles every 3 ft on a 24 ft
  driveway, 5 s per gap: reading counts 8 gaps (40), gold 7 (35). A
  fencepost error the reading and the model's own answer shared.
By-gold FALSE-ADMIT 12/863 = 1.39%; GENUINE-WRONG 1 (0.12%).
SAFETY-GEN fails by one item; the letter follows.

## Note V4 — SEALED A2 wrongs, M-haiku (7 of 811)

Gold errata (3): a0375, a1349, g0454 (as above). Conventions (2):
a0185 (cents vs dollars), a2261 (whether the host counts: gold says
no here, though DEV g0590's gold said yes). Genuine (1): g0790 —
3/5 of 10 groups × 9 members × 2 shells = 108; reading dropped the
members per group (12). Haiku's readings are 89.4% correct vs
sonnet's 95.9%; the engine-only rule A1 admits 47 wrong of 852 for
haiku vs 29 of 882 for sonnet — the same-model answer is what carries
the small model to 7 (H9: scale monotone in reading quality; the
gates alone are not enough at any scale).

## Note V5 — SEALED A2 wrongs, M-opus (13 of 962)

Gold errata (3): a0375, a1349, g0454 (as V3). Gold format (3): a1332
(answer "5/2"), a1327 ("3/7" parsed as 3; reading 3/7 = 0.4286),
a1495 ("1/6" parsed as 1; reading 40/240 = 0.1667). Rounding (4):
a1979, a1983, a1984, a1989. Unit (1): a0175. Conventions (2): a1412
(father ages), g1161 (Abraham: "another 1/4 of his land" read against
the original 80 m² — 140 — where gold reads it against the remaining
40 — 170; the model's own answer shares the reading). Genuine (0).
Opus: READING-CORRECT 98.4%, G-P6 false-abstain 9.8%, GATE-COST
13.4%, A1 968/17 — the highest reading quality of the four arms; A2
13 wrong of which 10 are gold format/errata/rounding, 3 conventions.
