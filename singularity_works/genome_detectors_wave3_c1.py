from __future__ import annotations

import ast
import re as _re2
import re as _re_ext
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

def _detect_subprocess_shell(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect subprocess calls with shell=True and string argument (not list).
    String + shell=True enables shell injection via metacharacters.
    List + shell=True is lower risk but still flagged.
    (Bandit B602/B603 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is not None:
        _SUBPROCESS_FNS = frozenset({
            "call", "run", "Popen", "check_call", "check_output",
        })
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn_name = (
                    func.attr if isinstance(func, ast.Attribute) else
                    func.id if isinstance(func, ast.Name) else ""
                )
                is_subprocess = (
                    fn_name in _SUBPROCESS_FNS and (
                        (isinstance(func, ast.Attribute) and
                         isinstance(func.value, ast.Name) and
                         func.value.id == "subprocess")
                        or isinstance(func, ast.Name)
                    )
                )
                if not is_subprocess:
                    self.generic_visit(node)
                    return
                shell_true = any(
                    kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                    and kw.value.value is True
                    for kw in node.keywords
                )
                if shell_true and node.args:
                    arg0 = node.args[0]
                    # String arg with shell=True is the worst case
                    is_string_arg = isinstance(arg0, (ast.Constant, ast.JoinedStr,
                                                       ast.BinOp))
                    severity = "critical" if is_string_arg else "high"
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"subprocess.{fn_name}(..., shell=True) at line {node.lineno}"
                            + (" with string arg â€” shell injection if any part is user-controlled"
                               if is_string_arg else " â€” prefer list args to avoid shell injection")
                        ),
                        evidence={
                            "rewrite_candidate":
                                f"subprocess.{fn_name}(['cmd', arg1, arg2])  "
                                f"# list avoids shell; omit shell=True",
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections






def _detect_ssl_version_pinned(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect pinned deprecated SSL/TLS versions: SSLv2, SSLv3, TLSv1, TLSv1_1.
    These are cryptographically broken. Use ssl.PROTOCOL_TLS_CLIENT.
    (Bandit B503/B504 equivalent)
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    _BROKEN_PROTOCOLS = frozenset({
        "PROTOCOL_SSLv2", "PROTOCOL_SSLv3",
        "PROTOCOL_TLSv1", "PROTOCOL_TLSv1_1",
        "PROTOCOL_SSLv23",   # deprecated alias â€” negotiates down to SSLv3
    })
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Attribute(self, node: ast.Attribute) -> None:
                if (node.attr in _BROKEN_PROTOCOLS
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "ssl"):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Deprecated SSL/TLS version ssl.{node.attr} at line {node.lineno} â€” "
                            f"cryptographically broken; use ssl.PROTOCOL_TLS_CLIENT"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "ssl.PROTOCOL_TLS_CLIENT  # negotiates best mutual version"
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic fallback for non-Python (Go, Java TLS config).
    # Gate behind tree is None â€” Python files contain these strings as literals
    # inside _BROKEN_PROTOCOLS frozenset, which would produce self-referential FPs.
    if not detections and tree is None:
        broken_pat = _re_ext.compile(
            r'SSLv[23]|TLSv1[^._]|TLSv1_1|PROTOCOL_TLS_?v1\b|'
            r'tls\.VersionTLS10|tls\.VersionTLS11|'
            r'SSLContext\.TLSv1_1',
            _re_ext.IGNORECASE,
        )
        for i, line in enumerate(content.splitlines(), 1):
            if broken_pat.search(line):
                detections.append(_Detection(
                    lineno=i,
                    message=(
                        f"Deprecated TLS version reference at line {i} â€” "
                        f"TLS 1.0/1.1 and SSLv3 are cryptographically broken"
                    ),
                    evidence={
                        "rewrite_candidate": "Use TLS 1.2 minimum; prefer TLS 1.3"
                    },
                ))
    return detections





# ===========================================================================
# Research loop v1.34 â€” 18 new detectors
# Sources: gosec (Apache-2.0), eslint-plugin-security (Apache-2.0),
#          njsscan (MIT), graudit (MIT), PayloadsAllTheThings (MIT)
# ===========================================================================

import re as _re2  # second alias for patterns with complex escaping


# â”€â”€ 1. NoSQL Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_nosql_injection(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect NoSQL injection: user-controlled input flowing into MongoDB
    operator position ($where, $ne, $gt, $nin) or find/aggregate calls.
    Sources: njsscan nosql_injection.yaml (MIT), PayloadsAllTheThings (MIT).
    Pattern: request input assigned to a dict used in .find()/.find_one()/
             .aggregate()/.update*() without sanitization.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _NOSQL_SINKS = frozenset({
        "find", "find_one", "find_one_and_update", "find_one_and_delete",
        "find_one_and_replace", "aggregate", "update", "update_one",
        "update_many", "delete_one", "delete_many", "replace_one",
        "count_documents", "distinct",
    })
    _REQUEST_SOURCES = frozenset({"request", "req"})
    _REQUEST_ATTRS   = frozenset({
        "args", "form", "json", "data", "get_json", "params", "values",
    })
    _NOSQL_OPERATORS = {"$where", "$ne", "$gt", "$lt", "$gte", "$lte",
                        "$nin", "$in", "$exists", "$regex", "$expr"}

    if tree is not None:
        tainted: dict[str, int] = {}

        def _is_req(node: ast.AST) -> bool:
            if not isinstance(node, ast.Call):
                return False
            f = node.func
            if isinstance(f, ast.Attribute):
                v = f.value
                if isinstance(v, ast.Attribute):
                    return (isinstance(v.value, ast.Name)
                            and v.value.id in _REQUEST_SOURCES
                            and v.attr in _REQUEST_ATTRS)
                if isinstance(v, ast.Name) and v.id in _REQUEST_SOURCES:
                    return True
            return False

        def _has_taint(node: ast.AST) -> bool:
            return _is_req(node) or any(
                isinstance(ch, ast.Name) and ch.id in tainted
                for ch in ast.walk(node)
            )

        class _Taint(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if _has_taint(node.value):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            tainted[t.id] = node.lineno
                self.generic_visit(node)

        class _Sink(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                method = func.attr if isinstance(func, ast.Attribute) else ""
                if method in _NOSQL_SINKS and node.args:
                    arg = node.args[0]
                    if _has_taint(arg):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"NoSQL injection: user-controlled value reaches "
                                f".{method}() at line {node.lineno} â€” "
                                f"attacker can inject $where/$ne/$gt operators"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "from bson import ObjectId\n"
                                    "# Validate type and use typed parameters:\n"
                                    "db.col.find({'_id': ObjectId(user_id)})  "
                                    "# never pass raw user dicts"
                                ),
                            },
                        ))
                self.generic_visit(node)

        _Taint().visit(tree)
        _Sink().visit(tree)

    # Heuristic fallback for non-Python content only.
    if not detections and tree is None:
        nosql_pat = _re2.compile(
            r'["\'](\$where|\$ne|\$gt|\$lt|\$nin|\$regex)["\']'
            r'.*(?:request|req|input|user|param)',
            _re2.IGNORECASE | _re2.DOTALL,
        )
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'["\'](\$where|\$ne|\$gt|\$nin)["\']', line):
                detections.append(_Detection(
                    lineno=i,
                    message=(
                        f"NoSQL operator literal at line {i} â€” "
                        f"verify value is not user-controlled"
                    ),
                    evidence={
                        "rewrite_candidate":
                            "Validate and cast user input before use in queries"
                    },
                ))
                break
    return detections




