from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FractalStage(StrEnum):
    PROBE = "PROBE"
    DERIVE = "DERIVE"
    VERIFY = "VERIFY"
    EMBODY = "EMBODY"
    RECURSE = "RECURSE"


@dataclass
class FractalEvent:
    stage: FractalStage
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FractalCycle:
    cycle_id: str
    events: list[FractalEvent] = field(default_factory=list)

    def mark(self, stage: FractalStage, status: str, **details: Any) -> None:
        self.events.append(FractalEvent(stage=stage, status=status, details=details))

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "events": [
                {
                    "stage": event.stage.value,
                    "status": event.status,
                    "details": event.details,
                }
                for event in self.events
            ],
        }
