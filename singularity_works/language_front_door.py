from __future__ import annotations
# complexity_justified: polyglot front door — language detection + IR normalization
# Every artifact enters as a UniversalSemanticIR regardless of source language.
# "unknown" is NOT a valid language — the forge always makes a determination.
# Python is the primary substrate and the fallback for ambiguous content.
# Isomorphism: the desugar + normalize pass in a compiler front-end, except
# the target representation is semantic intent, not IR bytecode.

import ast
import re
from .semantic_ir import (
    UniversalSemanticIR,
    TrustBoundary,
    ResourceViolation,
    StateMachine,
    StateNode,
    StateTransition,
    TemporalGap,
    SemanticNode,
)


# ---------------------------------------------------------------------------
# Language identification
# Architecture: decision tree, not threshold voting.
# Tier 1: unambiguous single-token confirms (never wrong).
# Tier 2: weighted scoring — highest scorer wins.
# Tier 3: Python is the fallback (the forge's primary substrate).
# "unknown" is never emitted.
# ---------------------------------------------------------------------------

# Single tokens that unambiguously identify a language.
# A match here overrides any scoring result.
_TIER1_CONFIRMS: list[tuple[str, str]] = [
    # Rust — syntax not shared with any other language
    ("fn main(", "rust"),
    ("pub fn ", "rust"),
    ("let mut ", "rust"),
    ("use std::", "rust"),
    ("impl ", "rust"),
    ("unsafe {", "rust"),
    ("Option<", "rust"),
    ("Result<", "rust"),
    ("&[u8]", "rust"),
    ("as_ptr()", "rust"),
    ("copy_nonoverlapping", "rust"),
    ("mem::transmute", "rust"),
    # Rust signals that appear in real Rust code without std — e.g. sqlx, actix.
    # "format!(" is a Rust macro invocation — unique syntax, no false positives
    # in any other supported language.  "fn " covers function defs in non-main
    # crates (safe here because Python is confirmed by ast.parse step 0).
    ("format!(", "rust"),
    ("fn ", "rust"),
    ("::<", "rust"),     # turbofish — e.g. Vec::<u8>::new()
    ("use crate::", "rust"),
    ("use sqlx::", "rust"),
    ("use actix", "rust"),
    ("use tokio::", "rust"),
    ("-> String", "rust"),
    ("-> Vec<", "rust"),
    # Go
    ("package main", "go"),
    ("package ", "go"),
    ("func main(", "go"),
    (":= ", "go"),
    ("float64", "go"),
    ("goroutine", "go"),
    ("chan ", "go"),
    # Java
    ("public class ", "java"),
    ("public static void main", "java"),
    ("System.out.print", "java"),
    ("new Random(", "java"),
    ("SecureRandom", "java"),
    ("@Override", "java"),
    ("import java.", "java"),
    ("extends ", "java"),
    # C / C++
    ("#include <", "c"),
    ("strncpy(", "c"),
    ("malloc(", "c"),
    ("sizeof(", "c"),
    ("NULL;", "c"),
    ("printf(\"", "c"),
    ("std::vector", "cpp"),
    ("std::string", "cpp"),
    ("cout <<", "cpp"),
    ("nullptr", "cpp"),
    ("template<", "cpp"),
    # JavaScript / TypeScript
    ("const ", "javascript"),
    ("let ", "javascript"),
    ("require(", "javascript"),
    ("module.exports", "javascript"),
    ("console.log(", "javascript"),
    ("=> {", "javascript"),
    ("async function", "javascript"),
    ("await ", "javascript"),
    ("__proto__", "javascript"),
    ("prototype.", "javascript"),
    # TypeScript — more specific signals over JS
    (": string", "typescript"),
    (": number", "typescript"),
    (": boolean", "typescript"),
    ("Promise<", "typescript"),
    ("interface ", "typescript"),
    # Python — specific markers not shared with others
    ("def ", "python"),
    ("import ", "python"),
    ("from ", "python"),
    ("    return", "python"),
    ("self.", "python"),
    ("__init__", "python"),
    ("elif ", "python"),
    ("print(", "python"),
]

# For tier-1: when multiple matches fire for different languages, pick by
# specificity (more specific token wins). If same language, confirmed.
_LANG_SPECIFICITY: dict[str, int] = {
    "rust": 10, "java": 9, "go": 9, "cpp": 8,
    "c": 7, "typescript": 8, "javascript": 6, "python": 5,
}


