# Wider Egress v0.2.2 — Descendant DNS Helper Loopback — Bounded Admission

Date: 2026-09-07 UTC
Mode: AUDIT -> CHECKPOINT
Role: R5 Reality Pressure Engine -> R1 Conservative Auditor
Status: **BOUNDED DESCENDANT DNS-HELPER LOOPBACK NON-DELIVERY QUALIFIED / GENERAL DNS & EGRESS LAW UNEARNED**
Authority: App/product security evidence only. No Main/Core, Governance Contact, provider, system-resolver, Internet-DNS, or product-wide runtime-law authority is created.

## Durable/currentness bindings
- App source: `43aa7feac7e8a15828116bd700b644560714496d`, clean and remote-exact before/after run.
- Recovery ingress: Gen14 `checkpoint-app-live-0014-43aa7feac7e8`, MATCH/NORMAL/READY, Core IDs null.
- Durable control: `f59a32946cea1af64e427a4d9db64a7075f691dd` / CHECKPOINT `64f1804e9d6ec64b1638cacbf25bd8963ad967958a1f2847e4d3a352c887a589`, independently fresh-clone verified.
- Parent lineage: supervision-lost v0.2.1.3 result `86833629ebd032f56dbc900145d40771dc38862fc1416c0ddfe88fd4e35af022`, retained `NOT_ADMITTED`; this v0.2.2 result does not retroactively admit it.

## Preserved discriminator
Artifact `state/attempt_artifacts/EGRESS_WIDER_V0_2_2_DESCENDANT_DNS_HELPER_LOOPBACK_20260907.py`
SHA `728daddb02e092f5726d023ef2ca895b93950bba0be0c998b0797aabe6969b2f`, 13,693 bytes / 354 lines, complete semantic read + syntax PASS before capture and execution.
Attempt `attempt-egress-wider-v0-2-2-descendant-dns-helper-loopback-first`.

The test uses the validated PowerShell `ProcessStartInfo` descendant-launch shape to run Windows `nslookup` against a parent-owned local DNS responder at `127.0.0.1:53`. No Internet endpoint, DNS-setting mutation, hosts-file change, provider call, or machine-wide firewall mutation is used.

## Exact first execution
Job `job-73b747f1e36d` completed with executor return code 0.
- stdout `ee47d457a662ed35d1054c68faee6d8b45cc561a1a9b709f11fcee6bb07882b9`, 3,689 bytes;
- stderr `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, 0 bytes;
- structured first result `9f282456b99ce30a9b5f41be83bba139515353c2e2b88c0afd19dfd79f88b082`, 3,269 bytes.

Positive control, unprotected:
- descendant `nslookup` root exit 0;
- parent-owned DNS responder received 3 DNS query datagrams;
- each observed query received a response; responder errors empty.

Protected discriminator:
- AppContainer verified true; immediate Job verified true; capability count 0; inherited handles false; timed_out false; protected root exit 0;
- parent-owned DNS responder received **zero DNS query datagrams**.

The listener is the decisive network signal. `PROTECTED_ROOT_EXIT_0 != DNS_DENIAL_PROOF`; qualification comes from observed positive DNS traffic unprotected versus observed zero DNS traffic protected under the same root/child/helper/server shape.

## Qualified claim
> On this tested Windows host/source/control boundary, the preserved PowerShell/Process.Start descendant `nslookup` reaches a parent-owned loopback DNS server and receives responses when unprotected, while the same root/child command under the zero-capability AppContainer + immediate Job primitive produces no DNS query at that server.

This qualifies only **descendant DNS-helper loopback non-delivery** for the exact tested path.

## Explicitly unearned
- Windows system-resolver denial;
- Internet DNS denial;
- DNS-over-HTTPS/TLS;
- QUIC;
- arbitrary UDP beyond prior bounded evidence;
- proxy/environment/helper generality;
- browser/plugin/import paths;
- COM/RPC/service/WSL;
- Job breakaway/process-tree escape resistance;
- production launch-site integration;
- `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as runtime fact.

`DNS_HELPER_LOOPBACK_DENIAL != SYSTEM_RESOLVER_DENIAL`
`DNS_HELPER_LOOPBACK_DENIAL != INTERNET_DNS_DENIAL`
`DNS_HELPER_RESULT != DOH_OR_DOT_RESULT`
`BOUNDED_DNS_HELPER_PASS != NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`

## Next frontier
Do not repeat this DNS-helper loopback path as a broader claim. Continue with a materially distinct bypass class—prefer process-tree/Job breakaway or proxy/environment indirection before any provider transport—and preserve a NEW Attempt before execution.
