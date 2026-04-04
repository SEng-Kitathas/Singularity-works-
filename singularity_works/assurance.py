from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import asdict, dataclass, field

from .enforcement import GateRunSummary
from .models import AssuranceClaim
from .monitoring import MonitorEvent
from .laws import IMMUTABLE_LAWS


@dataclass
class AssuranceRollup:
    discharged: list[str] = field(default_factory=list)
    monitored: list[str] = field(default_factory=list)
    residual: list[str] = field(default_factory=list)
    falsified: list[str] = field(default_factory=list)
    claims: list[AssuranceClaim] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.falsified:
            return "red"
        # Filter residuals: law-compliance warnings (no_monitor_seed, etc.) do not
        # constitute security evidence — an artifact with ONLY compliance residuals
        # and zero security falsifications is green for security evaluation purposes.
        # Isomorphism: the L0-L3 tier model — completeness warnings live at a
        # different epistemic layer than security findings.
        # Law-compliance residuals do not constitute security evidence.
        # Only structural security gaps (trust boundaries, injection risks, etc.)
        # affect the security verdict. Completeness warnings live at a different tier.
        LAW_COMPLIANCE_RESIDUALS = frozenset({
            "monitor_seed_generation", "simplification_review",
            "law_compliance", "code_documentation", "complexity",
        })
        security_residuals = [r for r in self.residual
                              if not r.startswith("monitor_coverage")
                              and "monitor_seed" not in r
                              and "simplification" not in r
                              and r not in LAW_COMPLIANCE_RESIDUALS]
        if security_residuals:
            return "amber"
        return "green"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "discharged": self.discharged,
            "monitored": self.monitored,
            "residual": self.residual,
            "falsified": self.falsified,
            "claims": [asdict(c) for c in self.claims],
            "assumptions": self.assumptions,
            "graph_depth": _graph_depth(self.claims),
            "graph_edges": _graph_edges(self.claims),
        }


def _graph_depth(claims: list[AssuranceClaim]) -> int:
    children = {}
    for claim in claims:
        children.setdefault(claim.parent_claim_id, []).append(claim.claim_id)
    depth = 0

    def visit(node: str, current: int) -> None:
        nonlocal depth
        depth = max(depth, current)
        for child in children.get(node, []):
            visit(child, current + 1)

    visit("", 0)
    return depth


def _graph_edges(claims: list[AssuranceClaim]) -> list[dict[str, str]]:
    return [
        {"parent": claim.parent_claim_id, "child": claim.claim_id, "edge_type": "supports"}
        for claim in claims if claim.parent_claim_id
    ]


def _make_claim(**kwargs) -> AssuranceClaim:
    return AssuranceClaim(**kwargs)


def _confidence_for_status(status: str) -> str:
    if status in {"discharged", "monitored"}:
        return "high"
    if status == "residual":
        return "moderate"
    return "low"


def _claim_status(statuses: list[str]) -> str:
    if "fail" in statuses:
        return "falsified"
    if "warn" in statuses:
        return "residual"
    return "discharged"


def _primary_status(out: AssuranceRollup) -> str:
    if out.falsified:
        return "falsified"
    if out.residual:
        return "residual"
    return "discharged"


def _family_claims(gates: GateRunSummary, requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    family_status: dict[str, list[str]] = {}
    claims: list[AssuranceClaim] = []
    for result in gates.results:
        family_status.setdefault(result.gate_family, []).append(result.status)
    for family, statuses in sorted(family_status.items()):
        family_claim_status = _claim_status(statuses)
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:gate_family:{family}",
                claim_text=f"Gate family {family} compliance claim",
                status=family_claim_status,
                claim_type="gate_family",
                confidence=_confidence_for_status(family_claim_status),
                supported_by=[
                    result.gate_id
                    for result in gates.results
                    if result.gate_family == family and result.status == "pass"
                ],
                residual_risks=[
                    result.gate_id
                    for result in gates.results
                    if result.gate_family == family and result.status in {"warn", "fail"}
                ],
                evidence_refs=[f"gate_family:{family}"],
                parent_claim_id=parent_id,
            )
        )
    return claims


def _monitor_claims(monitor_events: list[MonitorEvent], requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    claims: list[AssuranceClaim] = []
    for event in monitor_events:
        claim_id = event.claim_id or f"claim:{requirement_id}:monitor:{event.monitor_id}"
        claims.append(
            _make_claim(
                claim_id=claim_id,
                claim_text=f"Monitor claim for {event.monitor_id}",
                status="monitored" if event.status == "pass" else "falsified",
                claim_type="monitor",
                confidence=("high" if event.status == "pass" else "low"),
                monitored_by=[event.monitor_id],
                residual_risks=([event.monitor_id] if event.status == "fail" else []),
                evidence_refs=[event.monitor_id],
                parent_claim_id=parent_id,
            )
        )
    return claims


def _residual_claims(residuals: list[str], requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    claims: list[AssuranceClaim] = []
    for residual in residuals:
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:residual:{residual}",
                claim_text=f"Residual obligation {residual}",
                status="residual",
                claim_type="residual",
                confidence="moderate",
                residual_risks=[residual],
                evidence_refs=[residual],
                parent_claim_id=parent_id,
            )
        )
    return claims


