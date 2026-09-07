import json, os

OUT_DIR = os.path.join(os.path.dirname(__file__), "readings_sonnet_sealed")
os.makedirs(OUT_DIR, exist_ok=True)

def P(*steps, final=None):
    """steps: list of expr strings, node ids assigned n1..nk in order. final defaults to last."""
    nodes = [{"id": f"n{i+1}", "op": "evaluate", "expr": e} for i, e in enumerate(steps)]
    fin = final if final else nodes[-1]["id"]
    return {"nodes": nodes, "final": fin}

PLANS = {}

# ---------------- batch_sealed_06 ----------------
PLANS["a0581"] = P("{n0}*{n1}")
PLANS["a0582"] = P("{n0}*{n1}")
PLANS["a0583"] = None  # ceiling division, not expressible
PLANS["a0584"] = None  # ceiling division, not expressible
PLANS["a0585"] = P("{n0}-{n1}")
PLANS["a0586"] = P("{n1}-{n0}")
PLANS["a0588"] = P("{n0}*{n1}")
PLANS["a0593"] = None  # division "how many can each get" -> floor, not expressible
PLANS["a0596"] = P("{n0}-{n1}")
PLANS["a0605"] = P("{n0}-{n1}", "@n1-{n2}")
PLANS["a0607"] = P("{n0}*5")
PLANS["a0614"] = P("{n0}*{n1}")
PLANS["a0615"] = P("{n0}/60")
PLANS["a0616"] = P("{n0}+{n1}", "@n1*{n2}")
PLANS["a0619"] = P("{n0}-{n1}")
PLANS["a0621"] = P("{n0}*{n1}")
PLANS["a0622"] = None  # "eleven" not a slot/allowed constant
PLANS["a0625"] = P("{n0}+{n1}")
PLANS["a0634"] = P("{n0}/2")
PLANS["a0636"] = None  # nickel value 0.05 not a slot/allowed constant
PLANS["a0643"] = P("{n0}+{n1}", "{n0}+@n1")
PLANS["a0650"] = P("{n0}-{n1}", "{n2}*@n1", "{n0}+@n1+@n2")
PLANS["a0654"] = P("{n0}+{n1}", "{n2}+{n3}+{n4}", "@n2-@n1")
PLANS["a0656"] = P("{n0}+{n1}+{n2}", "@n1-{n3}")
PLANS["a0657"] = P("{n0}+{n1}+{n2}", "{n3}+{n4}", "@n1-@n2")

# ---------------- batch_sealed_07 ----------------
PLANS["a0658"] = P("{n0}+{n1}+{n2}", "@n1-{n3}")
PLANS["a0659"] = P("{n1}*{n0}", "@n1-{n2}", "{n0}+@n1+@n2")
PLANS["a0660"] = P("{n1}+{n2}", "{n0}-@n1")
PLANS["a0661"] = P("{n0}+{n1}+{n2}", "@n1-{n3}")
PLANS["a0662"] = P("{n0}+{n1}", "@n1*{n3}", "{n2}*{n4}", "@n2+@n3")
PLANS["a0666"] = P("{n0}*{n2}", "{n1}*{n3}", "@n1+@n2")
PLANS["a0667"] = P("{n0}-{n1}", "@n1+{n2}", "{n0}+@n1+@n2")
PLANS["a0671"] = None  # remainder, needs modulo
PLANS["a0697"] = P("{n2}-{n1}+{n0}")
PLANS["a0700"] = P("{n0}+{n1}", "@n1-{n2}", "@n2+{n3}")
PLANS["a0704"] = P("{n0}-{n1}-{n2}")
PLANS["a0710"] = P("{n0}+{n1}+{n2}", "@n1-{n3}")
PLANS["a0711"] = P("{n0}-{n1}-{n2}")
PLANS["a0719"] = P("{n0}-{n1}-{n2}")
PLANS["a0729"] = P("{n0}+{n1}")
PLANS["a0730"] = P("{n0}+{n1}")
PLANS["a0731"] = P("{n0}+{n1}")
PLANS["a0733"] = P("{n0}+{n1}")
PLANS["a0734"] = P("{n0}+{n1}")
PLANS["a0736"] = P("{n0}+{n1}")
PLANS["a0741"] = P("{n0}-{n1}", "@n1-{n1}")
PLANS["a0750"] = P("{n2}+{n0}+{n1}")
PLANS["a0755"] = None  # ceiling division, not expressible
PLANS["a0762"] = None  # remainder, needs modulo
PLANS["a0764"] = None  # remainder, needs modulo

