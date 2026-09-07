# -*- coding: utf-8 -*-
# origin: new for V1.9 -- reading reflexes, offline gold-graded (V19_SPEC)
"""
  python tools/reader19.py prep
      samples 1,800 items (seed 1900; 900 GSM8K + 900 ASDiv), splits
      DEV 600 / SEALED 1,200 by id hash, writes
        results/v19/data/sample.jsonl        (with golds; hashed)
        results/v19/bridge/batch_<phase>_NN.json   (NO golds)
  python tools/reader19.py controls
  python tools/reader19.py score --phase dev --proposer sonnet --answerer haiku
      reads results/v19/bridge/readings_<proposer>_<phase>/reading_<id>.json
        and results/v19/bridge/answers_<answerer>_<phase>_*.json,
      binds, gates, executes, grades, transfers; writes
        results/v19/R-<proposer>-<answerer>_<phase>_{summary,rows}.json

A READING is a planschema17 plan over slots "{n<i>}" = the question's
numbers in order of appearance. Binding substitutes the item's own
numbers; the concrete plan goes through plangate18 (G-P1..G-P5 with
G-P4' usage matching; bare tokens expected) and chainexec17. Calendar
constants (12, 60, 7, 24, 365) are whitelisted for the gate ONLY
inside this module's check (the V1.7 gate is not edited).
"""
import argparse
import hashlib
import json
import random
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
sys.path.insert(0, str(HERE / "tools"))
OUT = HERE / "results" / "v19"
DATA = OUT / "data"
BRIDGE = OUT / "bridge"
BATCH = 25
SEED = 1900
CALENDAR = {12.0, 60.0, 7.0, 24.0, 365.0}
NUM = re.compile(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)(?![\w])")
KEEP_CAP = {"how", "what", "when", "where", "which", "who", "why",
            "if", "there", "a", "an", "the", "each", "every", "all",
            "both", "some", "in", "on", "at", "after", "before",
            "during", "yesterday", "today", "tomorrow", "one", "two",
            "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "twenty", "thirty", "forty",
            "fifty", "hundred", "thousand", "half", "twice", "it",
            "he", "she", "they", "we", "you", "i", "this", "that",
            "these", "those", "of", "for", "to", "with", "by", "from",
            "and", "or", "but", "so", "then", "now", "last", "first",
            "next", "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday", "january", "february",
            "march", "april", "may", "june", "july", "august",
            "september", "october", "november", "december"}
STOP = {"a", "an", "the", "of", "to", "in", "on", "at", "for", "and",
        "is", "are", "was", "were", "be", "it", "its", "he", "she",
        "they", "his", "her", "their", "that", "this", "with", "by",
        "from", "as", "has", "have", "had", "did", "does", "do",
        "there", "each", "per", "how", "many", "much", "what", "if",
        "then", "than", "so", "will", "would", "total", "altogether"}


