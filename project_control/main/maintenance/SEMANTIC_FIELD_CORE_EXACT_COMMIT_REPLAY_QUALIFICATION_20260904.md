# Semantic Field Core v0.1 — Exact Committed-Artifact Replay Qualification

Date: 2026-09-04 UTC
Mode: BUILD-COMMIT
Role: R5 Reality Pressure Engine
Canonical process: RAHL Engineering Canonical SOP R4.2
Status: **PROMOTION_READY_WITH_EVIDENCE — SOURCE INTEGRATION; PUBLIC MAIN PROMOTION REMAINS A SEPARATE GATE**

## Claim boundary
This receipt qualifies the exact local semantic-field source commit for bounded source integration based on the evidence below. It does not itself advance public `main`, create release authority, certify security correctness, make language-specific lowerers canonical, or authorize App to copy Core implementation.

`PROMOTION_READY_WITH_EVIDENCE != PUBLIC_MAIN_PROMOTED`
`SOURCE_INTEGRATION_READY != PACKAGE_DESCRIPTION_CLEAN`
`CONTROL_CHECKPOINT != PRODUCT_PROMOTION`

## Exact lineage
Qualified public Main baseline:
`1b8f6bdc97387ce33d15de2bd3435bbbd0ade2a9`

Candidate commit:
`a7b4511734b1a1e507230308e75b31175aef4c4a`
subject: `forge: add canonical semantic field core`
parent: exact qualified Main baseline above.

Verified candidate/replay working state before and after replay:
- HEAD exact `a7b451...`;
- tracked working tree clean;
- public GitHub `main` independently remained `1b8f6bd...`;
- no GitHub `pcmmad/semantic-field-core-v01` branch existed at the pre-publication check;
- the local candidate's configured origin is a local App-source clone, not GitHub, so remote/public currentness was checked independently rather than inferred from local `origin`.

## Exact candidate delta
Nine readable files relative to qualified Main:
1. `docs/SEMANTIC_FIELD_CORE.md` — SHA `b8aa50ae873893a7c53a6b7ae78a3ebde2f3451f7bec95808d731b61c1c0d946`
2. `examples/verify_build.py` — SHA `04cc5995a34fa478c3db2289c75c5640e7483b778d9f333189c907d5d575b676`
3. `singularity_works/__init__.py` — SHA `e61851a5f11614f4db866bddc9d0d9113d3c774f419f4e93d8f8988159643714`
4. `singularity_works/semantic_field.py` — SHA `b130e05f631d72d84a14d300647089e124a832e30ec7619f62083269ca1188ec`
5. `singularity_works/semantic_field_bridge.py` — SHA `d8fe6650895409c3b80f78291af78c71552f0337c003b4f65ad5ac717d5e1c94`
6. `singularity_works/semantic_field_delta.py` — SHA `4c325afc881cb43077544a515268bb6f9626d565a86aa36a12543ab4c9be2274`
7. `singularity_works/semantic_field_index.py` — SHA `ef5a2d24ff0c9149ce6684f424928b84b256486557d550a2691730838738a831`
8. `singularity_works/semantic_materializer.py` — SHA `ffc2c7b839409c52ffc21ab8ea362ad979a2ace938850b529be6267e1176f2f4`
9. `tests/test_semantic_field.py` — SHA `516e67f9390e69d194b93e973beb963dc147ec6ffc6af6cfca7f45639a6de485`

`git diff --check 1b8f6bd..a7b451` PASS.
Changed-file machine-private/credential/private-key scan: 0 findings.

## R4.2 linear semantic admission
All nine candidate-readable files were read completely in deterministic order before replay interpretation.

- 9/9 files;
- 72,474 readable bytes;
- 1,735 lines;
- semantic-read stream SHA `0f63c6295532d6c0cbf385b588a6719db7220fd13dff7817485d09015704db16`;
- no source-level contradiction found that blocked replay admission.

Directly re-grounded ownership/authority semantics:
- Core/Main owns the semantic-field implementation;
- App/other consumers should depend on `semantic_field_bridge`, not donor/parser/security lab adapters;
- bridge schema `singularity-works.semantic-field-bridge/0.1`;
- source/evidence referents are exact/hash-bound;
- mutable bundle construction must verify before frozen snapshot admission;
- frozen index/projection authority remains NONE;
- exact fact revision identity is distinct from semantic continuity identity;
- generic evidence text/fingerprint is not automatically semantic meaning;
- explicit provider implementation identity may be semantic when the lowering states it;
- materialization remains evidence-bound, reversible, preconditioned, authority NONE, and requires re-lowering/readback for semantic correctness;
- FactBus / UniversalSemanticIR / existing Blueprint/LBE analysis models remain distinct rather than being silently replaced;
- parser/security/language-specific lowerer ownership is not promoted by this candidate.

## Exact committed replay — source gates
From exact replay HEAD `a7b451...`:
- `python -m compileall -q -f singularity_works`: PASS rc0;
- `python -m unittest discover -s tests -p test_semantic_field.py -v`: **8/8 PASS**;
- `python examples/verify_build.py`: PASS rc0;
- tracked source clean before and after replay.

The eight semantic-field tests cover:
1. coexistence with legacy Fact / UniversalSemanticIR;
2. frozen index projection == canonical scan, including UNKNOWN handling and authority NONE;
3. source drift rejection;
4. evidence-text change as revision refresh rather than semantic meaning change;
5. explicit provider implementation identity as semantic identity when declared;
6. materializer exact apply/inverse plus stale-source rejection;
7. stale index rejection across snapshot identity change;
8. bounded bridge descriptor/read surface.

## Full verification report
Exact replay generated:
`build_verification_summary.json`
- bytes: 190,995;
- lines: 5,737;
- SHA `78d11c30fdb0d10ea1e32b86b132f9c46d4ec381f0e9f2217069585efff5e94a`.

