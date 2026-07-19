extends RefCounted

class_name GameSetupModel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

var current_mode := GameSetupSpecScript.MODE_2D
var _selected := {}


func _init() -> void:
	for mode in GameSetupSpecScript.modes():
		_selected[mode] = _default_entry(mode)


func set_mode(mode: String) -> bool:
	if not GameSetupSpecScript.modes().has(mode):
		return false
	current_mode = mode
	return true


func select_preset(preset_id: String) -> bool:
	if not GameSetupSpecScript.is_supported(current_mode, preset_id):
		return false
	var entry := _entry(current_mode)
	entry["board_preset_id"] = preset_id
	if not GameSetupSpecScript.is_piece_set_supported(current_mode, preset_id, str(entry.get("piece_set_id", ""))):
		entry["piece_set_id"] = GameSetupSpecScript.default_piece_set_id(current_mode)
	_selected[current_mode] = entry
	return true


func selected_preset_id(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_entry(target_mode).get("board_preset_id", GameSetupSpecScript.STANDARD_PRESET_ID))
	return candidate if GameSetupSpecScript.is_supported(target_mode, candidate) else GameSetupSpecScript.STANDARD_PRESET_ID


func selected_spec() -> Dictionary:
	return GameSetupSpecScript.preset(current_mode, selected_preset_id())


func selected_shape() -> Array:
	return (selected_spec().get("shape", []) as Array).duplicate()

func selected_piece_set_id(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_entry(target_mode).get("piece_set_id", GameSetupSpecScript.default_piece_set_id(target_mode)))
	return candidate if GameSetupSpecScript.is_piece_set_supported(target_mode, selected_preset_id(target_mode), candidate) else GameSetupSpecScript.default_piece_set_id(target_mode)


func select_piece_set(piece_set_id: String) -> bool:
	if not GameSetupSpecScript.is_piece_set_supported(current_mode, selected_preset_id(), piece_set_id):
		return false
	var entry := _entry(current_mode)
	entry["piece_set_id"] = piece_set_id
	_selected[current_mode] = entry
	return true


func selected_random_mode(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_entry(target_mode).get("random_mode", GameSetupSpecScript.RANDOM_MODE_FIXED_SEED))
	return candidate if GameSetupSpecScript.is_random_mode_supported(candidate) else GameSetupSpecScript.RANDOM_MODE_FIXED_SEED


func select_random_mode(random_mode: String) -> bool:
	if not GameSetupSpecScript.is_random_mode_supported(random_mode):
		return false
	var entry := _entry(current_mode)
	entry["random_mode"] = random_mode
	_selected[current_mode] = entry
	return true


func selected_seed(mode: String = "") -> int:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate = _entry(target_mode).get("seed", GameSetupSpecScript.DEFAULT_SEED)
	return int(candidate) if GameSetupSpecScript.is_valid_seed(candidate) else GameSetupSpecScript.DEFAULT_SEED


func select_seed(seed) -> bool:
	if not GameSetupSpecScript.is_valid_seed(seed):
		return false
	var entry := _entry(current_mode)
	entry["seed"] = int(seed)
	_selected[current_mode] = entry
	return true


func selected_speed_level(mode: String = "") -> int:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate = _entry(target_mode).get("initial_speed_level", GameSetupSpecScript.MIN_SPEED_LEVEL)
	return int(candidate) if GameSetupSpecScript.is_valid_speed(candidate) else GameSetupSpecScript.MIN_SPEED_LEVEL


func select_speed_level(speed_level) -> bool:
	if not GameSetupSpecScript.is_valid_speed(speed_level):
		return false
	var entry := _entry(current_mode)
	entry["initial_speed_level"] = int(speed_level)
	_selected[current_mode] = entry
	return true


func reset_to_standard(mode: String = "") -> void:
	var target_mode := current_mode if mode.is_empty() else mode
	if GameSetupSpecScript.modes().has(target_mode):
		_selected[target_mode] = _default_entry(target_mode)


func apply_last_selected(values: Dictionary) -> void:
	for mode in GameSetupSpecScript.modes():
		var value = values.get(mode, {})
		if typeof(value) == TYPE_STRING:
			value = {"board_preset_id": str(value)}
		_selected[mode] = _validated_entry(mode, value if value is Dictionary else {})


func canonical_snapshot() -> Dictionary:
	var last_selected := {}
	for mode in GameSetupSpecScript.modes():
		last_selected[mode] = _validated_entry(mode, _entry(mode))
	var result := canonical_session_setup()
	result["last_selected"] = last_selected
	return result


func canonical_session_setup() -> Dictionary:
	return {
		"schema_version": GameSetupSpecScript.SCHEMA_VERSION,
		"mode": current_mode,
		"board_preset_id": selected_preset_id(),
		"board_shape": selected_shape(),
		"piece_set_id": selected_piece_set_id(),
		"random_mode": selected_random_mode(),
		"seed": selected_seed(),
		"initial_speed_level": selected_speed_level(),
	}


# tet4d-semantic-boundary: allow adapter-routing
func is_current_valid() -> bool:
	return (
		GameSetupSpecScript.is_supported(current_mode, selected_preset_id())
		and GameSetupSpecScript.is_piece_set_supported(current_mode, selected_preset_id(), selected_piece_set_id())
		and GameSetupSpecScript.is_random_mode_supported(selected_random_mode())
		and GameSetupSpecScript.is_valid_seed(selected_seed())
		and GameSetupSpecScript.is_valid_speed(selected_speed_level())
	)


func _entry(mode: String) -> Dictionary:
	var value = _selected.get(mode, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else _default_entry(mode)


func _default_entry(mode: String) -> Dictionary:
	return {
		"board_preset_id": GameSetupSpecScript.STANDARD_PRESET_ID,
		"piece_set_id": GameSetupSpecScript.default_piece_set_id(mode),
		"random_mode": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED,
		"seed": GameSetupSpecScript.DEFAULT_SEED,
		"initial_speed_level": GameSetupSpecScript.MIN_SPEED_LEVEL,
	}


# tet4d-semantic-boundary: allow adapter-routing
func _validated_entry(mode: String, raw: Dictionary) -> Dictionary:
	var result := _default_entry(mode)
	var preset_id := str(raw.get("board_preset_id", GameSetupSpecScript.STANDARD_PRESET_ID))
	if GameSetupSpecScript.is_supported(mode, preset_id):
		result["board_preset_id"] = preset_id
	var piece_set_id := str(raw.get("piece_set_id", result["piece_set_id"]))
	if GameSetupSpecScript.is_piece_set_supported(mode, str(result["board_preset_id"]), piece_set_id):
		result["piece_set_id"] = piece_set_id
	var random_mode := str(raw.get("random_mode", result["random_mode"]))
	if GameSetupSpecScript.is_random_mode_supported(random_mode):
		result["random_mode"] = random_mode
	var seed = raw.get("seed", result["seed"])
	if GameSetupSpecScript.is_valid_seed(seed):
		result["seed"] = int(seed)
	var speed = raw.get("initial_speed_level", result["initial_speed_level"])
	if GameSetupSpecScript.is_valid_speed(speed):
		result["initial_speed_level"] = int(speed)
	return result