def detect_language(content: str) -> str:
    """
    Determine source language from content.
    Returns a language string — never returns 'unknown'.
    Decision tree:
      0. Python structural pre-check: if ast.parse() succeeds it IS Python.
         No other supported language produces valid Python AST. This closes
         the self-referential FP where detection literal strings embedded in
         Python source (e.g. _HEURISTIC_PATTERNS) vote the file as the
         language they are written to detect.
      1. Tier-1 unambiguous confirms (single token, no false positives)
      2. If tie or no match, fall back to Python (the forge's substrate)
    """
    # Step 0 — Python structural proof (zero false positives).
    # ast.parse() raises SyntaxError immediately on the first non-Python token
    # so the cost for Rust/Go/Java/C/JS is one failed parse attempt, not a
    # full walk.  For Python the cost is already paid again in _build_python_ir.
    try:
        ast.parse(content)
        return "python"
    except SyntaxError:
        pass
    # Step 1 — Non-Python: token voting over tier-1 confirms.
    votes: dict[str, int] = {}
    for token, lang in _TIER1_CONFIRMS:
        if token in content:
            votes[lang] = votes.get(lang, 0) + _LANG_SPECIFICITY.get(lang, 1)
    if not votes:
        return "python"  # Structural nativity: default to primary substrate
    return max(votes, key=lambda k: votes[k])


# ---------------------------------------------------------------------------
# Python path — full AST analysis
# ---------------------------------------------------------------------------

