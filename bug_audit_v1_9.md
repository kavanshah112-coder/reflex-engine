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
