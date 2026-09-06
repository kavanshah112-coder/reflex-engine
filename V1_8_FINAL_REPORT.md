# V1.8 FINAL REPORT — Role-Aware Reuse

**Pre-registered outcome: C** on the frozen ladder (`V18_SPEC.md` §10, tag `v1.8-plan`, amendments A1–A2). Every threshold below is quoted against its frozen bar.

## Headline

- **Safety:** 11,400,000 evaluations across DEV-L, SEAL and REPLAY; 5,856,742 answers served, 1,640,387 of them by role-aware reuse; **0 binder-attributed wrong answers**; 10 wrong answers in total, all on the inherited V1.6 single-step path on one foreign item (B36: q17_0568250), identical to V1.7's own residue.
- **PROBE-B32:** the 8,842 questions V1.7 answered wrong, through the V1.8 binder: 8,421 served at the gold, 421 abstained, 0 served wrong.
- **RETAIN haiku:** 87.9% (4,406 of 5,012 V1.7 template-served sealed items, 937 of which V1.7 got wrong; all 4,406 now correct) + 29,134 new serves on items V1.7 escalated.
- **RETAIN sonnet:** 89.4% (4,554 of 5,092 V1.7 template-served sealed items, 840 of which V1.7 got wrong; all 4,554 now correct) + 29,230 new serves on items V1.7 escalated.
- **RETAIN opus:** 79.2% (1,886 of 2,380 V1.7 template-served sealed items, 357 of which V1.7 got wrong; all 1,886 now correct) + 32,335 new serves on items V1.7 escalated.
- **RETAIN fable:** 86.3% (3,158 of 3,659 V1.7 template-served sealed items, 542 of which V1.7 got wrong; all 3,158 now correct) + 31,028 new serves on items V1.7 escalated.
- **Coverage (SEAL 300k, run once):** composer alone 37.5%; dev-plan libraries haiku 48.75%, sonnet 48.83%, opus 48.98%, fable 48.96%; dev+sealed-plan libraries haiku 54.92%, sonnet 55.68%, opus 55.85%, fable 55.82%; union (586 templates) 55.61%.
- **COMPOUND:** raw ratio (certified binder serves per plan purchased, SEAL) haiku 60.5, sonnet 59.4, opus 59.4, fable 59.5 — the ≥5 bar is met on every scale; the signature-deduplicated ratio haiku 0.108, sonnet 0.107, opus 0.108, fable 0.108 cannot reach its frozen ≥2 bar by construction (bounded by templates/plans < 1) — a pre-registration defect, reported as the failed criterion it formally is.
- **HARVEST:** union library 586 templates (343 full-chain, 243 sub-chain) from 6,757 certified V1.7 plans; per-model probation on ACQ: zero wrong serves in the final libraries.
- **GAP:** adapter-gap share of escalations 0.00% (10% rule: the adapter arm does not run; V1.7's connector null had a measured reason — the composer never fails on a missing unit edge, it fails for want of a step grammar: structure gap 99.2%).
- **REAL-DIAG:** union-library reach on GSM8K/ASDiv/SciQ = 0 of 4,624 (all `no_skeleton`); unresolved-cue share of stated numbers GSM8K 65%, ASDiv 82%.
- **ENERGY:** measured — see §8.
- **haiku binding arm (§4.4):** vacuous by construction — the deterministic binder never produces a "two candidates" state (skeleton-exact lookup + ordinal roles), so there is no ambiguity for a model to resolve; haiku is reported REDUNDANT for binding (H7).

## 1. What V1.8 set out to do

V1.7 ended with composition proven and reuse broken: every one of its 8,842 wrong answers came from positional template replay (B32). V1.8 built one component — a deterministic role-aware binder (`roles18` + `binder18`) with usage accounting in the gate (G-P4′) — and asked whether the three generation problems that mattered (unsafe reuse, minting only from completed examples, a non-compounding library) close together. Templates are harvested from V1.7's witness-certified plans (`harvest18`): every stated number in the donor question gets a role (unit adjacency or the composer's cue grammar), the plan's literals are replaced by role markers, and a template serves only questions whose skeleton (text with number digits blanked, signs and exponents kept) equals a donor's. No regex over numbers exists anywhere in the path; no model is called inside the binder.

