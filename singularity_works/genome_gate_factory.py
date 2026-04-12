from __future__ import annotations
# complexity_justified: genome-gate coupling — the genome IS the detection spec.
# Detector families are split into dedicated modules; this file preserves the public factory surface.

from typing import TYPE_CHECKING, Any

from .genome import AntiPatternSpec, GenomeBundle
from .gates import Gate, GateFinding, GateResult
from .transformer_registry import is_auto_applicable
from .genome_detection_common import DetectionEvidence, SubjectView, _Detection
from .genome_iris import DynamicCapsule, build_iris_prompt, iris_escalate
from .genome_detectors_foundation_a import (
    _detect_resource_lifecycle,
    _detect_protocol_violation,
    _detect_shell_injection,
    _detect_dangerous_calls,
    _detect_verification_disabled,
    _detect_query_construction,
    _detect_placeholders,
    _detect_mutable_defaults,
)
from .genome_detectors_foundation_b1 import (
    _detect_toctou,
    _detect_ssrf,
    _detect_weak_rng,
    _detect_float_finance,
    _detect_unsafe_memory,
)
from .genome_detectors_foundation_b2 import (
    _detect_async_toctou,
    _detect_interprocedural_sqli,
    _detect_invariant_collision,
    _detect_init_cycle,
    _detect_timing_attack,
    _detect_path_traversal,
    _detect_redos,
    _detect_weak_hash,
    _detect_deserialization,
)
from .genome_detectors_wave2_a import (
    _detect_getattr_injection,
    _detect_tls_default_arg,
    _detect_template_injection,
    _detect_open_redirect,
    _detect_injection_patterns,
    _detect_mass_assignment,
)
from .genome_detectors_wave2_b import (
    _detect_format_string_c,
    _detect_integer_overflow_alloc,
    _detect_goroutine_leak,
    _detect_prototype_constructor_pollution,
    _detect_reflection_injection,
    _detect_unsigned_jwt,
)
from .genome_detectors_wave3_a1 import (
    _detect_jwt_algorithm_confusion,
    _detect_http_no_tls,
    _detect_xxe,
)
from .genome_detectors_wave3_a2 import (
    _detect_hardcoded_secrets,
    _detect_insecure_cookie,
    _detect_cors_wildcard,
)
from .genome_detectors_wave3_b1 import (
    _detect_crlf_injection,
    _detect_idor_missing_ownership,
    _detect_insecure_tempfile,
    _detect_unverified_ssl_context,
    _detect_cleartext_protocol,
)
from .genome_detectors_wave3_b2 import (
    _detect_pycrypto_import,
    _detect_django_mark_safe,
    _detect_orm_raw_injection,
    _detect_marshal_deserialize,
    _detect_yaml_unsafe_load,
)
from .genome_detectors_wave3_c1 import (
    _detect_subprocess_shell,
    _detect_ssl_version_pinned,
    _detect_nosql_injection,
    _detect_trojan_source,
    _detect_zip_slip,
)
from .genome_detectors_wave3_c2 import (
    _detect_jwt_none_algorithm,
    _detect_ssti_render_template_string,
    _detect_weak_rsa_key,
    _detect_graphql_introspection,
)
from .genome_detectors_wave3_d1 import (
    _detect_secret_serialization,
    _detect_csrf_exempt,
    _detect_flask_debug,
    _detect_bind_all_interfaces,
    _detect_ldap_injection,
    _detect_csv_injection,
)
from .genome_detectors_wave3_d2 import (
    _detect_paramiko_auto_add_policy,
    _detect_urllib3_disable_warnings,
    _detect_sqlite_load_extension,
    _detect_weak_cipher,
    _detect_decompression_bomb,
)
from .genome_detectors_wave3_d3 import (
    _detect_http_request_smuggling,
    _detect_weak_jwt_secret,
    _detect_account_enumeration,
    _detect_insecure_file_permissions,
    _detect_oauth_token_in_url,
)

if TYPE_CHECKING:
    from .facts import FactBus
    from .genome import GenomeCapsule, RadicalMapGenome


