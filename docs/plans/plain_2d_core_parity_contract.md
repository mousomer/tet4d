# Plain 2D Core Parity Contract

Role: Stage 10 native core snapshot/hash parity contract
Status: active
Last updated: 2026-05-20

## Scope

Stage 9 ported enough deterministic C++ gameplay core behavior to reproduce the
Python-authored `gameplay_plain_2d_short` trace on required fields. Stage 10
strengthens that parity to include canonical snapshot serialization and
Python-compatible `state_hash` values. The scope remains intentionally narrow:

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

For `gameplay_plain_2d_short`, Stage 10 requires these hashes:

- frame 0: `d02e1823a320d5a4c3203a3cb6d103518c5f5168a67f2ebffc193c23a0e80ced`;
- frame 1: `1f07ea939bcd495c97b21501b14fe1cd7a4e44b73e4ad4fad14dfd0ddb381847`;
- frame 2: `f1eed6ec35fc8d5aae39ededd81df9eff3bb9148b9def9c8b0d7e5b8e1d59e5a`;
- final: `2d3a6eb2744d46bc147ae7d21855036e1ff241a99261ab5324b20958ec353139`.

## Compared Fields

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
- per-frame and final `state_hash`;
- generator metadata, so the compact trace projection matches the Python
  golden trace exactly for this case.

## Native API Boundary

The Godot-facing Stage 10 API remains parity/smoke-only:

- `run_builtin_plain_2d_smoke_case()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json()`.
- `get_plain_2d_required_field_parity()`.

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
