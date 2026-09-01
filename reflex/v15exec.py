# -*- coding: utf-8 -*-
# origin: new for V1.5 -- deterministic path + execution over the packet
"""Turns an indexed packet into an answer, or declines.

This is the step that decides V1.5's economics. By the plan's energy
identity the saving is essentially equal to the fraction of queries
answered here with no model call, so every abstention below is a query
that costs a full LLM call and every wrong answer is worse than an
abstention twice over.

The regime it handles is the one real word problems actually live in:
a running quantity changed by events, and a question about the total,
the remainder, or a rate. That is not the physics-capability regime
`planner10` was built for -- there the path is a chain of typed
formulas over dimensioned kinds, and goal regression is the right
machinery. Here the "path" is the story's own event order, which the
substrate already carries, so execution walks it directly.

Refusal is the default. A story whose events do not compose into a
single running quantity, or whose question does not name something the
events produce, is declined rather than guessed at.
"""
import re

from . import relations as REL

NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")

TOTAL_ASK = re.compile(
    r"\b(in all|altogether|all together|in total|total|combined|"
    r"how many .* (?:does|do|did) .* have|sum)\b", re.I)
REMAIN_ASK = re.compile(
    r"\b(left|remain|remaining|still|leftover|have now|has now)\b", re.I)
# Language that means the quantities compose by rate or partition
# rather than by running sum. Its presence disqualifies the linear walk.
GROUPING = re.compile(
    r"\b(each|per|every|apiece|a piece|packages? of|boxes? of|"
    r"bags? of|sets? of|dozen|times as|divided|shared|split)\b", re.I)

OPTIMISATION = re.compile(
    r"\b(greatest|largest|biggest|maximum|most|smallest|least|"
    r"minimum|fewest|at most|at least|as many as possible)\b", re.I)

DIFF_ASK = re.compile(
    r"\b(how many more|how many fewer|how much more|how much less|"
    r"difference)\b", re.I)


def _num_in(text):
    m = NUM.findall((text or "").replace(",", ""))
    try:
        return float(m[0]) if m else None
    except ValueError:
        return None


def solve(state, packet):
    """-> (value, trace). value is None for an abstention.

    The engine computes every number. Nothing a producer wrote is
    returned as an answer, and a state that cannot be walked returns
    None rather than a plausible figure.
    """
    nodes = sorted(
        [n for n in state.nodes.values()
         if isinstance(n.get("content"), (int, float))],
        key=lambda n: (n.get("order") if n.get("order") is not None
                       else 0, n["id"]))
    if not nodes:
        return None, {"why": "no numeric nodes"}

    rels = {r.get("order"): r for r in state.relations.values()}
    ask = ((packet.get("target") or {}).get("span") or "")

    # OPTIMISATION / NUMBER-THEORY GUARD. A superlative in the ask
    # means the answer is the extremum of a search, not the endpoint of
    # a walk:
    #
    #   "45 heart stickers and 27 star stickers ... no stickers left
    #    over, what is the GREATEST number of pages?"
    #        walked to 72     gold 9   (gcd(45, 27))
    #
    # The mode detector had matched "left over" and run a subtraction.
    # This is V1.3's D10 class exactly -- GCD and LCM are not
    # expressible in this operator set -- and the honest response to an
    # inexpressible problem is to decline it, not to return whatever
    # the available operators produce.
    if OPTIMISATION.search(ask):
        return None, {"why": "superlative ask: an extremum, not a walk",
                      "ask": ask[:60]}

    # Which arithmetic the question is asking for. A question that
    # names none of these is not answered.
    if DIFF_ASK.search(ask):
        mode = "difference"
    elif REMAIN_ASK.search(ask):
        mode = "remainder"
    elif TOTAL_ASK.search(ask):
        mode = "total"
    else:
        return None, {"why": "ask names no supported operation",
                      "ask": ask[:60]}

    # Walk the story in event order, one running quantity.
    trace = []
    running = None
    for n in nodes:
        v = float(n["content"])
        o = n.get("order")
        r = rels.get(o)
        kind = (r or {}).get("relation_kind")
        span = (r or {}).get("span") or n.get("span") or ""
        op = None
        if kind == "transfer":
            op = "sub"                      # the subject loses it
        elif kind == "acquisition":
            op = "add"
        elif kind in ("possession", None, "undirected"):
            out = REL.resolve(span)
            op = out.op if out.status == REL.RESOLVED else None

        if running is None:
            running = v
            trace.append({"start": v, "node": n["id"]})
            continue

        # NO DEFAULT OPERATOR. The first version of this loop assumed
        # `add` whenever the question asked for a total and no operator
        # had been established, which is right for a plain aggregation
        # and wrong for everything else. It produced 7 wrong answers in
        # 16 served on the dev split -- a 43.75% wrong-fire:
        #
        #   "Jake has six fewer peaches than Steven. Steven has 13."
        #        6 + 13 = 19        gold 7
        #   "Steve gave him 16 more. Now Todd has 54 pieces."
        #        16 + 54 = 70       gold 38   (a reverse problem)
        #   "7 flowers each representing 70..."
        #        7 + 77 = 84        gold 490  (a rate, not a sum)
        #
        # Every one is a story whose arithmetic the engine had not
        # established and assumed. An assumed operator is an assumed
        # reading, and this arc's whole position is that an unproven
        # reading abstains.
        if op is None:
            return None, {"why": "no operator established for event",
                          "node": n["id"], "span": span[:60]}
        if op == "add":
            running += v
        elif op == "sub":
            running -= v
        elif op == "mul":
            running *= v
        elif op == "div":
            if v == 0:
                return None, {"why": "division by zero"}
            running /= v
        else:
            return None, {"why": "unsupported operator", "op": op}
        trace.append({"op": op, "operand": v, "node": n["id"],
                      "running": running})

    if mode == "difference" and len(nodes) == 2:
        running = abs(float(nodes[0]["content"])
                      - float(nodes[1]["content"]))
        trace.append({"op": "difference", "value": running})

    # SHAPE GUARD. Establishing an operator per event is not enough --
    # the linear walk must also be the right MODEL for the story, and
    # the first version assumed it always was. Rate and grouping
    # language means the quantities compose multiplicatively or by
    # partition, not by running sum:
    #
    #   "7 flowers EACH representing 7 colours ... 70 bouquets"
    #        walked to 84          gold 490   (7 x 70)
    #   "45 heart stickers and 27 star stickers ... "
    #        walked to 72          gold 9     (a partition)
    #   "Candies come in PACKAGES OF 4. Shirley ate 10."
    #        walked to -6          gold 2     (packaging)
    #
    # The engine can see the marker and cannot see the composition, so
    # it declines. This costs coverage on every rate problem, including
    # the ones a running sum would have got right by luck.
    if GROUPING.search(state.source or ""):
        return None, {"why": "rate/grouping language: linear walk is "
                             "not the story's shape"}

    # A count cannot be negative. Reaching one means the walk composed
    # the events in an order the story does not support.
    if running is not None and running < 0:
        return None, {"why": "negative running quantity",
                      "value": running}

    if running is None:
        return None, {"why": "nothing to return"}
    if len(trace) < 2:
        # A single given, restated. V1.4's B22 -- the answer must be
        # DERIVED, never the question's own input handed back.
        return None, {"why": "degenerate: no derivation performed"}
    return running, {"mode": mode, "steps": trace}