# ---------------------------------------------------------------- data
def _corpus():
    out = []
    with open(HERE / "corpora" / "gsm8k_test.jsonl", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            d = json.loads(line)
            out.append({"id": "g%04d" % i, "corpus": "gsm8k",
                        "text": d["question"].strip(),
                        "gold": d["answer"].split("####")[-1].strip()
                        .replace(",", "")})
    x = ET.parse(HERE / "corpora" / "asdiv.xml").getroot()
    for i, pr in enumerate(x.iter("Problem")):
        body = (pr.findtext("Body") or "").strip()
        q = (pr.findtext("Question") or "").strip()
        ans = (pr.findtext("Answer") or "").strip()
        m = re.match(r"-?\d[\d,]*(?:\.\d+)?", ans)
        if body and q and m:
            out.append({"id": "a%04d" % i, "corpus": "asdiv",
                        "text": "%s %s" % (body, q),
                        "gold": m.group(0).replace(",", "")})
    return out


def numbers_of(text):
    """[(raw, magnitude_str, start, end)] of stated numbers."""
    out = []
    for m in NUM.finditer(text):
        raw = m.group(1)
        if re.match(r"^-?\d+(?:st|nd|rd|th)$", text[m.start(1):m.end(1) + 2]):
            continue
        out.append((raw, raw.replace(",", "").lstrip("-"), m.start(1),
                    m.end(1)))
    return out


def skeleton(text, level=0):
    t = text
    t = NUM.sub(lambda m: ("-#" if m.group(1).startswith("-") else "#"), t)
    t = t.lower() if level == 0 else t
    if level >= 1:
        from reflex.roles18 import UNIT_CANON
        # names: capitalised tokens not at sentence start
        toks = re.split(r"(\s+)", t)
        out = []
        for tk in toks:
            if tk.strip() == "":
                out.append(tk)
                continue
            w = tk.strip(".,;:!?\"'()")
            # a name is any capitalised token that is not a frozen
            # sentence-starter / number word / unit (sentence-initial
            # names are common in word problems)
            if w[:1].isupper() and w.lower() not in UNIT_CANON and \
                    w.lower() not in KEEP_CAP:
                tk = tk.replace(w, "@")
            out.append(tk)
        t = "".join(out).lower()
        t = re.sub(r"[$€£]", "$", t)
        for u, c in sorted(UNIT_CANON.items(), key=lambda kv: -len(kv[0])):
            t = re.sub(r"\b%s\b" % re.escape(u), c.lower(), t)
    if level >= 2:
        t = re.sub(r"[^\w#@$\s]", " ", t)
        t = " ".join(w for w in t.split() if w not in STOP)
    return re.sub(r"\s+", " ", t).strip()


def prep():
    DATA.mkdir(parents=True, exist_ok=True)
    BRIDGE.mkdir(parents=True, exist_ok=True)
    pool = _corpus()
    rng = random.Random(SEED)
    g = [it for it in pool if it["corpus"] == "gsm8k"]
    a = [it for it in pool if it["corpus"] == "asdiv"]
    rng.shuffle(g)
    rng.shuffle(a)
    sample = g[:900] + a[:900]
    for it in sample:
        h = int(hashlib.sha256(it["id"].encode()).hexdigest(), 16)
        it["phase"] = "dev" if (h % 3 == 0) else "sealed"
        it["numbers"] = {"n%d" % i: n[1] for i, n in
                         enumerate(numbers_of(it["text"]))}
        it["skeleton_L0"] = skeleton(it["text"], 0)
        it["skeleton_L1"] = skeleton(it["text"], 1)
        it["skeleton_L2"] = skeleton(it["text"], 2)
    # rebalance to exactly 600 dev
    dev = [it for it in sample if it["phase"] == "dev"]
    sealed = [it for it in sample if it["phase"] == "sealed"]
    rng.shuffle(dev)
    rng.shuffle(sealed)
    while len(dev) > 600:
        it = dev.pop()
        it["phase"] = "sealed"
        sealed.append(it)
    while len(dev) < 600:
        it = sealed.pop()
        it["phase"] = "dev"
        dev.append(it)
    sample = sorted(dev + sealed, key=lambda x: x["id"])
    p = DATA / "sample.jsonl"
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        for it in sample:
            f.write(json.dumps(it) + "\n")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (DATA / "hashes.json").write_text(json.dumps(
        {"sample.jsonl": h, "seed": SEED, "n": len(sample),
         "dev": sum(1 for i in sample if i["phase"] == "dev"),
         "sealed": sum(1 for i in sample if i["phase"] == "sealed")},
        indent=1), encoding="utf-8")
    for phase in ("dev", "sealed"):
        items = [it for it in sample if it["phase"] == phase]
        for bi in range(0, len(items), BATCH):
            b = items[bi:bi + BATCH]
            (BRIDGE / ("batch_%s_%02d.json" % (phase, bi // BATCH))
             ).write_text(json.dumps(
                 [{"id": it["id"], "question": it["text"],
                   "numbers": it["numbers"]} for it in b], indent=0),
                 encoding="utf-8")
    print(json.dumps({"n": len(sample), "sha256": h,
                      "dev": len(dev), "sealed": len(sealed)}))


# ---------------------------------------------------------------- bind
_SLOT = re.compile(r"\{n(\d+)\}")


def bind(reading, numbers):
    """reading plan over {n<i>} -> concrete plan, or (None, why)."""
    if not isinstance(reading, dict) or "nodes" not in reading:
        return None, "format"
    nodes = []
    used = set()
    for n in reading["nodes"]:
        if not isinstance(n, dict):
            return None, "format"
        nd = {}
        for k, v in n.items():
            if isinstance(v, str):
                m = _SLOT.fullmatch(v.strip())
                if m:
                    key = "n" + m.group(1)
                    if key not in numbers:
                        return None, "slot_out_of_range"
                    used.add(key)
                    nd[k] = float(numbers[key])
                    continue
                if "{n" in v:
                    bad = []

                    def rep(mm):
                        key = "n" + mm.group(1)
                        if key not in numbers:
                            bad.append(key)
                            return "0"
                        used.add(key)
                        return numbers[key]
                    s = _SLOT.sub(rep, v)
                    if bad:
                        return None, "slot_out_of_range"
                    nd[k] = s
                    continue
            nd[k] = v
        nodes.append(nd)
    return {"nodes": nodes, "final": reading.get("final")}, None


def gate_check(plan, text):
    """plangate18 with calendar constants whitelisted for THIS check."""
    from reflex import plangate17, plangate18, roles18
    orig = plangate17.STRUCTURAL
    flags = (plangate18.STRUCTURAL_EXPR_OPTIONAL,
             plangate18.LITERAL_REUSE_OK, plangate18.UNIT_IN_EXPR_OK)
    plangate17.STRUCTURAL = set(orig) | CALENDAR
    plangate18.STRUCTURAL_EXPR_OPTIONAL = True
    plangate18.LITERAL_REUSE_OK = True
    plangate18.UNIT_IN_EXPR_OK = True
    try:
        return plangate18.check(plan, text, roles18.analyze(text))
    finally:
        plangate17.STRUCTURAL = orig
        (plangate18.STRUCTURAL_EXPR_OPTIONAL, plangate18.LITERAL_REUSE_OK,
         plangate18.UNIT_IN_EXPR_OK) = flags


def execute(reading, item):
    """-> dict(status, value, reason)"""
    from reflex import chainexec17
    if reading is None:
        return {"status": "null_reading"}
    plan, why = bind(reading, item["numbers"])
    if plan is None:
        return {"status": "bind_fail", "reason": why}
    try:
        ok, t = gate_check(plan, item["text"])
    except Exception as exc:                 # noqa: BLE001
        return {"status": "gate_error", "reason": repr(exc)[:80]}
    if not ok:
        return {"status": "gate_kill", "gate": t[-1].get("gate"),
                "reason": (t[-1].get("kill") or "")[:80]}
    try:
        v, cert = chainexec17.run(plan)
    except Exception as exc:                 # noqa: BLE001
        return {"status": "exec_error", "reason": repr(exc)[:80]}
    if v is None:
        return {"status": "exec_refused",
                "reason": (cert.get("why") if isinstance(cert, dict)
                           else "")[:80]}
    return {"status": "executed", "value": float(v)}


def parse_answer(s):
    if s is None:
        return None
    s = str(s).replace(",", "").replace("$", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def close(a, b, tol=1e-4):
    if a is None or b is None:
        return False
    return abs(a - b) <= max(tol * abs(b), 1e-6)


# ---------------------------------------------------------------- score
def _load_sample(phase):
    out = []
    with open(DATA / "sample.jsonl", encoding="utf-8") as f:
        for line in f:
            it = json.loads(line)
            if it["phase"] == phase:
                out.append(it)
    return out


def _load_readings(proposer, phase):
    d = BRIDGE / ("readings_%s_%s" % (proposer, phase))
    out = {}
    if not d.exists():
        return out
    for p in d.glob("reading_*.json"):
        iid = p.stem[len("reading_"):]
        try:
            out[iid] = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            out[iid] = "UNPARSEABLE"
    return out


def _load_answers(answerer, phase):
    out = {}
    for p in BRIDGE.glob("answers_%s_%s_*.json" % (answerer, phase)):
        try:
            out.update(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def score(phase, proposer, answerer):
    items = _load_sample(phase)
    readings = _load_readings(proposer, phase)
    answers = _load_answers(answerer, phase)
    rows = []
    st = Counter()
    kills = Counter()
    for it in items:
        r = readings.get(it["id"], "MISSING")
        gold = parse_answer(it["gold"])
        a = parse_answer(answers.get(it["id"]))
        row = {"id": it["id"], "corpus": it["corpus"], "gold": gold,
               "answer": a, "answer_correct": close(a, gold)}
        if r == "MISSING":
            row["status"] = "missing"
        elif r == "UNPARSEABLE":
            row["status"] = "format"
        else:
            reading = r.get("plan") if isinstance(r, dict) and \
                "plan" in r else r
            if reading is None:
                row["status"] = "null_reading"
            else:
                ex = execute(reading, it)
                row.update(ex)
                if ex["status"] == "gate_kill":
                    kills["%s: %s" % (ex["gate"], ex["reason"][:40])] += 1
        st[row["status"]] += 1
        if a is not None:
            st["answered"] += 1
        if row["answer_correct"]:
            st["answer_correct"] += 1
        if row["status"] == "executed":
            v = row["value"]
            row["reading_correct"] = close(v, gold)
            row["agree"] = close(v, a)
            st["reading_correct" if row["reading_correct"] else
               "reading_wrong"] += 1
            if row["agree"]:
                st["admitted"] += 1
                st["admitted_correct" if row["reading_correct"] else
                   "FALSE_ADMIT"] += 1
            elif row["reading_correct"]:
                st["disagree_but_correct"] += 1
            if not row["reading_correct"] and gold is not None and \
                    abs(v - gold) <= 0.02 * max(1e-9, abs(gold)):
                st["near_miss"] += 1
        rows.append(row)
    n = len(items)
    executed = st["executed"]
    admitted = st["admitted"]
    summ = {"arm": "R-%s-%s" % (proposer, answerer), "phase": phase,
            "n": n, "status": {k: v for k, v in st.items()
                               if k in ("missing", "format",
                                        "null_reading", "bind_fail",
                                        "gate_kill", "gate_error",
                                        "exec_error", "exec_refused",
                                        "executed")},
            "REACH": round(executed / n, 4),
            "READING_CORRECT": round(st["reading_correct"] / executed, 4)
            if executed else None,
            "admitted": admitted,
            "FALSE_ADMIT": round(st["FALSE_ADMIT"] / admitted, 4)
            if admitted else None,
            "FALSE_ADMIT_n": st["FALSE_ADMIT"],
            "READING_CORRECT_admitted": round(
                st["admitted_correct"] / admitted, 4) if admitted else None,
            "ANSWERER_CORRECT": round(st["answer_correct"] /
                                      max(1, st["answered"]), 4),
            "answered": st["answered"],
            "disagree_but_correct": st["disagree_but_correct"],
            "near_miss": st["near_miss"],
            "gate_kills": dict(kills.most_common(15)),
            "per_corpus": {}}
    for c in ("gsm8k", "asdiv"):
        rr = [x for x in rows if x["corpus"] == c]
        ex = [x for x in rr if x["status"] == "executed"]
        ad = [x for x in ex if x.get("agree")]
        summ["per_corpus"][c] = {
            "n": len(rr), "executed": len(ex),
            "reading_correct": sum(1 for x in ex if x["reading_correct"]),
            "admitted": len(ad),
            "false_admit": sum(1 for x in ad if not x["reading_correct"])}
    # transfer
    summ["transfer"] = transfer(items, readings, rows)
    OUT.mkdir(parents=True, exist_ok=True)
    base = "R-%s-%s_%s" % (proposer, answerer, phase)
    (OUT / ("%s_summary.json" % base)).write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    (OUT / ("%s_rows.json" % base)).write_text(
        json.dumps(rows, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))


def transfer(items, readings, rows):
    """For every executed reading, other items sharing its skeleton at
    L0/L1/L2: bind + gate + exec on them; grade vs gold."""
    by_id = {it["id"]: it for it in items}
    executed = [r["id"] for r in rows if r["status"] == "executed"]
    res = {}
    for L in (0, 1, 2):
        key = "skeleton_L%d" % L
        groups = {}
        for it in items:
            groups.setdefault(it[key], []).append(it["id"])
        refire = served = correct = wrong = 0
        donors_with_match = 0
        for d in executed:
            it = by_id[d]
            others = [o for o in groups.get(it[key], []) if o != d]
            if not others:
                continue
            donors_with_match += 1
            r = readings[d]
            reading = r.get("plan") if isinstance(r, dict) and \
                "plan" in r else r
            for o in others:
                refire += 1
                oi = by_id[o]
                if len(oi["numbers"]) != len(it["numbers"]):
                    continue
                ex = execute(reading, oi)
                if ex["status"] != "executed":
                    continue
                served += 1
                if close(ex["value"], parse_answer(oi["gold"])):
                    correct += 1
                else:
                    wrong += 1
        res["L%d" % L] = {"donors_with_match": donors_with_match,
                          "refire_pairs": refire, "served": served,
                          "correct": correct, "WRONG": wrong,
                          "skeletons": len(groups)}
    return res


# ---------------------------------------------------------------- controls
def controls():
    from reflex import plangate17, plangate18, chainexec17
    res = {}
    ok17, _ = plangate17.control_battery()
    ok18, _ = plangate18.control_battery()
    okx, _ = chainexec17.gate_control()
    res["gates"] = ok17 and ok18 and okx
    # bind battery on a GSM8K-shaped item
    it = {"id": "ctrl", "text": "Natalia sold clips to 48 of her friends "
                                "in April, and then she sold half as many "
                                "clips in May. How many clips did Natalia "
                                "sell altogether in April and May?",
          "gold": "72"}
    it["numbers"] = {"n%d" % i: n[1] for i, n in
                     enumerate(numbers_of(it["text"]))}
    good = {"nodes": [{"id": "n1", "op": "evaluate", "expr": "{n0}*0.5"},
                      {"id": "n2", "op": "evaluate", "expr": "@n1+{n0}"}],
            "final": "n2"}
    ex = execute(good, it)
    res["bind_good"] = ex.get("status") == "executed" and \
        close(ex.get("value"), 72.0)
    # a two-number item with slots swapped: caught by gate or by gold
    it2 = {"id": "ctrl2", "text": "Weng earns 12 dollars an hour for "
                                  "babysitting. Yesterday, she just did 50 "
                                  "minutes of babysitting. How much did "
                                  "she earn?", "gold": "10"}
    it2["numbers"] = {"n%d" % i: n[1] for i, n in
                      enumerate(numbers_of(it2["text"]))}
    right = {"nodes": [{"id": "n1", "op": "evaluate",
                        "expr": "{n0}*{n1}/60"}], "final": "n1"}
    # a WRONG reading with every slot present (12*60/50): the gate
    # cannot see it -- only gold, or in production only agreement,
    # can. The battery records which caught it.
    swapped = {"nodes": [{"id": "n1", "op": "evaluate",
                          "expr": "{n0}*60/{n1}"}], "final": "n1"}
    exr = execute(right, it2)
    exs = execute(swapped, it2)
    res["bind_right"] = exr.get("status") == "executed" and \
        close(exr.get("value"), 10.0)
    # multiplication is commutative: swap must still be caught by
    # gold, not the gate -- record which
    res["swap_caught_by"] = ("gate" if exs.get("status") != "executed"
                             else ("gold" if not close(exs.get("value"),
                                                       10.0) else "NOT"))
    # agreement battery: wrong value + answerer equal to it -> false admit
    res["false_admit_countable"] = (close(20.0, parse_answer("$20")) and
                                    not close(20.0, 10.0))
    # skeleton battery
    a1 = "Tom has 3 apples and Mary has 5 apples. How many apples do they have?"
    a2 = "Anna has 7 apples and Paul has 9 apples. How many apples do they have?"
    res["skeleton_L1_match"] = skeleton(a1, 1) == skeleton(a2, 1)
    res["skeleton_L0_differs"] = skeleton(a1, 0) != skeleton(a2, 0)
    res["pass"] = all(v for k, v in res.items()
                      if k not in ("swap_caught_by",)) and \
        res["swap_caught_by"] in ("gate", "gold")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "controls19.json").write_text(json.dumps(res, indent=1),
                                         encoding="utf-8")
    print(json.dumps(res, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "controls", "score"])
    ap.add_argument("--phase", default="dev", choices=["dev", "sealed"])
    ap.add_argument("--proposer", default="sonnet")
    ap.add_argument("--answerer", default="haiku")
    a = ap.parse_args()
    if a.cmd == "prep":
        prep()
    elif a.cmd == "controls":
        controls()
    else:
        score(a.phase, a.proposer, a.answerer)


if __name__ == "__main__":
    main()
