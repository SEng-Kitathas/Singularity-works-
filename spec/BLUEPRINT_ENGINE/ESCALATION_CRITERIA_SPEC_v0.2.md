# Logic Blueprint Escalation Criteria Spec v0.2
_Supersedes v0.1. Architect-validated 2026-04-04._

## What Changed from v0.1

v0.1 was output-driven — it escalated based on what the front gate *emitted* (red, amber,
suspicious-clean). That's necessary but insufficient. Code has structural, semantic, contextual,
and domain properties that demand LBE treatment regardless of what the gate says.

v0.2 adds:
- The Squeaky Clean Whitelist — defines what does NOT escalate, routes everything else
- Class E: Structural Complexity (input-driven, gate-agnostic)
- Class F: Semantic Role Mismatch (named behavior vs actual behavior)
- Class G: Temporal and Concurrent Patterns
- Class H: Alien/Novel Input (expands A2 significantly)
- Class I: Residual Obligation Density
- Class J: Domain-Specific Mandatory Review
- Class K: Effect Surface Without Validation
- Expanded Class A (residuals now hard-escalate)
- Expanded Class B (context/provenance, trust gap, diff-aware)

---

## The Squeaky Clean Whitelist

A gate result is **Squeaky Clean** — and therefore does NOT escalate — only when ALL of:

```
1. Gate result: no warn, no fail, no residual
2. Confidence: proven or high-confidence inferred (never plausible, indeterminate, or opaque)
3. Trust balance: trust_earned >= trust_claimed for every claim in the path
4. Role coherence: inferred subsystem role matches declared/named role
5. Path closure: no unresolved external call targets in any critical path
6. Alien score: 0 (no unknown structured input anywhere in the artifact)
7. Module family: not in a sensitive family (auth/crypto/payment/exec/deserialization/admin)
8. Diff-clean: not a recent change to a previously-verified security invariant
```

If ANY of those conditions fails, escalate. The A–K classes below define escalation
PRIORITY and REASON — not the routing decision. Routing is: not squeaky clean → LBE.

---

## Doctrine (unchanged from v0.1, restated for completeness)

1. Forge is default. All code enters through Forge first.
2. Blueprint is deep lane. Used when shallow classification is not enough.
3. Escalation is not only for failure. Squeaky clean is a strict standard.
4. Operator sovereignty. Operator may force escalation or pin any target.
5. Escalation must preserve reasons. No silent deep-lane jumps.

---

## Class A: Hard Escalation (mandatory, non-negotiable)

**A1. Forge result is red.**

**A2. Residual obligations present.**
Previously: residuals were emitted but did not trigger escalation. This is wrong.
Residuals mean the gate could not discharge an obligation — that is unresolved uncertainty
about a security property. Any residual in the result forces Blueprint pass.

**A3. Unknown structured input with semantic risk.**
Expanded from v0.1 A2. Now includes:
- Novel structured language or unknown DSL
- Config-as-code with execution semantics (Terraform lifecycle hooks, k8s Job specs,
  GitHub Actions with shell injection vectors, Ansible tasks)
- Template languages with eval semantics (Jinja2 macros, Twig, Smarty, ERB)
- Encoded or obfuscated strings that resolve to source at runtime
- Binary content embedded in source strings (shellcode patterns)
- Multi-language polyglot blobs (PHP + JS, SQL + Python, etc.)
- GraphQL/SPARQL/Datalog — query languages with their own injection surfaces

**A4. Wrapper theater plus sink/effect reachability.**
Safety is claimed but not earned, AND a real sink/effect path exists.

**A5. Cross-class blended risk over threshold.**
Examples: SSRF + render + exec; redirect + token + mutation;
deserialization + state mutation; query composition + redirect + wrapper claim.
The threshold is: 2+ distinct vuln classes in same path with any effect surface.

**A6. High ambiguity with meaningful effect surface.**
Ambiguity score high AND path touches real effects/sinks.

**A7. Sensitive subsystem touched — expanded.**
v0.1 listed: auth/session/token, process execution, storage mutation on credential-bearing
objects, deserialization of untrusted input, privileged file writes.

