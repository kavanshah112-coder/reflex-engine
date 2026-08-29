# -*- coding: utf-8 -*-
# origin: new for V1.1 — W5 commercial-scale simulation (V1_1_SPEC
# §5, Amendments B & C)
"""100,000-query varied-topic commercial simulation.

  python expsim_v11.py [--wipe]

Product configuration: W1b engine + typed producers (MEMORY.fact,
TEXT.qa) + gauntlet. Definition-family escalations are EXECUTED via
the sonnet bridge, but only until each unique question has K_TXT=3
recorded answers (Amendment C sampling; everything else is PRICED,
not executed — the commercial model). Bridge pass mechanics: pass 1
enqueues the sampled definition prompts; service with
service_bridge.py + sonnet agents; re-run with --wipe until 0
pending. Checkpoints every 10,000: rolling coverage, wrong-fire,
escalation rate, ACTIVE by class, executed/priced escalation tallies.
Sealed finals (g3_*) are evaluated once, at the end. Engine-side
J/query comes from a metered 500-item sample run separately
(exclusive) and is applied in analysis.
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
OUT = HERE / "results" / "expacq11" / "sim"
BRIDGE = HERE / "results" / "bridge_v11"
SIM_MODEL = "claude-sonnet-5"
CHECKPOINT_EVERY = 10000
PROBATION_EVERY = 500
K_TXT = 3


def grade_num(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    if a == 0:
        return abs(v) < 1e-9
    return abs(v - a) / abs(a) <= tol


def grade_item(it, value):
    if it.get("expect") == "text" or it.get("keywords"):
        t = (value or "").lower() if isinstance(value, str) else ""
        return bool(t) and all(k.lower() in t
                               for k in (it.get("keywords") or []))
    if isinstance(value, str):
        # numeric truth served as text (TEXT.qa): grade by
        # first-number extraction (bug_audit_v1_1 B1)
        import re as _re
        m = _re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                       value.replace(",", ""))
        value = float(m.group(0)) if m else None
    return grade_num(value, it.get("answer"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wipe", action="store_true")
    a = ap.parse_args()
    if a.wipe and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    from reflex import acquire as AQ
    from reflex.adapters.anthropic_bridge import \
        AnthropicBridgeAdapter
    from reflex.engine import Engine
    from reflex.gateway import ReflexGateway
    from reflex.packs import loader

    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    bridge = AnthropicBridgeAdapter(model=SIM_MODEL,
                                    bridge_dir=BRIDGE / SIM_MODEL)
    gw = ReflexGateway(bridge, engine=eng)
    traffic = json.loads((DATA / "g2_commercial.json").read_text(
        encoding="utf-8"))
    store = AQ.CandidateStore(OUT / "candidates.jsonl")
    inj = AQ.Injector()
    g = AQ.Gauntlet(store, inj, AQ.make_shadow_eval(eng, grade_num),
                    breeder=eng.breeder)
    g.activate_all_active()
    mem_prod = AQ.MemoryFactTracker()
    txt_prod = AQ.TextQATracker()
    def_answers = {}      # def-question key -> n recorded answers

    logf = open(OUT / "traffic.jsonl", "a", encoding="utf-8")
    shadow_accum = []
    W = {"n": 0, "covered_det": 0, "covered_text": 0,
         "covered_memory": 0, "wrong": 0, "esc_executed": 0,
         "esc_priced": 0, "bridge_pending": 0}
    window = {"n": 0, "cov": 0, "wrong": 0}
    t0 = time.time()
    try:
        for i, it in enumerate(traffic):
            is_shadow = (i % 7 == 3)
            fam = it.get("family", "physmix")
            served = None
            how = None
            r = eng.run_query(it["q"], f"s_{it['id']}")
            v = r.get("numeric_value")
            if v is not None and grade_num(v, it.get("answer")):
                served, how = v, ("memory" if r.get("memory_used")
                                  else "det")
            elif v is not None:
                how = "wrong"
            else:
                key = AQ.TextQATracker.norm_q(it["q"])
                hit = loader.TEXT_QA.get(key)
                if hit is not None:
                    served, how = hit["answer"], "text"
                elif fam == "definition" and \
                        def_answers.get(key, 0) < K_TXT:
                    c = bridge.complete(it["q"], max_tokens=300)
                    if c.pending:
                        W["bridge_pending"] += 1
                        how = "esc_pending"
                    else:
                        W["esc_executed"] += 1
                        def_answers[key] = def_answers.get(key,
                                                           0) + 1
                        if not is_shadow:
                            txt_prod.observe(it["q"], c.text)
                        how = "esc_exec"
                else:
                    W["esc_priced"] += 1
                    how = "esc_priced"
            ok = grade_item(it, served) if served is not None \
                else False
            W["n"] += 1
            window["n"] += 1
            if how == "det":
                W["covered_det"] += 1
            elif how == "memory":
                W["covered_memory"] += 1
            elif how == "text":
                W["covered_text"] += 1
            elif how == "wrong":
                W["wrong"] += 1
                window["wrong"] += 1
            if ok:
                window["cov"] += 1
            if is_shadow and fam != "definition":
                shadow_accum.append(it)
            elif how in ("det", "memory") and served is not None:
                mem_prod.observe(it["q"], [
                    {"concept": f["concept"], "value": f["value"],
                     "unit": f.get("unit")}
                    for f in r["_state"].facts
                    if f["status"] == "CERTIFIED"
                    and f.get("provenance") != "MEMORY"])
            logf.write(json.dumps(
                {"i": i, "id": it["id"], "family": fam,
                 "how": how, "ok": ok}) + "\n")
            if (i + 1) % PROBATION_EVERY == 0:
                newc = mem_prod.harvest(store, inj.W.KINDS9) + \
                    txt_prod.harvest(store)
                g.screen(newc)
                if shadow_accum:
                    g.probation_round(
                        [t for t in shadow_accum
                         if t.get("answer") is not None])
                    shadow_accum = []
            if (i + 1) % CHECKPOINT_EVERY == 0:
                by_class = {}
                for c2 in store.by_status("ACTIVE"):
                    k2 = c2.get("reflex_class", "?")
                    by_class[k2] = by_class.get(k2, 0) + 1
                ck = {"i": i + 1, **W,
                      "window_cov": round(window["cov"] /
                                          max(1, window["n"]), 4),
                      "window_wrong": window["wrong"],
                      "active_by_class": by_class,
                      "t_s": round(time.time() - t0)}
                with open(OUT / "checkpoints.jsonl", "a",
                          encoding="utf-8") as cf:
                    cf.write(json.dumps(ck) + "\n")
                print("checkpoint", json.dumps(ck), flush=True)
                window = {"n": 0, "cov": 0, "wrong": 0}
    finally:
        logf.close()
        store.save()
        g.write_overlay(OUT)
        (OUT / "sim_stats.json").write_text(json.dumps(
            {**W, "bridge": bridge.stats(),
             "pending_now": len(bridge.pending())},
            indent=1), encoding="utf-8")
    if W["bridge_pending"]:
        print(f"BRIDGE PENDING {len(bridge.pending())} — service "
              f"and re-run with --wipe")
        sys.exit(3)

    # sealed finals, once
    for name in ("g3_sim_sealed", "g3_sem_sealed",
                 "g3_adv_sealed"):
        items = json.loads((DATA / f"{name}.json").read_text(
            encoding="utf-8"))
        with open(OUT / f"ms_{name}.jsonl", "w",
                  encoding="utf-8") as f:
            for it in items:
                r = eng.run_query(it["q"], f"sf_{it['id']}",
                                  available=it.get("available"))
                v = r.get("numeric_value")
                served = v
                how = "det"
                if v is None:
                    hit = loader.TEXT_QA.get(
                        AQ.TextQATracker.norm_q(it["q"]))
                    if hit is not None:
                        served, how = hit["answer"], "text"
                expect = it.get("expect", "answer")
                if expect == "abstain":
                    correct = served is None
                else:
                    correct = grade_item(it, served)
                f.write(json.dumps({
                    "query_id": it["id"], "value": served,
                    "how": how, "correct": correct,
                    "answer": it.get("answer"),
                    "keywords": it.get("keywords"),
                    "expect": expect,
                    "family": it.get("family"),
                    "trap_answer": it.get("trap_answer")},
                    default=str) + "\n")
        print(f"sealed {name} done", flush=True)
    print(f"SIM COMPLETE in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