## 2. What was found before any counting run

Four ledger entries and two amendments precede the first sealed number (`bug_audit_v1_8.md`, `V18_SPEC.md` A1–A2):

- **B33 — haiku-13 was misdiagnosed.** The V1.7 ledger said the 13 certified-wrong haiku plans were dual-role drops. Reading them: 12 wrote `p*r*t/100 + p` (the amount) for a simple-interest ask, every number in its right role; the 13th differentiated its expression before calling `derivative_at`. Usage accounting cannot see the 12. **Amendment A1** added gate **G-P5 (certified formulas)**: a formula expression must be sympy-equivalent to the composer's own FORM table and the question must name the kind. Control: haiku-13 dies 13/13 (12 at G-P5, 1 at G-P4′).
- **B34 — sign-blind binding**, caught by probation on ACQ golds: two candidates served "greater than −216?" against +216. Role markers now carry the donor literal's sign; the skeleton keeps `-#` structural. Had probation been skipped, this was a sealed-volume SAFETY-BIND wrong.
- **B35 — an inherited V1.7 gate defect**: G-P3 read "in m/s^2 of a 52 kg mass" as an ask for m/s and killed every force chain (100% of the binder's gate abstentions; V1.7's largest fresh-plan kill class). Fixed inside plangate18 by swapping a continuation-aware unit reader around the plangate17 call; plangate17 stays byte-identical (repro 20,000/0 diffs).
- **Amendment A2 — canonical plan form.** 631 of 655 union collisions were `scale(@x, f)` vs `evaluate("@x*f")`; 24 were unit annotations. Harvest now rewrites multiply-by-marker to `scale` and derives units from upstream (a model unit that disagrees rejects the plan). Within-model collisions went to 0; union collisions 655 → 3.
- **B36 — the one wrong answer of the version**, on the inherited V1.6 path: a foreign item ("… With m = 57.0 and this result as v, apply …") that V1.7's chain marker never routed past the single-step engine, which served sentence one. Identical in all four V1.7 arms (the 4 `v16:symcore16` rows of PROBE-B32). Sealed numbers stand as found; a second marker is in v18_run behind the default (`--routing17` reproduces).

## 3. Safety — every arm, every set

