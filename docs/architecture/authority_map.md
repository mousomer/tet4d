# Authority Map

This map clarifies migration ownership. It does not replace
`config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`,
`docs/ARCHITECTURE_CONTRACT.md`, or relevant `docs/rds/*` product authorities.

## Current semantic authority

The existing Python implementation owns semantics for:

- topology
- legal movement
- rotation
- collision
- gravity/drop behavior
- trace semantics
- scoring
- replay correctness
- configuration defaults
- current gameplay behavior

These behaviors must not be rewritten during migration unless the task
explicitly requests a semantic change.

## Godot authority

Godot owns:

- UI shell
- menus
- scene composition
- input routing
- animation
- rendering
- camera/presentation
- inspector/probe panels
- product usability
- visual diagnostics

Godot does not own game-rule semantics.

## C++/GDExtension authority during migration

C++/GDExtension may own a ported subsystem only after:

1. The existing Python behavior is identified.
2. Existing Python utilities/functions are reused, wrapped, or mapped.
3. Golden traces, regression tests, or equivalent parity evidence exist.
4. The C++ implementation passes those parity checks.
5. This authority map or a narrower authority document records the transfer.

Until then, C++/GDExtension implementation is provisional.

Current accepted native authority is limited to already documented parity-backed
plain bounded gameplay surfaces in `docs/plans/godot_core_port_plan.md` and
`CURRENT_STATE.md`. Topology implementation remains deferred by
`docs/plans/topology_godot_core_port_plan.md`.
The first subsystem parity pilot is evidence only and does not change
authority.
The parity-pilot audit and promotion gates are evidence-only process routing and
do not change authority.
The second parity slice candidate selection is provisional parity-planning work
for trace metadata identity/digest only; it does not change authority.
The parity evidence review and third-slice candidate selection is provisional
parity-planning work for topology identifier normalization only; it does not
change authority. The routed review doc is
`docs/architecture/parity_evidence_review_and_third_slice_selection.md`.
Stage 20 topology identifier normalization parity evidence lives in
`docs/architecture/topology_identifier_normalization_parity.md` and remains
provisional evidence only. It does not change authority.
Stage 21 parity evidence package review lives in
`docs/architecture/parity_evidence_package_review.md` and summarizes the
current evidence package as provisional parity evidence only. It does not
change authority.
Stage 22 trace schema/version normalization parity lives in
`docs/architecture/trace_schema_version_normalization_parity.md` and remains
provisional schema/version metadata evidence only. It does not change
authority.
Stage 23 Python oracle boundary audit lives in
`docs/architecture/python_oracle_boundary_audit.md` and classifies Python
surfaces for migration porting decisions only. It does not transfer authority,
approve deletion of semantic Python code, or authorize gameplay, topology,
trace-event, movement, rendering, or Godot implementation changes.
Stage 24 parity tooling package review lives in
`docs/architecture/parity_tooling_package_review.md` and records the
package-routing decision only. Stage 25 applies that approved `tools/parity/`
routing/refactor without changing parity logic or transferring authority.
Stage 26 structural parity slice selection lives in
`docs/architecture/structural_parity_slice_selection.md` and selects trace
envelope validation for Stage 27 only. It does not implement trace envelope
validation, change trace-event semantics, or transfer authority.
Stage 27 trace envelope validation parity lives in
`docs/architecture/trace_envelope_validation_parity.md` and remains structural
envelope evidence only. It does not validate trace event semantics, board
states, piece positions, topology traversal, movement, rendering, native/Godot
comparison, or authority transfer.
Stage 28 Godot shell compliance and layout stabilization lives in
`docs/architecture/godot_shell_layout_stabilization.md` and remains
product-shell/layout work only. It audits existing Godot surfaces, records
boundary-risk bridge/router surfaces, and reserves the replay viewer shell
regions without changing gameplay, topology, trace semantics, parity evidence,
native authority, or authority transfer.

## Authority transfer requires parity

A C++/GDExtension subsystem is provisional until it satisfies
`docs/architecture/parity_protocol.md`.

C++ existence, cleaner implementation, type safety, or successful Godot display
do not transfer semantic authority.

Authority transfer is subsystem-specific. One C++ subsystem passing parity does
not make the whole native port authoritative.

## Authority transfer

The existing Python implementation remains the current semantic oracle.

Authority may move away from Python only through
`docs/architecture/authority_transfer_protocol.md`.

Parity evidence alone does not transfer authority.

A document may not claim C++/GDExtension, Godot, or GDScript owns semantic
gameplay behavior unless a completed transfer record exists and this authority
map has been updated.

## Forbidden migration shortcuts

- Reimplementing Python semantics in GDScript.
- Rewriting Python logic while porting unless explicitly requested.
- Changing semantics to make C++ cleaner.
- Duplicating topology, movement, collision, gravity, scoring, or trace
  utilities.
- Treating visual plausibility as semantic correctness.
- Letting Godot UI behavior define game-rule semantics.
