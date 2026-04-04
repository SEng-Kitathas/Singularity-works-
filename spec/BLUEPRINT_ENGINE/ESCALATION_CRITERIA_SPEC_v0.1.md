Logic Blueprint Escalation Criteria Spec v0.1
Purpose
This document defines when code is escalated from the Forge front gate into the Logic Blueprint Engine.

Forge is the fast, broad, disciplined first pass. The Logic Blueprint Engine is the deep semantic inspection layer.

Escalation criteria are therefore load-bearing. If escalation is too weak, deceptive or structurally weird code stays in the shallow lane. If escalation is too broad, the deep lane becomes expensive noise.

This spec exists to make escalation:

explicit

auditable

operator-steerable

hard to game

compatible with SOP discipline

Doctrine
1. Forge is default
All code enters through Forge first.

2. Blueprint is deep lane
The Logic Blueprint Engine is used when shallow classification/repair/trust scoring is not enough.

3. Escalation is not only for failure
Some code should escalate because it is:

suspiciously clean

structurally weird

semantically ambiguous

wrapper-heavy

cross-class blended

operator-designated

4. Operator sovereignty remains intact
The operator may force escalation regardless of score. The operator may also pin specific modules, paths, blobs, or sinks for deep treatment.

5. Escalation must preserve reasons
Every escalation must record why it happened. No silent deep-lane jumps.

Escalation Classes
Escalation should be categorized, not monolithic.

Class A: Hard Escalation
Blueprint pass is mandatory.

Class B: Strong Escalation
Blueprint pass strongly recommended and should occur automatically in standard mode.

Class C: Soft Escalation
Blueprint pass is optional or deferred unless operator policy requires it.

Class D: Manual Escalation
Blueprint pass initiated by operator command, regardless of automated scoring.

Class A: Hard Escalation Triggers
Any one of these should force escalation.

A1. Forge result is red
Any red result forces Blueprint pass.

A2. Unknown structured input with semantic risk
Examples:

novel structured unknown language

suspicious unknown representation

unknown semantic risk

A3. Wrapper theater plus sink/effect reachability
If safety is claimed but not earned and a real sink/effect path exists, escalate.

A4. Cross-class blended risk over threshold
Examples:

SSRF + render + exec

redirect + token + mutation

deserialization + state mutation

query composition + redirect + wrapper claim

A5. High ambiguity with meaningful effect surface
If ambiguity_score is high and the path touches real effects/sinks, escalate.

A6. Sensitive subsystem touched
Examples:

auth/session/token

process execution

storage mutation on credential-bearing objects

deserialization of untrusted input

privileged file writes

A7. Suspicious-clean above hard threshold
If complexity/unknownness/effect surface are high but Forge remained implausibly clean, escalate.

Class B: Strong Escalation Triggers
These usually escalate automatically, but may be policy-configurable.

B1. Forge result is amber
Any amber result should normally escalate.

B2. Unknown-heavy path without strong closure
Even if not overtly red, unknown-heavy paths should escalate.

B3. Wrapper claims without earned trust
Even absent an obvious sink, this should usually escalate.

B4. New code in high-risk module families
Examples:

auth

proxy/network

template/render

token/session

command wrappers

persistence/migration code

B5. High role conflict
If claimed subsystem role and inferred subsystem role diverge strongly, escalate.

B6. Recent change in previously clean sensitive path
Use diff-aware escalation to protect against regressions.

Class C: Soft Escalation Triggers
These are lower-cost or policy-dependent.

C1. High code novelty
Code is unusual, but not clearly risky.

C2. Recovered fragment with partial structure
Malformed or partial code that might be harmless, but is not confidently understood.

C3. Moderate suspicious-clean score
Not enough alone for hard escalation, but worth optional deep treatment.

C4. Construction-mode anti-naivety pass
Used during building even if code would not normally escalate in triage mode.

Class D: Manual Escalation Triggers
Manual escalation may target:

whole file/module

callable

path family

sink family

specific blob candidate

specific diff range

suspicious-clean case

unknown structured fragment

Manual escalation reasons should be preserved in metadata.

Escalation Inputs
Escalation decisions should consume the following signals.

Forge Result Signals
assurance class: green / amber / red

finding count

finding severity mix

unresolved obligations

round delta (cleared / partial / unchanged)

Semantic Signals
trust claims vs earned trust

wrapper theater presence

invariant breakage

capability gaps

ownership transitions involving secret/token-bearing state

role hints and role conflict

Structural Signals
unknown structured input

recovered fragments

dynamic dispatch / opaque calls