v0.2 adds:
- Cryptographic primitive implementation (any custom crypto)
- Payment/financial calculation with money-moving effects
- PII handling with storage or transmission effects
- Password storage or verification operations
- Certificate or key management operations
- Admin/superuser privilege elevation paths

**A8. Suspicious-clean above hard threshold.**
Complexity/unknownness/effect surface high but Forge remained implausibly clean.
This is the primary motivation for the LBE — the thing the front gate cannot catch.

**A9. Trust-earned vs trust-claimed gap.**
Any path where claimed_safe > earned_trust. Not just wrapper theater — any
case where a trust claim exists without corresponding earned evidence.
Includes:
- Trust claims with zero verification evidence
- Multi-hop trust where the chain is broken at any link
- Trust inherited from caller without propagation proof visible in the path

**A10. Semantic role mismatch — hard cases.**
Function name declares one role but inferred behavior is inconsistent:
- Named sanitize_* but calls subprocess/exec/requests
- Named validate_* but never produces a negative result
- Named safe_* or trusted_* but accepts untrusted input without narrowing
- Named helper/util but directly mutates auth state or issues tokens

This is the "clean but wrong" failure mode — passes all gates because nothing
technically fires, but the implementation is semantically incoherent.

---

## Class B: Strong Escalation (automatic in standard mode, policy-configurable)

**B1. Forge result is amber.**

**B2. Unknown-heavy path without strong closure.**
Even if not overtly red, unknown-heavy paths need deep treatment.

**B3. Wrapper claims without earned trust.**
Even absent an obvious sink, claims without evidence escalate.

**B4. New code in high-risk module families — expanded.**
v0.1: auth, proxy/network, template/render, token/session, command wrappers, persistence/migration.
v0.2 adds: crypto implementations, payment calculation, PII transformation, admin tooling,
seed/fixture code with production-data access, test utilities in production paths.

**B5. High role conflict.**
Claimed subsystem role and inferred subsystem role diverge strongly.

**B6. Diff-aware: recent change in previously-clean sensitive path.**
Any code change that touches a path previously verified as clean in a sensitive
module family. Use BLAKE3 hash of path entry points to detect.

**B7. Effect surface without corresponding validation visible.**
Any of:
- network.outbound without hostname/allowlist validation in same function scope
- storage.write without path normalization check visible
- process.exec without explicit allowlist visible
- token.issue without expiry set visible
- auth.state mutation without prior authentication check visible
- redirect without target validation visible

These may pass individual gates but the validation is elsewhere — the front gate
cannot close the path. The LBE can.

**B8. Exception handling changes around security operations.**
Code that modifies try/except/catch blocks around auth, crypto, or validation logic.
Swallowed exceptions around security operations are a common regression vector.

**B9. Trust chain with unverified inheritance.**
A called function is assumed safe because the caller validated — but the path
does not carry that validation guarantee forward. "Trust laundering" through
function call boundaries.

---

## Class C: Soft Escalation (optional or deferred, policy-dependent)

**C1. High code novelty.**
Unusual patterns not clearly risky.

**C2. Recovered fragment with partial structure.**
Malformed or partial code that may be harmless but is not confidently understood.

**C3. Moderate suspicious-clean score.**
Not enough alone for hard escalation.

**C4. Construction-mode anti-naivety pass.**
Continuous use during building even if code would not normally escalate in triage mode.

**C5. High structural complexity — soft threshold.**
Below hard thresholds but above baseline:
- Cyclomatic complexity > 10 (hard threshold would be > 20)
- Call depth > 4 (hard threshold would be > 8)
- Function length > 60 lines (hard threshold would be > 150)

**C6. Async/concurrent patterns without visible synchronization.**
Not obviously broken but concurrency without explicit synchronization evidence
is a soft signal for temporal vulnerability inspection.

**C7. Dynamic dispatch without explicit allowlist.**
getattr, __class__, type() used for behavior routing — soft if no sink reachable,
hard (A10) if a sink is reachable or role mismatch is present.

---

## Class D: Manual Escalation (operator-commanded)

Targets: whole file/module, callable, path family, sink family, specific blob,
specific diff range, suspicious-clean case, unknown structured fragment.

Reason must be preserved in metadata.

---

## Class E: Structural Complexity (NEW — input-driven, gate-agnostic)

