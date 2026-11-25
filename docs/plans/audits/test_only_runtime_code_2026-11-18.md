# Runtime code reached only by tests

The cleanup removed the five adapters below. The regression tests now drive the menu runner, 4D tuple coercion, numeric key handling, renderer profile application, and Explorer preview and storage directly. The live 4D tuple path renders opaque active cells. Legacy v1 edge-rule documents still round-trip through their store.

This review traces in-repository consumers. A test can keep a method callable long after the game has switched to another path. The clearest cleanup candidates are adapters where the same assertion can exercise the path the game uses today.

| Production owner and entry point | Test consumer | Finding |
| --- | --- | --- |
| `runtime_ui/pause_menu.py` · `_pause_menu_keydown` | `test_pause_menu.py` | Two tests send Escape and Q to this private handler. The running menu uses the menu runner and registers `_pause_root_escape` directly. Exercise keyboard routing through the runner before removing the handler. |
| `front4d_render.py` · `_overlay_active_layer_cells` | `test_overlay_transparency_render_paths.py` | The test uses the old tuple adapter. Rendering supplies piece state to `_active_layer_cells_from_piece_state`. Keep the overlay visibility and transparency assertions on the live path. |
| `locked_cell_explosion/surface.py` · `_commit_trace_retention_input` | `test_locked_cell_explosion.py` | The helper builds a temporary numeric edit from a second text buffer. Live key handling goes through `_handle_numeric_text_keydown`. Drive the valid and invalid retention inputs through that editor. |
| `rendering/trace_scene_renderer.gd` · `set_grid_visible`, `set_locked_cell_opacity` | `test_trace_scene_renderer.gd` | The app calls `apply_presentation_profile` to set both values. Exercise the same grid and opacity changes through a profile. Its other setter, `set_grid_mode`, is called by the boolean wrapper and directly by the same test. All three setters are reachable only from tests. |
| `runtime/topology_explorer_bridge.py` · legacy profile conversion and preview export | `test_topology_explorer_preview.py`, `test_topology_profile_store.py` | All imports from outside the module are in these two tests. `explorer_profile_from_edge_rules` has no repository caller. The general RDS §11.6.1 and the project structure still name the bridge. Decide whether legacy conversion is supported before removing its validation tests. |

## Test-only surfaces with a specific role

- The playbot's `play_one_piece_2d` and `play_one_piece_nd` drive deterministic whole-piece simulations. The score snapshot test also uses the 2D driver. These could live in test support if that API is retired.
- The Godot HUD's `layout_contract_snapshot` feeds locked-layout assertions and responsive acceptance tooling. Removing it would remove evidence about the rendered shell.
- The native `echo_text` and `add_integers` methods have a full C++ implementation, GDExtension binding and GDScript wrapper. The external caller in the repository is the extension smoke test. Both methods appear in the Stage 8 boundary contract and native README.

## Scope of evidence

The scan compared function definitions against names in tracked source, scenes, configuration, build scripts and tests. The findings above also use inspection of the defining method and its callers. Declarations, public exports and native bindings can keep a name visible even when every external consumer is a test. Conversely, engine callbacks, generated names and external consumers can execute code without a literal call in the repository. This is a static review, with no gameplay coverage measurement or claim of exhaustive reachability.

## Additional candidates from the name scan

Each row groups definitions with a matching name in a test and no other literal use found in the scanned implementation files. Test names in this index are leads for inspection. Methods with multiple owners, engine dispatch and tools that run acceptance probes need caller-level review. The cross-file chains discussed above were traced separately.

