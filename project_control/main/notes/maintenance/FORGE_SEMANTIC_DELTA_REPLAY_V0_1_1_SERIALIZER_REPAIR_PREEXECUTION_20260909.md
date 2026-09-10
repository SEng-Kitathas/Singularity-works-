# Forge Semantic Delta Replay v0.1.1 — Serializer Repair — Pre-Execution

Date: 2026-09-09 UTC
Status: **FROZEN CORE CANDIDATE / NOT EXECUTED**
Parent harness-invalid result: `d78079adf46e9e52824b9a73e314fe3ffbcb2da75c3ce710a5f33ed0b6683a7b`.
Durable control: `59edf0de14ebcb688c037611f72cba992ac51b4e` / CHECKPOINT `f3bb263e862db2aad798f7ca8df60d1a54f4987a54d23eb4b29ca50d13ce460d`, fresh-clone PASS 226.

Authorized behavioral repair only: frozen dataclass digest/descriptor serialization no longer uses `dataclasses.asdict()` (which deep-copies MappingProxy fields). v0.1.1 extracts dataclass fields shallowly and delegates nested mapping/list normalization to the incumbent `canonical_json` path. Typed operations, dependency ordering, base/target preconditions, target freeze check, authority NONE, and the real PyGoat discriminator are unchanged.
