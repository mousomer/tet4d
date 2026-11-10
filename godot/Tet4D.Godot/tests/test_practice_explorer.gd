extends RefCounted

const Practice = preload("res://scripts/presentation/practice_explorer.gd")
const InputContract = preload("res://scripts/input/live_input_contract.gd")
const Bridge = preload("res://scripts/native/tet4d_core_bridge.gd")
var failures: Array = []
var completed := false


func run() -> Array:
	var bridge = Bridge.new()
	_check(bridge.is_available(), "native provider available")
	for dimension in [3, 4]:
		_model_contract(bridge, dimension)
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	tree.root.size = Vector2i(1280, 800)
	var root := (load("res://scenes/game_bootstrap.tscn") as PackedScene).instantiate()
	tree.root.add_child(root)
	var app = root.get_node("App")
	app.set_process(false)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node("ReplayHud")
	app._return_to_main_menu()
	var entry := InputEventKey.new()
	entry.keycode = KEY_E
	entry.pressed = true
	app._input(entry)
	_check(app._practice != null and app._practice.dimension() == 2 and app._mode == "live_2d", "main-menu E enters the 2D topology Explorer")
	await _menu_entry_route(app, hud, tree)
	await _application_2d(app, hud, tree)
	for dimension in [3, 4]:
		var previous_panel = hud._practice_panel
		previous_panel._tabs.current_tab = 0
		var previous_tabs_id: int = previous_panel._tabs.get_instance_id()
		app._practice_action("dimension_%d" % dimension)
		await tree.process_frame
		await tree.process_frame
		_check(hud._practice_panel._tabs.get_instance_id() == previous_tabs_id and hud._practice_panel._tabs.current_tab == 0, "%dD dimension switch retains the actual Explorer tabs and selection" % dimension)
		hud._practice_panel._tabs.current_tab = 0
		app._fit_view()
		var model = app._practice
		_check(model != null and model.dimension() == dimension, "%dD practice initialized" % dimension)
		var initial: Array = model.cells.duplicate(true)
		var hash_before := _native_hash(app, dimension)
		app._process(120.0)
		_check(model.cells == initial and _native_hash(app, dimension) == hash_before, "%dD elapsed time cannot move, lock or advance native state" % dimension)
		_check(hud._practice_panel._tabs.get_tab_count() == 2 and hud._practice_panel._tabs.get_child(0).name == "View" and hud._practice_panel._tabs.get_child(1).name == "Piece", "%dD Explorer prioritizes View and keeps piece controls secondary" % dimension)
		var panel_text := ""
		for label in hud._practice_panel.find_children("*", "Label", true, false):
			panel_text += label.text + "\n"
		_check(not panel_text.contains("Coordinates") and not panel_text.contains("Selected cell") and not panel_text.contains("Local view yaw"), "%dD Explorer omits raw debug readouts" % dimension)
		_check(hud._practice_panel.visible and not hud._piece_preview_row.visible, "%dD practice controls replace ordinary object controls" % dimension)
		_check(app._current_snapshot.probe_markers.is_empty(), "%dD entry draws no target or slice dot" % dimension)
		var target_buttons: Array = hud._practice_panel.find_children("*", "Button", true, false).filter(func(button): return button.get_meta("practice_action", "") == "target")
		_check(target_buttons.size() == 1, "%dD Piece page offers New target" % dimension)
		if target_buttons.size() == 1:
			target_buttons[0].pressed.emit()
			_check(model.target.size() == dimension and app._current_snapshot.probe_markers.size() == 1 and not model.cells.has(model.target), "%dD New target draws one marker away from the object" % dimension)
			model.target = []
			app._refresh_practice_snapshot()
		var active_nodes: Array = app._renderer._cell_root.get_children().filter(func(node): return node.get_meta("presentation_role", "") == "active")
		_check(active_nodes.size() > 1 and active_nodes[0].get_child_count() == active_nodes[1].get_child_count(), "%dD Explorer does not draw a separate origin dot on its first object cell" % dimension)
		_check(hud._piece_control_strip.is_visible_in_tree() and hud._live_view_control_strip.is_visible_in_tree(), "%dD object helper and unified VIEW helper remain accessible" % dimension)
		_check(hud._live_view_control_strip.get_parent() == hud._practice_panel.view_controls_host and not hud._live_4d_view_module.visible, "%dD VIEW helper is mounted once with the clickable controls, without a lower duplicate" % dimension)
		_check(hud._live_view_control_strip.get_combined_minimum_size().y >= hud._live_view_control_strip._groups_box.get_combined_minimum_size().y, "%dD full view helper reports its complete content height to cockpit fitting" % dimension)
		var piece_help: Dictionary = hud._piece_control_strip.deterministic_snapshot()
		_check(not piece_help.roles.has("drop") and not piece_help.roles.has("hold"), "%dD practice helper omits unsupported drop and hold" % dimension)
		_check(piece_help.plane_glyphs.size() == (3 if dimension == 3 else 6) and piece_help.compass_keys.size() >= 4, "%dD full helper includes all rotation glyphs and movement keys" % dimension)
		var help_text := JSON.stringify(piece_help)
		_check(help_text.contains("Z/X") and help_text.contains("Retry object"), "%dD full practice help includes MacBook-accessible Y keys and Retry" % dimension)
		var view_help: Dictionary = hud._live_view_control_strip.deterministic_snapshot()
		_check(view_help.roles.has("view_pointer") and view_help.roles.has("view_framing"), "%dD full view helper includes gestures and framing" % dimension)
		if dimension == 4:
			_check(view_help.roles.has("view_exact") and view_help.roles.has("view_orient"), "4D full helper includes basis and slice orientation")
		for button in hud._practice_panel.find_children("*", "Button", true, false):
			_check(button.focus_mode == Control.FOCUS_NONE, "%dD dynamically created controls preserve the live keyboard capture policy" % dimension)
		for tab in range(2):
			hud._practice_panel._tabs.current_tab = tab
			await tree.process_frame
			await tree.process_frame
			var page: ScrollContainer = hud._practice_panel._tabs.get_child(tab)
			_check(page.size.y > 0 and page.size.x > 0, "%dD tab %d has usable content geometry" % [dimension, tab])
			_check(hud._practice_panel.get_global_rect().end.x <= tree.root.get_visible_rect().end.x + 1.0, "%dD tab %d stays inside logical viewport width: panel=%s viewport=%s" % [dimension, tab, hud._practice_panel.get_global_rect(), tree.root.get_visible_rect()])
		hud._practice_panel._tabs.current_tab = 0
		app._ensure_live_game_paused_for_focus_loss()
		_check(not app._live_mode_paused(), "%dD gravity-free practice does not become stuck paused after focus loss" % dimension)
		var before: Array = model.cells.duplicate(true)
		for pair in [[KEY_Z, KEY_X], [KEY_PAGEUP, KEY_PAGEDOWN]]:
			var up := InputEventKey.new()
			up.keycode = pair[0]
			up.pressed = true
			app._unhandled_input(up)
			_check(model.cells != before, "%dD %s moves object up" % [dimension, OS.get_keycode_string(pair[0])])
			up.keycode = pair[1]
			app._unhandled_input(up)
			_check(model.cells == before, "%dD %s reverses Y movement" % [dimension, OS.get_keycode_string(pair[1])])
		await _check_stable_panel(tree, app, hud, dimension)
		await _check_view_and_replacement(tree, app, hud, dimension)
		await _check_layout_stability(tree, app, hud, dimension)
		await _check_unified_view_controls(tree, app, hud, dimension)
		if dimension == 4:
			await _check_y_view_controls(tree, app, hud)
		# Existing relative owner, exercised through the actual app dispatch.
		app._translation_frame = "relative"
		if dimension == 3:
			app._camera_rig.nudge_yaw(PI / 2.0)
			app._camera_rig._process(10.0)
		else:
			app._apply_live_4d_basis_turn("xw", 1)
			app._set_live_4d_local_orientation(PI / 2.0, 0.0)
		var expected: String = app._control_frame_mapping(dimension).translation_command("move_x_pos", "relative")
		_check(not hud._piece_control_strip.deterministic_snapshot().roles.has("drop"), "%dD camera/basis updates retain practice helper roles" % dimension)
		hud._apply_hud_density("compact" if hud._hud_density != "compact" else "standard")
		_check(hud._live_view_control_strip.deterministic_snapshot().roles.has("view_framing"), "%dD density refresh retains the full view helper" % dimension)
		_check(hud._live_view_control_strip.get_combined_minimum_size().y >= hud._live_view_control_strip._groups_box.get_combined_minimum_size().y, "%dD density refresh retains complete helper fitting height" % dimension)
		var oracle = Practice.new(bridge)
		_check(oracle.begin(app._current_snapshot), "query oracle initializes")
		oracle.cells = model.cells.duplicate(true)
		oracle.command(expected)
		var event := InputEventAction.new()
		event.action = "live_%dd_move_x_pos" % dimension
		event.pressed = true
		app._unhandled_input(event)
		_check(model.cells == oracle.cells, "%dD keyboard camera-relative displacement matches native query" % dimension)
		before = model.cells.duplicate(true)
		if dimension == 4:
			var basis: Array = app._live_4d_basis.slots()
			var presentation = app._renderer._presentation
			var followed: Array = presentation.active_layer_indices()
			_check(not followed.is_empty() and app._practice_slice == -1, "uninspected 4D emphasis follows the object like Play")
			app._practice_action("slice_pos")
			_check(model.cells == before and app._live_4d_basis.slots() == basis and app._practice_slice >= 0, "slice selection is independent of object and basis")
			var inspected: Array = app._renderer._presentation.active_layer_indices()
			_check(inspected.size() == 1 and not followed.has(inspected[0]) and app._renderer._presentation.projection.mapper.semantic_slice_coordinate(inspected[0]) == app._practice_slice, "first Slice step emphasizes the inspected layer beyond the object")
			var framed: Array = app._renderer._grid._active_frames.filter(func(frame): return frame.visible).map(func(frame): return int(frame.get_meta("presentation_layer")))
			_check(framed == inspected, "the active-slice frame draws the inspected layer")
			_check(app._current_snapshot.probe_markers.is_empty(), "slice inspection never draws an entry-point dot")
			app._practice_action("basis_zw_pos")
			_check(model.cells == before and app._practice_slice == -1 and not app._current_snapshot.has("inspected_slice"), "basis change preserves object and returns emphasis to the object")
			_check(hud._live_4d_basis_snapshot.slots == app._live_4d_basis.slots(), "in-place practice refresh keeps the displayed view basis current")
		app._practice_action("view_reset")
		_check(model.cells == before, "%dD composite view reset preserves object" % dimension)
		if dimension == 4:
			_check(app._practice_slice == -1 and app._live_4d_basis.is_identity(), "Reset View restores canonical basis and object-following slice emphasis")
		app._practice_action("retry")
		_check(model.cells == initial, "%dD deterministic retry restores exact initial object" % dimension)
		for forbidden in ["tick", "hard_drop", "hold", "soft_drop"]:
			app._practice_action(forbidden)
		_check(model.cells == initial and _native_hash(app, dimension) == hash_before, "%dD game actions cannot leak into Sandbox or native session" % dimension)
		app._return_to_main_menu()
		if dimension == 4:
			app._input(entry)
		else:
			app._practice_action("dimension_3")
		_check(app._is_live_viewer_active(), "%dD choosing Explorer again returns from the menu" % dimension)
		_check(app._practice == model and model.cells == initial, "%dD menu return retains detached practice" % dimension)
		app._practice_action("play")
		_check(not hud._live_view_control_strip.deterministic_snapshot().practice and hud._live_view_control_strip.get_parent() == hud._live_4d_view_module, "%dD Play restores the ordinary passive VIEW component" % dimension)
		_check(app._practice == null and not hud._practice_panel.visible and hud._piece_preview_row.visible, "%dD Play restores ordinary controls" % dimension)
		if dimension == 4:
			_check(not app._live_4d_basis._free_inspection and int(app._live_4d_basis.slots()[1]) == 2, "Play restores the Y-fixed gameplay basis")
		_check(hud._piece_control_strip.deterministic_snapshot().roles.has("drop"), "%dD Play restores normal drop helper" % dimension)
		active_nodes = app._renderer._cell_root.get_children().filter(func(node): return node.get_meta("presentation_role", "") == "active")
		_check(active_nodes.size() > 1 and active_nodes[0].get_child_count() == active_nodes[1].get_child_count() + 1, "%dD ordinary Play retains its existing origin marker" % dimension)
		var play_hash := _native_hash(app, dimension)
		for key in [KEY_Z, KEY_X]:
			var practice_key := InputEventKey.new()
			practice_key.keycode = key
			practice_key.pressed = true
			app._unhandled_input(practice_key)
		_check(_native_hash(app, dimension) == play_hash, "%dD practice Y shortcuts do not leak into ordinary Play" % dimension)
		var live_before: Dictionary = app._current_snapshot.duplicate(true)
		app._process(app._live_gravity_interval_seconds)
		_check(app._current_snapshot != live_before, "%dD ordinary Play has automatic native gravity again" % dimension)
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	completed = true
	return failures


