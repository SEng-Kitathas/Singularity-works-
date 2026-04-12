from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .facts import FactBus

GateRunner = Callable[[dict[str, Any], "FactBus | None"], "GateResult"]


@dataclass
class GateFinding:
    code: str
    message: str
    severity: str = "medium"
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    gate_id: str
    gate_family: str
    status: str
    findings: list[GateFinding] = field(default_factory=list)
    discharged_claims: list[str] = field(default_factory=list)
    residual_obligations: list[str] = field(default_factory=list)


@dataclass
class Gate:
    gate_id: str
    gate_family: str
    description: str
    runner: GateRunner


