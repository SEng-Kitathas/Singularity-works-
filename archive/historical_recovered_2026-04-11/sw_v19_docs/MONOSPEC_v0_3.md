# Singularity Works — MONOSPEC v0.3

Last updated: 2026-03-27T12:40:00Z

## Purpose

This document consolidates the current Singularity Works build-grade architecture into a single master specification.

It unifies:
- forge architecture
- recovery layer
- pattern IR verification hooks
- QA gate packs
- misuse gates
- simplification/conformance
- evidence ledger
- lifecycle traceability + assurance
- runtime orchestration flow
- console HUD / telemetry

## Consolidation note

This is a merged operational spec, intended to replace fragmented drafting as the primary implementation reference.


---

# Included from `SINGULARITY_WORKS_RECOVERY_LAYER_SPEC.md`

# Singularity Works — Recovery Layer Specification

Last updated: 2026-03-27T12:05:00Z

## Purpose

The Recovery Layer reconstructs hidden structure from heterogeneous artifacts so the forge can operate on **recovered structure**, not only raw text or raw code.

Recovered structure includes:
- grammars
- protocol/state machines
- invariants
- requirement/code trace links
- exemplar families
- anti-pattern candidates
- monitorable claims

## Position in the architecture

The Recovery Layer sits between:
- **Formal Family Layer**
- **Exemplar Layer**
- **Retrieval Policy Layer**
- **Embodiment Layer**
- **QA / Evidence Layer**

It is the bridge that converts observations into structured, machine-usable artifacts.

## Inputs

1. Source code
2. Parser implementations
3. Requirements/spec prose
4. Execution traces
5. Validator results
6. Repository exemplars
7. Existing Pattern IR entries
8. Existing evidence ledger entries

## Outputs

1. `RecoveredGrammar`
2. `RecoveredProtocol`
3. `RecoveredInvariantSet`
4. `RecoveredTraceLink`
5. `RecoveredExemplarBundle`
6. `RecoveredMonitorSeed`
7. `RecoveryConfidenceReport`

## Core submodules

### A. Grammar recovery
Sources:
- parser code
- input samples
- traces

Methods:
- symbolic grammar extraction
- dynamic grammar inference
- grammar approximation from ad hoc parsers

Outputs:
- grammar rules
- parser coverage notes
- confidence score
- unsupported-path notes

### B. Protocol/state recovery
Sources:
- traces
- code
- message sequences
- validator failures

Methods:
- state inference
- protocol graph extraction
- adversarial counterexample refinement

Outputs:
- states
- transitions
- guards
- forbidden states
- confidence/probability
- ambiguity notes

### C. Spec / traceability recovery
Sources:
- requirements/spec prose
- code
- design artifacts
- tests/validators

Methods:
- trace-link recovery
- structure-aware alignment
- requirement normalization

Outputs:
- requirement ids
- linked code/artifacts
- confidence
- unresolved semantic gap notes

### D. Invariant recovery
Sources:
- code
- traces
- validators
- exemplars

Methods:
- value invariant mining
- scenario/state constraint mining
- anti-pattern contrast mining

Outputs:
- invariants
- scope
- supporting evidence
- residual obligations

### E. Monitor seed recovery
Sources:
- structured requirements
- protocol/state models
- invariants

Methods:
- requirement normalization
- monitor-template mapping
- temporal/predicate extraction

Outputs:
- monitor seeds
- required signals
- monitorability notes

## Required metadata

Every recovered artifact must carry:
- `artifact_id`
- `source_refs`
- `recovery_method`
- `confidence`
- `evidence_refs`
- `residual_uncertainty`
- `last_updated`
- `conflicts_with`
- `supports_requirements`
- `supports_radicals`

## Confidence discipline

Recovery is never “truth by default”.

Confidence levels:
- `high`
- `moderate`
- `low`
- `speculative`

Each recovered artifact must also state:
- what evidence supports it
- what evidence is missing
- what would falsify it

## Failure modes

1. Overfit recovery
2. False trace links
3. Spurious states/transitions
4. Grammar under-approximation
5. Grammar over-approximation
6. Invariant hallucination
7. Ambiguous monitor seeds

## Interaction with other layers

### To Pattern IR
Recovered structure can:
- instantiate new families
- enrich existing families
- add verification hooks
- create anti-pattern signatures

