extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")
const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["shell style application test requires SceneTree"]
	var manager = ShellStyleManagerScript.new()
	var panel: Control = SettingsPanelScript.new()
	panel.set_style_manager(manager)
	tree.root.add_child(panel)
	panel.size = Vector2(420, 620)
	await tree.process_frame
	if panel.get_meta("shell_style_theme_id", "") != "tron":
		failures.append("settings panel should receive tron style metadata")
	var title := panel.get_node_or_null("SettingsScroll/SettingsContent/SettingsIntro/SettingsTitle") as Label
	if title == null:
		failures.append("settings title missing")
	elif title.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
		failures.append("settings title should use accent.primary")
	var description := panel.get_node_or_null("SettingsScroll/SettingsContent/SettingsIntro/SettingsSubtitle") as Label
	if description == null:
		failures.append("settings subtitle missing")
	elif description.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.TEXT_MUTED):
		failures.append("settings subtitle should use text.muted")
	panel.set_setting_value("theme.name", "plain")
	panel.set_display_mode("plain")
	await tree.process_frame
	if panel.style_manager().get_theme_id() != "plain":
		failures.append("changing theme.name should update settings panel style manager")
	if title != null and title.get_theme_color("font_color") != panel.style_manager().get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
		failures.append("settings title should refresh when theme changes")
	panel.queue_free()
	await tree.process_frame
	failures.append_array(_check_settings_registry())
	failures.append_array(_check_replay_visual_roles())
	return failures


func _check_settings_registry() -> Array:
	var failures: Array = []
	var registry = SettingsRegistryScript.new()
	registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	var spec = registry.get_spec("theme.name")
	if spec == null:
		return ["theme.name setting missing"]
	if spec.default_value() != "tron":
		failures.append("theme.name default should be tron")
	var values: Array = []
	for option in spec.data.get("options", []):
		values.append(str(option.get("value", "")))
	if values != ["diagnostic", "plain", "tron"]:
		failures.append("theme.name options should be diagnostic/plain/tron, got %s" % values)
	if spec.control_type() != "dropdown":
		failures.append("theme.name should remain a dropdown")
	var manager = ShellStyleManagerScript.new()
	manager.set_theme(str(spec.default_value()))
	if manager.get_theme_id() != "tron":
		failures.append("theme.name default should drive style manager to tron")
	return failures


func _check_replay_visual_roles() -> Array: # tet4d-semantic-boundary: allow test-fixture
	var failures: Array = []
	var manager = ShellStyleManagerScript.new()
	manager.set_theme("tron")
	if ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_BOARD_FILL, "tron") != manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD):
		failures.append("board fill should use background.board")
	if ReplayVisuals.color_for_role(ReplayVisuals.ROLE_LIVE_BOARD_GRID, "tron") != manager.get_color(ShellStyleRolesScript.GRID_MINOR):
		failures.append("board grid should use grid.minor")
	if ReplayVisuals.slice_label_color("tron") != manager.get_color(ShellStyleRolesScript.LABEL_W_LAYER):
		failures.append("W/layer labels should use label.w_layer")
	if ReplayVisuals.event_marker_material("tron").albedo_color != manager.get_color(ShellStyleRolesScript.DIAGNOSTIC_BOUNDS):
		failures.append("event markers should use diagnostic.bounds")
	return failures
