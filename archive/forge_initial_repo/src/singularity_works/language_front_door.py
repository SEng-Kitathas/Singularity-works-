from __future__ import annotations

from pathlib import Path


_EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".sh": "bash",
    ".sql": "sql",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
}


def detect_language(path: str, content: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in _EXTENSION_MAP:
        return _EXTENSION_MAP[suffix]
    text = content.lstrip()
    if text.startswith("#!/usr/bin/env python") or text.startswith("#!/usr/bin/python"):
        return "python"
    if text.startswith("#!/usr/bin/env bash"):
        return "bash"
    if "fn main(" in content and "use " in content:
        return "rust"
    if "package main" in content and "func main()" in content:
        return "go"
    return "unknown"
