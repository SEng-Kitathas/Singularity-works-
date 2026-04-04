
from __future__ import annotations
from dataclasses import dataclass, field, asdict
@dataclass(frozen=True)
class Fact:
    kind: str
    payload: dict = field(default_factory=dict)
class FactBus:
    def __init__(self): self._facts=[]
    def publish(self, fact: Fact): self._facts.append(fact)
    def as_dicts(self): return [asdict(f) for f in self._facts]