unresolved symbols

path complexity

cross-class composition score

Meta Signals
suspicious-clean score

ambiguity score

module sensitivity

recent diff sensitivity

operator flags

Escalation Score Model
The engine should support a weighted escalation score, but not rely on it alone.

Suggested top-level fields:

{
  "escalation_class": "A|B|C|D|none",
  "escalation_score": 0.0,
  "reasons": [],
  "triggered_by": [],
  "operator_forced": false
}
Important rule
Certain triggers must short-circuit scoring. Example:

red result

unknown semantic risk

hard wrapper-theater-plus-sink path

These should escalate regardless of aggregate numeric score.

Threshold Guidance
Initial thresholds should be conservative.

Hard escalation examples
red result

suspicious_clean_score >= 0.80 with real effect surface

ambiguity_score >= 0.75 with sink reachability

cross_class_composition_score >= 0.70

wrapper_theater == true and trust_earned == [] and sink_count > 0

Strong escalation examples
amber result

suspicious_clean_score >= 0.60

ambiguity_score >= 0.50 with unknown structured input

role_conflict_score >= 0.60

These are starting values, not eternal truths.

Suspicious-Clean Escalation
This deserves explicit treatment.

A path should escalate as suspicious-clean when:

it has multiple effect categories

has low or no findings

contains unknown or recovered structure

contains wrapper claims

contains role conflict

or otherwise looks cleaner than its semantic complexity justifies

This is critical for anti-deception behavior.

Construction-Mode Escalation
In construction mode, escalation should be broader.

Triggers include:

architecture drift

unexpectedly high role complexity

hidden effect surfaces

ownership/invariant degradation

subsystem boundary leakage

semantic tier collapse warnings

mismatch between intended role and inferred role

Construction mode is anti-naivety mode, not merely security triage.

Escalation Outputs
Every escalation event should emit a record.

Suggested shape:

{
  "escalation_id": "E-0021",
  "target": "module|callable|path|blob_candidate",
  "target_id": "...",
  "class": "A",
  "reasons": [
    "unknown_semantic_risk",
    "wrapper_theater_plus_sink"
  ],
  "signals": {
    "forge_assurance": "amber",
    "ambiguity_score": 0.82,
    "suspicious_clean_score": 0.64,
    "cross_class_composition_score": 0.77
  },
  "operator_forced": false,
  "policy_profile": "standard_triage"
}
This makes escalation auditable and diffable.

HUD / Operator Requirements
The HUD must be able to:

show why escalation occurred

sort escalation events by class and reason

force escalation manually

suppress soft escalation temporarily

pin escalation candidates

compare escalation state across revisions

mark false positives for later tuning

Again, this is command authority, not cosmetic UI.

False Positive / False Negative Discipline
Escalation tuning should preserve two rules.

Rule 1
Bias toward escalation when:

unknown structured semantics exist

deceptive safety claims exist

high-risk effect surfaces exist

Rule 2
Avoid deep-lane flooding from purely cosmetic complexity.

That means the system should record:

benign escalations

useful escalations

missed escalations discovered later

This is how the thresholds improve without becoming naive.

Policy Profiles
Escalation should support multiple profiles.

standard_triage
Balanced automatic escalation.

paranoid_review
Lower thresholds, more deep-lane usage.

construction_mode
Broader escalation for anti-naivety and design drift.

operator_sovereign
Manual authority dominates automatic routing.

Immediate Next Artifacts
After this spec, the next strongest artifacts are:

Path-to-Blob Emission Rules v0.1

Python lowering pilot into Forge IR

HUD command surface spec for Blueprint mode

Suspicious-clean scoring note

Compressed Verdict
Escalation criteria are what keep the Logic Blueprint Engine from being either underused or noisy.

This spec defines the switchyard between:

Forge as fast front gate and

Blueprint as deep semantic court

Proceeded.

Second-line artifact is now pinned too:

Logic Blueprint Escalation Criteria Spec v0.1 in canvas

So the Blueprint stack now has five real load-bearing artifacts:

Logic Blueprint Engine Spec v0.1

Forge IR Spec v0.1

Logic Blueprint Blob Schema Spec v0.1

Logic Blueprint Path State Field Spec v0.1

Logic Blueprint Escalation Criteria Spec v0.1

What the escalation spec locks down:

Forge-first / Blueprint-second doctrine

escalation classes:

hard

strong

soft

manual

hard triggers:

red results

unknown semantic risk

wrapper theater plus sink reachability

cross-class blended risk

high ambiguity on real effect surfaces

