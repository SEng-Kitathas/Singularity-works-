from __future__ import annotations

import ast
from typing import Any


def _try_parse(content: str) -> ast.AST | None:
    try:
        return ast.parse(content)
    except SyntaxError:
        return None


# ---------------------------------------------------------------------------
# Standalone local analyzers (patterns requiring deeper semantic awareness)
# ---------------------------------------------------------------------------

def find_timing_attacks(content: str) -> list[dict[str, Any]]:
    """
    Detect non-constant-time string comparison in security-sensitive contexts.
    Isomorphism: a timing oracle is a side channel — the inequality branch
    leaks information about the secret through measured execution time.
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    _SECURITY_NAMES = frozenset({
        "token", "secret", "password", "auth", "key", "nonce",
        "verify", "check", "compare", "validate", "authenticate",
    })

    class _V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            fname = node.name.lower()
            is_security = any(s in fname for s in _SECURITY_NAMES)
            if not is_security:
                self.generic_visit(node)
                return
            # Look for == comparison involving parameters
            params = {a.arg for a in node.args.args}
            has_digest = False

            class _CompVisitor(ast.NodeVisitor):
                def visit_Call(self, n: ast.Call) -> None:
                    func = n.func
                    if isinstance(func, ast.Attribute) and func.attr in (
                        "compare_digest",
                    ):
                        nonlocal has_digest
                        has_digest = True
                    self.generic_visit(n)

                def visit_Compare(self, n: ast.Compare) -> None:
                    for op in n.ops:
                        if isinstance(op, ast.Eq):
                            # Left or right references a parameter
                            left_is_param = (
                                isinstance(n.left, ast.Name)
                                and n.left.id in params
                            )
                            right_is_param = any(
                                isinstance(c, ast.Name) and c.id in params
                                for c in n.comparators
                            )
                            if left_is_param or right_is_param:
                                findings.append({
                                    "lineno": n.lineno,
                                    "func": node.name,
                                    "message": (
                                        f"Non-constant-time comparison in security "
                                        f"function '{node.name}' at line {n.lineno} — "
                                        f"use hmac.compare_digest() to prevent timing oracle"
                                    ),
                                    "rewrite": (
                                        "import hmac\n"
                                        "return hmac.compare_digest(user_token, secret_token)"
                                    ),
                                })
                    self.generic_visit(n)

            cv = _CompVisitor()
            cv.visit(node)
            if has_digest:
                # Remove findings from this function if compare_digest is present
                findings[:] = [f for f in findings if f.get("func") != node.name]
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_incomplete_sanitization(content: str) -> list[dict[str, Any]]:
    """
    Detect path traversal checks that are incomplete:
    the function checks for '..' but does not normalize the path
    (URL-encoded traversal like %2e%2e%2f bypasses the check).
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    class _V(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            has_dotdot_check = False
            has_normalization = False
            has_path_join = False
            join_line = 0

            class _Inner(ast.NodeVisitor):
                def visit_Compare(self, n: ast.Compare) -> None:
                    nonlocal has_dotdot_check
                    for c in [n.left] + n.comparators:
                        if isinstance(c, ast.Constant) and ".." in str(c.value):
                            has_dotdot_check = True
                    self.generic_visit(n)

                def visit_Call(self, n: ast.Call) -> None:
                    nonlocal has_normalization, has_path_join, join_line
                    func = n.func
                    if isinstance(func, ast.Attribute):
                        if func.attr in ("abspath", "realpath", "resolve", "unquote",
                                         "unquote_plus"):
                            has_normalization = True
                        if func.attr == "join" and isinstance(func.value, ast.Attribute):
                            if func.value.attr == "path":
                                has_path_join = True
                                join_line = n.lineno
                    if isinstance(func, ast.Name) and func.id in (
                        "abspath", "realpath", "unquote"
                    ):
                        has_normalization = True
                    self.generic_visit(n)

            _Inner().visit(node)
            if has_dotdot_check and has_path_join and not has_normalization:
                findings.append({
                    "lineno": join_line,
                    "func": node.name,
                    "message": (
                        f"Incomplete path traversal check in '{node.name}': "
                        f"checks for '..' but does not decode URL encoding first — "
                        f"'%2e%2e%2f' bypasses the check; "
                        f"os.path.join at line {join_line} may traverse outside base"
                    ),
                    "rewrite": (
                        "from urllib.parse import unquote\n"
                        "path = unquote(path)\n"
                        "full = os.path.realpath(os.path.join(BASE_DIR, path))\n"
                        "if not full.startswith(os.path.realpath(BASE_DIR)):\n"
                        "    raise ValueError('Path traversal')"
                    ),
                })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_redos(content: str) -> list[dict[str, Any]]:
    """
    Detect ReDoS: regex patterns with nested quantifiers that cause
    catastrophic backtracking on adversarial input.
    Isomorphism: exponential branching factor in a nondeterministic finite
    automaton — the NFA backtracks through 2^n states for n-char input.
    """
    import re as _re
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    def _is_dangerous_regex(pattern: str) -> bool:
        """
        Detect catastrophic backtracking potential in a regex pattern.
        Key patterns:
          (X+)+ / (X+)* / ((X)+Y?)* — multiple quantified groups nested
          (a|b)+ — alternation under quantifier
        Strategy: count occurrences of )[+*?] — if two or more exist,
        nested quantification is present regardless of nesting depth.
        """
        # Find all "closing paren followed by quantifier" tokens
        # Note: use r'\)' NOT r'\\)' — we want the regex pattern
        # \) which matches a literal ) in the target string.
        close_quants = _re.findall(r'\)[+*?]', pattern)
        if len(close_quants) >= 2:
            return True
        # Alternation under quantifier: (a|b)+
        if _re.search(r'\([^()]*\|[^()]*\)[+*]', pattern):
            return True
        # Adjacent quantifiers (x++ possessive-like)
        if _re.search(r'[+*][+*]', pattern):
            return True
        return False

    # First pass: collect string variable assignments (pattern = r"...")
    _string_vars: dict[str, str] = {}

    class _CollectVars(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        _string_vars[t.id] = node.value.value
            self.generic_visit(node)

    _CollectVars().visit(tree)

    class _V(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            is_re_call = (
                isinstance(func, ast.Attribute)
                and func.attr in ("compile", "match", "search", "fullmatch", "findall")
                and isinstance(func.value, ast.Name)
                and func.value.id == "re"
            )
            if is_re_call and node.args:
                arg = node.args[0]
                pattern_str = None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    pattern_str = arg.value
                elif isinstance(arg, ast.Name) and arg.id in _string_vars:
                    # Resolve variable → string value from first-pass collection
                    pattern_str = _string_vars[arg.id]
                if pattern_str and _is_dangerous_regex(pattern_str):
                    findings.append({
                        "lineno": node.lineno,
                        "message": (
                            f"ReDoS: regex at line {node.lineno} contains nested "
                            f"quantifiers — adversarial input can cause exponential "
                            f"backtracking: {pattern_str[:60]!r}"
                        ),
                        "rewrite": (
                            "Use re2 (google-re2) which guarantees O(n) matching, "
                            "or rewrite pattern to eliminate nested quantifiers"
                        ),
                    })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


def find_weak_hash_usage(content: str) -> list[dict[str, Any]]:
    """
    Detect MD5/SHA1 used in security-sensitive contexts (passwords, tokens).
    Isomorphism: a cryptographic hash is a one-way function; MD5/SHA1 are
    no longer one-way for practical adversaries — collision and preimage
    attacks exist.
    """
    findings: list[dict[str, Any]] = []
    tree = _try_parse(content)
    if tree is None:
        return findings

    _SECURITY_CONTEXT = frozenset({
        "password", "passwd", "secret", "token", "auth", "credential",
        "hash", "store", "register", "secure",
    })
    _WEAK = frozenset({"md5", "sha1", "sha_1", "MD5", "SHA1"})

    class _V(ast.NodeVisitor):
        def __init__(self) -> None:
            self._func_name = ""

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._func_name = node.name.lower()
            self.generic_visit(node)
            self._func_name = ""

        def visit_Call(self, node: ast.Call) -> None:
            func = node.func
            alg = None
            if isinstance(func, ast.Attribute) and func.attr in _WEAK:
                if isinstance(func.value, ast.Name) and func.value.id == "hashlib":
                    alg = func.attr
            if alg and any(s in self._func_name for s in _SECURITY_CONTEXT):
                findings.append({
                    "lineno": node.lineno,
                    "alg": alg,
                    "message": (
                        f"Weak hash: hashlib.{alg} at line {node.lineno} in "
                        f"security context '{self._func_name}' — "
                        f"{alg.upper()} is broken for security use"
                    ),
                    "rewrite": (
                        "import bcrypt\n"
                        "hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())\n"
                        "# Or: passlib.hash.argon2.hash(password)"
                    ),
                })
            self.generic_visit(node)

    _V().visit(tree)
    return findings


