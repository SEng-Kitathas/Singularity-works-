from __future__ import annotations

import ast
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .escalation_gate import EscalationTrigger

# Infrastructure residuals/warns that don't indicate semantic uncertainty.
# These fire on almost all artifacts and should not affect escalation decisions.
_INFRA_RESIDUALS = frozenset({"monitor_seed_generation", "monitor_seed_gen"})
_INFRA_WARN_GATES = frozenset({"runtime.monitor_seed", "runtime.monitor_seed_gen"})

_SENSITIVE_MODULE_PATTERNS = re.compile(
    r'\b(login|logout|authenticate|signup|register|password|token|session|'
    r'jwt|oauth|saml|mfa|totp|csrf|auth|crypt|cipher|hash|hmac|aes|rsa|'
    r'payment|billing|checkout|invoice|credit_card|bank|stripe|paypal|'
    r'admin|superuser|privilege|sudo|root|permission|acl|rbac|'
    r'deserializ|pickle|marshal|yaml\.load|exec|subprocess|shell|popen|'
    r'migrate|seed|fixture|import_data|restore|backup)\b',
    re.IGNORECASE,
)

_DOMAIN_PAYMENT = re.compile(
    r'\b(Decimal|decimal|stripe|paypal|payment|checkout|invoice|price|amount|'
    r'charge|refund|balance|billing)\b')

_DOMAIN_CRYPTO = re.compile(
    r'\b(cipher|aes|rsa|dh|ecdh|ecdsa|hmac|pbkdf2|bcrypt|scrypt|argon2|'
    r'sha[0-9]+|md5|rc4|des|blowfish)\b', re.IGNORECASE)

_DOMAIN_PII = re.compile(
    r'\b(ssn|social_security|dob|date_of_birth|passport|driver_license|'
    r'health_record|medical|hipaa|gdpr|pii|personal_data)\b', re.IGNORECASE)

# ── Effect surface patterns for Class K ──────────────────────────────────

_NETWORK_CALLS = re.compile(
    r'\b(requests\.(get|post|put|patch|delete|head)|'
    r'urllib\.request|httpx\.|aiohttp\.|fetch\(|curl\b|'
    r'http\.Get|http\.Post|net/http)\b')

_HOST_VALIDATION = re.compile(
    r'\b(urlparse|parse_url|ALLOWED|allowlist|whitelist|in_\{|'
    r'\.hostname\s+(?:not\s+)?in\b|validate_host|check_host)\b')

_EXEC_CALLS = re.compile(
    r'\b(subprocess\.(run|Popen|call|check_output)|os\.system|'
    r'os\.popen|commands\.getoutput|shell=True|exec\(|eval\()\b')

_EXEC_ALLOWLIST = re.compile(
    r'\b(ALLOWED_COMMANDS|command_allowlist|allowed_commands|'
    r'in\s+\[.*\]|if\s+cmd\s+(?:not\s+)?in\b)\b')

_FILE_WRITES = re.compile(
    r'\b(open\s*\(.*["\']w["\']|write_text|write_bytes|'
    r'\.write\(|shutil\.copy|Path.*write)\b')

_PATH_NORMALIZATION = re.compile(
    r'\b(os\.path\.realpath|Path\.resolve|normpath|'
    r'startswith.*BASE|abspath)\b')

_TOKEN_ISSUE = re.compile(
    r'\b(jwt\.encode|create_access_token|generate_token|\.sign\(|Bearer)\b')

_EXPIRY_SET = re.compile(
    r'\b(exp|expires|expiry|expires_in|timedelta|'
    r'ExpiresAt|exp=|lifetime)\b')

_AUTH_STATE_MUTATION = re.compile(
    r'\b(login_user|set_cookie.*session|session\[.*(user|auth|role|logged)|'
    r'grant_role|add_to_role|current_user\s*=|request\.user\s*=)\b')

_AUTH_CHECK = re.compile(
    r'\b(login_required|@require_auth|is_authenticated|check_password|'
    r'verify_token|current_user\.is_authenticated|authenticate\()\b')


# ── AST utilities for Class E ──────────────────────────────────────────────

def _safe_parse(code: str) -> ast.AST | None:
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _cyclomatic_complexity(tree: ast.AST) -> int:
    """McCabe complexity: count branches across all callables."""
    count = 1
    branch_nodes = (ast.If, ast.While, ast.For, ast.ExceptHandler,
                    ast.With, ast.AsyncFor, ast.AsyncWith,
                    ast.comprehension, ast.Assert)
    for node in ast.walk(tree):
        if isinstance(node, branch_nodes):
            count += 1
        elif isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
    return count


def _max_call_depth(tree: ast.AST) -> int:
    """Maximum chain of attribute accesses (proxy for call depth)."""
    max_depth = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            depth = 1
            f = node.func
            while isinstance(f, ast.Attribute):
                depth += 1
                f = f.value
            max_depth = max(max_depth, depth)
    return max_depth


