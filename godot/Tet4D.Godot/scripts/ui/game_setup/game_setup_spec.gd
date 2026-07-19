extends RefCounted

class_name GameSetupSpec

const MODE_2D := "live_2d"
const MODE_3D := "live_3d"
const MODE_4D := "live_4d"
const STANDARD_PRESET_ID := "standard"
const SCHEMA_VERSION := 2
const DEFAULT_SEED := 1337
const MIN_SEED := 0
const MAX_SEED := 999999999
const MIN_SPEED_LEVEL := 1
const MAX_SPEED_LEVEL := 10
const RANDOM_MODE_FIXED_SEED := "fixed_seed"
const RANDOM_MODE_TRUE_RANDOM := "true_random"

const SPECS := {
	MODE_2D: [
		{"id": "compact", "label": "Compact", "shape": [4, 6], "description": "Tight native practice board"},
		{"id": STANDARD_PRESET_ID, "label": "Standard", "shape": [6, 6], "description": "Accepted Godot live default"},
		{"id": "large", "label": "Large", "shape": [10, 20], "description": "Classic tall playfield"},
	],
	MODE_3D: [
		{"id": "compact", "label": "Compact", "shape": [4, 8, 4], "description": "Readable compact volume"},
		{"id": STANDARD_PRESET_ID, "label": "Standard", "shape": [6, 10, 6], "description": "Accepted Godot live default"},
		{"id": "large", "label": "Large", "shape": [8, 16, 8], "description": "Expanded 3D board"},
	],
	MODE_4D: [
		{"id": "compact", "label": "Compact", "shape": [4, 8, 3, 3], "description": "Three-layer introduction"},
		{"id": STANDARD_PRESET_ID, "label": "Standard", "shape": [5, 10, 4, 4], "description": "Accepted four-layer live default"},
		{"id": "wide_w", "label": "Wide W", "shape": [8, 16, 5, 8], "description": "Eight-layer adaptive matrix"},
	],
}

const PIECE_SETS := {
	MODE_2D: [
		{"id": "classic", "label": "Classic Tetrominoes", "description": "The standard seven four-cell pieces."},
	],
	MODE_3D: [
		{"id": "native_3d", "label": "True 3D", "description": "Polycubes that can extend through the third axis."},
		{"id": "embedded_2d", "label": "Embedded 2D", "description": "Familiar flat pieces placed into 3D space."},
	],
	MODE_4D: [
		{"id": "standard_4d_5", "label": "True 4D (5-cell)", "description": "Five-cell pieces that can extend through the fourth axis."},
		{"id": "embedded_3d", "label": "Embedded 3D", "description": "Three-dimensional pieces placed into 4D space."},
		{"id": "embedded_2d", "label": "Embedded 2D", "description": "Familiar flat pieces placed into 4D space."},
	],
}

const RANDOM_MODES := [
	{"id": RANDOM_MODE_FIXED_SEED, "label": "Fixed Seed", "description": "The same seed reproduces the same piece sequence."},
	{"id": RANDOM_MODE_TRUE_RANDOM, "label": "True Random", "description": "A new effective seed is generated when the game starts."},
]


static func modes() -> Array:
	return [MODE_2D, MODE_3D, MODE_4D]


static func presets_for_mode(mode: String) -> Array:
	return (SPECS.get(mode, []) as Array).duplicate(true)


static func preset(mode: String, preset_id: String) -> Dictionary:
	for candidate in SPECS.get(mode, []):
		if str(candidate.get("id", "")) == preset_id:
			return (candidate as Dictionary).duplicate(true)
	return {}


static func is_supported(mode: String, preset_id: String) -> bool:
	return not preset(mode, preset_id).is_empty()

static func piece_sets_for_mode(mode: String, preset_id: String = STANDARD_PRESET_ID) -> Array:
	if not is_supported(mode, preset_id):
		return []
	return (PIECE_SETS.get(mode, []) as Array).duplicate(true)


static func piece_set(mode: String, piece_set_id: String) -> Dictionary:
	for candidate in PIECE_SETS.get(mode, []):
		if str(candidate.get("id", "")) == piece_set_id:
			return (candidate as Dictionary).duplicate(true)
	return {}


static func default_piece_set_id(mode: String) -> String:
	var options: Array = PIECE_SETS.get(mode, [])
	return str(options[0].get("id", "")) if not options.is_empty() else ""


static func is_piece_set_supported(mode: String, preset_id: String, piece_set_id: String) -> bool:
	if not is_supported(mode, preset_id):
		return false
	for candidate in piece_sets_for_mode(mode, preset_id):
		if str(candidate.get("id", "")) == piece_set_id:
			return true
	return false


static func random_modes() -> Array:
	return RANDOM_MODES.duplicate(true)


static func is_random_mode_supported(random_mode: String) -> bool:
	return random_mode == RANDOM_MODE_FIXED_SEED or random_mode == RANDOM_MODE_TRUE_RANDOM


static func is_valid_seed(value) -> bool:
	if typeof(value) == TYPE_FLOAT and (not is_finite(float(value)) or floor(float(value)) != float(value)):
		return false
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and int(value) >= MIN_SEED and int(value) <= MAX_SEED


static func is_valid_speed(value) -> bool:
	if typeof(value) == TYPE_FLOAT and (not is_finite(float(value)) or floor(float(value)) != float(value)):
		return false
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and int(value) >= MIN_SPEED_LEVEL and int(value) <= MAX_SPEED_LEVEL


static func speed_levels() -> Array:
	var result := []
	for value in range(MIN_SPEED_LEVEL, MAX_SPEED_LEVEL + 1):
		result.append(value)
	return result


static func piece_set_label(mode: String, piece_set_id: String) -> String:
	var resolved_id := piece_set_id if not piece_set_id.is_empty() else default_piece_set_id(mode)
	var spec := piece_set(mode, resolved_id)
	return str(spec.get("label", resolved_id))


static func mode_label(mode: String) -> String:
	match mode:
		MODE_2D:
			return "Play 2D"
		MODE_3D:
			return "Play 3D"
		MODE_4D:
			return "Play 4D"
		_:
			return "Play"


static func format_shape(shape: Array) -> String:
	var parts: Array = []
	for value in shape:
		parts.append(str(int(value)))
	return " × ".join(parts)
