extends RefCounted

class_name GameSetupModel

const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

var current_mode := GameSetupSpecScript.MODE_2D
var _selected := {
	GameSetupSpecScript.MODE_2D: GameSetupSpecScript.STANDARD_PRESET_ID,
	GameSetupSpecScript.MODE_3D: GameSetupSpecScript.STANDARD_PRESET_ID,
	GameSetupSpecScript.MODE_4D: GameSetupSpecScript.STANDARD_PRESET_ID,
}


func set_mode(mode: String) -> bool:
	if not GameSetupSpecScript.modes().has(mode):
		return false
	current_mode = mode
	return true


func select_preset(preset_id: String) -> bool:
	if not GameSetupSpecScript.is_supported(current_mode, preset_id):
		return false
	_selected[current_mode] = preset_id
	return true


func selected_preset_id(mode: String = "") -> String:
	var target_mode := current_mode if mode.is_empty() else mode
	var candidate := str(_selected.get(target_mode, GameSetupSpecScript.STANDARD_PRESET_ID))
	return candidate if GameSetupSpecScript.is_supported(target_mode, candidate) else GameSetupSpecScript.STANDARD_PRESET_ID


func selected_spec() -> Dictionary:
	return GameSetupSpecScript.preset(current_mode, selected_preset_id())


func selected_shape() -> Array:
	return (selected_spec().get("shape", []) as Array).duplicate()


func reset_to_standard(mode: String = "") -> void:
	var target_mode := current_mode if mode.is_empty() else mode
	if GameSetupSpecScript.modes().has(target_mode):
		_selected[target_mode] = GameSetupSpecScript.STANDARD_PRESET_ID


func apply_last_selected(values: Dictionary) -> void:
	for mode in GameSetupSpecScript.modes():
		var preset_id := str(values.get(mode, GameSetupSpecScript.STANDARD_PRESET_ID))
		_selected[mode] = preset_id if GameSetupSpecScript.is_supported(mode, preset_id) else GameSetupSpecScript.STANDARD_PRESET_ID


func canonical_snapshot() -> Dictionary:
	var last_selected := {}
	for mode in GameSetupSpecScript.modes():
		last_selected[mode] = selected_preset_id(mode)
	return {
		"mode": current_mode,
		"preset_id": selected_preset_id(),
		"board_shape": selected_shape(),
		"last_selected": last_selected,
	}
