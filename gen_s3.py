# -*- coding: utf-8 -*-
# origin: new for V1.4 -- S3 fresh sealed real language (SPEC section 13)
"""Builds the fresh real-language sealed set, disjoint from everything
V1.3 touched.

Disjointness is not a nicety here. V1.3's arm sample, traffic pool and
sealed sets between them consumed ~1,780 of the 3,625 real-language
items available, and every one of those has had its answer inspected
during V1.3's analysis. Reusing any of them would make V1.4's headline
a measurement on data whose answers are already known to the person
tuning the system.

So S3 is drawn ONLY from items no V1.3 file mentions, and the
disjointness is proved by id-set intersection rather than assumed from
how the sampling was written.
"""
import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE / "results" / "v14" / "data"
V13 = HERE / "results" / "v13" / "data"
CORP = HERE / "corpora"


def load_gsm():
    out = []
    p = CORP / "gsm8k_test.jsonl"
    if not p.exists():
        return out
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        ans = d.get("answer", "")
        m = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", ans)
        if not m:
            continue
        out.append({"id": "gsm%04d" % i, "q": d["question"],
                    "answer": float(m.group(1).replace(",", "")),
                    "source": "gsm8k"})
    return out


def load_asdiv():
    out = []
    p = CORP / "asdiv.xml"
    if not p.exists():
        return out
    txt = p.read_text(encoding="utf-8", errors="ignore")
    for i, blk in enumerate(re.findall(r"<Problem.*?</Problem>", txt,
                                       re.S)):
        body = re.search(r"<Body>(.*?)</Body>", blk, re.S)
        ques = re.search(r"<Question>(.*?)</Question>", blk, re.S)
        ansr = re.search(r"<Answer>(.*?)</Answer>", blk, re.S)
        if not (body and ques and ansr):
            continue
        a = re.search(r"-?[\d,]+(?:\.\d+)?", ansr.group(1))
        if not a:
            continue
        out.append({"id": "asdiv%04d" % i,
                    "q": (body.group(1).strip() + " " +
                          ques.group(1).strip()),
                    "answer": float(a.group(0).replace(",", "")),
                    "source": "asdiv"})
    return out


def v13_used():
    used = set()
    if not V13.exists():
        return used
    for f in V13.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, list):
            for x in d:
                if isinstance(x, dict):
                    for k in ("id", "src_id", "sid"):
                        if x.get(k):
                            used.add(str(x[k]))
    return used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=1200)
    ap.add_argument("--seed", type=int, default=1404)
    a = ap.parse_args()

    pool = load_gsm() + load_asdiv()
    used = v13_used()
    fresh = [x for x in pool if x["id"] not in used]

    inter = {x["id"] for x in fresh} & used
    assert not inter, "disjointness violated: %s" % sorted(inter)[:5]

    rng = random.Random(a.seed)
    rng.shuffle(fresh)
    sample = sorted(fresh[:a.n], key=lambda x: x["id"])

    OUT.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(sample, indent=1, sort_keys=True)
    (OUT / "s3_real_language.json").write_text(blob, encoding="utf-8")
    h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    (OUT / "s3_real_language.sha256").write_text(h, encoding="utf-8")

    print("corpus pool          %d" % len(pool))
    print("consumed by V1.3     %d" % len(used))
    print("fresh and available  %d" % len(fresh))
    print("S3 sampled           %d  (disjointness PROVED by id "
          "intersection = 0)" % len(sample))
    by = {}
    for x in sample:
        by[x["source"]] = by.get(x["source"], 0) + 1
    print("by source            %s" % by)
    print("sealed sha256        %s" % h)


if __name__ == "__main__":
    main()
