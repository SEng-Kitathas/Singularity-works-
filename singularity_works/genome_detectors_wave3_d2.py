from __future__ import annotations

import ast
import re as _re_ext
import re as _re2
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

def _detect_paramiko_auto_add_policy(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect paramiko SSH client with AutoAddPolicy â€” blindly accepts any host key,
    susceptible to MITM. Source: graudit python.db (MIT), gosec ssh.go (Apache-2.0).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if (isinstance(func, ast.Attribute)
                        and func.attr == "set_missing_host_key_policy"):
                    for arg in node.args:
                        # arg can be: Attribute (paramiko.AutoAddPolicy),
                        #             Name (AutoAddPolicy), or
                        #             Call (paramiko.AutoAddPolicy())
                        name = ""
                        if isinstance(arg, ast.Attribute):
                            name = arg.attr
                        elif isinstance(arg, ast.Name):
                            name = arg.id
                        elif isinstance(arg, ast.Call):
                            fn = arg.func
                            name = (fn.attr if isinstance(fn, ast.Attribute)
                                    else fn.id if isinstance(fn, ast.Name) else "")
                        if "AutoAddPolicy" in name:
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"paramiko AutoAddPolicy at line {node.lineno} â€” "
                                    f"SSH host key not verified, MITM possible"
                                ),
                                evidence={
                                    "rewrite_candidate": (
                                        "client.set_missing_host_key_policy(paramiko.RejectPolicy())\n"
                                        "client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))"
                                    ),
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)

    # Heuristic â€” non-Python only
    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if "AutoAddPolicy" in line:
                detections.append(_Detection(
                    lineno=i,
                    message=f"SSH AutoAddPolicy at line {i} â€” host key not verified",
                    evidence={"rewrite_candidate": "Use RejectPolicy and load known_hosts"},
                ))
    return detections




# â”€â”€ 15. urllib3 disable_warnings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_urllib3_disable_warnings(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect urllib3.disable_warnings() â€” suppresses InsecureRequestWarning,
    hiding TLS verification failures from logs. Source: graudit python.db (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "disable_warnings":
                    if isinstance(func.value, ast.Name) and func.value.id == "urllib3":
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"urllib3.disable_warnings() at line {node.lineno} â€” "
                                f"suppresses InsecureRequestWarning, hides TLS failures"
                            ),
                            evidence={
                                "rewrite_candidate": (
                                    "Fix the underlying TLS issue instead of silencing warnings.\n"
                                    "If using self-signed certs in dev: pass verify='/path/to/ca-bundle.crt'"
                                ),
                            },
                        ))
                self.generic_visit(node)
        _V().visit(tree)

    if not detections and tree is None:
        for i, line in enumerate(content.splitlines(), 1):
            if "urllib3.disable_warnings" in line or "disable_warnings()" in line:
                detections.append(_Detection(
                    lineno=i,
                    message=f"urllib3.disable_warnings() at line {i} â€” hides TLS errors",
                    evidence={"rewrite_candidate": "Fix the TLS configuration instead"},
                ))
    return detections




# â”€â”€ 16. SQLite enable_load_extension â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_sqlite_load_extension(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect sqlite3.enable_load_extension(True) â€” allows loading shared libraries
    via SQL, enabling code execution. Source: graudit python.db (MIT).
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "enable_load_extension":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and arg.value is True:
                            detections.append(_Detection(
                                lineno=node.lineno,
                                message=(
                                    f"enable_load_extension(True) at line {node.lineno} â€” "
                                    f"allows SQL to load shared libraries (code execution)"
                                ),
                                evidence={
                                    "rewrite_candidate":
                                        "Never enable load_extension in production; "
                                        "use Python functions registered via create_function() instead"
                                },
                            ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections




# â”€â”€ 17. DES / RC4 Cipher Usage â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_weak_cipher(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect DES, 3DES, RC4, RC2 cipher usage â€” all cryptographically broken.
    Source: gosec weakcrypto.go (Apache-2.0) G405.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    _WEAK_CIPHERS = frozenset({
        "DES", "TripleDES", "ARC2", "ARC4", "RC2", "RC4",
        "Blowfish", "CAST",
    })

    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Attribute(self, node: ast.Attribute) -> None:
                if node.attr in _WEAK_CIPHERS:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Weak cipher '{node.attr}' at line {node.lineno} â€” "
                            f"cryptographically broken; use AES-256-GCM"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "from cryptography.hazmat.primitives.ciphers.aead import AESGCM\n"
                                "key = AESGCM.generate_key(bit_length=256)"
                        },
                    ))
                self.generic_visit(node)
        _V().visit(tree)

    if not detections and tree is None:
        pat = _re2.compile(
            r'\b(?:DES|TripleDES|3DES|RC4|ARC4|RC2|ARC2|Blowfish)\b',
        )
        for i, line in enumerate(content.splitlines(), 1):
            if pat.search(line):
                m = pat.search(line)
                detections.append(_Detection(
                    lineno=i,
                    message=f"Weak cipher '{m.group()}' at line {i} â€” use AES-256-GCM",
                    evidence={"rewrite_candidate": "Use AES-256-GCM from the cryptography package"},
                ))
    return detections




