# Chain Verification Procedure
_Version: 2026-04-03b_

## Purpose
This file explains how to verify the corpus chain.
Its method role is auditability.
Its control role is to prevent blind trust in a stale, altered, or internally inconsistent package.

## What is included
- `manifest-sha256.txt` records SHA-256 for packaged files other than the manifest file itself
- `92 CORPUS_CHAIN_LEDGER.csv` records package seal order, artifact class, authority scope, file hash, previous entry hash, entry hash, and default read-next file
- `93 CORPUS_MERKLE_ROOT.txt` records a lightweight Merkle-style root across payload leaves

## Verification principle
The archive SHALL NOT assume integrity.
It SHALL verify integrity procedurally.

This package does not depend on magical immutability.
It depends on structural validation, sequence discipline, and honest regeneration after intentional changes.

## Required verification steps
1. Verify file presence
   - confirm expected package files are present
   - confirm no required traversal artifact is missing
   - confirm alphanumeric insertion nodes such as `06A ...` are treated as deliberate sequence members rather than accidental drift

2. Verify file-level SHA-256 values
   - compare packaged files against `manifest-sha256.txt`
   - treat any mismatch as a package-integrity failure until explained

3. Verify chain-ledger continuity
   - confirm each ledger row links correctly to the previous row according to the ledger's entry-hash scheme
   - confirm row order matches the intended package seal order
   - confirm `default_read_next_file` values still reflect the actual traversal design where applicable

4. Verify footer / tail alignment
   - confirm markdown provenance tails or structured tail metadata blocks still agree with the ledger's `default_read_next_file` field
   - confirm `Artifact class` and `Authority scope` remain consistent with the ledger metadata for doctrine-bearing artifacts

5. Verify Merkle-style root consistency
   - confirm the listed payload leaves match the package's stated leaf set and order
   - confirm the published root matches the stated folding convention

## Entry-hash note
A practical entry-hash scheme for this archive is SHA-256 over the pipe-joined fields:
`seq|file_name|artifact_class|authority_scope|file_sha256|prev_entry_sha256|default_read_next_file`

## Merkle-fold note
For this package, the Merkle-style root is computed by:
1. taking SHA-256 **hex digests** of each payload file in the listed leaf order
2. concatenating adjacent hex-digest strings as UTF-8 text
3. hashing that concatenated text with SHA-256 to form the next level
4. duplicating the final item at any odd-width level before folding

This is a deliberate package convention.
It is lightweight and reproducible, but it is not the same as folding raw binary digests.

## Order note
The chain ledger's row order is the **package seal order**.
The footer's default read-next pointer is the **operator/model traversal order**.
These two orders serve different functions and SHALL agree only where design makes them the same by choice.

## Failure handling
If verification fails, the corpus SHALL be treated as altered, incomplete, stale, or structurally inconsistent.

The model SHALL:
- halt blind trust
- enter diagnostic / recovery handling
- identify the break point
- continue only from the nearest still-valid state or after operator confirmation

## Important limit
The Merkle root and chain ledger prove package-internal consistency for the sealed archive version.
They do not prove authenticity outside that context.

---
## Provenance tail
- Artifact ID: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`
- Artifact class: `chain_verification`
- Authority scope: `package integrity verification and footer/ledger alignment`
- Default read-next file: `93 CORPUS_MERKLE_ROOT.txt`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
