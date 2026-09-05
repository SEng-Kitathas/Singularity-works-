# Singularity Works OS / Process Egress Enforcement Protocol v0.1

Status: **ATTEMPT 0 — PRESERVE BEFORE FIRST EXECUTION**
Date: 2026-09-05
Authority: App/product runtime security candidate only. No Main/Core semantic authority.
Canonical process parent: RAHL Engineering Canonical SOP R4.4.
Continuity ingress: ICF-CS v1.0.

## Decision target
Prove or falsify the smallest Windows-native protected execution domain in which an App-owned child process and its descendants cannot use ambient network access unless execution is deliberately routed through a separately qualified broker/Gate boundary.

This Attempt 0 does **not** claim machine-wide firewall control and does not wire a real provider.

## Why this boundary is next
Live source inspection found five production subprocess launch sites:
- `forge_app.render.persistent_host`;
- `forge_app.render.renderer_host`;
- `forge_app.recovery.session_supervisor`;
- `forge_app.recovery.reentry`;
- `forge_app.ergo.recovery_summary`.

The renderer/session children are explicitly replaceable or authority-NONE workers, yet they currently inherit ordinary OS process/network capability. The qualified Connection Gate and external-operation lifecycle perform no network I/O.

Therefore the first enforcement problem is **ambient capability containment of App-owned child processes**, not provider transport.

## Current host evidence before Attempt 0
Read-only host inspection on the current machine established:
- Windows 11 Home, build 26200, 64-bit;
- current process is not elevated;
- Windows Defender Firewall is enabled, but profile outbound policy is `NotConfigured`;
- `New-NetFirewallRule` exists but program/user rules would not distinguish protected Python descendants from the broker/parent identity;
- AppContainer APIs are present (`CreateAppContainerProfile`, `DeriveAppContainerSidFromAppContainerName`);
- process attribute APIs are present (`InitializeProcThreadAttributeList`, `UpdateProcThreadAttribute`);
- Job Object APIs are present (`CreateJobObjectW`, `SetInformationJobObject`, `AssignProcessToJobObject`, `IsProcessInJob`);
- the current harness process is already inside a Windows Job Object;
- `CheckNetIsolation LoopbackExempt -s` works on this host and demonstrates active AppContainer loopback policy.

The current outer Job is a live discriminator: nested-job compatibility SHALL be observed, not assumed.

## Platform contract used by Attempt 0
Microsoft documents the following mechanisms:
1. `PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES` with a `SECURITY_CAPABILITIES` structure creates the new process as an AppContainer process.
2. AppContainer network access is capability-driven. Network capability names such as `internetClient`, `internetClientServer`, and `privateNetworkClientServer` grant network access; Attempt 0 supplies **zero capability SIDs**.
3. Job Objects associate child processes by default when breakaway is not enabled.
4. Nested Job Objects are supported on Windows 8+ when a valid hierarchy can be formed.
5. `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` terminates processes in that Job (including nested child jobs) when the last Job handle closes.
6. Process handle inheritance should be false unless exact handles are intentionally required.

These are platform claims to be pressured locally. Documentation is not local qualification evidence.

## Attempt 0 architecture
### Protected domain
Attempt 0 defines one protected child process as:

`ZERO-NETWORK APPCONTAINER TOKEN + IMMEDIATE JOB OBJECT + NO HANDLE INHERITANCE`

