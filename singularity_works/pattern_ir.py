from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import asdict, dataclass, field

from .laws import BASELINE_AXIOMS, IMMUTABLE_LAWS
from .verification_hooks import (
    ContractHooks,
    CostHooks,
    EvidenceHooks,
    MonitorHooks,
    PropertyHooks,
    ProtocolHooks,
)


@dataclass
class PatternIR:
    pattern_id: str
    family: str
    radicals: list[str] = field(default_factory=list)
    description: str = ""
    contracts: ContractHooks = field(default_factory=ContractHooks)
    protocol_hooks: ProtocolHooks = field(default_factory=ProtocolHooks)
    property_hooks: PropertyHooks = field(default_factory=PropertyHooks)
    evidence_hooks: EvidenceHooks = field(default_factory=EvidenceHooks)
    cost_hooks: CostHooks = field(default_factory=CostHooks)
    monitor_hooks: MonitorHooks = field(default_factory=MonitorHooks)

    def to_dict(self) -> dict:
        return asdict(self)


def default_pattern_for_requirement(text: str) -> PatternIR:
    low = text.lower()
    radicals: list[str] = []
    family = "generic"
    if any(k in low for k in ["protocol", "state", "transition"]):
        radicals += ["STATE", "TRUST"]
        family = "protocol"
    if any(k in low for k in ["parse", "grammar", "input"]):
        radicals += ["PARSE", "STATE"]
        family = "parser"
    if not radicals:
        radicals = ["TRUST"]
    return PatternIR(
        pattern_id="pattern:auto",
        family=family,
        radicals=sorted(set(radicals)),
        description="Auto-derived starter pattern",
        contracts=ContractHooks(
            requires=["artifact.content_nonempty"],
            invariants=[
                "no_todo_markers",
                "no_fixme_markers",
                "no_placeholder_stubs",
            ],
        ),
        property_hooks=PropertyHooks(properties=["content_present"]),
        protocol_hooks=ProtocolHooks(
            allowed_transitions=["open->read", "open->write", "open->close", "read->close", "write->close"],
            forbidden_transitions=["close->read", "close->write", "close->close"],
            misuse_signatures=["todo_marker", "verify_false", "resource_order_misuse"],
        ),
        evidence_hooks=EvidenceHooks(
            required_gate_families=[
                "static",
                "structural",
                "dynamic",
                "conformance",
            ],
            linked_laws=[
                "LAW_1",
                "LAW_4",
                "LAW_OMEGA",
                "LAW_SIGMA",
            ],
            linked_claims=[
                "law_compliance",
                "qa_self_application",
            ],
        ),
        cost_hooks=CostHooks(
            expected_complexity="linear-ish",
            simplification_candidates=[
                "remove_dead_comments",
                "remove_todo_markers",
            ],
        ),
        monitor_hooks=MonitorHooks(
            monitor_templates=["must_not_contain", "must_contain"]
        ),
    )
