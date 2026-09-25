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
- The final CI sanitation gate ignores only untracked files inside the
  generated godot-cpp build tree. It still rejects staged changes, tracked
  worktree changes, and root-project untracked files, and prints any rejected
  paths for diagnosis.
- Editable installation had been rewriting stale, tracked
  `src/tet4d.egg-info` build metadata before the Godot lane began. Generated
  egg-info is no longer versioned and is ignored with the other Python build
  outputs, so the sanitation gate measures source-tree drift rather than
  packaging cache churn.
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
- The migration run also printed ObjectDB/resource/rendering RID leak summaries.
  The later fixture-ownership audit below supersedes their provisional
  classification as undifferentiated shutdown noise.
- macOS sandbox noise: CA certificate discovery, system configuration probes,
  and editor profiler snapshot-directory creation can be denied in isolated
  temporary homes. Each is non-fatal and absent from project behavior.
- No parser warning, scene/resource load failure, GDExtension symbol/load
  failure, native compiler diagnostic, parity mismatch, persistence regression,
  or crash was accepted.
- GUI evidence is local macOS evidence. Linux headless evidence is blocking in
  CI. Windows remains a declared but unverified packaging target.

### Godot 4.7.2 diagnostic ownership follow-up (2026-09-25)

The isolated macOS baseline passed 67 replay scripts and 59 topology transport
cases with no `SCRIPT ERROR`. A no-test headless SceneTree run had no exit
diagnostics. Each of the 67 scripts was then run separately; five reproduced
exit leaks. The same five run together had no leak diagnostics after their test
fixtures explicitly freed nodes they had created. The isolated full 67-script
suite then exited without any leak, resource-in-use, or allocator diagnostic;
its 59-case topology parity and bounded boot also passed.

| Exact diagnostic or signature | Phase and trigger | Classification and evidence |
| --- | --- | --- |
| `Shell settings could not be saved: installation failed with error 20 before an existing destination was modified.` | Headless replay; `test_shell_settings_store.gd` absent-destination failure | `EXPECTED_NEGATIVE_PATH`; injected rename failure and recovery assertions. Absent in the no-test probe. |
| `Shell settings could not be saved: temporary write failed with error 13 before the destination was modified.` | Headless replay; same test, incomplete write | `EXPECTED_NEGATIVE_PATH`; injected write failure and file-preservation assertion. |
| `Shell settings could not be saved: the previous destination could not be backed up (error 20) and was not modified.` | Headless replay; same test, backup failure | `EXPECTED_NEGATIVE_PATH`; injected rename failure and unchanged-destination assertion. |
| `Shell settings could not be saved: installation failed with error 20; the previous content was restored by rename.` | Headless replay; same test, rename recovery | `EXPECTED_NEGATIVE_PATH`; restoration and diagnostic assertions remain. |
| `Shell settings could not be saved: installation failed with error 20; the previous content was restored by copy.` | Headless replay; same test, copy recovery | `EXPECTED_NEGATIVE_PATH`; fallback and diagnostic assertions remain. |
| `Unsupported 4D basis plane: xy` | Headless replay; `test_slice_basis_4d.gd` | `EXPECTED_NEGATIVE_PATH`; the test passes an unsupported plane and checks rejection. |
| `Tet4D fixed-seed live setup requires seed.` | Headless replay; `test_configurable_live_sessions.gd` | `EXPECTED_NEGATIVE_PATH`; missing fixed seed is deliberately rejected. |
| `Tet4D live setup seed must be an integer.` | Headless replay; same test | `EXPECTED_NEGATIVE_PATH`; non-integer seed is deliberately rejected. |
| `Tet4D live setup contains unsupported field: unexpected` | Headless replay; same test | `EXPECTED_NEGATIVE_PATH`; unknown field is deliberately rejected. |
| `Could not create ObjectDB Snapshots directory: user://private/var/...` at `modules/objectdb_profiler/editor/objectdb_profiler_panel.cpp:162` | `--editor` import in the normal macOS isolated `TMPDIR`; never emitted by headless replay or boot | `KNOWN_ENGINE_OR_HARNESS_ADVISORY`; the editor prints it before GDExtension verification, plugin initialization, and global class registration, so no Tet4D code has run. The exact trigger is unresolved: standalone editor runs of an empty project, of Tet4D's `project.godot` alone, and of a full project copy under the same isolated roots did not reproduce it. This is editor snapshot storage, separate from exit-time ObjectDB cleanup. Import still exits successfully. |
| `CanvasItem` RIDs leaked (16 baseline) at `renderer_canvas_cull.cpp:2735` | Headless replay exit | `TET4D_OWNED_RESOURCE_LIFETIME_DEFECT`; standalone accessibility, navigation, and shell-style tests leaked 3, 2, and 11 detached CanvasItems respectively. Freeing their owned controls removed the warning in the combined focused run. |
| ObjectDB instances leaked (238 baseline) at `core/object/object.cpp:2536`; verbose `Cannot get path of node as it is not in a scene tree` at `scene/main/node.cpp:2431` | Headless replay exit and verbose leak listing | `TET4D_OWNED_RESOURCE_LIFETIME_DEFECT`; verbose output listed detached controls and Node3D objects. Five isolated tests leaked objects; explicit fixture frees removed their warnings. The path errors were generated while verbose cleanup tried to describe detached leaked nodes. |
| Resources still in use (22 baseline) at `core/io/resource.cpp:822` (`:817` with `--verbose`) | Headless replay exit | `TET4D_OWNED_RESOURCE_LIFETIME_DEFECT`; verbose output named retained GDScript resources, including `test_navigation_contract.gd`, along with themes/styles. The retained test nodes held these references; the combined focused run no longer reports them after node cleanup. |
| `DummyTexture` (25), `ShapedTextDataAdvanced` (14), and `FontAdvanced` (2) RID allocations leaked | Headless replay exit | `TET4D_OWNED_RESOURCE_LIFETIME_DEFECT`; detached styled controls retained texture/text/font resources. The focused cleanup removed all three RID families. |
| `Pages in use exist at exit in PagedAllocator: N12VariantPools12BucketMediumE` at `paged_allocator.h:170` | Headless replay exit | `TET4D_OWNED_RESOURCE_LIFETIME_DEFECT` downstream of retained test objects; reproduced by `test_display_presentation_runtime.gd` alone and removed when its detached camera rigs were freed. No allocator-specific workaround was added. |

