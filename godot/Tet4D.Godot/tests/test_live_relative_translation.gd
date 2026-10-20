extends RefCounted

const SetupSpec = preload("res://scripts/ui/game_setup/game_setup_spec.gd")

# Fixed specification data: RDS_3D_TETRIS §5 and RDS_4D_TETRIS §6.
# Each row is [Right, Forward, Slice+] as signed canonical axes. These are
# handwritten oracles, never obtained from ControlFrameMapping or the HUD.
# Columns are yaw 0, +90, 180, -90 respectively.
const THREE_D := [["+X", "-Z"], ["-Z", "-X"], ["-X", "+Z"], ["+Z", "+X"]]
const FOUR_D := [
	{"action": "", "slots": [1, 2, 3, 4], "rows": [["+X", "+Z", "+W"], ["+Z", "-X", "+W"], ["-X", "-Z", "+W"], ["-Z", "+X", "+W"]]},
	{"action": "view_zx_pos", "slots": [-3, 2, 1, 4], "rows": [["-Z", "+X", "+W"], ["+X", "+Z", "+W"], ["+Z", "-X", "+W"], ["-X", "-Z", "+W"]]},
	{"action": "view_zx_neg", "slots": [3, 2, -1, 4], "rows": [["+Z", "-X", "+W"], ["-X", "-Z", "+W"], ["-Z", "+X", "+W"], ["+X", "+Z", "+W"]]},
	{"action": "view_xw_pos", "slots": [4, 2, 3, -1], "rows": [["+W", "+Z", "-X"], ["+Z", "-W", "-X"], ["-W", "-Z", "-X"], ["-Z", "+W", "-X"]]},
	{"action": "view_xw_neg", "slots": [-4, 2, 3, 1], "rows": [["-W", "+Z", "+X"], ["+Z", "+W", "+X"], ["+W", "-Z", "+X"], ["-Z", "-W", "+X"]]},
	{"action": "view_zw_pos", "slots": [1, 2, 4, -3], "rows": [["+X", "+W", "-Z"], ["+W", "-X", "-Z"], ["-X", "-W", "-Z"], ["-W", "+X", "-Z"]]},
	{"action": "view_zw_neg", "slots": [1, 2, -4, 3], "rows": [["+X", "-W", "+Z"], ["-W", "-X", "+Z"], ["-X", "+W", "+Z"], ["+W", "+X", "+Z"]]},
]
# Separate fixed command and displacement oracles, including exact opposites.
const AXES := {
	"+X": ["move_x_pos", [1, 0, 0, 0], "-X"], "-X": ["move_x_neg", [-1, 0, 0, 0], "+X"],
	"+Z": ["move_z_pos", [0, 0, 1, 0], "-Z"], "-Z": ["move_z_neg", [0, 0, -1, 0], "+Z"],
	"+W": ["move_w_pos", [0, 0, 0, 1], "-W"], "-W": ["move_w_neg", [0, 0, 0, -1], "+W"],
}
var failures: Array = []
var moves_checked := 0
var completed := false


