# GitHome Project Context v0.1 — Qualification — 2026-09-09

Status: **READY_WITH_EVIDENCE — BOUNDED READ-ONLY PROJECT/GIT OBSERVATION + FRONTEND NAVIGATION MODEL**  
Authority: App frontend project-navigation only. No Forge semantic, Git mutation, remote/provider, Vault, or runtime authority.

## Lineage
WorkBench v0.1 prerequisite admission: `ad1e85f27e8ed61db5777341aaa3efe502988ba2a3dfc8897766d99129bacaea`.  
GitHome Attempt-0 commit: `3a1442283e75ec3b887a86a7f12737372f048855`.  
Real-App-repo integration commit: `feae3d7eaf2bad15f3df296d2175be3b8b8de75b`.

Upstream control during qualification: `d9b7c5e8b1854b705f134a2d6e1dca6acc9a1a47` / CHECKPOINT `b8333e3758cc98edb14c1302744bc3ef44210678dd1122e27648c51def6b588e`.

## Exact committed source at `feae3d7...`
- `forge_app/design/GITHOME_PROJECT_CONTEXT_CONTRACT_v0_1.md` — `1b9ea154885d9b9c0712bea041508c55a9009150c0bf251ed3b16cf8e5e2ab24`;
- `forge_app/shell/githome_model.py` — `4526c229a2046efc9094bf0631d30ff3f531e076e5e820ea02e9dbaa5fede961`;
- `forge_app/shell/__init__.py` — `ec950914bd1a95f862aca5cc36c2489b2701877bf77d23e975fe6b91fdf0e1d3`;
- fixture suite — `f470f36f3a8528277374a5ac30eac36f3a9cb764085a7d86088c23b528d511e3`;
- real-repo integration harness — `7ac55a9466793e87e6390ebbee43190d8a9f11ebca5e6c273b98d4ed9bc7afab`.

Production Git subprocess verbs are statically bounded to `status` and `ls-files`. No production file-write/network primitives were found in the pre-execution scan.

## Fixture pressure
Job `job-15fc79e9123d`, idempotency key `attempt-githome-project-context-v0-1-3a14422-tests-first`:
- **9/9 PASS**;
- rc0;
- exact result `fdb0c564b8490a6cf7c22084b0bd9ea979d87623817d9a92e9330c8e0fba683e`.

The disposable-repository suite verified:
- clean / modified / staged / untracked / ignored / deleted file states;
- deleted tracked paths remain modeled after filesystem disappearance;
- `.git/` internals are excluded while project directories remain complete;
- ignored files stay in the snapshot when hidden from default presentation;
- non-Git folders remain visible without fabricated Git identity;
- deterministic snapshot/model hashes;
- selection/filter/breadcrumb fail closed on invented paths;
- Workbench binding carries only exact hash/bundle/currentness metadata and keeps authority NONE;
- mutation-like Git commands are rejected by the read-only reducer.

## Real App repository pressure
Job `job-d053dfcaa0d7`, idempotency key `attempt-githome-real-repo-integration-v0-1-feae3d7-first`, rc0:
- **18/18 PASS**;
- exact result `0d89b5d244b9d79f420ddd2cb44c9febc48028197aa10a0ed769b44668ab7598`;
- exact observed HEAD `feae3d7eaf2bad15f3df296d2175be3b8b8de75b` on `forge/app-shell-rd`;
- **536 files** + **60 directories** = **596 total project entries**;
- **458 tracked files**;
- **78 ignored files**, retained in the complete snapshot;
- default presentation showed 506 entries while show-ignored exposed all 596;
- snapshot SHA `d9870cac20f20ce509d8c630f699900aa3c2c245275447ac7e8072d41a8c2c55`;
- model SHA `1e1f07777283ba0182206999fde1e6ead007f7347079c0513e3204bf61d11ba7`;
- zero scan errors;
- independent filesystem file/directory counts matched;
- independent Git tracked/ignored counts matched;
- source clean before and after;
- no source mutation.

## Qualified scope
GitHome v0.1 is qualified to observe a local project and Git working tree read-only, retain a complete non-`.git` project snapshot, expose Git currentness/state as a frontend dimension, filter/select/breadcrumb without deleting underlying state, render a cheap text projection, and bind a Workbench model by exact hash/currentness without copying semantic facts into GitHome.

## Not qualified
- Git add/commit/checkout/reset/clean/push/pull/fetch/merge/rebase UX;
- remote provider/API state;
- GitHub/GitLab account authority;
- Vault/secrets classification;
- semantic file overlays or file-to-Fact mappings;
- native windows/docking/input;
- large-repository performance or watch/incremental update behavior;
- symlink-heavy/pathological filesystem coverage beyond the tested behavior;
- semantic or runtime authority.

## Next product cut
Compose the qualified GitHome project-navigation model, Workbench semantic/evidence model, and Ergo recovery/currentness summary into a single renderer-neutral **Forge Shell Workspace** contract. The shell may route focus and panels but SHALL NOT merge their authority domains.

`GITHOME_OWNS_PROJECT_NAVIGATION`  
`FORGE_OWNS_PROJECT_UNDERSTANDING`  
`GIT_STATUS != SEMANTIC_VERDICT`  
`WORKBENCH_BINDING != SEMANTIC_AUTHORITY_TRANSFER`
