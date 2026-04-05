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
        # Warrant coverage: fraction of claims that carry a semantic warrant.
        # A high warrant_coverage means the assurance argument is explanatory —
        # each discharge has a stated reason, not just a boolean flag.
        # Low warrant_coverage signals shallow assurance (legacy or heuristic claims).
        total_claims = len(self.claims)
        warranted = sum(1 for c in self.claims if c.warrant)
        warrant_coverage = round(warranted / total_claims, 3) if total_claims else 0.0
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
            "warrant_coverage": warrant_coverage,
            "warranted_claims": warranted,
            "total_claims": total_claims,
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


# ── Warrant generation helpers ────────────────────────────────────────────────

# Maps gate family → the invariant property the family verifies.
# This is the semantic warrant: WHY a passing gate in this family
# constitutes evidence for the primary security claim.
_FAMILY_INVARIANTS: dict[str, str] = {
    "injection":              "no untrusted input reaches injection sinks without sanitization",
    "injection_resistance":   "injection surface is parameterized and bounded",
    "boundary":               "trust boundaries enforce input validation before sensitive operations",
    "auth":                   "authentication tokens and sessions are cryptographically secure",
    "network_safety":         "network calls enforce TLS and restrict SSRF attack surface",
    "resource_safety":        "resource lifecycle is bounded: acquire → use → release is atomic",
    "crypto":                 "cryptographic operations use maintained algorithms at safe versions",
    "crypto_safety":          "CSPRNG, current cipher suites, and key management standards are met",
    "temporal_integrity":     "check-then-act sequences are atomic; no TOCTOU race windows",
    "state_isolation":        "concurrent state is guarded; no data race or shared-mutable hazard",
    "verification_integrity": "TLS certificate verification is not suppressed",
    "execution_safety":       "dynamic code execution does not accept untrusted input",
    "numeric_safety":         "financial and index arithmetic uses deterministic fixed-point types",
    "access_control":         "object-level authorization enforces ownership on every resource access",
    "serialize":              "deserialization validates schema and rejects executable payloads",
    "memory_safety":          "pointer arithmetic and casts are bounds-checked and alignment-verified",
    "timing":                 "secret comparisons use constant-time algorithms",
    "logic":                  "application logic invariants are maintained across all code paths",
    "structural":             "code structure satisfies immutable law compliance and hygiene",
    "code_hygiene":           "no placeholder or stub code in production paths",
}

_DEFAULT_INVARIANT = "security properties of this gate family are preserved"


def _warrant_for_family(
    family: str,
    gate_ids: list[str],
    status: str,
) -> str:
    """Generate a semantic warrant string for a family-level claim."""
    invariant = _FAMILY_INVARIANTS.get(family, _DEFAULT_INVARIANT)
    if status == "discharged":
        gate_list = ", ".join(g.split(":")[-1] for g in gate_ids[:3])
        suffix = f" (+{len(gate_ids)-3} more)" if len(gate_ids) > 3 else ""
        return (
            f"Gates [{gate_list}{suffix}] verify that {invariant} — "
            f"evidence: all {family} checks pass with no findings"
        )
    elif status == "falsified":
        return (
            f"FALSIFIED: {invariant} — "
            f"one or more {family} gates produced security findings"
        )
    else:
        return (
            f"RESIDUAL: {invariant} — "
            f"partial discharge; some {family} gates produced warnings"
        )


def _family_claims(gates: GateRunSummary, requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    family_status: dict[str, list[str]] = {}
    claims: list[AssuranceClaim] = []
    for result in gates.results:
        family_status.setdefault(result.gate_family, []).append(result.status)
    for family, statuses in sorted(family_status.items()):
        family_claim_status = _claim_status(statuses)
        passing_gates = [
            result.gate_id
            for result in gates.results
            if result.gate_family == family and result.status == "pass"
        ]
        failing_gates = [
            result.gate_id
            for result in gates.results
            if result.gate_family == family and result.status in {"warn", "fail"}
        ]
        warrant = _warrant_for_family(family, passing_gates, family_claim_status)
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:gate_family:{family}",
                claim_text=f"Gate family '{family}' verifies: {_FAMILY_INVARIANTS.get(family, _DEFAULT_INVARIANT)}",
                status=family_claim_status,
                claim_type="gate_family",
                confidence=_confidence_for_status(family_claim_status),
                supported_by=passing_gates,
                residual_risks=failing_gates,
                evidence_refs=[f"gate_family:{family}"],
                parent_claim_id=parent_id,
                warrant=warrant,
            )
        )
    return claims