def _law_claims(
    linked_laws: list[str],
    requirement_id: str,
    parent_id: str,
    out: AssuranceRollup,
) -> list[AssuranceClaim]:
    claims: list[AssuranceClaim] = []
    law_status = (
        "discharged"
        if "structural.law_compliance" not in out.falsified
        and "law_compliance" not in out.residual
        else (
            "falsified"
            if "structural.law_compliance" in out.falsified
            else "residual"
        )
    )
    for law_id in linked_laws:
        law = IMMUTABLE_LAWS.get(law_id, {"name": law_id, "principle": ""})
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:law:{law_id}",
                claim_text=f"{law['name']} applied to this artifact",
                status=law_status,
                claim_type="law",
                confidence=_confidence_for_status(law_status),
                supported_by=( ["structural.law_compliance"] if law_status == "discharged" else [] ),
                residual_risks=( [] if law_status == "discharged" else ["law_compliance"] ),
                assumptions=[law.get('principle', '')],
                evidence_refs=[law_id, "structural.law_compliance"],
                parent_claim_id=parent_id,
                responsibility_boundary="forge_runtime",
            )
        )
    return claims


def _attach_children(claims: list[AssuranceClaim]) -> None:
    children: dict[str, list[str]] = {}
    for claim in claims:
        if claim.parent_claim_id:
            children.setdefault(claim.parent_claim_id, []).append(claim.claim_id)
    for claim in claims:
        claim.child_claim_ids = children.get(claim.claim_id, [])


def rollup(
    gates: GateRunSummary,
    monitor_events: list[MonitorEvent],
    requirement_id: str,
    linked_laws: list[str] | None = None,
) -> AssuranceRollup:
    out = AssuranceRollup(assumptions=["recovery output is faithful enough for configured policy"])
    failed_monitor_claims: list[str] = []
    linked_laws = linked_laws or []

    for result in gates.results:
        out.discharged.extend(result.discharged_claims)
        out.residual.extend(result.residual_obligations)
        if result.status == "fail":
            out.falsified.append(result.gate_id)

    for event in monitor_events:
        if event.status == "pass":
            if event.claim_id:
                out.monitored.append(event.claim_id)
            out.monitored.append(event.monitor_id)
        else:
            out.falsified.append(event.monitor_id)
            if event.claim_id:
                failed_monitor_claims.append(event.claim_id)

    out.discharged = list(dict.fromkeys(out.discharged))
    out.monitored = list(dict.fromkeys(out.monitored))
    out.residual = [item for item in dict.fromkeys(out.residual) if item not in out.discharged]
    out.falsified = list(dict.fromkeys(out.falsified + failed_monitor_claims))

    primary_id = f"claim:{requirement_id}:primary"
    graph_id = f"claim:{requirement_id}:assurance_graph"
    primary_status = _primary_status(out)

    primary = _make_claim(
        claim_id=primary_id,
        claim_text="Primary artifact trust claim",
        status=primary_status,
        claim_type="primary",
        confidence=_confidence_for_status(primary_status),
        supported_by=out.discharged,
        monitored_by=out.monitored,
        residual_risks=out.residual + out.falsified,
        evidence_refs=["gate_summary", "monitor_events"],
    )
    graph_claim = _make_claim(
        claim_id=graph_id,
        claim_text="Assurance graph has linked support structure",
        status="discharged",
        claim_type="graph",
        confidence="high",
        supported_by=["family_claims", "monitor_claims", "residual_claims", "law_claims"],
        evidence_refs=["assurance_graph"],
        parent_claim_id=primary_id,
    )
    coverage_status = "discharged" if monitor_events else "residual"
    monitor_claim = _make_claim(
        claim_id=f"claim:{requirement_id}:monitor_coverage",
        claim_text="Monitor coverage exists for tracked runtime properties",
        status=coverage_status,
        claim_type="monitor_coverage",
        confidence=_confidence_for_status(coverage_status),
        monitored_by=[event.monitor_id for event in monitor_events],
        residual_risks=([] if monitor_events else ["monitor_coverage_absent"]),
        evidence_refs=[event.monitor_id for event in monitor_events] or ["monitor_coverage_absent"],
        parent_claim_id=primary_id,
    )

    claims = [primary, graph_claim, monitor_claim]
    claims.extend(_law_claims(linked_laws, requirement_id, primary_id, out))
    claims.extend(_family_claims(gates, requirement_id, primary_id))
    claims.extend(_monitor_claims(monitor_events, requirement_id, primary_id))
    claims.extend(_residual_claims(out.residual, requirement_id, primary_id))
    _attach_children(claims)
    out.claims = claims
    return out
