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
		_assert_color(failures, tron.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY), Color.html("#060A12"), "tron Blueprint background.primary")
		_assert_color(failures, tron.get_color(ShellStyleRolesScript.ACCENT_PRIMARY), Color.html("#35C7D8"), "tron Blueprint accent.primary")
		_assert_color(failures, tron.get_color(ShellStyleRolesScript.ACCENT_FOCUS), Color.html("#7DD3FC"), "tron Blueprint accent.focus")
		_assert_color(failures, tron.get_color(ShellStyleRolesScript.CELL_LOCKED), Color.html("#6D5BD0"), "tron Blueprint locked cell")
		_assert_color(failures, tron.get_color(ShellStyleRolesScript.LABEL_W_LAYER), Color.html("#78909C"), "tron muted W label")
		if _green_dominance(tron.get_color(ShellStyleRolesScript.ACCENT_FOCUS)) > 0.2:
			failures.append("tron keycap/focus accent should not read as bright green")
		if tron.get_color(ShellStyleRolesScript.LABEL_HINT).r > tron.get_color(ShellStyleRolesScript.LABEL_HINT).b:
			failures.append("tron hint/action text should not read as magenta-dominant")
	return failures


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_color(failures: Array, actual: Color, expected: Color, label: String) -> void:
	if absf(actual.r - expected.r) > 0.001 or absf(actual.g - expected.g) > 0.001 or absf(actual.b - expected.b) > 0.001 or absf(actual.a - expected.a) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _green_dominance(color: Color) -> float:
	return color.g - maxf(color.r, color.b)


func _brightness(color: Color) -> float:
	return (color.r + color.g + color.b) / 3.0
