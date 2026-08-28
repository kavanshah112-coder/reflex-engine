# -*- coding: utf-8 -*-
"""V0.6 experiment driver (E2 traffic+generations, E4 evals, E7 pathfind,
E8 composition).

Stage traffic:
  Run the V0.6 system over v0.6_traffic with generation boundaries at
  [150, 400, 800, 1500, 2500]. At each boundary the breeder runs ALL
  targets on the records so far:
    T1/T2 patterns+lexemes (alignment mining vs the CURRENT registry,
          gated by gates6 on probes + v0.4 validation)
    T3    capabilities (V0.5 robust breeder + its gates)
    T4    links (typed, support-thresholded)
    T5    compositions (validated candidates; NOT deployed into the live
          registry — redundancy control, measured separately in E8)
  Artifacts per generation: patterns_gen{k}.json, registry_gen{k}.json,
  links_gen{k}.json, compositions_gen{k}.json, genstats with lineage.

Stage evals (pre-registered):
  hybrid sealed6: a_llm_only, v5_frozen (V5Engine), v6 gen0 config,
                  v6 FINAL generation
  pure sealed6:   every generation (cheap)
  external:       FINAL generation + v5_frozen + a_llm_only (frozen set,
                  evaluated exactly once at the end)
  probes:         every generation, pure (paraphrase/revaluation/negative)

Resumable throughout; all runs energy-metered with the V0.5 meter.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "v0_1"))
import v4  # noqa: F401,E402
from v4 import registry_v4 as R4                 # noqa: E402
from v5.energy import PowerMeter, total_j        # noqa: E402
from v5 import llm5                              # noqa: E402
from v5.engine5 import V5Engine, LLMOnly         # noqa: E402
from v6.breeder6 import breed_caps_grouped as breed_caps  # noqa: E402
from v6.engine6 import V6Engine                  # noqa: E402
from v6.patterns import PatternRegistry          # noqa: E402
from v6.breeder6 import (mine_patterns, mine_links,  # noqa
                         mine_compositions)
from v6.gates6 import deploy_patterns            # noqa: E402
from v6.concepts import ConceptGraph             # noqa: E402
from v6.capgraph import CapGraph                 # noqa: E402

RAW = ROOT / "results" / "raw_v6"
DATA = ROOT / "data"
PHASES = [150, 400, 800, 1500, 2500]


def load_items(name):
    return json.loads((DATA / f"v0.6_{name}.json").read_text(
        encoding="utf-8"))


def _load_records(tag):
    p = RAW / f"{tag}.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def done_ids(tag):
    return {r.get("query_id") for r in _load_records(tag)}


def _registry_from_json(path):
    reg = dict(R4.REGISTRY)
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    for name, spec in loaded.get("capabilities", {}).items():
        if name not in reg:
            reg[name] = spec
    return reg


def _save_registry_json(reg, path, version):
    ser = {name: {k: v for k, v in spec.items()
                  if k not in ("fn", "pre")}
           for name, spec in reg.items()}
    Path(path).write_text(json.dumps(
        {"version": version, "capabilities": ser,
         "hash": R4.registry_hash(reg)}, indent=1, default=str),
        encoding="utf-8")


def newest_generation():
    g = 0
    while (RAW / f"patterns_gen{g + 1}.json").exists():
        g += 1
    pr = PatternRegistry.load(RAW / f"patterns_gen{g}.json") if g else \
        PatternRegistry()
    regp = RAW / f"registry_gen{g}.json"
    reg = _registry_from_json(regp) if regp.exists() else \
        dict(R4.REGISTRY)
    links_p = RAW / f"links_gen{g}.json"
    links = json.loads(links_p.read_text()) if links_p.exists() else []
    return g, pr, reg, links


def make_engine(pr, reg):
    return V6Engine(pattern_registry=pr, mode="partial", integrity=True,
                    depaware=False, max_handoffs=2, registry=reg)


MONEY_GROUP = {"money", "cost_var", "cost_total", "profit", "net_profit",
               "revenue", "interest", "cost_eur", "final_amount",
               "sale_price", "net_interest"}


def _rekey_goal_direct(recs):
    """Label-agnostic T3 mining for GOAL-DIRECT handoffs (spec 11-E).

    Live V0.6 traffic exposed: with OOV asks resolving to generic
    'money', the gap finder proposes money-group kinds as DIRECT goal
    injections (e.g. 'cost_eur' on euro-free energy queries) and the LLM
    answers the WHOLE problem under that label. The expressions are
    often CORRECT (energy*price/3.6e6) but the kind labels are
    heterogeneous garbage, so label-grouped clustering can never breed
    them. Observations whose injection directly produced the final
    answer are re-keyed to the canonical generic kind 'money' — the
    input->output relation is what matters, and money-group asks are
    exactly what a bred money-output capability serves. Applied to a
    COPY; the raw experience log is never rewritten. Deployed from gen3
    onward (bug audit #2)."""
    import copy
    out = []
    for rec in recs:
        path = rec.get("path") or []
        goal_direct = (bool(path) and str(path[-1]).startswith("LLM[")
                       and rec.get("status") == "partial_answer")
        # ALSO: records that fell through to full LLM after an accepted
        # money-group handoff — the V4-lineage engine only answers
        # directly when injected == ak LITERALLY, so cost_eur for a
        # generic 'money' ask failed resume and fell through (bug audit
        # #3); the accepted expression value is still the observation.
        fell_through = (rec.get("status") == "llm_answer"
                        and any(h.get("accepted")
                                and h.get("target_kind") in MONEY_GROUP
                                for h in rec.get("handoffs", [])))
        if not (goal_direct or fell_through):
            out.append(rec)
            continue
        r2 = copy.deepcopy(rec)
        for h in r2.get("handoffs", []):
            if h.get("accepted") and h.get("target_kind") in MONEY_GROUP:
                h["target_kind_original"] = h["target_kind"]
                h["target_kind"] = "money"
        out.append(r2)
    return out


def run_generation_breeder(recs, items_by_id, pr, reg, gen_idx, probes,
                           val_items, traffic_items):
    """All breeder targets; returns (pr, reg, links, stats)."""
    t0 = time.time()
    mine_stats = mine_patterns(recs, items_by_id, reg, pr)
    pr, gate_rep = deploy_patterns(pr, probes, val_items, registry=reg)
    reg_new, cap_stats = breed_caps(_rekey_goal_direct(recs),
                                    traffic_items, reg, gen_idx)
    links = mine_links(recs, reg_new)
    comps = mine_compositions(recs, reg_new)
    stats = {"generation": gen_idx,
             "parent_registry_hash": R4.registry_hash(reg),
             "registry_hash": R4.registry_hash(reg_new),
             "pattern_mining": mine_stats,
             "pattern_gate": {k: v for k, v in gate_rep.items()
                              if k != "dropped"},
             "pattern_gate_dropped": gate_rep.get("dropped", []),
             "patterns": pr.stats(),
             "capabilities": {k: v for k, v in cap_stats.items()
                              if k not in ("provenance",)},
             "cap_provenance": cap_stats.get("provenance", []),
             "links": links, "compositions": comps,
             "breeder_seconds": time.time() - t0}
    return pr, reg_new, links, comps, stats


def stage_traffic(meter):
    llm5.activate_best()
    traffic = load_items("traffic")
    probes = load_items("probes")
    val_items = json.loads((DATA / "v0.4_validation.json").read_text(
        encoding="utf-8"))
    items_by_id = {i["id"]: i for i in traffic}
    tag = "traffic_stream"
    recs = _load_records(tag)
    done = {r.get("stream_pos") for r in recs}
    gen_idx, pr, reg, links = newest_generation()
    print(f"traffic resume: {len(recs)} records, gen{gen_idx}, "
          f"{len(reg)} caps, patterns {pr.stats()['qpats']}", flush=True)
    if gen_idx == 0 and not (RAW / "patterns_gen0.json").exists():
        RAW.mkdir(parents=True, exist_ok=True)
        pr.save(RAW / "patterns_gen0.json")
        _save_registry_json(reg, RAW / "registry_gen0.json", "gen0")
    meter.calibrate_ambient(10)
    eng = make_engine(pr, reg)
    f = open(RAW / f"{tag}.jsonl", "a", encoding="utf-8")
    start = 0
    for pi, end in enumerate(PHASES):
        for pos in range(start, end):
            if pos in done:
                continue
            it = traffic[pos]
            with meter.window(it["id"]) as w:
                rec = eng.process(it["query"], query_id=it["id"])
            rec["stream_pos"] = pos
            rec["phase"] = pi
            rec["generation"] = gen_idx
            rec["query"] = it["query"]
            rec["energy"] = w.result
            rec["energy_total_j"] = total_j(w.result)
            recs.append(rec)
            f.write(json.dumps(rec, default=str) + "\n")
            f.flush()
            if (pos + 1) % 100 == 0:
                st = pr.stats()
                print(f"  [traffic] {pos+1}/{PHASES[-1]} gen{gen_idx} "
                      f"caps={len(reg)} qpats={st['qpats']['deployed']}",
                      flush=True)
        start = end
        next_gen = pi + 1
        stats_p = RAW / f"genstats_gen{next_gen}.json"
        if (RAW / f"patterns_gen{next_gen}.json").exists():
            gen_idx = next_gen
            pr = PatternRegistry.load(RAW / f"patterns_gen{next_gen}.json")
            reg = _registry_from_json(RAW / f"registry_gen{next_gen}.json")
            eng = make_engine(pr, reg)
            continue
        window = [r for r in recs if r.get("stream_pos", 1e9) < end]
        pr, reg, links, comps, stats = run_generation_breeder(
            window, items_by_id, pr, reg, next_gen, probes, val_items,
            traffic[:end])
        stats["phase_end"] = end
        pr.generation = next_gen
        pr.save(RAW / f"patterns_gen{next_gen}.json")
        _save_registry_json(reg, RAW / f"registry_gen{next_gen}.json",
                            f"gen{next_gen}")
        (RAW / f"links_gen{next_gen}.json").write_text(
            json.dumps(links, indent=1))
        (RAW / f"compositions_gen{next_gen}.json").write_text(
            json.dumps(comps, indent=1))
        stats_p.write_text(json.dumps(stats, indent=1, default=str))
        st = pr.stats()
        print(f"  [gen{next_gen}] caps {len(reg)} "
              f"(+{stats['capabilities'].get('new_caps_deployed')}) "
              f"qpats {st['qpats']['deployed']} "
              f"apats {st['apats']['deployed']} "
              f"lex {st['lexicon']['deployed']} links {len(links)} "
              f"comps {len(comps)}", flush=True)
        gen_idx = next_gen
        eng = make_engine(pr, reg)
        cg = ConceptGraph(reg, pr)
        cg.save(RAW / f"conceptgraph_gen{next_gen}.json")
        CapGraph(reg, links).save(RAW / f"capgraph_gen{next_gen}.json")
    f.close()


def run_system(items, tag, engine, meter, mode_llm="hybrid"):
    done = done_ids(tag)
    todo = [it for it in items if it["id"] not in done]
    if not todo:
        print(f"{tag}: complete")
        return
    print(f"{tag}: {len(todo)} to run")
    f = open(RAW / f"{tag}.jsonl", "a", encoding="utf-8")
    for k, it in enumerate(todo):
        with meter.window(it["id"]) as w:
            rec = engine.process(it["query"], mode_llm=mode_llm,
                                 query_id=it["id"])
        rec["energy"] = w.result
        rec["energy_total_j"] = total_j(w.result)
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        if (k + 1) % 10 == 0:
            print(f"  {tag} {k+1}/{len(todo)}", flush=True)
    f.close()


def stage_evals(meter):
    llm5.activate_best()
    sealed = load_items("sealed")
    probes = load_items("probes")
    gfin, pr, reg, links = newest_generation()
    meter.calibrate_ambient(10)
    # pure per-generation sealed + probes
    for g in range(0, gfin + 1):
        prg = PatternRegistry.load(RAW / f"patterns_gen{g}.json")
        regg = _registry_from_json(RAW / f"registry_gen{g}.json")
        run_system(sealed, f"sealed_pure_gen{g}", make_engine(prg, regg),
                   meter, mode_llm="pure")
        run_system(probes, f"probes_gen{g}", make_engine(prg, regg),
                   meter, mode_llm="pure")
    # hybrid sealed: baselines + final
    run_system(sealed, "sealed_llm_only", LLMOnly(), meter)
    run_system(sealed, "sealed_v5_frozen", V5Engine(
        mode="partial", integrity=True, depaware=True, max_handoffs=2),
        meter)
    run_system(sealed, f"sealed_v6_gen{gfin}", make_engine(pr, reg),
               meter)
    # external (FINAL evaluation only — frozen set)
    ext = load_items("external")
    ext5 = json.loads((DATA / "v0.5_external.json").read_text(
        encoding="utf-8"))
    run_system(ext, "external_llm_only", LLMOnly(), meter)
    run_system(ext, "external_v5_frozen", V5Engine(
        mode="partial", integrity=True, depaware=True, max_handoffs=2),
        meter)
    run_system(ext, f"external_v6_gen{gfin}", make_engine(pr, reg),
               meter)
    run_system(ext5, f"external05_v6_gen{gfin}", make_engine(pr, reg),
               meter)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["traffic", "evals"],
                    required=True)
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    meter = PowerMeter(tag=f"bench6_{args.stage}",
                       raw_dir=RAW / "energy")
    meter.start()
    try:
        if args.stage == "traffic":
            stage_traffic(meter)
        else:
            stage_evals(meter)
    finally:
        meter.stop()


if __name__ == "__main__":
    main()
