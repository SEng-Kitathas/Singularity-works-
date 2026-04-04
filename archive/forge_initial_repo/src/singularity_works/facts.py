from __future__ import annotations

from .models import EvidenceEntry, EvidenceKind


def observed(claim: str, source: str, rationale: str = "", **metadata: object) -> EvidenceEntry:
    return EvidenceEntry(
        kind=EvidenceKind.OBSERVED,
        claim=claim,
        source=source,
        rationale=rationale,
        metadata=dict(metadata),
    )


def inferred(claim: str, source: str, rationale: str = "", **metadata: object) -> EvidenceEntry:
    return EvidenceEntry(
        kind=EvidenceKind.INFERRED,
        claim=claim,
        source=source,
        rationale=rationale,
        metadata=dict(metadata),
    )


def hypothesized(claim: str, source: str, rationale: str = "", **metadata: object) -> EvidenceEntry:
    return EvidenceEntry(
        kind=EvidenceKind.HYPOTHESIZED,
        claim=claim,
        source=source,
        rationale=rationale,
        metadata=dict(metadata),
    )


def unknown(claim: str, source: str, rationale: str = "", **metadata: object) -> EvidenceEntry:
    return EvidenceEntry(
        kind=EvidenceKind.UNKNOWN,
        claim=claim,
        source=source,
        rationale=rationale,
        metadata=dict(metadata),
    )
