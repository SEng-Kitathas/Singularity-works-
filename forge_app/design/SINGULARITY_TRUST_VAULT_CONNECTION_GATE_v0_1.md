# Singularity Works Trust / Vault / Connection Gate v0.1

Status: **WORKING architecture contract** — promoted from sidebar discourse on 2026-09-03.
Authority: App/product security architecture candidate. This is not a claim of cryptographic certification or completed enforcement.

## Security objective
Singularity Works SHALL treat external connectivity, exports, re-imports, credentials, and authority as explicit trust-boundary events.

The safe default is local secure operation. No external connection becomes usable merely because a provider identity is verified or a credential exists.

## Authority model
Locked distinctions:
- `VERIFIED_IDENTITY != AUTHORIZED_CAPABILITY != EFFECTIVE_AUTHORITY`.
- `VERIFIED_PLATFORM != FULL_AUTHORITY`.
- `CONNECTED != ARMED`.
- `OAUTH_SUCCESS != OPERATION_APPROVAL`.
- `TOKEN_SCOPE != OPERATOR_INTENT`.
- `CAPABILITY_AVAILABLE != CAPABILITY_ACTIVE`.
- `AUTHORITY_COMPOSES_BY_INTERSECTION_NOT_UNION`.
- adopted RAHL scar: `OPERATOR_INTENT != PLATFORM_APPROVAL_STATE`.

Effective authority is the intersection of:
1. verified provider identity;
2. credential/token capability ceiling;
3. Singularity Works connector policy;
4. explicit user grant;
5. resource scope;
6. active session arming;
7. consequence class/policy;
8. currentness/identity checks required by the operation.

No layer may silently widen authority granted by another layer.

## Connection Gate
All supported external access should converge through a capability-agnostic **Connection Gate / Egress Broker**.

Target flow:

```text
provider identity
  -> credential / OAuth grant
  -> provider capability ceiling
  -> Singularity Works user grant
  -> resource scope
  -> session arming
  -> consequence gate
  -> effective capability
  -> audit receipt
  -> external operation
```

The Gate must support GitHub, custom OAuth/API providers, model APIs, package registries, cloud services and future connectors without granting any provider a private authority model.

### Required connection receipt fields
Every consequence-bearing external transaction should identify, where applicable:
- WHO / principal;
- WHAT / operation;
- WHEN;
- WHERE / provider + endpoint/resource;
- WHY / operator intent or operation intent;
- connector identity/version;
- credential/grant identity without exposing secret material;
- effective capability;
- resource scope;
- consequence class;
- input/output hashes or object identities where meaningful;
- result/failure;
- approval/arming lineage.

## No ambient networking
Target enforcement law:
**`NO_EXTERNAL_CONNECTION_WITHOUT_GATE_AND_RECEIPT`**.

Application code, plugins, AI tooling, terminals and imported code should not receive ambient unrestricted networking by default. The eventual embodiment should enforce this at an actual process/network boundary, not merely by asking code to call a logger voluntarily.

External repository/API/web content is data, never authority:
- `EXTERNAL_CONTENT != OPERATOR_COMMAND`.
- `REMOTE_TEXT != AUTHORITY`.
- `PROMPT_LIKE_CONTENT != INTENT`.

A repository README, issue, model response or web page cannot mint connector permissions or execute consequence-bearing instructions because it contains imperative text.

## User friction policy
Security gates belong at trust/consequence boundaries, not every harmless read.

Desired UX:
- operator manually connects/arms a provider/resource envelope;
- normal low-consequence operations inside that envelope remain fast;
- higher-consequence operations require stronger confirmation/authority.

Example consequence escalation:
- repository read/fetch: low within armed scope;
- ordinary push to authorized non-protected branch: normal armed consequence;
- publish/package release: elevated;
- protected branch mutation: elevated;
- delete/permission/admin/security configuration: high;
- force push/history rewrite: high/destructive and may be categorically disabled by policy.

## Singularity Vault
The secure storage boundary belongs to the Singularity Works product as **Singularity Vault / The Vault**, not specifically to Forge.

Default law:
**`VAULT_IS_DEFAULT_WORK_SURFACE`**.

WIP and completed projects should remain inside the Vault unless the operator explicitly exports them.

Direct casual output to Documents/Desktop/arbitrary filesystem locations is not the default secure workflow.

### Vault contents may include
- projects/source/Git objects;
- project metadata;
- Attempts/evidence/checkpoints;
- recovery/re-entry state;
- connector credentials/secrets;
- imports/quarantine;
- export receipts;
- recovery bundles.

### Cryptographic target
The target is cryptographic agility with hybrid classical + post-quantum key protection where practical.

Bulk data should use a strong authenticated symmetric cipher with independently generated content keys. Public-key/PQ mechanisms should protect/derive/wrap keys rather than being misused as bulk-file ciphers.

Target metadata should identify at least:
- crypto suite/version;
- key epoch;
- bulk cipher;
- KDF;
- classical key-establishment/signature mechanism where used;
- PQ key-establishment/signature mechanism where used;
- rotation/recovery lineage.

Exact algorithm suite is **not yet qualified in this v0.1 design** and must be selected against current standards/provider/platform support at implementation time.

