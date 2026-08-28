# -*- coding: utf-8 -*-
"""P2b-1 verification: the pack-loader path reconstructs EXACTLY the
same domain tables as the lexpatch11-on-hardcoded path. Twin
subprocess dumps, byte-compared."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]

DUMP = r'''
import sys, json, re
from pathlib import Path
HERE = Path(r"{here}")
sys.path.insert(0, str(HERE / "reflex" / "_arc"))
mode = "{mode}"
if mode == "lexpatch":
    from v11 import lexpatch11
    lexpatch11.apply()
else:
    sys.path.insert(0, str(HERE))
    from reflex.packs import loader
    loader.apply(HERE / "packs" / "physics")
import v10.nlpw10 as W
import v10.universe10 as U10
import v9.universe9 as U9
import v11.semstate11 as SS
import v11.semparse11 as SP
import v11.semrun11 as SR
def ser(x):
    if isinstance(x, dict):
        return {{k: ser(v) for k, v in sorted(x.items())}}
    if isinstance(x, (list, tuple)):
        return [ser(v) for v in x]
    if isinstance(x, set):
        return sorted(x)
    if callable(x):
        return "<fn>"
    return x
out = {{
 "KINDS10": ser(U10.KINDS10),
 "W_KINDS": ser(dict(W.KINDS9)),
 "EXTRA_NOUNS": ser(W._EXTRA_NOUNS),
 "ADJ": ser(W._ADJ),
 "UNIT_WORDS": ser(W.UNIT_WORDS),
 "UNIT_IDX": ser(W._UNIT_IDX),
 "CONV": ser(W._CONV),
 "COMPARATIVES": ser(SS.COMPARATIVES),
 "ENT_RE": SP.ENT_RE.pattern,
 "REF_RE": SP.REF_RE.pattern,
 "CAPS9": ser(U9.CAPS9),
 "CAPS10": ser(U10.CAPS10_EXTRA),
 "REG11": ser(SR.REG11),
}}
print(json.dumps(out, sort_keys=True))
'''


def dump(mode):
    code = DUMP.format(here=HERE, mode=mode)
    p = subprocess.run([sys.executable, "-c", code],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    return json.loads(p.stdout)


if __name__ == "__main__":
    a = dump("lexpatch")
    b = dump("pack")
    bad = []
    for k in a:
        if a[k] != b[k]:
            bad.append(k)
    if bad:
        for k in bad:
            sa, sb = json.dumps(a[k]), json.dumps(b[k])
            print(f"MISMATCH {k}: lens {len(sa)} vs {len(sb)}")
            # first divergence point
            for i in range(min(len(sa), len(sb))):
                if sa[i] != sb[i]:
                    print("  at", i, ":", sa[max(0, i-60):i+60])
                    print("  vs ", " ", sb[max(0, i-60):i+60])
                    break
        sys.exit(1)
    print(f"PACK EQUALITY: all {len(a)} structures identical")
