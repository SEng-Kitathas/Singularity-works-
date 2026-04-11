# Maintenance Note — Singularity Works / CIL vNext
_Date: 2026-03-29_
_SOP: §21 Corrective Action Protocol_

---

## Update Rules (Active)
- Update Trace Matrix when: requirement/status changes
- Update Research Crosswalk when: research changes architecture or process pressure
- Update Doctrine Snapshot when: belief system changes (promotion or demotion)
- Update Revisit Ledger when: recursive replay newly obligated
- Update Experiment Pre-Registration Log when: new confirmatory experiment begins (BEFORE execution)
- Update Deviation Log when: ANY plan departed from (BEFORE analysis)
- Update Evaluation Log when: any experiment concludes (including null results)
- Update Addendum when: new high-value findings not yet integrated into main docs

---

## Active Process Debt

| Debt | Description | Risk Level | Target Horizon |
|---|---|---|---|
| PD-001 | No git version control on /tmp/sw_v19 | HIGH — reproducibility failure risk | Before next build session |
| PD-002 | No seed/version pinning on Python forge experiments | MEDIUM — MLOps standard not met | Before EXP-20260329-002 |
| PD-003 | cil_council integration requires live LM Studio — no offline oracle | MEDIUM — live test blocked without LM | When LM Studio session available |
| PD-004 | Full six-phase Loop+ extraction on MHT corpus deferred | LOW — shadow docs + build packages substitute | If replay required for this session |
| PD-005 | cil-forge system implementations are functional stubs | HIGH — cil-forge is not production until stubs replaced | Next cil-forge build session |
| PD-006 | No external baseline for forge detection accuracy | MEDIUM — ISO 17025 workstream separation violated | Before promoting P-001 to STABLE |
| PD-007 | cil_council.py self-audit false positive (P0 blocker) | CRITICAL — verify_build fails | Next action (EXP-20260329-003) |

---

## Recent Discipline Changes

| Date | Change | Reason |
|---|---|---|
| 2026-03-29 | UNIVERSAL_LAB_SOP_2026-03-29.md adopted | Uploaded by Rahl at session end |
| 2026-03-29 | Loop+ Meta Control Layer folded into SOP §12 | LOOP_PLUS_AGNOSTIC_GUIDE_META_CONTROL_2026-03-29bc-1.md uploaded |
| 2026-03-29 | All pre-SOP session work retroactively classified EXPLORATORY | DEV-20260329-001 |
| 2026-03-29 | Deviation Log opened | First two deviations logged |
| 2026-03-29 | Experiment Pre-Registration Log opened | First three experiments pre-registered |
| 2026-03-29 | Shadow doc backfill initiated | This session |

---

## Flags for Next Session

1. **P0 — Fix TM-012**: cil_council.py self-audit false positive. Execute EXP-20260329-003 (exploratory — find encoding approach). Then confirmatory test. verify_build must reach 0 failures.

2. **Establish git tracking** before any further /tmp/sw_v19 modifications. PD-001 is a reproducibility violation that compounds every session.

3. **Execute EXP-20260329-002** (confirmatory assault replication) as the first confirmatory experiment. This is the foundation. If it fails, pause everything else.

4. **EXP-20260329-001** (distortion budget calibration) requires SMEM state to build up — needs multiple sessions of forge context accumulation before meaningful test.

5. **Load shadow docs in order** at next session start. Resume command: load this file set → re-state incumbent baseline → check deviation log → check evaluation log → execute P0 fix → then proceed.