func run() -> Array:
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := (load("res://scenes/trace_replay.tscn") as PackedScene).instantiate()
	tree.root.add_child(root)
	var app = root.get_node("App")
	# Disable real-time gravity/repetition before any frame can advance gameplay.
	# Input still reaches the real app, native bridge, renderer and HUD.
	app.set_process(false)
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node("ReplayHud")
	hud._set_onboarding_visible(false)
	app._camera_rig.set_process(false)
	app._camera_rig.set_presentation_preferences(1.0, false)
	for dimension in [3, 4]:
		var mode := "live_%dd" % dimension
		hud._game_setup_model.set_mode(mode)
		hud._game_setup_model.select_control_frame("translation_frame", "relative")
		app._start_configured_live_game(_setup(mode, dimension))
		await tree.process_frame
		await tree.process_frame
		app._fit_view()
		_check(not app._pending_fit_view, "%s actual viewport fit completed" % mode)
		_check(app._mode == mode and not app._live_snapshot_game_over(), "%s launched actual native Live session" % mode)
		_check_frame(app, hud, "relative", mode)
		_check(app._current_snapshot.get("locked_cells", []).is_empty(), "%s empty deterministic board" % mode)
		if dimension == 3:
			for quarter in range(4):
				_set_yaw(app, dimension, float(quarter) * PI / 2.0)
				_check_row(app, dimension, THREE_D[quarter], "3D yaw %d" % (quarter * 90))
			_set_yaw(app, 3, 0.0)
			_drag(app, MOUSE_BUTTON_LEFT, Vector2(-PI / 2.0 / app._camera_rig.orbit_sensitivity, 0))
			_check_row(app, 3, THREE_D[0], "3D presented yaw before interpolation")
			app._camera_rig._process(10.0)
			_check_row(app, 3, THREE_D[1], "3D presented yaw after interpolation")
		else:
			for basis in FOUR_D:
				_action(app, "reset")
				if not str(basis.action).is_empty():
					_action(app, basis.action)
				_check(app._live_4d_basis.slots() == basis.slots, "4D exact %s slots" % basis.action)
				for quarter in range(4):
					_set_yaw(app, dimension, float(quarter) * PI / 2.0)
					_check_row(app, dimension, basis.rows[quarter], "4D %s L=%d" % [basis.action, quarter * 90])
				print("Live translation covered B=%s with all four L yaws" % [basis.slots])
			_action(app, "reset")
			_set_yaw(app, 4, deg_to_rad(44.0))
			_check_row(app, 4, FOUR_D[0].rows[0], "4D L=44 quantizes to zero")
			_action(app, "live_4d_camera_yaw_right")
			_check_row(app, 4, FOUR_D[0].rows[1], "4D keyboard L=49 quantizes to 90")
			app._camera_rig.nudge_yaw(PI / 2.0)
			_check_row(app, 4, FOUR_D[0].rows[1], "4D outer V yaw excluded")
		_lifecycle(app, hud, dimension)
		_absolute(app, hud, dimension)
	print("Live relative translation: %d command + displacement cases checked; %d failures" % [moves_checked, failures.size()])
	if failures.is_empty():
		print("LIVE_RELATIVE_TRANSLATION_PASS: 3D + 4D")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	completed = true
	return failures


func _setup(mode: String, dimension: int) -> Dictionary:
	var shape := [6, 10, 6] if dimension == 3 else [6, 10, 6, 6]
	return {
		"schema_version": 2, "contract_version": SetupSpec.BoardExtentContractScript.CONTRACT_VERSION,
		"mode": mode, "board_preset_id": "large", "board_shape": shape,
		"piece_set_id": "embedded_2d", "random_mode": "fixed_seed", "seed": 1337,
		"initial_speed_level": 1, "topology_profile": SetupSpec.bounded_topology_profile(shape),
	}


func _check_frame(app, hud, expected: String, label: String) -> void:
	_check(hud.live_control_frames().get("translation_frame") == expected, "%s configured %s" % [label, expected])
	_check(app._translation_frame == expected, "%s effective %s" % [label, expected])


func _action(app, name: String) -> void:
	var event := InputEventAction.new()
	event.action = name
	event.pressed = true
	app._unhandled_input(event)
	event.pressed = false
	app._unhandled_input(event)


func _drag(app, button_index: int, delta: Vector2) -> void:
	var button := InputEventMouseButton.new()
	button.button_index = button_index
	button.pressed = true
	app._unhandled_input(button)
	var motion := InputEventMouseMotion.new()
	motion.relative = delta
	app._unhandled_input(motion)
	button.pressed = false
	app._unhandled_input(button)


