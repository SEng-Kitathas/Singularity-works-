from __future__ import annotations
# complexity_justified: bridges external CILNX scaffold discovery, dynamic reference loading, append-only manifest emission, and runtime continuity receipts.

from dataclasses import dataclass
import json
import hashlib
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CilnxLocation:
    available: bool
    root: str
    python_ref: str
    internalized_python_ref: str
    schema_path: str
    adapter_report: str
    memory_schema: str
    version_hint: str


@dataclass(frozen=True)
class CilnxBridgeReceipt:
    available: bool
    continuity_written: bool
    root: str
    lineage_id: int
    manifest_sequence: int
    manifest_path: str
    segment_path: str
    audit_ok: bool
    detail: str

    def to_stats(self) -> dict[str, str]:
        return {
            'cilnx': 'online' if self.available else 'missing',
            'cilnx_write': 'yes' if self.continuity_written else 'no',
            'cilnx_manifest': str(self.manifest_sequence),
        }


@dataclass(frozen=True)
class CilnxDiscoveryConfig:
    env_var: str = 'CILNX_ROOT'
    scaffold_name: str = 'cilnx_v0_6_scaffold'
    ai_push_dir_name: str = 'AI_Pushes_Sandbox'


@lru_cache(maxsize=1)
def _candidate_roots() -> tuple[Path, ...]:
    config = CilnxDiscoveryConfig()
    candidates: list[Path] = []
    env_root = os.environ.get(config.env_var, '').strip()
    if env_root:
        candidates.append(Path(env_root))
    home = Path.home()
    desktop_root = home / 'Desktop' / config.ai_push_dir_name
    if desktop_root.exists():
        candidates.extend(desktop_root.rglob(config.scaffold_name))
    repo_root = Path(__file__).resolve().parents[1]
    for parent in [repo_root, *repo_root.parents]:
        probe = parent / config.ai_push_dir_name
        if probe.exists():
            candidates.extend(probe.rglob(config.scaffold_name))
    for drive in _available_windows_drives():
        try:
            candidates.extend(drive.rglob(config.scaffold_name))
        except Exception:
            continue
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        key = str(resolved).lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return tuple(unique)


def _available_windows_drives() -> tuple[Path, ...]:
    roots: list[Path] = []
    if os.name != 'nt':
        return tuple()
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = Path(f'{letter}:/')
        if drive.exists():
            roots.append(drive)
    return tuple(roots)


def _search_support_file(filename: str) -> str:
    for root in _candidate_roots():
        ai_push_root = next((parent for parent in [root, *root.parents] if parent.name == 'AI_Pushes_Sandbox'), None)
        if ai_push_root is None:
            continue
        try:
            match = next(ai_push_root.rglob(filename))
        except StopIteration:
            continue
        return str(match)
    return ''






def cilnx_forge_evidence_dir(project_root: str | Path) -> Path:
    root = Path(project_root)
    path = root / '.forge' / 'cilnx_bridge' / 'forge_evidence'
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_forge_evidence_rollup(
    project_root: str | Path,
    *,
    session_id: str,
    requirement_id: str,
    artifact_id: str,
    payload: dict[str, Any],
) -> Path:
    out_dir = cilnx_forge_evidence_dir(project_root)
    safe_session = session_id.replace('/', '_').replace('\\', '_')
    safe_requirement = requirement_id.replace('/', '_').replace('\\', '_')
    path = out_dir / f'{safe_session}__{safe_requirement}.json'
    body = {
        'session_id': session_id,
        'requirement_id': requirement_id,
        'artifact_id': artifact_id,
        'payload': payload,
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True), encoding='utf-8')
    return path


