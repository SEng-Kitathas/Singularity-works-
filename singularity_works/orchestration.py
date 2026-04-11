from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass
from pathlib import Path

from .assurance import AssuranceRollup, rollup
from .evidence_ledger import EvidenceLedger, EvidenceRecord
from .enforcement import EnforcementEngine, GateRunSummary
from .forge_context import ForgeContext
from .facts import Fact, FactBus
from .genome import RadicalMapGenome
from .genome_gate_factory import genome_gates_from_bundle, iris_escalate, DynamicCapsule
from .cil_council import CILCouncil
from .language_front_door import build_ir
from .semantic_ir import UniversalSemanticIR
from .gates import (
    assurance_hook_gate,
    family_alignment_gate,
    law_compliance_gate,
    monitor_seed_gate,
    required_fields_gate,
    simplification_gate,
    syntax_gate,
)
from .models import Artifact, Requirement, Risk, RunContext, TransformationCandidate
from .monitoring import MonitorEngine
from .pattern_ir import PatternIR, default_pattern_for_requirement
from .recovery import RecoveryEngine
from .switchboard import Switchboard
from .traceability import TraceLink, TraceabilityIndex
from .transformer import apply_transformations
from .transformer_registry import apply_by_axiom, is_auto_applicable



_LBE_CONFIRMED_DANGER_MARKERS = (
    "TAINTED INPUT REACHES",
    "STRUCTURAL OBLIGATION VIOLATED",
    "WITHOUT VALIDATED TRUST",
)
_LBE_MITIGATED_MARKERS = (
    "sanitization verified",
    "verified_verify",
)
_LBE_NO_FLOW_MARKERS = (
    "no taint flow detected",
    "no_sinks",
    "no sinks",
)


def _classify_lbe_verdict(verdict: str, risk: float) -> dict[str, object]:
    text = (verdict or "").strip()
    low = text.lower()
    if not text or low in {"no_sinks", "no sinks"}:
        return {
            "kind": "no_sinks",
            "falsify": False,
            "reason": "LBE found no dangerous sinks for this artifact.",
        }
    if any(marker in low for marker in _LBE_NO_FLOW_MARKERS):
        return {
            "kind": "no_taint_flow",
            "falsify": False,
            "reason": "LBE found a candidate path but no taint flow to the sink.",
        }
    if any(marker in low for marker in _LBE_MITIGATED_MARKERS):
        return {
            "kind": "mitigated_path",
            "falsify": False,
            "reason": "LBE found a path, but mitigation/sanitization was explicitly verified.",
        }
    if any(marker in text for marker in _LBE_CONFIRMED_DANGER_MARKERS):
        return {
            "kind": "confirmed_danger",
            "falsify": True,
            "reason": "LBE confirmed dangerous logic-path evidence at a sink or obligation boundary.",
        }
    if risk >= 0.95:
        return {
            "kind": "extreme_risk_inference",
            "falsify": True,
            "reason": "LBE reported extreme residual risk without a mitigating path classification.",
        }
    return {
        "kind": "informational",
        "falsify": False,
        "reason": "LBE produced a result, but not a falsifying verdict class.",
    }


@dataclass
class OrchestrationResult:
    artifact: Artifact
    pattern: dict
    gate_summary: GateRunSummary
    assurance: AssuranceRollup
    monitor_events: list
    trace_links: list
    risks: list[Risk]
    recursive_audit: dict
    transformation_plan: list[TransformationCandidate]
    applied_transformations: list[dict]
    fact_summary: dict
    genome_bundle: dict
    escalation_decision: "dict | None" = None  # populated by escalation_gate.evaluate()
    starmap_topology: "dict | None" = None  # populated by forge_starmap.build_evidence_topology()
    lbe_result: "dict | None" = None       # populated by lbe_pilot.analyze() when escalation routes to LBE
    lbe_blueprint: "dict | None" = None    # color-coded flow map: source→transform→sink + min replacement


