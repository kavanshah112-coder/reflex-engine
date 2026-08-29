# -*- coding: utf-8 -*-
# origin: new for V1.1 — W4 arm runner (V1_1_SPEC §4)
"""V1.1 ablation arms on G1 (the post-fix residual frontier).

  python exparms_v11.py --arm B0|B1|B2 [--miner-model ollama]
  python exparms_v11.py --arm B2 --miner-model bridge:claude-haiku-4-5
  python exparms_v11.py --arm B2 --miner-model bridge:claude-opus-5 --wipe

Bridge arms (per user directive: NO API keys in V1.1) run in passes:
pass 1 enqueues mining prompts (adapter returns pending, no
candidates), the queue is serviced by matching-model agents, then the
arm re-runs with --wipe until 0 pending. Frozen cadence identical to
V1.0 (shadow i%7==3, probation/500, miner 500 @ every 10th
escalation). Typed producers (MEMORY.fact, TEXT.qa) observe in all
mining arms; TEXT.qa answers come only from real escalation replies,
which on G1 numeric traffic do not arise (no text items) — the class
exercises fully in W5.
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

DATA = HERE / "results" / "expacq11" / "data"
ARMS = HERE / "results" / "expacq11" / "arms"
BRIDGE = HERE / "results" / "bridge_v11"
CHECKPOINTS = {100, 250, 500, 1000, 2000}
PROBATION_EVERY = 500
MINE_EVERY = 10
MINER_BUDGET = 500


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    if a == 0:
        return abs(v) < 1e-9
    return abs(v - a) / abs(a) <= tol


def load(name):
    return json.loads((DATA / f"{name}.json").read_text(
        encoding="utf-8"))


def run_arm(arm, miner_model, wipe=False):
    from reflex import acquire as AQ
    from reflex.engine import Engine
    from reflex.packs import loader

    if miner_model.startswith("bridge:"):
        model = miner_model.split(":", 1)[1]
        tag = f"{arm}-br-{model.split('-')[1]}"
    else:
        model = miner_model
        tag = arm if model == "ollama" else \
            f"{arm}-{model.split('-')[1]}"
    out = ARMS / tag
    if wipe and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    traffic = load("g1_traffic")
    val = load("g1_val")
    store = AQ.CandidateStore(out / "candidates.jsonl")
    inj = AQ.Injector()
    g = AQ.Gauntlet(store, inj, AQ.make_shadow_eval(eng, grade),
                    breeder=eng.breeder)
    g.activate_all_active()

    miner = None
    adapter = None
    if arm == "B2":
        if miner_model.startswith("bridge:"):
            from reflex.adapters.anthropic_bridge import \
                AnthropicBridgeAdapter
            adapter = AnthropicBridgeAdapter(
                model=model, bridge_dir=BRIDGE / model)
        elif model == "ollama":
            from reflex.adapters.ollama import OllamaAdapter
            adapter = OllamaAdapter()
        else:
            raise SystemExit("V1.1 uses bridge for API models "
                             "(no keys) — use bridge:<model>")
        miner = AQ.Miner(adapter, store)
    breeder_prod = (AQ.BreederProducer(eng.breeder, store)
                    if arm == "B1" else None)
    mem_prod = AQ.MemoryFactTracker()
    txt_prod = AQ.TextQATracker()

    logf = open(out / "traffic.jsonl", "a", encoding="utf-8")
    shadow_accum = []
    n_esc = 0
    n_mine_calls = 0
    stats = {}
    t0 = time.time()
    try:
        for i, it in enumerate(traffic):
            is_shadow = (i % 7 == 3)
            r = eng.run_query(it["q"], f"tr_{it['id']}")
            v = r.get("numeric_value")
            ok = grade(v, it.get("answer"))
            if not ok:
                n_esc += 1
            if is_shadow:
                shadow_accum.append(it)
            else:
                if ok:
                    mem_prod.observe(it["q"], [
                        {"concept": f["concept"],
                         "value": f["value"],
                         "unit": f.get("unit")}
                        for f in r["_state"].facts
                        if f["status"] == "CERTIFIED"])
                if breeder_prod is not None:
                    facts = [f for f in r["_state"].facts
                             if f["status"] == "CERTIFIED"]
                    breeder_prod.observe(it["q"], it["id"], facts,
                                         ok)
                if miner is not None and not ok and \
                        n_esc % MINE_EVERY == 0 and \
                        n_mine_calls < MINER_BUDGET:
                    cands = miner.mine(it["q"], inj,
                                       engine_record=r)
                    n_mine_calls += 1
                    g.screen(cands)
            logf.write(json.dumps(
                {"i": i, "id": it["id"], "ok": ok,
                 "wrong": (v is not None and not ok)}) + "\n")
            if (i + 1) % PROBATION_EVERY == 0:
                newc = mem_prod.harvest(store, inj.W.KINDS9) + \
                    txt_prod.harvest(store)
                if breeder_prod is not None:
                    newc += breeder_prod.harvest(
                        heldout=[(t["q"], []) for t in
                                 shadow_accum[-40:]])
                g.screen(newc)
                if shadow_accum:
                    g.probation_round(list(shadow_accum))
                    shadow_accum = []
                print(f"[{tag}] {i+1}: esc={n_esc} "
                      f"cands={len(store.rows)} "
                      f"active={len(store.by_status('ACTIVE'))} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            if (i + 1) in CHECKPOINTS:
                okv = wrv = 0
                for vt in val:
                    rv = eng.run_query(vt["q"], f"vp_{vt['id']}")
                    vv = rv.get("numeric_value")
                    if grade(vv, vt.get("answer")):
                        okv += 1
                    elif vv is not None:
                        wrv += 1
                with open(out / "checkpoints.jsonl", "a",
                          encoding="utf-8") as cf:
                    cf.write(json.dumps(
                        {"i": i + 1, "val_ok": okv,
                         "val_wrong": wrv,
                         "val_n": len(val)}) + "\n")
                print(f"[{tag}] checkpoint {i+1}: {okv}/{len(val)} "
                      f"wrong={wrv}", flush=True)
    finally:
        logf.close()
        store.save()
        stats = {"escalations": n_esc,
                 "miner_calls": n_mine_calls,
                 "candidates_total": len(store.rows)}
        for s in ("GATE_REJECTED", "PROBATION", "ACTIVE",
                  "REJECTED"):
            stats[f"cand_{s}"] = len(store.by_status(s))
        if adapter is not None:
            stats["adapter"] = adapter.stats()
            if hasattr(adapter, "pending"):
                stats["bridge_pending"] = len(adapter.pending())
        by_class = {}
        for c in store.by_status("ACTIVE"):
            by_class[c.get("reflex_class", "?")] = \
                by_class.get(c.get("reflex_class", "?"), 0) + 1
        stats["active_by_class"] = by_class
        (out / "arm_stats.json").write_text(
            json.dumps(stats, indent=1), encoding="utf-8")
        g.write_overlay(out)

    # sealed finals
    for name in ("g1_parse_sealed", "g3_sem_sealed",
                 "g3_adv_sealed"):
        items = load(name)
        with open(out / f"ms_{name}.jsonl", "w",
                  encoding="utf-8") as f:
            for it in items:
                r = eng.run_query(it["q"], f"sf_{it['id']}",
                                  available=it.get("available"))
                v = r.get("numeric_value")
                expect = it.get("expect", "answer")
                f.write(json.dumps({
                    "query_id": it["id"], "value": v,
                    "correct": (grade(v, it.get("answer"))
                                if expect == "answer"
                                else v is None),
                    "answer": it.get("answer"), "expect": expect,
                    "trap_answer": it.get("trap_answer"),
                    "status": r.get("status"),
                    "abstain_reason": r.get("abstain_reason")},
                    default=str) + "\n")
        print(f"[{tag}] sealed {name} done", flush=True)
    if stats.get("bridge_pending"):
        print(f"[{tag}] BRIDGE PENDING: "
              f"{stats['bridge_pending']} — service the queue and "
              f"re-run with --wipe", flush=True)
    print(f"[{tag}] ARM COMPLETE in {time.time()-t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["B0", "B1", "B2"])
    ap.add_argument("--miner-model", default="ollama")
    ap.add_argument("--wipe", action="store_true")
    a = ap.parse_args()
    run_arm(a.arm, a.miner_model, a.wipe)


if __name__ == "__main__":
    main()
