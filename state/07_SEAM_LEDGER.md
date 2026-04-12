# Singularity Works Seam Ledger

**Status:** Active reference surface for recursive seam closure  
**Scope:** `repo/singularity_works` live code surface  
**Use rule:** After each seam closure, re-open this ledger, update the seam status, note downstream seams changed, and only then recurse.

---

## Authority stack for this ledger
1. PCMMAD runtime law and immutable law stack
2. Forge unified standards and anti-pattern-to-invariant refactor protocol
3. Forge one-page scoring sheet
4. CODEX OMEGA as code-doctrine source, not as replacement for the control constitution

Operative cycle: **PROBE → DERIVE → VERIFY → EMBODY → RECURSE**

---

## Top-level seam map

### M1 — Split truth between workshop ledger and CILNX continuity
- **Status:** PARTIAL
- **Meaning:** Workshop operational truth still derives primarily from `EvidenceLedger` / `evidence.jsonl` while continuity authority is moving toward CILNX.
- **Current expression:** Cockpit session persistence and Forge evidence export ride the CILNX line, but workshop rollups and summaries are still ledger-first.
- **Downstream seams now:**
  - M1.1 rollup asymmetry
  - M1.2 replay asymmetry
  - M1.3 audit bifurcation
  - M1.4 promotion ambiguity
- **If corrected, new seams created:**
  - M1.a migration/backfill from JSONL
  - M1.b CILNX query/read model
  - M1.c HUD/source-of-truth retarget
  - M1.d projection/index/cache policy
- **Closure evidence required:** summary/readback path and workshop rollups no longer depend on JSONL as canonical truth.

### M2 — Canonical naming still split between Cockpit and vessel
- **Status:** CLOSED
- **Meaning:** Architecture story says Cockpit, implementation substrate still largely lives in `vessel.py` with wrappers.
- **Downstream seams now:**
  - M2.1 import drift
  - M2.2 doctrine/code mismatch
  - M2.3 maintenance/search tax
  - M2.4 semantic mismatch
- **If corrected, new seams created:**
  - M2.a internal rename blast radius
  - M2.b historical continuity rename migration
  - M2.c wrapper retirement policy
- **Closure evidence required:** canonical internal module path uses Cockpit language; wrappers become compatibility-only or retire.

### M3 — CILNX is canonical by role but still bridge-shaped
- **Status:** CLOSED
- **Meaning:** `cilnx_bridge.py` dynamically mounts the external CILNX scaffold instead of exposing a first-class native continuity subsystem.
- **Downstream seams now:**
  - M3.1 external path brittleness
  - M3.2 dynamic import dependency
  - M3.3 native abstraction gap
  - M3.4 testability friction
- **If corrected, new seams created:**
  - M3.a vendor/promote/pin decision
  - M3.b integrity and version pinning
  - M3.c canonical internal continuity API
- **Closure evidence required:** continuity API no longer depends on ad hoc bridge-only helpers and the external scaffold path is governed explicitly.

### M4 — Runtime integration concentration
- **Status:** OPEN
- **Meaning:** `runtime.py` coordinates summary, HUD, boot, persistence, continuity emission, evidence export, and anchor/front-end evaluation.
- **Downstream seams now:**
  - M4.1 high blast radius
  - M4.2 summary/test entanglement
  - M4.3 small-change regression risk
- **If corrected, new seams created:**
  - M4.a snapshot composer boundary
  - M4.b continuity emission boundary
  - M4.c entry-point choreography boundary
- **Closure evidence required:** runtime delegates composition/emission/rendering through explicit typed boundaries.

### M5 — Workshop orchestration concentration
- **Status:** OPEN
- **Meaning:** `orchestration.py` remains the major god-node for Forge analysis/build flow.
- **Downstream seams now:**
  - M5.1 coupling accumulation
  - M5.2 evolution pressure through one hub
  - M5.3 audit locality weakness
- **If corrected, new seams created:**
  - M5.a phase decomposition by PDVER
  - M5.b shared state ownership model
  - M5.c event-bus / typed-flow design
- **Closure evidence required:** phase responsibilities become more orthogonal without reducing verification truth.

---

## Meso seam map

### S1 — Evidence subsystem remains ledger-first
- **Status:** PARTIAL
- **Files:** `evidence_ledger.py`, `orchestration.py`, `runtime.py`
- **Meaning:** typed payload families still persist through a JSONL-led read model.
- **Creates:** payload typing seam, read amplification seam, projection duplication seam.

### S2 — Facts / Evidence / CILNX are adjacent not singular
- **Status:** OPEN
- **Files:** `facts.py`, `evidence_ledger.py`, `cilnx_bridge.py`
- **Meaning:** one semantic event can exist as typed fact, ledger record, and continuity export.
- **Creates:** ownership drift, query ambiguity, projection duplication.

### S3 — Kerr/HUD substrate mostly converged but lineage remnants remain
- **Status:** PARTIAL
- **Files:** `ergo_kerr.py`, `ergo_boot.py`, `ergo_audio.py`, `hud.py`, `kerr_ascii.py`, `hud_theme.py`
- **Meaning:** live substrate is real, but repo still contains alternative renderer/theme lineage.
- **Creates:** regression risk, canonical renderer ambiguity.

### S4 — HUD snapshot inflation
- **Status:** OPEN
- **Files:** `hud.py`
- **Meaning:** `HudSnapshot` is becoming the god read-model for many subsystems.
- **Creates:** ownership ambiguity, visibility-budget competition, composition pressure.

