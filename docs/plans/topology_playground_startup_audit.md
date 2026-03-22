# Topology Playground Startup Audit

Status date: 2026-03-11
Source of truth for migration status: [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
Archived migration audit: [`docs/history/topology_playground/topology_playground_reality_audit.md`](../history/topology_playground/topology_playground_reality_audit.md)
Scope: audit and instrumentation only; no optimization or path deletion in this thread.

## Goal

Explain why Topology Playground now feels slow to open, with measured evidence that separates first-frame-critical work from deferrable or compatibility-only work.

## Method

Instrumentation used:

- [`scripts/profile_topology_playground_startup.py`](scripts/profile_topology_playground_startup.py)

Trace shape:

1. `build_explorer_playground_launch(...)` on the ordinary explorer entry path
2. `_initial_topology_lab_state(...)`
3. first `_draw_menu(...)` / first interactive frame construction
4. one manual `compile_runtime_explorer_experiments(...)` pass for playability-analysis cost context

Measured launch profiles:

- 2D: `torus_2d`
- 3D: `full_wrap_3d`
- 4D: `full_wrap_4d`

Current stored explorer profiles still loaded during startup on this machine:

- 2D: `sphere_2d`
- 3D: `sphere_3d`
- 4D: `swap_xw_4d`

That stored-profile load matters because the startup path currently compiles the stored explorer profile before replacing it with the explicit launch profile.

## Entry Trace

Measured explorer-path startup currently does this before the first interactive frame:

1. [`src/tet4d/ui/pygame/topology_lab/app.py`](src/tet4d/ui/pygame/topology_lab/app.py) validates the incoming launch profile with `_profile_validation_error(...)`, which calls `compile_explorer_topology_preview(...)`.
2. [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) builds `_TopologyLabState` and loads the legacy topology profile plus the stored explorer profile.
3. [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py) refreshes scene state from that stored explorer profile, compiling an explorer preview.
4. If an explicit launch profile was provided, `_initial_topology_lab_state(...)` overwrites the stored profile with the launch profile, syncs canonical state again, and refreshes scene state again.
5. `_ensure_probe_state(...)` computes `recommended_explorer_probe_coord(...)`, which rebuilds the movement graph again.
6. First draw builds the explorer workspace, scene, overlays, and sandbox payload.

So the ordinary explorer path eagerly rebuilds the same launch-profile movement graph three times before the first frame, plus one extra compile attempt for the stored explorer profile.

## Measured Summary

| Dimension | Board dims | Stored profile compiled first | Launch profile | Launch build | State init | First draw | First interactive frame ready |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2D | `10x20` | `sphere_2d` | `torus_2d` | `27.0 ms` | `48.4 ms` | `20.1 ms` | `95.6 ms` |
| 3D | `6x18x6` | `sphere_3d` | `full_wrap_3d` | `146.5 ms` | `278.4 ms` | `8.3 ms` | `433.2 ms` |
| 4D | `10x20x6x4` | `swap_xw_4d` | `full_wrap_4d` | `1818.4 ms` | `3560.3 ms` | `8.8 ms` | `5387.5 ms` |

Takeaway: the slowdown is overwhelmingly pre-draw computation, not scene rendering.

## Phase Audit

| Phase | Eager or lazy | Called once or repeatedly | Measured / estimated cost | Required for first interactive frame | Defer/cache/remove note |
| --- | --- | --- | --- | --- | --- |
| Playground entry path | Eager | Once | `27.0 / 146.5 / 1818.4 ms` for `2D / 3D / 4D` | Partly. Startup must validate the launch profile, but it does not need a full preview compile just to answer valid/invalid. | Safe candidate: replace `_profile_validation_error(...)` full preview compile with cheaper validation or reuse the first preview graph later. |
| `TopologyPlaygroundState` creation / hydration | Eager | Repeated syncs during one startup | `48.4 / 278.4 / 3560.3 ms` total init; canonical sync itself is only about `0.9 / 0.9 / 1.1 ms` across startup calls | Partly. State creation is required; repeated sync + refresh passes are not. | Safe candidate: reduce startup sync count when explicit launch profile already exists. |
| Preset discovery / preset loading | Eager | Repeated lookup calls | Explorer preset lookups are tiny: `~1.0 / 1.1 / 1.3 ms` total in `scene_state`, `~0.5 / 0.5 / 0.6 ms` in `controls_panel`; designer preset lookup is effectively noise | No material impact. These are not the cause of the slow open. | Leave alone unless broader startup cleanup already touches this path. |
| Topology validation | Eager | Heavily repeated | `604 / 1948 / 14404` validation calls at startup; `5.0 / 21.7 / 227.8 ms` total | Only one validation pass per unique `(profile, dims)` is needed. The rest is redundant. | Safe candidate: stop revalidating inside every `neighbors_for_cell(...)` call once `build_movement_graph(...)` has already validated the input. |
| Movement graph compilation | Eager | Repeated | `4` startup graph builds, but only `2` unique signatures; total `70.3 / 418.3 / 5347.6 ms` | One graph build for the launch profile is plausibly first-frame-critical today. The other two launch-profile rebuilds are not. | Biggest candidate: cache/reuse the launch-profile graph across validation, preview, and probe recommendation. |
| Playability analysis | Lazy/manual | Not called during startup | `102.9 / 535.1 / 5468.9 ms` for one manual experiment-pack run | No. Startup does not populate `TopologyPlaygroundState.playability_analysis`; this remains deferred/manual. | Keep lazy. If surfaced earlier later, derive from cached preview/graph rather than recomputing. |
| Graphical explorer scene construction | Eager | Once | Workspace draw `4.5 / 3.7 / 4.3 ms`; scene draw `1.2 / 1.0 / 1.1 ms` | Yes, but the cost is already small. | Not a priority hotspot. |
| Seam arrow / overlay construction | Eager | Repeated only because preview compile repeats | Basis-arrow payload construction is tiny: `0.033 / 0.040 / 0.068 ms` | Only once, indirectly, as part of the preview shown on frame 1. | Piggyback on preview caching; no separate optimization needed. |
| Piece sandbox initialization | Eager on explorer entry path | Repeated `3` times before first frame | `ensure_piece_sandbox_state(...)` is only `0.182 / 0.206 / 0.228 ms`; shell-level `ensure_piece_sandbox(...)` is similarly tiny | Required on the current explorer route because the initial tool is `piece_sandbox`. | Not a startup hotspot. |
| First interactive frame readiness | Eager | Once | `95.6 / 433.2 / 5387.5 ms` | Yes | Dominated by repeated movement-graph work before the draw ever happens. |

## Evidence for Repeated Work

### 1. Same launch topology is rebuilt three times before frame 1

For the launch profile and board dims, startup currently pays for:

- one graph build in `build_explorer_playground_launch(...)` validation
- one graph build in `_refresh_explorer_scene_state(...)`
- one graph build in `recommended_explorer_probe_coord(...)`

In the 4D trace, those three `full_wrap_4d` graph builds cost about:

- `1806.9 ms`
- `1769.1 ms`
- `1771.6 ms`

That is the main reason 4D first-frame readiness exceeds five seconds.

### 2. A stored-profile detour runs even when the launch profile is already known

The explorer entry path receives an explicit launch profile, but `_initial_topology_lab_state(...)` still does this first:

- `load_runtime_explorer_topology_profile(...)`
- refresh scene state from the stored profile
- only then apply the explicit `initial_explorer_profile`
- refresh scene state again

On this machine the stored profiles were:

- 2D: `sphere_2d`
- 3D: `sphere_3d`
- 4D: `swap_xw_4d`

Those stored profiles are compatibility/state-resume paths, not the requested launch topology. They still run during startup.

### 3. Validation is duplicated inside graph construction

[`src/tet4d/engine/topology_explorer/movement_graph.py`](src/tet4d/engine/topology_explorer/movement_graph.py) validates the profile once in `build_movement_graph(...)`, then `neighbors_for_cell(...)` validates again for every cell.

For startup that means:

- 2D: `604` validations for one real launch
- 3D: `1948` validations
- 4D: `14404` validations

This is not the root cause by itself, but it is a measurable tax sitting inside the hottest path.

## Duplicated State Conversions

These are present, but they are not the dominant cost:

- [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py) converts UI-shell fields into runtime-owned `TopologyPlaygroundState` via `_runtime_*_from_ui(...)`, then mirrors pieces back with `sync_shell_state_from_canonical(...)`.
- Startup still runs both `controls_panel.sync_canonical_playground_state(...)` and the wrapper path in [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) while the launch profile is being applied.
- Those sync passes are cheap in milliseconds, but they help explain why preset lookups and state copying happen more often than strictly necessary.

## Heavy Init in Tabs / Tools That Are Not Initially Visible

No hidden-tab heavyweight comparable to the graph builds showed up.

What does happen eagerly:

- Analysis-side preset/value rows are still populated during first draw even when the scene pane is the active pane.
- The current explorer entry path defaults the active tool to `piece_sandbox`, so sandbox setup is not hidden work; it is part of the initial visible tool.

Measured result: this eager UI/tool work is small enough that it is not the startup problem.

## Compatibility Paths Still Running During Startup

These paths still execute on the measured explorer startup route:

- `load_topology_profile(...)` for the legacy topology profile
- `load_runtime_explorer_topology_profile(...)` for the stored explorer profile, even with an explicit launch profile already supplied
- `_bind_controls_panel_compat(...)` three times during one startup
- the `controls_panel`-driven refresh path that still owns part of startup orchestration

These match the reality audit: the migrated explorer path is live, but compatibility ownership and retained bridges still participate in startup.

## Ranked Hotspot List

1. Repeated `build_movement_graph(...)` on the same launch profile before frame 1.
2. Stored-profile load/refresh before the explicit launch profile is applied.
3. `recommended_explorer_probe_coord(...)` rebuilding the graph instead of reusing the preview result.
4. Per-cell `validate_explorer_topology_profile(...)` inside `neighbors_for_cell(...)`.
5. Manual playability experiment pack generation is extremely heavy in 4D, but it is correctly deferred today.

## Safe Optimization Candidates for the Next Thread

1. Reuse one launch-profile preview/graph across `build_explorer_playground_launch(...)`, `_refresh_explorer_scene_state(...)`, and probe initialization.
2. Skip the stored explorer-profile refresh when explorer startup already supplies an explicit `initial_explorer_profile`.
3. Replace `_profile_validation_error(...)` full preview compilation with a cheaper validation-only path, or consume a cached preview if one is already produced.
4. Remove redundant per-cell validation from `neighbors_for_cell(...)` once the caller has already validated `(profile, dims)`.
5. Derive the initial probe coordinate from the already-built preview graph instead of calling `recommended_explorer_probe_coord(...)` on a fresh graph build.
6. Keep playability analysis lazy; if it ever becomes pre-open or first-frame UI, feed it from cached graph/preview state rather than recomputing per experiment.
7. Treat preset lookup churn and sandbox `ensure_*` repetition as cleanup-only work after the graph rebuild problem is solved.

## Acceptance Criteria Check

- Startup phases are enumerated: yes.
- Actual instrumentation or a precise trace-based audit exists: yes, via [`scripts/profile_topology_playground_startup.py`](scripts/profile_topology_playground_startup.py).
- Highest-cost startup hotspots identified: yes.
- First-frame-critical vs deferrable work distinguished: yes.
- Duplicated and compatibility-only startup paths identified: yes.
