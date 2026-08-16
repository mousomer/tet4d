extends RefCounted

const SetupFieldSpecScript = preload("res://scripts/ui/game_setup/setup_field_spec.gd")
const SetupFieldRegistryScript = preload("res://scripts/ui/game_setup/setup_field_registry.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")
const GameSetupModelScript = preload("res://scripts/ui/game_setup/game_setup_model.gd")
const GameSetupPanelScript = preload("res://scripts/ui/game_setup/game_setup_panel.gd")

const EXPECTED_FIELD_IDS := {
	"live_2d": [
		"board_preset", "board_axis_0", "board_axis_1",
		"random_mode", "seed", "initial_speed_level",
	],
	"live_3d": [
		"board_preset", "board_axis_0", "board_axis_1", "board_axis_2",
		"piece_set", "random_mode", "seed", "initial_speed_level",
		"translation_frame", "rotation_frame",
	],
	"live_4d": [
		"board_preset", "board_axis_0", "board_axis_1", "board_axis_2",
		"board_axis_3", "piece_set", "random_mode", "seed",
		"initial_speed_level", "translation_frame", "rotation_frame",
	],
}


func run() -> Array:
	var failures: Array = []
	_check_registry_declarations(failures)
	_check_total_classification(failures)
	_check_disclosure_assignment(failures)
	_check_contextual_visibility(failures)
	_check_piece_set_choice_modes(failures)
	_check_session_identity_conformance(failures)
	_check_range_conformance(failures)
	_check_rule_enforcement(failures)
	await _check_panel_classification(failures)
	return failures


func _check_registry_declarations(failures: Array) -> void:
	var registry_failures: Array = SetupFieldRegistryScript.validate()
	if not registry_failures.is_empty():
		failures.append("declared setup fields must validate: %s" % str(registry_failures))


