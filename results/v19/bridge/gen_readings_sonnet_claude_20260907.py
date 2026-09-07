import json, os

OUTDIR = os.path.join(os.path.dirname(__file__), "readings_sonnet_sealed")
os.makedirs(OUTDIR, exist_ok=True)

def P(*steps, final=None):
    """steps: list of expr strings; nodes auto-named n1..nk; final defaults to last node."""
    nodes = [{"id": f"n{i+1}", "op": "evaluate", "expr": e} for i, e in enumerate(steps)]
    fid = final if final else nodes[-1]["id"]
    return {"nodes": nodes, "final": fid}

PLANS = {}

# ---- batch_sealed_42 ----
PLANS["g0996"] = P("{n0}/4", "@n1*2", "{n0}-{n1}-{n2}-@n2")
PLANS["g0999"] = P("{n1}*2+{n2}*1", "2/@n1*100")
PLANS["g1001"] = None
PLANS["g1004"] = P("{n2}/{n0}", "{n3}/{n1}", "@n1-@n2")
PLANS["g1005"] = P("{n0}*({n1}/{n2})", "@n1*{n3}", "@n2*12", "{n0}+@n3")
PLANS["g1013"] = P("{n0}+{n1}", "{n3}*({n2}/100)", "@n1*{n4}", "@n2/@n3")
PLANS["g1020"] = P("{n0}*3", "{n0}+{n1}+@n1")
PLANS["g1023"] = P("{n0}+{n1}+{n2}", "@n1*7")
PLANS["g1027"] = P("{n4}/{n3}", "@n1*{n5}")
PLANS["g1030"] = P("1-({n0}/100)", "1-({n1}/100)", "1-({n2}/100)", "@n1*@n2*@n3*100")
PLANS["g1031"] = P("{n0}-{n1}-{n2}", "@n1/{n1}")
PLANS["g1032"] = P("{n0}*2", "@n1*({n1}/{n2})")
PLANS["g1033"] = P("{n0}*{n1}", "{n2}*{n1}", "{n3}*{n1}", "@n2-@n3", "@n4/@n1")
PLANS["g1034"] = P("{n1}*{n2}", "{n3}*{n4}", "@n1+@n2")
PLANS["g1037"] = P("{n0}*{n2}", "{n1}*{n3}", "@n1+@n2", "{n4}-@n3")
PLANS["g1042"] = P("2*{n0}+{n1}", "{n2}*@n1", "{n0}-@n1+@n2", "@n3/3")
PLANS["g1044"] = P("{n0}*12+{n1}", "{n2}+{n3}", "@n2-@n1")
PLANS["g1047"] = P("{n0}-4", "1+1+0.5", "@n1/@n2", "@n3+4")
PLANS["g1048"] = P("{n3}-{n1}", "1-({n2}/100)", "@n2**@n1", "{n0}*@n3")
PLANS["g1050"] = P("{n1}*{n2}", "{n0}-@n1")
PLANS["g1052"] = P("{n0}+{n1}", "@n1-{n2}", "@n2+2*{n2}", "@n3-{n3}")
PLANS["g1056"] = None
PLANS["g1057"] = P("{n0}+{n0}*0.5", "@n1*{n1}")
PLANS["g1058"] = P("{n1}*2", "{n0}+{n1}+@n1")
PLANS["g1064"] = P("{n0}*2", "{n0}*3", "{n0}+@n1+@n2+{n1}+{n2}")