# â”€â”€ 18. Decompression Bomb â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_decompression_bomb(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect shutil.copyfileobj / io.copy without size limit after opening
    a compressed reader â€” decompression bomb allows DoS.
    Source: gosec decompression_bomb.go (Apache-2.0) G110.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    _DECOMPRESSOR_OPENS = frozenset({
        "GzipFile", "open", "BZ2File", "LZMAFile", "ZipFile",
    })
    _COPY_FNS = frozenset({"copyfileobj", "copy", "copy2", "copyfile"})

    if tree is not None:
        opened_decompressed: set[str] = set()

        class _OpenVisitor(ast.NodeVisitor):
            def _check_call(self, call: ast.Call, target_name: str) -> None:
                fn = call.func
                name = (fn.attr if isinstance(fn, ast.Attribute)
                        else fn.id if isinstance(fn, ast.Name) else "")
                mod = (fn.value.id if isinstance(fn, ast.Attribute)
                       and isinstance(fn.value, ast.Name) else "")
                if name in _DECOMPRESSOR_OPENS and mod in (
                    "gzip", "bz2", "lzma", "zipfile", "tarfile"
                ):
                    opened_decompressed.add(target_name)

            def visit_Assign(self, node: ast.Assign) -> None:
                if isinstance(node.value, ast.Call):
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            self._check_call(node.value, tgt.id)
                # Propagate: gz = src where src is already tracked
                elif isinstance(node.value, ast.Name):
                    if node.value.id in opened_decompressed:
                        for tgt in node.targets:
                            if isinstance(tgt, ast.Name):
                                opened_decompressed.add(tgt.id)
                self.generic_visit(node)

            def visit_With(self, node: ast.With) -> None:
                # with gzip.open(path) as src:
                for item in node.items:
                    if (isinstance(item.context_expr, ast.Call)
                            and item.optional_vars is not None
                            and isinstance(item.optional_vars, ast.Name)):
                        self._check_call(item.context_expr, item.optional_vars.id)
                self.generic_visit(node)

        class _CopyVisitor(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                fn   = (func.attr if isinstance(func, ast.Attribute)
                        else func.id if isinstance(func, ast.Name) else "")
                if fn in _COPY_FNS:
                    # Check if any arg is a decompressed reader
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id in opened_decompressed:
                            # Check if length arg provided (copyfileobj has length param)
                            has_length = any(
                                kw.arg == "length" for kw in node.keywords
                            ) or len(node.args) >= 3
                            if not has_length:
                                detections.append(_Detection(
                                    lineno=node.lineno,
                                    message=(
                                        f"{fn}() with decompressed reader at line "
                                        f"{node.lineno} without size limit â€” "
                                        f"decompression bomb allows DoS"
                                    ),
                                    evidence={
                                        "rewrite_candidate": (
                                            "shutil.copyfileobj(src, dst, length=65536)  "
                                            "# limit chunk size\n"
                                            "# Or track total bytes and raise if > threshold"
                                        ),
                                    },
                                ))
                self.generic_visit(node)

        _OpenVisitor().visit(tree)
        _CopyVisitor().visit(tree)

    return detections





# ===========================================================================
# v1.35.1 â€” HTTP Request Smuggling, OAuth token exposure, DOMPurify bypass,
#            weak JWT secret length, account enumeration timing
# ===========================================================================

# â”€â”€ HTTP Request Smuggling (CL.TE / TE.CL ambiguity) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



