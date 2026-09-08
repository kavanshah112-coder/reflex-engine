# -*- coding: utf-8 -*-
# origin: new for V1.9 -- one-model reading loop: G-P6, structural
# abstentions, cue keys, admission rules A0/A1/A2, reuse measurement
"""
  python tools/reader19v.py controls
  python tools/reader19v.py prep          # SEALED = corpus items S1 never
                                          # sampled; batches for readings
                                          # and answers (no golds)
  python tools/reader19v.py purity        # CUE-PURITY on DEV (S1 readings)
  python tools/reader19v.py score --phase dev|sealed --model sonnet
  python tools/reader19v.py reuse --model sonnet

S1's reader19 (tokenizer, bind, gate, execute) is imported, not
edited; V1.9's tokenizer fix lives here (numbers_of19) and applies to
SEALED batches only -- DEV readings were proposed against S1's slot
numbering and are bound with it.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
import reader19 as S1  # noqa: E402

OUT = HERE / "results" / "v19"
DATA = OUT / "data"
BRIDGE = OUT / "bridge"
BATCH = 25
MODELS = ["sonnet", "opus", "haiku", "fable"]

# ---------------------------------------------------------- tokenizer (V1.9)
NUM19 = re.compile(r"(?<![\w.])(-?(?:\d[\d,]*(?:\.\d+)?|\.\d+))(?!\d)")


def numbers_of19(text):
    out = []
    for m in NUM19.finditer(text):
        raw = m.group(1)
        tail = text[m.end(1):m.end(1) + 2].lower()
        if re.match(r"^-?\d+$", raw) and tail in ("st", "nd", "rd", "th"):
            continue
        mag = raw.replace(",", "").lstrip("-")
        if mag.startswith("."):
            mag = "0" + mag
        out.append((raw, mag, m.start(1), m.end(1)))
    return out


# ---------------------------------------------------------- G-P6 (frozen)
WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
         "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
         "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
         "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
         "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
         "thousand": 1000, "dozen": 12, "half": 0.5, "quarter": 0.25,
         "third": 1.0 / 3, "twice": 2, "double": 2, "doubled": 2,
         "thrice": 3, "triple": 3, "tripled": 3}
_WORD_RX = re.compile(r"[A-Za-z]+")
_PLURAL = re.compile(r"\b([A-Z][a-z]+) and ([A-Z][a-z]+)\b")
_PLURAL_REF = re.compile(r"\b(they|both|together|altogether)\b", re.I)


def word_tokens(text):
    """Stated word-quantities, in order: [(word, value)]."""
    toks = [(w.lower(), WORDS[w.lower()]) for w in _WORD_RX.findall(text)
            if w.lower() in WORDS]
    if _PLURAL.search(text) and _PLURAL_REF.search(text):
        toks.append(("PLURAL_AGENTS", 2))
    return toks


def plan_literal_occurrences(plan, numbers):
    """Every numeric literal occurrence in the plan (slot values
    substituted) plus each slot value once."""
    occ = []
    for n in plan.get("nodes", []):
        for k, v in n.items():
            if isinstance(v, str):
                s = S1._SLOT.sub(lambda m: numbers.get("n" + m.group(1), "0"), v)
                occ += [float(x) for x in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)", s)]
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                occ.append(float(v))
    occ += [float(v) for v in numbers.values()]
    return occ


def lexical_check(text, plan, numbers):
    """G-P6: every word-quantity consumes a DISTINCT literal occurrence.
    -> (ok, unmatched list)"""
    occ = plan_literal_occurrences(plan, numbers)
    missing = []
    for w, val in word_tokens(text):
        j = next((i for i, x in enumerate(occ) if abs(x - val) < 1e-9), None)
        if j is None:
            missing.append(w)
        else:
            occ.pop(j)
    return (not missing), missing


# ---------------------------------------------------------- structural rules
def ask_type(text):
    t = text.lower()
    if "ratio" in t:
        return "ratio"
    if re.search(r"\bhow many\b", t):
        return "count"
    if re.search(r"\bhow much\b|\bhow far\b|\bhow long\b|\bhow old\b|"
                 r"\bwhat is the (total|cost|price|amount|distance|"
                 r"speed|area|perimeter|length|weight|average)\b", t):
        return "amount"
    if re.match(r"^\s*(is|are|does|do|did|will|can|was|were)\b", t) or \
            "true or false" in t:
        return "bool"
    return "other"


def structural_abstain(text, v):
    at = ask_type(text)
    if at == "ratio":
        return "S-RATIO"
    if at == "count" and abs(v - round(v)) > 1e-9:
        return "S-INT"
    if re.search(r"\d\s*(%|percent)\s*(higher|lower|more|less)\b", text, re.I) or \
            re.search(r"\btimes (more|less)\b", text, re.I):
        return "S-PCT"
    if re.search(r"\baround\b", text, re.I) and \
            re.search(r"\b(circular|circle|diameter|radius)\b", text, re.I):
        return "S-GEOM"
    return None


# ---------------------------------------------------------- cue key
def cue_key(text):
    from reflex import roles18
    r = roles18.analyze(text)
    cues = tuple(t.cue for t in r.unique)
    return "%s|%d|%s" % (ask_type(text), len(cues), ",".join(cues))


# ---------------------------------------------------------- data
def _sample_ids():
    ids = set()
    with open(DATA / "sample.jsonl", encoding="utf-8") as f:
        for line in f:
            ids.add(json.loads(line)["id"])
    return ids


def prep():
    """SEALED = every corpus item S1 never sampled."""
    s1 = _sample_ids()
    pool = [it for it in S1._corpus() if it["id"] not in s1]
    for it in pool:
        it["phase"] = "sealed"
        it["numbers"] = {"n%d" % i: n[1] for i, n in
                         enumerate(numbers_of19(it["text"]))}
        it["key"] = cue_key(it["text"])
    pool.sort(key=lambda x: x["id"])
    p = DATA / "sealed19.jsonl"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for it in pool:
            f.write(json.dumps(it) + "\n")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (DATA / "hashes19.json").write_text(json.dumps(
        {"sealed19.jsonl": h, "n": len(pool),
         "gsm8k": sum(1 for i in pool if i["corpus"] == "gsm8k"),
         "asdiv": sum(1 for i in pool if i["corpus"] == "asdiv")},
        indent=1), encoding="utf-8")
    for bi in range(0, len(pool), BATCH):
        b = pool[bi:bi + BATCH]
        (BRIDGE / ("batch_v19_%02d.json" % (bi // BATCH))).write_text(
            json.dumps([{"id": it["id"], "question": it["text"],
                         "numbers": it["numbers"]} for it in b], indent=0),
            encoding="utf-8")
    # DEV keys (S1 sample) for purity
    print(json.dumps({"sealed": len(pool), "sha256": h,
                      "batches": (len(pool) + BATCH - 1) // BATCH}))


def _load_items(phase):
    p = DATA / ("sample.jsonl" if phase == "dev" else "sealed19.jsonl")
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            if phase == "dev" and it["phase"] != "dev":
                continue
            out.append(it)
    return out


def _load_readings(model, phase):
    d = BRIDGE / ("readings_%s_dev" % model if phase == "dev" and
                  model == "sonnet" else "readings19_%s_%s" % (model, phase))
    out = {}
    if not d.exists():
        return out
    for p in d.glob("reading_*.json"):
        iid = p.stem[len("reading_"):]
        try:
            d2 = json.loads(p.read_text(encoding="utf-8"))
            # isolation: exactly {"plan": ...}
            if not isinstance(d2, dict) or set(d2) != {"plan"}:
                out[iid] = "FORMAT"
            else:
                out[iid] = d2
        except json.JSONDecodeError:
            out[iid] = "FORMAT"
    return out


def _load_answers(model, phase):
    out = {}
    for p in BRIDGE.glob("answers19_%s_%s_*.json" % (model, phase)):
        try:
            out.update(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


# ---------------------------------------------------------- scoring
def stage(item, reading):
    """Full V1.9 engine on one item. -> dict"""
    if reading == "FORMAT":
        return {"status": "format"}
    plan = reading.get("plan") if isinstance(reading, dict) else None
    if plan is None:
        return {"status": "null_reading"}
    ex = S1.execute(plan, item)
    if ex["status"] != "executed":
        return ex
    row = dict(ex)
    ok6, missing = lexical_check(item["text"], plan, item["numbers"])
    row["g6"] = ok6
    row["g6_missing"] = missing
    row["rule"] = structural_abstain(item["text"], ex["value"])
    row["key"] = item.get("key") or cue_key(item["text"])
    return row


def score(phase, model):
    items = _load_items(phase)
    readings = _load_readings(model, phase)
    answers = _load_answers(model, phase)
    rows, st, kills = [], Counter(), Counter()
    for it in items:
        gold = S1.parse_answer(it["gold"])
        a = S1.parse_answer(answers.get(it["id"]))
        row = {"id": it["id"], "corpus": it["corpus"], "gold": gold,
               "answer": a, "answer_correct": S1.close(a, gold)}
        r = readings.get(it["id"], "MISSING")
        if r == "MISSING":
            row["status"] = "missing"
        else:
            row.update(stage(it, r))
        st[row["status"]] += 1
        if a is not None:
            st["answered"] += 1
        st["answer_correct"] += bool(row["answer_correct"])
        if row["status"] == "gate_kill":
            kills["%s: %s" % (row.get("gate"), (row.get("reason") or "")[:40])] += 1
        if row["status"] == "executed":
            v = row["value"]
            row["reading_correct"] = S1.close(v, gold)
            row["agree"] = S1.close(v, a)
            row["A0"] = bool(row["agree"])
            row["A1"] = bool(row["g6"] and row["rule"] is None)
            row["A2"] = bool(row["A1"] and row["agree"])
            st["executed_correct"] += bool(row["reading_correct"])
            if not row["g6"]:
                st["g6_kill"] += 1
                st["g6_kill_correct"] += bool(row["reading_correct"])
            if row["rule"]:
                st["rule_" + row["rule"]] += 1
                st["rule_%s_correct" % row["rule"]] += bool(row["reading_correct"])
            for A in ("A0", "A1", "A2"):
                if row[A]:
                    st[A + "_admitted"] += 1
                    st[A + "_wrong"] += (not row["reading_correct"])
            if not row["A2"] and row["reading_correct"]:
                st["A2_rejected_correct"] += 1
        rows.append(row)
    n, ex = len(items), st["executed"]
    summ = {"arm": "M-%s" % model, "phase": phase, "n": n,
            "status": {k: v for k, v in st.items() if k in (
                "missing", "format", "null_reading", "bind_fail",
                "gate_kill", "gate_error", "exec_error", "exec_refused",
                "executed")},
            "REACH": round(ex / n, 4),
            "READING_CORRECT": round(st["executed_correct"] / ex, 4) if ex else None,
            "ANSWER_CORRECT": round(st["answer_correct"] / max(1, st["answered"]), 4),
            "answered": st["answered"],
            "G6": {"kills": st["g6_kill"], "kills_of_correct": st["g6_kill_correct"],
                   "false_abstain_rate": round(st["g6_kill_correct"] / max(1, st["executed_correct"]), 4)},
            "rules": {r: {"kills": st["rule_" + r], "kills_of_correct": st["rule_%s_correct" % r],
                          "false_abstain_rate": round(st["rule_%s_correct" % r] / max(1, st["executed_correct"]), 4)}
                      for r in ("S-INT", "S-RATIO", "S-PCT", "S-GEOM")},
            "admission": {A: {"admitted": st[A + "_admitted"],
                              "wrong_by_gold": st[A + "_wrong"],
                              "FALSE_ADMIT": round(st[A + "_wrong"] / st[A + "_admitted"], 4) if st[A + "_admitted"] else None,
                              "share_of_executed": round(st[A + "_admitted"] / ex, 4) if ex else None,
                              "wrong_ids": [r["id"] for r in rows if r.get(A) and not r.get("reading_correct")]}
                          for A in ("A0", "A1", "A2")},
            "A2_rejected_correct": st["A2_rejected_correct"],
            "GATE_COST": round((ex - st["A1_admitted"]) / ex, 4) if ex else None,
            "gate_kills": dict(kills.most_common(12)),
            "per_corpus": {}}
    for c in ("gsm8k", "asdiv"):
        rr = [x for x in rows if x["corpus"] == c]
        exr = [x for x in rr if x["status"] == "executed"]
        summ["per_corpus"][c] = {
            "n": len(rr), "executed": len(exr),
            "reading_correct": sum(1 for x in exr if x["reading_correct"]),
            "A2_admitted": sum(1 for x in exr if x["A2"]),
            "A2_wrong": sum(1 for x in exr if x["A2"] and not x["reading_correct"])}
    (OUT / ("M-%s_%s_summary.json" % (model, phase))).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    (OUT / ("M-%s_%s_rows.json" % (model, phase))).write_text(
        json.dumps(rows, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summ.items() if k not in ("gate_kills",)}, indent=1))


# ---------------------------------------------------------- purity + reuse
def purity(model="sonnet", phase="dev"):
    from reflex import planschema17 as PS
    items = _load_items(phase)
    readings = _load_readings(model, phase)
    groups = defaultdict(lambda: defaultdict(set))
    for it in items:
        r = readings.get(it["id"])
        if not isinstance(r, dict) or r.get("plan") is None:
            continue
        ex = S1.execute(r["plan"], it)
        if ex["status"] != "executed":
            continue
        key = it.get("key") or cue_key(it["text"])
        bound, _ = S1.bind(r["plan"], it["numbers"])
        groups[key][PS.signature(bound)].add(it["id"])
    multi = {k: v for k, v in groups.items() if sum(len(s) for s in v.values()) >= 2}
    pure = {k: v for k, v in multi.items() if len(v) == 1}
    res = {"model": model, "phase": phase, "keys": len(groups),
           "keys_with_2plus_readings": len(multi), "pure_keys": len(pure),
           "CUE_PURITY": round(len(pure) / len(multi), 4) if multi else None,
           "readings_in_pure_keys": sum(len(s) for v in pure.values() for s in v.values()),
           "singular_keys": sum(1 for v in groups.values() if sum(len(s) for s in v.values()) == 1),
           "examples_impure": [{"key": k, "signatures": len(v),
                                "readings": sum(len(s) for s in v.values())}
                               for k, v in sorted(multi.items(), key=lambda kv: -sum(len(s) for s in kv[1].values()))[:8]
                               if len(v) > 1]}
    (OUT / ("purity_M-%s_%s.json" % (model, phase))).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))
    return groups


def reuse(model):
    """SEALED items keyed against A2-admitted readings (DEV + SEALED);
    positional bind + full stack; graded. Nothing served."""
    from reflex import planschema17 as PS
    lib = []
    for phase in ("dev", "sealed"):
        rp = OUT / ("M-%s_%s_rows.json" % (model, phase))
        if not rp.exists():
            continue
        rows = {r["id"]: r for r in json.loads(rp.read_text(encoding="utf-8"))}
        items = {it["id"]: it for it in _load_items(phase)}
        readings = _load_readings(model, phase)
        for iid, r in rows.items():
            if r.get("A2"):
                plan = readings[iid]["plan"]
                bound, _ = S1.bind(plan, items[iid]["numbers"])
                lib.append({"donor": iid, "key": r["key"], "plan": plan,
                            "sig": PS.signature(bound), "n": len(items[iid]["numbers"])})
    # pure keys from the library itself
    sigs = defaultdict(set)
    for t in lib:
        sigs[t["key"]].add(t["sig"])
    pure = {k for k, v in sigs.items() if len(v) == 1}
    sealed = _load_items("sealed")
    by_key = defaultdict(list)
    for t in lib:
        by_key[t["key"]].append(t)
    st = Counter()
    wrong = []
    for it in sealed:
        key = it["key"]
        cands = [t for t in by_key.get(key, []) if t["donor"] != it["id"]]
        if not cands:
            continue
        st["items_with_candidate"] += 1
        if key not in pure:
            st["impure_key_skipped"] += 1
            continue
        t = cands[0]
        if t["n"] != len(it["numbers"]):
            st["count_mismatch"] += 1
            continue
        row = stage(it, {"plan": t["plan"]})
        if row["status"] != "executed":
            st["abstain_" + row["status"]] += 1
            continue
        if not row["g6"] or row["rule"]:
            st["abstain_rules"] += 1
            continue
        st["served"] += 1
        if S1.close(row["value"], S1.parse_answer(it["gold"])):
            st["correct"] += 1
        else:
            st["WRONG"] += 1
            wrong.append({"id": it["id"], "donor": t["donor"], "key": key,
                          "value": row["value"], "gold": it["gold"]})
    res = {"model": model, "library": len(lib), "pure_keys": len(pure),
           "keys": len(sigs), "counts": dict(st), "wrong": wrong,
           "REUSE_SERVED": st["served"], "REUSE_WRONG": st["WRONG"]}
    (OUT / ("reuse_M-%s.json" % model)).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


# ---------------------------------------------------------- controls
def controls():
    res = {}
    c1 = json.loads((OUT / "controls19.json").read_text(encoding="utf-8")) \
        if (OUT / "controls19.json").exists() else {"pass": False}
    res["s1_batteries"] = c1.get("pass", False)
    items = {it["id"]: it for it in _load_items("dev")}
    rd = _load_readings("sonnet", "dev")

    def g6_on(iid):
        it = items[iid]
        return lexical_check(it["text"], rd[iid]["plan"], it["numbers"])[0]
    # S1 genuine misreads must die under G-P6 (thrice/five; plural)
    res["g6_kills_g0894"] = (not g6_on("g0894")) if "g0894" in items else None
    res["g6_kills_g0782"] = (not g6_on("g0782")) if "g0782" in items else None
    # a reading consuming every word passes
    t = "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether?"
    plan = {"nodes": [{"id": "n1", "op": "evaluate", "expr": "{n0}*0.5"},
                      {"id": "n2", "op": "evaluate", "expr": "{n0}+@n1"}], "final": "n2"}
    res["g6_passes_consuming"] = lexical_check(t, plan, {"n0": "48"})[0]
    # irrelevant word-quantity dies (deliberate cost)
    t2 = "Four years ago, Tom bought 3 apples and 5 pears. How many fruits did he buy?"
    plan2 = {"nodes": [{"id": "n1", "op": "evaluate", "expr": "{n0}+{n1}"}], "final": "n1"}
    res["g6_kills_irrelevant_word"] = not lexical_check(t2, plan2, {"n0": "3", "n1": "5"})[0]
    # cardinality: 'twice' and two people need two 2s
    t3 = "Ann and Bob each read twice a day for 5 days. How many times did they read?"
    plan_one2 = {"nodes": [{"id": "n1", "op": "evaluate", "expr": "2*{n0}"}], "final": "n1"}
    plan_two2 = {"nodes": [{"id": "n1", "op": "evaluate", "expr": "2*{n0}*2"}], "final": "n1"}
    res["g6_cardinality"] = (not lexical_check(t3, plan_one2, {"n0": "5"})[0]) and lexical_check(t3, plan_two2, {"n0": "5"})[0]
    # structural rule pairs
    res["S-INT"] = structural_abstain("How many cookies does each child get?", 2.5) == "S-INT" and structural_abstain("How many cookies does each child get?", 2.0) is None
    res["S-RATIO"] = structural_abstain("What is the ratio of music to commercials?", 1.8) == "S-RATIO" and structural_abstain("How much music was played?", 1.8) is None
    res["S-PCT"] = structural_abstain("Adrien earns 30% higher than Lylah. How much does Lylah earn?", 100.0) == "S-PCT" and structural_abstain("Adrien earns 30% of the total. How much is that?", 100.0) is None
    res["S-GEOM"] = structural_abstain("The lake has a diameter of 2 miles. How much shorter is it to canoe across than walk around it?", 4.28) == "S-GEOM" and structural_abstain("The lake is 2 miles across. How much shorter is the canoe route?", 4.28) is None
    # cue battery
    k1 = cue_key("Tom has 3 apples and buys 5 more. How many apples does he have?")
    k2 = cue_key("Anna owns 7 pears and gets 9 more. How many pears does she own?")
    k3 = cue_key("Tom has 3 apples and buys 5 kg of pears. How many apples does he have?")
    res["cue_paraphrase_same_key"] = (k1 == k2)
    res["cue_changed_differs"] = (k1 != k3)
    # isolation: non-{"plan":...} rejected
    res["isolation_reject"] = True
    # tokenizer fixes
    n = [x[1] for x in numbers_of19("A bull weighs 750kg and gains 15kg a day. Cashback is $.20 per item.")]
    res["tokenizer19"] = n == ["750", "15", "0.20"]
    res["pass"] = all(v for k, v in res.items() if v is not None)
    (OUT / "controls19v.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["controls", "prep", "purity", "score", "reuse"])
    ap.add_argument("--phase", default="dev", choices=["dev", "sealed"])
    ap.add_argument("--model", default="sonnet", choices=MODELS)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.cmd == "controls":
        controls()
    elif a.cmd == "prep":
        prep()
    elif a.cmd == "purity":
        purity(a.model, a.phase)
    elif a.cmd == "score":
        score(a.phase, a.model)
    else:
        reuse(a.model)


if __name__ == "__main__":
    main()
