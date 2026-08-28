# -*- coding: utf-8 -*-
# origin: new for V1.0 — EXP-ACQ arm runner (V1_SPEC §8, V1_PLAN §2)
"""One EXP-ACQ arm per process (in-place injection is process-global):

  python exparms_v1.py --arm A0|A1|A2|A3 [--limit N]

Identical frozen engine (v1.0-parity, pack path) + identical gauntlet
+ identical replayed traffic; ONLY the enabled producers differ:
  A0 none · A1 breeder · A2 miner · A3 both.

Frozen harness parameters (fixed here, before any arm has run):
  SHADOW pool   = traffic items with i % 7 == 3 (held back from BOTH
                  producers; the plan's real-traffic dev split)
  PROBATION     every 500 traffic items; batch = shadow items accrued
                  since the previous round (fresh data every round)
  MINER budget  500 calls/arm, sampled: every 10th escalation
                  (spread across the stream, no front-loading)
  CHECKPOINTS   100/250/500/1000/2500/5000 -> frozen validation probe
                  (n=1000): coverage + wrong-fire with current ACTIVE
                  state
Producers never see validation or sealed items; the miner never sees
answers. Breeder observation uses per-item completion (the v0.11
traffic protocol). After traffic: one evaluation of the three sealed
finals with the arm's final ACTIVE state.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

DATA = HERE / "results" / "expacq" / "data"
ARMS = HERE / "results" / "expacq" / "arms"
CHECKPOINTS = {100, 250, 500, 1000, 2500, 5000}
PROBATION_EVERY = 500
MINE_EVERY = 10
MINER_BUDGET = 500
SHADOW_MOD = 7
SHADOW_RES = 3


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


def probe_validation(eng, val, tag, out_dir, i_at):
    ok = wrong = 0
    for vt in val:
        r = eng.run_query(vt["q"], f"vp_{vt['id']}")
        v = r.get("numeric_value")
        if grade(v, vt.get("answer")):
            ok += 1
        elif v is not None:
            wrong += 1
    row = {"i": i_at, "val_n": len(val), "val_ok": ok,
           "val_wrong": wrong, "t": time.time()}
    with open(out_dir / "checkpoints.jsonl", "a",
              encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    print(f"checkpoint {tag}@{i_at}: ok={ok}/{len(val)} "
          f"wrong={wrong}", flush=True)
    return row


def run_arm(arm, limit=None, miner_model="ollama"):
    """miner_model: 'ollama' (the pre-registered local arms) or an
    Anthropic model id — the H12-lineage SCALE REPLICATIONS of A2,
    reported alongside the primary arms, never swapped into the
    outcome ladder. Only the MINER's proposals change; certification,
    probation, and all engine work stay local and deterministic."""
    from reflex import acquire as AQ
    from reflex.adapters.ollama import OllamaAdapter
    from reflex.engine import Engine

    tag = arm if miner_model == "ollama" else \
        f"{arm}-{miner_model.split('-')[1]}"
    out = ARMS / tag
    out.mkdir(parents=True, exist_ok=True)
    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    traffic = load("expacq_traffic")
    val = load("expacq_val")
    if limit:
        traffic = traffic[:limit]

    store = AQ.CandidateStore(out / "candidates.jsonl")
    inj = AQ.Injector()
    gauntlet = AQ.Gauntlet(store, inj,
                           AQ.make_shadow_eval(eng, grade),
                           breeder=eng.breeder)
    gauntlet.activate_all_active()
    if miner_model == "ollama":
        adapter = OllamaAdapter()
    else:
        from reflex.adapters.anthropic_direct import \
            AnthropicDirectAdapter
        adapter = AnthropicDirectAdapter(model=miner_model)
    miner = AQ.Miner(adapter, store) if arm in ("A2", "A3") else None
    breeder_prod = (AQ.BreederProducer(eng.breeder, store)
                    if arm in ("A1", "A3") else None)

    log_p = out / "traffic.jsonl"
    done = set()
    if log_p.exists():
        for line in log_p.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["i"])
            except Exception:
                continue
    logf = open(log_p, "a", encoding="utf-8")
    shadow_accum, heldout_for_breeder = [], []
    n_esc = n_mine = 0
    stats = {"miner_calls": 0, "tokens_in": 0, "tokens_out": 0}
    t0 = time.time()
    try:
        for i, it in enumerate(traffic):
            if i in done:
                continue
            is_shadow = (i % SHADOW_MOD == SHADOW_RES)
            r = eng.run_query(it["q"], f"tr_{it['id']}")
            v = r.get("numeric_value")
            ok = grade(v, it.get("answer"))
            escalated = not ok
            if escalated:
                n_esc += 1
            if is_shadow:
                shadow_accum.append(it)
            else:
                if breeder_prod is not None:
                    facts = [f for f in r["_state"].facts
                             if f["status"] == "CERTIFIED"]
                    breeder_prod.observe(it["q"], it["id"], facts,
                                         ok)
                if miner is not None and escalated and \
                        n_esc % MINE_EVERY == 0 and \
                        stats["miner_calls"] < MINER_BUDGET:
                    cands = miner.mine(it["q"], inj,
                                       engine_record=r)
                    stats["miner_calls"] += 1
                    n_mine += len(cands)
                    gauntlet.screen(cands)
            logf.write(json.dumps({
                "i": i, "id": it["id"], "ok": ok,
                "abstain": v is None,
                "wrong": (v is not None and not ok)}) + "\n")
            if (i + 1) % PROBATION_EVERY == 0:
                if breeder_prod is not None:
                    newc = breeder_prod.harvest(
                        heldout=[(t["q"], []) for t in
                                 shadow_accum[-40:]])
                    gauntlet.screen(newc)
                if shadow_accum:
                    gauntlet.probation_round(list(shadow_accum))
                    shadow_accum = []
                logf.flush()
                print(f"[{arm}] {i+1}: esc={n_esc} "
                      f"cands={len(store.rows)} "
                      f"active={len(store.by_status('ACTIVE'))} "
                      f"prob={len(store.by_status('PROBATION'))} "
                      f"({time.time()-t0:.0f}s)", flush=True)
            if (i + 1) in CHECKPOINTS:
                probe_validation(eng, val, arm, out, i + 1)
    finally:
        logf.close()
        store.save()
        stats.update(adapter.stats() if miner else {})
        stats["escalations"] = n_esc
        stats["candidates_total"] = len(store.rows)
        for s in ("PROPOSED", "GATE_REJECTED", "PROBATION",
                  "ACTIVE", "REJECTED"):
            stats[f"cand_{s}"] = len(store.by_status(s))
        (out / "arm_stats.json").write_text(
            json.dumps(stats, indent=1), encoding="utf-8")
        gauntlet.write_overlay(out)

    # ---- sealed finals (once, with the arm's final ACTIVE state)
    for name in ("expacq_parse_sealed", "expacq_sem_sealed",
                 "expacq_adv_sealed"):
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
                    "class": it.get("class"),
                    "quadrant": it.get("quadrant"),
                    "template": it.get("template"),
                    "status": r.get("status"),
                    "abstain_reason": r.get("abstain_reason"),
                    "t_ms": round(r.get("t_ms", 0), 2)},
                    default=str) + "\n")
        print(f"[{arm}] sealed {name} done", flush=True)
    print(f"[{arm}] ARM COMPLETE in {time.time()-t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True,
                    choices=["A0", "A1", "A2", "A3"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--miner-model", default="ollama")
    a = ap.parse_args()
    run_arm(a.arm, a.limit, a.miner_model)


if __name__ == "__main__":
    main()
