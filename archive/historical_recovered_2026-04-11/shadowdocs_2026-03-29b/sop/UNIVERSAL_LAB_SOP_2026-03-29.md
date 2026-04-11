# Universal Lab SOP for LM-Assisted Research & Software Projects
_Version: 2026-03-29 — Lab-Grade Chimera Edition_
_Lineage: r3 (Singularity Works extraction) + ax/ay (generic starter) + NIH ELN + GLP/ISO 17025 + PRISMA 2020 + Open Science pre-registration + MLOps reproducibility standards_

---

## Preamble: What This Is

This SOP is a **best-practices Chimera** — a single governing document synthesizing the strongest elements from:

- **NIH Electronic Lab Notebook standards** (immutable audit trail, witness discipline, raw data preservation)
- **OECD/FDA Good Laboratory Practice** (study director accountability, deviation tracking, QA independence, archivability)
- **ISO/IEC 17025** (traceability chains, method validation, internal audit, corrective action loops)
- **PRISMA 2020 + Open Science pre-registration** (confirmatory vs. exploratory split, HARKing prevention, kill criteria before data collection, deviation transparency)
- **MLOps reproducibility standards** (version everything, deterministic pipelines, experiment tracking, model registry, data lineage)
- **Singularity Works / Forge / CIL / TQ2 lineage** (PROBE→DERIVE→EMBODY→VERIFY→RECURSE, zero-loss extraction, shadow-control layer, anti-drift rules, evaluation theater governance)

It is **domain-agnostic** by design. The project-specific state section (§16) is the only part that changes per project.

---

## Part I: Foundational Law

### §1. The Master Loop

**PROBE → DERIVE → EMBODY → VERIFY → RECURSE**

This is not a suggestion. It is the control law.

```
PROBE     Interrogate the system, corpus, or problem until actual structure,
          failure modes, hidden dependencies, and contradictions are visible.
          Not surface plausibility. Not aesthetic appeal. Structure.

DERIVE    Translate probe results into a FALSIFIABLE interpretation.
          State explicitly: what changed, what did not, what strengthened,
          what weakened, what assumption is now under pressure.
          If you cannot write a falsifiable claim, you have not derived yet.

EMBODY    Instantiate the derivation into something testable:
          code, architecture, experiment, benchmark, document, spec,
          memory policy, process update, or next-step queue.
          Embodiment is not "write it down." It is "make it runnable or auditable."

VERIFY    THIS IS THE HARD BRAKE.
          Check whether embodiment cashes out the derivation.
          Requirements: direct test, baseline comparison, structural
          distinctness check, artifact generation, explicit residuals.
          Do NOT allow EMBODY → RECURSE without this stage.
          Mythology accumulates specifically in the gap between embody and verify.

RECURSE   Replay forward AND backward. If a new result meaningfully changes
          interpretation, rerun earlier seams under the new view.
          Earlier negatives are not permanent. Earlier positives are not permanent.
```

### §2. The Two Modes of Every Experiment (Open Science)

Every experiment is either **exploratory** or **confirmatory**. These must be declared before execution — not after results are known. Treating the same data as both is HARKing (Hypothesizing After Results are Known) and is a process violation.

```
EXPLORATORY   Hypothesis-generating. Minimize false negatives. Results are
              tentative and require a subsequent confirmatory test to promote.
              Label all exploratory findings explicitly as exploratory.

CONFIRMATORY  Hypothesis-testing. Minimize false positives. Requires:
              - pre-stated falsifiable hypothesis
              - pre-stated analysis plan
              - pre-stated kill criteria
              - pre-stated success threshold
              Once data are observed, the analysis plan is locked.
```

Deviations from a pre-stated plan must be recorded as deviations with justification — not silently adopted.

### §3. The Shadow-Control Layer

The project's persistent memory lives in a structured document set. These are not scratch notes. They are the lab notebook, the quality system, and the institutional memory combined.

**Required document set (load in this order):**