# ---------------- batch_sealed_08 ----------------
PLANS["a0768"] = None  # remainder, needs modulo
PLANS["a0769"] = None  # ceiling division
PLANS["a0771"] = None  # ceiling division
PLANS["a0781"] = None  # floor division (non-exact)
PLANS["a0783"] = None  # floor division (non-exact)
PLANS["a0787"] = None  # floor division (non-exact)
PLANS["a0791"] = None  # floor division (non-exact)
PLANS["a0797"] = None  # floor division (non-exact)
PLANS["a0798"] = None  # remainder, needs modulo
PLANS["a0799"] = None  # floor division (non-exact)
PLANS["a0802"] = None  # diophantine, not expressible
PLANS["a0803"] = None  # floor division (non-exact)
PLANS["a0810"] = None  # diophantine, not expressible
PLANS["a0811"] = None  # floor division (non-exact)
PLANS["a0814"] = None  # ceiling-to-multiple, not expressible
PLANS["a0816"] = None  # ceiling-to-multiple, not expressible
PLANS["a0818"] = None  # ceiling-to-multiple, not expressible
PLANS["a0835"] = P("{n1}/{n0}", "({n4}-{n2}*@n1)/{n3}", "@n2-@n1")
PLANS["a0850"] = None  # ratio, not a single numeric answer
PLANS["a0854"] = None  # ratio, not a single numeric answer
PLANS["a0856"] = None  # ratio, not a single numeric answer
PLANS["a0858"] = None  # ratio, not a single numeric answer
PLANS["a0859"] = None  # ratio, not a single numeric answer
PLANS["a0860"] = None  # ratio, not a single numeric answer
PLANS["a0862"] = P("{n0}/{n1}*{n2}")

# ---------------- batch_sealed_09 ----------------
PLANS["a0865"] = P("{n3}-{n2}+{n1}-{n0}")
PLANS["a0871"] = None  # GCD, not expressible
PLANS["a0874"] = P("{n0}*2**4")
PLANS["a0876"] = P("{n2}-{n0}+{n1}")
PLANS["a0879"] = P("{n1}+{n0}", "{n1}-{n0}", "@n1-@n2")
PLANS["a0881"] = None  # digit-reversal, not algebraic
PLANS["a0882"] = P("{n0}+{n1}+{n2}", "{n0}+{n1}-{n3}", "@n1-@n2")
PLANS["a0884"] = P("{n0}+{n2}-{n1}")
PLANS["a0893"] = P("{n1}-{n0}")
PLANS["a0894"] = P("{n0}+{n1}")
PLANS["a0895"] = P("{n0}+{n1}+{n2}", "@n1+{n3}")
PLANS["a0903"] = P("{n1}+{n2}", "{n1}-{n3}", "{n1}+@n1+@n2")
PLANS["a0905"] = None  # worm-in-well ceiling edge case, not expressible
PLANS["a0912"] = P("1+{n0}-{n1}+{n2}", "@n1+{n3}")
PLANS["a0917"] = P("{n0}+{n1}")
PLANS["a0921"] = P("{n2}-{n1}")
PLANS["a0926"] = P("{n2}-{n0}")
PLANS["a0928"] = P("{n0}-{n3}")
PLANS["a0932"] = P("{n0}+{n2}")
PLANS["a0933"] = P("{n0}+{n2}")
PLANS["a0934"] = P("{n0}-{n3}")
PLANS["a0937"] = P("{n1}+{n3}")
PLANS["a0942"] = P("{n0}-{n1}+{n2}")
PLANS["a0947"] = P("{n0}-{n1}-{n2}")
PLANS["a0953"] = P("{n0}+{n1}-{n2}")