| arm | library | split | n | served | binder serves | wrong | binder wrong | coverage | distractors served | engine errors |
|---|---|---|---|---|---|---|---|---|---|---|
| det18 | — | devl | 400,000 | 145,745 | 0 | 0 | 0 | 36.54% | 0 | 0 |
| B-haiku-dev | 242 | devl | 400,000 | 192,975 | 47,230 | 0 | 0 | 48.38% | 0 | 0 |
| B-haiku-dev | 242 | seal | 300,000 | 145,710 | 33,540 | 0 | 0 | 48.75% | 0 | 0 |
| B-haiku-dev | 242 | replay | 400,000 | 193,623 | 44,477 | 1 | 0 | 48.58% | 0 | 0 |
| B-sonnet-dev | 248 | devl | 400,000 | 193,367 | 47,622 | 0 | 0 | 48.48% | 0 | 0 |
| B-sonnet-dev | 248 | seal | 300,000 | 145,954 | 33,784 | 0 | 0 | 48.83% | 0 | 0 |
| B-sonnet-dev | 248 | replay | 400,000 | 193,952 | 44,806 | 1 | 0 | 48.66% | 0 | 0 |
| B-opus-dev | 254 | devl | 400,000 | 193,948 | 48,203 | 0 | 0 | 48.62% | 0 | 0 |
| B-opus-dev | 254 | seal | 300,000 | 146,391 | 34,221 | 0 | 0 | 48.98% | 0 | 0 |
| B-opus-dev | 254 | replay | 400,000 | 194,516 | 45,370 | 1 | 0 | 48.80% | 0 | 0 |
| B-fable-dev | 251 | devl | 400,000 | 193,900 | 48,155 | 0 | 0 | 48.61% | 0 | 0 |
| B-fable-dev | 251 | seal | 300,000 | 146,356 | 34,186 | 0 | 0 | 48.96% | 0 | 0 |
| B-fable-dev | 251 | replay | 400,000 | 194,478 | 45,332 | 1 | 0 | 48.79% | 0 | 0 |
| B-all-dev | 255 | devl | 400,000 | 194,155 | 48,410 | 0 | 0 | 48.67% | 0 | 0 |
| B-all-dev | 255 | seal | 300,000 | 146,547 | 34,377 | 0 | 0 | 49.03% | 0 | 0 |
| B-all-dev | 255 | replay | 400,000 | 194,741 | 45,595 | 1 | 0 | 48.86% | 0 | 0 |
| B-haiku-all | 554 | devl | 400,000 | 217,718 | 71,973 | 0 | 0 | 54.58% | 0 | 0 |
| B-haiku-all | 554 | seal | 300,000 | 164,146 | 51,976 | 0 | 0 | 54.92% | 0 | 0 |
| B-haiku-all | 554 | replay | 400,000 | 218,637 | 69,491 | 1 | 0 | 54.85% | 0 | 0 |
| B-sonnet-all | 573 | devl | 400,000 | 221,201 | 75,456 | 0 | 0 | 55.45% | 0 | 0 |
| B-sonnet-all | 573 | seal | 300,000 | 166,442 | 54,272 | 0 | 0 | 55.68% | 0 | 0 |
| B-sonnet-all | 573 | replay | 400,000 | 221,761 | 72,615 | 1 | 0 | 55.64% | 0 | 0 |
| B-opus-all | 582 | devl | 400,000 | 221,865 | 76,120 | 0 | 0 | 55.62% | 0 | 0 |
| B-opus-all | 582 | seal | 300,000 | 166,935 | 54,765 | 0 | 0 | 55.85% | 0 | 0 |
| B-opus-all | 582 | replay | 400,000 | 222,459 | 73,313 | 1 | 0 | 55.81% | 0 | 0 |
| B-fable-all | 576 | devl | 400,000 | 221,760 | 76,015 | 0 | 0 | 55.60% | 0 | 0 |
| B-fable-all | 576 | seal | 300,000 | 166,863 | 54,693 | 0 | 0 | 55.82% | 0 | 0 |
| B-fable-all | 576 | replay | 400,000 | 222,363 | 73,217 | 1 | 0 | 55.79% | 0 | 0 |
| B-all-all | 586 | devl | 400,000 | 220,540 | 74,795 | 0 | 0 | 55.29% | 0 | 0 |
| B-all-all | 586 | seal | 300,000 | 166,225 | 54,055 | 0 | 0 | 55.61% | 0 | 0 |
| B-all-all | 586 | replay | 400,000 | 221,469 | 72,323 | 1 | 0 | 55.56% | 0 | 0 |

Wrong-answer ledger of the version: q17_0568250. The B36 item is the only wrong answer in 11,400,000 evaluations; it is served by `v16:symcore16`, never by `bind:*` or `chain:composer`.

## 4. Reuse — RETAIN and what the binder abstains on

