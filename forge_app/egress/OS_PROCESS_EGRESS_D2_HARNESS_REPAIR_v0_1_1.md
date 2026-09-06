# OS/Process Egress Enforcement — D2 Descendant Harness Repair v0.1.1

Date: 2026-09-06
Status: **DESCENDANT TEST-HARNESS REPAIR CANDIDATE — PRESERVE BEFORE PROTECTED EXECUTION**
Authority: App/product test evidence only; no Main/Core, Connection Gate, provider, or semantic authority.
Parent Attempt 0 source: `e9b81750db265a467187c61962ffab3cff98d4fe`.

## Preserved first actual result
The first actual unchanged D0-D3 execution is already durably preserved in Attempt Store as:
`attempt-egress-enforcement-v0-1-d0-d3-first-actual-result`
blob SHA `a06c763d85ed605261a7624c384534b31ffd9425b42976c8f63d4d0437829a60`.

Observed result:
- D0 PASS;
- D1 PASS;
- D2 FAIL;
- D3 PASS;
- D2 descendant command returned rc1;
- frozen D2 accepted only curl connect/timeout failures 7/28, therefore descendant network denial was not proven;
- source remained clean;
- egress enforcement remained unqualified.

The first result SHALL remain immutable historical evidence.

## Failure localization
The exact D2 command shape was replayed outside AppContainer against a parent-owned loopback listener:

`cmd.exe /d /s /c "\"C:\\Windows\\System32\\curl.exe\" ..."`

It failed identically with rc1 and stderr stating that the quoted curl executable was not recognized. The listener received no connection.

Therefore:
`D2_RC1 != DESCENDANT_NETWORK_DENIAL`.
`D2_RC1 == TEST_HARNESS_COMMAND_QUOTING_FAILURE`.

## Pre-mutation quoting pressure
Three local-only, unprotected command-shape candidates were pressure-tested without touching source:

1. quoted executable + doubled outer quotes + `/s`: rc1; no listener connection; executable not recognized;
2. same doubled outer quotes without `/s`: rc1; no listener connection; executable not recognized;
3. whitespace-free resolved System32 curl path, unquoted, `cmd.exe /d /c`: rc0; parent listener accepted the HTTP request.

Only candidate 3 demonstrated that the descendant command actually launches curl under the current host.

## Minimal repair
D2 v0.1.1 SHALL:
1. resolve `curl.exe` exactly with the existing `_system_executable` helper;
2. fail closed before protected execution if the resolved executable path contains whitespace, because this bounded repair deliberately avoids another Windows shell quoting interpretation;
3. construct the child command with the exact whitespace-free resolved path **unquoted**;
4. use `cmd.exe /d /c` and remove `/s`;
5. retain the same curl flags, local-only `127.0.0.1` listener, 7/28 bounded failure acceptance, AppContainer + Job root, and listener-nonconnection requirement;
6. change no protected-process implementation semantics.

This repair is host-bounded. A future generic descendant launcher SHOULD avoid shell-string identity entirely rather than generalizing this workaround into a universal quoting rule.

## Qualification ceiling
A repaired D2 PASS can establish only that, on this tested host, the protected root's descendant curl invocation was successfully launchable in the unprotected control shape and then failed to reach the parent loopback listener under the protected AppContainer/Job path with an accepted curl network-failure code.

It still does not establish Internet/DNS/UDP/proxy/helper/plugin/COM/WSL escape resistance or the final runtime law.

`D2_REPAIRED_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`.

## Preservation/execution order
1. semantic-read this repair note + changed test completely;
2. static syntax/diff/privacy checks;
3. commit and non-force publish the descendant repair before protected execution;
4. because App source advances, re-establish recovery currentness before protected execution;
5. then execute the exact committed repaired discriminator without editing first;
6. preserve the first repaired result before diagnosis or further repair.
