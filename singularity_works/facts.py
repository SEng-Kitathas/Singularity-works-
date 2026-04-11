from __future__ import annotations
# complexity_justified: typed fact bus surface
from dataclasses import asdict, dataclass, field
from typing import Any


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


def _payload(obj: Any) -> dict[str, Any]:
    return asdict(obj)


def _decode(payload_cls, payload: dict[str, Any] | None):
    return payload_cls(**(payload or {}))


@dataclass
class TaintChainPayload:
    source_type: str = "USER_INPUT"
    source_line: int = 0
    boundary_type: str = "UNKNOWN"
    sink_line: int = 0
    hops: int = 1
    directed: bool = True


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


@dataclass
class CompoundDerivationPayload:
    rule: str = ""
    fact_type: str = ""
    description: str = ""
    injection_families: list[str] = field(default_factory=_list)
    trust_signal: bool = False


@dataclass
class SwitchboardDecisionPayload:
    candidate_id: str = ""
    tier: int = 0
    apply: bool = False
    rationale: str = ""


@dataclass
class PropagationPayload:
    rule_id: str = ""
    fact_type: str = ""
    severity: str = "medium"
    rationale: str = ""
    upstream_types: list[str] = field(default_factory=_list)


@dataclass
class DangerousSinkPayload:
    sink_type: str = "unknown"
    structure_id: str = ""


@dataclass
class ResourceLifecyclePayload:
    violations: list[dict[str, Any]] = field(default_factory=_list)


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
    def _from_payload(
        cls,
        *,
        fact_id: str,
        fact_type: str,
        scope: str,
        confidence: str,
        payload: Any,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls(
            fact_id=fact_id,
            fact_type=fact_type,
            scope=scope,
            confidence=confidence,
            payload=_payload(payload),
            evidence_refs=evidence_refs or [],
            linked_laws=linked_laws or [],
            upstream_facts=upstream_facts or [],
        )

    @classmethod
    def from_switchboard_decision(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: SwitchboardDecisionPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="switchboard_decision",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_propagation(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: PropagationPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type=payload.fact_type,
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_dangerous_sink(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: DangerousSinkPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="dangerous_sink_present",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_resource_lifecycle(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: ResourceLifecyclePayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="resource_lifecycle_incomplete",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

    @classmethod
    def from_compound_derivation(
        cls,
        *,
        fact_id: str,
        scope: str,
        confidence: str,
        payload: CompoundDerivationPayload,
        linked_laws: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> "Fact":
        return cls._from_payload(
            fact_id=fact_id,
            fact_type=payload.fact_type,
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
        )

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
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="trust_boundary_crossed",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
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
        return cls._from_payload(
            fact_id=fact_id,
            fact_type="taint_chain",
            scope=scope,
            confidence=confidence,
            payload=payload,
            linked_laws=linked_laws,
            evidence_refs=evidence_refs,
            upstream_facts=upstream_facts,
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

    def _decode_many(self, fact_type: str, payload_cls):
        return [_decode(payload_cls, fact.payload) for fact in self.by_type(fact_type)]

    def taint_chains(self) -> list[TaintChainPayload]:
        return self._decode_many("taint_chain", TaintChainPayload)

    def trust_boundaries(self) -> list[TrustBoundaryPayload]:
        return self._decode_many("trust_boundary_crossed", TrustBoundaryPayload)

    def compound_derivations(self) -> list[CompoundDerivationPayload]:
        fact_types = {
            "compound_taint_injection",
            "ssrf_confirmed",
            "critical_compound_hazard",
            "memory_corruption_via_taint",
        }
        compounds: list[CompoundDerivationPayload] = []
        for fact in self.facts:
            if fact.fact_type not in fact_types:
                continue
            payload = fact.payload or {}
            compounds.append(
                CompoundDerivationPayload(
                    rule=payload.get("rule", ""),
                    fact_type=fact.fact_type,
                    description=payload.get("description", ""),
                    injection_families=list(payload.get("injection_families", [])),
                    trust_signal=bool(payload.get("trust_signal", False)),
                )
            )
        return compounds

    def propagations(self) -> list[PropagationPayload]:
        fact_types = {
            "trust_sensitive_sink_hazard",
            "sql_injection_confirmed",
            "resource_trust_compound_hazard",
        }
        props: list[PropagationPayload] = []
        for fact in self.facts:
            if fact.fact_type not in fact_types:
                continue
            payload = fact.payload or {}
            props.append(
                PropagationPayload(
                    rule_id=payload.get("rule_id", ""),
                    fact_type=fact.fact_type,
                    severity=payload.get("severity", "medium"),
                    rationale=payload.get("rationale", ""),
                    upstream_types=list(payload.get("upstream_types", [])),
                )
            )
        return props

    def switchboard_decisions(self) -> list[SwitchboardDecisionPayload]:
        return self._decode_many("switchboard_decision", SwitchboardDecisionPayload)

    def dangerous_sinks(self) -> list[DangerousSinkPayload]:
        return self._decode_many("dangerous_sink_present", DangerousSinkPayload)

    def resource_lifecycle_issues(self) -> list[ResourceLifecyclePayload]:
        return self._decode_many("resource_lifecycle_incomplete", ResourceLifecyclePayload)

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
