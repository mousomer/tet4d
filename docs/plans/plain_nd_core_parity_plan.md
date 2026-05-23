# Plain ND Core Parity Plan

Role: Stage 14 migration architecture plan  
Status: active planning authority for plain bounded 3D/4D native parity  
Last updated: 2026-05-23

## 1. Decision summary

Stage 14 is planning-only. It does not implement 3D, 4D, topology transport,
endgame simulation, or live Godot 3D/4D gameplay.

The next native target is plain bounded 3D/4D gameplay trace parity against
the Python oracle:

- `gameplay_plain_3d_short`;
- `gameplay_plain_4d_short`.

The implementation strategy is conservative: preserve the accepted C++ plain
2D core and live `Plain2DSession`, then add a minimal plain-ND parity path
beside it. Shared helpers may be migrated only after 3D/4D parity is proven.
The C++ core does not become authoritative for 3D/4D until it matches the
Python golden traces, including `state_hash`.

## 2. Current accepted baseline

The accepted baseline is:

- Godot is the GDScript product shell.
- C++ GDExtension owns the live plain bounded 2D gameplay state.
- Godot captures input, owns presentation timing and HUD, sends command
  strings, and renders snapshots.
- C++ owns 2D movement/rotation legality, gravity tick result, lock, line
  clear, scoring, deterministic live piece sequence, game-over, and
  `state_hash`.
- Python remains the oracle/reference until replacement native behavior passes
  trace parity.
- Replay mode remains intact and consumes copied bundle traces.

Stage 14 must not disturb the accepted live 2D path.

## 3. Python oracle surfaces

The Python plain-ND gameplay oracle is centered on:

- `src/tet4d/engine/gameplay/game_nd.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/core/model/board.py`
- `src/tet4d/engine/core/rules/board_rules.py`
- `src/tet4d/engine/core/rules/lifecycle.py`
- `src/tet4d/engine/core/rules/locking.py`
- `src/tet4d/engine/core/piece_transform.py`
- `tools/migration/export_gameplay_trace.py`
- `tools/migration/trace_schema.py`
- `tools/migration/trace_cases.py`

Important oracle facts:

- Coordinates are tuples serialized as JSON arrays in axis order
  `(x, y, z)` for 3D and `(x, y, z, w)` for 4D.
- Axis `0` is `x`, axis `1` is gravity/down `y`, axis `2` is `z`, and axis
  `3` is `w`.
- Gravity axis is `1` for the existing plain 3D/4D cases.
- `y < 0` is allowed for an active piece before lock; locking cells above
  gravity top sets game-over in Python gameplay.
- `BoardND` stores sparse occupied cells as `coord -> color_id`.
- `GameConfigND` defaults to bounded topology, no gravity-axis wrapping,
  fixed seed RNG mode, `native_3d` for 3D, and `standard_4d_5` for 4D.
- `GameStateND` owns piece bags, spawn, move, soft drop, gravity step, hard
  drop, lock, clear/scoring, and game-over.
- `ActivePieceND` stores `shape`, `pos`, `rel_blocks`,
  `last_rotation_plane`, and `last_rotation_steps`.
- ND rotation is by explicit axis plane (`axis_a`, `axis_b`) and signed
  quarter-turn count through `rotate_blocks_nd`.
- Full-plane clears are levels along gravity axis where every non-gravity
  coordinate is occupied.
- Trace export serializes active cells, locked cells, legal move probes,
  command results, scores, line counts, and deterministic hashes.

## 4. Existing 3D/4D trace cases

The two plain-ND target traces are narrow by design.

`gameplay_plain_3d_short`:

- dimension: `3`
- board: `[5, 5, 5]`
- seed: `2002`
- settings: bounded, gravity axis `1`, piece set `native_3d`
- initial active piece: `TRACE_3D`, blocks `[[0,0,0],[1,0,0]]`, pos
  `[2,2,2]`, color id `8`
- commands: `move_axis(axis=2, delta=1)`, `soft_drop`, `hard_drop`
- frames: `3`
- frame hashes:
  - `38e0e8e58aa86f7c1ddc07866f57855277197da7275773b78e21f1645d44d383`
  - `7c68dd588ac5142ac2d2edf5f568cd61e3855a13127279f24a8679820812c755`
  - `b4d7e527117da73764e2ed96d088de5764f02a6252367a360d833861137281a5`
- final locked cells: `[2,4,3]` and `[3,4,3]`, value `8`
- final score: `5`
- final state hash:
  `9e183b178d0badec86b59a833782702d581b13a72d75bddeeda7f88333826dd7`

`gameplay_plain_4d_short`:

