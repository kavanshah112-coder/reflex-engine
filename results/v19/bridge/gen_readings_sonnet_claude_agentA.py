import json, os

OUT = os.path.join(os.path.dirname(__file__), "readings_sonnet_sealed")
os.makedirs(OUT, exist_ok=True)

def N(id_, expr):
    return {"id": id_, "op": "evaluate", "expr": expr}

def plan(nodes, final):
    return {"plan": {"nodes": nodes, "final": final}}

NULL = {"plan": None}

PLANS = {}

# ---- batch_sealed_30 ----
PLANS["g0377"] = plan([
    N("n1", "{n2}/{n0}"),
    N("n2", "{n1}*2"),
    N("n3", "@n1+{n1}+@n2"),
], "n3")

PLANS["g0379"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "@n1-{n2}"),
], "n2")

PLANS["g0380"] = plan([
    N("n1", "{n1}/100"),
    N("n2", "{n0}*@n1*(5/12)"),
    N("n3", "{n0}+@n2"),
    N("n4", "@n3/5"),
], "n4")

PLANS["g0382"] = plan([
    N("n1", "{n0}*2"),
    N("n2", "{n1}+{n2}"),
    N("n3", "{n0}+{n1}+@n1+@n2"),
], "n3")

PLANS["g0384"] = plan([
    N("n1", "({n1}-{n0})/{n1}"),
    N("n2", "{n2}/@n1"),
], "n2")

PLANS["g0385"] = plan([
    N("n1", "{n0}*({n2}/100)"),
    N("n2", "@n1/2"),
    N("n3", "@n2+{n3}"),
], "n3")

PLANS["g0386"] = plan([
    N("n1", "{n2}+{n3}+{n4}+{n5}+{n6}"),
    N("n2", "@n1/{n1}"),
], "n2")

PLANS["g0387"] = plan([
    N("n1", "{n0}*{n2}"),
    N("n2", "{n1}*{n3}"),
    N("n3", "@n1+@n2"),
], "n3")

PLANS["g0388"] = plan([
    N("n1", "{n0}*({n1}/{n2})"),
    N("n2", "{n0}+@n1"),
], "n2")

PLANS["g0389"] = plan([
    N("n1", "{n5}*{n1}*{n2}"),
    N("n2", "@n1-{n3}"),
], "n2")

PLANS["g0390"] = plan([
    N("n1", "{n0}+{n1}+{n2}"),
    N("n2", "{n3}/@n1"),
], "n2")

PLANS["g0392"] = plan([
    N("n1", "{n1}*2*(1-{n2}/100)"),
    N("n2", "{n0}+@n1"),
    N("n3", "{n3}-@n2"),
], "n3")

PLANS["g0394"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "@n1*2"),
    N("n3", "@n2+{n0}"),
], "n3")

PLANS["g0395"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n0}+@n1"),
    N("n3", "{n3}+{n4}"),
    N("n4", "@n2-@n3"),
    N("n5", "@n4+{n5}"),
], "n5")

PLANS["g0396"] = plan([
    N("n1", "{n0}*({n1}/{n2})"),
    N("n2", "{n0}*({n3}/{n4})"),
    N("n3", "{n0}-@n1-@n2-{n5}"),
], "n3")

PLANS["g0397"] = plan([
    N("n1", "{n2}-{n0}"),
    N("n2", "@n1/{n1}"),
], "n2")

PLANS["g0399"] = plan([
    N("n1", "{n0}+{n1}"),
], "n1")

PLANS["g0401"] = plan([
    N("n1", "{n0}*{n1}*{n2}"),
    N("n2", "@n1*12"),
], "n2")

PLANS["g0402"] = plan([
    N("n1", "{n0}*4/{n2}"),
    N("n2", "{n1}*4/{n3}"),
    N("n3", "@n1-@n2"),
], "n3")

PLANS["g0403"] = plan([
    N("n1", "{n0}*{n3}*{n4}"),
    N("n2", "@n1/1000"),
], "n2")

PLANS["g0407"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "{n0}-{n2}"),
    N("n3", "@n2-@n1-{n1}"),
], "n3")

PLANS["g0413"] = plan([
    N("n1", "(100-{n0})/100"),
    N("n2", "{n1}/100"),
    N("n3", "{n2}*@n1*@n2"),
], "n3")

PLANS["g0414"] = plan([
    N("n1", "{n0}*{n2}"),
    N("n2", "@n1*(1-{n1}/100)"),
], "n2")

