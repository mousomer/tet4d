extends RefCounted

class_name ShellControlStyleApplier

const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func apply_to_tree(root: Control, style_manager) -> void:
	if root == null or style_manager == null:
		return
	_apply_control(root, style_manager)
	for child in root.get_children():
		if child is Control:
			apply_to_tree(child as Control, style_manager)


func apply_panel(panel: Control, style_manager, elevated: bool = false) -> void:
	if panel == null or style_manager == null:
		return
	var background_role := ShellStyleRolesScript.BACKGROUND_ELEVATED if elevated else ShellStyleRolesScript.BACKGROUND_PANEL
	var border_role := ShellStyleRolesScript.ACCENT_PRIMARY
	if panel.name == "GameArea" or panel.theme_type_variation == "ViewportFrame":
		background_role = ShellStyleRolesScript.BACKGROUND_BOARD
		border_role = ShellStyleRolesScript.GRID_MAJOR
	elif panel.name.find("ControlModeCard") >= 0:
		background_role = ShellStyleRolesScript.BACKGROUND_ELEVATED
		border_role = ShellStyleRolesScript.ACCENT_PRIMARY
	elif panel.name.find("SettingRow") >= 0:
		background_role = ShellStyleRolesScript.BACKGROUND_ELEVATED
		border_role = ShellStyleRolesScript.GRID_MINOR
	elif _is_inspector_panel(panel):
		background_role = ShellStyleRolesScript.BACKGROUND_PANEL
		border_role = ShellStyleRolesScript.GRID_MINOR
	var style := _panel_box(style_manager, background_role, border_role, 12)
	panel.add_theme_stylebox_override("panel", style)
	panel.set_meta("shell_style_theme_id", style_manager.get_theme_id())


func _apply_control(control: Control, style_manager) -> void:
	control.set_meta("shell_style_theme_id", style_manager.get_theme_id())
	if control is PanelContainer:
		var elevated := _is_elevated_panel(control)
		apply_panel(control, style_manager, elevated)
	if control is Label:
		_apply_label(control as Label, style_manager)
	elif control is CheckBox:
		_apply_checkbox(control as CheckBox, style_manager)
	elif control is OptionButton:
		_apply_button(control as OptionButton, style_manager)
	elif control is Button:
		_apply_button(control as Button, style_manager)
	elif control is HSlider:
		_apply_slider(control as HSlider, style_manager)
	elif control is LineEdit:
		_apply_line_edit(control as LineEdit, style_manager)


func _apply_label(label: Label, style_manager) -> void:
	var role := ShellStyleRolesScript.TEXT_PRIMARY
	match label.theme_type_variation:
		"AccentLabel":
			role = ShellStyleRolesScript.ACCENT_PRIMARY
		"SecondaryLabel":
			role = ShellStyleRolesScript.TEXT_SECONDARY
		"DimLabel":
			role = ShellStyleRolesScript.TEXT_MUTED
		"WarningLabel":
			role = ShellStyleRolesScript.STATE_WARNING
		"StatusAccentLabel":
			role = ShellStyleRolesScript.ACCENT_PRIMARY
		"StatusErrorLabel":
			role = ShellStyleRolesScript.STATE_ERROR
		"CockpitValueLabel":
			role = ShellStyleRolesScript.DIAGNOSTIC_METADATA
		"WLayerLabel":
			role = ShellStyleRolesScript.LABEL_W_LAYER
		"KeycapLabel":
			role = ShellStyleRolesScript.TEXT_PRIMARY
	if label.name.find("ControlHintSectionHeader") >= 0:
		role = ShellStyleRolesScript.HINT_SECTION
	elif label.name.find("ControlHintKeycap") >= 0:
		role = ShellStyleRolesScript.HINT_KEYCAP_TEXT
	elif label.name.find("ControlHintAction") >= 0:
		role = ShellStyleRolesScript.HINT_ACTION
	elif label.name.find("ControlHintNote") >= 0:
		role = ShellStyleRolesScript.HINT_NOTE
	elif label.name.find("ControlHintWarning") >= 0:
		role = ShellStyleRolesScript.HINT_ERROR
	elif label.name.find("Hint") >= 0:
		role = ShellStyleRolesScript.LABEL_HINT
	elif label.name.find("ValueLabel") >= 0 or label.name.find("StateValue") >= 0:
		role = ShellStyleRolesScript.DIAGNOSTIC_METADATA
	elif label.name.find("WLayer") >= 0 or label.name.find("Slice") >= 0:
		role = ShellStyleRolesScript.LABEL_W_LAYER
	label.add_theme_color_override("font_color", style_manager.get_color(role))
	if label.theme_type_variation == "KeycapLabel":
		label.add_theme_stylebox_override("normal", _keycap_box(style_manager))
	elif label.name.find("StatusBadge") >= 0:
		var badge_border := ShellStyleRolesScript.STATE_ERROR if label.theme_type_variation == "StatusErrorLabel" else ShellStyleRolesScript.ACCENT_PRIMARY
		label.add_theme_stylebox_override("normal", _badge_box(style_manager, badge_border))