_STRATEGIES: dict[str, Any] = {
    'ast_resource_lifecycle': _detect_resource_lifecycle,
    'ast_protocol_violation': _detect_protocol_violation,
    'ast_dangerous_calls': _detect_dangerous_calls,
    'ast_shell_injection': _detect_shell_injection,
    'ast_verification_disabled': _detect_verification_disabled,
    'ast_query_construction': _detect_query_construction,
    'ast_mutable_defaults': _detect_mutable_defaults,
    'token_placeholder_check': _detect_placeholders,
    'ast_toctou': _detect_toctou,
    'ast_ssrf': _detect_ssrf,
    'ast_weak_rng': _detect_weak_rng,
    'ast_float_finance': _detect_float_finance,
    'ast_unsafe_memory': _detect_unsafe_memory,
    'ast_async_toctou': _detect_async_toctou,
    'interproc_sqli': _detect_interprocedural_sqli,
    'interproc_invariant_collision': _detect_invariant_collision,
    'interproc_init_cycle': _detect_init_cycle,
    'local_timing_attack': _detect_timing_attack,
    'local_path_traversal': _detect_path_traversal,
    'local_redos': _detect_redos,
    'local_weak_hash': _detect_weak_hash,
    'local_deserialization': _detect_deserialization,
    'local_getattr_injection': _detect_getattr_injection,
    'local_tls_default': _detect_tls_default_arg,
    'local_template_injection': _detect_template_injection,
    'local_open_redirect': _detect_open_redirect,
    'local_injection_patterns': _detect_injection_patterns,
    'local_mass_assignment': _detect_mass_assignment,
    'local_format_string_c': _detect_format_string_c,
    'local_integer_overflow_alloc': _detect_integer_overflow_alloc,
    'local_goroutine_leak': _detect_goroutine_leak,
    'local_prototype_constructor': _detect_prototype_constructor_pollution,
    'local_reflection_injection': _detect_reflection_injection,
    'local_unsigned_jwt': _detect_unsigned_jwt,
    'local_jwt_algorithm_confusion': _detect_jwt_algorithm_confusion,
    'local_http_no_tls': _detect_http_no_tls,
    'local_xxe': _detect_xxe,
    'local_hardcoded_secrets': _detect_hardcoded_secrets,
    'local_insecure_cookie': _detect_insecure_cookie,
    'local_cors_wildcard': _detect_cors_wildcard,
    'local_crlf_injection': _detect_crlf_injection,
    'must_enforce_object_ownership': _detect_idor_missing_ownership,
    'local_insecure_tempfile': _detect_insecure_tempfile,
    'local_unverified_ssl_context': _detect_unverified_ssl_context,
    'local_cleartext_protocol': _detect_cleartext_protocol,
    'local_pycrypto_import': _detect_pycrypto_import,
    'local_django_mark_safe': _detect_django_mark_safe,
    'local_orm_raw_injection': _detect_orm_raw_injection,
    'local_marshal_deserialize': _detect_marshal_deserialize,
    'local_yaml_unsafe_load': _detect_yaml_unsafe_load,
    'local_subprocess_shell': _detect_subprocess_shell,
    'local_ssl_version_pinned': _detect_ssl_version_pinned,
    'local_nosql_injection': _detect_nosql_injection,
    'local_trojan_source': _detect_trojan_source,
    'local_zip_slip': _detect_zip_slip,
    'local_jwt_none_algorithm': _detect_jwt_none_algorithm,
    'local_ssti_render_template': _detect_ssti_render_template_string,
    'local_weak_rsa_key': _detect_weak_rsa_key,
    'local_graphql_introspection': _detect_graphql_introspection,
    'local_secret_serialization': _detect_secret_serialization,
    'local_csrf_exempt': _detect_csrf_exempt,
    'local_flask_debug': _detect_flask_debug,
    'local_bind_all_interfaces': _detect_bind_all_interfaces,
    'local_ldap_injection': _detect_ldap_injection,
    'local_csv_injection': _detect_csv_injection,
    'local_paramiko_auto_add': _detect_paramiko_auto_add_policy,
    'local_urllib3_disable_warnings': _detect_urllib3_disable_warnings,
    'local_sqlite_load_extension': _detect_sqlite_load_extension,
    'local_weak_cipher': _detect_weak_cipher,
    'local_decompression_bomb': _detect_decompression_bomb,
    'local_http_request_smuggling': _detect_http_request_smuggling,
    'local_weak_jwt_secret': _detect_weak_jwt_secret,
    'local_account_enumeration': _detect_account_enumeration,
    'local_insecure_file_permissions': _detect_insecure_file_permissions,
    'local_oauth_token_in_url': _detect_oauth_token_in_url,
}


def _build_gate(capsule: "GenomeCapsule", ap: AntiPatternSpec) -> Gate | None:
    detect_fn = _STRATEGIES.get(ap.detection_strategy)
    if detect_fn is None:
        return None

    gate_id = f"genome:{capsule.pattern_id}:{ap.anti_pattern_id}"
    transformation_axiom = ap.transformation_axiom
    auto_apply_base = ap.auto_apply and is_auto_applicable(transformation_axiom)
    discharge_claim = f"capsule:{capsule.pattern_id}:{ap.anti_pattern_id}"

    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        subject_view = SubjectView.from_subject(subject)
        detections = detect_fn(subject_view.content, ap, semantic_ir=subject_view.semantic_ir)
        if not detections:
            return GateResult(gate_id, capsule.family, "pass", discharged_claims=[discharge_claim])
        findings = [
            GateFinding(
                code=ap.anti_pattern_id,
                message=det.message,
                severity=ap.severity,
                evidence=det.evidence.to_gate_evidence(
                    transformation_axiom=transformation_axiom,
                    auto_apply=auto_apply_base,
                    safety_level=ap.safety_level,
                    linked_laws=capsule.laws,
                ),
            )
            for det in detections
        ]
        return GateResult(
            gate_id,
            capsule.family,
            "fail",
            findings=findings,
            residual_obligations=[f"{ap.anti_pattern_id}_correction"],
        )

    return Gate(gate_id, capsule.family, f"{capsule.summary} — {ap.anti_pattern_id}", run)


def genome_gate_factory(capsule: "GenomeCapsule") -> list[Gate]:
    gates: list[Gate] = []
    for ap in capsule.anti_patterns:
        if not isinstance(ap, AntiPatternSpec):
            continue
        gate = _build_gate(capsule, ap)
        if gate is not None:
            gates.append(gate)
    return gates


def genome_gates_from_bundle(bundle: GenomeBundle, genome: "RadicalMapGenome") -> list[Gate]:
    gates: list[Gate] = []
    seen_gate_ids: set[str] = set()
    for selection in bundle.selected_patterns:
        capsule = genome.by_id.get(selection.pattern_id)
        if capsule is None:
            continue
        for gate in genome_gate_factory(capsule):
            if gate.gate_id not in seen_gate_ids:
                seen_gate_ids.add(gate.gate_id)
                gates.append(gate)
    return gates
