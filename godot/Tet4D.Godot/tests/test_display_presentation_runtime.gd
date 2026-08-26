extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const PreferencesScript = preload("res://scripts/ui/settings/shell_presentation_preferences.gd")


func run() -> Array:
	var failures: Array = []
	_test_camera_preferences(failures)
	failures.append_array(await _test_shell_preferences())
	return failures


func _test_camera_preferences(failures: Array) -> void:
	var low = CameraRigScript.new()
	low.set_presentation_preferences(PreferencesScript.camera_sensitivity_factor("low"), false)
	low.orbit(Vector2(20, 10))
	var low_snapshot: Dictionary = low.presentation_snapshot()
	var high = CameraRigScript.new()
	high.set_presentation_preferences(PreferencesScript.camera_sensitivity_factor("high"), false)
	high.orbit(Vector2(20, 10))
	var high_snapshot: Dictionary = high.presentation_snapshot()
	var baseline_yaw := CameraRigScript.PYTHON_DISPLAY_YAW_RAD
	if absf(float(high_snapshot.get("target_yaw")) - baseline_yaw) <= absf(float(low_snapshot.get("target_yaw")) - baseline_yaw):
		failures.append("camera sensitivity should change only camera response magnitude")
	var normal = CameraRigScript.new()
	normal.set_presentation_preferences(1.0, false)
	normal.orbit(Vector2(0, 10))
	var inverted = CameraRigScript.new()
	inverted.set_presentation_preferences(1.0, true)
	inverted.orbit(Vector2(0, 10))
	if signf(float(normal.presentation_snapshot().get("target_pitch")) - CameraRigScript.PYTHON_DISPLAY_PITCH_RAD) == signf(float(inverted.presentation_snapshot().get("target_pitch")) - CameraRigScript.PYTHON_DISPLAY_PITCH_RAD):
		failures.append("vertical inversion should reverse camera pitch direction")
	var panned = CameraRigScript.new()
	var pan_before: Vector3 = panned.presentation_snapshot().get("target_focus", Vector3.ZERO)
	# The pure camera contract can be exercised before tree attachment; the
	# app-level test covers the viewport-scaled drag path after readiness.
	panned.pan_focus(Vector3(1.0, 2.0, 0.0))
	if panned.presentation_snapshot().get("target_focus", Vector3.ZERO) == pan_before:
		failures.append("camera translation should update only the view focus")