| # | Document | Purpose |
|---|---|---|
| 1 | This SOP | Governing law — load first |
| 2 | Trace Matrix | Master operational table: requirements, status, evidence |
| 3 | Research Crosswalk | Research indexed by seam, not by paper |
| 4 | Addendum | Fast delta for newest findings |
| 5 | Maintenance Note | Update discipline record |
| 6 | Revisit Ledger | What must be replayed, when, and why |
| 7 | Doctrine Snapshot | All currently promoted beliefs, with evidence |
| 8 | Experiment Pre-Registration Log | All pre-stated hypotheses and analysis plans |
| 9 | Deviation Log | All departures from pre-stated plans, with justification |
| 10 | Extraction Docs | Zero-loss OIE+ELT+Systematic+DEFNLP passes over uploads |
| 11 | Evaluation Log | Honest scorecard per workstream, updated after each wave |
| 12 | Project Index | Archive manifest with hashes and load order |

**Update rule:** Update by delta, never by replacement. Every change is recorded. No silent overwrites.

---

## Part II: Governing Rules

### §4. Non-Negotiable Rules

These rules have no exceptions. Violations must be recorded as deviations.

**R-01 — Nothing locks in early**
No architecture, variable, doctrine, or result becomes final because it is currently winning.

**R-02 — Best current is not final**
Incumbent means: best current operational baseline, still provisional, must survive future replay.

**R-03 — No silent overwrite**
Update doctrine by delta. Every change is recorded. The prior state is preserved.

**R-04 — No orphan insight**
If a finding matters, it lands in the shadow layer. If it doesn't land, it doesn't count.

**R-05 — No fake progress**
A long discussion is not advancement unless: artifacts were produced, docs moved, or a seam was genuinely narrowed.

**R-06 — No disconnected research**
Research must change build pressure, doctrine, ordering, or active seams. Background signal stays labeled as background.

**R-07 — No feature spine without QA spine**
The evidence/verification chain advances with the build chain. They are not separable.

**R-08 — No hidden uncertainty**
If something is partial, residual, speculative, not wired, or not yet validated — say so explicitly in the record.

**R-09 — No closure by one failed framing**
A failed implementation kills that framing, not the variable class.

**R-10 — No single-source sufficiency**
No one thread, one upload, one report, one benchmark, or one model's opinion is sufficient alone.

**R-11 — No evaluation theater**
Structurally non-distinct experimental conditions producing identical results is an implementation error, not a data point. Audit before accepting.

**R-12 — No widening under unresolved failure modes**
When a central failure mode is unresolved, freeze scope and audit. Do not widen.

**R-13 — No substrate claim without empirical foothold**
A substrate idea with no empirical result is theory. Record it as theory.

**R-14 — Separate to measure. Compose to run.**
When multiple strata or branches exist, isolate them for attribution; compose only when earned.

**R-15 — No process automation debt forever**
Manual discipline degrades. Name the debt. Establish a horizon for closing it.

**R-16 — Exploratory and confirmatory must be declared in advance**
The same data cannot generate and test a hypothesis. Declare mode before execution.

**R-17 — Kill criteria are mandatory for confirmatory experiments**
A confirmatory experiment without pre-stated kill criteria is theater. State what would falsify the hypothesis before running.

**R-18 — Deviations are recorded, not adopted silently**
Any departure from a pre-stated plan must be logged in the Deviation Log with justification. The original plan is preserved.

**R-19 — Null results are recorded**
A null result is data. Suppressing it is a process violation. Record it in the Evaluation Log.

**R-20 — The LM applies extraction discipline to its own outputs**
The LM must evaluate its own responses using the same extraction standard applied to external sources. Overclaiming in LM output is a process failure.

---

## Part III: Epistemic Vocabulary

### §5. Status Terms