| Production file | Candidate definitions | Example test files |
| --- | --- | --- |
| `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd` | `ghost_cache_snapshot`, `_reset_live_4d_basis_only` | `test_ghost_piece.gd`, `test_live_2d_shell.gd` |
| `godot/Tet4D.Godot/scripts/design_lab/design_capture_store.gd` | `metadata_for_session` | `test_design_evaluation_laboratory.gd` |
| `godot/Tet4D.Godot/scripts/design_lab/design_comparison_session.gd` | `reset_request`, `frozen_arm` | `test_design_evaluation_laboratory.gd` |
| `godot/Tet4D.Godot/scripts/input/live_input_contract.gd` | `camera_control_specs` | `test_live_input_contract.gd` |
| `godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd` | `native_topology_transport_query` | `test_topology_transport_boundary.gd` |
| `godot/Tet4D.Godot/scripts/native/topology_contract_document.gd` | `is_loaded` | `test_topology_contract_document.gd` |
| `godot/Tet4D.Godot/scripts/platform/design_platform_profile.gd` | `for_os_name`, `has_system_back_gesture`, `requires_safe_area_insets` | `test_cross_platform_design_boundary.gd` |
| `godot/Tet4D.Godot/scripts/presentation/adaptive_layer_layout.gd` | `offset_for_layer`, `candidate_snapshot` | `test_adaptive_4d_layer_layout.gd` |
| `godot/Tet4D.Godot/scripts/presentation/built_in_style_catalog.gd` | `animated_style_ids` | `test_built_in_style_catalog.gd` |
| `godot/Tet4D.Godot/scripts/presentation/local_board_presentation_geometry.gd` | `cell_transform`, `cell_bounds` | `test_local_board_presentation_geometry.gd` |
| `godot/Tet4D.Godot/scripts/presentation/practice_explorer.gd` | `select_next_cell` | `test_practice_explorer.gd` |
| `godot/Tet4D.Godot/scripts/presentation/presentation_profile.gd` | `values_for_owner` | `test_presentation_designer.gd` |
| `godot/Tet4D.Godot/scripts/presentation/slice_basis_4d.gd` | `from_slots`, `canonical_movement_command` | `test_adaptive_4d_layer_layout.gd`, `test_slice_basis_4d.gd` |
| `godot/Tet4D.Godot/scripts/presentation/slice_local_orientation.gd` | `active_yaw_basis`, `orient_local_point` | `test_slice_local_orientation.gd` |
| `godot/Tet4D.Godot/scripts/rendering/camera_rig.gd` | `drawn_content_size`, `fitted_height_limited`, `nudge_roll`, `pan_focus`, `set_orientation_basis`, `orientation_indicator_snapshot`, `camera_space_point`, `is_world_point_behind`, `live_4d_all_yaw_safe_pitch_domain`, `live_4d_worst_case_semantic_forward_away_depth` | `test_built_in_style_catalog.gd`, `test_camera_rig.gd`, `test_locked_shell_layouts.gd`, `test_stage_58b_readability.gd` |
| `godot/Tet4D.Godot/scripts/rendering/cell_renderer.gd` | `presentation_weight` | `test_stage_58c_spatial_readability.gd` |
| `godot/Tet4D.Godot/scripts/rendering/grid_renderer.gd` | `grid_topology` | `test_spatial_scaffold.gd` |
| `godot/Tet4D.Godot/scripts/rendering/trace_coordinate_mapper.gd` | `slice_offset`, `slice_label_position`, `board_bounds`, `visible_board_shape` | `test_adaptive_4d_layer_layout.gd`, `test_coordinate_mapper.gd` |
| `godot/Tet4D.Godot/scripts/rendering/trace_scene_renderer.gd` | `set_grid_visible`, `set_locked_cell_opacity`, `live_4d_local_orientation_snapshot`, `live_4d_basis_snapshot`, `presentation_preferences_snapshot` | `test_accessibility_runtime.gd`, `test_live_2d_shell.gd`, `test_trace_scene_renderer.gd` |
| `godot/Tet4D.Godot/scripts/ui/game_setup/game_setup_panel.gd` | `visible_focus_controls`, `hidden_focus_controls` | `test_plain_setup_navigation.gd` |
| `godot/Tet4D.Godot/scripts/ui/game_setup/setup_field_registry.gd` | `visible_specs_for`, `specs_for_category`, `session_identity_keys` | `test_setup_field_taxonomy.gd` |
| `godot/Tet4D.Godot/scripts/ui/game_setup/setup_field_spec.gd` | `defines_session_identity` | `test_setup_field_taxonomy.gd` |
| `godot/Tet4D.Godot/scripts/ui/onboarding/live_onboarding_model.gd` | `dismiss` | `test_guided_onboarding.gd` |
| `godot/Tet4D.Godot/scripts/ui/presentation_designer.gd` | `revert_and_hide`, `capture_reference`, `revert_style`, `built_in_style_records`, `reference_profile`, `opening_profile`, `control_for_setting` | `test_built_in_style_catalog.gd`, `test_current_design_state.gd`, `test_presentation_designer.gd` |
| `godot/Tet4D.Godot/scripts/ui/replay_hud.gd` | `replay_hint_text`, `live_2d_hint_text`, `live_3d_hint_text`, `live_4d_hint_text`, `design_affordances_enabled`, `layout_contract_snapshot`, `windowed_size_persistence_ready`, `presentation_preferences_snapshot`, `live_command_feedback_text` | `run_responsive_acceptance.gd`, `test_accessibility_runtime.gd`, `test_live_2d_shell.gd`, `test_shell_display_settings.gd` |
| `godot/Tet4D.Godot/scripts/ui/replay_visuals.gd` | `active_cell_material`, `live_board_fill_material`, `slice_outline_material`, `normalize_locked_cell_opacity` | `test_replay_visuals.gd` |
| `godot/Tet4D.Godot/scripts/ui/settings/settings_store.gd` | `reset_to_defaults` | `test_shell_settings_store.gd` |
| `godot/Tet4D.Godot/scripts/ui/settings_panel.gd` | `set_setting_value`, `generated_control` | `test_settings_panel_generation.gd`, `test_shell_style_application.gd` |
| `godot/Tet4D.Godot/scripts/ui/style/shell_style_manager.gd` | `available_theme_ids`, `validate_all` | `test_shell_theme_palettes.gd` |
| `src/tet4d/ai/playbot/controller.py` | `play_one_piece_2d`, `play_one_piece_nd` | `test_playbot.py` |
| `src/tet4d/engine/gameplay/pieces_nd.py` | `get_standard_pieces_nd` | `test_pieces_nd.py` |
| `src/tet4d/engine/runtime/menu_config.py` | `authored_menu_graph`, `launcher_menu_items`, `ui_copy_payload` | `test_menu_policy.py` |
| `src/tet4d/engine/runtime/project_config.py` | `score_events_file_default_path`, `score_summary_file_default_path` | `test_frozen_runtime_paths.py`, `test_project_config.py` |
| `src/tet4d/engine/runtime/score_analyzer.py` | `reset_score_analyzer_runtime_state`, `score_analysis_summary_snapshot` | `test_score_analyzer.py` |
| `src/tet4d/engine/runtime/topology_playground_state.py` | `inspector_state`, `derived_state` | `test_topology_playground_state.py` |
| `src/tet4d/engine/tutorial/content.py` | `clear_tutorial_content_cache` | `test_tutorial_content.py` |
| `src/tet4d/engine/tutorial/manager.py` | `lesson_ids` | `test_tutorial_content.py` |
| `src/tet4d/ui/pygame/endgame_animation.py` | `select_endgame_live_locked_cells` | `test_endgame_animation.py` |
| `src/tet4d/ui/pygame/front4d_render.py` | `_overlay_active_layer_cells` | `test_overlay_transparency_render_paths.py` |
| `src/tet4d/ui/pygame/locked_cell_explosion/surface.py` | `_commit_trace_retention_input` | `test_locked_cell_explosion.py` |
| `src/tet4d/ui/pygame/runtime_ui/pause_menu.py` | `_pause_menu_keydown` | `test_pause_menu.py` |
| `src/tet4d/ui/pygame/ui_utils.py` | `text_fits` | `test_help_menu.py` |
