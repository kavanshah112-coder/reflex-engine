# -*- coding: utf-8 -*-
# origin: new for V1.0 — P3 checkpoint: the loop-close demo
"""LOOP-CLOSE (V1_SPEC §6 P3): a reflex mined from a live LLM
escalation, gate-certified, probation-promoted, then answering
previously-uncovered queries deterministically with a certificate.

DEMO TRAFFIC ONLY (V1_SPEC §0.7): numbers here are demo evidence, not
headlines. The sealed EXP-ACQ ablation is the claim-bearing run.

Flow: real parse11_oof abstentions -> gateway escalates to ollama ->
miner (same LLM) proposes structured candidates -> static gates ->
3 shadow batches from held-back traffic (probation) -> ACTIVE ->
re-run ALL prior abstentions; count flips; show one certificate.
Transcript -> results/demo/loop_close_transcript.json
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reflex.packs import loader                       # noqa: E402
loader.apply(HERE / "packs" / "physics")
from reflex import acquire as AQ                      # noqa: E402
from reflex.adapters.ollama import OllamaAdapter      # noqa: E402
from reflex.engine import Engine                      # noqa: E402
from reflex.gateway import ReflexGateway              # noqa: E402
from parity_run import grade                          # noqa: E402

OUT = HERE / "results" / "demo"
N_MINE = 12          # mine from the first N abstentions (demo scope)


def load_oof():
    items = {i["id"]: i for i in json.loads(
        (HERE / "battery/parse11_oof.json").read_text(
            encoding="utf-8"))}
    rows = [json.loads(l) for l in
            (HERE / "results/parity/v1_parse11_oof.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    abst = [items[r["query_id"]] for r in rows if r["value"] is None]
    return items, abst


def shadow_batches(n_batches=3, size=60):
    """Held-back REAL traffic (never the frozen validation set)."""
    traffic = json.loads(
        (HERE / "data/dev_traffic/parse11_traffic.json")
        .read_text(encoding="utf-8"))
    base = 20000                       # far past the v0.11 run's use
    return [traffic[base + i * size: base + (i + 1) * size]
            for i in range(n_batches)]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    transcript = {"started": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "stages": []}
    eng = Engine()
    gw = ReflexGateway(OllamaAdapter(), engine=eng)
    store = AQ.CandidateStore(OUT / "demo_candidates.jsonl")
    inj = AQ.Injector()
    miner = AQ.Miner(gw.llm, store)

    items, abst = load_oof()
    transcript["oof_abstentions_before"] = len(abst)
    print(f"OOF abstentions before: {len(abst)}")

    # ---- stage 1: live escalations + mining
    mined = []
    for it in abst[:N_MINE]:
        a = gw.ask(it["q"], qid=it["id"])
        cands = miner.mine(it["q"], inj)
        mined.extend(cands)
        transcript["stages"].append({
            "stage": "escalate+mine", "id": it["id"],
            "q": it["q"], "gateway_status": a.status,
            "candidates": [{"type": c["type"],
                            "payload": c["payload"]}
                           for c in cands]})
        print(f"  {it['id']}: escalated -> {len(cands)} candidates")

    # ---- stage 2: static gates
    g = AQ.Gauntlet(store, inj, None, breeder=eng.breeder)
    g.screen(mined)
    by = {}
    for c in mined:
        by.setdefault(c["status"], []).append(c)
    print(f"gates: {len(by.get('PROBATION', []))} to probation, "
          f"{len(by.get('GATE_REJECTED', []))} rejected")
    transcript["stages"].append({
        "stage": "gates",
        "probation": [{"type": c["type"], "payload": c["payload"]}
                      for c in by.get("PROBATION", [])],
        "rejected": [{"type": c["type"], "payload": c["payload"],
                      "why": c["history"][-1]["gate"]}
                     for c in by.get("GATE_REJECTED", [])]})

    # ---- stage 3: probation (3 shadow batches of held-back traffic)
    batches = shadow_batches()
    baselines = {}

    def shadow_eval(batch, cand):
        bid = id(batch)
        if bid not in baselines:
            base = {}
            for t in batch:
                r = eng.run_query(t["q"], f"sh_{t['id']}")
                base[t["id"]] = (r.get("numeric_value"),
                                 grade(r.get("numeric_value"),
                                       t.get("answer")))
            baselines[bid] = base
        base = baselines[bid]
        wrong = lift = 0
        for t in batch:
            r = eng.run_query(t["q"], f"sh_{t['id']}_c")
            v = r.get("numeric_value")
            ok = grade(v, t.get("answer"))
            bv, bok = base[t["id"]]
            if v is not None and not ok and (bv is None or bok):
                wrong += 1
            if ok and not bok:
                lift += 1
        return {"wrong": wrong, "lift": lift}

    g.shadow_eval = shadow_eval
    for i, batch in enumerate(batches):
        res = g.probation_round(batch)
        n_act = len(store.by_status("ACTIVE"))
        print(f"probation round {i+1}: "
              f"{len(store.by_status('PROBATION'))} in probation, "
              f"{n_act} ACTIVE, "
              f"{len(store.by_status('REJECTED'))} rejected")
    active = store.by_status("ACTIVE")
    transcript["stages"].append({
        "stage": "probation_done",
        "active": [{"type": c["type"], "payload": c["payload"],
                    "source": c["source"],
                    "authorship": c["authorship"]}
                   for c in active],
        "rejected_in_probation": len(store.by_status("REJECTED"))})

    # ---- stage 4: re-run ALL prior abstentions with ACTIVE reflexes
    flips = []
    still = 0
    for it in abst:
        a = gw.ask(it["q"], qid=f"re_{it['id']}")
        if a.status == "CERTIFIED_REFLEX":
            ok = grade(a.value, it.get("answer"))
            flips.append({"id": it["id"], "q": it["q"],
                          "value": a.value,
                          "answer": it.get("answer"),
                          "correct": ok})
        else:
            still += 1
    correct_flips = [f for f in flips if f["correct"]]
    wrong_flips = [f for f in flips if not f["correct"]]
    print(f"re-run: {len(correct_flips)} now certified-correct, "
          f"{len(wrong_flips)} certified-WRONG, {still} still "
          f"escalate/abstain")
    transcript["reflips"] = {"certified_correct": correct_flips,
                             "certified_wrong": wrong_flips,
                             "still_uncovered": still}

    # ---- stage 5: one full certificate for the report
    if correct_flips:
        ex = correct_flips[0]
        a = gw.ask(ex["q"], qid="loopclose_example")
        transcript["example_certificate"] = {
            "query": ex["q"], "value": a.value,
            "status": a.status,
            "certificate": a.certificate.detail}
        print("example:", ex["q"][:80], "->", a.value,
              f"({a.status})")

    transcript["llm_stats"] = gw.llm.stats()
    g.write_overlay(OUT)      # demo overlay kept OUT of packs/physics
    (OUT / "loop_close_transcript.json").write_text(
        json.dumps(transcript, indent=1, default=str),
        encoding="utf-8")
    closed = bool(correct_flips) and not wrong_flips
    print("LOOP-CLOSE:", "PASS" if closed else
          ("PARTIAL (wrong-fire present!)" if wrong_flips
           else "NOT CLOSED"))
    sys.exit(0 if closed else 1)


if __name__ == "__main__":
    main()