# ---- batch_sealed_43 ----
PLANS["g1065"] = P("{n0}*{n1}", "@n1+{n2}", "@n2/{n3}")
PLANS["g1066"] = P("{n0}*(1-{n1}/100)", "{n0}*2", "@n2*(1-{n2}/100)", "@n1+@n3")
PLANS["g1067"] = P("{n0}*{n1}", "{n0}*2", "@n2*{n2}", "@n1+@n3", "@n4/100")
PLANS["g1071"] = P("{n3}+{n4}+{n5}-{n6}", "@n1-{n1}", "{n0}+@n2*{n2}")
PLANS["g1073"] = P("{n0}/7", "{n1}+{n2}", "@n1-{n1}-@n2")
PLANS["g1076"] = None
PLANS["g1081"] = P("2*{n1}+{n0}")
PLANS["g1084"] = P("{n0}-{n1}", "@n1/2")
PLANS["g1085"] = P("{n0}/{n1}", "@n1*{n2}")
PLANS["g1087"] = P("{n0}-{n1}", "@n1*{n2}")
PLANS["g1089"] = P("3*{n1}", "{n0}/3", "@n1*@n2", "@n3*@n2")
PLANS["g1096"] = None
PLANS["g1099"] = P("{n0}/{n1}", "{n2}/{n3}", "@n1-@n2")
PLANS["g1102"] = P("{n0}-{n1}", "{n3}*(1-{n2}/100)", "{n5}*(1-{n4}/100)", "@n1+@n2+@n3")
PLANS["g1106"] = P("{n0}/{n1}", "@n1/{n2}")
PLANS["g1107"] = P("{n1}/({n0}/100)", "@n1-{n1}")
PLANS["g1108"] = P("{n0}+{n1}-{n2}")
PLANS["g1110"] = None
PLANS["g1111"] = P("{n0}*{n3}", "{n1}*{n4}", "{n2}*{n5}", "@n1+@n2+@n3")
PLANS["g1113"] = P("{n0}-{n1}+{n2}")
PLANS["g1115"] = P("{n0}-{n1}", "@n1-{n3}", "@n2/{n2}")
PLANS["g1116"] = P("{n0}*(1+{n1}/100)")
PLANS["g1119"] = None
PLANS["g1121"] = P("{n1}*{n0}", "@n1/2")
PLANS["g1122"] = P("{n2}*{n3}*{n6}", "{n4}*{n5}*{n6}", "{n0}-{n7}", "@n3-@n1-@n2", "@n4/{n6}")

# ---- batch_sealed_44 ----
PLANS["g1124"] = P("{n0}+{n1}", "@n1*4")
PLANS["g1125"] = P("{n0}*{n1}*{n2}", "@n1/{n3}")
PLANS["g1130"] = P("{n0}/{n1}", "{n0}*{n3}", "@n1*{n2}", "@n2+@n3", "@n4/{n4}")
PLANS["g1131"] = P("{n0}*({n1}/100)", "@n1/{n2}", "@n2*{n3}", "@n3*{n4}")
PLANS["g1132"] = P("{n1}/{n2}", "{n0}/@n1", "{n0}+@n2", "@n3*3")
PLANS["g1133"] = P("{n1}/{n3}", "@n1*2", "{n2}/@n2", "{n3}+@n3")
PLANS["g1135"] = P("{n0}*{n1}", "{n2}*{n3}", "{n4}*{n5}", "@n1+@n2+@n3")
PLANS["g1136"] = P("{n0}*12", "{n1}-@n1", "@n2-{n2}")
PLANS["g1138"] = P("3*7", "{n0}+{n2}*@n1", "{n1}+{n3}*@n1", "@n2+@n3")
PLANS["g1141"] = P("{n0}*{n1}", "{n2}*{n3}", "@n1+@n2", "@n3/12")
PLANS["g1143"] = None
PLANS["g1145"] = P("{n2}/{n0}", "{n3}/{n1}", "@n2*{n4}", "@n1+@n3", "@n4*{n5}")
PLANS["g1146"] = P("{n0}/{n1}", "@n1*({n3}/100)", "@n2*{n2}", "{n0}-@n3")
PLANS["g1149"] = None
PLANS["g1150"] = P("{n0}-{n1}+{n2}")
PLANS["g1151"] = P("{n0}+{n2}", "{n1}+{n3}", "@n1/@n2")
PLANS["g1155"] = P("{n1}*(1+{n2}/100)", "{n1}+@n1")
PLANS["g1156"] = P("{n0}*2-{n0}", "{n1}+{n2}", "@n1*@n2")
PLANS["g1162"] = P("{n1}/2-{n0}")
PLANS["g1163"] = P("{n0}*3*2")
PLANS["g1164"] = P("{n0}*12", "{n1}*2", "@n2-{n2}", "@n3*0.5", "{n1}+@n2+@n3+@n4", "@n1-@n5")
PLANS["g1165"] = None
PLANS["g1169"] = P("{n0}*3", "{n1}/{n2}", "@n1*(1-@n2)", "{n0}-@n3")
PLANS["g1173"] = P("{n0}*(1+{n2}/100)", "(@n1/{n1})*{n3}/{n4}")
PLANS["g1177"] = P("{n0}-{n0}/4", "{n1}-{n1}/3", "@n1+@n2")

