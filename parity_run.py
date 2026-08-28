# -*- coding: utf-8 -*-
# origin: new for V1.0 — E0 parity battery (V1_SPEC §7, V1_PLAN §1)
"""E0 parity battery: run the vendored V1 engine (C10 champion
configuration, replicated exactly from v11/run11.run_control) over
every ported sealed suite; diff ITEM-LEVEL against v0.11's recorded
C10 rows; enforce the frozen parity bounds.

  python parity_run.py [--suite cplx10_sealed] [--resolver on|off]

Resolver default ON (the C10 product path; requires local ollama).
All v0.11 sealed results had every resolver proposal validator-
rejected, so C8==C10; --resolver off exists to isolate any divergence
caused by resolver nondeterminism, and is NOT the parity claim.
"""
import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARC = HERE / "reflex" / "_arc"
BAT = HERE / "battery"
OUT = HERE / "results" / "parity"
sys.path.insert(0, str(ARC))

SUITES = ["sem11_sealed", "adv11_sealed", "parse11_sealed",
          "parse11_oof", "cplx10_sealed"]
BOUNDS = {  # frozen in V1_PLAN §1
    "parse11_sealed": {"acc_min": 0.832},
    "parse11_oof": {"acc_min": 0.668},
    "cplx10_sealed": {"acc_min": 1.0},          # 196/196 exact
}


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


def build_runner(resolver_on, engine_mode="lexpatch"):
    if engine_mode == "pack":
        return _build_pack_runner(resolver_on)
    from v11 import lexpatch11
    lexpatch11.apply()
    from v11.semparse11 import parse as sp
    from v11.integrity11 import certify
    from v11.semrun11 import run as srun
    from v11.pbreed11 import ParserBreeder11
    breeder = ParserBreeder11.load(
        ARC / "results/raw_v11/parser_breeder11.json")

    resolver = None
    if resolver_on:
        from v5 import llm5
        llm5.activate_best(warm=True)

        def resolver(query, fact, state):     # noqa: F811
            # verbatim v11/run11._resolver_llm
            from v4 import llm_bridge as B4
            cands = fact.get("ambiguity") or []
            names = {e: state.graph.entities[e]["name"] for e in cands
                     if e in state.graph.entities}
            prompt = (f"QUERY: {query}\nA quantity ({fact['concept']}"
                      f" = {fact['value']} {fact.get('unit', '')}, "
                      f"span \"{fact.get('span', '')[:80]}\") has an "
                      f"ambiguous entity. Candidates: {names}. Which "
                      f"entity id does it belong to? Do NOT solve the "
                      f"problem. Reply ONLY: "
                      f"{{\"entity\": \"<id>\"}}")
            try:
                out = B4.generate_json(prompt, max_tokens=40)
            except TypeError:
                out = B4.generate_json(prompt)
            if isinstance(out, dict):
                j = out.get("json") or {}
                e = j.get("entity")
                if e is None and out.get("raw"):
                    import re as _re
                    m = _re.search(r'"entity"\s*:\s*"(E\d+)"',
                                   str(out["raw"]))
                    e = m.group(1) if m else None
                return e
            return None

    def run_one(item):
        # verbatim C10 branch of v11/run11.run_control
        t0 = time.perf_counter()
        avail = item.get("available")
        rec = {"query_id": item["id"], "llm_calls": [],
               "reflex_parse": False}
        tp = time.perf_counter()
        st, info = sp(item["q"], item["id"])
        rec["parse_ms"] = (time.perf_counter() - tp) * 1e3
        extra = breeder.extract_struct(item["q"])
        known_unknown = [f for f in st.facts
                         if f["concept"] in (None, "UNKNOWN")]
        for (c, v, u) in extra:
            for f in known_unknown:
                if f["value"] is not None and \
                        abs(f["value"] - v) < 1e-9:
                    f["concept"] = c
                    rec["reflex_parse"] = True
        ti = time.perf_counter()
        certify(st)
        rec["integrity_ms"] = (time.perf_counter() - ti) * 1e3
        r = srun(st, info, item["q"], item["id"], use_llm=False,
                 resolver=resolver, redundancy=True, avail=avail)
        rec.update({k: r.get(k) for k in
                    ("status", "numeric_value", "abstain_reason",
                     "mode", "resolver_used", "redundancy_checked",
                     "invariant_violations")})
        rec["llm_calls"] = r.get("llm_calls", [])
        rec["t_ms"] = (time.perf_counter() - t0) * 1e3
        return rec

    return run_one


