# -*- coding: utf-8 -*-
# origin: new for V1.2 — W1.2 vocabulary-completeness audit
"""The anti-seed-luck battery: every resolution table must be fully
reachable by the gate/regex that feeds it. The B2 defect (ORDINALS
knew 'tenth', the reference regex stopped at 'fifth') is the founding
member. Every entry here is machine-checked; a table item no gate can
reach FAILS the audit."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "reflex" / "_arc"))

from reflex.packs import loader                       # noqa: E402
loader.apply(HERE / "packs" / "physics")
import v10.nlpw10 as W                                # noqa: E402
import v11.semparse11 as SP                           # noqa: E402
import v11.semstate11 as SS                           # noqa: E402


def check(name, missing, findings):
    status = "OK " if not missing else "GAP"
    print(f"  [{status}] {name}: "
          f"{'complete' if not missing else sorted(missing)[:8]}")
    if missing:
        findings.append((name, sorted(missing)))


def main():
    findings = []

    # 1. ORDINALS table vs the reference regex (the B2 audit)
    probe_noun = "tank"
    missing = {w for w in SS.ORDINALS
               if w != "last" and not SP.REF_RE.search(
                   f"the {w} {probe_noun}")}
    check("ORDINALS reachable by REF_RE", missing, findings)

    # 2. COMPARATIVES table vs the reference regex
    missing = {w for w in SS.COMPARATIVES
               if not SP.REF_RE.search(f"the {w} {probe_noun}")}
    check("COMPARATIVES reachable by REF_RE", missing, findings)

    # 3. role-cue lexicons: every cue regex must match its own
    #    canonical phrases (self-consistency of CUES)
    missing = {k for k, rx in W.CUE_RE.items()
               if not rx.search({"historical": "it was",
                                 "hypothetical": "if it were",
                                 "example": "for example",
                                 "negated": "it is not",
                                 "future": "it will",
                                 "spec_rating": "rated at"}[k])}
    check("CUE_RE self-consistency", missing, findings)

    # 4. unit index keys capturable by the unit-capture path:
    #    for every single-token unit key, _unit_after must capture it
    #    after a number
    from reflex.engine_patches import AUDIT_DEAD_UNIT_KEYS
    missing = set()
    for u in W._UNIT_IDX:
        if "/" in u or " " in u or "^" in u:
            continue        # compound forms have their own capture
        if u in AUDIT_DEAD_UNIT_KEYS:
            continue        # documented exceptions (single letters:
            #                 capture would be an ambiguity hazard)
        got = W._unit_after(f"5 {u} more", 1)
        if got.strip().lower().rstrip(".,;:!?") != u:
            missing.add(u)
    check("unit-index keys capturable by _unit_after", missing,
          findings)

    # 5. pack entity nouns vs ENT_RE ("<Noun> A" must match)
    lex = __import__("json").loads(
        (HERE / "packs/physics/lexicon.json").read_text(
            encoding="utf-8"))
    missing = {n for n in lex["entity_nouns"]
               if not SP.ENT_RE.search(f"{n.capitalize()} A")}
    check("pack entity nouns reachable by ENT_RE", missing,
          findings)

    # 6. target_verbs keys must be single lowercase tokens the
    #    retry's tokenizer can produce
    tok = re.compile(r"^[a-z_]+$")
    missing = {k for k in loader.TARGET_VERBS
               if not tok.match(k)}
    check("target_verbs tokenizable", missing, findings)

    print(f"AUDIT: {len(findings)} gap(s)")
    return findings


if __name__ == "__main__":
    f = main()
    sys.exit(1 if f else 0)
