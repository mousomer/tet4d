extends RefCounted

const AccessibilityPolicyScript = preload("res://scripts/ui/accessibility/accessibility_policy.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellControlStyleApplierScript = preload("res://scripts/ui/style/shell_control_style_applier.gd")


func run() -> Array:
	var failures: Array = []
	_test_policy_derivation(failures)
	_test_focus_and_contrast(failures)
	failures.append_array(await _test_live_propagation())
	return failures


func _test_policy_derivation(failures: Array) -> void:
	var policy = AccessibilityPolicyScript.new()
	var defaults: Dictionary = policy.deterministic_snapshot()
	if defaults.get("high_contrast") != false or defaults.get("reduced_motion") != false or defaults.get("show_help_hints") != true:
		failures.append("accessibility policy should expose schema-3 defaults")
	if defaults.get("focus_visibility_required") != true or defaults.get("non_colour_cues_required") != true:
		failures.append("focus visibility and non-colour cues should remain unconditional invariants")
	if not policy.configure(true, true, false):
		failures.append("changed accessibility values should produce a changed policy snapshot")
	if policy.configure(true, true, false):
		failures.append("unchanged accessibility values should not report a policy change")
	var reduced: Dictionary = policy.deterministic_snapshot()
	if reduced.get("transition_duration_scale") != 0.0 or reduced.get("camera_interpolation_scale") != 0.0:
		failures.append("Reduced Motion should derive immediate presentation transitions")
	if reduced.get("decorative_animation_enabled") != false or reduced.get("pulse_enabled") != false or reduced.get("flash_enabled") != false:
		failures.append("Reduced Motion should disable decorative animation, pulse, and flash")


func _test_focus_and_contrast(failures: Array) -> void:
	var style_manager = ShellStyleManagerScript.new()
	var applier = ShellControlStyleApplierScript.new()
	for theme_id in ["diagnostic", "plain", "tron"]:
		style_manager.set_theme(theme_id)
		var standard_focus := style_manager.get_color("accent.focus")
		style_manager.set_high_contrast_enabled(true)
		var high_focus := style_manager.get_color("accent.focus")
		if high_focus == standard_focus and theme_id != "diagnostic":
			failures.append("%s should compose with a semantic High Contrast focus role" % theme_id)
		var button := Button.new()
		applier.apply_to_tree(button, style_manager)
		var normal := button.get_theme_stylebox("normal") as StyleBoxFlat
		var hover := button.get_theme_stylebox("hover") as StyleBoxFlat
		var focus := button.get_theme_stylebox("focus") as StyleBoxFlat
		if normal == null or hover == null or focus == null:
			failures.append("%s controls should expose normal, hover, and focus geometry" % theme_id)
		elif (
			focus.get_border_width(SIDE_LEFT) <= hover.get_border_width(SIDE_LEFT)
			or focus.get_border_width(SIDE_LEFT) <= normal.get_border_width(SIDE_LEFT)
		):
			failures.append("%s focus should use a thicker static outline than hover or normal" % theme_id)
		style_manager.set_high_contrast_enabled(false)


func _test_live_propagation() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["accessibility runtime test requires the replay scene and SceneTree"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		return ["accessibility runtime test requires ReplayHud and TraceReplayApp"]
	var panel = hud._settings_screen_panel
	var state_hash_before := str(app._current_snapshot.get("state_hash", ""))
	panel._on_control_value_changed("accessibility.high_contrast", true)
	panel._on_control_value_changed("accessibility.reduced_motion", true)
	panel._on_control_value_changed("accessibility.show_help_hints", false)
	await tree.process_frame
	var policy: Dictionary = hud.presentation_preferences_snapshot().get("accessibility", {})
	if policy.get("high_contrast") != true or policy.get("reduced_motion") != true or policy.get("show_help_hints") != false:
		failures.append("all accessibility preferences should update live through ReplayHud")
	if not hud._style_manager.is_high_contrast_enabled():
		failures.append("High Contrast should compose through the shared style manager")
	var renderer_policy: Dictionary = app._renderer.presentation_preferences_snapshot()
	if renderer_policy.get("high_contrast") != true or renderer_policy.get("reduced_motion") != true:
		failures.append("renderer should consume the central accessibility policy")
	var camera_policy: Dictionary = app._camera_rig.presentation_snapshot()
	if camera_policy.get("interpolation_scale") != 0.0:
		failures.append("camera should consume the Reduced Motion interpolation policy")
	var layout: Dictionary = hud.layout_contract_snapshot()
	if (
		bool(layout.get("viewport_hints_visible", true))
		or bool(layout.get("bottom_hints_visible", true))
		or not str(layout.get("inspector_hint_text", "")).is_empty()
	):
		failures.append("optional help and control hints should hide live without hiding required state")
	if not state_hash_before.is_empty() and str(app._current_snapshot.get("state_hash", "")) != state_hash_before:
		failures.append("accessibility presentation must not change gameplay or replay identity")
	panel._on_control_value_changed("theme.name", "plain")
	panel.reset_accessibility_settings_to_defaults()
	await tree.process_frame
	if panel.setting_value("theme.name") != "plain":
		failures.append("Reset Accessibility Settings must preserve display theme")
	if panel.setting_value("accessibility.high_contrast") != false or panel.setting_value("accessibility.reduced_motion") != false or panel.setting_value("accessibility.show_help_hints") != true:
		failures.append("Reset Accessibility Settings should reset only its three bounded preferences")
	root.queue_free()
	await tree.process_frame
	return failures
