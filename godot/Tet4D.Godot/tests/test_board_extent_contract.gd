extends RefCounted

const BoardExtentContractScript = preload("res://scripts/generated/board_extent_contract_v1.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")


func run() -> Array:
	var failures: Array = []
	var bridge = Tet4DCoreBridgeScript.new()
	var contract: Dictionary = bridge.get_board_extent_contract()
	if contract.get("contract") != BoardExtentContractScript.CONTRACT_NAME or int(contract.get("contract_version", 0)) != BoardExtentContractScript.CONTRACT_VERSION:
		failures.append("native board-extent contract metadata must match generated binding")
	elif ((contract.get("modes", []) as Array)[2] as Dictionary).get("axis_order", []) != ["X", "Y", "Z", "W"]:
		failures.append("native board-extent contract must expose generated axis order")
	var model = GameSetupModelScript.new()
	for mode in GameSetupSpecScript.modes():
		model.set_mode(mode)
		for preset in GameSetupSpecScript.presets_for_mode(mode):
			var preset_id := str((preset as Dictionary).get("id", ""))
			if not model.select_preset(preset_id):
				failures.append("preset must remain selectable: %s/%s" % [mode, preset_id])
				continue
			for piece in GameSetupSpecScript.piece_sets_for_mode(mode, preset_id):
				var piece_id := str((piece as Dictionary).get("id", ""))
				model.select_piece_set(piece_id)
				var valid: Dictionary = bridge.validate_live_board_setup(model.canonical_session_setup())
				if not bool(valid.get("ok", false)):
					failures.append("generated preset request must validate: %s/%s/%s" % [mode, preset_id, piece_id])
	model.set_mode(GameSetupSpecScript.MODE_4D)
	var w_one_setup: Dictionary = model.canonical_session_setup()
	w_one_setup["board_shape"] = [5, 10, 4, 1]
	w_one_setup["topology_profile"] = GameSetupSpecScript.bounded_topology_profile([5, 10, 4, 1])
	for compatible_piece_set in ["embedded_3d", "embedded_2d"]:
		w_one_setup["piece_set_id"] = compatible_piece_set
		if not bool(bridge.validate_live_board_setup(w_one_setup).get("ok", false)):
			failures.append("W=1 must remain admissible for %s" % compatible_piece_set)
	w_one_setup["piece_set_id"] = "standard_4d_5"
	var w_one_standard := bridge.validate_live_board_setup(w_one_setup)
	if bool(w_one_standard.get("ok", true)) or str((w_one_standard.get("errors", [{}])[0] as Dictionary).get("code", "")) != "spawn_not_viable":
		failures.append("W=1 standard_4d_5 must reject through spawn viability")
	model.set_mode(GameSetupSpecScript.MODE_2D)
	var setup: Dictionary = model.canonical_session_setup()
	var good: Dictionary = bridge.live_2d_configure_checked(setup)
	if not bool(good.get("ok", false)) or not (good.get("errors", null) is Array):
		failures.append("checked native configuration must return structured success")
	else:
		var before_hash := bridge.live_2d_state_hash()
		for malformed_extent in [true, 6.0, "6"]:
			var invalid := setup.duplicate(true)
			invalid["board_shape"] = [malformed_extent, 6]
			invalid["topology_profile"] = GameSetupSpecScript.bounded_topology_profile([6, 6])
			var rejected: Dictionary = bridge.live_2d_configure_checked(invalid)
			if bool(rejected.get("ok", true)) or not (rejected.get("errors", []) is Array):
				failures.append("strict board decoding must reject non-integer extents with an error array")
			elif (rejected.get("errors", []) as Array).is_empty() or str((rejected.get("errors", [])[0] as Dictionary).get("code", "")) != "invalid_field_type":
				failures.append("strict board decoding must retain invalid_field_type identity")
		var missing_topology := setup.duplicate(true)
		missing_topology.erase("topology_profile")
		if bool(bridge.live_2d_configure_checked(missing_topology).get("ok", true)):
			failures.append("topology profile must be required for checked configuration")
		if bridge.live_2d_state_hash() != before_hash:
			failures.append("failed checked configuration must not mutate the live session")
	return failures
