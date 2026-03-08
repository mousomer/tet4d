# Cleanup Master Plan

Status date: 2026-03-07

This ledger tracks the remaining cleanup from the current live codebase. Code is
the source of truth. Docs/manifests are updated after code changes land.

## Structural stage rule

Unless a stage explicitly authorizes a semantic change, cleanup stages in this
ledger must not change gameplay, replay, tutorial, scoring, or packaging
behavior. Structural work means:

1. identify a canonical owner
2. migrate callers
3. add or preserve equivalence coverage
4. delete duplicates
5. sync docs/manifests after code is correct

## Stage Status Summary

| Stage | Domain | Status | Notes |
| --- | --- | --- | --- |
| 0 | Cleanup ledger | Complete | This file is the canonical cleanup ledger. |
| 1 | Narrow `engine.api` | Complete | `engine.api` now keeps stable engine contracts only; raw piece-transform helpers are no longer re-exported. |
| 2 | Canonical piece transforms | Complete | Canonical owner is `src/tet4d/engine/core/piece_transform.py`. |
| 3 | 2D/ND gameplay orchestration dedup | Partial | Shared lock-analysis / score-bookkeeping plus lock-and-respawn / hard-drop lifecycle are now centralized; bag refill and spawn-position logic remain mode-specific. |
| 4 | Split `cli/front2d.py` | Complete | `cli/front2d.py` is a thin launcher shim. |
| 5 | Runtime/settings ownership cleanup | Partial | Runtime storage ownership is mostly cleaned up; `menu_settings_state.py` remains a stable facade and `menu_structure_schema.py` is now a thinner facade over `runtime/menu_structure/`. |
| 6 | Remove keybinding persistence leakage from UI | Complete | Runtime-owned keybinding storage now owns JSON/path/profile file behavior. |
| 7 | Remove remaining `pygame` contamination from engine | Complete | Live code has `pygame_imports_non_test = 0`. |
| 8 | Unify launcher/bootstrap behavior | Mostly complete | `front.py` is already a thin compatibility wrapper; monitor for drift only. |
| 9 | Unify install/build authority | Complete | Editable install from `pyproject.toml` is now the single documented contract for dev/CI/local verification. |
| 10 | Release/packaging cleanup | Mostly complete | Installer workflows exist and are green; keep as a watch item. |
| 11 | Stop minifying operational code | Watch | No broad formatting issue found in current Python sources; enforce readability drift only. |
| 12 | Docs/manifests sync last | Complete for this batch | Code changes are now reflected in backlog/state/RDS/generated maintenance docs. |
| 13 | Explorer topology engine | Active | Phase 1 kernel and Phase 2 runtime/store/preview integration are complete; Phases 3-4 now add direct 2D/3D/4D explorer gluing editors while Normal Game remains on the legacy topology path. |

## Domain Ledger

### Engine public API

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/api.py` |
| Current duplicate owners | Raw transform helpers re-exported from `src/tet4d/engine/core/piece_transform.py` through `engine.api` |
| Migration status | Complete |
| Equivalence tests | `tests/unit/engine/test_engine_api_determinism.py`, `tests/unit/engine/test_replay_module.py` |
| Deletion checkpoint | Remove low-level transform re-exports once all callers use `engine.core.piece_transform` directly |

### Piece transforms

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/core/piece_transform.py` |
| Current duplicate owners | None in live code |
| Migration status | Complete |
| Equivalence tests | `tests/unit/engine/test_piece_transform.py`, `docs/plans/piece_transform_inventory.md` |
| Deletion checkpoint | Closed |

