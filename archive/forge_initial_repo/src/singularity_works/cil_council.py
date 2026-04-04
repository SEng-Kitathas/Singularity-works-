from __future__ import annotations

from .models import EvaluationResult


def should_promote(result: EvaluationResult) -> bool:
    return result.accepted and not result.unresolved_because and result.score >= 0.9


def operator_brief(result: EvaluationResult) -> list[str]:
    lines = []
    lines.append("accepted" if result.accepted else "rejected")
    lines.extend(f"accepted_because: {item}" for item in result.accepted_because)
    lines.extend(f"unresolved_because: {item}" for item in result.unresolved_because)
    return lines
