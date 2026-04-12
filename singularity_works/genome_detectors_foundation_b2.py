from __future__ import annotations

import ast
from typing import Any

from .genome_detection_common import (
    DetectionEvidence,
    SubjectView,
    _Detection,
    _interproc_analyze,
    _parse,
    _safe_dotall_finditer,
    _safe_dotall_search,
    _todo_hits,
    is_open_call,
)

def _detect_async_toctou(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Detect async TOCTOU: await check followed by await act without atomic wrapper.
    The window between the two awaits allows concurrent requests to bypass the check.
    Pattern: await db.getX() / if condition: / await db.setX()
    """
    import re
    detections: list[_Detection] = []
    # Look for await <check> then await <act> inside the same function body
    # without transaction/lock keyword
    async_check_act = re.compile(
        r'await\s+\w+[^\n]*(?:get|read|fetch|balance|check)[^\n]*'
        r'[\s\S]{0,600}'
        r'await\s+\w+[^\n]*(?:update|set|write|deduct|withdraw|decrement)',
        re.IGNORECASE
    )
    for m in async_check_act.finditer(content):
        line = content[:m.start()].count('\n') + 1
        has_lock = any(kw in content.lower() for kw in (
            'transaction', 'mutex', 'lock', 'atomic', 'serializable',
            'with_lock', 'for update', 'compare_and_swap', 'cas('
        ))
        if not has_lock:
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Async TOCTOU at line {line}: check-then-act across two await "
                    f"boundaries without atomic transaction â€” concurrent requests can "
                    f"both pass the balance check before either deduction commits"
                ),
                evidence={
                    "rewrite_candidate": (
                        "Wrap in a database transaction with SELECT FOR UPDATE, "
                        "or use a compare-and-swap atomic update: "
                        "UPDATE accounts SET balance = balance - amount "
                        "WHERE id = userId AND balance >= amount"
                    ),
                },
            ))
    # IR fallback for temporal gaps
    if not detections and semantic_ir is not None:
        for gap in getattr(semantic_ir, "temporal_gaps", []):
            if gap.gap_type == "ASYNC_ATOMICITY":
                detections.append(_Detection(
                    lineno=gap.check_line,
                    message=f"Async TOCTOU: {gap.description}",
                    evidence={"rewrite_candidate": "Use atomic database transaction or compare-and-swap"},
                ))
    return detections





def _detect_interprocedural_sqli(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Interprocedural: taint from request input flows through function calls into SQL sink."""
    r = _interproc_analyze(content)
    detections = []
    for p in r["taint_paths"]:
        if p["sink_type"] == "db_query":
            detections.append(_Detection(
                lineno=p["sink_line"],
                message=p["description"],
                evidence={"rewrite_candidate": "Parameterize ALL query components; validate table/column names against an allowlist"},
            ))
    return detections




def _detect_invariant_collision(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Semantic collision: Function B writes attribute that Function A whitelists, bypassing the guard."""
    r = _interproc_analyze(content)
    return [
        _Detection(
            lineno=v["line"],
            message=v["description"],
            evidence={"rewrite_candidate": "Route all writes through the guarded setter; make the unguarded setattr path unreachable"},
        )
        for v in r["invariant_violations"]
    ]




def _detect_init_cycle(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Circular initialization dependency between classes."""
    r = _interproc_analyze(content)
    return [
        _Detection(
            lineno=1,
            message=c["description"],
            evidence={"rewrite_candidate": "Use lazy initialization or dependency injection; pass initialized instances rather than calling mediator during __init__"},
        )
        for c in r["init_cycles"]
    ]




def _detect_timing_attack(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Non-constant-time string comparison in security-sensitive context."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=t["lineno"], message=t["message"],
                   evidence={"rewrite_candidate": t["rewrite"]})
        for t in r["timing_attacks"]
    ]




def _detect_path_traversal(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Incomplete path traversal sanitization â€” naive '..' check bypassable via URL encoding."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["incomplete_sanitization"]
    ]




def _detect_redos(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """ReDoS: regex with nested quantifiers causing exponential backtracking."""
    r = _interproc_analyze(content)
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["redos"]
    ]




def _detect_weak_hash(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Weak hash (MD5/SHA1) used in security-sensitive context."""
    r = _interproc_analyze(content)
    # Also check IR for weak_hash tokens (non-Python path)
    extra = []
    if not r["weak_hash"] and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        for tok in tokens:
            if tok.startswith("weak_hash:"):
                for tb in getattr(semantic_ir, "trust_boundaries", []):
                    if tb.boundary_type == "WEAK_HASH":
                        extra.append(_Detection(
                            lineno=tb.sink_line,
                            message=f"Weak hash '{tb.sink_name}' at line {tb.sink_line} in security context",
                            evidence={"rewrite_candidate": "Use bcrypt, argon2, or scrypt for passwords; SHA-256+ for digests"},
                        ))
    return [
        _Detection(lineno=f["lineno"], message=f["message"],
                   evidence={"rewrite_candidate": f["rewrite"]})
        for f in r["weak_hash"]
    ] + extra




def _detect_deserialization(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """Unsafe deserialization of user input (pickle.loads, yaml.load, etc.)."""
    detections = []
    # Python AST path
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == "loads"
                        and isinstance(func.value, ast.Name) and func.value.id == "pickle"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=f"pickle.loads at line {node.lineno} executes arbitrary code â€” attacker controls the deserialized object graph",
                        evidence={"rewrite_candidate": "Use json.loads for structured data; if binary format required, use message-pack or protobuf with schema validation"},
                    ))
                if (isinstance(func, ast.Attribute) and func.attr == "load"
                        and isinstance(func.value, ast.Name) and func.value.id == "yaml"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=f"yaml.load at line {node.lineno} can execute arbitrary Python via YAML tags",
                        evidence={"rewrite_candidate": "Use yaml.safe_load() which disables tag execution"},
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "deserialization:pickle_loads" in tokens or "deserialization:unsafe_deserialize" in tokens:
            for tb in getattr(semantic_ir, "trust_boundaries", []):
                if tb.boundary_type == "DESERIALIZATION":
                    detections.append(_Detection(
                        lineno=tb.sink_line,
                        message=f"Unsafe deserialization '{tb.sink_name}' at line {tb.sink_line}",
                        evidence={"rewrite_candidate": "Replace with safe_load or schema-validated binary format"},
                    ))
    return detections


# ---------------------------------------------------------------------------
# Strategy dispatch table
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Gate builder
# ---------------------------------------------------------------------------



