from __future__ import annotations
# complexity_justified: genome-gate coupling â€” the genome IS the detection spec.
# Every structured anti_pattern in a capsule generates a Gate here.
# This closes the DERIVE loop: genome selection (PROBE) -> genome gates (DERIVE).

from collections.abc import Mapping

from .ast_primitives import is_open_call
from .genome import AntiPatternSpec, GenomeBundle, GenomePatternSelection
from .interprocedural import analyze as _interproc_analyze
import ast
import io
import tokenize
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .gates import Gate, GateFinding, GateResult
from .transformer_registry import STRATEGIES, is_auto_applicable

if TYPE_CHECKING:
    from .facts import FactBus
    from .genome import GenomeCapsule, RadicalMapGenome


# ---------------------------------------------------------------------------
# Detection output type
# ---------------------------------------------------------------------------

@dataclass
class DetectionEvidence(Mapping[str, Any]):
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any] | None) -> "DetectionEvidence":
        return cls(details=dict(raw or {}))

    def to_gate_evidence(
        self,
        *,
        transformation_axiom: str,
        auto_apply: bool,
        safety_level: str,
        linked_laws: list[str],
    ) -> dict[str, Any]:
        rewrite_candidate = str(self.details.get("rewrite_candidate", "") or "")
        return {
            **self.details,
            "transformation_axiom": transformation_axiom,
            "auto_apply": auto_apply,
            "safety_level": safety_level,
            "linked_laws": linked_laws,
            "suggested_fix": rewrite_candidate,
        }

    def __getitem__(self, key: str) -> Any:
        return self.details[key]

    def __iter__(self):
        return iter(self.details)

    def __len__(self) -> int:
        return len(self.details)

    def get(self, key: str, default: Any = None) -> Any:
        return self.details.get(key, default)


@dataclass
class _Detection:
    lineno: int
    message: str
    evidence: DetectionEvidence

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, DetectionEvidence):
            self.evidence = DetectionEvidence.from_raw(self.evidence)


@dataclass(frozen=True)
class SubjectView:
    content: str
    semantic_ir: Any | None = None

    @classmethod
    def from_subject(cls, subject: dict[str, Any]) -> "SubjectView":
        return cls(
            content=str(subject.get("content", "") or ""),
            semantic_ir=subject.get("semantic_ir"),
        )

# ---------------------------------------------------------------------------
# Shared AST utilities
# ---------------------------------------------------------------------------

# Substrate-Sovereign resource limits.
# The forge reads content as inert data â€” no execution risk â€”
# but adversarially crafted inputs can cause ReDoS, stack overflow,
# or memory exhaustion in the analysis pipeline itself.
_MAX_CONTENT_BYTES = 2 * 1024 * 1024   # 2 MB hard cap on content analyzed
_MAX_CONTENT_LINES = 50_000             # 50K lines; pathological AST nesting guard
_MAX_REGEX_CONTENT = 500_000            # chars fed to DOTALL regex patterns


def _parse(content: str):
    """Parse Python source to AST with resource guards."""
    if not content.strip():
        return None
    # Size gate: reject oversized inputs before touching the AST machinery.
    # Adversarial: 10MB of deeply nested brackets triggers quadratic AST walk.
    if len(content) > _MAX_CONTENT_BYTES:
        return None
    try:
        return ast.parse(content)
    except SyntaxError:
        return None
    except RecursionError:
        # Pathologically deep nesting (50k nested calls) overflows the C stack
        # inside CPython's parser. Return None â€” strategies fall through to IR.
        return None
    except MemoryError:
        return None


def _safe_dotall_search(pattern, content: str, flags=0):
    """
    Run a DOTALL regex search with a content-length guard.
    DOTALL patterns with [^}]* quantifiers exhibit O(n^2) backtracking
    We limit the search window to _MAX_REGEX_CONTENT chars and scan in
    overlapping chunks so real matches near the beginning are not missed.
    """
    import re as _re
    if len(content) <= _MAX_REGEX_CONTENT:
        return _re.search(pattern, content, flags)
    # Chunked scan: overlap by 256 chars so matches spanning a boundary are caught
    chunk = _MAX_REGEX_CONTENT
    overlap = 256
    pos = 0
    while pos < len(content):
        window = content[pos:pos + chunk]
        m = _re.search(pattern, window, flags)
        if m:
            return m
        pos += chunk - overlap
    return None


def _safe_dotall_finditer(pattern, content: str, flags=0):
    """Chunked finditer for DOTALL patterns â€” same backtracking guard."""
    import re as _re
    if len(content) <= _MAX_REGEX_CONTENT:
        yield from _re.finditer(pattern, content, flags)
        return
    chunk = _MAX_REGEX_CONTENT
    overlap = 256
    pos = 0
    seen_starts: set[int] = set()
    while pos < len(content):
        window = content[pos:pos + chunk]
        for m in _re.finditer(pattern, window, flags):
            abs_start = pos + m.start()
            if abs_start not in seen_starts:
                seen_starts.add(abs_start)
                yield m
        pos += chunk - overlap


def _todo_hits(content: str) -> list[tuple[int, str]]:
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


# ---------------------------------------------------------------------------
# Detection strategies
# ---------------------------------------------------------------------------

