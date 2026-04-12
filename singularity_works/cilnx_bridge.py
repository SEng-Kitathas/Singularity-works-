from __future__ import annotations
# complexity_justified: bridges external CILNX scaffold discovery, dynamic reference loading, append-only manifest emission, and runtime continuity receipts.

from dataclasses import dataclass
import json
import hashlib
import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class CilnxLocation:
    available: bool
    root: str
    python_ref: str
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


def _candidate_roots() -> tuple[Path, ...]:
    return (
        Path(r'C:/Users/ancal/Desktop/AI_Pushes_Sandbox/historical data/Geometric reason/rosetta/CILNX_MASTER_DROP_2026-04-01/CILNX_MASTER_DROP_2026-04-01/builds/cilnx_v0_6_scaffold'),
    )




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
        adapter_report = Path(r'C:/Users/ancal/Desktop/AI_Pushes_Sandbox/historical data/Geometric reason/TQ2/GEOMETRIC_THREAD_PROJECT_ARCHIVE/06_CIL_ADAPTER/GEOMETRIC_CILNX_V0_6_ADAPTER_REPORT.md')
        memory_schema = Path(r'C:/Users/ancal/Desktop/AI_Pushes_Sandbox/system/CILNX_ROUTED_STATEFUL_MEMORY_SCHEMA_2026-04-09.md')
        if python_ref.exists() and schema_path.exists():
            return CilnxLocation(
                available=True,
                root=str(root),
                python_ref=str(python_ref),
                schema_path=str(schema_path),
                adapter_report=str(adapter_report) if adapter_report.exists() else '',
                memory_schema=str(memory_schema) if memory_schema.exists() else '',
                version_hint='v0.6',
            )
    return CilnxLocation(False, '', '', '', '', '', '')


def _load_python_ref(location: CilnxLocation) -> ModuleType:
    spec = importlib.util.spec_from_file_location('cilnx_ref_runtime', location.python_ref)
    if spec is None or spec.loader is None:
        raise RuntimeError('unable to load CILNX python reference')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module




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