def _build_python_ir(artifact_id: str, content: str) -> UniversalSemanticIR:
    ir = UniversalSemanticIR(
        artifact_id=artifact_id,
        language="python",
        content=content,
        confidence="high",
    )
    try:
        tree = ast.parse(content)
    except SyntaxError:
        ir.confidence = "low"
        return ir

    class _Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.opened: dict[str, int] = {}
            self.closed: set[str] = set()
            self.with_managed: set[str] = set()
            self.closed_lines: dict[str, int] = {}
            self.nodes: list[SemanticNode] = []
            self._nc = 0
            self.pickle_loads_found = False
            self.re_compile_found = False
            self.hmac_compare_found = False

        def _nid(self) -> str:
            self._nc += 1
            return f"n{self._nc}"

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            ir.has_async = True
            ir.function_names.append(node.name)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            ir.function_names.append(node.name)
            # Mutable default detection
            for default in node.args.defaults + node.args.kw_defaults:
                if default is not None and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    ir.has_mutable_defaults = True
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                ir.import_names.append(alias.name)
                ir.semantic_tokens.add(alias.name.split(".")[0])
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.module:
                ir.import_names.append(node.module)
                ir.semantic_tokens.add(node.module.split(".")[0])
            self.generic_visit(node)

        def visit_With(self, node: ast.With) -> None:
            for item in node.items:
                ctx = item.context_expr
                if _is_open_call(ctx) and isinstance(item.optional_vars, ast.Name):
                    self.with_managed.add(item.optional_vars.id)
                    ir.has_file_io = True
            self.generic_visit(node)

        def _is_request_input_expr(self, node: ast.AST) -> bool:
            if not isinstance(node, ast.Call):
                return False
            func = node.func
            if not isinstance(func, ast.Attribute):
                return False
            val = func.value
            if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Name):
                return val.value.id in ("request", "req")
            if isinstance(val, ast.Name):
                return val.id in ("request", "req")
            return False

        def _expr_has_request_input(self, node: ast.AST) -> bool:
            return any(self._is_request_input_expr(child) for child in ast.walk(node))

        def _expr_has_request_taint(self, node: ast.AST) -> bool:
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and f"REQUEST_INPUT:{child.id}" in ir.semantic_tokens:
                    return True
            return False

        def visit_Assign(self, node: ast.Assign) -> None:
            val = node.value
            if isinstance(val, ast.Call) and _is_open_call(val):
                ir.has_file_io = True
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.opened[target.id] = node.lineno
            if isinstance(val, ast.JoinedStr) or _is_string_build(val):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        ir.semantic_tokens.add(f"TAINTED_STRING:{target.id}")
            if self._expr_has_request_input(val) or self._expr_has_request_taint(val):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        ir.semantic_tokens.add(f"REQUEST_INPUT:{target.id}")
                        if isinstance(val, ast.JoinedStr) or _is_string_build(val):
                            ir.semantic_tokens.add(f"TAINTED_STRING:{target.id}")
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            # complexity_justified: isinstance dispatch across heterogeneous AST
            # node types — each branch is a distinct security detection target.
            func = node.func

            # close() calls
            if isinstance(func, ast.Attribute) and func.attr == "close":
                if isinstance(func.value, ast.Name):
                    self.closed.add(func.value.id)
                    self.closed_lines[func.value.id] = node.lineno

            # eval / exec
            if isinstance(func, ast.Name) and func.id in ("eval", "exec"):
                ir.has_dynamic_exec = True
                ir.dangerous_calls.append(func.id)
                ir.trust_boundaries.append(TrustBoundary(
                    boundary_type="EVAL_EXEC", sink_name=func.id,
                    sink_line=node.lineno, confidence="high",
                ))

            # pickle.loads
            if (isinstance(func, ast.Attribute) and func.attr == "loads"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "pickle"):
                ir.dangerous_calls.append("pickle.loads")
                ir.trust_boundaries.append(TrustBoundary(
                    boundary_type="DESERIALIZATION", sink_name="pickle.loads",
                    sink_line=node.lineno, confidence="high",
                ))
                ir.semantic_tokens.add("deserialization:pickle_loads")

            # hashlib.md5 / hashlib.sha1 in security context
            if isinstance(func, ast.Attribute) and func.attr in ("md5", "sha1"):
                if isinstance(func.value, ast.Name) and func.value.id == "hashlib":
                    ir.semantic_tokens.add(f"weak_hash:{func.attr}")
                    ir.trust_boundaries.append(TrustBoundary(
                        boundary_type="WEAK_HASH", sink_name=f"hashlib.{func.attr}",
                        sink_line=node.lineno, confidence="high",
                    ))

            # subprocess shell=True
            if isinstance(func, ast.Attribute) and func.attr in (
                "run", "Popen", "call", "check_call", "check_output"
            ):
                if isinstance(func.value, ast.Name) and func.value.id == "subprocess":
                    shell_true = any(
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                        for kw in node.keywords
                    )
                    if shell_true:
                        ir.has_shell_calls = True
                        ir.dangerous_calls.append(f"subprocess.{func.attr}(shell=True)")
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="SHELL", sink_name=f"subprocess.{func.attr}",
                            sink_line=node.lineno, confidence="high",
                        ))

            # os.system / os.popen
            if isinstance(func, ast.Attribute) and func.attr in ("system", "popen"):
                if isinstance(func.value, ast.Name) and func.value.id == "os":
                    ir.has_shell_calls = True
                    ir.dangerous_calls.append(f"os.{func.attr}")
                    ir.trust_boundaries.append(TrustBoundary(
                        boundary_type="SHELL", sink_name=f"os.{func.attr}",
                        sink_line=node.lineno, confidence="high",
                    ))

            # verify=False (TLS)
            for kw in node.keywords:
                if (kw.arg == "verify"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is False):
                    ir.has_tls_calls = True
                    ir.dangerous_calls.append("verify=False")
                    ir.trust_boundaries.append(TrustBoundary(
                        boundary_type="TLS", sink_name="request",
                        sink_line=node.lineno,
                        tainted_input="verify=False", confidence="high",
                    ))

            # SQL sinks
            if isinstance(func, ast.Attribute) and func.attr in (
                "execute", "executemany", "executescript", "raw", "query"
            ):
                ir.has_db_calls = True
                ir.semantic_tokens.add("DB_SINK")
                if node.args:
                    arg = node.args[0]
                    has_params = (
                        len(node.args) >= 2
                        or any(kw.arg in ("parameters", "params") for kw in node.keywords)
                    )
                    tainted = _is_string_build(arg) or (
                        isinstance(arg, ast.Name)
                        and f"TAINTED_STRING:{arg.id}" in ir.semantic_tokens
                    )
                    if tainted and not has_params:
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="DB_QUERY",
                            sink_name=f"{func.attr}",
                            sink_line=node.lineno,
                            tainted_input="string_built_query",
                            confidence="high",
                        ))

            # requests / httpx (network)
            if isinstance(func, ast.Attribute) and func.attr in (
                "get", "post", "put", "delete"
            ):
                if isinstance(func.value, ast.Name) and func.value.id in (
                    "requests", "httpx"
                ):
                    ir.has_network_calls = True

            # SSRF: request.args/body or tainted URL → requests/httpx network sink
            if isinstance(func, ast.Attribute) and func.attr in (
                "get", "post", "put", "delete", "request"
            ) and isinstance(func.value, ast.Name) and func.value.id in (
                "requests", "httpx", "session", "urllib"
            ):
                url_arg = node.args[0] if node.args else None
                if url_arg is None:
                    for kw in node.keywords:
                        if kw.arg in ("url",):
                            url_arg = kw.value
                            break
                if url_arg is not None:
                    tainted_name = None
                    if isinstance(url_arg, ast.Name) and f"REQUEST_INPUT:{url_arg.id}" in ir.semantic_tokens:
                        tainted_name = url_arg.id
                    if tainted_name or self._is_request_input_expr(url_arg) or self._expr_has_request_taint(url_arg):
                        ir.semantic_tokens.add("ssrf:user_url_to_network")
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="NETWORK", sink_name=f"{func.value.id}.{func.attr}",
                            sink_line=node.lineno,
                            tainted_input=tainted_name or "user_supplied_url", confidence="high",
                        ))

            # Track request.args.get / request.json.get → tainted variable / direct input presence
            if self._is_request_input_expr(node):
                ir.semantic_tokens.add("HAS_REQUEST_INPUT")

            self.generic_visit(node)

        def report_resource_violations(self) -> None:
            for var, acquire_line in self.opened.items():
                if var not in self.closed and var not in self.with_managed:
                    ir.resource_violations.append(ResourceViolation(
                        resource=var, violation="LEAKED",
                        acquire_line=acquire_line,
                        violation_line=acquire_line,
                    ))
                elif var in self.closed_lines:
                    close_line = self.closed_lines[var]
                    ir.state_machines.append(_make_resource_machine(
                        var, acquire_line, close_line,
                    ))

    v = _Visitor()
    v.visit(tree)
    v.report_resource_violations()
    ir.nodes = v.nodes

    # ── Cross-function return-taint propagation ─────────────────────────────
    # Detects patterns like:
    #   def get_url(): return request.args.get('url')
    #   def fetch(): url = get_url(); requests.get(url)   ← SSRF
    #
    # Algorithm: two-pass over the AST.
    # Pass 1: collect functions whose return value is tainted by request input.
    # Pass 2: for each assignment from a taint-returning call, propagate taint.
    #         Re-run network/DB sink detection with updated taint tokens.
    _propagate_cross_function_taint(tree, ir)

    # Async atomicity detection
    if ir.has_async and ir.has_db_calls:
        _detect_async_atomicity_gaps(content, ir)

    return ir


