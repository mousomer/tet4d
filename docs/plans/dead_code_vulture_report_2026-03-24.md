# Dead Code Report — Vulture 2026-03-24

Role: audit report
Status: reference
Source of truth: vulture 2.15 run against `src/` on 2026-03-24
Last updated: 2026-03-24

## Summary

Vulture identified **~475 LOC** of potentially dead code across **~115 items** in 40+ files.
All findings are 60% confidence except where marked 100%.

This report does not authorize deletion. Items marked **likely false positive** should be
verified before any removal. Items in `engine/runtime/api.py` and sibling `api.py` files
are almost certainly false positives (frontend/JS bridge surface — not analyzable by
static Python analysis).

---

## 100% confidence (safe to remove first)

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/render/panel_utils.py` | 154 | variable `min_controls_h` | 1 | |
| `ui/pygame/topology_lab/workspace_shell.py` | 615 | variable `analysis_pane_title` | 1 | |
| `ui/pygame/topology_lab/workspace_shell.py` | 616 | variable `scene_pane_title` | 1 | |
| `ui/pygame/topology_lab/workspace_shell.py` | 618 | variable `muted_color` | 1 | |

**Subtotal: 4 LOC**

---

## 60% confidence — grouped by area

### AI / playbot

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ai/playbot/__init__.py` | 20 | function `__getattr__` (20 lines) | 20 | Likely false positive — lazy-import pattern |
| `ai/playbot/controller.py` | 179 | property `assist_preview_cells` | 3 | |
| `ai/playbot/controller.py` | 608 | method `play_one_piece_2d` | 11 | |
| `ai/playbot/controller.py` | 620 | method `play_one_piece_nd` | 11 | |

**Subtotal: 45 LOC**

### Engine — core

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/core/model/board.py` | 37 | method `place` | 5 | |
| `engine/core/model/game2d_types.py` | 15 | variable `ROTATE_CW` | 1 | |
| `engine/core/model/game2d_types.py` | 16 | variable `ROTATE_CCW` | 1 | |
| `engine/core/model/game2d_views.py` | 30 | variable `has_current_piece` | 1 | |
| `engine/core/model/game_nd_views.py` | 31 | variable `has_current_piece` | 1 | |
| `engine/core/piece_transform.py` | 367 | function `_calculate_rotation_pivot` | 24 | |
| `engine/core/rng/engine_rng.py` | 18 | method `fork` | 4 | |

**Subtotal: 37 LOC**

### Engine — gameplay

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/gameplay/api.py` | 35 | `topology_mode_from_index_runtime` | 2 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 39 | `topology_mode_label_runtime` | 2 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 43 | `topology_mode_options_runtime` | 2 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 47 | `topology_designer_profiles_runtime` | 2 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 51 | `topology_designer_profile_label_runtime` | 2 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 55 | `topology_designer_resolve_runtime` | 17 | Likely false positive — frontend bridge |
| `engine/gameplay/api.py` | 74 | `topology_designer_export_runtime` | 16 | Likely false positive — frontend bridge |
| `engine/gameplay/game_nd.py` | 395 | method `_gravity_step` | 4 | |
| `engine/gameplay/pieces_nd.py` | 600 | function `get_standard_pieces_nd` | 17 | |
| `engine/gameplay/topology_designer.py` | 340 | function `designer_profile_index_by_id` | 11 | |

**Subtotal: 75 LOC** (47 LOC if frontend bridge items excluded)

### Engine — help system

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/help_text.py` | 902 | function `validate_help_text_contract` | 8 | |
| `engine/help_text.py` | 912 | function `clear_help_text_cache` | 4 | |
| `engine/runtime/help_topics.py` | 264 | function `help_topic_for_action` | 4 | |
| `engine/runtime/help_topics.py` | 301 | function `validate_help_topic_contract` | 7 | |
| `engine/runtime/help_topics.py` | 310 | function `clear_help_topic_caches` | 3 | |

**Subtotal: 26 LOC**

### Engine — runtime API (likely false positives)

All items in `engine/runtime/api.py` are thin bridge wrappers (~2 LOC each) that
expose Python functions to a frontend caller. Vulture cannot see cross-language call
sites. Treat this whole block as **likely false positives** unless the frontend bridge
is confirmed decommissioned.

| File | Lines | Items | LOC |
|------|-------|-------|-----|
| `engine/runtime/api.py` | 47–148 | 26 bridge functions | ~52 |
| `engine/tutorial/api.py` | 36, 86 | `tutorial_progress_snapshot_runtime`, `tutorial_runtime_event_log_tail_runtime` | 8 |

**Subtotal: ~60 LOC — likely false positives**

### Engine — runtime (other)

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/runtime/menu_config.py` | 109 | function `menu_entrypoints` | 2 | |
| `engine/runtime/settings_schema.py` | 441 | function `atomic_write_text` | 5 | |
| `engine/runtime/topology_playground_sandbox.py` | 48 | variable `set_id` | 1 | |
| `engine/runtime/topology_playground_state.py` | 574 | variable `topology_preset` | 3 | |

**Subtotal: 11 LOC**

