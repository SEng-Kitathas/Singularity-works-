# Control Currentness — Forge Materializer v0.1.1 v0.4 Key Migration PASS — 2026-09-09

Status: **FORGE CORE BOUNDED REGRESSION QUALIFICATION / BRIDGE STILL OPEN**
Predecessor control `83a3a9479282ef76984df3a028de561f04b76189` / CHECKPOINT `b5fb165270e11853cc86071c77868ab05eabdc4edf9e5f2ca852736695e6f8da`, fresh-clone verifier PASS 263.

Materializer v0.1.1 `904adf12d86a32a64cf74a42e297e2c6029282cd79c6abd89eb77374b1fcf089` changes only semantic-key dependency snapshot-delta v0.3 -> v0.4 plus version label. Regression harness `d8f98002d16cba7a54f51c9bea1a7d286a482a5cb6bc6303924efa8805763e26` preserves the incumbent 26 checks with the current v0.4 oracle.

First execution PASS 26/26. Exact summary/stdout `20ce4577eda90690147f919f532cbea803ec97552b3a71775f4c726661916604`; admission `2db1b63f2e66ef3e6f23e9bbc1e1125aab6c035531fcf8bece7f77f364fbdea2`. Selected semantic key is now `sem:cbcebb9cb857a8d6962fe58f`, matching current replay/bridge identity. Exact patch/inverse, stale-precondition rejection, observed single semantic removal, exact rollback and untouched PyGoat target all passed.

This closes only materializer semantic-identity migration. Delta->Patch bridge v0.1 remains NOT_ADMITTED and non-replayable; NEW bridge v0.1.1 is allowed only after this checkpoint is fresh-clone durable.
