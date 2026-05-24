# Plain ND Coverage Expansion Plan

Role: Stage 16 planning authority for broadening plain-ND parity beyond the short traces  
Status: Stage 17 oracle traces added; C++ parity for those traces is future work
Last updated: 2026-05-24

## 1. Decision Summary

Stage 15 proved the native sidecar ND scaffold can match the two short bounded
3D/4D traces and their `state_hash` values. Stage 16 does not implement new
gameplay semantics. It defines the next coverage expansion so the next native
implementation stage can safely add explicit trace cases for rotation,
clear/scoring, and spawn-blocked game-over without guessing at Python behavior.

Recommended direction:

- keep the accepted plain 2D core untouched
- keep the Stage 15 ND sidecar path
- add explicit Python-oracle trace cases before broadening C++ semantics
- keep Godot parity/list/export/status only
- defer live Godot 3D/4D, topology, endgame, and RNG/bag parity

Recommended next implementation sequence:

1. Stage 17: add explicit Python-oracle ND trace cases and migration coverage.
2. Stage 18: implement ND rotation parity against the new rotation traces.
3. Stage 19: implement ND clear/scoring parity against the new plane-clear traces.
4. Stage 20: implement ND spawn-blocked game-over parity and command rejection.

## 2. Current ND Baseline

The current native baseline is the Stage 15 sidecar ND scaffold:

- `CoordND`, `BoardShapeND`, `BoardND`, `PieceShapeND`, `ActivePieceND`,
  `GameStateND`, `GameCommandND`, `GameStepperND`
- trace exports for `gameplay_plain_3d_short` and `gameplay_plain_4d_short`
- parity-only Godot bridge methods for ND trace listing/export/status
- `compare_cpp_gameplay_trace.py --all-plain-nd`

Current native ND command coverage is narrow:

- `move_axis`
- `soft_drop`
- `hard_drop`
- basic lock/spawn path
- frame/final `state_hash`

Current native ND behavior is fixture-driven and does not attempt to be a full
generalization of Python ND gameplay yet.

## 3. Python Oracle References Inspected

Relevant Python sources and test coverage to inspect before any ND extension:

- `src/tet4d/engine/gameplay/game_nd.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/api.py`
- `tests/unit/engine/test_game_nd.py`
- `tests/unit/engine/test_topology.py`
- `tools/migration/export_gameplay_trace.py`
- `tools/migration/trace_schema.py`
- `tools/migration/trace_cases.py`
- `tools/migration/compare_cpp_gameplay_trace.py`
- `tools/migration/compare_trace.py`

Key semantics already confirmed from the oracle:

- rotation is explicit plane-based ND rotation, not a 2D-style single-turn API
- active-piece payload carries `last_rotation_plane` and `last_rotation_steps`
- clears are full gravity-axis slices, not generic shape clears
- spawn can set game-over when the next active piece cannot spawn legally
- locked cells above gravity top also set game-over
- `state_hash` includes the final snapshot and frame payloads under compact
  canonical JSON rules

## 4. Existing ND Trace Coverage

Currently checked-in gameplay traces relevant to ND are only:

- `gameplay_plain_3d_short`
- `gameplay_plain_4d_short`

Those traces cover:

- `move_axis`
- `soft_drop`
- `hard_drop`
- lock/respawn snapshot timing
- score and locked-cell digest
- frame/final `state_hash`

They do not cover:

- ND rotation
- ND plane/slice/line clear behavior
- ND scoring breadth
- spawn-blocked game-over
- soft-drop lock variants
- hard-drop edge cases
- broader RNG/bag or piece-sequence behavior

## 5. Coverage Gaps

The gaps that must be covered by explicit traces before broader native ND
implementation are:

- rotation semantics in 3D and 4D
- clear semantics in 3D and 4D
- spawn-blocked game-over in 3D and 4D
- soft-drop edge cases where the next gravity step locks immediately
- hard-drop edge cases at the gravity boundary
- optionally, deterministic fixture-based piece sequence breadth if the trace
  setup needs it

These gaps should stay explicit. They should not be hidden inside a broad
catch-all trace that mixes unrelated behaviors.

## 6. Proposed New Trace Cases

Stage 17 trace set:

- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`
- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`
- `gameplay_plain_3d_spawn_blocked_game_over`
- `gameplay_plain_4d_spawn_blocked_game_over`

Optional only if later needed for exporter fidelity:

- `gameplay_plain_3d_soft_drop_lock`
- `gameplay_plain_4d_soft_drop_lock`
- `gameplay_plain_3d_hard_drop_edge`
- `gameplay_plain_4d_hard_drop_edge`

Trace design rule:

- one behavior family per trace
- no rotation/clear/game-over/RNG mixing in the same case unless a very small
  snapshot fixture absolutely requires it

