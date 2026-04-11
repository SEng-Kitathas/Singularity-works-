from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from .gates import Gate, GateResult
from .facts import CompoundDerivationPayload, Fact, FactBus

if TYPE_CHECKING:
    pass


@dataclass
class GateRunSummary:
    results: list[GateResult] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        out = {"pass": 0, "warn": 0, "fail": 0, "residual": 0}
        for r in self.results:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    @property
    def open_residuals(self) -> list[str]:
        vals = []
        for r in self.results:
            vals.extend(r.residual_obligations)
        return list(dict.fromkeys(vals))


# ---------------------------------------------------------------------------
# Status severity for worst-case merge across iterations
# ---------------------------------------------------------------------------
_STATUS_SEVERITY: dict[str, int] = {"pass": 0, "residual": 1, "warn": 2, "fail": 3}


def _worse(a: str, b: str) -> str:
    return a if _STATUS_SEVERITY.get(a, 0) >= _STATUS_SEVERITY.get(b, 0) else b


class EnforcementEngine:
    def __init__(self) -> None:
        self.gates: list[Gate] = []

    def register(self, gate: Gate) -> None:
        self.gates.append(gate)

    # ── Single-pass (legacy / test path) ──────────────────────────────────
    def run(self, subject: dict[str, Any], bus: "FactBus | None" = None) -> GateRunSummary:
        """
        Single-pass enforcement. Passes the FactBus to gates that consume
        upstream facts. No re-ordering within a pass (termination discipline).
        """
        summary = GateRunSummary()
        for gate in self.gates:
            summary.results.append(gate.runner(subject, bus))
        return summary

    # ── Fixed-point convergence loop ───────────────────────────────────────
    def run_fixed_point(
        self,
        subject: dict[str, Any],
        bus: FactBus,
        max_iter: int = 3,
    ) -> GateRunSummary:
        """
        Budget-limited fixed-point enforcement loop.

        Each iteration runs all gates with the current bus state.  Between
        iterations the per-gate results are published as typed facts so that
        later gates can derive from earlier gate conclusions — enabling 2-hop
        and 3-hop taint chains that the single pass cannot reach.

        Convergence: the bus fact count did not change during an iteration,
        meaning no gate produced any new derivation.  Exits early on
        convergence or when the budget (max_iter) is exhausted.

        Returns a merged GateRunSummary taking the *worst-case* status for
        each gate across all iterations.  This is conservative — a gate that
        escalated to fail on iteration 2 stays fail in the final report.

        Architecture note: this closes the DERIVE→RECURSE portion of the
        PROBE→DERIVE→EMBODY→VERIFY→RECURSE loop.  Single-pass enforcement is
        DERIVE only.  Fixed-point is DERIVE+RECURSE.

        Isomorphism: this is the LBE pilot's N-pass taint-walk applied to the
        gate fabric.  Both solve the same problem — a single-pass linear scan
        cannot model multi-hop derivation — using the same convergence
        criterion: early exit when the working set stops growing.
        """
        # Accumulate worst-case results keyed by gate_id
        worst_by_gate: dict[str, GateResult] = {}

        for iteration in range(max_iter):
            facts_before = len(bus.facts)

            # ── Run all gates ──────────────────────────────────────────────
            iter_results: list[GateResult] = []
            for gate in self.gates:
                result = gate.runner(subject, bus)
                iter_results.append(result)

                # Merge into worst-case accumulator
                gid = result.gate_id
                if gid not in worst_by_gate:
                    worst_by_gate[gid] = result
                else:
                    prev = worst_by_gate[gid]
                    if _STATUS_SEVERITY.get(result.status, 0) > _STATUS_SEVERITY.get(prev.status, 0):
                        # Escalation: combine findings from both iterations
                        merged_findings = list(prev.findings) + [
                            f for f in result.findings
                            if f not in prev.findings
                        ]
                        merged_residuals = list(dict.fromkeys(
                            prev.residual_obligations + result.residual_obligations
                        ))
                        worst_by_gate[gid] = GateResult(
                            gate_id=gid,
                            gate_family=result.gate_family,
                            status=result.status,
                            findings=merged_findings,
                            discharged_claims=result.discharged_claims,
                            residual_obligations=merged_residuals,
                        )

            # ── Publish gate results as intermediate facts ─────────────────
            # These make gate conclusions available to downstream gates on the
            # next iteration — the critical step that enables multi-hop chains.
            for result in iter_results:
                _publish_gate_fact(bus, result, iteration)

            # ── Apply compound propagation rules ──────────────────────────
            _apply_propagation_rules(bus, iter_results)

            # ── Convergence check ──────────────────────────────────────────
            facts_after = len(bus.facts)
            if facts_after == facts_before:
                # No new facts — fixpoint reached, stop early
                break

        return GateRunSummary(results=list(worst_by_gate.values()))


# ---------------------------------------------------------------------------
# Inter-iteration fact publication
# ---------------------------------------------------------------------------

