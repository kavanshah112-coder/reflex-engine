# -*- coding: utf-8 -*-
"""V0.8 Capability Index (spec Section 9).

Wraps the frozen V0.3/V0.4 registry (+ optionally V0.6 bred caps) into
records with STABLE unique identifiers CAP_NNN. IDs are assigned by sorted
capability name at freeze time and never change afterwards; the frozen
index is persisted with a hash. Execution still goes through the proven
v4.registry_v4.execute — this module adds identity/metadata, not a new
executor.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from v4.registry_v4 import REGISTRY, execute as _exec4  # noqa: E402
from v3.capabilities import REGISTRY as PHYS            # noqa: E402
from v3 import ir as ir3                                # noqa: E402


def _provenance(name):
    if name in PHYS:
        return "v0.3-physics"
    return "v0.4-finance-engineering"


def build_index(extra_caps=None):
    """extra_caps: {name: spec} additions (e.g. V0.6 bred caps), executed
    via their own 'expr' through the v4 executor mechanism."""
    reg = dict(REGISTRY)
    prov = {n: _provenance(n) for n in reg}
    for n, spec in (extra_caps or {}).items():
        assert n not in reg, f"duplicate capability {n}"
        reg[n] = spec
        prov[n] = spec.get("provenance", "v0.6-bred")
    records, by_name = {}, {}
    for i, name in enumerate(sorted(reg), start=1):
        spec = reg[name]
        cid = f"CAP_{i:03d}"
        records[cid] = {
            "capability_id": cid,
            "concept": name,
            "input_kinds": list(spec["inputs"]),
            "output_kind": spec["output"],
            "units": {k: ir3.KINDS.get(k, "") for k in
                      list(spec["inputs"]) + [spec["output"]]},
            "preconditions": ("context_exclude=" +
                             ",".join(spec.get("context_exclude", []))
                             if spec.get("context_exclude") else
                             ("callable" if spec.get("pre") else "none")),
            "executor": spec.get("equation", spec.get("expr", "")),
            "provenance": prov[name],
            "builder": spec.get("builder", "curated"),
            "validation_status": "frozen-validated",
            "version": "v0.8",
            "dependencies": [],
        }
        by_name[name] = cid
    return {"records": records, "by_name": by_name, "registry": reg}


def index_hash(idx):
    slim = {cid: {"c": r["concept"], "i": r["input_kinds"],
                  "o": r["output_kind"]}
            for cid, r in sorted(idx["records"].items())}
    return hashlib.sha256(json.dumps(slim, sort_keys=True)
                          .encode()).hexdigest()


def save_index(idx, path):
    doc = {"hash": index_hash(idx), "n": len(idx["records"]),
           "records": idx["records"]}
    Path(path).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return doc["hash"]


def execute_cap(idx, cap_id, inputs):
    """Deterministic execution by CAP id. inputs: {kind: Quantity}."""
    name = idx["records"][cap_id]["concept"]
    return _exec4(name, inputs, registry=idx["registry"])


def gap_registry(idx, removed_names):
    """Return a shallow view with the pre-declared gap caps removed
    (Amendment A1). The index keeps ALL records (IDs stable); availability
    is what changes."""
    avail = {n for n in idx["registry"] if n not in set(removed_names)}
    return avail


GAP_CAPS = ["heat_to_temp_rise", "total_cost", "mass_from_density",
            "power_from_vi"]  # Amendment A1, structural choice
