# -*- coding: utf-8 -*-
# origin: new for V1.1 — supersede-and-re-run of the sim sealed
# finals (bug_audit_v1_1: B1 grading adapter, B2 ordinal gap)
"""Re-evaluate the three sim sealed finals with (a) the W1c
ordinal-fixed engine and (b) the corrected grading adapter (numeric
truths served as text are graded by number extraction — the value
rows never lied, the adapter refused strings). Originals preserved
under superseded_W1c/. The sim's acquired reflex state (its
acquired.json overlay) is applied so the finals see the end-of-run
engine, exactly as the original evaluation did."""
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "expacq11" / "data"
SIM = HERE / "results" / "expacq11" / "sim"

NUM_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?(?:[eE][+-]?\d+)?")


def extract_num(text):
    if not isinstance(text, str):
        return None
    ms = NUM_RE.findall(text.replace("$", "").replace(",", ""))
    if not ms:
        return None
    try:
        return float(ms[0])
    except ValueError:
        return None


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


def grade(it, served):
    expect = it.get("expect", "answer")
    if expect == "abstain":
        return served is None
    if expect == "text" or it.get("keywords"):
        t = served.lower() if isinstance(served, str) else ""
        return bool(t) and all(k.lower() in t
                               for k in (it.get("keywords") or []))
    v = served if not isinstance(served, str) else \
        extract_num(served)
    return grade_num(v, it.get("answer"))


def main():
    sup = SIM / "superseded_W1c"
    sup.mkdir(exist_ok=True)
    for name in ("g3_sim_sealed", "g3_sem_sealed",
                 "g3_adv_sealed"):
        src = SIM / f"ms_{name}.jsonl"
        if src.exists() and not (sup / src.name).exists():
            shutil.copy2(src, sup / src.name)

    from reflex import acquire as AQ
    from reflex.engine import Engine
    from reflex.packs import loader
    eng = Engine()
    inj = AQ.Injector()
    inj.breeder_ref = eng.breeder
    acq = json.loads((SIM / "acquired.json").read_text(
        encoding="utf-8"))
    n_applied = 0
    for c in acq:
        try:
            inj.apply(c)
            n_applied += 1
        except Exception as e:
            print("overlay apply failed:", c["type"], e)
    print(f"sim end-state overlay applied: {n_applied} reflexes")

    verdict = {}
    for name in ("g3_sim_sealed", "g3_sem_sealed",
                 "g3_adv_sealed"):
        items = json.loads((DATA / f"{name}.json").read_text(
            encoding="utf-8"))
        rows = []
        for it in items:
            r = eng.run_query(it["q"], f"rf_{it['id']}",
                              available=it.get("available"))
            served = r.get("numeric_value")
            how = "det"
            if served is None:
                hit = loader.TEXT_QA.get(
                    AQ.TextQATracker.norm_q(it["q"]))
                if hit is not None:
                    served, how = hit["answer"], "text"
            ok = grade(it, served)
            rows.append({"query_id": it["id"], "value": served,
                         "how": how, "correct": ok,
                         "answer": it.get("answer"),
                         "keywords": it.get("keywords"),
                         "expect": it.get("expect", "answer"),
                         "family": it.get("family"),
                         "trap_answer": it.get("trap_answer")})
        with open(SIM / f"ms_{name}.jsonl", "w",
                  encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + "\n")
        n = len(rows)
        ok_n = sum(1 for r in rows if r["correct"])
        wf = sum(1 for r in rows
                 if r["expect"] == "answer"
                 and r["value"] is not None and not r["correct"]
                 and not isinstance(r["value"], str)) + \
            sum(1 for r in rows if r["expect"] == "abstain"
                and r["value"] is not None)
        txt_wrong = sum(1 for r in rows
                        if isinstance(r["value"], str)
                        and not r["correct"]
                        and r["expect"] != "abstain")
        verdict[name] = {"n": n, "acc": round(ok_n / n, 4),
                         "wrong_fire_numeric": wf,
                         "text_served_incorrect": txt_wrong}
        print(name, verdict[name])
    (SIM / "refinals_verdict.json").write_text(
        json.dumps(verdict, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