func _check_total_classification(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var declared_ids: Array = []
		for spec in SetupFieldRegistryScript.specs_for_mode(mode):
			declared_ids.append(spec.id())
			if not SetupFieldSpecScript.ALLOWED_CATEGORIES.has(spec.category()):
				failures.append("%s/%s must resolve to exactly one taxonomy category" % [mode, spec.id()])
			if not spec.applies_to_mode(mode):
				failures.append("%s/%s must declare the mode it is rendered in" % [mode, spec.id()])
		if declared_ids != EXPECTED_FIELD_IDS.get(mode, []):
			failures.append("%s must classify every rendered setup field: %s" % [mode, str(declared_ids)])


func _check_disclosure_assignment(failures: Array) -> void:
	for spec in SetupFieldRegistryScript.specs_for_mode(GameSetupSpecScript.MODE_4D):
		match spec.category():
			SetupFieldSpecScript.CATEGORY_GAME_DEFINITION:
				if not spec.is_always_visible():
					failures.append("%s: game definition must stay in the ordinary path" % spec.id())
			SetupFieldSpecScript.CATEGORY_ADVANCED_GAMEPLAY_INPUT:
				if spec.disclosure() != SetupFieldSpecScript.DISCLOSURE_SECONDARY:
					failures.append("%s: advanced gameplay input must be visually secondary" % spec.id())
				if spec.defines_session_identity():
					failures.append("%s: advanced gameplay input must not define session identity" % spec.id())
	var advanced_ids: Array = _spec_ids(SetupFieldRegistryScript.specs_for_category(
		GameSetupSpecScript.MODE_4D, SetupFieldSpecScript.CATEGORY_ADVANCED_GAMEPLAY_INPUT
	))
	if advanced_ids != ["translation_frame", "rotation_frame"]:
		failures.append("4D advanced gameplay input must be exactly the control frames: %s" % str(advanced_ids))
	if not _spec_ids(SetupFieldRegistryScript.specs_for_category(
		GameSetupSpecScript.MODE_2D, SetupFieldSpecScript.CATEGORY_ADVANCED_GAMEPLAY_INPUT
	)).is_empty():
		failures.append("2D must declare no advanced gameplay input fields")


func _check_contextual_visibility(failures: Array) -> void:
	var fixed_seed := {"random_mode": GameSetupSpecScript.RANDOM_MODE_FIXED_SEED}
	var true_random := {"random_mode": GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM}
	var visible_ids: Array = []
	for spec in SetupFieldRegistryScript.visible_specs_for(GameSetupSpecScript.MODE_4D, fixed_seed):
		visible_ids.append(spec.id())
	if not visible_ids.has("seed"):
		failures.append("seed must be visible under fixed-seed randomness")
	visible_ids = []
	for spec in SetupFieldRegistryScript.visible_specs_for(GameSetupSpecScript.MODE_4D, true_random):
		visible_ids.append(spec.id())
	if visible_ids.has("seed"):
		failures.append("seed must be hidden under true-random randomness")
	for spec in SetupFieldRegistryScript.specs_for_mode(GameSetupSpecScript.MODE_2D):
		if spec.id() == "translation_frame" or spec.id() == "rotation_frame":
			failures.append("2D must not declare control-frame fields")
		if spec.id() == "piece_set":
			failures.append("2D must not declare a piece-set field while only one set exists")


# Binds the declared piece-set modes to the independently maintained piece-set
# catalogue, so a mode that gains or loses a real choice fails here.
func _check_piece_set_choice_modes(failures: Array) -> void:
	var declared: Array = SetupFieldRegistryScript.PIECE_SET_CHOICE_MODES
	for mode in GameSetupSpecScript.modes():
		var has_choice: bool = GameSetupSpecScript.piece_sets_for_mode(mode).size() > 1
		if has_choice != declared.has(mode):
			failures.append("%s declares a piece-set choice field as %s but publishes %d piece sets" % [
				mode, str(declared.has(mode)), GameSetupSpecScript.piece_sets_for_mode(mode).size(),
			])
		if not has_choice and GameSetupSpecScript.piece_sets_for_mode(mode).is_empty():
			failures.append("%s must still publish a piece set for the session payload" % mode)


func _check_session_identity_conformance(failures: Array) -> void:
	var model = GameSetupModelScript.new()
	model.set_mode(GameSetupSpecScript.MODE_4D)
	var payload_keys: Array = model.canonical_session_setup().keys()
	payload_keys.sort()
	var declared_keys: Array = SetupFieldRegistryScript.session_identity_keys()
	var envelope_keys: Array = SetupFieldRegistryScript.SESSION_ENVELOPE_KEYS.duplicate()
	var covered: Array = declared_keys.duplicate()
	for key in envelope_keys:
		if not covered.has(key):
			covered.append(key)
	covered.sort()
	if covered != payload_keys:
		failures.append("session identity fields must match canonical_session_setup: declared %s vs payload %s" % [
			str(covered), str(payload_keys),
		])
	for key in ["translation_frame", "rotation_frame"]:
		if payload_keys.has(key):
			failures.append("%s must stay outside the canonical session payload" % key)
		if declared_keys.has(key):
			failures.append("%s must not be declared as session identity" % key)


func _check_range_conformance(failures: Array) -> void:
	for mode in GameSetupSpecScript.modes():
		var ranges: Array = GameSetupSpecScript.board_axis_ranges(mode)
		for spec in SetupFieldRegistryScript.specs_for_mode(mode):
			var declared_min = spec.data.get("min")
			var declared_max = spec.data.get("max")
			match spec.value_type():
				"shape_axis":
					var axis_index: int = int(spec.data.get("axis_index", -1))
					if axis_index < 0 or axis_index >= ranges.size():
						failures.append("%s/%s declares an axis outside the board-extent contract" % [mode, spec.id()])
						continue
					var axis_range: Array = ranges[axis_index] as Array
					if int(declared_min) != int(axis_range[0]) or int(declared_max) != int(axis_range[1]):
						failures.append("%s/%s range must match the board-extent contract: declared %s-%s vs %s-%s" % [
							mode, spec.id(), str(declared_min), str(declared_max),
							str(axis_range[0]), str(axis_range[1]),
						])
				"int":
					var expected := _expected_int_range(spec.id())
					if expected.is_empty():
						failures.append("%s/%s has no owning numeric range source" % [mode, spec.id()])
					elif int(declared_min) != int(expected[0]) or int(declared_max) != int(expected[1]):
						failures.append("%s/%s range must match its owning constants: declared %s-%s vs %s-%s" % [
							mode, spec.id(), str(declared_min), str(declared_max),
							str(expected[0]), str(expected[1]),
						])


func _expected_int_range(field_id: String) -> Array:
	match field_id:
		"seed":
			return [GameSetupSpecScript.MIN_SEED, GameSetupSpecScript.MAX_SEED]
		"initial_speed_level":
			return [GameSetupSpecScript.MIN_SPEED_LEVEL, GameSetupSpecScript.MAX_SPEED_LEVEL]
	return []


func _spec_ids(specs: Array) -> Array:
	var ids: Array = []
	for spec in specs:
		ids.append(spec.id())
	return ids


func _check_rule_enforcement(failures: Array) -> void:
	var base: Dictionary = SetupFieldRegistryScript.field_data_for_mode(GameSetupSpecScript.MODE_4D)[0]
	var modes: Array = GameSetupSpecScript.modes()
	if not SetupFieldSpecScript.validate(base, modes).is_empty():
		failures.append("a declared registry field must validate as the rule-test baseline")

	var advanced_claiming_identity := base.duplicate(true)
	advanced_claiming_identity["category"] = SetupFieldSpecScript.CATEGORY_ADVANCED_GAMEPLAY_INPUT
	advanced_claiming_identity["disclosure"] = SetupFieldSpecScript.DISCLOSURE_SECONDARY
	_expect_failure(failures, advanced_claiming_identity, modes, "advanced field declared as session identity")

	var presentation_claiming_identity := base.duplicate(true)
	presentation_claiming_identity["category"] = SetupFieldSpecScript.CATEGORY_PRESENTATION_PREFERENCE
	presentation_claiming_identity["disclosure"] = SetupFieldSpecScript.DISCLOSURE_SECONDARY
	_expect_failure(failures, presentation_claiming_identity, modes, "presentation preference declared as session identity")

	var mismatched_disclosure := base.duplicate(true)
	mismatched_disclosure["disclosure"] = SetupFieldSpecScript.DISCLOSURE_SECONDARY
	_expect_failure(failures, mismatched_disclosure, modes, "category/disclosure mismatch")

	var stray_condition := base.duplicate(true)
	stray_condition["visible_when"] = {"field": "random_mode", "equals": "fixed_seed"}
	_expect_failure(failures, stray_condition, modes, "non-contextual field declaring visible_when")

	var missing_session_key := base.duplicate(true)
	missing_session_key.erase("session_key")
	_expect_failure(failures, missing_session_key, modes, "session identity without session_key")

	var seed_data: Dictionary = _field_data(GameSetupSpecScript.MODE_4D, "seed")
	var contextual_without_condition := seed_data.duplicate(true)
	contextual_without_condition.erase("visible_when")
	_expect_failure(failures, contextual_without_condition, modes, "contextual field without visible_when")

	var frame_data: Dictionary = _field_data(GameSetupSpecScript.MODE_4D, "translation_frame")
	var input_with_session_key := frame_data.duplicate(true)
	input_with_session_key["session_key"] = "translation_frame"
	_expect_failure(failures, input_with_session_key, modes, "input preference declaring session_key")

	var unknown_category := base.duplicate(true)
	unknown_category["category"] = "presentation"
	_expect_failure(failures, unknown_category, modes, "unknown category")

	var bad_pair := base.duplicate(true)
	bad_pair["control_type"] = "stepper"
	_expect_failure(failures, bad_pair, modes, "invalid value/control pair")

	var unknown_mode := base.duplicate(true)
	unknown_mode["modes"] = ["live_5d"]
	_expect_failure(failures, unknown_mode, modes, "unknown mode")

	var unsupported_field := base.duplicate(true)
	unsupported_field["persist"] = true
	_expect_failure(failures, unsupported_field, modes, "unsupported spec field")

	var enum_with_range := base.duplicate(true)
	enum_with_range["min"] = 0
	enum_with_range["max"] = 9
	_expect_failure(failures, enum_with_range, modes, "enum field declaring min/max")

	var missing_range := seed_data.duplicate(true)
	missing_range.erase("min")
	_expect_failure(failures, missing_range, modes, "numeric field without min")

	var inverted_range := seed_data.duplicate(true)
	inverted_range["min"] = seed_data.get("max")
	inverted_range["max"] = seed_data.get("min")
	_expect_failure(failures, inverted_range, modes, "numeric field with min greater than max")

	var axis_data: Dictionary = _field_data(GameSetupSpecScript.MODE_4D, "board_axis_0")
	var non_numeric_range := axis_data.duplicate(true)
	non_numeric_range["max"] = "sixteen"
	_expect_failure(failures, non_numeric_range, modes, "axis field with non-numeric max")


func _check_panel_classification(failures: Array) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var panel = GameSetupPanelScript.new()
	tree.root.add_child(panel)
	panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var model = GameSetupModelScript.new()
	for mode in GameSetupSpecScript.modes():
		for random_mode in [
			GameSetupSpecScript.RANDOM_MODE_FIXED_SEED,
			GameSetupSpecScript.RANDOM_MODE_TRUE_RANDOM,
		]:
			model.set_mode(mode)
			model.select_random_mode(random_mode)
			panel.configure(model)
			await tree.process_frame
			_compare_panel_to_registry(failures, panel, model, mode, random_mode)
	panel.queue_free()
	await tree.process_frame


# A setup field can be absent from the screen for two unrelated reasons:
# semantically, because the declared `visible_when` condition does not hold; and
# presentationally, because the disclosure section holding it is collapsed. Only
# the first belongs to the taxonomy, so this check pins both independently.
func _compare_panel_to_registry(failures: Array, panel, model, mode: String, random_mode: String) -> void:
	var context := "%s/%s" % [mode, random_mode]
	var entry := {"random_mode": model.selected_random_mode()}
	var applicable: Array = []
	for spec in SetupFieldRegistryScript.visible_specs_for(mode, entry):
		var control = _control_for_field(panel, spec.id())
		if control == null:
			failures.append("%s: declared field %s has no rendered control" % [context, spec.id()])
			continue
		applicable.append(control)
	for spec in SetupFieldRegistryScript.specs_for_mode(mode):
		if spec.is_visible_for(mode, entry):
			continue
		var hidden_control = _control_for_field(panel, spec.id())
		if hidden_control == null:
			continue
		if hidden_control.is_visible_in_tree():
			failures.append("%s: %s is declared hidden but the panel shows it" % [context, spec.id()])
		if hidden_control.focus_mode != Control.FOCUS_NONE:
			failures.append("%s: semantically hidden %s must not be a focus target" % [context, spec.id()])

	# Nothing rendered may be unclassified, in any disclosure state.
	var revealed: Array = []
	for control in applicable:
		if (control as Control).is_visible_in_tree():
			revealed.append(control)
	var rendered: Array = _visible_value_controls(panel)
	if _instance_ids(rendered) != _instance_ids(revealed):
		failures.append("%s: every rendered setup control must be classified: rendered %d, classified %d (%s)" % [
			context, rendered.size(), revealed.size(), _control_names(rendered),
		])

	# Collapse must be the only remaining reason an applicable field is hidden.
	for section_id in panel.disclosure_section_ids():
		panel.set_section_expanded(section_id, true)
	for spec in SetupFieldRegistryScript.visible_specs_for(mode, entry):
		var expanded_control = _control_for_field(panel, spec.id())
		if expanded_control == null:
			continue
		if not (expanded_control as Control).is_visible_in_tree():
			failures.append("%s: %s stays hidden with every section expanded" % [context, spec.id()])
		if (expanded_control as Control).focus_mode != Control.FOCUS_ALL:
			failures.append("%s: revealed %s must be a focus target" % [context, spec.id()])
	for section_id in panel.disclosure_section_ids():
		panel.set_section_expanded(section_id, false)


func _visible_value_controls(node: Node) -> Array:
	var controls: Array = []
	for child in node.get_children():
		if (child is OptionButton or child is LineEdit) and (child as Control).is_visible_in_tree():
			controls.append(child)
		controls.append_array(_visible_value_controls(child))
	return controls


func _control_for_field(panel, field_id: String):
	match field_id:
		"board_preset":
			return panel._board_selector
		"piece_set":
			return panel._piece_selector
		"random_mode":
			return panel._random_selector
		"seed":
			return panel._seed_input
		"initial_speed_level":
			return panel._speed_selector
		"translation_frame":
			return panel._translation_frame_selector
		"rotation_frame":
			return panel._rotation_frame_selector
	if field_id.begins_with("board_axis_"):
		var axis_index := int(field_id.trim_prefix("board_axis_"))
		if axis_index >= 0 and axis_index < panel._axis_inputs.size():
			return panel._axis_inputs[axis_index]
	return null


func _instance_ids(controls: Array) -> Array:
	var ids: Array = []
	for control in controls:
		ids.append((control as Object).get_instance_id())
	ids.sort()
	return ids


func _control_names(controls: Array) -> String:
	var names: Array = []
	for control in controls:
		names.append("%s:%s" % [(control as Node).name, (control as Object).get_class()])
	return ", ".join(names)


func _expect_failure(failures: Array, spec_data: Dictionary, modes: Array, description: String) -> void:
	if SetupFieldSpecScript.validate(spec_data, modes).is_empty():
		failures.append("validation must reject %s" % description)


func _field_data(mode: String, field_id: String) -> Dictionary:
	for spec_data in SetupFieldRegistryScript.field_data_for_mode(mode):
		if str((spec_data as Dictionary).get("id", "")) == field_id:
			return spec_data as Dictionary
	return {}
