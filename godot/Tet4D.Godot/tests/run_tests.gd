extends SceneTree

const TEST_SCRIPTS := [
	"res://tests/test_bundle_loader.gd",
	"res://tests/test_trace_snapshot_extractor.gd",
	"res://tests/test_replay_visuals.gd",
	"res://tests/test_shell_theme_palettes.gd",
	"res://tests/test_shell_style_manager.gd",
	"res://tests/test_shell_settings_registry.gd",
	"res://tests/test_presentation_parameter_contract.gd",
	"res://tests/test_presentation_designer.gd",
	"res://tests/test_persistent_file_replacement.gd",
	"res://tests/test_presentation_profile_library.gd",
	"res://tests/test_built_in_style_catalog.gd",
	"res://tests/test_design_evaluation_laboratory.gd",
	"res://tests/test_design_laboratory_runtime.gd",
	"res://tests/test_product_bootstraps.gd",
	"res://tests/test_cross_platform_design_boundary.gd",
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
	"res://tests/test_live_presentation_regressions.gd",
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
	"res://tests/test_live_4d_orientation_rosette.gd",
	"res://tests/test_live_4d_slice_tiling.gd",
	"res://tests/test_live_board_visual_grammar.gd",
	"res://tests/test_live_input_contract.gd",
	"res://tests/test_semantic_control_helpers.gd",
	"res://tests/test_live_cockpit.gd",
	"res://tests/test_live_3d_shared_cockpit.gd",
	"res://tests/test_live_2d_shared_cockpit.gd",
	"res://tests/test_stage_56g_responsive_cockpit.gd",
	"res://tests/test_cockpit_density_control_hierarchy.gd",
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
]

const EXPECTED_NEGATIVE_PATH_TESTS := {
	"res://tests/test_shell_settings_store.gd": "settings write, backup, install, and restoration failures",
	"res://tests/test_slice_basis_4d.gd": "unsupported basis input",
	"res://tests/test_configurable_live_sessions.gd": "invalid fixed-seed setup inputs",
}


func _initialize() -> void:
	call_deferred("_run_all")


func _run_all() -> void:
	# Every registered script must load, run, and return its failures array; an
	# unread result is never treated as success.  A test that aborts mid-run
	# still returns [] because run() is typed, so that case is caught by the
	# SCRIPT ERROR check in scripts/verify_godot_4_7.sh, not here.
	var failures: Array = _unregistered_scripts()
	var executed := 0
	for index in TEST_SCRIPTS.size():
		var script_path: String = TEST_SCRIPTS[index]
		print("Godot replay test %d/%d: %s" % [index + 1, TEST_SCRIPTS.size(), script_path])
		if EXPECTED_NEGATIVE_PATH_TESTS.has(script_path):
			print("EXPECTED_NEGATIVE_PATH: %s" % EXPECTED_NEGATIVE_PATH_TESTS[script_path])
		var script: Resource = load(script_path)
		if script == null or not script.can_instantiate():
			failures.append("%s failed to load; parse error?" % script_path)
			continue
		var test_case = script.new()
		if not test_case.has_method("run"):
			failures.append("%s has no run() method" % script_path)
			continue
		# Awaited unconditionally: a coroutine called without await raises a
		# script error and hangs the run, and awaiting a plain Array returns it.
		var outcome: Variant = await test_case.run()
		if typeof(outcome) != TYPE_ARRAY:
			failures.append(
				"%s returned %s instead of a failures array"
				% [script_path, type_string(typeof(outcome))]
			)
			continue
		executed += 1
		failures.append_array(outcome)
	if executed != TEST_SCRIPTS.size():
		failures.append(
			"executed %d of %d registered test scripts" % [executed, TEST_SCRIPTS.size()]
		)
	if failures.is_empty():
		print("Godot replay tests passed: %d scripts executed." % executed)
		quit(0)
		return
	for failure in failures:
		push_error(str(failure))
		print(str(failure))
	quit(1)


func _unregistered_scripts() -> Array:
	# A test file that nobody registered would otherwise never run at all.
	var directory := DirAccess.open("res://tests")
	if directory == null:
		return ["could not open res://tests to check test registration"]
	var missing: Array = []
	for file_name in directory.get_files():
		if not file_name.begins_with("test_") or not file_name.ends_with(".gd"):
			continue
		var script_path := "res://tests/%s" % file_name
		if not TEST_SCRIPTS.has(script_path):
			missing.append("%s is not registered in run_tests.gd" % script_path)
	return missing