func _set_yaw(app, dimension: int, yaw: float) -> void:
	var cells := _cells(app)
	var rig = app._camera_rig
	var before: float = rig.control_frame_yaw() if dimension == 3 else app._live_4d_local_orientation.local_yaw
	# Actual left-drag path: outer orbit is active, slice-local L is passive.
	var scale: float = rig.orbit_sensitivity * rig.presentation_snapshot().get("sensitivity_factor", 1.0)
	_drag(app, MOUSE_BUTTON_LEFT, Vector2((yaw - before) / scale * (-1.0 if dimension == 3 else 1.0), 0))
	# Advance camera interpolation by an explicit delta, never wall-clock time.
	rig._process(10.0)
	var actual: float = rig.control_frame_yaw() if dimension == 3 else app._live_4d_local_orientation.local_yaw
	_check(absf(wrapf(actual - yaw, -PI, PI)) < 0.001, "%dD presented yaw reached %s, got %s" % [dimension, yaw, actual])
	_check(_cells(app) == cells, "%dD view changes preserve native cells" % dimension)


func _cells(app) -> Array:
	var cells: Array = []
	for cell in app._current_snapshot.get("active_cells", []):
		cells.append(cell.get("position", []).duplicate())
	return cells


func _move(app, dimension: int, intent: String, axis: String, label: String, repeat_delta: float = -1.0) -> void:
	var before := _cells(app)
	_check(not before.is_empty(), "%s has an active piece" % label)
	if repeat_delta < 0.0:
		_action(app, "live_%dd_%s" % [dimension, intent])
	else:
		app._process_live_input_repeat(repeat_delta)
	var after := _cells(app)
	var expected: Array = AXES[axis]
	_check(str(app._current_snapshot.get("last_command")) == expected[0], "%s command expected %s got %s" % [label, expected[0], app._current_snapshot.get("last_command")])
	_check(app._current_snapshot.get("last_command_status") == "accepted", "%s movement must be accepted, got %s" % [label, app._current_snapshot.get("last_command_status")])
	_check(after.size() == before.size(), "%s active piece cell count stable" % label)
	for index in mini(before.size(), after.size()):
		for axis_index in dimension:
			_check(int(after[index][axis_index]) - int(before[index][axis_index]) == int(expected[1][axis_index]), "%s cell %d axis %d delta expected %d got %d" % [label, index, axis_index, expected[1][axis_index], int(after[index][axis_index]) - int(before[index][axis_index])])
	moves_checked += 1


func _check_row(app, dimension: int, row: Array, label: String) -> void:
	var intents := [["move_x_pos", "move_x_neg"], ["move_z_neg", "move_z_pos"], ["move_w_pos", "move_w_neg"]]
	for index in row.size():
		var before := _cells(app)
		_move(app, dimension, intents[index][0], row[index], label + " " + intents[index][0])
		_move(app, dimension, intents[index][1], AXES[row[index]][2], label + " " + intents[index][1])
		_check(_cells(app) == before, "%s opposite pair %s restores every cell" % [label, intents[index][0]])