### Proposed case details

`gameplay_plain_3d_rotation_short`

- behavior under test: single explicit 3D rotation and its snapshot fields
- dimension: 3
- fixture setup: small piece whose rotation is legal in an empty bounded board
- command sequence: one rotation command, optionally followed by a no-op
- required snapshot fields: `active_piece.rel_blocks`, `last_rotation_plane`,
  `last_rotation_steps`, `legal_moves`, `state_hash`
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: plane-based rotation, rotation-state serialization, rejection
  path for invalid rotation
- known risk: Python uses kick resolution, so the fixture must be chosen so the
  intended case does not depend on an ambiguous kick

`gameplay_plain_4d_rotation_short`

- behavior under test: single explicit 4D rotation
- dimension: 4
- fixture setup: small 4D piece with one legal rotation plane
- command sequence: one rotation command, optionally followed by a no-op
- required snapshot fields: same as above plus 4D coordinate serialization
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: 4D plane rotation and matching snapshot export
- known risk: 4D rotation plane/orientation semantics must match Python exactly

`gameplay_plain_3d_plane_clear_short`

- behavior under test: clearing one full gravity-axis slice and compaction
- dimension: 3
- fixture setup: nearly full plane with one deliberate hole and a falling piece
- command sequence: one lock-triggering command sequence
- required snapshot fields: `lines`, `score`, `locked_cells`, `locked_cell_digest`,
  `game_over`, `state_hash`
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: plane clear, compaction, scoring, hash export
- known risk: clear timing must match Python snapshot timing, especially whether
  the snapshot is taken after lock but before or after respawn

`gameplay_plain_4d_plane_clear_short`

- behavior under test: clearing one full gravity-axis hyperplane
- dimension: 4
- fixture setup: nearly full hyperplane with one deliberate hole
- command sequence: one lock-triggering command sequence
- required snapshot fields: same as 3D clear case
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: 4D hyperplane clear and scoring
- known risk: compaction ordering on the non-gravity axes must match Python

`gameplay_plain_3d_spawn_blocked_game_over`

- behavior under test: native spawn rejection when the next piece cannot be
  legally spawned
- dimension: 3
- fixture setup: nearly blocked board and forced post-lock respawn piece
- command sequence: one hard drop or lock-triggering action
- required snapshot fields: `game_over`, `game_over_reason`, `current_piece`,
  `state_hash`
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: spawn validation, game-over reason, command rejection after game-over
- known risk: the fixture must force a blocked spawn without relying on RNG

`gameplay_plain_4d_spawn_blocked_game_over`

- behavior under test: 4D spawn rejection and game-over reason reporting
- dimension: 4
- fixture setup: nearly blocked board and forced post-lock respawn piece
- command sequence: one hard drop or lock-triggering action
- required snapshot fields: same as 3D case
- expected state_hash policy: explicit golden hash from Python exporter
- C++ needed: same as above in 4D
- known risk: blocked-spawn geometry is easier to get wrong in 4D because the
  piece may be above the board while still being legal for several steps

## 7. ND Rotation Plan

Python rotation is explicit axis-plane rotation.

What the plan needs to preserve:

- rotation is encoded by the axes being rotated, not by a generic clockwise
  flag
- `ActivePieceND` stores the most recent rotation plane and step count
- `rotate_blocks_nd` is the source of truth for block transformation
- kicks, if any, are governed by Python's rotation-kick resolver

What the next implementation stage should do:

- add explicit rotation traces before broadening the C++ ND implementation
- verify whether 3D and 4D fixtures can be rotation-only without kicks
- if kicks are unavoidable, capture them in the Python trace and mirror them
  in C++
- serialize `last_rotation_plane` and `last_rotation_steps` in the native trace
  export

Open question to settle before implementation:

- whether the target rotation traces can be chosen so that no kick resolution
  is required, which would make the first C++ parity pass much safer

## 8. ND Clear/Scoring Plan

Python clear semantics are full gravity-axis slices:

- in 3D, a clear is a full plane orthogonal to gravity
- in 4D, a clear is a full hyperplane orthogonal to gravity
- surviving cells compact toward the gravity direction after the clear
- scoring is applied after lock and after clear resolution

The plan for the next stage:

- add a small 3D plane-clear trace and a small 4D plane-clear trace
- ensure the exporter records post-lock snapshot timing consistently
- verify score and line counters after the clear, not before
- verify locked-cell digest after compaction

If Python clear semantics are not obvious for a fixture, the blocker is in the
oracle/test layer, not the C++ implementation layer. The plan should add or
adjust Python trace fixtures first rather than guessing at native behavior.

## 9. ND Game-Over Plan

Python game-over should be treated as native-owned and fixture-driven in the
next stage.

The plan is:

- add explicit spawn-blocked game-over traces for 3D and 4D
- use fixed fixtures rather than letting RNG/bag breadth block the stage
- verify `game_over` and `game_over_reason` after the blocked spawn attempt
- verify commands after game-over are rejected except reset/new game if that
  path is exposed later

Game-over traces should be fixture-only at first. They should not require live
Godot ND commands or any topology behavior.

## 10. ND Soft-Drop/Hard-Drop Edge-Case Plan

Optional edge cases are useful only if they help disambiguate lock timing:

- soft-drop lock trace: proves the frame that transitions from movement to lock
- hard-drop edge trace: proves the gravity boundary and lock/respawn snapshot

Recommendation:

- do not make these the first Stage 17 traces
- add them only if rotation/clear/game-over traces leave an ambiguity about
  snapshot timing or command rejection

## 11. RNG/Piece-Sequence Decision

Default recommendation:

- keep the next stage fixture-driven
- do not port broad RNG/bag parity yet
- do not let piece-sequence breadth block rotation/clear/game-over coverage

The Stage 17 traces use explicit, deterministic fixtures and fixed spawn shapes
where needed. Broader RNG/bag parity can wait until the movement, rotation,
clear, and game-over semantics are already stable.

## 12. C++ Implementation Sequence

Recommended next implementation order:

1. Stage 17: add the explicit Python-oracle ND traces and migration coverage
   for the new case ids.
2. Stage 18: implement ND rotation parity to satisfy the new rotation traces.
3. Stage 19: implement ND clear/scoring parity to satisfy the new plane-clear
   traces.
4. Stage 20: implement ND spawn-blocked game-over parity and command rejection
   to satisfy the new game-over traces.

This sequence keeps trace design ahead of native behavior, which is the lower
risk path for an oracle-driven port.

## 13. Native Test Plan

Add or expand native tests to cover:

- explicit ND rotation acceptance and rejection
- plane-clear scoring and compacted locked-cell layout
- spawn-blocked game-over and `game_over_reason`
- command rejection after game-over
- stable `state_hash` parity for the new traces
- existing Stage 11 plain 2D parity remains green
- existing Stage 15 plain ND short-trace parity remains green

Prefer tests that directly exercise the ND state model before the trace export
path, then verify the exported JSON only after the semantics are stable.

## 14. Compare-Tool Plan

Current compare tooling supports `--all-plain-nd` for the implemented native
short traces. Stage 17 leaves that gate scoped to implemented C++ parity cases
so oracle-only future traces do not fail prematurely.

Compare-tool policy:

- keep `--all-plain-nd` limited to implemented native ND cases
- keep `--all-plain-2d` unchanged
- preserve first-mismatch reporting by frame/field path
- keep hash mismatch summaries visible
- add future explicit C++ case support only as semantics are implemented

If a new oracle-only trace is requested through `--case` before C++ support is
implemented, the compare tool should fail clearly as unsupported rather than
silently passing an incomplete set.

## 15. Godot API Boundary

No live Godot 3D/4D API belongs in this stage.

Allowed Godot surface:

- list ND parity cases
- export ND trace JSON
- report ND parity status
- smoke-test native ND export

Forbidden Godot surface:

- live ND commands
- live ND rotation
- live ND gravity stepping
- topology transport
- endgame
- Godot-side legality checks

Godot should remain a parity/list/export/status shell until the native ND
semantics are broader and stable.

## 16. Risks and Mitigations

- Risk: rotation fixtures depend on kicks and become hard to reason about.
  Mitigation: choose rotation fixtures that avoid kicks if possible; otherwise
  add explicit oracle coverage before native changes.
- Risk: plane clear timing differs between lock, clear, and respawn.
  Mitigation: add separate clear traces and keep snapshot timing explicit.
- Risk: spawn-blocked game-over is conflated with lock-above-top behavior.
  Mitigation: make the blocked-spawn fixture distinct from lock-above-top.
- Risk: RNG/bag parity becomes a blocker.
  Mitigation: keep Stage 17 fixture-driven and defer broad RNG work.
- Risk: live 2D behavior regresses while ND expands.
  Mitigation: preserve the Stage 11/12/13 2D tests and keep the 2D core
  untouched.

## 17. Acceptance Criteria for the Next Implementation Stage

Stage 16 is complete only if:

1. `docs/plans/plain_nd_coverage_expansion_plan.md` exists.
2. It names the next explicit ND trace cases to add.
3. It identifies Python oracle files/tests for rotation, clear/scoring, and
   game-over.
4. It identifies the C++ surfaces to extend.
5. It defines the next implementation stage as trace-first, not live Godot ND.
6. It preserves accepted live plain 2D.
7. It forbids live Godot ND APIs.
8. It forbids topology/endgame scope creep.
9. Existing 2D and ND parity gates remain green.
10. Governance and CI gates remain green.