# ---- batch_sealed_45 ----
PLANS["g1179"] = P("{n1}+{n2}", "{n1}+@n1", "@n2/{n0}*100")
PLANS["g1184"] = P("{n0}/{n1}", "@n1*{n2}")
PLANS["g1187"] = P("{n0}/60", "{n1}/{n2}", "@n1-@n2", "{n3}/@n3")
PLANS["g1191"] = P("{n2}-{n3}", "{n0}+{n1}*@n1")
PLANS["g1192"] = P("{n0}*{n1}*{n2}", "@n1*{n4}", "@n2+{n3}")
PLANS["g1193"] = P("{n0}*1+{n1}*1+{n2}*2+{n3}*{n4}")
PLANS["g1195"] = P("{n3}*2", "{n0}*{n6}", "{n0}+{n3}+@n1+@n2")
PLANS["g1197"] = P("{n1}/{n0}", "@n1*(1+{n2}/100)", "{n0}*2", "@n3*@n2", "{n1}+@n4")
PLANS["g1198"] = None
PLANS["g1200"] = None
PLANS["g1201"] = P("{n0}*(1/3)", "{n0}-@n1", "@n2*({n1}/{n2})", "@n1+@n3")
PLANS["g1204"] = P("{n0}*(1-{n1}/100)", "@n1*(1-{n2}/100)")
PLANS["g1205"] = P("{n4}*{n0}", "{n1}+{n2}+{n3}", "@n1-@n2")
PLANS["g1207"] = P("{n1}+{n2}+{n3}", "@n1*{n4}")
PLANS["g1208"] = P("{n0}/{n1}-1", "{n2}*@n1")
PLANS["g1209"] = P("{n0}*2", "@n1*2", "{n0}*{n1}+@n1*{n2}+@n2*{n3}")
PLANS["g1210"] = P("{n0}*{n1}", "@n1-{n2}")
PLANS["g1213"] = P("{n0}*(1+{n1}/100)", "{n2}*{n3}", "@n1-@n2")
PLANS["g1214"] = P("{n0}*{n1}", "@n1*0.5")
PLANS["g1215"] = None
PLANS["g1218"] = P("{n1}-{n0}+1", "@n1*{n2}", "@n2/{n3}", "@n3*{n4}")
PLANS["g1219"] = P("{n0}*{n1}", "{n2}*{n3}", "@n1+@n2")
PLANS["g1221"] = None
PLANS["g1223"] = P("{n1}*{n0}", "{n3}-{n1}", "@n2*{n2}", "@n1+@n3")
PLANS["g1225"] = P("5*2", "(@n1+{n0})/4")

# ---- batch_sealed_46 ----
PLANS["g1228"] = P("{n2}+{n0}", "@n1-{n1}")
PLANS["g1229"] = P("{n0}*(1+{n1}/100)", "@n1*(1-{n2}/100)")
PLANS["g1231"] = P("{n0}+{n1}+{n2}+{n3}+{n4}+{n5}+{n6}+{n7}+{n8}", "4+5", "@n1/@n2")
PLANS["g1232"] = P("{n0}*(1-{n1}/{n2})")
PLANS["g1233"] = P("{n0}*(1-{n1}/{n2})", "@n1*(1-{n3}/100)", "@n2*{n4}")
PLANS["g1234"] = P("{n1}/4", "{n0}/@n1")
PLANS["g1236"] = P("{n0}*{n1}", "{n2}*{n3}", "{n0}+@n1+@n2")
PLANS["g1240"] = P("{n0}*{n1}", "{n1}*2", "@n2-{n2}", "@n1+@n2+@n3", "{n3}/@n4")
PLANS["g1242"] = P("{n0}*0.5", "{n0}-@n1", "@n2*({n1}/{n2})", "@n2-@n3")
PLANS["g1245"] = P("{n2}+{n1}", "@n1/6", "{n0}*@n2-{n1}")
PLANS["g1247"] = P("{n0}*0.5", "@n1-{n1}", "{n0}-@n2", "@n3-1")
PLANS["g1248"] = P("{n0}*2*{n1}")
PLANS["g1249"] = P("{n1}+2*{n0}", "({n0}/2)*{n2}", "({n0}/2)*{n3}", "@n1+@n2+@n3")
PLANS["g1250"] = P("2*{n0}", "@n1/5")
PLANS["g1252"] = P("{n0}*0.5", "{n0}*2", "{n0}+@n1+@n2")
PLANS["g1254"] = P("{n1}-{n0}", "@n1*{n2}")
PLANS["g1255"] = P("{n0}-{n1}-{n2}", "{n1}*0.5", "{n2}*{n3}", "@n1*(0.5*0.5)", "@n2+@n3+@n4")
PLANS["g1258"] = P("{n0}/2", "{n0}+4*@n1")
PLANS["g1259"] = None
PLANS["g1261"] = P("{n0}*{n3}+{n1}*{n5}+{n2}*{n4}", "@n1*{n6}")
PLANS["g1263"] = P("{n0}+{n1}", "@n1*2", "7-3", "@n3*{n2}", "{n0}+@n1+@n2+@n4")
PLANS["g1266"] = P("{n0}*{n2}+{n1}*{n3}", "@n1*7")
PLANS["g1267"] = P("{n0}*{n1}+{n2}*{n3}", "@n1/2")
PLANS["g1269"] = None
PLANS["g1271"] = P("{n1}*2", "{n1}*0.5", "{n0}-{n1}-@n1-@n2")