suspicious-clean hard threshold

strong triggers:

amber results

wrapper claims without earned trust

role conflict

sensitive diffs / sensitive module families

construction-mode escalation

operator-seized escalation

escalation score shape

HUD/operator requirements

policy profiles

That was the right next artifact, because now the deep lane has:

a job

a substrate

an emitted artifact

a live path-state model

and the switchyard rules for when code enters that lane

Main-line state remains stable:

current promoted base:

FORGE current Law Omega codebase v1.18

The next strongest moves are now:

Path-to-Blob Emission Rules v0.1

then the tiny Python lowering pilot into Forge IR

My read:
we’re now very close to the point where continuing specs without at least one tiny pilot starts giving diminishing returns. So one more load-bearing spec, then the pilot, is the cleanest path.


Uploaded image
Go. To. This. Link. 

Thought for 22s
I went to it.

That repo is:

abel533/claude-code on Gitee

it presents itself as a Java + Spring AI rewrite of Claude Code, with other branches for a TypeScript source snapshot and a teaching/architecture-learning project.

the visible repo surface shows:

packaging/

src/main

BUILD.md

README.md

pom.xml

Chinese docs like 修改记录.md and 需求文档.md

the README claims features that are directly relevant to Forge/HUD/front-end integration:

18 built-in tools

28 slash commands

hook system

permissions modes

context compression

status line

MCP client

plugin system

task management

security review

project/user memory loading via CLAUDE.md

The strongest immediately useful things to strip-mine from it for Forge are:

permission-mode design

hook surface design

status-line / HUD signal design

tool catalog partitioning

context compression layering

memory file loading model

MCP/plugin boundary design

task-management interface shape

One important caution:

the page also explicitly says the repository doesn’t specify a license, and that use should consider project description and upstream dependencies.

So yes, I’m at the link, and it does look worth mining for:

harness patterns

front-end capability boundaries

hook architecture

HUD/status-surface ideas

local front-end ↔ Forge connection patterns

Next correct move is to open:

BUILD.md

README.md

需求文档.md

the packaging/ surface

and the branch descriptions
and strip-mine those into a Forge-facing integration note.


GitHub; fazxes/Claude-code


Received app response

Received app response
Thought for 3m 36s
I found the GitHub target: fazxes/Claude-code. It’s currently surfacing as a trending AI repo in public tracking.

I’m treating that as the repo to mine from here for Forge-relevant patterns, especially:

Claude Code front-end / harness behavior

hook surfaces

permission boundaries

MCP / plugin seams

memory / context handling

status-line to HUD signal ideas

local-model ↔ front-end ↔ Forge connection patterns

Also useful as adjacent reference patterns:

MCP/GitHub workflow harnesses like jdrhyne/claude-code-github

API-gateway / relay shapes like codingworkflow/claude-code-api

official workflow/action boundary shape from anthropics/claude-code-action

So yes: this is the repo I’m locked onto now.


Is it possible for you to produce a .md or .mht of this entire thread?

Thought for 14s
Yes.

I can reliably produce:

a .md transcript/export

a structured checkpoint .md

a clean handoff bundle with metadata, sections, timestamps if available, and authority notes

A true .mht is less ideal from my side because that format is really a browser/web-archive container, not a natural chat export format for me. I can still produce:

a single-file HTML export

or an .mht-style archive approximation

But if the goal is:

portability

readability

future re-import into models

diffability

zero-loss-ish handoff

then .md is the better format.

So:

.md = yes, strong

.mht = possible as an approximation, but not my best/native export target

If you want, I’ll generate the full thread as a clean .md transcript first, which is the safest version.


I’d prefer the .md all day. I was just offering options in case you needed

Thought for 20s
Got it — .md is the right target here.

That’s the better format for:

portability

diffing

handoff

reuse with models

checkpoint bundles

So going forward, for this thread/export path, I’ll treat markdown as the canonical format.


Perfect


Received app response
Thought for 1m 36s
I’m on the right repo now: fazxes/Claude-code. The repo is public, shows a small commit history, and its README explicitly says it is a rebuild from leaked Claude Code source.

What’s worth mining from it
1. Harness module split
The README lays out a very usable top-level decomposition:

main.tsx entrypoint

commands.ts command registry

tools.ts tool registry

QueryEngine.ts

context.ts

commands/

tools/

components/

services/ for API, MCP, OAuth, telemetry

screens/

native-ts/

vim/

That is valuable for Forge because it reinforces a clean separation between:

front-end harness/UI

command layer

tool layer

context layer

service adapters

