# -*- coding: utf-8 -*-
"""reflex-engine: the V1.0 integrated reflex architecture.

Distillation of the reflex-poc arc V0.1-V0.11 (see V1_SPEC.md).
Public surface: ReflexGateway(llm).ask(query) -> Answer.
"""
from .answer import (ABSTAINED, CERTIFIED_REFLEX, LLM_ESCALATED, Answer,
                     Certificate, Cost)
from .gateway import ReflexGateway

__all__ = ["ReflexGateway", "Answer", "Certificate", "Cost",
           "CERTIFIED_REFLEX", "LLM_ESCALATED", "ABSTAINED"]
__version__ = "1.0.0-p1"
