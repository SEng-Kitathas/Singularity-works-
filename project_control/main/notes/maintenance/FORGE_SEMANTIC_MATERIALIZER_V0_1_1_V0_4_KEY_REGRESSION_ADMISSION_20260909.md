# Forge Semantic Materializer v0.1.1 — v0.4 Semantic-Key Regression Admission

Date: 2026-09-09 UTC
Status: **BOUNDED REGRESSION PASS / MATERIALIZER IDENTITY CONTRACT MIGRATED TO SNAPSHOT-DELTA V0.4**
Control: `83a3a9479282ef76984df3a028de561f04b76189` / CHECKPOINT `b5fb165270e11853cc86071c77868ab05eabdc4edf9e5f2ca852736695e6f8da`.

Materializer `904adf12d86a32a64cf74a42e297e2c6029282cd79c6abd89eb77374b1fcf089` changes only semantic-key dependency v0.3 -> v0.4 plus version label. Regression harness `d8f98002d16cba7a54f51c9bea1a7d286a482a5cb6bc6303924efa8805763e26` uses the same 26 materialization/rollback checks with its oracle and receipt metadata also bound to snapshot-delta v0.4.

First execution PASS 26/26. Exact summary/stdout `20ce4577eda90690147f919f532cbea803ec97552b3a71775f4c726661916604`. Selected route semantic key is now `sem:cbcebb9cb857a8d6962fe58f`, matching the current replay/bridge identity. Exact source/evidence preconditions, deterministic patch, authority NONE, stale-precondition rejection, observed single semantic removal, stale-index rejection, exact inverse rollback, route-count restoration and untouched real PyGoat target all passed. PyGoat remained clean at `19d17cc8874861142b330636d068bbde54e86b85`.

This admits only the materializer's v0.4 semantic-key migration without regression on the bounded PyGoat route-removal contract. It does not itself qualify the replay->materializer bridge.

`MATERIALIZER_V0_1_1_KEY_MIGRATION_PASS != BRIDGE_QUALIFICATION`
`SEMANTIC_INTENT != UNIQUE_SOURCE_SYNTAX`
`MATERIALIZER_AUTHORITY = NONE`
