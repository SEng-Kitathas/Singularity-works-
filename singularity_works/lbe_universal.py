"""
Singularity Works — LBE Universal Structural Reasoner
Version: 2026-04-04 · substrate omega

DESIGN SPIRIT
─────────────
The LBE is not a pattern database. It is a first-principles reasoner.

Given any artifact in any language — Python, Rust, C, Java, Go, JavaScript,
Solidity, COBOL, Terraform HCL, or a completely alien DSL — the LBE must
be able to reason about WHAT THE CODE DOES in terms of:

  1. Where does external, untrusted data enter?       (Trust boundary ingress)
  2. How does that data move?                         (Taint propagation)
  3. Where does it produce effects?                   (Trust boundary egress)
  4. What does the code CLAIM about safety?           (Naming convention trust)
  5. What does the code EARN by actual validation?    (Structural trust)
  6. What obligations exist and are they fulfilled?   (Invariant accounting)

The confidence model is the bridge: Python AST → "parsed" (certainty).
Structural heuristics → "high-confidence inferred". Alien text →
"plausible" or "indeterminate". But ALWAYS produce some analysis.
NEVER fail silently. A low-confidence blob is better than no blob.

UNIVERSAL AXIOMS
────────────────
These hold regardless of language:

  Axiom 1: External data enters through identifiable boundaries.
           (Function params, reads, environment, network, files)

  Axiom 2: Data flows via assignment and argument passing.
           (= := <- ← → let var const set)

  Axiom 3: Effects occur at output boundaries.
           (Writes, executes, returns to caller, mutations)

  Axiom 4: Trust is EARNED by structural validation.
           (Comparison to constants, range checks, type narrowing,
            cryptographic verification, allowlist membership check)

  Axiom 5: Trust is CLAIMED by naming convention.
           (safe_, validated_, escaped_, trusted_, clean_ prefixes/suffixes)

  Axiom 6: Claimed trust without earned trust = wrapper theater.

  Axiom 7: Structural obligations must be discharged.
           (Acquire → release, input → validate → use, alloc → free)

ARCHITECTURE
────────────
  UniversalIR                — language-agnostic semantic graph
  UniversalLowering          — text → UniversalIR (structural heuristics)
  UniversalPathWalker        — UniversalIR → paths (taint flow)
  UniversalBlobEmitter       — paths → blobs (obligation accounting)
  analyze_universal(code)    → list[dict]  (blob dicts)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL IR
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class UNode:
    """A node in the Universal IR graph."""
    node_id: str
    kind: str           # CALLABLE | SOURCE | TRANSFORM | SINK | VALIDATION |
                        # ASSIGNMENT | CLAIM | UNKNOWN
    label: str          # human-readable description
    line: int
    text: str = ""      # raw text fragment
    confidence: str = "plausible"   # parsed | inferred | plausible | indeterminate


@dataclass
class UTaintFlow:
    """A taint flow path from source to sink."""
    flow_id: str
    source_node: UNode
    sink_node: UNode
    transforms: list[UNode]
    validations: list[UNode]
    claims: list[str]
    earned_trust: list[str]
    # Is the sink reachable without earning trust?
    trust_gap: bool = True
    confidence: str = "plausible"


@dataclass
class UObligation:
    """A structural obligation detected in the code."""
    obligation_id: str
    kind: str       # VALIDATE_BEFORE_USE | RELEASE_AFTER_ACQUIRE |
                    # CONSTANT_TIME_COMPARE | NO_REUSE_AFTER_FREE |
                    # COMMIT_AFTER_WRITE | CHECK_BEFORE_ACCESS
    description: str
    acquisition_line: int
    fulfillment_found: bool = False
    confidence: str = "plausible"


@dataclass
class UniversalIR:
    language_guess: str = "unknown"
    parse_confidence: str = "plausible"
    callables: list[UNode] = field(default_factory=list)
    sources: list[UNode] = field(default_factory=list)
    sinks: list[UNode] = field(default_factory=list)
    transforms: list[UNode] = field(default_factory=list)
    validations: list[UNode] = field(default_factory=list)
    claims: list[UNode] = field(default_factory=list)
    assignments: list[UNode] = field(default_factory=list)
    obligations: list[UObligation] = field(default_factory=list)
    taint_flows: list[UTaintFlow] = field(default_factory=list)
    unknowns: list[UNode] = field(default_factory=list)
    raw_symbols: dict[str, str] = field(default_factory=dict)
    # symbol → assigned_from: dict for taint propagation
    assignment_map: dict[str, list[str]] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE DETECTION
# ══════════════════════════════════════════════════════════════════════════════

_LANG_SIGNALS = [
    ("c",          [r'#include\s*<', r'\bmallocé\b|\bmalloc\s*\(', r'int\s+main\s*\(']),
    ("cpp",        [r'#include\s*<\w+>', r'std::', r'namespace\s+\w+']),
    ("go",         [r'^package\s+\w+', r'\bfunc\s+\w+\s*\(', r':=\s']),
    ("rust",       [r'\bfn\s+\w+\s*\(', r'\blet\s+(?:mut\s+)?\w+', r'\bunsafe\s*\{']),
    ("java",       [r'\bpublic\s+(?:class|interface)', r'\bimport\s+java\.', r'\bSystem\.out\.']),
    ("javascript", [r'\bconst\s+\w+\s*=', r'\bfunction\s+\w+\s*\(', r'\blet\s+\w+\s*=']),
    ("typescript", [r':\s*(?:string|number|boolean|any)\b', r'interface\s+\w+\s*\{', r'=>']),
    ("solidity",   [r'\bpragma\s+solidity\b', r'\bcontract\s+\w+\b', r'\bmapping\s*\(']),
    ("terraform",  [r'\bresource\s+"', r'\bprovider\s+"', r'\bvariable\s+"']),
    ("hcl",        [r'\bresource\s+"', r'\bmodule\s+"', r'\bdata\s+"']),
    ("yaml",       [r'^---\s*$', r'^\s+\w+:\s', r'apiVersion:']),
    ("cobol",      [r'IDENTIFICATION\s+DIVISION', r'PROCEDURE\s+DIVISION', r'\bMOVE\b.*\bTO\b']),
    ("python",     [r'def\s+\w+\s*\(', r'\bimport\s+\w+', r'from\s+\w+\s+import']),
    ("csharp",     [r'\busing\s+System\b', r'\bnamespace\s+\w+', r'public\s+\w+\s+\w+\s*\(']),
    ("php",        [r'<\?php', r'\$\w+\s*=', r'->getParam\b']),
    ("ruby",       [r'\bdef\s+\w+', r'\brequire\s+[\'"]', r'\bend\b']),
    ("swift",      [r'\bfunc\s+\w+\s*\(', r'\bvar\s+\w+\s*:', r'\bimport\s+Foundation']),
    ("kotlin",     [r'\bfun\s+\w+\s*\(', r'\bval\s+\w+\s*=', r'\bdata\s+class\b']),
]


def detect_language(code: str) -> tuple[str, str]:
    """Returns (language, confidence)."""
    best_lang, best_count = "unknown", 0
    for lang, signals in _LANG_SIGNALS:
        count = sum(1 for s in signals if re.search(s, code, re.MULTILINE))
        if count > best_count:
            best_lang, best_count = lang, count
    confidence = "inferred" if best_count >= 2 else "plausible" if best_count == 1 else "indeterminate"
    return best_lang, confidence


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL SOURCE DETECTION  (Axiom 1)
# ══════════════════════════════════════════════════════════════════════════════
#
# Any pattern that indicates externally-controlled data entering the system.
# Language-agnostic — looks for semantic signals, not named APIs.

_SOURCE_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, source_kind, label)

    # HTTP / Web input
    (r'request\s*\.\s*(?:args|form|json|data|values|body|params)\b',
     "HttpParam", "HTTP request parameter"),
    (r'req\s*\.\s*(?:body|params|query|headers)\b',
     "HttpParam", "HTTP request body/params"),
    (r'\bgetParam\s*\(|\bgetParameter\s*\(|\binput\s*\.\s*get\s*\(',
     "HttpParam", "HTTP parameter read"),
    (r'\$_(?:GET|POST|REQUEST|COOKIE|SERVER)\b',
     "HttpParam", "PHP superglobal"),
    (r'@PathVariable|@RequestParam|@RequestBody',
     "HttpParam", "Spring MVC annotation"),

    # Environment
    (r'os\s*\.\s*environ\b|getenv\s*\(|environ\s*\[\s*["\']',
     "EnvRead", "environment variable"),
    (r'\bENV\s*\[|\$ENV\{|\bSystem\.getenv\s*\(',
     "EnvRead", "environment variable"),

    # Command line
    (r'\bargv\s*\[|\bargs\s*\[|\bsys\.argv\b',
     "CmdArg", "command-line argument"),
    (r'parser\.(?:parse_args|add_argument)\b|\bclick\.option\b',
     "CmdArg", "CLI argument"),

    # File / network I/O
    (r'open\s*\([^)]*["\']r["\']|\bfread\s*\(|\bfgets\s*\(|\bgets\s*\(',
     "FileRead", "file read"),
    (r'readline\s*\(\s*\)|\bstdin\s*\.\s*read|\bsys\.stdin\b',
     "StreamRead", "stdin read"),
    (r'\brecv\s*\(|\brecvfrom\s*\(|\bsocket\s*\.\s*recv',
     "NetworkRead", "socket receive"),

    # User input primitives
    (r'\binput\s*\(|\bprompt\s*\(|\bread_line\s*\(',
     "UserInput", "direct user input"),

    # Database results flowing back as new input
    (r'\.fetchone\s*\(\s*\)\[|\brow\s*\[\s*["\'].*?["\']',
     "DbResult", "database result used as input"),

    # Deserialization inputs
    (r'json\s*\.\s*loads\s*\(|yaml\s*\.\s*(?:safe_)?load\s*\(',
     "Deserialized", "deserialized external data"),

    # Function parameters (heuristic — any function that looks route-facing)
    (r'@app\s*\.\s*route|@router\s*\.\s*(?:get|post|put|delete|patch)',
     "RouteHandler", "route handler (all params untrusted)"),
]

_COMPILED_SOURCES = [
    (re.compile(p, re.IGNORECASE), kind, label)
    for p, kind, label in _SOURCE_PATTERNS
]


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL SINK DETECTION  (Axiom 3)
# ══════════════════════════════════════════════════════════════════════════════
#
# Semantic categories, not API names.

_SINK_PATTERNS: list[tuple[str, str, str, float]] = [
    # (pattern, sink_kind, label, base_risk)

    # SQL / Query execution
    (r'\.execute\s*\(|\.query\s*\(|\.raw\s*\(|\.search\s*\(',
     "QueryExec", "query execution", 0.9),
    (r'executeQuery\s*\(|executeUpdate\s*\(|prepareStatement\s*\(',
     "QueryExec", "JDBC query", 0.9),
    (r'\bSELECT\b.*\bFROM\b|\bINSERT\b.*\bINTO\b|\bDELETE\b.*\bFROM\b',
     "QueryExec", "inline SQL", 0.85),

    # Command / process execution
    (r'subprocess\s*\.\s*(?:run|Popen|call|check_output)',
     "CommandExec", "subprocess execution", 0.95),
    (r'\bexec\s*\(|\beval\s*\(|\bsystem\s*\(|\bpopen\s*\(',
     "CommandExec", "exec/eval/system call", 0.95),
    (r'Runtime\s*\.\s*exec\s*\(|ProcessBuilder\s*\(',
     "CommandExec", "Java process execution", 0.95),
    (r'\bos\s*\.\s*system\s*\(|\bspawn\w*\s*\(',
     "CommandExec", "OS command spawn", 0.92),

    # Template / render
    (r'Template\s*\(.*?\)\s*\.\s*render|render_template_string\s*\(',
     "RenderInline", "dynamic template render", 0.88),
    (r'\.innerHTML\s*=|\bdocument\.write\s*\(',
     "RenderInline", "DOM injection", 0.88),

    # Network outbound
    (r'requests\s*\.\s*(?:get|post|put|patch|delete)\s*\(',
     "OutboundRequest", "HTTP outbound request", 0.80),
    (r'fetch\s*\(|axios\s*\.\s*(?:get|post)\s*\(',
     "OutboundRequest", "JS fetch/axios", 0.80),
    (r'urllib\s*\.\s*request|\bhttpclient\b|\bcurl_exec\b',
     "OutboundRequest", "HTTP client call", 0.80),

    # File write / path ops
    (r'open\s*\([^)]*["\'][wa]["\']|\.write\s*\(|\bfwrite\s*\(',
     "FileWrite", "file write operation", 0.78),
    (r'os\s*\.\s*rename\s*\(|shutil\s*\.\s*(?:copy|move)',
     "FileWrite", "filesystem move/rename", 0.75),

    # Deserialization sinks
    (r'pickle\s*\.\s*loads?\s*\(|yaml\s*\.\s*load\s*\(',
     "UnknownEffect", "unsafe deserialization", 0.92),
    (r'shelve\s*\.\s*open\s*\(|Marshal\s*\.\s*load\s*\(',
     "UnknownEffect", "pickle-backed store", 0.88),
    (r'ObjectInputStream\s*\(|\.readObject\s*\(',
     "UnknownEffect", "Java object deserialization", 0.92),

    # Memory operations (unsafe)
    (r'unsafe\s*\{[^}]*\*\s*\w+|\*\s*ptr\.offset\s*\(',
     "MemorySafety", "unsafe dereference", 0.90),
    (r'malloc\s*\(|calloc\s*\(|realloc\s*\(',
     "MemoryAlloc", "heap allocation", 0.60),

    # Redirect
    (r'redirect\s*\(|Response\s*\.\s*redirect\s*\(',
     "Redirect", "HTTP redirect", 0.75),

    # Auth / session state mutation
    (r'setattr\s*\(|session\s*\[',
     "AuthStateMutation", "state mutation", 0.82),

    # LDAP / directory
    (r'\.search\s*\(\s*["\'][^"\']+["\']|ldap.*filter',
     "LDAPQuery", "LDAP search/filter", 0.85),

    # XML / XPath
    (r'\.xpath\s*\(|XPathFactory\s*\.',
     "XPathExec", "XPath expression evaluation", 0.85),
    (r'XMLParser\s*\(.*resolve_entities\s*=\s*True',
     "UnknownEffect", "XXE-enabled XML parser", 0.90),

    # Dynamic dispatch
    (r'\bgetattr\s*\(\s*\w+\s*,\s*\w+\s*\)',
     "DynamicDispatch", "dynamic attribute lookup", 0.80),
    (r'Class\s*\.\s*forName\s*\(',
     "ReflectionExec", "reflective class instantiation", 0.92),
]

_COMPILED_SINKS = [
    (re.compile(p, re.IGNORECASE | re.DOTALL), kind, label, risk)
    for p, kind, label, risk in _SINK_PATTERNS
]


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL TRANSFORM DETECTION  (Axiom 2)
# ══════════════════════════════════════════════════════════════════════════════

_TRANSFORM_PATTERNS = [
    (r'f["\'][^"\']*\{[^}]+\}[^"\']*["\']',              "StringInterpolation",  "f-string/template interpolation"),
    (r'"[^"]*"\s*%\s*\w|"[^"]*"\s*\+\s*\w',              "StringConcat",         "string concatenation"),
    (r'format\s*\(|\.format\s*\(',                         "StringFormat",         "string format call"),
    (r'sprintf\s*\(|string\.format\s*\(',                  "StringFormat",         "sprintf/format"),
    (r'\+\s*\w+\s*\+|\|\|\s*\w+\s*\|\||\.\s*concat\s*\(', "StringConcat",         "string concat operator"),
    (r'base64\s*\.\s*(?:b64)?decode|atob\s*\(',            "Decode",               "base64 decode"),
    (r'(?:url|html|xml)_?decode|urllib\s*\.\s*parse\s*\.\s*unquote', "Decode",  "URL/HTML decode"),
]

_COMPILED_TRANSFORMS = [
    (re.compile(p, re.IGNORECASE | re.DOTALL), kind, label)
    for p, kind, label in _TRANSFORM_PATTERNS
]


# ══════════════════════════════════════════════════════════════════════════════
# TRUST EARNED SIGNALS  (Axiom 4)
# ══════════════════════════════════════════════════════════════════════════════

_TRUST_EARNED_PATTERNS = [
    (r'hmac\s*\.\s*compare_digest\s*\(',         "hmac_compare_digest"),
    (r'secrets\s*\.\s*compare_digest\s*\(',       "secrets_compare_digest"),
    (r'os\s*\.\s*path\s*\.\s*realpath\s*\(',      "path_realpath"),
    (r'\.startswith\s*\(\s*(?:BASE|base|ROOT)',    "path_prefix_check"),
    (r'in\s+(?:ALLOWED|ALLOWLIST|WHITELIST|VALID)',  "allowlist_membership"),
    (r'if\s+\w+\s+not\s+in\s+\(',                "not_in_allowlist"),
    (r'(?:urlparse|parse_url)\s*\([^)]+\)\s*\.\s*hostname', "url_hostname_parsed"),
    (r'abort\s*\(\s*403\s*\)|raise\s+(?:Forbidden|PermissionDenied)', "access_denied_raised"),
    (r'parameterize\s*\(|placeholder\s*=|%s|:\w+\b.*?bind', "parameterized_query"),
    (r'prepared\s+statement|PreparedStatement\s*\(', "prepared_statement"),
    (r'verify\s*=\s*True|verify_ssl\s*=\s*True',  "tls_verified"),
]

_COMPILED_TRUST_EARNED = [
    (re.compile(p, re.IGNORECASE), name)
    for p, name in _TRUST_EARNED_PATTERNS
]


# ══════════════════════════════════════════════════════════════════════════════
# TRUST CLAIMED SIGNALS  (Axiom 5)
# ══════════════════════════════════════════════════════════════════════════════

_TRUST_CLAIM_RE = re.compile(
    r'\b(?:safe|clean|validated|sanitized|escaped|trusted|filtered|purified)'
    r'[\s_]?\w*\s*='
    r'|\w+[\s_]?(?:safe|clean|validated|sanitized|escaped|trusted)\s*=',
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════════════════════════
# STRUCTURAL OBLIGATION DETECTION  (Axiom 7)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ObligationSpec:
    kind: str
    description: str
    trigger: re.Pattern
    discharge: re.Pattern


_OBLIGATION_SPECS = [
    ObligationSpec(
        "VALIDATE_BEFORE_USE",
        "external input must be validated before reaching a dangerous sink",
        re.compile(
            r'request\s*\.\s*(?:args|form|json|body)|os\s*\.\s*environ'
            r'|\$_(?:GET|POST|REQUEST)',
            re.IGNORECASE,
        ),
        re.compile(
            r'hmac\.compare_digest|in\s+ALLOWED|\.hostname\s+(?:not\s+)?in'
            r'|abort\s*\(\s*403|raise.*Forbidden|parameterized|%s\b',
            re.IGNORECASE,
        ),
    ),
    ObligationSpec(
        "CONSTANT_TIME_COMPARE",
        "secret values must be compared using constant-time comparison",
        re.compile(
            r'(?:hashlib|hmac)\.\w+.*hexdigest\s*\(\s*\)|check_password\b'
            r'|verify_token\b|compare_hash\b',
            re.IGNORECASE,
        ),
        re.compile(r'compare_digest\s*\(', re.IGNORECASE),
    ),
    ObligationSpec(
        "COMMIT_AFTER_WRITE",
        "database writes must be followed by commit or managed transaction",
        re.compile(r'db\s*\.\s*(?:add|save|create|insert|update)\b', re.IGNORECASE),
        re.compile(r'\.commit\s*\(\s*\)|transaction\s*\(|with\s+db\b', re.IGNORECASE),
    ),
    ObligationSpec(
        "SESSION_BEFORE_REDIRECT",
        "auth session must be established before redirect",
        re.compile(r'\blogin\b.*?return\s+redirect|def\s+login\b', re.IGNORECASE | re.DOTALL),
        re.compile(r'session\s*\[|login_user\s*\(|set_cookie\s*\(', re.IGNORECASE),
    ),
    ObligationSpec(
        "TOKEN_REVOKE_BEFORE_ROTATE",
        "old token must be revoked before issuing new one",
        re.compile(
            # Only trigger in explicit refresh/rotation contexts,
            # not simple token generation functions
            r'create_refresh_token|rotate.*token|new.*refresh_token\b'
            r'|token.*rotation|reissue.*token',
            re.IGNORECASE,
        ),
        re.compile(
            r'revoke\s*\(|blacklist\s*\(|delete.*token|token.*delete'
            r'|invalidate\s*\(',
            re.IGNORECASE,
        ),
    ),
    ObligationSpec(
        "GOROUTINE_CANCELLATION",
        "goroutines must have a cancellation/exit path",
        re.compile(r'\bgo\s+func\s*\(', re.DOTALL),
        re.compile(
            r'context\.Context|ctx\.Done\s*\(\s*\)|select\s*\{[^}]*case\s*<-',
            re.DOTALL,
        ),
    ),
    ObligationSpec(
        "NO_REUSE_AFTER_FREE",
        "memory must not be accessed after deallocation",
        re.compile(r'\bdrop\s*\(\s*\w+\s*\)', re.DOTALL),
        re.compile(r'let\s+\w+\s*=\s*\w+\.clone\(\)|Arc::|Rc::', re.DOTALL),
    ),
    ObligationSpec(
        "SAFE_MEMORY_ARITHMETIC",
        "pointer arithmetic or allocation size must be bounds-checked",
        re.compile(
            r'(?:int|size_t)\s+\w+\s*=\s*\w+\s*\*\s*\w+.*?malloc\s*\(',
            re.DOTALL,
        ),
        re.compile(
            r'__builtin_(?:u?mul|add|sub)_overflow|SIZE_MAX\s*/|'
            r'checked_(?:mul|add)|> (?:UINT|INT)_MAX',
        ),
    ),
    ObligationSpec(
        "PROTOTYPE_GUARD",
        "object merge must guard against prototype pollution",
        re.compile(
            r'for\s*\([^)]*of\s+Object\.keys[^)]*\)\s*\{[^}]*\w+\[key\]\s*=',
            re.DOTALL,
        ),
        re.compile(
            r'hasOwnProperty\s*\(\s*key\s*\)'
            r'|key\s*===\s*["\'](?:__proto__|constructor)["\']',
        ),
    ),
    ObligationSpec(
        "CSPRNG_FOR_SECRETS",
        "security tokens must use a CSPRNG",
        re.compile(
            # Only trigger when weak RNG (random, rand, Math.random) is used
            r'\brandom\.(?:random|randint|choice|randrange|uniform)\s*\('
            r'|\bMath\.random\s*\(|\brand(?:n|om)?\s*\((?!.*crypto)',
            re.IGNORECASE,
        ),
        re.compile(
            r'secrets\.\w+\s*\(|os\.urandom\s*\('
            r'|crypto\.randomBytes\s*\(|SecureRandom\s*\(',
            re.IGNORECASE,
        ),
    ),
    ObligationSpec(
        "CSRF_TOKEN_IN_CALLBACK",
        "OAuth callbacks must validate state/CSRF token",
        re.compile(r'oauth_callback\b|callback.*code\s*=\s*request', re.IGNORECASE),
        re.compile(r'state\s*=\s*request|csrf_token|verify_state\s*\(', re.IGNORECASE),
    ),
    ObligationSpec(
        "TOKEN_EXPIRY_AFTER_RESET",
        "password reset tokens must be consumed/expired after use",
        re.compile(r'reset_password\b|set_password\s*\(', re.IGNORECASE),
        re.compile(
            r'token\.delete\s*\(\s*\)|mark_used\s*\(|expire\s*\('
            r'|timedelta.*token|token.*expir',
            re.IGNORECASE,
        ),
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL LOWERING PASS
# ══════════════════════════════════════════════════════════════════════════════

def lower_universal(code: str, artifact_id: str = "") -> UniversalIR:
    """
    Lower any text artifact to UniversalIR using structural heuristics.
    Confidence reflects how much of the structure was recoverable.
    """
    lang, lang_conf = detect_language(code)
    ir = UniversalIR(
        language_guess=lang,
        parse_confidence=lang_conf,
    )

    lines = code.splitlines()
    _ctr = [0]

    def nid(kind: str, line: int) -> str:
        _ctr[0] += 1
        return f"U-{kind[:3].upper()}-{line}-{_ctr[0]:04d}"

    # ── Sources ──────────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        for pattern, kind, label in _COMPILED_SOURCES:
            if pattern.search(line):
                n = UNode(nid("SRC", lineno), "SOURCE", label, lineno,
                          line.strip()[:80], lang_conf)
                ir.sources.append(n)

                # Taint map: extract variable receiving the source
                _extract_assignment_taint(ir, line, n, lineno)
                break  # one source per line

    # ── Sinks ────────────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        for pattern, kind, label, _ in _COMPILED_SINKS:
            if pattern.search(line):
                n = UNode(nid("SNK", lineno), "SINK", f"{kind}: {label}",
                          lineno, line.strip()[:80], lang_conf)
                n.kind = kind  # store actual sink kind
                ir.sinks.append(n)
                break

    # ── Transforms ───────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        for pattern, kind, label in _COMPILED_TRANSFORMS:
            if pattern.search(line):
                n = UNode(nid("XFM", lineno), "TRANSFORM", label, lineno,
                          line.strip()[:60], lang_conf)
                ir.transforms.append(n)
                break

    # ── Trust earned ─────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        for pattern, name in _COMPILED_TRUST_EARNED:
            if pattern.search(line):
                n = UNode(nid("VAL", lineno), "VALIDATION", name, lineno,
                          line.strip()[:60], lang_conf)
                ir.validations.append(n)
                break

    # ── Trust claims ─────────────────────────────────────────────────────────
    for lineno, line in enumerate(lines, 1):
        if _TRUST_CLAIM_RE.search(line):
            n = UNode(nid("CLM", lineno), "CLAIM",
                      "naming-convention safety claim", lineno,
                      line.strip()[:60], lang_conf)
            ir.claims.append(n)

    # ── Obligation accounting ─────────────────────────────────────────────────
    for spec in _OBLIGATION_SPECS:
        triggered = spec.trigger.search(code)
        if not triggered:
            continue
        discharged = bool(spec.discharge.search(code))
        # Find trigger line
        trigger_line = 0
        for lineno, line in enumerate(lines, 1):
            if spec.trigger.search(line):
                trigger_line = lineno
                break
        ir.obligations.append(UObligation(
            obligation_id=f"OBL-{spec.kind}",
            kind=spec.kind,
            description=spec.description,
            acquisition_line=trigger_line,
            fulfillment_found=discharged,
            confidence=lang_conf,
        ))

    return ir


def _extract_assignment_taint(ir: UniversalIR, line: str, source_node: UNode,
                               lineno: int) -> None:
    """Extract lhs = source_call() assignments for taint map building."""
    # Python/JS: var = source_call(...)
    m = re.match(r'\s*(\w+)\s*=\s*', line)
    if m:
        var = m.group(1)
        ir.assignment_map.setdefault(var, []).append(source_node.label)
        ir.raw_symbols[var] = f"tainted_from:{source_node.label}"


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL PATH WALKER
# ══════════════════════════════════════════════════════════════════════════════

def walk_universal(ir: UniversalIR, code: str) -> list[UTaintFlow]:
    """
    Identify taint flows from sources to sinks.
    For each source→sink pair in the same code scope:
      - check if transforms connect them
      - check if validations are present
      - determine trust gap
    """
    flows: list[UTaintFlow] = []
    flow_ctr = [0]

    if not ir.sources and not ir.obligations:
        return flows

    # Collect trust earned and claimed at module level
    earned = [v.label for v in ir.validations]
    claimed = [c.text for c in ir.claims]

    # Build tainted symbol set from assignment map
    tainted_symbols = set(ir.assignment_map.keys())
    # Also consider source node text snippets as taint markers
    source_texts = {s.text[:20] for s in ir.sources}

    for sink in ir.sinks:
        # Check if sink line references any tainted symbol or source text
        sink_line_text = sink.text

        reaches_tainted = (
            any(sym in sink_line_text for sym in tainted_symbols)
            or any(st[:10] in sink_line_text for st in source_texts if len(st) > 3)
        )

        # Also: if sink is after source in code and transforms exist between them
        # → conservative: assume tainted path is reachable
        source_before_sink = any(s.line < sink.line for s in ir.sources)
        transforms_present = bool(ir.transforms)

        if not (reaches_tainted or (source_before_sink and transforms_present)):
            # Still emit for obligation violations even without direct taint
            if not ir.obligations:
                continue

        flow_ctr[0] += 1
        # Most relevant source (closest before sink)
        relevant_sources = sorted(
            [s for s in ir.sources if s.line <= sink.line],
            key=lambda s: sink.line - s.line,
        )
        nearest_source = relevant_sources[0] if relevant_sources else (
            ir.sources[0] if ir.sources else None
        )
        if nearest_source is None:
            continue

        # Transforms between source and sink
        between_transforms = [
            t for t in ir.transforms
            if (nearest_source.line <= t.line <= sink.line)
        ]

        trust_gap = len(earned) == 0

        flow = UTaintFlow(
            flow_id=f"F-{flow_ctr[0]:04d}",
            source_node=nearest_source,
            sink_node=sink,
            transforms=between_transforms,
            validations=ir.validations,
            claims=claimed,
            earned_trust=earned,
            trust_gap=trust_gap,
            confidence=ir.parse_confidence,
        )
        flows.append(flow)

    return flows


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL BLOB EMITTER
# ══════════════════════════════════════════════════════════════════════════════

def emit_universal_blobs(
    ir: UniversalIR,
    flows: list[UTaintFlow],
    artifact_id: str = "",
) -> list[dict]:
    """
    Emit blobs from:
      1. Taint flows (source → sink with trust gap)
      2. Unfulfilled obligations (structural invariant violations)
    """
    blobs: list[dict] = []
    ctr = [0]

    # ── Taint flow blobs ─────────────────────────────────────────────────────
    for flow in flows:
        sink_kind = getattr(flow.sink_node, 'kind', 'UnknownEffect')

        # Base risk by sink kind
        sink_risks = {
            "QueryExec": 0.90, "CommandExec": 0.95, "ReflectionExec": 0.92,
            "RenderInline": 0.88, "OutboundRequest": 0.78, "Redirect": 0.72,
            "UnknownEffect": 0.82, "DynamicDispatch": 0.80, "LDAPQuery": 0.85,
            "XPathExec": 0.85, "FileWrite": 0.75, "AuthStateMutation": 0.82,
            "MemorySafety": 0.92, "MemoryAlloc": 0.60,
        }
        base_risk = sink_risks.get(sink_kind, 0.70)

        # Reduce if earned trust present
        if flow.earned_trust:
            base_risk *= 0.20
        # Reduce if transforms are validation-named
        if any("escape" in t.label or "sanitize" in t.label or "encode" in t.label
               for t in flow.transforms):
            base_risk *= 0.35

        # Deception: claims without earned trust
        deception = 0.70 if (flow.claims and not flow.earned_trust) else 0.0
        legitimacy = min(1.0, len(flow.earned_trust) * 0.35)

        # Confidence degrades with uncertainty
        conf_map = {
            "parsed": "high-confidence inferred",
            "inferred": "high-confidence inferred",
            "plausible": "plausible",
            "indeterminate": "indeterminate",
        }
        confidence = conf_map.get(flow.confidence, "plausible")

        # Verdict
        if flow.trust_gap and not flow.earned_trust:
            if "SQL" in sink_kind or sink_kind == "QueryExec":
                verdict = f"[{ir.language_guess.upper()}] TAINTED INPUT REACHES SQL SINK — injection path confirmed"
            elif sink_kind == "CommandExec":
                verdict = f"[{ir.language_guess.upper()}] TAINTED INPUT REACHES COMMAND SINK — command injection"
            elif sink_kind == "OutboundRequest":
                verdict = f"[{ir.language_guess.upper()}] TAINTED INPUT REACHES NETWORK SINK — SSRF risk"
            elif sink_kind == "ReflectionExec":
                verdict = f"[{ir.language_guess.upper()}] TAINTED INPUT REACHES REFLECTION SINK"
            else:
                verdict = (f"[{ir.language_guess.upper()}] TAINTED INPUT REACHES {sink_kind} "
                          f"WITHOUT VALIDATED TRUST")
        elif flow.claims and not flow.earned_trust:
            verdict = (f"[{ir.language_guess.upper()}] WRAPPER THEATER — safety claimed "
                      f"by naming but not earned by {sink_kind}")
        else:
            verdict = (f"[{ir.language_guess.upper()}] Path reaches {sink_kind} — "
                      f"earned trust: {flow.earned_trust[:2]}")

        ctr[0] += 1
        blobs.append({
            "blob_id": f"U-{ctr[0]:04d}",
            "path_id": flow.flow_id,
            "checkpoint_kind": "sink_boundary",
            "callable_id": f"universal:{ir.language_guess}",
            "module_id": artifact_id,
            "entry_sources": [{"source": flow.source_node.label,
                               "var": flow.source_node.text[:40],
                               "line": flow.source_node.line,
                               "trust": "untrusted", "confidence": flow.confidence}],
            "transform_chain": [f"{t.label}@L{t.line}" for t in flow.transforms[:4]],
            "effects": [sink_kind],
            "sinks": [{"sink_kind": sink_kind, "var": flow.sink_node.text[:40],
                       "line": flow.sink_node.line, "tainted": flow.trust_gap}],
            "trust_claims": flow.claims[:3],
            "trust_earned": flow.earned_trust[:3],
            "trust_state": "untrusted" if flow.trust_gap else "narrowed",
            "wrapper_theater": bool(flow.claims and not flow.earned_trust),
            "risk_score": round(min(1.0, base_risk), 3),
            "deception_score": round(deception, 3),
            "legitimacy_score": round(legitimacy, 3),
            "ambiguity_score": 0.1 if flow.confidence in ("plausible", "indeterminate") else 0.0,
            "suspicious_clean_score": 0.0,
            "confidence_class": confidence,
            "verdict": verdict,
            "notes": [
                f"Language: {ir.language_guess} (confidence: {ir.parse_confidence})",
                f"Obligation status: {len([o for o in ir.obligations if not o.fulfillment_found])}"
                f"/{len(ir.obligations)} unfulfilled",
            ],
        })

    # ── Obligation violation blobs ────────────────────────────────────────────
    # Emit a blob for each unfulfilled structural obligation
    # (even if no direct taint flow was found)
    for obl in ir.obligations:
        if obl.fulfillment_found:
            continue
        if any(b["notes"] and obl.kind in str(b["notes"]) for b in blobs):
            continue  # already covered by a taint flow blob

        # Suppress VALIDATE_BEFORE_USE and CONSTANT_TIME_COMPARE obligation blobs
        # when no sink is detected — prevents FPs on code that delegates validation
        # to an opaque call (e.g., user.check_password() handles timing internally)
        if obl.kind in ("VALIDATE_BEFORE_USE", "CONSTANT_TIME_COMPARE") and not ir.sinks:
            continue

        # Suppress SESSION_BEFORE_REDIRECT when no redirect sink is detected
        if obl.kind == "SESSION_BEFORE_REDIRECT" and not any(
            "Redirect" in getattr(s, "kind", "") for s in ir.sinks
        ):
            continue

        ctr[0] += 1
        # Map obligation kind to sink_kind and risk
        obl_map = {
            "VALIDATE_BEFORE_USE":     ("QueryExec",        0.85),
            "CONSTANT_TIME_COMPARE":   ("TimingOracle",     0.82),
            "COMMIT_AFTER_WRITE":      ("QueryExec",        0.75),
            "SESSION_BEFORE_REDIRECT": ("AuthStateMutation",0.80),
            "TOKEN_REVOKE_BEFORE_ROTATE": ("TokenIssue",    0.78),
            "GOROUTINE_CANCELLATION":  ("GoroutineLeak",    0.80),
            "NO_REUSE_AFTER_FREE":     ("MemorySafety",     0.92),
            "SAFE_MEMORY_ARITHMETIC":  ("IntegerOverflow",  0.85),
            "PROTOTYPE_GUARD":         ("PrototypePollution",0.88),
            "CSPRNG_FOR_SECRETS":      ("WeakRandomness",   0.88),
            "CSRF_TOKEN_IN_CALLBACK":  ("AuthStateMutation",0.82),
            "TOKEN_EXPIRY_AFTER_RESET":("TokenIssue",       0.78),
        }
        sink_kind, risk = obl_map.get(obl.kind, ("UnknownEffect", 0.75))

        blobs.append({
            "blob_id": f"U-{ctr[0]:04d}",
            "path_id": f"P-obl-{obl.obligation_id}",
            "checkpoint_kind": "obligation_violation",
            "callable_id": f"universal:{ir.language_guess}",
            "module_id": artifact_id,
            "entry_sources": [],
            "transform_chain": [],
            "effects": [sink_kind],
            "sinks": [{"sink_kind": sink_kind, "var": "structural",
                       "line": obl.acquisition_line, "tainted": True}],
            "trust_claims": [],
            "trust_earned": [],
            "trust_state": "untrusted",
            "wrapper_theater": False,
            "risk_score": round(risk, 3),
            "deception_score": 0.0,
            "legitimacy_score": 0.0,
            "ambiguity_score": 0.1 if obl.confidence in ("plausible", "indeterminate") else 0.0,
            "suspicious_clean_score": 0.0,
            "confidence_class": "high-confidence inferred"
                if obl.confidence == "inferred" else "plausible",
            "verdict": (
                f"[{ir.language_guess.upper()}] STRUCTURAL OBLIGATION VIOLATED — "
                f"{obl.description}"
            ),
            "notes": [
                f"Obligation: {obl.kind}",
                f"Triggered at line {obl.acquisition_line}",
                f"Discharge pattern not found in artifact",
                f"Language confidence: {ir.parse_confidence}",
            ],
        })

    return blobs


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def analyze_universal(code: str, artifact_id: str = "") -> list[dict]:
    """
    Complete universal analysis round-trip:
    text → UniversalIR → taint flows + obligations → blobs

    Works on any language, any syntax, any structure.
    Confidence degrades gracefully for alien artifacts.
    """
    ir = lower_universal(code, artifact_id)
    flows = walk_universal(ir, code)
    return emit_universal_blobs(ir, flows, artifact_id)
