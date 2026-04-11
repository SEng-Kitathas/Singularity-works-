# complexity_justified: escalation routing keeps coupled risk thresholds in one place to prevent split-brain security policy.
"""
Singularity Works — Escalation Gate
Version: 2026-04-04 · v1.21

Implements the Logic Blueprint Engine escalation decision from
ESCALATION_CRITERIA_SPEC_v0.2.md.

Architecture:
  evaluate(result, code, req, context) → EscalationDecision

  EscalationDecision contains:
    - squeaky_clean: bool (True only if ALL 8 whitelist conditions pass)
    - route_to_lbe: bool (True if not squeaky_clean)
    - triggers: list[EscalationTrigger] with class, reason, confidence
    - squeaky_clean_failures: list[str] — which conditions failed
    - priority: A|B|C|D|E|F|G|H|I|J|K (highest-priority class that fired)

Currently evaluates without the LBE running:
  Condition 1: gate_counts (warn=0, fail=0)
  Condition 2: confidence proxy from recursive_audit flags
  Condition 3: trust gap proxy from falsified gate families
  Condition 4: role coherence — stub (requires LBE path engine)
  Condition 5: unresolved calls via AST walk (Class E4)
  Condition 6: alien score proxy from pattern_ir
  Condition 7: sensitive module family from requirement tags + code patterns
  Condition 8: diff-awareness — stub (requires git integration)

Class E (Structural Complexity) — AST-based, all evaluable now
Class K (Effect Surface Without Validation) — AST-based, all evaluable now
Class I (Residual Density) — from gate_summary.open_residuals
Class H (Alien/Novel) — from pattern analysis
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from singularity_works.orchestration import OrchestrationResult
    from singularity_works.models import Requirement


# ── Data model ────────────────────────────────────────────────────────────

class EscalationClass(str, Enum):
    A = "A"   # Hard — mandatory
    B = "B"   # Strong — automatic in standard mode
    C = "C"   # Soft — optional/deferred
    D = "D"   # Manual — operator-commanded
    E = "E"   # Structural Complexity
    F = "F"   # Semantic Role Mismatch
    G = "G"   # Temporal/Concurrent Patterns
    H = "H"   # Alien/Novel Input
    I = "I"   # Residual Obligation Density
    J = "J"   # Domain-Specific Mandatory Review
    K = "K"   # Effect Surface Without Validation

    @property
    def priority_rank(self) -> int:
        """Lower = higher priority. A=0, B=1, ... K=10."""
        return list(EscalationClass).index(self)


@dataclass
class EscalationTrigger:
    escalation_class: EscalationClass
    trigger_id: str          # e.g. "A2", "K1", "E1"
    reason: str
    confidence: str          # certain|high|moderate|low
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class EscalationDecision:
    squeaky_clean: bool
    route_to_lbe: bool
    triggers: list[EscalationTrigger]
    squeaky_clean_failures: list[str]
    priority: str            # highest-class letter that fired, or "none"
    summary: str             # human-readable one-liner

    def to_dict(self) -> dict:
        return {
            "squeaky_clean": self.squeaky_clean,
            "route_to_lbe": self.route_to_lbe,
            "priority": self.priority,
            "trigger_count": len(self.triggers),
            "triggers": [
                {
                    "class": t.escalation_class.value,
                    "trigger_id": t.trigger_id,
                    "reason": t.reason,
                    "confidence": t.confidence,
                    "evidence_refs": t.evidence_refs,
                }
                for t in self.triggers
            ],
            "squeaky_clean_failures": self.squeaky_clean_failures,
            "summary": self.summary,
        }


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


# ── Main evaluator ────────────────────────────────────────────────────────

def evaluate(
    result: "OrchestrationResult",
    code: str,
    requirement: "Requirement",
    context: dict | None = None,
) -> EscalationDecision:
    """
    Evaluate whether a gate result warrants LBE escalation.

    Parameters
    ----------
    result      : OrchestrationResult from orc.run()
    code        : original source code artifact
    requirement : Requirement object
    context     : optional dict with keys: is_diff, module_family, author_trusted

    Returns EscalationDecision.
    """
    ctx = context or {}
    triggers: list[EscalationTrigger] = []
    sc_failures: list[str] = []

    assurance = result.assurance
    audit = result.recursive_audit or {}
    gate_counts = audit.get("gate_counts", {})
    naivety_flags = audit.get("naivety_flags", [])
    assurance_dict = assurance.to_dict()
    falsified = assurance_dict.get("falsified", [])
    residual = assurance_dict.get("residual", [])

    gate_summary = result.gate_summary
    open_residuals: list = []
    gate_results: list = []
    if gate_summary is not None:
        open_residuals = getattr(gate_summary, "open_residuals", [])
        gate_results = getattr(gate_summary, "results", [])

    # Filter infrastructure noise — monitor_seed fires on all artifacts and
    # represents "no specific monitor assigned", not a semantic residual.
    semantic_residuals = [r for r in open_residuals if r not in _INFRA_RESIDUALS]
    assurance_residuals = [r for r in residual if r not in _INFRA_RESIDUALS]
    semantic_warns = [gr for gr in gate_results
                      if gr.status == "warn" and gr.gate_id not in _INFRA_WARN_GATES]

    warns = len(semantic_warns)
    fails = gate_counts.get("fail", 0)
    residual_count = len(semantic_residuals) + len(assurance_residuals)

    req_text_lower = requirement.text.lower()
    req_tags = set(getattr(requirement, "tags", []))
    code_lower = code.lower()

    # ── Parse code once ───────────────────────────────────────────────
    tree = _safe_parse(code)

    # ════════════════════════════════════════════════════════════════════
    # SQUEAKY CLEAN WHITELIST — 8 conditions
    # ════════════════════════════════════════════════════════════════════

    # Condition 1: no warn, no fail, no residual
    if warns > 0 or fails > 0 or residual_count > 0:
        sc_failures.append(
            f"condition_1_gate_not_clean: warn={warns} fail={fails} residual={residual_count}")

    # Condition 2: confidence proxy
    # "recovery_not_high_confidence" in naivety_flags → not proven/high-confidence
    # We proxy: if audit says low recovery_confidence AND fails>0 → not confident
    if audit.get("recovery_confidence") == "low" and fails > 0:
        sc_failures.append("condition_2_confidence_not_high")

    # Condition 3: trust gap proxy
    # Falsified gate families that involve trust/wrapper claims indicate trust gap
    trust_related_falsified = [
        f for f in falsified
        if any(k in f for k in ("trust", "wrapper", "safe_", "sanitiz", "validate_"))
    ]
    if trust_related_falsified:
        sc_failures.append(
            f"condition_3_trust_gap: {trust_related_falsified[:2]}")

    # Condition 4: role coherence — stub pending LBE path engine
    # Will be populated once role inference is available.

    # Condition 5: unresolved call targets
    if tree is not None and _has_unresolved_calls(tree):
        sc_failures.append("condition_5_unresolved_calls")

    # Condition 6: alien score
    if (_CONFIG_AS_CODE.search(code) or _QUERY_LANG.search(code) or
            _TEMPLATE_EVAL.search(code) or _OBFUSCATED.search(code) or
            _POLYGLOT.search(code)):
        sc_failures.append("condition_6_alien_content_detected")

    # Condition 7: sensitive module family
    if (_SENSITIVE_MODULE_PATTERNS.search(code) or
            req_tags & {"auth", "crypto", "payment", "admin", "deserialization"}):
        sc_failures.append("condition_7_sensitive_module_family")

    # Condition 8: diff-awareness — stub pending git integration
    if ctx.get("is_diff") and ctx.get("touches_verified_invariant"):
        sc_failures.append("condition_8_diff_touches_verified_invariant")

    # ════════════════════════════════════════════════════════════════════
    # CLASS A: HARD ESCALATION
    # ════════════════════════════════════════════════════════════════════

    if assurance.status == "red":
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A1",
            f"Forge result is red: falsified={falsified[:3]}",
            "certain", falsified[:5],
        ))

    if residual_count > 0:
        semantic_all = semantic_residuals + assurance_residuals
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A2",
            f"Residual obligations present ({residual_count}): {semantic_all[:3]}",
            "certain", semantic_all[:5],
        ))

    if _OBFUSCATED.search(code) or _POLYGLOT.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A3",
            "Alien/novel input: obfuscated content or polyglot artifact",
            "high",
        ))

    if warns > 0:
        warn_gates = [gr.gate_id for gr in gate_results if gr.status == "warn"]
        triggers.append(EscalationTrigger(
            EscalationClass.A, "A_WARN",
            f"Gate warnings present ({warns}): {warn_gates[:3]}",
            "certain", warn_gates[:5],
        ))

    # A7/A8: suspicious-clean — high complexity but green
    if tree is not None and assurance.status == "green":
        cc = _cyclomatic_complexity(tree)
        if cc > 15 and fails == 0 and warns == 0:
            triggers.append(EscalationTrigger(
                EscalationClass.A, "A8",
                f"Suspicious-clean: cyclomatic_complexity={cc} but all gates pass",
                "moderate", [f"cc={cc}"],
            ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS B: STRONG ESCALATION
    # ════════════════════════════════════════════════════════════════════

    if (assurance.status == "green"
            and "residual_obligations_present" in naivety_flags
            and residual_count > 0):  # only if semantic residuals remain after infra filter
        triggers.append(EscalationTrigger(
            EscalationClass.B, "B2",
            "Unknown-heavy path: residual_obligations_present in naivety_flags despite green status",
            "high",
        ))

    if _SENSITIVE_MODULE_PATTERNS.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.B, "B4",
            "Code touches sensitive module family (auth/crypto/payment/exec/deserialization)",
            "high",
        ))

    # B7: effect surface without corresponding validation
    _check_k_class(code, triggers)  # Class K shares the B-severity routing concept

    # ════════════════════════════════════════════════════════════════════
    # CLASS E: STRUCTURAL COMPLEXITY
    # ════════════════════════════════════════════════════════════════════

    if tree is not None:
        cc = _cyclomatic_complexity(tree)
        if cc > 20:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E1",
                f"Cyclomatic complexity {cc} exceeds hard threshold (20)",
                "certain", [f"cc={cc}"],
            ))
        elif cc > 10:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E1_soft",
                f"Cyclomatic complexity {cc} exceeds soft threshold (10)",
                "moderate", [f"cc={cc}"],
            ))

        call_depth = _max_call_depth(tree)
        if call_depth > 8:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E2",
                f"Call chain depth {call_depth} exceeds hard threshold (8)",
                "high", [f"call_depth={call_depth}"],
            ))

        fn_lines = _max_function_lines(code)
        if fn_lines > 150:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E3",
                f"Longest function {fn_lines} lines exceeds hard threshold (150)",
                "certain", [f"max_fn_lines={fn_lines}"],
            ))
        elif fn_lines > 60:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E3_soft",
                f"Longest function {fn_lines} lines exceeds soft threshold (60)",
                "moderate", [f"max_fn_lines={fn_lines}"],
            ))

        if _has_unresolved_calls(tree):
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E4",
                "Unresolved external call targets in critical path",
                "moderate",
            ))

        closure_depth = _closure_nesting_depth(tree)
        if closure_depth > 3:
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E5",
                f"Closure nesting depth {closure_depth} exceeds threshold (3)",
                "high", [f"closure_depth={closure_depth}"],
            ))

        if _has_dynamic_dispatch(code):
            triggers.append(EscalationTrigger(
                EscalationClass.E, "E6",
                "Reflection or dynamic import detected",
                "high",
            ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS H: ALIEN / NOVEL INPUT
    # ════════════════════════════════════════════════════════════════════

    if _CONFIG_AS_CODE.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H2",
            "Config-as-code with execution semantics detected (Terraform/k8s/Actions)",
            "high",
        ))

    if _QUERY_LANG.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H3",
            "Query language with injection surface detected (GraphQL/SPARQL/Cypher)",
            "high",
        ))

    if _TEMPLATE_EVAL.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H4",
            "Template language with eval semantics detected (Jinja2/Twig/ERB)",
            "high",
        ))

    if _OBFUSCATED.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.H, "H6",
            "Encoded or obfuscated content detected",
            "certain",
        ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS I: RESIDUAL OBLIGATION DENSITY
    # ════════════════════════════════════════════════════════════════════

    if residual_count > 3:
        triggers.append(EscalationTrigger(
            EscalationClass.I, "I2",
            f"High residual obligation density: {residual_count} residuals",
            "certain", (open_residuals + residual)[:5],
        ))

    # ════════════════════════════════════════════════════════════════════
    # CLASS J: DOMAIN-SPECIFIC MANDATORY REVIEW
    # ════════════════════════════════════════════════════════════════════

    if _DOMAIN_CRYPTO.search(code) and re.search(
            r'\bdef\s+\w*(encrypt|decrypt|cipher|hash_|derive_key)\w*', code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J1",
            "Cryptographic primitive implementation detected — never write your own crypto",
            "certain",
        ))

    # J2: weak hash in password storage context — check both argument name and function name
    _WEAK_HASH_FUNC = re.compile(r'\bhashlib\.(md5|sha1|sha256)\s*\(', re.IGNORECASE)
    _PW_CONTEXT = re.compile(r'def\s+\w*(?:store|hash|password|pw|verify|check|auth)\w*\s*\(|'
                             r'\bpassword\b|\bpw\b|\bpasswd\b', re.IGNORECASE)
    if _WEAK_HASH_FUNC.search(code) and _PW_CONTEXT.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J2",
            "Weak hash (MD5/SHA1/SHA256) in password storage context — use bcrypt/argon2",
            "certain",
        ))
    elif re.search(r'\b(md5|sha1|sha256)\s*\(.*password', code, re.IGNORECASE):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J2",
            "Weak hash for password detected",
            "certain",
        ))

    if _DOMAIN_PAYMENT.search(code) and re.search(
            r'\b(float|int)\s*\(.*(?:price|amount|total|charge)', code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J3",
            "Financial calculation using float/int — Decimal required for currency math",
            "high",
        ))

    if _DOMAIN_PII.search(code):
        triggers.append(EscalationTrigger(
            EscalationClass.J, "J4",
            "PII handling code detected — requires privacy review",
            "high",
        ))

    # ════════════════════════════════════════════════════════════════════
    # DECISION
    # ════════════════════════════════════════════════════════════════════

    squeaky_clean = len(sc_failures) == 0
    route_to_lbe = not squeaky_clean or len(triggers) > 0

    # Highest-priority class
    if triggers:
        best = min(triggers, key=lambda t: t.escalation_class.priority_rank)
        priority = best.escalation_class.value
    else:
        priority = "none"

    # Summary
    if squeaky_clean and not triggers:
        summary = "Squeaky clean — LBE not required"
    elif assurance.status == "red":
        summary = f"Class {priority}: gate failed — LBE mandatory ({len(falsified)} falsified)"
    else:
        top = triggers[0] if triggers else None
        summary = (
            f"Class {priority}: {top.trigger_id} — {top.reason[:80]}"
            if top else "LBE recommended"
        )

    return EscalationDecision(
        squeaky_clean=squeaky_clean,
        route_to_lbe=route_to_lbe,
        triggers=triggers,
        squeaky_clean_failures=sc_failures,
        priority=priority,
        summary=summary,
    )


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
