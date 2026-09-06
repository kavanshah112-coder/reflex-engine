# -*- coding: utf-8 -*-
# origin: new for V1.8 -- one JSON with every number the report cites
"""python tools/aggregate18.py -> results/v18/aggregate18.json"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "results" / "v18"
V17 = HERE / "results" / "v17"
ARMS = ["det18", "B-haiku-dev", "B-sonnet-dev", "B-opus-dev", "B-fable-dev",
        "B-all-dev", "B-haiku-all", "B-sonnet-all", "B-opus-all",
        "B-fable-all", "B-all-all"]


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    agg = {"arms": {}, "retain": {}, "libraries": {}, "controls": None,
           "gapclass": None, "realdiag": None, "energy": None,
           "v17_reference": {}}
    for arm in ARMS:
        agg["arms"][arm] = {}
        for split in ("devl", "seal", "replay"):
            s = load(OUT / ("%s_%s_summary.json" % (arm, split)))
            if s is None:
                continue
            w = load(OUT / ("%s_%s_wrong.json" % (arm, split))) or {}
            agg["arms"][arm][split] = {
                "n": s["n"], "in_domain": s["in_domain"],
                "served": s["served"], "chain_served": s["chain_served"],
                "bind_served": s["bind_served"], "WRONG": s["WRONG"],
                "WRONG_bind": s["WRONG_bind"],
                "coverage": s["coverage_in_domain"],
                "wrong_fire": s["wrong_fire"],
                "distractors_served": s["SAFETY2_distractor_served"],
                "engine_errors": s["engine_errors"],
                "ms_per_query": s["ms_per_query"],
                "bind_abstain": s["bind_abstain"],
                "lib_templates": s["lib_templates"],
                "by_k": s["by_k"],
                "wrong_rows": [(r["id"], r["path"]) for r in
                               w.get("wrong", [])]}
    for p in sorted(OUT.glob("retain_*_seal.json")):
        d = load(p)
        agg["retain"][d["arm"]] = d
    for m in ["haiku", "sonnet", "opus", "fable", "all"]:
        for sc in ("dev", "all"):
            d = load(OUT / ("planlib18_%s_%s.json" % (m, sc)))
            if d is None:
                continue
            h = load(OUT / ("harvest_%s_%s.json" % (m, sc)))
            agg["libraries"]["%s_%s" % (m, sc)] = {
                "templates": len(d["templates"]),
                "ledger": {k: v for k, v in d["ledger"].items()
                           if not k.startswith("probe_gate")},
                "harvest_ledger": (h or {}).get("ledger") or
                d.get("harvest_ledger"),
                "full": sum(1 for t in d["templates"]
                            if t["kind"] == "full"),
                "sub": sum(1 for t in d["templates"]
                           if t["kind"] == "sub"),
                "skeletons": sum(len(t["skeletons"]) for t in
                                 d["templates"])}
    agg["controls"] = load(OUT / "controls18.json")
    agg["gapclass"] = load(OUT / "B-all-all_devl_gapclass.json")
    agg["realdiag"] = load(OUT / "realdiag18.json")
    agg["energy"] = load(OUT / "energy18.json")
    agg["devl_manifest"] = load(OUT / "data" / "devl_manifest.json")
    for m in ["haiku", "sonnet", "opus", "fable"]:
        agg["v17_reference"][m] = {}
        for split in ("seal", "replay"):
            s = load(V17 / ("R-%s_%s_summary.json" % (m, split)))
            if s:
                agg["v17_reference"][m][split] = {
                    "served": s["served"], "WRONG": s["WRONG"],
                    "coverage": s["coverage_in_domain"],
                    "wrong_fire": s["wrong_fire"],
                    "mint_served": s.get("mint_served")}
    (OUT / "aggregate18.json").write_text(json.dumps(agg, indent=1),
                                          encoding="utf-8")
    print("arms:", {a: list(v) for a, v in agg["arms"].items()})
    print("retain:", list(agg["retain"]))


if __name__ == "__main__":
    main()
