# Egress Wider v0.2.1.3 — First Execution / Supervision-Lost Preservation

Date: 2026-09-07 UTC
Status: **FIRST EXECUTION OCCURRED / EXACT OUTPUT PRESERVED / NOT ADMITTED**
Mode after execution: **AUDIT**
Authority: App/security evidence only; no Main/Core, Governance Contact, provider, product-wide runtime-law, or promotion authority.

## Preconditions that were verified before execution
- durable control successor `f59a32946cea1af64e427a4d9db64a7075f691dd` / CHECKPOINT `64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589` was non-force published and independently fresh-clone verified;
- App source `43aa7feac7e8a15828116bd700b644560714496d` was clean and remote-exact;
- Gen14 remained `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null;
- preserved artifact `99ef2cbbc08eef598fb9c8b02ae38d5b9d88a3c4fcde576b96cf047b1942185e` was byte-exact at 12,247 bytes and its Attempt Store row still stated `executed=false`;
- the earlier sibling PASS/admission `440964f6... -> bbf0043e...` remained separate lineage.

## One-shot execution
- job: `job-485c0f471477`;
- exact preserved artifact was launched once without editing;
- execution service final state: `FAILED`;
- failure kind: `SUPERVISION_LOST`;
- process exit code: unknown / null;
- same Attempt SHALL NOT be rerun.

The artifact emitted a complete JSON object before supervision was lost. Its self-reported status was `PASS_BOUNDED_DESCENDANT_UDP_LOOPBACK_DENIAL`. The unprotected Process.Start descendant delivered the exact 45-byte UDP payload to the parent-owned loopback listener. Under the protected AppContainer+immediate-Job root, the listener observed no datagram; the receipt reported AppContainer verified, immediate Job verified, zero capabilities, no inherited handles, no timeout, and protected root exit 0.

Those observations are preserved as evidence, but the execution service did not preserve a trustworthy process return code. Therefore they are **not promoted to a new bounded admission** in this generation.

## Exact first-output preservation
- stdout: `a7976870977a5eff67c92d9273cd63e28ab07c5e5ee6dd8a0bba56a81727af18`, 2,831 bytes;
- stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, 0 bytes;
- uncertainty-aware first result: `86833629ebd032f56dbc900145d40771dc38862fc1416c0ddfe88fd4e35af022`, 2,698 bytes;
- classification: `OBSERVED_PASS_SIGNAL_WITH_SUPERVISION_LOST`;
- admission status: `NOT_ADMITTED`;
- runtime law earned: `false`.

Attempt Store after exact preservation: **141 blobs / 141 attempts / 220 events**, integrity `ok`.

## Claim ceiling
`SUPERVISION_LOST != VERIFIED_PROCESS_EXIT_STATUS`
`ARTIFACT_SELF_REPORT_PASS != BOUNDED_ADMISSION_WHEN_EXECUTOR_FINALITY_IS_UNKNOWN`
`OBSERVED_DESCENDANT_UDP_LOOPBACK_NONDELIVERY != GENERAL_DESCENDANT_EGRESS_DENIAL`
`DESCENDANT_UDP_LOOPBACK_DENIAL != INTERNET_EGRESS_DENIAL`
`WIDER_ATTEMPT_PASS_SIGNAL != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Exact next audit seam
Inspect the execution-supervision/journal path for `job-485c0f471477` to determine whether terminal process status can be independently recovered without replaying the attempt. If final exit status cannot be recovered, preserve this first execution as permanently uncertain and design a **new separately identified reconciliation/discriminator Attempt** rather than rerunning `99ef2cbbc08eef598fb9c8b02ae38d5b9d88a3c4fcde576b96cf047b1942185e`.