| model | V1.7 template serves (SEAL) | of which wrong | V1.8 binder serves on the same items | RETAIN | lost (reason) | new serves on V1.7 escalations |
|---|---|---|---|---|---|---|
| B-haiku-dev vs R-haiku | 5,012 | 937 | 4,406 | 87.9% | no_skeleton 606 | 29,134 |
| B-haiku-all vs R-haiku | 5,012 | 937 | 4,812 | 96.0% | donor_self 36, no_skeleton 164 | 47,164 |
| B-sonnet-dev vs R-sonnet | 5,092 | 840 | 4,554 | 89.4% | no_skeleton 538 | 29,230 |
| B-sonnet-all vs R-sonnet | 5,092 | 840 | 4,875 | 95.7% | no_skeleton 183, donor_self 34 | 49,397 |
| B-opus-dev vs R-opus | 2,380 | 357 | 1,886 | 79.2% | no_skeleton 494 | 32,335 |
| B-opus-all vs R-opus | 2,380 | 357 | 2,217 | 93.2% | donor_self 20, no_skeleton 143 | 52,548 |
| B-fable-dev vs R-fable | 3,659 | 542 | 3,158 | 86.3% | no_skeleton 501 | 31,028 |
| B-fable-all vs R-fable | 3,659 | 542 | 3,480 | 95.1% | donor_self 24, no_skeleton 155 | 51,213 |
| B-all-dev vs R-opus | 2,380 | 357 | 1,886 | 79.2% | no_skeleton 494 | 32,491 |
| B-all-all vs R-opus | 2,380 | 357 | 2,217 | 93.2% | donor_self 20, no_skeleton 143 | 51,838 |

Every item lost from V1.7's template coverage is `no_skeleton`: its skeleton had a single donor and the two-donor rule kept it out of the library. Not one loss is a binding ambiguity — the deterministic binder either has the skeleton or it does not. The coverage cost of honesty (Q1) turned out to be the cost of the two-donor rule, not of role resolution.

## 5. Compounding

- **haiku (dev library, 554 plans purchased):** 33,540 certified binder serves on SEAL = **60.5 per plan**; 145 distinct signatures and 405 distinct skeletons served, 82.8 serves per skeleton; dedup ratio 0.108 against an upper bound of 0.262.
- **sonnet (dev library, 569 plans purchased):** 33,784 certified binder serves on SEAL = **59.4 per plan**; 148 distinct signatures and 416 distinct skeletons served, 81.2 serves per skeleton; dedup ratio 0.107 against an upper bound of 0.260.
- **opus (dev library, 576 plans purchased):** 34,221 certified binder serves on SEAL = **59.4 per plan**; 150 distinct signatures and 420 distinct skeletons served, 81.5 serves per skeleton; dedup ratio 0.108 against an upper bound of 0.260.
- **fable (dev library, 575 plans purchased):** 34,186 certified binder serves on SEAL = **59.5 per plan**; 149 distinct signatures and 419 distinct skeletons served, 81.6 serves per skeleton; dedup ratio 0.108 against an upper bound of 0.259.

The raw ratio is linear in the stream (Fig. 5): a purchased plan keeps serving at a constant rate, which is what amortisation looks like on a stationary synthetic stream. The frozen dedup criterion was ill-posed — deduplicating by structure signature removes the axis along which reuse happens, so the ratio is bounded by (distinct signatures served)/(plans purchased) < 1 and no library could pass. The letter follows the frozen text; the lesson (a threshold must be checked for satisfiability before freezing) joins B24's in the methods ledger. REAL-DIAG supplies the number R11 asked for: on natural text the reach is zero, so the raw ratio is the generator's redundancy, exactly as the caveat said.

## 6. Harvest

| library | plans in | templatized | two-donor candidates | admitted | full | sub | probation wrongs | inert |
|---|---|---|---|---|---|---|---|---|
| haiku dev | 554 | 549 | 244 | 242 | 112 | 130 | 0 | 2 |
| haiku all | 1631 | 1609 | 597 | 554 | 324 | 230 | 0 | 43 |
| sonnet dev | 569 | 564 | 250 | 248 | 118 | 130 | 0 | 2 |
| sonnet all | 1687 | 1678 | 618 | 573 | 338 | 235 | 0 | 45 |
| opus dev | 576 | 573 | 256 | 254 | 120 | 134 | 0 | 2 |
| opus all | 1726 | 1719 | 630 | 582 | 345 | 237 | 0 | 48 |
| fable dev | 575 | 571 | 253 | 251 | 119 | 132 | 0 | 2 |
| fable all | 1713 | 1705 | 624 | 576 | 341 | 235 | 0 | 48 |
| union dev | — | — | — | 255 | 119 | 136 | — | — |
| union all | — | — | — | 586 | 343 | 243 | — | — |

