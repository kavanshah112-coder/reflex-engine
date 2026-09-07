import json, os

OUTDIR = "results/v19/bridge/readings_sonnet_sealed"
os.makedirs(OUTDIR, exist_ok=True)

def evalnode(nid, expr):
    return {"id": nid, "op": "evaluate", "expr": expr}

def plan_chain(exprs):
    """exprs: list of expr strings, each may reference previous via @n1 etc.
    Returns plan dict with nodes n1..nk, final = nk."""
    nodes = []
    for i, e in enumerate(exprs, start=1):
        nodes.append(evalnode(f"n{i}", e))
    return {"nodes": nodes, "final": f"n{len(exprs)}"}

def single(expr):
    return plan_chain([expr])

# ---- explicit per-id plan definitions ----
plans = {}

def setp(idn, plan):
    plans[idn] = plan

def null(idn):
    plans[idn] = None

# ---------------- batch 18 ----------------
null("a1737")
null("a1739")
null("a1741")
null("a1746")
null("a1750")
null("a1752")
null("a1753")
setp("a1755", single("12/4"))
null("a1759")
null("a1760")
null("a1762")
null("a1765")
setp("a1770", single("{n0}*{n1}"))
setp("a1771", single("{n0}/{n1}"))
setp("a1776", single("{n0}-{n1}"))
setp("a1780", single("{n0}*{n1}"))
setp("a1783", single("{n0}-{n1}"))
setp("a1797", single("{n0}/{n1}"))
setp("a1798", single("{n0}*{n1}"))
setp("a1800", single("{n0}*{n1}"))
setp("a1804", single("{n0}*{n1}"))
setp("a1808", single("{n0}-{n1}"))
setp("a1814", single("{n0}+{n1}"))
setp("a1821", single("{n1}/{n0}"))
setp("a1824", single("{n0}*{n1}"))

# ---------------- batch 19 ----------------
setp("a1829", single("{n0}-{n1}"))
setp("a1832", single("{n0}*{n1}"))
setp("a1836", single("{n0}-{n1}"))
setp("a1839", single("3+4"))
null("a1847")
setp("a1851", single("12+3"))
null("a1856")
null("a1857")
null("a1860")
null("a1862")
null("a1864")
null("a1869")
null("a1871")
null("a1872")
null("a1873")
setp("a1874", single("2+3"))
null("a1877")
null("a1879")
null("a1891")
null("a1894")
null("a1897")
null("a1902")
null("a1903")
null("a1905")
null("a1915")

