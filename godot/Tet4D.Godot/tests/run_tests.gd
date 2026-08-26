extends SceneTree


func _initialize() -> void:
	call_deferred("_run_all")


func _run_all() -> void:
	var failures: Array = []
	for script_path in [
		"res://tests/test_bundle_loader.gd",
		"res://tests/test_trace_snapshot_extractor.gd",
		"res://tests/test_replay_visuals.gd",
		"res://tests/test_shell_theme_palettes.gd",
		"res://tests/test_shell_style_manager.gd",
		"res://tests/test_shell_settings_registry.gd",
		"res://tests/test_presentation_parameter_contract.gd",
		"res://tests/test_shell_settings_store.gd",
		"res://tests/test_shell_settings_persistence.gd",
		"res://tests/test_shell_display_settings.gd",
		"res://tests/test_display_presentation_runtime.gd",
		"res://tests/test_accessibility_runtime.gd",
		"res://tests/test_game_setup_model.gd",
		"res://tests/test_board_extent_contract.gd",
		"res://tests/test_plain_setup_navigation.gd",
		"res://tests/test_setup_field_taxonomy.gd",
		"res://tests/test_setup_progressive_disclosure.gd",
		"res://tests/test_adaptive_4d_layer_layout.gd",
		"res://tests/test_slice_basis_4d.gd",
		"res://tests/test_slice_local_orientation.gd",
		"res://tests/test_control_frame_mapping.gd",
		"res://tests/test_next_piece_preview.gd",
		"res://tests/test_ghost_piece.gd",
		"res://tests/test_configurable_live_sessions.gd",
		"res://tests/test_local_board_presentation_geometry.gd",
		"res://tests/test_coordinate_mapper.gd",
		"res://tests/test_board_presentation_model.gd",
		"res://tests/test_camera_rig.gd",
		"res://tests/test_live_board_visual_grammar.gd",
		"res://tests/test_live_input_contract.gd",
		"res://tests/test_trace_scene_renderer.gd",
		"res://tests/test_tet4d_core_extension.gd",
		"res://tests/test_topology_contract_document.gd",
		"res://tests/test_topology_transport_boundary.gd",
		"res://tests/test_live_loop_parity_acceptance.gd",
		"res://tests/test_demo_entry_flow.gd",
		"res://tests/test_guided_onboarding.gd",
		"res://tests/test_navigation_contract.gd",
		"res://tests/test_player_facing_copy.gd",
		"res://tests/test_stage_47b_acceptance_contract.gd",
		"res://tests/test_stage_48_acceptance_regressions.gd",
		"res://tests/test_live_menu_input_routing.gd",
		"res://tests/test_live_viewer_restoration.gd",
		"res://tests/test_live_2d_shell.gd",
		"res://tests/test_scene_integrity.gd",
		"res://tests/test_replay_viewer_layout.gd",
		"res://tests/test_settings_panel_generation.gd",
		"res://tests/test_settings_screen_navigation.gd",
		"res://tests/test_shell_style_application.gd",
		"res://tests/test_particle_renderer.gd",
	]:
		var test_case = load(script_path).new()
		if script_path in [
			"res://tests/test_camera_rig.gd",
			"res://tests/test_trace_scene_renderer.gd",
			"res://tests/test_ghost_piece.gd",
			"res://tests/test_demo_entry_flow.gd",
			"res://tests/test_live_2d_shell.gd",
			"res://tests/test_replay_viewer_layout.gd",
			"res://tests/test_settings_panel_generation.gd",
			"res://tests/test_shell_settings_persistence.gd",
			"res://tests/test_display_presentation_runtime.gd",
			"res://tests/test_accessibility_runtime.gd",
			"res://tests/test_settings_screen_navigation.gd",
			"res://tests/test_shell_style_application.gd",
			"res://tests/test_stage_47b_acceptance_contract.gd",
			"res://tests/test_stage_48_acceptance_regressions.gd",
			"res://tests/test_live_menu_input_routing.gd",
			"res://tests/test_live_viewer_restoration.gd",
			"res://tests/test_plain_setup_navigation.gd",
			"res://tests/test_setup_field_taxonomy.gd",
		"res://tests/test_setup_progressive_disclosure.gd",
		]:
			failures.append_array(await test_case.run())
		else:
			failures.append_array(test_case.run())
	if failures.is_empty():
		print("Godot replay tests passed.")
		quit(0)
		return
	for failure in failures:
		push_error(str(failure))
		print(str(failure))
	quit(1)