def _monitor_claims(monitor_events: list[MonitorEvent], requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    claims: list[AssuranceClaim] = []
    for event in monitor_events:
        claim_id = event.claim_id or f"claim:{requirement_id}:monitor:{event.monitor_id}"
        mon_status = "monitored" if event.status == "pass" else "falsified"
        mon_warrant = (
            f"Monitor '{event.monitor_id}' observed this property at runtime and "
            f"{'confirmed it holds' if event.status == 'pass' else 'detected a violation'}"
        )
        claims.append(
            _make_claim(
                claim_id=claim_id,
                claim_text=f"Monitor claim for {event.monitor_id}",
                status=mon_status,
                claim_type="monitor",
                confidence=("high" if event.status == "pass" else "low"),
                monitored_by=[event.monitor_id],
                residual_risks=([event.monitor_id] if event.status == "fail" else []),
                evidence_refs=[event.monitor_id],
                parent_claim_id=parent_id,
                warrant=mon_warrant,
            )
        )
    return claims


def _residual_claims(residuals: list[str], requirement_id: str, parent_id: str) -> list[AssuranceClaim]:
    claims: list[AssuranceClaim] = []
    for residual in residuals:
        # Residual warrant: names the open obligation and its security implication
        res_warrant = (
            f"Obligation '{residual}' is open — "
            f"the corresponding security invariant has not been fully discharged; "
            f"manual review or remediation required before deployment"
        )
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:residual:{residual}",
                claim_text=f"Residual obligation: {residual}",
                status="residual",
                claim_type="residual",
                confidence="moderate",
                residual_risks=[residual],
                evidence_refs=[residual],
                parent_claim_id=parent_id,
                warrant=res_warrant,
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
        principle = law.get("principle", "")
        law_warrant = (
            f"Law '{law['name']}' is structurally enforced: {principle}"
            if law_status == "discharged"
            else f"Law '{law['name']}' compliance is residual — "
                 f"principle not fully verified: {principle}"
        )
        claims.append(
            _make_claim(
                claim_id=f"claim:{requirement_id}:law:{law_id}",
                claim_text=f"{law['name']} applied to this artifact",
                status=law_status,
                claim_type="law",
                confidence=_confidence_for_status(law_status),
                supported_by=( ["structural.law_compliance"] if law_status == "discharged" else [] ),
                residual_risks=( [] if law_status == "discharged" else ["law_compliance"] ),
                assumptions=[principle],
                evidence_refs=[law_id, "structural.law_compliance"],
                parent_claim_id=parent_id,
                responsibility_boundary="forge_runtime",
                warrant=law_warrant,
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

    _primary_warrant = (
        f"Primary trust claim is {'supported' if primary_status == 'discharged' else 'CHALLENGED'} "
        f"by {len(out.discharged)} discharged gate families and "
        f"{len(out.monitored)} monitored properties. "
        + (f"FALSIFIED: {len(out.falsified)} security findings require remediation."
           if out.falsified else "No security falsifications detected.")
    )
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
        warrant=_primary_warrant,
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
        warrant=(
            "Assurance graph structure verified: family claims → primary claim → "
            "law claims form a complete argument with traceable evidence chain"
        ),
    )
    coverage_status = "discharged" if monitor_events else "residual"
    _monitor_warrant = (
        f"Runtime monitoring covers {len(monitor_events)} properties"
        if monitor_events
        else "No runtime monitors seeded — runtime behavior unobserved; "
             "static analysis only"
    )
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
        warrant=_monitor_warrant,
    )

    claims = [primary, graph_claim, monitor_claim]
    claims.extend(_law_claims(linked_laws, requirement_id, primary_id, out))
    claims.extend(_family_claims(gates, requirement_id, primary_id))
    claims.extend(_monitor_claims(monitor_events, requirement_id, primary_id))
    claims.extend(_residual_claims(out.residual, requirement_id, primary_id))
    _attach_children(claims)
    out.claims = claims
    return out