Launch sequence:
1. validate an exact absolute executable path;
2. create/derive a per-user AppContainer profile SID;
3. initialize `STARTUPINFOEX` with `PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES`;
4. set `SECURITY_CAPABILITIES.AppContainerSid` to the profile SID;
5. set `Capabilities = NULL`, `CapabilityCount = 0`, `Reserved = 0`;
6. create a Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` and **no breakaway flags**;
7. create the child with `EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED`, `bInheritHandles = FALSE`;
8. while the child is still suspended, verify its token reports `TokenIsAppContainer != 0`;
9. while still suspended, assign it to the immediate Job Object;
10. verify `IsProcessInJob(child, immediate_job) == TRUE`;
11. only after both security predicates are observed, resume the child;
12. on any setup/verification failure, terminate the suspended child and fail closed;
13. keep the Job handle open for the execution lifetime;
14. close the Job before profile cleanup so lingering descendants are terminated by the Job boundary.

`APPCONTAINER_SETUP_FAILURE -> CHILD_NEVER_RESUMES`
`JOB_ASSIGNMENT_FAILURE -> CHILD_NEVER_RESUMES`
`SECURITY_PREDICATE_UNKNOWN -> FAIL_CLOSED`

## Authority topology
Protected child / descendants:
- App-owned runtime execution;
- network capability target: NONE;
- semantic authority: NONE;
- external consequence authority: NONE.

Future broker / Connection Gate process:
- remains outside the zero-network protected domain;
- may later own narrowly scoped transport submission only after current Gate authority and exact operation identity are rechecked;
- is not implemented by Attempt 0.

Main/Core:
- unchanged;
- no semantic truth is minted by containment success/failure.

## Initial protected-domain candidates
Strong candidates for later integration, **after the primitive qualifies**:
- persistent renderer worker;
- one-shot renderer worker;
- session coordinator / resumed App worker;
- future plugin/imported-code worker.

Not automatically claimed protected in Attempt 0:
- current production launch sites themselves (integration is a later gate);
- Git source inspection;
- re-entry Git worktree creation;
- provider transport (absent);
- arbitrary machine processes.

`PRIMITIVE_QUALIFIED != PRODUCTION_LAUNCH_SITES_INTEGRATED`

## Environment / filesystem nonclaim
Attempt 0 inherits the parent environment because executable viability inside AppContainer is itself under test. Handle inheritance is disabled.

This does **not** qualify:
- environment-variable secret minimization;
- AppContainer filesystem ACL design;
- proxy-variable hygiene;
- registry access policy;
- named-pipe/broker IPC ACLs.

If an OS binary cannot start under the zero-capability AppContainer because of filesystem/token restrictions, that is valid Attempt 0 evidence. Isolation SHALL NOT be weakened merely to make the test green.

## Initial hostile discriminator set
No real external network endpoint is contacted in Attempt 0.

### D0 — protected process viability + predicates
Launch an OS-provided local command that exits successfully.
Require:
- process creation succeeds;
- token is observed AppContainer;
- immediate Job membership is observed;
- command exits 0;
- if the harness is already Job-contained, nested assignment must still succeed locally.

### D1 — direct loopback bypass
Parent creates a local `127.0.0.1` TCP listener.
Launch system `curl.exe` as the protected root process against that listener with proxies disabled.
The listener returns a local HTTP response only if a connection arrives.
Require:
- protected process itself started (CreateProcess succeeded);
- no listener connection is observed;
- curl returns a bounded connect/timeout failure (`7` or `28` in the frozen first discriminator). Any other nonzero result is **not** accepted as network-denial proof and must be investigated.

This is a local loopback discriminator, not proof of Internet/DNS denial.

### D2 — descendant loopback bypass
Parent creates the same local listener.
Launch protected `cmd.exe`; `cmd.exe` launches `curl.exe` as a descendant against the listener.
Require:
- protected root is AppContainer + Job member;
- descendant launch path runs without intentionally requesting breakaway;
- no listener connection is observed;
- descendant curl returns the same bounded connect/timeout failure (`7` or `28`). A command-launch/access failure is not accepted as descendant network-denial evidence.

This pressures both AppContainer capability inheritance and Job descendant containment without contacting an external endpoint.

### D3 — Job-close termination
Launch a protected local sleeper with a short host timeout.
Require:
- timeout occurs;
- closing the immediate Job terminates the still-running protected process promptly;
- the process does not remain alive after Job close.

## Explicitly deferred hostile surfaces
Attempt 0 does not yet prove:
- external Internet denial;
- DNS transport denial;
- UDP/QUIC/raw-socket denial;
- proxy helper / named-pipe broker escape;
- COM/RPC mediated network consequences;
- WSL/container/helper-service escape;
- child explicitly requesting breakaway;
- shell-extension/Git filter helper escape;
- production renderer/session integration;
- machine-wide containment.

Those become next discriminators only after Attempt 0 establishes whether this primitive is viable.

## First-run interpretation
### PASS candidate
All D0–D3 pass and the exact implementation remains semantically coherent.
Disposition: `READY_WITH_EVIDENCE_FOR_BOUNDED_PROTECTED_PROCESS_PRIMITIVE`, **not** runtime-law qualification.

### Expected useful failures
Any of these are valid evidence:
- `CreateAppContainerProfile` denied;
- OS executable cannot launch in the AppContainer;
- AppContainer token verification fails;
- nested Job assignment fails because of outer Job policy;
- loopback unexpectedly succeeds;
- descendant succeeds where root is denied;
- Job close does not terminate the target;
- cleanup/profile deletion fails.

Disposition: preserve failure exactly, repair the architecture or narrow its claim; never weaken the discriminator to manufacture green.

## Qualification ceiling
Even a green Attempt 0 can establish only:

> On this tested Windows host, a bounded App-owned process primitive can be created under a zero-network-capability AppContainer, observed as an AppContainer token, attached to an immediate no-breakaway Job, and pressured against local loopback/direct-descendant escape plus Job-close termination.

It cannot establish:
`NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

That law remains unearned until the primitive is integrated into the actual protected production launch paths and broader bypass classes are attacked.

## Preservation rule
The complete Attempt 0 protocol, implementation, package surface, and hostile tests SHALL be committed and remotely read back **before first enforcement execution**.

`ATTEMPT_0_IS_EVIDENCE_NOT_SCRATCH_SPACE`
`PRESERVE_BEFORE_FIRST_EXECUTION`

After preservation/readback, execute the exact frozen tests without editing them first. Any failure becomes the next evidence-bearing development input.