Locked distinction:
- `ENCRYPTED != RECOVERABLE`.

Key recovery must be deliberately designed so a single machine/TPM failure cannot destroy irreplaceable work. Recovery bundles must themselves be encrypted, independently test-restorable, and evidence-bearing.

## Filesystem export is explicit egress
Locked laws:
- `FILESYSTEM_EXPORT_IS_EXPLICIT_EGRESS`.
- `EXPORTED_COPY != SECURE_CANON`.
- `EXTERNAL_ROUND_TRIP_BREAKS_TRUST_CONTINUITY`.

An export outside the Vault should require deliberate user selection and a two-stage warning/confirmation for raw filesystem egress unless policy explicitly establishes another trusted destination class.

Export receipt should record:
- export ID;
- project/secure ancestor identity;
- checkpoint/currentness identity;
- Git/source revision when applicable;
- tree/file hashes or Merkle identity;
- destination;
- timestamp;
- operator approval;
- reason/classification;
- encryption state;
- connector identity if remote;
- signed/verified manifest identity when available.

## Re-import trust lifecycle
Locked laws:
- `REIMPORTED_COPY != SECURE_CANON`.
- `KNOWN_EXPORT_PROVENANCE != CURRENT_QUALIFICATION`.
- `REIMPORT_NEVER_OVERWRITES_SECURE_ANCESTOR`.
- `PROMOTION_BY_QUALIFIED_DELTA != REPLACEMENT`.

Any code/data that left the secure environment returns through **Import Quarantine** even when Forge/Singularity Works previously exported it.

Target flow:

```text
secure project
  -> export receipt
  -> external descendant
  -> re-import quarantine
  -> lineage recognition
  -> exact delta
  -> LBE semantic/security/quality pressure
  -> tests/sandbox where required
  -> operator review
  -> qualified secure descendant
```

A returning copy must never replace the secure ancestor directly through the normal interface.

### Fast path for exact known return
If an import is bit-identical to a known exported signed/hashed manifest, Singularity Works may classify it `EXACT_KNOWN_EXPORT_RETURN` and use a cheap requalification path. It still crosses the import gate; provenance does not bypass qualification.

## LBE re-import pressure
Re-import analysis should address both security and engineering quality.

Security/effect examples:
- new network destinations/effects;
- filesystem writes;
- credential/secret access;
- privilege expansion;
- subprocess/dynamic execution;
- install/build hooks;
- dependency/supply-chain changes;
- unknown binaries/obfuscation;
- CI/workflow permission changes.

Quality examples:
- semantic contract changes;
- test degradation;
- error-handling regression;
- excessive complexity/duplication;
- dependency bloat;
- performance regression;
- architecture boundary violations;
- evidence/currentness/provenance degradation.

The intent is not merely “malware scan”; it is to keep secure-lineage quality above the promotion threshold.

## Remote-transport honesty
Singularity Works controls its local Vault and connector policy, not every provider's transport/storage implementation.

Connector UX should distinguish:
- local Vault protection;
- transport protection/currentness;
- provider-controlled at-rest state;
- whether remote plaintext access is inherently required for the provider feature;
- whether a user policy requires a stronger transport mode than the provider can prove.

Do not display a generic “post-quantum secure” badge for a path whose remote side cannot substantiate that claim.

## RAHL ancestry donor pressure
The following ancestry scars are especially relevant and should be pressure-tested before project-local promotion:
- `CALLER_CONSTRUCTIBLE_GRANT != CAPABILITY`;
- `GRANT_FOR_REQUEST_A != GRANT_FOR_REQUEST_B`;
- `REQUEST_IDENTITY_IS_PART_OF_CONSEQUENCE_AUTHORITY`;
- `CALLER_SUBJECT != ARTIFACT_SUBJECT_UNLESS_BOUND`;
- `PROCESS_AUTOMATION_AUTHORITY != ARTIFACT_RELEASE_AUTHORITY`;
- `ARTIFACT_DENIAL != PROCESS_QUARANTINE_AUTHORITY`;
- `UNVERIFIED_TEMP_BYTES_CAN_REACH_PUBLICATION_BOUNDARY`;
- `TEMP_VERIFIED != PUBLISHED_BYTES_VERIFIED`.

These are donor candidates, not automatically canonical product law merely because they are useful.

## Manual parity
Connection and security QOL should also respect:
**`AUTO_CAPABILITY_WITHOUT_MANUAL_OPERATOR_PATH == INCOMPLETE_CAPABILITY`**
unless a concrete safety reason justifies no manual path.

Examples that should remain manually accessible:
- arm/disarm connector;
- inspect active grants;
- revoke grant;
- inspect receipts;
- export/import/requalify;
- manually quarantine a project/import;
- manually request LBE requalification;
- inspect why an operation was denied.

## v0.1 non-claims / open seams
Not yet embodied or qualified:
- actual process/network sandbox enforcement;
- OAuth implementation;
- secret-store implementation;
- final cryptographic suite/key hierarchy;
- hardware-backed key policy;
- Vault filesystem/container format;
- export receipt signature format;
- remote provider transport attestation;
- re-import semantic/security pipeline implementation;
- GitHub connector grant model;
- human UX/confirmation testing;
- enterprise/multi-user authority delegation.
