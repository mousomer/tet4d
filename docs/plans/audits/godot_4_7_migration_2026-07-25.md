# Godot 4.7 Migration Audit

Date: 2026-07-25
Branch: `codex/configurable-plain-boards`
Scope: Godot product shell, GDExtension descriptor, native build dependency,
local verification, and blocking CI

## Decision and boundaries

Tet4D now targets Godot `4.7.1-stable`, the newest officially published stable
4.7 patch on the migration date. The exact engine build is
`4.7.1.stable.official.a13da4feb`, from engine commit
`a13da4feb8d8aefc283c3763d33a2f170a18d541`.

The `godot-cpp` submodule is pinned to
`5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731`, the official binding commit that
synchronized with the upstream 4.7-stable API. Godot 4.7.1's dumped extension
API and that binding baseline are structurally identical after excluding the
patch-version header. Both normalized documents hash to
`013259b6f497cb9e83a92d7fd571471c5e884272311ba15ac4e874f212b34e3c`.

This migration changes compatibility and build infrastructure only. Python
remains the semantic oracle. It introduces no gameplay, topology, replay,
state-hash, RNG, scoring, persistence-schema, or native-authority change.

## Reproducible release inputs

| Platform | Official asset | SHA-256 |
| --- | --- | --- |
| Linux x86_64 | `Godot_v4.7.1-stable_linux.x86_64.zip` | `c7ff14fd28472c8d4f193043de30278dcf7e5241a1dcf7566b02e27addaa33ba` |
| macOS universal | `Godot_v4.7.1-stable_macos.universal.zip` | `897cb7f9799796c717ae75f31446aed883dc92b1d6c3b33d893cc7843fff2fa9` |

The canonical URLs and executable paths live in
`config/project/policy_pack.json`. CI reads those values rather than tracking a
mutable `latest` download.

## Repository version inventory

| Category | Locations | Disposition |
| --- | --- | --- |
| Project declarations | `project.godot` | Updated from 4.6/4.6.3 to 4.7/4.7.1 |
| Native compatibility | `.gdextension`, build script | Minimum raised to 4.7; build API fixed at 4.7 |
| Binding source | `native/third_party/godot-cpp` | Submodule advanced to the selected immutable commit |
| Dependency tooling | `pyproject.toml` | SCons 4.10.1 pinned for reproducible native builds |
| CI/tooling | `.github/workflows/ci.yml`, verification scripts | Added exact engine acquisition and blocking Godot/native/parity lane |
| Current operator docs | workflow and Godot/native READMEs | Updated to the new supported baseline |
| Historical plans and audits | archived stage records and the static-analysis audit | Preserved as historical evidence; not rewritten |
| Copied assets/traces | bundle and migration evidence | Unchanged |

No Godot C#, NuGet, Mono, or dotnet dependency is active. The retained Unity C#
spike is unrelated historical scope.

## Official migration-guide audit

The complete Godot 4.7 migration guide was reviewed against every tracked
GDScript, scene, resource, project setting, native descriptor, and extension
API use.

| 4.7 change area | Tet4D use found | Result |
| --- | --- | --- |
| Packed-array element property setters | Packed arrays are returned and tested, but no affected element-property setter pattern exists | No code change |
| `RichTextLabel` image API changes | Rich text and theme roles exist; no `add_image` or `update_image` call exists | No code change |
| `TreeItem.select()` changes | `.select()` calls are on other UI controls, not `TreeItem` | No code change |
| Input device ID changes | No logic assumes device ID zero for keyboard or mouse | No code change |
| Typed inherited-return parsing changes | Exact 4.7.1 registration/import succeeds for all 78 scripts | No code change |
| Jolt/physics and soft-body changes | No affected physics API or resource is used | No code change |
| `Area3D`/look-at/audio-area changes | No affected methods or masking behavior is used | No code change |
| RenderingServer particles or EXR image changes | No affected API is used | No code change |
| Font variation/import changes | No imported font assets or variation resources exist | No asset reimport needed |
| Editor/OpenXR changes | No editor plugin or OpenXR integration exists | No code change |
| Default stretch-aspect change | Project previously relied on the 4.6 default | Added explicit `window/stretch/aspect="keep"` to preserve layout behavior |

The project otherwise keeps its existing renderer, stretch mode, window
dimensions, theme resources, input map, autoload behavior, and shell settings.
No automatic resource conversion or broad re-save was accepted.

## GDExtension and native build review

- The entry symbol remains `tet4d_core_library_init`.
- `reloadable = true` remains valid.
- `compatibility_minimum` is now `4.7`.
- Debug and release paths remain declared for macOS framework, Linux shared
  library, and Windows DLL outputs.
- The build remains C++17 and uses the repository's existing SCons graph.
- Linux static archive creation uses SCons' response-file support. The first
  GitHub acceptance run exposed Ubuntu's process argument limit when GNU `ar`
  received the complete generated binding object list directly; the response
  file preserves the identical archive inputs without changing native or
  gameplay behavior.
- Clean removal of the exact ignored binding/native output directories was
  followed by a full binding regeneration and native rebuild.
- No project-source compiler warning or error was emitted. macOS emitted only
  sandbox-restricted `confstr()` probes from the build environment.

