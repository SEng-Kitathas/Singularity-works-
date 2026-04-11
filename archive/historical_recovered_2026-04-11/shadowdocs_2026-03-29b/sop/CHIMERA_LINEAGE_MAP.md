# Chimera Lineage Map
_Version: 2026-03-29_

This document records what was taken from each source standard, what was adapted,
and what was created new. Preserving the lineage is part of the audit trail.

---

## Source Standards

### 1. NIH Electronic Lab Notebook (ELN) Standards (2024)

**What we took:**
- Immutable audit trail requirement — no erasure, correction by addendum
- Raw data preservation before any transformation
- Date + author + witness discipline on every significant entry
- Archivability requirement (retrievable, hash-verified format)
- "Record what you actually did, not what the protocol says"

**Where it appears:** §13 (Traceability & Audit Standards), §8 (Experiment Execution), Phase A of extraction protocol, BagIt archive format in Project Index

**What we adapted:** Witness signature → LM session attribution (equivalent function in a solo digital lab context)

---

### 2. OECD/FDA Good Laboratory Practice (21 CFR Part 58)

**What we took:**
- Study director accountability (single point of control per study)
- Independent QA function (internal audit trigger conditions)
- Deviation must be recorded before analysis — not after
- Null results are data — suppression is a violation
- Corrective action protocol (record, correct, retroactive flag)
- All documentation version-controlled, traceable, and archivable

**Where it appears:** R-18 (deviations recorded), R-19 (null results recorded), §19 (Corrective Action Protocol), §20 (Internal Audit Trigger Conditions), Deviation Log template

**What we adapted:** Physical lab QA inspector → internal audit trigger conditions (equivalent function in a digital research context)

---

### 3. ISO/IEC 17025 (Testing and Calibration Laboratories)

**What we took:**
- Traceability chain requirement — every result linked to its source
- Method validation before use (structural distinctness check is the analog)
- Internal audit and corrective action loops
- Workstream separation (scope of accreditation is bounded — evidence from outside scope doesn't carry in)
- Results reported with quantification of variance across runs

**Where it appears:** §13 (Traceability), §15 (Workstream Separation), R-11 (evaluation theater), Experiment Report "confidence" field with variance requirement

**What we adapted:** Physical method validation → structural distinctness check + external baseline requirement (equivalent function for digital experiments)

---

### 4. PRISMA 2020 + Open Science Pre-Registration

**What we took:**
- Confirmatory vs. exploratory declared before data are observed
- HARKing (Hypothesizing After Results are Known) named and governed as a process violation
- Pre-analysis plan locked before execution
- Kill criteria (what would falsify) are mandatory
- Deviations from plan are reported transparently, not adopted silently
- Null results have the same publication/record obligation as positive results
- "A plan, not a prison" — deviations are permitted but must be logged

**Where it appears:** §2 (Two Modes of Every Experiment), R-16, R-17, R-18, R-19, Experiment Pre-Registration Log, Deviation Log, "NULL RESULT RECORDED" field in every experiment report

**What we adapted:** Journal submission pre-registration → internal Pre-Registration Log (equivalent function for single-investigator lab)

---

### 5. MLOps Reproducibility Standards

**What we took:**
- Version everything: code + data + models + config (not just code)
- Every artifact linked to the code + data hash that produced it
- Random seeds set and recorded — non-determinism is a reproducibility failure
- Deterministic pipelines as a hard requirement
- Experiment tracking (MLflow/W&B pattern) → Experiment Pre-Registration + Report + Evaluation Log
- Data lineage (DVC pattern) → Phase A ELT ingest + hash manifest in Project Index
- Results reported with variance across seeds

**Where it appears:** §14 (Version Control Requirements), Experiment Spec "SAMPLE/SEED PLAN" field, Project Index artifact table with hashes, Experiment Report "CONFIDENCE" field requiring seed coverage

**What we adapted:** MLflow/DVC specific tooling → tool-agnostic requirements (the principles, not the specific stack)

---

### 6. Singularity Works / Forge / CIL / TQ2 Research Lineage

**What we took:**
- PROBE → DERIVE → EMBODY → VERIFY → RECURSE as the master loop
- VERIFY as the explicit hard brake between EMBODY and RECURSE
- Shadow-control layer as the project's immune system
- Zero-loss extraction six-phase protocol (OIE + ELT + Systematic + DEFNLP)
- Loop+ external research protocol
- Evaluation theater as a named, governed failure mode
- Substrate claims require empirical foothold
- Workstream separation and separate scorecards
- LM self-evaluation discipline
- All 18 promoted architectural laws (L-01 through L-18)
- All confirmed isomorphisms table
- Anti-drift rules (R-01 through R-10)
- Compaction/context-loss recovery procedure
- Closure standard (five conditions)
- Status vocabulary (Open / Active / Incumbent / Collapsed etc.)

**Where it appears:** Throughout — this is the spine of the SOP

**What we adapted:** Project-specific context moved to §24 (replaceable per project). All universally applicable doctrine preserved in core sections.

---

### 7. General Scientific Lab Notebook Best Practices (Columbia, Purdue, UAH)

**What we took:**
- "Record everything that happens, including deviations, accidents, and errors"
- "Record what you did, not what the manual says"
- Every entry titled descriptively (not "test 3")
- Errors corrected by addendum, not erasure
- Lab notebook is a legal/institutional record — not personal property
- Cross-reference supporting documentation consistently

**Where it appears:** §8 (Experiment Execution), §13 (Traceability), Experiment Report "DEVIATIONS FROM PLAN" field

---

## What Was Created New (Not From Prior Standards)

These elements emerged from the synthesis and from the specific failure modes observed in LM-assisted research:

1. **Evaluation theater as a first-class process failure** — not addressed in any prior standard at this level of specificity. Named, defined, given a governing rule (R-11), an audit trigger (§20), and a required field in every experiment report.

2. **LM self-evaluation discipline** — the requirement that the LM apply the same extraction discipline to its own outputs (R-20, §17). No prior standard covers this because prior standards don't involve LMs.

3. **Structural distinctness check as a mandatory field** — the requirement that experimenters explicitly confirm that conditions are genuinely different before running. This is implied by reproducibility standards but never stated as a required field.

4. **"Nearby variables still open" as a mandatory experiment field** — forces experimenters to explicitly state what the experiment does NOT close, preventing premature closure.

5. **"What recursive replay is triggered by a positive result" and "...by a null result" as separate mandatory fields** — forces explicit bidirectional thinking about how results propagate backward through earlier seams.

6. **Process debt tracking** — the Maintenance Note's explicit "Active Process Debt" section with target horizons. Standard process debt tracking exists in DevOps but not in lab notebooks or research SOPs.

---

## What Was Deliberately Excluded

- Physical sample management (GLP) — not applicable to digital research
- GxP compliance specifics (FDA approval pathways) — too domain-specific
- Statistical power analysis requirements (PRISMA clinical trial standards) — applicable but beyond current scope; flag for future addition
- Peer review and publication requirements (PRISMA) — not applicable to internal lab
- Specific tooling mandates (MLflow, DVC, W&B) — principles extracted, tools left to project choice