- dimension: `4`
- board: `[5, 5, 4, 4]`
- seed: `2003`
- settings: bounded, gravity axis `1`, piece set `standard_4d_5`
- initial active piece: `TRACE_4D`, blocks `[[0,0,0,0],[1,0,0,0]]`, pos
  `[2,2,1,1]`, color id `8`
- commands: `move_axis(axis=3, delta=1)`, `soft_drop`, `hard_drop`
- frames: `3`
- frame hashes:
  - `be685ea62f4886479f3162ec67b3c4062e087a746a3a8d51f9aaa8ba984aa7eb`
  - `84845aeec0566417ebcde69f0ecd92c1a87b6afc7290a2e6ca9099abafe6163f`
  - `9486343ef48eb65fb44ff96a13378cba134869bc4507a36551acf630d1da7488`
- final locked cells: `[2,4,1,2]` and `[3,4,1,2]`, value `8`
- final score: `5`
- final state hash:
  `d34d21da0a1c4aa6e947230e68e8b16a3e212b40bb7da1ccaef24200e7f80449`

The target traces do not exercise ND rotation, plane clears, topology,
spawn-blocked game-over, RNG piece-bag order beyond post-lock respawn snapshot
fields, or live Godot input.

## 5. C++ 2D core surfaces to preserve

The accepted native 2D code currently owns:

- `Coord2D`
- `PieceShape2D`
- `ActivePiece2D`
- `Board2D`
- `GameState2D`
- `GameCommand2D`
- `GameStepper2D`
- `Plain2DSession`
- `plain_2d_trace` export and required-field/hash parity APIs
- `Tet4DCoreApi` Godot wrapper methods for parity and live 2D

These surfaces must stay stable while ND parity is added. The live 2D session
has product acceptance and should not be templated or generalized as the first
ND step.

## 6. Generalization strategy

Choose the sidecar path first.

Stage 15 should add a minimal plain-ND parity path beside the existing 2D core
rather than refactoring the accepted 2D implementation into a template or
generic engine immediately. This reduces risk to live 2D and makes trace
debugging clearer.

Allowed early sharing:

- canonical JSON/hash helpers;
- simple coordinate serialization helpers with exact Python ordering;
- trace projection utilities where field names already match.

Deferred sharing:

- replacing `Board2D` with `BoardND`;
- changing `Plain2DSession`;
- unifying 2D and ND rotation implementations;
- adding live 3D/4D Godot command APIs.

## 7. What stays 2D-specific

The following stay 2D-specific until ND parity proves a better shared owner:

- live `Plain2DSession`;
- Godot `live_2d_*` API methods;
- Stage 11 plain 2D parity fixtures;
- 2D classic live sequence;
- 2D input bindings and live HUD;
- 2D spawn assumptions in live mode;
- 2D `Coord2D`/`Board2D` types.

No Stage 15 work should weaken accepted live 2D behavior.

## 8. Proposed ND data model

Use a simple runtime-dimensional coordinate model, not C++ templates.

Recommended types:

```text
CoordND
  values: vector<int>

PieceShapeND
  name: string
  blocks: vector<CoordND>
  color_id: int

ActivePieceND
  shape: PieceShapeND
  pos: CoordND
  rel_blocks: vector<CoordND>
  last_rotation_plane: optional<pair<int,int>>
  last_rotation_steps: int

BoardND
  dims: vector<int>
  cells: map<CoordND,int, LexicographicCoordLess>
```

Reasons:

- Golden traces serialize coordinates as variable-length arrays.
- A single runtime-dimensional type covers both 3D and 4D target traces.
- Lexicographic map ordering can match Python `sorted(tuple(...))`.
- Avoiding templates keeps exported trace debugging straightforward.
- Fixed `Coord3`/`Coord4` can be added later only if profiling or ergonomics
  demand it.

Validation rules:

- All coords must have `dimension == dims.size()`.
- All dimension sizes must be positive.
- Gravity axis must be within dimension.
- Bounded plain checks reject any non-gravity out-of-bounds coordinate and any
  coordinate where `coord[gravity_axis] >= dims[gravity_axis]`.
- Active cells above gravity top are allowed before lock.
- Occupancy ignores active cells above gravity top.

## 9. Proposed ND command model

Stage 15 should support only the command forms required by the target traces:

```text
move_axis(axis:int, delta:int)
soft_drop
hard_drop
gravity_step (optional for future plain-ND expansion)
```

`move_axis` mutates only through C++ legality checks. `soft_drop` and
`gravity_step` are gravity-axis `+1` movement attempts. `hard_drop` repeatedly
applies gravity-axis movement until blocked, then locks and respawns through
the native ND state.

