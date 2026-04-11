#!/usr/bin/env python3
"""
Singularity Works — Forge Bridge
Wires LM Studio local models + Claude Code + the Forge into one loop.

Architecture:
  Claude Code (harness + file access)
       ↕
  Forge Bridge (this file — model routing + dialectic orchestration)
       ↕
  LM Studio (synthesis engine — coder + reasoner)
       ↕
  Singularity Works Forge (validation engine — invariant checking)

Model roles (auto-detected from LM Studio):
  REASONER  — 35B MoE reasoning-distilled  → deep analysis, architecture
  CODER     — 7B coder                      → fast synthesis, applying fixes
  GHOST     — 0.8B                          → pre-screening, quick checks

Dialectic loop:
  forge detects violation
  → CODER generates fix with forge findings as structured constraints
  → forge validates
  → if still failing complex issues: REASONER analyzes, CODER implements
  → forge validates again
  → terminates when green or budget exhausted
"""

from __future__ import annotations
import json
import sys
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LM_HOST = os.environ.get("LM_HOST", "127.0.0.1")
LM_PORT = os.environ.get("LM_PORT", "1234")
LM_BASE = f"http://{LM_HOST}:{LM_PORT}"

# Role assignment heuristics — matched against loaded model names
_ROLE_PATTERNS = {
    "reasoner": [
        "35b", "reasoning", "distill", "r1", "r7b-32b", "think", "qwq", "opus"
    ],
    "coder": [
        "coder", "code", "instruct", "7b", "8b", "14b"
    ],
    "ghost": [
        "0.8b", "0.5b", "1b", "tiny", "mini", "small", "ghost"
    ],
}

# Forge package location (relative to this file, or absolute via env)
FORGE_DIR = Path(os.environ.get(
    "FORGE_DIR",
    str(Path(__file__).parent.parent / "sw_v19")
))


# ---------------------------------------------------------------------------
# LM Studio API
# ---------------------------------------------------------------------------

def _get(path: str, timeout: int = 5) -> dict | None:
    try:
        req = urllib.request.Request(f"{LM_BASE}{path}")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _post(path: str, body: dict, timeout: int = 120) -> dict | None:
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{LM_BASE}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def is_lm_running() -> bool:
    result = _get("/health")
    return result is not None


def list_models() -> list[dict]:
    """Return all models currently loaded in LM Studio."""
    result = _get("/v1/models")
    if result and "data" in result:
        return result["data"]
    return []


def assign_roles(models: list[dict]) -> dict[str, str | None]:
    """
    Assign REASONER / CODER / GHOST roles to loaded models.
    Uses name heuristics — deterministic, no guessing.
    """
    roles: dict[str, str | None] = {
        "reasoner": None, "coder": None, "ghost": None
    }
    for model in models:
        model_id = model.get("id", "").lower()
        for role, patterns in _ROLE_PATTERNS.items():
            if roles[role] is not None:
                continue
            if any(p in model_id for p in patterns):
                roles[role] = model.get("id")
    # Fallback: if only one model loaded, it covers all roles
    if models and all(v is None for v in roles.values()):
        roles["reasoner"] = roles["coder"] = roles["ghost"] = models[0]["id"]
    # If coder is unassigned but reasoner is, use reasoner as coder
    if roles["coder"] is None and roles["reasoner"]:
        roles["coder"] = roles["reasoner"]
    return roles


