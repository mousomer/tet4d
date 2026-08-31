extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["live Viewer restoration test requires SceneTree and replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	var hud = root.get_node_or_null("ReplayHud")
	if app == null or hud == null:
		root.queue_free()
		return ["live Viewer restoration test requires app and HUD owners"]

	var mode_shapes := {
		"live_2d": [6, 10],
		"live_3d": [6, 10, 6],
		"live_4d": [5, 10, 4, 4],
	}
	for mode in mode_shapes:
		await _assert_live_return(tree, app, hud, mode, mode_shapes[mode], failures)
	await _assert_paused_live_return(tree, app, hud, failures)
	await _assert_replay_viewer_isolation(tree, app, hud, failures)

	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _assert_live_return(
	tree: SceneTree,
	app,
	hud,
	mode: String,
	shape: Array,
	failures: Array
) -> void:
	app._start_configured_live_game(_setup(mode, shape))
	await tree.process_frame
	await tree.process_frame
	_dispatch_hold(app, mode)
	await tree.process_frame
	app._camera_rig.nudge_yaw(0.37)
	app._camera_rig.nudge_pitch(0.19)
	app._camera_rig.zoom(-1.0)
	if mode == "live_4d":
		app._set_live_4d_local_orientation(0.42, 0.17)
		app._apply_live_4d_basis_turn("xw", 1)
		await tree.process_frame
	var bridge_instance_before: int = app._live_bridge.get_instance_id()
	var native_before := _native_surface(app, mode)
	var pre_exit_view: Dictionary = app._camera_rig.presentation_snapshot()

	app._return_to_main_menu()
	await tree.process_frame
	await _click_text_prefix(tree, hud, "Advanced / Diagnostics", failures)
	await _click_text_prefix(tree, hud, "Replay Demos", failures)
	await _click_text(tree, hud, "Viewer", failures)
	await tree.process_frame
	await tree.process_frame

	if hud.current_screen() != hud.SCREEN_VIEWER:
		failures.append("%s Viewer navigation should return to the Viewer screen" % mode)
	if app._live_bridge.get_instance_id() != bridge_instance_before:
		failures.append("%s Viewer return must preserve the native bridge instance" % mode)
	if _native_surface(app, mode) != native_before:
		failures.append("%s Viewer return must preserve gameplay, Hold, NEXT, and Ghost truth" % mode)
	if not _session_started(app, mode):
		failures.append("%s Viewer return must retain the existing native live session" % mode)
	if not bool(app._renderer.current_bounds().get("ok", false)):
		failures.append("%s Viewer return must restore valid live renderer bounds" % mode)
	if app._renderer._grid_root.get_child_count() == 0:
		failures.append("%s Viewer return must restore live board grid geometry" % mode)
	if app._renderer._cell_root.get_child_count() == 0:
		failures.append("%s Viewer return must restore active/locked/Ghost cell geometry" % mode)
	if app._camera_rig._camera == null or not app._camera_rig._camera.current:
		failures.append("%s Viewer return must reactivate the live camera owner" % mode)
	if app._live_mode_paused():
		failures.append("%s Viewer return must restore the pre-navigation running state" % mode)
	if hud.live_interaction_owns_input():
		failures.append("%s Viewer return must not retain a transient UI input owner" % mode)
	var focus_owner := tree.root.gui_get_focus_owner()
	if focus_owner != null and hud._viewer_screen.is_ancestor_of(focus_owner):
		failures.append("%s Viewer return must restore live keyboard capture" % mode)
	_assert_canonical_reentry(app, mode, pre_exit_view, failures)

	var state_before_fit := _native_surface(app, mode)
	var view_before_fit: Dictionary = app._camera_rig.presentation_snapshot()
	var basis_before_fit: String = app._live_4d_basis.key() if mode == "live_4d" else ""
	var local_before_fit: Dictionary = app._live_4d_local_orientation.snapshot() if mode == "live_4d" else {}
	app._fit_view()
	await tree.process_frame
	var view_after_fit: Dictionary = app._camera_rig.presentation_snapshot()
	for key in ["current_yaw", "current_pitch", "current_roll", "projection", "horizontal_reflection_active"]:
		if view_after_fit.get(key) != view_before_fit.get(key):
			failures.append("%s Fit after Viewer return must preserve %s" % [mode, key])
	if mode == "live_4d" and (
		app._live_4d_basis.key() != basis_before_fit
		or app._live_4d_local_orientation.snapshot() != local_before_fit
	):
		failures.append("live_4d Fit after Viewer return must preserve B and L")
	if _native_surface(app, mode) != state_before_fit:
		failures.append("%s Fit after Viewer return must preserve gameplay" % mode)

	var state_before_temporary_navigation := _native_surface(app, mode)
	var view_before_temporary_navigation: Dictionary = app._camera_rig.presentation_snapshot()
	var basis_before_temporary_navigation: String = app._live_4d_basis.key() if mode == "live_4d" else ""
	var local_before_temporary_navigation: Dictionary = app._live_4d_local_orientation.snapshot() if mode == "live_4d" else {}
	hud.show_screen(hud.SCREEN_SETTINGS)
	await tree.process_frame
	await _click_text(tree, hud, "Viewer", failures)
	await tree.process_frame
	if app._camera_rig.presentation_snapshot() != view_before_temporary_navigation:
		failures.append("%s temporary Viewer navigation must preserve its live view" % mode)
	if mode == "live_4d" and (
		app._live_4d_basis.key() != basis_before_temporary_navigation
		or app._live_4d_local_orientation.snapshot() != local_before_temporary_navigation
	):
		failures.append("live_4d temporary Viewer navigation must preserve B and L")
	if _native_surface(app, mode) != state_before_temporary_navigation:
		failures.append("%s temporary Viewer navigation must preserve gameplay" % mode)


func _assert_paused_live_return(tree: SceneTree, app, hud, failures: Array) -> void:
	app._live_4d_paused = true
	app._refresh_live_4d_snapshot()
	var native_before := _native_surface(app, "live_4d")
	app._return_to_main_menu()
	await tree.process_frame
	await _click_text_prefix(tree, hud, "Advanced / Diagnostics", failures)
	await _click_text_prefix(tree, hud, "Replay Demos", failures)
	await _click_text(tree, hud, "Viewer", failures)
	await tree.process_frame
	await tree.process_frame
	if not app._live_4d_paused:
		failures.append("live_4d Viewer return must preserve a pre-navigation paused state")
	if _native_surface(app, "live_4d") != native_before:
		failures.append("paused live_4d Viewer return must preserve gameplay truth")


func _assert_canonical_reentry(app, mode: String, pre_exit_view: Dictionary, failures: Array) -> void:
	var expected: Array = {
		"live_2d": [0.0, 0.0, false],
		"live_3d": [CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD, false],
		"live_4d": [CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD, true],
	}[mode]
	var view: Dictionary = app._camera_rig.presentation_snapshot()
	if (
		not is_equal_approx(float(view.get("current_yaw", 0.0)), float(expected[0]))
		or not is_equal_approx(float(view.get("current_pitch", 0.0)), float(expected[1]))
		or not is_equal_approx(float(view.get("current_roll", 0.0)), 0.0)
		or bool(view.get("horizontal_reflection_active", false)) != bool(expected[2])
	):
		failures.append("%s Viewer return must establish its canonical E4 presentation" % mode)
	if (
		is_equal_approx(float(view.get("current_yaw", 0.0)), float(pre_exit_view.get("current_yaw", 0.0)))
		and is_equal_approx(float(view.get("current_pitch", 0.0)), float(pre_exit_view.get("current_pitch", 0.0)))
	):
		failures.append("%s Main Menu exit must not preserve the prior noncanonical pose" % mode)
	if mode == "live_4d" and (
		not app._live_4d_basis.is_identity()
		or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0}
	):
		failures.append("live_4d Viewer return must rebuild canonical B and L")


