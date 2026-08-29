# Adaptive Reflex Arc — Hypothesis Ledger V0.1 → V0.11

Historic statuses are reproduced AS RECORDED at the time, from the
in-repo logs (sources cited). Nothing is rewritten with hindsight;
where a later version overturned an earlier reading, both entries
stand and the overturn is noted in the later version's row.

Status key: CONFIRMED / VALIDATED · PARTIAL · FALSIFIED / REFUTED ·
INCONCLUSIVE · NOT TESTED.

## V0.1 (source: ARC_INVENTION_LOG_v01_v04.md)
| Hypothesis | Prediction | Result | Status |
|---|---|---|---|
| Reflex micro-nodes answer recurring numeric queries cheaper than an LLM | cheaper at equal accuracy | hybrid 83.7% vs llama 79.5% at 0.27× FLOPs; reflex-solved ~2950× cheaper | PARTIAL |
| Compute scales cubically with reasoning depth | p≈3 | fitted p≈0.3–0.4 — escalation-driven, not depth-driven | FALSIFIED |

## V0.2
| | | | |
|---|---|---|---|
| Hashed n-grams replace the MiniLM embedder | parity, ~200,000× cheaper | parity (p=0.38), OOD AUROC 0.993 | VALIDATED |
| External error predictor as risk gate | beats native confidence | AUROC 0.89 vs 0.55 | VALIDATED |
| Graph substrate beats cascade end-to-end | e2e win | matched-coverage: most of the win was gate quality; graph-unique value = composition + adversarial containment | PARTIAL (OUTCOME B) |

## V0.3
| | | | |
|---|---|---|---|
| Typed capability registry + forward value-planner | composition of unseen chains | 95.9% e2e; 100% on 62 unseen compositions | VALIDATED |
| Suspect-path rule catches wrong-question routing | kills tax_margin family errors | confirmed at oracle level (V0.4) | VALIDATED |

## V0.4
| | | | |
|---|---|---|---|
| Partial-path planning with typed gap detection | mid-chain gaps delegated | mechanics proven; accuracy advantage config-dependent | PARTIAL |
| Structured LLM handoff (v3 protocol + validation battery) | validated handoff beats free-form | v3 proven (84.3% handoff); v1 REFUTED (harmful) | MIXED (v3 ✓, v1 ✗) |
| Capability breeder with sealed-posttest yield | net-positive bred capabilities | proven by experiment (breeder_v4.json) | VALIDATED |

## V0.5 — energy economics (OUTCOME A)
| | | | |
|---|---|---|---|
| Whole-system energy metering (GPU L2 + CPU L3) | attributable per-query joules | validated; 574 vs 1687 J/correct hybrid vs LLM | VALIDATED |
| Workload-repetition amortization | energy falls with repetition | Regime C reached 0 LLM calls; lifetime zero-LLM operation | VALIDATED (nuance disclosed) |
| Structural reuse beats response caching | structure >> literal | exact-cache 4% hit vs structural reuse | VALIDATED |
| Dependency-aware gap contracts | better gap solves | mixed-negative on sealed | NOT VALIDATED |

## V0.6 — autonomous growth (OUTCOME B)
| | | | |
|---|---|---|---|
| Structural-alignment pattern mining | patterns from traffic without labels | 202 alignments from 2,500 queries; deployment-gated | SUPPORTED |
| Pollution degrades recall before correctness | zero wrong deployments ≤30% | held at every pollution level (re-confirmed V0.9, V0.10) | CONFIRMED (3×) |
| Bootstrap cascade (growth compounds) | compounding self-improvement | partially confirmed / partially falsified | MIXED |

## V0.7 — substrate transfer (OUTCOME E; source: results/v07_invention_log.md)
| | | | |
|---|---|---|---|
| Cross-model substrate creation | big builders build better | capabilities scale with builder | PARTIALLY CONFIRMED |
| Small manager on large-built substrate | within 2pp | inconclusive-by-ceiling; NEGATIVE off-distribution (repaired in V0.8 by typed contracts) | INCONCLUSIVE→(V0.8 ✓) |
| Parameter substitution ("small+substrate = big") | gap closes | gap closure NEGATIVE | FALSIFIED |
| Recognition remains limiting | wall persists at scale | confirmed — the arc's recurring wall | CONFIRMED |

## V0.8 — path manager + indexed supervision (OUTCOME C+E; source: results/v08_invention_log.md)
| | | | |
|---|---|---|---|
| Path Manager reduces full-query LLM calls | step delegation wins | 95.4% vs 5.6% llama-alone; 822 vs 7,116 J/correct | CONFIRMED |
| Typed-expression boundary (I4/I5) is the safety mechanism | raw values unsafe | raw-value I0–I3 stuck at 36–39%; typed 84%+ | CONFIRMED |
| Reflex→Reflex links improve composition | fewer expansions | null (re-confirmed at 1000 caps in V0.9) | FALSIFIED |
| Small LLM supervises larger substrate | retention | 95.9% retention | CONFIRMED |
| Structural recognition breaks the OOV wall | sealed recognition up | R7 83.1% @ 0.29% wrong-fire vs 62.6%/8.7% control; EXTERNAL stays parser-bound 25.9% | PARTIAL |

