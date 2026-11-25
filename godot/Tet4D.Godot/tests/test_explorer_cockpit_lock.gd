extends RefCounted

const Contract = preload("res://scripts/input/live_input_contract.gd")
const Probe = preload("res://tests/fixtures/explorer_input_probe.gd")
const BASELINE := "res://tests/fixtures/explorer_cockpit_baseline.json"
const WRITE_ENV := "TET4D_WRITE_EXPLORER_BASELINE"
var completed := false
var _legacy_action_names: Dictionary = {}

func run() -> Array:
	var failures: Array = []
	# The frozen Phase 0 fixture owns this list; new IDs are tested separately.
	var frozen: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(BASELINE))
	for row in JSON.parse_string(frozen["2"].action_bindings): _legacy_action_names[str(row[0])] = true
	var tree := Engine.get_main_loop() as SceneTree
	var previous_scale := tree.root.content_scale_size
	var previous_size := tree.root.size
	var previous_minimum := tree.root.min_size
	var saved := {}
	# Default-binding lock is independent of persisted and earlier-test bindings.
	for action in Contract.ACTION_SPECS:
		saved[action] = InputMap.action_get_events(action) if InputMap.has_action(action) else null
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		InputMap.action_erase_events(action)
		var spec: Dictionary = Contract.ACTION_SPECS[action]
		for key in spec.get("keys", []):
			var event := InputEventKey.new()
			event.keycode = key
			event.shift_pressed = spec.get("shift", false)
			InputMap.action_add_event(action, event)
		for key in spec.get("alt_keys", []):
			var event := InputEventKey.new()
			event.keycode = key
			event.alt_pressed = true
			InputMap.action_add_event(action, event)
	var scene = load("res://scenes/game_bootstrap.tscn").instantiate()
	var app = scene.get_node("App")
	app.set_script(Probe)
	tree.root.add_child(scene)
	app.set_process(false)
	await _frames(tree, 10)
	var hud = scene.get_node("ReplayHud")
	var storage := DirAccess.create_temp("explorer-lock")
	hud._settings_store._storage_path = storage.get_current_dir().path_join("settings.json")
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	hud._set_onboarding_visible(false)
	hud._game_setup_model = load("res://scripts/ui/game_setup/game_setup_model.gd").new()
	tree.root.min_size = Vector2i.ZERO
	tree.root.size = Vector2i(1280, 800)
	tree.root.content_scale_size = Vector2i(1280, 800)
	var actual := {}
	for dimension in [2, 3, 4]:
		app._practice_action("dimension_%d" % dimension)
		await _frames(tree, 20)
		app.observing = true
		var keys := {}
		var candidates: Array = []
		for code in range(KEY_A, KEY_Z + 1): candidates.append(code)
		for code in range(KEY_0, KEY_9 + 1): candidates.append(code)
		candidates.append_array([KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_PAGEUP, KEY_PAGEDOWN, KEY_BACKSPACE, KEY_SPACE, KEY_MINUS, KEY_EQUAL, KEY_PLUS, KEY_BRACKETLEFT, KEY_BRACKETRIGHT, KEY_SHIFT, KEY_CTRL])
		for action in Contract.ACTION_SPECS:
			if str(action).begins_with("shell_"): continue
			for code in Contract.ACTION_SPECS[action].get("keys", []):
				if code not in candidates: candidates.append(code)
		candidates.sort()
		for code in candidates:
			for shifted in [false, true]:
				var event := InputEventKey.new()
				event.keycode = code
				event.shift_pressed = shifted
				event.pressed = true
				app.observed.clear()
				app._input(event)
				if app.observed.is_empty(): app._unhandled_input(event)
				keys[("Shift+" if shifted else "") + OS.get_keycode_string(code)] = app.observed.duplicate()
				app._reset_live_repeat_state()
		var tabs := {}
		var panel = hud._explorer_cockpit.panel
		for tab in panel._tabs.get_tab_count():
			panel._tabs.current_tab = tab
			await _frames(tree, 2)
			var nodes: Array = []
			var buttons := {}
			for node in panel.find_children("*", "Control", true, false):
				if not node.is_visible_in_tree(): continue
				var role := str(node.get_meta("semantic_role", node.get_meta("cockpit_role", "")))
				var identity := _identity(node, panel)
				nodes.append([identity, node.get_class(), role])
				if node is Button and node.has_meta("practice_action"):
					app.observed.clear()
					node.pressed.emit()
					buttons[identity] = {"text": node.text, "commands": app.observed.duplicate(), "action": node.get_meta("binding_action", ""), "disabled": node.disabled}
				if node is OptionButton:
					for index in node.item_count:
						app.observed.clear()
						if not node.is_item_disabled(index): node.item_selected.emit(index)
						buttons[identity + "/item_%d" % index] = {"text": node.get_item_text(index), "commands": app.observed.duplicate(), "disabled": node.is_item_disabled(index)}
			tabs[str(panel._tabs.get_child(tab).name)] = {"nodes": nodes, "buttons": buttons}
		actual[str(dimension)] = {"keys": keys, "tabs": tabs, "piece_helper": _helper_rows(hud._piece_control_strip._groups, dimension), "view_helper": _helper_rows(hud._live_view_control_strip._groups, dimension, true), "action_bindings": _legacy_binding_signature()}
		actual[str(dimension)] = _legacy_id_projection(actual[str(dimension)], dimension)
		app.observing = false
	scene.queue_free()
	await tree.process_frame
	tree.root.size = previous_size
	tree.root.content_scale_size = previous_scale
	tree.root.min_size = previous_minimum
	for action in saved:
		InputMap.erase_action(action)
		if saved[action] != null:
			InputMap.add_action(action)
			for event in saved[action]: InputMap.action_add_event(action, event)
	if OS.get_environment(WRITE_ENV) == "1":
		var file := FileAccess.open(BASELINE, FileAccess.WRITE)
		if file == null:
			failures.append("Explorer lock: cannot write baseline")
		else:
			file.store_string(JSON.stringify(actual, "\t", true) + "\n")
			failures.append("Explorer lock: baseline written; review and rerun without " + WRITE_ENV)
	else:
		var expected = JSON.parse_string(FileAccess.get_file_as_string(BASELINE))
		if not expected is Dictionary:
			failures.append("Explorer lock: missing or invalid baseline")
		else:
			failures.append_array(_differences(actual, expected))
			# Prove the checker catches command, control and helper regressions.
			for section in ["keys", "tabs", "piece_helper", "view_helper"]:
				var mutated: Dictionary = actual.duplicate(true)
				mutated["2"][section] = null
				if _differences(mutated, actual).is_empty():
					failures.append("Explorer lock comparator missed mutation in " + section)
	completed = true
	return failures