# ---------------------------------------------------------------------------
# Heuristic path — multi-language structural extraction
# ---------------------------------------------------------------------------

_HEURISTIC_PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {
    "eval_exec": [
        ("eval",     re.compile(r'\beval\s*\(')),
        ("exec",     re.compile(r'\bexec\s*\(')),
        ("Function", re.compile(r'new\s+Function\s*\(')),
    ],
    "shell_injection": [
        ("shell_true",    re.compile(r'shell\s*=\s*[Tt]rue')),
        ("system",        re.compile(r'\bsystem\s*\(')),
        ("popen",         re.compile(r'\bpopen\s*\(')),
        ("Command_new",   re.compile(r'Command::new\s*\(')),
        ("ProcessBuilder",re.compile(r'ProcessBuilder')),
    ],
    "tls_disabled": [
        ("verify_false",          re.compile(r'verify\s*=\s*[Ff]alse')),
        ("rejectUnauthorized",    re.compile(r'rejectUnauthorized\s*:\s*false')),
        ("InsecureSkipVerify",    re.compile(r'InsecureSkipVerify\s*:\s*true')),
    ],
    "sql_injection": [
        ("fstring_execute",  re.compile(r'execute\s*\(\s*f[\'"]')),
        ("format_execute",   re.compile(r'execute\s*\([^)]*\.format\s*\(')),
        ("concat_execute",   re.compile(r'execute\s*\([^)]*\+\s*\w+')),
        ("template_literal", re.compile(r'execute\s*\(`[^`]*\$\{')),
        # Rust: format!("SELECT ... {}", var) — query string built before call
        ("rust_format_sql",  re.compile(
            r'format!\s*\(\s*["\'](?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\b',
            re.IGNORECASE,
        )),
    ],
    "db_calls": [
        ("execute", re.compile(r'\.(execute|query|executeQuery|executemany)\s*\(')),
    ],
    "file_io": [
        ("open",        re.compile(r'\bopen\s*\(')),
        ("fopen",       re.compile(r'\bfopen\s*\(')),
        ("File_open",   re.compile(r'File::open')),
        ("readFile",    re.compile(r'readFile\s*\(')),
    ],
    "network": [
        ("fetch",    re.compile(r'\bfetch\s*\(')),
        ("requests", re.compile(r'\brequests\.(get|post)\s*\(')),
        ("axios",    re.compile(r'\baxios\.(get|post)\s*\(')),
    ],
    "async_patterns": [
        ("async_def", re.compile(r'\basync\s+(def|fn|function)\b')),
        ("await",     re.compile(r'\bawait\b')),
    ],
    "unsafe": [
        ("unsafe_block", re.compile(r'\bunsafe\s*\{')),
        ("raw_pointer",  re.compile(r'\*const\s+|\*mut\s+')),
        ("ptr_offset",   re.compile(r'ptr::offset|as_ptr\(\)')),
    ],
    "prototype_pollution": [
        ("proto_write", re.compile(r'\.__proto__\s*=')),
        ("proto_key",   re.compile(r'["\']__proto__["\']')),
        ("constructor_pollution", re.compile(r'\.constructor\.prototype')),
    ],
    "toctou": [
        ("access_then_open", re.compile(r'access\s*\(.*W_OK')),
        ("stat_then_open",   re.compile(r'\bstat\s*\(')),
    ],
    "ssrf": [
        ("user_url_fetch",  re.compile(r'req\.body\.url|req\.query\.url|userUrl|webhookUrl')),
        ("user_url_get",    re.compile(r'req\.body\.[\'"]?url[\'"]?')),
    ],
    "weak_rng": [
        ("new_random_time", re.compile(r'new\s+Random\s*\(')),
        ("srand_time",      re.compile(r'srand\s*\(')),
        ("math_random",     re.compile(r'Math\.random\s*\(\s*\)')),
    ],
    "float_finance": [
        ("float64_finance", re.compile(r'float64')),
        ("double_finance",  re.compile(r'\bdouble\s+\w*(?:balance|amount|rate|price)')),
        ("float_calc",      re.compile(r'(?:balance|amount|rate|price)\s*\*.*\d+\.\d+')),
    ],
    "unsafe_cast": [
        ("raw_ptr_cast",  re.compile(r'as_ptr\(\)')),
        ("copy_nono",     re.compile(r'copy_nonoverlapping')),
        ("mem_transmute", re.compile(r'mem::transmute')),
        ("strncpy",       re.compile(r'\bstrncpy\s*\(')),
    ],
    "deserialization": [
        ("pickle_loads",   re.compile(r'pickle\.loads\s*\(')),
        ("yaml_load_bare", re.compile(r'yaml\.load\s*\([^)]*\)')),
        ("unserialize",    re.compile(r'\bunserialize\s*\(')),
        ("ObjectInputStream", re.compile(r'ObjectInputStream')),
    ],
    "resource_leak": [
        ("stream_no_destroy", re.compile(r'createReadStream')),
        ("open_no_with",      re.compile(r'\bopen\s*\([^)]+\)')),
    ],
    "weak_hash": [
        ("md5",  re.compile(r'\bmd5\s*\(|\bMD5\s*\(')),
        ("sha1", re.compile(r'\bsha1\s*\(|\bSHA1\s*\(')),
    ],
    "path_traversal": [
        ("dotdot_check", re.compile(r'\.\.\s*in\s+\w+|path.*traversal|sanitize.*path')),
        ("join_userpath", re.compile(r'os\.path\.join.*request|path\.join.*req\.')),
    ],
}


