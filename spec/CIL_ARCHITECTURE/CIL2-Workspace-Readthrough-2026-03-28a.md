# CIL2 Workspace Readthrough — 2026-03-28a
This is the folder/crate-by-crate pass over the multi-crate archive. Status values are operational, not emotional.
| Crate | Status | LOC | Internal Deps | Notes |
|---|---|---:|---|---|
| cil | **Implemented** | 31092 | - | Core exact ledger/container implementation; strong and central, but still one piece of the broader substrate. |
| cil-adaptive | **Implemented** | 964 | cil-core | ΔU/SPA adaptive control seam present and meaningful. |
| cil-audit | **Implemented** | 1176 | cil-core | Robust audit surface (CSVF/FCHL/NFD/merkle) and a clear assurance spine. |
| cil-core | **Implemented** | 4444 | - | Foundational branded/epistemic/resource/domain types; one of the strongest substrate crates. |
| cil-council | **Implemented** | 19287 | cil-core | cil-model | cil-routing | cil-subsystems | Very dense orchestration and audit-compliant deliberation surface; likely a future integration hub. |
| cil-driftd | **Implemented** | 223 | cil | Focused daemon with clear responsibility. |
| cil-ffi | **Implemented** | 780 | cil-adaptive | cil-audit | cil-core | cil-governor | cil-pipeline | cil-taint | Useful bridge for Python integration and orchestration exposure. |
| cil-glaciald | **Partial** | 252 | cil | Useful daemon, but compression-tier policy still looks thinner than the maximal doctrine. |
| cil-governor | **Implemented** | 4428 | cil-core | cil-quantization | Strong control/safety operations layer with OODA/flight rule pressure. |
| cil-model | **Implemented** | 3518 | cil-core | cil-quantization | Substantial model lifecycle and backend surface. |
| cil-pipeline | **Implemented** | 1618 | cil-core | cil-subsystems | cil-taint | Embodies the cognitive pipeline strongly. |
| cil-quantization | **Implemented** | 37168 | cil-core | The densest subsystem; quantization is treated as governed architecture, not tuning fluff. |
| cil-reasoning | **Implemented** | 2386 | cil-core | Hypothesis/CHE/CRA/EBC reasoning seam is real and substantive. |
| cil-retrieval | **Implemented** | 936 | cil-core | Solid retrieval kernel, but still smaller in surface area than doctrine around it. |
| cil-routing | **Implemented** | 838 | cil-core | Routing/bandit seam is clear and connected. |
| cil-subsystems | **Implemented** | 7194 | cil-core | Implements the named subsystem taxonomy and is load-bearing. |
| cil-taint | **Implemented** | 942 | cil-core | One of the clearest “complete” seams in the workspace. |
| cil-tools | **Partial** | 123 | cil | Small CLI/tooling surface; more convenience layer than doctrine center. |
| cilfsd | **Partial** | 1605 | cil | Critical ingestion/index bridge, but obvious TODOs remain in persistence, deletions, and search realism. |
| neal-cil | **Missing** | 32 | - | Placeholder, effectively superseded by the richer crate family and not yet carrying real weight. |