def generate(
    model_id: str,
    system: str,
    user: str,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:
    """Generate from LM Studio via OpenAI-compatible endpoint."""
    body = {
        "model": model_id,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    result = _post("/v1/chat/completions", body, timeout=180)
    if result and "choices" in result:
        return result["choices"][0]["message"]["content"]
    if result and "error" in result:
        return f"[MODEL_ERROR] {result['error']}"
    return "[NO_RESPONSE]"


# ---------------------------------------------------------------------------
# Forge runner
# ---------------------------------------------------------------------------

def run_forge(content: str, requirement: str, project_tag: str = "forge") -> dict:
    """
    Run Singularity Works forge on content.
    Returns structured gate result.
    """
    if not FORGE_DIR.exists():
        return {"error": f"Forge not found at {FORGE_DIR}"}

    script = f"""
import sys
sys.path.insert(0, {str(FORGE_DIR)!r})
import json, shutil, tempfile
from pathlib import Path
from singularity_works.orchestration import Orchestrator
from singularity_works.models import Requirement, RunContext
from singularity_works.facts import FactBus

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    shutil.copytree(str(Path({str(FORGE_DIR)!r}) / 'configs'), base / 'configs')
    orc = Orchestrator(base / 'evidence.jsonl')
    orc.facts = FactBus()
    req = Requirement('REQ-BRIDGE', {requirement!r}, tags=['security', 'quality'])
    ctx = RunContext(
        session_id='bridge-run',
        mode='qa',
        project_tag={project_tag!r},
        metadata={{'apply_transformations': True}},
    )
    result = orc.run(ctx, req, {content!r})
    c = result.gate_summary.counts
    findings = []
    for r in result.gate_summary.results:
        for f in r.findings:
            if f.severity in ('critical', 'high'):
                findings.append({{
                    'gate': r.gate_id,
                    'code': f.code,
                    'message': f.message,
                    'severity': f.severity,
                    'rewrite_candidate': f.evidence.get('rewrite_candidate', ''),
                    'transformation_axiom': f.evidence.get('transformation_axiom', ''),
                    'linked_laws': f.evidence.get('linked_laws', []),
                }})
    candidates = []
    for c2 in result.transformation_plan:
        candidates.append({{
            'id': c2.candidate_id,
            'summary': c2.summary,
            'axiom': c2.transformation_axiom,
            'auto': c2.auto_apply,
            'rewrite': c2.rewrite_candidate,
        }})
    derived = {{f.fact_type for f in orc.facts.facts
                if 'hazard' in f.fact_type or 'confirmed' in f.fact_type}}
    output = {{
        'status': result.assurance.status,
        'counts': result.gate_summary.counts,
        'findings': findings,
        'transformation_candidates': candidates,
        'derived_facts': list(derived),
        'applied_transformations': result.applied_transformations or [],
    }}
    print(json.dumps(output))
"""
    try:
        r = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, timeout=60
        )
        if r.stdout.strip():
            return json.loads(r.stdout.strip())
        return {"error": r.stderr.strip() or "no output"}
    except subprocess.TimeoutExpired:
        return {"error": "forge timeout"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Dialectic loop
# ---------------------------------------------------------------------------

_FORGE_SYSTEM = """You are the CODER half of the Singularity Works dialectic loop.
The REASONER (Forge) has identified invariant violations in the code below.
Your job: produce a corrected version of the code that satisfies ALL findings.

Rules:
1. Preserve the original function signatures and interface exactly.
2. Do not introduce new dependencies unless the forge finding explicitly requires it.
3. Return ONLY the corrected code — no explanation, no markdown fences, no comments beyond what exists in the original.
4. Every finding must be addressed. Do not leave any finding unresolved.
5. The forge will validate your output. You will be called again if it fails."""

_REASONER_SYSTEM = """You are the REASONER in the Singularity Works dialectic loop.
The coder has failed to fix the code after multiple attempts. Your job:
1. Deeply analyze why the fixes aren't working.
2. Produce a step-by-step repair plan that a coder can execute.
3. Be precise about what invariant is violated and exactly what structural change is needed.
4. Do not write the code — write the plan. The coder will implement it."""


def dialectic_fix(
    content: str,
    requirement: str,
    roles: dict[str, str | None],
    project_tag: str = "forge",
    max_rounds: int = 3,
) -> dict[str, Any]:
    """
    Run the dialectic repair loop:
      forge → coder → forge → [if fail] reasoner → coder → forge
    Returns final forge result + transcript of rounds.
    """
    # Initial forge pass
    forge_result = run_forge(content, requirement, project_tag)
    if forge_result.get("error"):
        return {"error": forge_result["error"], "rounds": []}

    rounds = []
    current_content = content
    current_result = forge_result

    if current_result.get("status") == "green":
        return {
            "status": "green",
            "rounds": 0,
            "final_content": current_content,
            "forge_result": current_result,
        }

    coder_id = roles.get("coder")
    reasoner_id = roles.get("reasoner")

    if not coder_id:
        return {
            "status": current_result.get("status"),
            "error": "No coder model available",
            "forge_result": current_result,
        }

    for round_num in range(1, max_rounds + 1):
        findings_text = "\n".join(
            f"  [{f['severity'].upper()}] {f['gate']}: {f['message']}"
            + (f"\n    Fix: {f['rewrite_candidate']}" if f.get("rewrite_candidate") else "")
            for f in current_result.get("findings", [])
        )
        derived_text = ", ".join(current_result.get("derived_facts", []))

        round_info: dict[str, Any] = {
            "round": round_num,
            "forge_status_before": current_result.get("status"),
            "finding_count": len(current_result.get("findings", [])),
        }

        # Escalate to reasoner on round 2+
        if round_num >= 2 and reasoner_id and reasoner_id != coder_id:
            plan = generate(
                reasoner_id,
                _REASONER_SYSTEM,
                f"FINDINGS:\n{findings_text}\n"
                + (f"\nDERIVED HAZARDS: {derived_text}\n" if derived_text else "")
                + f"\nCURRENT CODE:\n{current_content}",
                temperature=0.1,
                max_tokens=2048,
            )
            round_info["reasoner_plan"] = plan[:500]
            # Prepend plan to coder context
            coder_context = f"REPAIR PLAN FROM REASONER:\n{plan}\n\nAPPLY THIS PLAN TO:\n{current_content}"
        else:
            coder_context = (
                f"FORGE FINDINGS (must all be fixed):\n{findings_text}\n"
                + (f"\nDERIVED COMPOUND HAZARDS: {derived_text}\n" if derived_text else "")
                + f"\nCODE TO FIX:\n{current_content}"
            )

        fixed = generate(
            coder_id,
            _FORGE_SYSTEM,
            coder_context,
            temperature=0.1,
            max_tokens=4096,
        )

        # Strip any accidental markdown fences
        fixed = re.sub(r"^```[a-z]*\n?", "", fixed, flags=re.MULTILINE)
        fixed = re.sub(r"\n?```$", "", fixed, flags=re.MULTILINE).strip()

        if fixed.startswith("[MODEL_ERROR]") or fixed == "[NO_RESPONSE]":
            round_info["error"] = fixed
            rounds.append(round_info)
            break

        # Re-validate with forge
        new_result = run_forge(fixed, requirement, project_tag)
        round_info["forge_status_after"] = new_result.get("status")
        round_info["findings_after"] = len(new_result.get("findings", []))
        rounds.append(round_info)

        current_content = fixed
        current_result = new_result

        if current_result.get("status") == "green":
            break

    return {
        "status": current_result.get("status"),
        "rounds": len(rounds),
        "final_content": current_content,
        "forge_result": current_result,
        "round_log": rounds,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_status() -> None:
    if not is_lm_running():
        print(json.dumps({"lm_studio": "offline", "models": []}))
        return
    models = list_models()
    roles = assign_roles(models)
    print(json.dumps({
        "lm_studio": "online",
        "base_url": LM_BASE,
        "models": [m["id"] for m in models],
        "roles": roles,
        "forge_dir": str(FORGE_DIR),
        "forge_present": FORGE_DIR.exists(),
    }, indent=2))


def _cmd_models() -> None:
    models = list_models()
    for m in models:
        print(m["id"])


def _cmd_best_coder() -> None:
    models = list_models()
    roles = assign_roles(models)
    print(roles.get("coder") or (models[0]["id"] if models else ""))


def _cmd_validate(args: list[str]) -> None:
    if not args:
        print(json.dumps({"error": "usage: validate <file> [requirement]"}))
        return
    path = Path(args[0])
    if not path.exists():
        # Treat as inline content
        content = args[0]
    else:
        content = path.read_text(encoding="utf-8", errors="replace")
    req = args[1] if len(args) > 1 else "Code must be safe, correct, and law-compliant."
    result = run_forge(content, req)
    print(json.dumps(result, indent=2))


def _cmd_fix(args: list[str]) -> None:
    if not args:
        print(json.dumps({"error": "usage: fix <file> [requirement]"}))
        return
    if not is_lm_running():
        print(json.dumps({"error": "LM Studio not running"}))
        return
    path = Path(args[0])
    if not path.exists():
        content = args[0]
    else:
        content = path.read_text(encoding="utf-8", errors="replace")
    req = args[1] if len(args) > 1 else "Code must be safe, correct, and law-compliant."
    models = list_models()
    roles = assign_roles(models)
    result = dialectic_fix(content, req, roles)
    print(json.dumps(result, indent=2))


def main() -> None:
    args = sys.argv[1:]
    if not args:
        _cmd_status()
        return
    cmd = args[0]
    rest = args[1:]
    dispatch = {
        "status":     _cmd_status,
        "models":     _cmd_models,
        "best-coder": _cmd_best_coder,
        "validate":   lambda: _cmd_validate(rest),
        "fix":        lambda: _cmd_fix(rest),
    }
    fn = dispatch.get(cmd)
    if fn:
        fn()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
