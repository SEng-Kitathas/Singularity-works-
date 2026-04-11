from __future__ import annotations
# complexity_justified: integrated forge runtime surface
from dataclasses import asdict
from pathlib import Path
import json
import time

from .evidence_ledger import EvidenceLedger
from .hud import ConsoleHUD, snapshot_from_run_result
from .models import Requirement, RunContext
from .orchestration import Orchestrator

GOOD_CONTENT = """from pathlib import Path

def read_text(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')

def safe_open_and_close(path: str):
    fh = open(path, 'r', encoding='utf-8')
    try:
        return fh.read()
    finally:
        fh.close()
"""

BAD_CONTENT = """def unsafe_open(path):
    fh = open(path)
    # TODO: close file later
    return fh.read()
"""

SECURITY_CONTENT = """import requests

def fetch(url: str):
    return requests.get(url, verify=False).text
"""

EXECUTION_CONTENT = """def parse_number(expr: str):
    return eval(expr)
"""


def _demo_requirement(good: bool | None = None, scenario: str | None = None) -> Requirement:
    if scenario == "security":
        return Requirement(
            requirement_id="REQ-DEMO-SECURITY",
            text=(
                "Verification should be enabled. Artifact must not contain eval. "
                "Dangerous execution primitives should be absent."
            ),
            tags=["quality", "security"],
        )
    if scenario == "execution":
        return Requirement(
            requirement_id="REQ-DEMO-EXECUTION",
            text=(
                "Artifact must not contain eval. Dangerous execution primitives should be absent. "
                "Use safer parsing instead of dynamic execution."
            ),
            tags=["quality", "security", "execution"],
        )
    req_id = "REQ-DEMO-GOOD" if good else "REQ-DEMO-BAD"
    text = (
        "Artifact must not contain TODO. Resource discipline should be respected "
        "and code must close file. Artifact must not contain eval. "
        "Dangerous execution primitives should be absent."
    )
    return Requirement(requirement_id=req_id, text=text, tags=["quality"])


def _summary(base_dir: Path, ctx: RunContext, result, req: Requirement) -> dict:
    ledger = EvidenceLedger(base_dir / "evidence.jsonl")
    primary_claim = ledger.rollup_claim(
        f"claim:{req.requirement_id}:primary",
        ctx.session_id,
    )
    return {
        "session_id": ctx.session_id,
        "artifact_id": result.artifact.artifact_id,
        "assurance": result.assurance.to_dict(),
        "gate_counts": result.gate_summary.counts,
        "session_rollup": ledger.rollup_session(ctx.session_id),
        "requirement_rollup": ledger.rollup_requirement(
            req.requirement_id,
            ctx.session_id,
        ),
        "artifact_rollup": ledger.rollup_artifact(result.artifact.artifact_id),
        "primary_claim_rollup": primary_claim,
        "recursive_audit": result.recursive_audit,
        "derivation_trace": result.derivation_trace,
        "transformation_plan": [asdict(candidate) for candidate in result.transformation_plan],
        "applied_transformations": [asdict(item) for item in result.applied_transformations],
        "embodiment_trace": result.embodiment_trace,
        "verification_trace": result.verification_trace,
        "fractal_cycle": result.fractal_cycle,
        "linked_laws": result.pattern.get("linked_laws", []),
        "genome_bundle": result.genome_bundle,
        "fact_summary": result.fact_summary,
    }


def _render_summary(ctx: RunContext, req: Requirement, result, orchestrator: Orchestrator) -> None:
    snap = snapshot_from_run_result(
        result,
        orchestrator,
        app_name="Singularity Works",
        version="v1.36",
        branch="main",
        uptime_s=0.0,
        display_mode="full",
    )
    snap.mode = ctx.mode
    snap.provider = "local"
    snap.session_id = ctx.session_id
    snap.project_tag = ctx.project_tag
    snap.phase = "complete"
    snap.requirement = req.requirement_id
    snap.radical = "+".join(result.pattern.get("radicals", [])) or "TRUST"
    snap.validator = "gate-pack"
    snap.progress_label = "demo run"
    snap.progress_value = 1.0
    snap.stats = {
        "assurance": result.assurance.status,
        "family": result.artifact.family,
        "monitors": str(len(result.monitor_events)),
        "depth": result.recursive_audit["implementation_depth"],
        "derive": f"g{result.derivation_trace.get('gate_count',0)}/m{result.derivation_trace.get('monitor_count',0)}",
        "verify": result.verification_trace.get('assurance_verification',{}).get('status','unknown'),
        "embody": result.verification_trace.get('embodiment_verification',{}).get('status','unknown'),
    }
    snap.risks = result.assurance.residual + result.assurance.falsified
    snap.warnings = result.recursive_audit["naivety_flags"]
    snap.events = [
        "orchestration complete",
        f"artifact={result.artifact.artifact_id}",
        f"assurance={result.assurance.status}",
        f"derive={result.derivation_trace.get('gate_count',0)} gates/{result.derivation_trace.get('monitor_count',0)} monitors",
        f"verify={result.verification_trace.get('gate_verification',{}).get('status','unknown')}",
    ]
    hud = ConsoleHUD()
    with hud:
        hud.render(snap)
        time.sleep(1.0)


def demo_run(
    base_dir: str | Path,
    good: bool = True,
    show_hud: bool = True,
    apply_transformations: bool = False,
    scenario: str | None = None,
) -> dict:
    base_dir = Path(base_dir)
    # Ensure genome and configs are accessible from base_dir.
    # The Orchestrator resolves genome at ledger_path.parent / "configs" / "seed_genome.json".
    _own_configs = Path(__file__).parent.parent / "configs"
    target_configs = base_dir / "configs"
    if _own_configs.exists() and not target_configs.exists():
        import shutil
        shutil.copytree(str(_own_configs), str(target_configs))
    orchestrator = Orchestrator(base_dir / "evidence.jsonl")
    if scenario == "security":
        session_id = "demo-session-security-remediated" if apply_transformations else "demo-session-security"
    elif scenario == "execution":
        session_id = "demo-session-execution-remediated" if apply_transformations else "demo-session-execution"
    elif good:
        session_id = "demo-session-good"
    else:
        session_id = "demo-session-bad-remediated" if apply_transformations else "demo-session-bad"
    ctx = RunContext(
        session_id=session_id,
        mode="run",
        project_tag="singularity-works",
        metadata={"apply_transformations": apply_transformations},
    )
    req = _demo_requirement(good, scenario)
    if scenario == "security":
        content = SECURITY_CONTENT
    elif scenario == "execution":
        content = EXECUTION_CONTENT
    else:
        content = GOOD_CONTENT if good else BAD_CONTENT
    result = orchestrator.run(ctx, req, content)
    summary = _summary(base_dir, ctx, result, req)
    summary["good"] = good
    (base_dir / f"{ctx.session_id}_summary.json").write_text(
        json.dumps(summary, indent=2)
    )
    if show_hud:
        _render_summary(ctx, req, result, orchestrator)
    return summary