### To Retrieval
Recovered structure should constrain retrieval:
- retrieve by radical/family/state relevance
- retrieve by requirement linkage
- retrieve by unresolved obligations

### To Embodiment
Recovered structure should inform emission:
- parser emitters use recovered grammar
- protocol emitters use recovered states/guards
- monitors use recovered requirement seeds

### To QA
Recovered structure becomes:
- static assumptions
- runtime monitors
- misuse constraints
- simplification constraints

## Build v1 scope

Implement v1 in this order:
1. requirement/code trace-link objects
2. grammar recovery interface
3. protocol/state recovery interface
4. invariant recovery interface
5. monitor seed objects
6. confidence/evidence reporting

## Non-goals for v1

- full theorem proving
- perfect semantic recovery
- universal parser recovery across every language
- automated acceptance of low-confidence recovered structure

## Core law

Do not merely mine examples.
Recover hidden structure, attach confidence and evidence, and pass only the recoverable, auditable structure forward.


---

# Included from `SINGULARITY_WORKS_QA_GATE_PACKS_SPEC.md`

# Singularity Works — QA Gate Pack Specification

Last updated: 2026-03-27T12:05:00Z

## Purpose

Turn the evaluation framework into concrete gate packs that can be run consistently across code generation, refactoring, recovery, and embodiment.

## Gate families

### 1. Static gates
For:
- contracts
- invariants
- null/bounds/resource classes
- deterministic representation policy

Examples:
- precondition gate
- postcondition gate
- forbidden-state construction gate
- representation-consistency gate

### 2. Structural gates
For:
- module integrity
- lifecycle/ownership clarity
- pattern conformance
- interface sanity

Examples:
- cohesion/coupling gate
- ownership/lifecycle gate
- radical-family conformance gate
- anti-pattern gate

### 3. Dynamic gates
For:
- property checks
- metamorphic checks
- mutation pressure
- differential sibling analysis

Examples:
- property-based gate
- metamorphic gate
- mutation-survival gate
- sibling-divergence gate

### 4. Runtime gates
For:
- monitor execution
- protocol conformance
- temporal drift
- architecture assertions

Examples:
- runtime monitor gate
- architectural runtime query gate
- resource drift gate
- protocol violation gate

### 5. Conformance/simplification gates
For:
- misuse rejection
- architecture conformance
- unnecessary complexity
- semantic-preserving simplification

Examples:
- API misuse gate
- protocol misuse gate
- architecture constraint gate
- simplification recommendation gate

## Gate result contract

Each gate returns:
- `gate_id`
- `family`
- `status`
- `discharged_claims`
- `residual_obligations`
- `findings`
- `evidence_refs`
- `severity_rollup`

## Build pass order

1. Static
2. Structural
3. Dynamic
4. Runtime
5. Conformance/simplification
6. Assurance rollup

## Status semantics

- `pass`: claim discharged for scope
- `warn`: concern present, but not fatal
- `fail`: claim falsified or violated
- `residual`: insufficient evidence to discharge

## Residual-risk discipline

Residual is not “ignore later.”
Residual means:
- tracked
- linked
- surfaced in HUD
- attached to assurance rollup

## Required first build gate packs

### Pack A — Core integrity
- null/bounds/resource
- representation policy
- forbidden-state construction

### Pack B — Pattern/conformance
- family fit
- anti-pattern hits
- misuse detection
- ownership/lifecycle

### Pack C — Dynamic quality
- property-based
- metamorphic
- mutation-assisted
- sibling differential

### Pack D — Runtime evidence
- requirement-derived monitors
- protocol monitors
- architectural runtime checks

### Pack E — Complexity/conformance
- smell signal
- simplification proposal
- retained-complexity justification

## Core law

A candidate is not “good” because it compiles.
A candidate is better only insofar as claims about it are discharged, monitored, or explicitly left residual with justification.


---

# Included from `SINGULARITY_WORKS_MISUSE_GATE_SPEC.md`

# Singularity Works — Misuse Gate Specification

Last updated: 2026-03-27T12:05:00Z

## Purpose

Detect incorrect usage of APIs, protocols, resources, state machines, and pattern families.

## Why this exists

Passing tests is not enough.
Many failures come from:
- wrong call order
- missing preconditions
- missing cleanup
- invalid state transition
- security API misuse
- protocol misuse
- pattern misuse

## Inputs

