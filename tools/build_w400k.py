# -*- coding: utf-8 -*-
"""V1.10 W-400K workload builder (frozen seed 11010; deterministic).

Tiers (V110_SPEC.md §5.1):
  T1  one-step arithmetic, plain narrative language        80,000  generator
  T2  two/three-step simple word problems                  80,000  generator
  T3  GSM8K train (real)                                    7,473  corpus
  T3p SVAMP (real structural variants)                      1,000  corpus
  T4  complex word problems — AUTHORING REQUESTS           20,000  plan+values (text authored via bridge)
  P1  physics single formula                               80,000  build_q100k tier-A physics caps
  P2  physics chains k=3                                   60,000  build_q1m
  P3  physics chains k=5-6, multidomain, non-monotonic     40,000  build_q1m
  P4  physics word problems — AUTHORING REQUESTS           10,000  P3-style plan+values
  PC  SciQ test concept MC                                  1,000  corpus
  D   distractors (no computable ask)                       2% overlay, generator
Golds: T1/T2/T4 = python eval AND reader19 execute agree (two evaluators);
P1 = build_q100k witness formula; P2-P4 = chain_witness17 double replay;
corpora = as given (never relabelled). Splits by sha1(id): acq 40 / dev 10 /
seal 25 / replay 25. Authored tiers additionally carry author_model
(round-robin by hash) so no arm is sealed on items its model authored.
"""
import hashlib
import json
import math
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tools"))
import build_q100k as Q16  # noqa: E402
import build_q1m as Q17  # noqa: E402
import chain_witness17 as CW  # noqa: E402
import reader19 as S1  # noqa: E402
import reader19v as V  # noqa: E402
from reflex import planschema17 as PS  # noqa: E402

SEED = 11010
DATA = HERE / "results" / "v110" / "data"
BRIDGE = HERE / "results" / "v110" / "bridge"
QUOTA = {"T1": 80000, "T2": 80000, "T4": 20000, "P1": 80000,
         "P2": 60000, "P3": 40000, "P4": 10000}
MODELS = ["sonnet", "opus", "haiku", "fable"]

NAMES = ["Ann", "Ben", "Carla", "Dev", "Elena", "Farid", "Grace", "Hugo",
         "Ines", "Jamal", "Kira", "Leo", "Maya", "Noah", "Olga", "Priya",
         "Quinn", "Ravi", "Sara", "Tom", "Uma", "Victor", "Wren", "Yara",
         "Zane", "Mr. Lopez", "Mrs. Chen", "Ms. Okafor", "Coach Diaz",
         "Aunt Mei"]
THINGS = ["apples", "marbles", "stickers", "books", "pencils", "coins",
          "cookies", "cards", "shells", "balloons", "tickets", "eggs",
          "buttons", "beads", "stamps", "oranges", "toy cars", "photos",
          "crayons", "cupcakes", "bottles", "cans", "flowers", "rocks"]
GROUPS = ["boxes", "bags", "baskets", "packs", "shelves", "crates",
          "jars", "rows", "trays", "cartons"]
PEOPLE = ["friends", "students", "children", "cousins", "teammates",
          "neighbors", "classmates", "players"]
ITEMS_PRICE = ["notebook", "pen", "ticket", "sandwich", "toy", "book",
               "mug", "cap", "poster", "puzzle"]

# ---------------------------------------------------------------- helpers


def h(s):
    return hashlib.sha1(s.encode()).hexdigest()


def split_of(iid):
    x = int(h(iid)[:8], 16) / 0xFFFFFFFF
    return "acq" if x < 0.40 else "dev" if x < 0.50 else "seal" if x < 0.75 else "replay"


def author_of(iid):
    return MODELS[int(h("author:" + iid)[:8], 16) % 4]


def slots_plan(exprs):
    """exprs: list of expression strings over {n0}.. and @n<k> -> reading plan."""
    nodes = [{"id": "n%d" % (i + 1), "op": "evaluate", "expr": e}
             for i, e in enumerate(exprs)]
    return {"nodes": nodes, "final": nodes[-1]["id"]}


def eval_plan(exprs, vals):
    env = {}
    for i, e in enumerate(exprs):
        ee = e
        for k, v in vals.items():
            ee = ee.replace("{%s}" % k, "(%r)" % float(v))
        for j in range(i):
            ee = ee.replace("@n%d" % (j + 1), "(%r)" % env["n%d" % (j + 1)])
        env["n%d" % (i + 1)] = eval(ee, {"__builtins__": {}}, {})  # noqa: S307
    return env["n%d" % len(exprs)]


