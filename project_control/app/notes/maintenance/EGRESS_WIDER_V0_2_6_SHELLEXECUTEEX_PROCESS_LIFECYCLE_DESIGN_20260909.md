# Wider Egress v0.2.6 — ShellExecuteExW Process Lifecycle — Pre-Execution Design

Date: 2026-09-09 UTC
Status: **FROZEN CANDIDATE / NOT EXECUTED**
Parent admission: `99b28994df07e35b604865adf57ca193d19ee3991232a0e68c76b64cf3f45cd8`.
Durable control: `8a401838b8e4d5d8b0be669ac98a9bdaec37580d` / CHECKPOINT `28904a9d34ebc80b46eec719a1987acdebc92c476458357dbe3cf772b369b1a2`.
Helper source `312d666b624bd182a4c201090cd5ecd9da5996ab96fbc5df4c799a3b7496e28d`; helper DLL `8922a45ce1814a86edbed007a6e444f0f42556b3e3e5a67f30b16552c98892b4`.
Artifact SHA `1f2bd6a10477b3c03119420e98044068f96d7fd039b2a12c098f2312c51fff41`.

This is a distinct ShellExecuteExW launch API path, not a repeat of direct CreateProcessW breakaway flags. Helper probe 43 was verified both unprotected and under the AppContainer+immediate-Job primitive before freeze. The helper uses `SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI`, verb `open`, exact system PowerShell, and a 30-second sleep child.

Positive requires returned PID alive after root exit plus cleanup. Protected requires verified AppContainer/immediate Job/zero capabilities/no inherited handles. A protected launch failure qualifies only bounded protected ShellExecuteExW denial, not Job-specific denial. A protected returned child alive after Forge Job close is bounded bypass evidence for this path; returned child absent after close is bounded containment evidence.

`SHELLEXECUTEEX_PATH != PROVEN_OUT_OF_PROCESS_BROKER`
`PROTECTED_SHELLEXECUTEEX_DENIAL != JOB_SPECIFIC_DENIAL`
`SHELLEXECUTEEX_RESULT != ALL_PROCESS_TREE_ESCAPE_RESISTANCE`
