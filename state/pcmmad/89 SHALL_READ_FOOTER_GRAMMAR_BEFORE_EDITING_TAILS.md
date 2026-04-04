# Footer Grammar Protocol
_Version: 2026-04-03b_

## Purpose
This file defines the archive's footer grammar.
Its operator role is to keep tail metadata legible and auditable.
Its control role is to stop per-file provenance tails from drifting into vague decoration or contradictory read-order claims.

## Why this exists
A footer is not ornamental.
In this archive a footer is the smallest repeatable unit of provenance pressure.
It reminds both operator and model:
- what this artifact is
- how much authority it actually has
- what file it points to by default
- where to verify package integrity
- what mutation discipline governs edits to it

Without a grammar, tails become soft ritual.
With a grammar, tails become compact control metadata.

## Footer grammar
Markdown artifacts SHALL end with a structured footer containing:
1. **Artifact ID** — exact file name
2. **Artifact class** — the file's functional role in the archive
3. **Authority scope** — what the file is allowed to govern
4. **Default read-next file** — the next file in the human/model read path, not the package seal order
5. **Verify with** — the integrity artifacts used to confirm package coherence
6. **Mutation rule** — how changes to the artifact are supposed to be recorded
7. **Isolation warning** — reminder that no single file outranks the archive-wide consensus surface

CSV template artifacts SHALL express the same ideas as trailing comment rows.
Plain-text package artifacts MAY express the same ideas as structured metadata lines when markdown footers would be inappropriate.

## Critical distinction: read path vs package chain
The archive has two different orders:

### 1. Default read path
This is the guidance surface for a human operator or model traversing the archive.
It is encoded in per-file footers as **Default read-next file**.

### 2. Package chain order
This is the order used by the chain ledger to seal the package.
It is recorded in `92 CORPUS_CHAIN_LEDGER.csv` through `seq`, `prev_entry_sha256`, and `entry_sha256`.

These orders SHALL NOT be conflated.

Read-order filenames MAY use numeric or alphanumeric insertion points when append-only growth needs a mid-chain control artifact. Example: `06A ...` between `06 ...` and `07 ...`.
A file can point to one document as the next thing to read while still appearing elsewhere in the package seal order.

## Tail-edit discipline
When a footer is changed:
1. update the file footer itself
2. update the `default_read_next_file` field in `92 CORPUS_CHAIN_LEDGER.csv`
3. verify that `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md` still describes the actual verification logic
4. regenerate `manifest-sha256.txt`
5. regenerate `92 CORPUS_CHAIN_LEDGER.csv`
6. regenerate `93 CORPUS_MERKLE_ROOT.txt`
7. bump the package version if the change is doctrine-bearing or package-bearing

## SHALL NOT rules
- SHALL NOT use the footer as decorative boilerplate only
- SHALL NOT let footer read-next pointers contradict the chain ledger's default read-next field
- SHALL NOT let package seal order masquerade as operator read order
- SHALL NOT overstate authority scope
- SHALL NOT treat a footer as permission to ignore the rest of the archive

## Method note
A good footer is small, explicit, and boring.
That is a feature.
The archive's goal is not poetic tails.
It is stable, low-ambiguity, audit-friendly metadata pressure.

---
## Provenance tail
- Artifact ID: `89 SHALL_READ_FOOTER_GRAMMAR_BEFORE_EDITING_TAILS.md`
- Artifact class: `footer_grammar`
- Authority scope: `footer semantics, read-next meaning, and tail-edit rules`
- Default read-next file: `90 SHALL_READ_APPEND_ONLY_PROTOCOL_BEFORE_MUTATING_CORPUS.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
