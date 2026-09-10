# Forge Semantic Materializer v0.1.1 — Semantic-Key Version Repair — Pre-Execution

Date: 2026-09-09 UTC
Status: **FROZEN CORE CANDIDATE / NOT EXECUTED**
Parent bridge mismatch: `08e451c3052ac2516adf0a8e5c5e9404e6a0f5ff9efe9f5e701d67f7989fe297`.
Control: `83a3a9479282ef76984df3a028de561f04b76189` / CHECKPOINT `b5fb165270e11853cc86071c77868ab05eabdc4edf9e5f2ca852736695e6f8da`, fresh-clone PASS 263.

Authorized repair only: `fact_semantic_key` dependency changes from snapshot-delta v0.3 to current qualified v0.4; materializer version label advances to 0.1.1. SourcePatch fields, exact evidence/source preconditions, patch identity, apply/inverse behavior, authority NONE and explicit-apply requirement are unchanged. First gate is a NEW PyGoat route materialization regression preserving the incumbent 26-check suite.

Pre-execution audit correction: the regression sibling also moves its semantic-key/delta oracle from snapshot-delta v0.3 to v0.4 so the same 26 checks evaluate the current qualified semantic identity contract. This is test-oracle currentness only; materializer behavior remains key-import/version-only.

Final pre-execution receipt audit corrected `artifact_hashes.delta` to reference snapshot-delta v0.4, matching the actual regression oracle. Metadata only; acceptance behavior unchanged.