## V0.9 — SQR / LLM-as-interpreter (OUTCOME F; source: V09_INVENTION_LOG.md)
| | | | |
|---|---|---|---|
| H1 interpreter > engine | accuracy + economics | accuracy ✓ 3/3 models; economics ✗ (SQR costs MORE) | PARTIAL |
| H4 SQR beats the external wall | EXT9 ≥55%, EXT8 ≥40% | EXT9 94% (+52pp); EXT8 88.9%; failed only the ≤2% abstention clause | PARTIAL |
| H7 advantage grows with tier | widening gap | FALSIFIED — depth wall at 5–7 steps (horizon max_depth=5, proven in V0.10 autopsy) | FALSIFIED |
| H8 interpretation narrower than solving | smaller output | SQR output 19–20× LARGER | FALSIFIED |
| H9 transfer-down harmless | no harm | sonnet→llama 83.3%; 125/125 ≤5 steps perfect | CONFIRMED |
| H6 pollution: correctness first | zero wrong deploys | zero at every level through 50% | CONFIRMED |

## V0.10 — integration (OUTCOME F headline; source: invention_log.md)
| | | | |
|---|---|---|---|
| H1 cheap NLP worker replaces LLM SQR | ≤5% parse cost at ≥B accuracy | covered domains: 100% vs B 16.3-58.2% at 0 calls / 0.3 J-per-correct; out-of-family still needs the LLM interpreter (fails safe) | PARTIAL |
| H2 unknown-budget routing cuts LLM use | ≥50% call cut | 100% call cut on sealed (0 escalations), cases fire where designed | CONFIRMED |
| H3 parser reflexes replace NLP parses | ≥30% held-out | 31+9 patterns, 0 wrong deployments, but 12.8% held-out coverage | FALSIFIED at threshold |
| H4 long-path manager breaks the 5-step wall | ≥80% at 7-20 steps | cause=search horizon (autopsy); goal regression linear; sealed 196/196 incl 20-step, all managers | CONFIRMED |
| H5 role validation cuts wrong-role fire | ≤2% executed | ZERO role-trap executions, every system/manager (V0.9 haiku was 7.95%); residual gate failure is contradiction+entity-binding, not role | CONFIRMED (target class) |
| H6 incremental matrices reduce computation | ≥40% cut | 20.3x parse saving; 24.6x transport compression | CONFIRMED |
| H7 targeted steps cheaper than full solves | <0.7x tokens | stronger: 0 steps needed on sealed; on externals typed steps answer precisely where full solves hallucinate impossible items | CONFIRMED |
| H8 energy savings grow with complexity | monotone gap | A diverges (accuracy->0 at depth) while G flat at 0.3 J/correct — V0.9's falsification reversed | CONFIRMED |
| H9 large models still benefit | -30% calls/tokens | haiku +41.3pp AND -100% calls; sonnet -100% calls at equal 100% (gate-excluded from the outcome box) | CONFIRMED (gated) |
| H10 breeder learns language->matrix | ≥10 patterns, 100% precision | 31 patterns, zero conflicts through 50% pollution; coverage clause fails | MIXED |
| H11 structural reuse beats literal caching | ≥80% variant hits | 100% paraphrase+revalued vs exact-only literal; cross-domain null by construction | CONFIRMED |
| H12 small managers execute large substrates | within 2pp | IDENTICAL 100% under 8B/haiku/sonnet at 0 calls on covered domains | CONFIRMED |

Final report: results/v0.10_final_report.md · outcome:
results/processed/v010_outcome.json (headline F: the frozen 2%
adversarial gate excluded every system; all performance bars passed).

## V0.11 — semantic integrity + long-horizon parser (OUTCOME A; source: invention_log_v0_11.md)
| | | | |
|---|---|---|---|
| H1 multi-dim state cuts binding errors | >=80% cut | 44.7% -> 0.000 wrong-exec (p=3e-13) | CONFIRMED |
| H2 fact identity kills false contradictions | <=5% FP | 0% FP; valid-change 100%; canonical-unit conflicts caught | CONFIRMED |
| H3 integrity beats the 2% gate | <=2% | 0.000 on every sealed suite (C1: 40-45%) | CONFIRMED |
| H4 quarantine is local | >=90% containment | 100% both directions, 0 unnecessary abstention | CONFIRMED |
| H6 traffic grows coverage | monotone growth | EXACTLY flat 846/1000 at 100->25,000 | FALSIFIED |
| H7 breeding generalizes held-out | >=10pp lift | 17 patterns, ZERO lift (mechanism: unit-naming already generalizes lexically) | FALSIFIED |
| H10 coverage cuts workload energy | >=20% | 84.1% total saving at all scales; escalations = 99.7% of residual | CONFIRMED (architectural) |
| H11 J/correct beats V0.10 | <= | 0.53 vs 0.75 J/q at equal 100% regression + 39.5pp more coverage | CONFIRMED |
| H12 safety across scale | <=2% | 0 wrong-exec under haiku AND sonnet; I4 held live (all LLM proposals rejected) | CONFIRMED |

