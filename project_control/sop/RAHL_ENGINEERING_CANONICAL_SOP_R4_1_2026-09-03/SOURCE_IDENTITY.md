# RAHL R4.1 Source Identity

This Git tree contains a **Git-safe derivative** of the active R4.1 surface for cross-thread control.

Canonical carrier SHA-256: `af4364fbcf8e5d33aa2ad06e4da9c4669d4be2ffcbc332e416742bec1543f4d2`

Exact active-source bundle SHA-256 before Git-safe transformations: `b28baeec01ac92b10e3c14d53a86d9aa80ec5041805176a0687dc5ee032d0e7a`

`SOURCE_ACTIVE_FILE_HASHES.json` preserves exact source member hashes.
`GIT_SAFE_TRANSFORMS.json` identifies the evidence-only transformations made to avoid publishing machine-local paths and a test fixture key.

The canonical R4.1 verifier/hostile results in Main state apply to the original carrier, not to the transformed Git-safe derivative.

## Derivative verification boundary
The embedded `git_safe_active/MANIFEST_SHA256.json` and `git_safe_active/VERIFY_CANONICAL_SOP.py` are canonical-source reference artifacts. Because declared evidence transformations change derivative bytes, they are **not** a verifier/manifest pair for the Git-safe derivative. Use `project_control/VERIFY_CHECKPOINT.py` for the Git control tree and the original R4.1 carrier for canonical SOP verification.
