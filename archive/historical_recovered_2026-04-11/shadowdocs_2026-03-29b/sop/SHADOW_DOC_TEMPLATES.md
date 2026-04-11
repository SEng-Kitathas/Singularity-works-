# Shadow Document Templates
_Version: 2026-03-29_

All templates follow the same rule: update by delta, never by replacement.
Prior state is preserved. Changes are additive.

---

# TRACE MATRIX TEMPLATE

| ID | Requirement / Seam | Status | Mode | Evidence | Workstream | Notes |
|---|---|---|---|---|---|---|
| TM-001 | `<fill in>` | Open | Exploratory/Confirmatory | `<artifact ID>` | `<workstream>` | `<fill in>` |

**Status options:** Open / Active / Incumbent / Promotable / Provisional / Stable / Collapsed / Quarantined / Deviated

---

# RESEARCH CROSSWALK TEMPLATE

```
SEAM ID:                   [RC-NNN]
SEAM NAME:                 [descriptive]
WORKSTREAM:                [which scorecard line]

REPRESENTATIVE SOURCES:
  - [citation or artifact — not a citation dump]

CORE TAKEAWAY:
  [what the literature actually says — stripped of jargon]

PROJECT-NATIVE TRANSLATION:
  [what this means in our specific system/terminology]

ARCHITECTURE / PROCESS IMPLICATION:
  [what this changes in the build or process — or "none" if background]

EVIDENCE STRENGTH:          HIGH / MEDIUM / LOW / SPECULATIVE
ISOMORPHS FOUND:            [any cross-domain structural equivalents]
RESIDUAL UNCERTAINTY:       [what this seam does NOT resolve]
NEXT EXPERIMENT PRESSURE:   [what this research makes us want to run]
```

---

# DOCTRINE SNAPSHOT TEMPLATE

_Date: [timestamp]_
_Supersedes: [prior snapshot ID]_

## Promoted Beliefs (Stable)
_(survived recursive replay; treated as hard constraints)_
- `<statement — with evidence artifact ID>`

## Provisional Beliefs
_(integrated but subject to replay)_
- `<statement — with evidence artifact ID and replay trigger>`

## Exploratory Signals
_(tentative; require confirmatory test before promotion)_
- `<statement — labeled EXPLORATORY>`

## Quarantined Claims
_(overclaiming, theater, or single-pass validation)_
- `<statement — with reason for quarantine>`

## Collapsed Paths
_(fully exhausted under closure standard)_
- `<path — with closure evidence>`

## Open Tensions
_(contradictions not yet resolved)_
- `<tension — between belief A and evidence B>`

---

# REVISIT LEDGER TEMPLATE

```
REVISIT ID:         [RV-YYYYMMDD-NNN]
DATE TRIGGERED:     [timestamp]
TRIGGER:            [what finding or failure created this obligation]
SEAMS AFFECTED:     [list of trace matrix IDs or experiment IDs]
WHAT MUST BE DONE:  [specific — not "look at it again"]
PRIORITY:           P0 (blocking) / P1 (high) / P2 (medium) / P3 (background)
STATUS:             OPEN / IN PROGRESS / RESOLVED
RESOLVED DATE:      [if resolved]
RESOLUTION:         [what happened when revisited]
```

---

# MAINTENANCE NOTE TEMPLATE

_Date: [timestamp]_

## Update Rules (Active)
- Update Trace Matrix when: requirement/status changes
- Update Research Crosswalk when: research changes architecture or process
- Update Addendum when: new high-value findings not yet in main docs
- Update Doctrine Snapshot when: belief system changes
- Update Revisit Ledger when: recursive replay is newly obligated
- Update Pre-Registration Log when: new confirmatory experiment begins
- Update Deviation Log when: any plan is departed from
- Update Evaluation Log when: any experiment concludes (including null results)

## Active Process Debt
_(manual steps that should eventually be automated)_
- `<debt item — with target horizon for closing>`

## Recent Discipline Changes
- `<what changed in process and why>`

## Flags for Next Session
- `<specific flags — deviations unresolved, theater flags pending, etc.>`

---

# ADDENDUM TEMPLATE

_Pass: [date]_
_Supersedes addendum: [prior date]_

## New Decisions
- `<what changed and why>`

## Promoted Findings (This Pass)
- `<statement — labeled PROMOTED, with evidence>`

## Newly Quarantined Claims
- `<statement — with reason>`

## New Recursive Replay Obligations
- `<what must be revisited and why>`

## Updated Phrasing Worth Preserving
_(exact language that should carry forward)_
- `<quote>`

---

# CURRENT STATE TEMPLATE

_Date: [timestamp]_