# â”€â”€ 2. Trojan Source â€” Bidirectional Unicode â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

_BIDI_CHARS = frozenset({
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # LRE/RLE/PDF/LRO/RLO
    "\u2066", "\u2067", "\u2068", "\u2069",              # LRI/RLI/FSI/PDI
    "\u200e", "\u200f",                                   # LRM/RLM
})




def _detect_trojan_source(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect bidirectional Unicode characters that can disguise malicious code.
    CVE-2021-42574 â€” affects all languages.
    Source: gosec trojansource.go (Apache-2.0), eslint detect-bidi-characters (Apache-2.0).
    """
    detections: list[_Detection] = []
    for i, line in enumerate(content.splitlines(), 1):
        for ch in line:
            if ch in _BIDI_CHARS:
                detections.append(_Detection(
                    lineno=i,
                    message=(
                        f"Trojan source: bidirectional Unicode character "
                        f"U+{ord(ch):04X} at line {i} â€” "
                        f"can disguise logic so reviewers see different code than compiler"
                    ),
                    evidence={
                        "rewrite_candidate":
                            "Remove all bidirectional control characters from source files; "
                            "configure editor to display/reject them"
                    },
                ))
                break  # one detection per line is enough
    return detections




# â”€â”€ 3. Zip Slip â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_zip_slip(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect unsafe archive extraction: zipfile.extractall() or tarfile.extractall()
    without path sanitization â€” allows writing to arbitrary filesystem paths.
    Source: graudit python.db (MIT), njsscan zip_path_overwrite.yaml (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    _SAFE_GUARDS = frozenset({"basename", "abspath", "realpath", "commonpath", "commonprefix"})

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "extractall":
                    # Check if there's a members/filter arg with path checking
                    has_filter = any(
                        kw.arg in ("members", "filter", "path")
                        for kw in node.keywords
                    )
                    # Check surrounding context for path.basename etc
                    # (simple heuristic â€” no full control flow)
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f".extractall() at line {node.lineno} without verified path "
                            f"sanitization â€” Zip Slip allows writing outside target directory"
                        ),
                        evidence={
                            "rewrite_candidate": (
                                "for member in archive.namelist():\n"
                                "    dest = os.path.realpath(os.path.join(target, member))\n"
                                "    if not dest.startswith(os.path.realpath(target)):\n"
                                "        raise ValueError('Zip Slip detected')\n"
                                "archive.extract(member, target)"
                            ),
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic: detect extractall in non-Python
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if _re2.search(r'\.extractall\s*\(', line):
                detections.append(_Detection(
                    lineno=i,
                    message=f".extractall() at line {i} â€” verify path sanitization (Zip Slip)",
                    evidence={"rewrite_candidate": "Validate each member path before extraction"},
                ))
    return detections




# â”€â”€ 4. JWT None Algorithm â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



