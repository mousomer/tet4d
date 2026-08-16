extends RefCounted

class_name SetupFieldRegistry

const SetupFieldSpecScript = preload("res://scripts/ui/game_setup/setup_field_spec.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

const ALL_MODES := ["live_2d", "live_3d", "live_4d"]
const CONTROL_FRAME_MODES := ["live_3d", "live_4d"]
const CONTROL_FRAME_OPTIONS := [
	{"value": "relative", "label": "Relative"},
	{"value": "absolute", "label": "Absolute"},
]

# Axis fields are generated per mode from the board-extent contract and are
# inserted directly after this field, matching the rendered panel order.
const AXIS_ANCHOR_FIELD := "board_preset"

const INVARIANT_FIELDS := [
	{
		"id": "board_preset",
		"label": "Preset Shortcut",
		"description": "Named board shortcut; editing dimensions derives Custom.",
		"category": "game_definition",
		"disclosure": "ordinary",
		"identity": "session_identity",
		"session_key": "board_preset_id",
		"value_type": "enum",
		"control_type": "selector",
		"modes": ALL_MODES,
	},
	{
		"id": "piece_set",
		"label": "Piece Set",
		"description": "Piece family the session generates.",
		"category": "game_definition",
		"disclosure": "ordinary",
		"identity": "session_identity",
		"session_key": "piece_set_id",
		"value_type": "enum",
		"control_type": "selector",
		"modes": ALL_MODES,
	},
	{
		"id": "random_mode",
		"label": "Randomness",
		"description": "Whether the piece sequence is reproducible.",
		"category": "game_definition",
		"disclosure": "ordinary",
		"identity": "session_identity",
		"session_key": "random_mode",
		"value_type": "enum",
		"control_type": "selector",
		"modes": ALL_MODES,
	},
	{
		"id": "seed",
		"label": "Seed",
		"description": "Reproducible sequence seed; meaningful only under fixed-seed randomness.",
		"category": "contextual_game_definition",
		"disclosure": "contextual",
		"identity": "session_identity",
		"session_key": "seed",
		"value_type": "int",
		"control_type": "numeric_entry",
		"modes": ALL_MODES,
		"min": GameSetupSpecScript.MIN_SEED,
		"max": GameSetupSpecScript.MAX_SEED,
		"visible_when": {"field": "random_mode", "equals": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED},
	},
	{
		"id": "initial_speed_level",
		"label": "Starting Speed",
		"description": "Starting gravity cadence.",
		"category": "game_definition",
		"disclosure": "ordinary",
		"identity": "session_identity",
		"session_key": "initial_speed_level",
		"value_type": "int",
		"control_type": "selector",
		"modes": ALL_MODES,
		"min": GameSetupSpecScript.MIN_SPEED_LEVEL,
		"max": GameSetupSpecScript.MAX_SPEED_LEVEL,
	},
	{
		"id": "translation_frame",
		"label": "Translation",
		"description": "Relative controls follow the current view; Absolute controls use canonical axes and planes.",
		"category": "advanced_gameplay_input",
		"disclosure": "secondary",
		"identity": "input_preference",
		"value_type": "enum",
		"control_type": "selector",
		"modes": CONTROL_FRAME_MODES,
		"options": CONTROL_FRAME_OPTIONS,
	},
	{
		"id": "rotation_frame",
		"label": "Rotation",
		"description": "Relative controls follow the current view; Absolute controls use canonical axes and planes.",
		"category": "advanced_gameplay_input",
		"disclosure": "secondary",
		"identity": "input_preference",
		"value_type": "enum",
		"control_type": "selector",
		"modes": CONTROL_FRAME_MODES,
		"options": CONTROL_FRAME_OPTIONS,
	},
]

const SESSION_ENVELOPE_KEYS := [
	"schema_version",
	"contract_version",
	"mode",
	"topology_profile",
]


static func field_data_for_mode(mode: String) -> Array:
	var fields: Array = []
	for declared in INVARIANT_FIELDS:
		var data: Dictionary = declared as Dictionary
		if not (data.get("modes", []) as Array).has(mode):
			continue
		fields.append(_with_resolved_options(data, mode))
		if str(data.get("id", "")) == AXIS_ANCHOR_FIELD:
			fields.append_array(_axis_field_data(mode))
	return fields


static func specs_for_mode(mode: String) -> Array:
	var specs: Array = []
	for spec_data in field_data_for_mode(mode):
		specs.append(SetupFieldSpecScript.new(spec_data))
	return specs


static func visible_specs_for(mode: String, entry: Dictionary) -> Array:
	var specs: Array = []
	for spec in specs_for_mode(mode):
		if spec.is_visible_for(mode, entry):
			specs.append(spec)
	return specs


static func specs_for_disclosure(mode: String, disclosure: String) -> Array:
	var specs: Array = []
	for spec in specs_for_mode(mode):
		if spec.disclosure() == disclosure:
			specs.append(spec)
	return specs


static func specs_for_category(mode: String, category: String) -> Array:
	var specs: Array = []
	for spec in specs_for_mode(mode):
		if spec.category() == category:
			specs.append(spec)
	return specs


static func session_identity_keys() -> Array:
	var keys: Array = []
	for mode in GameSetupSpecScript.modes():
		for spec in specs_for_mode(mode):
			var key: String = spec.session_key()
			if not key.is_empty() and not keys.has(key):
				keys.append(key)
	keys.sort()
	return keys


static func validate() -> Array: # tet4d-semantic-boundary: allow diagnostic-presentation
	var failures: Array = []
	var known_modes: Array = GameSetupSpecScript.modes()
	for declared in INVARIANT_FIELDS:
		var declared_modes: Array = (declared as Dictionary).get("modes", []) as Array
		for mode in declared_modes:
			if not known_modes.has(str(mode)):
				failures.append("%s: unknown declared mode %s" % [str((declared as Dictionary).get("id", "")), str(mode)])
	for mode in known_modes:
		var seen_ids: Array = []
		for spec_data in field_data_for_mode(mode):
			var field_id := str((spec_data as Dictionary).get("id", ""))
			if seen_ids.has(field_id):
				failures.append("%s: duplicate setup field id in mode %s" % [field_id, mode])
			seen_ids.append(field_id)
			failures.append_array(SetupFieldSpecScript.validate(spec_data, known_modes))
	return failures


static func _with_resolved_options(data: Dictionary, mode: String) -> Dictionary:
	var resolved := data.duplicate(true)
	match str(data.get("id", "")):
		"board_preset":
			resolved["options"] = _preset_options(mode)
		"piece_set":
			resolved["options"] = _piece_set_options(mode)
		"random_mode":
			resolved["options"] = _random_mode_options()
	return resolved


static func _axis_field_data(mode: String) -> Array:
	var fields: Array = []
	var ranges: Array = GameSetupSpecScript.board_axis_ranges(mode)
	var axis_order: Array = (GameSetupSpecScript.BoardExtentContractScript.mode_spec(mode).get("axis_order", []) as Array)
	for axis_index in range(ranges.size()):
		var axis_range: Array = ranges[axis_index] as Array
		var axis_name := str(axis_order[axis_index]) if axis_index < axis_order.size() else str(axis_index)
		fields.append({
			"id": "board_axis_%d" % axis_index,
			"label": axis_name,
			"description": "Board extent along %s." % axis_name,
			"category": SetupFieldSpecScript.CATEGORY_GAME_DEFINITION,
			"disclosure": SetupFieldSpecScript.DISCLOSURE_ORDINARY,
			"identity": SetupFieldSpecScript.IDENTITY_SESSION,
			"session_key": "board_shape",
			"value_type": "shape_axis",
			"control_type": "stepper",
			"modes": [mode],
			"axis_index": axis_index,
			"min": int(axis_range[0]),
			"max": int(axis_range[1]),
		})
	return fields


static func _preset_options(mode: String) -> Array:
	var options: Array = []
	for spec in GameSetupSpecScript.presets_for_mode(mode):
		options.append({
			"value": str((spec as Dictionary).get("id", "")),
			"label": str((spec as Dictionary).get("label", "")),
		})
	options.append({"value": "", "label": "Custom"})
	return options


static func _piece_set_options(mode: String) -> Array:
	var options: Array = []
	for spec in GameSetupSpecScript.piece_sets_for_mode(mode):
		options.append({
			"value": str((spec as Dictionary).get("id", "")),
			"label": str((spec as Dictionary).get("label", "")),
		})
	return options


static func _random_mode_options() -> Array:
	var options: Array = []
	for spec in GameSetupSpecScript.random_modes():
		options.append({
			"value": str((spec as Dictionary).get("id", "")),
			"label": str((spec as Dictionary).get("label", "")),
		})
	return options
