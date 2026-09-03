# V1.7 bug audit

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