### S5 — Operator truth can overflow visibility budget
- **Status:** OPEN
- **Files:** `hud.py`
- **Meaning:** critical truths can be internally present but visually crowded out.
- **Creates:** visibility hierarchy seam, paging/mode seam.

### S6 — Dry-plan truth vs live-launch truth
- **Status:** OPEN
- **Files:** `vessel.py`, `runtime.py`
- **Meaning:** normal HUD path surfaces dry receipts rather than full live launch truth.
- **Creates:** operator realism seam, launch-mode policy seam.

### S7 — Windows-first platform coupling
- **Status:** OPEN
- **Files:** `window_anchor.py`, `ergo_audio.py`, `vessel.py`
- **Meaning:** front-end shell remains operationally Windows-native.
- **Creates:** portability and degraded-capability policy seams.

### S8 — Hardcoded external CILNX location knowledge
- **Status:** OPEN
- **Files:** `cilnx_bridge.py`
- **Meaning:** canonical CILNX discovery is machine/path specific.
- **Creates:** portability, upgrade, integrity, and override seams.

### S9 — LBE family not singular
- **Status:** PARTIAL
- **Files:** `lbe_generic.py`, `lbe_pilot.py`, `lbe_universal.py`, `lbe_blueprint.py`
- **Meaning:** multiple LBE generations remain in the live repo.
- **Creates:** canonical LBE ambiguity and lineage-residue drift.

### S10 — Detector/rule accretion hotspot
- **Status:** OPEN
- **Files:** `genome_gate_factory.py`
- **Meaning:** detector density and dict-heavy rule construction make this a maintenance/provenance hotspot.
- **Creates:** maintainability, false-positive governance, detector provenance seams.

---

## Micro seam map

### μ1 — Soft payload boundary in evidence records
- **Status:** OPEN
- **Files:** `evidence_ledger.py`
- **Meaning:** typed payload families exist, but `payload` remains a soft dict boundary.

### μ2 — `RunContext.metadata` as soft escape hatch
- **Status:** OPEN
- **Files:** `models.py`
- **Meaning:** untyped metadata can bypass stricter context evolution.

### μ3 — Compatibility wrappers remain live
- **Status:** CLOSED
- **Files:** `claude_vessel.py`, `forge_doctor.py`, `cockpit.py`
- **Meaning:** wrapper presence signals canonical naming/substrate is not singular.

### μ4 — Orphan / low-inbound capability islands
- **Status:** OPEN
- **Files:** `kerr_ascii.py`, `hud_theme.py`, `lbe_generic.py`, `local_model_adapter.py`, `sw_oracle.py`, `forge_mcp_server.py`, `util.py`
- **Meaning:** either lineage residue or unintegrated capability.

### μ5 — Hardcoded path + dynamic import in CILNX bridge
- **Status:** OPEN
- **Files:** `cilnx_bridge.py`
- **Meaning:** brittle continuity ingress boundary.

### μ6 — Summary path still ledger-first
- **Status:** OPEN
- **Files:** `runtime.py`
- **Meaning:** exact local expression of M1.

### μ7 — Forge context not harmonized with CILNX continuity
- **Status:** OPEN
- **Files:** `forge_context.py`
- **Meaning:** another memory/continuity substrate exists beside the new canonical line.

### μ8 — Runtime/HUD event vocabulary partly stringly
- **Status:** CLOSED
- **Files:** `runtime.py`, `hud.py`
- **Meaning:** typed state exists, but some event surfaces remain string protocols.

---

## Reference rule after each seam closure
For every seam closure pass:
1. update the seam status (`OPEN` → `PARTIAL` or `CLOSED`)
2. write the exact verification anchors used
3. note which downstream seams disappeared, narrowed, or were created
4. rescore the relevant Forge one-page dimensions
5. recurse only on the next real seam

## Latest closure notes
- M2 narrowed: canonical internal runtime promoted to `cockpit_runtime.py`; `vessel.py` reduced to compatibility wrapper.
- M3 narrowed: CILNX discovery now prefers environment/discovery search over machine-specific absolute paths, though dynamic external mounting remains.
- μ8 closed: runtime/HUD event surfaces now use `HudEventRecord` rather than raw string protocols.
- M1 narrowed: EvidenceLedger now writes canonical records to the CILNX continuity line while mirroring the legacy ledger path for compatibility.
- M2 closed: compatibility wrapper files removed; canonical internal module path is now `cockpit_runtime.py`.
- μ3 closed: `vessel.py`, `claude_vessel.py`, and `forge_doctor.py` wrappers were retired from the live package surface.
- S3 narrowed: retired `kerr_ascii.py` and `hud_theme.py` as non-canonical renderer/theme remnants.
- S9 narrowed: retired `lbe_generic.py` from the live surface to reduce multi-lineage ambiguity.
- μ4 narrowed: removed zero-inbound capability islands `local_model_adapter.py`, `sw_oracle.py`, and `util.py`.

- M3 closed: runtime continuity now uses internalized `cilnx_ref_v06.py` instead of dynamic external python-ref mounting.
- S1 narrowed: Evidence ledger now writes to CILNX-backed continuity and has payload/query/rollup helper separation.
- S2 narrowed: fact payload/codecs extracted from FactBus body into `facts_payloads.py`.
- S10 narrowed: MCP and bounty helper/spec surfaces extracted from god-nodes.
- S1 narrowed again: evidence rollup logic extracted to `evidence_rollups.py`, reducing `evidence_ledger.py` concentration.