func _model_contract(bridge, dimension: int) -> void:
	var dims: Array = [8, 10, 8] if dimension == 3 else [8, 10, 8, 8]
	var source: Array = [[0, 0, 0], [1, 0, 0], [1, 1, 0]] if dimension == 3 else [[0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0]]
	var snapshot := {"dimension": dimension, "board_shape": dims, "active_cells": []}
	for cell in source:
		snapshot.active_cells.append({"position": cell})
	var model = Practice.new(bridge)
	_check(model.begin(snapshot), "%dD fixture initialized" % dimension)
	var initial: Array = model.cells.duplicate(true)
	var expected: Array = [[3, 4, 3], [4, 4, 3], [4, 5, 3]] if dimension == 3 else [[3, 4, 3, 3], [4, 4, 3, 3], [4, 5, 3, 3]]
	_check(initial == expected, "%dD fixed coordinate oracle for native normalization/centering" % dimension)
	var face_steps: Array = model.neighbors()
	_check(face_steps[0].target == ([2, 4, 3] if dimension == 3 else [2, 4, 3, 3]), "%dD native -X neighbor matches canonical coordinate oracle" % dimension)
	for axis in "xyzw".substr(0, dimension):
		_check(model.command("move_%s_pos" % axis) and model.command("move_%s_neg" % axis), "%dD %s both directions accepted" % [dimension, axis])
		_check(model.cells == initial, "%dD opposite %s restores exact coordinates" % [dimension, axis])
	for plane in ["xy", "xz", "yz", "xw", "yw", "zw"]:
		if dimension == 3 and "w" in plane:
			continue
		for turn in range(4):
			_check(model.command("rotate_%s_pos" % plane), "%dD %s quarter-turn accepted" % [dimension, plane])
		_check(model.cells == initial, "%dD four %s turns restore exact pose" % [dimension, plane])
		model.command("rotate_%s_pos" % plane)
		model.command("rotate_%s_neg" % plane)
		_check(model.cells == initial, "%dD inverse %s restores exact pose" % [dimension, plane])
	# Explicit wall exhaustion: reject the whole object, including Y's top edge.
	for axis in "xyzw".substr(0, dimension):
		model.retry()
		for attempt in range(12):
			model.command("move_%s_neg" % axis)
		var wall: Array = model.cells.duplicate(true)
		_check(not model.command("move_%s_neg" % axis) and model.cells == wall, "%dD %s wall rejection is atomic" % [dimension, axis])
		_check(model.neighbors().size() == dimension * 2, "%dD native neighbor directions explicit" % dimension)
	model.retry()
	_check(model.cells == initial, "%dD retry restores initial native geometry" % dimension)
	var detached: Dictionary = model.snapshot(true, 3 if dimension == 4 else 2, 0)
	_check(detached.probe_markers.size() == dimension * 2, "%dD only requested neighbor dots are drawn" % dimension)
	_check(model.place_target(), "%dD New target finds a native-legal target" % dimension)
	var first_target: Array = model.target.duplicate()
	_check(model.snapshot(false, 3 if dimension == 4 else 2, -1).probe_markers.size() == 1, "%dD New target explicitly adds one target marker" % dimension)
	_check(not model.cells.has(first_target) and first_target[1] != model.cells[0][1], "%dD target starts away from the object and needs Y movement" % dimension)
	# Reach it through ordinary deliberate commands, one axis at a time.
	var reached := true
	var anchor: Array = model.cells[0].duplicate()
	for axis in dimension:
		var delta: int = int(first_target[axis]) - int(anchor[axis])
		for step in absi(delta):
			reached = model.command("move_%s_%s" % ["xyzw"[axis], "pos" if delta > 0 else "neg"]) and reached
	_check(reached and model.cells.has(first_target), "%dD the marked target is reachable by deliberate moves" % dimension)
	model.retry()
	_check(model.place_target(), "%dD a second target is available" % dimension)
	_check(signi(int(first_target[1]) - int(initial[0][1])) == -signi(int(model.target[1]) - int(initial[0][1])), "%dD successive targets alternate Y direction" % dimension)
	model.target = []
	_check(detached.state_hash == "" and detached.practice and detached.locked_cells.is_empty(), "practice rendering never claims gameplay identity or locks")
	detached.active_cells.clear()
	_check(model.cells == initial, "render inputs cannot alias authoritative query results")
	_check(not model.command("move_w_neg") if dimension == 3 else not model.command("rotate_xq_pos"), "invalid dimensional command rejected")
	var narrow_shape: Array = [2, 4, 2] if dimension == 3 else [2, 4, 2, 2]
	var square: Array = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]] if dimension == 3 else [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [1, 1, 0, 0]]
	var narrow := {"dimension": dimension, "board_shape": narrow_shape, "active_cells": []}
	for cell in square:
		narrow.active_cells.append({"position": cell})
	_check(model.begin(narrow), "%dD an even-width piece fits an exactly matching even board extent" % dimension)
	var tiny := {"dimension": dimension, "board_shape": [1, 4, 1] if dimension == 3 else [1, 4, 1, 1], "piece_set_id": "embedded_2d", "active_cells": [{"position": [0, 1, 0] if dimension == 3 else [0, 1, 0, 0]}]}
	_check(model.begin(tiny), "replacement boundary fixture initializes")
	var tiny_cells: Array = model.cells.duplicate(true)
	_check(not model.replace_piece(0) and model.cells == tiny_cells and model.selected_piece == -1, "a native catalogue piece that does not fit is rejected atomically")
	_check(not model.replace_piece(-1) and not model.replace_piece(9999) and model.cells == tiny_cells, "unavailable replacements preserve the previous object")


