extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const PreferencesScript = preload("res://scripts/ui/settings/shell_presentation_preferences.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	_test_camera_preferences(failures)
	failures.append_array(await _test_shell_preferences())
	return failures


func _test_camera_preferences(failures: Array) -> void:
	var low = CameraRigScript.new()
	low.set_presentation_preferences(PreferencesScript.camera_sensitivity_factor("low"), false, false)
	low.orbit(Vector2(20, 10))
	var low_snapshot: Dictionary = low.presentation_snapshot()
	var high = CameraRigScript.new()
	high.set_presentation_preferences(PreferencesScript.camera_sensitivity_factor("high"), false, false)
	high.orbit(Vector2(20, 10))
	var high_snapshot: Dictionary = high.presentation_snapshot()
	var baseline_yaw := CameraRigScript.PYTHON_DISPLAY_YAW_RAD
	if absf(float(high_snapshot.get("target_yaw")) - baseline_yaw) <= absf(float(low_snapshot.get("target_yaw")) - baseline_yaw):
		failures.append("camera sensitivity should change only camera response magnitude")
	var normal = CameraRigScript.new()
	normal.set_presentation_preferences(1.0, false, false)
	normal.orbit(Vector2(0, 10))
	var inverted = CameraRigScript.new()
	inverted.set_presentation_preferences(1.0, true, true)
	inverted.orbit(Vector2(0, 10))
	if signf(float(normal.presentation_snapshot().get("target_pitch")) - CameraRigScript.PYTHON_DISPLAY_PITCH_RAD) == signf(float(inverted.presentation_snapshot().get("target_pitch")) - CameraRigScript.PYTHON_DISPLAY_PITCH_RAD):
		failures.append("vertical inversion should reverse camera pitch direction")
	if not bool(inverted.presentation_snapshot().get("reduced_motion", false)):
		failures.append("reduced motion should reach the camera interpolation owner")


func _test_shell_preferences() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["presentation accessibility runtime test requires SceneTree"]
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
		return ["presentation accessibility runtime test requires ReplayHud"]
	var panel = hud._settings_screen_panel
	var state_hash_before := str(app._current_snapshot.get("state_hash", "")) if app != null else ""
	panel._on_control_value_changed("display.ui_scale", "extra_large")
	panel._on_control_value_changed("display.hud_density", "compact")
	panel._on_control_value_changed("display.board_detail", "full")
	panel._on_control_value_changed("accessibility.contrast_mode", "high")
	panel._on_control_value_changed("accessibility.animation_mode", "reduced")
	panel._on_control_value_changed("camera.sensitivity", "high")
	panel._on_control_value_changed("camera.invert_y", true)
	panel._on_control_value_changed("controls_help.contextual_help", "hidden")
	await tree.process_frame
	var preferences: Dictionary = hud.presentation_preferences_snapshot()
	if absf(float(preferences.get("ui_scale_factor")) - 1.3) > 0.001:
		failures.append("maximum UI scale should apply through the central shell owner")
	if preferences.get("hud_density") != "compact" or preferences.get("contextual_help") != "hidden":
		failures.append("HUD density and contextual help should apply independently")
	if preferences.get("contrast_mode") != "high" or preferences.get("animation_mode") != "reduced":
		failures.append("contrast and reduced motion should apply through the shell owner")
	if absf(float(preferences.get("camera_sensitivity_factor")) - 1.45) > 0.001 or preferences.get("camera_invert_y") != true:
		failures.append("camera preferences should propagate without changing controls")
	if app != null:
		var renderer_preferences: Dictionary = app._renderer.presentation_preferences_snapshot()
		if renderer_preferences != {"board_detail": "full", "contrast_mode": "high", "animation_mode": "reduced"}:
			failures.append("board detail, contrast, and motion should reach the shared 2D/3D/4D renderer")
		var bounds_before: Dictionary = app._renderer.current_bounds().duplicate(true)
		panel._on_control_value_changed("display.board_detail", "minimal")
		await tree.process_frame
		if app._renderer.current_bounds() != bounds_before:
			failures.append("board-detail presets must not change board geometry or camera-fit bounds")
		if not state_hash_before.is_empty() and str(app._current_snapshot.get("state_hash", "")) != state_hash_before:
			failures.append("presentation settings must not change replay or gameplay identity")
	hud.set_display_mode("plain")
	hud.show_screen("settings")
	await tree.process_frame
	var focus_control := panel.generated_control("display.window_mode") as Control
	var focus_style := focus_control.get_theme_stylebox("focus") as StyleBoxFlat if focus_control != null else null
	if focus_style == null or focus_style.get_border_width(SIDE_LEFT) < 3:
		failures.append("Plain high-contrast settings focus should have an explicit heavy frame")
	var focus_color: Color = hud._style_manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS)
	if focus_style != null and focus_style.border_color != focus_color:
		failures.append("high-contrast focus frame should use the semantic focus role")
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
	if bool(layout.get("viewport_hints_visible", true)) or bool(layout.get("bottom_hints_visible", true)) or not str(layout.get("inspector_hint_text", "")).is_empty():
		failures.append("hidden contextual help should remove non-essential hints from live play")
	if not bool(layout.get("onboarding", {}).get("visible", false)):
		failures.append("hiding contextual help must not reset or hide separate onboarding")
	panel._on_control_value_changed("controls_help.contextual_help", "always")
	await tree.process_frame
	layout = hud.layout_contract_snapshot()
	if not bool(layout.get("viewport_hints_visible", false)) or str(layout.get("inspector_hint_text", "")).is_empty():
		failures.append("always-visible contextual help should expose viewport and inspector guidance")
	if str(layout.get("top_summary_text", "")).find("SCORE") == -1:
		failures.append("compact HUD should retain essential live score information")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
