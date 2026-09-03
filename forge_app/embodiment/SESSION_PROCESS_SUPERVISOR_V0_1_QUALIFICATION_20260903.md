# Singularity Works Session Process Supervisor v0.1 — Qualification — 2026-09-03

Status: **READY_WITH_EVIDENCE for one supervised coordinator process per resume generation, actual external process death, checkpoint crash association, two-death quarantine, and automatic isolated re-entry on the tested Windows/local-process boundary.**

Not qualified for whole descendant-process-tree containment, supervisor death after child death before crash receipt, cross-machine supervision, or formal availability/safety certification.

## Goal
Move checkpoint crash reputation out of the dying resumed session process and into a separately surviving supervisor.

Locked laws:
- `SESSION_PROCESS_DEATH != CHECKPOINT_DATA_DEATH`.
- `DYING_PROCESS != CRASH_REPUTATION_AUTHORITY`.
- `SUPERVISOR_OBSERVATION != CHILD_SELF_REPORT`.
- `RESUME_ID != REUSABLE_PROCESS_SLOT`.
- `CHILD_READY_ACK != SESSION_STABILITY`.
- `CRASH_ID_REPLAY_USES_ORIGINAL_OBSERVATION`.
- `LAUNCH_PID != COORDINATOR_PID`.
- `READY_IDENTITY_BINDS_RESUME_NONCE_NOT_LAUNCHER_PID`.

## Attempt-0 preservation
Unexecuted supervisor protocol/code/worker/tests were committed and pushed before first execution:

`0cf924b` — `singularity-works: preserve session process supervisor attempt zero`.

Attempt 0 included:
- `forge_app/recovery/SESSION_PROCESS_SUPERVISOR_PROTOCOL_v0_1.md`;
- `forge_app/recovery/session_supervisor.py`;
- `forge_app/embodiment/session_coordinator_worker_v0_1.py`;
- `forge_app/embodiment/test_session_process_supervisor_v0_1.py`;
- recovery package exports.

## First targeted execution scar
Command:
`python -W error::ResourceWarning -m unittest forge_app.embodiment.test_session_process_supervisor_v0_1 -v`

Result: **4/5 PASS, 1 ERROR**.

Passing immediately:
- expected shutdown produced no crash reputation;
- resume ID reuse was rejected;
- two actual externally killed child processes quarantined a disposable checkpoint and prepared re-entry in the temporary test environment;
- wrong ready identity was rejected.

Failure:
replaying the same deterministic crash ID called `record_crash()` again after more wall-clock time had elapsed. The existing immutable event carried the original `seconds_since_resume`; the replay supplied a later value under the same event ID, so Attempt Store correctly rejected it:
`event_id conflict with different immutable event`.

Classification: real uncertain-observation replay defect.

Narrow repair:
`ffd9958` — `singularity-works: replay durable crash observation exactly`.

New law:
**`CRASH_ID_REPLAY_USES_ORIGINAL_OBSERVATION`.**

On duplicate crash ID, supervisor now finds and returns the existing durable crash observation rather than recomputing elapsed time or attempting a different immutable event.

Targeted retest: **5/5 PASS**.

## First live campaign scar — launcher PID != coordinator PID
A first real-project campaign at source `ffd995835d24...` used the actual project Attempt Store and spawned the actual coordinator worker under the PCMMAD server Python runtime.

Supervisor launch handle PID:
`24096`.

Worker/coordinator self-reported PID:
`25576`.

The original strict ready check required equality and therefore failed closed with:
`ready identity mismatch`.

No quarantine success was claimed from that run.
The failed probe checkpoint/resume remains evidence in the live store; it was not rewritten away.

An explicit orphan check afterward reported no running task for PID `25576`.

Classification: real Windows/runtime process-wrapper identity seam. `Popen.pid` is not universally the resumed coordinator's execution identity.

## Process-identity repair
Descendant commit:
`2206baeb5297b100888bf14ec47f46d05a541740` — `singularity-works: bind supervisor to coordinator process identity`.

Repair:
- supervisor creates a unique per-resume instance nonce;
- nonce is injected into child environment;
- child ready receipt echoes protocol/checkpoint/resume/coordinator PID/nonce;
- supervisor validates protocol + checkpoint + resume + nonce;
- ready-reported coordinator PID becomes the kill subject;
- launch-handle PID remains separately recorded;
- PID equality is no longer falsely required.

The child still receives no Attempt Store path/capability.

New laws:
- `LAUNCH_PID != COORDINATOR_PID`.
- `READY_IDENTITY_BINDS_RESUME_NONCE_NOT_LAUNCHER_PID`.

Targeted post-repair suite: **5/5 PASS**.

## Full regression
After the process-identity repair:
`python -W error::ResourceWarning -m unittest discover -s forge_app/embodiment -p test_*.py -v`

Result: **60/60 PASS** in 10.239 seconds.

## Live real-project external-kill campaign
Live source:
`2206baeb5297b100888bf14ec47f46d05a541740`.

Disposable checkpoint:
`checkpoint-live-supervisor-kill-probe2-2206baeb5297`.

Checkpoint immutable blob:
`5e8be6aff2a5122c2ca0f9cda8b542ed8834574a1f9038edd8f79b09ba39c89c`.

Parent/known-good checkpoint:
`checkpoint-app-live-0004-c3a3cadee9d2`.

