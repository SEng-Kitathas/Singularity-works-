from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from forge_semantic_fact_ir_v0_1_2 import canonical_json, freeze_bundle
from forge_semantic_fact_adapters_v0_1_5 import adapt_python_security, adapt_relation_v03
from forge_semantic_fact_index_v0_2 import SemanticFactIndex
from forge_semantic_materializer_v0_1_1 import apply_patch_to_text, plan_replace_fact_evidence, unified_diff
from forge_semantic_snapshot_delta_v0_4 import diff_snapshots, fact_semantic_key

TARGET = ROOT / "investigation" / "vuln_benchmark_quarry_20260902" / "PyGoat"
RUN = ROOT / "investigation" / "sw_forge_reconstruction" / "semantic_materialization_trials" / "pygoat_route_roundtrip_v0_1_1_20260909"
SANDBOX = RUN / "sandbox" / "PyGoat"
LOGICAL_URLS = "PyGoat/introduction/urls.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def dump(name: str, obj: Any) -> None:
    p = RUN / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def git_state() -> dict[str, Any]:
    def g(args: list[str]) -> str:
        r = subprocess.run(["git", "-C", str(TARGET), *args], text=True, capture_output=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else f"ERR:{r.stderr[-500:]}"
    status = g(["status", "--porcelain=v1", "--untracked-files=no"])
    return {"head": g(["rev-parse", "HEAD"]), "tracked_dirty_lines": len(status.splitlines()) if status else 0}


def collect_original_sources() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(TARGET.rglob("*.py")):
        if ".git" in p.parts or "migrations" in p.parts or any(x in p.parts for x in ["venv", ".venv", "__pycache__"]):
            continue
        logical = f"PyGoat/{str(p.relative_to(TARGET)).replace(chr(92), '/')}"
        out[logical] = p.read_text(encoding="utf-8", errors="replace")
    return out


def collect_sandbox_sources() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(SANDBOX.rglob("*.py")):
        logical = f"PyGoat/{str(p.relative_to(SANDBOX)).replace(chr(92), '/')}"
        out[logical] = p.read_text(encoding="utf-8", errors="replace")
    return out


def copy_python_surface(source_texts: Mapping[str, str]) -> None:
    if SANDBOX.exists():
        shutil.rmtree(SANDBOX)
    SANDBOX.mkdir(parents=True, exist_ok=True)
    for logical, text in source_texts.items():
        rel = Path(logical.split("/", 1)[1])
        p = SANDBOX / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def merge_all(bundles):
    work = list(bundles)
    while len(work) > 1:
        nxt = []
        for i in range(0, len(work), 2):
            nxt.append(work[i].merge(work[i + 1]) if i + 1 < len(work) else work[i])
        work = nxt
    return work[0]


def build_snapshot(source_texts: Mapping[str, str], tag: str):
    relation = load(f"mat_rel_{tag}", CODE / "forge_relation_layer_wrapper_v0_3.py")
    pysec = load(f"mat_py_{tag}", CODE / "forge_security_overlay_python_ast_v0_2.py")
    relation_sources = {}
    security_bundles = []
    for logical, text in source_texts.items():
        rel = Path(logical.split("/", 1)[1]).with_suffix("")
        parts = list(rel.parts)
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        module = ".".join(parts) or rel.stem
        relation_sources[module] = {"path": logical, "text": text}
        security_bundles.append(adapt_python_security(pysec.analyze_python(text, logical), {logical: text}))
    rel_out = relation.analyze_python_semantics(relation_sources)
    rel_bundle = adapt_relation_v03(rel_out, source_texts_by_path=source_texts)
    build = rel_bundle.merge(merge_all(security_bundles))
    return freeze_bundle(build, source_texts), rel_out


def select_homepage_route_fact(snapshot):
    matches = []
    for fid, fact in snapshot.facts.items():
        if fact.predicate != "passes_callable":
            continue
        subject = snapshot.entities[fact.subject_id]
        if subject.name != "introduction.urls::<module>":
            continue
        if not isinstance(fact.object_value, Mapping):
            continue
        oid = fact.object_value.get("entity_id")
        if oid not in snapshot.entities:
            continue
        obj = snapshot.entities[oid]
        props = fact.properties.get("relation_properties", {})
        if obj.name == "introduction.views.home" and props.get("host_call") == "path" and props.get("argument_index") == 1:
            matches.append(fid)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one homepage route fact, got {len(matches)}")
    return matches[0]


def main() -> int:
    RUN.mkdir(parents=True, exist_ok=True)
    before_git = git_state()
    original_sources = collect_original_sources()
    original_target_file_sha = sha(TARGET / "introduction" / "urls.py")

    old_snapshot, _ = build_snapshot(original_sources, "old")
    old_index = SemanticFactIndex.build(old_snapshot)
    old_routes = old_index.query(old_snapshot, predicates=["passes_callable"])
    selected_fact_id = select_homepage_route_fact(old_snapshot)
    selected_fact = old_snapshot.facts[selected_fact_id]
    intended_semantic_key = fact_semantic_key(old_snapshot, selected_fact)
    selected_evidence = old_snapshot.evidence[selected_fact.evidence_ids[0]]
    selected_source = old_snapshot.sources[selected_evidence.source_id]

    old_line = original_sources[selected_source.path].encode("utf-8")[selected_evidence.start_byte:selected_evidence.end_byte].decode("utf-8")
    indentation = old_line[: len(old_line) - len(old_line.lstrip(" \t"))]
    newline = "\r\n" if old_line.endswith("\r\n") else "\n" if old_line.endswith("\n") else ""
    replacement = f"{indentation}# LBE semantic materialization: homepage route removed{newline}"

    patch = plan_replace_fact_evidence(
        old_snapshot,
        original_sources,
        fact_id=selected_fact_id,
        new_text=replacement,
        intended_operation="remove_semantic_relation:passes_callable",
    )
    patch2 = plan_replace_fact_evidence(
        old_snapshot,
        original_sources,
        fact_id=selected_fact_id,
        new_text=replacement,
        intended_operation="remove_semantic_relation:passes_callable",
    )
    inverse = patch.inverse()
    dump("patch_plan.json", patch.as_dict())
    dump("inverse_patch_plan.json", inverse.as_dict())
    (RUN / "patch.diff").write_text(unified_diff(patch), encoding="utf-8")

    # Hostile precondition: any drift must reject before mutation.
    precondition_rejected = False
    try:
        apply_patch_to_text(patch, original_sources[selected_source.path] + "# drift")
    except ValueError:
        precondition_rejected = True

    # Materialization plane begins here: isolated sandbox only.
    copy_python_surface(original_sources)
    sandbox_pre_sources = collect_sandbox_sources()
    sandbox_pre_snapshot, _ = build_snapshot(sandbox_pre_sources, "sandbox_pre")
    sandbox_file = SANDBOX / Path(selected_source.path.split("/", 1)[1])
    sandbox_pre_text = sandbox_file.read_text(encoding="utf-8")
    post_text, apply_receipt = apply_patch_to_text(patch, sandbox_pre_text)
    sandbox_file.write_text(post_text, encoding="utf-8")
    sandbox_readback = sandbox_file.read_text(encoding="utf-8")
    post_sources = collect_sandbox_sources()
    post_snapshot, _ = build_snapshot(post_sources, "post")
    observed = diff_snapshots(old_snapshot, post_snapshot)
    post_index = SemanticFactIndex.build(post_snapshot)
    post_routes = post_index.query(post_snapshot, predicates=["passes_callable"])

    stale_index_rejected = False
    try:
        old_index.query(post_snapshot, predicates=["passes_callable"])
    except ValueError:
        stale_index_rejected = True

    # Roll back using emitted inverse patch and prove exact source/map restoration.
    rollback_text, rollback_receipt = apply_patch_to_text(inverse, sandbox_readback)
    sandbox_file.write_text(rollback_text, encoding="utf-8")
    rollback_sources = collect_sandbox_sources()
    rollback_snapshot, _ = build_snapshot(rollback_sources, "rollback")
    rollback_index = SemanticFactIndex.build(rollback_snapshot)
    rollback_routes = rollback_index.query(rollback_snapshot, predicates=["passes_callable"])

    after_git = git_state()
    original_target_file_sha_after = sha(TARGET / "introduction" / "urls.py")

    observed_removed = set(observed.removed_semantic_keys)
    checks = {
        "target_clean_before": before_git["tracked_dirty_lines"] == 0,
        "target_clean_after": after_git["tracked_dirty_lines"] == 0,
        "target_head_unchanged": before_git["head"] == after_git["head"],
        "target_file_hash_unchanged": original_target_file_sha == original_target_file_sha_after,
        "selected_fact_unique": selected_fact_id in old_snapshot.facts,
        "selected_fact_exact_evidence_path": selected_source.path == LOGICAL_URLS,
        "patch_intent_key_matches_selected_fact": patch.intended_semantic_key == intended_semantic_key,
        "patch_plan_deterministic": patch == patch2,
        "patch_authority_none": patch.materializer_authority == "NONE",
        "explicit_apply_required": patch.explicit_apply_required is True,
        "drifted_precondition_rejected": precondition_rejected,
        "sandbox_pre_snapshot_exactly_matches_original": sandbox_pre_snapshot.bundle_id == old_snapshot.bundle_id and canonical_json(sandbox_pre_snapshot.as_dict()) == canonical_json(old_snapshot.as_dict()),
        "patch_readback_post_hash_exact": sha_bytes(sandbox_readback.encode("utf-8")) == patch.expected_post_sha256,
        "observed_delta_authority_none": observed.delta_authority == "NONE",
        "observed_removed_exact_intended_key": observed_removed == {intended_semantic_key},
        "observed_has_no_semantic_additions": len(observed.added_semantic_keys) == 0,
        "observed_has_no_ambiguity": len(observed.ambiguous_semantic_keys) == 0,
        "observed_has_no_multiplicity_change": len(observed.multiplicity_changes) == 0,
        "route_count_decreases_exactly_one": len(old_routes.selected_fact_ids) - len(post_routes.selected_fact_ids) == 1,
        "old_index_rejects_post_snapshot": stale_index_rejected,
        "post_snapshot_differs_from_old": post_snapshot.bundle_id != old_snapshot.bundle_id,
        "inverse_precondition_matches_post": inverse.expected_source_sha256 == patch.expected_post_sha256,
        "rollback_source_exact": rollback_text == original_sources[selected_source.path] and sha_bytes(rollback_text.encode("utf-8")) == patch.expected_source_sha256,
        "rollback_snapshot_exact": rollback_snapshot.bundle_id == old_snapshot.bundle_id and canonical_json(rollback_snapshot.as_dict()) == canonical_json(old_snapshot.as_dict()),
        "rollback_route_count_exact": len(rollback_routes.selected_fact_ids) == len(old_routes.selected_fact_ids),
        "sandbox_only_mutation": after_git == before_git and original_target_file_sha_after == original_target_file_sha,
    }

    summary = {
        "schema": "forge.semantic-materialization-pygoat-route/0.1.1",
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "pass_count": sum(checks.values()),
        "check_count": len(checks),
        "target_git": {"before": before_git, "after": after_git},
        "selected": {
            "fact_id": selected_fact_id,
            "semantic_key": intended_semantic_key,
            "source_path": selected_source.path,
            "source_sha256": selected_source.sha256,
            "evidence_id": selected_evidence.evidence_id,
            "evidence_start_byte": selected_evidence.start_byte,
            "evidence_end_byte": selected_evidence.end_byte,
            "evidence_snippet_sha256": selected_evidence.snippet_sha256,
            "old_text": patch.old_text,
            "new_text": patch.new_text,
        },
        "snapshots": {
            "old": old_snapshot.bundle_id,
            "sandbox_pre": sandbox_pre_snapshot.bundle_id,
            "post": post_snapshot.bundle_id,
            "rollback": rollback_snapshot.bundle_id,
        },
        "route_counts": {
            "old": len(old_routes.selected_fact_ids),
            "post": len(post_routes.selected_fact_ids),
            "rollback": len(rollback_routes.selected_fact_ids),
        },
        "observed_delta": {
            "delta_id": observed.delta_id,
            "changed_sources": len(observed.changed_sources),
            "refreshed_facts": len(observed.refreshed_facts),
            "retained_revision_facts": len(observed.retained_revision_fact_ids),
            "added_semantic_keys": list(observed.added_semantic_keys),
            "removed_semantic_keys": list(observed.removed_semantic_keys),
            "ambiguous_semantic_keys": list(observed.ambiguous_semantic_keys),
            "multiplicity_changes": [x.__dict__ for x in observed.multiplicity_changes],
        },
        "apply_receipt": apply_receipt,
        "rollback_receipt": rollback_receipt,
        "artifact_hashes": {
            "materializer": sha(CODE / "forge_semantic_materializer_v0_1_1.py"),
            "ir": sha(CODE / "forge_semantic_fact_ir_v0_1_2.py"),
            "adapters": sha(CODE / "forge_semantic_fact_adapters_v0_1_5.py"),
            "index": sha(CODE / "forge_semantic_fact_index_v0_2.py"),
            "delta": sha(CODE / "forge_semantic_snapshot_delta_v0_4.py"),
            "relation": sha(CODE / "forge_relation_layer_wrapper_v0_3.py"),
            "python_security": sha(CODE / "forge_security_overlay_python_ast_v0_2.py"),
        },
        "not_proven": [
            "semantic substitution/addition materialization",
            "multi-file patch transactions",
            "language-agnostic syntax lowering",
            "capability/provider substitution round trip",
            "concurrent source edits / optimistic transaction conflict resolution",
            "public/source promotion readiness",
        ],
    }
    dump("summary.json", summary)
    dump("observed_delta.json", observed.as_dict())
    dump("apply_receipt.json", apply_receipt)
    dump("rollback_receipt.json", rollback_receipt)
    manifest = []
    for p in sorted(RUN.iterdir()):
        if p.is_file() and p.name != "output_manifest.json":
            b = p.read_bytes()
            manifest.append({"path": p.name, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)})
    dump("output_manifest.json", {"schema": "forge.semantic-materialization-output-manifest/0.1", "files": manifest, "count": len(manifest)})
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
