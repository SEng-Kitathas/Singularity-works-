from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .evidence_ledger import EvidenceLedger


@dataclass(slots=True)
class ForgeContext:
    workspace: Path
    run_id: str
    evidence_path: Path = field(init=False)
    evidence_ledger: EvidenceLedger = field(init=False)

    def __post_init__(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.evidence_path = self.workspace / f"{self.run_id}.evidence.jsonl"
        self.evidence_ledger = EvidenceLedger(self.evidence_path)
