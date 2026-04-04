from __future__ import annotations
# complexity_justified: genome axiom -> rewrite strategy registry
# This is the bridge that makes genome transformation_axioms executable.
# Every axiom name in a capsule must resolve here. If it doesn't, the
# candidate is escalated (review_required) rather than silently skipped.

from typing import Callable

# Rewrite function signature: (content: str) -> (new_content, changed, before, after)
RewriteFn = Callable[[str], tuple[str, bool, str, str]]


def _rewrite_leaked_open(content: str) -> tuple[str, bool, str, str]:
    """
    Replace leaked open()/read() pair with context manager.
    Skips intervening blank lines and comment lines so that
    TODO markers between open() and return don't block the rewrite.
    """
    before = content
    lines = content.splitlines()
    out: list[str] = []
    changed = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if "=" in stripped and "open(" in stripped:
            indent = line[: len(line) - len(line.lstrip())]
            left = stripped.split("=", 1)[0].strip()
            # Scan ahead: skip blank lines and comment lines to find return
            j = i + 1
            skipped: list[str] = []
            while j < len(lines):
                nxt = lines[j].strip()
                if nxt == "" or nxt.startswith("#"):
                    skipped.append(lines[j])
                    j += 1
                else:
                    break
            if j < len(lines) and lines[j].strip() == f"return {left}.read()":
                out.append(f"{indent}with open(path, 'r', encoding='utf-8') as {left}:")
                out.append(f"{indent}    return {left}.read()")
                changed = True
                i = j + 1  # skip open line + intervening comments + return line
                continue
        out.append(line)
        i += 1
    after = "\n".join(out)
    return after, changed, before, after


def _rewrite_verify_false(content: str) -> tuple[str, bool, str, str]:
    """Re-enable TLS verification disabled by verify=False."""
    import re
    before = content
    after, count = re.subn(r"verify\s*=\s*False", "verify=True", content)
    return after, count > 0, before, after


def _rewrite_eval_to_literal_eval(content: str) -> tuple[str, bool, str, str]:
    """Replace eval() with ast.literal_eval() and inject import if needed."""
    before = content
    if "eval(" not in content:
        return content, False, before, content
    after = content.replace("eval(", "ast.literal_eval(")
    if "import ast" not in after:
        lines = after.splitlines()
        insert_at = 0
        while insert_at < len(lines) and lines[insert_at].startswith(("from __future__", "#")):
            insert_at += 1
        if insert_at < len(lines) and lines[insert_at].startswith("import "):
            lines.insert(insert_at + 1, "import ast")
        else:
            lines.insert(insert_at, "import ast")
        after = "\n".join(lines)
    return after, after != before, before, after


def _remove_todo_lines(content: str) -> tuple[str, bool, str, str]:
    """Remove TODO/FIXME comment lines."""
    before = content
    kept: list[str] = []
    changed = False
    for line in content.splitlines():
        low = line.lower()
        if "todo" in low or "fixme" in low:
            changed = True
            continue
        kept.append(line)
    after = "\n".join(kept)
    return after, changed, before, after


# Registry: genome transformation_axiom name -> rewrite function
# None means the axiom requires human judgment — forge escalates automatically.
STRATEGIES: dict[str, RewriteFn | None] = {
    "prefer_scoped_cleanup_to_manual_cleanup": _rewrite_leaked_open,
    "prefer_verified_tls_to_disabled": _rewrite_verify_false,
    "prefer_literal_eval_to_dynamic_eval": _rewrite_eval_to_literal_eval,
    "remove_todo_markers": _remove_todo_lines,
    # Human-review axioms: forge produces candidates but does not auto-apply
    "replace_mutable_default_with_none_sentinel": None,
    "prefer_explicit_args_to_shell_string": None,
    "prefer_parameter_binding_to_string_interpolation": None,
    "prefer_atomic_open_to_access_then_open": None,
    "inject_host_denylist_validation": None,
    "prefer_csprng_to_prng": None,
    "prefer_decimal_to_float_for_money": None,
    "wrap_unsafe_in_bounds_checked_function": None,
    "prefer_explicit_state_machine_for_sensitive_sequences": None,
    "push_validation_to_sink_boundary": None,
}


def apply_by_axiom(
    content: str,
    axiom: str,
) -> tuple[str, bool, str, str]:
    """
    Apply the rewrite strategy registered under axiom.
    Returns (new_content, changed, before, after).
    If axiom is unknown or None, returns unchanged content with changed=False.
    """
    fn = STRATEGIES.get(axiom)
    if fn is None:
        return content, False, content, content
    return fn(content)


def is_auto_applicable(axiom: str) -> bool:
    """True if the axiom has an executable rewrite strategy."""
    return axiom in STRATEGIES and STRATEGIES[axiom] is not None