PLANS["g0416"] = plan([
    N("n1", "{n1}-{n0}"),
    N("n2", "{n0}-@n1"),
], "n2")

PLANS["g0417"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1*({n2}/100)"),
    N("n3", "{n3}*7"),
    N("n4", "@n1+@n2+@n3"),
], "n4")

# ---- batch_sealed_31 ----
PLANS["g0418"] = plan([
    N("n1", "{n2}*{n1}/{n0}"),
    N("n2", "@n1*2"),
], "n2")

PLANS["g0419"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "@n1-{n2}"),
], "n2")

PLANS["g0423"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "{n3}/{n4}"),
    N("n3", "{n2}*@n2"),
    N("n4", "{n2}-@n3"),
    N("n5", "@n1+@n3"),
    N("n6", "{n0}+@n4"),
    N("n7", "@n5-@n6"),
], "n7")

PLANS["g0425"] = plan([
    N("n1", "{n2}+{n3}"),
    N("n2", "{n0}*@n1"),
    N("n3", "{n1}*{n2}"),
    N("n4", "@n2+@n3"),
], "n4")

PLANS["g0427"] = plan([
    N("n1", "{n2}/{n3}"),
    N("n2", "1-@n1"),
    N("n3", "{n0}+{n4}"),
    N("n4", "{n1}*@n2"),
    N("n5", "@n3/@n4"),
], "n5")

PLANS["g0428"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "{n0}+@n1"),
    N("n3", "@n2-{n1}"),
    N("n4", "{n1}-@n3"),
], "n4")

PLANS["g0429"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "@n1+{n1}"),
    N("n3", "{n0}+@n2"),
], "n3")

PLANS["g0430"] = plan([
    N("n1", "{n2}*{n3}"),
    N("n2", "{n0}+{n1}+@n1"),
    N("n3", "@n2*(1-{n4}/100)"),
], "n3")

PLANS["g0431"] = plan([
    N("n1", "{n0}+{n1}+{n2}"),
    N("n2", "{n3}+{n4}"),
    N("n3", "@n1-@n2"),
], "n3")

PLANS["g0434"] = plan([
    N("n1", "{n2}*100"),
    N("n2", "@n1*({n4}/100)"),
    N("n3", "@n1-@n2"),
    N("n4", "{n3}*{n0}"),
    N("n5", "@n3-@n4"),
    N("n6", "@n5/{n1}"),
], "n6")

PLANS["g0435"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "@n1/4"),
], "n2")

PLANS["g0436"] = plan([
    N("n1", "{n0}/{n1}"),
    N("n2", "@n1*2"),
    N("n3", "{n0}-@n2"),
], "n3")

PLANS["g0438"] = plan([
    N("n1", "{n0}*2"),
    N("n2", "@n1*{n2}"),
    N("n3", "{n3}*{n4}"),
    N("n4", "@n2+@n3"),
    N("n5", "@n4/{n1}"),
], "n5")

PLANS["g0439"] = plan([
    N("n1", "4*4"),
    N("n2", "@n1-4"),
    N("n3", "@n2+{n0}"),
], "n3")

PLANS["g0441"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "{n2}+{n3}"),
    N("n3", "@n2-@n1"),
    N("n4", "@n3*{n4}"),
], "n4")

PLANS["g0442"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n3}/{n5}"),
    N("n3", "@n2*{n4}"),
    N("n4", "{n0}+@n1-@n3"),
], "n4")

PLANS["g0447"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "{n2}+{n3}"),
    N("n3", "@n1-@n2"),
], "n3")

PLANS["g0448"] = plan([
    N("n1", "{n2}*{n3}"),
    N("n2", "{n0}-{n2}"),
    N("n3", "@n2*{n4}"),
    N("n4", "@n1+@n3-{n1}"),
], "n4")

PLANS["g0449"] = NULL

PLANS["g0450"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "@n1-{n4}"),
    N("n3", "@n2-{n2}-{n3}"),
], "n3")

PLANS["g0452"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "{n2}*{n3}"),
    N("n3", "@n1+@n2"),
    N("n4", "{n1}+{n3}"),
    N("n5", "@n3/@n4"),
], "n5")

PLANS["g0453"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "@n1*{n2}"),
    N("n3", "2*{n3}"),
    N("n4", "@n2+@n3"),
], "n4")