# ---- batch_sealed_47 ----
PLANS["g1272"] = P("{n2}*({n3}/100)", "{n0}*{n2}+{n1}*@n1")
PLANS["g1273"] = P("{n1}+{n2}", "{n0}-@n1")
PLANS["g1275"] = P("{n0}+{n1}+{n2}*2", "@n1*({n3}/100)")
PLANS["g1276"] = P("({n0}+{n1})*2")
PLANS["g1277"] = P("{n1}+({n1}+{n0})", "@n1/2")
PLANS["g1278"] = P("{n0}+{n1}+{n2}", "@n1-{n3}")
PLANS["g1281"] = P("5*{n0}*2", "@n1*7", "{n1}-@n2")
PLANS["g1284"] = P("{n0}*2", "@n1*(1+{n1})", "@n2-{n2}")
PLANS["g1285"] = P("{n0}-{n1}-{n2}-{n3}")
PLANS["g1288"] = P("{n0}*2*7", "{n1}*({n2}*60)", "@n1+@n2", "@n3*{n3}")
PLANS["g1294"] = P("{n2}+{n2}*(1-{n0}/100)", "{n4}*(1-{n3}/100)", "@n1+@n2")
PLANS["g1295"] = P("{n0}*{n1}", "(1+{n2})*{n3}", "@n1-@n2", "@n3/{n4}")
PLANS["g1296"] = P("{n0}+{n1}+{n2}+2*{n3}")
PLANS["g1297"] = P("{n1}*{n4}+{n2}*{n5}+{n3}*{n6}", "{n7}-@n1", "@n2*{n8}")
PLANS["g1298"] = None
PLANS["g1300"] = P("7-2", "@n1*{n0}", "@n2*{n1}", "@n3*{n2}")
PLANS["g1306"] = P("{n0}*0.5", "{n2}+2", "{n3}-@n1-@n2", "{n1}-@n3")
PLANS["g1307"] = P("{n0}*{n1}*{n2}", "{n3}-@n1")
PLANS["g1310"] = P("({n0}/2)/{n1}", "@n1/2", "{n0}/@n2")
PLANS["g1311"] = P("{n1}*{n0}", "@n1-{n2}")
PLANS["g1312"] = P("{n1}*{n2}+{n3}", "{n0}*@n1", "@n2*{n4}")
PLANS["g1313"] = P("{n1}*(1+{n2}/100)", "@n1/{n0}")
PLANS["g1314"] = P("{n1}-{n2}", "@n1*2", "{n0}+@n2", "@n3-{n3}", "@n4+{n4}")
PLANS["g1315"] = P("60/{n0}", "60/{n1}", "@n1-@n2")
PLANS["g1316"] = P("{n0}*(1-{n1}/100)", "{n2}*{n3}", "@n1+@n2")

# ---- write files, verify against source batches ----
BATCH_FILES = [f"batch_sealed_{i}.json" for i in (42,43,44,45,46,47)]
BRIDGE_DIR = os.path.dirname(__file__)

all_ids = []
for fn in BATCH_FILES:
    with open(os.path.join(BRIDGE_DIR, fn), encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
        all_ids.append(it["id"])

missing = [i for i in all_ids if i not in PLANS]
extra = [i for i in PLANS if i not in all_ids]
if missing:
    raise SystemExit(f"MISSING plans for: {missing}")
if extra:
    raise SystemExit(f"EXTRA plans not in any batch: {extra}")

n_written = 0
n_null = 0
for id_ in all_ids:
    plan = PLANS[id_]
    obj = {"plan": plan}
    path = os.path.join(OUTDIR, f"reading_{id_}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    n_written += 1
    if plan is None:
        n_null += 1

print(f"WROTE {n_written} files, {n_null} null, {n_written-n_null} plans, total ids {len(all_ids)}")