# ---------------- batch 20 ----------------
null("a1917")
null("a1925")
null("a1927")
null("a1930")
null("a1936")
null("a1940")
null("a1942")
setp("a1949", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1958", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1964", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1972", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1975", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1976", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
setp("a1978", plan_chain(["{n0}+{n1}", "@n1+{n2}"]))
null("a1982")
setp("a1988", plan_chain([
    "{n0}+{n1}", "@n1+{n2}", "@n2+{n3}", "@n3+{n4}", "@n4+{n5}", "@n5/6"
]))
setp("a1993", plan_chain(["{n0}+{n1}", "@n1-{n2}"]))
setp("a1995", plan_chain(["{n0}+{n1}", "@n1-{n2}"]))
setp("a1997", plan_chain(["{n0}+{n1}", "@n1-{n2}"]))
setp("a2009", plan_chain(["{n0}+{n1}", "@n1-{n2}"]))
null("a2014")
null("a2016")
null("a2018")
null("a2025")
null("a2027")

# ---------------- batch 21 ----------------
null("a2030")
null("a2036")
null("a2042")
null("a2046")
null("a2049")
null("a2052")
null("a2053")
null("a2062")
null("a2065")
null("a2066")
null("a2071")
null("a2079")
null("a2091")
setp("a2095", plan_chain(["{n0}*{n2}", "{n1}*{n3}", "@n1+@n2"]))
setp("a2098", plan_chain(["{n1}*{n2}", "{n0}+@n1"]))
setp("a2102", plan_chain(["{n1}*{n2}", "{n0}+@n1"]))
setp("a2108", plan_chain(["{n0}*{n1}", "@n1+{n2}"]))
setp("a2111", plan_chain(["{n1}*{n2}", "{n0}+@n1"]))
null("a2119")
null("a2121")
null("a2122")
null("a2123")
null("a2125")
null("a2128")
null("a2138")

# ---------------- batch 22 ----------------
null("a2140")
null("a2154")
setp("a2157", single("12+3"))
setp("a2167", plan_chain(["{n0}-{n1}", "@n1+{n2}"]))
setp("a2171", plan_chain(["{n0}-{n1}", "@n1+{n2}"]))
setp("a2178", plan_chain(["{n0}-{n1}", "@n1+{n2}"]))
setp("a2183", plan_chain(["{n0}-{n1}", "@n1+{n2}"]))
null("a2190")
null("a2193")
null("a2194")
null("a2195")
null("a2196")
null("a2201")
null("a2202")
null("a2203")
setp("a2208", plan_chain(["5+5", "@n1*5"]))
setp("a2210", plan_chain(["5+5", "@n1*3"]))
setp("a2216", plan_chain(["3+5", "@n1*3"]))
null("a2217")
setp("a2220", plan_chain(["5+3", "5*@n1"]))
null("a2223")
null("a2225")
null("a2230")
null("a2232")
null("a2234")

# ---------------- batch 23 ----------------
null("a2237")
null("a2240")
null("a2241")
setp("a2242", plan_chain(["{n0}-{n1}", "@n1*{n2}"]))
setp("a2249", plan_chain(["{n0}-{n1}", "@n1*{n2}"]))
setp("a2253", plan_chain(["{n1}-{n2}", "{n0}*@n1"]))
setp("a2254", plan_chain(["{n0}-{n1}", "@n1*{n2}"]))
setp("a2255", plan_chain(["{n1}-{n2}", "{n0}*@n1"]))
setp("a2257", plan_chain(["{n1}-{n2}", "{n0}*@n1"]))
setp("a2260", plan_chain(["{n0}-{n1}", "@n1*{n2}"]))
setp("a2265", single("{n0}/{n1}"))
setp("a2266", single("{n0}/{n1}"))
setp("a2277", single("{n0}/{n1}"))
setp("a2280", single("{n1}/{n0}"))
setp("a2281", single("{n0}/{n1}"))
setp("a2282", single("{n0}/{n1}"))
setp("a2293", single("{n1}/{n0}"))
setp("a2295", single("{n0}/{n2}"))
setp("a2302", single("{n1}/{n0}"))
setp("g0000", plan_chain(["{n0}-3", "@n1-4", "@n2*{n1}"]))
setp("g0001", plan_chain(["{n0}*0.5", "{n0}+@n1"]))
setp("g0002", plan_chain([
    "{n2}/100",      # n1: rate
    "{n0}*@n1",      # n2: increase
    "{n0}+@n2",      # n3: new value
    "{n0}+{n1}",     # n4: cost
    "@n3-@n4",       # n5: profit
]))
setp("g0006", plan_chain([
    "{n1}*{n0}",   # n1: Charleston = Seattle*4
    "@n1*2",       # n2: Toulouse = Charleston*2
    "@n2+@n1",     # n3: Toulouse+Charleston
    "@n3+{n1}",    # n4: + Seattle
]))
setp("g0007", plan_chain([
    "{n2}/100",     # n1: 0.4
    "{n0}*@n1",     # n2: 80 GB
    "@n2/{n1}",     # n3: 40 min
    "{n0}/{n1}",    # n4: 100 min full download
    "@n3+{n3}",     # n5: 40+20
    "@n5+@n4",      # n6: total
]))
null("g0008")

# ---- verify against actual input ids ----
files = [f"results/v19/bridge/batch_sealed_{i}.json" for i in range(18, 24)]
all_ids = []
for f in files:
    data = json.load(open(f, encoding="utf-8"))
    for item in data:
        all_ids.append(item["id"])

missing = [i for i in all_ids if i not in plans]
extra = [i for i in plans if i not in all_ids]
if missing:
    raise SystemExit(f"MISSING plans for: {missing}")
if extra:
    raise SystemExit(f"EXTRA plans not in input: {extra}")
if len(all_ids) != 150:
    raise SystemExit(f"expected 150 ids, got {len(all_ids)}")

count_null = 0
count_plan = 0
for idn in all_ids:
    p = plans[idn]
    obj = {"plan": p}
    outpath = os.path.join(OUTDIR, f"reading_{idn}.json")
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    if p is None:
        count_null += 1
    else:
        count_plan += 1

print(f"wrote {len(all_ids)} files; plan={count_plan} null={count_null}")
