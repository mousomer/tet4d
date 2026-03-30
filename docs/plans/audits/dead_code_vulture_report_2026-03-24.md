Role: audit
Status: reference
Source of truth: vulture 2.15 run against `src/` on 2026-03-24
Supersedes: none
Last updated: 2026-03-24

# Dead Code Report — Vulture 2026-03-24

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
