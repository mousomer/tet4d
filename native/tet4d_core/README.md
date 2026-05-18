# tet4d native core skeleton

Stage 8 proves that the Godot shell can load and call a native C++
GDExtension. It is not gameplay implementation.

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

This skeleton must not expose gameplay, topology, endgame, trace parity, or
Python runtime APIs.