These fire on properties of the code itself before any gate output is considered.

**E1. Cyclomatic complexity above hard threshold.**
> 20 branches/conditions in a single callable. High path count means the front
gate's bounded pattern matching cannot cover the space. LBE mandatory.

**E2. Call depth above hard threshold.**
Call chains > 8 hops deep without intermediate validation. Taint propagation
through deep chains is structurally underspecified in the front gate.

**E3. Function length above hard threshold.**
> 150 lines in a single callable. Too long to reason about locally.
The LBE can summarize and checkpoint within the function.

**E4. Unresolved external call targets in critical path.**
Any call to a function not visible in the artifact where that function could
carry taint or have security-relevant effects. The front gate cannot close paths
that extend beyond the artifact boundary.

**E5. Heavy closure/callback nesting.**
More than 3 levels of closure nesting where the inner closure captures external
state. Taint propagation through closures is notoriously hard to track statically.

**E6. Reflection or dynamic import.**
importlib, __import__, require() with non-literal strings, Class.forName(),
dynamic dispatch via eval-equivalent. Even if no obvious sink is reachable,
the dynamic resolution surface requires deep path analysis.

---

## Class F: Semantic Role Mismatch (NEW)

**F1. Named role contradicts inferred behavior — soft cases.**
(Hard cases are A10.)
- Named cache_* but touches auth state
- Named format_* but makes network calls
- Named check_* or assert_* but has side effects
- Named read_only_* but modifies storage

**F2. Public API surface inconsistency.**
Function signature implies one trust posture (e.g., takes `user_id: int`) but
internally treats the input as potentially untrusted without stated reason.

**F3. Error behavior is inconsistent with security claim.**
A function claims to be safe but swallows exceptions that would invalidate the
safety claim. Silently returning a default value instead of failing when validation
fails is a common "clean but wrong" pattern.

---

## Class G: Temporal and Concurrent Patterns (NEW)

**G1. Check-then-act with non-atomic operations.**
Any pattern where a condition is checked and then a separate operation depends
on that condition remaining true. TOCTOU class. The front gate catches some
explicit patterns (tempfile.mktemp) but not the general form.

**G2. State machine code.**
Explicit state enumeration with transition logic. Temporal invariant breaks
(invalid state transitions, missing guards) are the primary vulnerability class
and require path-walking across state transitions.

**G3. Async/concurrent shared mutable state.**
Shared mutable objects accessed from async functions or threads without
explicit synchronization evidence. Race conditions in auth state are particularly
dangerous.

**G4. Cached values used after revalidation window.**
Values read from cache used in security decisions without freshness check.
Especially dangerous in auth, permission, and rate-limit contexts.

---

## Class H: Alien/Novel Input (EXPANDS v0.1 A2)

**H1. Unknown language or DSL.**
Code in a language the front gate has no parser for. Partial recovery only.

**H2. Config-as-code with execution semantics.**
Terraform, Ansible, GitHub Actions, k8s Job/CronJob specs — these are not
"just config" when they contain lifecycle hooks, shell commands, or template
expansion with user-controlled values.

**H3. Query language with injection surface.**
GraphQL mutations, SPARQL, Datalog, Cypher (Neo4j) — each has its own injection
class that the front gate's SQL/NoSQL patterns don't cover.

**H4. Template language with eval semantics.**
Jinja2 macros, Twig, Smarty, ERB, Handlebars helpers — template languages that
allow arbitrary code execution within template expansion.

**H5. Multi-language polyglot.**
PHP + JS in same blob, SQL embedded in Python, shell in YAML — the front gate
analyzes as one language but the artifact has multiple semantic layers.

**H6. Encoded or obfuscated content.**
Base64, hex-encoded strings that decode to source. Strings that match shellcode
byte patterns. Intentionally obfuscated identifier names.

**H7. RuneFlow and similar custom language artifacts.**
Any artifact identified as a custom/novel language spec. These require
full alien-tech first-principles analysis — no parser preblessing.

---

## Class I: Residual Obligation Density (NEW)

**I1. Any residual present — hard escalation.**
(Moved from C to A2 above. Restated here for completeness.)
Residuals are the gate admitting it could not discharge an obligation.
That is non-negotiable — it requires LBE treatment.