The owning fixtures were `test_presentation_parameter_contract.gd` (one
`TraceSceneRenderer`), `test_display_presentation_runtime.gd` (five camera
rigs), `test_accessibility_runtime.gd` (three buttons),
`test_navigation_contract.gd` (HUD and unparented quit button), and
`test_shell_style_application.gd` (unparented button and control group).
`free()` is used only for these detached test nodes after their assertions;
tree-attached scene fixtures retain their existing `queue_free()` plus frame
advancement. No production ownership or gameplay semantics changed. The replay
runner now prints per-script progress and labels the three tests expected to
emit rejection errors. `SCRIPT ERROR` detection and the step deadline remain.
The verification script now rejects only the established exit-time leak
families in each Godot phase; a replay of the original baseline log exercises
the rejecting branch, while the cleaned log is accepted. It does not allowlist
generic `ERROR:` or `WARNING:` lines, and the separate editor snapshot-storage
error remains visible during import.

## CI acceptance

The `godot-4-7` job checks out submodules recursively, installs pinned SCons,
downloads and verifies the manifest's exact Linux engine archive, builds and
tests the extension, runs 2D/ND/setup and geometry/query parity, performs the
canonical Godot verification, and asserts that import/testing did not dirty
the checkout. It does not replace the Python 3.11–3.14 matrix.

Final implementation head `6bd592e0329547ee03923f01fdaeb7d03aba89e3`
passes the migration-specific
checks and `CODEX_MODE=1 ./scripts/verify.sh`. An isolated no-commit merge of
current `origin/master` `c10ed4e6a190daa85976162c1feb866c743b9462` with
the migration implementation also passes a clean native rebuild, native tests,
every parity lane,
the exact Godot verifier, and the full repository verifier. The first
merge-context full-verifier attempt correctly rejected a Python environment
installed from the primary worktree; rerunning in a temporary environment
editable-installed from the merged worktree passed.

GitHub Actions push run
[`30179384125`](https://github.com/mousomer/tet4d/actions/runs/30179384125)
and pull-request run
[`30179385253`](https://github.com/mousomer/tet4d/actions/runs/30179385253)
both pass on final implementation head
`6bd592e0329547ee03923f01fdaeb7d03aba89e3`. Each run passes the Python
3.11–3.14 matrix and the blocking Linux Godot 4.7.1 lane: exact download and
checksum, engine/binding pins, clean native build and native tests, all parity
lanes, exact Godot verification, and the clean-checkout gate.

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