func _assert_replay_viewer_isolation(tree: SceneTree, app, hud, failures: Array) -> void:
	app._enter_replay_mode()
	await tree.process_frame
	var document_before = app._current_document
	var camera_before: Dictionary = app._camera_rig.presentation_snapshot()
	hud.show_screen(hud.SCREEN_BROWSER)
	await tree.process_frame
	await _click_text(tree, hud, "Viewer", failures)
	await tree.process_frame
	if app._mode != app.MODE_REPLAY or app._current_document != document_before:
		failures.append("replay Viewer navigation must retain replay ownership and document")
	if app._camera_rig.presentation_snapshot() != camera_before:
		failures.append("replay Viewer navigation must not execute live camera restoration")


func _native_surface(app, mode: String) -> Dictionary:
	var bridge = app._live_bridge
	match mode:
		"live_2d":
			return {
				"hash": bridge.live_2d_state_hash(),
				"snapshot": JSON.parse_string(bridge.live_2d_snapshot_json()),
				"next": bridge.live_2d_next_piece_preview(),
				"hold": bridge.live_2d_held_piece_preview(),
				"hold_available": bridge.live_2d_hold_available(),
				"ghost": bridge.live_2d_hard_drop_destination(),
			}
		"live_3d":
			return {
				"hash": bridge.live_3d_state_hash(),
				"snapshot": JSON.parse_string(bridge.live_3d_snapshot_json()),
				"next": bridge.live_3d_next_piece_preview(),
				"hold": bridge.live_3d_held_piece_preview(),
				"hold_available": bridge.live_3d_hold_available(),
				"ghost": bridge.live_3d_hard_drop_destination(),
			}
		_:
			return {
				"hash": bridge.live_4d_state_hash(),
				"snapshot": JSON.parse_string(bridge.live_4d_snapshot_json()),
				"next": bridge.live_4d_next_piece_preview(),
				"hold": bridge.live_4d_held_piece_preview(),
				"hold_available": bridge.live_4d_hold_available(),
				"ghost": bridge.live_4d_hard_drop_destination(),
			}


