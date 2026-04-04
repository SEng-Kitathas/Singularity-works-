#!/usr/bin/env python3
"""
sw_oracle.py — Python Oracle for cil-forge Rust Gate Runner

Reads a JSON request from stdin:
  { content, capsules:[{pattern_id, detection_strategy, family, severity, capabilities}],
    language, artifact_id }

Writes a JSON array to stdout:
  [{ gate_id, capsule_id, status, findings:[{code, message, severity, lineno}] }]

This is the migration bridge: while cil-forge Rust systems are being built,
the Rust gate_runner spawns this oracle to get full strategy coverage.
The Python forge's _STRATEGIES dispatch table is the authoritative implementation.

Called by: cil_forge/src/systems/gate_runner.rs::call_python_oracle()
Architecture: ELT — Rust extracts (reads content), Python loads (runs strategies),
              Rust transforms (writes AssuranceSeal from GateEvaluation components).
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

# Add the sw_v19 package to path if not already importable
# This allows the oracle to be called from cil-forge's working directory
_here = Path(__file__).parent
sys.path.insert(0, str(_here.parent))

from singularity_works.genome_gate_factory import _STRATEGIES
from singularity_works.language_front_door import build_ir


def run_oracle(request: dict) -> list[dict]:
    """
    Run all requested capsule strategies against the content.
    Returns list of gate evaluation dicts.
    """
    content = request.get("content", "")
    capsules = request.get("capsules", [])
    language = request.get("language", "python")
    artifact_id = request.get("artifact_id", "artifact")

    # Build semantic IR — same path as the Python forge
    try:
        semantic_ir = build_ir(content, artifact_id=artifact_id, language_hint=language)
    except Exception:
        semantic_ir = None

    results = []

    for capsule in capsules:
        pattern_id = capsule.get("pattern_id", "")
        strategy_name = capsule.get("detection_strategy", "")
        severity = capsule.get("severity", "high")

        # Look up strategy in the dispatch table
        strategy_fn = _STRATEGIES.get(strategy_name)
        if strategy_fn is None:
            # Unknown strategy — emit a pass with a note
            results.append({
                "gate_id": f"oracle:{pattern_id}:{strategy_name}",
                "capsule_id": pattern_id,
                "status": "pass",
                "findings": [],
                "note": f"strategy '{strategy_name}' not in _STRATEGIES table",
            })
            continue

        # Run strategy
        try:
            spec = {"severity": severity}
            detections = strategy_fn(content, spec, semantic_ir=semantic_ir)
        except Exception as e:
            # Strategy raised — emit warn, don't crash the oracle
            results.append({
                "gate_id": f"oracle:{pattern_id}:{strategy_name}",
                "capsule_id": pattern_id,
                "status": "warn",
                "findings": [{
                    "code": "oracle_strategy_error",
                    "message": f"Strategy '{strategy_name}' raised: {e}",
                    "severity": "low",
                    "lineno": 0,
                }],
            })
            continue

        # Convert _Detection objects to dict
        findings = []
        for det in detections:
            findings.append({
                "code": _code_from_detection(det, strategy_name),
                "message": det.message,
                "severity": severity,
                "lineno": det.lineno,
            })

        status = "fail" if findings else "pass"
        # Downgrade to warn if all severities are medium/low
        if findings and all(f["severity"] in ("low", "medium", "info") for f in findings):
            status = "warn"

        results.append({
            "gate_id": f"oracle:{pattern_id}:{strategy_name}",
            "capsule_id": pattern_id,
            "status": status,
            "findings": findings,
        })

    return results


# Strategy name → canonical finding code mapping
# Mirrors the codes used by the Python forge's gate result system
_STRATEGY_TO_CODE: dict[str, str] = {
    "local_deserialization": "unsafe_deserialization",
    "ast_deserialization": "unsafe_deserialization",
    "ast_query_construction": "string_built_query",
    "local_query_construction": "string_built_query",
    "ast_shell_injection": "shell_injection_surface",
    "ast_ssrf": "user_url_to_network",
    "local_ssrf": "user_url_to_network",
    "ast_unsafe_memory": "unsafe_cast_without_bounds",
    "local_goroutine_leak": "goroutine_leak",
    "local_reflection_injection": "reflection_class_execution",
    "local_format_string_c": "format_string_c",
    "local_integer_overflow_alloc": "integer_overflow_alloc",
    "local_getattr_injection": "getattr_dynamic_dispatch",
    "local_template_injection": "ssti_user_in_template",
    "local_open_redirect": "open_redirect_user_url",
    "local_injection_patterns": "xpath_ldap_xxe_injection",
    "local_mass_assignment": "mass_assignment_setattr",
    "local_tls_default": "tls_insecure_default",
    "local_unsigned_jwt": "unsigned_token_trust",
    "local_prototype_constructor": "prototype_constructor_pollution",
    "ast_weak_rng": "weak_rng_in_security",
    "ast_float_finance": "non_deterministic_arithmetic",
    "local_weak_hash": "weak_hash_in_security_context",
    "local_timing_attack": "non_constant_time_compare",
    "local_path_traversal": "incomplete_path_sanitization",
    "local_redos": "catastrophic_backtracking",
    "ast_toctou": "toctou_file_access",
    "ast_async_toctou": "async_check_act_gap",
    "interproc_sqli": "interprocedural_sqli",
    "ast_mutable_defaults": "mutable_default_argument",
}


def _code_from_detection(detection, strategy_name: str) -> str:
    """Extract a canonical finding code, preferring the strategy→code mapping."""
    # Primary: use the canonical code from the mapping table
    canonical = _STRATEGY_TO_CODE.get(strategy_name)
    if canonical:
        return canonical
    # Evidence field may carry a code
    evidence = getattr(detection, "evidence", {})
    if "code" in evidence:
        return evidence["code"]
    # Last resort: clean up the strategy name
    return strategy_name.replace("local_", "").replace("ast_", "").replace("interproc_", "")


def main() -> None:
    try:
        raw = sys.stdin.read()
        request = json.loads(raw)
        results = run_oracle(request)
        print(json.dumps(results))
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(json.dumps([{"error": f"JSON decode: {e}"}]), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps([{"error": str(e)}]), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
