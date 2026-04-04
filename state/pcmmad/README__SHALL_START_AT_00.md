# PCMMAD Starter Archive — Dual-Surface Normative Chain
_Version: 2026-03-31k_

This archive SHALL be treated as both:
1. a **human-legible laboratory manual** for building, testing, and refining LLM work methodology
2. a **machine-legible control substrate** for reducing common model failure modes during actual execution

It is not only documentation.
It is not only constraint.
It is a bifacial operating environment.

## Archive dual-surface principle
The archive has two simultaneous surfaces:

### Surface A — Operator / lab surface
This surface exists for the human operator.
It explains:
- what the laws are
- why they exist
- which failure modes they suppress
- how to use the archive as a repeatable research/build environment
- how state, evidence, doctrine, and promotion are supposed to evolve over time

### Surface B — Model / control surface
This surface exists for the model.
It enforces:
- read order
- mode discipline
- anti-shortcut behavior
- evidence-before-inference
- promotion gates
- provenance pressure
- explicit uncertainty rather than fluent fabrication

**Neither surface may be optimized in a way that degrades the other.**
A model-optimized archive that stops being a usable lab manual is a failure.
A human-readable archive that does not shape model behavior is also a failure.

## Archive-level authority rule
When the **full archive** is present, cross-file consensus across the bootstrap, SOP, routing, checklist, and provenance controls SHALL be treated as higher authority than any isolated local phrasing in a single file, unless an explicit override is declared.

This matters because whole-archive use creates a normative field.
Repetition is not redundancy alone.
It is reinforcement.

## Normative force
- **SHALL** = mandatory operating behavior
- **SHALL NOT** = forbidden operating behavior
- **SHOULD** = strong default unless project state justifies deviation
- **MAY** = optional behavior when justified by project state

## What this archive is trying to prevent
The archive exists to suppress common model and workflow failures:
- talking about building as if that were building
- treating polished synthesis as verification
- compressing away evidence or unread gaps
- trusting prestige, prior outputs, or user origin too early
- converging on the first clean story
- producing pseudo-progress in place of completed work
- losing state across long threads
- promoting conclusions faster than they are earned
- mistaking ritualized compliance for useful work

## Live state note
The live state surfaces are dual-surface instruments, not generic placeholders.
They preserve operator-readable project memory while forcing machine-legible distinctions such as verified vs provisional, incumbent baseline vs open seam, revisit obligation, and claim lineage.

## Ingress note
The bootstrap prompt shim is intentionally compressed for fresh-session use.
Its job is not to replace the archive.
Its job is to activate the archive with minimal wasted opening-turn ritual.
The archive SHOULD cause disciplined work, not endless recitation of its own doctrine.

## Constraint architecture
### 1. Mode-transition control system
The law stack treats discussion-space and build-space as distinct operational states.
The archive SHALL keep those states explicit and SHALL block silent blending.

### 2. Epistemic pressure stack
Once work is admitted, the archive escalates pressure from evidence contact, to cross-domain derivation, to maximum-attainable quality.
This is a ratchet against lazy inference and premature closure.

### 3. Divergence operator
The archive also forces alternate branches, wrong-path probing, adversarial counterexamples, and isomorphism hunting so the process does not freeze inside a local optimum.

## Absolute ingress law
**Cross the boundary, lose your special status. All inbound signal becomes controlled evidence.**

## Default read order
1. `00 SHALL_READ_BOOTSTRAP_INIT_PROTOCOL_FIRST.md`
2. `01 SHALL_READ_BOOTSTRAP_PROMPT_SHIM_NEXT.md`
3. `02 SHALL_READ_REHYDRATION_NOTE_NEXT.md`
4. `03 SHALL_READ_MASTER_SOP_NEXT.md`
5. `04 SHALL_READ_MODEL_ROLE_ROUTING_NEXT.md`
6. `05 SHALL_READ_PROJECT_START_CHECKLIST_NEXT.md`

