# Wider Egress v0.2.7.2 — WMI HRESULT Encoder Repair — Pre-Execution

Date: 2026-09-09 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent diagnosis: `71898d70a9fcb7758eaeffd344761d5d1f1d92d02edc198a3896bcc765abb04a`.
Durable control: `dbe988b4a6773a79d31935b46984b17fb9c4c421` / CHECKPOINT `f84f5b8886dd56c7c9ec8baa52c34f5c08a3e1890074f76188d9e110a58e6f67`, fresh-clone PASS 201.
Artifact SHA: `4bf2403ee909154172512bd0c3d0c681fe47c048ffb1eae741331005b005f9dc`.

Behavioral delta from immutable v0.2.7.1: only the two WMI exception encoders change. `[uint32]$_.Exception.HResult` is removed; each catch masks the signed HRESULT directly with `-band 0xFFFF`, preserving class-bind prefix `0x20000000` and Create-invocation prefix `0x30000000`. All WMI creation/supervision/protected behavior remains unchanged.
