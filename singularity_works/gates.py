from __future__ import annotations
# complexity_justified: gate constructors remain centralized while types and analysis helpers are split into dedicated modules.

import ast

from .gates_analysis import (
    ResourceAnalysis,
    _abstraction_pressure_finding,
    _deep_nesting,
    _deep_nesting_finding,
    _duplication_finding,
    _line_length_finding,
    _looks_declarative_literal_row,
    _normalized_dup_lines,
    _parse_python,
    _resource_analysis,
    _resource_transform_findings,
    _suggestion_dict,
)
from .gates_types import Gate, GateFinding, GateResult
from .models import SimplificationSuggestion

def required_fields_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        required = ["artifact_id", "requirement_id", "content", "family"]
        missing = []
        for key in required:
            if key not in subject:
                missing.append(key)
                continue
            value = subject.get(key)
            if value is None:
                missing.append(key)
                continue
            if key != "content" and value == "":
                missing.append(key)
        if missing:
            finding = GateFinding("missing_fields", f"Missing required fields: {missing}", "high")
            return GateResult(
                "static.required_fields",
                "static",
                "fail",
                findings=[finding],
                residual_obligations=["required_fields"],
            )
        return GateResult("static.required_fields", "static", "pass", discharged_claims=["required_fields"])
    return Gate("static.required_fields", "static", "Check required fields", run)


def syntax_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        # Language-aware: only parse as Python when the semantic IR confirms Python
        # or the language is unknown. Non-Python content has already been validated
        # structurally by the polyglot front door at medium confidence.
        semantic_ir = subject.get("semantic_ir")
        language = "python"
        if semantic_ir is not None:
            language = getattr(semantic_ir, "language", "python")
        elif bus is not None:
            ir_facts = bus.by_type("semantic_ir_ready")
            if ir_facts:
                language = ir_facts[0].payload.get("language", "python")
        if language not in ("python", "unknown"):
            return GateResult(
                "static.syntax", "static", "pass",
                discharged_claims=["syntax_validity"],
            )
        _, err = _parse_python(subject.get("content", ""))
        if err is not None:
            finding = GateFinding("syntax_error", str(err), "critical")
            return GateResult(
                "static.syntax", "static", "fail",
                findings=[finding],
                residual_obligations=["syntax_validity"],
            )
        return GateResult("static.syntax", "static", "pass", discharged_claims=["syntax_validity"])
    return Gate("static.syntax", "static", "Parse candidate as Python or validated polyglot", run)
def law_compliance_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        # Forge-internal: verifies pattern evidence hooks carry required law linkage.
        # Placeholder content detection is now genome-derived (code_hygiene.no_placeholders capsule).
        findings: list[GateFinding] = []
        pattern = subject.get("pattern", {}) or {}
        evidence_hooks = pattern.get("evidence_hooks", {}) or {}
        linked_laws = set(evidence_hooks.get("linked_laws", []))
        required_laws = {"LAW_1", "LAW_4", "LAW_OMEGA"}
        missing_laws = sorted(required_laws - linked_laws)
        if missing_laws:
            findings.append(
                GateFinding(
                    "missing_law_links",
                    f"Pattern evidence hooks missing required laws: {missing_laws}",
                    "medium",
                    {"missing_laws": missing_laws},
                )
            )
        status = "warn" if findings else "pass"
        return GateResult(
            "structural.law_compliance",
            "structural",
            status,
            findings=findings,
            discharged_claims=(["law_compliance"] if status == "pass" else []),
            residual_obligations=([] if status == "pass" else ["law_compliance"]),
        )
    description = "Enforce immutable law linkage on pattern evidence hooks"
    return Gate("structural.law_compliance", "structural", description, run)


def family_alignment_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        req = subject.get("requirement_text", "").lower()
        family = subject.get("family", "")
        radicals = set(subject.get("radicals", []))
        findings: list[GateFinding] = []
        if any(k in req for k in ["protocol", "state", "transition"]) and family != "protocol":
            findings.append(
                GateFinding(
                    "family_mismatch",
                    "Requirement references protocol/state but family is not protocol",
                    "medium",
                )
            )
        if any(k in req for k in ["parse", "grammar", "input"]) and family != "parser":
            findings.append(
                GateFinding(
                    "family_mismatch",
                    "Requirement references parsing but family is not parser",
                    "medium",
                )
            )
        if (any(k in req for k in ["resource", "close", "cleanup"])
                and not any(k in req for k in ["ownership", "idor", "own", "authorize", "access control"])
                and "RESOURCE" not in radicals):
            findings.append(
                GateFinding(
                    "radical_gap",
                    "Requirement references resource discipline but RESOURCE radical absent",
                    "medium",
                )
            )
        status = "warn" if findings else "pass"
        return GateResult(
            "structural.family_alignment",
            "structural",
            status,
            findings=findings,
            discharged_claims=(["family_alignment"] if status == "pass" else []),
            residual_obligations=([] if status == "pass" else ["family_alignment"]),
        )
    return Gate("structural.family_alignment", "structural", "Check family/radical alignment", run)