func _native_hash(app, dimension: int) -> String:
	return app._live_bridge.live_3d_state_hash() if dimension == 3 else app._live_bridge.live_4d_state_hash()


func _check_stable_panel(tree: SceneTree, app, hud, dimension: int) -> void:
	var panel = hud._practice_panel
	var dimension_controls: Array = panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id())
	panel._tabs.current_tab = 0
	panel.configure(4 if dimension == 3 else 3)
	panel.configure(dimension)
	_check(panel._tabs.current_tab == 0 and dimension_controls == panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id()), "%dD dimension changes retain Explorer tabs and controls" % dimension)
	panel._tabs.current_tab = 1
	for frame in range(4):
		await tree.process_frame
	var scroll: ScrollContainer = panel._tabs.get_child(1)
	scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)
	await tree.process_frame
	var position := scroll.scroll_vertical
	var panel_id: int = panel.get_instance_id()
	var button_ids: Array = panel.find_children("*", "Button", true, false).map(func(button): return button.get_instance_id())
	var helper_ids: Array = hud._piece_control_strip.find_children("*", "Label", true, false).map(func(label): return label.get_instance_id())
	var events := {"theme": 0, "reparent": 0}
	panel._title.theme_changed.connect(func(): events.theme += 1)
	hud._piece_control_strip.tree_exiting.connect(func(): events.reparent += 1)
	for key in [KEY_Z, KEY_X, KEY_Z, KEY_X]:
		var event := InputEventKey.new()
		event.keycode = key
		event.pressed = true
		app._unhandled_input(event)
		await tree.process_frame
		_check(hud._practice_panel.get_instance_id() == panel_id and panel._tabs.current_tab == 1, "%dD movement preserves Explorer panel identity and selected tab" % dimension)
		_check(scroll.scroll_vertical == position, "%dD movement preserves side-panel scroll position" % dimension)
	_check(events.theme == 0 and events.reparent == 0, "%dD movement neither restyles the panel nor reparents helper controls" % dimension)
	_check(button_ids == panel.find_children("*", "Button", true, false).map(func(button): return button.get_instance_id()), "%dD movement preserves every Explorer button" % dimension)
	_check(helper_ids == hud._piece_control_strip.find_children("*", "Label", true, false).map(func(label): return label.get_instance_id()), "%dD movement preserves helper rows" % dimension)
	panel._tabs.current_tab = 0


