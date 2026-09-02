from __future__ import annotations

from pathlib import Path
import textwrap
import mcp.types as types


def _get_open_seams() -> list[types.TextContent]:
    """Return open seams from the trace matrix."""
    seams = [
        "SW-032: forge_context.py sections/parts bug — FIXED in v1.20",
        "SW-033: auth_rate_limit empirical battery — CLOSED in v1.20 (3 cases, 49/49)",
        "SW-034: IDOR/ownership protocol monitor — MISSING, P1",
        "SW-035: Polyglot front door (Tree-sitter/SCIP/CPG) — DEFERRED",
        "SW-036: SSRF requirement-selection sensitivity — KNOWN LIMIT",
        "SW-037: good_service_issue_only FP — KNOWN LIMIT, low priority",
    ]
    text = "# Forge Open Seams\n" + "\n".join(f"  {s}" for s in seams)
    return [types.TextContent(type="text", text=text)]


def _get_live_shadow() -> list[types.TextContent]:
    """Return the current Live Shadow from state/pcmmad/."""
    shadow_path = Path("state/pcmmad/10A SHALL_INIT_LIVE_SHADOW_NEXT.md")
    if shadow_path.exists():
        return [types.TextContent(type="text",
            text=shadow_path.read_text(encoding="utf-8"))]

    # No persisted Live Shadow: fail closed on currentness rather than replaying
    # a hard-coded historical snapshot as if it were live authority.
    text = textwrap.dedent("""
        # LIVE SHADOW — UNAVAILABLE

        Status: UNKNOWN / STALE FALLBACK

        No persisted Live Shadow was found at the expected state path. Historical
        benchmark/status strings are intentionally not synthesized as current truth.
        Rehydrate from the project state surfaces before making load-bearing decisions.
    """).strip()
    return [types.TextContent(type="text", text=text)]


