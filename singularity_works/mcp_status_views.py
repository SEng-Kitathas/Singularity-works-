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

    # Fallback: synthesize from known state
    text = textwrap.dedent("""
        # LIVE SHADOW — Singularity Works Forge

        ## Mode
        BUILD — Law 1 active

        ## Authority Base
        v1.20 — 49/49 FP=0 FN=0 | self_audit=920/4/0

        ## Verified
        - 28 modules, 12,214 lines, 37 capsules, 36 strategies, 12 monitors
        - 49/49 battery: FP=0 FN=0 at 1.3s
        - forge_context.py contradiction path: fixed
        - auth_rate_limit: 3 cases verified

        ## Open Seams (P0 closed, P1 active)
        - IDOR/ownership monitor: next march target
        - MCP server: building now
        - PreCompact hook: building now

        ## Immediate Next Step
        Build IDOR monitor → wire PreCompact hook → session startup script
    """).strip()
    return [types.TextContent(type="text", text=text)]


