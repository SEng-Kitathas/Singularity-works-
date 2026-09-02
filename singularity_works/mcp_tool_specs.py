from __future__ import annotations

import mcp.types as types


def build_tool_specs() -> list[types.Tool]:
    return [
        types.Tool(
            name="forge_run_battery",
            description=(
                "Run the current Singularity Works verify_build verification suite. "
                "The public tool name is retained for compatibility; historical corpus "
                "battery counts are not implied unless verify_build explicitly emits them. "
                "Returns compile, assurance, and self-verification status."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="forge_get_assurance",
            description=(
                "Get a security verdict for a code snippet against a requirement. "
                "Returns green (passes) or red (fails) with finding codes and evidence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Source code to analyze",
                    },
                    "requirement": {
                        "type": "string",
                        "description": "Security requirement to check against (e.g. 'No SQL injection.')",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session identifier for evidence ledger",
                    },
                },
                "required": ["code", "requirement"],
            },
        ),
        types.Tool(
            name="forge_run_assurance_on_file",
            description=(
                "Run forge security analysis on a file path. "
                "Reads the file and checks against the given requirement."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to analyze",
                    },
                    "requirement": {
                        "type": "string",
                        "description": "Security requirement to check against",
                    },
                },
                "required": ["file_path", "requirement"],
            },
        ),
        types.Tool(
            name="forge_get_open_seams",
            description=(
                "Return the current open seams from the forge trace matrix. "
                "These are unresolved security/architectural gaps that need attention."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="forge_get_live_shadow",
            description=(
                "Return the current PCMMAD Live Shadow — the minimum high-fidelity "
                "active state of the forge session. Use this to understand what's "
                "verified, what's provisional, and what the immediate next step is."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="forge_get_escalation",
            description=(
                "Get the escalation decision for a code artifact. "
                "Returns whether the code should route to the Logic Blueprint Engine (LBE), "
                "which escalation classes fired (A=hard, B=strong, E=complexity, "
                "H=alien, J=domain, K=effect-surface), and a squeaky_clean verdict. "
                "Use this to understand WHY code needs deeper analysis beyond the front gate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to evaluate"},
                    "requirement": {"type": "string", "description": "Security requirement text"},
                },
                "required": ["code", "requirement"],
            },
        ),
        types.Tool(
            name="forge_get_blueprint",
            description=(
                "Get the LBE Blueprint for a code artifact — a color-coded flow map "
                "showing WHAT the code does: every source→transform→sink path with "
                "RED (tainted/dangerous), YELLOW (wrapper theater), GREEN (validated), "
                "PURPLE (obligation violated). Includes Mermaid flowchart and the "
                "minimum replacement annotation — the exact surgical change that turns "
                "each red path green. Works on any language."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Source code to map"},
                    "requirement": {"type": "string", "description": "Security requirement context"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="forge_generate_bounty_report",
            description=(
                "Run forge on a code artifact and generate a structured bug bounty report "
                "(HackerOne/Bugcrowd/Generic) with CVSS scores, CWE references, directed "
                "taint chains, PoC reproduction steps, and remediation. Returns markdown."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code":     {"type": "string",  "description": "Source code to analyze"},
                    "target":   {"type": "string",  "description": "Target app/file name"},
                    "platform": {"type": "string",  "description": "HackerOne | Bugcrowd | Generic"},
                    "scope":    {"type": "string",  "description": "Optional scope note"},
                    "save_to":  {"type": "string",  "description": "Optional output directory"},
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="forge_commit_verified",
            description=(
                "Gate: commit only after the current verify_build suite passes. "
                "Requires compile and self-verification; if verify_build emits an explicit "
                "battery object, that battery must pass too."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Git commit message",
                    },
                    "require_battery": {
                        "type": "boolean",
                        "description": "Whether to require the verify_build qualification suite before committing (legacy field name; default: true)",
                    },
                },
                "required": ["message"],
            },
        ),
    ]
