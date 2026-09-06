# OS/Process Egress Enforcement — D2 Descendant Harness Repair v0.1.2

Date: 2026-09-06
Status: **DESCENDANT DISCRIMINATOR REPAIR CANDIDATE — PRESERVE BEFORE FIRST COMMITTED EXECUTION**
Authority: App/product test evidence only; no Main/Core, Connection Gate, provider, or semantic authority.
Parent source: `9bc35af608fef5cb84cd96a9a96967d1a8117ea6`.

## Why v0.1.2 exists
The original frozen D2 failed rc1 because its `cmd.exe /s /c` quoting did not execute curl even outside AppContainer.

v0.1.1 repaired that quoting for the unprotected host control, but the committed protected D2 still returned rc1. That first repaired result is preserved exactly at:
`state/egress_d2_harness_repair_v0_1_1_first_result_20260906.json`
SHA `11fbb751b5f6d35be296bda41b3bb0f4d5d26926b1e66e3a0a629b0dc41edeec`.

Further protected local-only diagnostics established:
- AppContainer root `cmd.exe` runs;
- direct protected curl runs;
- `cmd.exe` descendant-launch attempts return rc1;
- protected PowerShell using `System.Diagnostics.Process.Start` successfully launches descendant `cmd.exe` and descendant `curl.exe --version`.

Therefore v0.1.1 remained harness-bound, not a network-containment result.

## Validated descendant command shape
A PowerShell root using `System.Diagnostics.ProcessStartInfo` with `UseShellExecute=false` was pressure-tested against a parent-owned loopback listener.

Unprotected control:
- descendant curl launched;
- listener accepted connection;
- propagated child exit 0.

Protected zero-capability AppContainer + immediate Job:
- root AppContainer verified;
- immediate Job verified;
- listener accepted no connection;
- descendant curl propagated exit 28.

Diagnostic receipt command SHA for the protected shape:
`760d23f51dac0df157dff998f7e387a3e62b6c9f440a81f0bf309471c76d9d89`.

## v0.1.2 test construction
D2 SHALL use one helper-generated PowerShell script that:
1. constructs `System.Diagnostics.ProcessStartInfo` for exact resolved `curl.exe`;
2. uses `UseShellExecute=false`;
3. launches the exact local-loopback curl argument string;
4. waits for the child;
5. exits with the child exit code;
6. maps any Process.Start/script exception to sentinel exit 190, which is never accepted as network denial.

The test SHALL execute that same construction twice against separate parent-owned listeners:

### Positive control
Unprotected PowerShell root:
- listener MUST accept connection;
- root/propagated child exit MUST be 0.

### Protected discriminator
PowerShell root launched through unchanged `run_zero_network_process`:
- root token MUST be AppContainer;
- root MUST be in immediate Job;
- capability count remains zero through the primitive receipt;
- parent listener MUST NOT accept connection;
- propagated child curl exit MUST be 7 or 28.

No external endpoint is contacted.

## Claim ceiling
A green committed v0.1.2 D2 can qualify only:

> On this tested Windows host, the same PowerShell/Process.Start descendant curl shape reaches parent loopback without containment but fails to reach it under the zero-capability AppContainer + immediate Job root, returning a bounded curl network-failure code.

It does not qualify Internet, DNS, UDP/QUIC, proxy/helper, COM/RPC, WSL, plugin, breakaway, provider, or production-launch integration.

`D2_V0_1_2_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`.

## Preservation order
1. completely semantic-read this note and changed test;
2. static syntax/diff/privacy gates;
3. commit + non-force publish exact descendant source;
4. fresh-clone readback;
5. because source advances, re-establish recovery currentness before execution;
6. execute committed D2 v0.1.2 unchanged for the first time;
7. preserve exact first result before any regression/repair;
8. only if D2 passes, run D0-D3 regression from the same exact commit.
