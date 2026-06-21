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
	var style := StyleBoxFlat.new()
	style.bg_color = style_manager.get_color(
		ShellStyleRolesScript.BACKGROUND_ELEVATED if elevated else ShellStyleRolesScript.BACKGROUND_PANEL
	)
	style.border_color = style_manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY)
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(12)
	panel.add_theme_stylebox_override("panel", style)
	panel.set_meta("shell_style_theme_id", style_manager.get_theme_id())


func _apply_control(control: Control, style_manager) -> void:
	control.set_meta("shell_style_theme_id", style_manager.get_theme_id())
	if control is PanelContainer:
		var elevated := control.name == "GameArea" or control.name.find("Row") >= 0
		apply_panel(control, style_manager, elevated)
	if control is Label:
		_apply_label(control as Label, style_manager)
	elif control is Button:
		_apply_button(control as Button, style_manager)
	elif control is OptionButton:
		_apply_button(control as OptionButton, style_manager)
	elif control is CheckBox:
		_apply_checkbox(control as CheckBox, style_manager)
	elif control is HSlider:
		_apply_slider(control as HSlider, style_manager)


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
	if label.name.find("Hint") >= 0 or label.text.find("Hint") >= 0:
		role = ShellStyleRolesScript.LABEL_HINT
	label.add_theme_color_override("font_color", style_manager.get_color(role))


func _apply_button(button: Button, style_manager) -> void:
	button.add_theme_color_override("font_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	button.add_theme_color_override("font_hover_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	button.add_theme_color_override("font_pressed_color", style_manager.get_color(ShellStyleRolesScript.TEXT_INVERSE))
	button.add_theme_stylebox_override("normal", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.GRID_MINOR))
	button.add_theme_stylebox_override("hover", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.ACCENT_FOCUS))
	button.add_theme_stylebox_override("focus", _button_box(style_manager, ShellStyleRolesScript.BACKGROUND_ELEVATED, ShellStyleRolesScript.ACCENT_FOCUS))
	button.add_theme_stylebox_override("pressed", _button_box(style_manager, ShellStyleRolesScript.ACCENT_PRIMARY, ShellStyleRolesScript.ACCENT_PRIMARY))


func _apply_checkbox(checkbox: CheckBox, style_manager) -> void:
	checkbox.add_theme_color_override("font_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))
	checkbox.add_theme_color_override("font_hover_color", style_manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY))


func _apply_slider(slider: HSlider, style_manager) -> void:
	slider.add_theme_color_override("guide_color", style_manager.get_color(ShellStyleRolesScript.GRID_MINOR))
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


func _button_box(style_manager, background_role: String, border_role: String) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = style_manager.get_color(background_role)
	style.border_color = style_manager.get_color(border_role)
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	style.set_content_margin_all(8)
	return style
