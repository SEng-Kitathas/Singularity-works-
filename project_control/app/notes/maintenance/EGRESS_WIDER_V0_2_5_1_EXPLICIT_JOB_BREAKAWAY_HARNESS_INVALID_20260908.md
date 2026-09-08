# Wider Egress v0.2.5.1 — Explicit Job Breakaway — HARNESS_INVALID

Date: 2026-09-08 UTC
Status: **FIRST ATTEMPT IMMUTABLE / HARNESS_INVALID / NO BREAKAWAY CLAIM**
Authority: App/process-lifecycle evidence only. No Main/Core, network, provider, Governance Contact global, production, or runtime-law authority.

## Currentness / lineage
- durable control `a95ec5355b6946927eec6403a1764491f837e9e2` / CHECKPOINT `09bdf45b6aa912da4f97e4f142387dc80f9ac093a5fab7885f004e1ed9aecc7d`, independently fresh-clone verified PASS 154 before execution;
- stale-control v0.2.5 artifact `fdfad311f15929c70bacde6026be491a5b9e0efdf07d37791b5649a14f7db25b` remains preserved/unexecuted;
- currentness-only v0.2.5.1 artifact `50095130e14f4d564dbca18cf0a6ace6c3805ffca38598856bd4a6fe4b1d9bb8`, 17,731 bytes / 381 lines, complete semantic read + exact Attempt Store capture before execution;
- frozen helper source `77927e4fcf9c874428d78415cda05f52998e59e2133af1d41126348cc8fa7a34`, DLL `8019c83a601e76be23a8762f61ed1f557f940dc11f9328893a785c6b42b8903a`.

## Exact first execution
- job `job-34b75435461c`; executor finality FAILED / rc3 / NONZERO_EXIT;
- stdout `abe290d86ef467c62bc8a4c17e402b00f6a8d4008f1082997387ea79c67334b0`, 1,544 bytes;
- stderr empty SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- structured first result `60c928361d0f350447d2577f671915263446f4d7e40afb5cea12161abc19add8`, 1,786 bytes.

The artifact aborted at its outer-execution-Job gate. The execution worker reported current outer Job limits `0x2000`: `KILL_ON_JOB_CLOSE=true`, `SILENT_BREAKAWAY_OK=false`, `BREAKAWAY_OK=false`. Because the positive-control helper could not be isolated from that executor Job, both `positive_control` and `protected` remained null. No `CREATE_BREAKAWAY_FROM_JOB` child creation was attempted.

Earlier server synchronous-plane probing observed a different outer Job shape (`0x3000`, including `SILENT_BREAKAWAY_OK`). That is a distinct execution-plane property and SHALL NOT be transferred by inference. It must be re-measured on the exact plane before any repair Attempt uses it.

Classification: `HARNESS_INVALID_OUTER_EXECUTION_JOB_NO_SILENT_BREAKAWAY`. Admission: **NOT_ADMITTED**. Same Attempt SHALL NOT be rerun.

`EXECUTION_PLANE_JOB_POLICY != FORGE_IMMEDIATE_JOB_POLICY`
`OUTER_JOB_PRECHECK_FAILURE != CREATE_BREAKAWAY_FROM_JOB_DENIAL`
`POSITIVE_CONTROL_NOT_REACHED != PROTECTED_PASS`
`HARNESS_INVALID != SAFE_TO_REPLAY_SAME_ATTEMPT`

## Repair boundary
Before a new Attempt is frozen, measure the candidate execution plane's actual outer Job limits. A NEW v0.2.5.2 may preserve identical discriminator behavior while changing only execution-plane/currentness/lineage bindings if and only if that plane verifies `SILENT_BREAKAWAY_OK`. The original v0.2.5/v0.2.5.1 artifacts and first result remain immutable.