PLANS["g0455"] = plan([
    N("n1", "{n1}*{n2}*{n3}"),
    N("n2", "{n0}*@n1"),
    N("n3", "@n2/{n4}"),
    N("n4", "@n3*{n5}"),
], "n4")

PLANS["g0456"] = plan([
    N("n1", "{n0}*(1+{n1}/100)"),
    N("n2", "{n0}+@n1"),
    N("n3", "@n2*2"),
], "n3")

PLANS["g0458"] = plan([
    N("n1", "{n1}+{n3}"),
    N("n2", "{n0}+{n2}"),
    N("n3", "@n1/@n2*100"),
], "n3")

# ---- batch_sealed_32 ----
PLANS["g0465"] = NULL

PLANS["g0467"] = plan([
    N("n1", "2*2"),
    N("n2", "2*@n1"),
    N("n3", "2+1+@n1+@n2"),
    N("n4", "{n0}*@n3"),
], "n4")

PLANS["g0468"] = plan([
    N("n1", "{n1}+{n2}+{n3}"),
    N("n2", "@n1*2"),
    N("n3", "{n0}+@n2-{n4}"),
], "n3")

PLANS["g0469"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1/{n2}"),
], "n2")

PLANS["g0470"] = plan([
    N("n1", "3*{n0}-{n1}"),
    N("n2", "{n0}+@n1"),
    N("n3", "{n2}-@n2"),
], "n3")

PLANS["g0476"] = plan([
    N("n1", "{n0}/{n1}"),
    N("n2", "@n1/{n2}"),
], "n2")

PLANS["g0479"] = plan([
    N("n1", "{n2}*(1+{n1}/100)"),
    N("n2", "@n1*{n3}"),
    N("n3", "2*{n0}"),
    N("n4", "@n2+@n3"),
], "n4")

PLANS["g0480"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "3*{n1}"),
    N("n3", "@n1+@n2"),
], "n3")

PLANS["g0482"] = plan([
    N("n1", "{n2}+{n3}"),
    N("n2", "{n0}-@n1"),
], "n2")

PLANS["g0484"] = plan([
    N("n1", "{n3}*({n1}/{n2})"),
    N("n2", "{n0}*@n1"),
], "n2")

PLANS["g0485"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "@n1-{n0}"),
], "n2")

PLANS["g0488"] = plan([
    N("n1", "{n0}*(2/3)"),
    N("n2", "@n1*(1/3)"),
], "n2")

PLANS["g0491"] = plan([
    N("n1", "{n0}*{n2}"),
    N("n2", "{n1}-@n1"),
], "n2")

PLANS["g0493"] = plan([
    N("n1", "1*{n1}"),
    N("n2", "@n1-{n2}"),
    N("n3", "{n3}*{n0}"),
    N("n4", "@n2*100"),
    N("n5", "@n4/@n3"),
], "n5")

PLANS["g0494"] = plan([
    N("n1", "3*{n2}"),
    N("n2", "@n1+{n3}"),
    N("n3", "@n2/12"),
], "n3")

PLANS["g0497"] = plan([
    N("n1", "{n1}+{n2}"),
    N("n2", "{n0}*@n1"),
], "n2")

PLANS["g0498"] = NULL

PLANS["g0499"] = plan([
    N("n1", "{n1}-{n2}"),
    N("n2", "{n0}/@n1"),
], "n2")

PLANS["g0501"] = plan([
    N("n1", "{n0}/{n1}"),
    N("n2", "{n2}/{n3}"),
    N("n3", "@n1+@n2"),
    N("n4", "@n3*{n4}"),
], "n4")

PLANS["g0503"] = plan([
    N("n1", "{n2}+{n0}"),
    N("n2", "2*@n1+{n1}"),
], "n2")

PLANS["g0504"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "{n1}-{n0}-@n1"),
    N("n3", "@n2/2"),
], "n3")

PLANS["g0508"] = plan([
    N("n1", "{n1}/2"),
    N("n2", "2*{n0}"),
    N("n3", "{n0}+@n1+@n2+{n1}"),
], "n3")

PLANS["g0509"] = plan([
    N("n1", "{n1}+{n2}"),
    N("n2", "@n1/{n0}"),
], "n2")

PLANS["g0510"] = NULL

PLANS["g0511"] = plan([
    N("n1", "{n0}*7"),
    N("n2", "@n1-{n1}"),
], "n2")

# ---- batch_sealed_33 ----
PLANS["g0514"] = plan([
    N("n1", "{n0}/4"),
    N("n2", "3*@n1"),
], "n2")

