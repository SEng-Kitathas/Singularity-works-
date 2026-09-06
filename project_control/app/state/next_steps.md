# Next Steps — Singularity Works App

Last updated: 2026-09-06 UTC

## Historical pre-official ICF-CS durable continuity publication — CLOSED
- Published `pcmmad/project-control@63f7a74f47be4179b5871fd7ff9da819b54e3ab9` from exact parent `cb8d01c5e635347e038b4dffea49387945aea72d`.
- Frozen CHECKPOINT `500d7c167ff5d27e6287edf675d7bbc06a91b5a7c169ffa44df753e6af6bb049`, verifier PASS 96, independent remote/fresh-clone exact.
- Closure receipt `e515beb3f00da247a979c83a4c0f80dc926d47f72315026fc4cedb3755c263ef`.
- Post-push receipt/pointer delta waits for the next normal checkpoint.


## Immediate P0 — ICF-CS v1.1 + Gen12 durable control refresh
1. Publish exact v1.1 payload `f6f4ab2bafdb0ef2a7db1622a00462990baf980284d5b33827807caea1d41f63`, detached receipt `418346ed6373887b5b924e71ca2bf4b83effad20b7269ab40607f5d2750b970c`, standard `62be845da364ae81f59b6320c9b34b136236bf5be8aa8036018da48efcb754f4`, machine `d67726aeb402c280770eeaf314068ed7a1330beb21167d9d6d9b7c4674425bb0`, qualification `7d20ed708adb4f7ee147b56da41deac77146b56fc85bd769be3a6d240b3e2029`, epoch profile `733b799815abdb4b1ff735635f7928953c12944ece579365b5aae138d90f90f8` and v1.0 demotion receipt `3225fd952d704d31047ffdf01bffbc0968e4428357342ccb8ce5094ae8385057` on both control strands.
2. Publish current Commander `95ff8a58543c8aa2a2f20eb98cca47a30c3b64a5e8823c5f84edd3ad25cc9761` and ingress pointer `7fc1675989ec806095fbc250c9d6c6adc213c7af3ca13dc0f1f515fc44f290b3`.
3. Record live public Main `287c0bad0e9b3fef3002b91702e86b410cada4ce` while preserving semantic Core anchor `a7b4511734b1a1e507230308e75b31175aef4c4a`.
4. Record App source `e9b81750db265a467187c61962ffab3cff98d4fe` and Gen12 `checkpoint-app-live-0012-e9b81750db26` MATCH/NORMAL; Gen11 historical/source-stale.
5. Preserve predecessor control `63f7a74f47be4179b5871fd7ff9da819b54e3ab9` / CHECKPOINT `500d7c167ff5d27e6287edf675d7bbc06a91b5a7c169ffa44df753e6af6bb049` as prior verified generation.
6. Complete semantic read of all changed readable control representations; verify manifest/privacy/diff/staged hashes and exact sealed binaries.
7. Non-force push only after live remote race check; require independent ref + fresh-clone verifier/readback.
8. After durable readback, execute exact frozen D0-D3 Attempt 0 without editing first.

## P0 — OS/process network egress enforcement Attempt 0
0. Query the R4.4 Global Cross-Project Scar Ledger for relevant prior containment/network/process scars when the live registry is available; inspect provenance and re-derive under current constraints before reuse.
1. Inspect actual Windows/process-launch topology and available enforcement primitives on the current machine.
2. Define the exact protected execution-domain boundary: which Singularity Works child processes/plugins/imported code are denied ambient network access by default.
3. Define the broker/Gate allow path so an approved network consequence requires current Connection Gate authority plus an exact prepared-operation/lifecycle identity.
4. Attempt 0 is already preserved; after successor control readback, execute exact frozen D0-D3 without editing first.
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
- App local/remote source exact `e9b81750db265a467187c61962ffab3cff98d4fe`, clean; Attempt 0 preserved/unexecuted;
- exact merge parents `[328249429cc6e86e15db9797bd58eff5fabc5a2d, a7b4511734b1a1e507230308e75b31175aef4c4a]`;
- forward-sync qualification receipt SHA `ef9cbb12293a0077e143ee8c991a466bc23019a303221a13be85bf3cc46c604e`;
- remote closure SHA `8119f920e0c8e1c34c85ebe8e6ab5d01cbf32e5ab01309a8ede68e40145fa2ec`;
- fresh remote compile PASS / semantic 8/8 / App 94/94 / full verify_build PASS;
- canonical bridge schema `singularity-works.semantic-field-bridge/0.1`;
- current LKG generation 12 `checkpoint-app-live-0012-e9b81750db26`, source MATCH/NORMAL; Gen11 historical/source-stale;
- Gen12 evidence `state/live_resume_session_0012.json` SHA `aeff0db397135d8f227f11e17c1b7b939235b6ae11ee2ae97053246d9d605e0a`;
- evidence Attempt `attempt-live-resume-session-0012-lkg`, exact blob same SHA;
- Attempt Store 104 blobs / 104 attempts / 175 events, integrity ok, WAL/FULL.

## Closed this cycle
The early Main->App forward-sync gate is closed for qualified Main `a7b4511...` / App merge `b674dba...`.
Generation 10 and Gen11 remain historical; Gen11 is source-stale against current App. Generation 12 is current LKG/source MATCH/NORMAL.

## Control-plane follow-up
Current durable predecessor ICF/R4.4/gen11 control is `pcmmad/project-control@63f7a74f47be4179b5871fd7ff9da819b54e3ab9`, CHECKPOINT `500d7c167ff5d27e6287edf675d7bbc06a91b5a7c169ffa44df753e6af6bb049`, verifier PASS 96, fresh clone exact/clean. Previous `cb8d01c5...` remains historical. Fixed-point post-push receipt/pointer state waits for the next normal checkpoint.

## Historical ICF-CS v1.0 adoption — 2026-09-05
At that historical v1.0 generation, ICF durability was the prerequisite ahead of egress Attempt 0; the current prerequisite is v1.1/source/Gen12 successor control publication. The product/security frontier itself is unchanged.

## Historical pre-official ICF-CS Git-control closure — 2026-09-05
The provisional ICF generation is durable at `63f7a74...`; official-addendum successor publication above is the current P0 before egress implementation.
