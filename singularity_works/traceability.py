from __future__ import annotations
from dataclasses import dataclass, field, asdict

@dataclass
class TraceLink:
    source_id: str
    target_id: str
    link_type: str
    confidence: str = 'moderate'
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

class TraceabilityIndex:
    def __init__(self) -> None:
        self.links: list[TraceLink] = []

    def add(self, link: TraceLink) -> None:
        self.links.append(link)

    def by_source(self, source_id: str) -> list[TraceLink]:
        return [x for x in self.links if x.source_id == source_id]

    def by_target(self, target_id: str) -> list[TraceLink]:
        return [x for x in self.links if x.target_id == target_id]