func _check(ok: bool, message: String) -> void:
	if not ok:
		failures.append("Practice Explorer: " + message)


func _check_view_and_replacement(tree: SceneTree, app, hud, dimension: int) -> void:
	var model = app._practice
	var original_piece: int = model.selected_piece
	var original_cells: Array = model.cells.duplicate(true)
	var original_target: Array = model.target.duplicate()
	var original_cell: int = model.selected_cell
	var hash_before := _native_hash(app, dimension)
	var panel = hud._practice_panel
	var dimension_controls: Array = panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id())
	panel._tabs.current_tab = 0
	panel.configure(4 if dimension == 3 else 3)
	panel.configure(dimension)
	_check(panel._tabs.current_tab == 0 and dimension_controls == panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id()), "%dD dimension changes retain Explorer tabs and controls" % dimension)
	panel._tabs.current_tab = 1
	await tree.process_frame
	var scroll: ScrollContainer = panel._tabs.get_child(1)
	scroll.scroll_vertical = 20
	await tree.process_frame
	var scroll_position := scroll.scroll_vertical
	var controls: Array = panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id())
	var piece_rows: Array = hud._piece_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id())
	var view_rows: Array = hud._live_view_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id())
	if dimension == 3:
		app._camera_rig.nudge_yaw(PI)
		app._camera_rig._process(10.0)
	else:
		app._set_live_4d_local_orientation(PI, 0.0)
	app._publish_legend_screen_directions()
	hud._live_binding_signature = "stale-test-binding-signature"
	hud._window_mode_poll_accumulator = 1.0
	hud._process(0.3)
	_check(piece_rows == hud._piece_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id()), "%dD periodic binding refresh preserves helper rows" % dimension)
	var operations := ["view_fit", "view_reset", "neighbors", "neighbors", "cell", "retry", "dimension_%d" % dimension]
	if dimension == 4:
		operations.append_array(["basis_xw_pos", "basis_xw_neg", "basis_zw_pos", "basis_zw_neg", "slice_pos", "slice_neg", "view_reset"])
	for operation in operations:
		app._practice_action(operation)
		app._publish_legend_screen_directions()
		await tree.process_frame
		_check(piece_rows == hud._piece_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id()), "%dD %s preserves piece helper row instances" % [dimension, operation])
		_check(view_rows == hud._live_view_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id()), "%dD %s preserves view helper row instances" % [dimension, operation])
		_check(panel._tabs.current_tab == 1 and scroll.scroll_vertical == scroll_position, "%dD %s preserves the selected right pane and scroll" % [dimension, operation])
	_check(model.piece_names().size() > 1 and original_piece >= 0, "%dD configured native catalogue supplies selectable pieces" % dimension)
	var choice := posmod(original_piece + 1, model.piece_names().size())
	app._practice_action("target")
	var marked_target: Array = model.target.duplicate()
	var basis: Array = app._live_4d_basis.slots()
	var orientation: Dictionary = app._live_4d_local_orientation.snapshot()
	var inspected_slice: int = app._practice_slice
	var camera: Dictionary = app._camera_rig.presentation_snapshot()
	panel._pieces.item_selected.emit(choice)
	_check(model.selected_piece == choice and app._current_snapshot.current_piece == model.piece_names()[choice], "%dD native piece selector replaces the object" % dimension)
	var replacement: Array = model.cells.duplicate(true)
	app._practice_action("move_y_neg")
	app._practice_action("retry")
	_check(model.cells == replacement, "%dD Retry restores the replacement's baseline" % dimension)
	var replace_key := InputEventKey.new()
	replace_key.keycode = KEY_SPACE
	replace_key.pressed = true
	app._input(replace_key)
	_check(model.selected_piece == posmod(choice + 1, model.piece_names().size()), "%dD Space replaces the piece through the actual input interception path" % dimension)
	_check(not app._live_mode_paused(), "%dD replacement shortcut leaves practice controls active" % dimension)
	replace_key.echo = true
	app._input(replace_key)
	_check(model.selected_piece == posmod(choice + 1, model.piece_names().size()), "%dD held Space does not replace repeatedly" % dimension)
	replace_key.echo = false
	replace_key.keycode = KEY_P
	app._unhandled_input(replace_key)
	_check(model.selected_piece == posmod(choice + 2, model.piece_names().size()), "%dD P remains a replacement alias" % dimension)
	var valid_piece: int = model.selected_piece
	var valid_cells: Array = model.cells.duplicate(true)
	app._practice_action("piece_unknown")
	_check(model.selected_piece == valid_piece and model.cells == valid_cells, "%dD malformed selector actions do not silently choose piece zero" % dimension)
	_check(app._live_4d_basis.slots() == basis and app._live_4d_local_orientation.snapshot() == orientation and app._practice_slice == inspected_slice, "%dD replacement preserves basis/orientation/slice" % dimension)
	_check(app._camera_rig.presentation_snapshot() == camera, "%dD replacement preserves camera pose and framing" % dimension)
	_check(controls == panel.find_children("*", "BaseButton", true, false).map(func(node): return node.get_instance_id()) and panel._tabs.current_tab == 1, "%dD replacement preserves selector, buttons and selected pane" % dimension)
	_check(piece_rows == hud._piece_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id()) and view_rows == hud._live_view_control_strip.find_children("*", "Label", true, false).map(func(node): return node.get_instance_id()), "%dD replacement preserves both helper panes" % dimension)
	_check(_native_hash(app, dimension) == hash_before, "%dD all inspection/replacement operations preserve the native game queue and hash" % dimension)
	app._practice_action("piece_%d" % original_piece)
	_check(model.cells == original_cells, "%dD original catalogue choice can be restored" % dimension)
	_check(model.target == marked_target, "%dD piece replacement preserves the marked target" % dimension)
	model.target = original_target
	model.selected_cell = original_cell
	app._practice_action("view_reset")
	panel._tabs.current_tab = 0