# ---------------- batch_sealed_10 ----------------
PLANS["a0954"] = P("{n0}-{n1}")
PLANS["a0956"] = P("{n0}+{n1}")
PLANS["a0958"] = P("{n1}-{n0}")
PLANS["a0959"] = P("{n0}+{n1}")
PLANS["a0961"] = P("{n0}-{n1}")
PLANS["a0963"] = P("{n0}-{n1}")
PLANS["a0964"] = P("{n0}-{n1}")
PLANS["a0965"] = P("{n0}+{n1}")
PLANS["a0967"] = P("{n0}-{n1}")
PLANS["a0968"] = None  # GCD, not expressible
PLANS["a0969"] = None  # LCM, not expressible
PLANS["a0974"] = None  # GCD, not expressible
PLANS["a0975"] = None  # GCD, not expressible
PLANS["a0983"] = P("{n0}-{n1}-{n2}")
PLANS["a0985"] = P("{n0}-{n1}+{n2}")
PLANS["a0987"] = P("{n2}-{n0}-{n1}")
PLANS["a0990"] = P("{n0}-{n1}-{n2}")
PLANS["a0991"] = P("{n0}-{n1}-{n2}")
PLANS["a0997"] = P("{n0}-{n1}-{n2}")
PLANS["a1002"] = P("{n1}-{n2}", "{n1}+@n1", "{n0}-@n2")
PLANS["a1003"] = P("{n0}+{n1}", "@n1-{n2}")
PLANS["a1021"] = P("{n0}-{n1}")
PLANS["a1026"] = P("{n0}-{n1}")
PLANS["a1031"] = P("{n0}-{n1}")
PLANS["a1033"] = P("{n0}-{n1}")

# ---------------- batch_sealed_11 ----------------
PLANS["a1034"] = P("{n0}-{n1}")
PLANS["a1035"] = P("{n0}-{n1}")
PLANS["a1041"] = P("{n0}-{n1}")
PLANS["a1043"] = P("{n0}+{n1}")
PLANS["a1066"] = P("{n1}/{n0}", "{n3}*@n1")
PLANS["a1068"] = P("{n1}-{n0}", "{n4}+@n1")
PLANS["a1070"] = P("{n1}-{n0}", "{n4}+@n1")
PLANS["a1075"] = P("{n1}/{n0}", "{n3}*@n1")
PLANS["a1083"] = P("{n0}-{n1}")
PLANS["a1084"] = None  # ton->pound conversion (2000) not a slot/allowed constant
PLANS["a1085"] = None  # coin-count optimization, not expressible
PLANS["a1087"] = None  # coin values 0.05/0.25 not slots/allowed constants
PLANS["a1089"] = P("{n0}+{n1}")
PLANS["a1092"] = P("({n1}-{n0})/2")
PLANS["a1097"] = P("{n0}+{n1}", "@n1/100")
PLANS["a1099"] = P("{n1}*60+{n2}", "@n1+{n0}", "{n3}*60+{n4}", "@n3-@n2")
PLANS["a1101"] = P("{n1}-{n0}", "{n2}*{n1}/@n1", "@n2/1000")
PLANS["a1111"] = P("{n0}-{n1}", "{n2}/@n1", "({n0}+{n1})*@n2")
PLANS["a1113"] = P("{n2}/{n1}", "{n0}*@n1", "@n2-{n2}")
PLANS["a1115"] = P("{n2}/{n0}", "{n1}*@n1", "{n2}-@n2")
PLANS["a1117"] = P("{n2}/{n0}", "{n1}*@n1", "{n2}-@n2")
PLANS["a1124"] = P("{n0}+{n1}", "{n2}/@n1", "({n1}-{n0})*@n2")
PLANS["a1126"] = P("{n1}+{n2}", "{n0}/@n1", "{n2}*@n2")
PLANS["a1127"] = P("{n0}+{n1}", "{n2}/@n1", "({n1}-{n0})*@n2")
PLANS["a1128"] = P("{n1}-{n0}", "{n2}/@n1", "{n1}*@n2")

# ---------------- validation against input batches ----------------
BATCH_FILES = [
    "batch_sealed_06.json", "batch_sealed_07.json", "batch_sealed_08.json",
    "batch_sealed_09.json", "batch_sealed_10.json", "batch_sealed_11.json",
]
bridge_dir = os.path.dirname(__file__)
all_ids = []
for bf in BATCH_FILES:
    with open(os.path.join(bridge_dir, bf), "r", encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
        all_ids.append(it["id"])

missing = [i for i in all_ids if i not in PLANS]
extra = [i for i in PLANS if i not in all_ids]
if missing:
    raise SystemExit(f"Missing plans for ids: {missing}")
if extra:
    raise SystemExit(f"Extra plans not in any batch: {extra}")
if len(all_ids) != 150:
    raise SystemExit(f"Expected 150 ids total, got {len(all_ids)}")

null_count = 0
written = 0
for _id in all_ids:
    plan = PLANS[_id]
    obj = {"plan": plan}
    out_path = os.path.join(OUT_DIR, f"reading_{_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    written += 1
    if plan is None:
        null_count += 1

print(f"written={written} null={null_count} non_null={written-null_count}")
