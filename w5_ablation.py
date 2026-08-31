# -*- coding: utf-8 -*-
# origin: new for V1.4 -- C0/C1/C2 ablation on S1 (SPEC sections 8, 14)
"""Does the substrate catch what the flat plan IR could not?

Model-free by construction. Every case carries a CORRECT state and a
CORRUPT state over the same text, so each arm is scored twice:

    DETECTION       does it flag the corrupt state
    FALSE POSITIVE  does it flag the correct one

Reporting only the first is how a detector that fires on everything
scores 100%. V1.3's B10 is the precedent in this arc: non-degeneracy
rejected correct plans whose answer happened to coincide with an input,
and the cost surfaced only when somebody counted.

C0 is V1.3's representation, reconstructed faithfully: the relational
state is PROJECTED DOWN to `quantities / plan / target / dismissed`,
discarding identity, order, scope and context -- exactly what V1.3
never had -- and then `planir`'s own checks are run on it.

Two deliberate generosities to C0, both stated because they make its
score an UPPER bound rather than a convenient one:

  1. `agreement` is given the same IR twice, so it always passes. With
     no model there is no second parse, and letting a check fail for
     want of an input it could never have had would flatter C1/C2.
  2. the projection preserves the plan DAG, so groupings that the flat
     IR CAN express are expressed. Where C0 misses those, it misses
     because nothing CHECKS the grouping -- not because the notation
     was too weak.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
DATA = HERE / "results" / "v14" / "data"
OUT = HERE / "results" / "v14"


def build_state(text, spec):
    from reflex.rss import State
    st = State(text)
    for n in spec["nodes"]:
        meta = {k: v for k, v in n.items()
                if k not in ("span", "content")}
        st.add_node(n["span"], n.get("content"), **meta)
    for r in spec["relations"]:
        meta = {k: v for k, v in r.items()
                if k not in ("span", "args")}
        st.add_relation(r["span"], r["args"], **meta)
    return st


def project_to_flat_ir(state):
    """The V1.3 representation. Identity, order, scope and context are
    dropped -- that IS the projection, and the point of the arm."""
    from reflex import relations as REL
    qs, idmap = [], {}
    for i, n in enumerate(sorted(state.nodes.values(),
                                 key=lambda x: int(x["id"][1:])), 1):
        if isinstance(n.get("content"), (int, float)):
            qid = "q%d" % len(qs) + ""
            qid = "q%d" % (len(qs) + 1)
            idmap[n["id"]] = qid
            qs.append({"id": qid, "value": n["content"], "unit": "",
                       "kind": "count", "span": n.get("span", "")})
    plan, last = [], None
    for j, r in enumerate(sorted(state.relations.values(),
                                 key=lambda x: (x.get("order", 0),
                                                x["id"])), 1):
        out = REL.resolve(r.get("span", ""))
        op = out.op or "sub"
        args = [idmap.get(a) for a in r["args"] if idmap.get(a)]
        if last and len(args) < 2:
            args = ([last] + args)[:2]
        args = [a for a in args if a][:2]
        if len(args) < 2:
            continue
        sid = "s%d" % j
        plan.append({"op": op, "args": args, "out": sid})
        last = sid
    return {"quantities": qs, "plan": plan,
            "target": {"kind": "count", "scope": "the answer"},
            "dismissed": []}


def c0_flags(state, kinds):
    """True when V1.3's check suite would REJECT this state."""
    from reflex import planir
    ir = project_to_flat_ir(state)
    if not ir["quantities"] or not ir["plan"]:
        return False, "not_expressible"       # C0 sees nothing to reject
    try:
        ok, rep = planir.verify(ir, ir, state.source, kinds)
    except Exception as e:
        return False, "verify_error:%s" % e
    if ok:
        return False, "passed_all_checks"
    first = next((k for k, v in rep.items()
                  if isinstance(v, dict) and not v.get("ok")), "?")
    return True, first


def c2_flags(state, ask, applic=None):
    from reflex import semint
    ctx = {"ask": ask, "applicability_failures": applic or []}
    clean, findings = semint.inspect(state, ctx)
    return (not clean), (sorted(findings) if findings else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=str(DATA / "s1_adversarial.json"))
    a = ap.parse_args()

    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
    import v10.universe10 as U10
    from reflex import relations as REL

    cases = json.loads(Path(a.suite).read_text(encoding="utf-8"))
    arms = ("C0_flat_ir", "C2_substrate_integrity")
    det = {k: defaultdict(int) for k in arms}
    fp = {k: defaultdict(int) for k in arms}
    tot = defaultdict(int)
    miss_examples = defaultdict(list)

    for c in cases:
        cls = c["seeded_class"]
        tot[cls] += 1
        good = build_state(c["text"], c["correct"])
        bad = build_state(c["text"], c["corrupt"])
        for st in (good, bad):
            REL.resolve_state(st)

        f_bad, _ = c0_flags(bad, U10.KINDS10)
        f_good, _ = c0_flags(good, U10.KINDS10)
        det["C0_flat_ir"][cls] += int(f_bad)
        fp["C0_flat_ir"][cls] += int(f_good)

        b2, why_b = c2_flags(bad, c["ask"])
        g2, why_g = c2_flags(good, c["ask"])
        det["C2_substrate_integrity"][cls] += int(b2)
        fp["C2_substrate_integrity"][cls] += int(g2)
        if not b2 and len(miss_examples[cls]) < 2:
            miss_examples[cls].append({"id": c["id"],
                                       "text": c["text"][:90]})

    rep = {"suite": Path(a.suite).name, "n": len(cases),
           "by_class": {}, "totals": {}}
    print("%-32s %5s | %-18s | %-18s"
          % ("seeded class", "n", "C0 flat IR", "C2 substrate+int"))
    print("%-32s %5s | %8s %9s | %8s %9s"
          % ("", "", "detect", "false+", "detect", "false+"))
    for cls in sorted(tot):
        n = tot[cls]
        row = {}
        for arm in arms:
            row[arm] = {"detected": det[arm][cls],
                        "false_positive": fp[arm][cls], "n": n,
                        "detection_rate": round(det[arm][cls] / n, 3),
                        "false_positive_rate": round(fp[arm][cls] / n, 3)}
        rep["by_class"][cls] = row
        print("%-32s %5d | %5d %5.0f%% %5.0f%% | %5d %5.0f%% %5.0f%%"
              % (cls, n,
                 det["C0_flat_ir"][cls], 100 * det["C0_flat_ir"][cls] / n,
                 100 * fp["C0_flat_ir"][cls] / n,
                 det["C2_substrate_integrity"][cls],
                 100 * det["C2_substrate_integrity"][cls] / n,
                 100 * fp["C2_substrate_integrity"][cls] / n))
    N = sum(tot.values())
    for arm in arms:
        d = sum(det[arm].values())
        f = sum(fp[arm].values())
        rep["totals"][arm] = {"n": N, "detected": d, "false_positive": f,
                              "detection_rate": round(d / N, 4),
                              "false_positive_rate": round(f / N, 4)}
    print()
    for arm in arms:
        t = rep["totals"][arm]
        print("  %-26s detection %5.1f%%   false-positive %5.1f%%"
              % (arm, 100 * t["detection_rate"],
                 100 * t["false_positive_rate"]))
    rep["c2_misses"] = {k: v for k, v in miss_examples.items() if v}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "w5_ablation.json").write_text(json.dumps(rep, indent=1),
                                          encoding="utf-8")
    print("\nwrote", OUT / "w5_ablation.json")


if __name__ == "__main__":
    main()
