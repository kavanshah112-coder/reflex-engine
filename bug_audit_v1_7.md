# V1.7 bug audit

## B32 — replay templates bind wrong small constants (whitelist blind spot)

**Found:** 2026-09-04, R-haiku million run (first R-arm to finish): WRONG
605/289/937/1238 across acq/dev/seal/replay (~0.8% wrong-fire per
split, ~18.7% of replay-template serves), every wrong row
`mint:chain:haiku_plan_*`. The composer/det path inside the same runs
stayed at zero wrong. Summaries preserved as written
(`R-haiku_*_summary.json`, `R-haiku_*_wrong.json`).

**What happened:** planlib17's templatizer blanks question numbers
into regex groups but leaves plan literals that belong to the
STRUCTURAL whitelist ({0,1,2,0.5,100,1000,9.8,3.6,60} + small ints
0-6) as literals — exactly the anti-value-smuggling carve-out. A
template minted from "interest at 2% over 6 years, multiply by 3"
matches a sibling question with rate 5%, 8 years, no multiplier: the
differing constants are all whitelist-small, so G-P4's stated-number
honesty check cannot flag them, the plan executes cleanly, and the
end-to-end witness verifies the plan's OWN arithmetic — which answers
the DONOR question, not this one. The whitelist that closes
value-smuggling opens constant-swapping: two gates, each individually
sound, compose into a blind spot.

**Status:** the R-<model> arms are pre-registered and run-once; the
sealed numbers stand as found (R-haiku FAILS SAFETY-1: 0.8% > 0.5%).
Structural fix for any superseding run: a replayed plan may serve only
if EVERY numeric literal in the substituted plan (whitelist included)
appears verbatim in the question text or is introduced by a formula's
own physics constants — i.e., the whitelist exemption applies to gate
G-P4's honesty check, never to replay binding.


## B31 — minted chain reflex served a prefix of a longer chain

**Found:** 2026-09-04, minted dev arms: M-sonnet 67 wrong of 42,907
served (all one reflex, `chain_lcm_interest`); M-all inherited them.
Superseded summaries preserved in git history at the commit before
the rerun.

**What happened:** the reflex's pattern was not end-anchored, so on
k=4 questions beginning "Compute the lcm... simple interest..." it
matched the PREFIX and served the 2-step answer — B30's
partial-answer class reappearing inside the minted layer. Probation
(2,000 ACQ offers) never sampled a colliding longer chain; dev's
100k did. Opus end-anchored all its patterns explicitly and had zero
such wrongs — the defect was pattern-hygiene variance between
minters.

**Fix (structural, gauntlet + serving path):** a minted chain match
must CONSUME the whole question (match end within 2 chars of the
stripped text end). Enforced in the gauntlet's probation loop AND in
the runner's replay path, so the class is closed for every minted
chain and every replayed plan, not just the traced reflex — which
this rule renders inert (SAFETY-4 revocation by generalization).
Sonnet re-gauntleted; union rebuilt; arms rerun.

Numbering continues the arc (B1–B29 in prior audits). Superseded runs
preserved; fixes verified offline before reruns.

## B30 — single-step parser served step one of a foreign chain

**Found:** 2026-09-04, first post-merge dev/ACQ runs: 5 wrong of
112,789 served (dev 3 @ 8e-05, ACQ 2 @ 2.7e-05) — the arc's first
nonzero wrong-fire since V1.6's dev loop. Superseded runs preserved
under `results/v17/premerge/` and the post-merge summaries committed
as found.

**What happened:** bridge authors phrase chains like *"Compute
4*(6 + 7). With this as principal p, find p·r·t/100 for r = 2 and
t = 5, and multiply the interest by 6."* V1.6's single-step parser
(`sciparse16` via `gateway16`) matched the LEADING sub-question and
served its value (52 = 4×13) as the whole answer. The V1.6
whole-question-ownership rule was enforced through end-anchored
patterns, and two pattern families own the tail trivially (`.*$`
tails in `_choose2`; greedy env groups in `_eval`), so ownership
silently held while meaning did not. The end-to-end witness cannot
catch it: it verifies the plan that EXECUTED, and a first-step serve
executes a valid single-step plan. Only the gold disagreed — the
V1.3 lesson ("matches the text, not the question") reappearing one
layer down.

**Fix (V1.7 layer; no V1.6 module touched):** chain-marked text is
out of the single-step engine's domain BY DEFINITION — a partial
answer to a chain is a wrong answer. `v17_run` routes any text with
a result-reference or sequential connective ("with this", "from
this", "then", multi-sentence structure) past the entire V1.6 path;
such queries belong to the composer, minted chain reflexes, and
plans, all of which answer the WHOLE question or nothing.

**Verified:** all five texts route to the chain path after the fix;
post-merge dev/ACQ reruns reported in `det_dev_summary.json` /
`det_acq_summary.json` (see report).
