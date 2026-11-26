extends RefCounted

class_name GraphicalLanguageConfig

# Reads the graphical-language tuning values from config/graphical_language.json.
# Code never carries its own copy of a value: a missing or invalid entry is
# reported loudly and yields NAN, and test_graphical_language_config.gd
# validates the shipped file against REQUIRED_NUMBERS and the other lists.

const CONFIG_PATH := "res://config/graphical_language.json"
const FACE_KEYS := ["base", "top", "front", "right", "left", "back", "bottom"]
# A gradient needs a start and an end stop.
const MIN_GRADIENT_STOPS := 2
const REQUIRED_NUMBERS := [
	"cockpit.inline_arrow.size",
	"cockpit.inline_arrow.span_factor",
	"cockpit.inline_arrow.line_width",
	"cockpit.compass_arrow_length",
	"cockpit.plane_glyph_size",
	"luminous.board.active.whiten",
	"luminous.board.active.cell_emission",
	"luminous.board.active.face_emission",
	"luminous.board.active.edge_emission",
	"luminous.board.halo.alpha",
	"luminous.board.halo.scale_cells",
	"luminous.board.halo.texture_size_px",
	"luminous.board.locked.alpha_scale",
	"luminous.board.seam.alpha",
	"luminous.board.seam.darken",
	"luminous.board.bevel.width_cells",
	"luminous.board.bevel.light_lerp_to_white",
	"luminous.board.bevel.dark_darken",
	"luminous.board.bevel.thickness_cells",
	"luminous.board.bevel.min_thickness",
	"luminous.board.ghost_form.fill_alpha",
	"luminous.board.ghost_form.outline_lighten",
	"luminous.board.ghost_form.outline_emission",
	"luminous.board.ghost_form.outline_alpha",
	"luminous.board.edges.emission",
	"luminous.board.edges.thickness_scale",
	"luminous.board.edges.render_priority",
	"luminous.shell.radius.keycap",
	"luminous.shell.radius.control",
	"luminous.shell.radius.panel",
	"luminous.shell.radius.emphasis",
	"luminous.shell.border_lift",
]
const REQUIRED_SHADE_TABLES := [
	"luminous.board.active.face_shades",
	"luminous.board.locked.face_shades",
]
# Paired arrays of equal length (gradient stops and their alphas).
const REQUIRED_NUMBER_LISTS := [
	["luminous.board.halo.gradient_offsets", "luminous.board.halo.gradient_alphas"],
]

static var _data = null


static func number(path: String) -> float:
	var found = _lookup(_config(), path)
	if typeof(found) not in [TYPE_FLOAT, TYPE_INT]:
		push_error("%s: %s is missing or not a number" % [CONFIG_PATH, path])
		return NAN
	return float(found)


static func integer(path: String) -> int:
	return int(number(path))


static func numbers(path: String) -> PackedFloat32Array:
	var found = _lookup(_config(), path)
	var result := PackedFloat32Array()
	if not (found is Array):
		push_error("%s: %s is missing or not a list" % [CONFIG_PATH, path])
		return result
	for entry in found:
		result.append(float(entry))
	return result


static func shades(path: String) -> Dictionary:
	var found = _lookup(_config(), path)
	if not (found is Dictionary):
		push_error("%s: %s is missing or not a face table" % [CONFIG_PATH, path])
		return {}
	return found


# Every failure in the given document (the shipped file when data is null).
static func validate(data = null) -> Array:
	var document = _config() if data == null else data
	var failures: Array = []
	if not (document is Dictionary) or (document as Dictionary).is_empty():
		return ["%s did not load as a JSON object" % CONFIG_PATH]
	for path in REQUIRED_NUMBERS:
		if typeof(_lookup(document, path)) not in [TYPE_FLOAT, TYPE_INT]:
			failures.append("%s must be a number" % path)
	for path in REQUIRED_SHADE_TABLES:
		var table = _lookup(document, path)
		if not (table is Dictionary):
			failures.append("%s must be a face table" % path)
			continue
		for face in FACE_KEYS:
			if typeof((table as Dictionary).get(face)) not in [TYPE_FLOAT, TYPE_INT]:
				failures.append("%s.%s must be a number" % [path, face])
	for pair in REQUIRED_NUMBER_LISTS:
		var first = _lookup(document, pair[0])
		var second = _lookup(document, pair[1])
		if not (first is Array) or not (second is Array) or (first as Array).size() != (second as Array).size() or (first as Array).size() < MIN_GRADIENT_STOPS:
			failures.append("%s and %s must be number lists of equal length, at least two" % pair)
	return failures


static func _config() -> Dictionary:
	if _data == null:
		_data = {}
		var text := FileAccess.get_file_as_string(CONFIG_PATH)
		var parsed = JSON.parse_string(text)
		if parsed is Dictionary:
			_data = parsed
		else:
			push_error("%s could not be read as a JSON object" % CONFIG_PATH)
	return _data


static func _lookup(document, path: String):
	var node = document
	for key in path.split("."):
		if not (node is Dictionary) or not (node as Dictionary).has(key):
			return null
		node = (node as Dictionary)[key]
	return node