def _build_heuristic_ir(
    artifact_id: str, content: str, language: str
) -> UniversalSemanticIR:
    conf = "medium"
    ir = UniversalSemanticIR(
        artifact_id=artifact_id,
        language=language,
        content=content,
        confidence=conf,
    )
    lines = content.splitlines()
    for category, patterns in _HEURISTIC_PATTERNS.items():
        for name, rx in patterns:
            for i, line in enumerate(lines, 1):
                if rx.search(line):
                    ir.semantic_tokens.add(f"{category}:{name}")
                    if category == "eval_exec":
                        ir.has_dynamic_exec = True
                        ir.dangerous_calls.append(name)
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="EVAL_EXEC", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "shell_injection":
                        ir.has_shell_calls = True
                        ir.dangerous_calls.append(name)
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="SHELL", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "tls_disabled":
                        ir.has_tls_calls = True
                        ir.dangerous_calls.append(name)
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="TLS", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "sql_injection":
                        ir.has_db_calls = True
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="DB_QUERY", sink_name=name,
                            sink_line=i, tainted_input="string_construction",
                            confidence=conf,
                        ))
                    elif category == "db_calls":
                        ir.has_db_calls = True
                    elif category == "file_io":
                        ir.has_file_io = True
                    elif category == "network":
                        ir.has_network_calls = True
                    elif category == "async_patterns":
                        ir.has_async = True
                    elif category == "unsafe":
                        ir.has_unsafe_blocks = True
                    elif category == "prototype_pollution":
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="PROTOTYPE_POLLUTION", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "toctou":
                        ir.temporal_gaps.append(TemporalGap(
                            gap_type="TOCTOU", check_line=i, act_line=i+1,
                            description=f"TOCTOU: {name} at line {i}",
                        ))
                        ir.semantic_tokens.add("toctou:detected")
                    elif category == "ssrf":
                        ir.has_network_calls = True
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="NETWORK", sink_name=name,
                            sink_line=i, tainted_input="user_supplied_url",
                            confidence=conf,
                        ))
                        ir.semantic_tokens.add("ssrf:user_url_to_network")
                    elif category == "weak_rng":
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="WEAK_RNG", sink_name=name,
                            sink_line=i, tainted_input="predictable_seed",
                            confidence=conf,
                        ))
                        ir.semantic_tokens.add("weak_rng:non_csprng")
                    elif category == "float_finance":
                        ir.semantic_tokens.add("float_finance:precision_risk")
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="NUMERIC_PRECISION", sink_name=name,
                            sink_line=i, tainted_input="float_in_financial_context",
                            confidence=conf,
                        ))
                    elif category == "unsafe_cast":
                        ir.has_unsafe_blocks = True
                        ir.dangerous_calls.append(name)
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="UNSAFE_MEMORY", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "deserialization":
                        ir.dangerous_calls.append(name)
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="DESERIALIZATION", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                        ir.semantic_tokens.add("deserialization:unsafe_deserialize")
                    elif category == "resource_leak":
                        ir.has_file_io = True
                        ir.semantic_tokens.add(f"resource_leak:{name}")
                    elif category == "weak_hash":
                        ir.semantic_tokens.add(f"weak_hash:{name}")
                        ir.trust_boundaries.append(TrustBoundary(
                            boundary_type="WEAK_HASH", sink_name=name,
                            sink_line=i, confidence=conf,
                        ))
                    elif category == "path_traversal":
                        ir.semantic_tokens.add("path_traversal:detected")
    return ir


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_open_call(node: object) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        (isinstance(func, ast.Name) and func.id == "open")
        or (isinstance(func, ast.Attribute) and func.attr == "open")
    )


