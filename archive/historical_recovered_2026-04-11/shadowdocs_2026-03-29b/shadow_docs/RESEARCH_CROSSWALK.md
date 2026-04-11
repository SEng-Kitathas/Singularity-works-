# Research Crosswalk — Singularity Works / CIL vNext
_Version: 2026-03-29 (initial backfill from session MHT)_
_SOP: UNIVERSAL_LAB_SOP_2026-03-29.md §12_

**Update rule:** Add new seam entries; never replace existing. Append under each seam.

---

```
SEAM ID:                   RC-001
SEAM NAME:                 Semantic Compression via Multimodal Centroid
WORKSTREAM:                CIL Memory / CRHQ Quantization
REPRESENTATIVE SOURCES:
  - arXiv 2509.24431 — "Semantic Compression via Multimodal Representation Learning"
CORE TAKEAWAY:
  When modality gap is sufficiently reduced via high contrastive temperature,
  centroid becomes a faithful representation of the semantic concept.
  N embeddings can be replaced by 1 centroid + residuals.
  Temperature parameter controls centroid tightness.
PROJECT-NATIVE TRANSLATION:
  Temperature ↔ distortion_budget: same single degree of freedom.
  High temperature = reduced modality gap = tight centroid = low distortion budget.
  CRHQ centrality-guided precision allocation maps onto per-family temperature calibration.
  smem_get_priors() now computes calibrated distortion_budget per radical family
  using support density and confidence spread — this IS the temperature parameter.
ARCHITECTURE / PROCESS IMPLICATION:
  distortion_budget becomes a computed field in smem_get_priors(), not a hand-tuned constant.
  Extension: self-calibrating codebook training in semantic_vq.rs by adapting per-family temperature.
EVIDENCE STRENGTH:          HIGH (proven in arXiv paper)
ISOMORPHS FOUND:
  - Temperature ↔ Distortion budget (confirmed, implemented)
  - High support density → tight centroid → lower budget (CIL-015 effective_distortion_budget())
RESIDUAL UNCERTAINTY:       Self-calibrating codebook training not yet implemented in semantic_vq.rs
NEXT EXPERIMENT PRESSURE:   EXP-20260329-001 — does calibrated budget actually change hit rate?
```

---

```
SEAM ID:                   RC-002
SEAM NAME:                 Zep/Graphiti Bi-Temporal Memory Model
WORKSTREAM:                CIL Memory (all layers)
REPRESENTATIVE SOURCES:
  - arXiv 2501.13956 — "Zep: A Temporal Knowledge Graph Architecture for Agent Memory"
CORE TAKEAWAY:
  Four-field bi-temporal model: t_created/t_expired ∈ T' (transactional) +
  valid_from/valid_until ∈ T (event timeline).
  Contradiction resolution: set valid_until of old belief = valid_from of contradicting evidence.
  Zep outperforms MemGPT on LongMemEval by 18.5% with 90% lower latency.
PROJECT-NATIVE TRANSLATION:
  CIL adopts the 4-field model directly: BiTemporal struct in both Python (forge_context.py)
  and Rust (cil.rs). ContradictionGraph.contradict() implements Zep invalidation mechanism.
  CIL is architecturally ahead of Zep: epistemic state vector [U/I/P/T_edge] vs. just temporal range.
ARCHITECTURE / PROCESS IMPLICATION:
  CIL-014 closed. BiTemporal struct is the canonical timestamp envelope for all memory objects.
  Prior tri-temporal design (superseded_at field) is retired — Zep 4-field is cleaner.
EVIDENCE STRENGTH:          HIGH (peer reviewed, benchmarked)
ISOMORPHS FOUND:
  - Zep t_valid/t_invalid ↔ CIL valid_from/valid_until (adopted directly)
  - Graphiti episodic subgraph ↔ EPMEM layer
RESIDUAL UNCERTAINTY:       Zep uses LLM for contradiction detection; CIL uses consolidation gates + heuristics
NEXT EXPERIMENT PRESSURE:   E2E test: does EPMEM/SMEM properly accumulate over multiple assault sessions?
```

---

```
SEAM ID:                   RC-003
SEAM NAME:                 IRIS — LLM-Assisted Static Analysis
WORKSTREAM:                Forge / IRIS Escalation
REPRESENTATIVE SOURCES:
  - arXiv 2405.17238 — "IRIS: LLM-Assisted Static Analysis for Detecting Security Vulnerabilities"
CORE TAKEAWAY:
  IRIS = LLM infers taint specs → formal taint engine (CodeQL) → LLM false positive filtering.
  On CWE-Bench-Java: CodeQL finds 27/120; IRIS+GPT-4 finds 55/120 (+103.7%).
  IRIS also finds 4 previously unknown vulnerabilities.
PROJECT-NATIVE TRANSLATION:
  Forge = heuristic extraction → pattern gate → LLM validation (dual architecture to IRIS).
  When forge IR confidence == "low" AND no static high/critical findings:
  escalate to IRIS-mode — REASONER infers source/sink specs as DynamicCapsule.
  iris_escalate() and system_iris_escalation() implement this path.
ARCHITECTURE / PROCESS IMPLICATION:
  IRIS escalation is wired and best-effort. Not yet tested with live LM.
  The L2→L3 bridge: static gate fails → IRIS escalation → synthesis → dialectic council validation.
EVIDENCE STRENGTH:          HIGH (peer reviewed, reproducible benchmark)
ISOMORPHS FOUND:
  - IRIS (LLM→formal→LLM) ↔ Forge (heuristic→gate→LLM) — dual convergence loop
  - IRIS source/sink inference ↔ Forge capability inference
RESIDUAL UNCERTAINTY:       IRIS tests on Java; forge is polyglot. Taint spec inference quality
                            varies by language. REASONER model (35B) not tested for taint quality.
NEXT EXPERIMENT PRESSURE:   Test iris_escalate() on intentionally ambiguous/minified code
```

