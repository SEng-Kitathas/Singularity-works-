# Wider Egress v0.2.5.3 — Explicit Breakaway Child-Membership Repair — Pre-Execution

Date: 2026-09-08 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Durable control: `8071b0945ee7f9a7709eef0ef62c42141a2ebc39` / CHECKPOINT `1002110708b3bd53db376249dd384cfe26dcfb2d6aa6340880124f8cea6cb021`.
Execution-plane record: `df57157d14dff5648027a7fd7d3ab1354f9c4b298f276b44098768ae705cf003` (`0x1800`, explicit+silent breakaway true).
Parent result: `af0ce57433f71ad41dd74f06d922b88bad8fc8f69d0f8ca13496eafb47ab4601` HARNESS_INVALID.
Artifact SHA: `e6913d1b923153a6943b3f3fb34e50c7054f9123a3d940e33d8719d89cf2031d`.
Helper source/DLL remain `77927e4f...` / `8019c83a...` byte-identical.

Repair scope: Python observation only. The helper/root may remain in the outer runSync Job; the positive control now accepts explicit child-creation success, then directly queries the returned sleeping child PID with `IsProcessInJob(child, NULL)` and requires that child to be alive and outside all Jobs before cleanup. Protected success similarly records child liveness/membership after the immediate Forge Job is closed. Any surviving protected child is a bypass regardless of whether it subsequently belongs to another outer Job. `ERROR_ACCESS_DENIED` from an in-Job protected helper remains the only bounded-denial PASS classifier.

No network activity is part of this discriminator.

`ROOT_JOB_MEMBERSHIP != CHILD_JOB_MEMBERSHIP`
`PROTECTED_CHILD_SURVIVAL_AFTER_IMMEDIATE_JOB_CLOSE == BREAKAWAY_BYPASS_EVIDENCE`
`CREATE_FAILURE_ERROR_ACCESS_DENIED_IN_JOB == BOUNDED_EXPLICIT_BREAKAWAY_DENIAL_EVIDENCE`
