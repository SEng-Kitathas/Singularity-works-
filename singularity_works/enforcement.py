from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from .gates import Gate, GateResult

if TYPE_CHECKING:
    from .facts import FactBus


@dataclass
class GateRunSummary:
    results: list[GateResult] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out = {"pass": 0, "warn": 0, "fail": 0, "residual": 0}
        for r in self.results:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    @property
    def open_residuals(self) -> list[str]:
        vals = []
        for r in self.results:
            vals.extend(r.residual_obligations)
        return list(dict.fromkeys(vals))


class EnforcementEngine:
    def __init__(self) -> None:
        self.gates: list[Gate] = []

    def register(self, gate: Gate) -> None:
        self.gates.append(gate)

    def run(self, subject: dict[str, Any], bus: "FactBus | None" = None) -> GateRunSummary:
        """
        Run all registered gates against subject.
        Passes the FactBus to gates that consume upstream facts.
        Each gate receives the same bus snapshot — gates are not re-ordered
        or re-run within a single enforcement pass (termination discipline).
        """
        summary = GateRunSummary()
        for gate in self.gates:
            summary.results.append(gate.runner(subject, bus))
        return summary