func _identity(node: Node, root: Node) -> String:
	if node == root: return "."
	var label := str(node.name)
	if label.begins_with("@"):
		var ordinal := 0
		for sibling in node.get_parent().get_children():
			if sibling == node: break
			if sibling.get_class() == node.get_class(): ordinal += 1
		label = "%s_%d" % [node.get_class(), ordinal]
	return _identity(node.get_parent(), root) + "/" + label

func _frames(tree: SceneTree, count: int) -> void:
	for frame in count: await tree.process_frame


func _differences(actual: Dictionary, expected: Dictionary) -> Array:
	var differences: Array = []
	if actual.keys() != expected.keys():
		# JSON serialization sorts fixture dictionaries; compare sets, not order.
		var actual_keys := actual.keys()
		var expected_keys := expected.keys()
		actual_keys.sort()
		expected_keys.sort()
		if actual_keys != expected_keys: differences.append("Explorer lock: dimension set differs")
	for dimension in actual:
		if JSON.stringify(actual[dimension], "", true) == JSON.stringify(expected.get(dimension), "", true): continue
		for section in actual[dimension]:
			if JSON.stringify(actual[dimension][section], "", true) != JSON.stringify(expected.get(dimension, {}).get(section), "", true):
				differences.append("Explorer lock: %sD %s differs from reviewed baseline" % [dimension, section])
				if section == "keys" and actual[dimension][section] is Dictionary:
					for key in actual[dimension][section]:
						var expected_key: Variant = expected.get(dimension, {}).get(section, {}).get(key)
						if actual[dimension][section][key] != expected_key:
							differences.append("Explorer lock: %sD %s actual=%s expected=%s" % [dimension, key, actual[dimension][section][key], expected_key])
	return differences


func _helper_rows(groups: Array, dimension: int, view: bool = false) -> Array:
	var rows: Array = []
	for group in groups:
		var role := str(group.get("cockpit_role", ""))
		for item in group.get("items", []):
			var actions: Array = []
			var metadata: Dictionary = item[2] if item.size() > 2 and item[2] is Dictionary else {}
			if view:
				for field in ["action", "negative_action", "positive_action"]:
					if not str(metadata.get(field, "")).is_empty(): actions.append(metadata[field])
			else:
				var owner := "live_%dd_" % (3 if dimension == 2 else dimension)
				var keys := str(item[0]).replace(" ", "").split("/")
				for action in _legacy_action_names:
					var eligible := str(action).begins_with(owner) or str(action).begins_with("explorer_")
					if role == "translate": eligible = eligible and "_move_" in str(action)
					elif role == "rotate": eligible = eligible and "_rotate_" in str(action)
					elif role == "session": eligible = action == ("explorer_replace_piece" if str(item[1]) == "Replace piece" else owner + "reset")
					if eligible and Contract._display_key(action).replace(" ", "") in keys: actions.append(action)
			actions.sort()
			rows.append({"role": role, "item": item.duplicate(true), "action_ids": actions})
	return rows


func _legacy_binding_signature() -> String:
	var rows: Array = JSON.parse_string(Contract.binding_signature())
	return JSON.stringify(rows.filter(func(row): return _legacy_action_names.has(str(row[0]))))


# Explicit namespace migration only. Keys, commands, node identities, binding
# values and helper text still compare against the untouched Phase 0 fixture.
func _legacy_id_projection(value: Variant, dimension: int) -> Variant:
	if value is Array:
		return value.map(func(item): return _legacy_id_projection(item, dimension))
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = _legacy_id_projection(value[key], dimension)
		return result
	if not value is String: return value
	var owner := "live_%dd_" % (3 if dimension == 2 else dimension)
	var aliases := {
		"explorer_move_y_neg": "explorer_move_up", "explorer_move_y_pos": "explorer_move_down",
		"explorer_2d_move_y_neg": "live_3d_move_z_neg", "explorer_2d_move_y_pos": "live_3d_move_z_pos",
		"explorer_retry": owner + "reset", "explorer_reset_view": "reset", "explorer_fit_view": "replay_fit_view",
		"explorer_view_xz_neg": "view_zx_neg", "explorer_view_xz_pos": "view_zx_pos",
		"explorer_view_xw_neg": "view_xw_neg", "explorer_view_xw_pos": "view_xw_pos",
		"explorer_view_zw_neg": "view_zw_neg", "explorer_view_zw_pos": "view_zw_pos",
	}
	if aliases.has(value): return aliases[value]
	if value.begins_with("explorer_camera_"): return value.replace("explorer_camera_", "live_4d_camera_")
	if value.begins_with("explorer_move_") and value not in ["explorer_move_up", "explorer_move_down"]: return value.replace("explorer_", owner)
	if value.begins_with("explorer_rotate_"): return value.replace("explorer_", owner)
	return value
