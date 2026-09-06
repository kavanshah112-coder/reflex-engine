# -*- coding: utf-8 -*-
# origin: new for V1.8 -- the evaluation runner (SPEC 8, 9)
"""One arm over one split.

  python v18_run.py --split {acq,dev,seal,replay,devl} --arm <name>
                    [--lib results/v18/planlib18_<m>_<scope>.json ...]
                    [--gate17] [--limit N] [--offset N] [--tag T]

Path per item, in order: V1.6 single-step engine (non-chain text
only, B30 routing kept) -> composer17 through plangate18 (G-P1..4,
G-P4', G-P5) -> binder18 over the role-aware library -> ESCALATED.
No positional template, no minted regex chain, no model call is in
this path. --gate17 routes the composer through plangate17 instead
(the V1.7 gate, for the byte-exact reproduction check).

Per-item rows carry the path and, on escalation, the binder's abstain
reason; summaries carry bind counters, abstain-reason counts and the
G-P4'/G-P5 kills on composer plans (the cost of the new gates on the
deterministic path).
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))

from v17_run import grade  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev",
                    choices=["acq", "dev", "seal", "replay", "devl"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--arm", default="det18")
    ap.add_argument("--tag", default="")
    ap.add_argument("--lib", nargs="*", default=[])
    ap.add_argument("--gate17", action="store_true")
    ap.add_argument("--routing17", action="store_true",
                    help="V1.7's chain marker only (B36 reproduction)")
    ap.add_argument("--reflexlib", default=str(
        HERE / "results" / "v16" / "reflexlib_all.json"))
    a = ap.parse_args()

    if a.split == "devl":
        src = HERE / "results" / "v18" / "data" / "devl.jsonl"
    else:
        src = HERE / "results" / "v17" / "data" / ("q1m_%s.jsonl"
                                                    % a.split)
    items = []
    with open(src, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i < a.offset:
                continue
            items.append(json.loads(line))
            if a.limit and len(items) >= a.limit:
                break

    import re as _re
    from reflex import (acquire16, binder18, chainexec17, composer17,
                        plangate17, plangate18, roles18)
    from reflex.gateway16 import ask16

    CHAIN_MARKED = _re.compile(
        r"\b(?:with (?:this|it|that)\b|from this\b|"
        r"using (?:this|that|it)\b|the (?:result|interest|difference|"
        r"count|sum|total|value)\b.*\b(?:then|multiply|subtract|add|"
        r"divide)|then\b|; )", _re.I)
    # B36 (V1.8): B30's marker missed result-references that name the
    # result as a variable ("With m = 57 and this result as v, apply
    # ...") and any second sentence that consumes "that/the result" --
    # 90,290 of Q-1M's two-sentence chains never matched. V1.6 abstains
    # on almost all of them; on ONE foreign item (q17_0568250) it
    # served sentence one, in every V1.7 arm and in V1.8's SEAL/REPLAY
    # runs (executed with the V1.7 marker; --routing17 reproduces).
    CHAIN_MARKED18 = _re.compile(
        r"\b(?:this|that|the) result\b|\bas (?:a |the )?"
        r"(?:principal|speed|mass|acceleration|force|distance|height|"
        r"voltage|current|resistance|v|p|m|a)\b|"
        r"\b(?:multiply|divide|add|subtract|increase|decrease|express|"
        r"convert)\b[^.]*\b(?:that|it|the result)\b", _re.I)
    library = json.loads(Path(a.reflexlib).read_text(
        encoding="utf-8")) if Path(a.reflexlib).exists() else []
    lib = binder18.Library.load(a.lib) if a.lib else None
    gate = plangate17.check if a.gate17 else plangate18.check

    st = Counter()
    by_k = defaultdict(Counter)
    reasons = Counter()
    kills = Counter()
    wrong_rows, safety2, rows = [], [], []
    t0 = time.perf_counter()
    for it in items:
        text = it["text"]
        served, path, reason, tpl = None, None, None, None
        try:
            chainish = bool(CHAIN_MARKED.search(text)) or \
                text.count(". ") >= 2 or (
                    not a.routing17 and bool(CHAIN_MARKED18.search(text)))
            if not chainish:
                r = ask16(text, it["id"])
                if r["status"] == "SERVED":
                    served, path = r["value"], "v16:" + r["path"]
                elif r["status"] == "ESCALATED" and library:
                    hit = acquire16.apply_library(text, library)
                    if hit is not None:
                        served, path = hit["value"], "v16:reflex"
            roles = None
            comp = None
            if served is None:
                comp_plan = composer17.parse_chain(text)
                if comp_plan is not None:
                    if a.gate17:
                        ok, transcript = gate(comp_plan, text)
                    else:
                        roles = roles18.analyze(text)
                        ok, transcript = gate(comp_plan, text, roles)
                    if ok:
                        v, cert = chainexec17.run(comp_plan)
                        if v is not None:
                            served, path = v, "chain:composer"
                            st["chain_served"] += 1
                        else:
                            st["composer_exec_refused"] += 1
                            comp = "exec_refused"
                    else:
                        st["gate_killed"] += 1
                        g = transcript[-1].get("gate") or "?"
                        kills["composer:" + g] += 1
                        comp = "gate:%s:%s" % (g, (transcript[-1].get(
                            "kill") or "")[:40])
                else:
                    comp = "none"
            if served is None and lib is not None:
                roles = roles or roles18.analyze(text)
                v, cert, info = binder18.serve(text, lib, qid=it["id"],
                                               roles=roles)
                if v is not None:
                    served, path = v, info["path"]
                    tpl = info["template"]
                    st["bind_served"] += 1
                else:
                    reason = info["reason"]
                    reasons[(reason or "?").split(":")[0]
                            if not (reason or "").startswith("gate")
                            else reason] += 1
        except Exception as exc:            # noqa: BLE001  (B27)
            st["engine_error"] += 1
            path = "engine-error:%s" % type(exc).__name__
        rec = {"id": it["id"], "k": it.get("k"), "path": path,
               "served": served is not None}
        if tpl:
            rec["tpl"] = tpl
        if served is not None:
            if it.get("distractor"):
                st["SAFETY2_SERVED"] += 1
                safety2.append(it["id"])
                rec["correct"] = False
            else:
                if it["gold_type"] == "bool" and \
                        isinstance(served, float) and path and \
                        (path.startswith("chain") or
                         path.startswith("bind")):
                    served_g = served > 0
                else:
                    served_g = served
                ok = grade(it, served_g)
                st["served"] += 1
                st["correct" if ok else "WRONG"] += 1
                kk = "k%s" % it.get("k")
                by_k[kk]["served"] += 1
                by_k[kk]["correct" if ok else "wrong"] += 1
                if path and path.startswith("bind"):
                    by_k[kk]["bind"] += 1
                    if not ok:
                        st["WRONG_bind"] += 1
                rec["correct"] = ok
                if not ok:
                    wrong_rows.append({
                        "id": it["id"], "text": text[:200],
                        "value": str(served)[:40],
                        "gold": str(it["gold"])[:30], "path": path})
        else:
            st["escalated"] += 1
            by_k["k%s" % it.get("k")]["escalated"] += 1
            if reason:
                rec["reason"] = reason
            if comp:
                rec["comp"] = comp
        rows.append(rec)
    wall = time.perf_counter() - t0

    n = len(items)
    n_dist = sum(1 for i in items if i.get("distractor"))
    n_in = n - n_dist
    served = st["served"]
    summ = {"arm": a.arm, "split": a.split, "n": n, "in_domain": n_in,
            "distractors": n_dist, "served": served,
            "chain_served": st["chain_served"],
            "bind_served": st["bind_served"],
            "correct": st["correct"], "WRONG": st["WRONG"],
            "WRONG_bind": st["WRONG_bind"],
            "coverage_in_domain": round(served / n_in, 4) if n_in
            else None,
            "wrong_fire": round(st["WRONG"] / served, 6) if served
            else None,
            "SAFETY2_distractor_served": st["SAFETY2_SERVED"],
            "gate_killed": st["gate_killed"],
            "composer_gate_kills": dict(kills),
            "composer_exec_refused": st["composer_exec_refused"],
            "bind_abstain": dict(reasons),
            "escalated": st["escalated"],
            "engine_errors": st["engine_error"],
            "ms_per_query": round(1000 * wall / n, 3) if n else None,
            "model_calls": 0, "gate": "plangate17" if a.gate17
            else "plangate18", "lib": a.lib,
            "lib_templates": len(lib) if lib else 0,
            "by_k": {k: dict(v) for k, v in sorted(by_k.items())}}
    out = HERE / "results" / "v18"
    out.mkdir(parents=True, exist_ok=True)
    tag = ("_%s" % a.tag) if a.tag else ""
    base = "%s_%s%s" % (a.arm, a.split, tag)
    (out / ("%s_summary.json" % base)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    (out / ("%s_wrong.json" % base)).write_text(
        json.dumps({"wrong": wrong_rows, "safety2": safety2}, indent=1),
        encoding="utf-8")
    with open(out / ("%s.jsonl" % base), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({k: v for k, v in summ.items() if k != "by_k"},
                     indent=1))
    print("by_k:", json.dumps(summ["by_k"]))


if __name__ == "__main__":
    main()