- source/IR
- protocol/state model
- family/radical constraints
- cross-project exemplars
- anti-pattern registry

## Detection model

Misuse detection must not rely on frequency alone.

Use:
1. graph-shaped usage representation
2. state/protocol constraints
3. cross-project exemplars
4. precondition/call-order constraints
5. security-sensitive misuse classes

## Misuse classes

### API misuse
- wrong order
- missing precondition
- missing post action
- incorrect exception/error handling
- incompatible parameter/state usage

### Protocol misuse
- invalid transition
- skipped handshake
- illegal retry/replay
- terminal-state re-entry
- missing acknowledgement/finalization

### Resource misuse
- acquire without release
- use after close
- duplicated release
- partial cleanup

### Security misuse
- unsafe defaults
- key/nonce misuse
- insecure verification usage
- disabled validation path

### Pattern misuse
- inappropriate family selection
- violating required invariants
- misapplied concurrency/control pattern
- wrong abstraction depth

## Outputs

- misuse findings
- severity
- required fixes
- candidate exemplars
- linked constraints
- linked residual risk

## Required behavior

If misuse is detected, the gate should:
1. identify the violated constraint
2. identify the state/context
3. show the nearest known-good exemplar
4. propose the minimally invasive compliant correction

## Core law

Do not only ask whether the code passes.
Ask whether it uses the right thing in the right order under the right preconditions.


---

# Included from `SINGULARITY_WORKS_SIMPLIFICATION_CONFORMANCE_SPEC.md`

# Singularity Works — Simplification & Conformance Specification

Last updated: 2026-03-27T12:05:00Z

## Purpose

Apply pressure toward lower structural burden without sacrificing invariants, determinism, stability, or substrate fit.

## Goal

Not “shortest code at all costs.”
Not “prettiest refactor.”
The goal is:

> the least-complex representation that preserves required behavior and required constraints

## Inputs

- candidate artifact
- family/radical expectations
- invariants
- cost model
- smell signals
- equivalence hints
- regression/differential evidence

## Simplification classes

1. structural simplification
2. control-flow simplification
3. state-model simplification
4. duplicate/isomorphic collapse
5. resource-lifecycle simplification
6. abstraction-level correction

## Conformance classes

1. architecture conformance
2. family conformance
3. protocol conformance
4. requirement conformance
5. retained-complexity justification

## Required outputs

- candidate simpler form
- equivalence status
- expected gains
- retained-complexity reasons
- residual uncertainty

## Decision rule

Prefer the lower-burden form when:
- semantics are preserved
- invariants are preserved
- determinism is preserved
- substrate fit is not degraded
- QA evidence does not weaken

If complexity remains, record:
- why it remains
- what evidence justified retention
- what future trigger would re-open simplification

## Core law

Complexity is guilty until proven necessary.
If complexity survives review, it must do so with an argument.


---

# Included from `SINGULARITY_WORKS_ENFORCEMENT_VERIFICATION_LAYER.md`

# Singularity Works — Enforcement & Verification Layer (Agnostic)

Last updated: 2026-03-27T10:05:00Z

## Purpose

Turn the Universal Code Evaluation Framework into a machine-usable QA spine for the forge.

This layer is not a separate afterthought. It is the mechanism that:
- discharges what can be proven
- stress-tests what cannot
- monitors what remains uncertain
- records residual risk and evidence

## Design principle

Every meaningful claim about a candidate build should end in one of four buckets:

1. **Statically discharged**
2. **Dynamically stressed**
3. **Runtime monitored**
4. **Residual / unresolved**

## Gate families

### A. Static gates
Best for:
- Layer 0 (atomic integrity)
- Layer 5 (determinism/numerical integrity)
- Layer 6 (constraints/invariants)

Mechanisms:
- contract checks (pre/post/invariant)
- abstract-interpretation-style fact inference
- null/bounds/overflow/resource checks
- assume/guarantee summaries
- protocol/state precondition checks
- forbidden-state construction checks

Outputs:
- discharged facts
- residual obligations
- summary facts for callers/components

### B. Structural / composition gates
Best for:
- Layer 1 (structural integrity)
- Layer 2 (pattern usage soundness)
- Layer 7 (interaction/composition)
- Layer 9 (isomorphism/redundancy)