def _publish_gate_fact(bus: FactBus, result: GateResult, iteration: int) -> None:
    """
    Publish a gate result as a typed FactBus fact so subsequent iterations
    can read it.  Uses deduplication (fact_id already-seen) from FactBus to
    avoid re-publishing unchanged results.

    Fact type convention:
      gate_fail   — gate produced a fail verdict
      gate_warn   — gate produced a warn verdict
      gate_pass   — gate produced a pass verdict (published once, iter 0 only)

    Only fail/warn facts carry finding payloads — pass facts are lightweight
    acknowledgement tokens to prevent re-derivation waste.
    """
    status = result.status
    if status not in ("fail", "warn"):
        # Pass facts: lightweight, only publish once (iter 0)
        if iteration == 0:
            fact_id = f"gate_pass:{result.gate_id}"
            bus.publish(Fact(
                fact_id=fact_id,
                fact_type="gate_pass",
                scope=result.gate_id,
                confidence="high",
                payload={"gate_id": result.gate_id, "family": result.gate_family},
            ))
        return

    fact_type = f"gate_{status}"
    # Include finding digest in fact_id so escalations (same gate, worse status)
    # are published as distinct facts rather than deduplicated with earlier pass.
    finding_sig = ":".join(f.code for f in result.findings[:3])
    fact_id = f"{fact_type}:{result.gate_id}:{finding_sig}"
    bus.publish(Fact(
        fact_id=fact_id,
        fact_type=fact_type,
        scope=result.gate_id,
        confidence="high",
        payload={
            "gate_id": result.gate_id,
            "gate_family": result.gate_family,
            "finding_codes": [f.code for f in result.findings],
            "finding_messages": [f.message[:120] for f in result.findings[:3]],
            "severity": result.findings[0].severity if result.findings else "medium",
        },
    ))


# ---------------------------------------------------------------------------
# Compound propagation rules — multi-hop derivation
# ---------------------------------------------------------------------------

_INJECTION_FAMILIES = frozenset({
    "injection", "boundary", "query_integrity", "injection_resistance",
})
_TRUST_FAMILIES = frozenset({
    "boundary", "auth", "network_safety", "verification_integrity",
    "state_protocol", "trust_boundary_hardening",
})
_NETWORK_FAMILIES = frozenset({
    "network", "network_safety", "ssrf_protection",
})
_MEMORY_FAMILIES = frozenset({
    "memory_safety", "memory",
})


def _apply_propagation_rules(bus: FactBus, results: list[GateResult]) -> None:
    """
    Emit compound derived facts from the set of this-iteration gate results.

    Each rule maps a conjunction of gate-family failures to a higher-order
    fact type.  The derived fact enables the next iteration's gates to treat
    compound conditions as first-class bus signals — closing the DERIVE loop.

    Current rule set (extensible):
      R1: injection_failure + trust_violation
          → compound_taint_injection (2-hop: tainted input reaches injection sink)
      R2: trust_violation + network_failure
          → ssrf_confirmed (2-hop: trust boundary + network sink)
      R3: trust_violation + injection_failure + dangerous_sink_present
          → critical_compound_hazard (3-hop: all three axes active simultaneously)
      R4: memory_failure + trust_violation
          → memory_corruption_via_taint (2-hop: tainted input reaches unsafe memory)

    Isomorphism: this is a micro-Prolog forward-chaining over typed facts —
    the same mechanism as Datalog or production-rule engines, applied to the
    forge's security evidence surface.
    """
    fail_families: set[str] = set()
    for r in results:
        if r.status == "fail":
            fail_families.add(r.gate_family or "")
            for f in r.findings:
                # Include gate_id family prefix as additional signal
                gid = r.gate_id.split(":")[0] if ":" in r.gate_id else r.gate_id
                fail_families.add(gid)

    has_injection = bool(fail_families & _INJECTION_FAMILIES)
    trust_boundaries = bus.trust_boundaries() if hasattr(bus, "trust_boundaries") else []
    has_trust     = (
        bool(fail_families & _TRUST_FAMILIES)
        or bool(trust_boundaries)
    )
    has_network   = bool(fail_families & _NETWORK_FAMILIES)
    has_memory    = bool(fail_families & _MEMORY_FAMILIES)
    dangerous_sinks = bus.dangerous_sinks() if hasattr(bus, "dangerous_sinks") else []
    has_sink      = bool(dangerous_sinks)

    # R1 — 2-hop: tainted input → injection sink
    if has_injection and has_trust:
        bus.publish(Fact.from_compound_derivation(
            fact_id="compound:taint_injection",
            scope="compound",
            confidence="high",
            payload=CompoundDerivationPayload(
                rule="R1",
                fact_type="compound_taint_injection",
                injection_families=sorted(fail_families & _INJECTION_FAMILIES),
                trust_signal=bool(trust_boundaries),
            ),
            upstream_facts=["gate_fail", "trust_boundary_crossed"],
        ))

    # R2 — 2-hop: trust violation + network sink
    if has_trust and has_network:
        bus.publish(Fact.from_compound_derivation(
            fact_id="compound:ssrf_confirmed",
            scope="compound",
            confidence="high",
            payload=CompoundDerivationPayload(
                rule="R2",
                fact_type="ssrf_confirmed",
            ),
            upstream_facts=["gate_fail", "trust_boundary_crossed"],
        ))

    # R3 — 3-hop: injection + trust + dangerous sink (all three)
    if has_injection and has_trust and has_sink:
        bus.publish(Fact.from_compound_derivation(
            fact_id="compound:critical_hazard",
            scope="compound",
            confidence="high",
            payload=CompoundDerivationPayload(
                rule="R3",
                fact_type="critical_compound_hazard",
                description=(
                    "tainted input reaches injection sink through trust boundary "
                    "with confirmed dangerous side-effect"
                ),
            ),
            upstream_facts=["gate_fail", "trust_boundary_crossed", "dangerous_sink_present"],
        ))

    # R4 — 2-hop: tainted input + unsafe memory operation
    if has_memory and has_trust:
        bus.publish(Fact.from_compound_derivation(
            fact_id="compound:memory_corruption_via_taint",
            scope="compound",
            confidence="high",
            payload=CompoundDerivationPayload(
                rule="R4",
                fact_type="memory_corruption_via_taint",
            ),
            upstream_facts=["gate_fail", "trust_boundary_crossed"],
        ))
