# Intent–Constraint–Frontier Continuity Standard — ICF-CS v1.0

Status: PROJECT-AGNOSTIC CONTINUITY / REHYDRATION STANDARD
Process authority: continuity/cold-start pattern under the current canonical process SOP; no domain/product/source authority by inclusion.
Current process parent for this project: RAHL Engineering Canonical SOP R4.4.

## Purpose
ICF-CS prevents fresh-instance rollback by separating continuity information that ages at different rates.

A project may preserve accurate philosophy while carrying stale work status. A task queue may preserve current work while forgetting why the project exists. A donor, handoff, or polished historical artifact may also be easier to discover than the current authority surface.

ICF-CS prevents those failure modes by making direction, constraints, and current frontier separately explicit and discoverable.

## Core model
### 1. Intent
Intent states what the project is ultimately trying to become, why it exists, and what success means.

Intent is slow-changing and owner-governed. It is not inferred from whichever task or artifact is newest.

Intent should answer:
- What is this project ultimately for?
- What kind of system/product/research outcome is being pursued?
- What must remain true about the project even when the immediate task changes?
- What does success look like at the project level?

### 2. Constraints
Constraints are the load-bearing decisions, authority ceilings, sequencing laws, anti-regressions, scars, qualification rules, and ownership boundaries that must not be casually reopened.

Constraints may evolve, but only through explicit supersession, promotion/demotion, or new evidence. They are not equivalent to remembered preferences or old prose.

Constraints should answer:
- What must not be silently violated?
- Which ownership/authority boundaries govern mutation?
- Which qualification and readback gates are mandatory?
- Which scars exist specifically to prevent known regressions?
- Which sequence/order dependencies are load-bearing?

### 3. Frontier
Frontier states what is actually earned, provisional, blocked, deferred, open, and next **right now**.

Frontier is intentionally fast-changing. It must be rewritten/superseded as reality moves rather than being preserved as eternal doctrine.

Frontier should answer:
- What is verified now?
- What remains provisional/UNKNOWN?
- What is blocked and by what gate?
- What is explicitly deferred?
- What is the immediate highest-value discriminator or next action?

## Core separation law
`DIRECTION != CONSTRAINTS != FRONTIER != HISTORY`

Corollaries:
- Intent is not a task queue.
- Constraints are not historical narration.
- Frontier is not doctrine merely because it is current.
- History is not current ingress merely because it is detailed.
- A single artifact should not be forced to perform all four jobs.

## Required current-ingress surfaces
A conforming project SHOULD provide:
1. a reusable ICF-CS standard definition;
2. a current project Commander’s Intent / Intent–Constraints–Frontier instance;
3. a short discoverable current-ingress pointer;
4. Current State / Next Steps / Doctrine Snapshot / Revisit Ledger / Trace Matrix;
5. Live Shadow;
6. Design Thread Stream;
7. Research Epistemic Shadow where active research meaning exists.

The pointer must be easy to find without semantic archaeology.

Recommended filenames:
- `state/doctrine_snapshot/INTENT_CONSTRAINT_FRONTIER_CONTINUITY_STANDARD.md`
- `state/doctrine_snapshot/PROJECT_COMMANDERS_INTENT_CURRENT.md`
- `checkpoints/PROJECT_INTENT_CURRENT.md`

Names may differ when a stronger project-local contract requires it, but discoverability and role separation must remain.

## Standard cold-start grammar
For a fresh thread, fresh model instance, recovery re-entry, or context roll:

`CURRENT STATE -> ICF-CS -> R4.4 + NEXT/DOCTRINE/REVISIT/TRACE -> LIVE SHADOW -> DTS -> LIVE READBACK BEFORE MUTATION`

Interpretation:
1. **CURRENT STATE** establishes the best current operational baseline.
2. **ICF-CS instance** restores project direction, load-bearing constraints, and the present frontier without treating history as authority.
3. **Canonical process + state instruments** restore qualification rules, open seams, traceability, and next-action discipline.
4. **LIVE SHADOW** restores the minimum active state.
5. **DTS** restores chronology/forensic lineage only after current ingress is known.
6. **LIVE READBACK BEFORE MUTATION** re-verifies consequence-bearing current facts in the live environment.

The exact current canonical process version is project/current-state data. The grammar must use the live canonical process rather than hard-coding an obsolete SOP version.

## Conflict grammar
If materially load-bearing surfaces disagree:

`CONFLICT -> RECOVERY/AUDIT -> LOCALIZE -> REPAIR/SUPERSEDE -> READBACK -> RESUME`

Rules:
- Do not smooth contradictions into a coherent narrative.
- Do not choose the newest timestamp by default.
- Localize whether the conflict is Intent, Constraint, Frontier, History, or pointer/currentness drift.
- Preserve historical truth while repairing current authority.
- Mutation resumes only after consequence-bearing readback.

## Authority/currentness laws
`HISTORICAL_HANDOFF != CURRENT_INGRESS`

