from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class EvidenceKind(str, Enum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    HYPOTHESIZED = "hypothesized"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class EvidenceEntry:
    kind: EvidenceKind
    claim: str
    source: str
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(slots=True)
class Fingerprint:
    language: str
    digest: str
    tokens: tuple[str, ...]
    normalized_lines: tuple[str, ...]


@dataclass(slots=True)
class IntakeArtifact:
    path: str
    content: str
    language: str
    fingerprint: Fingerprint


@dataclass(slots=True)
class EvaluationResult:
    accepted: bool
    score: float
    accepted_because: list[str] = field(default_factory=list)
    unresolved_because: list[str] = field(default_factory=list)
    operator_brief: list[str] = field(default_factory=list)
    evidence: list[EvidenceEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
