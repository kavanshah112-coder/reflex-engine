# -*- coding: utf-8 -*-
# origin: new for V1.0 (public surface per V1_SPEC §3)
"""Answer / Certificate / Cost — the gateway's public return types."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

CERTIFIED_REFLEX = "CERTIFIED_REFLEX"
LLM_ESCALATED = "LLM_ESCALATED"
ABSTAINED = "ABSTAINED"
STATUSES = (CERTIFIED_REFLEX, LLM_ESCALATED, ABSTAINED)


@dataclass
class Cost:
    """Per-answer resource accounting. Joule fields are populated only
    on metered local runs (V0.5 protocol); API adapters report
    calls/tokens only — never joules (V1_SPEC §0.5)."""
    llm_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    wall_ms: float = 0.0
    gpu_j: Optional[float] = None
    cpu_j: Optional[float] = None


@dataclass
class Certificate:
    """Machine-readable provenance for one answer.

    kind: 'derivation' (certified reflex path), 'escalation' (which LLM
    answered and why the engine escalated), or 'abstention' (which
    integrity condition blocked answering).
    detail: kind-specific trace — facts used (with identity keys and
    statuses), checks passed, plan steps, pack/reflex versions and
    authorship, or the escalation reason chain.
    """
    kind: str
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Answer:
    value: Any
    status: str
    certificate: Certificate
    cost: Cost

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"bad status {self.status!r}")
