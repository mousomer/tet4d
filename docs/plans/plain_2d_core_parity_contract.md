# Plain 2D Core Parity Contract

Role: Stage 11 native core plain 2D parity contract
Status: active
Last updated: 2026-05-20

## Scope

Stage 9 ported enough deterministic C++ gameplay core behavior to reproduce the
Python-authored `gameplay_plain_2d_short` trace on required fields. Stage 10
strengthened that parity to include canonical snapshot serialization and
Python-compatible `state_hash` values. Stage 11 broadens that same plain
bounded 2D parity surface with three additional small Python golden traces.
The scope remains intentionally narrow:

- plain bounded 2D only;
- board size `6 x 6`;
- synthetic `TRACE_2D` active pieces only;
- authored trace commands only;
- rotation, hard drop/lock, and single-line clear coverage;
- post-lock spawn state exactly as exported by the Python oracle.

This contract does not authorize 3D, 4D, topology transport, endgame
simulation, or Python runtime calls from Godot. Stage 12 adds a separate live
plain bounded 2D shell that must keep C++ as the gameplay authority and must
not alter the Stage 11 trace parity contract.

Stage 12b live sequencing and game-over lifecycle are explicitly separate from
this parity fixture path. Live mode may use a deterministic fixed classic
sequence owned by `Plain2DSession`, and its snapshots may expose live-only
fields such as `game_over`, `game_over_reason`, `paused`, current piece, and
last command. Parity cases continue to use the synthetic active piece, authored
command list, and post-lock spawn shape recorded below.

## Stage 11 Trace Definitions

- `gameplay_plain_2d_short`: two-cell `TRACE_2D` domino at `(2, 3)` with move
  right, soft drop, hard drop; locks two cells with score `5`.
- `gameplay_plain_2d_rotation_short`: four-cell `TRACE_2D` T-like shape at
  `(2, 2)` with clockwise rotation and soft drop; no lock.
- `gameplay_plain_2d_hard_drop_lock`: one-cell `TRACE_2D` piece at `(2, -1)`
  with hard drop; locks one cell with score `5`.
- `gameplay_plain_2d_line_clear_short`: one-cell `TRACE_2D` piece at `(5, 4)`
  with authored starting locked cells; hard drop completes one row, clears it,
  leaves one survivor cell, and scores `45`.

## Canonical Snapshot And Hash Contract

The Python trace authority uses `tools/migration/trace_schema.py`:

- canonical JSON text: `json.dumps(payload, indent=2, sort_keys=True) + "\n"`;
- compact canonical JSON for hashes:
  `json.dumps(payload, sort_keys=True, separators=(",", ":"))`;
- stable hash: SHA-256 of the compact canonical JSON UTF-8 bytes.

Frame hashes are computed by `frame_payload(...)` over the complete frame
payload before adding that frame's `state_hash` key.

Final hash is computed over:

```text
{
  "case_id": "gameplay_plain_2d_short",
  "final_snapshot": <full final state snapshot>,
  "frames": <frames including each frame state_hash>
}
```

Stage 11 requires frame/final hashes to match these Python golden traces:

- `gameplay_plain_2d_short`: final
  `2d3a6eb2744d46bc147ae7d21855036e1ff241a99261ab5324b20958ec353139`.
- `gameplay_plain_2d_rotation_short`: final
  `8f2941eb755e7474ef5a43f35ed70ead49e3625dc8c22521b70227873838ce19`.
- `gameplay_plain_2d_hard_drop_lock`: final
  `05a15c901374c974d167774aacbd53bc56662ee9a10556b86acbeb94158b95a9`.
- `gameplay_plain_2d_line_clear_short`: final
  `b12eb245dc55563078b0342123f3bc519549b3eb75b40c5fd691e41536c95fc1`.

## Compared Fields

`tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d` compares these
C++ trace fields against the Stage 11 Python golden traces:

- `case_id`, `dimension`, `seed`, `topology_id`, `trace_type`,
  `trace_version`;
- command payloads;
- initial active piece, board shape, locked cells, settings, and settings
  digest;
- each frame's active piece, command payload, command result, drop/lock status,
  legal moves, lines, locked-cell digest, locked cells, score, and topology
  event;
- final locked-cell count, locked-cell digest, and score.
- per-frame and final `state_hash`;
- generator metadata, so the compact trace projection matches the Python
  golden trace exactly for this case.

## Native API Boundary

The Godot-facing Stage 11 API remains parity/smoke-only:

- `run_builtin_plain_2d_smoke_case()`;
- `list_plain_2d_parity_cases()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json(case_id)`;
- `get_plain_2d_required_field_parity(case_id)`.

It must not expose live gameplay APIs such as `step_game`, `move_piece`,
`rotate_piece`, `drop`, `lock`, topology APIs, or endgame APIs.

Stage 12 live plain 2D APIs are documented in
`docs/plans/godot_core_port_plan.md`. They are allowed only for plain bounded
2D and must not be used to mutate or reinterpret golden traces.

## Verification

Run:

```bash
./scripts/test_godot_tet4d_core.sh
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d
./scripts/build_godot_tet4d_core.sh
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```
