from __future__ import annotations
# complexity_justified: switchboard derivation engine over FactBus
# Phase 1: DERIVE — propagation rules compose compound facts from antecedents.
# Phase 2: ROUTE  — autonomy tiering routes transformation candidates.
# Isomorphism: blackboard system + forward-chaining rule engine.
# Each compound fact is traceable to its upstream evidence.

from dataclasses import dataclass, field
from typing import Any

from .facts import Fact, FactBus, PropagationPayload
from .models import TransformationCandidate


TIER_REFUSE = 0
TIER_ESCALATE = 1
TIER_SUGGEST = 3
TIER_AUTO = 4

_CONFIDENCE_RANK: dict[str, int] = {
    "high": 4, "moderate": 3, "low": 2, "speculative": 1,
}
_SAFETY_AUTO: frozenset[str] = frozenset({"safe", "high_confidence_safe"})


@dataclass
class PropagationRule:
    rule_id: str
    antecedents: list[str]
    output_type: str
    severity: str
    rationale: str
    confidence: str = "high"
    linked_laws: list[str] = field(default_factory=list)


# Derivation axioms: where multiple signals compose into emergent danger.
_RULES: list[PropagationRule] = [
    PropagationRule(
        rule_id="trust_and_dangerous_sink",
        antecedents=["trust_boundary_crossed", "dangerous_sink_present"],
        output_type="trust_sensitive_sink_hazard",
        severity="critical",
        rationale="Trust boundary crossed AND dangerous sink present — compound hazard.",
        linked_laws=["LAW_4", "LAW_OMEGA"],
    ),
    PropagationRule(
        rule_id="db_sink_and_tainted_query",
        antecedents=["trust_boundary_crossed", "query_construction_tainted"],
        output_type="sql_injection_confirmed",
        severity="critical",
        rationale="Trust boundary AND tainted query construction — SQL injection confirmed.",
        linked_laws=["LAW_4", "LAW_OMEGA"],
    ),
    PropagationRule(
        rule_id="resource_and_trust_compound",
        antecedents=["dangerous_sink_present", "resource_lifecycle_incomplete"],
        output_type="resource_trust_compound_hazard",
        severity="high",
        rationale="Dangerous sink AND incomplete resource lifecycle — compound surface.",
        linked_laws=["LAW_4"],
    ),
]


@dataclass
class SwitchboardDecision:
    candidate_id: str
    tier: int
    apply: bool
    rationale: str
    upstream_fact_ids: list[str] = field(default_factory=list)

    def fact_payload(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "tier": self.tier,
            "apply": self.apply,
            "rationale": self.rationale,
        }


@dataclass
class DerivedFinding:
    rule_id: str
    output_type: str
    severity: str
    rationale: str
    upstream_types: list[str]
    confidence: str = "high"


