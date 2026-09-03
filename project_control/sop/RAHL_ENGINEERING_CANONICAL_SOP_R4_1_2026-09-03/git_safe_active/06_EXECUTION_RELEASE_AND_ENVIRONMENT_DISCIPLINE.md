# 06 — Execution, Release, and Environment Discipline

### E01 — Name the discriminator
Before consequential execution, name what the run can distinguish. Tool work must advance the discriminator or preserve evidence.

### E02 — Durable run receipt
Consequential or durable runs SHOULD record, where applicable:
- working directory;
- interpreter/runtime/toolchain identity;
- consequence-bearing environment variables/configuration;
- start/end timestamps;
- process/job identity;
- stdout and stderr;
- exit code;
- completion marker/status;
- stable artifact paths;
- input/output hashes or identities where needed.

### E03 — Completion is not consequence
Inspect final artifact/state/effect. Tool completion is not task success.

### E04 — Ambiguity remains UNKNOWN
Timeout, disconnected foreground, partial output, submitted job, started job, completed process, and registered artifact are distinct states. Do not infer across missing readback.

### E05 — Mutation claims require readback
Do not claim saved, written, executed, committed, tested, verified, uploaded, extracted, registered, synchronized, or promoted without the corresponding evidence surface confirming it.

### E06 — Release/package qualification
Sealed/release artifacts require exact membership when claimed, manifest/hash identity, clean extraction/replay where relevant, explicit lineage, assurance ceiling, and exclusion of accidental runtime state.

### E07 — Verifier purity
Verification must not silently contaminate the specimen. Isolate generated state when needed.

### E08 — Membership vs identity
Completeness of the selected set and identity of present members are separate checks.

### E09 — Common-mode declarations
A verifier and specification sharing one mutable declaration is a common-mode trust boundary unless a distinct witness exists.

### E10 — Environment identity contract
For evidence where environment can change meaning, explicitly name:
1. subject identity;
2. authoritative representation (sealed bytes, repository object, checkout form, parsed object, runtime state, semantic replay, etc.);
3. admissible transformations;
4. consequence-bearing environment dimensions;
5. assurance class actually verified;
6. residual dimensions not sealed.

Repository normalization policy is artifact-class relative. A fresh clone/materialization gate exercises a different surface from an existing working tree.

### E11 — Portable evidence surfaces
Prefer machine-readable evidence protocols over parsing human-formatted error/traceback text when evidence is load-bearing.

### E12 — Archive transport
When an archive must cross transport size limits, verify the canonical unsplit archive first, then split below the smallest relevant limit. Record configured part size, part hashes/order, and a deterministic reassembly/verification method. No fixed transport limit is universal SOP law.

`LOCAL_EXECUTION_COMPLETE != ASSISTANT_READBACK_COMPLETE`
`ARTIFACT_REGISTERED != CHAT_RENDERED`
`SUBMITTED != STARTED`
`STARTED != COMPLETED`
`COMPLETED != REGISTERED`
`SEALED_ARTIFACT != SEALED_ENVIRONMENT`
`LOCKED_BYTES != CHECKED_OUT_BYTES`
`NORMALIZED_EQUIVALENCE != SEALED_BYTE_IDENTITY`
`PORTABLE_GATE != WEAKER_GATE`
`SEALED_ENVIRONMENT != REPRODUCED_ENVIRONMENT`
`IDENTITY_POLICY_IS_ARTIFACT_CLASS_RELATIVE`
