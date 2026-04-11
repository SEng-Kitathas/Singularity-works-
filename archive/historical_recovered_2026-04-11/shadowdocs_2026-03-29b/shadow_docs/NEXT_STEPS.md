# Next Steps — Singularity Works / CIL vNext
_Date: 2026-03-29_
_SOP: §18 Session End protocol_

---

## Ordered Queue

| # | Action | Type | Workstream | Why This Order | SOP Reference |
|---|---|---|---|---|---|
| 1 | Fix TM-012: cil_council.py self-audit false positive | EXP-20260329-003 (Exploratory) | Forge / Safety | P0 blocker — verify_build fails; must clear before any packaging | TM-012 |
| 2 | git init /tmp/sw_v19; tag current state as v1.13 | Process | All | PD-001 — reproducibility debt; must close before EXP-20260329-002 | PD-001 |
| 3 | Run EXP-20260329-002: confirmatory assault replication (fresh checkout) | Confirmatory experiment | Forge / Detection | Foundation of all downstream work; must be confirmed, not just exploratory | EXP-20260329-002 |
| 4 | Run TM-020: ForgeContext v4.0 E2E integration test with assault suite | Integration test | CIL Memory (Python) | Verify EPMEM/SMEM/Contradiction stack works under real load | TM-020 |
| 5 | Package complete shadow doc set with build artifacts | Doc | Process | Close the backfill; archive this session | SOP §11 Phase F |
| 6 | Begin SMEM state accumulation for EXP-20260329-001 | Passive (run multiple forge sessions with forge_context_path active) | CIL Memory | Needs N sessions before distortion budget test has meaningful state | EXP-20260329-001 |
| 7 | Implement cil-forge system_gate_runner real dispatch (replace inline heuristics) | Build | cil-forge Rust | RV-20260329-006 prerequisite; Python oracle comparison requires real dispatch | TM-017 |
| 8 | Wire cil_council quick_validate() into orchestrator IRIS validation path | Build | CIL Council / IRIS | Completes the L2→L3 bridge; requires P0 fix first | TM-019 |
| 9 | Port ContradictionGraph from Rust to Python forge_context.py | Build | CIL Memory (Python) | RV-20260329-005 — Python side currently uses simpler list | TM-006 |
| 10 | Run EXP-20260329-001: distortion budget calibration test | Confirmatory experiment | CIL Memory | Needs SMEM state built up first (step 6) | EXP-20260329-001 |

---

## What Recursive Replay Is Triggered by the Next Meaningful Finding

- If EXP-20260329-002 SUPPORTED: → RV-20260329-001 (P-001 advances toward STABLE)
- If EXP-20260329-002 NULL: → RV-20260329-002 (P0 pause — forensics first)
- If EXP-20260329-001 SUPPORTED: → RV-20260329-003 (extend to semantic_vq.rs)
- If EXP-20260329-001 NULL: → RV-20260329-004 (try alternative integration points)
- If cil-forge oracle match confirmed: → RV-20260329-006 resolved
- If cil_council live test runs: → RV-20260329-007 resolved

---

## What Must Not Happen Next

_(explicit anti-drift guidance per SOP R-05, R-12)_

- **DO NOT** widen scope (new capsules, new systems, new architecture) while TM-012 P0 is open.
- **DO NOT** run EXP-20260329-002 before git tracking is established (PD-001 would invalidate the reproducibility claim of that experiment).
- **DO NOT** treat any pre-SOP result as STABLE without a confirmatory replication under the SOP standard.
- **DO NOT** let shadow docs lag behind build changes. Update by delta, not by replacement.
- **DO NOT** run any confirmatory experiment without first entering it in the Pre-Registration Log.
- **DO NOT** adopt any deviation from a pre-stated experiment plan silently — log it first.
- **DO NOT** mix workstream evidence — a CIL Memory result does not advance a Forge Detection claim without an explicit cross-workstream validation step.