The trace exporter should record command IDs and command payloads exactly as
Python does. Godot should not receive live ND gameplay commands in this stage.

## 10. Proposed ND rotation strategy

Rotation is the highest-risk part and is not covered by
`gameplay_plain_3d_short` or `gameplay_plain_4d_short`.

Stage 15 should not implement broad ND rotation unless a target trace requires
it. If a basic parser branch is needed, it should reject or mark unsupported
ND rotation cases rather than pretending parity exists.

When ND rotation becomes an explicit target, it must mirror Python
`rotate_blocks_nd`:

- rotate in the specified `(axis_a, axis_b)` plane;
- use signed quarter-turn count modulo 4;
- compute the pivot from active-plane bounding-box parity;
- for mixed parity, use the block nearest the active-plane center of mass;
- preserve non-rotation axes;
- update `last_rotation_plane` and `last_rotation_steps`;
- run placement through the same bounded/collision legality path;
- compare rotated active cells directly against Python trace cells and hashes.

## 11. Proposed ND drop/lock strategy

Plain-ND gravity uses axis `1` in the current target traces.

Soft drop:

- attempt to move active piece by `+1` on gravity axis;
- return `true` if movement succeeds, `false` if blocked;
- do not lock automatically for the `soft_drop` command.

Gravity step:

- if movement succeeds, keep active piece;
- if movement fails, lock current piece and respawn.

Hard drop:

- repeatedly apply gravity movement while legal;
- lock when the next gravity move is blocked;
- respawn if lock did not set game-over.

Lock:

- ignore active cells with `coord[gravity_axis] < 0` when committing visible
  locked cells;
- if any mapped active cell is above gravity top at lock time, set
  game-over;
- otherwise write visible active cells to `BoardND.cells` with the piece color
  id;
- add `lock_piece_points` to score;
- clear planes only when explicit trace coverage is added.

Spawn:

- for the Stage 15 target traces, initial active pieces are fixture-provided
  by trace case data.
- post-lock respawn should match Python enough to reproduce the active-piece
  payload after hard drop; because final trace hash includes final snapshot,
  this cannot be omitted.
- full RNG/bag parity beyond the target snapshots should remain a later
  explicit trace target.

Game-over:

- set native game-over when spawn cannot produce a legal eventually visible
  piece, when lock occurs above gravity top, or when no active piece exists
  for a gameplay command.
- Do not implement game-over in GDScript.

## 12. Proposed ND clear/scoring strategy

The target plain 3D/4D short traces do not clear planes. Stage 15 can match
them with lock-piece scoring only (`5` points).

Before broad ND clear/scoring is trusted, add explicit Python golden traces
that cover:

- one full 3D plane clear;
- two-plane clear;
- board-clear bonus in 3D;
- one full 4D hyperplane clear;
- scoring with the existing clear table and layer-size weighting rules.

When implemented, the native rule must mirror Python `BoardND.clear_planes`
and `score_with_clear_bonuses`: a full level is a complete non-gravity
coordinate plane at one gravity-axis value, and surviving cells above cleared
levels shift toward larger gravity coordinates.

## 13. Snapshot/hash parity plan

Reuse the Stage 10 compact canonical JSON/SHA-256 approach.

The C++ ND trace export must project exactly the same contract fields as
Python `export_gameplay_trace.py`:

- `case_id`
- `commands`
- `dimension`
- `final`
- `frames`
- `generator`
- `initial`
- `seed`
- `topology_id`
- `trace_type`
- `trace_version`

Frame payloads must include:

- `active_piece`
- `command`
- `command_id`
- `command_result`
- `drop_lock_status`
- `frame_index`
- `legal_moves`
- `lines`
- `locked_cell_digest`
- `locked_cells`
- `score`
- `state_hash`
- `topology_event`

ND active-piece payload must include:

- `cells`
- `color_id`
- `last_rotation_plane`
- `last_rotation_steps`
- `pos`
- `rel_blocks`
- `shape`

Coordinate serialization rules:

- serialize coordinates as arrays in axis order;
- sort coordinate arrays lexicographically;
- sort locked cells by coordinate;
- use compact canonical JSON with sorted object keys for `state_hash`;
- emit `null` for absent rotation plane and topology events.

`tools/migration/compare_cpp_gameplay_trace.py` should add explicit supported
cases for `gameplay_plain_3d_short` and `gameplay_plain_4d_short` only after
the native exporter exists. Until then, `--all-plain-2d` remains the accepted
2D gate.

## 14. Trace coverage gaps

Current plain-ND gaps:

- no ND rotation trace;
- no ND gravity-step trace in plain topology;
- no 3D plane clear trace;
- no 4D hyperplane clear trace;
- no spawn-blocked/game-over trace;
- no RNG/bag sequence parity trace;
- no topology transport in the plain-ND target;
- no live Godot 3D/4D path;
- no ghost/drop-target snapshot.

These gaps are acceptable for Stage 15 only if the stage is scoped to the two
existing short traces and documents unsupported behavior honestly.

## 15. Test plan

Native tests for Stage 15:

- construct fixture `GameStateND` for the 3D target trace;
- verify `move_axis(axis=2, delta=1)` updates cells and returns `true`;
- verify `soft_drop` updates gravity-axis position and returns `true`;
- verify `hard_drop` locks the two cells, scores `5`, and respawns the Python
  post-lock piece payload;
- repeat the same for the 4D target trace with `axis=3`;
- verify coordinate sorting and locked-cell digest parity;
- verify per-frame and final `state_hash` parity for both target traces;
- verify unsupported ND rotation cases fail explicitly until a rotation trace
  is introduced;
- verify existing Stage 11 plain 2D parity cases still pass.

Godot tests for Stage 15 should remain parity/smoke oriented only:

- native extension still loads;
- plain 2D live bridge still exposes accepted fields;
- replay loader still loads 3D/4D golden traces from the copied bundle;
- no live 3D/4D command dispatch exists.

Python migration tests:

- `compare_trace.py migration/golden_traces` remains green;
- `compare_cpp_gameplay_trace.py --all-plain-2d` remains green;
- new ND compare cases become required only after native ND exporter support is
  added.

## 16. Godot integration boundary

Stage 15 should not add live 3D/4D Godot gameplay.

Godot already displays copied 3D/4D replay traces through the shared replay
renderer. That is sufficient for native ND parity development. If Godot gets
new Stage 15 surface area, it should be limited to smoke/parity methods that
export or list native ND trace cases. It must not compute movement legality,
hard-drop distance, rotation, clear, scoring, spawn, or game-over.

Live 3D/4D shell work belongs after native trace parity is complete.

## 17. Implementation stages after Stage 14

Recommended sequence:

1. Stage 15: add native plain-ND trace contract scaffolding and a minimal ND
   data model beside the accepted 2D core; target only fixture construction,
   coordinate serialization, hashes, and explicit unsupported branches.
2. Stage 16: pass `gameplay_plain_3d_short` native trace parity.
3. Stage 17: pass `gameplay_plain_4d_short` native trace parity using the
   same sidecar ND path.
4. Stage 18: add explicit ND rotation/clear/game-over trace planning and then
   implementation only where golden traces exist.
5. Stage 19: prototype live Godot 3D/4D shell only after native plain-ND trace
   parity is stable.
6. Stage 20: plan topology transport parity separately before any wrap,
   invert, sphere-like, Topology Lab, or launch semantics are ported.

The stage numbers may be split smaller if a parity gate grows.

## 18. Risks and mitigations

- Risk: breaking accepted live 2D while generalizing. Mitigation: sidecar
  ND path first; no `Plain2DSession` refactor in Stage 15.
- Risk: coordinate ordering mismatch. Mitigation: use lexicographic `CoordND`
  ordering and compare digest/hash on every frame.
- Risk: rotation drift. Mitigation: defer ND rotation until an explicit trace
  requires it, then port Python `rotate_blocks_nd` exactly.
- Risk: hidden topology scope creep. Mitigation: target only
  `topology_id=plain`, bounded mode, no explorer transport.
- Risk: scoring/clear overreach. Mitigation: implement only lock score for
  short traces until clear traces exist.
- Risk: Godot becomes gameplay authority. Mitigation: no live ND command API
  in Stage 15; Godot remains replay/parity shell only.
- Risk: Python piece-bag parity gets confused with fixture parity.
  Mitigation: fixture initialization remains separate from any future live or
  RNG sequence path.

## 19. Acceptance criteria before starting implementation

Implementation may start only when:

- this plan is checked in and referenced from current state/backlog/RDS/core
  port docs;
- worktree is clean from Stage 13/14 planning edits;
- accepted live 2D behavior remains preserved;
- the next implementation stage explicitly targets only native trace parity,
  not live Godot 3D/4D;
- Python oracle surfaces and target hashes are recorded;
- 3D/4D trace coverage gaps are acknowledged;
- topology, endgame, C#, Python runtime calls from Godot, and Godot-side
  gameplay legality remain forbidden;
- existing plain 2D native parity, Godot tests, migration checks, and
  governance checks pass.
