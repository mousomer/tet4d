extends RefCounted

const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["settings panel generation test requires SceneTree"]
	var panel: Control = SettingsPanelScript.new()
	tree.root.add_child(panel)
	panel.size = Vector2(420, 620)
	await tree.process_frame
	_assert_node_type(failures, panel.get_node_or_null("SettingsScroll"), ScrollContainer, "settings panel should use ScrollContainer")
	var content: Node = panel.get_node_or_null("SettingsScroll/SettingsContent")
	_assert_node_type(failures, content, VBoxContainer, "settings panel should use VBoxContainer content")
	if content != null:
		_assert_node_type(failures, content.get_node_or_null("SettingsIntro/SettingsTitle"), Label, "settings panel should include title")
		_assert_node_type(failures, content.get_node_or_null("SettingsIntro/SettingsSubtitle"), Label, "settings panel should include shell-only subtitle")
		_assert_section(failures, content, "Replay")
		_assert_section(failures, content, "Display")
		_assert_section(failures, content, "Theme")
		_assert_section(failures, content, "Diagnostics")
		_assert_section(failures, content, "Controls Help")
		_assert_row(failures, content, "replay.playback_speed")
		_assert_row(failures, content, "replay.loop_enabled")
		_assert_row(failures, content, "display.show_w_labels")
		_assert_row(failures, content, "display.projection_strength")
		_assert_row(failures, content, "theme.name")
		_assert_row(failures, content, "diagnostics.show_layout_bounds")
		_assert_row(failures, content, "controls_help.show_keyboard_hints")
	_assert_control_type(failures, panel, "replay.loop_enabled", CheckBox, "bool should produce checkbox")
	_assert_control_type(failures, panel, "display.show_w_labels", CheckBox, "bool display setting should produce checkbox")
	_assert_control_type(failures, panel, "replay.playback_speed", HBoxContainer, "float should produce slider group")
	_assert_slider_value_label(failures, panel, "replay.playback_speed")
	_assert_control_type(failures, panel, "display.projection_strength", HBoxContainer, "float display setting should produce slider group")
	_assert_slider_value_label(failures, panel, "display.projection_strength")
	_assert_control_type(failures, panel, "theme.name", OptionButton, "enum should produce dropdown")
	_assert_dropdown_options(failures, panel, "theme.name", ["diagnostic", "tron", "plain"])
	_assert_wrapped_setting_label(failures, content, "display.projection_strength")
	panel.queue_free()
	await tree.process_frame
	return failures


func _assert_node_type(failures: Array, node: Node, expected_type, label: String) -> void:
	if node == null:
		failures.append("%s: missing node" % label)
	elif not is_instance_of(node, expected_type):
		failures.append("%s: expected %s, got %s" % [label, expected_type, node.get_class()])


func _assert_section(failures: Array, content: Node, label_text: String) -> void:
	var node := content.get_node_or_null("SectionHeader__%s" % label_text.replace(" ", "_"))
	if node == null:
		failures.append("missing settings section %s" % label_text)


func _assert_row(failures: Array, content: Node, setting_id: String) -> void:
	var node := content.get_node_or_null("SettingRow__%s" % setting_id.replace(".", "__"))
	if node == null:
		failures.append("missing settings row %s" % setting_id)


func _assert_control_type(failures: Array, panel, setting_id: String, expected_type, label: String) -> void:
	var control: Control = panel.generated_control(setting_id)
	if control == null:
		failures.append("%s: missing generated control for %s" % [label, setting_id])
	elif not is_instance_of(control, expected_type):
		failures.append("%s: expected %s, got %s" % [label, expected_type, control.get_class()])


func _assert_slider_value_label(failures: Array, panel, setting_id: String) -> void:
	var group: Control = panel.generated_control(setting_id)
	if group == null:
		return
	if group.get_node_or_null("Slider") == null:
		failures.append("%s should include Slider" % setting_id)
	if group.get_node_or_null("ValueLabel") == null:
		failures.append("%s should include numeric value label" % setting_id)


func _assert_dropdown_options(failures: Array, panel, setting_id: String, expected_values: Array) -> void:
	var control := panel.generated_control(setting_id) as OptionButton
	if control == null:
		return
	var actual_values: Array = []
	for index in range(control.item_count):
		actual_values.append(str(control.get_item_metadata(index)))
	if actual_values != expected_values:
		failures.append("%s dropdown values: expected %s, got %s" % [setting_id, expected_values, actual_values])


func _assert_wrapped_setting_label(failures: Array, content: Node, setting_id: String) -> void:
	if content == null:
		return
	var row := content.get_node_or_null("SettingRow__%s" % setting_id.replace(".", "__"))
	if row == null:
		return
	var text_box := row.get_child(0) as VBoxContainer
	if text_box == null or text_box.get_child_count() == 0:
		failures.append("%s should keep label and description in a text column" % setting_id)
		return
	var label := text_box.get_child(0) as Label
	if label == null:
		failures.append("%s should include a label" % setting_id)
	elif label.autowrap_mode == TextServer.AUTOWRAP_OFF:
		failures.append("%s label should wrap instead of clipping" % setting_id)