Mechanisms:
- interface/ownership/lifecycle checks
- pattern-family conformance
- anti-pattern detection
- compatibility/conflict checks
- canonicalization / equivalence candidates
- protocol-state conformance
- malformed-pattern scans

Outputs:
- structure verdicts
- composition conflicts
- redundancy candidates
- protocol/state mismatches

### C. Dynamic adversarial gates
Best for:
- Layer 0 edge behavior
- Layer 5/6 when static discharge is incomplete
- Layer 7/10 behavior under stress

Mechanisms:
- property-based tests
- metamorphic relations
- differential tests
- property-based mutation testing
- adversarial spec mining / counterexample search
- grammar/state-guided fuzzing

Outputs:
- violated properties
- surviving mutants
- metamorphic breaches
- counterexample traces
- coverage over state/property space

### D. Runtime / architectural gates
Best for:
- Layer 3 (architecture)
- Layer 10 (temporal/stability)
- Layer 11 (socio-technical traceability)
- selected Layer 7 properties in deployment

Mechanisms:
- runtime verification monitors
- architectural runtime queries
- temporal/protocol monitors
- drift/latency/resource watchpoints
- evidence capture and ledgering
- branch comparison / field feedback later

Outputs:
- runtime violations
- temporal drift signals
- architecture-level hypothesis confirmation/refutation
- evidence ledger entries

## Mapping from evaluation layers to gate families

### Layer 0 — Atomic / Implementation Integrity
Primary gates:
- static contracts
- abstract interpretation
- dynamic edge/property tests

### Layer 1 — Structural / Modular Integrity
Primary gates:
- structural checks
- interface/lifecycle/ownership checks

### Layer 2 — Pattern & Usage Soundness
Primary gates:
- family conformance
- anti-pattern scans
- exemplar comparison

### Layer 3 — Architectural Integrity
Primary gates:
- architecture queries
- runtime architectural verification
- dependency/failure-isolation checks

### Layer 4 — Performance & Substrate Alignment
Primary gates:
- cost/perf profilers
- algorithmic smell checks
- substrate mismatch heuristics
- benchmark hooks

### Layer 5 — Determinism & Numerical Integrity
Primary gates:
- repeatability checks
- numerical invariant checks
- representation policy checks

### Layer 6 — Constraint & Invariant Enforcement
Primary gates:
- contract checks
- invariant mining/verification
- invalid-state construction refusal

### Layer 7 — Interaction & Composition Integrity
Primary gates:
- compatibility/conflict checks
- state/protocol interaction monitors
- adversarial composition tests

### Layer 8 — Cost Model
Primary gates:
- measured runtime/memory/branch/caching evidence
- non-linear cost reporting
- residual-cost notes

### Layer 9 — Isomorphism & Redundancy Detection
Primary gates:
- canonicalization
- equivalence candidates
- minimal-description-length ranking
- e-graph sidecar later

### Layer 10 — Temporal & Stability Analysis
Primary gates:
- soak/repeat tests
- drift monitors
- recovery-path checks
- runtime monitors

### Layer 11 — Socio-Technical / Ownership Layer
Primary gates:
- traceability checks
- evidence completeness
- ownership metadata
- single-point-of-failure reporting

## Residual-risk discipline

A candidate should never simply “pass.”

It should produce an evidence object like:

- static_passes
- structural_passes
- dynamic_passes
- runtime_monitor_plan
- unresolved_obligations
- residual_risk
- evidence_refs

## Relation to Pattern IR

Pattern IR should carry verification hooks:
- required contracts
- state/protocol constraints
- anti-pattern signatures
- property templates
- metamorphic relations
- runtime monitor templates
- cost expectations
- equivalence hints

That way evaluation becomes automatic:
- pattern selected
- enforcement hooks loaded
- candidate emitted
- gates run
- evidence recorded

## Immediate implementation target for Singularity Works

1. Add an **evidence ledger schema**
2. Add **gate result objects**
3. Add **pattern-linked verification hooks**
4. Add a **gate orchestrator**
5. Add initial gate packs:
   - static contract pack
   - structural pack
   - property/metamorphic pack
   - runtime/architecture pack

## Clean summary

The forge should not ask only:
> what pattern should I use?

It should also ask:
> what evidence discharges the claims this pattern is making?


---

# Included from `SINGULARITY_WORKS_CONSOLE_HUD_MODULE.md`

# Singularity Works — Console HUD / Telemetry Module