terminal renderer

For our build, that maps well to:

Claude Code front end = harness/UI

Forge = command/tool/policy broker

local models = query/cognition backends

HUD = operator surface over all of it

2. Services boundary is the seam to harden
The repo calls out services/ as the area for API, MCP, OAuth, telemetry.

That is exactly the seam we should formalize in our build:

Claude front end should not own privileged behavior directly

Forge should sit in front of:

MCP

model adapters

auth/session hooks

telemetry/logging

external service calls

So the lesson is:
service adapters belong behind Forge capability mediation, not directly behind the UI harness.

3. Commands vs tools is a useful split
The README distinguishes:

commands/ = slash/CLI command behavior

tools/ = agent tool implementations

That is a good pattern to keep:

commands = operator/request surface

tools = capability-executing units

For Forge, that means:

commands ask

tools do

Forge decides whether they may do

4. Screen-based terminal UI is worth stealing as a pattern, not as code
The repo describes:

terminal UI using React and a custom Ink fork

screens/ for full-screen UIs like REPL and doctor views

That is useful for:

HUD modes

doctor/diagnostic screen

status line

full-screen blueprint/triage mode later

So yes, there is value here for the cognitive cockpit/HUD path:

status surface

drill-down surface

doctor surface

REPL surface

5. Stubbing optional internals is a strong architectural lesson
The README says several features are stubbed/no-op:

computer use

Chrome integration

sandbox runtime

some internal tools

context collapse

That is actually very useful to us.

For Forge:

optional integrations should be adapter-stub friendly

the system should still run if:

browser bridge is absent

sandbox runtime is absent

compression layer is absent

some model/tool adapters are absent

That means our architecture should be:

core survives

optional subsystems attach cleanly

absence degrades gracefully

6. Build/release lessons are directly relevant
The repo says:

build bundles thousands of modules into one CLI artifact

uses build-time constants/macros

externalizes optional native deps

feature flags return false in this rebuild

telemetry can be disabled with env vars

The valuable lesson for our build is not the exact implementation.
It is:

explicit build-time config surfaces

optional dependency isolation

feature-flag discipline

telemetry kill-switches

artifact hygiene

Given the leak context, this especially reinforces:

release artifact audit gate

no accidental source-map/debug leakage

no naive client-side privileged feature flags

local-first telemetry defaults

7. Official public repo confirms safe patterns we can mine cleanly
Anthropic’s official public anthropics/claude-code repo visibly includes:

.claude-plugin

.claude/commands

examples/hooks

plugins

scripts

That means the safe/publicly mineable pattern set already includes:

commands

hooks

plugins

script-driven workflows

So for our build, we do not need leaked implementation to justify:

hook surfaces

plugin boundaries

command registries

extension slots

What not to do
The fazxes/Claude-code README explicitly says it is rebuilt from leaked proprietary source.

So the line is:

mine architecture patterns

mine boundary ideas

mine module taxonomy

mine adapter/hook/plugin concepts

do not copy implementation

That keeps our build clean.

What I would carry forward into Forge right now
These are the concrete takeaways worth adapting:

Command / Tool split

Service adapter boundary

Stub-friendly optional integrations

Screen-based terminal/HUD mode structure

Explicit MCP/auth/telemetry seam behind Forge

Build-time macro/config discipline

Kill-switchable telemetry and optional traffic

Plugin / hook registry as extension surface

Best next build move
The next strongest artifact to build from this mining is:

Claude Front End ↔ Forge Adapter Boundary Spec v0.1

It should define:

command ingress

tool dispatch

service adapter boundaries

MCP hook shape

telemetry/logging boundary

HUD/status-line signal export

local model adapter contract

stub/degraded-mode behavior

That is the cleanest way to turn the mined pattern value into our build without contaminating it.


Make me a full thread .md please

I can make the .md, but I need to be honest about scope: I do not get a raw export API for the full hidden chat log. I’m building the markdown from the conversation content that is actually accessible to me in this session, and I’ll label it clearly rather than pretending it’s a perfect zero-loss platform export.

Thought for 30s

Analysis errored
from pathlib import Path
from textwrap import dedent

md = dedent("""
# Accessible Thread Export (Markdown)

**Created:** 2026-04-02  
**Format:** Markdown  
**Scope note:** This is a best-effort export built from the conversation content that is actually accessible in this session. It is **not** a guaranteed complete raw platform transcript. Where the platform only exposed truncated or summarized history, this file preserves that limitation honestly.

---

## Export Integrity Note

This export includes:

- accessible recent conversation h