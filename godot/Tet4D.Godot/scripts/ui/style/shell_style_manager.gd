extends RefCounted

class_name ShellStyleManager

const PaletteScript = preload("res://scripts/ui/style/shell_theme_palette.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")

signal theme_changed(theme_id: String)

const PALETTE_PATH := "res://config/shell_theme_palettes.json"
const DEFAULT_THEME_ID := "tron"
const REQUIRED_THEME_IDS := ["diagnostic", "plain", "tron"]

var _palettes: Dictionary = {}
var _active_theme_id := DEFAULT_THEME_ID


func _init() -> void:
	load_palettes(PALETTE_PATH)


func load_palettes(path: String) -> void:
	_palettes.clear()
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Failed to open shell theme palette file: %s" % path)
		return
	var parsed = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Shell theme palette file must contain a JSON object: %s" % path)
		return
	var themes: Dictionary = parsed.get("themes", {})
	for theme_id in themes.keys():
		var values = themes.get(theme_id)
		if typeof(values) == TYPE_DICTIONARY:
			_palettes[str(theme_id)] = PaletteScript.new(str(theme_id), values)
	if not _palettes.has(_active_theme_id):
		_active_theme_id = DEFAULT_THEME_ID if _palettes.has(DEFAULT_THEME_ID) else _first_available_theme()


func set_theme(theme_id: String) -> void:
	var normalized := str(theme_id)
	var next_theme := normalized if _palettes.has(normalized) else DEFAULT_THEME_ID
	if not _palettes.has(next_theme):
		next_theme = _first_available_theme()
	if next_theme == _active_theme_id:
		return
	_active_theme_id = next_theme
	theme_changed.emit(_active_theme_id)


func get_theme_id() -> String:
	return _active_theme_id


func get_color(role: String) -> Color:
	var palette = _palettes.get(_active_theme_id)
	if palette == null:
		return Color.WHITE
	return palette.get_color(role)


func has_role(role: String) -> bool:
	var palette = _palettes.get(_active_theme_id)
	return palette != null and palette.has_role(role)


func available_theme_ids() -> Array:
	var ids: Array = []
	for theme_id in REQUIRED_THEME_IDS:
		if _palettes.has(theme_id):
			ids.append(theme_id)
	return ids


func palette(theme_id: String):
	return _palettes.get(theme_id)


func validate_all() -> Array: # tet4d-semantic-boundary: allow diagnostic-presentation
	var failures: Array = []
	for theme_id in REQUIRED_THEME_IDS:
		if not _palettes.has(theme_id):
			failures.append("missing theme %s" % theme_id)
	for theme_id in _palettes.keys():
		if not REQUIRED_THEME_IDS.has(str(theme_id)):
			failures.append("unknown theme %s" % theme_id)
		var palette = _palettes.get(theme_id)
		if palette != null:
			failures.append_array(palette.validate())
		else:
			failures.append("%s did not load as a palette" % theme_id)
	return failures


func required_color_roles() -> Array:
	return ShellStyleRolesScript.required_color_roles()


func _first_available_theme() -> String:
	for theme_id in REQUIRED_THEME_IDS:
		if _palettes.has(theme_id):
			return theme_id
	return ""
