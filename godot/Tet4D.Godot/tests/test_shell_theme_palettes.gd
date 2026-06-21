extends RefCounted

const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	var manager = ShellStyleManagerScript.new()
	failures.append_array(manager.validate_all())
	_assert_equal(failures, manager.available_theme_ids(), ["diagnostic", "plain", "tron"], "theme ids")
	for theme_id in manager.available_theme_ids():
		var palette = manager.palette(theme_id)
		if palette == null:
			failures.append("%s palette missing" % theme_id)
			continue
		for role in ShellStyleRolesScript.required_color_roles():
			if not palette.has_role(role):
				failures.append("%s missing role %s" % [theme_id, role])
			var color: Color = palette.get_color(role)
			if color.a <= 0.0:
				failures.append("%s role %s should parse to a visible Color" % [theme_id, role])
	var diagnostic = manager.palette("diagnostic")
	var plain = manager.palette("plain")
	var tron = manager.palette("tron")
	if diagnostic != null and plain != null and tron != null:
		if _brightness(plain.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)) <= _brightness(diagnostic.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)):
			failures.append("plain background.primary should be lighter than diagnostic")
		if _brightness(plain.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)) <= _brightness(tron.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)):
			failures.append("plain background.primary should be lighter than tron")
		if tron.get_color(ShellStyleRolesScript.ACCENT_PRIMARY) == diagnostic.get_color(ShellStyleRolesScript.ACCENT_PRIMARY):
			failures.append("tron accent.primary should differ from diagnostic")
		if tron.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY) == diagnostic.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY):
			failures.append("tron should not be identical to diagnostic")
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _brightness(color: Color) -> float:
	return (color.r + color.g + color.b) / 3.0
