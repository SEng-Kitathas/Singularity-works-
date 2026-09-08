# Wider Egress v0.2.5.4 — Explicit Breakaway Positive-Criterion Repair — Pre-Execution

Date: 2026-09-08 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Control `2726d4edbfa2d1af3977b4dda81c26da9385320d` / CHECKPOINT `6378560c5ed9993a302fc88386cb47d789cdc01f8895fa99e460dbc0b90bd264`.
Plane record `de4e66d5a24666dea371088290a133085566f2965b309e1f6d1d0da216d91a04` = `0x1800`, explicit+silent breakaway true.
Parent result `27af68192010146a421ea95900407bdc58c47984496fba98a163bbfc069854bf`.
Artifact SHA `1f7db5a043a755c0598f572de8ce2da979abe2de8ec5e40d52db66a18a9eb24e`. Helper source/DLL unchanged `77927e4f...` / `8019c83a...`.

Behavioral repair: remove only the positive rejection requiring `IsProcessInJob(child,NULL)==false`. Positive still requires exact explicit-child creation success, child alive after helper/root exit, and successful cleanup; any-Job membership remains recorded. Protected branch is unchanged: verified in-Forge-Job `ERROR_ACCESS_DENIED` is bounded denial; explicit creation success followed by a child still alive after `run_zero_network_process` closes the immediate Forge Job is bypass evidence.

No network activity. No prior Attempt replay.
