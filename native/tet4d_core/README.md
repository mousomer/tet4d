# tet4d native core

Stage 8 proved that the Godot shell can load and call a native C++
GDExtension. Stage 9 added the smallest plain bounded 2D deterministic core
needed to match `gameplay_plain_2d_short` on required trace fields. Stage 10
adds Python-compatible snapshot serialization and `state_hash` parity for that
same short trace. It is not playable Godot gameplay.

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

Allowed Stage 10 parity/smoke API:

- `run_builtin_plain_2d_smoke_case()`
- `get_plain_2d_parity_status()`
- `export_plain_2d_trace_json()`
- `get_plain_2d_required_field_parity()`

Run native C++ tests and trace parity with:

```bash
./scripts/test_godot_tet4d_core.sh
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --case gameplay_plain_2d_short
```

Stage 10 compares required trace fields plus frame/final `state_hash` values.
This core must not expose live gameplay, topology, endgame, or Python runtime
APIs.
