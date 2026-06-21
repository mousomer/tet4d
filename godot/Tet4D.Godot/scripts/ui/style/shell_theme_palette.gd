extends RefCounted

class_name ShellThemePalette

const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")

var theme_id := ""
var _raw_values: Dictionary = {}
var _colors: Dictionary = {}


func _init(id: String = "", values: Dictionary = {}) -> void:
	theme_id = id
	_raw_values = values.duplicate()
	_parse_colors()


func get_color(role: String) -> Color:
	if _colors.has(role):
		return _colors.get(role)
	return _colors.get(ShellStyleRolesScript.TEXT_PRIMARY, Color.WHITE)


func has_role(role: String) -> bool:
	return _colors.has(role)


func validate() -> Array: # tet4d-semantic-boundary: allow diagnostic-presentation
	var failures: Array = []
	if theme_id == "":
		failures.append("palette id is empty")
	for role in ShellStyleRolesScript.required_color_roles():
		if not _raw_values.has(role):
			failures.append("%s missing role %s" % [theme_id, role])
		elif not _colors.has(role):
			failures.append("%s role %s did not parse as a color" % [theme_id, role])
	for role in _raw_values.keys():
		if not ShellStyleRolesScript.is_known_color_role(str(role)):
			failures.append("%s has unknown role %s" % [theme_id, role])
	return failures


func _parse_colors() -> void:
	_colors.clear()
	for role in _raw_values.keys():
		var hex := str(_raw_values.get(role, "")).strip_edges()
		if hex.begins_with("#"):
			hex = hex.substr(1)
		if hex.length() != 6 and hex.length() != 8:
			continue
		_colors[str(role)] = Color.html(hex)