func _lifecycle(app, hud, dimension: int) -> void:
	_action(app, "reset")
	if dimension == 4:
		_action(app, "view_xw_pos")
	_set_yaw(app, dimension, PI / 2.0)
	var row: Array = THREE_D[1] if dimension == 3 else FOUR_D[3].rows[1]
	var cells := _cells(app)
	var framing: Dictionary = app._camera_rig.presentation_snapshot()
	var zoom := InputEventMouseButton.new()
	zoom.button_index = MOUSE_BUTTON_WHEEL_UP
	zoom.pressed = true
	app._unhandled_input(zoom)
	_drag(app, MOUSE_BUTTON_RIGHT, Vector2(23, -17))
	var changed: Dictionary = app._camera_rig.presentation_snapshot()
	_check(changed.zoom_multiplier != framing.zoom_multiplier and changed.target_focus != framing.target_focus, "%dD actual zoom/pan changed framing" % dimension)
	_check(_cells(app) == cells, "%dD zoom/pan preserves native cells" % dimension)
	_check_row(app, dimension, row, "%dD zoom/pan" % dimension)
	var fit := InputEventMouseButton.new()
	fit.button_index = MOUSE_BUTTON_LEFT
	fit.double_click = true
	fit.pressed = true
	app._unhandled_input(fit)
	_check(is_equal_approx(app._camera_rig.presentation_snapshot().zoom_multiplier, 1.0), "%dD Fit restored zoom baseline" % dimension)
	_check_row(app, dimension, row, "%dD fitted framing" % dimension)
	hud._restart_game_button.pressed.emit()
	_check_frame(app, hud, "relative", "after Restart Game")
	_check_row(app, dimension, row, "%dD Restart Game preserves view" % dimension)
	# Poll real held Input with explicit DAS/ARR deltas. Changing the view while
	# held must remap the next repeat rather than reuse the keydown's command.
	var action := "live_%dd_move_x_pos" % dimension
	Input.action_press(action)
	_move(app, dimension, "move_x_pos", row[0], "%dD held initial" % dimension)
	app._process_live_input_repeat(0.0)
	var held_cells := _cells(app)
	app._process_live_input_repeat(0.05)
	_check(_cells(app) == held_cells, "%dD DAS does not repeat early" % dimension)
	_move(app, dimension, "move_x_pos", row[0], "%dD DAS repeat" % dimension, 0.25)
	_set_yaw(app, dimension, PI)
	var next_row: Array = THREE_D[2] if dimension == 3 else FOUR_D[3].rows[2]
	_move(app, dimension, "move_x_pos", next_row[0], "%dD ARR remaps held intent" % dimension, 0.1)
	Input.action_release(action)
	app._process_live_input_repeat(0.0)
	held_cells = _cells(app)
	app._process_live_input_repeat(1.0)
	_check(_cells(app) == held_cells, "%dD release stops repeats" % dimension)
	# Return the deliberately repeated moves to the interior before checking
	# Reset View. A wall rejection must fail, never masquerade as a mapping pass.
	_move(app, dimension, "move_x_neg", AXES[next_row[0]][2], "%dD undo ARR" % dimension)
	_set_yaw(app, dimension, PI / 2.0)
	for index in range(2):
		_move(app, dimension, "move_x_neg", AXES[row[0]][2], "%dD undo held %d" % [dimension, index])
	held_cells = _cells(app)
	_action(app, "reset")
	_check_frame(app, hud, "relative", "after Reset View")
	_check(_cells(app) == held_cells, "%dD Reset View preserves native cells" % dimension)
	_check_row(app, dimension, THREE_D[0] if dimension == 3 else FOUR_D[0].rows[0], "%dD Reset View" % dimension)
	app._enter_replay_mode()
	app._start_configured_live_game(_setup("live_%dd" % dimension, dimension))
	_check_frame(app, hud, "relative", "after mode re-entry")
	_check_row(app, dimension, THREE_D[0] if dimension == 3 else FOUR_D[0].rows[0], "%dD mode re-entry" % dimension)
	_set_yaw(app, dimension, 3.0 * PI / 2.0)
	_check_row(app, dimension, THREE_D[3] if dimension == 3 else FOUR_D[0].rows[3], "%dD re-entry remaps" % dimension)


func _absolute(app, hud, dimension: int) -> void:
	hud._game_setup_model.select_control_frame("translation_frame", "absolute")
	app._start_configured_live_game(_setup("live_%dd" % dimension, dimension))
	_check_frame(app, hud, "absolute", "%dD intentional Absolute" % dimension)
	if dimension == 4:
		_action(app, "view_zw_neg")
	for quarter in range(4):
		_set_yaw(app, dimension, float(quarter) * PI / 2.0)
		_check_row(app, dimension, ["+X", "-Z"] if dimension == 3 else ["+X", "-Z", "+W"], "%dD Absolute yaw %d" % [dimension, quarter])


func _check(ok: bool, message: String) -> void:
	if not ok:
		failures.append("Live relative translation: " + message)
