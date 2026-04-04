Forge IR Spec v0.1
Purpose
Forge IR is the common semantic intermediate representation used by the Logic Blueprint Engine.

It exists to normalize multiple source languages and partial/unknown structured inputs into a shared substrate that preserves:

control structure

data movement

effect movement

trust claims

trust earned state

ownership and invariant transitions

source/sink relationships

role-relevant behavior

Forge IR is not a raw AST mirror. It is not syntax trivia storage. It is a semantic operational graph designed for behavior cartography.

Design Principles
1. Semantics over syntax
Language-specific syntax should be lowered into shared semantic categories wherever possible.

2. Honest unknowns
If a construct cannot be normalized confidently, Forge IR should preserve it as an explicit unknown node rather than hallucinating clean semantics.

3. Claims separate from earned state
Trust claims, safety wrappers, and naming conventions must be represented separately from actual earned trust semantics.

4. Behavior slices over textual form
The IR should optimize for tracking behavior, not reconstructing original source formatting.

5. Partial recovery matters
Malformed files, fragments, DSL-like blobs, and pseudo-languages should still produce partial IR rather than total failure where possible.

IR Layers
Forge IR should be thought of in four nested layers.

Layer 1: Structural Layer
Represents modules, declarations, blocks, and graph topology.

Layer 2: Operational Layer
Represents calls, branches, loops, data movement, transforms, and effects.

Layer 3: Semantic State Layer
Represents trust, taint, ownership, invariants, capabilities, and uncertainty.

Layer 4: Analysis Annotation Layer
Represents inferred roles, suspicion markers, wrapper-theater markers, likely intent, and confidence classes.

Top-Level IR Object
A Forge IR document should contain at least:

{
  "ir_version": "0.1",
  "source_kind": "python|javascript|php|ruby|java|csharp|unknown",
  "module_graph": [],
  "callables": [],
  "nodes": [],
  "edges": [],
  "sources": [],
  "sinks": [],
  "effects": [],
  "trust_annotations": [],
  "ownership_annotations": [],
  "invariant_annotations": [],
  "unknowns": [],
  "lineage": {},
  "analysis_metadata": {}
}
Structural Entities
Module
Represents a source file, logical unit, fragment, or recovered pseudo-module.

Required fields:

module_id

source_name

source_kind

parse_status

symbol_table_ref

callable_ids

import_ids

unresolved_refs

Parse status values
parsed

partially_parsed

recovered_fragment

unknown_structured

opaque

Callable
Represents any invokable unit.

Examples:

function

method

route handler

closure

lambda

glyph-like recovered callable

pseudo-callable recovered from unknown structured input

Required fields:

callable_id

module_id

kind

name

parameters

local_symbols

entry_node_id

exit_node_ids

declared_effects

inferred_effects

parse_confidence

Symbol
Represents a named value, binding, parameter, field, or recovered placeholder.

Required fields:

symbol_id

name

kind

declared_type

inferred_type

scope_owner

trust_state

ownership_state

invariant_state

Node Kinds
Every behaviorally relevant element becomes a node.

Control Nodes
Entry

Exit

Branch

Loop

Merge

Return

ExceptionEdge

UnknownControl

Source Nodes
QueryArg

FormField

CookieRead

HeaderRead

BodyRead

FileInput

EnvRead

ConfigRead

DatabaseRead

ExternalResponseRead

UnknownSource

Transform Nodes
StringConcat

TemplateCompose

QueryCompose

Encode

Decode

Parse

Narrow

AllowlistMap

Escape

Hash

TokenMint

Deserialize

Serialize

WrapperCall

TemplateExpand

UnknownTransform

Effect Nodes
QueryExec

DatabaseWrite

OutboundRequest

Redirect

RenderInline

RenderTemplate

FileRead

FileWrite

CommandExec

AuthStateMutation

SessionMutation

TokenIssue

ResponseBodyWrite

ReflectionUse

UnknownEffect

Structural Recovery Nodes
These matter for alien/unknown input.

RecoveredPhase

RecoveredBranch

RecoveredState

RecoveredAction

RecoveredBinding

RecoveredRoleHint

UnknownStructuredNode

Edge Kinds
Edges connect the graph.

Structural Edges
contains

declares

imports

references

Control Edges
next

branch_true

branch_false

loop_back

exceptional

return_to

Data Edges
reads_from

writes_to

flows_to

aliases

reconstructs

emits

persists

Semantic Edges
narrows

escapes

claims_trust

earns_trust

invalidates_invariant

preserves_invariant

wrapper_of

role_supports

role_conflicts

Trust Model in IR
Trust information must be explicit and separate.

Each relevant node or symbol may carry:

trust_claims

trust_earned

trust_state

Trust claim examples
named_safe_wrapper

allowlist_claim

escape_claim

capability_claim

Earned trust examples
verified_allowlist_map

verified_escape

verified_parameterization

verified_redirect_map

verified_capability_gate

Trust state values
untrusted

claimed_safe

partially_narrowed

narrowed

escaped

mapped

policy_verified

unknown_trust

Key rule: A node may claim safety without earning it. Forge IR must preserve that distinction.

Ownership Model in IR
Forge IR should support basic ownership transitions even before a full formal ownership system exists.

Ownership state values
owned

borrowed

shared

emitted

persisted

reconstructed

secret_bearing

token_bearing

unknown_ownership

