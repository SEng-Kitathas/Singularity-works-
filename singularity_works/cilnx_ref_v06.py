
from __future__ import annotations

import argparse
import json
import struct
import hashlib
import zlib
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Iterable

MAGIC_SEG = b"CILNXSG1"
MAGIC_MAN = b"CILNXMN1"
CODEC_NONE = 0
CODEC_ZLIB = 1


def _stable(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _h(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


def _hexh(*parts: bytes) -> str:
    return _h(*parts).hex()


def _chunked(seq: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


@dataclass
class BlobDescriptor:
    blob_id: int
    blob_class: int
    media_type: str
    codec: int
    size: int
    hash: str
    path: str


class BlobStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, blob_class: int, media_type: str, codec: int, data: bytes) -> BlobDescriptor:
        digest = _hexh(b"CILNX_BLOB_V1", data)
        blob_id = int(digest[:32], 16)
        sub = self.root / digest[:2] / digest[2:4]
        sub.mkdir(parents=True, exist_ok=True)
        path = sub / digest
        if codec == CODEC_ZLIB:
            payload = zlib.compress(data)
        else:
            payload = data
        path.write_bytes(payload)
        return BlobDescriptor(
            blob_id=blob_id,
            blob_class=blob_class,
            media_type=media_type,
            codec=codec,
            size=len(data),
            hash=digest,
            path=str(path),
        )

    def read_bytes(self, desc: BlobDescriptor | dict[str, Any]) -> bytes:
        if isinstance(desc, dict):
            codec = desc["codec"]
            path = Path(desc["path"])
        else:
            codec = desc.codec
            path = Path(desc.path)
        data = path.read_bytes()
        return zlib.decompress(data) if codec == CODEC_ZLIB else data


@dataclass
class NodeRecord:
    id: int
    kernel_kind: int
    role_code: int
    bundle_id: int
    parent_id: int = 0
    order_key: int = 0
    depth: int = 0
    branch_class: int = 0
    group_key: int = 0
    rollup_parent_id: int = 0
    purpose: str = ""
    boundary: str = ""
    interface_desc: str = ""
    invariants: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)
    created_at_ns: int = 0
    modified_at_ns: int = 0
    actor_id: int = 0
    tool_id: int = 0
    confidence: float = 0.0
    content_ref: int = 0
    inline_payload_ref: int = 0
    evidence_refs: list[int] = field(default_factory=list)
    overlay_refs: list[int] = field(default_factory=list)
    relation_refs: list[int] = field(default_factory=list)
    flags: int = 0
    self_hash: str = ""

    def canonical_map(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("self_hash", None)
        return d

    def seal(self) -> "NodeRecord":
        self.self_hash = _hexh(b"CILNX_NODE_V1", _stable(self.canonical_map()))
        return self


@dataclass
class RelationRecord:
    id: int
    relation_kind: int
    src_id: int
    dst_id: int
    created_at_ns: int = 0
    actor_id: int = 0
    tool_id: int = 0
    confidence: float = 0.0
    qualifiers: dict[str, Any] = field(default_factory=dict)
    self_hash: str = ""

    def canonical_map(self) -> dict[str, Any]:
        d = asdict(self)
        d.pop("self_hash", None)
        return d

    def seal(self) -> "RelationRecord":
        self.self_hash = _hexh(b"CILNX_REL_V1", _stable(self.canonical_map()))
        return self


@dataclass
class SegmentDescriptor:
    segment_id: int
    path: str
    schema_fp: int
    created_at_ns: int
    block_count: int
    segment_root_hash: str
    prev_segment_root_hash: str
    metaindex: dict[str, Any]
    footer: dict[str, Any]


class SegmentWriter:
    def __init__(self, root: str | Path, max_objects_per_block: int = 128):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_objects_per_block = max_objects_per_block

    def _sort_objects(self, objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            objects,
            key=lambda o: (
                0 if o["kind"] == "node" else 1,
                o["payload"].get("bundle_id", 0),
                o["payload"].get("parent_id", 0),
                o["payload"].get("order_key", 0),
                o["payload"].get("created_at_ns", 0),
                o["id"],
            ),
        )

    def write_segment(
        self,
        *,
        segment_id: int,
        schema_fp: int,
        nodes: list[NodeRecord],
        relations: list[RelationRecord],
        prev_segment_root_hash: str = "0" * 64,
    ) -> SegmentDescriptor:
        created = time.time_ns()
        objects: list[dict[str, Any]] = []

        for n in nodes:
            if not n.created_at_ns:
                n.created_at_ns = created
            n.seal()
            objects.append({"kind": "node", "id": n.id, "payload": {**n.canonical_map(), "self_hash": n.self_hash}})

        for r in relations:
            if not r.created_at_ns:
                r.created_at_ns = created
            r.seal()
            objects.append({"kind": "relation", "id": r.id, "payload": {**r.canonical_map(), "self_hash": r.self_hash}})

        objects = self._sort_objects(objects)
        path = self.root / f"seg-{segment_id:032x}.cils"

        metaindex: dict[str, Any] = {}
        block_hashes: list[str] = []
        id_index: list[dict[str, Any]] = []
        parent_order: list[dict[str, Any]] = []
        time_index: list[dict[str, Any]] = []
        type_role_index: list[dict[str, Any]] = []
        rollup_index: list[dict[str, Any]] = []
        checkpoint_index: list[dict[str, Any]] = []

        with path.open("wb") as f:
            f.write(MAGIC_SEG)

            object_offsets: list[tuple[int, int]] = []

            for block_id, chunk in enumerate(_chunked(objects, self.max_objects_per_block)):
                payload = b"\n".join(_stable(x) for x in chunk)
                stored = zlib.compress(payload)
                env = {
                    "block_id": block_id,
                    "object_count": len(chunk),
                    "uncompressed_size": len(payload),
                    "compressed_size": len(stored),
                    "codec": CODEC_ZLIB,
                    "first_object_id": chunk[0]["id"],
                    "last_object_id": chunk[-1]["id"],
                }
                env["block_hash"] = _hexh(b"CILNX_BLOCK_V1", _stable(env), payload)
                block_hashes.append(env["block_hash"])

                envb = _stable(env)
                f.write(struct.pack("<I", len(envb)))
                f.write(envb)
                f.write(struct.pack("<I", len(stored)))
                block_payload_start = f.tell()
                f.write(stored)

                for local_offset, obj in enumerate(chunk):
                    object_offsets.append((block_id, local_offset))
                    id_index.append(
                        {"object_id": obj["id"], "block_id": block_id, "local_offset": local_offset, "object_kind": obj["kind"]}
                    )
                    p = obj["payload"]
                    created_at_ns = p.get("created_at_ns", 0)
                    time_index.append(
                        {"created_at_ns": created_at_ns, "object_id": obj["id"], "block_id": block_id, "local_offset": local_offset}
                    )
                    if obj["kind"] == "node":
                        parent_order.append(
                            {
                                "bundle_id": p.get("bundle_id", 0),
                                "parent_id": p.get("parent_id", 0),
                                "order_key": p.get("order_key", 0),
                                "node_id": obj["id"],
                                "block_id": block_id,
                                "local_offset": local_offset,
                            }
                        )
                        type_role_index.append(
                            {
                                "kernel_kind": p.get("kernel_kind", 0),
                                "role_code": p.get("role_code", 0),
                                "object_id": obj["id"],
                                "block_id": block_id,
                                "local_offset": local_offset,
                            }
                        )
                        role = p.get("role_code", 0)
                        if role in (0x4001, 0x4002, 0x4004):  # checkpoint snapshot/operator brief/seam map
                            rollup_index.append(
                                {
                                    "rollup_node_id": obj["id"],
                                    "source_scope_ref": p.get("content_ref", 0),
                                    "dirty_flag": 0,
                                    "checkpoint_seq": 0,
                                    "block_id": block_id,
                                    "local_offset": local_offset,
                                }
                            )
                        if role == 0x4001:
                            checkpoint_index.append(
                                {
                                    "checkpoint_node_id": obj["id"],
                                    "manifest_sequence": 0,
                                    "source_manifest_hash": "0" * 64,
                                    "block_id": block_id,
                                    "local_offset": local_offset,
                                }
                            )

            def wm(name: str, entries: list[dict[str, Any]]) -> None:
                start = f.tell()
                data = _stable(entries)
                f.write(struct.pack("<I", len(data)))
                f.write(data)
                metaindex[name] = {
                    "offset": start,
                    "length": len(data),
                    "codec": 0,
                    "object_count": len(entries),
                    "hash": _hexh(data),
                }

            wm("ID_INDEX", sorted(id_index, key=lambda x: x["object_id"]))
            wm(
                "PARENT_ORDER_INDEX",
                sorted(parent_order, key=lambda x: (x["bundle_id"], x["parent_id"], x["order_key"], x["node_id"])),
            )
            wm("TIME_INDEX", sorted(time_index, key=lambda x: (x["created_at_ns"], x["object_id"])))
            wm("TYPE_ROLE_INDEX", sorted(type_role_index, key=lambda x: (x["kernel_kind"], x["role_code"], x["object_id"])))
            wm("ROLLUP_INDEX", sorted(rollup_index, key=lambda x: (x["checkpoint_seq"], x["rollup_node_id"])))
            wm("CHECKPOINT_INDEX", sorted(checkpoint_index, key=lambda x: (x["manifest_sequence"], x["checkpoint_node_id"])))

            metaindex_offset = f.tell()
            mib = _stable(metaindex)
            f.write(struct.pack("<I", len(mib)))
            f.write(mib)

            footer = {
                "magic": MAGIC_SEG.decode(),
                "version": 1,
                "schema_fingerprint": schema_fp,
                "segment_id": segment_id,
                "created_at_ns": created,
                "block_count": len(block_hashes),
                "metaindex_offset": metaindex_offset,
                "metaindex_length": len(mib),
                "prev_segment_root_hash": prev_segment_root_hash,
                "flags": 0,
            }
            footer["segment_root_hash"] = _hexh(
                b"CILNX_SEGMENT_V1", _stable(footer), _stable(block_hashes), _stable(metaindex)
            )
            fb = _stable(footer)
            f.write(struct.pack("<I", len(fb)))
            f.write(fb)
            f.write(struct.pack("<I", len(fb)))
            f.write(MAGIC_SEG)

        return SegmentDescriptor(
            segment_id=segment_id,
            path=str(path),
            schema_fp=schema_fp,
            created_at_ns=created,
            block_count=len(block_hashes),
            segment_root_hash=footer["segment_root_hash"],
            prev_segment_root_hash=prev_segment_root_hash,
            metaindex=metaindex,
            footer=footer,
        )


class SegmentReader:
    def open(self, path: str | Path) -> SegmentDescriptor:
        data = Path(path).read_bytes()
        assert data[:8] == MAGIC_SEG and data[-8:] == MAGIC_SEG
        n = struct.unpack("<I", data[-12:-8])[0]
        start = len(data) - 12 - n
        footer = json.loads(data[start:start + n])
        off = footer["metaindex_offset"]
        mlen = struct.unpack("<I", data[off:off + 4])[0]
        mi = json.loads(data[off + 4:off + 4 + mlen])
        return SegmentDescriptor(
            footer["segment_id"],
            str(path),
            footer["schema_fingerprint"],
            footer["created_at_ns"],
            footer["block_count"],
            footer["segment_root_hash"],
            footer["prev_segment_root_hash"],
            mi,
            footer,
        )

    def _iter_blocks(self, seg: SegmentDescriptor):
        data = Path(seg.path).read_bytes()
        p = 8
        for _ in range(seg.block_count):
            env_n = struct.unpack("<I", data[p:p + 4])[0]
            p += 4
            env = json.loads(data[p:p + env_n])
            p += env_n
            payload_n = struct.unpack("<I", data[p:p + 4])[0]
            p += 4
            payload = data[p:p + payload_n]
            p += payload_n
            yield env, zlib.decompress(payload)

    def iter_objects(self, seg: SegmentDescriptor):
        for env, raw in self._iter_blocks(seg):
            for line in raw.splitlines():
                yield json.loads(line)

    def read_meta_entries(self, seg: SegmentDescriptor, name: str):
        data = Path(seg.path).read_bytes()
        m = seg.metaindex[name]
        off = m["offset"]
        n = struct.unpack("<I", data[off:off + 4])[0]
        return json.loads(data[off + 4:off + 4 + n])


class ManifestStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _global_root(self, lineage_id: int, manifest_sequence: int, seg_roots: list[str], previous_manifest_hash: str, flags: int = 0) -> str:
        return _hexh(
            b"CILNX_GLOBAL_ROOT_V1",
            _stable(
                {
                    "lineage_id": lineage_id,
                    "manifest_sequence": manifest_sequence,
                    "segment_roots": seg_roots,
                    "checkpoint_table_ref": 0,
                    "previous_manifest_hash": previous_manifest_hash,
                    "flags": flags,
                }
            ),
        )

    def seal(
        self,
        *,
        lineage_id: int,
        manifest_sequence: int,
        schema_fp: int,
        segment_descriptors: list[SegmentDescriptor],
        previous_manifest_hash: str = "0" * 64,
        checkpoint_table: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        created = time.time_ns()
        seg_roots = [s.segment_root_hash for s in segment_descriptors]
        global_root = self._global_root(lineage_id, manifest_sequence, seg_roots, previous_manifest_hash)
        rec = {
            "format_version": 1,
            "current_schema_fingerprint": schema_fp,
            "lineage_id": lineage_id,
            "manifest_sequence": manifest_sequence,
            "created_at_ns": created,
            "active_segment_table": [s.__dict__ for s in segment_descriptors],
            "checkpoint_table": checkpoint_table or [],
            "checkpoint_table_ref": 0,
            "mount_defaults_ref": 0,
            "detector_defaults_ref": 0,
            "policy_defaults_ref": 0,
            "global_root_hash": global_root,
            "previous_manifest_hash": previous_manifest_hash,
            "signature_set_ref": 0,
            "receipt_set_ref": 0,
            "flags": 0,
        }
        rec["manifest_hash"] = _hexh(b"CILNX_MANIFEST_V1", _stable(rec))
        line = self.root / f"lineage-{lineage_id:032x}"
        line.mkdir(parents=True, exist_ok=True)
        path = line / f"manifest-{manifest_sequence:020d}.cilm"
        payload = _stable(rec)
        path.write_bytes(MAGIC_MAN + struct.pack("<I", len(payload)) + payload + MAGIC_MAN)
        rec["path"] = str(path)
        return rec

    def read(self, path: str | Path) -> dict[str, Any]:
        data = Path(path).read_bytes()
        assert data[:8] == MAGIC_MAN and data[-8:] == MAGIC_MAN
        n = struct.unpack("<I", data[8:12])[0]
        rec = json.loads(data[12:12 + n])
        rec["path"] = str(path)
        return rec


class CheckpointCompactor:
    def __init__(self, blob_store: BlobStore):
        self.blob_store = blob_store

    def compute_dirty_scope(self, source_manifest: dict[str, Any], prior_checkpoint_seq: int | None = None) -> dict[str, Any]:
        return {
            "lineage_id": source_manifest["lineage_id"],
            "manifest_sequence": source_manifest["manifest_sequence"],
            "prior_checkpoint_seq": prior_checkpoint_seq,
            "dirty_reason": "new_manifest_or_explicit_checkpoint",
        }

    def emit_checkpoint_nodes(self, source_manifest: dict[str, Any], dirty_scope: dict[str, Any], children_of_root: list[dict[str, Any]]) -> list[NodeRecord]:
        created = time.time_ns()
        scope_blob = self.blob_store.put_bytes(
            blob_class=6,
            media_type="application/json",
            codec=CODEC_ZLIB,
            data=_stable({"source_manifest_hash": source_manifest["manifest_hash"], "dirty_scope": dirty_scope}),
        )
        brief_blob = self.blob_store.put_bytes(
            blob_class=6,
            media_type="text/markdown",
            codec=CODEC_ZLIB,
            data=(
                f"# Operator Brief\n\n"
                f"- source manifest: `{source_manifest['manifest_hash']}`\n"
                f"- children at root: {len(children_of_root)}\n"
                f"- dirty reason: {dirty_scope['dirty_reason']}\n"
            ).encode("utf-8"),
        )
        seam_blob = self.blob_store.put_bytes(
            blob_class=6,
            media_type="application/json",
            codec=CODEC_ZLIB,
            data=_stable(
                {
                    "dominant_roles": sorted({c["role_code"] for c in children_of_root}),
                    "child_ids": [c["id"] for c in children_of_root],
                }
            ),
        )
        seq = source_manifest["manifest_sequence"] + 1
        bundle_id = 0xC1000000000000000000000000000000 | seq
        root_id = bundle_id + 1
        brief_id = bundle_id + 2
        seam_id = bundle_id + 3
        checkpoint_id = bundle_id + 4
        return [
            NodeRecord(
                id=root_id,
                kernel_kind=5,
                role_code=0x4201,
                bundle_id=bundle_id,
                parent_id=0,
                order_key=0,
                depth=0,
                branch_class=6,
                purpose="checkpoint session bundle",
                created_at_ns=created,
            ),
            NodeRecord(
                id=checkpoint_id,
                kernel_kind=1,
                role_code=0x4001,
                bundle_id=bundle_id,
                parent_id=root_id,
                order_key=1,
                depth=1,
                branch_class=6,
                purpose="checkpoint snapshot",
                content_ref=scope_blob.blob_id,
                created_at_ns=created,
            ),
            NodeRecord(
                id=brief_id,
                kernel_kind=1,
                role_code=0x4002,
                bundle_id=bundle_id,
                parent_id=root_id,
                order_key=2,
                depth=1,
                branch_class=5,
                purpose="operator brief",
                content_ref=brief_blob.blob_id,
                created_at_ns=created,
            ),
            NodeRecord(
                id=seam_id,
                kernel_kind=1,
                role_code=0x4004,
                bundle_id=bundle_id,
                parent_id=root_id,
                order_key=3,
                depth=1,
                branch_class=5,
                purpose="seam map",
                content_ref=seam_blob.blob_id,
                created_at_ns=created,
            ),
        ]


class Verifier:
    def __init__(self):
        self.reader = SegmentReader()

    def quick_verify_segment(self, path: str | Path) -> dict[str, Any]:
        try:
            seg = self.reader.open(path)
            return {"mode": "quick", "segment_id": seg.segment_id, "ok": seg.footer["magic"] == MAGIC_SEG.decode(), "failures": []}
        except Exception as e:
            return {"mode": "quick", "segment_id": None, "ok": False, "failures": [str(e)]}

    def full_verify_segment(self, path: str | Path) -> dict[str, Any]:
        seg = self.reader.open(path)
        objs = list(self.reader.iter_objects(seg))
        failures: list[str] = []
        node_depths: dict[int, int] = {}
        last_order: dict[tuple[int, int], int] = {}

        for obj in objs:
            p = obj["payload"]
            if obj["kind"] == "node":
                exp = _hexh(b"CILNX_NODE_V1", _stable({k: v for k, v in p.items() if k != "self_hash"}))
                if p["self_hash"] != exp:
                    failures.append(f"node_hash:{p['id']}")
                nid = p["id"]
                parent = p.get("parent_id", 0)
                depth = p.get("depth", 0)
                if parent == 0 and depth != 0:
                    failures.append(f"root_depth:{nid}")
                if parent != 0 and parent in node_depths and depth != node_depths[parent] + 1:
                    failures.append(f"depth_mismatch:{nid}")
                if p.get("rollup_parent_id", 0) == nid:
                    failures.append(f"rollup_self:{nid}")
                node_depths[nid] = depth
                scope = (p.get("bundle_id", 0), parent)
                lk = last_order.get(scope, -1)
                if p.get("order_key", 0) < lk:
                    failures.append(f"order_regress:{nid}")
                last_order[scope] = p.get("order_key", 0)
            else:
                exp = _hexh(b"CILNX_REL_V1", _stable({k: v for k, v in p.items() if k != "self_hash"}))
                if p["self_hash"] != exp:
                    failures.append(f"rel_hash:{p['id']}")
                if p["src_id"] == 0 or p["dst_id"] == 0:
                    failures.append(f"rel_zero_endpoint:{p['id']}")
        return {
            "mode": "full",
            "segment_id": seg.segment_id,
            "ok": not failures,
            "failures": failures,
            "checked_objects": len(objs),
            "checked_blocks": seg.block_count,
        }

    def audit_verify_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        seg_roots = [s["segment_root_hash"] for s in manifest["active_segment_table"]]
        expected = _hexh(
            b"CILNX_GLOBAL_ROOT_V1",
            _stable(
                {
                    "lineage_id": manifest["lineage_id"],
                    "manifest_sequence": manifest["manifest_sequence"],
                    "segment_roots": seg_roots,
                    "checkpoint_table_ref": 0,
                    "previous_manifest_hash": manifest.get("previous_manifest_hash", "0" * 64),
                    "flags": manifest.get("flags", 0),
                }
            ),
        )
        failures = []
        if expected != manifest["global_root_hash"]:
            failures.append("global_root_mismatch")
        temp = dict(manifest)
        temp.pop("manifest_hash", None)
        temp.pop("path", None)
        if _hexh(b"CILNX_MANIFEST_V1", _stable(temp)) != manifest["manifest_hash"]:
            failures.append("manifest_hash_mismatch")
        return {"mode": "audit", "ok": not failures, "failures": failures, "checked_segments": len(seg_roots)}


class QueryEngine:
    def __init__(self, manifest: dict[str, Any]):
        self.reader = SegmentReader()
        self.by_id: dict[int, dict[str, Any]] = {}
        self.parent_order: list[dict[str, Any]] = []
        self.time_index: list[dict[str, Any]] = []
        self.type_role_index: list[dict[str, Any]] = []
        self.rollup_index: list[dict[str, Any]] = []
        self.checkpoint_index: list[dict[str, Any]] = []

        for s in manifest["active_segment_table"]:
            seg = self.reader.open(s["path"])
            for obj in self.reader.iter_objects(seg):
                self.by_id[obj["id"]] = obj
            self.parent_order.extend(self.reader.read_meta_entries(seg, "PARENT_ORDER_INDEX"))
            self.time_index.extend(self.reader.read_meta_entries(seg, "TIME_INDEX"))
            self.type_role_index.extend(self.reader.read_meta_entries(seg, "TYPE_ROLE_INDEX"))
            self.rollup_index.extend(self.reader.read_meta_entries(seg, "ROLLUP_INDEX"))
            self.checkpoint_index.extend(self.reader.read_meta_entries(seg, "CHECKPOINT_INDEX"))

        self.parent_order.sort(key=lambda x: (x["bundle_id"], x["parent_id"], x["order_key"], x["node_id"]))
        self.time_index.sort(key=lambda x: (x["created_at_ns"], x["object_id"]))
        self.type_role_index.sort(key=lambda x: (x["kernel_kind"], x["role_code"], x["object_id"]))

    def get_node(self, object_id: int) -> dict[str, Any] | None:
        obj = self.by_id.get(object_id)
        return obj["payload"] if obj and obj["kind"] == "node" else None

    def children(self, bundle_id: int, parent_id: int, start: int | None = None, end: int | None = None) -> list[dict[str, Any]]:
        out = []
        for e in self.parent_order:
            if (
                e["bundle_id"] == bundle_id
                and e["parent_id"] == parent_id
                and (start is None or e["order_key"] >= start)
                and (end is None or e["order_key"] <= end)
            ):
                out.append(self.by_id[e["node_id"]]["payload"])
        return out

    def by_role(self, role_code: int) -> list[dict[str, Any]]:
        return [self.by_id[e["object_id"]]["payload"] for e in self.type_role_index if e["role_code"] == role_code]

    def by_time(self, start_ns: int, end_ns: int) -> list[dict[str, Any]]:
        return [
            self.by_id[e["object_id"]]["payload"]
            for e in self.time_index
            if start_ns <= e["created_at_ns"] <= end_ns
        ]

    def checkpoint_artifacts(self) -> list[dict[str, Any]]:
        return [self.by_id[e["checkpoint_node_id"]]["payload"] for e in self.checkpoint_index]


def demo(out_root: str | Path) -> dict[str, Any]:
    out_root = Path(out_root)
    blobs = BlobStore(out_root / "blobs")
    sw = SegmentWriter(out_root / "segments", max_objects_per_block=2)
    ms = ManifestStore(out_root / "manifest")
    now = time.time_ns()

    nodes = [
        NodeRecord(id=1, kernel_kind=5, role_code=0xF201, bundle_id=1, parent_id=0, order_key=0, depth=0, branch_class=0, purpose="session root", created_at_ns=now),
        NodeRecord(id=2, kernel_kind=1, role_code=0x0001, bundle_id=1, parent_id=1, order_key=1, depth=1, branch_class=1, purpose="pattern family", created_at_ns=now),
        NodeRecord(id=3, kernel_kind=1, role_code=0x0002, bundle_id=1, parent_id=2, order_key=1, depth=2, branch_class=1, purpose="pattern instance A", created_at_ns=now),
        NodeRecord(id=4, kernel_kind=1, role_code=0x0002, bundle_id=1, parent_id=2, order_key=2, depth=2, branch_class=1, purpose="pattern instance B", created_at_ns=now),
    ]
    rels = [
        RelationRecord(id=100, relation_kind=4, src_id=3, dst_id=2, created_at_ns=now),
        RelationRecord(id=101, relation_kind=4, src_id=4, dst_id=2, created_at_ns=now),
    ]
    seg1 = sw.write_segment(segment_id=1, schema_fp=1, nodes=nodes, relations=rels)
    manifest1 = ms.seal(lineage_id=1, manifest_sequence=0, schema_fp=1, segment_descriptors=[seg1])

    q1 = QueryEngine(manifest1)
    dirty = CheckpointCompactor(blobs).compute_dirty_scope(manifest1, None)
    checkpoint_nodes = CheckpointCompactor(blobs).emit_checkpoint_nodes(manifest1, dirty, q1.children(bundle_id=1, parent_id=1))
    seg2 = sw.write_segment(segment_id=2, schema_fp=1, nodes=checkpoint_nodes, relations=[], prev_segment_root_hash=seg1.segment_root_hash)
    manifest2 = ms.seal(
        lineage_id=1,
        manifest_sequence=1,
        schema_fp=1,
        segment_descriptors=[seg1, seg2],
        previous_manifest_hash=manifest1["manifest_hash"],
        checkpoint_table=[{"manifest_sequence": 1, "checkpoint_segment": seg2.segment_id}],
    )

    q2 = QueryEngine(manifest2)
    ver = Verifier()
    result = {
        "segments": [seg1.path, seg2.path],
        "manifest_v0": manifest1["path"],
        "manifest_v1": manifest2["path"],
        "children_of_root_v0": q1.children(bundle_id=1, parent_id=1),
        "children_of_root_v1": q2.children(bundle_id=1, parent_id=1),
        "forge_pattern_instances": q2.by_role(0x0002),
        "checkpoint_artifacts": q2.checkpoint_artifacts(),
        "quick_verify_seg1": ver.quick_verify_segment(seg1.path),
        "full_verify_seg1": ver.full_verify_segment(seg1.path),
        "full_verify_seg2": ver.full_verify_segment(seg2.path),
        "audit_manifest_v1": ver.audit_verify_manifest(manifest2),
    }
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default="./demo_out")
    args = ap.parse_args()
    print(json.dumps(demo(args.out), indent=2))