# Node identity cannot detect a fit search replay: measure every rendered-frame
# boundary, including the temporary scale=1 jump that used to follow Space.
func _check_layout_stability(tree: SceneTree, app, hud, dimension: int) -> void:
	var original_size := tree.root.size
	var original_minimum := tree.root.min_size
	tree.root.min_size = Vector2i.ZERO
	var original_piece: int = app._practice.selected_piece
	var original_target: Array = app._practice.target.duplicate()
	var original_neighbors: bool = app._practice_neighbors
	var panel = hud._practice_panel
	var cockpit = hud._live_cockpit
	for window_size in [Vector2i(1280, 800), Vector2i(1280, 720), Vector2i(1024, 720)]:
		tree.root.size = window_size
		panel._tabs.current_tab = 1
		for frame in 180:
			await tree.process_frame
			if frame > 30 and cockpit.fit_settled():
				break
		_check(cockpit.fit_settled(), "%dD %s initial fit settles" % [dimension, window_size])
		var scroll: ScrollContainer = panel._tabs.get_child(1)
		scroll.scroll_vertical = 20
		await tree.process_frame
		var before := _layout_snapshot(hud)
		var operations := ["space", "move_y_neg", "rotate_xy_pos", "retry", "piece_0", "boundary_rejection", "cell", "neighbors", "target", "view_fit", "view_reset", "long_feedback", "camera_turn"]
		if dimension == 4:
			operations.append_array(["basis_xw_pos", "slice_pos", "slice_neg", "basis_xw_neg", "basis_xy_pos", "basis_xy_neg", "basis_yz_pos", "basis_yz_neg", "basis_yw_pos", "slice_pos", "slice_neg", "basis_yw_neg"])
		for operation in operations:
			if operation == "space":
				var event := InputEventKey.new()
				event.keycode = KEY_SPACE
				event.pressed = true
				app._input(event)
			elif operation == "boundary_rejection":
				for attempt in int(app._current_snapshot.board_shape[1]) + 1:
					app._practice_action("move_y_neg")
				_check(app._practice.feedback.begins_with("Object unchanged:"), "%dD boundary feedback fixture reaches native rejection" % dimension)
			elif operation == "long_feedback":
				app._practice.feedback = "Object unchanged: blocked boundary. ".repeat(30)
				app._refresh_practice_snapshot()
			elif operation == "camera_turn":
				if dimension == 4:
					app._set_live_4d_local_orientation(PI / 2.0, 0.0)
				else:
					app._camera_rig.nudge_yaw(PI / 2.0)
					app._camera_rig._process(10.0)
			else:
				app._practice_action(operation)
			var stable := true
			for frame in 24:
				await tree.process_frame
				stable = _same_layout(before, _layout_snapshot(hud)) and stable
			_check(stable, "%dD %s %s keeps panel/board geometry, fit scales, scrollbars, tab and scroll stable on every frame" % [dimension, window_size, operation])
			if operation == "long_feedback":
				var feedback_scroll: ScrollContainer = panel._feedback.get_parent()
				var bar := feedback_scroll.get_v_scroll_bar()
				_check(bar.max_value > bar.page and panel._feedback.text.begins_with(app._practice.feedback), "%dD long feedback remains complete and scrollable inside its allocation" % dimension)
		app._practice_action("retry")
		app._practice_action("view_reset")
	var feedback_slot: ScrollContainer = panel._feedback.get_parent()
	var previous_height := feedback_slot.custom_minimum_size.y
	var font_size: int = panel._feedback.get_theme_font_size("font_size")
	panel._feedback.add_theme_font_size_override("font_size", font_size * 2)
	await tree.process_frame
	_check(feedback_slot.custom_minimum_size.y > previous_height, "%dD readout allocation responds to font changes" % dimension)
	panel._feedback.remove_theme_font_size_override("font_size")
	tree.root.min_size = original_minimum
	tree.root.size = original_size
	app._practice_action("piece_%d" % original_piece)
	app._practice.target = original_target
	app._practice_neighbors = original_neighbors
	app._practice_action("view_reset")
	app._practice_action("retry")
	for frame in 90:
		await tree.process_frame


