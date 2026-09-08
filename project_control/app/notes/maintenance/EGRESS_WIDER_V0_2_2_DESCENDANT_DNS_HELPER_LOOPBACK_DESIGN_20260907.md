# Wider Egress v0.2.2 — Descendant DNS Helper Loopback — Pre-Execution Design

Date: 2026-09-07 UTC
Status: **FROZEN CANDIDATE / NOT YET EXECUTED**
Parent: `attempt-egress-wider-v0-2-1-3-descendant-udp-loopback-cwd-repair-first-result` (`86833629...`).
Artifact: `state/attempt_artifacts/EGRESS_WIDER_V0_2_2_DESCENDANT_DNS_HELPER_LOOPBACK_20260907.py`
SHA-256: `728daddb02e092f5726d023ef2ca895b93950bba0be0c998b0797aabe6969b2f`

This is materially distinct from generic UDP: a descendant `nslookup` helper is launched through the validated PowerShell `ProcessStartInfo` shape against a parent-owned DNS responder at `127.0.0.1:53`. No Internet endpoint or DNS-setting mutation is used. Positive control must deliver an actual DNS query and receive a minimal local A response. Protected phase uses the identical root/child command and treats parent-listener query receipt as decisive.

Claim ceiling: `BOUNDED_DESCENDANT_DNS_HELPER_LOOPBACK_ONLY`. It does not establish system-resolver denial, Internet DNS denial, QUIC, proxy/helper generality, breakaway resistance, or the product-wide runtime law.