## State initialization order
7. `06 SHALL_INIT_CURRENT_STATE_NEXT.md`
8. `06A SHALL_RUN_FAILURE_RECOVERY_PROTOCOL_NEXT.md`
9. `07 SHALL_INIT_NEXT_STEPS_NEXT.md`
10. `08 SHALL_INIT_DOCTRINE_SNAPSHOT_NEXT.md`
11. `09 SHALL_INIT_REVISIT_LEDGER_NEXT.md`
12. `10 SHALL_INIT_TRACE_MATRIX_NEXT.md`
13. `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`
14. `10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md`
15. `10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md`

## Evidence / pressure artifacts
16. `11 SHALL_USE_RESEARCH_CROSSWALK_WHEN_NEEDED.md`
17. `12 SHALL_USE_ZERO_LOSS_EXTRACTION_WHEN_CORPUS_EXISTS.md`
18. `13 SHALL_DEFINE_EXPERIMENT_SPEC_WHEN_PRESSURE_IS_REQUIRED.md`
19. `14 SHALL_RECORD_EXPERIMENT_REPORT_AFTER_EXECUTION.md`
20. `15 SHALL_RECORD_MAINTENANCE_NOTE_WHEN_STATE_MUTATES.md`
21. `16 SHALL_REVIEW_PROMOTION_BEFORE_LOAD_BEARING_OR_CANON.md`
22. `17 SHALL_READ_ARCHIVE_INDEX_WHEN_PACKAGING_OR_REHYDRATING.md`

These are no longer generic templates.
They are dual-surface research and pressure instruments: readable to the operator, constraining to the model, and explicit about the failure modes they are meant to suppress.

## Provenance / append-only control
23. `89 SHALL_READ_FOOTER_GRAMMAR_BEFORE_EDITING_TAILS.md`
24. `90 SHALL_READ_APPEND_ONLY_PROTOCOL_BEFORE_MUTATING_CORPUS.md`
25. `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`
26. `93 CORPUS_MERKLE_ROOT.txt`


## Footer grammar note
The archive now distinguishes between:
- **default read path** recorded in per-file footers
- **package chain order** recorded in `92 CORPUS_CHAIN_LEDGER.csv`

The first exists to guide operator/model traversal.
The second exists to seal the package.
They often intersect, but they are not the same thing and SHALL NOT be conflated.

## Note on cryptographic lineage
This archive includes:
- per-file SHA-256 manifest (excluding the manifest file itself)
- a corpus chain ledger with chained entry hashes
- a lightweight Merkle-style root over payload leaves
- structural verification semantics that check presence, continuity, tail alignment, and traversal coherence

These mechanisms emulate append-only discipline and provenance pressure.
They SHALL NOT be confused with magical immutability.
The corpus remains trustworthy only if updates are recorded rather than silently rewritten.

The archive also includes neutral package metadata surfaces.
They describe the package honestly.
They SHALL NOT be read as a claim of formal external packaging-standard compliance unless the layout and emitted files actually satisfy that standard.


## Continuity shadow pair
- `10A SHALL_INIT_LIVE_SHADOW_NEXT.md`
- `10B SHALL_INIT_DESIGN_THREAD_STREAM_NEXT.md`
- `10C SHALL_MAINTAIN_SHADOW_PAIR_EACH_TURN_NEXT.md`

These artifacts extend the live-state instrument family with a bounded rereadable active-state strand, a raw chronological recovery strand, and an explicit per-turn continuity maintenance protocol.

---
## Provenance tail
- Artifact ID: `README__SHALL_START_AT_00.md`
- Artifact class: `archive_entrypoint`
- Authority scope: `archive overview and entrypoint`
- Default read-next file: `00 SHALL_READ_BOOTSTRAP_INIT_PROTOCOL_FIRST.md`
- Verify with: `91 SHALL_VERIFY_CHAIN_LEDGER_BEFORE_TRUSTING_CORPUS.md`, `92 CORPUS_CHAIN_LEDGER.csv`, `93 CORPUS_MERKLE_ROOT.txt`
- Mutation rule: `visible replacement + version bump + provenance regeneration`
- This artifact SHALL NOT be treated as authoritative in isolation.