### Gameplay orchestration

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/core/rules/lifecycle.py` for lock/respawn/drop flow plus `src/tet4d/engine/gameplay/lock_flow.py` for lock-analysis / score bookkeeping |
| Current duplicate owners | `src/tet4d/engine/gameplay/game2d.py`, `src/tet4d/engine/gameplay/game_nd.py` |
| Migration status | Active |
| Equivalence tests | `tests/unit/engine/test_game2d.py`, `tests/unit/engine/test_game_nd.py`, `tests/unit/engine/test_score_analyzer.py` |
| Deletion checkpoint | Remove duplicated lock-analysis plus lock-and-respawn / hard-drop flow from 2D/ND mode files; leave bag refill and spawn-position logic mode-specific unless a net-deletion shared owner emerges |

### 2D launcher

| Field | Value |
| --- | --- |
| Canonical owner | `cli/front2d.py` as thin launcher over `src/tet4d/ui/pygame/front2d_game.py` |
| Current duplicate owners | None material |
| Migration status | Complete |
| Equivalence tests | 2D launcher/runtime regression slices in `tests/unit/engine/` |
| Deletion checkpoint | Closed |

### Runtime settings

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/runtime/menu_settings_state.py` facade over `runtime/menu_settings/` |
| Current duplicate owners | Minor glue remains in the facade |
| Migration status | Partial |
| Equivalence tests | `tests/unit/engine/test_keybindings.py`, settings persistence suites |
| Deletion checkpoint | Further split only if hotspot pressure grows again |

### Keybinding persistence

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/runtime/keybinding_store.py` |
| Current duplicate owners | None for file/path/json ownership in live code |
| Migration status | Complete |
| Equivalence tests | `tests/unit/engine/test_keybindings.py`, pause/menu keybinding flows |
| Deletion checkpoint | UI keybinding module no longer reads/writes JSON or resolves profile paths directly |

### Engine/UI boundary

| Field | Value |
| --- | --- |
| Canonical owner | Import boundary scripts + current package split |
| Current duplicate owners | None in live code |
| Migration status | Complete |
| Equivalence tests | `scripts/arch_metrics.py`, `scripts/check_architecture_boundaries.sh`, `scripts/check_engine_core_purity.sh` |
| Deletion checkpoint | Closed; keep zero-budget enforcement |

### Launcher/bootstrap

| Field | Value |
| --- | --- |
| Canonical owner | `front.py` compatibility wrapper plus `cli/front*.py` |
| Current duplicate owners | No critical duplication left |
| Migration status | Mostly complete |
| Equivalence tests | launcher route tests and release smoke paths |
| Deletion checkpoint | Keep as watch item unless bootstrap drift returns |

### Install/build authority

| Field | Value |
| --- | --- |
| Canonical owner | `pyproject.toml` editable install contract |
| Current duplicate owners | None in active docs/scripts/workflows |
| Migration status | Complete |
| Equivalence tests | `scripts/bootstrap_env.sh`, CI workflows, verify import checks |
| Deletion checkpoint | Remove `requirements.txt` authority and update docs/scripts to the editable-install path only |

### Packaging/release

| Field | Value |
| --- | --- |
| Canonical owner | `pyproject.toml` version + packaging scripts/workflows |
| Current duplicate owners | None material |
| Migration status | Mostly complete |
| Equivalence tests | packaging workflows and release installers |
| Deletion checkpoint | Watch only unless install-contract drift returns |

### Docs/manifests

| Field | Value |
| --- | --- |
| Canonical owner | Code first, then `CURRENT_STATE.md`, `docs/BACKLOG.md`, generated maintenance docs, relevant RDS |
| Current duplicate owners | Manual narrative and generated maintenance sections |
| Migration status | Complete for this batch |
| Equivalence tests | `tools/governance/generate_maintenance_docs.py --check`, contract validation |
| Deletion checkpoint | Docs/manifests updated after code cleanup is complete |

### Explorer topology engine

| Field | Value |
| --- | --- |
| Canonical owner | `src/tet4d/engine/topology_explorer/` for pure gluing semantics plus `src/tet4d/engine/runtime/topology_explorer_store.py`, `src/tet4d/engine/runtime/topology_explorer_bridge.py`, and `src/tet4d/engine/runtime/topology_explorer_preview.py` for runtime-owned storage/preview integration |
| Current duplicate owners | Legacy explorer edge-rule profiles in `src/tet4d/engine/gameplay/topology_designer.py` still back Normal Game only; Explorer 2D/3D/4D lab editing now targets the general gluing model directly |
| Migration status | Active |
| Equivalence tests | `tests/unit/engine/test_topology_explorer.py`, `tests/unit/engine/test_topology_explorer_store.py`, `tests/unit/engine/test_topology_explorer_preview.py`, `tests/unit/engine/test_topology_lab_menu.py` |
| Deletion checkpoint | Remove the legacy bridge after live explorer gameplay/runtime also consume the general gluing model directly |

