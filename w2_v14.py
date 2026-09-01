# -*- coding: utf-8 -*-
# origin: new for V1.4 -- model arms over the substrate
"""Runs one model arm: real language -> relational state -> certified
answer or abstention.

  python w2_v14.py --model claude-haiku-4-5 --arm C5
  python w2_v14.py --model claude-haiku-4-5 --arm C5 --seal

Arms are the ablation of SPEC section 14:

  C1  substrate only              spans verified, executed
  C2  + semantic integrity        the 15 detectors
  C3  + capability applicability
  C5  complete                    C2 + C3 + check 8 + agreement

The bridge lives OUTSIDE the repository (D-i). V1.3's opus arm was
disqualified because a servicing agent read `reflex/planir.py` and
tuned its answers against the checker; a prompt asking it not to is
weaker than a directory in which the checker does not exist.
"""
import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "v14" / "data"
OUT = HERE / "results" / "v14" / "arms"
BRIDGE = Path("C:/Users/admin/Downloads/v14-bridge")

ARMS = {
    "C1": {"integrity": False, "applicability": False,
           "check8": False, "agreement": False},
    "C2": {"integrity": True, "applicability": False,
           "check8": False, "agreement": False},
    "C3": {"integrity": False, "applicability": True,
           "check8": False, "agreement": False},
    "C5": {"integrity": True, "applicability": True,
           "check8": True, "agreement": True},
}


def grade(v, a, tol=2e-2):
    if v is None or a is None:
        return False
    try:
        v, a = float(v), float(a)
    except (TypeError, ValueError):
        return False
    return abs(v) < 1e-9 if a == 0 else abs(v - a) / abs(a) <= tol


def sig(state):
    from reflex import relations as REL
    ops = []
    for r in sorted(state.relations.values(), key=lambda x: x["id"]):
        o = REL.resolve(r.get("span", ""))
        idents = sorted({(state.get(x) or {}).get("identity")
                         for x in r["args"] if state.get(x)} - {None})
        ops.append((o.op if o.status == "resolved" else o.status,
                    tuple(idents)))
    return tuple(sorted(ops))


def solve(adapter, item, cfg):
    """One item. Returns a record; `value` is non-None only when the
    ENGINE computed it and every enabled gate passed."""
    from reflex import (kindderive as KD, relations as REL, rssexec,
                        semint, state_agent as SA)
    q = item["q"]
    rec = {"id": item["id"], "answer": item.get("answer"),
           "value": None, "status": None, "abstain": None}

    # Request BOTH samples before checking pending, so one servicing
    # round enqueues the whole dual parse instead of two.
    a = SA.produce(adapter, q, variant=0)
    b = SA.produce(adapter, q, variant=1) if cfg["agreement"] else None
    if a.get("pending") or (b is not None and b.get("pending")):
        rec["status"] = "pending"
        return rec
    if a.get("refused"):
        rec["status"] = "model_refused"
        return rec
    st, info = SA.to_state(a.get("payload"), q)
    rec["dropped_spans"] = len(info.get("dropped") or [])
    rec["nodes"] = len(st.nodes)
    rec["relations"] = len(st.relations)

    if cfg["agreement"]:
        st2, _ = SA.to_state(b.get("payload"), q)
        if sig(st) != sig(st2):
            rec["status"] = "abstained"
            rec["abstain"] = "agreement"
            return rec

    ok, bad = st.verify_spans()
    if not ok:
        rec["status"] = "abstained"
        rec["abstain"] = "span_not_verbatim"
        return rec
    ok, bad = st.verify_refs()
    if not ok:
        rec["status"] = "abstained"
        rec["abstain"] = "dangling_reference"
        return rec

    KD.derive_state(st)
    all_ok, relrep = REL.resolve_state(st)
    rec["relations_resolved"] = relrep["resolved"]
    if relrep["ambiguous"]:
        rec["status"] = "abstained"
        rec["abstain"] = "ambiguous_relation"
        rec["detail"] = relrep["ambiguous"][:2]
        return rec
    if relrep["unknown"]:
        rec["status"] = "abstained"
        rec["abstain"] = "unknown_relation"
        rec["detail"] = relrep["unknown"][:2]
        return rec

    if cfg["integrity"]:
        clean, findings = semint.inspect(st, {"ask": info.get("ask")})
        if not clean:
            rec["status"] = "abstained"
            rec["abstain"] = "integrity:" + sorted(findings)[0]
            rec["findings"] = sorted(findings)
            return rec

    value, trace = rssexec.execute(st)
    if value is None:
        rec["status"] = "abstained"
        rec["abstain"] = "not_evaluable"
        rec["detail"] = trace
        return rec

    if cfg["check8"]:
        ask_span = (info.get("ask") or {}).get("span") or ""
        tkind, _ = KD.derive(ask_span or q)
        ok8, d8 = KD.check_target_integrality(tkind, value)
        if not ok8:
            rec["status"] = "abstained"
            rec["abstain"] = "check8_integrality"
            rec["detail"] = d8
            return rec

    rec["value"] = value
    rec["status"] = "certified"
    rec["correct"] = grade(value, item.get("answer"))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--arm", default="C5", choices=sorted(ARMS))
    ap.add_argument("--split", default="s3_real_language")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--seal", action="store_true")
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.adapters.anthropic_bridge import AnthropicBridgeAdapter

    adapter = AnthropicBridgeAdapter(model=a.model,
                                     bridge_dir=BRIDGE / a.model)
    items = json.loads((DATA / ("%s.json" % a.split))
                       .read_text(encoding="utf-8"))
    if a.limit:
        items = items[:a.limit]
    cfg = ARMS[a.arm]

    st = Counter()
    ab = Counter()
    rows = []
    t0 = time.time()
    for it in items:
        r = solve(adapter, it, cfg)
        st[r["status"]] += 1
        if r["status"] == "certified":
            st["correct" if r.get("correct") else "WRONG"] += 1
        if r.get("abstain"):
            ab[r["abstain"]] += 1
        rows.append(r)

    pend = len(adapter.pending())
    served = st["certified"]
    summ = {"model": a.model, "arm": a.arm, "split": a.split,
            "n": len(items), "status": dict(st),
            "abstain_reasons": dict(ab),
            "certified": served, "correct": st["correct"],
            "wrong": st["WRONG"],
            "coverage": round(served / len(items), 4) if items else None,
            "wrong_fire": (round(st["WRONG"] / served, 5)
                           if served else None),
            "bridge_pending": pend,
            "token_source": "synthetic-bridge",   # B7: never energy
            "wall_s": round(time.time() - t0)}
    if pend and a.seal:
        summ["sealed_with_pending"] = pend
        summ["status"]["abstained_unresolved"] = st.get("pending", 0)
        summ["status"].pop("pending", None)

    OUT.mkdir(parents=True, exist_ok=True)
    tag = "%s_%s" % (a.model.split("-")[1], a.arm)
    with open(OUT / ("%s.jsonl" % tag), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    (OUT / ("%s_summary.json" % tag)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summ.items()
                      if k != "abstain_reasons"}, indent=1))
    print("abstain reasons:", json.dumps(dict(ab), indent=1))
    if pend and not a.seal:
        print("\nBRIDGE PENDING %d" % pend)
        sys.exit(3)


if __name__ == "__main__":
    main()
