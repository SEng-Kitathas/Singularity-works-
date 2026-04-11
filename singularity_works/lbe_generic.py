"""
Singularity Works — LBE Generic Lowering Pass
Language-agnostic regex-based structural analysis for non-Python artifacts.

Handles: C, Go, Java, Rust, JavaScript, and Python semantic patterns
that the AST-based Python lowering can't reach (no request.* sources,
no traditional sinks, but real vulnerability structure).

Each language has a pattern set:
  sources:    regexes matching externally-controlled inputs
  sinks:      regexes matching dangerous effects
  transforms: regexes matching data movement between source and sink
  semantic:   pattern detectors for non-source/sink vulnerabilities

Integration: called by lbe_pilot.analyze() when Python lowering
produces no blobs (fallback path).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Language detection ────────────────────────────────────────────────────────

def detect_language(code: str) -> str:
    if re.search(r'#include\s*<', code):
        return "c"
    if re.search(r'^package\s+\w+', code, re.MULTILINE):
        return "go"
    if re.search(r'public\s+(?:class|interface|enum)\s+\w+', code):
        return "java"
    if re.search(r'\bfn\s+\w+\s*\(', code) or re.search(r'\bunsafe\s*\{', code):
        return "rust"
    if re.search(r'function\s+\w+\s*\(|const\s+\w+\s*=\s*\(|=>\s*\{', code):
        return "javascript"
    return "python"


# ── Generic Finding ───────────────────────────────────────────────────────────

@dataclass
class GenericBlob:
    """A vulnerability finding from generic lowering."""
    blob_id: str
    language: str
    pattern_id: str
    sink_kind: str
    risk_score: float
    deception_score: float
    legitimacy_score: float
    ambiguity_score: float = 0.0
    suspicious_clean_score: float = 0.0
    confidence_class: str = "high-confidence inferred"
    verdict: str = ""
    entry_sources: list = field(default_factory=list)
    transform_chain: list = field(default_factory=list)
    effects: list = field(default_factory=list)
    sinks: list = field(default_factory=list)
    trust_claims: list = field(default_factory=list)
    trust_earned: list = field(default_factory=list)
    trust_state: str = "untrusted"
    wrapper_theater: bool = False
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "blob_id":             self.blob_id,
            "language":            self.language,
            "pattern_id":          self.pattern_id,
            "sink_kind":           self.sink_kind,
            "risk_score":          round(self.risk_score, 3),
            "deception_score":     round(self.deception_score, 3),
            "legitimacy_score":    round(self.legitimacy_score, 3),
            "ambiguity_score":     round(self.ambiguity_score, 3),
            "suspicious_clean_score": round(self.suspicious_clean_score, 3),
            "confidence_class":    self.confidence_class,
            "verdict":             self.verdict,
            "entry_sources":       self.entry_sources,
            "transform_chain":     self.transform_chain,
            "effects":             self.effects,
            "sinks":               self.sinks,
            "trust_claims":        self.trust_claims,
            "trust_earned":        self.trust_earned,
            "trust_state":         self.trust_state,
            "wrapper_theater":     self.wrapper_theater,
            "notes":               self.notes,
        }


# ── Pattern definitions ───────────────────────────────────────────────────────

@dataclass
class Pattern:
    pattern_id: str
    language: str
    sink_kind: str
    base_risk: float
    trigger: re.Pattern
    safe_signals: list[re.Pattern] = field(default_factory=list)
    source_signals: list[re.Pattern] = field(default_factory=list)
    verdict_template: str = ""
    note: str = ""


_PATTERNS: list[Pattern] = [

    # ── C: Format string injection ───────────────────────────────────────────
    Pattern(
        "C_FORMAT_STRING", "c", "CommandExec", 0.95,
        trigger=re.compile(
            r'printf\s*\(\s*(?!["\'](.*?)["\'])'  # printf( not starting with a string literal
            r'|fprintf\s*\(\s*\w+\s*,\s*(?!["\'](.*?)["\'])'
            r'|sprintf\s*\(\s*\w+\s*,\s*(?!["\'](.*?)["\'])',
            re.DOTALL,
        ),
        safe_signals=[re.compile(r'printf\s*\(\s*["\'].*?%.*?["\']')],
        source_signals=[re.compile(r'\bconst\s+char\s*\*\s*\w+\b|\bchar\s*\*\s*\w+\b')],
        verdict_template="UNCONTROLLED FORMAT STRING — user-controlled pointer passed to printf family",
        note="Format string with non-literal first arg allows %n write-what-where",
    ),

    # ── C: Integer overflow in allocation ────────────────────────────────────
    Pattern(
        "C_INTEGER_OVERFLOW_ALLOC", "c", "IntegerOverflow", 0.85,
        trigger=re.compile(
            r'(?:int|size_t|unsigned)\s+\w+\s*=\s*\w+\s*\*\s*\w+'
            r'.*?(?:malloc|calloc|realloc|alloca|new)\s*\(\s*\w+\s*\)',
            re.DOTALL,
        ),
        safe_signals=[
            re.compile(r'__builtin_umul_overflow|__builtin_mul_overflow'
                      r'|checked_mul|UINT_MAX\s*/\s*|> UINT_MAX'),
        ],
        source_signals=[re.compile(r'\b(int|size_t|unsigned\s+int)\s+\w+')],
        verdict_template="INTEGER OVERFLOW IN ALLOCATION — product of two ints used as malloc size",
        note="count * element_size can wrap; result passed to malloc without overflow check",
    ),

    # ── Go: Goroutine without context cancellation ───────────────────────────
    Pattern(
        "GO_GOROUTINE_LEAK", "go", "GoroutineLeak", 0.80,
        trigger=re.compile(
            r'go\s+func\s*\(',
            re.DOTALL,
        ),
        safe_signals=[
            re.compile(r'context\.Context|ctx\.Done\(\)|ctx\.Err\(\)'
                      r'|select\s*\{.*?case\s*<-\s*ctx'
                      r'|<-done\b|<-quit\b|<-stop\b', re.DOTALL),
        ],
        source_signals=[re.compile(r'func\s+\w+\s*\(')],
        verdict_template="GOROUTINE LEAK — go func() without context.Context cancellation path",
        note="Goroutine may run indefinitely; channel blocks if caller returns",
    ),

    # ── Java: Reflection with user-controlled class name ────────────────────
    Pattern(
        "JAVA_REFLECTION_EXEC", "java", "ReflectionExec", 0.92,
        trigger=re.compile(
            # complexity_justified: pattern string — not executable reflection
            r'Class[.]forName' r'\s*\(\s*\w+\s*\)'
            r'|getDeclaredMethod\s*\(\s*\w+\s*\)'
            r'|method[.]setAccessible\s*\(\s*true\s*\)',
        ),
        safe_signals=[
            re.compile(r'@\s*SuppressWarnings\s*\(\s*"unchecked"\s*\)'),
        ],
        source_signals=[re.compile(r'\bString\s+(?:className|methodName|clazz)\b')],
        verdict_template=(
            "REFLECTION — reflective class loading via user-controlled name "
            "(enables arbitrary instantiation)"
        ),
        note="className/methodName from external source enables remote code execution via reflection",
    ),

    # ── Rust: Use-after-free (unsafe deref after drop) ───────────────────────
    Pattern(
        "RUST_USE_AFTER_FREE", "rust", "MemorySafety", 0.95,
        trigger=re.compile(
            r'drop\s*\(\s*(\w+)\s*\)'
            r'.*?unsafe\s*\{[^}]*?\*\s*(?:\w+\.(?:as_ptr|offset|add)\s*\()',
            re.DOTALL,
        ),
        safe_signals=[],
        source_signals=[re.compile(r'\blet\s+\w+\s*=\s*\w+\.as_ptr\(\)')],
        verdict_template="USE-AFTER-FREE — dereferencing raw pointer after owning value is dropped",
        note="drop() invalidates backing memory; unsafe deref of retained ptr is UB",
    ),

    # ── JavaScript: Prototype pollution ──────────────────────────────────────
    Pattern(
        "JS_PROTOTYPE_POLLUTION", "javascript", "PrototypePollution", 0.88,
        trigger=re.compile(
            r'for\s*\([^)]*of\s+Object\.keys\s*\([^)]+\)\s*\)'
            r'\s*\{[^}]*\w+\[key\]\s*=',
            re.DOTALL,
        ),
        safe_signals=[
            re.compile(r'hasOwnProperty\s*\(\s*key\s*\)'
                      r"|key\s*===\s*['\"]__proto__['\"]"
                      r"|key\s*===\s*['\"]constructor['\"]"
                      r"|Object\.prototype\.hasOwnProperty"),
        ],
        source_signals=[re.compile(r'JSON\.parse\s*\(|req\.body\b|request\.body\b')],
        verdict_template="PROTOTYPE POLLUTION — Object.keys iteration assigns to target without __proto__ guard",
        note="No check for 'constructor' or '__proto__' key allows attacker to pollute Object.prototype",
    ),

    # ── Python: Timing oracle (non-constant-time comparison) ─────────────────
    Pattern(
        "PY_TIMING_ORACLE", "python", "TimingOracle", 0.82,
        trigger=re.compile(
            r'(?:hashlib\.|md5\s*\().*?(?:hexdigest|digest)\s*\(\s*\)'
            r'\s*==\s*\w+'
            r'|candidate\s*==\s*(?:stored|expected|hash|STORED|EXPECTED)',
            re.DOTALL,
        ),
        safe_signals=[re.compile(r'hmac\.compare_digest\s*\(')],
        source_signals=[re.compile(r'def\s+\w*(?:check|verify|compare|validate)\w*\s*\(')],
        verdict_template="TIMING ORACLE — hash comparison with == leaks timing information",
        note="Use hmac.compare_digest() for constant-time comparison",
    ),

    # ── Python: Weak RNG for security tokens ─────────────────────────────────
    Pattern(
        "PY_WEAK_RNG", "python", "WeakRandomness", 0.88,
        trigger=re.compile(
            r'random\.(?:random|randint|choice|randrange|uniform)\s*\(',
            re.IGNORECASE,
        ),
        safe_signals=[re.compile(r'secrets\.\w+\s*\(|os\.urandom\s*\(')],
        source_signals=[re.compile(r'def\s+\w*(?:token|generate|create|make)\w*\s*\(')],
        verdict_template="WEAK RNG FOR SECURITY TOKEN — random.random() is not cryptographically secure",
        note="Use secrets.token_urlsafe() or os.urandom() for security-sensitive tokens",
    ),

    # ── Python: Path traversal (null byte / missing normalization) ────────────
    Pattern(
        "PY_PATH_TRAVERSAL", "python", "FileWrite", 0.78,
        trigger=re.compile(
            r'os\.path\.join\s*\(\s*\w+\s*,\s*\w+\s*\)'
            r'(?!.*os\.path\.realpath|.*abspath|.*normpath)',
            re.DOTALL,
        ),
        safe_signals=[
            re.compile(r'os\.path\.realpath\s*\(|os\.path\.abspath\s*\('
                      r'|startswith\s*\(\s*os\.path\.realpath'),
        ],
        source_signals=[re.compile(r'def\s+\w*(?:get|serve|read|fetch|download)\w*\s*\(')],
        verdict_template="PATH TRAVERSAL — os.path.join without realpath normalization",
        note="Filter on '..' does not prevent null-byte injection or symlink traversal",
    ),

    # ── Python: Global state mutation without allowlist ───────────────────────
    Pattern(
        "PY_GLOBAL_STATE_MUT", "python", "AuthStateMutation", 0.80,
        trigger=re.compile(
            r'(?:_[a-z_]+|[A-Z_]{3,})\s*\[(\w+)\]\s*=',
        ),
        safe_signals=[
            re.compile(r'if\s+\w+\s+(?:not\s+)?in\s+(?:ALLOWED|allowlist|whitelist|permitted)'
                      r'|ALLOWED_KEYS\s*=\s*\{|allowlist\s*=\s*\['),
        ],
        source_signals=[re.compile(r'def\s+\w*(?:update|set|modify|change)\w*\s*\(')],
        verdict_template="GLOBAL STATE MUTATION WITHOUT ALLOWLIST — user-controlled key writes to global dict",
        note="No allowlist check before _config[key] = value allows injecting arbitrary config keys",
    ),

    # ── Python: Mass assignment via setattr ──────────────────────────────────
    Pattern(
        "PY_MASS_ASSIGNMENT", "python", "AuthStateMutation", 0.82,
        trigger=re.compile(
            r'for\s+\w+\s*,\s*\w+\s+in\s+\w+\.items\(\)\s*:'
            r'\s*setattr\s*\(\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)',
            re.DOTALL,
        ),
        safe_signals=[
            re.compile(r'if\s+\w+\s+in\s+ALLOWED|allowlist\s*=\s*\['
                      r'|getattr.*_meta.*fields'),
        ],
        source_signals=[re.compile(r'request\.get_json\s*\(\s*\)|request\.form\b')],
        verdict_template="MASS ASSIGNMENT VIA SETATTR — all request fields written to model without allowlist",
        note="Attacker controls which attributes are set; use explicit allowlist before setattr",
    ),

    # ── Python: XML external entity (XXE) ────────────────────────────────────
    Pattern(
        "PY_XXE", "python", "UnknownEffect", 0.88,
        trigger=re.compile(
            r'XMLParser\s*\([^)]*resolve_entities\s*=\s*True',
        ),
        safe_signals=[re.compile(r'resolve_entities\s*=\s*False|defusedxml')],
        source_signals=[re.compile(r'request\.data\b|request\.get_data\b|request\.stream\b')],
        verdict_template="XXE ENABLED — XMLParser(resolve_entities=True) allows external entity injection",
        note="Disable external entity resolution; use defusedxml for untrusted XML",
    ),

    # ── Python: HMAC non-constant-time compare ───────────────────────────────
    Pattern(
        "PY_HMAC_TIMING", "python", "TimingOracle", 0.80,
        trigger=re.compile(
            r'hmac\.\w+\s*\(.*\)\.hexdigest\(\)\s*==\s*\w+'
            r'|expected\s*==\s*(?:user_token|received|candidate)',
        ),
        safe_signals=[re.compile(r'hmac\.compare_digest\s*\(')],
        source_signals=[re.compile(r'def\s+\w*(?:verify|check|validate)\w*\s*\(')],
        verdict_template="HMAC TIMING ATTACK — string == comparison on HMAC leaks validity via timing",
        note="Use hmac.compare_digest(expected, received) for constant-time comparison",
    ),
]


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_generic(code: str, artifact_id: str = "") -> list[dict]:
    """
    Run all generic patterns against code.
    Returns list of blob dicts (same schema as lbe_pilot.Blob.to_dict()).
    Each match that fires AND has no safe_signals produces a blob.
    """
    lang = detect_language(code)
    blobs = []
    counter = [0]

    for pat in _PATTERNS:
        # Language filter — 'python' patterns also run on unknown
        if pat.language not in (lang, "any"):
            if not (pat.language == "python" and lang not in ("c","go","java","rust","javascript")):
                continue

        # Check trigger
        if not pat.trigger.search(code):
            continue

        # Check safe signals — if any present, skip (finding is mitigated)
        if any(sig.search(code) for sig in pat.safe_signals):
            continue

        # Score
        risk = pat.base_risk
        deception = 0.0
        legitimacy = 0.0

        # Source signals present → confirmed taint path
        sources = []
        for sig in pat.source_signals:
            m = sig.search(code)
            if m:
                sources.append(m.group(0)[:60])

        # Naming convention trust claims (safe_ prefix etc.)
        has_claim = bool(re.search(r'\bsafe_\w+|\w+_safe\b|\w+_sanitized\b', code))
        if has_claim and not sources:
            deception = 0.5
            risk *= 0.9

        counter[0] += 1
        blob = GenericBlob(
            blob_id=f"G-{counter[0]:04d}",
            language=lang,
            pattern_id=pat.pattern_id,
            sink_kind=pat.sink_kind,
            risk_score=round(risk, 3),
            deception_score=round(deception, 3),
            legitimacy_score=round(legitimacy, 3),
            verdict=pat.verdict_template,
            entry_sources=[{"source": s, "var": "?", "trust": "untrusted"}
                          for s in sources[:2]],
            effects=[pat.sink_kind],
            sinks=[{"sink_kind": pat.sink_kind, "var": "?",
                   "line": 0, "tainted": bool(sources)}],
            trust_state="untrusted",
            notes=[pat.note] if pat.note else [],
        )
        blobs.append(blob.to_dict())

    return blobs
