# -*- coding: utf-8 -*-
# origin: new for V1.0 — EXP-ACQ controls (V1_SPEC §8-§9, V1_PLAN §2)
"""K controls, one per invocation (fresh process each — injection is
process-global):

  python k_controls.py K2                 # integrity OFF (C2 semantics)
  python k_controls.py K4 --arm A2        # miner, gauntlet DISABLED
  python k_controls.py K3 --model claude-haiku-4-5   # pure LLM (API)
  python k_controls.py K3 --model ollama [--meter]   # pure LLM local
  python k_controls.py CAL                # miner-energy calibration

K3 grading: the model is asked to end with the final number alone;
the last numeric token is extracted. abstain-expected items answered
= wrong-fire (that is the point of the control).
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

DATA = HERE / "results" / "expacq" / "data"
OUT = HERE / "results" / "expacq" / "controls"
FINALS = ("expacq_parse_sealed", "expacq_sem_sealed",
          "expacq_adv_sealed")


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


def write_rows(tag, name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / f"ms_{name}_{tag}.jsonl", "w",
              encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    n = len(rows)
    wrong_ans = sum(1 for r in rows if r["expect"] == "answer"
                    and r["value"] is not None
                    and not r["correct"])
    ans_abst = sum(1 for r in rows if r["expect"] == "abstain"
                   and r["value"] is not None)
    acc = sum(bool(r["correct"]) for r in rows) / n
    print(f"[{tag}] {name}: n={n} acc={acc:.3f} "
          f"wrong_fire={wrong_ans + ans_abst} "
          f"gate={100 * (wrong_ans + ans_abst) / n:.1f}%",
          flush=True)


def sealed_row(it, v):
    expect = it.get("expect", "answer")
    return {"query_id": it["id"], "value": v,
            "correct": (grade(v, it.get("answer"))
                        if expect == "answer" else v is None),
            "answer": it.get("answer"), "expect": expect,
            "trap_answer": it.get("trap_answer")}


def run_k2():
    """Integrity OFF: parse then certify EVERYTHING with a known
    concept (v0.11 C2 semantics) — what certification buys in the
    integrated engine."""
    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.engine import Engine
    eng = Engine()

    def bypass(st):
        for f in st.facts:
            if f["concept"] not in (None, "UNKNOWN"):
                f["status"] = "CERTIFIED"
    eng._certify = bypass
    for name in FINALS:
        rows = []
        for it in load(name):
            r = eng.run_query(it["q"], f"k2_{it['id']}",
                              available=it.get("available"))
            rows.append(sealed_row(it, r.get("numeric_value")))
        write_rows("K2", name, rows)


def run_k4(arm):
    """Gauntlet DISABLED: every proposal from the arm's miner is
    applied (no gates, no probation), crash-tolerant; then the sealed
    finals. Measures what the gates buy (H5)."""
    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex import acquire as AQ
    from reflex.engine import Engine
    eng = Engine()
    inj = AQ.Injector()
    inj.breeder_ref = eng.breeder
    cands = []
    p = HERE / "results" / "expacq" / "arms" / arm / \
        "candidates.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            cands.append(json.loads(line))
        except Exception:
            continue
    applied = crashed = 0
    seen = set()
    for c in cands:
        key = json.dumps([c["type"], c["payload"]], sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        try:
            inj.apply(c)
            applied += 1
        except Exception:
            crashed += 1
    print(f"[K4-{arm}] applied {applied} unique proposals "
          f"({crashed} failed to apply) of {len(cands)} rows")
    for name in FINALS:
        rows = []
        for it in load(name):
            try:
                r = eng.run_query(it["q"], f"k4_{it['id']}",
                                  available=it.get("available"))
                v = r.get("numeric_value")
            except Exception:
                v = None            # engine crash on an item counts
                #                     as no answer; tallied honestly
            rows.append(sealed_row(it, v))
        write_rows(f"K4-{arm}", name, rows)


K3_PROMPT = ("Solve this problem. Think briefly, then end your reply "
             "with ONLY the final numeric answer (no units) on its "
             "own last line. If it cannot be determined, end with: "
             "CANNOT\n\nPROBLEM: {q}")
NUM_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][+-]?\d+)?")


def extract_num(text):
    if not text:
        return None
    tail = text.strip().splitlines()
    for line in reversed(tail):
        line = line.strip()
        if not line:
            continue
        if "CANNOT" in line.upper():
            return None
        ms = NUM_RE.findall(line.replace("$", ""))
        if ms:
            try:
                return float(ms[-1].replace(",", ""))
            except ValueError:
                return None
        break
    ms = NUM_RE.findall(text.replace("$", ""))
    if ms:
        try:
            return float(ms[-1].replace(",", ""))
        except ValueError:
            return None
    return None


def run_k3(model, meter_on):
    if model == "ollama":
        from reflex.adapters.ollama import OllamaAdapter
        ad = OllamaAdapter()
        tag = "K3-llama"
    else:
        from reflex.adapters.anthropic_direct import \
            AnthropicDirectAdapter
        ad = AnthropicDirectAdapter(model=model)
        tag = f"K3-{model.split('-')[1]}"
    meter = None
    if meter_on:
        from v5.energy import PowerMeter
        meter = PowerMeter(tag=tag, raw_dir=OUT)
        meter.start()
        try:
            meter.calibrate_ambient(20)
        except Exception as e:
            print("ambient calibration failed:", e)
    try:
        for name in FINALS:
            done_p = OUT / f"ms_{name}_{tag}.jsonl"
            done = set()
            if done_p.exists():
                for line in done_p.read_text(
                        encoding="utf-8").splitlines():
                    try:
                        done.add(json.loads(line)["query_id"])
                    except Exception:
                        pass
            OUT.mkdir(parents=True, exist_ok=True)
            f = open(done_p, "a", encoding="utf-8")
            rows_all = []
            try:
                for it in load(name):
                    if it["id"] in done:
                        continue
                    w = meter.window(it["id"]) if meter else None
                    if w:
                        w.__enter__()
                    try:
                        c = ad.complete(K3_PROMPT.format(q=it["q"]),
                                        max_tokens=600)
                    finally:
                        if w:
                            w.__exit__(None, None, None)
                    row = sealed_row(it, extract_num(c.text))
                    row["tokens_out"] = c.tokens_out
                    if w and w.result:
                        row["gpu_j"] = w.result.get("gpu_j")
                        row["cpu_j_model"] = w.result.get(
                            "cpu_j_model")
                    f.write(json.dumps(row, default=str) + "\n")
                    f.flush()
                    rows_all.append(row)
            finally:
                f.close()
            if rows_all:
                write_rows(tag + "_summary", name, rows_all)
    finally:
        if meter:
            meter.stop()
    print(f"[{tag}] done; adapter stats: {ad.stats()}")


def run_cal():
    """Miner-energy calibration: 30 metered llama mining calls on
    escalated-residual queries -> J/call, J/token (the cost axis for
    local mining; API miners are priced by tokens)."""
    from v5.energy import PowerMeter
    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex import acquire as AQ
    from reflex.adapters.ollama import OllamaAdapter
    from reflex.engine import Engine
    import tempfile
    eng = Engine()
    store = AQ.CandidateStore(Path(tempfile.mktemp()))
    inj = AQ.Injector()
    miner = AQ.Miner(OllamaAdapter(), store)
    items = load("expacq_traffic")[:30]
    meter = PowerMeter(tag="miner_cal", raw_dir=OUT)
    meter.start()
    try:
        meter.calibrate_ambient(20)
    except Exception as e:
        print("ambient calibration failed:", e)
    js, toks = [], 0
    try:
        for it in items:
            rec = eng.run_query(it["q"], f"cal_{it['id']}")
            w = meter.window(it["id"])
            w.__enter__()
            try:
                miner.mine(it["q"], inj, engine_record=rec)
            finally:
                w.__exit__(None, None, None)
            if w.result and w.result.get("gpu_j") is not None:
                js.append((w.result.get("gpu_j") or 0) +
                          (w.result.get("cpu_j_model") or 0))
    finally:
        meter.stop()
    st = miner.adapter.stats()
    toks = st["tokens_in"] + st["tokens_out"]
    cal = {"n_calls": len(js), "j_total": sum(js),
           "j_per_call": sum(js) / len(js) if js else None,
           "tokens_total": toks,
           "j_per_token": sum(js) / toks if toks else None,
           "adapter": st}
    (HERE / "results" / "expacq" /
     "miner_energy_calibration.json").write_text(
        json.dumps(cal, indent=1), encoding="utf-8")
    print("calibration:", cal)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("control", choices=["K2", "K3", "K4", "CAL"])
    ap.add_argument("--arm", default="A2")
    ap.add_argument("--model", default="ollama")
    ap.add_argument("--meter", action="store_true")
    a = ap.parse_args()
    if a.control == "K2":
        run_k2()
    elif a.control == "K4":
        run_k4(a.arm)
    elif a.control == "K3":
        run_k3(a.model, a.meter)
    else:
        run_cal()


if __name__ == "__main__":
    main()