def simplification_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        content = subject.get("content", "")
        lines_raw = content.splitlines()
        tree, _err = _parse_python(content)
        findings: list[GateFinding] = []
        function_count = 0
        deep_nesting = 0
        declarative_module = False
        analysis = None

        if tree is not None:
            function_count = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
            declarative_module = function_count == 0 and all(
                isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.Assign, ast.AnnAssign, ast.Expr))
                for node in tree.body
            )
            deep_nesting = _deep_nesting(tree)
            analysis = _resource_analysis(tree)
            findings.extend(_resource_transform_findings(analysis))

        long_lines = [(idx + 1, line) for idx, line in enumerate(lines_raw) if len(line.rstrip()) > 100]
        normalized_lines = _normalized_dup_lines(lines_raw)
        duplicate_lines = len(normalized_lines) - len(set(normalized_lines))
        long_line_limit = 140 if declarative_module else 120
        significant_long = [
            item
            for item in long_lines
            if len(item[1].rstrip()) > long_line_limit and not _looks_declarative_literal_row(item[1])
        ]
        # Suppress nesting warning when file already carries complexity_justified.
        # The marker signals that the author has reasoned about the depth.
        complexity_justified = "complexity_justified" in content.lower()
        schema_like_surface = (
            complexity_justified
            and content.count("@dataclass") >= 5
            and "payload" in content.lower()
        )
        optional = [
            None if (declarative_module or complexity_justified) else _line_length_finding(significant_long),
            _duplication_finding(lines_raw, duplicate_lines, declarative_module, schema_like_surface),
            None if complexity_justified else _deep_nesting_finding(deep_nesting),
            _abstraction_pressure_finding(function_count, len(lines_raw), declarative_module),
        ]
        findings.extend(f for f in optional if f is not None)
        status = "warn" if findings else "pass"
        if status == "warn" and not complexity_justified:
            suggestion = SimplificationSuggestion(
                suggestion_id="suggest:justify_complexity",
                summary="Either simplify or justify retained complexity",
                rationale="Residual complexity should carry an explicit argument",
                expected_gain="medium",
                confidence="high",
                rewrite_candidate="# complexity_justified: explain why this burden is necessary",
                safety_level="review_required",
                auto_apply=False,
                linked_laws=["LAW_OMEGA"],
            )
            findings.append(
                GateFinding(
                    "retained_complexity",
                    "Simplification pressure present without complexity justification marker",
                    "medium",
                    {"suggestions": [_suggestion_dict(suggestion)]},
                )
            )
        return GateResult(
            "conformance.simplification",
            "conformance",
            status,
            findings=findings,
            discharged_claims=([] if status == "warn" else ["simplification_review"]),
            residual_obligations=([] if status == "pass" else ["simplification_review"]),
        )
    return Gate("conformance.simplification", "conformance", "Recommend lower-burden equivalent forms", run)
def monitor_seed_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        seeds = subject.get("monitor_seeds", [])
        if not seeds:
            finding = GateFinding("no_monitor_seed", "No monitor seeds derived", "medium")
            return GateResult(
                "runtime.monitor_seed",
                "runtime",
                "warn",
                findings=[finding],
                residual_obligations=["monitor_seed_generation"],
            )
        return GateResult("runtime.monitor_seed", "runtime", "pass", discharged_claims=["monitor_seed_generation"])
    return Gate("runtime.monitor_seed", "runtime", "Ensure monitor seeds exist", run)


def assurance_hook_gate() -> Gate:
    def run(subject: dict[str, Any], bus: "FactBus | None" = None) -> GateResult:
        claim_ids = subject.get("claim_ids", [])
        if not claim_ids:
            finding = GateFinding("no_claims", "No assurance claims linked to subject", "medium")
            return GateResult(
                "runtime.assurance_hook",
                "runtime",
                "warn",
                findings=[finding],
                residual_obligations=["assurance_claim_linkage"],
            )
        return GateResult("runtime.assurance_hook", "runtime", "pass", discharged_claims=["assurance_claim_linkage"])
    return Gate("runtime.assurance_hook", "runtime", "Ensure claim linkage exists", run)
