from __future__ import annotations

import ast
import re as _re

from .models import Artifact, MonitorSeed
from .monitoring_core import _safe_parse


def _auth_endpoint_rate_limited(content: str) -> tuple[bool, str]:
    """
    Auth endpoints must implement rate limiting to prevent brute-force attacks.

    Checks for presence of any rate-limiting signal in auth-like functions:
    - Import of flask_limiter, slowapi, ratelimit, django-ratelimit
    - @limiter.limit / @ratelimit / @throttle decorators
    - sleep() / time.sleep() (cheap man's rate limiting)
    - Any call to check_rate_limit / rate_limit / throttle

    This is a negative check: if an auth function has none of these, it fires.
    """
    tree = _safe_parse(content)
    if tree is None:
        return False, "content must parse for rate-limit monitor"

    _AUTH_FUNC_KEYWORDS = {"login", "signin", "authenticate", "verify_password",
                           "check_password", "validate_credentials"}
    _RATE_LIMIT_IMPORTS = {"flask_limiter", "slowapi", "ratelimit", "limits",
                           "django_ratelimit", "throttle", "redis"}
    _RATE_LIMIT_CALLS  = {"rate_limit", "ratelimit", "throttle", "check_rate_limit",
                          "is_rate_limited", "sleep", "time_sleep"}
    _RATE_LIMIT_DECO   = {"limit", "ratelimit", "throttle", "rate_limit", "shared_limit"}

    # Check imports first — if rate limiting library present anywhere, pass
    import_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_names.add(alias.name.split(".")[0].lower())
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_names.add(node.module.split(".")[0].lower())

    if import_names & _RATE_LIMIT_IMPORTS:
        return True, "rate-limiting library imported"

    # Find auth-like functions and check for rate limiting signals within them
    failures: list[str] = []
    relevant_seen = False

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(k in node.name.lower() for k in _AUTH_FUNC_KEYWORDS):
            continue
        relevant_seen = True

        # Check decorators
        has_rate_limit = False
        for deco in node.decorator_list:
            deco_name = ""
            if isinstance(deco, ast.Name):
                deco_name = deco.id.lower()
            elif isinstance(deco, ast.Attribute):
                deco_name = deco.attr.lower()
            elif isinstance(deco, ast.Call):
                func = deco.func
                deco_name = (func.id if isinstance(func, ast.Name)
                             else func.attr if isinstance(func, ast.Attribute)
                             else "").lower()
            if deco_name in _RATE_LIMIT_DECO:
                has_rate_limit = True
                break

        if has_rate_limit:
            continue

        # Check calls inside function body
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            fname = (func.id if isinstance(func, ast.Name)
                     else func.attr if isinstance(func, ast.Attribute)
                     else "").lower()
            if fname in _RATE_LIMIT_CALLS:
                has_rate_limit = True
                break

        if not has_rate_limit:
            failures.append(
                f"{node.name}: auth function with no rate-limiting — "
                f"vulnerable to brute-force credential stuffing"
            )

    if not relevant_seen:
        return True, "no auth-like function found"
    if failures:
        return False, "; ".join(failures[:3])
    return True, "auth functions have rate-limiting controls"


def _must_rate_limit_auth_endpoint(artifact: "Artifact", seed: "MonitorSeed") -> tuple[bool, str]:
    return _auth_endpoint_rate_limited(artifact.content)




# ── IDOR / Object Ownership Monitor ──────────────────────────────────────────
#
# Detects: functions that accept a resource ID from an external source
# (request args, route path params) and perform a database access
# without an ownership check — the canonical IDOR pattern.
#
# "User can reach the action" ≠ "User owns the object being acted on."
#
# Ownership signals accepted:
#   - current_user.id comparison
#   - owner_id in DB query filter
#   - abort(403) / PermissionDenied raise
#   - @owner_required decorator
#   - g.user / request.user check

_IDOR_REQUEST_ID = _re.compile(
    r'\b(?:request\.(?:args|form|json|view_args|data|values)\s*'
    r'(?:\.|\.get\s*\(|\[)|request\.get_json\s*\(\s*\))',
    _re.IGNORECASE,
)

_IDOR_ROUTE_DECORATOR = _re.compile(
    r'@(?:app|bp|router|api)\.(?:route|get|post|put|patch|delete)\b|'
    r'@require_http_methods\b',
    _re.IGNORECASE,
)

_IDOR_ROUTE_ID_PARAM = _re.compile(r'\b\w+_id\b')

_IDOR_DB_ACCESS = _re.compile(
    r'\b(?:\.get\s*\(|\.filter_by\s*\(|\.filter\s*\(|'
    r'\.find\s*\(|\.find_one\s*\(|\.query\s*\(|'
    r'\.objects\s*\.|SELECT\b)',
    _re.IGNORECASE,
)

_IDOR_OWNERSHIP = _re.compile(
    r'\b(?:current_user\.id\b|'
    r'g\.user(?:\.id)?\b|'
    r'request\.user(?:\.id)?\b|'
    r'owner_id\b|'
    r'user_id\s*==|'
    r'=\s*current_user\b|'
    r'filter_by\s*\(.*owner|'
    r'\.filter\s*\(.*owner_id\s*==\s*current_user|'
    r'check_ownership\b|verify_ownership\b|is_owner\b|'
    r'@owner_required\b|'
    r'abort\s*\(\s*403\b|'
    r'raise\s+(?:Forbidden|PermissionDenied|Http403|HTTPException))',
    _re.IGNORECASE,
)


def _object_ownership_enforced(content: str) -> tuple[bool, str]:
    """
    Resource access via external ID must enforce object-level ownership.

    Fires when a function:
    1. Receives a resource ID from request args/form/json OR a route path param
    2. Performs a database access
    3. Does NOT have a visible ownership check

    Returns (True, reason) if ownership is enforced or not applicable.
    Returns (False, reason) if IDOR pattern is detected.
    """
    # Quick pass — if no DB access at all, not applicable
    if not _IDOR_DB_ACCESS.search(content):
        return True, "no database access detected"

    has_request_id = bool(_IDOR_REQUEST_ID.search(content))
    has_route_id = (bool(_IDOR_ROUTE_DECORATOR.search(content)) and
                    bool(_IDOR_ROUTE_ID_PARAM.search(content)))

    resource_id_surface = has_request_id or has_route_id

    if not resource_id_surface:
        return True, "no externally-supplied resource ID detected"

    has_ownership = bool(_IDOR_OWNERSHIP.search(content))
    if has_ownership:
        return True, "object-level ownership check detected"

    source = "request parameter" if has_request_id else "route path parameter"
    return (
        False,
        f"resource ID from {source} used in database access "
        f"without visible ownership check — "
        f"any authenticated user may access any object (IDOR)"
    )


def _must_enforce_object_ownership(
    artifact: "Artifact", seed: "MonitorSeed"
) -> tuple[bool, str]:
    return _object_ownership_enforced(artifact.content)


