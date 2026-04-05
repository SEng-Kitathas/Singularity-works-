from __future__ import annotations
# complexity_justified: declarative datamodel surface
from dataclasses import dataclass, field
from typing import Any


def _list() -> list:
    return []


def _dict() -> dict:
    return {}


@dataclass
class Requirement:
    requirement_id: str
    text: str
    source_ref: str = ""
    priority: str = "normal"
    tags: list[str] = field(default_factory=_list)


@dataclass
class Artifact:
    artifact_id: str
    artifact_type: str
    content: str
    origin: str = ""
    version: str = "1.2.0"
    family: str = "generic"
    radicals: list[str] = field(default_factory=_list)
    metadata: dict[str, Any] = field(default_factory=_dict)


@dataclass
class MonitorSeed:
    monitor_id: str
    requirement_id: str
    kind: str
    expression: str
    severity: str = "medium"
    required_signals: list[str] = field(default_factory=_list)
    claim_id: str = ""
    confidence: str = "moderate"


@dataclass
class RecoveryArtifact:
    structure_id: str
    structure_type: str
    confidence: str = "moderate"
    supports_requirements: list[str] = field(default_factory=_list)
    supports_radicals: list[str] = field(default_factory=_list)
    payload: dict[str, Any] = field(default_factory=_dict)


@dataclass
class Risk:
    risk_id: str
    description: str
    severity: str = "medium"
    status: str = "open"
    linked_requirements: list[str] = field(default_factory=_list)
    linked_artifacts: list[str] = field(default_factory=_list)
    linked_claims: list[str] = field(default_factory=_list)


@dataclass
class AssuranceClaim:
    claim_id: str
    claim_text: str
    status: str = "residual"
    claim_type: str = "generic"
    confidence: str = "moderate"
    supported_by: list[str] = field(default_factory=_list)
    monitored_by: list[str] = field(default_factory=_list)
    residual_risks: list[str] = field(default_factory=_list)
    assumptions: list[str] = field(default_factory=_list)
    responsibility_boundary: str = "software"
    evidence_refs: list[str] = field(default_factory=_list)
    parent_claim_id: str = ""
    child_claim_ids: list[str] = field(default_factory=_list)
    # Warrant: semantic reason WHY this evidence constitutes support for the claim.
    # Without a warrant, confidence inflation is possible — gates can discharge
    # claims without actually verifying the relevant invariant.
    # Format: "[gate/monitor_id] verifies [invariant] required by [claim]"
    # Empty warrant = legacy/shallow claim (still counted but flagged in audit)
    warrant: str = ""


@dataclass
class SimplificationSuggestion:
    suggestion_id: str
    summary: str
    rationale: str
    expected_gain: str = "medium"
    confidence: str = "moderate"
    rewrite_candidate: str = ""
    target_spans: list[list[int]] = field(default_factory=_list)
    safety_level: str = "review_required"
    auto_apply: bool = False
    linked_laws: list[str] = field(default_factory=_list)


@dataclass
class RunContext:
    session_id: str
    mode: str = "run"
    project_tag: str = "default"
    metadata: dict[str, Any] = field(default_factory=_dict)

@dataclass
class TransformationCandidate:
    candidate_id: str
    summary: str
    rationale: str
    rewrite_candidate: str = ""
    target_spans: list[list[int]] = field(default_factory=_list)
    source_gate: str = ""
    confidence: str = "moderate"
    safety_level: str = "review_required"
    auto_apply: bool = False
    linked_laws: list[str] = field(default_factory=_list)
    transformation_axiom: str = ""