func _dispatch_hold(app, mode: String) -> void:
	match mode:
		"live_2d":
			app._live_2d_command("hold")
		"live_3d":
			app._live_3d_command("hold")
		_:
			app._live_4d_command("hold")


func _session_started(app, mode: String) -> bool:
	match mode:
		"live_2d":
			return app._live_2d_session_started
		"live_3d":
			return app._live_3d_session_started
		_:
			return app._live_4d_session_started


func _setup(mode: String, shape: Array) -> Dictionary:
	return {
		"schema_version": 2,
		"contract_version": 1,
		"mode": mode,
		"board_preset_id": "standard",
		"board_shape": shape,
		"piece_set_id": "classic" if mode == "live_2d" else ("native_3d" if mode == "live_3d" else "standard_4d_5"),
		"random_mode": "fixed_seed",
		"seed": 1337,
		"initial_speed_level": 1,
		"topology_profile": {"contract_version": 1, "rank": shape.size(), "dimensions": shape.duplicate(), "seams": []},
	}


func _click_text(tree: SceneTree, root: Node, text: String, failures: Array) -> void:
	for child in root.find_children("*", "Button", true, false):
		var button := child as Button
		if button != null and button.is_visible_in_tree() and button.text == text:
			await _click(tree, button)
			return
	failures.append("expected visible %s navigation button" % text)


func _click_text_prefix(tree: SceneTree, root: Node, text: String, failures: Array) -> void:
	for child in root.find_children("*", "Button", true, false):
		var button := child as Button
		if button != null and button.is_visible_in_tree() and button.text.begins_with(text):
			await _click(tree, button)
			return
	failures.append("expected visible %s navigation button" % text)


func _click(tree: SceneTree, control: Control) -> void:
	var point := control.get_global_rect().get_center()
	for pressed in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = point
		event.global_position = point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = pressed
		tree.root.push_input(event)
		await tree.process_frame
