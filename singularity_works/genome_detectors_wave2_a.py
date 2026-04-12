from __future__ import annotations

import ast
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

def _detect_getattr_injection(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    getattr(obj, user_input) is eval in disguise.
    Any attribute lookup driven by user data allows invoking arbitrary methods.
    Isomorphism: same sourceâ†’sink as eval/exec but through the attribute namespace.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        # Track variables sourced from request.* 
        tainted: set[str] = set()
        class _V(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if isinstance(node.value, ast.Call):
                    f = node.value.func
                    if (isinstance(f, ast.Attribute) and
                            isinstance(f.value, ast.Attribute) and
                            isinstance(f.value.value, ast.Name) and
                            f.value.value.id == "request"):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                    elif (isinstance(f, ast.Attribute) and
                            isinstance(f.value, ast.Name) and
                            f.value.id in ("request", "args", "form", "params")):
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                self.generic_visit(node)
            def visit_Call(self, node: ast.Call) -> None:
                if (isinstance(node.func, ast.Name) and node.func.id == "getattr"
                        and len(node.args) >= 2):
                    attr_arg = node.args[1]
                    if isinstance(attr_arg, ast.Name) and (
                            attr_arg.id in tainted or
                            # Heuristic: single-letter variable as attr name = suspicious
                            len(attr_arg.id) <= 3):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"getattr() with variable attribute '{attr_arg.id}' at line "
                                f"{node.lineno} â€” if user-controlled, any method on the target "
                                f"object can be invoked; equivalent to eval"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate attribute name against an explicit allowlist before "
                                "calling getattr(); e.g. ALLOWED = {'html', 'json', 'text'}; "
                                "getattr(module, fmt) if fmt in ALLOWED else abort(400)"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback: semantic_tokens populated by heuristic front door
    if not detections and semantic_ir is not None:
        for t in getattr(semantic_ir, "semantic_tokens", set()):
            if t.startswith("getattr_injection"):
                detections.append(_Detection(
                    lineno=1,
                    message="getattr() with user-controlled attribute name detected",
                    evidence={"rewrite_candidate": "Validate attribute name against allowlist"},
                ))
    return detections



def _detect_tls_default_arg(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    verify=False as a function default silently disables TLS for all callers.
    Worse than a single call-site because it's invisible to callers.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def _check_defaults(self, fn_node: ast.FunctionDef) -> None:
                args = fn_node.args
                n_args = len(args.args)
                n_def = len(args.defaults)
                for i, default in enumerate(args.defaults):
                    if isinstance(default, ast.Constant) and default.value is False:
                        arg_idx = n_args - n_def + i
                        if arg_idx < n_args:
                            arg_name = args.args[arg_idx].arg
                            if arg_name == "verify":
                                detections.append(_Detection(
                                    lineno=fn_node.lineno,
                                    message=(
                                        f"TLS insecure default: verify=False in function "
                                        f"'{fn_node.name}' signature at line {fn_node.lineno} â€” "
                                        f"all callers inherit disabled certificate validation"
                                    ),
                                    evidence={"rewrite_candidate":
                                        "Change default to verify=True; require callers to "
                                        "explicitly opt out if needed; add a comment explaining why"},
                                ))
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                self._check_defaults(node)
                self.generic_visit(node)
            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                self._check_defaults(node)
                self.generic_visit(node)
        _V().visit(tree)
    # IR fallback
    if not detections and semantic_ir is not None:
        for tb in getattr(semantic_ir, "trust_boundaries", []):
            if tb.boundary_type == "TLS_DISABLED" and "default" in tb.sink_name.lower():
                detections.append(_Detection(
                    lineno=tb.sink_line,
                    message=f"TLS disabled in default argument at line {tb.sink_line}",
                    evidence={"rewrite_candidate": "Change default to verify=True"},
                ))
    return detections



def _detect_template_injection(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Server-side template injection (SSTI): user input flows into a Jinja2 Template()
    constructor as an f-string or concatenation. Allows arbitrary expression evaluation
    including __import__('os').popen('id').read().
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_template_call = (
                    (isinstance(func, ast.Name) and func.id == "Template") or
                    (isinstance(func, ast.Attribute) and func.attr == "Template")
                )
                if is_template_call and node.args:
                    arg = node.args[0]
                    # f-string with interpolation = tainted template string
                    if isinstance(arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"SSTI: Template() at line {node.lineno} receives an f-string â€” "
                                f"user data embedded in the template allows expression evaluation; "
                                f"{{{{7*7}}}} â†’ 49; {{{{''.__class__.__mro__[1].__subclasses__()}}}} â†’ RCE"
                            ),
                            evidence={"rewrite_candidate":
                                "Use a static template string and pass user data as render context: "
                                "Template('Hello, {{ name }}!').render(name=user_input)"},
                        ))
                    # string concat with a Name (variable) is also suspicious
                    elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"SSTI: Template() at line {node.lineno} may receive "
                                f"user-controlled string via concatenation"
                            ),
                            evidence={"rewrite_candidate":
                                "Pass user data as render context variables, not as part of "
                                "the template string itself"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)

        # Pattern 2 (separate pass): only for TOP-LEVEL functions
        # writing to module-level names. Nested functions are excluded
        # because they commonly write to outer-scope algorithm dicts (e.g. color[node]).
        if isinstance(tree, ast.Module):
            # Collect module-level assigned names (not inside any function)
            module_level_names: set[str] = set()
            for stmt in tree.body:
                if isinstance(stmt, ast.Assign):
                    for tgt in stmt.targets:
                        if isinstance(tgt, ast.Name):
                            module_level_names.add(tgt.id)
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    module_level_names.add(stmt.target.id)
            # Only check top-level FunctionDef nodes
            for stmt in tree.body:
                if not isinstance(stmt, ast.FunctionDef):
                    continue
                param_names = {arg.arg for arg in stmt.args.args}
                for child in ast.walk(stmt):
                    if not isinstance(child, ast.Assign):
                        continue
                    for tgt in child.targets:
                        if (isinstance(tgt, ast.Subscript) and
                                isinstance(tgt.value, ast.Name) and
                                isinstance(tgt.slice, ast.Name) and
                                tgt.slice.id in param_names and
                                tgt.value.id in module_level_names):
                            detections.append(_Detection(
                                lineno=child.lineno,
                                message=(
                                    f"Unvalidated key mutation at line {child.lineno}: "
                                    f"dict['{tgt.slice.id}'] = value where '{tgt.slice.id}' "
                                    f"is a parameter and '{tgt.value.id}' is a module-level "
                                    f"variable â€” attacker controls which key is mutated"
                                ),
                                evidence={"rewrite_candidate":
                                    "Validate key against an allowlist before assignment"},
                            ))
    return detections



def _detect_open_redirect(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Open redirect: redirect() called with user-supplied URL without allowlist validation.
    Enables phishing (attacker spoofs trusted domain in redirect) and OAuth token theft.
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        tainted: set[str] = set()
        class _V(ast.NodeVisitor):
            def visit_Assign(self, node: ast.Assign) -> None:
                if isinstance(node.value, ast.Call):
                    f = node.value.func
                    # Handle: request.args.get(), request.form.get(), etc.
                    is_request_source = False
                    if isinstance(f, ast.Attribute):
                        v = f.value
                        # request.something (direct)
                        if isinstance(v, ast.Name) and v.id == "request":
                            is_request_source = True
                        # request.args.get / request.form.get (nested)
                        elif (isinstance(v, ast.Attribute) and
                              isinstance(v.value, ast.Name) and
                              v.value.id == "request"):
                            is_request_source = True
                    if is_request_source:
                        for t in node.targets:
                            if isinstance(t, ast.Name):
                                tainted.add(t.id)
                self.generic_visit(node)
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_redirect = (
                    (isinstance(func, ast.Name) and func.id == "redirect") or
                    (isinstance(func, ast.Attribute) and func.attr in ("redirect", "Redirect"))
                )
                if is_redirect and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Name) and arg.id in tainted:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"Open redirect at line {node.lineno}: redirect() receives "
                                f"user-supplied URL '{arg.id}' without allowlist validation â€” "
                                f"attacker can redirect to any external site"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate target against a list of safe paths, or use url_for() "
                                "for internal redirects; reject targets with external hosts"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections




def _detect_injection_patterns(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Structured query injection: XPATH, LDAP, XXE, shelve.
    Taint-aware: tracks f-string assignments before they reach query calls.
    """
    import re as _re
    detections: list[_Detection] = []

    def _line_is_comment(pos: int) -> bool:
        ls = content.rfind('\n', 0, pos) + 1
        return content[ls:pos].lstrip().startswith('#')

    def _extract_fstring_tainted(tree) -> set[str]:
        """Variables assigned from f-strings that include other variables."""
        tainted_fstrings: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.JoinedStr):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            tainted_fstrings.add(t.id)
        return tainted_fstrings

    # XPATH: .xpath(f"...") OR .xpath(tainted_variable)
    tree = _parse(content)
    if tree is not None:
        tainted_fstrs = _extract_fstring_tainted(tree)
        class _V(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_xpath = isinstance(func, ast.Attribute) and func.attr == 'xpath'
                if is_xpath and node.args:
                    arg = node.args[0]
                    # Direct f-string in call
                    if isinstance(arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"XPath injection at line {node.lineno}: "
                                f"f-string directly in xpath() call â€” user data enables auth bypass"
                            ),
                            evidence={"rewrite_candidate": "Use XPath parameter binding"},
                        ))
                    # Variable that was assigned from an f-string
                    elif isinstance(arg, ast.Name) and arg.id in tainted_fstrs:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"XPath injection at line {node.lineno}: "
                                f"variable '{arg.id}' (built from f-string) used in xpath() â€” "
                                f"attacker can inject XPath logic"
                            ),
                            evidence={"rewrite_candidate": "Use XPath parameter binding; escape user input"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)

    # XXE: etree.XMLParser(resolve_entities=True)
    for m in _re.finditer(r'XMLParser\s*\(', content):
        if _line_is_comment(m.start()):
            continue
        pre20 = content[max(0, m.start()-20):m.start()]
        if '.' not in pre20:
            continue
        call_window = content[m.start():m.start()+200]
        if 'resolve_entities' not in call_window or '=True' not in call_window:
            continue
        line = content[:m.start()].count('\n') + 1
        detections.append(_Detection(
            lineno=line,
            message=(
                f"XXE injection at line {line}: XMLParser(resolve_entities=True) allows "
                f"external entity expansion â€” reads local files, enables SSRF"
            ),
            evidence={"rewrite_candidate": "Use XMLParser(resolve_entities=False) or defusedxml"},
        ))

    # LDAP: .search() where arg is a tainted variable OR inline f-string
    if tree is not None:
        tainted_fstrs2 = _extract_fstring_tainted(tree)
        class _V2(ast.NodeVisitor):
            def visit_Call(self, node: ast.Call) -> None:
                func = node.func
                is_ldap_search = (isinstance(func, ast.Attribute) and
                                  func.attr == 'search' and
                                  not (isinstance(func.value, ast.Name) and
                                       func.value.id in ('re', '_re', 'regex')))
                if is_ldap_search and len(node.args) >= 2:
                    filter_arg = node.args[1]
                    # Inline f-string
                    if isinstance(filter_arg, ast.JoinedStr):
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"LDAP injection at line {node.lineno}: "
                                f"f-string directly in search() filter â€” user can bypass auth"
                            ),
                            evidence={"rewrite_candidate": "Use ldap3 escape_filter_chars() on user input"},
                        ))
                    # Tainted variable
                    elif isinstance(filter_arg, ast.Name) and filter_arg.id in tainted_fstrs2:
                        detections.append(_Detection(
                            lineno=node.lineno,
                            message=(
                                f"LDAP injection at line {node.lineno}: "
                                f"variable '{filter_arg.id}' (built from f-string) used in "
                                f"search() filter â€” attacker can inject filter logic"
                            ),
                            evidence={"rewrite_candidate": "Use ldap3 escape_filter_chars() on all user values"},
                        ))
                self.generic_visit(node)
        _V2().visit(tree)

    # shelve: shelve.open() with user-controlled data in scope
    for m in _re.finditer(r'shelve\s*[.]\s*open\s*\(', content):
        if _line_is_comment(m.start()):
            continue
        pre3 = content[max(0, m.start()-3):m.start()]
        if "r'" in pre3 or 'r"' in pre3:
            continue
        ctx = content[max(0, m.start()-500):m.start()+500]
        if any(kw in ctx for kw in ['cookies', 'request.', 'args.get', 'form.get']):
            line = content[:m.start()].count('\n') + 1
            detections.append(_Detection(
                lineno=line,
                message=(
                    f"Unsafe deserialization via shelve at line {line}: shelve uses pickle "
                    f"internally â€” user-controlled data enables arbitrary code execution"
                ),
                evidence={"rewrite_candidate": "Replace shelve with json-backed storage"},
            ))

    return detections



def _detect_mass_assignment(content: str, _spec: dict, *, semantic_ir: "Any | None" = None) -> list[_Detection]:
    """
    Mass assignment: user-controlled key used to mutate objects without allowlist.
    Catches:
    1. setattr() in loop over dict.items() â€” classic mass assignment
    2. dict[param_key] = value where param_key is a function parameter
    3. setattr(obj, param_key, value) where param_key is a function parameter
    """
    detections: list[_Detection] = []
    tree = _parse(content)
    if tree is not None:
        class _V(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                param_names = {arg.arg for arg in node.args.args}
                # Pattern 1: for key, value in data.items(): setattr(obj, key, value)
                for child in ast.walk(node):
                    if not isinstance(child, ast.For):
                        continue
                    has_setattr = any(
                        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id == 'setattr'
                        for n in ast.walk(child)
                    )
                    is_dict_items = (
                        isinstance(child.iter, ast.Call) and
                        isinstance(child.iter.func, ast.Attribute) and
                        child.iter.func.attr == 'items'
                    )
                    if has_setattr and is_dict_items:
                        detections.append(_Detection(
                            lineno=child.lineno,
                            message=(
                                f"Mass assignment at line {child.lineno}: setattr() over "
                                f"dict.items() without allowlist â€” attackers can set arbitrary attributes"
                            ),
                            evidence={"rewrite_candidate":
                                "Use an explicit ALLOWED set; check key in ALLOWED before setattr()"},
                        ))

                # Pattern 2: module_dict[param] = value.
                # Only fires for TOP-LEVEL functions writing to module-level dicts.
                # Skips nested functions (where dict is from enclosing scope â€” normal algo pattern).
                self.generic_visit(node)  # handled separately below

                # Pattern 3: setattr(obj, param_key, value) â€” non-loop single call
                for child in ast.walk(node):
                    if not isinstance(child, ast.Expr):
                        continue
                    if not isinstance(child.value, ast.Call):
                        continue
                    call = child.value
                    if (isinstance(call.func, ast.Name) and call.func.id == 'setattr'
                            and len(call.args) >= 2
                            and isinstance(call.args[1], ast.Name)
                            and call.args[1].id in param_names):
                        detections.append(_Detection(
                            lineno=child.lineno,
                            message=(
                                f"Unvalidated setattr at line {child.lineno}: "
                                f"setattr(obj, '{call.args[1].id}', value) where attribute "
                                f"name is a function parameter â€” attacker controls which "
                                f"attribute is set"
                            ),
                            evidence={"rewrite_candidate":
                                "Validate attribute name against an explicit allowlist"},
                        ))
                self.generic_visit(node)
        _V().visit(tree)
    return detections