func _test_shell_preferences() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["display presentation runtime test requires SceneTree"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(960, 720)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null:
		root.queue_free()
		return ["display presentation runtime test requires ReplayHud"]
	var panel = hud._settings_screen_panel
	var state_hash_before := str(app._current_snapshot.get("state_hash", "")) if app != null else ""
	var theme_before_scale = hud.theme
	panel._on_control_value_changed("display.ui_scale", "extra_large")
	panel._on_control_value_changed("display.hud_density", "compact")
	panel._on_control_value_changed("display.board_detail", "full")
	panel._on_control_value_changed("camera.sensitivity", "high")
	panel._on_control_value_changed("camera.invert_y", true)
	await tree.process_frame
	var preferences: Dictionary = hud.presentation_preferences_snapshot()
	if absf(float(preferences.get("ui_scale_factor")) - 1.3) > 0.001:
		failures.append("maximum UI scale should apply through the central shell owner")
	if (
		hud.theme == theme_before_scale
		or hud.theme.has_default_base_scale()
		or absf(ThemeDB.fallback_base_scale - 1.3) > 0.001
	):
		failures.append("runtime UI scaling should rebuild the theme so cached control metrics relayout")
	var scaled_extent: Vector2 = hud.size * hud.scale
	if hud.scale.distance_to(Vector2(1.3, 1.3)) > 0.001 or scaled_extent.x + 0.5 < tree.root.size.x or scaled_extent.y + 0.5 < tree.root.size.y:
		failures.append("runtime UI scaling should enlarge the HUD while preserving transformed viewport coverage")
	if preferences.get("hud_density") != "compact":
		failures.append("HUD density should apply through the shell owner")
	if absf(float(preferences.get("camera_sensitivity_factor")) - 1.45) > 0.001 or preferences.get("camera_invert_y") != true:
		failures.append("camera preferences should propagate without changing controls")
	if app != null:
		var renderer_preferences: Dictionary = app._renderer.presentation_preferences_snapshot()
		if renderer_preferences.get("board_detail") != "full":
			failures.append("board detail should reach the shared 2D/3D/4D renderer")
		var bounds_before: Dictionary = app._renderer.current_bounds().duplicate(true)
		panel._on_control_value_changed("display.board_detail", "minimal")
		await tree.process_frame
		if app._renderer.current_bounds() != bounds_before:
			failures.append("board-detail presets must not change board geometry or camera-fit bounds")
		if not state_hash_before.is_empty() and str(app._current_snapshot.get("state_hash", "")) != state_hash_before:
			failures.append("presentation settings must not change replay or gameplay identity")
		var deterministic_snapshot_before: Dictionary = app._current_snapshot.duplicate(true)
		var canonical_setup_before: Dictionary = app._active_live_setup.duplicate(true)
		var document_before = app._current_document
		var basis_before: Array = app._live_4d_basis.slots()
		var local_orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var camera_before: Dictionary = app._camera_rig.presentation_snapshot()
		var background_before: Color = app._world_environment.environment.background_color
		var profile_before = hud.presentation_profile()
		var variant = profile_before.with_overrides({
			"replay.playback_speed": 0.5,
			"replay.loop_enabled": false,
			"theme.name": "tron",
			"display.ui_scale": "large",
			"display.hud_density": "detailed",
			"accessibility.high_contrast": true,
			"display.grid_visible": false,
			"board.grid_opacity": 0.55,
			"board.boundary_opacity": 0.65,
			"active_cells.opacity": 0.65,
			"ghost.opacity": 1.25,
			"slice_set.spacing": 1.4,
			"environment.background_intensity": 1.3,
		})
		if not app.apply_presentation_profile(variant):
			failures.append("bounded app profile entry point should accept a valid live presentation variant")
		await tree.process_frame
		var applied_values: Dictionary = app._renderer.presentation_preferences_snapshot().get("profile", {}).get("values", {})
		for setting_id in ["board.grid_opacity", "board.boundary_opacity", "active_cells.opacity", "ghost.opacity", "slice_set.spacing", "environment.background_intensity"]:
			if applied_values.get(setting_id) != variant.value(setting_id):
				failures.append("live profile application should reach renderer/environment value %s" % setting_id)
		if app._world_environment.environment.background_color == background_before:
			failures.append("palette and background intensity should update live through the environment owner")
		if absf(app._state.playback_speed - 0.5) > 0.001 or app._state.loop_enabled:
			failures.append("bounded profile application should reach replay-presentation consumers")
		var live_hud_preferences: Dictionary = hud.presentation_preferences_snapshot()
		if absf(float(live_hud_preferences.get("ui_scale_factor")) - 1.15) > 0.001 or live_hud_preferences.get("hud_density") != "detailed":
			failures.append("bounded profile application should reach shell-owned scale and density consumers")
		if not bool(live_hud_preferences.get("accessibility", {}).get("high_contrast", false)) or hud._grid_visible:
			failures.append("bounded profile application should compose accessibility and quick grid presentation state")
		if app._current_snapshot != deterministic_snapshot_before or app._active_live_setup != canonical_setup_before or app._current_document != document_before:
			failures.append("profile switching must not reconstruct or mutate deterministic replay/session state")
		if app._live_4d_basis.slots() != basis_before or app._live_4d_local_orientation.snapshot() != local_orientation_before:
			failures.append("profile switching must not reset 4D basis or slice-local orientation")
		var camera_after: Dictionary = app._camera_rig.presentation_snapshot()
		for pose_key in ["target_yaw", "target_pitch", "target_roll", "current_yaw", "current_pitch", "current_roll", "target_focus", "current_focus", "zoom_multiplier"]:
			if camera_after.get(pose_key) != camera_before.get(pose_key):
				failures.append("profile switching must preserve runtime camera pose field %s" % pose_key)
		app.apply_presentation_profile(profile_before)
	hud.set_display_mode("plain")
	hud.show_screen("settings")
	await tree.process_frame
	if hud._style_manager.get_theme_id() != "plain":
		failures.append("runtime theme changes should reach the central shell style owner")
	var scroll := panel.get_node_or_null("SettingsScroll") as ScrollContainer
	if scroll == null or scroll.size.y <= 0 or not scroll.is_visible_in_tree() or scroll.get_v_scroll_bar() == null:
		failures.append("maximum-scale Settings controls should remain inside a viewport-safe scroll surface")
	hud.set_live_4d_mode(false, false, "reset")
	hud.set_snapshot({
		"trace_type": "live_4d",
		"state_hash": "stage51",
		"score": 120,
		"clears": 2,
		"current_piece": "T4",
		"next_piece": "L4",
		"board_shape": [5, 10, 4, 8],
		"dimension": 4,
		"last_command": "reset",
		"last_command_status": "reset",
		"active_w": 0,
		"w_slice_count": 8,
	}, false)
	var layout: Dictionary = hud.layout_contract_snapshot()
	if not bool(layout.get("onboarding", {}).get("visible", false)):
		failures.append("display preferences must not reset or hide separate onboarding")
	if str(layout.get("top_summary_text", "")).find("SCORE") == -1:
		failures.append("compact HUD should retain essential live score information")
	panel._on_control_value_changed("display.ui_scale", "standard")
	await tree.process_frame
	if hud.scale.distance_to(Vector2.ONE) > 0.001 or hud.size.x + 0.5 < tree.root.size.x or hud.size.y + 0.5 < tree.root.size.y:
		failures.append("standard UI scale should restore identity transform and full logical viewport bounds")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
