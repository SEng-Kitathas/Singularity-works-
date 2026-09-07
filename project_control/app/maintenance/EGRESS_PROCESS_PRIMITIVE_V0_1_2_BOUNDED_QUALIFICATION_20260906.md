# OS/Process Egress Protected-Process Primitive v0.1.2 — Bounded Qualification

Date: 2026-09-06 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED PROTECTED-PROCESS PRIMITIVE QUALIFIED / BROADER RUNTIME LAW UNEARNED**
Authority: App/product security primitive only. No Main/Core, provider, Connection Gate, semantic, checkpoint-Core-restoration, or general network authority is created by this receipt.

## Exact qualified source
App branch:
`forge/app-shell-rd@43aa7feac7e8a15828116bd700b644560714496d`

Parent:
`9bc35af608fef5cb84cd96a9a96967d1a8117ea6`.

Fresh-clone verification proved exact two-file delta and clean source.

Exact committed v0.1.2 artifacts:
- `forge_app/egress/OS_PROCESS_EGRESS_D2_HARNESS_REPAIR_v0_1_2.md` SHA `fa76950d39d38f7755233357ee9b25db41462f7d64e093942df447ae875556d5`;
- `forge_app/embodiment/test_os_process_egress_enforcement_v0_1.py` SHA `f49f1dbc03477c42a10b9a0361ba55b4c670321102bc8e7cfc8bd0119ad9b502`;
- protected-process implementation remained unchanged at `forge_app/egress/windows_protected_process.py` SHA `80163d67a40b7604920f70d25a23d982c73dd368a62f8872c7632ca1e1904790`.

## Recovery currentness gate
Source advancement from v0.1.1 correctly made Gen13 source-stale. Generation 14 was independently earned before v0.1.2 protected execution:

`checkpoint-app-live-0014-43aa7feac7e8`

checkpoint blob:
`4efabde670986f65fc3e1736452300b299f79045e5b537ea46425e1dbbbd2136`.

Gen14 evidence:
`state/live_resume_session_0014.json`
SHA `bc4bbddd0addc9be743ca01d7f022b2d2b1228373e1eac7d181937a008a32c50`.

Qualification evidence:
- exact Gen13 parent;
- four meaningful operations;
- non-stable before threshold;
- STABLE only after >10 seconds healthy lease;
- LKG promotion afterward;
- source MATCH / NORMAL / READY;
- early crash 0;
- not quarantined;
- Core contract/currentness/semantic-snapshot IDs remain null.

## Evidence lineage preserved
Original first actual D0-D3 result remains immutable evidence:
- D0 PASS;
- D1 PASS;
- D2 FAIL rc1;
- D3 PASS;
- Attempt Store blob `a06c763d85ed605261a7624c384534b31ffd9425b42976c8f63d4d0437829a60`.

The original D2 failure was localized to a broken `cmd.exe /s /c` quoting harness.

v0.1.1 descendant source was preserved at `9bc35af608fef5cb84cd96a9a96967d1a8117ea6`. Its first protected D2 still returned rc1 and is preserved at:
`state/egress_d2_harness_repair_v0_1_1_first_result_20260906.json`
SHA `11fbb751b5f6d35be296bda41b3bb0f4d5d26926b1e66e3a0a629b0dc41edeec`.

Further local-only diagnostics proved:
- AppContainer root `cmd.exe` could run;
- direct protected curl could run;
- `cmd.exe` descendant-launch behavior returned rc1;
- protected PowerShell using `System.Diagnostics.Process.Start` could launch descendant `cmd.exe` and descendant `curl.exe`;
- therefore descendant process creation itself was not the failure.

A validated PowerShell/Process.Start descendant curl shape then showed:
- unprotected: parent loopback accepted connection, exit 0;
- protected zero-capability AppContainer + immediate Job: no loopback connection, propagated curl exit 28.

That diagnostic is preserved in:
`notes/maintenance/EGRESS_D2_POWERSHELL_DESCENDANT_DIAGNOSIS_20260906.md`.

