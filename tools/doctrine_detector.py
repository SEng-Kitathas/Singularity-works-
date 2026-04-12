from __future__ import annotations

"""Singularity Works doctrine detector.

Purpose:
- scan the live `singularity_works` package
- identify doctrine/code-quality seams
- emit machine-readable and human-readable reports

This detector is intentionally conservative. It is a seam-finder, not a proof engine.
"""

from dataclasses import dataclass, asdict
import ast
import io
import json
import re
import tokenize
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    seam_id: str
    severity: str
    file: str
    line: int
    category: str
    message: str
    evidence: str


@dataclass(frozen=True)
class ModuleStats:
    file: str
    classes: int
    dataclasses: int
    enums: int
    functions: int
    dict_literals: int
    lines: int


SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _iter_live_py(package_root: Path) -> Iterable[Path]:
    for path in sorted(package_root.glob("*.py")):
        if path.name.startswith("__pycache__"):
            continue
        yield path


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))


def _todo_comment_findings(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    tokens = tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8", errors="replace")).readline)
    for token in tokens:
        if token.type == tokenize.COMMENT:
            low = token.string.lower()
            if 'todo' in low or 'fixme' in low:
                findings.append((token.start[0], token.string.strip()))
    return findings


def _has_dynamic_import(tree: ast.AST) -> int | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'importlib' or alias.name.startswith('importlib.'):
                    return getattr(node, 'lineno', 1)
        elif isinstance(node, ast.ImportFrom):
            if node.module == 'importlib' or (node.module and node.module.startswith('importlib.')):
                return getattr(node, 'lineno', 1)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'spec_from_file_location':
                return getattr(node, 'lineno', 1)
            if isinstance(node.func, ast.Name) and node.func.id == '__import__':
                return getattr(node, 'lineno', 1)
    return None


def _absolute_path_findings(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    absolute_pattern = re.compile(r"(?<![A-Za-z])[A-Z]:[\\/]", re.IGNORECASE)
    for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if absolute_pattern.search(line):
            findings.append((idx, line.strip()))
    return findings


def _module_stats(path: Path, tree: ast.AST) -> ModuleStats:
    classes = 0
    dataclasses = 0
    enums = 0
    functions = 0
    dict_literals = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
            deco_names = []
            for deco in node.decorator_list:
                if isinstance(deco, ast.Name):
                    deco_names.append(deco.id)
                elif isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name):
                    deco_names.append(deco.func.id)
            if "dataclass" in deco_names:
                dataclasses += 1
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "Enum":
                    enums += 1
                elif isinstance(base, ast.Attribute) and base.attr == "Enum":
                    enums += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.Dict):
            dict_literals += 1
    lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    return ModuleStats(path.name, classes, dataclasses, enums, functions, dict_literals, lines)


def _has_phrase(path: Path, pattern: re.Pattern[str]) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if pattern.search(line):
            findings.append(Finding("", "", path.name, idx, "", "", line.strip()))
    return findings


