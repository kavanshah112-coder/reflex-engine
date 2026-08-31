# -*- coding: utf-8 -*-
# origin: new for V1.3 -- W6 corpora (V1_3_SPEC section 9)
"""Builds the two W6 document corpora and their ground-truthed queries.

  D-generic  equipment specs, tariffs, invoices, service schedules
  D-user     plastics quoting: material sheets, machine rate cards,
             part specs, finishing rates

Identical structure and identical query design in both, so the
cross-corpus comparison in section 9 isolates DOMAIN and nothing else.

Ground truth is produced by construction, never by solving: the
generator knows the numbers it wrote into the documents, so an answer
is exact and no grader has to interpret prose. Every fact carries
provenance -- source id, version, validity window -- because section 9
certifies FACTUAL answers on provenance rather than on derivation, and
provenance cannot be reconstructed after the fact.

Three hazards are planted deliberately, identically in both corpora:
  CONFLICT    two live documents disagree about one fact
  STALE       a revision exists outside its validity window
  SUPERSEDED  an older version is still present alongside its
              replacement
Without them a provenance layer cannot be shown to do anything.
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "v13" / "corpora"

PUMPS = ["Centrifugal Pump CP-{}", "Booster Pump BP-{}",
         "Vacuum Pump VP-{}", "Chiller Unit CU-{}",
         "Air Compressor AC-{}"]
REGIONS = ["Northland", "Eastport", "Southgate", "Westmere"]

POLYMERS = ["ABS GP-{}", "Polypropylene PP-{}", "Nylon PA6-{}",
            "Polycarbonate PC-{}", "HDPE HD-{}"]
MACHINES = ["Injection Press IP-{}", "Toggle Press TP-{}",
            "Electric Press EP-{}"]


def doc(did, title, version, valid_from, valid_to, body, facts):
    return {"id": did, "title": title, "version": version,
            "valid_from": valid_from, "valid_to": valid_to,
            "text": body, "facts": facts}


def build_generic(rng):
    docs, facts = [], {}
    for i in range(12):
        name = PUMPS[i % len(PUMPS)].format(100 + i)
        kw = round(rng.uniform(1.5, 45.0), 1)
        hrs = rng.choice([4, 6, 8, 12, 16, 24])
        eff = rng.choice([0.72, 0.78, 0.84, 0.9])
        did = "G-EQ-%03d" % i
        body = ("EQUIPMENT SPECIFICATION - %s\n"
                "Rated power: %s kW\n"
                "Nominal duty: %s hours per day\n"
                "Drive efficiency: %s\n"
                "Installed at the %s site.\n"
                % (name, kw, hrs, eff, REGIONS[i % 4]))
        f = {"power_kw": kw, "duty_h": hrs, "efficiency": eff}
        docs.append(doc(did, name, 1, "2025-01-01", "2027-12-31",
                        body, f))
        facts[name] = dict(f, doc=did)
    for i in range(8):
        reg = REGIONS[i % 4]
        rate = round(rng.uniform(0.09, 0.31), 4)
        standing = round(rng.uniform(8.0, 45.0), 2)
        did = "G-TF-%03d" % i
        title = "Tariff %s S%d" % (reg, i)
        body = ("ELECTRICITY TARIFF - %s - Schedule %d\n"
                "Energy rate: %s USD per kWh\n"
                "Standing charge: %s USD per month\n"
                % (reg, i, rate, standing))
        f = {"rate": rate, "standing": standing}
        docs.append(doc(did, title, 2, "2026-01-01", "2026-12-31",
                        body, f))
        facts[title] = dict(f, doc=did)
    for i in range(12):
        qty = rng.randint(4, 260)
        unit = round(rng.uniform(1.2, 340.0), 2)
        did = "G-IN-%03d" % i
        title = "Invoice %d" % (9000 + i)
        body = ("INVOICE %d\n"
                "Line 1: Filter cartridge FC-%d\n"
                "Quantity: %d units\n"
                "Unit price: %s USD\n"
                % (9000 + i, 200 + i, qty, unit))
        f = {"qty": qty, "unit_price": unit}
        docs.append(doc(did, title, 1, "2026-02-01", "2027-02-01",
                        body, f))
        facts[title] = dict(f, doc=did)
    for i in range(8):
        interval = rng.choice([500, 1000, 2000, 4000])
        labour = round(rng.uniform(45.0, 140.0), 2)
        did = "G-SV-%03d" % i
        title = "Service SS-%d" % i
        body = ("SERVICE SCHEDULE SS-%d\n"
                "Service interval: %d operating hours\n"
                "Labour rate: %s USD per hour\n"
                % (i, interval, labour))
        f = {"interval_h": interval, "labour": labour}
        docs.append(doc(did, title, 1, "2026-01-01", "2027-06-30",
                        body, f))
        facts[title] = dict(f, doc=did)
    return docs, facts


def build_user(rng):
    docs, facts = [], {}
    for i in range(12):
        name = POLYMERS[i % len(POLYMERS)].format(500 + i)
        dens = round(rng.uniform(0.91, 1.42), 3)
        price = round(rng.uniform(1.15, 4.90), 2)
        shrink = round(rng.uniform(0.4, 2.2), 2)
        did = "U-MT-%03d" % i
        body = ("MATERIAL DATA SHEET - %s\n"
                "Density: %s g/cm3\n"
                "Resin price: %s USD per kg\n"
                "Mould shrinkage: %s percent\n"
                % (name, dens, price, shrink))
        f = {"density": dens, "price_kg": price, "shrinkage": shrink}
        docs.append(doc(did, name, 1, "2026-01-01", "2027-12-31",
                        body, f))
        facts[name] = dict(f, doc=did)
    for i in range(8):
        name = MACHINES[i % len(MACHINES)].format(80 + i * 10)
        rate = round(rng.uniform(38.0, 145.0), 2)
        setup = round(rng.uniform(0.5, 4.0), 2)
        tonnage = rng.choice([80, 120, 180, 250, 350, 500])
        did = "U-MC-%03d" % i
        body = ("MACHINE RATE CARD - %s\n"
                "Clamping force: %d tonnes\n"
                "Hourly rate: %s USD per hour\n"
                "Setup allowance: %s hours\n"
                % (name, tonnage, rate, setup))
        f = {"rate_h": rate, "setup_h": setup, "tonnage": tonnage}
        docs.append(doc(did, name, 1, "2026-01-01", "2027-12-31",
                        body, f))
        facts[name] = dict(f, doc=did)
    for i in range(12):
        pname = "Part PN-%d" % (3000 + i)
        wt = round(rng.uniform(4.0, 380.0), 1)
        cav = rng.choice([1, 2, 4, 8, 16])
        cyc = round(rng.uniform(8.0, 65.0), 1)
        runner = round(rng.uniform(0.5, 24.0), 1)
        did = "U-PT-%03d" % i
        body = ("PART SPECIFICATION - %s\n"
                "Shot weight per part: %s g\n"
                "Cavities in tool: %d\n"
                "Cycle time: %s seconds\n"
                "Runner weight per shot: %s g\n"
                % (pname, wt, cav, cyc, runner))
        f = {"weight_g": wt, "cavities": cav, "cycle_s": cyc,
             "runner_g": runner}
        docs.append(doc(did, pname, 1, "2026-03-01", "2027-12-31",
                        body, f))
        facts[pname] = dict(f, doc=did)
    for i in range(8):
        pack = rng.randint(12, 240)
        freight = round(rng.uniform(0.35, 3.10), 2)
        did = "U-FN-%03d" % i
        title = "Packing PF-%d" % i
        body = ("PACKING AND FREIGHT SHEET PF-%d\n"
                "Parts per carton: %d\n"
                "Freight cost: %s USD per kg\n"
                % (i, pack, freight))
        f = {"per_carton": pack, "freight_kg": freight}
        docs.append(doc(did, title, 1, "2026-01-01", "2027-12-31",
                        body, f))
        facts[title] = dict(f, doc=did)
    return docs, facts


def plant_hazards(docs, facts, rng, prefix):
    """CONFLICT / STALE / SUPERSEDED, three of each."""
    hz = []
    numeric = sorted(t for t, f in facts.items()
                     if any(isinstance(v, (int, float))
                            for v in f.values()))
    for j, title in enumerate(rng.sample(numeric, 9)):
        base = facts[title]
        key = sorted(k for k, v in base.items()
                     if isinstance(v, (int, float)))[0]
        if j < 3:
            bad = round(float(base[key]) * 1.37 + 1, 3)
            did = "%s-CF-%03d" % (prefix, j)
            docs.append(doc(did, title + " (alternate record)", 1,
                            "2026-01-01", "2027-12-31",
                            "SUPPLEMENTARY RECORD - %s\n%s: %s\n"
                            % (title, key, bad), {key: bad}))
            hz.append({"type": "conflict", "title": title,
                       "key": key, "true": base[key],
                       "false": bad, "doc": did})
        elif j < 6:
            newer = round(float(base[key]) * 0.81, 3)
            did = "%s-ST-%03d" % (prefix, j)
            docs.append(doc(did, title + " (expired revision)", 3,
                            "2024-01-01", "2025-06-30",
                            "REVISION (EXPIRED) - %s\n%s: %s\n"
                            % (title, key, newer), {key: newer}))
            hz.append({"type": "stale", "title": title, "key": key,
                       "true": base[key], "expired": newer,
                       "doc": did})
        else:
            old = round(float(base[key]) * 1.19, 3)
            did = "%s-SU-%03d" % (prefix, j)
            docs.append(doc(did, title + " (version 0, superseded)",
                            0, "2023-01-01", "2027-12-31",
                            "SUPERSEDED VERSION 0 - %s\n%s: %s\n"
                            % (title, key, old), {key: old}))
            hz.append({"type": "superseded", "title": title,
                       "key": key, "true": base[key], "old": old,
                       "doc": did})
    return hz


LABELS = {"power_kw": "rated power in kW",
          "duty_h": "nominal duty in hours per day",
          "efficiency": "drive efficiency",
          "rate": "energy rate in USD per kWh",
          "standing": "standing charge per month in USD",
          "qty": "quantity of units",
          "unit_price": "unit price in USD",
          "interval_h": "service interval in operating hours",
          "labour": "labour rate in USD per hour",
          "density": "density in g/cm3",
          "price_kg": "resin price in USD per kg",
          "shrinkage": "mould shrinkage in percent",
          "rate_h": "hourly machine rate in USD",
          "setup_h": "setup allowance in hours",
          "tonnage": "clamping force in tonnes",
          "weight_g": "shot weight per part in g",
          "cavities": "number of cavities",
          "cycle_s": "cycle time in seconds",
          "runner_g": "runner weight per shot in g",
          "per_carton": "parts per carton",
          "freight_kg": "freight cost in USD per kg"}


def make_queries(facts, kind, rng, n=300):
    """Half FACTUAL (retrieval only), half DERIVED (retrieval AND
    computation). Templates differ per corpus but the SPLIT and the
    count are identical, which is what makes the two comparable."""
    qs = []
    titles = sorted(facts)
    has = lambda k: [t for t in titles if k in facts[t]]
    if kind == "generic":
        left, right = has("power_kw"), has("rate")
        pool = titles
    else:
        left, right = has("cycle_s"), has("rate_h")
        pool = titles
    while len(qs) < n:
        i = len(qs)
        pre = "g" if kind == "generic" else "u"
        if i % 2 == 0:
            t = rng.choice(pool)
            f = facts[t]
            keys = sorted(k for k, v in f.items()
                          if isinstance(v, (int, float)))
            key = rng.choice(keys)
            qs.append({"id": "%s%04d" % (pre, i), "family": "factual",
                       "q": "What is the %s for %s?"
                            % (LABELS[key], t),
                       "answer": float(f[key]),
                       "needs": [f["doc"]], "title": t, "key": key})
        else:
            a, b = rng.choice(left), rng.choice(right)
            fa, fb = facts[a], facts[b]
            if kind == "generic":
                days = rng.choice([20, 22, 30])
                ans = round(fa["power_kw"] * fa["duty_h"] * days
                            * fb["rate"], 4)
                q = ("The %s runs its nominal daily duty for %d days. "
                     "Priced on %s, what is the energy cost in USD?"
                     % (a, days, b))
                extra = {"days": days}
            else:
                shots = rng.choice([500, 1000, 2500, 5000])
                ans = round(fa["cycle_s"] * shots / 3600.0
                            * fb["rate_h"], 4)
                q = ("A run of %d shots of %s is quoted on %s. "
                     "What is the machine cost in USD?"
                     % (shots, a, b))
                extra = {"shots": shots}
            qs.append({"id": "%s%04d" % (pre, i), "family": "derived",
                       "q": q, "answer": ans,
                       "needs": [fa["doc"], fb["doc"]],
                       "titles": [a, b], "given": extra})
    return qs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for kind, builder, prefix in (("generic", build_generic, "G"),
                                  ("user", build_user, "U")):
        rng = random.Random(1303 if kind == "generic" else 1304)
        docs, facts = builder(rng)
        hz = plant_hazards(docs, facts, rng, prefix)
        qs = make_queries(facts, kind, rng)
        for nm, obj in (("docs", docs), ("facts", facts),
                        ("hazards", hz), ("queries", qs)):
            (OUT / ("%s_%s.json" % (kind, nm))).write_text(
                json.dumps(obj, indent=1), encoding="utf-8")
        fam = {}
        for q in qs:
            fam[q["family"]] = fam.get(q["family"], 0) + 1
        print("%-8s docs=%3d facts=%3d hazards=%d queries=%d %s"
              % (kind, len(docs), len(facts), len(hz), len(qs), fam))


if __name__ == "__main__":
    main()
