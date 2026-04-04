from __future__ import annotations

import hashlib
import re

from .models import Fingerprint


_COMMENT_MARKERS = ("#", "//", "--")


def _strip_inline_comment(line: str) -> str:
    for marker in _COMMENT_MARKERS:
        index = line.find(marker)
        if index != -1:
            return line[:index]
    return line


def normalize_source(source: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw in source.splitlines():
        line = _strip_inline_comment(raw).strip()
        if not line:
            continue
        line = re.sub(r"\s+", " ", line)
        lines.append(line)
    return tuple(lines)


def tokenize(normalized_lines: tuple[str, ...]) -> tuple[str, ...]:
    joined = "\n".join(normalized_lines).lower()
    return tuple(token for token in re.split(r"[^a-zA-Z0-9_]+", joined) if token)


def fingerprint(language: str, source: str) -> Fingerprint:
    normalized_lines = normalize_source(source)
    digest = hashlib.sha256("\n".join(normalized_lines).encode("utf-8")).hexdigest()
    return Fingerprint(
        language=language,
        digest=digest,
        tokens=tokenize(normalized_lines),
        normalized_lines=normalized_lines,
    )
