# Topology Playground Reality Audit

Status date: 2026-03-11  
Scope: audit [`docs/plans/topology_playground_migration.md`](docs/plans/topology_playground_migration.md) against the live branch state, current code, and current status docs.

## Goal

Stop duplicate work.

Future topology-playground stages should consult this audit first and scope only
to still-missing pieces.

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
| One unified topology playground | `partial` | Ordinary explorer/custom-topology entry now converges on [`src/tet4d/ui/pygame/launch/topology_lab_menu.py`](src/tet4d/ui/pygame/launch/topology_lab_menu.py) via [`src/tet4d/ui/pygame/topology_lab/app.py`](src/tet4d/ui/pygame/topology_lab/app.py) and `run_explorer_playground(...)`. But compatibility-only `run_topology_lab_menu(...)` still exists, and retained shell-local mirrors are still present in [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py). | Finish the compatibility cleanup only; do not rebuild the unified shell from scratch. |
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
| Stage 7: Demotion of old detached surfaces | `partial` | The ordinary launcher path is already minimal, and the migrated explorer path clearly demotes `Analysis View` to secondary. But compatibility-only `run_topology_lab_menu(...)`, normal-mode legacy editor rows, and legacy export compatibility still remain for non-migrated/manual paths. | Only compatibility deletion/consolidation remains. Do not redo launcher minimalization or `Analysis View` demotion on the migrated path. |

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