PLANS["g0518"] = plan([
    N("n1", "4*{n0}+6*{n1}"),
    N("n2", "@n1/2"),
    N("n3", "@n2*(1-{n2}/{n3})"),
], "n3")

PLANS["g0519"] = plan([
    N("n1", "{n1}*60"),
    N("n2", "2*@n1"),
    N("n3", "@n2+{n0}"),
], "n3")

PLANS["g0521"] = plan([
    N("n1", "{n2}*{n1}"),
    N("n2", "{n0}-{n1}-@n1"),
    N("n3", "@n2*(3/4)"),
], "n3")

PLANS["g0522"] = plan([
    N("n1", "{n0}-1"),
    N("n2", "2*@n1"),
    N("n3", "@n2-2"),
    N("n4", "{n0}+@n1+@n2+@n3"),
], "n4")

PLANS["g0525"] = plan([
    N("n1", "{n0}/3"),
    N("n2", "{n1}/{n2}"),
    N("n3", "@n1/@n2"),
], "n3")

PLANS["g0526"] = plan([
    N("n1", "{n1}*24"),
    N("n2", "@n1*7"),
    N("n3", "@n2*{n2}"),
], "n3")

PLANS["g0527"] = plan([
    N("n1", "{n0}*2"),
    N("n2", "@n1*24"),
    N("n3", "@n2/{n1}"),
], "n3")

PLANS["g0529"] = plan([
    N("n1", "{n1}-{n0}"),
    N("n2", "@n1/{n0}"),
], "n2")

PLANS["g0534"] = plan([
    N("n1", "{n0}*4"),
    N("n2", "{n0}+@n1"),
], "n2")

PLANS["g0537"] = plan([
    N("n1", "{n1}-{n2}"),
    N("n2", "2*{n0}"),
    N("n3", "{n0}+{n1}+@n1+@n2"),
], "n3")

PLANS["g0538"] = plan([
    N("n1", "{n1}+{n2}+{n3}"),
    N("n2", "{n0}-@n1"),
], "n2")

PLANS["g0543"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "@n1*{n2}"),
], "n2")

PLANS["g0544"] = plan([
    N("n1", "{n1}+1"),
    N("n2", "{n0}*({n1}/@n1)"),
], "n2")

PLANS["g0547"] = plan([
    N("n1", "{n1}**3"),
    N("n2", "{n0}*@n1"),
], "n2")

PLANS["g0548"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "{n2}+@n1"),
], "n2")

PLANS["g0558"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "@n1*({n1}/{n2})"),
], "n2")

PLANS["g0560"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n3}*{n4}"),
    N("n3", "@n1+@n2"),
], "n3")

PLANS["g0562"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n0}+@n1"),
], "n2")

PLANS["g0566"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "@n1/3"),
    N("n3", "@n2-{n1}"),
], "n3")

PLANS["g0567"] = plan([
    N("n1", "3*{n1}"),
    N("n2", "({n1}/2)*{n2}"),
    N("n3", "{n0}+@n1+@n2"),
], "n3")

PLANS["g0568"] = plan([
    N("n1", "{n2}-{n0}"),
    N("n2", "{n2}-{n1}"),
    N("n3", "{n2}+@n1+@n2"),
], "n3")

PLANS["g0571"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n3}*{n4}"),
    N("n3", "{n0}+@n1+@n2"),
], "n3")

PLANS["g0573"] = plan([
    N("n1", "{n2}*12"),
    N("n2", "{n1}*@n1"),
    N("n3", "{n0}-@n2"),
], "n3")

PLANS["g0576"] = plan([
    N("n1", "{n0}+{n1}+{n2}+{n3}"),
    N("n2", "{n4}*{n5}"),
    N("n3", "@n1*@n2"),
], "n3")

# ---- batch_sealed_34 ----
PLANS["g0578"] = plan([
    N("n1", "{n0}/2"),
    N("n2", "{n0}+@n1"),
    N("n3", "@n2/{n1}"),
    N("n4", "{n0}-{n2}"),
    N("n5", "@n3*@n4"),
], "n5")

PLANS["g0582"] = plan([
    N("n1", "{n0}*(1-{n1}/100)"),
    N("n2", "{n0}+@n1"),
], "n2")

PLANS["g0583"] = plan([
    N("n1", "2*12"),
    N("n2", "@n1+{n1}"),
    N("n3", "12+@n1+{n0}+@n2"),
], "n3")

