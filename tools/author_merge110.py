# -*- coding: utf-8 -*-
"""Merge bridge-authored T4/P4 stories into W-400K and apply QC.

Author agents read  bridge/author_<tier>_<model>_<NNN>.json  ([{id, start, steps, features}] or [{id, plan, features, kind_hint}])
and write            bridge/authored_<tier>_<model>_<NNN>.json ({id: story})
QC agents (a DIFFERENT model) read bridge/qcq_<tier>_<NNN>.json ([{id, question}]) and write
                     bridge/qc_<qcmodel>_<tier>_<NNN>.json ({id: answer})

  python tools/author_merge110.py stories   # pull authored stories into the item records, write qcq batches
  python tools/author_merge110.py qc        # grade QC answers against gold; QC-rejected -> split 'dev' (never sealed)
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "tools"))
import reader19 as S1  # noqa: E402
import reader19v as V  # noqa: E402

DATA = HERE / "results" / "v110" / "data"
BRIDGE = HERE / "results" / "v110" / "bridge"
SPLITS = ("acq", "dev", "seal", "replay")
QC_OF = {"sonnet": "opus", "opus": "sonnet", "haiku": "fable", "fable": "haiku"}


def _load_all():
    items = {}
    for sp in SPLITS:
        for line in (DATA / ("w400k_%s.jsonl" % sp)).read_text(encoding="utf-8").splitlines():
            if line.strip():
                it = json.loads(line); items[it["id"]] = it
    return items


def _write_all(items):
    for sp in SPLITS:
        with open(DATA / ("w400k_%s.jsonl" % sp), "w", encoding="utf-8", newline="\n") as f:
            for it in sorted(items.values(), key=lambda x: x["id"]):
                if it["split"] == sp:
                    f.write(json.dumps(it) + "\n")


def stories():
    items = _load_all()
    led = Counter()
    for p in sorted(BRIDGE.glob("authored_*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            led["bad_file"] += 1; continue
        for iid, story in d.items():
            it = items.get(iid)
            if it is None or not it.get("authored"):
                led["unknown_id"] += 1; continue
            if it.get("text"):
                led["already"] += 1; continue
            if not isinstance(story, str) or len(story.strip()) < 20:
                led["empty"] += 1; continue
            it["text"] = story.strip()
            it["numbers"] = {"n%d" % i: n[1] for i, n in enumerate(V.numbers_of19(it["text"]))}
            it["key"] = V.cue_key(it["text"])
            it["qc"] = "pending"
            led["merged_" + it["tier"]] += 1
    _write_all(items)
    # QC batches: every authored item with text and qc pending, grouped by tier and by the QC model
    pend = [it for it in items.values() if it.get("authored") and it.get("text") and it.get("qc") == "pending"]
    by = {}
    for it in pend:
        by.setdefault((it["tier"], QC_OF[it["author_model"]]), []).append({"id": it["id"], "question": it["text"]})
    nb = 0
    for (tier, qcm), lst in by.items():
        for bi in range(0, len(lst), 25):
            (BRIDGE / ("qcq_%s_%s_%03d.json" % (tier, qcm, bi // 25))).write_text(json.dumps(lst[bi:bi + 25], indent=0), encoding="utf-8")
            nb += 1
    led["qc_batches"] = nb
    print(json.dumps(dict(led), indent=1))


def qc():
    items = _load_all()
    led = Counter()
    ans = {}
    for p in BRIDGE.glob("qc_*.json"):
        try:
            ans.update(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            led["bad_file"] += 1
    for iid, a in ans.items():
        it = items.get(iid)
        if it is None or it.get("qc") != "pending":
            continue
        ok = S1.close(S1.parse_answer(a), S1.parse_answer(it["gold"]))
        it["qc"] = "pass" if ok else "reject"
        it["qc_answer"] = a
        led["qc_pass_" + it["tier"] if ok else "qc_reject_" + it["tier"]] += 1
        if not ok and it["split"] in ("seal", "replay"):
            it["split_original"] = it["split"]; it["split"] = "dev"
            led["moved_to_dev"] += 1
    _write_all(items)
    print(json.dumps(dict(led), indent=1))




def qcbatches():
    """Rewrite qcq batches restricted to what the runs score with a model in the loop:
    every authored item in SEAL/REPLAY, plus the E-SAMPLE authored items of ACQ/DEV (spec amendment: QC restricted if budget forces)."""
    import engine110 as E
    items = _load_all()
    keep = {it["id"] for it in items.values() if it.get("authored") and it.get("text") and it["split"] in ("seal", "replay")}
    for sp in ("acq", "dev"):
        keep |= {it["id"] for it in E.sample_ids(sp) if it.get("authored")}
    for p in BRIDGE.glob("qcq_*.json"):
        p.unlink()
    pend = [it for it in items.values() if it["id"] in keep and it.get("qc") == "pending"]
    by = {}
    for it in sorted(pend, key=lambda x: x["id"]):
        by.setdefault((it["tier"], QC_OF[it["author_model"]]), []).append({"id": it["id"], "question": it["text"]})
    nb = Counter()
    for (tier, qcm), lst in by.items():
        for bi in range(0, len(lst), 25):
            (BRIDGE / ("qcq_%s_%s_%03d.json" % (tier, qcm, bi // 25))).write_text(json.dumps(lst[bi:bi + 25], indent=0), encoding="utf-8")
            nb["%s_%s" % (tier, qcm)] += 1
    print(json.dumps({"qc_items": len(pend), "batches": dict(nb), "total_batches": sum(nb.values())}, indent=1))


if __name__ == "__main__":
    {"stories": stories, "qc": qc, "qcbatches": qcbatches}[sys.argv[1]]()
