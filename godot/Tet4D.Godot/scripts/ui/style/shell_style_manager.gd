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
var _high_contrast := false


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
	var color: Color = palette.get_color(role)
	return _high_contrast_color(role, color, palette) if _high_contrast else color


func set_contrast_mode(mode: String) -> void:
	var high_contrast := mode == "high"
	if high_contrast == _high_contrast:
		return
	_high_contrast = high_contrast
	theme_changed.emit(_active_theme_id)


func contrast_mode() -> String:
	return "high" if _high_contrast else "standard"


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


func _high_contrast_color(role: String, color: Color, palette) -> Color:
	var background: Color = palette.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)
	var dark_background := background.get_luminance() < 0.5
	if role in [
		ShellStyleRolesScript.TEXT_PRIMARY,
		ShellStyleRolesScript.TEXT_SECONDARY,
		ShellStyleRolesScript.TEXT_MUTED,
		ShellStyleRolesScript.HINT_KEYCAP_TEXT,
		ShellStyleRolesScript.HINT_ACTION,
		ShellStyleRolesScript.HINT_NOTE,
		ShellStyleRolesScript.LABEL_HINT,
	]:
		return Color.WHITE if dark_background else Color.BLACK
	if role in [
		ShellStyleRolesScript.ACCENT_FOCUS,
		ShellStyleRolesScript.GRID_MAJOR,
		ShellStyleRolesScript.GRID_AXIS,
		ShellStyleRolesScript.HINT_KEYCAP_BORDER,
	]:
		return Color(1.0, 0.85, 0.1) if dark_background else Color(0.0, 0.12, 0.35)
	if role == ShellStyleRolesScript.GRID_MINOR:
		return Color(0.64, 0.7, 0.78) if dark_background else Color(0.28, 0.32, 0.38)
	return color