func _layout_snapshot(hud) -> Dictionary:
	var cockpit = hud._live_cockpit
	var panel = hud._practice_panel
	var scroll: ScrollContainer = panel._tabs.get_child(panel._tabs.current_tab)
	return {
		"panel": panel.get_global_rect(), "board": hud._game_viewport_container.get_global_rect(),
		"side": cockpit.side_scroll.get_global_rect(), "deck": cockpit.control_deck.get_global_rect(),
		"side_scale": cockpit.side_fit.fit_scale, "deck_scale": cockpit.deck_fit.fit_scale,
		"side_bar": cockpit.side_scroll.get_v_scroll_bar().visible,
		"deck_bar": cockpit.deck_scroll.get_v_scroll_bar().visible,
		"tab": panel._tabs.current_tab, "scroll": scroll.scroll_vertical,
	}


func _same_layout(before: Dictionary, after: Dictionary) -> bool:
	for key in before:
		if before[key] is Rect2:
			if not (before[key] as Rect2).is_equal_approx(after[key]):
				return false
		elif before[key] is float:
			if not is_equal_approx(before[key], after[key]):
				return false
		elif before[key] != after[key]:
			return false
	return true


func _check_y_view_controls(tree: SceneTree, app, hud) -> void:
	var panel = hud._practice_panel
	panel._tabs.current_tab = 0
	var model = app._practice
	var cells: Array = model.cells.duplicate(true)
	var hash_before := _native_hash(app, 4)
	var expected := {"xy": [2, -1, 3, 4], "yz": [1, 3, -2, 4], "yw": [1, 4, 3, -2]}
	for plane in expected:
		app._practice_action("view_reset")
		var buttons: Array = panel.find_children("*", "Button", true, false)
		var plus = buttons.filter(func(button): return button.get_meta("practice_action", "") == "basis_%s_pos" % plane)[0]
		var minus = buttons.filter(func(button): return button.get_meta("practice_action", "") == "basis_%s_neg" % plane)[0]
		_check(plus.is_visible_in_tree() and minus.is_visible_in_tree(), "%s view controls are visible on the primary View page" % plane.to_upper())
		plus.pressed.emit()
		await tree.process_frame
		_check(app._live_4d_basis.slots() == expected[plane], "%s button rotates the view in its exact plane" % plane.to_upper())
		_check(model.cells == cells and _native_hash(app, 4) == hash_before, "%s view turn never rotates the piece or advances gameplay" % plane.to_upper())
		_check(app._control_frame_mapping(4).axis_for_local("y").axis == absi(int(expected[plane][1])) - 1, "%s relative object rotations follow the displayed vertical axis" % plane.to_upper())
		_check(app._camera_rig._orientation_basis_snapshot.visible_axes[1] == app._live_4d_basis.indicator_snapshot().visible_axes[1], "%s camera axis indicator follows the turned vertical slot" % plane.to_upper())
		if plane == "yw":
			_check(app._live_4d_basis.layer_count(app._current_snapshot.board_shape) == app._current_snapshot.board_shape[1], "YW turns slice along canonical Y using its true extent")
		minus.pressed.emit()
		_check(app._live_4d_basis.is_identity(), "%s inverse view button restores the basis" % plane.to_upper())
	app._practice_action("view_reset")
	panel._tabs.current_tab = 0


