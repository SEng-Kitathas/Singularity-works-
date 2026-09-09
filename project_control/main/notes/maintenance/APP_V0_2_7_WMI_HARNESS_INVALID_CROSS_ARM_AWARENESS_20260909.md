# App v0.2.7 WMI HARNESS_INVALID — Main Cross-Arm Awareness

Date: 2026-09-09 UTC
Status: **CROSS-ARM AWARENESS / ZERO MAIN-CORE PROMOTION**

App artifact `01461d5f61a7e1cc85a8365ff11565df7ada1069c46b9a90ea036394dbc762b5` executed once under control `b8c5e6f9c7032e2a25c25ac4b4e50de91183d64c` / CHECKPOINT `59643050ecd2c741ca81253c59f1ce88e9344866a683420a9f90c702d46c1520`. First result `3dbc3f7b0dda8cf13ec3f4d59933d0bdda992b914123e33ee62324fa391bf236` is HARNESS_INVALID / NOT_ADMITTED. Positive WMI `Win32_Process.Create` reached success return but the frozen PowerShell then assigned reserved automatic `$PID`, causing root exit 1 before returned child PID/liveness/lineage could be captured; protected phase was not reached. Diagnosis `6f0c88e6419a09c60d969a5c9ab58e04e0642898fcf3a5b9637ebda79dd07655`.

No WMI containment/denial claim and no Main/Core promotion. NEW App v0.2.7.1 may repair only the local PID variable after checkpoint.
