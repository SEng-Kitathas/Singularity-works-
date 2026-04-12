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

def _detect_jwt_algorithm_confusion(
    content: str,
    _spec: dict,
    *,
    semantic_ir: "Any | None" = None,
) -> list[_Detection]:
    """
    JWT algorithm confusion: jwt.decode() called without explicit algorithms=[],
    or with algorithms=['none'], allows attackers to strip signature verification.

    CVE-2015-9235 class. python-jwt, PyJWT < 2.4.0 all vulnerable without algorithms=.
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is None:
        return detections

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "decode":
            continue
        # Check caller is jwt-like
        caller = func.value
        caller_name = (caller.id if isinstance(caller, ast.Name)
                       else caller.attr if isinstance(caller, ast.Attribute)
                       else "")
        if "jwt" not in caller_name.lower() and "token" not in caller_name.lower():
            continue

        kw_map = {kw.arg: kw.value for kw in node.keywords if kw.arg}
        algo_node = kw_map.get("algorithms")
        options_node = kw_map.get("options")

        # No algorithms= kwarg at all
        if algo_node is None:
            detections.append(_Detection(
                lineno=node.lineno,
                message=(
                    f"JWT algorithm confusion at line {node.lineno}: "
                    f"jwt.decode() called without explicit algorithms= parameter â€” "
                    f"attacker can supply 'none' algorithm or switch RS256â†’HS256"
                ),
                evidence={
                    "rewrite_candidate": (
                        "Always specify algorithms=[\"HS256\"] or [\"RS256\"] â€” "
                        "never allow the token header to dictate the algorithm"
                    ),
                },
            ))
            continue

        # algorithms=['none'] or ["None"]
        if isinstance(algo_node, ast.List):
            for elt in algo_node.elts:
                if isinstance(elt, ast.Constant) and str(elt.value).lower() in ("none", ""):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"JWT algorithm confusion at line {node.lineno}: "
                            f"algorithms=['none'] explicitly permits unsigned tokens"
                        ),
                        evidence={
                            "rewrite_candidate": "Remove 'none' from algorithms= list",
                        },
                    ))

        # options={'verify_signature': False}
        if isinstance(options_node, ast.Dict):
            for k, v in zip(options_node.keys, options_node.values):
                if (isinstance(k, ast.Constant) and k.value == "verify_signature"
                        and isinstance(v, ast.Constant) and v.value is False):
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"JWT verification disabled at line {node.lineno}: "
                            f"options={{\"verify_signature\": False}} skips signature check"
                        ),
                        evidence={
                            "rewrite_candidate": "Remove verify_signature=False; always verify",
                        },
                    ))

    return detections




# ---------------------------------------------------------------------------
# HTTP Non-TLS Internal Call Detection
# CWE-319: Cleartext Transmission of Sensitive Information
# Pattern: requests.get("http://...") / http:// literal in network call
# ---------------------------------------------------------------------------



def _detect_http_no_tls(
    content: str,
    _spec: dict,
    *,
    semantic_ir: "Any | None" = None,
) -> list[_Detection]:
    """
    Detect cleartext HTTP (non-TLS) in internal or hardcoded network calls.
    requests.get("http://..."), urllib.request.urlopen("http://...") etc.
    Does NOT flag user-controlled URLs (those are SSRF territory).
    """
    tree = _parse(content)
    detections: list[_Detection] = []
    if tree is None:
        return detections

    _NET_ATTRS = frozenset({"get", "post", "put", "delete", "patch", "request", "urlopen"})
    _NET_MODS  = frozenset({"requests", "httpx", "urllib", "aiohttp", "session"})

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in _NET_ATTRS:
            continue
        caller = func.value
        caller_name = (caller.id if isinstance(caller, ast.Name)
                       else caller.attr if isinstance(caller, ast.Attribute)
                       else "")
        # Also handle urllib.request.urlopen
        if caller_name not in _NET_MODS:
            if isinstance(caller, ast.Attribute) and isinstance(caller.value, ast.Name):
                if caller.value.id not in _NET_MODS:
                    continue
            else:
                continue

        # Check if the first argument is a string literal starting with http://
        url_arg = node.args[0] if node.args else None
        if url_arg is None:
            for kw in node.keywords:
                if kw.arg in ("url",):
                    url_arg = kw.value
                    break
        if url_arg is None:
            continue

        # Only flag LITERAL strings (not variables â€” those are SSRF, not cleartext)
        if not isinstance(url_arg, ast.Constant) or not isinstance(url_arg.value, str):
            continue
        if not url_arg.value.startswith("http://"):
            continue

        detections.append(_Detection(
            lineno=node.lineno,
            message=(
                f"Cleartext HTTP at line {node.lineno}: "
                f"hardcoded 'http://' URL in network call â€” "
                f"use https:// to prevent credential/data interception"
            ),
            evidence={
                "url": url_arg.value[:80],
                "rewrite_candidate": "Change http:// to https:// and enforce TLS verification",
            },
        ))

    return detections




# ---------------------------------------------------------------------------
# Capsule expansion v1.29.1 â€” Bug bounty coverage
# Detectors: XXE, hardcoded secrets, insecure cookie, CORS wildcard,
# CRLF header injection, IDOR gate (wires existing capsules)
# ---------------------------------------------------------------------------

import re as _re_ext  # alias to avoid shadowing the ast-path _re used above


# â”€â”€ XXE â€” XML External Entity Injection â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€



def _detect_xxe(
    content: str, _spec: dict, *, semantic_ir: "Any | None" = None
) -> list[_Detection]:
    """
    Detect unsafe XML parsing that allows external entity expansion.
    Covers: stdlib xml.etree / xml.sax / minidom, lxml without resolve_entities=False,
    expat without entity handlers disabled. defusedxml is the safe alternative.
    """
    tree = _parse(content)
    detections: list[_Detection] = []

    if tree is not None:
        _UNSAFE_XML_MODS = frozenset({
            "xml", "minidom", "ElementTree", "sax", "expat",
        })
        _UNSAFE_XML_CALLS = frozenset({
            "parse", "fromstring", "XML", "fromstringlist",
            "ParseCreate", "ParserCreate", "create_parser",
        })

        class _V(ast.NodeVisitor):
            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    if alias.name.startswith("xml.") and "defusedxml" not in alias.name:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Unsafe XML import '{alias.name}' at line {node.lineno} â€” "
                                f"stdlib xml parsers expand external entities by default"
                            ),
                            evidence={
                                "rewrite_candidate":
                                    "Use defusedxml: import defusedxml.ElementTree as ET",
                            },
                        ))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                mod = node.module or ""
                if mod.startswith("xml.") and "defusedxml" not in mod:
                    detections.append(_Detection(
                        lineno=node.lineno,
                        message=(
                            f"Unsafe XML import from '{mod}' at line {node.lineno} â€” "
                            f"external entity expansion not disabled"
                        ),
                        evidence={
                            "rewrite_candidate":
                                "Use defusedxml: from defusedxml import ElementTree",
                        },
                    ))
                self.generic_visit(node)

        _V().visit(tree)

    # Heuristic fallback â€” catches Rust/Go/Java XML parsers
    if not detections and semantic_ir is not None:
        tokens = getattr(semantic_ir, "semantic_tokens", set())
        if "xxe:unsafe_xml_parse" in tokens:
            detections.append(_Detection(
                lineno=0,
                message="Unsafe XML parsing detected â€” external entity expansion risk",
                evidence={"rewrite_candidate": "Disable DTD/entity processing before parsing"},
            ))
    return detections




# â”€â”€ Hardcoded Secrets / Credentials â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Expanded from detect-secrets DENYLIST (MIT/Apache-2.0) + forge additions.
# Covers multi-language variable naming patterns including Spanish (contraseÃ±a).
_SECRET_NAMES = _re_ext.compile(
    r'\b(?:'
    # Core credential names (detect-secrets denylist)
    r'api_?key|auth_?key|service_?key|account_?key|db_?key|database_?key|'
    r'priv_?key|private_?key|client_?key|'
    r'db_?pass|database_?pass|key_?pass|'
    r'password|passwd|pwd|secret|'
    # Spanish/multilingual (detect-secrets)
    r'contrase[Ã±n]a|'
    # Extended forge additions
    r'apikey|access_token|auth_token|'
    r'client_secret|database_url|db_password|'
    r'jwt_secret|encryption_key|signing_key|'
    r'bearer_token|credentials|'
    # Common env var patterns
    r'secret_key|app_secret|master_key|'
    r'stripe_key|twilio_token|sendgrid_key|'
    r'github_token|gitlab_token|slack_token|'
    r'aws_secret|gcp_key|azure_key|'
    r'oauth_secret|refresh_token|session_secret'
    r')\b',
    _re_ext.IGNORECASE,
)
_SECRET_VALUE = _re_ext.compile(
    r'(?:'
    # AWS
    r'AKIA[0-9A-Z]{16}|'
    # GitHub PAT
    r'ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82}|'
    # Stripe
    r'sk_live_[A-Za-z0-9]{24,}|'
    # Generic high-entropy string (32+ hex chars or long base64)
    r'[0-9a-fA-F]{32,}|'
    r'[A-Za-z0-9+/]{40,}={0,2}'
    r')'
)




