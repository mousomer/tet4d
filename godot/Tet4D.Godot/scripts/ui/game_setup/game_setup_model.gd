extends RefCounted

class_name GameSetupModel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")

var current_mode := GameSetupSpecScript.MODE_2D
var _drafts := {}
var _last_valid := {}
var _validation := {}
var _bridge


func _init(bridge = null) -> void:
	_bridge = bridge if bridge != null else Tet4DCoreBridgeScript.new()
	for mode in GameSetupSpecScript.modes():
		_drafts[mode] = _default_entry(mode)
		_last_valid[mode] = _default_entry(mode)
		_validation[mode] = {"ok": true, "errors": []}
		_validate_mode(mode)


func set_mode(mode: String) -> bool:
	if not GameSetupSpecScript.modes().has(mode):
		return false
	current_mode = mode
	return true


func select_preset(preset_id: String) -> bool:
	if not GameSetupSpecScript.is_supported(current_mode, preset_id):
		return false
	var entry := _draft_entry(current_mode)
	entry["board_shape"] = (GameSetupSpecScript.preset(current_mode, preset_id).get("shape", []) as Array).duplicate()
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func selected_preset_id(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	return GameSetupSpecScript.preset_id_for_shape(target_mode, selected_shape(target_mode))


func selected_spec() -> Dictionary:
	return GameSetupSpecScript.preset(current_mode, selected_preset_id())


func selected_shape(mode: String = "") -> Array:
	var target_mode := current_mode if mode.is_empty() else mode
	var shape = _draft_entry(target_mode).get("board_shape", [])
	return (shape as Array).duplicate() if shape is Array else []


func selected_axis_text(axis: int, mode: String = "") -> String:
	var shape := selected_shape(mode)
	return str(shape[axis]) if axis >= 0 and axis < shape.size() else ""


func set_axis_text(axis: int, text: String) -> bool:
	if axis < 0 or axis >= selected_shape().size():
		return false
	var entry := _draft_entry(current_mode)
	var shape: Array = entry.get("board_shape", [])
	shape[axis] = int(text) if text.strip_edges().is_valid_int() else text
	entry["board_shape"] = shape
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func adjust_axis(axis: int, delta: int) -> bool:
	if axis < 0 or axis >= selected_shape().size() or delta == 0:
		return false
	var shape := selected_shape()
	var fallback_shape := last_valid_shape(current_mode)
	var base := int(shape[axis]) if typeof(shape[axis]) == TYPE_INT else int(fallback_shape[axis])
	return set_axis_text(axis, str(base + delta))


func selected_piece_set_id(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_draft_entry(target_mode).get("piece_set_id", GameSetupSpecScript.default_piece_set_id(target_mode)))
	return candidate if GameSetupSpecScript.is_piece_set_supported(target_mode, "", candidate) else GameSetupSpecScript.default_piece_set_id(target_mode)


func select_piece_set(piece_set_id: String) -> bool:
	if not GameSetupSpecScript.is_piece_set_supported(current_mode, "", piece_set_id):
		return false
	var entry := _draft_entry(current_mode)
	entry["piece_set_id"] = piece_set_id
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func selected_random_mode(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_draft_entry(target_mode).get("random_mode", GameSetupSpecScript.RANDOM_MODE_FIXED_SEED))
	return candidate if GameSetupSpecScript.is_random_mode_supported(candidate) else GameSetupSpecScript.RANDOM_MODE_FIXED_SEED


func select_random_mode(random_mode: String) -> bool:
	if not GameSetupSpecScript.is_random_mode_supported(random_mode):
		return false
	var entry := _draft_entry(current_mode)
	entry["random_mode"] = random_mode
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func selected_seed(mode: String = "") -> int:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate = _draft_entry(target_mode).get("seed", GameSetupSpecScript.DEFAULT_SEED)
	return int(candidate) if GameSetupSpecScript.is_valid_seed(candidate) else GameSetupSpecScript.DEFAULT_SEED


func select_seed(seed) -> bool:
	if not GameSetupSpecScript.is_valid_seed(seed):
		return false
	var entry := _draft_entry(current_mode)
	entry["seed"] = int(seed)
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func selected_speed_level(mode: String = "") -> int:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate = _draft_entry(target_mode).get("initial_speed_level", GameSetupSpecScript.MIN_SPEED_LEVEL)
	return int(candidate) if GameSetupSpecScript.is_valid_speed(candidate) else GameSetupSpecScript.MIN_SPEED_LEVEL


func select_speed_level(speed_level) -> bool:
	if not GameSetupSpecScript.is_valid_speed(speed_level):
		return false
	var entry := _draft_entry(current_mode)
	entry["initial_speed_level"] = int(speed_level)
	_drafts[current_mode] = entry
	_validate_mode(current_mode)
	return true


func reset_to_standard(mode: String = "") -> void:
	var target_mode := current_mode if mode.is_empty() else mode
	if GameSetupSpecScript.modes().has(target_mode):
		_drafts[target_mode] = _default_entry(target_mode)
		_validate_mode(target_mode)


func reset_sizes(mode: String = "") -> void:
	var target_mode := current_mode if mode.is_empty() else mode
	if not GameSetupSpecScript.modes().has(target_mode):
		return
	var entry := _draft_entry(target_mode)
	entry["board_shape"] = GameSetupSpecScript.canonical_default_shape(target_mode)
	_drafts[target_mode] = entry
	_validate_mode(target_mode)


func apply_last_selected(values: Dictionary) -> void:
	for mode in GameSetupSpecScript.modes():
		var value = values.get(mode, {})
		if typeof(value) == TYPE_STRING:
			value = {"board_preset_id": str(value)}
		_drafts[mode] = _entry_from_persisted(mode, value if value is Dictionary else {})
		_validate_mode(mode)
		if not is_valid(mode):
			_drafts[mode] = _default_entry(mode)
			_validate_mode(mode)


func canonical_snapshot() -> Dictionary:
	var result := canonical_session_setup()
	result["last_selected"] = last_valid_entries()
	return result


func canonical_session_setup(mode: String = "") -> Dictionary:
	var target_mode := current_mode if mode.is_empty() else mode
	var entry := _draft_entry(target_mode)
	var shape = entry.get("board_shape", [])
	return {
		"schema_version": GameSetupSpecScript.SCHEMA_VERSION,
		"contract_version": GameSetupSpecScript.BoardExtentContractScript.CONTRACT_VERSION,
		"mode": target_mode,
		"board_preset_id": GameSetupSpecScript.preset_id_for_shape(target_mode, shape) if shape is Array else "",
		"board_shape": (shape as Array).duplicate() if shape is Array else shape,
		"piece_set_id": entry.get("piece_set_id", ""),
		"random_mode": entry.get("random_mode", ""),
		"seed": entry.get("seed", null),
		"initial_speed_level": entry.get("initial_speed_level", null),
		"topology_profile": GameSetupSpecScript.bounded_topology_profile(shape) if shape is Array else {},
	}


func is_current_valid() -> bool:
	return is_valid(current_mode)


func is_valid(mode: String) -> bool:
	return bool((_validation.get(mode, {}) as Dictionary).get("ok", false))


func validation_result(mode: String = "") -> Dictionary:
	var target_mode := current_mode if mode.is_empty() else mode
	return (_validation.get(target_mode, {"ok": false, "errors": []}) as Dictionary).duplicate(true)


func validation_errors(mode: String = "") -> Array:
	return (validation_result(mode).get("errors", []) as Array).duplicate(true)


func validate_current_draft() -> bool:
	_validate_mode(current_mode)
	return is_current_valid()


func last_valid_entries() -> Dictionary:
	var result := {}
	for mode in GameSetupSpecScript.modes():
		var entry = _last_valid.get(mode, _default_entry(mode))
		result[mode] = _persisted_entry(mode, entry as Dictionary)
	return result


func last_valid_shape(mode: String = "") -> Array:
	var target_mode := current_mode if mode.is_empty() else mode
	var entry = _last_valid.get(target_mode, _default_entry(target_mode))
	var shape = (entry as Dictionary).get("board_shape", [])
	return (shape as Array).duplicate() if shape is Array else GameSetupSpecScript.canonical_default_shape(target_mode)


func _draft_entry(mode: String) -> Dictionary:
	var value = _drafts.get(mode, {})
	return (value as Dictionary).duplicate(true) if value is Dictionary else _default_entry(mode)


func _default_entry(mode: String) -> Dictionary:
	return {
		"board_shape": GameSetupSpecScript.canonical_default_shape(mode),
		"piece_set_id": GameSetupSpecScript.default_piece_set_id(mode),
		"random_mode": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED,
		"seed": GameSetupSpecScript.DEFAULT_SEED,
		"initial_speed_level": GameSetupSpecScript.MIN_SPEED_LEVEL,
	}


func _entry_from_persisted(mode: String, raw: Dictionary) -> Dictionary:
	var result := _default_entry(mode)
	if raw.has("board_shape"):
		result["board_shape"] = raw.get("board_shape")
	elif GameSetupSpecScript.is_supported(mode, str(raw.get("board_preset_id", ""))):
		result["board_shape"] = (GameSetupSpecScript.preset(mode, str(raw.get("board_preset_id", ""))).get("shape", []) as Array).duplicate()
	for key in ["piece_set_id", "random_mode", "seed", "initial_speed_level"]:
		if raw.has(key):
			result[key] = raw.get(key)
	return result


func _persisted_entry(mode: String, entry: Dictionary) -> Dictionary:
	var shape = entry.get("board_shape", [])
	return {
		"board_preset_id": GameSetupSpecScript.preset_id_for_shape(mode, shape) if shape is Array else "",
		"board_shape": (shape as Array).duplicate() if shape is Array else shape,
		"piece_set_id": entry.get("piece_set_id", ""),
		"random_mode": entry.get("random_mode", ""),
		"seed": entry.get("seed", null),
		"initial_speed_level": entry.get("initial_speed_level", null),
	}


# tet4d-semantic-boundary: allow adapter-routing
func _validate_mode(mode: String) -> void:
	var response = _bridge.validate_live_board_setup(canonical_session_setup(mode))
	var result: Dictionary = response if response is Dictionary else {"ok": false, "errors": []}
	var errors: Array = (result.get("errors", []) as Array).duplicate(true)
	var entry := _draft_entry(mode)
	if not GameSetupSpecScript.is_random_mode_supported(str(entry.get("random_mode", ""))):
		errors.append({"code": "invalid_random_mode", "path": "$.random_mode"})
	if not GameSetupSpecScript.is_valid_seed(entry.get("seed", null)):
		errors.append({"code": "invalid_seed", "path": "$.seed"})
	if not GameSetupSpecScript.is_valid_speed(entry.get("initial_speed_level", null)):
		errors.append({"code": "invalid_speed", "path": "$.initial_speed_level"})
	_validation[mode] = {"ok": errors.is_empty(), "errors": errors}
	if errors.is_empty():
		_last_valid[mode] = _draft_entry(mode)
