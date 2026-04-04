# Next Steps — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

### Immediate
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P0 | Fix forge_context.py sections/parts bug | NameError on contradiction path is a real defect; self-audit blind spot confirmed by ChatGPT live run | None — fix is trivial str replacement | verify_build passes, contradiction path runs without NameError |
| P0 | Add auth_rate_limit battery cases (3 cases: no-rate-limit, decorator-present, library-import) | Monitor runner exists, recovery seeding exists, but zero battery evidence | Monitor already registered in _MONITOR_RUNNERS | 3 cases pass with correct red/green verdict |
| P0 | Run full 46+3 battery after above fixes | Confirm no regressions | P0 fixes above | 49/49 FP=0 FN=0 |
| P0 | Commit v1.20 + push to GitHub | Lock the clean state | Battery passes | git tag v1.20, pushed |

### Near-term
| Priority | Action | Why it matters | Dependency / trigger | Done when |
|---|---|---|---|---|
| P1 | IDOR/ownership protocol monitor | ChatGPT's explicit next march target; catches "can reach" vs "allowed to touch this object" auth gap | v1.20 clean | monitor fires on bad IDOR, passes on proper ownership check |
| P1 | Refine good_service_issue_only FP | Refresh-rotation monitor fires when no request-bound token present; context-breadth mismatch | Not blocking | rotation seam only fires when refresh_token read from request confirmed |
| P1 | JWT algo confusion test cases (beyond unit test) | Strategy written, needs battery integration | v1.20 clean | 2 cases in battery: no-algorithms catches, explicit-algorithms passes |
| P1 | HTTP non-TLS test cases | Same as above | v1.20 clean | 2 cases: hardcoded http:// catches, https:// passes |
| P2 | forge_context.py: audit full memory stack for similar runtime-only bugs | sections/parts found by external run; may have siblings | P0 bug fixed | self-audit passes + manual contradiction path test run |

### Waiting on evidence
| Evidence needed | Why blocked | Source or acquisition path | Earliest revisit trigger |
|---|---|---|---|
| IDOR pattern corpus | Need real/synthetic code samples showing ownership check absence vs presence | Write synthetic cases; consult OWASP IDOR guidance | P1 work begins |
| Behavioral reliability data for GPT under natural language | GPT may choose wrong artifact, wrong mode, wrong operation | Run actual GPT sessions with low-supervision prompts | Post-v1.20 |
| Tree-sitter/SCIP/CPG front door implementation | Polyglot semantic layer; no Python source yet | ChatGPT recommended; arXiv/GitHub for SCIP bindings | After IDOR + behavioral pass |

### Waiting on embodiment / verification
| Pending embodiment or check | Why blocked | Dependency | Done when |
|---|---|---|---|
| Auth rate-limit battery verification | Monitor runner exists but untested end-to-end | P0 fix session | 3 cases pass |
| forge_context.py contradiction path runtime test | Bug identified, not patched in current codebase | P0 fix session | contradiction-case test runs to completion |
| SSRF requirement-selection sensitivity root cause | Generic phrasing produces false green; routing vs detection issue | Deep-dive into orchestration bundle selection | Requirement phrasing no longer affects SSRF verdict |

### Demotion / replay candidates
| Candidate | Why it may need replay or demotion | What would decide it | Current status |
|---|---|---|---|
| good_service_issue_only in refresh battery | Refresh-rotation seam produces FP when no request-bound token — not a correct red | Battery case that confirms FP vs correct green | KNOWN GAP, low priority |
| genome capsule `trust_boundary_validation` dominance (21/37) | 57% concentration may mean under-coverage of other attack classes | New capsule additions beyond trust-boundary | Active awareness, no demotion yet |
| forge_context.py memory stack hardening claims | compile_context contradiction path untested | Run contradiction case through full pipeline | PROVISIONAL until tested |
