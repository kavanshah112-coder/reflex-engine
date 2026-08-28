# -*- coding: utf-8 -*-
# origin: new for V1.0 — EXP-ACQ analysis (V1_SPEC §8-§9)
"""Deterministic EXP-ACQ analysis -> results/expacq/analysis.json.

Per arm: learning curve (checkpoint probes), traffic tallies, sealed
finals with the V0.11 gate_rate definition, candidate funnel, miner
cost. Cross-arm: paired McNemar on the sealed parser final, lift per
cost, break-even N (V1_PLAN: 719 J avoided per reuse; miner J from
the metered calibration when present).
"""
import json
import sys
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS_DIR = HERE / "results" / "expacq" / "arms"
OUT = HERE / "results" / "expacq"
ARM_NAMES = ["A0", "A1", "A2", "A3"]
LLM_JQ = 719.0


def rows(p):
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def gate_rate(rs):
    n = len(rs)
    wrong_ans = sum(1 for r in rs if r["expect"] == "answer"
                    and r["value"] is not None and not r["correct"])
    ans_abst = sum(1 for r in rs if r["expect"] == "abstain"
                   and r["value"] is not None)
    return {"n": n, "acc": sum(bool(r["correct"]) for r in rs) / n
            if n else None,
            "coverage": sum(1 for r in rs
                            if r["value"] is not None) / n
            if n else None,
            "wrong_fire": wrong_ans + ans_abst,
            "gate_rate": (wrong_ans + ans_abst) / n if n else None}


def mcnemar(a, b):
    am = {r["query_id"]: bool(r["correct"]) for r in a}
    bm = {r["query_id"]: bool(r["correct"]) for r in b}
    common = sorted(set(am) & set(bm))
    win = sum(1 for q in common if bm[q] and not am[q])
    lose = sum(1 for q in common if am[q] and not bm[q])
    n = win + lose
    if n == 0:
        return {"n": len(common), "win": 0, "lose": 0, "p": 1.0}
    k = min(win, lose)
    p = min(1.0, sum(comb(n, i) for i in range(k + 1)) / 2 ** n * 2)
    return {"n": len(common), "win": win, "lose": lose,
            "p": round(p, 10)}


def main():
    A = {"arms": {}, "stats": {}, "cost": {}}
    cal_p = OUT / "miner_energy_calibration.json"
    cal = (json.loads(cal_p.read_text(encoding="utf-8"))
           if cal_p.exists() else None)
    sealed_rows = {}
    for arm in ARM_NAMES:
        d = ARMS_DIR / arm
        if not d.exists():
            continue
        e = {"checkpoints": rows(d / "checkpoints.jsonl")}
        tr = rows(d / "traffic.jsonl")
        e["traffic"] = {
            "n": len(tr),
            "ok": sum(1 for r in tr if r["ok"]),
            "wrong": sum(1 for r in tr if r.get("wrong")),
            "escalated": sum(1 for r in tr if not r["ok"])}
        st_p = d / "arm_stats.json"
        e["arm_stats"] = (json.loads(st_p.read_text(
            encoding="utf-8")) if st_p.exists() else {})
        for name in ("expacq_parse_sealed", "expacq_sem_sealed",
                     "expacq_adv_sealed"):
            rs = rows(d / f"ms_{name}.jsonl")
            if rs:
                e[name] = gate_rate(rs)
                if name == "expacq_parse_sealed":
                    sealed_rows[arm] = rs
        # cost axis
        s = e["arm_stats"]
        tok = (s.get("tokens_in", 0) or 0) + \
            (s.get("tokens_out", 0) or 0)
        cost = {"miner_calls": s.get("miner_calls", 0),
                "miner_tokens": tok}
        if cal and tok:
            cost["miner_j_est"] = tok * cal["j_per_token"]
        e["cost"] = cost
        A["arms"][arm] = e
    for arm in ("A1", "A2", "A3"):
        if arm in sealed_rows and "A0" in sealed_rows:
            A["stats"][f"parse_sealed:{arm}_vs_A0"] = mcnemar(
                sealed_rows["A0"], sealed_rows[arm])
    if "A2" in sealed_rows and "A3" in sealed_rows:
        A["stats"]["parse_sealed:A3_vs_A2"] = mcnemar(
            sealed_rows["A2"], sealed_rows["A3"])
    # break-even (H7): reuses to repay a minted reflex at 719 J/q
    for arm in ("A2", "A3"):
        e = A["arms"].get(arm)
        if not e or not e["cost"].get("miner_j_est"):
            continue
        n_active = e["arm_stats"].get("cand_ACTIVE", 0)
        if n_active:
            j_per_active = e["cost"]["miner_j_est"] / n_active
            A["cost"][arm] = {
                "j_per_active_reflex": j_per_active,
                "break_even_reuses": j_per_active / LLM_JQ}
    (OUT / "analysis.json").write_text(
        json.dumps(A, indent=1, sort_keys=True, default=str),
        encoding="utf-8")
    for arm, e in A["arms"].items():
        ck = e["checkpoints"]
        curve = " ".join(f"{c['i']}:{c['val_ok']}" for c in ck)
        ps = e.get("expacq_parse_sealed") or {}
        print(f"{arm}: curve[{curve}] "
              f"sealed_acc={ps.get('acc')} "
              f"gate={ps.get('gate_rate')} "
              f"active={e['arm_stats'].get('cand_ACTIVE')}")
    print("-> analysis.json")


if __name__ == "__main__":
    main()
