<!-- CONTROL SNAPSHOT TEMPORAL SCOPE: This is an immutable historical awareness receipt. Its statement that public Main remained `287c0bad0e9b3fef3002b91702e86b410cada4ce` was true at receipt creation and is superseded by current repository head `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`. Core qualification anchor remains unchanged. The server-source receipt SHA remains `ab37477b15980ef457d88bc6fe01d37321605b97163e1d0496e6ecba0074af56`. -->

# Main Awareness — App Egress Protected-Process Primitive v0.1.2 — 2026-09-06

Status: **CROSS-ARM AWARENESS ONLY / NO MAIN CORE SOURCE MUTATION.**

Current App source:
`forge/app-shell-rd@43aa7feac7e8a15828116bd700b644560714496d`, local/remote exact, clean and independently fresh-clone verified.

Current recovery ingress:
Gen14 `checkpoint-app-live-0014-43aa7feac7e8`, blob `4efabde670986f65fc3e1736452300b299f79045e5b537ea46425e1dbbbd2136`, evidence SHA `bc4bbddd0addc9be743ca01d7f022b2d2b1228373e1eac7d181937a008a32c50`, VERIFIED/RESUMED/STABLE/LKG/source MATCH/NORMAL.

App bounded qualification:
`notes/maintenance/EGRESS_PROCESS_PRIMITIVE_V0_1_2_BOUNDED_QUALIFICATION_20260906.md` SHA `3d27639447f1d47ac71e892a766444a3e7c8627ff3120b791ecf4470ebeedda6`, preserved in App Attempt Store as `attempt-egress-process-primitive-v0-1-2-bounded-qualification`.

Evidence:
- original Attempt-0 D0/D1/D3 PASS, D2 FAIL preserved at `a06c763d85ed605261a7624c384534b31ffd9425b42976c8f63d4d0437829a60`;
- v0.1.1 first repaired D2 remained FAIL rc1 at `11fbb751b5f6d35be296bda41b3bb0f4d5d26926b1e66e3a0a629b0dc41edeec`;
- first committed v0.1.2 D2 PASS `5919cdc7af94d0e34d5884366eb3f328762422c03f2346afd332690820863b68`;
- same-commit D0-D3 regression PASS 4/4 `1a571cae54279aa4b79646b87dfb254701957088d481bc7b0de7c832935055fa`.

Protected-process implementation remained unchanged at Git SHA `80163d67a40b7604920f70d25a23d982c73dd368a62f8872c7632ca1e1904790`. The v0.1.2 change is the descendant discriminator/harness lineage only.

Qualified bounded claim: on the exact tested Windows host/source/test boundary, the zero-capability AppContainer + immediate Job primitive passed the committed D0-D3 loopback/process-tree discriminators, including a positive-control-backed PowerShell/Process.Start descendant curl discriminator.

Not qualified: general external egress containment, DNS/UDP/QUIC/proxy/helper/plugin/COM/RPC/WSL/breakaway resistance, production launch-site integration, broker/Gate allow path, provider safety, checkpoint Core identity, or `NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT` as runtime law.

Main public branch head remains `287c0bad0e9b3fef3002b91702e86b410cada4ce`; semantic Core qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a`. No App pressure from this bounded qualification currently requires a Main/Core code change.

Latest durable cross-thread control `f120ff577cd3a3df438d354ae9cd0662d037663f` predates App `43aa7fe...`/Gen14/bounded qualification. The next normal control checkpoint should absorb the new state before wider bypass/production-integration attempts.