Last updated: 2026-03-27T11:50:00Z

## Goal

Provide a live operator-facing HUD for Windows with:
- minimal dependencies
- robust rendering
- forge/QA/evidence visibility
- graceful fallback when advanced console features are unavailable

## Recommended implementation path

Primary path:
- Python stdlib
- Win32 `SetConsoleMode` via `ctypes`
- VT/ANSI escape sequences for layout, cursor control, color, and alternate screen

Fallback path:
- plain text periodic redraw without alternate-screen features

## Why this path

It keeps dependency count low while still allowing:
- full-screen dashboard mode
- color status bands
- progress bars
- event log panes
- hidden cursor / controlled repaint
- title updates
- screen clearing and panel layout

## HUD information model

### Top bar
- app name
- mode (run / dialectic / doctor / genome / qa)
- provider/model
- active project tag
- session id
- uptime

### Left column
- current phase
- current requirement / claim
- current pattern family / radical
- current validator / monitor
- current branch / context id

### Center
- progress bars
- task counts
- pass / warn / fail / residual counts
- recent latency / throughput
- token/request stats if available
- queue depth / pending work items

### Right column
- residual risks
- active warnings
- recent anti-pattern hits
- divergence / misuse / conformance flags
- current evidence/assurance rollup summary

### Bottom pane
- rolling event log
- latest checkpoints
- latest failures / recoveries
- latest monitor violations
- latest simplification / refactoring notes

## HUD design principles

1. **Readable first**
   ASCII-safe layout by default.
2. **Color is secondary, not mandatory**
   Colors reinforce status, but meaning must still be visible in monochrome.
3. **Operator should never lose the system state**
   Alternate screen is preferred, but key summaries should be recoverable in logs.
4. **No dependency trap**
   Start stdlib-only; optional richer frontend can come later.
5. **Evidence-aware**
   HUD is not only a progress toy. It should surface QA/evidence/residual state.

## Minimum feature set for build v1

- VT enablement on Windows
- alternate-screen dashboard mode
- terminal resize awareness
- sectioned ASCII layout
- color status labels
- progress bars
- event log tail
- snapshot-based rendering API
- plain-text fallback mode


---

# Included from `SINGULARITY_WORKS_PATTERN_IR_VERIFICATION_HOOKS_SPEC.md`

# Singularity Works — Pattern IR Verification Hooks Specification

Last updated: 2026-03-27T12:20:00Z

## Purpose

Define how verification and enforcement attach directly to Pattern IR so evaluation becomes automatic, repeatable, and composable.

Pattern IR must not be only:
- family labels
- exemplars
- emitters

It must also carry:
- claims
- constraints
- monitors
- gate hooks
- assurance links

## Design rule

Every Pattern IR entry should answer:
1. What does this pattern claim?
2. What constraints must hold?
3. What evidence can discharge those claims?
4. What monitors/tests/gates should be attached?
5. What residual risks remain if claims are not fully discharged?

## Hook classes

### 1. Contract hooks
Attach:
- preconditions
- postconditions
- invariants
- forbidden states
- representational constraints

Used by:
- static gates
- runtime guards
- simplification checks

### 2. Protocol hooks
Attach:
- state graph references
- allowed transitions
- forbidden transitions
- handshake/finalization rules
- protocol misuse signatures

Used by:
- protocol misuse gates
- runtime monitors
- recovery refinement

### 3. Property hooks
Attach:
- property templates
- metamorphic relations
- differential expectations
- mutation targets
- oracle assumptions

Used by:
- dynamic gates
- sibling differential checks
- mutation-aware QA

### 4. Evidence hooks
Attach:
- required evidence classes
- gate families required
- acceptable residual categories
- linked requirement IDs
- linked assurance claims

Used by:
- evidence ledger
- assurance rollup
- HUD summaries

### 5. Cost/substrate hooks
Attach:
- complexity expectations
- resource bounds
- numerical representation policy
- performance warnings
- simplification candidates

Used by:
- conformance/simplification gates
- substrate alignment checks
- retained-complexity justification

### 6. Monitor hooks
Attach:
- monitor templates
- required runtime signals
- severity mapping
- monitor activation conditions
- escalation rules

Used by:
- runtime verification
- requirement-to-monitor synthesis
- HUD/event surface

## Minimal hook schema

Every Pattern IR entry should allow:

