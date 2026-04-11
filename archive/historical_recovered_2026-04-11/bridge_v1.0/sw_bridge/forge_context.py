#!/usr/bin/env python3
"""
Singularity Works — Forge Context Manager v3.0
Upgrades claude-code-context-system v2.0 with:
  - Forge gate result recording per session
  - Genome capsule hit tracking per project (priors for future runs)
  - Model routing preferences per project
  - Shadow doc / trace matrix wiring
  - Windows-compatible paths
  - Zero new dependencies (stdlib only)

Backward compatible: reads v2.0 files, writes v3.0.
"""

from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class ForgeContext:
    """
    Project context for a Singularity Works session.
    Stores: project state, forge gate history, genome priors,
    model routing preferences, decisions, tasks, issues.
    """

    VERSION = "3.0.0"

    def __init__(self, path: str | Path = ".forge-context.json") -> None:
        self.path = Path(path)
        self._ctx: dict[str, Any] = {}

    # ── persistence ───────────────────────────────────────────────────

    def init(
        self,
        project_name: str,
        project_root: str = ".",
        project_type: str = "unknown",
        description: str = "",
    ) -> None:
        timeline_id = str(uuid4())
        self._ctx = {
            "version": self.VERSION,
            "project": {
                "name": project_name,
                "root": str(Path(project_root).absolute()),
                "type": project_type,
                "description": description,
                "goals": [],
                "constraints": [],
            },
            "codebase": {
                "key_files": [],
                "conventions": {},
                "dependencies": [],
            },
            "forge": {
                # Genome capsule hit frequency — which capsules fire / succeed
                # Structure: { capsule_id: { "fires": N, "green_after_fix": N } }
                "genome_priors": {},
                # Recent gate result summaries per session
                "sessions": [],
                # Transformation axioms that produced green outcomes in this project
                "proven_axioms": [],
                # Compound facts that were derived in this project
                "derived_fact_history": [],
            },
            "models": {
                # Which LM Studio model worked best for what in this project
                # Auto-updated by the bridge after successful rounds
                "routing_prefs": {
                    "reasoner": None,
                    "coder": None,
                    "ghost": None,
                },
                "last_seen": {},  # model_id → last_used timestamp
            },
            "shadow_docs": {
                # Paths to shadow docs / trace matrix from the forge session
                # Allows forge sessions to carry forward design knowledge
                "trace_matrix": None,
                "research_crosswalk": None,
                "custom_docs": [],
            },
            "log": {
                "tasks": [],
                "decisions": [],
                "issues": [],
            },
            "timelines": [
                {
                    "id": timeline_id,
                    "name": "main",
                    "parent": None,
                    "created": _now(),
                    "status": "active",
                }
            ],
            "active_timeline": timeline_id,
            "session_id": str(uuid4()),
            "created": _now(),
            "updated": _now(),
            "integrity": {"hash": ""},
        }
        self._rehash()

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"No context at {self.path}")
        self._ctx = json.loads(self.path.read_text(encoding="utf-8"))
        # Migrate v2.0 if needed
        if self._ctx.get("version", "").startswith("2."):
            self._migrate_v2()

    def save(self) -> None:
        self._ctx["updated"] = _now()
        self._rehash()
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._ctx, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _rehash(self) -> None:
        # Hash everything except the integrity block itself
        body = {k: v for k, v in self._ctx.items() if k != "integrity"}
        self._ctx["integrity"] = {
            "hash": _sha256(json.dumps(body, sort_keys=True)),
            "timestamp": _now(),
        }

    def verify(self) -> bool:
        body = {k: v for k, v in self._ctx.items() if k != "integrity"}
        expected = _sha256(json.dumps(body, sort_keys=True))
        return self._ctx.get("integrity", {}).get("hash") == expected

    def _migrate_v2(self) -> None:
        """Migrate v2.0 claude-code-context schema to v3.0 forge-context."""
        old = self._ctx
        project = old.get("singletonState", {}).get("project", {})
        log = old.get("logState", {})
        self.init(
            project_name=project.get("name", "migrated"),
            project_root=project.get("root", "."),
            project_type=project.get("type", "unknown"),
            description=project.get("description", ""),
        )
        # Carry over tasks, decisions, issues
        self._ctx["log"]["tasks"] = log.get("tasks", [])
        self._ctx["log"]["decisions"] = log.get("decisions", [])
        self._ctx["log"]["issues"] = log.get("issues", [])
        self._ctx["version"] = self.VERSION

    # ── forge integration ─────────────────────────────────────────────

    def record_forge_session(
        self,
        session_id: str,
        files_analyzed: list[str],
        gate_counts: dict[str, int],
        findings: list[dict],
        genome_capsules_fired: list[str],
        transformation_candidates: list[dict],
        applied_transformations: int,
        final_status: str,
        rounds: int = 0,
    ) -> None:
        """Record a complete forge session result into project context."""
        session = {
            "id": session_id,
            "timestamp": _now(),
            "files": files_analyzed,
            "gate_counts": gate_counts,
            "finding_count": len(findings),
            "high_critical": sum(
                1 for f in findings if f.get("severity") in ("critical", "high")
            ),
            "capsules_fired": genome_capsules_fired,
            "candidates": len(transformation_candidates),
            "applied": applied_transformations,
            "status": final_status,
            "dialect_rounds": rounds,
        }
        sessions = self._ctx["forge"]["sessions"]
        sessions.append(session)
        # Keep last 50 sessions
        if len(sessions) > 50:
            self._ctx["forge"]["sessions"] = sessions[-50:]

        # Update genome priors
        for capsule_id in genome_capsules_fired:
            priors = self._ctx["forge"]["genome_priors"]
            if capsule_id not in priors:
                priors[capsule_id] = {"fires": 0, "green_after_fix": 0}
            priors[capsule_id]["fires"] += 1
            if final_status == "green" and applied_transformations > 0:
                priors[capsule_id]["green_after_fix"] += 1

        # Record proven transformation axioms
        for tc in transformation_candidates:
            axiom = tc.get("transformation_axiom") or tc.get("axiom")
            if axiom and final_status == "green":
                proven = self._ctx["forge"]["proven_axioms"]
                if axiom not in proven:
                    proven.append(axiom)

    def get_genome_priors(self) -> dict[str, dict]:
        """Return capsule hit data for this project — feeds genome bundle selection."""
        return self._ctx["forge"]["genome_priors"]

    def top_capsules(self, n: int = 5) -> list[str]:
        """Top N capsules by fire frequency — project-specific priors."""
        priors = self._ctx["forge"]["genome_priors"]
        return sorted(priors, key=lambda k: priors[k]["fires"], reverse=True)[:n]

    # ── model routing preferences ─────────────────────────────────────

    def update_model_preference(
        self, role: str, model_id: str
    ) -> None:
        """Record which model succeeded for a role in this project."""
        self._ctx["models"]["routing_prefs"][role] = model_id
        self._ctx["models"]["last_seen"][model_id] = _now()

    def get_preferred_models(self) -> dict[str, str | None]:
        return self._ctx["models"]["routing_prefs"]

    # ── shadow docs / trace matrix ────────────────────────────────────

    def link_shadow_doc(self, doc_type: str, path: str) -> None:
        """
        Link a shadow document (trace matrix, research crosswalk, etc.)
        so the forge session can carry forward design knowledge.
        """
        sd = self._ctx["shadow_docs"]
        if doc_type == "trace_matrix":
            sd["trace_matrix"] = str(path)
        elif doc_type == "research_crosswalk":
            sd["research_crosswalk"] = str(path)
        else:
            custom = sd["custom_docs"]
            entry = {"type": doc_type, "path": str(path), "linked": _now()}
            # Deduplicate by path
            custom[:] = [c for c in custom if c["path"] != str(path)]
            custom.append(entry)

    def get_shadow_context(self) -> str:
        """
        Load and return shadow doc content as a condensed string
        for injecting into LLM context.
        """
        parts = []
        sd = self._ctx["shadow_docs"]
        for key in ("trace_matrix", "research_crosswalk"):
            p = sd.get(key)
            if p and Path(p).exists():
                content = Path(p).read_text(encoding="utf-8", errors="replace")
                parts.append(f"=== {key.upper().replace('_',' ')} ===\n{content[:4000]}")
        for custom in sd.get("custom_docs", []):
            p = custom.get("path")
            if p and Path(p).exists():
                content = Path(p).read_text(encoding="utf-8", errors="replace")
                parts.append(f"=== {custom['type'].upper()} ===\n{content[:2000]}")
        return "\n\n".join(parts)

    # ── tasks, decisions, issues (v2.0 compatible) ───────────────────

    def add_task(
        self,
        description: str,
        priority: str = "medium",
        dependencies: list[str] | None = None,
    ) -> str:
        tasks = self._ctx["log"]["tasks"]
        tid = f"task-{len(tasks)+1:03d}"
        tasks.append({
            "id": tid,
            "description": description,
            "status": "pending",
            "priority": priority,
            "created": _now(),
            "timeline_id": self._ctx["active_timeline"],
            "dependencies": dependencies or [],
            "notes": [],
        })
        return tid

    def update_task(self, task_id: str, status: str) -> None:
        for t in self._ctx["log"]["tasks"]:
            if t["id"] == task_id:
                t["status"] = status
                if status == "completed":
                    t["completed"] = _now()
                break

    def add_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: list[dict] | None = None,
        related_tasks: list[str] | None = None,
    ) -> str:
        decisions = self._ctx["log"]["decisions"]
        prev_hash = decisions[-1]["hash"] if decisions else None
        obj: dict[str, Any] = {
            "id": f"dec-{len(decisions)+1:03d}",
            "timestamp": _now(),
            "decision": decision,
            "rationale": rationale,
            "alternatives": alternatives or [],
            "related_tasks": related_tasks or [],
            "timeline_id": self._ctx["active_timeline"],
            "previous_hash": prev_hash,
        }
        obj["hash"] = _sha256(json.dumps(obj, sort_keys=True))
        decisions.append(obj)
        return obj["id"]

    def add_issue(
        self, description: str, severity: str, location: str = ""
    ) -> str:
        issues = self._ctx["log"]["issues"]
        iid = f"issue-{len(issues)+1:03d}"
        issues.append({
            "id": iid,
            "description": description,
            "severity": severity,
            "location": location,
            "discovered": _now(),
            "timeline_id": self._ctx["active_timeline"],
        })
        return iid

    def resolve_issue(self, issue_id: str, resolution: str) -> None:
        for i in self._ctx["log"]["issues"]:
            if i["id"] == issue_id:
                i["resolved"] = _now()
                i["resolution"] = resolution
                break

    def track_file(self, path: str, purpose: str) -> None:
        p = Path(path)
        file_hash = "pending"
        if p.exists():
            file_hash = _sha256(p.read_bytes().decode("utf-8", errors="replace"))[:12]
        key_files = self._ctx["codebase"]["key_files"]
        entry = {"path": str(path), "purpose": purpose, "updated": _now(), "hash": file_hash}
        key_files[:] = [f for f in key_files if f["path"] != str(path)]
        key_files.append(entry)

    # ── timeline management ───────────────────────────────────────────

    def create_timeline(self, name: str, parent: str | None = None) -> str:
        tid = str(uuid4())
        self._ctx["timelines"].append({
            "id": tid,
            "name": name,
            "parent": parent or self._ctx["active_timeline"],
            "created": _now(),
            "status": "active",
        })
        return tid

    def switch_timeline(self, tid: str) -> None:
        if any(t["id"] == tid for t in self._ctx["timelines"]):
            self._ctx["active_timeline"] = tid

    # ── summary ───────────────────────────────────────────────────────

    def summary(self) -> str:
        p = self._ctx["project"]
        log = self._ctx["log"]
        forge = self._ctx["forge"]
        models = self._ctx["models"]
        tasks = log["tasks"]
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        open_issues = sum(1 for i in log["issues"] if "resolved" not in i)
        recent_sessions = forge["sessions"][-5:]
        top_caps = self.top_capsules(5)
        prefs = models["routing_prefs"]

        lines = [
            f"╔═ Singularity Works — {p['name']} ({'v' + self._ctx['version']})",
            f"║  Root   : {p['root']}",
            f"║  Type   : {p['type']}",
            f"║",
            f"║  TASKS       {completed}/{len(tasks)} completed",
            f"║  DECISIONS   {len(log['decisions'])}",
            f"║  ISSUES      {open_issues} open",
            f"║",
            f"║  FORGE SESSIONS   {len(forge['sessions'])}",
            f"║  GENOME PRIORS    {len(forge['genome_priors'])} capsules tracked",
            f"║  TOP CAPSULES     {', '.join(top_caps) or 'none yet'}",
            f"║  PROVEN AXIOMS    {len(forge['proven_axioms'])}",
            f"║",
            f"║  MODEL ROUTING",
            f"║    Reasoner : {prefs.get('reasoner') or 'auto'}",
            f"║    Coder    : {prefs.get('coder') or 'auto'}",
            f"║    Ghost    : {prefs.get('ghost') or 'auto'}",
        ]
        if recent_sessions:
            lines.append("║")
            lines.append("║  RECENT FORGE SESSIONS")
            for s in recent_sessions:
                status_sym = "✓" if s["status"] == "green" else "✗"
                lines.append(
                    f"║    {status_sym} {s['timestamp'][:16]} | "
                    f"{s['finding_count']} findings | "
                    f"{s['applied']} fixed | "
                    f"{s['dialect_rounds']} rounds"
                )
        lines.append(f"║")
        lines.append(f"║  INTEGRITY  {'✓ valid' if self.verify() else '✗ MISMATCH'}")
        lines.append("╚" + "═" * 60)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Singularity Works Context Manager v3.0")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init")
    p_init.add_argument("--name", required=True)
    p_init.add_argument("--root", default=".")
    p_init.add_argument("--type", default="unknown")
    p_init.add_argument("--desc", default="")
    p_init.add_argument("--file", default=".forge-context.json")

    p_summary = sub.add_parser("summary")
    p_summary.add_argument("--file", default=".forge-context.json")

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("--file", default=".forge-context.json")

    p_task = sub.add_parser("task")
    p_task.add_argument("--file", default=".forge-context.json")
    p_task.add_argument("--desc", required=True)
    p_task.add_argument("--priority", default="medium")

    p_decision = sub.add_parser("decision")
    p_decision.add_argument("--file", default=".forge-context.json")
    p_decision.add_argument("--text", required=True)
    p_decision.add_argument("--why", required=True)

    p_link = sub.add_parser("link-shadow")
    p_link.add_argument("--file", default=".forge-context.json")
    p_link.add_argument("--type", required=True)
    p_link.add_argument("--path", required=True)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "init":
        ctx = ForgeContext(args.file)
        ctx.init(args.name, args.root, args.type, args.desc)
        ctx.save()
        print(f"Initialized: {args.file}")
        print(ctx.summary())

    elif args.cmd == "summary":
        ctx = ForgeContext(args.file)
        ctx.load()
        print(ctx.summary())

    elif args.cmd == "verify":
        ctx = ForgeContext(args.file)
        ctx.load()
        ok = ctx.verify()
        print("✓ Integrity valid" if ok else "✗ Hash mismatch — context may be corrupted")

    elif args.cmd == "task":
        ctx = ForgeContext(args.file)
        ctx.load()
        tid = ctx.add_task(args.desc, args.priority)
        ctx.save()
        print(f"Task added: {tid}")

    elif args.cmd == "decision":
        ctx = ForgeContext(args.file)
        ctx.load()
        did = ctx.add_decision(args.text, args.why)
        ctx.save()
        print(f"Decision recorded: {did}")

    elif args.cmd == "link-shadow":
        ctx = ForgeContext(args.file)
        ctx.load()
        ctx.link_shadow_doc(args.type, args.path)
        ctx.save()
        print(f"Linked {args.type} → {args.path}")


if __name__ == "__main__":
    main()