### External kill 1
Resume:
`resume-live-supervisor-c-2206baeb`.

- launch PID: `2844`;
- coordinator PID: `22232`;
- nonce: `c70769f40ed740799cb957324bf575e8`;
- supervisor-measured death time: ~0.093 seconds after resume start;
- launch-handle return code recorded by v0.1 receipt: `15`;
- checkpoint became `CRASH_ASSOCIATED`;
- early crash count 1;
- SAFE_ONLY;
- not quarantined.

### External kill 2
Resume:
`resume-live-supervisor-d-2206baeb`.

- launch PID: `13084`;
- coordinator PID: `16636`;
- nonce: `7e6ca5bdd95842f8ae36df335667fd74`;
- supervisor-measured death time: ~0.109 seconds after resume start;
- launch-handle return code recorded by v0.1 receipt: `15`;
- checkpoint became `QUARANTINED`;
- early crash count 2;
- INSPECT_ONLY.

Post-campaign task check found no running tasks for the killed coordinator PIDs.

## Automatic re-entry result
The second death caused the existing manager-level quarantine handler to prepare:

`reentry-quarantine-checkpoint-live-supervisor-kill-probe2-2206baeb5297`.

Verified:
- trigger `quarantine_auto`;
- popup severity `RECOVERY_ISOLATED`;
- quarantine remained active;
- source currentness MATCH for the risky checkpoint;
- source isolation `EXACT_DETACHED_WORKTREE`;
- re-entry source exact at `2206baeb5297b100888bf14ec47f46d05a541740`;
- open/inspect/compare/return-to-LKG/dismiss actions present;
- return-to-LKG pointed to `checkpoint-app-live-0004-c3a3cadee9d2`.

The risky checkpoint blob remained exact and unchanged.
The active App source HEAD/status remained exact and clean throughout the two deaths.

## Known-good recovery boundary during campaign
`ResumeCheckpointManager.choose_recovery()` continued to select generation-4 LKG:
`checkpoint-app-live-0004-c3a3cadee9d2`.

Important currentness caveat:
generation 4 was a valid LKG by checkpoint reputation but its source `c3a3cad...` was older than the live campaign source `2206bae...`. Ergo's source-currentness layer therefore must continue to treat that old LKG conservatively for normal resume. A new current-source LKG is created after this qualification report is committed; the campaign did not pretend the older LKG was source-current merely because it remained the reputation-preferred recovery point.

## Live evidence preservation
Live campaign file:
`state/live_session_process_supervisor_v0_1.json`
SHA-256:
`42a3ee5ef1465cb8ac9a9723e53b6dd4b6ab2717ddbadaf983ab63feadde74e7`.

Attempt Store preservation:
`attempt-live-session-process-supervisor-v0-1`
with exact verified readback and the same blob SHA.

Live store after evidence capture:
- integrity `ok`;
- WAL;
- synchronous FULL;
- 59 blobs / 59 attempts / 89 events.

## Current source hashes at qualification
At Git `2206baeb5297b100888bf14ec47f46d05a541740`:
- `forge_app/recovery/session_supervisor.py`
  SHA `5b44bc47ba4134c20f2df811495f1e87d3d02bf17a908fa09aa4c5a25624c9ac`;
- `forge_app/recovery/SESSION_PROCESS_SUPERVISOR_PROTOCOL_v0_1.md`
  SHA `3d23d06178a568590b4b674e712a998218da1bcfcf1b2de4b150edfdc0074e34`;
- `forge_app/embodiment/session_coordinator_worker_v0_1.py`
  SHA `9bc746bb09593f1188037a3c9b7b68451e10d45a0c5d0434dd9b318192f803a7`;
- `forge_app/embodiment/test_session_process_supervisor_v0_1.py`
  SHA `7e7c56b159b15ca240bd6b1642742a2a4a6135a717f674ea69894e770a5542c4`.

## Bounded claim
On the tested local Windows/process boundary, Singularity Works can durably record the resume identity before session work, validate an actual coordinator process independently from a platform launcher wrapper, externally kill that coordinator, and have a surviving supervisor associate the death with the exact checkpoint/resume generation.

Two distinct early externally observed coordinator deaths quarantine the disposable checkpoint through the existing reputation engine and automatically create the existing isolated re-entry lane/popup, while checkpoint bytes and the active source remain intact.

The dying coordinator is not the crash-reputation authority and receives no Attempt Store writer capability in this v0.1 path.

## Remaining seams
- supervisor process death after coordinator death but before crash receipt;
- recovery/reconciliation of a durable `checkpoint_resumed` generation when supervisor dies before a terminal receipt;
- whole descendant-process-tree / job-object containment if the coordinator forks children;
- explicit process start/ready/terminal receipt durability beyond current checkpoint lifecycle events and transient ready file;
- coordinator exit-code observation distinct from launch-wrapper return code when PIDs differ;
- graceful in-process shutdown protocol beyond external expected termination;
- heartbeat/watchdog integration into the external supervisor;
- OS session/logoff/machine crash;
- multi-host supervision;
- privilege/sandbox boundary around the coordinator process;
- formal availability/safety certification.

## Next pressure
After committing this report, create a new current-source checkpoint/LKG containing the qualified supervisor code. Then begin the Connection Gate authority state machine as the next security substrate, while keeping supervisor-death-before-receipt and process-tree containment in the P0 recovery queue.
