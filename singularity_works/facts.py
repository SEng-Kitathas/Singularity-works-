from __future__ import annotations
# complexity_justified: typed fact bus surface
from dataclasses import asdict, dataclass, field
from typing import Any


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


@dataclass
class TaintChainPayload:
    source_type: str = "USER_INPUT"
    source_line: int = 0
    boundary_type: str = "UNKNOWN"
    sink_line: int = 0
    hops: int = 1
    directed: bool = True

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrustBoundaryPayload:
    source: str = "unknown"
    boundary_type: str = "UNKNOWN"
    sink_name: str = ""
    sink_line: int = 0
    tainted_input: str | None = None
    directed: bool = False
    source_line: int = 0
    source_type: str = "UNKNOWN"
    hops: int = 0
    structure_id: str = ""
    dangerous_calls: list[str] = field(default_factory=_list)

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Fact:
    fact_id: str
    fact_type: str
    scope: str
    confidence: str = "moderate"
    payload: dict[str, Any] = field(default_factory=_dict)
    evidence_refs: list[str] = field(default_factory=_list)
    linked_laws: list[str] = field(default_factory=_list)
    upstream_facts: list[str] = field(default_factory=_list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_trust_boundary(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: TrustBoundaryPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls(
            fact_id=fact_id,
            fact_type="trust_boundary_crossed",
            scope=scope,
            confidence=confidence,
            payload=payload.to_payload(),
            evidence_refs=evidence_refs or [],
            linked_laws=linked_laws or [],
            upstream_facts=upstream_facts or [],
        )

    @classmethod
    def from_taint_chain(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: TaintChainPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls(
            fact_id=fact_id,
            fact_type="taint_chain",
            scope=scope,
            confidence=confidence,
            payload=payload.to_payload(),
            evidence_refs=evidence_refs or [],
            linked_laws=linked_laws or [],
            upstream_facts=upstream_facts or [],
        )


class FactBus:
    def __init__(self) -> None:
        self.facts: list[Fact] = []
        self._seen: set[str] = set()

    def publish(self, fact: Fact) -> None:
        if fact.fact_id in self._seen:
            return
        self._seen.add(fact.fact_id)
        self.facts.append(fact)

    def by_type(self, fact_type: str) -> list[Fact]:
        return [fact for fact in self.facts if fact.fact_type == fact_type]

    def taint_chains(self) -> list[TaintChainPayload]:
        chains: list[TaintChainPayload] = []
        for fact in self.by_type("taint_chain"):
            payload = fact.payload or {}
            chains.append(
                TaintChainPayload(
                    source_type=payload.get("source_type", "USER_INPUT"),
                    source_line=int(payload.get("source_line", 0) or 0),
                    boundary_type=payload.get("boundary_type", "UNKNOWN"),
                    sink_line=int(payload.get("sink_line", 0) or 0),
                    hops=int(payload.get("hops", 1) or 1),
                    directed=bool(payload.get("directed", True)),
                )
            )
        return chains

    def trust_boundaries(self) -> list[TrustBoundaryPayload]:
        boundaries: list[TrustBoundaryPayload] = []
        for fact in self.by_type("trust_boundary_crossed"):
            payload = fact.payload or {}
            boundaries.append(
                TrustBoundaryPayload(
                    source=payload.get("source", "unknown"),
                    boundary_type=payload.get("boundary_type", "UNKNOWN"),
                    sink_name=payload.get("sink_name", ""),
                    sink_line=int(payload.get("sink_line", 0) or 0),
                    tainted_input=payload.get("tainted_input"),
                    directed=bool(payload.get("directed", False)),
                    source_line=int(payload.get("source_line", 0) or 0),
                    source_type=payload.get("source_type", "UNKNOWN"),
                    hops=int(payload.get("hops", 0) or 0),
                    structure_id=payload.get("structure_id", ""),
                    dangerous_calls=list(payload.get("dangerous_calls", [])),
                )
            )
        return boundaries

    def all_types(self) -> set[str]:
        return {f.fact_type for f in self.facts}

    def has_type(self, fact_type: str) -> bool:
        return any(f.fact_type == fact_type for f in self.facts)

    def compound_present(self, *fact_types: str) -> bool:
        """True if ALL of the given fact types are present on the bus."""
        present = self.all_types()
        return all(t in present for t in fact_types)

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for fact in self.facts:
            counts[fact.fact_type] = counts.get(fact.fact_type, 0) + 1
        return {
            "total": len(self.facts),
            "counts": counts,
            "fact_ids": [fact.fact_id for fact in self.facts],
        }
