# Governance Contact v1.0 Pending Carrier — Main Awareness — 2026-09-06

Status: **PUBLISHED DETACHED RELEASE CARRIER / NOT ACTIVE / ZERO AUTHORITY EFFECT.**

Public Main branch advanced:
`287c0bad0e9b3fef3002b91702e86b410cada4ce` -> `6ea95275cdc409ed222e4720b6b04aadaa17e6bf`.

Commit subject:
`chore(authority): publish Governance Contact v1.0 detached release`.

Delta scope is `authority/rahl-sop/**` only. No Core semantic/runtime source changed. Core qualification anchor remains `a7b4511734b1a1e507230308e75b31175aef4c4a`.

`authority/rahl-sop/CURRENT.md` is byte-identical across the old/new Main heads, SHA `b67afd696dff0687343e241fb32a0803eec2f57bd51830a8221e3707939a092a`.

Therefore current universal authority remains:
- sealed R4.4 base `04f3e94efe8c901cc83a12a9c8531be8a9bb350728b8f9eba53db0fd082b3bbc`;
- active ICF-CS v1.1 standard `62be845da364ae81f59b6320c9b34b136236bf5be8aa8036018da48efcb754f4`.

Governance Contact v1.0 release carrier:
- ZIP SHA `c4ab4a516e088b6c28b5240d6b3877d2e3fb889a8bbbfd406e8e0c73bebdd1ae`, 47,754 bytes, 18 members, CRC/testzip clean;
- detached release receipt SHA `cf2e7bd8e5ed613d3c3a99b7f8645833ddb742ac4939bd1719092b277ef286e6`;
- package qualification receipt SHA `509aba0bb859db49d9311e08acae98d8c7bdfbbb1d41cdd157d1675e70f8a302`;
- deterministic seal result SHA `1e77ffa3c779d6332712814dc4ba02ef9a05513eedab6f2d6935b95a49d9da8a`;
- frozen target inventory SHA `4f06428c7b57d8f134d2cf9750a80655f11bb9bcdec869445a2542dd45b8f0e9`.

Complete local semantic read of the exact ZIP payload:
18 readable members / 2,303 source lines / 2,357 deterministic stream lines / stream SHA `ae5e645ffaab627ae0959bf6780591bd0dae622a91cad265b39c1885b7ac75ff`.

Clean-extraction `VERIFY_RELEASE.py` replay:
`PASS: GOVERNANCE_CONTACT_RELEASE_PACKAGE_QUALIFIED_INTERNAL`, with no runtime byproducts.

The release itself repeatedly binds:
- `AUTHORITY_EFFECT = NONE_PENDING_RELEASE_LIFECYCLE`;
- `DETACHED_RELEASED != TARGET_PUBLISHED`;
- `TARGET_PUBLISHED != REPOSITORY_ADMITTED`;
- `REPOSITORY_ADMITTED != LOCAL_AUTHORITY_RECONCILED`;
- `LOCAL_AUTHORITY_RECONCILED != POST_PUBLICATION_READBACK`;
- `POST_PUBLICATION_READBACK != ACTIVE`;
- `CARRIER_PRESENT != PROJECT_SPECIFIC_AUTHORITY_REWRITE`.

Detached receipt target lifecycle counts are all zero: published 0, repository-admitted 0, locally reconciled 0, post-publication readback 0.

This project therefore records the carrier and branch-head movement but does **not** promote Governance Contact v1.0 into active local or universal authority.
