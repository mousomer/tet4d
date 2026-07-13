extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")
const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const ShellControlStyleApplierScript = preload("res://scripts/ui/style/shell_control_style_applier.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["shell style application test requires SceneTree"]
	var manager = ShellStyleManagerScript.new()
	failures.append_array(_check_control_hint_palette(manager))
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
	var loop_checkbox := panel.generated_control("replay.loop_enabled") as CheckBox
	if loop_checkbox == null:
		failures.append("replay loop checkbox should be generated")
	else:
		var checked_box := loop_checkbox.get_theme_stylebox("checked") as StyleBoxFlat
		if checked_box == null:
			failures.append("checkbox should receive a checked cockpit stylebox")
		elif checked_box.bg_color != manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
			failures.append("checked checkbox should use accent.primary")
		var unchecked_box := loop_checkbox.get_theme_stylebox("unchecked") as StyleBoxFlat
		if unchecked_box == null:
			failures.append("checkbox should receive an unchecked cockpit stylebox")
		elif unchecked_box.border_color != manager.get_color(ShellStyleRolesScript.GRID_MINOR):
			failures.append("unchecked checkbox should use grid.minor border")
	var speed_group := panel.generated_control("replay.playback_speed") as HBoxContainer
	var speed_slider: HSlider = null
	var speed_value_label: Label = null
	if speed_group != null:
		speed_slider = speed_group.get_node_or_null("Slider") as HSlider
		speed_value_label = speed_group.get_node_or_null("ValueLabel") as Label
	if speed_slider == null:
		failures.append("playback speed slider should be generated")
	else:
		var slider_track := speed_slider.get_theme_stylebox("grabber_area") as StyleBoxFlat
		var slider_fill := speed_slider.get_theme_stylebox("slider") as StyleBoxFlat
		if slider_track == null:
			failures.append("slider should receive a cockpit track stylebox")
		elif slider_track.bg_color != manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD):
			failures.append("slider track should use background.board")
		if slider_fill == null:
			failures.append("slider should receive a cockpit fill stylebox")
		elif slider_fill.bg_color != manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
			failures.append("slider fill should use accent.primary")
	if speed_value_label == null:
		failures.append("playback speed value label should be generated")
	elif speed_value_label.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.DIAGNOSTIC_METADATA):
		failures.append("numeric value labels should use diagnostic.metadata")
	panel.set_setting_value("theme.name", "plain")
	panel.set_display_mode("plain")
	await tree.process_frame
	if panel.style_manager().get_theme_id() != "plain":
		failures.append("changing theme.name should update settings panel style manager")
	if title != null and title.get_theme_color("font_color") != panel.style_manager().get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
		failures.append("settings title should refresh when theme changes")
	var plain_button := Button.new()
	plain_button.name = "CommandCard__Plain_Focus_Check"
	ShellControlStyleApplierScript.new().apply_to_tree(plain_button, panel.style_manager())
	var plain_normal := plain_button.get_theme_stylebox("normal") as StyleBoxFlat
	var plain_focus := plain_button.get_theme_stylebox("focus") as StyleBoxFlat
	if plain_normal == null or plain_focus == null:
		failures.append("plain menu cards should define normal and focused surfaces")
	elif plain_focus.bg_color != panel.style_manager().get_color(ShellStyleRolesScript.ACCENT_SOFT):
		failures.append("plain focused menu cards should use the visible soft accent surface")
	elif plain_focus.bg_color == plain_normal.bg_color:
		failures.append("plain focused menu cards should remain distinguishable from unselected cards")
	panel.queue_free()
	await tree.process_frame
	failures.append_array(_check_settings_registry())
	failures.append_array(_check_replay_visual_roles())
	return failures


func _check_control_hint_palette(manager) -> Array:
	var failures: Array = []
	var applier = ShellControlStyleApplierScript.new()
	var group := HBoxContainer.new()
	var section := Label.new()
	section.name = "ControlHintSectionHeader"
	section.text = "Movement"
	section.theme_type_variation = "SecondaryLabel"
	group.add_child(section)
	var keycap := Label.new()
	keycap.name = "ControlHintKeycap"
	keycap.text = "A / D"
	keycap.theme_type_variation = "KeycapLabel"
	group.add_child(keycap)
	var action := Label.new()
	action.name = "ControlHintAction"
	action.text = "X- / X+"
	action.theme_type_variation = "SecondaryLabel"
	group.add_child(action)
	var note := Label.new()
	note.name = "ControlHintNote"
	note.text = "Left: CCW"
	note.theme_type_variation = "DimLabel"
	group.add_child(note)
	var warning := Label.new()
	warning.name = "ControlHintWarning"
	warning.text = "GAME OVER · Piece out of bounds"
	warning.theme_type_variation = "WarningLabel"
	group.add_child(warning)
	var status := Label.new()
	status.name = "TopStatusBadgeLabel"
	status.text = "[ GAME OVER ] Piece out of bounds"
	status.theme_type_variation = "StatusErrorLabel"
	group.add_child(status)
	applier.apply_to_tree(group, manager)
	var keycap_box := keycap.get_theme_stylebox("normal") as StyleBoxFlat
	if keycap_box == null:
		failures.append("keycap should receive a cockpit stylebox")
	elif keycap_box.border_color != manager.get_color(ShellStyleRolesScript.HINT_KEYCAP_BORDER):
		failures.append("keycap border should use hint.keycap.border")
	if section.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.HINT_SECTION):
		failures.append("control section headers should use hint.section")
	if keycap.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.HINT_KEYCAP_TEXT):
		failures.append("keycap text should use hint.keycap.text")
	if action.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.HINT_ACTION):
		failures.append("control action text should use hint.action")
	if note.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.HINT_NOTE):
		failures.append("control notes should use hint.note")
	if warning.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.HINT_ERROR):
		failures.append("control game-over warnings should use hint.error")
	var status_box := status.get_theme_stylebox("normal") as StyleBoxFlat
	if status.get_theme_color("font_color") != manager.get_color(ShellStyleRolesScript.STATE_ERROR):
		failures.append("status error badges should use state.error text")
	if status_box == null:
		failures.append("status error badges should receive a badge stylebox")
	elif status_box.border_color != manager.get_color(ShellStyleRolesScript.STATE_ERROR):
		failures.append("status error badges should use state.error border")
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
	var labels: Array = []
	for option in spec.data.get("options", []):
		labels.append(str(option.get("label", "")))
	if labels != ["Diagnostic", "Plain", "Vector Arcade"]:
		failures.append("theme.name labels should present tron as Vector Arcade, got %s" % labels)
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
		failures.append("W/layer labels should use config-owned label.w_layer")
	if ReplayVisuals.event_marker_material("tron").albedo_color != manager.get_color(ShellStyleRolesScript.DIAGNOSTIC_BOUNDS):
		failures.append("event markers should use diagnostic.bounds")
	if ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACCENT_SOFT, "tron") != manager.get_color(ShellStyleRolesScript.ACCENT_SOFT):
		failures.append("soft accent should use config-owned accent.soft")
	return failures