func _check_unified_view_controls(tree: SceneTree, app, hud, dimension: int) -> void:
	var panel = hud._practice_panel
	panel._tabs.current_tab = 0
	var hash_before := _native_hash(app, dimension)
	var cells: Array = app._practice.cells.duplicate(true)
	var groups: Array = InputContract.practice_view_control_groups(app._mode)
	if dimension == 4:
		var exact: Array = groups.filter(func(group): return group.cockpit_role == "view_exact")[0].items
		_check(exact.size() == 6, "unified VIEW includes helper bindings for all six planes")
		for item in exact:
			var metadata: Dictionary = item[2]
			for prefix in ["negative_", "positive_"]:
				app._practice_action("view_reset")
				var command: String = metadata[prefix + "command"]
				var action: String = metadata[prefix + "action"]
				var buttons: Array = panel.find_children("*", "Button", true, false)
				var button = buttons.filter(func(candidate): return candidate.get_meta("practice_action", "") == command)[0]
				_check(button.get_meta("binding_action") == action and button.text == str(metadata[prefix + "binding"]).replace("Shift+", "⇧"), "%s keycap displays its authoritative keyboard binding" % command)
				button.pressed.emit()
				var clicked: Array = app._live_4d_basis.slots()
				app._practice_action("view_reset")
				var key: InputEventKey = InputContract.binding_events(action)[0].duplicate()
				key.pressed = true
				app._input(key)
				_check(app._live_4d_basis.slots() == clicked and not app._live_4d_basis.is_identity(), "%s shortcut and clickable helper execute exactly the same rotation" % command)
				key.echo = true
				app._input(key)
				_check(app._live_4d_basis.slots() == clicked, "%s held shortcut does not repeat or invoke the unshifted plane" % command)
		# A rebound/cleared action must change the same keycap and dispatch path.
		var action := "explorer_view_xy_neg"
		var saved: Array = InputMap.action_get_events(action)
		InputMap.action_erase_events(action)
		var rebound := InputEventKey.new()
		rebound.keycode = KEY_F9
		InputMap.action_add_event(action, rebound)
		hud._refresh_configured_control_reference()
		var buttons: Array = panel.find_children("*", "Button", true, false)
		var keycap = buttons.filter(func(button): return button.get_meta("binding_action", "") == action)[0]
		_check(keycap.text == "F9", "rebinding updates the unified helper keycap")
		app._practice_action("view_reset")
		rebound.pressed = true
		app._input(rebound)
		_check(app._live_4d_basis.slots() == [-2, 1, 3, 4], "rebound Explorer shortcut rotates XY rather than another plane")
		InputMap.action_erase_events(action)
		hud._refresh_configured_control_reference()
		buttons = panel.find_children("*", "Button", true, false)
		keycap = buttons.filter(func(button): return button.get_meta("binding_action", "") == action)[0]
		_check(keycap.text == "Unbound", "clearing a shortcut does not print or resurrect its default")
		app._practice_action("view_reset")
		app._input(rebound)
		_check(app._live_4d_basis.is_identity(), "cleared shortcut stops dispatching")
		var cleared_default := InputEventKey.new()
		cleared_default.keycode = KEY_1
		cleared_default.shift_pressed = true
		cleared_default.pressed = true
		app._input(cleared_default)
		app._unhandled_input(cleared_default)
		_check(app._live_4d_basis.is_identity(), "cleared Shift+1 never falls through to the plain XZ shortcut")
		for event in saved:
			InputMap.action_add_event(action, event)
		hud._refresh_configured_control_reference()
	# 3D and 4D share look helpers and command identities.
	app._practice_action("view_reset")
	var yaw_before: float = app._live_4d_local_orientation.local_yaw if dimension == 4 else app._camera_rig.presentation_snapshot().current_yaw
	var look_key: InputEventKey = InputContract.binding_events("live_4d_camera_yaw_left")[0].duplicate()
	look_key.pressed = true
	app._input(look_key)
	var yaw_after: float = app._live_4d_local_orientation.local_yaw if dimension == 4 else app._camera_rig.presentation_snapshot().current_yaw
	_check(not is_equal_approx(yaw_before, yaw_after), "%dD look helper shortcut changes camera orientation" % dimension)
	_check(app._practice.cells == cells and _native_hash(app, dimension) == hash_before, "%dD helper buttons/shortcuts leave object coordinates and native gameplay unchanged" % dimension)
	app._practice_action("view_reset")
	for frame in 90:
		await tree.process_frame