The report was read completely before promotion interpretation.
Verified discriminator behavior:
- compile true;
- good assurance GREEN;
- intentionally bad assurance RED;
- bad remediated GREEN;
- security assurance RED;
- security remediated GREEN;
- execution assurance RED;
- execution remediated GREEN;
- semantic-field tests passed;
- self-verification passed.

Self-audit totals:
- pass 6,614;
- warn 29;
- fail 0;
- residual 0.

The 29 warnings are inherited simplification-review debt in existing modules. The five new semantic-field production modules each self-audited 73 pass / 0 warn / 0 fail / 0 residual.

## Exact wheel boundary
Build frontend probe showed `python -m build` unavailable in the active control Python. R4.2 strongest-sufficient-plane fallback used:
`python -m pip wheel . --no-deps --wheel-dir <isolated-dir>`.

Exact candidate wheel:
`singularity_works-1.0.0-py3-none-any.whl`
- bytes: 335,085;
- SHA `0cccdbc37f25fc875ee5fc957aa50d67910d6ac1951ac52dd28457bee219d4a6`;
- ZIP CRC PASS;
- 100 wheel members;
- 93 `singularity_works/` package members;
- no `.pyc`, `__pycache__`, Git, or semantic-read scratch artifacts;
- all five semantic-field production modules present.

The installed wheel metadata/WHEEL/entry points were semantically read through exact byte-preserving text surrogates where the server reader rejected extensionless `METADATA` by filename.

Console entry points remain:
- `forge = singularity_works.cli:forge`;
- `forge-hud = singularity_works.cli:forge_hud`.

## Parent-wheel control
To resolve the earlier non-like-for-like 88 KB working-tree wheel memory, an exact `git archive` snapshot of qualified Main `1b8f6bd...` was built with the same `pip wheel --no-deps` frontend/environment.

Qualified Main parent wheel:
- bytes: 320,864;
- SHA `b3198eefd3f74034526e0d3490d007ed08051499a1c8fd87c4423b449fa81c62`;
- 95 total wheel members;
- 88 package members.

Candidate vs parent:
- candidate adds exactly five package members: `semantic_field.py`, `semantic_field_bridge.py`, `semantic_field_delta.py`, `semantic_field_index.py`, `semantic_materializer.py`;
- candidate removes no wheel members;
- compressed wheel byte delta: +14,221.

Therefore the 335 KB candidate wheel is consistent with the current qualified-Main packaging surface plus exactly the five new semantic-field modules. The historical ~88 KB wheel is not a valid like-for-like comparator for this replay.

## Fresh installed-surface replay
A new venv was created outside the source tree and the exact wheel was installed with declared dependencies.

Results:
- venv creation PASS;
- full wheel/dependency install PASS;
- `singularity_works` imported from the fresh venv `site-packages`, not the replay source directory;
- all five installed semantic-field module bytes exactly equal their candidate source bytes;
- bridge smoke PASS with schema `singularity-works.semantic-field-bridge/0.1`;
- bridge descriptor authority NONE / target_execution false;
- indexed fact projection PASS / projection authority NONE;
- installed `forge --help` PASS;
- safe external file scan PASS, GREEN, 0 findings, Max CVSS 0.0.

The safe-scan reports were read completely:
- JSON SHA `dc456e98e05758c0830eb9b8e2b3916ee097286d2efbb1d7b7cf40b92d3efa8c`, 448 bytes, 17 lines;
- Markdown SHA `0f2dadafe7b9eca51ac65f1126737207ea8d8dac7ddfa325e76a9ad4a3a22739`, 1,387 bytes, 34 lines;
- findings 0;
- taint chains 0;
- warrant coverage 1.0 / 29 of 29 claims.

## Inherited packaging-description debt — does not originate in candidate
The wheel's long description/metadata is inherited from the qualified-Main packaging configuration/README and contains stale product-description/counter text, including older self-audit counters and an old module-count description. A same-frontend exact parent build establishes that this metadata surface already exists on qualified Main and was not added by the semantic-field candidate.

This is a real documentation/package-description debt and SHALL remain visible. It does **not** invalidate the candidate's semantic-field implementation or installed byte identity, but it should be repaired in a separately scoped packaging/documentation pass rather than being silently folded into this bounded semantic-field source integration.

`INHERITED_METADATA_DEBT != CANDIDATE_SEMANTIC_REGRESSION`
`PACKAGE_DESCRIPTION_CLEAN != INSTALLED_SURFACE_CORRECT`

## Verdict
Exact commit `a7b4511734b1a1e507230308e75b31175aef4c4a` is:

**PROMOTION_READY_WITH_EVIDENCE for bounded semantic-field source integration.**

Evidence earned:
- exact qualified-Main parent;
- complete R4.2 candidate semantic read;
- compile PASS;
- 8/8 semantic tests PASS;
- full verify_build discriminator PASS;
- 6,614 pass / 29 inherited warn / 0 fail / 0 residual self-audit;
- exact wheel build and parent-wheel control;
- exact installed module identity;
- installed bridge/CLI/safe-scan smoke PASS;
- source diff hygiene/privacy scan PASS;
- tracked replay source remains clean.

## Authority / next gate
This verdict does **not** itself authorize or claim public `main` advancement.

The next safe durability action is to publish the exact candidate commit to a dedicated remote candidate branch `pcmmad/semantic-field-core-v01`, non-force, after confirming the remote branch still does not exist. Candidate-branch persistence does not change qualified public Main and does not make App a consumer.

Public Main promotion requires a separate explicit promotion action/gate with current remote-main readback, exact candidate lineage, and post-promotion App handshake if/when shared Core actually advances.