`DONOR != AUTHORITY`

`RECENT_TIMESTAMP != CURRENT_AUTHORITY`

`STALE_GREEN != CURRENT_EVIDENCE`

`REMEMBERED_POINTER != CURRENT_STATE_EVIDENCE`

`CONTINUITY != PROOF`

`CURRENT_POINTER != CURRENT_FACT_UNTIL_READBACK`

`INTENT != MUTATION_PERMISSION`

`FRONTIER != DOCTRINE_AUTHORITY`

## Freshness discipline
Intent, Constraints, Frontier, and History age differently.

A conforming ICF instance SHALL therefore identify:
- which statements are slow-changing owner/governing intent;
- which statements are load-bearing constraints and how they may be superseded;
- which statements are current frontier facts/pointers requiring live currentness verification;
- which statements are historical lineage only.

A fresh timestamp on an old handoff does not make its content current.
A copied artifact does not gain authority from its new storage location.

## Discoverable-pointer rule
A project SHALL expose a bounded current-ingress pointer that identifies the current ICF instance and the immediate read order.

The pointer is navigation, not proof.
It should contain:
- project identity;
- current ICF instance path/hash when available;
- current process-SOP pointer/version;
- Current State path;
- Live Shadow path;
- exact cold-start order;
- warning that live currentness readback is required before mutation.

The pointer should not become a second full handoff or duplicate the entire project state.

## Historical/donor discipline
Historical handoffs, donor archives, archaeology, prior project states, model outputs, and imported research may inform recovery or hypothesis generation but do not become project direction authority by presence.

`HISTORICAL_HANDOFF != CURRENT_INGRESS`

`DONOR != AUTHORITY`

When a historical artifact remains useful, mark its role explicitly:
- history;
- donor;
- evidence;
- provenance;
- superseded constraint;
- retired frontier;
- or current authority if independently re-promoted.

## Continuity-surface responsibilities
- **Current State:** best current operational facts and verified/provisional boundary.
- **ICF instance:** direction + load-bearing constraints + present frontier.
- **Doctrine Snapshot:** governing laws/authority boundaries and qualified doctrine.
- **Next Steps:** executable queue ordered by current dependencies.
- **Revisit Ledger:** unresolved, questioned, superseded, or conditional claims.
- **Trace Matrix:** evidence/claim/qualification lineage.
- **Live Shadow:** minimum high-fidelity active state for immediate re-entry.
- **DTS:** chronological recovery spine/history.
- **RES:** interpreted research frontier with authority NONE_BY_CONTENT unless separately promoted.

No one surface should silently impersonate another.

## Mutation discipline
Before consequential mutation after re-entry:
1. locate current ingress;
2. read Intent / Constraints / Frontier;
3. reconcile Current/Next/Doctrine/Revisit/Trace/Live/DTS as needed;
4. identify remembered pointers that require live verification;
5. perform live currentness readback;
6. only then mutate;
7. read back consequences;
8. update Frontier and continuity if load-bearing state changed.

## Benchmark / evaluation extension
The same authority/currentness failure appears in steering data and benchmark corpora.

Required distinctions:

`EXPECTED_LABEL != PROMPT_CONTENT`

`BENCHMARK_ITEM != DOCTRINE_AUTHORITY`

`FORMAT_FAILURE != SEMANTIC_FAILURE`

`SEMANTIC_AGREEMENT != AUTHORITY_FIDELITY`

Interpretation:
- Expected answers/labels must not leak into prompts or candidate-visible content.
- Benchmark examples do not become doctrine merely because they are labeled correct.
- Syntax/schema/format failure must be measured separately from semantic reasoning failure.
- A model may semantically agree with a proposition while still violating the authority/currentness boundary that governs whether the proposition may be acted on.

Evaluation items that encode authority/currentness claims should carry provenance, scope, and currentness just like continuity prose.

## Anti-regression requirements
A conforming project should be able to reject at least these hostile conditions:
- stale historical handoff presented as current ingress;
- donor project prose presented as current project authority;
- remembered commit/path/endpoint treated as current without readback;
- green historical result presented as current evidence after source/environment drift;
- expected benchmark answer leaked into prompt content;
- benchmark label contradicts the project’s earned authority/currentness doctrine;
- Frontier text silently promoted into immutable doctrine;
- Intent text used as direct mutation permission.

## Adoption and supersession
ICF-CS is additive to the canonical process SOP and project-local authority topology.

It does not replace:
- the canonical process SOP;
- project-specific doctrine;
- source/release qualification;
- recovery qualification;
- evidence/readback requirements.

A later ICF-CS revision may supersede this standard only through explicit adoption with preserved provenance and readback.

`ICF_CS != PROJECT_DOMAIN_AUTHORITY`

`ICF_CS != SUBSTITUTE_FOR_LIVE_READBACK`

`ICF_CS != SUBSTITUTE_FOR_CANONICAL_PROCESS`
