# Tet4D Unity Trace Replay Spike

This Unity project is a replay-only spike for tet4d migration work.

It consumes a copied Stage 4 migration bundle from:

- `Assets/StreamingAssets/tet4d_bundle/`

It does not:

- call Python at runtime;
- read `src/`, `config/`, `tools/`, or `docs/` at runtime;
- implement gameplay rules;
- implement topology transport;
- simulate endgame particles;
- treat inspector, prefab, or scene values as semantic authority.

## Bundle Sync

Copy the generated bundle into `StreamingAssets` with:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py \
  --bundle migration/exported_bundle \
  --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle
```

Check for drift with:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py \
  --bundle migration/exported_bundle \
  --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle \
  --check
```

## Runtime Scope

The runtime loads:

- `manifest.json`
- `config/tet4d_config_bundle.json`
- copied topology traces
- copied gameplay traces
- copied endgame traces

The runtime renders frames and metadata only. Python remains the semantic
oracle and the exported bundle remains non-authoritative.

## Opening In Unity

1. Open `unity/Tet4D.Unity/` in Unity.
2. Let Unity import the project and generate `.meta`, `Library/`, and other
   local files.
3. Create or open a scene and add a `TraceReplayController` component.
4. Enter Play Mode to bootstrap the camera, renderer, and HUD.

`Assets/Tet4D/Scenes/` is reserved for the replay scene, but the actual
`.unity` asset was not generated in this environment because the Unity editor
and CLI are unavailable here.

## Tests

If Unity CLI is installed locally, run EditMode tests with a command like:

```bash
Unity \
  -batchmode \
  -projectPath unity/Tet4D.Unity \
  -runTests \
  -testPlatform EditMode \
  -testResults unity/Tet4D.Unity/TestResults_EditMode.xml \
  -quit
```

The C# tests cover bundle authority flags, manifest loading, and sample trace
parsing. They were written but not executed in this environment.

## Known Limitations

- The visuals are intentionally rough and diagnostic-first.
- The runtime uses copied bundle JSON and does not try to match pygame output.
- 4D is displayed as visible W-separated board slices rather than a final 4D
  presentation.
