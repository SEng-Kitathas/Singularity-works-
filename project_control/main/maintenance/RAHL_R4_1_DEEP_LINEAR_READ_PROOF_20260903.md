# RAHL R4.1 Deep Linear Read Proof — 2026-09-03

Carrier: `RAHL_ENGINEERING_CANONICAL_SOP_R4_1_2026-09-03.zip`
Carrier SHA-256: `af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`
Carrier bytes: `309036`

## Traversal result
Main performed a recursive deterministic archive-order traversal, not only the package's required 36-file outer inspection.

- immediate outer files: 36
- recursive encountered file records: 162
- textual payloads decoded/read linearly: 159
- ZIP carriers recursively traversed: 3
- textual lines traversed: 16276
- textual bytes traversed: 735925
- unread payloads: 0
- recursive linear-stream SHA-256: `f81b1da9347c05adb9198de4406a57050e2164dac2468ad307589003708263c2`

The 3 archive carriers encountered are the R4.1 outer carrier plus the exact R4.0 parent and R3.1 ancestry occurrences reached through the archive tree. R3.1 is encountered both directly under R4.1 ancestry and inside the exact R4.0 parent. Both occurrences were reread as they occur in the traversal.

Full attachment-runtime ledger:
`RAHL_R4_1_DEEP_LINEAR_READ_LEDGER_20260903.json`
SHA `5c4abf2d730722ab608c88a0cb445ee67ca33cb0126e2b32605d40b2bd260d0e`.

Compact proof ledger:
`RAHL_R4_1_DEEP_LINEAR_READ_PROOF_COMPACT_20260903.json`
SHA `cffcaf58fce6327d972cad933f8215b5eec029e04003490bf3d4627ed9c31550`.

## Independent verification
- R4.1 canonical verifier: PASS, rc=0.
- R4.1 hostile suite: 17/17 rejected, rc=0, zero unexpected passes.
- Embedded R4.0 verifier: PASS, rc=0.
- Embedded R3.1 verifier: PASS, rc=0.
- R3.1 retained assurance ceiling: `STRUCTURE_SOURCE_CLASS_BODY_COVERAGE_AND_INTEGRITY_ONLY`.

The R4.1 hostile suite re-manifests semantic mutations before verification, so semantic rejections are not merely consequences of changed bytes.

## R4.0 -> R4.1 exact package delta
- common logical members: 34
- byte-identical members: 20
- changed members: 14
- added members: 2
- removed members: 0

Changed:
`00_READ_ME_FIRST.md`; `02_ENGINEERING_AUTHORITY_SURFACE.md`; `04_RESEARCH_GOVERNANCE.md`; `05_RESEARCH_MACHINERY_AND_MODES.md`; `11_ACTIVE_SCAR_INDEX.md`; `12_COLD_START_PROTOCOL.md`; `14_CHANGELOG_AND_CULL_LEDGER.md`; `15_CLAIM_CEILING_AND_NONCLAIMS.md`; `MANIFEST_SHA256.json`; `PROMOTION_RECEIPT.md`; `RELEASE_VERIFICATION.md`; `VERIFY_CANONICAL_SOP.py`; `machine/SCARS.json`; `tests/RUN_HOSTILE_TESTS.py`.

Added:
`ancestry/RAHL_ENGINEERING_CANONICAL_SOP_R4_0_2026-09-02.zip`; `machine/BASE_TIER_ENGINEERING_METABOLISM.json`.

## Authority boundary
Deep reading ancestry does not activate ancestry as current process doctrine.

`ANCESTRY_PRESENT != ANCESTRY_CURRENT`
`EVIDENCE_PRESENT != EVIDENCE_PROMOTED`

R4.1 supersedes R4.0 only in the universal process/cold-start scope. Forge/Main project-local obligations remain stronger where more specific.
