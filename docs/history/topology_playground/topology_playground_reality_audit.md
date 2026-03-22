# Topology Playground Reality Audit

Archived/supporting note: consult
`docs/plans/topology_playground_current_authority.md` first for the live
topology-playground architecture. Newer task instructions and the
current-authority manifest take precedence over this audit. Use this file only
as supporting background to avoid reopening already-completed migration work.

Status date: 2026-03-12
Scope: audit [`docs/plans/topology_playground_migration.md`](docs/plans/topology_playground_migration.md) against the live branch state, current code, and current status docs.

## Goal

Stop duplicate work.

Future topology-playground stages should consult the current-authority manifest
first, then use this audit only to scope still-missing cleanup without
reopening accepted architecture.

## Sources Checked

- [`docs/plans/topology_playground_migration.md`](docs/plans/topology_playground_migration.md)
- [`CURRENT_STATE.md`](CURRENT_STATE.md)
- [`docs/BACKLOG.md`](docs/BACKLOG.md)
- [`docs/plans/explorer_playground_unification.md`](docs/plans/explorer_playground_unification.md)
- [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md)
- [`config/menu/structure.json`](config/menu/structure.json)
- [`src/tet4d/engine/runtime/topology_playground_state.py`](src/tet4d/engine/runtime/topology_playground_state.py)
- [`src/tet4d/engine/runtime/topology_playground_sandbox.py`](src/tet4d/engine/runtime/topology_playground_sandbox.py)
- [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py)
- [`src/tet4d/ui/pygame/topology_lab/app.py`](src/tet4d/ui/pygame/topology_lab/app.py)
- [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py)
- [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py)
- [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py)
- [`tests/unit/engine/test_topology_lab_menu.py`](tests/unit/engine/test_topology_lab_menu.py)
- [`tests/unit/engine/test_topology_playground_state.py`](tests/unit/engine/test_topology_playground_state.py)
- [`tests/unit/engine/test_topology_playground_sandbox.py`](tests/unit/engine/test_topology_playground_sandbox.py)
- [`tests/unit/engine/test_topology_playground_launch.py`](tests/unit/engine/test_topology_playground_launch.py)

## Short Conclusion

The original migration plan is no longer the live status authority. Most of the
planned migration has already shipped under later implementation batches.

Do not reopen completed work for:

- canonical playground state creation
- explorer-first seam editing
- board settings living in the playground shell
- sandbox integration
- play launch from current playground draft
- minimal launcher topology routing
- `Analysis View` demotion on the migrated explorer path

Real remaining work is narrower:

1. migrate the remaining retained analysis/edit-panel consumers from UI-local
   shell mirrors onto the engine/runtime-owned
   `TopologyPlaygroundState`