class Orchestrator:
    def __init__(self, ledger_path: str | Path, forge_context_path: "str | Path | None" = None) -> None:
        self.ledger = EvidenceLedger(ledger_path)
        self.recovery = RecoveryEngine()
        self.monitors = MonitorEngine()
        self.traces = TraceabilityIndex()
        self.switchboard = Switchboard()
        self.facts = FactBus()
        genome_path = Path(ledger_path).parent / "configs" / "seed_genome.json"
        self.genome = RadicalMapGenome.load(genome_path) if genome_path.exists() else None
        # Base gates: forge-internal checks that always run regardless of genome bundle.
        # Semantic pattern detection (misuse, query_integrity, placeholders) is now
        # genome-derived and registered per-evaluation in _evaluate_subject.
        # This closes the DERIVE loop: genome selection -> genome gates -> enforcement.
        self._base_gates = [
            required_fields_gate(),
            syntax_gate(),
            law_compliance_gate(),
            family_alignment_gate(),
            monitor_seed_gate(),
            assurance_hook_gate(),
            simplification_gate(),
        ]
        # ForgeContext v4.0 — CIL SBUF/EPMEM/SMEM memory integration
        self._forge_ctx: "ForgeContext | None" = None
        if forge_context_path is not None:
            self._forge_ctx = ForgeContext(forge_context_path)
            try:
                self._forge_ctx.load()
            except FileNotFoundError:
                pass  # fresh project — caller must call .init() + .save()
        # CIL Council — optional dialectic REASONER+CODER validation layer.
        # Active when LM Studio is reachable. Best-effort — never blocks the forge.
        self._council: "CILCouncil | None" = CILCouncil()


    def _publish_fact(
        self,
        fact_type: str,
        scope: str,
        payload: dict,
        *,
        confidence: str = "moderate",
        evidence_refs: list[str] | None = None,
        linked_laws: list[str] | None = None,
        upstream_facts: list[str] | None = None,
    ) -> None:
        fact_id = f"{scope}:{fact_type}:{len(self.facts.facts)}"
        self.facts.publish(
            Fact(
                fact_id=fact_id,
                fact_type=fact_type,
                scope=scope,
                confidence=confidence,
                payload=payload,
                evidence_refs=evidence_refs or [],
                linked_laws=linked_laws or [],
                upstream_facts=upstream_facts or [],
            )
        )

    def _task_capabilities(
        self,
        requirement: Requirement,
        content: str,
        pattern: PatternIR,
        semantic_ir: "UniversalSemanticIR | None" = None,
    ) -> list[str]:
        # Capability inference: requirement text + content keywords + semantic IR signals.
        # The semantic IR provides the most reliable signal — it has already run language
        # detection and structural extraction, so its tokens are language-agnostic.
        low = f"{requirement.text} {content}".lower()
        capabilities: list[str] = ["code_completeness"]  # always

        # Keyword-based inference (fast path)
        if any(t in low for t in ["open(", "close", "resource", "file", "stream", "handle"]):
            capabilities.append("resource_safety")
        if any(t in low for t in ["query", "select ", "insert ", "sql", "db", "execute",
                                   "redirect", "header", "location", "cors", "xml", "etree",
                                   "elementtree", "minidom", "parsecreate", "fromstring",
                                   "set_cookie", "access-control", "idor", "owner"]):
            capabilities.append("injection_resistance")
        if any(t in low for t in ["state", "protocol", "transition", "eval", "verify", "atomic",
                                   "await ", "async ", "concurrent", "race", "mutex", "lock",
                                   "goroutine", "chan ", "channel", "go func", "cancellation",
                                   "context.", "waitgroup", "coroutine", "thread"]):
            capabilities.append("temporal_integrity")
            capabilities.append("state_isolation")
        if any(t in low for t in ["verify", "boundary", "trust", "auth", "token", "session",
                                   "cookie", "secret", "password", "api_key", "apikey",
                                   "crypt", "hash", "rng", "random", "ssrf", "request",
                                   "host", "url", "webhook", "cors", "xml.etree", "xml.sax",
                                   "set_cookie", "httponly", "samesite"]):
            capabilities.append("trust_boundary_hardening")
        if any(t in low for t in ["float", "decimal", "money", "currency", "financial",
                                   "balance", "amount", "rate", "interest", "price"]):
            capabilities.append("deterministic_precision")
        if any(t in low for t in ["pickle", "deserializ", "serial", "marshal", "yaml.load",
                                   "unsafe", "injection", "sink", "taint"]):
            capabilities.append("sink_isolation")

        # Semantic IR signals (authoritative — derived from actual content analysis)
        if semantic_ir is not None:
            tokens = getattr(semantic_ir, "semantic_tokens", set())
            boundaries = [tb.boundary_type for tb in getattr(semantic_ir, "trust_boundaries", [])]

            if any(t.startswith("float_finance") for t in tokens):
                capabilities.append("deterministic_precision")
            if any(t.startswith("weak_rng") or t.startswith("weak_hash") for t in tokens):
                capabilities.append("trust_boundary_hardening")
                capabilities.append("tls_integrity")
            if any(t.startswith("ssrf") for t in tokens):
                capabilities.append("trust_boundary_hardening")
                capabilities.append("sink_isolation")
            if any(t.startswith("deserialization") for t in tokens):
                capabilities.append("sink_isolation")
                capabilities.append("trust_boundary_hardening")
            if any(t.startswith("toctou") or t.startswith("async_patterns") for t in tokens):
                capabilities.append("temporal_integrity")
                capabilities.append("state_isolation")
            if any(t.startswith("prototype_pollution") for t in tokens):
                capabilities.append("trust_boundary_hardening")
                capabilities.append("injection_resistance")
            if any(t.startswith("unsafe_cast") or t.startswith("resource_leak") for t in tokens):
                capabilities.append("trust_boundary_hardening")
            if semantic_ir.has_async:
                capabilities.append("temporal_integrity")
                capabilities.append("state_isolation")
            if semantic_ir.has_db_calls:
                capabilities.append("injection_resistance")
            if semantic_ir.has_dynamic_exec:
                capabilities.append("trust_boundary_hardening")
                capabilities.append("injection_resistance")

            # Boundary type signals
            if "DB_QUERY" in boundaries:
                capabilities.append("injection_resistance")
            if "WEAK_RNG" in boundaries or "WEAK_HASH" in boundaries:
                capabilities.append("tls_integrity")
            if "NETWORK" in boundaries:
                capabilities.append("trust_boundary_hardening")
                capabilities.append("sink_isolation")
            if "DESERIALIZATION" in boundaries:
                capabilities.append("sink_isolation")
            if "NUMERIC_PRECISION" in boundaries:
                capabilities.append("deterministic_precision")
            if "PROTOTYPE_POLLUTION" in boundaries:
                capabilities.append("trust_boundary_hardening")
                capabilities.append("injection_resistance")

        # Pattern radical signals
        for radical in pattern.radicals:
            if radical == "TRUST":
                capabilities.append("trust_boundary_hardening")
            if radical == "STATE":
                capabilities.append("temporal_integrity")
                capabilities.append("state_isolation")
            if radical == "BOUND":
                capabilities.append("deterministic_precision")
                capabilities.append("sink_isolation")
            if radical == "VERIFY":
                capabilities.append("tls_integrity")
                capabilities.append("trust_boundary_hardening")

        if not capabilities:
            capabilities.append("resource_safety")

        return sorted(set(capabilities))

    def _genome_bundle(
        self,
        requirement: Requirement,
        content: str,
        pattern: PatternIR,
        semantic_ir: "UniversalSemanticIR | None" = None,
    ) -> dict:
        if self.genome is None:
            return {"selected_patterns": []}
        capabilities = self._task_capabilities(requirement, content, pattern, semantic_ir=semantic_ir)
        # Use detected language from semantic IR — structural nativity.
        # "python" was the wrong default; the forge is language-agnostic.
        language = "python"
        if semantic_ir is not None:
            language = getattr(semantic_ir, "language", "python") or "python"
        # Fetch calibrated distortion budgets from SMEM if forge context active.
        # This is the RV-20260329-004 fix: budget_weights feeds INTO bundle selection,
        # not just returned from priors. Lower budget = tighter centroid = higher capsule priority.
        budget_weights: "dict[str, float] | None" = None
        if self._forge_ctx is not None:
            smem_priors = self._forge_ctx.smem_get_priors()
            if smem_priors:
                budget_weights = {
                    cid: data.get("distortion_budget", 0.20)
                    for cid, data in smem_priors.items()
                }
        return self.genome.bundle_for_task(
            language=language,
            capabilities=capabilities,
            preferred_radicals=pattern.radicals,
            budget_weights=budget_weights,
        )

    def _record(self, record_type: str, record_id: str, payload: dict) -> None:
        self.ledger.append(EvidenceRecord(record_type, record_id, payload))

    def _append_trace(self, link: TraceLink) -> None:
        self.traces.add(link)
        linked_requirements = [link.source_id] if link.source_id.startswith("REQ") else []
        self._record(
            "trace_link",
            f"{link.source_id}->{link.target_id}:{link.link_type}",
            link.to_dict() | {"linked_requirements": linked_requirements},
        )

    def _transformation_plan(self, gate_summary: GateRunSummary) -> list[TransformationCandidate]:
        plan: list[TransformationCandidate] = []
        seen: set[str] = set()
        for result in gate_summary.results:
            for finding in result.findings:
                evidence = finding.evidence or {}
                suggestions = list(evidence.get("suggestions", []))
                if not suggestions and evidence.get("rewrite_candidate"):
                    # Genome-derived gates carry transformation_axiom in evidence.
                    # Use the registry to resolve auto_apply and safety_level rather
                    # than branching on gate_id — that was the old hardcoded coupling.
                    transformation_axiom = evidence.get("transformation_axiom", "")
                    rewrite_candidate = evidence.get("rewrite_candidate", "")
                    inferred_laws = list(evidence.get("linked_laws", []))
                    inferred_safety = evidence.get("safety_level", "review_required")
                    # If the evidence already carries auto_apply from the genome capsule, honour it.
                    # Only fall through to registry check if not set.
                    inferred_auto = bool(evidence.get("auto_apply", False))
                    if transformation_axiom and not inferred_auto:
                        inferred_auto = is_auto_applicable(transformation_axiom)
                    suggestions.append(
                        {
                            "suggestion_id": f"auto:{result.gate_id}:{finding.code}",
                            "summary": evidence.get("suggested_fix", finding.message),
                            "rationale": finding.message,
                            "rewrite_candidate": rewrite_candidate,
                            "transformation_axiom": transformation_axiom,
                            "target_spans": evidence.get("target_spans", []),
                            "confidence": evidence.get("confidence", "moderate"),
                            "linked_laws": inferred_laws,
                            "safety_level": inferred_safety,
                            "auto_apply": inferred_auto,
                        }
                    )
                for item in suggestions:
                    cid = item.get("suggestion_id") or f"{result.gate_id}:{finding.code}"
                    if cid in seen:
                        continue
                    seen.add(cid)
                    plan.append(
                        TransformationCandidate(
                            candidate_id=cid,
                            summary=item.get("summary", finding.message),
                            rationale=item.get("rationale", finding.message),
                            rewrite_candidate=item.get("rewrite_candidate", ""),
                            target_spans=item.get("target_spans", evidence.get("target_spans", [])),
                            source_gate=result.gate_id,
                            confidence=item.get("confidence", "moderate"),
                            safety_level=item.get("safety_level", "review_required"),
                            auto_apply=bool(item.get("auto_apply", False)),
                            linked_laws=item.get("linked_laws", []),
                            transformation_axiom=item.get("transformation_axiom", ""),
                        )
                    )
        return plan

    def _recursive_audit(
        self,
        gate_summary: GateRunSummary,
        assurance: AssuranceRollup,
        recovery_confidence: str,
    ) -> dict:
        counts = gate_summary.counts
        naivety: list[str] = []
        if counts.get("warn", 0) > 0:
            naivety.append("warnings_present")
        if recovery_confidence != "high":
            naivety.append("recovery_not_high_confidence")
        if assurance.residual:
            naivety.append("residual_obligations_present")
        if len(assurance.claims) < 4:
            naivety.append("assurance_graph_too_shallow")
        depth = "thin"
        if counts.get("pass", 0) >= 6 and not assurance.residual and not assurance.falsified:
            depth = "moderate"
        if (
            counts.get("pass", 0) >= 7
            and counts.get("warn", 0) == 0
            and not assurance.residual
            and not assurance.falsified
            and len(assurance.claims) >= 4
        ):
            depth = "solid-for-current-scope"
        return {
            "gate_counts": counts,
            "recovery_confidence": recovery_confidence,
            "naivety_flags": naivety,
            "implementation_depth": depth,
            "assurance_status": assurance.status,
        }

    def _gate_payload(self, requirement: Requirement, artifact: Artifact, result, claim_ids: list[str]) -> dict:
        return {
            "requirement_id": requirement.requirement_id,
            "artifact_id": artifact.artifact_id,
            "status": result.status,
            "gate_id": result.gate_id,
            "gate_family": result.gate_family,
            "discharged_claims": result.discharged_claims,
            "residual_obligations": result.residual_obligations,
            "findings": [finding.__dict__ for finding in result.findings],
            "linked_requirements": [requirement.requirement_id],
            "linked_claims": claim_ids,
        }

    def _monitor_payload(self, requirement: Requirement, event) -> dict:
        linked_claims = [event.claim_id] if event.claim_id else []
        return event.__dict__ | {"linked_requirements": [requirement.requirement_id], "linked_claims": linked_claims}

    def _risk_records(
        self,
        requirement: Requirement,
        artifact: Artifact,
        gate_summary: GateRunSummary,
        monitor_events: list,
        claim_ids: list[str],
    ) -> list[Risk]:
        risks: list[Risk] = []
        for result in gate_summary.results:
            if result.status not in {"fail", "warn"}:
                continue
            risks.append(Risk(
                risk_id=f"risk:{result.gate_id}:{artifact.artifact_id}",
                description=f"Gate {result.gate_id} returned {result.status}",
                severity="high" if result.status == "fail" else "medium",
                linked_requirements=[requirement.requirement_id],
                linked_artifacts=[artifact.artifact_id],
                linked_claims=claim_ids,
            ))
        for event in monitor_events:
            if event.status == "pass":
                continue
            linked_claims = [event.claim_id] if event.claim_id else []
            risks.append(Risk(
                risk_id=f"risk:{event.monitor_id}:{artifact.artifact_id}",
                description=event.message,
                severity=event.severity,
                linked_requirements=[requirement.requirement_id],
                linked_artifacts=[artifact.artifact_id],
                linked_claims=linked_claims,
            ))
        return risks

    def _evaluate_subject(
        self,
        requirement: Requirement,
        artifact: Artifact,
        recovery,
        pattern,
        genome_bundle: dict,
        session_key: str,
        semantic_ir: "UniversalSemanticIR | None" = None,
    ):
        claim_ids = [seed.claim_id for seed in recovery.monitor_seeds if seed.claim_id]
        claim_ids += [f"claim:{requirement.requirement_id}:primary"]
        protocol_model = {}
        for structure in recovery.structures:
            if structure.structure_type == "resource_protocol":
                protocol_model = structure.payload
                break
        subject = {
            "artifact_id": artifact.artifact_id,
            "requirement_id": requirement.requirement_id,
            "requirement_text": requirement.text,
            "content": artifact.content,
            "family": artifact.family,
            "radicals": artifact.radicals,
            "monitor_seeds": [seed.monitor_id for seed in recovery.monitor_seeds],
            "claim_ids": claim_ids,
            "protocol_model": protocol_model,
            "pattern": pattern.to_dict(),
            "genome_bundle": genome_bundle,
            # Universal Semantic IR: language-agnostic substrate for all gates.
            # Gates that need richer semantic structure pull from here.
            # None means IR was not built (e.g. post-transformation re-evaluation).
            "semantic_ir": semantic_ir,
        }
        # Publish recovery-derived semantic facts before enforcement so fact-consuming
        # gates receive them during the single enforcement pass.
        # Only publish when the CONTENT analysis found dangerous behavior — not from
        # requirement keyword inference alone. This prevents false facts on clean artifacts.
        for structure in recovery.structures:
            if structure.structure_type == "trust_boundary":
                # Content analysis found dangerous calls or verify=False — real signal
                self._publish_fact(
                    "trust_boundary_crossed",
                    artifact.artifact_id,
                    {
                        "structure_id": structure.structure_id,
                        "dangerous_calls": structure.payload.get("dangerous_calls", []),
                    },
                    confidence=structure.confidence,
                    linked_laws=pattern.evidence_hooks.linked_laws,
                )
            elif structure.structure_type == "resource_protocol":
                # Only flag as dangerous sink if resource is genuinely unclosed
                # (not covered by with-statement or try/finally)
                is_safe = (
                    structure.payload.get("close_seen")
                    or structure.payload.get("with_open_seen")
                    or structure.payload.get("try_finally_close_seen")
                )
                if not is_safe:
                    self._publish_fact(
                        "dangerous_sink_present",
                        artifact.artifact_id,
                        {
                            "structure_id": structure.structure_id,
                            "sink_type": "unclosed_resource",
                        },
                        confidence=structure.confidence,
                        linked_laws=pattern.evidence_hooks.linked_laws,
                    )
        # Publish Universal Semantic IR — derived facts from the polyglot front door.
        # These supplement the recovery-derived facts above and enable cross-gate
        # derivation in the switchboard for any source language.
        if semantic_ir is not None:
            self._publish_fact(
                "semantic_ir_ready",
                artifact.artifact_id,
                {
                    "language": semantic_ir.language,
                    "confidence": semantic_ir.confidence,
                    "has_dynamic_exec": semantic_ir.has_dynamic_exec,
                    "has_db_calls": semantic_ir.has_db_calls,
                    "has_shell_calls": semantic_ir.has_shell_calls,
                    "dangerous_calls": semantic_ir.dangerous_calls,
                    "trust_boundary_count": len(semantic_ir.trust_boundaries),
                },
                confidence=semantic_ir.confidence,
                linked_laws=pattern.evidence_hooks.linked_laws,
            )
            # Publish IR-derived trust boundaries for all languages.
            # Python trust boundaries now carry source_line from the AST taint tracker.
            # Non-Python boundaries carry sink info from heuristic patterns.
            for tb in semantic_ir.unvalidated_boundaries():
                # Publish trust_boundary_crossed with directed chain info
                chain = tb.to_chain_dict()
                self._publish_fact(
                    "trust_boundary_crossed",
                    artifact.artifact_id,
                    {
                        "source": "semantic_ir",
                        "boundary_type": tb.boundary_type,
                        "sink_name": tb.sink_name,
                        "sink_line": tb.sink_line,
                        "tainted_input": tb.tainted_input,
                        "directed": chain["directed"],
                        "source_line": chain["source_line"],
                        "source_type": chain["source_type"],
                        "hops": chain["hops"],
                    },
                    confidence=tb.confidence,
                    linked_laws=pattern.evidence_hooks.linked_laws,
                )
                # Publish directed taint_chain fact for multi-hop derivation
                if tb.is_directed():
                    from .facts import Fact as _Fact
                    fact_id = (
                        f"taint_chain:{artifact.artifact_id}:"
                        f"{tb.source_line}:{tb.sink_line}:{tb.boundary_type}"
                    )
                    self.facts.publish(_Fact(
                        fact_id=fact_id,
                        fact_type="taint_chain",
                        scope=artifact.artifact_id,
                        confidence=tb.confidence,
                        payload=chain,
                        linked_laws=list(pattern.evidence_hooks.linked_laws),
                    ))
            # Publish tainted query construction for switchboard derivation
            if any(tb.boundary_type == "DB_QUERY" for tb in semantic_ir.trust_boundaries):
                self._publish_fact(
                    "query_construction_tainted",
                    artifact.artifact_id,
                    {"source": "semantic_ir"},
                    confidence=semantic_ir.confidence,
                    linked_laws=["LAW_4", "LAW_OMEGA"],
                )
            # Publish resource lifecycle incompleteness if IR detected violations
            if semantic_ir.resource_violations:
                self._publish_fact(
                    "resource_lifecycle_incomplete",
                    artifact.artifact_id,
                    {
                        "violations": [
                            {"resource": v.resource, "violation": v.violation}
                            for v in semantic_ir.resource_violations
                        ]
                    },
                    confidence=semantic_ir.confidence,
                    linked_laws=["LAW_1", "LAW_4"],
                )
        # Build per-evaluation enforcement engine:
        # base gates (always) + genome-derived gates (task-scoped from bundle).
        # This is the DERIVE step of the PROBE->DERIVE->RECURSE loop.
        enforcement = EnforcementEngine()
        for gate in self._base_gates:
            enforcement.register(gate)
        if self.genome is not None:
            for gate in genome_gates_from_bundle(genome_bundle, self.genome):
                enforcement.register(gate)
        # Fixed-point enforcement: iterates until convergence or budget exhaustion.
        # max_iter=3 allows 2-hop derivation (iter 0 detects, 1 derives, 2 confirms)
        # without unbounded computation. Falls back to single-pass if bus is stable.
        gate_summary = enforcement.run_fixed_point(subject, bus=self.facts, max_iter=3)
        for result in gate_summary.results:
            self._record(
                "gate_result",
                f"{result.gate_id}:{session_key}",
                self._gate_payload(requirement, artifact, result, claim_ids),
            )
            self._publish_fact(
                "gate_status",
                artifact.artifact_id,
                {"gate_id": result.gate_id, "status": result.status},
                confidence="high",
                linked_laws=pattern.evidence_hooks.linked_laws,
            )
            for finding in result.findings:
                self._publish_fact(
                    "gate_finding",
                    artifact.artifact_id,
                    {
                        "gate_id": result.gate_id,
                        "code": finding.code,
                        "message": finding.message,
                        "severity": finding.severity,
                    },
                    confidence="high",
                    linked_laws=list((finding.evidence or {}).get("linked_laws", [])),
                )
        transformation_plan = self._transformation_plan(gate_summary)
        if transformation_plan:
            self._record(
                "transformation_plan",
                f"transform:{session_key}",
                {
                    "requirement_id": requirement.requirement_id,
                    "artifact_id": artifact.artifact_id,
                    "linked_requirements": [requirement.requirement_id],
                    "candidates": [candidate.__dict__ for candidate in transformation_plan],
                },
            )
            for candidate in transformation_plan:
                self._publish_fact(
                    "transformation_candidate",
                    artifact.artifact_id,
                    {
                        "candidate_id": candidate.candidate_id,
                        "summary": candidate.summary,
                        "auto_apply": candidate.auto_apply,
                        "safety_level": candidate.safety_level,
                    },
                    confidence=candidate.confidence,
                    linked_laws=candidate.linked_laws,
                )
        monitor_events = self.monitors.run(artifact, recovery.monitor_seeds)
        for event in monitor_events:
            self._record(
                "monitor_event",
                f"{event.monitor_id}:{session_key}",
                self._monitor_payload(requirement, event),
            )
            self._publish_fact(
                "monitor_event",
                artifact.artifact_id,
                {
                    "monitor_id": event.monitor_id,
                    "status": event.status,
                    "claim_id": event.claim_id,
                },
                confidence="high",
            )
            self._append_trace(
                TraceLink(
                    requirement.requirement_id,
                    event.monitor_id,
                    "requirement_to_monitor",
                    "high",
                )
            )
            self._append_trace(
                TraceLink(
                    event.monitor_id,
                    artifact.artifact_id,
                    "monitor_to_artifact",
                    "high",
                    metadata={"claim_id": event.claim_id},
                )
            )
        assurance = rollup(
            gate_summary,
            monitor_events,
            requirement.requirement_id,
            pattern.evidence_hooks.linked_laws,
        )
        risks = self._risk_records(requirement, artifact, gate_summary, monitor_events, claim_ids)
        audit = self._recursive_audit(gate_summary, assurance, recovery.confidence)
        return gate_summary, monitor_events, assurance, risks, audit, transformation_plan

    def _persist_assurance(
        self,
        requirement: Requirement,
        artifact: Artifact,
        assurance: AssuranceRollup,
        session_key: str,
        gate_summary: "GateRunSummary | None" = None,
        semantic_ir: "Any | None" = None,
    ) -> None:
        self._record(
            "assurance_rollup",
            f"assurance:{session_key}",
            {
                "requirement_id": requirement.requirement_id,
                "artifact_id": artifact.artifact_id,
                **assurance.to_dict(),
                "linked_requirements": [requirement.requirement_id],
            },
        )
        for claim in assurance.claims:
            self._record(
                "assurance_claim",
                f"{claim.claim_id}:{session_key}",
                claim.__dict__ | {
                    "requirement_id": requirement.requirement_id,
                    "artifact_id": artifact.artifact_id,
                    "linked_requirements": [requirement.requirement_id],
                    "linked_claims": [claim.claim_id],
                },
            )

        # ── CIL Memory (v4.0) ──────────────────────────────────────────
        if self._forge_ctx is not None and gate_summary is not None:
            _sm = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
            _rm = {
                "INJECTION": "TRUST", "TRUST": "TRUST", "SERIALIZE": "TRUST",
                "REDIRECT": "TRUST", "AUTH": "VERIFY", "TLS": "VERIFY",
                "CRYPTO": "VERIFY", "MEMORY": "BOUND", "UNSAFE": "BOUND",
                "STATE": "STATE", "CONCURRENCY": "STATE", "TEMPORAL": "STATE",
                "NUMERIC": "BOUND", "LOGIC": "STATE", "RUNTIME": "STATE",
            }
            ir_lang = getattr(semantic_ir, "language", "") if semantic_ir else ""
            ir_conf = getattr(semantic_ir, "confidence", "high") if semantic_ir else "high"
            for result in gate_summary.results:
                if result.status in ("fail", "warn") and result.findings:
                    parts = result.gate_id.split(":")
                    capsule_id = parts[1] if len(parts) > 1 else ""
                    radical = _rm.get(capsule_id.split(".")[0].upper(), "TRUST")
                    best_sev = max(result.findings, key=lambda f: _sm.get(f.severity, 0)).severity
                    self._forge_ctx.sbuf_push(
                        session_id=session_key,
                        artifact_id=artifact.artifact_id,
                        gate_id=result.gate_id,
                        status=result.status,
                        severity=best_sev,
                        finding_codes=[f.code for f in result.findings],
                        finding_messages=[f.message for f in result.findings[:2]],
                        radical_tags=[radical],
                        capsule_id=capsule_id,
                        language=ir_lang,
                        confidence=ir_conf,
                    )

    def run(
        self,
        ctx: RunContext,
        requirement: Requirement,
        candidate_content: str,
    ) -> OrchestrationResult:
        self._record(
            "session_start",
            ctx.session_id,
            {
                "mode": ctx.mode,
                "project_tag": ctx.project_tag,
                "requirement_id": requirement.requirement_id,
            },
        )
        self.facts = FactBus()
        # Build Universal Semantic IR — the substrate all gates reason over.
        # Language-agnostic: full AST fidelity for Python, structural heuristics
        # for other languages with explicit confidence annotation.
        # Substrate-Sovereign gate: enforce content size limit before any processing.
        # The forge reads content as inert data with no execution risk, but
        # adversarial inputs can cause ReDoS, stack overflow, or memory pressure.
        _ORCH_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
        if len(candidate_content.encode("utf-8", errors="replace")) > _ORCH_MAX_BYTES:
            self._record(
                "substrate_gate_reject",
                f"oversized:{ctx.session_id}",
                {
                    "reason": "content_too_large",
                    "size_bytes": len(candidate_content.encode("utf-8", errors="replace")),
                    "limit_bytes": _ORCH_MAX_BYTES,
                    "requirement_id": requirement.requirement_id,
                },
            )
            # Truncate to limit — analyze the beginning of the file.
            # Better than rejecting outright: real vulns often appear near top.
            candidate_content = candidate_content.encode(
                "utf-8", errors="replace")[:_ORCH_MAX_BYTES].decode("utf-8", errors="replace")
        semantic_ir = build_ir(
            content=candidate_content,
            artifact_id=f"artifact:{ctx.session_id}",
        )
        pattern = default_pattern_for_requirement(requirement.text)
        genome_bundle = self._genome_bundle(requirement, candidate_content, pattern, semantic_ir=semantic_ir)
        self._record(
            "pattern_selected",
            f"pattern:{ctx.session_id}",
            {
                "pattern_id": pattern.pattern_id,
                "family": pattern.family,
                "radicals": pattern.radicals,
                "requirement_id": requirement.requirement_id,
                "linked_laws": pattern.evidence_hooks.linked_laws,
                "genome_bundle": genome_bundle,
            },
        )
        self._publish_fact(
            "pattern_selected",
            ctx.session_id,
            {
                "pattern_id": pattern.pattern_id,
                "family": pattern.family,
                "radicals": pattern.radicals,
            },
            confidence="high",
            linked_laws=pattern.evidence_hooks.linked_laws,
        )
        for selected in genome_bundle.get("selected_patterns", []):
            self._publish_fact(
                "genome_pattern_selected",
                ctx.session_id,
                {
                    "pattern_id": selected["pattern_id"],
                    "family": selected["family"],
                    "radicals": selected["radicals"],
                    "emitters": selected["emitters"],
                },
                confidence="moderate",
                linked_laws=selected.get("laws", []),
            )
        recovery = self.recovery.derive(requirement, candidate_content)
        for structure in recovery.structures:
            self._publish_fact(
                "recovered_structure",
                ctx.session_id,
                {
                    "structure_id": structure.structure_id,
                    "structure_type": structure.structure_type,
                    "confidence": structure.confidence,
                },
                confidence=structure.confidence,
            )
            self._record(
                "recovered_structure",
                f"{structure.structure_id}:{ctx.session_id}",
                {
                    "requirement_id": requirement.requirement_id,
                    "type": structure.structure_type,
                    "confidence": structure.confidence,
                    "radicals": structure.supports_radicals,
                    "payload": structure.payload,
                    "linked_requirements": [requirement.requirement_id],
                },
            )
            self._append_trace(
                TraceLink(
                    requirement.requirement_id,
                    structure.structure_id,
                    "requirement_to_recovered_structure",
                    structure.confidence,
                    metadata={"structure_type": structure.structure_type},
                )
            )
        artifact = Artifact(
            artifact_id=f"artifact:{ctx.session_id}",
            artifact_type="candidate",
            content=candidate_content,
            origin="orchestrator",
            family=recovery.family or pattern.family,
            radicals=recovery.radicals or pattern.radicals,
            metadata={
                "recovery_confidence": recovery.confidence,
                "recovery_rationale": recovery.rationale,
                "genome_bundle": genome_bundle,
            },
        )
        self._publish_fact(
            "artifact_constructed",
            artifact.artifact_id,
            {
                "family": artifact.family,
                "radicals": artifact.radicals,
            },
            confidence=recovery.confidence,
            linked_laws=pattern.evidence_hooks.linked_laws,
        )
        self._append_trace(
            TraceLink(
                requirement.requirement_id,
                artifact.artifact_id,
                "requirement_to_artifact",
                "high",
            )
        )
        gate_summary, monitor_events, assurance, risks, audit, transformation_plan = (
            self._evaluate_subject(
                requirement,
                artifact,
                recovery,
                pattern,
                genome_bundle,
                ctx.session_id,
                semantic_ir=semantic_ir,
            )
        )
        applied_transformations: list[dict] = []
        # Switchboard routes transformation_candidate facts through the autonomy
        # tiering matrix and publishes switchboard_decision facts back onto the bus.
        # Routing ALWAYS happens — switchboard_decision facts are available for
        # downstream reasoning regardless of whether execution is authorized.
        # Execution requires explicit policy authorization via ctx.metadata or
        # a future ForgePolicy object. This separates recommendation from commitment.
        self.switchboard.route(self.facts)
        eligible_plan: list[TransformationCandidate] = []
        if ctx.metadata.get("apply_transformations") and transformation_plan:
            # Policy authorized: apply all auto-eligible candidates
            auto_apply_ids = {c.candidate_id for c in transformation_plan if c.auto_apply}
            eligible_plan = [c for c in transformation_plan if c.candidate_id in auto_apply_ids]
            transformed_content, applied = apply_transformations(artifact.content, eligible_plan)
            applied_transformations = [item.__dict__ for item in applied if item.applied]
            if transformed_content != artifact.content:
                transformed_recovery = self.recovery.derive(requirement, transformed_content)
                artifact = Artifact(
                    artifact_id=f"{artifact.artifact_id}:transformed",
                    artifact_type="candidate",
                    content=transformed_content,
                    origin="orchestrator.transform",
                    family=transformed_recovery.family or pattern.family,
                    radicals=transformed_recovery.radicals or pattern.radicals,
                    metadata={
                        "recovery_confidence": transformed_recovery.confidence,
                        "recovery_rationale": transformed_recovery.rationale,
                        "genome_bundle": genome_bundle,
                    },
                )
                self._record(
                    "transformation_application",
                    f"apply:{ctx.session_id}",
                    {
                        "requirement_id": requirement.requirement_id,
                        "source_artifact_id": f"artifact:{ctx.session_id}",
                        "transformed_artifact_id": artifact.artifact_id,
                        "applied_transformations": applied_transformations,
                    },
                )
                gate_summary, monitor_events, assurance, risks, audit, transformation_plan = (
                    self._evaluate_subject(
                        requirement,
                        artifact,
                        transformed_recovery,
                        pattern,
                        genome_bundle,
                        f"{ctx.session_id}:transformed",
                        semantic_ir=None,
                    )
                )
                recovery = transformed_recovery
        # ── IRIS escalation — low-conf IR + no static findings ──────
        _ir_low = (semantic_ir is not None and
                   getattr(semantic_ir, "confidence", "high") == "low")
        _static_clean = not any(
            f.severity in ("critical", "high")
            for r in gate_summary.results for f in r.findings
        )
        if _ir_low and _static_clean:
            try:
                _dc = iris_escalate(
                    content=candidate_content,
                    artifact_id=f"artifact:{ctx.session_id}",
                    language=getattr(semantic_ir, "language", "unknown"),
                    semantic_ir=semantic_ir,
                )
                if _dc is not None:
                    _iris_dets = _dc.to_detections(candidate_content)
                    if _iris_dets:
                        self._record("iris_escalation",
                            f"iris:{ctx.session_id}",
                            {"artifact_id": f"artifact:{ctx.session_id}",
                             "classes": _dc.vulnerability_classes,
                             "confidence": _dc.confidence,
                             "count": len(_iris_dets),
                             "reasoning": _dc.reasoning[:200]})
                        from .gates import GateResult, GateFinding
                        # ── Council validation (TM-019) ─────────────────────
                        # Run quick_validate() on the top IRIS detection.
                        # If council disagrees (confidence < 0.5), downgrade to medium.
                        # Council is best-effort — timeout/offline never blocks.
                        _iris_severity = "high"
                        if self._council is not None and _iris_dets:
                            try:
                                _top_det = _iris_dets[0]
                                _is_valid, _council_conf, _council_synthesis = (
                                    self._council.quick_validate(
                                        claim=_top_det.message[:400],
                                        code_context=candidate_content[:1500],
                                    )
                                )
                                if not _is_valid or _council_conf < 0.5:
                                    _iris_severity = "medium"
                                self._record(
                                    "council_validation",
                                    f"council:{ctx.session_id}",
                                    {
                                        "artifact_id": f"artifact:{ctx.session_id}",
                                        "consensus": "AGREE" if _is_valid else "CHALLENGE",
                                        "confidence": _council_conf,
                                        "downgraded": _iris_severity == "medium",
                                        "synthesis": _council_synthesis[:200],
                                    },
                                )
                            except Exception:
                                pass  # Council validation is always best-effort
                        gate_summary.results.append(GateResult(
                            gate_id="iris:dynamic:taint_inference",
                            status="fail",
                            findings=[
                                GateFinding(code="iris_taint_inference",
                                            message=d.message, severity=_iris_severity,
                                            evidence=d.evidence)
                                for d in _iris_dets
                            ],
                        ))
                        gate_summary.counts["fail"] = gate_summary.counts.get("fail", 0) + 1
            except Exception:
                pass  # IRIS escalation is always best-effort

        self._persist_assurance(requirement, artifact, assurance, ctx.session_id,
                                  gate_summary=gate_summary, semantic_ir=semantic_ir)
        for risk in risks:
            self._record(
                "risk",
                risk.risk_id,
                risk.__dict__
                | {
                    "requirement_id": requirement.requirement_id,
                    "artifact_id": artifact.artifact_id,
                },
            )
        self._record(
            "recursive_audit",
            f"audit:{ctx.session_id}",
            {
                "requirement_id": requirement.requirement_id,
                "artifact_id": artifact.artifact_id,
                **audit,
            },
        )
        # Auto-consolidate CIL memory after each run
        if self._forge_ctx is not None:
            pending = self._forge_ctx.sbuf.witnesses()
            if pending:
                self._forge_ctx.consolidate(ctx.session_id, assurance.status)
            if assurance.status in ("red", "green"):
                try:
                    self._forge_ctx.save()
                except Exception:
                    pass

        # Forge StarMap — build evidence topology over gate results + monitor events
        starmap_dict = None
        try:
            from .forge_starmap import build_evidence_topology_full as _starmap_build
            # Build a lightweight proxy result for from_result() — includes monitor_events
            _proxy = type('_R', (), {
                'gate_summary': gate_summary,
                'assurance': assurance,
                'monitor_events': monitor_events,
            })()
            _starmap_topo = _starmap_build(_proxy)
            starmap_dict = _starmap_topo.to_dict()
        except Exception:
            pass  # Non-fatal

        # Escalation gate — evaluate before returning result
        escalation_dict = None
        try:
            from .escalation_gate import evaluate as _escalation_evaluate
            _esc_result = _escalation_evaluate(
                # Pass a partial result object for evaluation
                type('_R', (), {
                    'assurance': assurance,
                    'recursive_audit': audit,
                    'gate_summary': gate_summary,
                    'risks': risks,
                })(),
                candidate_content,
                requirement,
            )
            escalation_dict = _esc_result.to_dict()
        except Exception:
            pass  # Non-fatal — gate result is bonus, not blocking

        # LBE Pilot — run if escalation gate routed to LBE
        # Attaches blobs to result; rebuilds StarMap with combined gate+blob evidence
        lbe_dict = None
        if escalation_dict and escalation_dict.get("route_to_lbe"):
            try:
                from .lbe_pilot import analyze as _lbe_analyze
                from .forge_starmap import ForgeStarMap

                # First pass: build StarMap from gate evidence only (already computed above)
                _sm_gate_obj = ForgeStarMap.from_gate_summary(gate_summary, assurance)
                for ev in monitor_events:
                    if ev.status in ("fail", "warn"):
                        from .forge_starmap import _monitor_to_family
                        _fam = _monitor_to_family(ev.monitor_id)
                        _w = 0.8 if ev.status == "fail" else 0.5
                        _sm_gate_obj._add(f"monitor:{ev.monitor_id[-30:]}", _fam, _w, "finding")
                _sm_gate_metrics = _sm_gate_obj.analyze()

                # LBE analysis with gate-derived StarMap metrics
                _lbe_r = _lbe_analyze(
                    candidate_content,
                    artifact_id=artifact.artifact_id,
                    starmap_metrics=_sm_gate_metrics,
                )

                # Second pass: rebuild StarMap with blobs included (richer evidence)
                if _lbe_r.blobs:
                    _sm_full = ForgeStarMap.from_combined(gate_summary, assurance, _lbe_r.blobs)
                    for ev in monitor_events:
                        if ev.status in ("fail", "warn"):
                            from .forge_starmap import _monitor_to_family
                            _fam = _monitor_to_family(ev.monitor_id)
                            _w = 0.8 if ev.status == "fail" else 0.5
                            _sm_full._add(f"monitor:{ev.monitor_id[-30:]}", _fam, _w, "finding")
                    starmap_dict = _sm_full.analyze().to_dict()

                lbe_dict = {
                    "artifact_id":  _lbe_r.artifact_id,
                    "elapsed_ms":   round(_lbe_r.elapsed_ms, 2),
                    "path_count":   len(_lbe_r.paths),
                    "blob_count":   len(_lbe_r.blobs),
                    "highest_risk": round(_lbe_r.highest_risk_blob.risk_score, 3)
                                    if _lbe_r.highest_risk_blob else 0.0,
                    "verdict":      _lbe_r.highest_risk_blob.verdict
                                    if _lbe_r.highest_risk_blob else "no_sinks",
                    "blobs":        [b.to_dict() for b in _lbe_r.blobs],
                }

                # Bridge LBE verdict classes into assurance using explicit semantics.
                _lbe_verdict = str(lbe_dict.get("verdict", ""))
                _lbe_risk = float(lbe_dict.get("highest_risk", 0.0) or 0.0)
                _lbe_policy = _classify_lbe_verdict(_lbe_verdict, _lbe_risk)
                lbe_dict["bridge_policy"] = _lbe_policy
                if _lbe_policy.get("falsify"):
                    _falsifier = f"lbe:{_lbe_verdict}"
                    if _falsifier not in assurance.falsified:
                        assurance.falsified.append(_falsifier)
                    for _claim in assurance.claims:
                        if getattr(_claim, "claim_type", "") == "primary":
                            _claim.status = "falsified"
                            _claim.confidence = "low"
                            if _falsifier not in _claim.residual_risks:
                                _claim.residual_risks.append(_falsifier)
                            _claim.warrant = (
                                "Primary trust claim is CHALLENGED by "
                                f"{len(assurance.discharged)} discharged gate families and "
                                f"{len(assurance.monitored)} monitored properties. "
                                "FALSIFIED: LBE confirmed dangerous logic-path evidence: "
                                f"{_lbe_verdict}"
                            )
                            break


                # Blueprint — color-coded flow map over LBE results
                _blueprint_dict = None
                try:
                    from .lbe_blueprint import analyze_blueprint as _bp_analyze
                    _bp = _bp_analyze(candidate_content, artifact_id=_lbe_r.artifact_id)
                    _blueprint_dict = _bp.to_dict()
                except Exception:
                    pass
            except Exception:
                pass  # Non-fatal — LBE is bonus cartography, not blocking

        result = OrchestrationResult(
            artifact=artifact,
            pattern={
                "pattern_id": pattern.pattern_id,
                "family": pattern.family,
                "radicals": pattern.radicals,
                "linked_laws": pattern.evidence_hooks.linked_laws,
            },
            gate_summary=gate_summary,
            assurance=assurance,
            monitor_events=monitor_events,
            trace_links=self.traces.links[:],
            risks=risks,
            recursive_audit=audit,
            transformation_plan=transformation_plan,
            applied_transformations=applied_transformations,
            fact_summary=self.facts.summary(),
            genome_bundle=genome_bundle,
            escalation_decision=escalation_dict,
            starmap_topology=starmap_dict,
            lbe_result=lbe_dict,
            lbe_blueprint=_blueprint_dict if lbe_dict else None,
        )
        try:
            from dataclasses import asdict as _dc_asdict
            from .hud import snapshot_from_run_result as _snapshot_from_run_result
            result.hud_snapshot = _dc_asdict(
                _snapshot_from_run_result(
                    result,
                    self,
                    app_name="Singularity Works",
                    version="v1.37",
                    branch="main",
                    uptime_s=0.0,
                    display_mode="full",
                )
            )
        except Exception:
            result.hud_snapshot = None
        return result