def _is_string_build(node: object) -> bool:
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return True
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "format":
            return True
    return False


def _make_resource_machine(
    var: str, acquire_line: int, close_line: int
) -> StateMachine:
    m = StateMachine(tracked=var)
    m.states = [
        StateNode("UNACQUIRED"),
        StateNode("OPEN"),
        StateNode("CLOSED", is_terminal=True),
    ]
    m.transitions = [
        StateTransition("UNACQUIRED", "OPEN", f"open() at line {acquire_line}"),
        StateTransition("OPEN", "CLOSED", f"close() at line {close_line}"),
    ]
    return m


def _detect_async_atomicity_gaps(content: str, ir: UniversalSemanticIR) -> None:
    # Detect check-then-act across two await boundaries
    check_act = re.compile(
        r'await\s+\w+.*(?:balance|get|fetch|read)',
        re.IGNORECASE
    )
    act_pattern = re.compile(
        r'await\s+\w+.*(?:update|set|deduct|withdraw|write|decrement)',
        re.IGNORECASE
    )
    lines = content.splitlines()
    check_lines = [i+1 for i, l in enumerate(lines) if check_act.search(l)]
    act_lines   = [i+1 for i, l in enumerate(lines) if act_pattern.search(l)]
    if check_lines and act_lines:
        has_lock = any(
            kw in content.lower()
            for kw in ('transaction', 'mutex', 'lock', 'atomic', 'for update', 'compare_and_swap')
        )
        if not has_lock:
            ir.temporal_gaps.append(TemporalGap(
                gap_type="ASYNC_ATOMICITY",
                check_line=check_lines[0],
                act_line=act_lines[0],
                description="async check-then-act without atomic transaction",
            ))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Substrate-Sovereign resource limits for the IR builder.
# Same threat model as _parse(): content is inert data but adversarial
# sizing can cause memory pressure or regex DoS in heuristic extraction.
_IR_MAX_CONTENT_BYTES = 2 * 1024 * 1024   # 2 MB
_IR_MAX_CONTENT_LINES = 50_000