| Term | Meaning |
|---|---|
| **Open** | Not explored enough to justify closure |
| **Active** | Currently under investigation |
| **Incumbent** | Best current baseline; still provisional; must survive future replay |
| **Exploratory** | Hypothesis-generating; results are tentative |
| **Confirmatory** | Hypothesis-testing under a pre-stated plan |
| **Promotable** | Finding meets promotion criteria; not yet formally integrated |
| **Provisional** | Integrated into doctrine; subject to replay |
| **Stable** | Survived recursive replay; treated as hard constraint |
| **Collapsed** | Only after full closure standard is satisfied |
| **Deviated** | Experiment departed from pre-stated plan; deviation logged |
| **Quarantined** | Overclaiming, non-distinct evaluation, or single-pass validation; not promotable |

### §6. Closure Standard

A path is only **collapsed** when ALL five conditions are met:

1. Direct test executed
2. Nearby-combination test executed
3. Inversion / wrong-looking test executed
4. Recursive replay after later findings
5. Still no meaningful gain beyond redundancy

One failed framing ≠ variable closure. Silence ≠ evidence. Null result ≠ dead seam.

---

## Part IV: Experiment Protocol

### §7. Pre-Registration (Required for Confirmatory Experiments)

Before running any confirmatory experiment, record in the Experiment Pre-Registration Log:

```
EXPERIMENT ID:        [unique ID, date-stamped]
MODE:                 CONFIRMATORY or EXPLORATORY
HYPOTHESIS:           [exactly one falsifiable claim]
WHAT WOULD FALSIFY:   [the kill criterion — specific and measurable]
SUCCESS THRESHOLD:    [minimum result to consider hypothesis supported]
ANALYSIS PLAN:        [exactly how results will be analyzed — pre-stated]
BASELINES:            [comparators — internal and external]
VARIANTS:             [what changes between conditions]
STRUCTURAL DISTINCTNESS CHECK: [confirm conditions are genuinely different]
DEVIATION POLICY:     [any deviation from above must be logged before analysis]
```

For exploratory experiments, the pre-registration is a plan doc (scope, goal, what would be interesting) — not a locked analysis plan.

### §8. Experiment Execution

During execution:

- Record **what was actually done**, not what the protocol says (NIH ELN standard)
- Record **all deviations** immediately, before analysis
- Record **all raw observations**, regardless of whether they seem relevant
- Record **failure conditions** — crashes, timeouts, unexpected behavior — as data
- Do not re-run until a good result appears without logging the failed runs

### §9. Experiment Report (Required for Every Meaningful Experiment)

```
EXPERIMENT ID:        [matches pre-registration]
MODE:                 CONFIRMATORY or EXPLORATORY
HYPOTHESIS TESTED:    [exact claim from pre-registration]
RESULT:               [what actually happened]
VERDICT:              SUPPORTED / NOT SUPPORTED / INCONCLUSIVE
WHAT CHANGED:         [specific deltas from baseline]
WHAT DID NOT CHANGE:  [what remained stable]
DEVIATIONS FROM PLAN: [any; if none, state "none"]
EVALUATION THEATER CHECK: [are conditions structurally distinct? confirm]
EXTERNAL BASELINE:    [result vs. comparator — mandatory]
RESIDUALS:            [what this experiment does NOT resolve]
DOCTRINE EFFECT:      [what this changes in the belief system, if anything]
RECURSIVE REPLAY OBLIGATIONS: [what earlier seams must be revisited]
NEXT ACTION:          [specific, ordered]
NULL RESULT RECORDED: [yes/no — null results must be recorded]
```

### §10. Required Experiment Classes (General)

Every research program should eventually run:

- **Baseline isolation**: does the simplest possible comparator beat random?
- **Structural distinctness confirmation**: are the conditions genuinely different?
- **External neural/statistical baseline**: does the substrate actually outperform a minimal learned model?
- **Ablation**: what happens when one component is removed?
- **Noise/adversarial test**: does performance degrade gracefully or catastrophically?
- **Recursive replay**: do earlier results hold under new findings?

For code intelligence / forge projects, additionally:

- **Assault pass**: clean code → all GREEN; known failures → all RED
- **Self-audit**: the system audits its own source under the same standard applied outward
- **Zero-false-green verification**: this is a hard architectural invariant, not a goal

