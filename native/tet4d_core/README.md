# tet4d native core

Stage 8 proved that the Godot shell can load and call a native C++
GDExtension. Stage 9 added the smallest plain bounded 2D deterministic core
needed to match `gameplay_plain_2d_short` on required trace fields. Stage 10
adds Python-compatible snapshot serialization and `state_hash` parity for that
same short trace. Stage 11 broadens the same plain bounded 2D parity surface to
small rotation, hard-drop/lock, and line-clear traces. It is not playable Godot
gameplay. Stage 12 adds the first live plain bounded 2D session. Godot sends
command strings and renders returned snapshots; C++ owns movement, rotation,
gravity tick, hard drop, lock, line clear, scoring, spawn, status, and hash.
Stage 12b keeps live piece selection in C++ with a deterministic fixed classic
sequence (`I, O, T, S, Z, J, L`) separate from the Stage 11 parity fixtures.
The live session also owns game-over detection and command rejection: snapshots
include `game_over`, `game_over_reason`, `paused`, and `state_hash`, and
gameplay commands after game-over are rejected until reset/new game. Stage 13
adds display-only `next_piece` and `last_command_status` fields for the Godot
HUD; Godot may time gravity and input repeat, but C++ owns the result of every
`tick`, movement, rotation, soft drop, hard drop, lock, line clear, score,
piece sequence, game-over, and hash update. Stage 15 adds a sidecar plain-ND
trace scaffold for `gameplay_plain_3d_short` and
`gameplay_plain_4d_short`. Stage 18 adds native parity only for
`gameplay_plain_3d_rotation_short` and
`gameplay_plain_4d_rotation_short`. Stage 19 adds native parity only for
`gameplay_plain_3d_plane_clear_short` and
`gameplay_plain_4d_plane_clear_short`. Stage 20 adds native parity only for
`gameplay_plain_3d_spawn_blocked_game_over` and
`gameplay_plain_4d_spawn_blocked_game_over`; it remains parity infrastructure
only and does not add live Godot 3D/4D gameplay. Stage 22 adds the first live
plain-ND gameplay path for 3D only. `PlainNDSession` owns live 3D state,
movement, rotation, soft/hard drop, tick/lock, clear/scoring, spawn/game-over,
command status, and `state_hash`; Godot still only sends commands and renders
snapshot JSON. Stage 39 adds provisional C++ core geometry helpers for
normalizing, translating, rotating, and hashing ND piece blocks, backed by
Python oracle parity tests and exposed to Godot as query helpers only. Live 4D,
topology, endgame, Python runtime calls, Godot-side gameplay legality, and
native semantic authority transfers remain deferred.

The native source tree has two layers:

- `src/core/`: plain C++ helpers with no Godot types.
- `src/godot/`: GDExtension bindings that expose the minimal `Tet4DCoreApi`
  wrapper to Godot.

The official `godot-cpp` repository is included as a Git submodule at
`native/third_party/godot-cpp`. On a fresh checkout, initialize submodules,
build the local extension, then run the Godot smoke tests:

```bash
git submodule update --init --recursive
./scripts/build_godot_tet4d_core.sh
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The extension test loads `res://addons/tet4d_core/tet4d_core.gdextension`.
It will fail on a fresh checkout until the submodule exists and the native
library has been built into `godot/Tet4D.Godot/addons/tet4d_core/bin/`.

To rebuild after C++ changes, run:

```bash
./scripts/build_godot_tet4d_core.sh
```

Allowed Stage 8 API:

- `get_core_version()`
- `get_core_status()`
- `echo_text(text)`
- `stable_hash_text(text)`
- `add_integers(a, b)`

Allowed Stage 11 parity/smoke API:

- `run_builtin_plain_2d_smoke_case()`
- `list_plain_2d_parity_cases()`
- `get_plain_2d_parity_status()`
- `export_plain_2d_trace_json(case_id)`
- `get_plain_2d_required_field_parity(case_id)`

Allowed Stage 12 live plain-2D API:

- `live_2d_reset()`
- `live_2d_apply_command(command)`
- `live_2d_tick()`
- `live_2d_snapshot_json()`
- `live_2d_status()`
- `live_2d_state_hash()`

Allowed Stage 20 plain-ND parity API:

- `run_builtin_plain_nd_smoke_case()`
- `list_plain_nd_parity_cases()`
- `get_plain_nd_parity_status()`
- `export_plain_nd_trace_json(case_id)`
- `get_plain_nd_required_field_parity(case_id)`

Allowed Stage 22 live plain-3D API:

- `live_3d_reset()`
- `live_3d_apply_command(command)`
- `live_3d_tick()`
- `live_3d_snapshot_json()`
- `live_3d_status()`
- `live_3d_state_hash()`

Allowed Stage 39 core geometry query API:

- `geometry_normalize_blocks(blocks)`
- `geometry_translate_blocks(blocks, offset)`
- `geometry_rotate_blocks(blocks, axis_a, axis_b, quarter_turns)`
- `geometry_hash_blocks(blocks)`

Allowed Stage 40 legality/topology diagnostic query API:

- `query_piece_pose_legal(dims, piece_cells, occupied_cells)`
- `query_topology_axis_wrap_cell_step(dims, wrapped_axes, coord, axis, delta)`

Run native C++ tests and trace parity with:

```bash
./scripts/test_godot_tet4d_core.sh
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-nd
```

Stage 11 compares required trace fields plus frame/final `state_hash` values
for `gameplay_plain_2d_short`, `gameplay_plain_2d_rotation_short`,
`gameplay_plain_2d_hard_drop_lock`, and
`gameplay_plain_2d_line_clear_short`.
The live API is plain bounded 2D only. It exposes the current piece name in
live status/snapshot data plus native next-piece and game-over fields, but
Godot must not choose or mutate the piece sequence, compute legality, or
synthesize game-over. The plain-ND API is trace export/list/status only for
the two short bounded 3D/4D golden traces, the two Stage 18 rotation traces,
the two Stage 19 plane-clear traces, and the two Stage 20 spawn-blocked
game-over traces. Stage 18 rotation uses
Python-compatible local `rel_blocks` plane rotation and serializes
`last_rotation_plane` / `last_rotation_steps` for hash parity. Stage 19
clear/scoring uses Python-compatible full gravity-axis plane/hyperplane clear,
locked-cell compaction, generic `lines`, score, and hash parity. Stage 20
spawn-blocked game-over uses Python-compatible spawn position, blocked
active-piece preservation, unchanged locked cells, `drop_lock_status.game_over`,
and hash parity. Stage 22 exposes live 3D only through the native session API
above. Stage 39 geometry helpers are deterministic query helpers only. They
must remain parity-backed by Python `piece_transform` behavior and must not
become gameplay legality, topology, replay, endgame, Python runtime, C#,
Steam, console behavior, or authority transfer. Stage 40 adds deterministic
legality and topology diagnostics only: bounded pose/translation/rotation
legality, collision, duplicate-cell rejection, bounded/torus neighbor
resolution, and seam transport metadata are parity-backed against Python public
engine APIs and `ExplorerTransportResolver`. These helpers must not become
live gameplay, topology traversal, replay schema, endgame, or authority
transfer.