PLANS["g0585"] = plan([
    N("n1", "{n1}+{n2}"),
    N("n2", "2*{n1}"),
    N("n3", "3*{n2}"),
    N("n4", "@n2+@n3"),
    N("n5", "@n4-@n1"),
    N("n6", "@n5*{n0}"),
], "n6")

PLANS["g0586"] = plan([
    N("n1", "{n2}*{n3}"),
    N("n2", "{n4}*{n5}"),
    N("n3", "@n1+@n2"),
    N("n4", "@n3*({n0}/{n1})"),
], "n4")

PLANS["g0587"] = plan([
    N("n1", "(1-{n0}/100)+(1+{n1}/100)+1"),
    N("n2", "{n2}/@n1"),
    N("n3", "({n1}/100)+({n0}/100)"),
    N("n4", "@n2*@n3"),
], "n4")

PLANS["g0589"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "@n1*{n2}"),
], "n2")

PLANS["g0592"] = plan([
    N("n1", "{n0}+{n1}"),
    N("n2", "2*{n1}"),
    N("n3", "{n2}+@n2"),
    N("n4", "@n3-@n1"),
], "n4")

PLANS["g0594"] = plan([
    N("n1", "{n2}*({n1}/{n0})"),
    N("n2", "@n1*7"),
], "n2")

PLANS["g0595"] = plan([
    N("n1", "2*{n0}"),
    N("n2", "@n1+{n1}"),
], "n2")

PLANS["g0596"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1+{n2}"),
    N("n3", "@n2-{n3}"),
    N("n4", "@n3/{n4}"),
], "n4")

PLANS["g0597"] = plan([
    N("n1", "1+2+3"),
    N("n2", "{n0}/@n1"),
    N("n3", "@n2*3"),
], "n3")

PLANS["g0598"] = NULL

PLANS["g0599"] = plan([
    N("n1", "{n0}*4"),
    N("n2", "{n1}*4"),
    N("n3", "{n2}*2"),
    N("n4", "@n1+@n2+@n3"),
], "n4")

PLANS["g0600"] = plan([
    N("n1", "{n0}*(1+{n1}/100)"),
    N("n2", "@n1-2"),
], "n2")

PLANS["g0602"] = plan([
    N("n1", "{n0}/{n1}"),
    N("n2", "{n2}/@n1"),
], "n2")

PLANS["g0604"] = plan([
    N("n1", "2*{n0}"),
    N("n2", "{n1}*@n1"),
    N("n3", "{n0}+@n1+@n2"),
    N("n4", "{n2}-@n3"),
], "n4")

PLANS["g0605"] = plan([
    N("n1", "4*{n0}*{n1}"),
    N("n2", "2*{n2}*{n3}"),
    N("n3", "@n1+@n2"),
], "n3")

PLANS["g0607"] = plan([
    N("n1", "{n1}*{n2}"),
    N("n2", "{n0}/@n1"),
    N("n3", "@n2*100"),
], "n3")

PLANS["g0608"] = plan([
    N("n1", "{n2}+{n3}"),
    N("n2", "@n1*(1-{n1}/100)"),
    N("n3", "{n0}-@n2"),
], "n3")

PLANS["g0609"] = plan([
    N("n1", "{n0}/{n1}"),
    N("n2", "@n1*{n3}"),
    N("n3", "@n2*7"),
], "n3")

PLANS["g0612"] = NULL
PLANS["g0613"] = NULL

PLANS["g0614"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1*2"),
    N("n3", "365/7"),
    N("n4", "@n2*@n3"),
], "n4")

PLANS["g0617"] = NULL

# ---- batch_sealed_35 ----
PLANS["g0618"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1*(1/4)"),
    N("n3", "@n1-@n2"),
    N("n4", "@n3*(1/3)"),
    N("n5", "@n3-@n4"),
], "n5")

PLANS["g0621"] = plan([
    N("n1", "{n0}*2*{n1}"),
    N("n2", "@n1*{n2}"),
], "n2")

PLANS["g0623"] = plan([
    N("n1", "{n0}-{n1}"),
    N("n2", "@n1+{n2}"),
], "n2")

PLANS["g0624"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "{n2}*{n3}"),
    N("n3", "@n2-@n1"),
], "n3")

PLANS["g0626"] = NULL
PLANS["g0627"] = NULL

PLANS["g0630"] = plan([
    N("n1", "{n3}*({n1}/100)"),
    N("n2", "@n1*(1-{n2}/100)"),
], "n2")

