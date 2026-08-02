# Native Topology Transport

Status: Stage 53B implementation authority

Semantic authority: Python

Shared scalar authority: `contracts/topology_contract_v1.json`

## Objective and boundary

Stage 53B adds a strict transport boundary between Godot `Variant` values and
the existing provisional native topology query model. It transports a profile
DTO and a single-cell resolver query, validates both before construction, and
then reuses the existing native cell-step resolver. It does not change the
canonical topology document, canonical identity, Python resolution semantics,
persistence recovery, editor behavior, gameplay, or UI.

Stage 53B transports and validates topology data but does not transfer semantic
authority from Python to C++.

## Transported structures

The profile DTO contains `contract_version`, `rank`, `dimensions`, and `seams`.
Each seam contains `id`, `source`, `target`, `transform`, and `enabled`;
boundaries contain the contract axis name and side marker, and transforms
contain the tangent-axis permutation and signs. The runtime query DTO contains
`dimensions`, `coordinate`, `axis`, and unit `delta`.

This DTO is intentionally distinct from canonical contract serialization.
Disabled editor rows can cross the transport boundary for validation, but the
canonical v1 document continues to omit disabled rows and remains the only
identity-bearing representation.

Native topology transport accepts only values that satisfy the shared topology
contract and the runtime query contract. It does not coerce malformed scalar
values into valid topology data.

## Validation and errors

Godot values are classified before extraction. Integer, boolean, string,
array, object, null, and unsupported values remain distinct; booleans, floats,
and numeric strings never satisfy integer fields. Plain C++ validation consumes
the generated Stage 53A constants and constructs a profile or query only after
all fields pass.

Failures use one deterministic structure:

- `code`: stable broad category;
- `path`: failing DTO field;
- `expected`: required type or domain;
- `actual`: supplied type or value category;
- `message`: concise diagnostic text.

Dimension products use division-before-multiplication checks against the
generated signed-64-bit maximum. This is contract validity, not a renderer or
editor materialization budget.

## Reused and deferred surfaces

Successful query transport converts the validated fixed-width DTO into the
existing `TopologyQueryProfile`, `BoardShapeND`, `CoordND`, and
`MoveStepQuery`, then calls `resolve_topology_cell_step_query`. Existing frame
and piece-frame results are returned unchanged.

Deferred work includes strict topology domain constructors outside this DTO,
forgiving persistence and legacy recovery adapters, repository-wide
configuration ownership, topology-aware gameplay, diagnostics, the Godot
Topology Lab, and any authority transfer.