def load_forge_evidence_rollup(project_root: str | Path, *, session_id: str, requirement_id: str) -> dict[str, Any] | None:
    out_dir = cilnx_forge_evidence_dir(project_root)
    safe_session = session_id.replace('/', '_').replace('\\', '_')
    safe_requirement = requirement_id.replace('/', '_').replace('\\', '_')
    path = out_dir / f'{safe_session}__{safe_requirement}.json'
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def cilnx_session_state_path(project_root: str | Path) -> Path:
    root = Path(project_root)
    path = root / '.forge' / 'cilnx_bridge' / 'vessel_session_state.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def persist_cockpit_session_state(project_root: str | Path, payload: dict[str, Any]) -> Path:
    path = cilnx_session_state_path(project_root)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding='utf-8')
    return path


def load_cockpit_session_state(project_root: str | Path) -> dict[str, Any] | None:
    path = cilnx_session_state_path(project_root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None

def locate_canonical_cilnx() -> CilnxLocation:
    for root in _candidate_roots():
        python_ref = root / 'python_ref' / 'cilnx_ref.py'
        schema_path = root / 'schema' / 'cilnx.fbs'
        adapter_report = Path(_search_support_file('GEOMETRIC_CILNX_V0_6_ADAPTER_REPORT.md')) if _search_support_file('GEOMETRIC_CILNX_V0_6_ADAPTER_REPORT.md') else Path()
        memory_schema = Path(_search_support_file('CILNX_ROUTED_STATEFUL_MEMORY_SCHEMA_2026-04-09.md')) if _search_support_file('CILNX_ROUTED_STATEFUL_MEMORY_SCHEMA_2026-04-09.md') else Path()
        if python_ref.exists() and schema_path.exists():
            return CilnxLocation(
                available=True,
                root=str(root),
                python_ref=str(python_ref),
                internalized_python_ref='singularity_works.cilnx_ref_v06',
                schema_path=str(schema_path),
                adapter_report=str(adapter_report) if adapter_report and adapter_report.exists() else '',
                memory_schema=str(memory_schema) if memory_schema and memory_schema.exists() else '',
                version_hint='v0.6',
            )
    return CilnxLocation(False, '', '', '', '', '', '', '')


def _load_python_ref(location: CilnxLocation):
    from . import cilnx_ref_v06
    return cilnx_ref_v06




def _descriptor_from_dict(cilnx: ModuleType, raw: dict[str, Any]) -> Any:
    return cilnx.SegmentDescriptor(
        segment_id=int(raw['segment_id']),
        path=str(raw['path']),
        schema_fp=int(raw['schema_fp']),
        created_at_ns=int(raw['created_at_ns']),
        block_count=int(raw['block_count']),
        segment_root_hash=str(raw['segment_root_hash']),
        prev_segment_root_hash=str(raw.get('prev_segment_root_hash', '0' * 64)),
        metaindex=dict(raw.get('metaindex', {})),
        footer=dict(raw.get('footer', {})),
    )

def _lineage_id(project_root: Path) -> int:
    digest = hashlib.sha256(str(project_root).encode('utf-8')).hexdigest()
    return int(digest[:32], 16)


def emit_singularity_continuity(
    project_root: str | Path,
    *,
    cockpit_lifecycle: str,
    relaunch_action: str,
    front_readiness: str,
    front_achieved: bool,
    anchor_supported: bool,
    rationale: str,
) -> CilnxBridgeReceipt:
    location = locate_canonical_cilnx()
    if not location.available:
        return CilnxBridgeReceipt(False, False, '', 0, 0, '', '', False, 'canonical CILNX scaffold not found')
    cilnx = _load_python_ref(location)
    root = Path(project_root)
    out_root = root / '.forge' / 'cilnx_bridge'
    blobs = cilnx.BlobStore(out_root / 'blobs')
    writer = cilnx.SegmentWriter(out_root / 'segments', max_objects_per_block=8)
    manifests = cilnx.ManifestStore(out_root / 'manifest')
    verifier = cilnx.Verifier()
    lineage_id = _lineage_id(root)
    line_dir = out_root / 'manifest' / f'lineage-{lineage_id:032x}'
    previous_manifest = None
    previous_hash = '0' * 64
    manifest_sequence = 0
    previous_descriptors: list[Any] = []
    prev_segment_root_hash = '0' * 64
    if line_dir.exists():
        manifest_files = sorted(line_dir.glob('manifest-*.cilm'))
        if manifest_files:
            previous_manifest = manifests.read(manifest_files[-1])
            previous_hash = previous_manifest['manifest_hash']
            manifest_sequence = int(previous_manifest['manifest_sequence']) + 1
            previous_descriptors = [_descriptor_from_dict(cilnx, item) for item in previous_manifest['active_segment_table']]
            if previous_descriptors:
                prev_segment_root_hash = previous_descriptors[-1].segment_root_hash
    now = time.time_ns()
    bundle_id = 0x5A000000000000000000000000000000 | manifest_sequence
    root_id = bundle_id + 1
    forge_id = bundle_id + 2
    cockpit_id = bundle_id + 3
    cilnx_id = bundle_id + 4
    root_blob = blobs.put_bytes(6, 'application/json', cilnx.CODEC_ZLIB, cilnx._stable({
        'system': 'Singularity Works',
        'forge_role': 'workshop',
        'cockpit_role': 'front_end',
        'cilnx_role': 'persistence_storage',
    }))
    state_blob = blobs.put_bytes(6, 'application/json', cilnx.CODEC_ZLIB, cilnx._stable({
        'cockpit_lifecycle': cockpit_lifecycle,
        'relaunch_action': relaunch_action,
        'front_readiness': front_readiness,
        'front_achieved': front_achieved,
        'anchor_supported': anchor_supported,
        'rationale': rationale,
    }))
    nodes = [
        cilnx.NodeRecord(id=root_id, kernel_kind=5, role_code=0xF201, bundle_id=bundle_id, parent_id=0, order_key=0, depth=0, branch_class=0, purpose='singularity works root', content_ref=root_blob.blob_id, created_at_ns=now),
        cilnx.NodeRecord(id=forge_id, kernel_kind=1, role_code=0x0001, bundle_id=bundle_id, parent_id=root_id, order_key=1, depth=1, branch_class=1, purpose='forge workshop', created_at_ns=now),
        cilnx.NodeRecord(id=cockpit_id, kernel_kind=1, role_code=0x0002, bundle_id=bundle_id, parent_id=root_id, order_key=2, depth=1, branch_class=1, purpose='cockpit front end', content_ref=state_blob.blob_id, created_at_ns=now),
        cilnx.NodeRecord(id=cilnx_id, kernel_kind=1, role_code=0x0003, bundle_id=bundle_id, parent_id=root_id, order_key=3, depth=1, branch_class=1, purpose='cilnx continuity substrate', created_at_ns=now),
    ]
    rels = [
        cilnx.RelationRecord(id=bundle_id + 10, relation_kind=4, src_id=forge_id, dst_id=root_id, created_at_ns=now),
        cilnx.RelationRecord(id=bundle_id + 11, relation_kind=4, src_id=cockpit_id, dst_id=root_id, created_at_ns=now),
        cilnx.RelationRecord(id=bundle_id + 12, relation_kind=4, src_id=cilnx_id, dst_id=root_id, created_at_ns=now),
    ]
    segment_id = manifest_sequence + 1
    seg = writer.write_segment(segment_id=segment_id, schema_fp=1, nodes=nodes, relations=rels, prev_segment_root_hash=prev_segment_root_hash)
    current_descriptors = [*previous_descriptors, seg]
    manifest = manifests.seal(
        lineage_id=lineage_id,
        manifest_sequence=manifest_sequence,
        schema_fp=1,
        segment_descriptors=current_descriptors,
        previous_manifest_hash=previous_hash,
        checkpoint_table=previous_manifest['checkpoint_table'] if previous_manifest else [],
    )
    audit = verifier.audit_verify_manifest(manifest)
    return CilnxBridgeReceipt(
        available=True,
        continuity_written=True,
        root=location.root,
        lineage_id=lineage_id,
        manifest_sequence=manifest_sequence,
        manifest_path=manifest['path'],
        segment_path=seg.path,
        audit_ok=bool(audit.get('ok', False)),
        detail='continuity manifest advanced',
    )