func _apply_button(button: Button, style_manager) -> void:
	button.add_theme_color_override("font_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	button.add_theme_color_override("font_hover_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	button.add_theme_color_override("font_pressed_color", style_manager.get_color(ShellStyleRolesScript.TEXT_INVERSE))
	var margin := 8
	button.add_theme_stylebox_override("normal", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.GRID_MINOR, margin))
	button.add_theme_stylebox_override("hover", _button_box(style_manager, ShellStyleRolesScript.ACCENT_SOFT, ShellStyleRolesScript.ACCENT_FOCUS, margin))
	button.add_theme_stylebox_override("focus", _button_box(style_manager, ShellStyleRolesScript.ACCENT_SOFT, ShellStyleRolesScript.ACCENT_FOCUS, margin))
	button.add_theme_stylebox_override("pressed", _button_box(style_manager, ShellStyleRolesScript.ACCENT_PRIMARY, ShellStyleRolesScript.ACCENT_PRIMARY, margin))


func _apply_checkbox(checkbox: CheckBox, style_manager) -> void:
	checkbox.add_theme_color_override("font_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	checkbox.add_theme_color_override("font_hover_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	checkbox.add_theme_color_override("font_pressed_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	checkbox.add_theme_stylebox_override("normal", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_PANEL, ShellStyleRolesScript.GRID_MINOR))
	checkbox.add_theme_stylebox_override("hover", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.ACCENT_FOCUS))
	checkbox.add_theme_stylebox_override("focus", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.ACCENT_FOCUS))
	checkbox.add_theme_stylebox_override("pressed", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.ACCENT_PRIMARY))
	checkbox.add_theme_stylebox_override("unchecked", _checkbox_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, ShellStyleRolesScript.GRID_MINOR))
	checkbox.add_theme_stylebox_override("unchecked_hover", _checkbox_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, ShellStyleRolesScript.ACCENT_FOCUS))
	checkbox.add_theme_stylebox_override("checked", _checkbox_box(style_manager, ShellStyleRolesScript.ACCENT_PRIMARY, ShellStyleRolesScript.ACCENT_FOCUS))
	checkbox.add_theme_stylebox_override("checked_hover", _checkbox_box(style_manager, ShellStyleRolesScript.ACCENT_PRIMARY, ShellStyleRolesScript.ACCENT_FOCUS))


func _apply_slider(slider: HSlider, style_manager) -> void:
	slider.add_theme_color_override("guide_color", style_manager.get_color(ShellStyleRolesScript.GRID_MINOR))
	var track := StyleBoxFlat.new()
	track.bg_color = style_manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD)
	track.border_color = style_manager.get_color(ShellStyleRolesScript.GRID_MINOR)
	track.set_border_width_all(1)
	track.set_corner_radius_all(4)
	slider.add_theme_stylebox_override("grabber_area", track)
	slider.add_theme_stylebox_override("grabber_area_highlight", track)
	var fill := StyleBoxFlat.new()
	fill.bg_color = style_manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY)
	fill.set_corner_radius_all(4)
	slider.add_theme_stylebox_override("slider", fill)
	var grabber := StyleBoxFlat.new()
	grabber.bg_color = style_manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS)
	grabber.border_color = style_manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY)
	grabber.set_border_width_all(1)
	grabber.set_corner_radius_all(6)
	slider.add_theme_stylebox_override("grabber", grabber)
	slider.add_theme_stylebox_override("grabber_highlight", grabber)


func _apply_line_edit(line_edit: LineEdit, style_manager) -> void:
	line_edit.add_theme_color_override("font_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	line_edit.add_theme_color_override("font_placeholder_color", style_manager.get_color(ShellStyleRolesScript.TEXT_MUTED))
	line_edit.add_theme_color_override("caret_color", style_manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS))
	line_edit.add_theme_stylebox_override("normal", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, ShellStyleRolesScript.GRID_MINOR))
	line_edit.add_theme_stylebox_override("focus", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, ShellStyleRolesScript.ACCENT_FOCUS))


func _flat_box(style_manager, background_role: String, border_role: String, radius: int = 4, content_margin: int = 8) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = style_manager.get_color(background_role)
	style.border_color = style_manager.get_color(border_role)
	style.set_border_width_all(1)
	style.set_corner_radius_all(radius)
	style.set_content_margin_all(content_margin)
	return style


func _button_box(style_manager, background_role: String, border_role: String, content_margin: int = 8) -> StyleBoxFlat:
	return _flat_box(style_manager, background_role, border_role, 4, content_margin)


func _keycap_box(style_manager) -> StyleBoxFlat:
	return _flat_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, ShellStyleRolesScript.HINT_KEYCAP_BORDER, 3, 4)


func _badge_box(style_manager, border_role: String) -> StyleBoxFlat:
	return _flat_box(style_manager, ShellStyleRolesScript.BACKGROUND_BOARD, border_role, 4, 5)


func _panel_box(style_manager, background_role: String, border_role: String, content_margin: int) -> StyleBoxFlat:
	return _flat_box(style_manager, background_role, border_role, 4, content_margin)


func _checkbox_box(style_manager, background_role: String, border_role: String) -> StyleBoxFlat:
	return _flat_box(style_manager, background_role, border_role, 3, 4)


func _is_inspector_panel(panel: Control) -> bool:
	return panel.name.find("Inspector") >= 0 or panel.name.find("Settings") >= 0 or panel.name.find("Diagnostics") >= 0 or panel.name.find("Event") >= 0


func _is_elevated_panel(panel: Control) -> bool:
	return [
		"TopStatusPanel",
		"TopReplaySummaryPanel",
		"AuthorityPanel",
		"BottomReplayControls",
	].has(panel.name)
