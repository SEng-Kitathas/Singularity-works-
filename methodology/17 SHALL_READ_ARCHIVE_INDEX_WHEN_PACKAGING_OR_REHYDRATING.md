# Project Archive Index
_Version: 2026-04-03b_

## Archive classes
### Core control spine
- 00 SHALL_READ_BOOTSTRAP_INIT_PROTOCOL_FIRST.md
- 01 SHALL_READ_BOOTSTRAP_PROMPT_SHIM_NEXT.md
- 02 SHALL_READ_REHYDRATION_NOTE_NEXT.md
- 03 SHALL_READ_MASTER_SOP_NEXT.md
- 04 SHALL_READ_MODEL_ROLE_ROUTING_NEXT.md
- 05 SHALL_READ_PROJECT_START_CHECKLIST_NEXT.md

### Ingress note
The prompt shim is the archive's compressed activation surface.
It is optimized for full-archive drops, fast re-entry, and minimum-waste first turns.
It compresses doctrine into session-entry grammar without replacing the archive's deeper methodology.

### Live state surfaces
- 06 SHALL_INIT_CURRENT_STATE_NEXT.md
- 07 SHALL_INIT_NEXT_STEPS_NEXT.md
- 08 SHALL_INIT_DOCTRINE_SNAPSHOT_NEXT.md
- 09 SHALL_INIT_REVISIT_LEDGER_NEXT.md
- 10 SHALL_INIT_TRACE_MATRIX_NEXT.md
- 10A SHALL_INIT_LIVE_SHADOW_NEXT.md
- 10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md
- 10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md

These files are dual-surface live state instruments.
They preserve operator-readable project memory while enforcing machine-legible distinctions such as mode state, verified/provisional boundaries, revisit obligations, and traceability.

### Research / extraction surfaces
- 11 SHALL_USE_RESEARCH_CROSSWALK_WHEN_NEEDED.md
- 12 SHALL_USE_ZERO_LOSS_EXTRACTION_WHEN_CORPUS_EXISTS.md
- 18 SHALL_USE_MANIFEST_TEMPLATE_WHEN_EXTERNAL_EVIDENCE_EXISTS.csv
- 19 SHALL_USE_OIE_TRIPLES_TEMPLATE_WHEN_EXTRACTION_IS_USEFUL.csv
- 20 SHALL_USE_EXTRACTION_MATRIX_TEMPLATE_WHEN_EVIDENCE_IS_BROAD.csv

These files are dual-surface research instruments.
They preserve inventory, extraction granularity, cross-domain translation, and compression-loss resistance while also constraining the model against prestige import, unread-evidence drift, and premature narrative collapse.

### Pressure / mutation surfaces
- 13 SHALL_DEFINE_EXPERIMENT_SPEC_WHEN_PRESSURE_IS_REQUIRED.md
- 14 SHALL_RECORD_EXPERIMENT_REPORT_AFTER_EXECUTION.md
- 15 SHALL_RECORD_MAINTENANCE_NOTE_WHEN_STATE_MUTATES.md
- 16 SHALL_REVIEW_PROMOTION_BEFORE_LOAD_BEARING_OR_CANON.md

These files are dual-surface pressure and mutation instruments.
They convert testing, reporting, mutation logging, and promotion into auditable gates rather than vibes-driven workflow.


### Footer / tail grammar surface
- 89 SHALL_READ_FOOTER_GRAMMAR_BEFORE_EDITING_TAILS.md

This file defines the archive's per-artifact footer grammar and the distinction between **default read path** and **package chain order**.
It exists so provenance tails remain stable metadata rather than vague ritual.

### Provenance / verification surfaces
- 89 SHALL_READ_FOOTER_GRAMMAR_BEFORE_EDITING_TAILS.md
- 90 SHALL_READ_APPEND_ONLY_PROTOCOL_BEFORE_MUTATING_CORPUS.md
- 91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md
- 92 CORPUS_CHAIN_LEDGER.csv
- 93 CORPUS_MERKLE_ROOT.txt
- manifest-sha256.txt
- PACKAGE_INFO.txt
- PACKAGE_LAYOUT_AND_FORMAT_NOTE.txt
- ro-crate-metadata.json

## Archive design note
This archive is intentionally bifacial.
Some files are sharper and more control-oriented.
Some files are more explanatory and operator-oriented.
That is not drift.
It is design.

The archive should remain intelligible to a human operator while still exerting enough normative pressure to shape model behavior.
The compressed ingress surface exists to reduce ritual overhead, not to reduce rigor.

The package metadata surfaces are intentionally neutral.
They describe the flat package honestly and SHALL NOT imply formal BagIt compliance unless the archive layout is changed to satisfy that standard.

## Normative note
This index SHALL be updated when appended artifacts are added to the sealed corpus or when doctrine-bearing control files are materially rewritten.

---
## Provenance tail
- Artifact ID: `17 SHALL_READ_ARCHIVE_INDEX_WHEN_PACKAGING_OR_REHYDRATING.md`
- Artifact class: `archive_index`
- Authority scope: `package structure and read-map`
- Default read-next file: `18 SHALL_USE_MANIFEST_TEMPLATE_WHEN_EXTERNAL_EVIDENCE_EXISTS.csv`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