PLANS["g0638"] = plan([
    N("n1", "{n0}/4"),
    N("n2", "{n1}/3"),
    N("n3", "{n2}*@n1"),
    N("n4", "{n3}*@n2"),
    N("n5", "@n3+@n4"),
], "n5")

PLANS["g0640"] = plan([
    N("n1", "{n1}/3"),
    N("n2", "@n1-{n2}"),
    N("n3", "{n0}+{n1}+@n1+@n2+{n3}"),
], "n3")

PLANS["g0642"] = plan([
    N("n1", "{n0}*{n3}"),
    N("n2", "{n3}*({n4}/{n5})"),
    N("n3", "{n1}*@n2"),
    N("n4", "{n2}*{n0}"),
    N("n5", "@n4*{n6}"),
    N("n6", "@n1+@n3+@n5"),
], "n6")

PLANS["g0645"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "@n1*3"),
], "n2")

PLANS["g0646"] = plan([
    N("n1", "{n0}*{n1}"),
    N("n2", "{n2}*{n3}"),
    N("n3", "@n1+@n2"),
], "n3")

PLANS["g0648"] = plan([
    N("n1", "2+{n1}"),
    N("n2", "@n1*{n0}"),
], "n2")

PLANS["g0649"] = plan([
    N("n1", "{n2}*{n0}"),
    N("n2", "@n1+{n3}"),
], "n2")

PLANS["g0650"] = plan([
    N("n1", "{n0}*{n1}-{n2}"),
    N("n2", "{n5}*{n3}*(1-{n4}/100)"),
    N("n3", "@n2-@n1"),
], "n3")

PLANS["g0651"] = plan([
    N("n1", "2*{n0}"),
    N("n2", "{n0}+@n1"),
    N("n3", "@n2*(1+{n1}/{n2})"),
], "n3")

PLANS["g0654"] = plan([
    N("n1", "{n2}*{n3}"),
    N("n2", "@n1/{n1}"),
    N("n3", "@n2/12"),
], "n3")

PLANS["g0655"] = plan([
    N("n1", "{n1}/{n2}"),
    N("n2", "{n0}*(1-@n1)"),
], "n2")

PLANS["g0660"] = plan([
    N("n1", "2*{n1}"),
    N("n2", "{n0}-@n1"),
    N("n3", "@n2/2"),
], "n3")

PLANS["g0665"] = plan([
    N("n1", "{n0}*(1-{n1}/100)"),
    N("n2", "@n1*{n2}"),
], "n2")

PLANS["g0666"] = plan([
    N("n1", "{n1}/{n2}"),
    N("n2", "@n1*{n3}"),
    N("n3", "@n2+{n0}"),
    N("n4", "{n3}+@n2+@n3"),
    N("n5", "@n4/3"),
], "n5")

PLANS["g0668"] = plan([
    N("n1", "{n0}*({n1}/100)"),
    N("n2", "@n1*({n3}/100)"),
], "n2")

PLANS["g0669"] = plan([
    N("n1", "{n0}+{n1}+{n2}"),
    N("n2", "@n1*{n3}"),
], "n2")

PLANS["g0670"] = plan([
    N("n1", "{n0}+{n1}+{n2}"),
    N("n2", "@n1/3"),
], "n2")

PLANS["g0672"] = NULL

# ---- write files ----
ids_in_order = []
for batch in ["batch_sealed_30.json","batch_sealed_31.json","batch_sealed_32.json",
              "batch_sealed_33.json","batch_sealed_34.json","batch_sealed_35.json"]:
    p = os.path.join(os.path.dirname(__file__), batch)
    with open(p, "r", encoding="utf-8") as f:
        items = json.load(f)
    for it in items:
        ids_in_order.append(it["id"])

assert len(ids_in_order) == 150, f"expected 150 ids, got {len(ids_in_order)}"

missing = [i for i in ids_in_order if i not in PLANS]
if missing:
    raise SystemExit(f"MISSING PLANS FOR: {missing}")

extra = [i for i in PLANS if i not in ids_in_order]
if extra:
    raise SystemExit(f"EXTRA PLANS NOT IN INPUT: {extra}")

null_count = 0
written = 0
for id_ in ids_in_order:
    obj = PLANS[id_]
    if obj["plan"] is None:
        null_count += 1
    out_path = os.path.join(OUT, f"reading_{id_}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    written += 1

print(f"WROTE {written} files, {null_count} null, {written-null_count} non-null")
