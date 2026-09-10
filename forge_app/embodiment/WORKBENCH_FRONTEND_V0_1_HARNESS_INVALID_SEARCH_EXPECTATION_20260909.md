# Forge Workbench Frontend v0.1 — First Test HARNESS_INVALID — 2026-09-09

Status: **FIRST EXECUTION PRESERVED / NOT ADMITTED / TEST-ONLY REPAIR PERMITTED**

Attempt-0 source commit: `f14ed1dd677bfabdb93c8a6b18fdcf6c14e404b9`  
Parent App commit: `43aa7feac7e8a15828116bd700b644560714496d`  
Control at launch: `d9b7c5e8b1854b705f134a2d6e1dca6acc9a1a47` / CHECKPOINT `b8333e3758cc98edb14c1302744bc3ef44210678dd1122e27648c51def6b588e`  
Execution job: `job-652321b01d46`  
Idempotency key: `attempt-forge-workbench-frontend-v0-1-f14ed1dd-tests-first`  
Return code: `1`  
Observed suite: **10 PASS / 1 FAIL / 11 total**  
Preserved first-result SHA: `ad36a6145abd809fe0d72abd07d183aafa3abec73df6f731759f36a82cf6bb1c`

## Exact failure
`test_lenses_and_search_only_filter_existing_entities` searched for `request.user.name` and expected the route entity to remain visible.

That string exists only inside the fixture fact's `object_value`. The frozen Workbench v0.1 contract explicitly defines search over existing presentation identity strings, source path, fact **predicates**, and UNKNOWN question/reason text. The implementation follows that contract and deliberately does not search fact object payloads in v0.1.

Therefore the failure is classified:

**HARNESS_INVALID_CONTRACT_MISMATCH**

It is not evidence that the Workbench search implementation violated its frozen contract.

## Permitted v0.1.1 repair
Change only the failing test query from the unsupported fact-object string `request.user.name` to the existing fact predicate `reads_value`.

No production implementation change.  
No Workbench contract semantic change.  
No widening of search semantics.  
No source-materialization authority.  
No same-Attempt replay.

The repaired suite must be preserved in a new App commit before execution and executed under a new immutable Attempt identity through the qualified idempotent submission rail.

`HARNESS_INVALID != IMPLEMENTATION_FAILURE`  
`TEST_REPAIR != CONTRACT_WIDENING`  
`ATTEMPT_0_REMAINS_IMMUTABLE`
