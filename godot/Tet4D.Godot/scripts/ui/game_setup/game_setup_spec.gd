extends RefCounted

class_name GameSetupSpec

const MODE_2D := "live_2d"
const MODE_3D := "live_3d"
const MODE_4D := "live_4d"
const STANDARD_PRESET_ID := "standard"

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
