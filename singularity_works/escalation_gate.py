# complexity_justified: coupled escalation thresholds kept together to avoid split policy.
"""
Singularity Works — Escalation Gate
Version: 2026-04-04 · v1.21

Implements the Logic Blueprint Engine escalation decision from
ESCALATION_CRITERIA_SPEC_v0.2.md.

Architecture:
  evaluate(result, code, req, context) → EscalationDecision

  EscalationDecision contains:
    - squeaky_clean: bool (True only if ALL 8 whitelist conditions pass)
    - route_to_lbe: bool (True if not squeaky_clean)
    - triggers: list[EscalationTrigger] with class, reason, confidence
    - squeaky_clean_failures: list[str] — which conditions failed
    - priority: A|B|C|D|E|F|G|H|I|J|K (highest-priority class that fired)

Currently evaluates without the LBE running:
  Condition 1: gate_counts (warn=0, fail=0)
  Condition 2: confidence proxy from recursive_audit flags
  Condition 3: trust gap proxy from falsified gate families
  Condition 4: role coherence — stub (requires LBE path engine)
  Condition 5: unresolved calls via AST walk (Class E4)
  Condition 6: alien score proxy from pattern_ir
  Condition 7: sensitive module family from requirement tags + code patterns
  Condition 8: diff-awareness — stub (requires git integration)

Class E (Structural Complexity) — AST-based, all evaluable now
Class K (Effect Surface Without Validation) — AST-based, all evaluable now
Class I (Residual Density) — from gate_summary.open_residuals
Class H (Alien/Novel) — from pattern analysis
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from .escalation_primitives import (
    _AUTH_CHECK,
    _AUTH_STATE_MUTATION,
    _BUILTINS,
    _CONFIG_AS_CODE,
    _DOMAIN_CRYPTO,
    _DOMAIN_PAYMENT,
    _DOMAIN_PII,
    _EXEC_ALLOWLIST,
    _EXEC_CALLS,
    _EXPIRY_SET,
    _FILE_WRITES,
    _HOST_VALIDATION,
    _NETWORK_CALLS,
    _OBFUSCATED,
    _PATH_NORMALIZATION,
    _POLYGLOT,
    _PW_CONTEXT,
    _QUERY_LANG,
    _SENSITIVE_MODULE_PATTERNS,
    _TOKEN_ISSUE,
    _WEAK_HASH_FUNC,
    _check_k_class,
    _closure_nesting_depth,
    _cyclomatic_complexity,
    _has_dynamic_dispatch,
    _has_unresolved_calls,
    _max_call_depth,
    _max_function_lines,
    _safe_parse,
    _TEMPLATE_EVAL,
)

if TYPE_CHECKING:
    from singularity_works.orchestration import OrchestrationResult
    from singularity_works.models import Requirement


# ── Data model ────────────────────────────────────────────────────────────

class EscalationClass(str, Enum):
    A = "A"   # Hard — mandatory
    B = "B"   # Strong — automatic in standard mode
    C = "C"   # Soft — optional/deferred
    D = "D"   # Manual — operator-commanded
    E = "E"   # Structural Complexity
    F = "F"   # Semantic Role Mismatch
    G = "G"   # Temporal/Concurrent Patterns
    H = "H"   # Alien/Novel Input
    I = "I"   # Residual Obligation Density
    J = "J"   # Domain-Specific Mandatory Review
    K = "K"   # Effect Surface Without Validation

    @property
    def priority_rank(self) -> int:
        """Lower = higher priority. A=0, B=1, ... K=10."""
        return list(EscalationClass).index(self)


@dataclass
class EscalationTrigger:
    escalation_class: EscalationClass
    trigger_id: str          # e.g. "A2", "K1", "E1"
    reason: str
    confidence: str          # certain|high|moderate|low
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class EscalationDecision:
    squeaky_clean: bool
    route_to_lbe: bool
    triggers: list[EscalationTrigger]
    squeaky_clean_failures: list[str]
    priority: str            # highest-class letter that fired, or "none"
    summary: str             # human-readable one-liner

    def to_dict(self) -> dict:
        return {
            "squeaky_clean": self.squeaky_clean,
            "route_to_lbe": self.route_to_lbe,
            "priority": self.priority,
            "trigger_count": len(self.triggers),
            "triggers": [
                {
                    "class": t.escalation_class.value,
                    "trigger_id": t.trigger_id,
                    "reason": t.reason,
                    "confidence": t.confidence,
                    "evidence_refs": t.evidence_refs,
                }
                for t in self.triggers
            ],
            "squeaky_clean_failures": self.squeaky_clean_failures,
            "summary": self.summary,
        }


# ── Main evaluator ────────────────────────────────────────────────────────

def evaluate(
    result: "OrchestrationResult",
    code: str,
    requirement: "Requirement",
    context: dict | None = None,
) -> EscalationDecision:
    """
    Evaluate whether a gate result warrants LBE escalation.

    Parameters
    ----------
    result      : OrchestrationResult from orc.run()
    code        : original source code artifact
    requirement : Requirement object
    context     : optional dict with keys: is_diff, module_family, author_trusted

    Returns EscalationDecision.
    """
    ctx = context or {}
    triggers: list[EscalationTrigger] = []
    sc_failures: list[str] = []

    assurance = result.assurance
    audit = result.recursive_audit or {}
    gate_counts = audit.get("gate_counts", {})
    naivety_flags = audit.get("naivety_flags", [])
    assurance_dict = assurance.to_dict()
    falsified = assurance_dict.get("falsified", [])
    residual = assurance_dict.get("residual", [])

    gate_summary = result.gate_summary
    open_residuals: list = []
    gate_results: list = []
    if gate_summary is not None:
        open_residuals = getattr(gate_summary, "open_residuals", [])
        gate_results = getattr(gate_summary, "results", [])

    # Filter infrastructure noise — monitor_seed fires on all artifacts and
    # represents "no specific monitor assigned", not a semantic residual.
    semantic_residuals = [r for r in open_residuals if r not in _INFRA_RESIDUALS]
    assurance_residuals = [r for r in residual if r not in _INFRA_RESIDUALS]
    semantic_warns = [gr for gr in gate_results
                      if gr.status == "warn" and gr.gate_id not in _INFRA_WARN_GATES]

    warns = len(semantic_warns)
    fails = gate_counts.get("fail", 0)
    residual_count = len(semantic_residuals) + len(assurance_residuals)

    req_text_lower = requirement.text.lower()
    req_tags = set(getattr(requirement, "tags", []))
    code_lower = code.lower()

    # ── Parse code once ───────────────────────────────────────────────
    tree = _safe_parse(code)

    # ════════════════════════════════════════════════════════════════════
    # SQUEAKY CLEAN WHITELIST — 8 conditions
    # ════════════════════════════════════════════════════════════════════

    # Condition 1: no warn, no fail, no residual
    if warns > 0 or fails > 0 or residual_count > 0:
        sc_failures.append(
            f"condition_1_gate_not_clean: warn={warns} fail={fails} residual={residual_count}")

    # Condition 2: confidence proxy
    # "recovery_not_high_confidence" in naivety_flags → not proven/high-confidence
    # We proxy: if audit says low recovery_confidence AND fails>0 → not confident
    if audit.get("recovery_confidence") == "low" and fails > 0:
        sc_failures.append("condition_2_confidence_not_high")

    # Condition 3: trust gap proxy
    # Falsified gate families that involve trust/wrapper claims indicate trust gap
    trust_related_falsified = [
        f for f in falsified
        if any(k in f for k in ("trust", "wrapper", "safe_", "sanitiz", "validate_"))
    ]
    if trust_related_falsified:
        sc_failures.append(
            f"condition_3_trust_gap: {trust_related_falsified[:2]}")

    # Condition 4: role coherence — stub pending LBE path engine
    # Will be populated once role inference is available.

    # Condition 5: unresolved call targets
    if tree is not None and _has_unresolved_calls(tree):
        sc_failures.append("condition_5_unresolved_calls")

    # Condition 6: alien score
    if (_CONFIG_AS_CODE.search(code) or _QUERY_LANG.search(code) or
            _TEMPLATE_EVAL.search(code) or _OBFUSCATED.search(code) or
            _POLYGLOT.search(code)):
        sc_failures.append("condition_6_alien_content_detected")

    # Condition 7: sensitive module family
    if (_SENSITIVE_MODULE_PATTERNS.search(code) or
            req_tags & {"auth", "crypto", "payment", "admin", "deserialization"}):
        sc_failures.append("condition_7_sensitive_module_family")

    # Condition 8: diff-awareness — stub pending git integration
    if ctx.get("is_diff") and ctx.get("touches_verified_invariant"):
        sc_failures.append("condition_8_diff_touches_verified_invariant")

    # ════════════════════════════════════════════════════════════════════
    # CLASS A: HARD ESCALATION
    # ════════════════════════════════════════════════════════════════════

    if assurance.status == "red":
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A1",
            f"Forge result is red: falsified={falsified[:3]}",
            "certain", falsified[:5],
        ))

    if residual_count > 0:
        semantic_all = semantic_residuals + assurance_residuals
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A2",
            f"Residual obligations present ({residual_count}): {semantic_all[:3]}",
            "certain", semantic_all[:5],
        ))

    if _OBFUSCATED.search(code) or _POLYGLOT.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A3",
            "Alien/novel input: obfuscated content or polyglot artifact",
            "high",
        ))

    if warns > 0:
        warn_gates = [gr.gate_id for gr in gate_results if gr.status == "warn"]
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A_WARN",
            f"Gate warnings present ({warns}): {warn_gates[:3]}",
            "certain", warn_gates[:5],
        ))

    # A7/A8: suspicious-clean — high complexity but green
    if tree is not None and assurance.status == "green":
        cc = _cyclomatic_complexity(tree)
        if cc > 15 and fails == 0 and warns == 0:
            triggers.append(EscalationTrigger(
                EscalationClass.A, "A8",
                f"Suspicious-clean: cyclomatic_complexity={cc} but all gates pass",
                "moderate", [f"cc={cc}"],
            ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS B: STRONG ESCALATION
    # ════════════════════════════════════════════════════════════════════

    if (assurance.status == "green"
            and "residual_obligations_present" in naivety_flags
            and residual_count > 0):  # only if semantic residuals remain after infra filter
        triggers.append(EscalationTrigger(
            EscalationClass.B, "B2",
            "Unknown-heavy path: residual_obligations_present in naivety_flags despite green status",
            "high",
        ))

    if _SENSITIVE_MODULE_PATTERNS.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.B, "B4",
            "Code touches sensitive module family (auth/crypto/payment/exec/deserialization)",
            "high",
        ))

    # B7: effect surface without corresponding validation
    _check_k_class(code, triggers)  # Class K shares the B-severity routing concept

    # ════════════════════════════════════════════════════════════════════
    # CLASS E: STRUCTURAL COMPLEXITY
    # ════════════════════════════════════════════════════════════════════

    if tree is not None:
        cc = _cyclomatic_complexity(tree)
        if cc > 20:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E1",
                f"Cyclomatic complexity {cc} exceeds hard threshold (20)",
                "certain", [f"cc={cc}"],
            ))
        elif cc > 10:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E1_soft",
                f"Cyclomatic complexity {cc} exceeds soft threshold (10)",
                "moderate", [f"cc={cc}"],
            ))

        call_depth = _max_call_depth(tree)
        if call_depth > 8:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E2",
                f"Call chain depth {call_depth} exceeds hard threshold (8)",
                "high", [f"call_depth={call_depth}"],
            ))

        fn_lines = _max_function_lines(code)
        if fn_lines > 150:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E3",
                f"Longest function {fn_lines} lines exceeds hard threshold (150)",
                "certain", [f"max_fn_lines={fn_lines}"],
            ))
        elif fn_lines > 60:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E3_soft",
                f"Longest function {fn_lines} lines exceeds soft threshold (60)",
                "moderate", [f"max_fn_lines={fn_lines}"],
            ))

        if _has_unresolved_calls(tree):
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E4",
                "Unresolved external call targets in critical path",
                "moderate",
            ))

        closure_depth = _closure_nesting_depth(tree)
        if closure_depth > 3:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E5",
                f"Closure nesting depth {closure_depth} exceeds threshold (3)",
                "high", [f"closure_depth={closure_depth}"],
            ))

        if _has_dynamic_dispatch(code):
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E6",
                "Reflection or dynamic import detected",
                "high",
            ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS H: ALIEN / NOVEL INPUT
    # ════════════════════════════════════════════════════════════════════

    if _CONFIG_AS_CODE.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H2",
            "Config-as-code with execution semantics detected (Terraform/k8s/Actions)",
            "high",
        ))

    if _QUERY_LANG.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H3",
            "Query language with injection surface detected (GraphQL/SPARQL/Cypher)",
            "high",
        ))

    if _TEMPLATE_EVAL.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H4",
            "Template language with eval semantics detected (Jinja2/Twig/ERB)",
            "high",
        ))

    if _OBFUSCATED.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H6",
            "Encoded or obfuscated content detected",
            "certain",
        ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS I: RESIDUAL OBLIGATION DENSITY
    # ════════════════════════════════════════════════════════════════════

    if residual_count > 3:
        triggers.append(EscalationTrigger(
            EscalationClass.I, "I2",
            f"High residual obligation density: {residual_count} residuals",
            "certain", (open_residuals + residual)[:5],
        ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS J: DOMAIN-SPECIFIC MANDATORY REVIEW
    # ════════════════════════════════════════════════════════════════════

    if _DOMAIN_CRYPTO.search(code) and re.search(
            r'\bdef\s+\w*(encrypt|decrypt|cipher|hash_|derive_key)\w*', code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J1",
            "Cryptographic primitive implementation detected — never write your own crypto",
            "certain",
        ))

    # J2: weak hash in password storage context — check both argument name and function name
    if _WEAK_HASH_FUNC.search(code) and _PW_CONTEXT.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J2",
            "Weak hash (MD5/SHA1/SHA256) in password storage context — use bcrypt/argon2",
            "certain",
        ))
    elif re.search(r'\b(md5|sha1|sha256)\s*\(.*password', code, re.IGNORECASE):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J2",
            "Weak hash for password detected",
            "certain",
        ))

    if _DOMAIN_PAYMENT.search(code) and re.search(
            r'\b(float|int)\s*\(.*(?:price|amount|total|charge)', code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J3",
            "Financial calculation using float/int — Decimal required for currency math",
            "high",
        ))

    if _DOMAIN_PII.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J4",
            "PII handling code detected — requires privacy review",
            "high",
        ))

    # ════════════════════════════════════════════════════════════════════
    # DECISION
    # ════════════════════════════════════════════════════════════════════

    squeaky_clean = len(sc_failures) == 0
    route_to_lbe = not squeaky_clean or len(triggers) > 0

    # Highest-priority class
    if triggers:
        best = min(triggers, key=lambda t: t.escalation_class.priority_rank)
        priority = best.escalation_class.value
    else:
        priority = "none"

    # Summary
    if squeaky_clean and not triggers:
        summary = "Squeaky clean — LBE not required"
    elif assurance.status == "red":
        summary = f"Class {priority}: gate failed — LBE mandatory ({len(falsified)} falsified)"
    else:
        top = triggers[0] if triggers else None
        summary = (
            f"Class {priority}: {top.trigger_id} — {top.reason[:80]}"
            if top else "LBE recommended"
        )

    return EscalationDecision(
        squeaky_clean=squeaky_clean,
        route_to_lbe=route_to_lbe,
        triggers=triggers,
        squeaky_clean_failures=sc_failures,
        priority=priority,
        summary=summary,
    )


