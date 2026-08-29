# -*- coding: utf-8 -*-
# origin: new for V1.2 — W2.3 real-language acquisition loop
"""The product loop on REAL human language (3,000-draw stream).

  python realloop_v12.py --model claude-sonnet-5 [--wipe]
  python realloop_v12.py --model claude-opus-5 [--wipe]     # replication

Frozen budget split (300 bridge calls/arm): up to 200 theory-answer
calls (each unique theory question until K_TXT=3 observations) + up
to 100 mining calls (every 24th numeric escalation, gap-directed).
Typed producers + gauntlet live; MEMORY.fact expected inert (it
learns from COVERED traffic, and real-language coverage starts ~0 —
reported, not hidden). Escalations otherwise priced. Bridge pass
mechanics; sealed real-language finals evaluated once per arm at the
end (FULL/UNITS/THEORY).
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
DATA = HERE / "results" / "real" / "data"
BRIDGE = HERE / "results" / "bridge_v11"
K_TXT = 3
BUDGET_ANSWER, BUDGET_MINE = 200, 100
MINE_EVERY = 24
CHECKPOINTS = {500, 1000, 1500, 2000, 2500, 3000}


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
        import re as _re
        m = _re.search(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?",
                       value.replace(",", ""))
        value = float(m.group(0)) if m else None
    return grade_num(value, it.get("answer"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--wipe", action="store_true")
    a = ap.parse_args()
    tag = a.model.split("-")[1]
    out = HERE / "results" / "real" / f"loop_{tag}"
    if a.wipe and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    from reflex import acquire as AQ
    from reflex.adapters.anthropic_bridge import \
        AnthropicBridgeAdapter
    from reflex.engine import Engine
    from reflex.packs import loader
    eng = Engine(resolver=None, redundancy=True, use_breeder=True)
    bridge = AnthropicBridgeAdapter(
        model=a.model, bridge_dir=BRIDGE / f"real_{a.model}")
    store = AQ.CandidateStore(out / "candidates.jsonl")
    inj = AQ.Injector()
    g = AQ.Gauntlet(store, inj,
                    AQ.make_shadow_eval(eng, grade_num),
                    breeder=eng.breeder)
    g.activate_all_active()
    miner = AQ.Miner(bridge, store)
    mem_prod = AQ.MemoryFactTracker()
    txt_prod = AQ.TextQATracker()
    def_answers = {}
    stream = json.loads((DATA / "real_traffic_stream.json")
                        .read_text(encoding="utf-8"))

    n_ans_calls = n_mine_calls = n_esc = pend = 0
    W = {"covered": 0, "text": 0, "wrong": 0, "priced": 0}
    logf = open(out / "traffic.jsonl", "a", encoding="utf-8")
    shadow = []
    t0 = time.time()
    try:
        for i, it in enumerate(stream):
            is_shadow = (i % 7 == 3)
            r = eng.run_query(it["q"], f"rl_{it['sid']}")
            v = r.get("numeric_value")
            served, how = None, None
            if v is not None:
                ok = grade_item(it, v)
                served, how = v, ("covered" if ok else "wrong")
            else:
                key = AQ.TextQATracker.norm_q(it["q"])
                hit = loader.TEXT_QA.get(key)
                if hit is not None:
                    served, how = hit["answer"], "text"
                elif it.get("family") == "theory" and \
                        def_answers.get(key, 0) < K_TXT and \
                        n_ans_calls < BUDGET_ANSWER:
                    c = bridge.complete(it["q"], max_tokens=250)
                    if c.pending:
                        pend += 1
                        how = "pending"
                    else:
                        n_ans_calls += 1
                        def_answers[key] = def_answers.get(key,
                                                           0) + 1
                        if not is_shadow:
                            txt_prod.observe(it["q"], c.text)
                        how = "esc_exec"
                else:
                    n_esc += 1
                    if it.get("family") != "theory" and \
                            n_esc % MINE_EVERY == 0 and \
                            n_mine_calls < BUDGET_MINE and \
                            not is_shadow:
                        cands = miner.mine(it["q"], inj,
                                           engine_record=r)
                        if cands or not bridge.pending():
                            n_mine_calls += 1
                        g.screen(cands)
                    how = how or "priced"
                    W["priced"] += 1
            if how == "covered":
                W["covered"] += 1
            elif how == "wrong":
                W["wrong"] += 1
            elif how == "text":
                W["text"] += 1
            if is_shadow and it.get("answer") is not None:
                shadow.append(it)
            elif how == "covered":
                mem_prod.observe(it["q"], [
                    {"concept": f["concept"], "value": f["value"],
                     "unit": f.get("unit")}
                    for f in r["_state"].facts
                    if f["status"] == "CERTIFIED"
                    and f.get("provenance") != "MEMORY"])
            logf.write(json.dumps({"i": i, "sid": it["sid"],
                                   "how": how}) + "\n")
            if (i + 1) % 500 == 0:
                newc = mem_prod.harvest(store, inj.W.KINDS9) + \
                    txt_prod.harvest(store)
                g.screen(newc)
                if shadow:
                    g.probation_round(list(shadow))
                    shadow = []
            if (i + 1) in CHECKPOINTS:
                by_class = {}
                for c2 in store.by_status("ACTIVE"):
                    k2 = c2.get("reflex_class", "?")
                    by_class[k2] = by_class.get(k2, 0) + 1
                print(f"[{tag}] ck {i+1}: {W} ans_calls="
                      f"{n_ans_calls} mine={n_mine_calls} "
                      f"pend={pend} active={by_class} "
                      f"({time.time()-t0:.0f}s)", flush=True)
    finally:
        logf.close()
        store.save()
        g.write_overlay(out)
        (out / "loop_stats.json").write_text(json.dumps(
            {**W, "ans_calls": n_ans_calls,
             "mine_calls": n_mine_calls,
             "bridge": bridge.stats(),
             "pending_now": len(bridge.pending())},
            indent=1), encoding="utf-8")
    if bridge.pending():
        print(f"[{tag}] BRIDGE PENDING {len(bridge.pending())} — "
              f"service and re-run with --wipe")
        sys.exit(3)

    # sealed real-language finals, once, with the arm's end-state
    for name in ("real_full_sealed", "real_units_sealed",
                 "real_theory_sealed"):
        items = json.loads((DATA / f"{name}.json").read_text(
            encoding="utf-8"))
        with open(out / f"ms_{name}.jsonl", "w",
                  encoding="utf-8") as f:
            for it in items:
                r = eng.run_query(it["q"], f"sf_{it['id']}")
                served = r.get("numeric_value")
                how = "det"
                if served is None:
                    hit = loader.TEXT_QA.get(
                        AQ.TextQATracker.norm_q(it["q"]))
                    if hit is not None:
                        served, how = hit["answer"], "text"
                ok = grade_item(it, served) if served is not None \
                    else False
                f.write(json.dumps({
                    "query_id": it["id"], "value": served,
                    "how": how, "correct": ok,
                    "answer": it.get("answer"),
                    "keywords": it.get("keywords"),
                    "answered": served is not None},
                    default=str) + "\n")
        print(f"[{tag}] sealed {name} done", flush=True)
    print(f"[{tag}] LOOP COMPLETE in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
