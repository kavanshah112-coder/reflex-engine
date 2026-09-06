# -*- coding: utf-8 -*-
# origin: new for V1.8 -- REAL-DIAG (SPEC 5, decision 12.5; Q5, R11)
"""The frozen V1.3 real-language corpora (GSM8K test, ASDiv, SciQ)
through the lean V1.8 path -- composer17 + binder18 over the union
library -- with NO threshold. This exists to put a number beside the
synthetic compounding ratio: how much of a certified library harvested
from generator text is reachable from natural text at all.

  python tools/realdiag18.py [--lib results/v18/planlib18_all_all.json]

Writes results/v18/realdiag18.json. Corpus golds are NOT graded here
(V1.3's corpora carry their own grading; the diagnostic question is
reach, not accuracy): served counts and abstain reasons only, plus the
bind serves graded where a numeric gold exists.
"""
import argparse
import io
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
OUT = HERE / "results" / "v18"


def _corpora():
    import build_q1m as BQ
    out = [dict(d, corpus=("gsm8k" if d["sid"].startswith("g") else
                           "asdiv")) for d in BQ.load_distractors()]
    z = HERE / "corpora" / "sciq.zip"
    if z.exists():
        zf = zipfile.ZipFile(z)
        for name in zf.namelist():
            if not name.endswith(".json"):
                continue
            try:
                data = json.load(io.TextIOWrapper(zf.open(name),
                                                  encoding="utf-8"))
            except Exception:                 # noqa: BLE001
                continue
            if isinstance(data, list):
                for i, d in enumerate(data[:2000]):
                    q = d.get("question")
                    if q:
                        out.append({"text": q, "gold": d.get(
                            "correct_answer"), "sid": "s%05d" % i,
                            "corpus": "sciq"})
            break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", nargs="*",
                    default=[str(OUT / "planlib18_all_all.json")])
    a = ap.parse_args()
    from reflex import binder18, chainexec17, composer17, plangate18, \
        roles18
    lib = binder18.Library.load(a.lib)
    items = _corpora()
    st = Counter()
    reasons = Counter()
    per_corpus = {}
    graded = Counter()
    for it in items:
        c = it["corpus"]
        pc = per_corpus.setdefault(c, Counter())
        pc["n"] += 1
        text = it["text"]
        roles = roles18.analyze(text)
        pc["bare_tokens"] += len(roles.bare())
        pc["tokens"] += len(roles.unique)
        plan = composer17.parse_chain(text)
        if plan is not None:
            ok, _t = plangate18.check(plan, text, roles)
            if ok:
                v, _c = chainexec17.run(plan)
                if v is not None:
                    pc["composer_served"] += 1
                    continue
        v, cert, info = binder18.serve(text, lib, roles=roles)
        if v is not None:
            pc["bind_served"] += 1
            try:
                g = float(str(it.get("gold")).replace(",", ""))
                graded["correct" if abs(v - g) <= max(
                    1e-4 * abs(g), 1e-6) else "WRONG"] += 1
            except (TypeError, ValueError):
                graded["ungradable"] += 1
        else:
            reasons[c + ":" + (info["reason"] or "?").split(":")[0]] += 1
    res = {"lib": a.lib, "templates": len(lib), "n": len(items),
           "per_corpus": {k: dict(v) for k, v in per_corpus.items()},
           "abstain_reasons": dict(reasons),
           "bind_serves_graded": dict(graded),
           "note": "reach diagnostic, no threshold (SPEC 12.5); a "
                   "library harvested from generator phrasing is "
                   "expected to have near-zero skeleton reach on "
                   "natural text -- that expectation is the point"}
    (OUT / "realdiag18.json").write_text(json.dumps(res, indent=1),
                                         encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
