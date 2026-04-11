# Universal Lab SOP — Singularity Works / CIL vNext Edition
_Version: 2026-03-29 — Lab-Grade Chimera Edition + Loop+ Meta Control Fold_
_Lineage: UNIVERSAL_LAB_SOP_2026-03-29.md (base) + LOOP_PLUS_AGNOSTIC_GUIDE_META_CONTROL_2026-03-29bc-1.md (folded)_
_Project: Singularity Works / CIL vNext / cil-forge / KarnOS/SYNAPSE_

**NOTE: §12 of this document supersedes the Loop+ definition in the base SOP.
All other sections are identical to UNIVERSAL_LAB_SOP_2026-03-29.md.**

---

For the full base SOP text, load UNIVERSAL_LAB_SOP_2026-03-29.md.
This file records only the delta: the updated §12 with the folded Loop+ guide.

---

## §12. Loop+ (External Research Protocol) — UPDATED WITH META CONTROL LAYER

_Replaces §12 in the base SOP. Governs all external evidence entering the project._

Loop+ is the outer research loop — eight stages executed in order:

1. Primary-source pass (arXiv, PubMed, IEEE, SSRN, Zenodo, OSF Preprints)
2. Discovery expansion (cross-domain structural equivalents)
3. Fast-signal / implementation-clue pass (Ars Technica, HN, Wired)
4. Isomorph-predator pass (hunt structural equivalents in unrelated domains)
5. Native ontology translation (import findings into project language)
6. Control-layer update (what changes in the shadow docs)
7. Experiment pressure (what does this research make us run next?)
8. Recursive replay (do earlier conclusions survive the new evidence?)

**All eight stages are now governed by a stricter meta control spine:**

> **OIE + ELT + Systematic Extraction + DEFNLP-style Post-Processing**

This applies to ALL external evidence entering the project:
- uploaded corpora
- web research
- benchmark packets
- design threads
- standards / docs / news bundles
- any external evidence

---

### The Four Meta Control Layers

**1.1 OIE Layer (Open Information Extraction)**

Use an Open Information Extraction mindset. Maximize fact capture without assuming a narrow schema.

Capture: entities, relations, claims, dependencies, contradictions, process rules, benchmark implications, doctrine changes.

Normalization: (subject, predicate, object, confidence/evidence-strength, source-pointer).

Goal: prevent hidden facts remaining trapped in prose. Make external evidence queryable and recomposable.

**1.2 ELT Layer (Extract → Load → Transform)**

Rule: preserve raw material FIRST, manifest it, hash it where practical, ONLY THEN transform/summarize/reinterpret.

Required outputs (when justified): raw manifest, corpus map, file inventory, checksums/IDs, structured transformed outputs downstream.

Goal: future-proof the corpus. Allow re-interpretation. Prevent irreversible filtering mistakes. This is why we do not summarize before preserving raw structure.

**1.3 Systematic Extraction Layer**

For each meaningful evidence pass:
- predefine variables / seams being extracted
- use standardized extraction matrix
- distinguish: new signal / reinforcement / contradiction / correction / unresolved seam
- make disagreement handling explicit

Matrix fields: source | seam | claim | evidence strength | doctrine effect | status | next action.

Goal: reduce omission, inconsistency, hindsight distortion.

**1.4 DEFNLP-Style Post-Processing Layer**

After primary extraction, run a rescue/cleanup pass looking for:
- orphan signal
- missed acronyms / aliases
- repeated claims under different wording
- hidden dependencies
- baseline mistakes
- category errors
- facts stranded in side notes / implementation notes
- contradictions between local and global summaries

Goal: catch what the first pass missed. Prevent summary loss. Tighten doctrine delta before promotion.

---

### Loop+ Execution Under the Meta Control Layer

**Stage A — Research:** Primary sources + discovery + fast-signal + internal corpus + cross-domain isomorphs.

**Stage B — Extract:** OIE-style fact extraction + ELT-style preservation + systematic extraction matrix.

**Stage C — Rescue:** DEFNLP-style post-processing + duplicate/alias merge + contradiction recovery + baseline correction recovery.

**Stage D — Translate:** Convert outside signal into project-native ontology (or project-neutral operational terms for agnostic use).

**Stage E — Pressure:** Use translated findings to update control docs, change queue order, define experiments, demote stale assumptions, promote load-bearing findings.

**Stage F — Recurse:** Replay earlier seams if the new evidence changes interpretation.

---

### Default Artifact Set (every serious Loop+ pass)

1. manifest
2. OIE/triples table (when useful)
3. standardized extraction matrix
4. post-process synthesis
5. main synthesis / doctrine delta
6. package archive (when corpus is large enough)

---

### Minimal Operating Questions (answer for every Loop+ corpus)

1. What is genuinely new signal?
2. What only reinforces what we already knew?
3. What contradicts or weakens current doctrine?
4. What was a baseline or interpretation mistake?
5. What is still unresolved?
6. What should be promoted into the control layer?
7. What should become experiment pressure?
8. What older conclusion must be replayed recursively?

---

### Anti-Failure Rules

- Do not summarize before preserving raw structure. (ELT over ETL — always)
- Do not treat one source family as sufficient.
- Do not let fast-signal outlets masquerade as primary mechanism proof.
- Do not let extraction stop at the first clean summary.
- Do not leave doctrine-changing facts trapped in prose.
- Do not fail to distinguish evidence from interpretation.
- Do not fail to record what remains unresolved.

---

### Loop+ Short Form

> Research broadly → preserve raw evidence → extract facts openly → standardize claims → rescue orphan signal → translate locally → pressure experiments → replay recursively

Or:

> **OIE + ELT + Systematic Extraction + DEFNLP-style rescue** wrapped around the normal research loop.

---

### Research Rules (unchanged from base SOP)

- Group findings by seam, not by paper
- Prefer representative sources over citation dumps
- Translate findings out of external jargon before promoting
- Record what a finding changes in the build — not just that it exists
- Null research results (seams that found nothing) are recorded

**Source priority:** Internal extraction docs > peer-reviewed primary literature > pre-prints with code > pre-prints without code > review articles > secondary commentary.