2. further decompose
   `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
3. delete the remaining compatibility-only lab entry / legacy export bridge if
   the product still intends to retire them fully

No new inspection hooks were needed for this audit.

## Classification Legend

- `done`: shipped on the ordinary migrated path
- `partial`: shipped for the migrated path, but retained compatibility debt or
  parallel owners still exist
- `duplicated`: planning/status tracking already exists elsewhere and should not
  be redone from the original plan
- `obsolete`: the original assumption is no longer true
- `missing`: not found in current code or status docs

## Target Surface Audit

| Planned area | Class | Reality audit | Missing-only scope |
| --- | --- | --- | --- |
| Play menus: minimal preset launcher only | `done` | [`config/menu/structure.json`](config/menu/structure.json) now describes `Play` as a minimal launcher and exposes only `Play 2D/3D/4D`, `Play Last Custom Topology`, and `Open Explorer Playground`. [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md) and [`docs/rds/RDS_MENU_STRUCTURE.md`](docs/rds/RDS_MENU_STRUCTURE.md) match that contract. | None. Do not re-migrate launcher topology editing out of the launcher; it is already out. |
| One unified topology playground | `partial` | Ordinary explorer/custom-topology entry now converges on [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) via [`src/tet4d/ui/pygame/topology_lab/app.py`](src/tet4d/ui/pygame/topology_lab/app.py) and `run_explorer_playground(...)`. The compatibility-only `run_topology_lab_menu(...)` alias has now been removed after caller audit, but retained shell-local mirrors are still present in [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py). | Finish the retained compatibility cleanup only; do not rebuild the unified shell from scratch. |
| Graphical explorer: primary editing surface | `done` | The live shell labels the panes as `Explorer Editor (primary)` and `Analysis View (secondary)`. Core seam authoring happens through scene picking, transform editing, and scene-linked actions in [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py). Explorer-side edit behavior is pinned in [`tests/unit/engine/test_topology_lab_menu.py`](tests/unit/engine/test_topology_lab_menu.py). | None. |
| Abstract line+dots / graph research view: secondary analysis only | `done` | On the migrated explorer path, [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py) now exposes board/preset/settings/export/experiment rows plus read-only seam context (`analysis_boundary`, `analysis_glue`, `analysis_transform`). It no longer exposes row-based seam apply/remove editing for the general explorer editor path. | None for the migrated path. Do not reintroduce row-first seam editing. |

## Canonical State Audit

| Planned area | Class | Reality audit | Missing-only scope |
| --- | --- | --- | --- |
| One canonical in-memory playground state | `partial` | [`src/tet4d/engine/runtime/topology_playground_state.py`](src/tet4d/engine/runtime/topology_playground_state.py) now exists and owns dimension, board sizes, topology draft, probe state, sandbox state, preset metadata, launch settings, and dirty tracking. The migrated explorer path synchronizes through [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py). But the UI shell still carries mirrored fields for retained/non-migrated consumers. | Migrate the remaining retained panel consumers and remove shadow ownership once compatibility paths are intentionally retired. |

## Stage Audit

| Stage from original plan | Class | Reality audit | Missing-only scope |
| --- | --- | --- | --- |
| Stage 0: Architecture freeze | `obsolete` | The original document explicitly says later stages are not implemented. That is no longer true. Live status authority now sits in [`CURRENT_STATE.md`](CURRENT_STATE.md), [`docs/BACKLOG.md`](docs/BACKLOG.md), and the completed unification doc [`docs/plans/explorer_playground_unification.md`](docs/plans/explorer_playground_unification.md). | Do not use the Stage 0 doc as completion status. Keep it as historical design intent only. |
| Stage 1: Canonical state | `done` | The canonical owner exists in [`src/tet4d/engine/runtime/topology_playground_state.py`](src/tet4d/engine/runtime/topology_playground_state.py), with direct regression coverage in [`tests/unit/engine/test_topology_playground_state.py`](tests/unit/engine/test_topology_playground_state.py). | None. |
| Stage 2: Explorer consumes canonical state | `partial` | Scene refresh, preview compilation, selection, probe, and other migrated explorer behavior consume canonical state on the live path, as reflected in [`CURRENT_STATE.md`](CURRENT_STATE.md), [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md), and [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py). Retained UI-local mirrors still exist for compatibility debt. | Migrate remaining retained consumers only. Do not redo the already-routed explorer path. |
| Stage 3: Direct explorer-side editing | `done` | Explorer-side boundary picks, seam picks, glue-slot inspection, and linked transform editing are live in [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) and covered in [`tests/unit/engine/test_topology_lab_menu.py`](tests/unit/engine/test_topology_lab_menu.py). | None. |
| Stage 4: Board settings in playground | `done` | The explorer path exposes `dimension`, board-size rows, piece set, speed, and `explorer_preset` in [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py). Those settings feed canonical state and refresh the scene. | None. |
| Stage 5: Piece sandbox integration | `done` | Sandbox ownership moved into [`src/tet4d/engine/runtime/topology_playground_sandbox.py`](src/tet4d/engine/runtime/topology_playground_sandbox.py), while [`src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`](src/tet4d/ui/pygame/topology_lab/piece_sandbox.py) is now an adapter. Covered by [`tests/unit/engine/test_topology_playground_sandbox.py`](tests/unit/engine/test_topology_playground_sandbox.py) and sandbox-focused lab tests. | None. |
| Stage 6: Play launch from playground state | `done` | [`src/tet4d/ui/pygame/topology_lab/play_launch.py`](src/tet4d/ui/pygame/topology_lab/play_launch.py) now launches from [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py), which derives gameplay config directly from `TopologyPlaygroundState`. Covered in [`tests/unit/engine/test_topology_playground_launch.py`](tests/unit/engine/test_topology_playground_launch.py). | None. |
| Stage 7: Demotion of old detached surfaces | `partial` | The ordinary launcher path is already minimal, and the migrated explorer path clearly demotes `Analysis View` to secondary. `run_topology_lab_menu(...)` has been removed after caller audit, while normal-mode legacy editor rows, legacy resolved-profile export, and retained shell-local reset/unavailable fallbacks still remain for non-migrated/manual paths. | Only compatibility deletion/consolidation remains. Do not redo launcher minimalization or `Analysis View` demotion on the migrated path. |

## Duplicate-Work Guardrails

If a later thread proposes any of the following as new work, treat it as
already done unless it is explicitly fixing a regression:

- add a canonical topology playground state
- move board size and explorer presets into the playground shell
- make the explorer scene the primary seam editor
- integrate sandbox movement/rotation into the playground
- launch play from the current in-memory playground draft
- slim the launcher to preset-only topology entry points
- demote the `Analysis View` pane on the explorer path

If a later thread needs new scope, it should start from one of these missing-only
targets instead:

1. remove retained UI-local shadow ownership in
   [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py)
   and adjacent retained consumers
2. split
   [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py)
   into smaller stable owners
3. remove compatibility-only legacy lab/export paths if product support for
   them is intentionally dropped


## 2026-03-12 Missing-Only Pass Note

- Retained mirrors migrated or reduced: active explorer board/play settings, explorer profile loading, explorer draft updates, seam selection, and sandbox profile handoff now route through canonical helpers in [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py) instead of treating shell-local fields as authoritative. Dimension-mismatch rebuilds now fall back to shell snapshots only long enough to rehydrate a new canonical `TopologyPlaygroundState`.
- Extracted from `topology_lab_menu.py`: startup/state-construction responsibilities now live in [`src/tet4d/ui/pygame/launch/topology_lab_state_factory.py`](src/tet4d/ui/pygame/launch/topology_lab_state_factory.py), and the active menu flow calls shared controls-panel handlers directly instead of maintaining the old compatibility rebinding surface in [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py).
- Compatibility paths bypassed or isolated: `_bind_controls_panel_compat(...)` is no longer part of the migrated path, sandbox profile handoff no longer writes the shell mirror first, and the later same-day retirement pass removed `run_topology_lab_menu(...)` after caller audit while the migrated explorer entry continued through `run_explorer_playground(...)`.
- Still remains: shell snapshot fields still exist in [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py) for legacy/non-migrated consumers, and normal-mode legacy rows plus resolved-profile export now remain as isolated helpers in [`src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`](src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py).

## 2026-03-12 Legacy-Consumer Retirement Pass

- Shell snapshot consumers migrated: the live probe step/reset/highlight path in [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py) and [`src/tet4d/ui/pygame/topology_lab/boundary_picker.py`](src/tet4d/ui/pygame/topology_lab/boundary_picker.py) now mutates canonical probe state through [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py) helpers (`replace_probe_state(...)`, `set_highlighted_glue_id(...)`) instead of writing shell snapshot fields directly on the migrated explorer path. The remaining non-explorer reset branch in `controls_panel.py` is still local snapshot cleanup.
- Split out of `controls_panel.py`: normal-mode preset/topology-mode/edge-rule row definitions plus legacy resolved-profile export now live in [`src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`](src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py), leaving [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py) as the canonical explorer-flow owner with thin legacy delegation only.
- `run_topology_lab_menu(...)`: removed from [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) after caller audit found no remaining `src/` callers. Focused coverage now stays on `run_explorer_playground(...)` in [`tests/unit/engine/test_topology_lab_menu.py`](tests/unit/engine/test_topology_lab_menu.py).
- Still remains: retained shell snapshot fields in [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py) still backstop local probe-unavailable snapshots, non-explorer reset/rehydration, and other non-migrated/manual paths; normal-mode legacy rows plus resolved-profile export still exist intentionally through [`src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py`](src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py); broader `topology_lab_menu.py` decomposition is still separate follow-up work.

## 2026-03-12 Menu Audit Note

- Menu audit completed in [`docs/history/topology_playground/topology_explorer_menu_audit.md`](docs/history/topology_playground/topology_explorer_menu_audit.md).
- Main duplicated areas: `Save` / `Export` / `Experiments` / `Back` exist in both Analysis View rows and the workspace action bar; `Explorer Preset` exists in both the Analysis View row and transform-editor preset arrows; `Play This Topology` is exposed as both a tool-like mode and a direct launch action.
- Main partial/misleading areas: `Game Type` still mixes the live canonical explorer shell with the retained legacy compatibility editor, the transform-editor preset pill is button-styled but inert, and read-only analysis rows still look like ordinary editable menu rows.
- Recommended next cleanup direction: isolate or hide legacy-only rows from the primary shell, remove duplicated command affordances, and clarify command-vs-tool labeling before any broader UI cleanup.


## 2026-03-12 Unsafe Topology Audit Note

- Unsafe-topology correctness is now tracked in
  [`docs/history/topology_playground/unsafe_topology_correctness_audit.md`](docs/history/topology_playground/unsafe_topology_correctness_audit.md).
- This does not reopen completed migration stages. The migrated canonical-state
  route and direct play-launch route remain the current status authority.
- The new audit's main finding is cross-surface contract drift, not stage
  regression:
  - preview / probe model point-cell connectivity
  - gameplay models rigid-piece transport and blocks only true
    `cellwise_deformation`
  - sandbox is currently stricter than gameplay and still rejects
    `rigid_transform` seam moves
- Separate unsafe preset usability failure also remains for preview-invalid
  dimension pairings, especially sphere-like cross-axis families when board
  extents do not satisfy bijection requirements.