---

## Part V: Zero-Loss Extraction Protocol

### §11. Six-Phase Extraction

All uploads treated as lab evidence. Run all six phases for significant uploads.

**Phase A — ELT Ingest**
Preserve raw files. Create manifest. Hash all artifacts. Map corpus shape. Do not destroy source structure before interpretation. (Follows ELT over ETL: raw data preserved in full before any transformation.)

**Phase B — OIE Extraction**
Normalize: entities, relations, claims, process patterns, dependencies, contradictions, implicit assumptions.
- Coreference resolution: all mentions of the same entity resolve to a single record
- Triple extraction: every stated fact → (Subject, Predicate, Object)
- Pattern-over-term: search for structures and motifs, not just keywords

**Phase C — Standardized Extraction Matrix**
For each meaningful claim:

| Field | Content |
|---|---|
| Source | Artifact + location |
| Claim | Exact statement |
| Evidence strength | HIGH / MEDIUM / LOW / UNVERIFIED |
| Mode | CONFIRMATORY finding / EXPLORATORY signal / BACKGROUND |
| Doctrine effect | What this changes |
| Status | Open / Promotable / Provisional / Stable / Quarantined |
| Next action | Specific |

**Phase D — DEFNLP Post-Processing**
Rescue what would otherwise vanish:
- Orphan signal (findings buried in narrative)
- Hidden dependencies (A requires B, but B is buried)
- Baseline errors (assumptions quietly wrong)
- Category errors (mixing workstream A evidence into workstream B)
- **Evaluation theater** (non-distinct conditions producing identical results)
- **HARKing** (hypothesis reconstruction after results observed)
- Self-referential patterns (system flagging its own patterns)

**Phase E — Control-Layer Integration**
Promote only what is: repeated, load-bearing, architecture-shaping, research-validated, implementation-relevant, or process-critical. Everything else stays provisional or exploratory.

**Phase F — Output Package**
For significant extractions: manifest + extraction doc + triples table + standardized matrix + post-process synthesis + package zip. Use BagIt format for archiving (bag-info.txt + manifest-sha256.txt).

---

## Part VI: Research Loop

### §12. Loop+ (External Research Protocol)

Eight stages, executed in order:

1. Primary-source pass (arXiv, PubMed, IEEE, SSRN, Zenodo, OSF Preprints)
2. Discovery pass (cross-domain structural equivalents)
3. Fast-signal pass (Ars Technica, HN, Wired — for implementation clues)
4. Isomorph-predator pass (hunt structural equivalents across unrelated domains)
5. Native ontology translation (import findings into project language)
6. Control-layer update (what changes in the shadow docs)
7. Experiment pressure (what does this research make us run next?)
8. Recursive replay (do earlier conclusions survive the new evidence?)

**Research rules:**
- Group findings by seam, not by paper
- Prefer representative sources over citation dumps
- Translate findings out of external jargon before promoting
- Record what a finding changes in the build — not just that it exists
- Null research results (seams that found nothing) are recorded

**Source priority:** Internal extraction docs > peer-reviewed primary literature > pre-prints with code > pre-prints without code > review articles > secondary commentary.

---

## Part VII: Traceability & Audit Standards

### §13. Immutable Record Requirements (NIH ELN / GLP)

Every significant finding, experiment, and doc update must be:

- **Dated** — timestamp at creation
- **Authored** — which session/agent produced it
- **Linked** — to the source artifact or experiment that generated it
- **Preserved in original form** — raw observations not overwritten
- **Deviation-tracked** — any change to a plan recorded as deviation, not replacement
- **Archivable** — all artifacts in a retrievable, hash-verified format

Errors are corrected by **addendum**, not by erasure. The original record is preserved with a cross-reference to the correction.

### §14. Version Control Requirements (MLOps)

For any software or ML project, version control applies to:

- Code (Git — every experiment branch tracked)
- Data (DVC or equivalent — dataset versions hashed)
- Models/artifacts (registry — every artifact linked to code + data hash that produced it)
- Configuration (hyperparameters, seeds, environment spec — version-controlled alongside code)
- Random seeds (set and recorded — non-determinism is a reproducibility failure)

**Reproducibility standard:** Given the same code version + data version + config version + seed, results must be reproducible within stated variance bounds. Any run that cannot be reproduced is flagged as a reproducibility failure and logged.

### §15. Workstream Separation (Audit Requirement)

When a project contains distinguishable workstreams, maintain **separate scorecards** in the Evaluation Log. Evidence from workstream A does not advance claims in workstream B without an explicit cross-workstream validation step.

Example pattern: theoretical substrate (no empirical foothold yet) vs. validated runtime (empirical signal confirmed). These are separate lines in the scorecard.

---

## Part VIII: Session Protocol

### §16. At Session Start — Mandatory Rehydration

Before doing anything substantive:

> *Treat this project as a lab, not a casual conversation. You are resuming a long-horizon research and build process with persistent shadow docs, artifact corpus, experiment history, doctrine snapshots, revisit ledgers, and recursive process rules. Do not assume memory from chat context is sufficient.*

Load in order:
1. This SOP
2. Trace matrix + crosswalk + addendum + maintenance note
3. Latest next-steps / work queue
4. Latest SOP cycle update
5. Latest revisit ledger
6. Doctrine snapshot
7. Experiment pre-registration log + deviation log
8. Relevant extraction docs
9. Active-seam experiment reports + evaluation log

Re-state explicitly:
- Current incumbent baseline (per workstream)
- Open seams (ordered by priority)
- What is actually verified vs. provisional
- What the Deviation Log shows
- What would falsify the current working hypothesis

### §17. During Session

- Classify every experiment before running it: exploratory or confirmatory
- Pre-register confirmatory experiments before observing data
- Record deviations immediately
- Record null results
- Apply self-evaluation discipline to all LM outputs

### §18. At Session End

Update (only if there is a real delta):
- Trace matrix (if requirement/status changed)
- Research crosswalk (if research changed architecture)
- Addendum (if new high-value findings)
- Maintenance note (if discipline changed)
- Next-steps (if queue changed)
- Doctrine snapshot (if belief system changed)
- Revisit ledger (if recursive replay is now obligated)
- Deviation log (if any plan was departed from)
- Evaluation log (if any experiment concluded)

### §19. Compaction / Context-Loss Recovery

1. Stop widening immediately
2. Load this SOP
3. Load the full shadow-doc set in order (§16)
4. Re-state incumbent baseline vs. open seams
5. Check deviation log — were any in-progress deviations not resolved?
6. Check evaluation theater — were any recent results from non-distinct conditions?
7. Check workstream separation — is evidence being mixed across scorecard lines?
8. Only then resume

---

## Part IX: Quality Assurance

### §20. Internal Audit Trigger Conditions

Run an internal audit when any of the following occur:

- A seam produces identical results across conditions designed to be different → **evaluation theater audit**
- A finding is promoted that was only observed once → **single-observation promotion audit**
- Two workstreams' evidence is cited together to support a joint claim → **workstream separation audit**
- An analysis plan was not pre-registered before data collection → **HARKing risk audit**
- A null result was not recorded → **suppression audit**
- A deviation was adopted silently → **deviation log audit**
- The project scope widened while a central failure mode was unresolved → **scope creep audit**

### §21. Corrective Action Protocol

When an audit finds a violation:

1. Record the finding in the Maintenance Note (what happened, when, why)
2. Record the correction (what will change going forward)
3. Record the retroactive effect (what prior results are now suspect)
4. Add a Revisit Ledger entry for any affected seams
5. Do not delete the original incorrect record — annotate it with a cross-reference

---

## Part X: Architectural Doctrine (Carry-Forward)

These findings are stable enough to carry forward as hard constraints. They originated in the Forge/CIL/TQ2 lineage and apply to any project with analogous architectural concerns.

### §22. Promoted Laws