def _max_function_lines(code: str) -> int:
    """Longest function in lines."""
    lines = code.splitlines()
    tree = _safe_parse(code)
    if tree is None:
        return 0
    max_lines = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, 'end_lineno', node.lineno)
            max_lines = max(max_lines, end - node.lineno + 1)
    return max_lines


def _has_unresolved_calls(tree: ast.AST) -> bool:
    """Check for calls to names not defined in the module."""
    defined: set[str] = set()
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add((alias.asname or alias.name).split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
    unresolved = called - defined - _BUILTINS
    return len(unresolved) > 0


def _closure_nesting_depth(tree: ast.AST) -> int:
    """Max depth of nested function definitions."""
    def _depth(node: ast.AST, current: int) -> int:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            current += 1
        child_max = current
        for child in ast.iter_child_nodes(node):
            child_max = max(child_max, _depth(child, current))
        return child_max
    return _depth(tree, 0)


def _has_dynamic_dispatch(code: str) -> bool:
    return bool(re.search(
        r'\b(getattr|setattr|__import__|importlib\.import_module|'
        r'Class\.forName|eval\s*\(|exec\s*\()\b', code))


_BUILTINS = frozenset([
    'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
    'sorted', 'reversed', 'list', 'dict', 'set', 'tuple', 'str', 'int',
    'float', 'bool', 'bytes', 'type', 'isinstance', 'issubclass',
    'hasattr', 'getattr', 'setattr', 'delattr', 'callable', 'iter',
    'next', 'open', 'super', 'object', 'property', 'staticmethod',
    'classmethod', 'abs', 'all', 'any', 'bin', 'chr', 'dir', 'divmod',
    'format', 'hash', 'hex', 'id', 'input', 'max', 'min', 'oct', 'ord',
    'pow', 'repr', 'round', 'slice', 'sum', 'vars', 'zip', 'Exception',
    'ValueError', 'TypeError', 'KeyError', 'IndexError', 'RuntimeError',
    'NotImplementedError', 'AttributeError', 'ImportError', 'OSError',
    'IOError', 'FileNotFoundError', 'PermissionError', 'StopIteration',
    'True', 'False', 'None',
])


# ── Alien detection ───────────────────────────────────────────────────────

_CONFIG_AS_CODE = re.compile(
    r'\b(resource\s+"aws_|provider\s+"|\bterraform\b|'
    r'apiVersion:\s*|kind:\s*(Job|CronJob|Deployment)|'
    r'- name:\s*\w+\s*\n\s*uses:|shell:\s*\|)',
    re.MULTILINE)

_QUERY_LANG = re.compile(
    r'\b(query\s*\{|mutation\s*\{|CONSTRUCT\s+\{|SPARQL|'
    r'MATCH\s+\(|MERGE\s+\(|Cypher)\b')

_TEMPLATE_EVAL = re.compile(
    r'\{%\s*(macro|call|set|do|for|if)\s|'
    r'\{\{-?\s*\w+\s*\|.*\}\}|'
    r'<%=|<%\s*\w+')

_OBFUSCATED = re.compile(
    r'(base64\.b64decode\s*\(|'
    r'eval\s*\(\s*(?:base64|bytes|decode|compile)|'
    r'\\x[0-9a-f]{2}(?:\\x[0-9a-f]{2}){8,})')

_POLYGLOT = re.compile(
    r'(<\?php|<script\s|import\s+React|package\s+main\s*\n|'
    r'fn\s+main\(\)\s*\{.*\}|def\s+\w+.*:\s*\n.*SELECT)',
    re.DOTALL)



def _check_k_class(code: str, triggers: list[EscalationTrigger]) -> None:
    """Class K: Effect surface without corresponding validation."""

    # K1: network.outbound without hostname validation
    if _NETWORK_CALLS.search(code) and not _HOST_VALIDATION.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.K, "K1",
            "network.outbound detected without visible hostname/allowlist validation",
            "high",
        ))

    # K2: storage.write without path normalization
    if _FILE_WRITES.search(code) and not _PATH_NORMALIZATION.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.K, "K2",
            "storage.write detected without visible path normalization",
            "moderate",
        ))

    # K3: process.exec without explicit allowlist
    if _EXEC_CALLS.search(code) and not _EXEC_ALLOWLIST.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.K, "K3",
            "process.exec detected without visible allowlist check",
            "high",
        ))

    # K4: token.issue without expiry
    if _TOKEN_ISSUE.search(code) and not _EXPIRY_SET.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.K, "K4",
            "token.issue detected without visible expiry configuration",
            "high",
        ))

    # K5: auth.state mutation without prior auth check
    if _AUTH_STATE_MUTATION.search(code) and not _AUTH_CHECK.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.K, "K5",
            "auth.state mutation detected without visible prior authentication check",
            "high",
        ))
