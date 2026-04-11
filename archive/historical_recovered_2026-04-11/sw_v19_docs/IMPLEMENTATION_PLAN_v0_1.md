# Singularity Works — Implementation Plan v0.1

Last updated: 2026-03-27T12:40:00Z

## Objective

Move from consolidated specification to a buildable, integrated codebase with the fewest external dependencies practical on Windows.

## Build strategy

### Stage 1 — Core substrate
Deliver:
- typed core models
- Pattern IR core
- verification hooks model
- evidence ledger core
- runtime orchestration shell
- HUD shell

Exit condition:
- package imports cleanly
- objects serialize
- HUD can render snapshots
- orchestration can move a dummy task through all phases

### Stage 2 — QA spine
Deliver:
- gate engine
- static gate pack
- structural gate pack
- dynamic gate pack stubs
- runtime gate pack stubs
- misuse gate stubs
- simplification/conformance stubs

Exit condition:
- gates can register and run
- evidence ledger records gate outputs
- HUD surfaces gate counts and residuals

### Stage 3 — Recovery spine
Deliver:
- recovery object model
- trace-link objects
- grammar/protocol/invariant interfaces
- requirement-to-monitor seed objects

Exit condition:
- recovery results can be attached to Pattern IR and evidence ledger
- orchestration can DERIVE from input task/context

### Stage 4 — Traceability / assurance
Deliver:
- lifecycle traceability object model
- requirement linkage
- assurance claim rollups
- residual-risk rollups

Exit condition:
- one requirement can be linked through artifact, gate result, monitor, risk, and assurance claim

### Stage 5 — Integrated runtime
Deliver:
- real orchestration loop
- session persistence
- HUD live updates
- project-tag aware execution
- basic branch/context support

Exit condition:
- end-to-end run from requirement/task to artifact/evidence/HUD completes

### Stage 6 — Higher-order intelligence
Deliver:
- repository exemplar mining
- retrieval policy
- recovery refinement
- monitor generation
- differential/mutation extensions
- simplification recommendations
- assurance enrichment

Exit condition:
- system can improve candidate choice with evidence-backed iteration

## Folder layout

```text
Singularity-Works/
  README.md
  pyproject.toml
  launch_sw.bat
  launch_sw.ps1
  configs/
    default.json
  docs/
    MONOSPEC_v0_3.md
    IMPLEMENTATION_PLAN_v0_1.md
  singularity_works/
    __init__.py
    models.py
    pattern_ir.py
    verification_hooks.py
    evidence_ledger.py
    gates.py
    enforcement.py
    recovery.py
    traceability.py
    assurance.py
    orchestration.py
    hud.py
    runtime.py
    util.py
  examples/
    demo_run.py
```

## Coding rules

1. stdlib-first
2. Windows-first behavior
3. ASCII-safe operator surface
4. append-only evidence recording for v1
5. no hidden magical global state
6. every subsystem emits structured data, not only logs

## Immediate next implementation order

1. `models.py`
2. `verification_hooks.py`
3. `pattern_ir.py`
4. `evidence_ledger.py`
5. `gates.py`
6. `enforcement.py`
7. `hud.py`
8. `recovery.py`
9. `traceability.py`
10. `assurance.py`
11. `orchestration.py`
12. `runtime.py`
13. demo + launchers

## Ready-to-build criterion

The starter codebase is ready when:
- the package installs locally
- the demo run executes without external services
- the HUD renders
- the evidence ledger records
- gate packs can run stubs
- one end-to-end orchestrated cycle completes
