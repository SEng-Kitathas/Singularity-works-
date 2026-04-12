# complexity_justified: core memory and contradiction state kept together for audited retrieval behavior.
#!/usr/bin/env python3
"""Singularity Works — Forge Context Manager v4.0."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .forge_context_blocks import (
    EpistemicStatus,
    _decode_contradiction,
    _decode_semantic,
    _decode_witness,
    _encode_semantic,
    _now,
    _sha256,
)
from .forge_context_memory import ForgeContextMemoryMixin
from .forge_context_ops import ForgeContextOpsMixin


class ForgeContext(ForgeContextMemoryMixin, ForgeContextOpsMixin):
    """Project cognitive ledger for a Singularity Works session."""

    VERSION = "4.0.0"
    CONSOLIDATION_CONFIG = {
        "min_confidence_for_promotion": 0.6,
        "min_support_for_stable": 3,
        "max_epmem_entries": 500,
        "max_sessions": 100,
    }

    def __init__(self, path: str = ".forge-context.json") -> None:
        self.path = Path(path)
        self._ctx: dict = {}
        from .forge_context_blocks import SessionBuffer
        self.sbuf = SessionBuffer()

    def _epmem_blocks(self):
        return [_decode_witness(entry) for entry in self._ctx.get("epmem", [])]

    def _smem_blocks(self):
        return [_decode_semantic(entry) for entry in self._ctx.get("smem", [])]

    def _contradiction_blocks(self):
        return [_decode_contradiction(entry) for entry in self._ctx.get("contradictions", [])]

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
            "codebase": {"key_files": [], "conventions": {}, "dependencies": []},
            "epmem": [],
            "smem": [],
            "contradictions": [],
            "forge": {
                "genome_priors": {},
                "sessions": [],
                "proven_axioms": [],
                "derived_fact_history": [],
            },
            "models": {
                "routing_prefs": {"reasoner": None, "coder": None, "ghost": None},
                "last_seen": {},
            },
            "shadow_docs": {
                "trace_matrix": None,
                "research_crosswalk": None,
                "custom_docs": [],
            },
            "log": {"tasks": [], "decisions": [], "issues": []},
            "timelines": [{
                "id": timeline_id, "name": "main", "parent": None,
                "created": _now(), "status": "active",
            }],
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
        v = self._ctx.get("version", "")
        if v.startswith("2."):
            self._migrate_v2()
        elif v.startswith("3."):
            self._migrate_v3()

    def save(self) -> None:
        self._ctx["updated"] = _now()
        self._rehash()
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._ctx, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _rehash(self) -> None:
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
        old = self._ctx
        project = old.get("singletonState", {}).get("project", {})
        log = old.get("logState", {})
        self.init(
            project_name=project.get("name", "migrated"),
            project_root=project.get("root", "."),
            project_type=project.get("type", "unknown"),
            description=project.get("description", ""),
        )
        self._ctx["log"]["tasks"] = log.get("tasks", [])
        self._ctx["log"]["decisions"] = log.get("decisions", [])
        self._ctx["log"]["issues"] = log.get("issues", [])

    def _migrate_v3(self) -> None:
        old = self._ctx
        self.init(
            project_name=old.get("project", {}).get("name", "migrated"),
            project_root=old.get("project", {}).get("root", "."),
            project_type=old.get("project", {}).get("type", "unknown"),
            description=old.get("project", {}).get("description", ""),
        )
        self._ctx["project"]["goals"] = old.get("project", {}).get("goals", [])
        self._ctx["project"]["constraints"] = old.get("project", {}).get("constraints", [])
        self._ctx["codebase"] = old.get("codebase", self._ctx["codebase"])
        self._ctx["forge"] = old.get("forge", self._ctx["forge"])
        self._ctx["models"] = old.get("models", self._ctx["models"])
        self._ctx["shadow_docs"] = old.get("shadow_docs", self._ctx["shadow_docs"])
        self._ctx["log"] = old.get("log", self._ctx["log"])
        self._ctx["timelines"] = old.get("timelines", self._ctx["timelines"])
        self._ctx["active_timeline"] = old.get("active_timeline", self._ctx["active_timeline"])
        self._ctx["session_id"] = old.get("session_id", self._ctx["session_id"])
        self._ctx["created"] = old.get("created", self._ctx["created"])
        self._ctx["updated"] = old.get("updated", self._ctx["updated"])

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
        epmem_count = len(self._ctx.get("epmem", []))
        smem_stable = sum(1 for b in self._ctx.get("smem", []) if b.get("status") == EpistemicStatus.STABLE_SEMANTIC.value)
        smem_provisional = sum(1 for b in self._ctx.get("smem", []) if b.get("status") == EpistemicStatus.PROVISIONAL_SEMANTIC.value)
        contradiction_count = len(self._ctx.get("contradictions", []))
        lines = [
            "╔" + "═" * 60,
            f"║  SINGULARITY WORKS CONTEXT  v{self.VERSION}",
            f"║  PROJECT   {p.get('name', '?')}  [{p.get('type', '?')}]",
            f"║  ROOT      {p.get('root', '?')}",
            "║",
            f"║  TASKS     {completed}/{len(tasks)} completed  |  open issues: {open_issues}",
            f"║  FORGE     sessions={len(forge['sessions'])}  priors={len(self.get_genome_priors())}  top_caps={', '.join(top_caps) or '-'}",
            f"║  MEMORY    epmem={epmem_count}  smem(stable={smem_stable}, provisional={smem_provisional})  contradictions={contradiction_count}",
            "║",
            "║  ROUTING",
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
                    f"║    {status_sym} {s['timestamp'][:16]} | {s['finding_count']} findings | {s['applied']} fixed | {s['dialect_rounds']} rounds"
                )
        lines.append("║")
        lines.append(f"║  INTEGRITY  {'✓ valid' if self.verify() else '✗ MISMATCH'}")
        lines.append("╚" + "═" * 60)
        return "\n".join(lines)


from .forge_context_cli import main


if __name__ == "__main__":
    main()
