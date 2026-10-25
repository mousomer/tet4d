extends RefCounted

const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")
const GameSetupPanelScript = preload("res://scripts/ui/game_setup/game_setup_panel.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const StyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const StyleApplierScript = preload("res://scripts/ui/style/shell_control_style_applier.gd")
const PreferencesScript = preload("res://scripts/ui/settings/shell_presentation_preferences.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_minimum := tree.root.min_size
	tree.root.min_size = Vector2i.ZERO
	var original_canvas := tree.root.content_scale_size
	var original_base_scale := ThemeDB.fallback_base_scale
	var style_manager = StyleManagerScript.new()
	var style_applier = StyleApplierScript.new()
	for viewport_size in [Vector2i(1512, 982), Vector2i(1440, 900), Vector2i(1280, 720), Vector2i(1024, 640), Vector2i(800, 500)]:
		tree.root.size = viewport_size
		tree.root.content_scale_size = viewport_size
		for mode in GameSetupSpecScript.modes():
			for scale_id in ["standard", "extra_large"]:
				var ui_scale := PreferencesScript.ui_scale_factor(scale_id)
				ThemeDB.fallback_base_scale = ui_scale
				await _check_setup(failures, tree, viewport_size, mode, ui_scale, style_manager, style_applier)
	ThemeDB.fallback_base_scale = original_base_scale
	var settings = SettingsPanelScript.new()
	tree.root.add_child(settings)
	for width in [800.0, 520.0, 280.0, 220.0]:
		settings.size = Vector2(width, 500)
		await _settle(tree)
		if settings.size.x > width + 1.0:
			failures.append("settings must contract to available width %s, got %s" % [width, settings.size.x])
		var scroll := settings.get_node("SettingsScroll") as ScrollContainer
		for setting_id in settings._rows_by_id:
			var row := settings._rows_by_id[setting_id] as Control
			if row.get_global_rect().end.x > scroll.get_global_rect().end.x + 1.0:
				failures.append("settings row %s must stay in its viewport at width %s" % [setting_id, width])
		var setting_row := settings._rows_by_id["display.window_mode"] as Control
		var row_content := setting_row.get_node("SettingRowContent") as BoxContainer
		if width <= 280.0 and not row_content.vertical:
			failures.append("narrow settings must reflow label/control columns before scrolling")
	settings.size = Vector2(280, 300)
	await _settle(tree)
	var reset := settings.find_child("ResetAccessibilitySettingsButton", true, false) as Button
	reset.grab_focus()
	await _settle(tree)
	if not settings._scroll.get_global_rect().grow(1.0).encloses(reset.get_global_rect()):
		failures.append("height-only settings resize must retain focused reset accessibility")
	settings.free()
	tree.root.size = original_size
	tree.root.min_size = original_minimum
	tree.root.content_scale_size = original_canvas
	return failures


func _check_setup(failures: Array, tree: SceneTree, viewport_size: Vector2i, mode: String, ui_scale: float, style_manager, style_applier) -> void:
	var panel = GameSetupPanelScript.new()
	panel.theme = ReplayVisuals.build_theme("plain")
	panel.theme.default_base_scale = 0.0
	tree.root.add_child(panel)
	panel.size = Vector2(viewport_size) / ui_scale
	panel.scale = Vector2.ONE * ui_scale
	var model = GameSetupModelScript.new()
	model.set_mode(mode)
	panel.configure(model)
	style_applier.apply_to_tree(panel, style_manager)
	await _settle(tree)
	var footer := panel.find_child("SetupActions", true, false) as Control
	if footer == null:
		failures.append("%s setup at %s must keep essential actions in a fixed footer" % [mode, viewport_size])
	else:
		var viewport_rect := Rect2(Vector2.ZERO, Vector2(viewport_size))
		if not viewport_rect.grow(1.0).encloses(footer.get_global_rect()):
			failures.append("%s setup footer must fit %s: %s" % [mode, viewport_size, footer.get_global_rect()])
		for action_name in ["StartGameButton", "ResetSetupButton", "BackButton"]:
			var action := panel.find_child(action_name, true, false) as Control
			if action == null or not footer.get_global_rect().grow(1.0).encloses(action.get_global_rect()):
				failures.append("%s setup must keep %s visible at %s" % [mode, action_name, viewport_size])
	var scroll := panel.find_child("SetupScroll", true, false) as ScrollContainer
	if scroll != null:
		var content := scroll.get_child(0) as Control
		if content.get_global_rect().end.x > scroll.get_global_rect().end.x + 1.0:
			failures.append("%s setup content must contract within the horizontal viewport at %s" % [mode, viewport_size])
		if viewport_size.y >= 900 and ui_scale == 1.0 and scroll.get_v_scroll_bar().visible:
			failures.append("%s collapsed setup must not scroll when ordinary content fits %s" % [mode, viewport_size])
		for focus_control in panel.visible_focus_controls():
			focus_control.grab_focus()
			await _settle(tree)
			var surface := scroll if scroll.is_ancestor_of(focus_control) else footer
			if surface != null and not surface.get_global_rect().grow(1.0).encloses(focus_control.get_global_rect()):
				failures.append("%s setup focus %s must remain visible at %s scale %s: %s in %s" % [mode, focus_control.name, viewport_size, ui_scale, focus_control.get_global_rect(), surface.get_global_rect()])
		if viewport_size.y == 500:
			for section_id in panel.disclosure_section_ids():
				panel.set_section_expanded(section_id, true)
			await _settle(tree)
			if not scroll.get_v_scroll_bar().visible:
				failures.append("%s expanded setup must scroll when minimum content exceeds a small viewport" % mode)
	if viewport_size.y == 500 and footer != null:
		var previous_bottom := footer.get_global_rect().end.y
		panel.size.y -= 80.0
		await _settle(tree)
		if footer.get_global_rect().end.y >= previous_bottom - 1.0:
			failures.append("%s height-only setup resize must reposition the action footer" % mode)
		if not panel.get_global_rect().grow(1.0).encloses(footer.get_global_rect()):
			failures.append("%s height-only setup resize must retain essential action visibility" % mode)
	panel.free()


func _settle(tree: SceneTree) -> void:
	for frame in range(12):
		await tree.process_frame