def _propagate_cross_function_taint(tree: ast.AST, ir: "UniversalSemanticIR") -> None:
    """
    Fixed-point cross-function return-taint propagation.

    Covers patterns:
      1. Single-hop getter: get_url() returns request.args.get('url')
      2. Multi-hop chain:   build_url() calls get_raw() and returns result
      3. urllib.request.urlopen / httpx client patterns
      4. Does NOT generate FPs when the sink is guarded by allowlist + urlparse check
    """
    _REQUEST_ATTRS = frozenset({
        "args", "form", "cookies", "headers", "json",
        "data", "values", "files", "params", "query_params",
    })
    _NETWORK_ATTRS = frozenset({
        "get", "post", "put", "delete", "patch", "request", "urlopen", "open",
    })
    _NETWORK_MODS = frozenset({
        "requests", "httpx", "urllib", "aiohttp", "session", "client",
    })
    # httpx/requests client class constructors — instances inherit network-client status
    _CLIENT_CONSTRUCTORS = frozenset({
        "AsyncClient", "Client", "Session",
    })
    # Allowlist / validation patterns that sanitise the URL
    _ALLOWLIST_INDICATORS = frozenset({
        "ALLOWED", "ALLOWLIST", "WHITELIST", "VALID_HOSTS", "PERMITTED",
    })

    def _is_direct_request_call(node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if not isinstance(func, ast.Attribute):
            return False
        val = func.value
        if isinstance(val, ast.Attribute) and isinstance(val.value, ast.Name):
            return val.value.id in ("request", "req") and val.attr in _REQUEST_ATTRS
        if isinstance(val, ast.Name):
            return val.id in ("request", "req")
        return False

    def _contains_taint_returning_call(node: ast.AST, taint_fns: set) -> bool:
        """True if node is a call to a taint-returning fn, or contains one in args."""
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            callee = (func.id if isinstance(func, ast.Name)
                      else func.attr if isinstance(func, ast.Attribute)
                      else None)
            if callee and callee in taint_fns:
                return True
        return False

    def _is_validated(func_node: ast.AST) -> bool:
        """True if the function contains an allowlist / urlparse hostname check."""
        text = set()
        for child in ast.walk(func_node):
            if isinstance(child, ast.Name):
                text.add(child.id.upper())
            elif isinstance(child, ast.Attribute):
                text.add(child.attr.upper())
            elif isinstance(child, ast.Constant) and isinstance(child.value, str):
                text.add(child.value.upper())
        # Allowlist membership check
        if text & _ALLOWLIST_INDICATORS:
            return True
        # urlparse(...).hostname
        if "URLPARSE" in text and "HOSTNAME" in text:
            return True
        return False

    # ── Pass 1: discover taint-returning functions (fixed-point) ──────────
    taint_fns: set[str] = set()
    current_tokens: set[str] = set(ir.semantic_tokens)

    for _iter in range(6):  # max 6 hops — covers all real code
        prev_size = len(taint_fns)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name in taint_fns:
                continue
            for child in ast.walk(node):
                if not isinstance(child, ast.Return) or child.value is None:
                    continue
                val = child.value
                # (a) direct request call
                if any(_is_direct_request_call(c) for c in ast.walk(val)):
                    taint_fns.add(node.name)
                    break
                # (b) return a known-tainted name
                if isinstance(val, ast.Name) and f"REQUEST_INPUT:{val.id}" in current_tokens:
                    taint_fns.add(node.name)
                    break
                # (c) return a call that contains a taint-returning function
                if _contains_taint_returning_call(val, taint_fns):
                    taint_fns.add(node.name)
                    break
        if len(taint_fns) == prev_size:
            break  # converged

    if not taint_fns:
        return

    # ── Pass 2: find network sinks reached by newly tainted names ──────────
    # Track client instances: c = httpx.AsyncClient() AND async with httpx.AsyncClient() as c:
    network_clients: set[str] = set()
    for node in ast.walk(tree):
        # Assignment form: c = httpx.AsyncClient()
        if isinstance(node, ast.Assign):
            val = node.value
            if isinstance(val, ast.Call):
                func = val.func
                if isinstance(func, ast.Attribute) and func.attr in _CLIENT_CONSTRUCTORS:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            network_clients.add(target.id)
                elif isinstance(func, ast.Name) and func.id in _CLIENT_CONSTRUCTORS:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            network_clients.add(target.id)
        # With statement form: async with httpx.AsyncClient() as c:
        elif isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
            for item in node.items:
                ctx = item.context_expr
                var = item.optional_vars
                if not isinstance(var, ast.Name):
                    continue
                if isinstance(ctx, ast.Call):
                    func = ctx.func
                    if isinstance(func, ast.Attribute) and func.attr in _CLIENT_CONSTRUCTORS:
                        network_clients.add(var.id)
                    elif isinstance(func, ast.Name) and func.id in _CLIENT_CONSTRUCTORS:
                        network_clients.add(var.id)

    # Find functions that: (a) assign from taint-returning fn, (b) call network sink
    from .semantic_ir import TrustBoundary
    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Skip if this function itself validates URLs
        if _is_validated(func_node):
            continue

        local_taint: set[str] = set()

        # Find assignments from taint-returning calls
        for child in ast.walk(func_node):
            if not isinstance(child, ast.Assign):
                continue
            val = child.value
            if not isinstance(val, ast.Call):
                continue
            callee_name = (val.func.id if isinstance(val.func, ast.Name)
                           else val.func.attr if isinstance(val.func, ast.Attribute)
                           else None)
            if callee_name and callee_name in taint_fns:
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        local_taint.add(target.id)
                        ir.semantic_tokens.add(f"REQUEST_INPUT:{target.id}")
                        ir.semantic_tokens.add("HAS_REQUEST_INPUT")

        if not local_taint:
            continue

        # Check for network sinks consuming the newly tainted names
        for child in ast.walk(func_node):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in _NETWORK_ATTRS:
                continue

            # Determine if the caller is a network module or client instance
            caller = func.value
            caller_name = (caller.id if isinstance(caller, ast.Name)
                           else caller.attr if isinstance(caller, ast.Attribute)
                           else None)
            # Drill down one more level for urllib.request.urlopen
            if caller_name not in _NETWORK_MODS and caller_name not in network_clients:
                if isinstance(caller, ast.Attribute):
                    outer = caller.value
                    outer_name = (outer.id if isinstance(outer, ast.Name) else None)
                    if outer_name not in _NETWORK_MODS:
                        continue
                    caller_name = f"{outer_name}.{caller.attr}"
                else:
                    continue

            # Get the URL argument
            url_arg = child.args[0] if child.args else None
            if url_arg is None:
                for kw in child.keywords:
                    if kw.arg in ("url",):
                        url_arg = kw.value
                        break
            if url_arg is None:
                continue

            # Check if url arg is tainted (direct name or embedded in f-string/concat)
            tainted_name: str | None = None
            if isinstance(url_arg, ast.Name) and url_arg.id in local_taint:
                tainted_name = url_arg.id
            elif not isinstance(url_arg, ast.Name):
                for ch in ast.walk(url_arg):
                    if isinstance(ch, ast.Name) and ch.id in local_taint:
                        tainted_name = ch.id
                        break

            if tainted_name:
                line = getattr(child, "lineno", 0)
                ir.trust_boundaries.append(TrustBoundary(
                    boundary_type="NETWORK",
                    sink_name=f"{caller_name}.{func.attr}",
                    sink_line=line,
                    tainted_input=f"indirect_taint:{tainted_name}←{','.join(sorted(taint_fns))}",
                    validated=False,
                    confidence="medium",
                ))


def build_ir(
    content: str,
    artifact_id: str = "artifact",
    language_hint: str | None = None,
) -> UniversalSemanticIR:
    """
    Build a UniversalSemanticIR from content in any supported language.
    Language is always determined — "unknown" is never returned.
    Python gets full AST fidelity; other languages get structural heuristics
    with explicit confidence annotation.

    Resource bounds: inputs exceeding 2MB or 50K lines return a minimal IR
    with confidence="low" rather than raising or hanging. The forge reads
    content as inert data — no execution risk — but unbounded inputs can
    cause memory pressure or ReDoS in the heuristic extraction pass.
    """
    # Size gate — enforce before any processing
    content_bytes = len(content.encode("utf-8", errors="replace"))
    if content_bytes > _IR_MAX_CONTENT_BYTES:
        # Return a minimal stub IR with low confidence.
        # Gate strategies will still run via IR token checks but will find nothing
        # because we can't safely analyze oversized content.
        lang = language_hint or detect_language(content[:4096])  # sniff first 4KB only
        return UniversalSemanticIR(
            artifact_id=artifact_id,
            language=lang,
            content=content[:1024],   # store only a snippet for reference
            confidence="low",
        )
    # Line count guard — extremely deep nesting can overflow the recursive
    # Python IR builder's internal call stack
    line_count = content.count("\n")
    if line_count > _IR_MAX_CONTENT_LINES:
        # Truncate to first _IR_MAX_CONTENT_LINES lines and analyze that
        content = "\n".join(content.splitlines()[:_IR_MAX_CONTENT_LINES])

    language = language_hint or detect_language(content)
    if language == "python":
        return _build_python_ir(artifact_id, content)
    return _build_heuristic_ir(artifact_id, content, language)
