from __future__ import annotations

from .models import EvaluationResult


def route(result: EvaluationResult) -> str:
    if result.accepted and not result.unresolved_because:
        return "promote"
    if result.accepted and result.unresolved_because:
        return "hold"
    return "reject"
