# -*- coding: utf-8 -*-
# origin: new for V1.8 -- role-aware plan reuse (SPEC 4 steps 1-5)
"""A TEMPLATE is a certified plan whose stated-number literals were
replaced by role markers at harvest:

    "$s<step>|<cue>|<ordinal>"            in a keyed slot
    "{$s<step>|<cue>|<ordinal>}"          inside an expression string

and whose donor question's SKELETON (roles18.skeleton_of) is the
lookup key. No regex over numbers exists anywhere in this path.

serve(text, library, ...) ->
    (value, cert, info) with info["path"] = "bind:<template>" on a
    serve, or (None, None, info) with info["reason"] one of
      no_skeleton   unresolved   unbound_slot   expr_count
      collision     donor_self   gate:<G>       exec_refused
Every bound plan passes the FULL gate (plangate18: G-P1..4 + G-P4')
and chainexec17 (per-step + end witness) exactly as a fresh plan
would (SPEC 4 step 5). Reuse saves structure-finding, never
certification.
"""
import json
import re

from . import chainexec17, plangate18
from . import roles18 as R

_MARK = re.compile(r"^\$s(\d+)\|([^|]+)\|(\d+)$")
_EMARK = re.compile(r"\{\$s(\d+)\|([^|]+)\|(\d+)\}")


class Library(object):
    def __init__(self, templates):
        self.templates = templates
        self.by_skel = {}
        for t in templates:
            for sk in t.get("skeletons") or [t.get("skeleton")]:
                self.by_skel.setdefault(sk, []).append(t)
        self.donors = set()
        for t in templates:
            self.donors.update(t.get("donors", []))

    @classmethod
    def load(cls, paths):
        tpls = []
        for p in paths:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            tpls.extend(d["templates"] if isinstance(d, dict) else d)
        return cls(tpls)

    def __len__(self):
        return len(self.templates)


def _fmt(tok):
    return tok.raw


def bind(template, roles):
    """-> (plan, None) or (None, reason)"""
    if roles.bare():
        return None, "unresolved"
    nodes = []
    for n in template["plan"]["nodes"]:
        nd = {}
        for k, v in n.items():
            if isinstance(v, str):
                m = _MARK.match(v)
                if m:
                    tok = roles.find(int(m.group(1)), m.group(2),
                                     int(m.group(3)))
                    if tok is None:
                        return None, "unbound_slot"
                    nd[k] = float(tok.raw)
                    continue
                if "{$s" in v:
                    missing = []

                    def rep(mm):
                        tok = roles.find(int(mm.group(1)), mm.group(2),
                                         int(mm.group(3)))
                        if tok is None:
                            missing.append(1)
                            return ""
                        return tok.raw
                    s = _EMARK.sub(rep, v)
                    if missing:
                        return None, "unbound_slot"
                    nd[k] = s
                    continue
            nd[k] = v
        nodes.append(nd)
    return {"nodes": nodes, "final": template["plan"]["final"]}, None


def serve(text, library, qid=None, roles=None, exclude_donors=True):
    roles = roles or R.analyze(text)
    info = {"reason": None, "path": None, "template": None}
    cands = library.by_skel.get(roles.skeleton)
    if not cands:
        info["reason"] = "no_skeleton"
        return None, None, info
    if exclude_donors and qid is not None and qid in library.donors:
        # never serve a template on a question that donated it
        if any(qid in t.get("donors", []) for t in cands):
            info["reason"] = "donor_self"
            return None, None, info
    bound = []
    reason = None
    for t in cands:
        plan, why = bind(t, roles)
        if plan is None:
            reason = reason or why
            continue
        bound.append((t, plan))
    if not bound:
        info["reason"] = reason or "unbound_slot"
        return None, None, info
    # multiplicity rule: identical bound plans agree; differing ones
    # abstain -- no ranking heuristic (R8)
    keys = {json.dumps(p, sort_keys=True) for _t, p in bound}
    if len(keys) > 1:
        info["reason"] = "collision"
        info["collision_n"] = len(keys)
        return None, None, info
    t, plan = bound[0]
    ok, transcript = plangate18.check(plan, text, roles)
    if not ok:
        info["reason"] = "gate:" + (transcript[-1].get("gate") or "?")
        info["kill"] = transcript[-1].get("kill")
        return None, None, info
    v, cert = chainexec17.run(plan)
    if v is None:
        info["reason"] = "exec_refused"
        info["kill"] = cert.get("why") if isinstance(cert, dict) else None
        return None, None, info
    info["path"] = "bind:%s" % t.get("name")
    info["template"] = t.get("name")
    cert = dict(cert)
    cert["template"] = t.get("name")
    cert["gate"] = transcript
    return v, cert, info