def _build_pack_runner(resolver_on):
    """Route through the pack-driven Engine (reflex/engine.py) —
    identical recipe, tables from packs/physics instead of hardcoded
    state."""
    sys.path.insert(0, str(HERE))
    from reflex.engine import Engine
    resolver = None
    if resolver_on:
        from v5 import llm5
        llm5.activate_best(warm=True)
        def resolver(query, fact, state):     # noqa: F811
            from v4 import llm_bridge as B4
            cands = fact.get("ambiguity") or []
            names = {e: state.graph.entities[e]["name"] for e in cands
                     if e in state.graph.entities}
            prompt = (f"QUERY: {query}\nA quantity ({fact['concept']}"
                      f" = {fact['value']} {fact.get('unit', '')}, "
                      f"span \"{fact.get('span', '')[:80]}\") has an "
                      f"ambiguous entity. Candidates: {names}. Which "
                      f"entity id does it belong to? Do NOT solve the "
                      f"problem. Reply ONLY: "
                      f"{{\"entity\": \"<id>\"}}")
            try:
                out = B4.generate_json(prompt, max_tokens=40)
            except TypeError:
                out = B4.generate_json(prompt)
            if isinstance(out, dict):
                j = out.get("json") or {}
                e = j.get("entity")
                if e is None and out.get("raw"):
                    import re as _re
                    m = _re.search(r'"entity"\s*:\s*"(E\d+)"',
                                   str(out["raw"]))
                    e = m.group(1) if m else None
                return e
            return None

    eng = Engine(resolver=resolver, redundancy=True,
                 use_breeder=True)

    def run_one(item):
        r = eng.run_query(item["q"], item["id"],
                          available=item.get("available"))
        r.pop("_state", None)
        r.pop("_info", None)
        return r

    return run_one


def run_suite(name, run_one):
    items = json.loads((BAT / f"{name}.json").read_text(
        encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for it in items:
        r = run_one(it)
        expect = it.get("expect", "answer")
        v = r.get("numeric_value")
        rows.append({
            "query_id": it["id"], "value": v,
            "correct": (grade(v, it.get("answer"))
                        if expect == "answer" else v is None),
            "answer": it.get("answer"), "expect": expect,
            "status": r.get("status"),
            "abstain_reason": r.get("abstain_reason"),
            "resolver_used": r.get("resolver_used"),
            "n_llm_calls": len(r.get("llm_calls") or []),
            "parse_ms": round(r.get("parse_ms", 0), 3),
            "t_ms": round(r.get("t_ms", 0), 2),
            "trap_answer": it.get("trap_answer")})
    with open(OUT / f"v1_{name}.jsonl", "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, default=str) + "\n")
    return rows


def wrong_fire(rows):
    """V0.11 analyze gate definition."""
    wrong_ans = sum(1 for r in rows
                    if r["expect"] == "answer" and
                    r["value"] is not None and not r["correct"])
    ans_on_abst = sum(1 for r in rows
                      if r["expect"] == "abstain"
                      and r["value"] is not None)
    return wrong_ans + ans_on_abst


def diff_reference(name, rows):
    ref_p = BAT / f"reference_ms_{name}_C10.jsonl"
    ref = {}
    for line in ref_p.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        ref[d["query_id"]] = d
    diffs = []
    for r in rows:
        g = ref.get(r["query_id"])
        if g is None:
            diffs.append((r["query_id"], "missing_in_reference"))
            continue
        if bool(r["correct"]) != bool(g["correct"]):
            diffs.append((r["query_id"],
                          f"correct {g['correct']}->{r['correct']} "
                          f"(ref v={g.get('value')} "
                          f"new v={r.get('value')})"))
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=None)
    ap.add_argument("--resolver", default="on",
                    choices=["on", "off"])
    ap.add_argument("--engine", default="lexpatch",
                    choices=["lexpatch", "pack"])
    a = ap.parse_args()
    run_one = build_runner(a.resolver == "on", engine_mode=a.engine)
    suites = [a.suite] if a.suite else SUITES
    verdict = {}
    for name in suites:
        t0 = time.perf_counter()
        rows = run_suite(name, run_one)
        n = len(rows)
        acc = sum(bool(r["correct"]) for r in rows) / n
        wf = wrong_fire(rows)
        llm = sum(r["n_llm_calls"] for r in rows)
        diffs = diff_reference(name, rows)
        ok = wf == 0 and not diffs
        b = BOUNDS.get(name)
        if b and acc < b["acc_min"]:
            ok = False
        verdict[name] = {"n": n, "acc": round(acc, 4),
                         "wrong_fire": wf, "llm_step_calls": llm,
                         "item_diffs": diffs, "ok": ok,
                         "wall_s": round(time.perf_counter() - t0,
                                         1)}
        print(f"{name}: n={n} acc={acc:.4f} wrong_fire={wf} "
              f"diffs={len(diffs)} "
              f"{'OK' if ok else 'FAIL'}", flush=True)
        for d in diffs[:10]:
            print("   diff:", d)
    (OUT / "parity_verdict.json").write_text(
        json.dumps(verdict, indent=1), encoding="utf-8")
    all_ok = all(v["ok"] for v in verdict.values())
    print("PARITY:", "PASS" if all_ok else "FAIL")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
