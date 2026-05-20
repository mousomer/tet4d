# Plain 2D Core Parity Contract

Role: Stage 9 native core parity contract
Status: active
Last updated: 2026-05-18

## Scope

Stage 9 ports only enough deterministic C++ gameplay core behavior to reproduce
the Python-authored `gameplay_plain_2d_short` trace. This is the first semantic
port stage, but it is still intentionally narrow:

- plain bounded 2D only;
- board size `6 x 6`;
- seed metadata `2001`;
- one synthetic `TRACE_2D` two-cell active piece at `(2, 3)`;
- commands: move right, soft drop, hard drop;
- hard drop locks the synthetic piece at `(3, 5)` and `(4, 5)`;
- lock score is `5`;
- no line clear occurs;
- the post-lock spawn is the classic `I` piece at `(2, -2)`.

This contract does not authorize 3D, 4D, topology transport, endgame
simulation, playable Godot controls, or Python runtime calls from Godot.

## Required Compared Fields

`tools/migration/compare_cpp_gameplay_trace.py --case gameplay_plain_2d_short`
compares these C++ trace fields against
`migration/golden_traces/gameplay/gameplay_plain_2d_short.json`:

- `case_id`, `dimension`, `seed`, `topology_id`, `trace_type`,
  `trace_version`;
- command payloads;
- initial active piece, board shape, locked cells, settings, and settings
  digest;
- each frame's active piece, command payload, command result, drop/lock status,
  legal moves, lines, locked-cell digest, locked cells, score, and topology
  event;
- final locked-cell count, locked-cell digest, and score.

Frame and final `state_hash` values are intentionally excluded in Stage 9.
Those hashes are Python canonical-JSON SHA-256 values over complete trace
payloads; the native core currently proves field parity and defers full hash
parity until the native trace serializer owns the same canonical JSON hashing
surface.

## Native API Boundary

The Godot-facing Stage 9 API remains parity/smoke-only:

- `run_builtin_plain_2d_smoke_case()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json()`.

It must not expose live gameplay APIs such as `step_game`, `move_piece`,
`rotate_piece`, `drop`, `lock`, topology APIs, or endgame APIs.

## Verification

Run:

```bash
./scripts/test_godot_tet4d_core.sh
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --case gameplay_plain_2d_short
./scripts/build_godot_tet4d_core.sh
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```