| Law | Statement |
|---|---|
| L-01 | No rule-generator without coupling. Rules/gates/strategies that live outside the core capsule/genome drift from day one. |
| L-02 | No domain without decision. Domain/language detection must always commit. "Unknown" is an architectural failure. |
| L-03 | No IR fallback conditional on upstream success. If a signal channel holds signal, the gate must receive it unconditionally. |
| L-04 | No vector truth alone. Vectors guide retrieval. Exact truth lives in the ledger. |
| L-05 | No centroid without residual. Outliers spawn subfamilies; they are not compression targets. |
| L-06 | No belief promotion without retained contradiction. The Contradiction Graph is not optional. |
| L-07 | No session without working-memory reset. After consolidation, the working buffer clears. |
| L-08 | Temperature and distortion budget are one degree of freedom. Treat as such. |
| L-09 | No feature spine without QA spine. They advance together. |
| L-10 | No architecture without governance twin. Runtime and shadow-control co-evolve. |
| L-11 | No evaluation theater. Non-distinct conditions → identical results → implementation error, not data. |
| L-12 | No widening under unresolved failure modes. Audit and resolve first. |
| L-13 | No substrate claim without empirical foothold. Theory is theory until it survives contact with a benchmark. |
| L-14 | Separate to measure. Compose to run. |
| L-15 | No layered memory without all four layers. SBUF + EPMEM + SMEM + Contradiction Graph. Missing any one is architectural decay. |
| L-16 | Confirmatory and exploratory must be declared before results are observed. HARKing is a process violation. |
| L-17 | Kill criteria are mandatory for confirmatory experiments. |
| L-18 | Null results are data. Suppression is a process violation. |

### §23. Confirmed Isomorphisms

These structural equivalences have been validated and should be probed actively in new domains:

| Domain A | Domain B | Shared structure |
|---|---|---|
| Temperature | Distortion budget | Control centroid tightness |
| IRIS (LLM→formal→LLM) | Forge (heuristic→gate→LLM) | Same dual convergence loop |
| CLS hippocampus | SBUF | Fast/slow memory, same computational structure |
| NEAL R-pipeline | Switchboard L0-L5 | Sequential confidence gates |
| PatternIR radicals | NEAL-CORE radicals | Same abstraction invented twice — confirms correctness |
| TQ2 strata (whole-plane / blockwise) | Local + global invariant decomposition | Task structure determines operator family |
| K2 chain accumulation | Episodic memory consolidation | Structure builds over steps |
| Preregistration | Pre-stated kill criteria in this SOP | Same falsifiability enforcement mechanism |
| MLOps version control | Shadow-doc control layer | Same principle: version everything, audit trail is the record |

---

## Part XI: Project-Specific State

### §24. Project Context (Replace Per Project)

_This section is project-specific. For universal/generic use, leave this as a template and fill in at project start._

**Project name:** `<fill in>`
**One-sentence mission:** `<fill in>`
**Current incumbent baseline (per workstream):** `<fill in>`
**Top priority open seams:** `<fill in>`
**Hard constraints that must survive every session:** `<fill in>`
**Workstream scorecard lines:** `<fill in>`

---

## Part XII: Final Principles

### §25. The Lab's Operating System

This SOP is the operating system, not a checklist. The lab runs on:

> **PROBE → DERIVE → EMBODY → VERIFY → RECURSE**
> inside a persistent shadow-control layer with immutable audit trail,
> with exploratory/confirmatory declared before results are observed,
> with pre-stated kill criteria for every confirmatory experiment,
> with null results recorded as data,
> with deviations logged before analysis,
> with evaluation theater caught by structural distinctness checks,
> with workstream evidence kept separate by default,
> with version control applied to code, data, models, and config,
> with zero-loss extraction for all significant uploads,
> with Loop+ for cross-domain isomorph hunting,
> with explicit uncertainty at every layer,
> and with the hard brake — VERIFY — enforced between EMBODY and RECURSE.
>
> Upload archive → continue is enough to resume.
> That is the goal. That is the standard. That is the lab.