## 7. Gaps, connectors, the haiku arm, real language

Gap classification of the union library's 178,344 DEV-L escalations: structure gap 99.19%, adapter gap 0.00%, binding gap 0.80% (collisions 1380), semantic kill 0.00%. The adapter arm does not run (10% rule): connectors were a null in V1.7 because the composer never fails on a missing type-flow edge — it fails because it has no grammar for the step. The haiku binding arm has no input class (the binder never reaches a two-candidate state), so haiku is redundant for binding by construction. REAL-DIAG: 0 of 4,624 natural-language items reach any template.

## 8. Energy

Lean path (composer + binder + gate + witness), batch-metered with instrument controls on both sides of every batch: J per certified serve 0.110068 (sd 0.002216); J per question, engine only, 0.061242. Amortised J per question with V1.4's measured local-model calls as proxies: 847.944 (producer 64.9 J) / 865.198 (pure answer 1,910 J). The bridge's own draw is unmeasurable from here; the proxies are labelled as such.

## 9. Outcome on the frozen ladder

- SAFETY-B32: pass (0 served wrong of 8,842).
- SAFETY-1: max wrong-fire SEAL 0.00000%, REPLAY 0.00050% (bar ≤0.1%; expectation 0 not met on REPLAY: B36).
- SAFETY-2: 0 distractors served anywhere.
- SAFETY-BIND: 0 binder-attributed wrongs.
- SAFETY-3: fresh-plan arm not re-run this version (no bridge planning); haiku-13 control 13/13 killed under the new gates.
- SAFETY-4: 0 wrongs attributable to any harvested template.
- GATE-CTRL: PASS.
- RETAIN ≥60% on ≥2 scales: pass (haiku, sonnet, opus, fable).
- HARVEST ≥300 union: pass (586).
- COMPOUND raw ≥5: pass; dedup ≥2: **fail by construction** (bounded < 1).
- GAP measured: pass; adapter arm gated off (0.00% < 10%).
- DEVVOL: pass (every arm ran DEV-L 400k before its sealed run).
- ENERGY: measured.

**OUTCOME C.** Safe, retained, harvested, and compounding on the raw ratio — rung C by the letter of a dedup criterion that no library could satisfy. The aggregates say the reuse problem is closed on this corpus; the pre-registration says the compounding claim was mis-specified, and it is right about that.

## 10. What V1.8 claims, and does not

It claims that a witness-certified plan can be served again on a question it was not written for, binding every number by role and never by position, at the composer's standard: 1,640,387 binder serves across 11,400,000 evaluations with zero wrong, including 8,421 of the 8,842 questions V1.7 got wrong. It does not claim compounding on natural language (reach 0), does not claim the dedup criterion was met, and does not claim a fleet energy figure beyond what §8 measured. The binder is a fixed function of the text; what it cannot resolve it abstains on; and the one wrong answer of the version was made by the oldest code in the path, on the phrasing class that code was never asked to see.

## Reproduction

```
python tools/build_devl18.py                 # DEV-L, seed 1800
python tools/probe_b32_18.py                 # PROBE-B32 + haiku-13
python tools/harvest18.py build|probate --model <m> --scope dev|all
python tools/harvest18.py union --scope dev|all
python tools/controls18.py --lib results/v18/planlib18_all_all.json
python v18_run.py --split devl|seal|replay --arm B-<m>-<scope> --lib results/v18/planlib18_<m>_<scope>.json
python tools/retain18.py --model <m> --split seal --arm B-<m>-dev --plans-purchased N
python tools/gapclass18.py --rows results/v18/B-all-all_devl.jsonl --data results/v18/data/devl.jsonl
python tools/realdiag18.py ; python tools/meter18.py
```
