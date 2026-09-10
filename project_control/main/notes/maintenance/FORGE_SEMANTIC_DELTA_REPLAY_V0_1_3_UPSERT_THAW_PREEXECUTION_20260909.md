# Forge Semantic Delta Replay v0.1.3 — UPSERT Payload Thaw — Pre-Execution

Date: 2026-09-09 UTC
Status: **FROZEN CORE CANDIDATE / NOT EXECUTED**
Parent result: `2b0d36b419b464ef1f98ead7224e2350c4bb86f975e4e3ae1dbef514060eb8b2`.
Control: `046378934b064627d5fd1694fea028bbd09a61ed` / CHECKPOINT `c575f9c916f98f114ae5e41f97cc01709515f358a3dfa6c3d9aa751beb095a27`, fresh-clone PASS 238.

Authorized repair only: after validating the frozen UPSERT payload digest, reconstruct target entities/facts/unknowns with thawed nested values before insertion into the mutable replay workspace; source/evidence dataclasses pass through because they carry no MappingProxy-backed nested state. No change to operation grammar, IDs, dependency order, base preconditions, target freeze verification, authority NONE, or the PyGoat acceptance suite.
