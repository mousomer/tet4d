# Plain ND Core Parity Contract

Role: native plain-ND trace-parity contract
Status: active native trace-parity contract through Stage 20; Stage 21 live ND planning is separate
Last updated: 2026-05-25

## Scope

The sidecar native C++ plain-ND trace path lives beside the accepted plain 2D
core. Stage 15 targets these Python-oracle golden traces:

- `gameplay_plain_3d_short`
- `gameplay_plain_4d_short`

Stage 18 adds rotation parity for:

- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`

Stage 19 adds clear/scoring parity for:

- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`

Stage 20 adds spawn-blocked game-over parity for:

- `gameplay_plain_3d_spawn_blocked_game_over`
- `gameplay_plain_4d_spawn_blocked_game_over`

It does not authorize live Godot 3D/4D gameplay, topology transport,
wrap/invert/sphere behavior, endgame simulation, C#, Python runtime calls from
Godot, or Godot-side gameplay legality. Stage 21 does not change this
trace-parity contract; it only plans future live plain 3D/4D Godot prototype
work in `docs/plans/live_plain_nd_godot_prototype_plan.md`.

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

### gameplay_plain_3d_plane_clear_short

- dimension: `3`
- board shape: `[2,3,2]`
- seed: `2023`
- topology: plain bounded
- gravity axis: `1`
- piece set: `native_3d`
- initial active piece: single-cell `TRACE_3D`
- initial active cells: `[[0,2,0]]`
- command:
  - `{"action":"lock_current_piece","id":"lock_plane_clear"}`
- initial locked fixture:
  - `{"coord":[1,2,0],"value":1}`
  - `{"coord":[0,2,1],"value":1}`
  - `{"coord":[1,2,1],"value":1}`
  - `{"coord":[1,1,1],"value":2}`
- expected clear: one full gravity-axis plane at `y=2`
- expected post-clear locked cells:
  - `{"coord":[1,2,1],"value":2}`
- expected `lines`: `1`
- expected `score`: `45`
- expected final locked digest:
  `5e9f3e56cd4891c7e96d954d52ed20072b2a62d12ac347db608cf8f630d4bd8b`
- expected frame state hash:
  `40af964de14050ef5d068e95d559385a6880450998b76d230da5450b7e2528d3`
- expected final state hash:
  `9c1737872582996818277166c9b8d900a2362868315f15d1a8f9338e7afa6d57`

### gameplay_plain_4d_plane_clear_short

- dimension: `4`
- board shape: `[2,3,1,2]`
- seed: `2024`
- topology: plain bounded
- gravity axis: `1`
- piece set: `embedded_2d`
- initial active piece: single-cell `TRACE_4D`
- initial active cells: `[[0,2,0,0]]`
- command:
  - `{"action":"lock_current_piece","id":"lock_hyperplane_clear"}`
- initial locked fixture:
  - `{"coord":[1,2,0,0],"value":1}`
  - `{"coord":[0,2,0,1],"value":1}`
  - `{"coord":[1,2,0,1],"value":1}`
  - `{"coord":[1,1,0,1],"value":2}`
- expected clear: one full gravity-axis hyperplane at `y=2`
- expected post-clear locked cells:
  - `{"coord":[1,2,0,1],"value":2}`
- expected `lines`: `1`
- expected `score`: `45`
- expected final locked digest:
  `06d0e35d7aea4e8c938561bdda9e42e377b77b3a09281e7ffdfd03e30e84fb4b`
- expected frame state hash:
  `6a6506b6f88f177570acac30881d5e17d6cbbc24a86143a22018a4e1164fec2b`
- expected final state hash:
  `7b18f81b698dd0638fc1a11db4a896273f6d3bf3e5e31ded6241af3b6d1bee1f`

### gameplay_plain_3d_spawn_blocked_game_over

- dimension: `3`
- board shape: `[5,5,5]`
- seed: `2025`
- topology: plain bounded
- gravity axis: `1`
- piece set: `native_3d`
- initial active piece: `null`
- initial locked fixture:
  - `{"coord":[2,0,2],"value":9}`
- command:
  - `{"action":"spawn_new_piece","id":"spawn_blocked"}`
- expected spawned active piece: `TRACE_3D_NEXT`, color id `7`
- expected active cells after blocked spawn:
  - `[2,-2,2]`
  - `[2,0,2]`
- expected `drop_lock_status.game_over`: `true`
- expected locked cells: unchanged blocking fixture
- expected final locked digest:
  `79dc09f39b5262ff1799fcca6103cf58a19393a8a08595aedbc926820a1e086b`
- expected frame state hash:
  `3d0edddb4835421ecc60f681144bed191d90081b69bf7746d3bd6fb601310cef`
- expected final state hash:
  `a950c1badd7dd47dda27d140b7aef5097e9331a890c145419076f1e938317619`

### gameplay_plain_4d_spawn_blocked_game_over

- dimension: `4`
- board shape: `[5,5,5,5]`
- seed: `2026`
- topology: plain bounded
- gravity axis: `1`
- piece set: `embedded_2d`
- initial active piece: `null`
- initial locked fixture:
  - `{"coord":[2,0,2,2],"value":9}`
- command:
  - `{"action":"spawn_new_piece","id":"spawn_blocked"}`
- expected spawned active piece: `TRACE_4D_NEXT`, color id `7`
- expected active cells after blocked spawn:
  - `[2,-2,2,2]`
  - `[2,0,2,2]`
- expected `drop_lock_status.game_over`: `true`
- expected locked cells: unchanged blocking fixture
- expected final locked digest:
  `3bdf132722194fb8c15892d5f679a439d6802c53803b2d7d15a1024d5b0c6031`
- expected frame state hash:
  `5a1262677f381cba918b8b3da7e73eb21f12c2fb5728cc2f7f02ea90142a7fdd`
- expected final state hash:
  `ee8f825bce34feb8fa7f9bdd15157f699bba9c34a650a582de6a6a3ee81d8ad6`

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

The rotation traces are implemented in Stage 18. The plane-clear/scoring
traces are implemented in Stage 19. The spawn-blocked game-over traces are
implemented in Stage 20 for the explicit fixtures only.

Stage 20 native C++ does not implement or claim parity for:

- plane clears beyond the two explicit single-clear fixtures above
- broader ND game-over behavior beyond the two explicit spawn-blocked fixtures
- command rejection after game-over beyond the legal-move probe behavior
  observed by the Stage 17 traces
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

Stage 20 is acceptable only if plain 2D parity remains green, the two short
plain-ND traces still match, the two rotation traces still match, the two
plane-clear/scoring traces still match, and the two spawn-blocked game-over
traces match Python golden traces including frame/final hashes. `--all-plain-nd`
is the native sidecar ND gate for the implemented short, rotation,
clear/scoring, and spawn-blocked traces.