```json
{
  "pattern_id": "string",
  "radicals": ["..."],
  "contracts": {
    "requires": ["..."],
    "ensures": ["..."],
    "invariants": ["..."],
    "forbidden_states": ["..."]
  },
  "protocol_hooks": {
    "state_model_ref": "optional",
    "allowed_transitions": ["..."],
    "forbidden_transitions": ["..."]
  },
  "property_hooks": {
    "properties": ["..."],
    "metamorphic_relations": ["..."],
    "differential_expectations": ["..."]
  },
  "evidence_hooks": {
    "required_gate_families": ["..."],
    "required_evidence_types": ["..."],
    "linked_requirements": ["..."],
    "linked_claims": ["..."]
  },
  "cost_hooks": {
    "expected_complexity": "optional",
    "resource_bounds": ["..."],
    "simplification_candidates": ["..."]
  },
  "monitor_hooks": {
    "monitor_templates": ["..."],
    "required_signals": ["..."],
    "severity_mapping": {}
  }
}
```

## Verification hook lifecycle

1. Pattern selected
2. Hooks loaded
3. Candidate artifact emitted
4. Gate orchestrator resolves which gates/monitors apply
5. Results recorded in evidence ledger
6. Assurance claims updated
7. HUD updated

## Required first implementation

Pattern IR v1 must support:
- contract hooks
- evidence hooks
- monitor hooks
- cost hooks
- protocol hook stubs

## Core law

A pattern is not complete unless the forge knows how to check what the pattern is promising.


---

# Included from `SINGULARITY_WORKS_EVIDENCE_LEDGER_SPEC.md`

# Singularity Works — Evidence Ledger Specification

Last updated: 2026-03-27T12:20:00Z

## Purpose

Provide a durable, queryable record of:
- what was checked
- what passed
- what failed
- what remains residual
- what requirement or claim each result supports

## Design principles

1. Evidence must be linkable.
2. Evidence must be attributable.
3. Evidence must be queryable by requirement, artifact, pattern, gate, and claim.
4. Residual risk must be explicit.
5. Evidence should support assurance arguments, not remain isolated.

## Primary objects

### RequirementRecord
Fields:
- requirement_id
- source_ref
- normalized_text
- priority
- linked_claim_ids
- linked_artifact_ids

### ArtifactRecord
Fields:
- artifact_id
- artifact_type
- origin
- version
- family
- radicals
- linked_pattern_ids

### GateRunRecord
Fields:
- gate_run_id
- gate_id
- gate_family
- timestamp
- subject_artifact_id
- status
- findings
- discharged_claim_ids
- residual_obligations

### MonitorEventRecord
Fields:
- monitor_event_id
- monitor_id
- requirement_id
- subject_artifact_id
- severity
- violation_type
- event_time
- context_snapshot_ref

### RiskRecord
Fields:
- risk_id
- description
- severity
- status
- linked_requirements
- linked_claims
- linked_artifacts
- mitigation_refs

### AssuranceClaimRecord
Fields:
- claim_id
- claim_text
- claim_type
- status
- supported_by
- monitored_by
- residual_risks
- assumptions
- responsibility_boundary

## Core indexes

The ledger should support lookup by:
- requirement_id
- artifact_id
- pattern_id
- gate_family
- monitor_id
- claim_id
- risk_id
- timestamp/session_id

## Rollup semantics

### Claim status
- discharged
- monitored
- residual
- falsified

### Risk rollup
- green
- amber
- red

### Session rollup
- counts by gate family
- counts by status
- current open residuals
- active monitor violations
- unresolved high-severity risks

## Evidence record contract

Every evidence record must answer:
- what generated this?
- what claim does it bear on?
- what artifact was involved?
- what requirement does it support?
- what residuals remain?

## Minimal persistence shape

JSONL or append-only JSON is acceptable for v1.
SQLite is acceptable for v2 when query complexity rises.

## Required first implementation

v1 ledger must support:
- append-only event recording
- rollup by requirement
- rollup by artifact
- rollup by claim
- risk summary export for HUD

## Core law

If a claim matters, its supporting evidence must be findable.


---

# Included from `SINGULARITY_WORKS_RUNTIME_ORCHESTRATION_FLOW_SPEC.md`

# Singularity Works — Runtime Orchestration Flow Specification

Last updated: 2026-03-27T12:20:00Z