**Project:** `<name>`
**Mission:** `<one sentence>`

## Incumbent Baseline (per workstream)
| Workstream | Incumbent | Empirical Foothold | Last Updated |
|---|---|---|---|
| `<name>` | `<description>` | YES/NO/PARTIAL | `<date>` |

## Open Seams (ordered by priority)
| Priority | Seam | Blocking? | Next Action |
|---|---|---|---|
| P0 | `<seam>` | YES/NO | `<action>` |

## Verified Findings
- `<list with experiment IDs>`

## Provisional Findings (need confirmatory test)
- `<list — labeled EXPLORATORY>`

## Current Blockers
- `<list>`

## Active Deviations (unresolved)
- `<list — deviation log IDs>`

## Theater Flags (unresolved)
- `<list>`

## Process Debt (active)
- `<list>`

## Resume Point
`<specific — experiment ID, seam, or doc update in progress>`

---

# NEXT STEPS TEMPLATE

_Date: [timestamp]_

## Ordered Queue

| # | Action | Type | Workstream | Why This Order |
|---|---|---|---|---|
| 1 | `<action>` | Experiment/Doc/Audit | `<workstream>` | `<reason>` |

## What Recursive Replay Is Triggered by the Next Meaningful Finding
- `<seams to revisit>`

## What Must Not Happen Next
_(explicit anti-drift guidance)_
- `<what to avoid and why>`

---

# ZERO-LOSS EXTRACTION TEMPLATE

_Source: [artifact name + hash]_
_Date: [timestamp]_

## Corpus Scope
`<what was extracted and from where>`

## Phase A — Manifest
| # | Artifact | Type | Hash | Role |
|---|---|---|---|---|
| C1 | `<name>` | `<type>` | `<sha256>` | `<role>` |

## Phase B — New Signal
_(entities, relations, claims, process patterns — not seen before)_
- `<statement>`

## Phase B — Reinforcement of Existing Doctrine
_(what this confirms that we already believed)_
- `<statement + prior belief ID>`

## Phase C — Extraction Matrix
| ID | Source | Claim | Evidence | Mode | Doctrine Effect | Status | Next Action |
|---|---|---|---|---|---|---|---|
| M-001 | C1 | `<claim>` | HIGH/MED/LOW | CONF/EXPL | `<effect>` | `<status>` | `<action>` |

## Phase D — Orphaned Findings
_(high-value signal that would otherwise vanish)_
1. `<finding — specific>`

## Phase D — Flags
- Evaluation theater suspected: `<yes/no — detail>`
- HARKing risk: `<yes/no — detail>`
- Workstream mixing: `<yes/no — detail>`
- Null results suppressed: `<yes/no — detail>`

## Phase E — Doctrine Effect
`<what this extraction changes in the belief system, overall>`

---

# PROJECT START CHECKLIST

- [ ] Read Load-First Rehydration Note
- [ ] Read Universal Lab SOP
- [ ] Create or load Current State
- [ ] Create or load Next Steps
- [ ] Create or load Trace Matrix
- [ ] Create or load Doctrine Snapshot
- [ ] Create or load Revisit Ledger
- [ ] Create Experiment Pre-Registration Log (blank)
- [ ] Create Deviation Log (blank)
- [ ] Create Evaluation Log (with workstream scorecards)
- [ ] Create Maintenance Note
- [ ] Create Project Index (with hashes)
- [ ] Declare incumbent baseline per workstream
- [ ] Declare open seams in priority order
- [ ] Classify first experiment as exploratory or confirmatory
- [ ] Begin work

---

# PROJECT INDEX TEMPLATE

_Version: [date]_

## Must-Read (Load Order)
1. `LOAD_FIRST_REHYDRATION_NOTE.md`
2. `UNIVERSAL_LAB_SOP_2026-03-29.md`
3. `TRACE_MATRIX.md`
4. `RESEARCH_CROSSWALK.md`
5. `ADDENDUM.md`
6. `MAINTENANCE_NOTE.md`
7. `REVISIT_LEDGER.md`
8. `DOCTRINE_SNAPSHOT.md`
9. `EXPERIMENT_PREREGISTRATION_LOG.md`
10. `DEVIATION_LOG.md`
11. `EVALUATION_LOG.md`

## Extraction Docs
| Artifact | Hash | Date | Role |
|---|---|---|---|
| `<name>` | `<sha256>` | `<date>` | `<role>` |

## Experiment Artifacts
| Exp ID | Spec | Report | Status |
|---|---|---|---|
| EXP-... | `<path>` | `<path>` | `<status>` |

## Project-Specific Artifacts
`<fill in>`