V0.11 headline: **OUTCOME A** — the first since V0.5, and the first
with safety + coverage + economics simultaneously. Bugs B2/B3
(harness restriction; unported conversions) caught by the
preserve-supersede-rerun protocol; post-fix chains match ground
truth to machine precision.

## V1.0 (reflex-engine, v1.0-final) — retitled: the ledger now spans V0.1 → V1.0

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| V1-H1 | Integration preserves every arc result | CONFIRMED | 5 sealed suites, zero item diffs ×3 runs; 196/196 @ 0 LLM; 0.403 J/q |
| V1-H2 | Breeder stays falsified (A1≈A0) | CONFIRMED+ | ZERO candidates in 5,000 residual queries (needs completed parses) |
| V1-H3 | Miner lifts certified coverage (A2>A0) | FALSIFIED @ llama-8B | 132 ACTIVE, zero lift; SCALE REPLICATIONS: haiku +5.8pp (p≈4e-9), sonnet +7.2pp (p≈0), monotone |
| V1-H4 | A3 ≥ A2 (complementarity) | trivial (0=0) | breeder inert ⇒ untestable on this stream |
| V1-H5 | Gates necessary (K4 > gated +5pp wrong-fire) | FALSIFIED | ungated = 0 wrong-fire (certification is the backstop); cost = lost coverage (sem −5.3pp, adv −8.2pp) |
| V1-H6 | Wrong-fire 0.000 all gated arms | CONFIRMED | 6 arms × 3 finals + every probe: zero |
| V1-H7 | Break-even ≤ 50 reuses | MIXED | letter 31≤50 (llama) but zero utilization; sonnet: ≈$3.5 for +7.2pp |
| V1-H8 | Loop-close | CONFIRMED | momentum kind+cap mined live, certified, paraphrases 14.0/30.0 |

Outcome (frozen ladder): **C** — integration total, pre-registered
acquisition bet falsified at local scale, channel proven at API scale
at zero safety cost.

## V1.1 (reflex-engine, v1.1-final) — the ledger now spans V0.1 → V1.1

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| J1 | Engine fixes lift V1.0 residual ≥15pp | CONFIRMED++ | +92.8pp; then parse11/OOF 100.0%; 180k sweep: 0 residual, 0 wrong |
| J2 | Post-fix frontier harder for miners | RESOLVED BEYOND | frontier VANISHED in-universe; ablation vacuous (Amendment C) |
| J3 | Opus ≥ sonnet reflex minting (bridge) | CONFIRMED | strict-gate mints: opus 12/20 > haiku 8 > sonnet 6; content high everywhere |
| J4 | MEMORY.fact: omitted constants at 0 wrong | CONFIRMED | 2,776 serves, 0 wrong; 8 constants incl. all material densities |
| J5 | TEXT.qa: repeats at 0 wrong, never displaces functional | CONFIRMED | 4,696 serves; precedence machine-tested; 2 rubric-synonym misses reported |
| J6 | Commercial cost/query falls over 100k | CONFIRMED | coverage 93.5→95.1%; 95.4% energy saving vs pure LLM |
| J7 | Zero wrong-fire everywhere | VIOLATED ONCE (B2), zero post-fix | latent ordinal gap: 1/76 on fresh seed; supersede-rerun → sem 100% |

Outcome: **A** (ladder letter), with the B2 violation stated beside
the headline; open class logged as the arc's top safety item.

## V1.2 (v1.2-final) — the ledger now spans V0.1 → V1.2

| # | Hypothesis | Verdict | Evidence |
|---|---|---|---|
| K1 | Certification sweep zero wrong-fire | CONFIRMED | 10,160 trap items / 65 seeds / 0.000; guard+alias PARITY-PLUS green |
| K2 | Vocab audit finds gaps | CONFIRMED (2) | comparatives closed; capture-hijack keys documented dead |
| K3 | Safety transfers to real language | CONFIRMED | zero-shot 519/520 abstained; post-acq worst track 0.83% ≤ 2%; all wrongs itemized |
| K4 | Real coverage (no bars) | 0.0% sealed | all tracks, both arms; TEXT.qa serves repeats only (19/arm traffic) |
| K5 | Acquisition lifts real coverage | FALSIFIED both arms | gap = arithmetic composition; SCALE INVERSION: opus 17 vs sonnet 7 traffic wrongs, +1 sealed |
| K6 | < 1.0 J/certified serve | CONFIRMED | 0.356±0.018 protocol; 0.0211±0.0009 batch-true (~21 mJ) |
| K7 | certify.py regenerates | CONFIRMED | verdict CERTIFIED + one-page certificate |

Outcome: **B** — safety + economics transfer to real human language;
acquisition is in-universe-bound. "Dimensional gates certify physics,
not story semantics" = V1.3's problem statement.
