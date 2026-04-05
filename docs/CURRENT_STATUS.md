# Singularity Works — Current Status

**Version:** v1.29  
**Date:** 2026-04-04  
**Gate score:** 53/53 FP=0 FN=0  
**Self-audit:** 1418 pass / 42 warn / 7 fail (known — see below)

---

## What's Live

| Component | State |
|---|---|
| Gate fabric | 53 gates, 0 FP, 0 FN, ~2.3s |
| Genome-gate coupling | LIVE — 7 base + genome-derived gates per evaluation |
| LBE Universal Reasoner | LIVE — 7 axioms, 17-language detection, 30+ sources, 28 sinks |
| LBE Blueprint | LIVE — RED/YELLOW/GREEN/PURPLE flow maps + ★ min replacement |
| StarMap topology | LIVE — Fiedler λ₂, integrity, interference, curvature, T1-T4 tier |
| MCP server | 8 tools: forge_run_battery, forge_get_assurance, forge_run_assurance_on_file, forge_get_open_seams, forge_get_live_shadow, forge_get_escalation, forge_get_blueprint, forge_commit_verified |
| FactBus | LIVE — typed append-only provenance blackboard |
| Forge HUD | v2.0 — three-wing operator cockpit, WebSocket event stream, file watcher, read-only annotated file view |

---

## Self-Audit Notes

### 7 FAILs — `language_front_door.py` (known, not a real defect)

The genome-derived gates fire on the **detection regex strings embedded in
`language_front_door.py`**. For example, `"ObjectInputStream"` appears as a
regex pattern in a detection list — the genome gate treats it as actual unsafe
deserialization code. This is a self-referential false positive: the forge's
detection library contains the same strings it's trained to find.

**Fix path:** Annotate detection-string regions with a suppression marker so
genome gates skip regex/pattern literal sections. Not blocking — these are
not real violations in the forge's own production logic.

### 42 WARNs — `runtime.monitor_seed` (expected)

Internal forge modules don't expose HTTP endpoints or rate-limit surfaces. The
monitor seed derivation correctly warns that no monitor seeds were found, because
these files are not network-facing artifacts. This is correct behavior.

### `conformance.simplification` WARNs

Several files have complex control nesting (depth ≥ 7) or long lines. These
are flagged but not fatal. `lbe_pilot.py`, `orchestration.py`, `recovery.py`,
`genome_gate_factory.py` are the primary candidates for future refactor.

---

## Next Honest Weaknesses (from surviving flags)

1. **Genome gate suppression for detection literal regions** — fix the 7 self-referential FAILs
2. **Fixed-point propagation loop** — current enforcement is single-pass; two-hop derivation requires iteration
3. **Trust chain directionality** — `trust_boundary_crossed` is boolean, needs source→transform→sink directed model
4. **Assurance graph warrant layer** — claim tree exists but doesn't encode semantic reason (GSN-style)
5. **Recovery layer genome coupling** — recovery still uses keyword heuristics; should instantiate capsule protocols

---

## Forge HUD

**Files:** `forge_hud.html` + `forge_hud_server.py` (root of repo)

```bash
pip install flask flask-cors flask-socketio watchdog
python3 forge_hud_server.py
# Open forge_hud.html in browser
```

**Architecture:**
- Operator commands → Smart Canvas (bottom dock)
- Claude Code builds → MCP tools fire on every file write
- Forge analyzes continuously → HUD shows results live via WebSocket
- Center panel: READ-ONLY annotated file view — tainted lines highlighted, inline gate annotations
- Center stream: live MCP event log per pipeline phase
- File watcher: auto-analyzes any changed file in watched project dir