---

```
SEAM ID:                   RC-004
SEAM NAME:                 ECS Archetype Model for Forge Runtime
WORKSTREAM:                cil-forge Rust
REPRESENTATIVE SOURCES:
  - hecs crate documentation; Entity Component System literature; Bevy ECS analysis
CORE TAKEAWAY:
  Archetype ECS: entities with same component set stored contiguously in memory.
  Gate runner iterating over (SemanticIR, GenomeCapsuleBinding) stays hot in L1 cache.
  hecs confirmed over Bevy (no render stack) and shipyard (archetype model preferred).
PROJECT-NATIVE TRANSLATION:
  cil-forge uses hecs archetype ECS. ArtifactSource → DetectedLanguage → UniversalSemanticIR
  → GenomeCapsuleBinding → GateEvaluation → AssuranceSeal: each is a component.
  Systems are stateless functions over component queries. Gate runner is parallel-safe
  because gates don't share write state per artifact.
ARCHITECTURE / PROCESS IMPLICATION:
  cil-forge scaffold complete. Systems are functional stubs.
  Migration path: Python forge as oracle during Rust system implementation.
EVIDENCE STRENGTH:          HIGH (established pattern; Unity DOTS proof of concept at scale)
ISOMORPHS FOUND:
  - ECS archetype ↔ Forge gate pipeline (SoA layout, parallel systems)
  - SoA memory layout ↔ cache-friendly gate runner
RESIDUAL UNCERTAINTY:       Parallel gate runner (rayon) not yet implemented — sequential now.
NEXT EXPERIMENT PRESSURE:   Benchmark: Rust gate runner vs Python oracle on same content samples
```

---

```
SEAM ID:                   RC-005
SEAM NAME:                 Temporal Knowledge Graph Contradiction Resolution
WORKSTREAM:                CIL Memory (Contradiction Graph)
REPRESENTATIVE SOURCES:
  - arXiv 2509.15464 — "Temporal Reasoning over Evolving Knowledge Graphs"
  - arXiv 2502.05665 — "Graph-based Agent Memory: Taxonomy, Techniques, and Applications"
CORE TAKEAWAY:
  EvoKG: confidence-based contradiction resolution + temporal trend tracking.
  Bi-temporal model tracks when facts hold vs. when they were recorded (Zep aligned).
  Graph-based agent memory is the 2025-2026 frontier: topological model of experience.
PROJECT-NATIVE TRANSLATION:
  ContradictionGraph in cil.rs is the CIL implementation of temporal KG contradiction resolution.
  EpistemicStatus progression (Hypothesis → ProvisionalSemantic → StableSemantic) maps onto
  EvoKG's confidence-based promotion.
  active_roots() returns current worldview — nodes with no incoming contradiction edges.
ARCHITECTURE / PROCESS IMPLICATION:
  CIL-015 closed. Graph is operational in Rust (unit tested).
  Python side uses list-based ContradictionBlock list (simpler, adequate for forge-scale).
EVIDENCE STRENGTH:          HIGH (multiple converging papers)
ISOMORPHS FOUND:
  - Zep t_valid/t_invalid ↔ ContradictionGraph Zep mechanism
  - EvoKG confidence resolution ↔ EpistemicStatus support thresholds
RESIDUAL UNCERTAINTY:       Python ContradictionGraph is a list, not a proper graph — 
                            no chain traversal. Rust graph not yet integrated into Python forge.
NEXT EXPERIMENT PRESSURE:   Test contradiction detection in SMEM after 3+ forge sessions
```

---

```
SEAM ID:                   RC-006
SEAM NAME:                 MemVerse / Agent Memory Architecture Landscape
WORKSTREAM:                CIL Memory (architecture positioning)
REPRESENTATIVE SOURCES:
  - MemVerse (arXiv 2512.03627) — multimodal memory for lifelong learning agents
  - Hindsight (arXiv 2512.12818) — subjective belief + behavioral profile tracking
  - Graph-based Agent Memory survey (arXiv 2602.05665)
CORE TAKEAWAY:
  Two dominant paradigms: parameter-embedded memory (rigid, expensive to update) vs.
  external static storage (RAG-style, lacks abstraction).
  MemVerse: short-term + long-term knowledge graph + parametric memory (three-tier).
  CIL's four-layer stack (SBUF/EPMEM/SMEM/Contradiction) is architecturally superior
  to both dominant paradigms: dynamic, structured, contradiction-aware, epistemically governed.
PROJECT-NATIVE TRANSLATION:
  CIL is ahead of MemVerse: CIL adds epistemic state machine + contradiction graph.
  CIL is ahead of Hindsight: CIL has bi-temporal indexing + distortion budget calibration.
  Gap vs. MemVerse: CIL doesn't yet track subjective beliefs / behavioral profiles —
  that's DEJI persona territory, not forge territory.
ARCHITECTURE / PROCESS IMPLICATION:
  No architecture change required. Positioning confirmed.
EVIDENCE STRENGTH:          HIGH (survey + primary papers)
ISOMORPHS FOUND:
  - CLS hippocampus ↔ SBUF (fast-write, cleared after consolidation) — confirmed in literature
  - Episodic/semantic memory split ↔ EPMEM/SMEM split
RESIDUAL UNCERTAINTY:       CIL's advantage over MemVerse is theoretical until E2E tested.
NEXT EXPERIMENT PRESSURE:   Run E2E over 10+ sessions and compare SMEM state quality
```