**I2. High residual count — priority signal.**
More than 3 residuals in a single artifact. Even if all are low-severity,
density indicates the front gate's model of the code is significantly incomplete.

---

## Class J: Domain-Specific Mandatory Review (NEW)

These escalate regardless of gate result because the domain has invariants
the front gate is not equipped to verify.

**J1. Cryptographic primitive implementation.**
Any code that implements a cipher, hash function, PRNG, key derivation function,
or MAC from scratch. The invariant is: never implement your own crypto.
Even a "clean" implementation of a known algorithm should be flagged.

**J2. Password storage or verification.**
bcrypt/argon2/scrypt required. MD5/SHA1/SHA256 for passwords is always red.
The front gate catches obvious cases but the LBE can reason about the full
storage pipeline.

**J3. Financial calculation with money-moving effects.**
Any code path that ends in a payment, credit, debit, or balance mutation.
Invariants: Decimal not float, no integer overflow in currency math,
correct rounding semantics (ROUND_HALF_UP for most jurisdictions).

**J4. PII handling with storage or transmission.**
Code that touches name, email, SSN, DOB, health data, or similar.
The LBE checks: is there encryption at rest/transit visible? Is access logged?
Is retention policy enforced?

**J5. Key/certificate management.**
Private key generation, storage, rotation, or deletion. Any of these done wrong
is catastrophic and irreversible.

**J6. Admin/superuser privilege operations.**
Granting roles, modifying ACLs, creating privileged accounts.
These require explicit authorization checks that the front gate can miss.

---

## Class K: Effect Surface Without Validation (NEW)

These are cases where an effect is reached but the corresponding validation
is not visible in the artifact — it may exist elsewhere, but the front gate
cannot close the path.

**K1. network.outbound without hostname validation.**
Any requests.get/post, fetch, curl, http.Get etc. where the target
is not validated against an explicit allowlist in the visible scope.

**K2. storage.write without path normalization.**
Any file write where the path is not os.path.realpath'd and checked
against a base directory before the write.

**K3. process.exec without explicit allowlist.**
Any subprocess, os.system, exec, Popen where the command or any argument
is not checked against an explicit allowlist before execution.

**K4. token.issue without expiry.**
Any token generation where expiry is not explicitly set in the visible scope.

**K5. auth.state mutation without prior authentication check.**
Any operation that changes session state, grants roles, or logs in a user
where an explicit authentication check is not visible in the same path.

**K6. deserialization of untrusted input.**
pickle.loads, yaml.load, marshal.loads, Java ObjectInputStream,
PHP unserialize — without a safe_load equivalent or trusted-source check.

---

## Escalation Signal Schema

Every escalation must carry:

```json
{
  "escalation_class": "A|B|C|D|E|F|G|H|I|J|K",
  "escalation_trigger": "A2|B7|E1|...",
  "reason": "human-readable explanation",
  "evidence_refs": ["gate result ID", "pattern match ID", "..."],
  "confidence": "certain|high|moderate|low",
  "operator_forced": false,
  "squeaky_clean_failures": ["condition 2", "condition 6"]
}
```

`squeaky_clean_failures` lists exactly which whitelist conditions failed.
This is the primary audit surface.

---

## Implementation Order

1. Squeaky Clean gate — implement the 8-condition whitelist check first.
   This is the routing logic. Everything else is priority annotation.

2. Residual escalation — wire A2 (any residual → hard escalate).
   Currently residuals are emitted and ignored. This is the lowest-cost
   highest-impact fix.

3. Effect Surface checks (Class K) — these are detectable with the
   current front gate's AST surface. Add as post-gate escalation checks.

4. Structural Complexity (Class E) — add complexity metrics to the
   structural extraction pass. Cyclomatic complexity is O(AST walk).

5. Alien/Novel expansion (Class H) — extend the existing alien blob
   detection with the new sub-categories.

6. Domain triggers (Class J) — implement as genome capsule families
   that flag for LBE rather than producing verdicts themselves.

7. Semantic role mismatch (Class F) and Temporal patterns (Class G) —
   these require the Path Engine to be meaningful. Implement after
   the LBE pilot is running.