## First committed D2 v0.1.2 execution
After v0.1.2 commit/push/fresh-clone verification and Gen14 MATCH/NORMAL/READY, the committed D2 test executed unchanged for the first time.

Job:
`job-04e8cae5ca54`.

Result:
**PASS — 1/1**, rc0, 3.243s.

Preserved exact result:
`state/egress_d2_v0_1_2_first_result_20260906.json`
SHA / Attempt Store blob:
`5919cdc7af94d0e34d5884366eb3f328762422c03f2346afd332690820863b68`.

The committed D2 semantics require, in sequence:
1. unprotected PowerShell/Process.Start descendant curl reaches a parent-owned `127.0.0.1` HTTP listener and exits 0;
2. protected root is verified AppContainer;
3. protected root is verified immediate Job member;
4. protected primitive reports capability count 0;
5. protected descendant does not reach the parent listener;
6. propagated descendant curl exit is 7 or 28;
7. launch/script exceptions map to sentinel 190 and cannot masquerade as network denial.

## Same-commit D0-D3 regression
No test edit occurred between the first committed D2 PASS and regression.

Job:
`job-f094548ac3ab`.

Exact raw execution log identities:
- stdout: 0 bytes, SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- stderr: 1,053 bytes, SHA `cc4976f2cadc5560439ce56abe31061665bdd6bdef00ea111fa6a7fced808e56`.

Observed:
- D0 PASS;
- D1 PASS;
- D2 PASS;
- D3 PASS;
- 4 tests;
- 6.821s;
- overall `OK`;
- process return code 0.

Preserved exact regression result:
`state/egress_d0_d3_v0_1_2_regression_result_20260906.json`
SHA / Attempt Store blob:
`1a571cae54279aa4b79646b87dfb254701957088d481bc7b0de7c832935055fa`.

Post-regression source readback:
- local HEAD `43aa7feac7e8a15828116bd700b644560714496d`;
- remote App branch exact same commit;
- worktree clean;
- test Git SHA `f49f1dbc03477c42a10b9a0361ba55b4c670321102bc8e7cfc8bd0119ad9b502`;
- implementation Git SHA `80163d67a40b7604920f70d25a23d982c73dd368a62f8872c7632ca1e1904790`.

## Qualified bounded claims
The following are now qualified **for this exact tested Windows host/source/test boundary**:

### D0
The primitive launches the protected root in a zero-capability AppContainer and immediately assigns it to the Job object before resume; the receipt observes AppContainer=true, immediate_job=true, capability_count=0.

### D1
The protected root cannot connect to the parent-owned loopback listener under the tested curl discriminator; the parent listener remains unconnected and curl returns a bounded network-failure code.

### D2
The same validated PowerShell/Process.Start descendant curl construction reaches parent loopback when unprotected but does not reach it when the root is launched under the zero-capability AppContainer + immediate Job primitive; the protected descendant propagates curl network-failure 7/28.

### D3
Closing the Job handle terminates a protected root that exceeds its timeout, and the receipt records the bounded job-close/timeout semantics exercised by the committed test.

## Explicitly unearned claims
This receipt does **not** establish:
- production launch-site integration;
- a broker/gate allow path;
- Internet egress denial generally;
- DNS denial;
- UDP/QUIC denial;
- proxy/helper/browser/plugin escape resistance;
- COM/RPC/WSL/service escape resistance;
- breakaway resistance beyond the exact tested Job/AppContainer path;
- all descendant launch mechanisms;
- provider safety;
- Connection Gate completeness;
- semantic/Core authority;
- checkpoint Core restoration identity;
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as a runtime law.

`LOCAL_LOOPBACK_PROCESS_CONTAINMENT != GENERAL_EXTERNAL_EGRESS_CONTAINMENT`.
`BOUNDED_PRIMITIVE_QUALIFIED != PRODUCTION_ENFORCEMENT_INTEGRATED`.
`D0_D3_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`.

## Promotion decision
**PROMOTE only the bounded protected-process primitive evidence described above to QUALIFIED.**

The next security frontier is wider bypass pressure and eventual production launch-site integration, while preserving the current authority ceiling and requiring new attempts for materially new claims.
