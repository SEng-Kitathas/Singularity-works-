from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .forge_context_blocks import _now, _sha256


class ForgeContextOpsMixin:
    # ── v3.0 compat methods ───────────────────────────────────────────

    def get_genome_priors(self) -> dict[str, dict]:
        return self.smem_get_priors()

    def top_capsules(self, n: int = 5) -> list[str]:
        priors = self.smem_get_priors()
        return sorted(priors, key=lambda k: priors[k].get("fires", 0), reverse=True)[:n]

    def update_model_preference(self, role: str, model_id: str) -> None:
        self._ctx["models"]["routing_prefs"][role] = model_id
        self._ctx["models"]["last_seen"][model_id] = _now()

    def get_preferred_models(self) -> dict[str, str | None]:
        return self._ctx["models"]["routing_prefs"]

    def link_shadow_doc(self, doc_type: str, path: str) -> None:
        sd = self._ctx["shadow_docs"]
        if doc_type == "trace_matrix":
            sd["trace_matrix"] = str(path)
        elif doc_type == "research_crosswalk":
            sd["research_crosswalk"] = str(path)
        else:
            custom = sd["custom_docs"]
            entry = {"type": doc_type, "path": str(path), "linked": _now()}
            custom[:] = [c for c in custom if c["path"] != str(path)]
            custom.append(entry)

    def get_shadow_context(self) -> str:
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

    def add_task(self, description: str, priority: str = "medium",
                 dependencies: list[str] | None = None) -> str:
        tasks = self._ctx["log"]["tasks"]
        tid = f"task-{len(tasks)+1:03d}"
        tasks.append({
            "id": tid, "description": description, "status": "pending",
            "priority": priority, "created": _now(),
            "timeline_id": self._ctx["active_timeline"],
            "dependencies": dependencies or [], "notes": [],
        })
        return tid

    def update_task(self, task_id: str, status: str) -> None:
        for t in self._ctx["log"]["tasks"]:
            if t["id"] == task_id:
                t["status"] = status
                if status == "completed":
                    t["completed"] = _now()
                break

    def add_decision(self, decision: str, rationale: str,
                     alternatives: list[dict] | None = None,
                     related_tasks: list[str] | None = None) -> str:
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

    def add_issue(self, description: str, severity: str, location: str = "") -> str:
        issues = self._ctx["log"]["issues"]
        iid = f"issue-{len(issues)+1:03d}"
        issues.append({
            "id": iid, "description": description, "severity": severity,
            "location": location, "discovered": _now(),
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
            try:
                file_hash = _sha256(p.read_bytes().decode("utf-8", errors="replace"))[:12]
            except Exception:
                pass
        key_files = self._ctx["codebase"]["key_files"]
        entry = {"path": str(path), "purpose": purpose, "updated": _now(), "hash": file_hash}
        key_files[:] = [f for f in key_files if f["path"] != str(path)]
        key_files.append(entry)

    def create_timeline(self, name: str, parent: str | None = None) -> str:
        tid = str(uuid4())
        self._ctx["timelines"].append({
            "id": tid, "name": name,
            "parent": parent or self._ctx["active_timeline"],
            "created": _now(), "status": "active",
        })
        return tid

    def switch_timeline(self, tid: str) -> None:
        if any(t["id"] == tid for t in self._ctx["timelines"]):
            self._ctx["active_timeline"] = tid