def two_evaluator_gold(text, exprs):
    """gold by python eval; must agree with reader19's execute (bind + chainexec17)."""
    nums = V.numbers_of19(text)
    vals = {"n%d" % i: n[1] for i, n in enumerate(nums)}
    if len(vals) != len(set(re.findall(r"\{(n\d+)\}", " ".join(exprs)))):
        return None, None
    g1 = eval_plan(exprs, vals)
    item = {"text": text, "numbers": vals, "gold": str(g1)}
    ex = S1.execute(slots_plan(exprs), item)
    if ex.get("status") != "executed" or ex.get("value") is None:
        return None, ex.get("status")
    if not S1.close(ex["value"], g1):
        return None, "evaluator_disagree"
    return g1, vals


def fmt(v):
    return ("%d" % v) if float(v).is_integer() else ("%.2f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- T1


def gen_t1(rng):
    n1, n2 = rng.choice(NAMES), rng.choice(NAMES)
    while n2 == n1:
        n2 = rng.choice(NAMES)
    th, gp, pp, it = rng.choice(THINGS), rng.choice(GROUPS), rng.choice(PEOPLE), rng.choice(ITEMS_PRICE)
    a, b = rng.randint(2, 90), rng.randint(2, 60)
    k = rng.randrange(14)
    if k == 0:
        t = f"{n1} has {a} {th}. {n2} gives {n1} {b} more {th}. How many {th} does {n1} have now?"; e = ["{n0}+{n1}"]
    elif k == 1:
        a = max(a, b + 1)
        t = f"{n1} had {a} {th} and gave {b} of them to {n2}. How many {th} does {n1} have left?"; e = ["{n0}-{n1}"]
    elif k == 2:
        t = f"There are {a} {gp} of {th}. Each of the {gp} holds {b} {th}. How many {th} are there altogether?"; e = ["{n0}*{n1}"]
    elif k == 3:
        b = rng.randint(2, 12); a = b * rng.randint(2, 15)
        t = f"{n1} shares {a} {th} equally among {b} {pp}. How many {th} does each of the {pp} get?"; e = ["{n0}/{n1}"]
    elif k == 4:
        t = f"{n1} has {a} {th} and {n2} has {b} {th}. How many {th} do they have together?"; e = ["{n0}+{n1}"]
    elif k == 5:
        a = max(a, b + 1)
        t = f"{n1} has {a} {th}. {n2} has {b} {th}. How many more {th} does {n1} have than {n2}?"; e = ["{n0}-{n1}"]
    elif k == 6:
        p = rng.randint(2, 40)
        t = f"A {it} costs {p} dollars. How much do {b} of them cost?"; e = ["{n0}*{n1}"]
    elif k == 7:
        b = rng.randint(2, 12); a = b * rng.randint(2, 20)
        t = f"{n1} paid {a} dollars for {b} identical {it}s. What was the price of one {it}?"; e = ["{n0}/{n1}"]
    elif k == 8:
        a = rng.randint(20, 200); b = rng.randint(1, a - 1)
        t = f"{n1} had {a} dollars and spent {b} dollars on a {it}. How much money does {n1} have left?"; e = ["{n0}-{n1}"]
    elif k == 9:
        t = f"A bus makes {a} trips a day and carries {b} people on each trip. How many people does it carry in a day?"; e = ["{n0}*{n1}"]
    elif k == 10:
        b = rng.randint(2, 9); a = b * rng.randint(3, 30)
        t = f"{a} {th} are put into {gp} of {b}. How many {gp} are filled?"; e = ["{n0}/{n1}"]
    elif k == 11:
        t = f"{n1} read {a} pages on Monday and {b} pages on Tuesday. How many pages did {n1} read in total?"; e = ["{n0}+{n1}"]
    elif k == 12:
        a = rng.randint(30, 300); b = rng.randint(5, a - 5)
        t = f"A tank held {a} liters of water. {b} liters were used. How many liters are left in the tank?"; e = ["{n0}-{n1}"]
    else:
        t = f"{n1} runs {a} laps every day. How many laps does {n1} run in {b} days?"; e = ["{n0}*{n1}"]
    return t, e


# ---------------------------------------------------------------- T2 (2-3 steps)


def gen_t2(rng):
    n1, n2 = rng.choice(NAMES), rng.choice(NAMES)
    while n2 == n1:
        n2 = rng.choice(NAMES)
    th, gp, pp, it = rng.choice(THINGS), rng.choice(GROUPS), rng.choice(PEOPLE), rng.choice(ITEMS_PRICE)
    k = rng.randrange(16)
    if k == 0:
        a, b = rng.randint(10, 80), rng.randint(2, 40); c = rng.randint(1, a + b - 1)
        t = f"{n1} had {a} {th}. She bought {b} more and then gave {c} to {n2}. How many {th} does {n1} have now?"; e = ["{n0}+{n1}", "@n1-{n2}"]
    elif k == 1:
        a, b = rng.randint(2, 20), rng.randint(2, 30); c = rng.randint(1, a * b - 1)
        t = f"There are {a} {gp} with {b} {th} in each. {n1} takes {c} {th} out. How many {th} are left in the {gp}?"; e = ["{n0}*{n1}", "@n1-{n2}"]
    elif k == 2:
        a, b, c = rng.randint(5, 30), rng.randint(2, 12), rng.randint(1, 100)
        t = f"{n1} earns {a} dollars an hour. He worked {b} hours today and then spent {c} dollars on dinner. How much money does he have left from today's pay?"; e = ["{n0}*{n1}", "@n1-{n2}"]
        if a * b <= c:
            return None
    elif k == 3:
        b = rng.randint(2, 10); a = b * rng.randint(2, 12); c = rng.randint(2, 9)
        t = f"{a} {pp} are split into teams of {b}. Each team needs {c} {th}. How many {th} are needed in all?"; e = ["{n0}/{n1}", "@n1*{n2}"]
    elif k == 4:
        a, b, c = rng.randint(10, 60), rng.randint(1, 9), rng.randint(2, 15)
        if b >= a:
            return None
        t = f"A {it} normally costs {a} dollars. Today there is a discount of {b} dollars on each {it}. How much does {n1} pay for {c} {it}s?"; e = ["{n0}-{n1}", "@n1*{n2}"]
    elif k == 5:
        a, b, c = rng.randint(30, 90), rng.randint(2, 6), rng.randint(5, 80)
        t = f"{n1} drives at {a} kilometers per hour for {b} hours and then drives {c} more kilometers. How many kilometers does {n1} drive in total?"; e = ["{n0}*{n1}", "@n1+{n2}"]
    elif k == 6:
        a, b, c = rng.randint(2, 20), rng.randint(2, 20), rng.randint(2, 20)
        t = f"{n1} has {a} {th}, {n2} has {b} {th}, and their friend has {c} {th}. How many {th} do the three of them have altogether?"; e = ["{n0}+{n1}", "@n1+{n2}"]
    elif k == 7:
        a, b = rng.randint(3, 15), rng.randint(3, 15); c = rng.randint(2, 12)
        t = f"A baker makes {a} trays of muffins in the morning and {b} trays in the afternoon. Each tray holds {c} muffins. How many muffins does the baker make that day?"; e = ["{n0}+{n1}", "@n1*{n2}"]
    elif k == 8:
        a, b, c = rng.randint(50, 500), rng.randint(5, 40), rng.randint(2, 9)
        if a <= b * c:
            return None
        t = f"{n1} had {a} dollars. She bought {c} {it}s at {b} dollars each. How much money does she have left?"; e = ["{n1}*{n2}", "{n0}-@n1"]
    elif k == 9:
        b = rng.randint(2, 8); a = b * rng.randint(4, 25); c = rng.randint(1, a // b - 1)
        t = f"{n1} has {a} {th} and packs them equally into {b} {gp}. Then {n2} takes {c} {th} from one of the {gp}. How many {th} are left in that one?"; e = ["{n0}/{n1}", "@n1-{n2}"]
    elif k == 10:
        a, b, c = rng.randint(2, 12), rng.randint(2, 12), rng.randint(2, 12)
        t = f"A garden has {a} rows of tulips with {b} tulips in each row, and {c} extra tulips by the gate. How many tulips are in the garden?"; e = ["{n0}*{n1}", "@n1+{n2}"]
    elif k == 11:
        a, b = rng.randint(20, 100), rng.randint(2, 19); c = rng.randint(2, 6)
        t = f"{n1} scored {a} points in the first game and {b} fewer points in the second game. How many points did {n1} score in the two games?"; e = ["{n0}-{n1}", "{n0}+@n1"]
    elif k == 12:
        a, b, c = rng.randint(2, 10), rng.randint(2, 10), rng.randint(2, 10)
        t = f"Each of {a} {pp} brings {b} {th} and {n1} brings {c} {th} more than one of them. How many {th} do they have altogether?"; e = ["{n0}*{n1}", "{n1}+{n2}", "@n1+@n2"]
    elif k == 13:
        a, b, c = rng.randint(3, 12), rng.randint(3, 12), rng.randint(1, 8)
        t = f"{n1} buys {a} packs of {th} with {b} {th} in each pack. She uses {c} {th} for a project and shares the rest equally between herself and {n2}. How many {th} does {n2} get?"; e = ["{n0}*{n1}", "@n1-{n2}", "@n2/2"]
        if (a * b - c) % 2:
            return None
    elif k == 14:
        a, b, c = rng.randint(10, 40), rng.randint(2, 9), rng.randint(2, 9)
        t = f"A train has {a} cars. Each car has {b} rows of seats with {c} seats in a row. How many seats does the train have?"; e = ["{n1}*{n2}", "{n0}*@n1"]
    else:
        a, b, c = rng.randint(100, 400), rng.randint(20, 90), rng.randint(20, 90)
        if a <= b + c:
            return None
        t = f"A shop had {a} {th}. It sold {b} in the morning and {c} in the afternoon. How many {th} are left?"; e = ["{n1}+{n2}", "{n0}-@n1"]
    return t, e


# ---------------------------------------------------------------- T4 authoring requests (plan + values + brief)


def gen_t4_request(rng):
    """4-6 step arithmetic plan with values and an authoring brief; text authored later."""
    depth = rng.choice([4, 4, 5, 5, 6])
    ops = []
    vals = {}
    exprs = []
    vals["n0"] = rng.randint(12, 240)
    prev = "{n0}"
    cur = vals["n0"]
    for i in range(1, depth + 1):
        op = rng.choice(["+", "-", "*", "/", "+", "*"])
        if op == "/":
            d = rng.choice([2, 3, 4, 5, 6])
            if cur % d:
                op = "-"
        if op == "+":
            v = rng.randint(3, 80); cur += v
        elif op == "-":
            v = rng.randint(1, max(1, int(cur) - 1)) if cur > 2 else 1; cur -= v
        elif op == "*":
            v = rng.randint(2, 9); cur *= v
        else:
            v = d; cur //= d
        vals["n%d" % i] = v
        exprs.append("%s%s{n%d}" % (prev, op, i)); prev = "@n%d" % i
        ops.append(op)
        if cur > 5_000_000 or cur <= 0:
            return None
    brief = {
        "steps": [{"op": o, "value": vals["n%d" % (i + 1)]} for i, o in enumerate(ops)],
        "start": vals["n0"],
        "answer": cur,
        "features": rng.sample(["one distractor sentence with a number that is NOT used",
                                "at least one quantity written as a word (e.g. 'a dozen', 'twice', 'half')",
                                "two named people whose amounts are compared",
                                "a unit change stated in words (minutes to hours, cents to dollars)",
                                "the question asked about an intermediate quantity's final state",
                                "a time-ordered story (morning, then afternoon, then evening)"], k=rng.choice([1, 2, 2, 3])),
    }
    return {"exprs": exprs, "values": vals, "gold": cur, "brief": brief}


# ---------------------------------------------------------------- P tiers


def gen_p1(rng):
    caps = [c for c, v in Q16.CAP_T.items() if v[4].startswith("physics")]
    cap = rng.choice(caps)
    text, gold, wit, leaves = Q16.gen_tierA(rng, cap)
    return {"text": text, "gold": gold, "witness": wit, "leaves": leaves, "cap": cap}


def gen_p2(rng):
    it = Q17.gen_item(rng, 3)
    if it is None or it["gold_type"] != "num":
        return None
    if not any(lf.startswith("physics") for lf in it["leaves"]):
        return None
    return it


def gen_p3(rng):
    it = Q17.gen_item(rng, rng.choice([5, 6, 6]))
    if it is None or it["gold_type"] != "num":
        return None
    phys = sum(1 for lf in it["leaves"] if lf.startswith("physics"))
    doms = {lf.split("/")[0] for lf in it["leaves"]}
    # the V1.7 generator never places two physics steps in one chain (unit state);
    # P3 = >=1 physics step, >=2 domains, non-monotonic step order, k 5-6
    if phys < 1 or len(doms) < 2 or not it["nonmono"]:
        return None
    return it


def gen_p4_request(rng):
    it = gen_p3(rng)
    if it is None:
        return None
    return {"plan": it["plan"], "gold": it["gold"], "leaves": it["leaves"],
            "generator_text": it["text"], "k": it["k"],
            "brief": {"features": rng.sample([
                "a real-world scenario (vehicle, machine, circuit, lab bench)",
                "one distractor quantity with a unit that is NOT used",
                "at least one value given in a different unit than the formula needs (km/h, minutes, grams)",
                "no formula named in the text; the reader must infer which physical law applies at each step",
                "the steps told out of order (the last quantity mentioned first)"], k=rng.choice([2, 3]))}}


# ---------------------------------------------------------------- corpora


def corpus_items():
    out = []
    for i, line in enumerate((HERE / "corpora" / "gsm8k_train.jsonl").read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        d = json.loads(line)
        out.append({"id": "w10_T3_%06d" % i, "tier": "T3", "corpus": "gsm8k_train",
                    "text": d["question"].strip(),
                    "gold": d["answer"].split("####")[-1].strip().replace(",", ""),
                    "gold_type": "num"})
    for i, d in enumerate(json.loads((HERE / "corpora" / "svamp.json").read_text(encoding="utf-8"))):
        out.append({"id": "w10_T3p_%06d" % i, "tier": "T3p", "corpus": "svamp",
                    "text": ("%s %s" % (d["Body"].strip().rstrip(".") + ".", d["Question"].strip())).strip(),
                    "gold": fmt(float(d["Answer"])), "gold_type": "num", "svamp_type": d.get("Type")})
    z = zipfile.ZipFile(HERE / "corpora" / "sciq.zip")
    sq = json.loads(z.read("SciQ dataset-2 3/test.json"))
    for i, d in enumerate(sq):
        rng = random.Random(h("sciq:%d" % i))
        opts = [d["correct_answer"], d["distractor1"], d["distractor2"], d["distractor3"]]
        rng.shuffle(opts)
        letters = "ABCD"
        text = d["question"].strip() + " " + " ".join("(%s) %s" % (letters[j], o) for j, o in enumerate(opts))
        out.append({"id": "w10_PC_%06d" % i, "tier": "PC", "corpus": "sciq",
                    "text": text, "gold": letters[opts.index(d["correct_answer"])],
                    "gold_type": "mc"})
    return out


def gen_distractor(rng):
    """narrative with numbers but NO computable ask -> must escalate."""
    t, _ = gen_t1(rng) if rng.random() < 0.5 else (gen_t2(rng) or gen_t1(rng))
    body = t.rsplit(".", 1)[0] if "." in t else t
    # replace the ask
    q = rng.choice(["Why do you think that happened?", "What is the name of the person mentioned first?",
                    "Is this story set indoors or outdoors?", "Write one sentence about what happens next.",
                    "Which item is mentioned in the story?"])
    return body + ". " + q


# ---------------------------------------------------------------- main


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    BRIDGE.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    items = []
    led = Counter()

    def add(tier, rec):
        rec["id"] = "w10_%s_%06d" % (tier, led["n_" + tier])
        rec["tier"] = tier
        led["n_" + tier] += 1
        items.append(rec)

    # T1 / T2 (two-evaluator gold)
    for tier, gen in (("T1", gen_t1), ("T2", gen_t2)):
        tries = 0
        while led["n_" + tier] < QUOTA[tier] and tries < QUOTA[tier] * 4:
            tries += 1
            r = gen(rng)
            if r is None:
                led["rej_" + tier] += 1
                continue
            text, exprs = r
            gold, vals = two_evaluator_gold(text, exprs)
            if gold is None:
                led["rej_" + tier + "_" + str(vals)] += 1
                continue
            add(tier, {"text": text, "gold": fmt(gold), "gold_type": "num",
                       "plan": slots_plan(exprs), "numbers": vals})
    # T4 requests
    while led["n_T4"] < QUOTA["T4"]:
        r = gen_t4_request(rng)
        if r is None:
            led["rej_T4"] += 1
            continue
        add("T4", {"text": None, "gold": fmt(r["gold"]), "gold_type": "num",
                   "plan": slots_plan(r["exprs"]), "numbers": r["values"], "brief": r["brief"],
                   "authored": True})
    # P1
    while led["n_P1"] < QUOTA["P1"]:
        it = gen_p1(rng)
        add("P1", {"text": it["text"], "gold": repr(float(it["gold"])),  # B37: never round a float gold
                   "gold_type": "num", "witness": it["witness"], "leaves": it["leaves"], "cap": it["cap"]})
    # P2 / P3
    for tier, gen in (("P2", gen_p2), ("P3", gen_p3)):
        tries = 0
        while led["n_" + tier] < QUOTA[tier] and tries < QUOTA[tier] * 60:
            tries += 1
            it = gen(rng)
            if it is None:
                led["rej_" + tier] += 1
                continue
            add(tier, {"text": it["text"], "gold": repr(float(it["gold"])), "gold_type": "num",
                       "plan": it["plan"], "leaves": it["leaves"], "k": it["k"],
                       "nonmono": it["nonmono"], "multidomain": it["multidomain"], "sig": it["sig"]})
    # P4 requests
    tries = 0
    while led["n_P4"] < QUOTA["P4"] and tries < QUOTA["P4"] * 80:
        tries += 1
        r = gen_p4_request(rng)
        if r is None:
            led["rej_P4"] += 1
            continue
        add("P4", {"text": None, "gold": repr(float(r["gold"])), "gold_type": "num", "plan": r["plan"],
                   "leaves": r["leaves"], "k": r["k"], "generator_text": r["generator_text"],
                   "brief": r["brief"], "authored": True})
    # corpora
    for rec in corpus_items():
        items.append(rec)
        led["n_" + rec["tier"]] += 1
    # distractors 2%
    n_d = int(0.02 * len(items))
    for _ in range(n_d):
        add("D", {"text": gen_distractor(rng), "gold": None, "gold_type": "none", "distractor": True})

    # splits, authors, reader fields
    for it in items:
        it["split"] = split_of(it["id"])
        if it.get("authored"):
            it["author_model"] = author_of(it["id"])
        if it.get("text"):
            it["numbers"] = {"n%d" % i: n[1] for i, n in enumerate(V.numbers_of19(it["text"]))}
            it["key"] = V.cue_key(it["text"])
    items.sort(key=lambda x: x["id"])
    by_split = Counter()
    for sp in ("acq", "dev", "seal", "replay"):
        p = DATA / ("w400k_%s.jsonl" % sp)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            for it in items:
                if it["split"] == sp:
                    f.write(json.dumps(it) + "\n")
                    by_split[sp] += 1
    # authoring batches (25 per file; text None; golds NOT included)
    for tier in ("T4", "P4"):
        reqs = [it for it in items if it["tier"] == tier]
        for bi in range(0, len(reqs), 25):
            b = reqs[bi:bi + 25]
            payload = []
            for it in b:
                if tier == "T4":
                    payload.append({"id": it["id"], "start": it["brief"]["start"],
                                    "steps": it["brief"]["steps"], "features": it["brief"]["features"]})
                else:
                    payload.append({"id": it["id"], "plan": it["plan"], "features": it["brief"]["features"],
                                    "kind_hint": it["leaves"]})
            (BRIDGE / ("author_%s_%s_%03d.json" % (tier, b[0]["author_model"], bi // 25))).write_text(
                json.dumps(payload, indent=0), encoding="utf-8")
    hashes = {("w400k_%s.jsonl" % sp): hashlib.sha256((DATA / ("w400k_%s.jsonl" % sp)).read_bytes()).hexdigest()
              for sp in ("acq", "dev", "seal", "replay")}
    for c in ("gsm8k_train.jsonl", "svamp.json", "sciq.zip"):
        hashes["corpora/" + c] = hashlib.sha256((HERE / "corpora" / c).read_bytes()).hexdigest()
    (DATA / "HASHES.json").write_text(json.dumps(hashes, indent=1), encoding="utf-8")
    man = {"seed": SEED, "n": len(items), "by_tier": {k[2:]: v for k, v in led.items() if k.startswith("n_")},
           "rejects": {k: v for k, v in led.items() if k.startswith("rej_")},
           "by_split": dict(by_split), "distractors": n_d,
           "authored_batches": len(list(BRIDGE.glob("author_*.json")))}
    (DATA / "w400k_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
