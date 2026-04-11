from __future__ import annotations
# complexity_justified: transformation policy and safe rewrite dispatch

from typing import Iterable
import re

from .models import AppliedTransformation, TransformationCandidate
from .transformer_registry import apply_by_axiom



def _remove_todo_lines(content: str) -> tuple[str, bool, str, str]:
    before = content
    kept: list[str] = []
    changed = False
    for line in content.splitlines():
        low = line.lower()
        if "todo" in low or "fixme" in low:
            changed = True
            continue
        kept.append(line)
    after = "\n".join(kept)
    return after, changed, before, after


def _rewrite_leaked_open(content: str) -> tuple[str, bool, str, str]:
    before = content
    lines = content.splitlines()
    out: list[str] = []
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if "=" in stripped and "open(" in stripped and i + 1 < len(lines):
            indent = line[: len(line) - len(line.lstrip())]
            left = stripped.split("=", 1)[0].strip()
            nxt = lines[i + 1].strip()
            if nxt == f"return {left}.read()":
                out.append(f"{indent}with open(path, 'r', encoding='utf-8') as {left}:")
                out.append(f"{indent}    return {left}.read()")
                changed = True
                i += 2
                continue
        out.append(line)
        i += 1
    after = "\n".join(out)
    return after, changed, before, after


def _rewrite_verify_false(content: str) -> tuple[str, bool, str, str]:
    before = content
    after, count = re.subn(r"verify\s*=\s*False", "verify=True", content)
    return after, count > 0, before, after




def _rewrite_eval_to_literal_eval(content: str) -> tuple[str, bool, str, str]:
    before = content
    if "eval(" not in content:
        return content, False, before, content
    after = content.replace("eval(", "ast.literal_eval(")
    if "import ast" not in after:
        lines = after.splitlines()
        insert_at = 0
        while insert_at < len(lines) and lines[insert_at].startswith(("from __future__", "#")):
            insert_at += 1
        if insert_at < len(lines) and lines[insert_at].startswith("import "):
            lines.insert(insert_at + 1, "import ast")
        else:
            lines.insert(insert_at, "import ast")
        after = "\n".join(lines)
    return after, after != before, before, after

def _unique_candidates(plan: Iterable[TransformationCandidate]) -> list[TransformationCandidate]:
    seen: set[str] = set()
    out: list[TransformationCandidate] = []
    for item in plan:
        if item.candidate_id in seen:
            continue
        seen.add(item.candidate_id)
        out.append(item)
    return out


def _auto_applicable(plan: list[TransformationCandidate]) -> list[TransformationCandidate]:
    return [c for c in plan if c.auto_apply and c.safety_level in {"safe", "high_confidence_safe"}]


def apply_transformations(content: str, plan: list[TransformationCandidate]) -> tuple[str, list[AppliedTransformation]]:
    current = content
    applied: list[AppliedTransformation] = []
    for candidate in _auto_applicable(_unique_candidates(plan)):
        axiom = getattr(candidate, "transformation_axiom", "") or ""
        # Primary path: genome-derived candidates carry a transformation_axiom.
        # Route through the registry — no string matching on gate_id or summary.
        if axiom:
            new, changed, before, after = apply_by_axiom(current, axiom)
        else:
            # Legacy fallback for candidates without an axiom (non-genome gates).
            # This path shrinks as genome coverage expands.
            summary = candidate.summary.lower()
            source = candidate.source_gate
            if "todo" in summary or "stub" in summary or source == "dynamic.no_stub_markers":
                new, changed, before, after = _remove_todo_lines(current)
            elif "literal_eval" in candidate.rewrite_candidate.lower() or "dangerous calls" in summary:
                new, changed, before, after = _rewrite_eval_to_literal_eval(current)
            elif "verify=true" in candidate.rewrite_candidate.lower() or "verify=false" in candidate.rationale.lower():
                new, changed, before, after = _rewrite_verify_false(current)
            elif "resource" in summary or "context manager" in summary or source == "conformance.misuse":
                new, changed, before, after = _rewrite_leaked_open(current)
            else:
                applied.append(
                    AppliedTransformation(
                        candidate_id=candidate.candidate_id,
                        summary=candidate.summary,
                        applied=False,
                        transformation_axiom=axiom,
                        source_gate=candidate.source_gate,
                        safety_level=candidate.safety_level,
                    )
                )
                continue
        applied.append(
            AppliedTransformation(
                candidate_id=candidate.candidate_id,
                summary=candidate.summary,
                applied=changed,
                before_snippet=before if changed else "",
                after_snippet=after if changed else "",
                transformation_axiom=axiom,
                source_gate=candidate.source_gate,
                safety_level=candidate.safety_level,
            )
        )
        current = new
    return current, applied