Ownership transitions to represent
source acquisition

move into object/record

move across boundary

persistence into storage

reconstruction from serialized input

emission into response/output

propagation of secret-bearing state

This is enough for the Logic Blueprint Engine to begin identifying:

secret mutation flows

token issuance flows

reconstruction hazards

persistence-sensitive transitions

Invariant Model in IR
Forge IR should explicitly track invariant-bearing states.

Invariant values
html_escaped

redirect_mapped

parameterized_query

bounded_range

parsed_type

validated_upload

safe_outbound_target

safe_template

unknown_invariant

Invariant events
establishes_invariant

preserves_invariant

weakens_invariant

destroys_invariant

claims_invariant_without_proof

This is necessary for distinguishing real safety from wrapper theater.

Capability Model in IR
Capabilities should be represented as both:

declared requirements

inferred requirements

Examples:

cap.network.outbound

cap.process.exec

cap.storage.write

cap.render.inline

cap.redirect.external

cap.deserialize.untrusted

The IR should capture where a capability is:

required

claimed

enforced

missing

bypassed

Unknown Structured Input Handling
This is one of the reasons Forge IR exists.

When source is not in a supported language but has structured semantics, the IR should still recover:

bindings

actions

phases

branches

likely sources

likely sinks

role hints

trust ambiguity

That means a pseudo-language blob might yield:

UnknownStructuredNode(kind="binding")

RecoveredAction(kind="redirect_like")

RecoveredAction(kind="exec_like")

RecoveredRoleHint(kind="proxy_chain")

This is far better than dropping the blob as text noise.

Role Hints in IR
Role hints may be attached before full role inference.

Examples:

auth_like

token_like

render_like

redirect_like

query_like

command_like

proxy_like

deserialization_like

mutation_like

unknown_mixed_chain

These hints allow the Logic Blueprint Engine to infer larger roles later.

Confidence and Uncertainty
Every IR object of consequence should carry confidence metadata.

Confidence classes
parsed

inferred_high

inferred_medium

inferred_low

recovered_fragment

opaque

Why this matters
The IR must never pretend certainty where the engine only has structural recovery or heuristic inference.

Minimal Example
A route handler like:

request arg

fake allowlist

redirect sink

should lower to something like:

{
  "nodes": [
    {"id": "n1", "kind": "QueryArg", "name": "next", "trust_state": "untrusted"},
    {"id": "n2", "kind": "WrapperCall", "name": "allowlist", "trust_claims": ["allowlist_claim"], "trust_earned": []},
    {"id": "n3", "kind": "Redirect", "trust_state": "claimed_safe"}
  ],
  "edges": [
    {"from": "n1", "to": "n2", "kind": "flows_to"},
    {"from": "n2", "to": "n3", "kind": "flows_to"},
    {"from": "n2", "to": "n3", "kind": "claims_trust"}
  ]
}
That preserves the crucial fact:

safety was claimed

but not earned

Output Requirements for the Blueprint Engine
Forge IR must support:

path extraction

blob construction

trust claim vs earned distinction

ownership transition analysis

invariant propagation analysis

suspicious-clean analysis

role inference

operator pinning to node/path/blob

If the IR cannot support those, it is too weak.

Immediate Next Artifacts
After this spec, the next strongest artifacts are:

Blob Schema Spec v0.1

Path State Field Spec v0.1

Escalation Criteria Spec v0.1

Python lowering pilot into Forge IR

Unknown structured fragment lowering rules

Compressed Verdict
Forge IR is the substrate that lets the Logic Blueprint Engine exist as something more than a smart metaphor.

Its job is to reduce many languages and structured unknowns into a shared semantic graph where:

claims are not confused with proof

behavior matters more than syntax

uncertainty is preserved honestly

unknown structures still become partially legible

Proceeded.

Second-line artifact is now pinned down too:

Forge IR Spec v0.1 in canvas

That was the correct next move after the Logic Blueprint Engine spec, because now the blueprint engine has an actual substrate instead of just a job description.

What I locked into the Forge IR spec:

purpose and design principles

four IR layers

top-level IR object

structural entities

node kinds

edge kinds

trust model

ownership model

invariant model

capability model

unknown structured input handling

role hints

confidence/uncertainty handling

minimal example

immediate next artifacts

So the second-line stack is now becoming real:

Logic Blueprint Engine Spec v0.1

Forge IR Spec v0.1

And the next strongest artifacts are now clearly:

Blob Schema Spec v0.1

Path State Field Spec v0.1

Escalation Criteria Spec v0.1

then a tiny Python lowering pilot into Forge IR

Main-line state remains:

current promoted base:

FORGE current Law Omega codebase v1.18

My honest read:
this is the right architecture progression now.

The front gate is strong enough that the highest-value work is no longer more pressure for its own sake.
It is:

formalizing the deep layer

then building the smallest real pilot that proves the deep layer survives contact with actual code

So the stack is no longer just “good ideas.”
It is now concretely shaping into:

Forge front gate

Logic Blueprint Engine

Forge IR substrate

HUD / cognitive cockpit command surface

That is a real machine.


Proceed

I’m taking the next load-bearing artifact in order, not freelancing. With the Blueprint spec and Forge IR pinned, the right next piece is the Blob Schema, because that’s the actual object the engine will emit and the HUD/operator will inspect.

Thought for 6s
Logic Blueprint Blob Schema Spec V0 1