Windows packaging remains declared but is not newly verified here. Linux is
the blocking CI platform; macOS is the local review platform.

## Verification evidence

Pre-change compatibility was established by running the unchanged project with
the exact 4.7.1 engine before advancing the binding. Script registration,
scene/resource import, the complete Godot test runner, GDExtension load, native
tests, and bounded startup all passed.

After the clean rebuild, these canonical lanes pass locally:

```bash
./scripts/build_godot_tet4d_core.sh
./scripts/test_godot_tet4d_core.sh
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-2d
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-nd
PYTHONPATH=src .venv/bin/python tools/migration/compare_cpp_gameplay_trace.py --all-plain-setup
GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
```

`verify_godot_4_7.sh` rejects any engine other than the manifest's exact build,
rejects submodule drift, compares the engine and binding extension APIs,
imports an isolated project copy, registers all scripts, runs the full Godot
suite, loads the native extension, and performs bounded startup. Using a copy
prevents editor-generated `.uid` sidecars from modifying the checkout.

The full Godot suite continues to cover menu/setup/live 2D/3D/4D/replay,
settings and setup persistence, schema migration and malformed-data recovery,
layout/style/resource integrity, native state/hash parity, and failure paths.

## Visual and input review

A real macOS window from the exact 4.7.1 archive was inspected at its compact
startup size and after resizing to 1100 by 760 points. The following surfaces
showed no unexplained change in layout, font metrics/hinting, control sizing,
theme color, camera framing, rendering order, line thickness, or input
response:

- main menu and bounded game-setup forms;
- live 2D board, live 3D volume, and live 4D W-slice matrix;
- active/locked cells, W labels, grid/edge hierarchy, help panel, and native
  authority/status header;
- replay-case browser and Vector Arcade Cockpit navigation;
- Settings controls, scrolling, theme resources, and resized-window layout.

Keyboard focus/navigation and activation worked across the reviewed routes.
Existing Godot tests cover keyboard shortcuts, mouse filtering and camera
input, controller-neutral event behavior, replay input isolation, themes, and
layout bounds. No device-ID-zero assumption exists. The Topology Explorer is a
Python/pygame surface rather than part of this Godot shell; its implementation
was unchanged and remains covered by the full Python explorer suite.

No screenshot/golden comparison harness exists for these shell surfaces, so
the screenshots are transient review evidence rather than new repository
artifacts.

## Performance comparison

| Measurement | Exact 4.7.1 pre-change | Exact 4.7.1 final | Assessment |
| --- | ---: | ---: | --- |
| Isolated editor import | 3.35 s | 3.57 s | No material regression |
| Complete Godot headless suite | 13.26 s | 13.36 s | No material regression |
| Bounded startup | 1.35 s | 1.36 s | No material regression |
| Native standalone tests | 19.04 s | 16.14 s | Normal run variation; no regression |

The first clean final binding/native rebuild took 474.20 seconds. The
pre-change build measurement was an incremental cached build, so it is not
presented as an equivalent comparison. No existing representative frame-time
or memory harness was available, and none was introduced for this migration.

## Warning and limitation classification

- Expected negative-path test diagnostics: invalid shell settings and invalid
  native setup inputs are intentionally exercised and remain assertions.
- Test-harness shutdown noise: ObjectDB/resource/rendering RID leak summaries
  remain after the suite. This migration did not introduce a demonstrated
  runtime regression; the counts are recorded for future harness cleanup.
- macOS sandbox noise: CA certificate discovery, system configuration probes,
  and editor profiler snapshot-directory creation can be denied in isolated
  temporary homes. Each is non-fatal and absent from project behavior.
- No parser warning, scene/resource load failure, GDExtension symbol/load
  failure, native compiler diagnostic, parity mismatch, persistence regression,
  or crash was accepted.
- GUI evidence is local macOS evidence. Linux headless evidence is blocking in
  CI. Windows remains a declared but unverified packaging target.

## CI acceptance

The `godot-4-7` job checks out submodules recursively, installs pinned SCons,
downloads and verifies the manifest's exact Linux engine archive, builds and
tests the extension, runs 2D/ND/setup and geometry/query parity, performs the
canonical Godot verification, and asserts that import/testing did not dirty
the checkout. It does not replace the Python 3.11–3.14 matrix.

Branch head `d9e6da3b0868f77aa26a6fd2e3b13496df40f949` passes the migration-specific
checks and `CODEX_MODE=1 ./scripts/verify.sh`. An isolated no-commit merge of
current `origin/master` `c10ed4e6a190daa85976162c1feb866c743b9462` with
that head also passes a clean native rebuild, native tests, every parity lane,
the exact Godot verifier, and the full repository verifier. The first
merge-context full-verifier attempt correctly rejected a Python environment
installed from the primary worktree; rerunning in a temporary environment
editable-installed from the merged worktree passed.

GitHub results are recorded after the final branch head is published; a queued
or skipped job is not acceptance.

## Explicit acceptance statements

- Supported Godot baseline: `4.7.1-stable`.
- Supported binding baseline:
  `5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731`, API version `4.7`.
- Godot is still the product shell and input/rendering adapter.
- Python remains the semantic authority.
- Native C++ remains provisional and parity-backed.
- No new authority or product-routing decision is introduced.
