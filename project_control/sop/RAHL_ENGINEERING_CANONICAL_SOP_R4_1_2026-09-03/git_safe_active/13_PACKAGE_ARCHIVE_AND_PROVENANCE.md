# 13 — Package, Archive, and Provenance Discipline

## Canonical package rules
- one unique package identity SHALL map to one exact payload tree;
- a changed payload requires a new identity/version or an explicit append-only overlay/supersession relation;
- `FINAL` in a filename is not evidence;
- logical member identities use `/` canonical separators independent of host OS;
- manifest membership and member hashes are separately checked;
- package verifier SHALL avoid writing into the specimen tree;
- release receipt states an assurance ceiling and nonclaims;
- active universal surfaces are scanned for accidental project/person/runtime current-state contamination.

## Ancestry
Historical/parent artifacts MAY be carried under `ancestry/` for provenance. Their presence does not make their historical status/currentness active doctrine.

## Evidence
Qualification artifacts MAY be carried under `evidence/`. Evidence preserves provenance and supports claims; it does not self-promote into process authority.

## Transport splitting
Transport-specific part-size ceilings are configuration, not universal law. Verify canonical archive first; split after verification; hash/order parts; provide deterministic reassembly and post-reassembly hash verification.

`SAME_LOGICAL_ID != SAME_ARTIFACT_IF_BYTES_DIFFER`
`ANCESTRY_PRESENT != ANCESTRY_CURRENT`
`EVIDENCE_PRESENT != EVIDENCE_PROMOTED`
`FINAL_LABEL != VERIFIED_RELEASE`