def detect(package_root: Path) -> tuple[list[ModuleStats], list[Finding]]:
    findings: list[Finding] = []
    stats: list[ModuleStats] = []
    module_names = {path.stem for path in _iter_live_py(package_root)}
    inbound: dict[str, int] = {name: 0 for name in module_names}
    texts: dict[str, str] = {}
    trees: dict[str, ast.AST] = {}
    for path in _iter_live_py(package_root):
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = _parse(path)
        texts[path.name] = text
        trees[path.name] = tree
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 1 and node.module in module_names:
                inbound[node.module] = inbound.get(node.module, 0) + 1
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('singularity_works.'):
                mod = node.module.split('.')[-1]
                if mod in module_names:
                    inbound[mod] = inbound.get(mod, 0) + 1

    for path in _iter_live_py(package_root):
        text = texts[path.name]
        tree = trees[path.name]
        stats.append(_module_stats(path, tree))

        # TODO / stub pressure
        for idx, comment in _todo_comment_findings(path):
            findings.append(Finding("DQ-STUB", "high", path.name, idx, "stub", "TODO/FIXME comment marker detected.", comment))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name) and node.exc.func.id == 'NotImplementedError':
                findings.append(Finding("DQ-STUB", "high", path.name, getattr(node, 'lineno', 1), "stub", "NotImplementedError raise detected.", 'raise NotImplementedError(...)'))

        # hardcoded absolute paths
        for idx, line in _absolute_path_findings(path):
            findings.append(Finding("DQ-PATH", "high", path.name, idx, "portability", "Hardcoded absolute path detected.", line))

        # compatibility wrapper detection
        if "compatibility wrapper" in text.lower():
            findings.append(Finding("DQ-WRAP", "medium", path.name, 1, "wrapper", "Compatibility wrapper present; canonical naming/substrate may still be split.", path.name))

        # legacy vessel naming residue
        if path.name not in {"vessel.py"}:
            for idx, line in enumerate(text.splitlines(), start=1):
                if re.search(r"vessel", line):
                    findings.append(Finding("DQ-NAME", "low", path.name, idx, "naming", "Legacy 'vessel' naming residue detected.", line.strip()))
                    break

        # dynamic import / external mounting
        dyn_line = _has_dynamic_import(tree)
        if dyn_line is not None:
            findings.append(Finding("DQ-DYNIMPORT", "medium", path.name, dyn_line, "integration", "Dynamic import / mounted external dependency detected.", path.name))

        # stringly runtime events
        for idx, line in enumerate(text.splitlines(), start=1):
            if "snap.events.append(f\"" in line and ":" in line:
                findings.append(Finding("DQ-STR-EVENT", "medium", path.name, idx, "event_protocol", "Stringly runtime event protocol detected.", line.strip()))

        # dict hotspots
        module_stat = stats[-1]
        if module_stat.dict_literals >= 40:
            findings.append(Finding("DQ-DICT-HOTSPOT", "medium", path.name, 1, "typed_boundary", f"High dict-literal density ({module_stat.dict_literals}) suggests possible dict spill hotspot.", path.name))

        # oversized modules
        if module_stat.lines >= 500:
            findings.append(Finding("DQ-SIZE", "medium", path.name, 1, "module_size", f"Large module ({module_stat.lines} lines) may indicate concentration seam.", path.name))

        # soft metadata boundary
        if path.name == "models.py" and "metadata: dict[str, object]" in text:
            findings.append(Finding("DQ-META", "medium", path.name, 1, "soft_boundary", "RunContext metadata remains an untyped escape hatch.", "RunContext.metadata"))

        if path.name == "evidence_ledger.py" and "payload: dict[str, object]" in text:
            findings.append(Finding("DQ-PAYLOAD", "medium", path.name, 1, "soft_boundary", "EvidenceRecord payload remains a soft dict boundary.", "EvidenceRecord.payload"))

        # zero-inbound lineage remnants heuristics
        if inbound.get(path.stem, 0) == 0 and path.name not in {"__init__.py", "runtime.py", "cockpit_runtime.py", "cockpit.py", "assurance.py", "models.py", "evidence_ledger.py", "facts.py", "orchestration.py", "hud.py", "forge_mcp_server.py"}:
            findings.append(Finding("DQ-ORPHAN", "low", path.name, 1, "integration", "Potential capability island / lineage remnant; verify canonical role.", path.name))

    findings.sort(key=lambda f: (-SEVERITY_ORDER[f.severity], f.file, f.line, f.seam_id))
    return stats, findings


def render_markdown(stats: list[ModuleStats], findings: list[Finding]) -> str:
    lines = []
    lines.append("# Doctrine Detector Report")
    lines.append("")
    lines.append(f"- Modules scanned: {len(stats)}")
    lines.append(f"- Findings: {len(findings)}")
    lines.append("")
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f.severity] += 1
    lines.append("## Severity counts")
    for sev in ["critical", "high", "medium", "low"]:
        lines.append(f"- {sev}: {counts[sev]}")
    lines.append("")
    lines.append("## Findings")
    for finding in findings:
        lines.append(f"- [{finding.seam_id}] {finding.severity.upper()} {finding.file}:{finding.line} — {finding.message} | `{finding.evidence}`")
    lines.append("")
    lines.append("## Module stats")
    for stat in stats:
        lines.append(
            f"- {stat.file}: lines={stat.lines}, classes={stat.classes}, dataclasses={stat.dataclasses}, enums={stat.enums}, functions={stat.functions}, dict_literals={stat.dict_literals}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_root = repo_root / "singularity_works"
    out_json = repo_root / "results" / "doctrine_detector_report.json"
    out_md = repo_root / "results" / "doctrine_detector_report.md"
    stats, findings = detect(package_root)
    out_json.write_text(
        json.dumps(
            {
                "module_stats": [asdict(s) for s in stats],
                "findings": [asdict(f) for f in findings],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    out_md.write_text(render_markdown(stats, findings), encoding="utf-8")
    print(json.dumps({"json": str(out_json), "markdown": str(out_md), "findings": len(findings)}, indent=2))


if __name__ == "__main__":
    main()
