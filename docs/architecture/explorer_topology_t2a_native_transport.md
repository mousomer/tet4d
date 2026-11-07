# T2A native Explorer piece transport

Status: candidate implementation; no runtime authority transfer.
Design authority: [T1 piece contract](explorer_topology_piece_transport_contract.md)
and `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`.

## Scope and acceptance

This provider slice implements rank-2 bounded, cylinder and torus unit translations,
recorded per-cell inverses, complete indexed state admission, revision-bound
atomic application and Retry. Acceptance requires native preservation,
deterministic fixed-seed sequences, reviewed fixture conformance, unchanged
legacy parity and the repository verifier. Godot integration is T2B; rotations,
twisted seams and remaining profiles are separate work. The authority map and
terminal transfer records are unchanged.

## Production ownership

The extension build enables C++ exceptions through godot-cpp's supported
`disable_exceptions=false` option on every target. The core catches allocation
and length failures as `resource_limit` before publishing a replacement envelope;
these failures must not unwind through the Godot adapter boundary.

`native/tet4d_core/include/tet4d_core/explorer_piece.hpp` declares value-owned
`ExplorerPiece`, `PieceInverse`, `PieceCandidate`, `PieceEnvelope` and
`ExplorerPieceRuntime`. The implementation responsibilities are:

- `explorer_piece_state.cpp`: strict typed-state validation, admitted-profile
  normalization, signed local frames and exact canonical value comparison.
- `explorer_piece_transport.cpp`: pure `propose_piece_translation` and
  `propose_piece_inverse`, per-cell witnesses and periodic affine classification.
- `explorer_piece_runtime.cpp`: serialized `apply`, `retry` and value snapshots.

The existing `decode_topology_transport_profile` validates profile structure and
scalar limits. The admitted bounded/cylinder/torus subset normalizes disabled rows,
labels, seam direction and ordering to the existing canonical v1 payload
meaning; it does not replace the canonical schema or identity algorithm.
`topology_query_profile_from_transport` and `resolve_topology_cell_step_query`
perform every actual forward and inverse cell step. No second seam resolver is
introduced; `query.cpp`, ordinary geometry/pivots and Play are unchanged.

Original geometry is validated for normalized coordinates, lexicographic ID
assignment, uniqueness and face connectivity. Current cells are validated by
persistent ID, frame and occupancy; current chart connectivity is irrelevant.
Frames compose as `T F`; inverse steps are reconstructed as `-T a`, even though
T2A's admitted seams happen to have identity physical transport. Frame utilities
retain signed permutations for subsequent T2C operations.

Proposals canonicalize incoming row order, validate the full source, compute all
destinations and verify the reverse cells/frames before classification. Exact
canonical values bind proposals; no digest or trusted boolean authorizes a
commit. Runtime `apply` holds a mutex through source/revision comparison,
native recomputation, full-candidate comparison, private envelope preparation
and a no-throw owned-pointer swap. Allocation and revision failures publish
nothing. Snapshots return copies and expose no borrowed mutable state.

The envelope retains optional inverse descriptors but no diagnostic trace in
T2A. A matching inverse pops the top descriptor after success; descriptors can
also be supplied independently of history. Retry restores the compatible initial
semantic piece, clears undo to its empty initial baseline and increments the
revision. A different object, original geometry or profile baseline is rejected.
The signed 64-bit revision never wraps or rewinds, including extent-one moves.

Resource admission is capped at 4,096 cells and 4,096 retained descriptors, with
at most 64 authored seam rows before canonicalization. These are implementation
limits, not mathematical invalidity. Arithmetic uses the existing v1 axis/volume
envelope and signed 64-bit affine displacements. Invalid typed DTOs fail before
indexing or narrowing. No piece JSON/Variant boundary is exposed in this slice;
strict external serialization and Godot adapters remain later T2 work.

## Permanent native evidence

`explorer_piece_tests.cpp` executes production functions through the standard
`scripts/test_godot_tet4d_core.sh` runner and its
`--explorer-piece-conformance` mode. The full repository gate invokes that runner.
`explorer_piece_assertions.hpp` supplies reusable conservation, exact recovery,
atomic no-op, frame, occupancy and deterministic-proposal assertions for T2C.

`tools/migration/export_explorer_piece_fixtures.py` transcribes approved JSON
fields into an ignored build header, including full expected states, witnesses,
inverse versions and E8 lifecycle values. It computes no movement results and
never changes fixture expectations. Native output records the fixture SHA-256.
E1, bounded interior, E2, E8, E9 and torus self-step execute directly.

The owner expanded T2A to include cylinders with either X or Y wrapping. The
original E3 Y-only wrapping fixture, cylinder wall and cylinder wrap cases execute
directly. A separately labeled `E3_torus_companion` also checks the same reviewed
chart-split correspondence on the torus. Expected fixture data stays unchanged.
Cylinder acceptance requires both directions on the wrapped axis, blocking on
the unwrapped axis, exact inverses, extent-one behavior, periodic classification,
and the same conservation/atomicity sequence checks as bounded and torus boards.

Fixed seeds 172, 176 and 20261106 exercise nine shapes against seven board sizes,
all four profile variants (bounded, X-cylinder, Y-cylinder, torus) and all eight 2D signed frames. Only shapes whose initial
occupancy fits are admitted. Each sequence attempts 32 actions, checks every
accepted transition, and reverses every accepted action with its descriptor.
Failures print the seed, shape index, board, topology, frame and action prefix.
Counts distinguish admitted initial states/sequences, successful commits,
rejected translation requests, committed inverse recoveries and complete-envelope
atomic rejection assertions. Profile/source/action/candidate/inverse corruption,
partial wall blocks, ABA, Retry and resource exhaustion are permanent regressions.

## Verification and remaining acceptance

Run the native harness first, then the T1 contract checker, focused canonical,
resolver and native parity tests, `git diff --check`, `./gov check`, and
`CODEX_MODE=1 ./scripts/verify.sh` using the governed interpreter. Test output and
the PR bind measured results to the checked tree; expected fixtures retain their
T1 `not_run` metadata. Product authority, Godot integration, other platforms and
human UI acceptance are not established by this provider suite.
