from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass, field

@dataclass
class ContractHooks:
    requires: list[str] = field(default_factory=list)
    ensures: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)
    forbidden_states: list[str] = field(default_factory=list)

@dataclass
class ProtocolHooks:
    state_model_ref: str = ""
    allowed_transitions: list[str] = field(default_factory=list)
    forbidden_transitions: list[str] = field(default_factory=list)
    misuse_signatures: list[str] = field(default_factory=list)

@dataclass
class PropertyHooks:
    properties: list[str] = field(default_factory=list)
    metamorphic_relations: list[str] = field(default_factory=list)
    differential_expectations: list[str] = field(default_factory=list)

@dataclass
class EvidenceHooks:
    required_gate_families: list[str] = field(default_factory=list)
    required_evidence_types: list[str] = field(default_factory=list)
    linked_requirements: list[str] = field(default_factory=list)
    linked_claims: list[str] = field(default_factory=list)
    linked_laws: list[str] = field(default_factory=list)

@dataclass
class CostHooks:
    expected_complexity: str = ""
    resource_bounds: list[str] = field(default_factory=list)
    simplification_candidates: list[str] = field(default_factory=list)

@dataclass
class MonitorHooks:
    monitor_templates: list[str] = field(default_factory=list)
    required_signals: list[str] = field(default_factory=list)
    severity_mapping: dict[str, str] = field(default_factory=dict)