### Engine — topology explorer

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/topology_explorer/transport_resolver.py` | 460 | method `seam_for_boundary` | 5 | |

**Subtotal: 5 LOC**

### Engine — tutorial

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `engine/tutorial/events.py` | 9 | variable `EVENT_HINT_SHOWN` | 1 | |
| `engine/tutorial/manager.py` | 168 | method `clear_predicates` | 2 | |
| `engine/tutorial/runtime.py` | 119 | function `_is_translation_step` | 4 | |
| `engine/tutorial/runtime.py` | 125 | function `_is_rotation_step` | 4 | |

**Subtotal: 11 LOC**

### UI — pygame misc

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/frontend_nd_setup.py` | 57 | variable `RANDOM_MODE_FIXED_INDEX` | 1 | |
| `ui/pygame/frontend_nd_setup.py` | 58 | variable `RANDOM_MODE_TRUE_RANDOM_INDEX` | 1 | |
| `ui/pygame/projection3d.py` | 77 | function `clear_projection_lattice_cache` | 2 | |
| `ui/pygame/projection3d.py` | 81 | function `projection_lattice_cache_keys` | 2 | |
| `ui/pygame/projection3d.py` | 85 | function `projection_lattice_cache_size` | 2 | |

**Subtotal: 8 LOC**

### UI — pygame render

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/render/control_icons.py` | 65 | function `clear_action_icon_cache` | 2 | |
| `ui/pygame/render/control_icons.py` | 69 | function `action_icon_cache_size` | 2 | |
| `ui/pygame/render/front3d_cell_render.py` | 64 | function `overlay_alpha_label` | 3 | |

**Subtotal: 7 LOC**

### UI — settings hub (snapshot-for-cancel pattern)

These `original_*` attributes store pre-edit values for cancel/revert. They may be
**intentionally unused at read time** (stored only for cancel paths). Verify the
cancel flow is actually wired before removing.

| File | Lines | Items | LOC |
|------|-------|-------|-----|
| `ui/pygame/launch/settings_hub_actions.py` | 195–213 | 11 `original_*` attributes | ~17 |
| `ui/pygame/launch/settings_hub_model.py` | 107–120 | 12 `original_*` variables | ~14 |

**Subtotal: ~31 LOC — verify cancel flow before touching**

### UI — runtime UI

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/runtime_ui/loop_runner_nd.py` | 40 | function `_load_animation_settings_for_dimension` | 3 | |
| `ui/pygame/runtime_ui/pause_menu.py` | 487 | function `_pause_menu_keydown` | 13 | |

**Subtotal: 16 LOC**

### UI — topology lab launcher

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/launch/topology_lab_menu.py` | 257 | function `_explorer_sidebar_lines` | 26 | |

**Subtotal: 26 LOC**

### UI — topology lab core

| File | Line | Item | LOC | Notes |
|------|------|------|-----|-------|
| `ui/pygame/topology_lab/camera_controls.py` | 24 | variable `mouse_hint` | 1 | |
| `ui/pygame/topology_lab/camera_controls.py` | 25 | variable `key_hint` | 1 | |
| `ui/pygame/topology_lab/controls_panel.py` | 662 | function `_explorer_slot_label` | 7 | |
| `ui/pygame/topology_lab/controls_panel.py` | 972 | function `_reset_to_mode_dimension` | 5 | |
| `ui/pygame/topology_lab/controls_panel.py` | 1052 | function `_cycle_preset` | 9 | |
| `ui/pygame/topology_lab/controls_panel.py` | 1094 | function `_cycle_topology_mode` | 9 | |
| `ui/pygame/topology_lab/piece_sandbox.py` | 75 | function `_rotate_blocks_for_action` | 7 | |
| `ui/pygame/topology_lab/projection_scene.py` | 173 | function `_coord_matches_slice` | ~5 | |
| `ui/pygame/topology_lab/projection_scene.py` | 541 | function `_draw_projection_heading` | 30 | |
| `ui/pygame/topology_lab/state_ownership.py` | 132–174 | ~10 unused dataclass/NamedTuple fields | ~15 | Part of in-progress restructure |

**Subtotal: ~89 LOC**

---

## LOC summary

| Category | LOC | Notes |
|----------|-----|-------|
| 100% confidence | 4 | Safe to remove |
| AI / playbot | 45 | `__getattr__` likely false positive (~20 LOC) |
| Engine — core | 37 | |
| Engine — gameplay | 75 | 28 LOC likely false positives (frontend bridge) |
| Engine — help | 26 | |
| Engine — runtime API | ~60 | **Likely all false positives** (frontend bridge) |
| Engine — runtime other | 11 | |
| Engine — topology explorer | 5 | |
| Engine — tutorial | 11 | |
| UI — misc | 8 | |
| UI — render | 7 | |
| UI — settings hub | ~31 | Verify cancel flow first |
| UI — runtime UI | 16 | |
| UI — topology lab launcher | 26 | |
| UI — topology lab core | ~89 | |
| **Total** | **~475** | |
| After excluding likely false positives | **~335** | Excluding frontend bridge (~60 LOC) + `__getattr__` (~20 LOC) |

---

## Recommended removal order

1. **100% confidence variables** (4 LOC) — zero risk.
2. **Topology lab dead helpers** in `controls_panel.py`, `projection_scene.py`,
   `topology_lab_menu.py` (~89 LOC) — self-contained, no cross-module risk.
3. **Tutorial dead items** (`events.py`, `manager.py`, `runtime.py`) (11 LOC).
4. **Engine core orphans** (`piece_transform.py`, `board.py`, `rng`) (37 LOC).
5. **Help system cache/validate functions** (26 LOC).
6. **Confirm cancel flow** before removing `original_*` settings hub fields (~31 LOC).
7. **Confirm frontend bridge is live** before touching any `*_runtime` functions in
   `api.py` files (~60 LOC).