class Switchboard:
    """
    Derivation engine + autonomy router.
    derive() runs propagation rules → emits compound facts.
    route() routes transformation candidates under the autonomy matrix.
    """

    def derive(self, bus: FactBus) -> list[DerivedFinding]:
        """
        Run propagation rules. Emits compound facts for satisfied antecedents.
        Returns list of derived findings.
        """
        derived: list[DerivedFinding] = []
        already = bus.all_types()
        for rule in _RULES:
            if rule.output_type in already:
                continue
            if not all(bus.has_type(ant) for ant in rule.antecedents):
                continue
            upstream = [
                f.fact_id
                for t in rule.antecedents
                for f in bus.by_type(t)
            ]
            scope = upstream[0].split(":")[0] if upstream else "switchboard"
            bus.publish(Fact.from_propagation(
                fact_id=f"{scope}:{rule.output_type}:derived",
                scope=scope,
                confidence=rule.confidence,
                payload=PropagationPayload(
                    rule_id=rule.rule_id,
                    fact_type=rule.output_type,
                    severity=rule.severity,
                    rationale=rule.rationale,
                    upstream_types=rule.antecedents,
                ),
                upstream_facts=upstream,
                linked_laws=rule.linked_laws,
            ))
            derived.append(DerivedFinding(
                rule_id=rule.rule_id,
                output_type=rule.output_type,
                severity=rule.severity,
                rationale=rule.rationale,
                upstream_types=rule.antecedents,
                confidence=rule.confidence,
            ))
        return derived

    def route(self, bus: FactBus) -> list[SwitchboardDecision]:
        """
        Phase 1 derive, Phase 2 route. Returns routing decisions.
        """
        self.derive(bus)
        candidates = bus.by_type("transformation_candidate")
        already_decided: set[str] = {
            f.payload.get("candidate_id", "")
            for f in bus.by_type("switchboard_decision")
        }
        decisions: list[SwitchboardDecision] = []
        for fact in candidates:
            cid = fact.payload.get("candidate_id", fact.fact_id)
            if cid in already_decided:
                continue
            candidate = _candidate_from_fact(fact)
            tier, rationale = _tier_for(candidate, bus)
            decision = SwitchboardDecision(
                candidate_id=cid,
                tier=tier,
                apply=(tier >= TIER_AUTO),
                rationale=rationale,
                upstream_fact_ids=[fact.fact_id],
            )
            decisions.append(decision)
            bus.publish(Fact(
                fact_id=f"{fact.scope}:switchboard_decision:{cid}",
                fact_type="switchboard_decision",
                scope=fact.scope,
                confidence=fact.confidence,
                payload=decision.fact_payload(),
                evidence_refs=fact.evidence_refs,
                linked_laws=fact.linked_laws,
                upstream_facts=[fact.fact_id],
            ))
        return decisions

    def auto_apply_candidates(self, bus: FactBus) -> list[str]:
        return [
            f.payload["candidate_id"]
            for f in bus.by_type("switchboard_decision")
            if f.payload.get("apply", False)
        ]


def _tier_for(candidate: TransformationCandidate, bus: FactBus) -> tuple[int, str]:
    conf_rank = _CONFIDENCE_RANK.get(candidate.confidence, 0)
    safety_ok = candidate.safety_level in _SAFETY_AUTO
    auto_flagged = candidate.auto_apply

    propagations = bus.propagations() if hasattr(bus, "propagations") else []
    propagation_types = {p.fact_type for p in propagations}
    if {"trust_sensitive_sink_hazard", "sql_injection_confirmed"} & propagation_types:
        if "trust" in candidate.source_gate.lower() or "dangerous" in candidate.rationale.lower():
            return TIER_ESCALATE, "compound hazard derived — escalate to human review"

    if conf_rank >= _CONFIDENCE_RANK["moderate"] and safety_ok and auto_flagged:
        return TIER_AUTO, "confidence≥moderate + safety=safe + auto_apply=true → auto-remediate"
    if conf_rank >= _CONFIDENCE_RANK["moderate"] and safety_ok:
        return TIER_SUGGEST, "confidence≥moderate + safety=safe but auto_apply=false → suggest"
    if conf_rank >= _CONFIDENCE_RANK["low"] and safety_ok:
        return TIER_ESCALATE, "confidence=low + safety=safe → escalate for review"
    return TIER_REFUSE, "insufficient confidence or unsafe transformation → refuse"


def _candidate_from_fact(fact: Fact) -> TransformationCandidate:
    p = fact.payload
    return TransformationCandidate(
        candidate_id=p.get("candidate_id", fact.fact_id),
        summary=p.get("summary", ""),
        rationale=p.get("rationale", ""),
        rewrite_candidate=p.get("rewrite_candidate", ""),
        target_spans=p.get("target_spans", []),
        source_gate=p.get("source_gate", ""),
        confidence=p.get("confidence", fact.confidence),
        safety_level=p.get("safety_level", "review_required"),
        auto_apply=bool(p.get("auto_apply", False)),
        linked_laws=p.get("linked_laws", fact.linked_laws),
    )
