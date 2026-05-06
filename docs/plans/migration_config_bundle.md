# Migration Config Bundle

Role: migration packaging boundary  
Status: active  
Last updated: 2026-05-06

## Purpose

Stage 4 exports a disposable migration bundle for future engine replay spikes.
The bundle packages config snapshots, golden trace indexes/copies, schema
metadata, and authority-doc indexes so Unity/Godot work can consume one
directory without scraping the Python repository layout.

The exported bundle is not authoritative. Authority remains in `config/`, the
Python runtime under `src/`, checked-in golden traces under
`migration/golden_traces/`, and the docs/tests/governance that define and
validate those sources.

## Locations

- Exporter: `tools/migration/export_config_bundle.py`
- Drift checker: `tools/migration/compare_config_bundle.py`
- Unity bundle sync: `tools/migration/sync_unity_bundle.py`
- Godot bundle sync: `tools/migration/sync_godot_bundle.py`
- Generated bundle: `migration/exported_bundle/`
- Trace authority: `migration/golden_traces/`

## Bundle Contents

- `manifest.json`: bundle metadata, authority flags, trace index, config digest
  summary, schema index reference, docs index reference, and verification
  commands.
- `config/tet4d_config_bundle.json`: source config snapshot with repo-relative
  paths, SHA-256 digests, raw payloads where safe, and trace/schema references.
- `traces/`: copied topology, gameplay, and endgame golden traces.
- `schemas/schema_index.json`: config schema digests plus the code-defined
  trace schema helper reference.
- `docs/authority_index.json`: digests and roles for the docs that define the
  migration authority boundary.
- `README.md`: concise generated/non-authoritative usage notes.

## Contract

- Bundle files are generated deterministically and checked into the repository
  only as reproducible migration artifacts.
- Bundle JSON uses canonical sorted formatting and stable SHA-256 digests.
- Bundle contents use repo-relative paths only and contain no timestamps, local
  absolute paths, memory reprs, or runtime object identities.
- The exporter must not mutate source config, golden traces, runtime code, or
  docs authority.
- Unity/Godot replay spikes may consume the bundle as input data, but engine
  scene, inspector, or project defaults must not become config authority.
- Unity runtime must consume a copied `StreamingAssets` bundle rather than
  reading `migration/exported_bundle/` directly from the repository root.
- Godot runtime must consume a copied `res://assets/tet4d_bundle/` bundle
  rather than reading `migration/exported_bundle/` directly from the
  repository root.

## Regeneration

```bash
PYTHONPATH=src .venv/bin/python tools/migration/export_config_bundle.py --out migration/exported_bundle
PYTHONPATH=src .venv/bin/python tools/migration/export_config_bundle.py --check
PYTHONPATH=src .venv/bin/python tools/migration/compare_config_bundle.py migration/exported_bundle
PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py --bundle migration/exported_bundle --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle
PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py --bundle migration/exported_bundle --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle --check
PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py --bundle migration/exported_bundle --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle
PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py --bundle migration/exported_bundle --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle --check
```

Trace freshness remains covered separately by:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/compare_trace.py migration/golden_traces
```

## Migration Rule

Future Unity/Godot work should first load this bundle, locate the topology,
gameplay, and endgame traces, and replay those traces frame-by-frame before
implementing independent topology transport, gameplay drop/lock logic, or
endgame simulation. Python remains the semantic oracle until a replacement
core passes trace parity.
