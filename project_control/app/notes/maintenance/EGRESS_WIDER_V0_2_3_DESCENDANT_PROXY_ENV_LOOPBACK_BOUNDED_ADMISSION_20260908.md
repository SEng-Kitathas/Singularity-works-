# Wider Egress v0.2.3 — Descendant Proxy/Environment Loopback — Bounded Admission

Date: 2026-09-08 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED DESCENDANT PROXY/ENVIRONMENT LOOPBACK NON-DELIVERY QUALIFIED / GENERAL PROXY & EGRESS LAW UNEARNED**
Authority: App/product security evidence only. No Main/Core, provider, system-proxy, Internet, or product-wide runtime-law authority is created.

## Durable/currentness bindings
- App source `43aa7feac7e8a15828116bd700b644560714496d`, clean and remote-exact before/after execution.
- Public Main `e66c071fc25f8d08bfc7ebf0551948392d652f35`; semantic Core anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a`.
- Recovery ingress Gen14 `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null.
- Durable control `f59a32946cea1af64e427a4d9db64a7075f691dd` / CHECKPOINT `64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589`.
- Governance Contact resolves `GOVERNANCE_CONTACT_LOCALLY_BINDING_ADDITIVE_PROCESS_DOCTRINE` at the Git target through exact activation token `b5a2e35f300c6f72d93fc80b877ef0478a3628442b705e50f6893cbceafb5094`; global ACTIVE remains forbidden because the detached completion receipt is absent.
- Parent lineage: descendant DNS-helper bounded admission `63e5a830b18bb8d6c5f291468e7a6b9ed491ed580f37a0a7aceb6e584dc79225`.

## Preserved discriminator
Artifact `state/attempt_artifacts/EGRESS_WIDER_V0_2_3_DESCENDANT_PROXY_ENV_LOOPBACK_20260907.py`
SHA `7878188e532b1828c41fb9075999425ef7ed03a9d1f11d6d3b76fe21d243577c`, 15,295 bytes / 380 lines, syntax PASS and complete semantic read 380/380 before capture/execution.
Attempt `attempt-egress-wider-v0-2-3-descendant-proxy-env-loopback-first`.

The test uses only two parent-owned `127.0.0.1` HTTP listeners:
1. an environment-selected proxy listener;
2. a direct target listener.

The PowerShell root validates the exact `SW_PROXY_ENV_MARKER` and `ALL_PROXY` value before `Process.Start`. Descendant curl is invoked without an explicit proxy argument. Parent process temporarily sets proxy variables and clears NO_PROXY/no_proxy, then restores all managed variables in `finally`.

No Internet endpoint, DNS query, provider call, registry/system-proxy mutation, hosts-file change, OAuth credential, or machine-wide firewall mutation is used.

## Exact first execution
Job `job-72933961f711` completed normally with executor return code 0.
- exact stdout / structured result SHA `c60ee5e079b0eed9c99e7bd86142560a1d46ace1bd2a372283d3980be710e56c`, 3,331 bytes / 90 lines;
- exact stderr SHA `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, 0 bytes;
- raw stdout, raw stderr and structured-result identities were preserved in Attempt Store before this admission.

### Positive control — unprotected
- root exit 0;
- proxy listener received exactly 1 connection;
- first request line was an absolute proxy-form request: `GET http://127.0.0.1:<target-port>/proxy-env-v023 HTTP/1.1`;
- direct target listener received 0 connections;
- listener errors empty.

This proves the exact root/descendant command uses the inherited environment-selected proxy path when unprotected rather than silently connecting directly to the target.

### Protected discriminator
Receipt observations:
- `appcontainer_verified = true`;
- `immediate_job_verified = true`;
- `capability_count = 0`;
- `inherited_handles = false`;
- `environment_inherited = true`;
- `timed_out = false`;
- protected descendant/root propagated curl exit `28`;
- proxy listener received **0 connections**;
- direct target listener received **0 connections**;
- listener errors empty.

The root would have returned sentinel `192` if the exact marker or `ALL_PROXY` value were not inherited, and sentinel `191` if descendant `Process.Start` failed. Neither occurred. Therefore the protected result is not a missing-environment or child-launch harness green.

## Qualified claim
> On this exact Windows host/source/control boundary, the preserved PowerShell/Process.Start descendant curl command uses an inherited environment-selected parent-owned loopback proxy when unprotected, while the same root/child command inside the zero-capability AppContainer + immediate Job primitive inherits the exact proxy environment but reaches neither the proxy listener nor the direct target listener.

This qualifies only **descendant proxy/environment loopback non-delivery** for the exact tested path.

## Explicitly unearned
- arbitrary/system proxy configuration denial;
- PAC/WPAD/WinHTTP/WinINET proxy behavior;
- Internet proxy or Internet direct egress denial;
- helper/browser/plugin/import generality;
- DoH/DoT/QUIC;
- COM/RPC/service/WSL paths;
- Job breakaway/process-tree escape resistance;
- production launch-site integration;
- provider transport;
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as runtime fact.

`PROXY_ENV_LOOPBACK_NONDELIVERY != GENERAL_PROXY_DENIAL`
`PROXY_ENV_LOOPBACK_NONDELIVERY != INTERNET_EGRESS_DENIAL`
`ENVIRONMENT_INHERITED != ENVIRONMENT_MEDIATED_BYPASS`
`LOCAL_PROXY_RESULT != SYSTEM_PROXY_CONFIGURATION_RESULT`
`LOCAL_TOKEN_VALID != GLOBAL_ACTIVE`
`BOUNDED_PROXY_ENV_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Do not repeat this environment-selected proxy path as a broader claim. The next materially distinct, locality-preserving class should pressure **process-tree / Job breakaway or equivalent descendant escape behavior** without provider/Internet transport. Preserve a NEW Attempt before any execution.
