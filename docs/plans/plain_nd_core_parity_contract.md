# Plain ND Core Parity Contract

Role: native plain-ND trace-parity contract
Status: active for Stage 15 movement/drop traces and Stage 18 rotation traces
Last updated: 2026-05-24

## Scope

The sidecar native C++ plain-ND trace path lives beside the accepted plain 2D
core. Stage 15 targets these Python-oracle golden traces:

- `gameplay_plain_3d_short`
- `gameplay_plain_4d_short`

Stage 18 adds rotation parity for:

- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`

It does not authorize live Godot 3D/4D gameplay, topology transport,
wrap/invert/sphere behavior, endgame simulation, C#, Python runtime calls from
Godot, or Godot-side gameplay legality.

## Python Oracle References

The authoritative semantics for this scaffold are:

- `src/tet4d/engine/gameplay/game_nd.py`
- `src/tet4d/engine/gameplay/pieces_nd.py`
- `src/tet4d/engine/core/model/board.py`
- `src/tet4d/engine/core/rules/lifecycle.py`
- `src/tet4d/engine/core/rules/locking.py`
- `tools/migration/export_gameplay_trace.py`
- `tools/migration/trace_cases.py`
- `tools/migration/trace_schema.py`

Coordinates serialize in axis order: `[x,y,z]` for 3D and `[x,y,z,w]` for
4D. Axis `1` is the gravity axis. Active cells may exist above gravity top
where `y < 0`; locked cells may not.

## Target Cases

### gameplay_plain_3d_short

- dimension: `3`
- board shape: `[5,5,5]`
- seed: `2002`
- topology: plain bounded
- gravity axis: `1`
- piece set: `native_3d`
- initial active piece: `TRACE_3D`
- initial active cells: `[[2,2,2],[3,2,2]]`
- commands:
  - `{"action":"move_axis","axis":2,"delta":1,"id":"move_z"}`
  - `{"action":"soft_drop","id":"soft_drop"}`
  - `{"action":"hard_drop","id":"hard_drop"}`
- expected final locked cells:
  - `{"coord":[2,4,3],"value":8}`
  - `{"coord":[3,4,3],"value":8}`
- expected final score: `5`
- expected final locked digest:
  `4b7a6b700d15a928dd23c2a187403358cb3dcf1fd03c8855559d26663d6ded1d`
- expected final state hash:
  `9e183b178d0badec86b59a833782702d581b13a72d75bddeeda7f88333826dd7`

### gameplay_plain_4d_short

- dimension: `4`
- board shape: `[5,5,4,4]`
- seed: `2003`
- topology: plain bounded
- gravity axis: `1`
- piece set: `standard_4d_5`
- initial active piece: `TRACE_4D`
- initial active cells: `[[2,2,1,1],[3,2,1,1]]`
- commands:
  - `{"action":"move_axis","axis":3,"delta":1,"id":"move_w"}`
  - `{"action":"soft_drop","id":"soft_drop"}`
  - `{"action":"hard_drop","id":"hard_drop"}`
- expected final locked cells:
  - `{"coord":[2,4,1,2],"value":8}`
  - `{"coord":[3,4,1,2],"value":8}`
- expected final score: `5`
- expected final locked digest:
  `49a3a8a0dffab41bfaaf4c5dc3210d2d50de7f52d9891f4a2ec812d645114463`
- expected final state hash:
  `d34d21da0a1c4aa6e947230e68e8b16a3e212b40bb7da1ccaef24200e7f80449`

### gameplay_plain_3d_rotation_short

- dimension: `3`
- board shape: `[5,5,5]`
- seed: `2021`
- topology: plain bounded
- gravity axis: `1`
- piece set: `native_3d`
- initial active piece: `TRACE_3D`
- initial active cells: `[[2,2,2],[2,2,3],[2,3,2],[3,2,2]]`
- command:
  - `{"action":"rotate","axis_a":0,"axis_b":2,"delta":1,"id":"rotate_xz_cw"}`
- expected rotated active cells:
  - `[2,2,2]`
  - `[2,2,3]`
  - `[2,3,3]`
  - `[3,2,3]`
- expected `last_rotation_plane`: `[0,2]`
- expected `last_rotation_steps`: `1`
- expected final state hash:
  `2d2ada3b5b425bf649c66cd8e6b2c3c2e24a57c4f8a7dc8aab26ac72a33a7e4d`

### gameplay_plain_4d_rotation_short

- dimension: `4`
- board shape: `[5,5,5,5]`
- seed: `2022`
- topology: plain bounded
- gravity axis: `1`
- piece set: `standard_4d_5`
- initial active piece: `TRACE_4D`
- initial active cells: `[[2,2,2,2],[2,2,3,2],[2,3,2,2],[3,2,2,2]]`
- command:
  - `{"action":"rotate","axis_a":0,"axis_b":3,"delta":1,"id":"rotate_xw_cw"}`
- expected rotated active cells:
  - `[2,2,2,1]`
  - `[2,2,2,2]`
  - `[2,2,3,2]`
  - `[2,3,2,2]`
- expected `last_rotation_plane`: `[0,3]`
- expected `last_rotation_steps`: `1`
- expected final state hash:
  `c3ccf55ccbac1998e7973ba4dc5e163398f2e32a6999cc933a3e4065dd71d34c`

## Snapshot Fields

The native trace export must match the Python contract projection:

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

Frame payloads include active piece data, command data, command result,
drop/lock status, legal move probes, score, line count, locked cells,
locked-cell digest, topology event, and `state_hash`.

## Hash Rules

Native hashes must match Python `tools/migration/trace_schema.py`:

- JSON is compact canonical JSON with sorted keys.
- Coordinates are sorted lexicographically.
- Locked cells are sorted by coordinate.
- `state_hash` is SHA-256 of the compact canonical payload.
- The final hash is computed from `case_id`, `final_snapshot`, and the hashed
  frame payloads.
- ND `final_snapshot` includes the identity `piece_frame` payload:
  `{"permutation":[0..n-1],"signs":[1..1]}`.

## Unsupported Or Deferred Semantics

Stage 17 adds Python-oracle golden traces for the following deferred semantics:

- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`
- `gameplay_plain_3d_spawn_blocked_game_over`
- `gameplay_plain_4d_spawn_blocked_game_over`

The rotation traces are implemented in Stage 18. Plane-clear/scoring and
spawn-blocked game-over traces remain oracle-only until later stages implement
those broader ND semantics.

Stage 18 native C++ does not implement or claim parity for:

- plane clears beyond Python oracle trace generation
- spawn-blocked ND game-over fixtures in C++
- seeded RNG/bag parity beyond fixture-driven post-lock respawn
- topology transport
- live Godot 3D/4D commands
- ghost/drop preview
- endgame simulation

Unsupported trace case IDs must fail clearly rather than silently exporting an
unverified trace.

## Native API Boundary

Allowed native/Godot-facing plain-ND parity APIs:

- `list_plain_nd_parity_cases()`
- `get_plain_nd_parity_status()`
- `export_plain_nd_trace_json(case_id)`
- `get_plain_nd_required_field_parity(case_id)`
- `run_builtin_plain_nd_smoke_case()`

Forbidden Stage 15 APIs:

- `create_live_3d_session`
- `create_live_4d_session`
- `step_nd_game`
- live `move_axis`
- live ND rotation
- topology APIs
- endgame APIs

## Verification

Required parity checks:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-nd
```

Stage 18 is acceptable only if plain 2D parity remains green, the two short
plain-ND traces still match, and the two rotation traces match Python golden
traces including frame/final hashes.