func _menu_entry_route(app, hud, tree) -> void:
	# Leave the Explorer first: the Main Menu retains a live Explorer session,
	# so only a cleared one proves the card itself opens 2D.
	app._practice_action("play")
	_check(app._practice == null, "Play clears the Explorer before the card route")
	app._return_to_main_menu()
	await tree.process_frame
	var card := hud._main_menu_screen.find_child("CommandCard__Explorer", true, false) as Button
	_check(card != null, "Main Menu lists the Explorer card")
	if card == null:
		return
	card.pressed.emit()
	await tree.process_frame
	await tree.process_frame
	_check(app._practice != null and app._practice.dimension() == 2 and app._mode == "live_2d", "Main Menu Explorer card opens the 2D topology Explorer")
	_check(hud._practice_panel != null and hud._practice_panel._topology.is_visible_in_tree(), "Main Menu Explorer entry shows the topology selector")
	for dimension in [3, 4, 2]:
		var buttons: Array = hud._practice_panel.find_children("*", "Button", true, false).filter(func(button): return button.get_meta("practice_action", "") == "dimension_%d" % dimension)
		_check(buttons.size() == 1, "Explorer panel offers one %dD button" % dimension)
		if buttons.size() != 1:
			return
		buttons[0].pressed.emit()
		await tree.process_frame
		await tree.process_frame
		_check(app._practice != null and app._practice.dimension() == dimension, "Explorer panel %dD button switches the Explorer to %dD" % [dimension, dimension])
	app._practice_action("dimension_3")
	var retained = app._practice
	app._return_to_main_menu()
	await tree.process_frame
	card.pressed.emit()
	await tree.process_frame
	_check(app._practice == retained and app._practice.dimension() == 3 and app._is_live_viewer_active(), "Main Menu Explorer card resumes a retained 3D Explorer instead of resetting to 2D")
	app._practice_action("dimension_2")
	await tree.process_frame
	await tree.process_frame


func _application_2d(app, hud, tree) -> void:
	var play_before: String = app._live_bridge.live_2d_state_hash()
	app._practice_action("dimension_2")
	await tree.process_frame
	await tree.process_frame
	_check(app._practice != null and app._practice.dimension() == 2, "2D entry")
	if app._practice == null or app._practice.dimension() != 2:
		return
	_check(hud._practice_panel._topology.is_visible_in_tree(), "2D topology selector visible")
	_check(app._live_bridge.live_2d_state_hash() == play_before, "2D entry leaves Play untouched")
	var initial: Dictionary = app._practice.topology_2d.current.duplicate(true)
	app._process(120.0)
	_check(app._practice.topology_2d.current == initial, "2D no automatic gravity")
	for topology in 4:
		app._practice_action("topology_%d" % topology)
		for command in ["move_x_neg", "move_x_pos", "move_y_neg", "move_y_pos"]:
			for step in 23:
				app._practice_action(command)
				var native: Dictionary = app._live_bridge.explorer_2d({"op": "snapshot"})
				var drawn: Array = app._current_snapshot.active_cells
				_check(drawn.size() == native.piece.cells.size(), "2D rendered count")
				for index in drawn.size():
					_check(drawn[index].position == native.piece.cells[index].coordinate and drawn[index].cell_id == native.piece.cells[index].id and drawn[index].frame == native.piece.cells[index].frame, "2D rendered canonical ID/coordinate/frame")
		app._practice_action("retry")
		_check(app._practice.topology_2d.current.piece == app._practice.topology_2d.current.initial_piece, "2D UI Retry exact")
	var before_view: Dictionary = app._live_bridge.explorer_2d({"op": "snapshot"})
	app._practice_action("view_fit")
	app._practice_action("view_reset")
	_check(app._live_bridge.explorer_2d({"op": "snapshot"}) == before_view, "2D view independent")
	for command in ["rotate_cw", "rotate_ccw", "soft_drop", "hard_drop", "hold", "rotate_xy_pos"]:
		app._live_2d_command(command)
	_check(app._live_bridge.explorer_2d({"op": "snapshot"}) == before_view, "2D unsupported controls do not attempt transport")
	_check(app._live_bridge.live_2d_state_hash() == play_before, "2D app Play isolation")
	app._practice_action("play")
	_check(app._practice == null and app._mode == "live_2d", "2D return to Play")
	var play_start: String = app._live_bridge.live_2d_state_hash()
	app._live_2d_command("soft_drop")
	_check(app._live_bridge.live_2d_state_hash() != play_start, "2D ordinary gameplay restored")
	app._start_practice(4)
	await tree.process_frame