## Purpose

Define the execution order connecting recovery, embodiment, QA, assurance, and HUD.

## Top-level loop

### 0. Initialize
- load context
- load configuration
- load project tag
- load relevant requirements/specs
- load session/evidence state
- start HUD

### 1. PROBE
- inspect target artifact or task
- collect constraints
- collect relevant requirements
- collect recent failures / residual risks
- collect candidate exemplars

### 2. DERIVE
- recover structure
- recover trace links
- identify relevant families/radicals
- derive verification hooks
- derive monitor seeds
- decide retrieval need

### 3. RETRIEVE
- symbolic filter
- structural rank
- optional learned rerank
- produce clean-room exemplar bundle

### 4. EMBODY
- emit candidate artifact
- attach gates
- attach monitors/tests/validators
- attach simplification candidates

### 5. VERIFY
Run gate packs in order:
1. static
2. structural
3. dynamic
4. runtime/bootstrap monitors
5. conformance/simplification

### 6. RECORD
- write gate results
- write monitor results
- write residual risks
- update linked requirements and claims
- update lineage/evolution memory

### 7. ASSURE
- roll evidence into claim state
- update assurance summaries
- update session risk color/state

### 8. DISPLAY
- refresh HUD snapshot
- surface current phase
- surface residuals and failures
- surface monitor violations and throughput

### 9. RECURSE
- if failed or residual-heavy, refine and iterate
- if good enough under configured policy, finalize
- if ambiguous, retain branch/residual note

## Short-circuit rules

Immediate stop conditions:
- critical invariant violation
- critical forbidden-state construction
- critical monitor violation
- assurance claim falsified

Warning-only conditions:
- simplification recommendation only
- medium residuals
- recoverable misuse with correction candidate

## Required orchestration outputs

Each run should end with:
- final artifact or refusal
- evidence summary
- open residual list
- linked requirements
- assurance rollup
- HUD/export summary

## Core law

The forge is not finished when code is emitted.
It is finished when the emitted artifact has been checked, recorded, rolled up, and surfaced.


---

# Included from `SINGULARITY_WORKS_UNIFIED_MASTER_SPEC_DRAFT_v0_2.md`

# Singularity Works — Unified Master Specification Draft v0.2

Last updated: 2026-03-27T12:20:00Z

## Mission

Build a Windows-first, low-dependency, pattern-driven software forge with:
- structure recovery
- constrained embodiment
- rigorous QA/enforcement
- lifecycle traceability
- assurance rollups
- live operator telemetry

## Core layers

1. Formal Family Layer
2. Exemplar Layer
3. Recovery Layer
4. Retrieval Policy Layer
5. Embodiment Layer
6. Enforcement / Evidence Layer
7. Simplification / Conformance Layer
8. Lifecycle Traceability Layer
9. Assurance / Argument Layer
10. Operator HUD / Telemetry Layer

## Primary operating law

PROBE → DERIVE → RETRIEVE → EMBODY → VERIFY → RECORD → ASSURE → DISPLAY → RECURSE

## Core objects

- Pattern IR entry
- verification hooks
- recovered structures
- exemplar bundles
- gate results
- monitor events
- risk records
- assurance claims
- HUD snapshots

## Minimum viable build set

### A. Recovery
- recovery interfaces
- grammar/state/traceability seed objects

### B. Verification
- gate engine
- gate pack registration
- evidence ledger

### C. Traceability/Assurance
- lifecycle schema
- claim rollups
- residual-risk summaries

### D. HUD
- VT-enabled Windows console renderer
- plain-text fallback
- forge/QA/evidence telemetry

### E. Runtime flow
- orchestration loop connecting all above

## Build-ready criterion

Ready to build when the system can:
1. load a requirement/spec set
2. recover enough structure to select patterns
3. attach verification hooks to emitted artifacts
4. run gate packs
5. generate monitor seeds or monitors for tracked claims
6. record evidence and residuals
7. roll evidence into assurance summaries
8. show live state in the HUD

## Remaining step after this draft

Consolidate this draft with:
- Recovery Layer spec
- QA Gate Packs spec
- Misuse Gate spec
- Simplification/Conformance spec
- Evidence Ledger spec
- Pattern IR Verification Hooks spec
- Runtime Orchestration Flow spec
- HUD module spec

into a single implementation-grade master spec.
