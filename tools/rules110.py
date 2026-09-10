"""RULES measurement (post-hoc, engine unchanged): false abstention of Z-SLOT and S-MULTI on DEV.
A rule's false abstention = sampled DEV items the rule blocked on which the un-blocked suggestion (A2S) would have
served the gold, over all sampled DEV items (the rule's cost); also published over blocked items.
Z-SLOT blocks items with no numbers; a library plan needs {n} slots to bind, so its false abstention is 0 by construction
(measured anyway by bypassing the rule). Reads lib_<arm>_acq2 (the sealed library) and the DEV bridge answers."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import engine110 as E

out = {}
for arm in ("sonnet", "opus", "haiku", "fable"):
    lib = E.Lib.load(str(E.HERE / "results" / "v110" / ("lib_%s_acq2.json" % arm)))
    answers = E.load_answers(arm, "dev")
    sample = E.sample_ids("dev")
    res = {"sampled": 0}
    for rule in ("Z-SLOT", "S-MULTI"):
        res[rule] = {"blocked": 0, "would_serve": 0, "would_serve_correct": 0, "would_serve_wrong": 0}
    for it in sample:
        if it["tier"] not in ("T1", "T2", "T3", "T3p", "T4") or it.get("gold_type") != "num":
            continue
        res["sampled"] += 1
        own = E.parse_own(it, answers.get(it["id"]))
        if own is None:
            continue
        sg = E.suggest(it, lib, own, arm)
        rule = sg.get("skip")
        if not rule:
            continue
        res[rule]["blocked"] += 1
        # bypass the rule once, for measurement only
        if rule == "Z-SLOT":
            it2 = dict(it); it2["numbers"] = it2.get("numbers") or {}
            saved = E.S_MULTI; E.S_MULTI = re.compile(r"(?!x)x")
            sg2 = E.suggest(dict(it2, numbers=it2["numbers"] or {"_": 0}), lib, own, arm)
            E.S_MULTI = saved
            sg2 = {"A2S": None} if not it.get("numbers") else sg2  # no slots -> nothing can bind
        else:
            saved = E.S_MULTI; E.S_MULTI = re.compile(r"(?!x)x")
            sg2 = E.suggest(it, lib, own, arm)
            E.S_MULTI = saved
        if sg2.get("A2S") is not None:
            res[rule]["would_serve"] += 1
            if E.grade(it, sg2["A2S"][0]):
                res[rule]["would_serve_correct"] += 1
            else:
                res[rule]["would_serve_wrong"] += 1
    for rule in ("Z-SLOT", "S-MULTI"):
        r = res[rule]
        r["false_abstention_of_sample"] = r["would_serve_correct"] / res["sampled"] if res["sampled"] else None
        r["false_abstention_of_blocked"] = r["would_serve_correct"] / r["blocked"] if r["blocked"] else None
        r["pass_3pct"] = (r["false_abstention_of_sample"] or 0) < 0.03
    out[arm] = res
    print(arm, json.dumps(res))
Path(E.HERE / "results" / "v110" / "rules110.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
