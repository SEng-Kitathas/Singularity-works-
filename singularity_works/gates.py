from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable
import ast
import io
import tokenize

from .laws import BASELINE_AXIOMS
from .models import SimplificationSuggestion

if TYPE_CHECKING:
    from .facts import FactBus

# Gate runner type: subject dict + optional FactBus for fact-consuming gates
GateRunner = Callable[[dict[str, Any], "FactBus | None"], "GateResult"]


@dataclass
class GateFinding:
    code: str
    message: str
    severity: str = "medium"
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    gate_id: str
    gate_family: str
    status: str
    findings: list[GateFinding] = field(default_factory=list)
    discharged_claims: list[str] = field(default_factory=list)
    residual_obligations: list[str] = field(default_factory=list)


@dataclass
class Gate:
    gate_id: str
    gate_family: str
    description: str
    runner: GateRunner


def _parse_python(content: str):
    try:
        return ast.parse(content), None
    except SyntaxError as exc:
        return None, exc



def _is_open_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Name) and func.id == "open"
    ) or (
        isinstance(func, ast.Attribute) and func.attr == "open"
    )


def _todo_comments(content: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        for tok_type, tok_str, start, _end, _line in tokens:
            if tok_type != tokenize.COMMENT:
                continue
            low = tok_str.lower()
            if "todo" in low or "fixme" in low:
                hits.append((start[0], tok_str.strip()))
    except tokenize.TokenError:
        pass
    return hits


class _TransitionVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.transitions: dict[str, list[tuple[str, int]]] = {}
        self.dangerous_calls: list[str] = []
        self.verify_false = False
        self.has_with_open = False
        self.has_try_finally_close = False
        self.managed_names: set[str] = set()

    def _record(self, name: str, action: str, lineno: int) -> None:
        self.transitions.setdefault(name, []).append((action, lineno))

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            ctx = item.context_expr
            if _is_open_call(ctx):
                self.has_with_open = True
                if isinstance(item.optional_vars, ast.Name):
                    name = item.optional_vars.id
                    self.managed_names.add(name)
                    self._record(name, "open", node.lineno)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        if node.finalbody:
            for child in ast.walk(ast.Module(body=node.finalbody, type_ignores=[])):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if child.func.attr == "close":
                        self.has_try_finally_close = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        value = node.value
        if _is_open_call(value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self._record(target.id, "open", node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in {"eval", "exec"}:
            self.dangerous_calls.append(func.id)
        elif isinstance(func, ast.Attribute):
            value = func.value
            if isinstance(value, ast.Name):
                self._record(value.id, func.attr, node.lineno)
        for keyword in node.keywords:
            if keyword.arg == "verify" and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is False:
                    self.verify_false = True
        self.generic_visit(node)


def _resource_analysis(tree) -> dict[str, Any]:
    visitor = _TransitionVisitor()
    visitor.visit(tree)
    leaked: list[str] = []
    use_after_close: list[str] = []
    close_before_open: list[str] = []
    protocol_warnings: list[str] = []
    transition_graph: dict[str, list[str]] = {}
    line_map: dict[str, list[int]] = {}
    managed_names = visitor.managed_names

    for name, seq in visitor.transitions.items():
        state = "unseen"
        transition_graph[name] = [action for action, _ in seq]
        line_map[name] = [lineno for _, lineno in seq]
        for action, _lineno in seq:
            if action == "open":
                state = "open"
                continue
            if action == "close":
                if state != "open":
                    close_before_open.append(name)
                state = "closed"
                continue
            if state == "closed":
                use_after_close.append(name)
            if action in {"send", "recv", "read", "write", "handshake", "connect"} and state == "unseen":
                protocol_warnings.append(name)
        if state == "open" and name not in managed_names and name not in leaked:
            leaked.append(name)

    return {
        "leaked": sorted(set(leaked)),
        "dangerous_calls": sorted(set(visitor.dangerous_calls)),
        "dangerous_verify_false": visitor.verify_false,
        "has_with_open": visitor.has_with_open,
        "has_try_finally_close": visitor.has_try_finally_close,
        "use_after_close": sorted(set(use_after_close)),
        "close_before_open": sorted(set(close_before_open)),
        "protocol_warnings": sorted(set(protocol_warnings)),
        "transition_graph": transition_graph,
        "line_map": line_map,
        "managed_names": sorted(managed_names),
    }


def _protocol_edge_violations(
    transition_graph: dict[str, list[str]],
    protocol_model: dict[str, Any],
) -> list[dict[str, Any]]:
    allowed = {tuple(x) for x in protocol_model.get("allowed_edges", []) if len(x) == 2}
    forbidden = {tuple(x) for x in protocol_model.get("forbidden_edges", []) if len(x) == 2}
    violations: list[dict[str, Any]] = []
    if not allowed and not forbidden:
        return violations
    for name, seq in transition_graph.items():
        pairs = list(zip(seq, seq[1:]))
        bad_pairs = []
        for pair in pairs:
            if pair in forbidden:
                bad_pairs.append({"pair": pair, "reason": "forbidden"})
            elif allowed and pair not in allowed:
                bad_pairs.append({"pair": pair, "reason": "not_allowed"})
        if bad_pairs:
            violations.append({"name": name, "violations": bad_pairs, "sequence": seq})
    return violations


def _normalized_dup_lines(lines_raw: list[str]) -> list[str]:
    out: list[str] = []
    ignorable_prefixes = (
        "@dataclass",
        "return {",
        "return [",
        "fields =",
        "counts =",
        "return Gate(",
        "return GateResult(",
        "return GateFinding(",
        "GateFinding(",
        "GateResult(",
        "Gate(",
        "detections.append(_Detection(",
        "detections: list[_Detection] = []",
        "tree = _parse(",
        "tree = _safe_parse(",
        "self.generic_visit(",
        "message=(",
        "evidence={",
        '"suggestions":',
        '"rewrite_candidate":',
    )
    for raw in lines_raw:
        line = raw.strip()
        if len(line) < 8:
            continue
        if line.startswith(ignorable_prefixes):
            continue
        if "field(default_factory=" in line:
            continue
        if line in {
            "else:", "try:", "finally:", "continue", "return True", "return False", "return None",
            "if tree is None:", "if tree is not None:", "for node in ast.walk(tree):",
            "for child in ast.walk(node):", "if failures:", "relevant_seen = True",
            "func = node.func", "requirement,", "structures,", "gain += 1",
            "confidence_score += 1", "monitor_seeds.append(", "self._monitor_seed(",
            "self._append_structure(",
        }:
            continue
        if all(ch in "{}[](),:.'\"_-=+" for ch in line):
            continue
        out.append(line)
    return out


def _deep_nesting(tree) -> int:
    depth_seen = 0
    control_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)

    def visit(node, depth=0):
        nonlocal depth_seen
        if isinstance(node, control_nodes):
            depth_seen = max(depth_seen, depth + 1)
            depth += 1
        for child in ast.iter_child_nodes(node):
            visit(child, depth)

    visit(tree)
    return depth_seen


def _suggestion_dict(suggestion: SimplificationSuggestion) -> dict[str, Any]:
    return {
        "suggestion_id": suggestion.suggestion_id,
        "summary": suggestion.summary,
        "rationale": suggestion.rationale,
        "expected_gain": suggestion.expected_gain,
        "confidence": suggestion.confidence,
        "rewrite_candidate": suggestion.rewrite_candidate,
        "target_spans": suggestion.target_spans,
        "safety_level": getattr(suggestion, "safety_level", "review_required"),
        "auto_apply": getattr(suggestion, "auto_apply", False),
        "linked_laws": getattr(suggestion, "linked_laws", []),
    }


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
def _resource_transform_findings(analysis: dict[str, Any]) -> list[GateFinding]:
    findings: list[GateFinding] = []
    leaked = analysis["leaked"]
    if leaked and not analysis["has_with_open"]:
        for name in leaked:
            lines = analysis["line_map"].get(name, [])
            suggestion = SimplificationSuggestion(
                suggestion_id=f"suggest:{name}:with_context",
                summary="Resource handling could be simplified to a context manager",
                rationale="Context managers reduce lifecycle mistakes and structural burden",
                expected_gain="high",
                confidence="high",
                rewrite_candidate=f"with open(path, 'r', encoding='utf-8') as {name}:\n    data = {name}.read()",
                target_spans=([[min(lines), max(lines)]] if lines else []),
            )
            findings.append(
                GateFinding(
                    "transform_candidate",
                    "Resource handling could be simplified to a context manager",
                    "medium",
                    {
                        "suggestions": [_suggestion_dict(suggestion)],
                        "transformation_type": "context_manager_refactor",
                        "target_spans": suggestion.target_spans,
                    },
                )
            )
    for name in analysis["use_after_close"]:
        lines = analysis["line_map"].get(name, [])
        suggestion = SimplificationSuggestion(
            suggestion_id=f"suggest:{name}:reorder",
            summary="Reorder resource operations so reads/writes happen before close",
            rationale="Current lifecycle order is invalid or fragile",
            expected_gain="high",
            confidence="moderate",
            rewrite_candidate=f"# move {name}.read()/write() before {name}.close()",
            target_spans=([[min(lines), max(lines)]] if lines else []),
        )
        findings.append(
            GateFinding(
                "transform_candidate",
                "Reorder resource operations so reads/writes happen before close",
                "medium",
                {
                    "suggestions": [_suggestion_dict(suggestion)],
                    "transformation_type": "resource_order_refactor",
                    "target_spans": suggestion.target_spans,
                },
            )
        )
    return findings


def _looks_declarative_literal_row(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith('"') and '{"score":' in stripped and '"severity":' in stripped:
        return True
    if stripped.startswith('"') and 'CWE-' in stripped:
        return True
    return False


def _line_length_finding(significant_long: list[tuple[int, str]]):
    if not significant_long:
        return None
    suggestions = []
    for num, line in significant_long[:5]:
        preview = line[:60].rstrip()
        suggestions.append(
            _suggestion_dict(
                SimplificationSuggestion(
                    suggestion_id=f"suggest:wrap:{num}",
                    summary=f"Wrap long line {num}",
                    rationale="Shorter lines improve local readability and auditability",
                    expected_gain="low",
                    confidence="moderate",
                    rewrite_candidate=preview,
                    target_spans=[[num, num]],
                )
            )
        )
    return GateFinding(
        "line_length",
        f"{len(significant_long)} very long lines detected",
        "low",
        {
            "suggestions": suggestions,
            "line_numbers": [num for num, _ in significant_long[:5]],
            "target_spans": [[num, num] for num, _ in significant_long[:5]],
        },
    )


def _duplication_finding(lines_raw: list[str], duplicate_lines: int, declarative_module: bool):
    threshold_base = max(60 if declarative_module else 12, len(lines_raw) // 4)
    duplicate_ratio = duplicate_lines / max(1, len(lines_raw))
    if duplicate_lines <= threshold_base and duplicate_ratio <= 0.20:
        return None
    suggestion = SimplificationSuggestion(
        suggestion_id="suggest:deduplicate",
        summary="Deduplicate repeated logic",
        rationale="Repeated code raises maintenance burden and drift risk",
        expected_gain="medium",
        confidence="moderate",
        rewrite_candidate="# extract shared helper or consolidate repeated branches",
    )
    return GateFinding(
        "duplication",
        f"{duplicate_lines} duplicate non-empty lines detected",
        "medium",
        {
            "suggestions": [_suggestion_dict(suggestion)],
            "target_spans": [],
            "duplicate_ratio": round(duplicate_ratio, 3),
        },
    )


def _deep_nesting_finding(deep_nesting: int):
    if deep_nesting < 7:
        return None
    suggestions = [
        _suggestion_dict(
            SimplificationSuggestion(
                suggestion_id="suggest:flatten_nesting",
                summary="Flatten nested control flow",
                rationale="Guard clauses reduce nesting and improve auditability",
                expected_gain="medium",
                confidence="moderate",
                rewrite_candidate="# extract guard clauses and early returns",
            )
        )
    ]
    return GateFinding(
        "deep_nesting",
        f"Control nesting depth={deep_nesting}",
        "medium",
        {"suggestions": suggestions, "target_spans": []},
    )


def _abstraction_pressure_finding(function_count: int, line_count: int, declarative_module: bool):
    if declarative_module or function_count != 1 or line_count <= 40:
        return None
    suggestion = SimplificationSuggestion(
        suggestion_id="suggest:extract_helper",
        summary="Extract a helper from the oversized function",
        rationale="Splitting can reduce local burden without changing behavior",
        expected_gain="medium",
        confidence="moderate",
        rewrite_candidate="# extract a helper for one responsibility slice",
    )
    return GateFinding(
        "abstraction_pressure",
        "Large single-function artifact may admit simplification/splitting review",
        "low",
        {"suggestions": [_suggestion_dict(suggestion)], "target_spans": []},
    )


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
        optional = [
            None if (declarative_module or complexity_justified) else _line_length_finding(significant_long),
            _duplication_finding(lines_raw, duplicate_lines, declarative_module),
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
