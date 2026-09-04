# Next Steps — Singularity Works App

Last updated: 2026-09-04 UTC

## P0 — OS/process network egress enforcement Attempt 0
0. Query the R4.4 Global Cross-Project Scar Ledger for relevant prior containment/network/process scars when the live registry is available; inspect provenance and re-derive under current constraints before reuse.
1. Inspect actual Windows/process-launch topology and available enforcement primitives on the current machine.
2. Define the exact protected execution-domain boundary: which Singularity Works child processes/plugins/imported code are denied ambient network access by default.
3. Define the broker/Gate allow path so an approved network consequence requires current Connection Gate authority plus an exact prepared-operation/lifecycle identity.
4. Preserve the complete enforcement Attempt 0 implementation/protocol/tests before first execution.
5. Hostile-test direct raw sockets, subprocess/helper-binary escape, plugin/imported-code escape, DNS, loopback/local service, inherited handles/capabilities and proxy/environment-mediated egress.
6. Unsupported/unknown enforcement state must fail closed for the protected domain.
7. Renderer/recovery processes that do not require network should remain network-denied by default.
8. Manual operator inspection of active egress grants/receipts is required.
9. Do not claim machine-wide firewall control unless that exact boundary is actually proven.
10. Apply the R4.4 complete linear semantic-read gate to every changed readable protocol/code/test/report/evidence artifact before qualification/promotion.

## P0 — enforcement architecture safety
11. Keep credential/token secret storage outside authority metadata; future secrets belong in the Vault boundary.
12. Broker transport submission must recheck current authority; a prepared operation or old ALLOW receipt is not ambient capability.
13. Preserve operation lifecycle distinctions through transport: PREPARED / SUBMITTED / STARTED / COMPLETED_LOCAL / UNKNOWN_OUTCOME / REMOTE_OBSERVED.
14. `UNKNOWN_OUTCOME != SAFE_TO_RETRY`; provider transport later must reconcile rather than blind-retry.
15. `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` remains UNKNOWN/unearned until enforcement evidence exists.

## P0 — semantic admission / RES
16. Keep App RES synchronized whenever the research meaning/frontier changes; RES remains authority NONE.
17. Any readable artifact not fully linearly read remains NOT ADMITTED regardless of hashes/tests.
18. Distinguish enforcement mechanism proof from scope semantics: `ENFORCEMENT_TEST_PASS != ENFORCEMENT_SCOPE_SEMANTICALLY_UNAMBIGUOUS`.

## P1 — canonical semantic bridge product consumption
19. App may consume `singularity_works.semantic_field_bridge` only through explicit bounded interfaces/tests.
20. Do not copy or privately reimplement Core semantic-field logic inside `forge_app/**`.
21. Separately qualify checkpoint `core_contract_version`, `core_currentness_id`, and `semantic_snapshot_id` restoration/currentness semantics before populating those fields.

## P1 — first real provider only after egress enforcement
22. Start with exact GitHub App repo/branch read/push scope only.
23. Admin/delete/force-push unavailable in Singularity Works policy regardless of broader token ceiling.
24. OAuth/PKCE, provider revocation/currentness and secure token storage each receive separate qualification.
25. Provider-native idempotency/reconciliation must map to the qualified operation lifecycle.

## Recovery queue retained
26. Supervisor death after coordinator death before crash receipt.
27. Missing-terminal-receipt reconciliation.
28. Whole descendant-process-tree/job containment.
29. Coordinator exit code vs wrapper exit code.
30. Independent supervisor watchdog/heartbeat.

## Vault / export / GitHome
31. Threat-model Vault before crypto/container selection.
32. Define export receipt + Import Quarantine object model.
33. Define GitHome project/tree substrate and surface Gate/lifecycle state without UI-private authority.

## Cross-strand
34. Main/Core remains owner of canonical semantic extraction/currentness/snapshot meaning and bridge implementation.
35. App source now contains exact qualified Main semantic-field ancestry through merge `b674dbaaf428970c486753168e75847a345eb1c2`.
36. Main/Core and App maintain separate zero-authority RES surfaces and cross-reference rather than silently merging authority domains.

## Current verified baseline
- R4.4 current process carrier SHA `04f3e94efe8c901cc83a12a9c8531be8a9bb350728b8f9eba53db0fd082b3bbc`;
- App local/remote source exact `b674dbaaf428970c486753168e75847a345eb1c2`, clean;
- exact merge parents `[328249429cc6e86e15db9797bd58eff5fabc5a2d, a7b4511734b1a1e507230308e75b31175aef4c4a]`;
- forward-sync qualification receipt SHA `ef9cbb12293a0077e143ee8c991a466bc23019a303221a13be85bf3cc46c604e`;
- remote closure SHA `8119f920e0c8e1c34c85ebe8e6ab5d01cbf32e5ab01309a8ede68e40145fa2ec`;
- fresh remote compile PASS / semantic 8/8 / App 94/94 / full verify_build PASS;
- canonical bridge schema `singularity-works.semantic-field-bridge/0.1`;
- current LKG generation 11 `checkpoint-app-live-0011-b674dbaaf428`, source MATCH/NORMAL;
- gen11 evidence `state/live_resume_session_0011.json` SHA `817daa41119e499c3bc8cc978d0ea625be4598ef6a8263f3acf5cf84392fa3e9`;
- evidence Attempt `attempt-live-resume-session-0011-lkg`, exact blob same SHA;
- Attempt Store 102 blobs / 102 attempts / 169 events, integrity ok, WAL/FULL.

## Closed this cycle
The early Main->App forward-sync gate is closed for qualified Main `a7b4511...` / App merge `b674dba...`.
Generation 10 remains historical evidence and source-stale SAFE_ONLY; generation 11 is current LKG.

## Control-plane follow-up
A new normal `pcmmad/project-control` checkpoint must absorb the forward-sync/gen11 continuity state. Last independently verified durable anchor before this mutation remains `cadd64cde4428719b1f3ff6981a4224ea4e22fb8`.
