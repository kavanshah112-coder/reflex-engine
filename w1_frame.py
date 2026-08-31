# -*- coding: utf-8 -*-
# origin: new for V1.3 — W1 measurement (V1_3_SPEC §4)
"""Builds the frame index from IN-UNIVERSE traffic and measures the
three W1 deliverables:

  (a) frame quality on held-out in-universe items, where the needed
      kinds are known: RECALL (does the frame contain them?) and the
      narrowing factor (15 of 77 kinds, not 77).
  (b) the no-frame signal on REAL human language — how often the
      frame declines, which is the early abstention boundary.
  (c) prompt-size reduction.

Neither the V1.3 sealed splits nor any sealed battery suite is
touched: the index is built from V0.11 dev traffic, held-out
evaluation uses a disjoint slice of that same dev traffic, and the
real-language read uses the V1.3 TRAFFIC pool only.

  python w1_frame.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
OUT = HERE / "results" / "v13"
N_INDEX, N_HELDOUT = 1500, 400


def main():
    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    from reflex.engine import Engine
    from reflex.frame import FrameIndex

    eng = Engine()
    dev = json.loads(
        (HERE / "data/dev_traffic/parse11_traffic.json")
        .read_text(encoding="utf-8"))
    index_items = dev[:N_INDEX]
    held = dev[N_INDEX:N_INDEX + N_HELDOUT]

    fi = FrameIndex()
    n = fi.build(eng, index_items)
    print(f"index built: {n} labelled rows from {len(index_items)} "
          f"in-universe items ({len(fi.all_kinds)} kinds total)")
    thr = fi.calibrate(held, percentile=5)
    print(f"no-frame threshold (5th pct of held-out in-universe "
          f"best-match): {thr:.4f}")

    # (a) held-out in-universe frame quality
    hits = miss = noframe = 0
    kind_counts = []
    for it in held:
        need, solved = FrameIndex.label_item(eng, it["q"],
                                             f"ho_{it['id']}")
        if not solved or not need:
            continue
        fr = fi.frame(it["q"])
        if fr is None:
            noframe += 1
            continue
        kind_counts.append(fr["n_kinds"])
        if need <= set(fr["kinds"]):
            hits += 1
        else:
            miss += 1
    total = hits + miss + noframe
    recall = hits / total if total else 0.0
    avg_kinds = (sum(kind_counts) / len(kind_counts)
                 if kind_counts else 0)

    # (b) the no-frame signal on REAL language (traffic pool only)
    real = json.loads((OUT / "data/v13_traffic_pool.json")
                      .read_text(encoding="utf-8"))
    real_num = [x for x in real if x.get("answer") is not None]
    real_theory = [x for x in real if x.get("answer") is None]
    def rate(items):
        if not items:
            return None, 0
        nf = sum(1 for x in items if fi.frame(x["q"]) is None)
        return nf / len(items), len(items)
    nf_num, n_num = rate(real_num[:400])
    nf_th, n_th = rate(real_theory[:200])
    nf_uni, n_uni = rate(held[:200])

    res = {
        "index_rows": n, "kinds_total": len(fi.all_kinds),
        "no_frame_threshold": thr,
        "in_universe_heldout": {
            "n": total, "frame_contains_needed_kinds": hits,
            "frame_missing_kinds": miss, "no_frame": noframe,
            "recall": round(recall, 4),
            "avg_kinds_in_frame": round(avg_kinds, 1),
            "narrowing": f"{avg_kinds:.1f} of {len(fi.all_kinds)}"},
        "no_frame_rate": {
            "in_universe": {"rate": round(nf_uni, 4), "n": n_uni},
            "real_numeric": {"rate": round(nf_num, 4), "n": n_num},
            "real_theory": {"rate": round(nf_th, 4), "n": n_th}},
        "prompt_size": {
            "v1_2_kinds_listed": len(fi.all_kinds),
            "v1_3_kinds_listed": round(avg_kinds, 1),
            "reduction": round(1 - avg_kinds / len(fi.all_kinds), 3)},
    }
    (OUT / "w1_frame.json").write_text(json.dumps(res, indent=1),
                                       encoding="utf-8")
    fi.save(OUT / "frame_index.json")
    print(f"(a) held-out in-universe: recall {recall:.1%} "
          f"({hits}/{total}), frame carries {avg_kinds:.1f} of "
          f"{len(fi.all_kinds)} kinds")
    print(f"(b) no-frame rate: in-universe {nf_uni:.1%} | "
          f"real numeric {nf_num:.1%} | real theory {nf_th:.1%}")
    print(f"(c) prompt narrowing: "
          f"{res['prompt_size']['reduction']:.1%} fewer kinds listed")


if __name__ == "__main__":
    main()
