# CILNX Intelligent Continuity Addendum — 2026-04-12

## Status
Active implementation doctrine addendum for Singularity Works / CILNX alignment.

## Thesis
CILNX is **not** a dumb storage box. It is an intelligent continuity substrate.

That means the target shape is:
- immutable typed memory objects
- temporal event structure
- provenance-native lineage
- query/projection separation
- format discipline by artifact class

## Canonical meaning currently verified
- `CIL` is canonically **Cognitive Inter-symbolic Ledger**.
- `NX` is now canonized as **Next**.
- Full canonical expansion: **Cognitive Inter-symbolic Ledger Next**.
- Meaning: the next-generation continuity substrate evolved from the original CIL line, while preserving ledger/provenance identity and extending it into richer typed continuity, event structure, provenance, and projection-aware memory planes.

## Canonical naming
- **CILNX = Cognitive Inter-symbolic Ledger Next**
- This expansion is now canonized for Singularity Works and the active CILNX scaffold line.
- `Next` denotes the evolved continuity substrate beyond the older monolithic CIL framing: typed, temporal, provenance-native, projection-aware, and memory-plane explicit.

## Internal implementation doctrine

### 1. Memory objects first
Every persisted family should have a typed envelope with:
- schema/version
- artifact family
- timestamps
- lineage / derivation identity
- provenance links
- integrity hash or equivalent verification hook

### 2. Eventful / temporal by default
Session state, evidence, transformations, recovery state, and operator actions should be represented as temporal objects, not unordered dumps.

### 3. Provenance is native, not decorative
CILNX should model:
- entities / artifacts
- activities / transformations / runs
- agents / operators / model roles
- derivation / generation / influence links

### 4. Projection is not canonical storage
Human-readable outputs such as:
- JSON / JSONL summaries
- Markdown reports
- operator HUD surfaces
are projections.
The canonical continuity substrate should remain richer than those projections.

### 5. Format discipline by artifact class
Use the simplest format that preserves the right invariants.

#### Good default split
- **JSON / JSONL**: human-readable projections, compatibility paths, debugging, export surfaces
- **CBOR / MessagePack-like compact row/object forms**: typed immutable event objects when schema is light but machine efficiency matters
- **Protocol Buffers / FlatBuffers / schema-driven binary envelopes**: strongly typed transport or persisted envelopes where strict contracts and smaller/faster structured serialization are useful
- **Parquet / columnar projections**: analytics / batch mining / offline longitudinal slicing, not primary operational continuity for live event mutation
- **Graph/provenance representation**: for derivation/query layers where lineage traversal matters more than row scanning

### 6. Distinct memory planes remain required
Do not flatten these into one undifferentiated store:
- episodic / session / recovery memory
- semantic / stable memory
- evidence / event memory
- cartography / LBE / blueprint outputs
- report artifacts
- routing / query / index surfaces

### 7. Bug-bounty-first output, not bug-bounty-only ontology
Singularity Works may be used primarily for bug bounty hunting and reporting, but CILNX should still model:
- maximum-standard reports as typed report artifacts
- LBE / blueprint maps as distinct cartography artifacts
- linked evidence and derivation trails beneath both

## Current seam order implied by this addendum
1. move remaining ledger-first workshop truth toward CILNX-native query/projection structures
2. harmonize ForgeContext families with CILNX memory planes
3. continue reducing dict/string spill at continuity boundaries
4. strengthen typed artifact-family envelopes before adding new persistence classes
5. keep human-readable JSON/JSONL as projections, not as the final intelligence substrate
