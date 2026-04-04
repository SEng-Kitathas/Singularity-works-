# Trace Matrix — Singularity Works Forge
_Version: 2026-04-03 · v1.19_

| ID | Requirement / Capability | Status | Priority | Notes |
|---|---|---|---|---|
| SW-001 | Python compile clean | ✅ VERIFIED | P0 | compile=True at v1.19 |
| SW-002 | Good path assurance: green | ✅ VERIFIED | P0 | Good path green at v1.19 |
| SW-003 | Bad path assurance: red + remediated green | ✅ VERIFIED | P0 | Bad/security/execution all red; remediated green |
| SW-004 | Self-audit: 0 fail, 0 residual | ✅ VERIFIED | P0 | 920 pass / 4 warn / 0 fail at v1.19 |
| SW-005 | 38-case assault battery: 38/38 | ✅ VERIFIED | P0 | FP=0 FN=0 this session |
| SW-006 | 8-case protocol battery: 8/8 | ✅ VERIFIED | P0 | FP=0 FN=0 this session |
| SW-007 | SSRF: direct request input to network sink | ✅ VERIFIED | P0 | Caught via gate + IR |
| SW-008 | SSRF: cross-function 1-hop getter | ✅ VERIFIED | P0 | _propagate_cross_function_taint |
| SW-009 | SSRF: cross-function 2-hop chain | ✅ VERIFIED | P0 | Fixed-point converges |
| SW-010 | SSRF: httpx AsyncClient() via WITH statement | ✅ VERIFIED | P0 | WITH-statement client tracking |
| SW-011 | SSRF: urllib.request.urlopen direct | ✅ VERIFIED | P0 | Attribute chain drill-down in SSRF gate |
| SW-012 | SSRF: FP suppression on hardcoded URLs | ✅ VERIFIED | P0 | Taint-returning fn requires request.* source |
| SW-013 | SSRF: FP suppression on allowlist-validated callers | ✅ VERIFIED | P0 | _is_validated() checks urlparse+ALLOWED pattern |
| SW-014 | Auth/session-before-redirect protocol monitor | ✅ VERIFIED | P0 | must_establish_session_before_redirect |
| SW-015 | Auth cookie hardening monitor | ✅ VERIFIED | P0 | must_harden_auth_cookies — secure+httponly+samesite |
| SW-016 | Logout/auth-state clearance monitor | ✅ VERIFIED | P0 | must_clear_auth_state_on_logout |
| SW-017 | Transaction finalization monitor | ✅ VERIFIED | P0 | must_finalize_transaction_after_write |
| SW-018 | Refresh token rotation/revocation monitor | ✅ VERIFIED | P0 | must_rotate_or_revoke_refresh_token |
| SW-019 | Refresh token family integrity monitor | ✅ VERIFIED | P0 | must_preserve_refresh_token_family_integrity |
| SW-020 | Callback state/CSRF validation monitor | ✅ VERIFIED | P0 | must_validate_state_token_before_callback_use |
| SW-021 | OAuth callback silent-abstention fix | ✅ VERIFIED | P0 | OAuth-named fn with exchange_code + no state = red |
| SW-022 | Recovery token protocol monitor | ✅ VERIFIED | P0 | must_validate_and_consume_recovery_token |
| SW-023 | JWT algorithm confusion detection | ✅ IMPLEMENTED | P1 | Strategy registered; battery cases pending |
| SW-024 | HTTP non-TLS detection | ✅ IMPLEMENTED | P1 | Strategy registered; battery cases pending |
| SW-025 | Auth endpoint rate limiting monitor | ✅ IMPLEMENTED | P1 | Runner + seeding registered; battery cases pending |
| SW-026 | seed_genome.json — 37 capsules load clean | ✅ VERIFIED | P0 | GenomeCapsule(**kwargs) no TypeError |
| SW-027 | SMEM budget_weights capsule ordering | ✅ IMPLEMENTED | P1 | bundle_for_task() uses SMEM priors; ordering confirmed changed |
| SW-028 | ContradictionGraph query methods | ✅ IMPLEMENTED | P2 | active_roots, chain, summary — in forge_context.py |
| SW-029 | CIL council IRIS hook | ✅ IMPLEMENTED | P2 | Wired, offline-graceful; live quality unverified |
| SW-030 | Python oracle bridge (sw_oracle.py) | ✅ IMPLEMENTED | P2 | Canonical code mapping; cil-forge gate_runner uses it |
| SW-031 | Goroutine self-scan guard | ✅ VERIFIED | P0 | Docstring pattern defused in genome_gate_factory.py |
| SW-032 | forge_context.py sections/parts bug fix | ❌ OPEN | P0 | NameError on contradiction path; not yet patched |
| SW-033 | auth_rate_limit empirical battery | ❌ OPEN | P0 | Monitor exists; 0 test cases |
| SW-034 | IDOR/ownership protocol monitor | ❌ MISSING | P1 | Next march target per ChatGPT recommendation |
| SW-035 | Polyglot front door (Tree-sitter/SCIP/CPG) | ❌ MISSING | P2 | Architecture locked conceptually; code not started |
| SW-036 | SSRF requirement-selection sensitivity | ⚠️ KNOWN LIMIT | P2 | Generic phrasings can produce false green |
| SW-037 | good_service_issue_only FP | ⚠️ KNOWN LIMIT | P3 | Refresh rotation context-breadth mismatch |
