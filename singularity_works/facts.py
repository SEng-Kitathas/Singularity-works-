from __future__ import annotations
# complexity_justified: typed fact bus surface
from dataclasses import asdict, dataclass, field
from typing import Any


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


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
