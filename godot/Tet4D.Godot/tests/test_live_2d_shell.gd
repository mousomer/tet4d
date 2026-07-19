extends RefCounted

const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var replay_hint := ReplayHudScript.replay_hint_text()
	var live_hint := ReplayHudScript.live_2d_hint_text()
	var live_3d_hint := ReplayHudScript.live_3d_hint_text()
	var live_4d_hint := ReplayHudScript.live_4d_hint_text()
	if not live_hint.contains("A/D") or not live_hint.contains("Hard Drop") or not live_hint.contains("Tab Play 3D"):
		failures.append("live 2D hint text should expose movement, drop, and Tab-to-Live-3D controls")
	if live_hint.contains("Frame"):
		failures.append("live 2D hint text should not expose replay frame controls")
	if replay_hint.contains("Hard Drop") or replay_hint.contains("Rotate CW"):
		failures.append("replay hint text should not expose live gameplay controls")
	if not live_3d_hint.contains("R/T") or not live_3d_hint.contains("F/G") or not live_3d_hint.contains("V/B") or not live_3d_hint.contains("Backspace Restart Game"):
		failures.append("live 3D hint text should expose direct rotation and reset controls")
	if not live_4d_hint.contains("Q / E W- / W+") or not live_4d_hint.contains("Y / U XW") or not live_4d_hint.contains("H / J YW") or not live_4d_hint.contains("N / M ZW") or not live_4d_hint.contains("I / K") or not live_4d_hint.contains(", / . Roll") or not live_4d_hint.contains("Shift Drag Roll") or not live_4d_hint.contains("Tab Replay Demos") or live_4d_hint.contains("Q/Esc Quit"):
		failures.append("live 4D hint text should expose W controls, camera controls, six rotation planes, and Esc-only quit")
	if absf(TraceReplayAppScript.LIVE_GRAVITY_INTERVAL_SECONDS - 0.5) > 0.001:
		failures.append("live gravity shell interval should default to 0.5 seconds")
	if TraceReplayAppScript.LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS <= 0.0:
		failures.append("live horizontal repeat interval should be configured")
	_assert_live_gameplay_hud_copy(failures)

	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		failures.append("trace replay scene should load for live input map test")
		return failures
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		failures.append("live input map test requires SceneTree")
		return failures
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app := root.get_node_or_null("App")
	if app == null:
		failures.append("trace replay scene should include App for live shell checks")
	else:
		app._enter_live_2d_mode()
		await tree.process_frame
		var live_snapshot: Dictionary = app._current_snapshot
		if str(live_snapshot.get("trace_type", "")) != "live_2d":
			failures.append("live mode should create a live snapshot")
		var initial_piece := str(live_snapshot.get("current_piece", ""))
		if initial_piece != "I":
			failures.append("live mode should start with native I piece, got %s" % initial_piece)
		app._dispatch_live_gameplay_command("hard_drop")
		live_snapshot = app._current_snapshot
		if str(live_snapshot.get("current_piece", "")) != "O":
			failures.append("live hard drop should route to C++ and spawn O")
		if str(app._hud._summary_label.text).find("SCORE 5") == -1 or str(app._hud._summary_label.text).find("LOCKED") == -1:
			failures.append("Live 2D HUD should expose score and lock feedback after hard drop")
		app._enter_replay_mode()
		await tree.process_frame
		var replay_hash := str(app._live_bridge.live_2d_state_hash())
		var live_event := InputEventAction.new()
		live_event.action = "live_hard_drop"
		live_event.pressed = true
		app._unhandled_input(live_event)
		if str(app._live_bridge.live_2d_state_hash()) != replay_hash:
			failures.append("replay mode should not dispatch live gameplay commands")
		app._enter_live_2d_mode()
		live_snapshot = app._current_snapshot
		if app._live_2d_paused:
			failures.append("switching back to Live 2D should resume the selected live mode")
		if str(live_snapshot.get("current_piece", "")) != "O":
			failures.append("switching back to Live 2D should preserve the native live session")
		var q_event_2d := InputEventKey.new()
		q_event_2d.keycode = KEY_Q
		q_event_2d.pressed = true
		var hash_before_q_2d := str(app._live_bridge.live_2d_state_hash())
		app._unhandled_input(q_event_2d)
		if app._mode != TraceReplayAppScript.MODE_LIVE_2D:
			failures.append("Q should not leave Live 2D")
		if str(app._live_bridge.live_2d_state_hash()) != hash_before_q_2d:
			failures.append("Q should not dispatch a Live 2D gameplay command")
		var live_2d_focus_space_event := InputEventKey.new()
		live_2d_focus_space_event.keycode = KEY_SPACE
		live_2d_focus_space_event.pressed = true
		var hash_before_live_2d_space := str(app._live_bridge.live_2d_state_hash())
		app._input(live_2d_focus_space_event)
		if str(app._live_bridge.live_2d_state_hash()) == hash_before_live_2d_space:
			failures.append("Space should dispatch Live 2D hard_drop before UI accept handling")
		if str(app._current_snapshot.get("last_command", "")) != "hard_drop":
			failures.append("Space should map to Live 2D hard_drop")
		app._enter_live_3d_mode()
		if app._mode != TraceReplayAppScript.MODE_LIVE_3D:
			failures.append("app should enter Live 3D mode on direct call, got %s" % str(app._mode))
		var direct_live_3d_snapshot = JSON.parse_string(app._live_bridge.live_3d_snapshot_json())
		if typeof(direct_live_3d_snapshot) == TYPE_DICTIONARY and str(direct_live_3d_snapshot.get("trace_type", "")) != "live_3d":
			failures.append("direct native live 3D snapshot had trace type %s" % str(direct_live_3d_snapshot.get("trace_type", "")))
		elif typeof(direct_live_3d_snapshot) != TYPE_DICTIONARY:
			failures.append("direct native live 3D snapshot should parse")
		var live_3d_snapshot: Dictionary = app._current_snapshot
		if str(live_3d_snapshot.get("trace_type", "")) != "live_3d":
			failures.append("live 3D mode should create a live 3D snapshot, got %s" % str(live_3d_snapshot.get("trace_type", "")))
		if str(live_3d_snapshot.get("current_piece", "")) != "I3":
			failures.append("live 3D should start with native I3 piece, got %s" % str(live_3d_snapshot.get("current_piece", "")))
		var live_3d_initial_hash := str(app._live_bridge.live_3d_state_hash())
		app._dispatch_live_3d_gameplay_command("move_x_pos")
		if str(app._live_bridge.live_3d_state_hash()) == live_3d_initial_hash:
			failures.append("live 3D X movement should route to C++")
		app._dispatch_live_3d_gameplay_command("rotate_xz_pos")
		if str(app._current_snapshot.get("last_rotation_plane", "")) != "XZ":
			failures.append("live 3D XZ rotation should route through C++")
		if str(app._current_snapshot.get("last_rotation_label", "")) != "XZ+":
			failures.append("live 3D XZ rotation should expose a signed HUD rotation label")
		app._dispatch_live_3d_gameplay_command("move_z_pos")
		if str(app._current_snapshot.get("last_rotation_label", "")) != "XZ+":
			failures.append("live 3D should preserve the last signed rotation label after movement")
		app._dispatch_live_3d_gameplay_command("hard_drop")
		if str(app._current_snapshot.get("current_piece", "")) != "O3":
			failures.append("live 3D hard drop should route to C++ and spawn O3")
		if str(app._hud._summary_label.text).find("O3 > L3") == -1 or str(app._hud._summary_label.text).find("LOCKED") == -1:
			failures.append("Live 3D HUD should expose the new piece queue and lock feedback")
		app._enter_replay_mode()
		await tree.process_frame
		var replay_3d_hash := str(app._live_bridge.live_3d_state_hash())
		var live_3d_event := InputEventAction.new()
		live_3d_event.action = "live_3d_hard_drop"
		live_3d_event.pressed = true
		app._unhandled_input(live_3d_event)
		if str(app._live_bridge.live_3d_state_hash()) != replay_3d_hash:
			failures.append("replay mode should not dispatch live 3D gameplay commands")
		app._enter_live_3d_mode()
		if app._mode != TraceReplayAppScript.MODE_LIVE_3D:
			failures.append("app should enter Live 3D mode, got %s" % str(app._mode))
		if app._live_3d_paused:
			failures.append("switching back to Live 3D should resume the selected live mode")
		if str(app._current_snapshot.get("current_piece", "")) != "O3":
			failures.append("switching back to Live 3D should preserve the native live session")
		var q_event_3d := InputEventKey.new()
		q_event_3d.keycode = KEY_Q
		q_event_3d.pressed = true
		var hash_before_q_3d := str(app._live_bridge.live_3d_state_hash())
		app._unhandled_input(q_event_3d)
		if app._mode != TraceReplayAppScript.MODE_LIVE_3D:
			failures.append("Q should not leave Live 3D")
		if str(app._live_bridge.live_3d_state_hash()) != hash_before_q_3d:
			failures.append("Q should not dispatch a Live 3D gameplay command")
		var live_3d_focus_space_event := InputEventKey.new()
		live_3d_focus_space_event.keycode = KEY_SPACE
		live_3d_focus_space_event.pressed = true
		var hash_before_live_3d_space := str(app._live_bridge.live_3d_state_hash())
		app._input(live_3d_focus_space_event)
		if str(app._live_bridge.live_3d_state_hash()) == hash_before_live_3d_space:
			failures.append("Space should dispatch Live 3D hard_drop before UI accept handling")
		if str(app._current_snapshot.get("last_command", "")) != "hard_drop":
			failures.append("Space should map to Live 3D hard_drop")
		app._enter_live_4d_mode()
		if app._mode != TraceReplayAppScript.MODE_LIVE_4D:
			failures.append("app should enter Live 4D mode on direct call, got %s" % str(app._mode))
		var direct_live_4d_snapshot = JSON.parse_string(app._live_bridge.live_4d_snapshot_json())
		if typeof(direct_live_4d_snapshot) == TYPE_DICTIONARY and str(direct_live_4d_snapshot.get("trace_type", "")) != "live_4d":
			failures.append("direct native live 4D snapshot had trace type %s" % str(direct_live_4d_snapshot.get("trace_type", "")))
		elif typeof(direct_live_4d_snapshot) != TYPE_DICTIONARY:
			failures.append("direct native live 4D snapshot should parse")
		var live_4d_snapshot: Dictionary = app._current_snapshot
		if str(live_4d_snapshot.get("trace_type", "")) != "live_4d":
			failures.append("live 4D mode should create a live 4D snapshot, got %s" % str(live_4d_snapshot.get("trace_type", "")))
		if str(live_4d_snapshot.get("current_piece", "")) != "TRACE_4D":
			failures.append("live 4D should start with native TRACE_4D piece, got %s" % str(live_4d_snapshot.get("current_piece", "")))
		if int(live_4d_snapshot.get("w_slice_count", 0)) != 4:
			failures.append("live 4D should expose W slice count")
		if app._camera_rig._current_view_preset != "LIVE_4D_FITTED_W_SLICE_VIEW":
			failures.append("live 4D should open in the fitted W-slice camera preset")
		if app._camera_rig._current_fit_state != "fit OK":
			failures.append("live 4D should open already fitted")
		var camera_hash_before := str(app._live_bridge.live_4d_state_hash())
		var live_4d_camera := app._camera_rig.get_node_or_null("Camera3D") as Camera3D
		if live_4d_camera == null:
			failures.append("Live 4D camera should exist for zoom checks")
		var fitted_camera_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var zoom_in_event := InputEventKey.new()
		zoom_in_event.keycode = KEY_EQUAL
		zoom_in_event.unicode = 43
		zoom_in_event.pressed = true
		app._input(zoom_in_event)
		if live_4d_camera != null and live_4d_camera.size >= fitted_camera_size:
			failures.append("Live 4D =/+ zoom should reduce orthographic size")
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Live 4D zoom keys should not mutate gameplay state")
		var zoomed_in_camera_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var zoom_status: String = app._camera_rig.view_status_text()
		if zoom_status.find("size") == -1 or zoom_status.find("zoom") == -1 or zoom_status.find("manual") == -1:
			failures.append("Live 4D camera diagnostics should expose size, zoom, and manual state after zoom")
		var zoom_out_event := InputEventKey.new()
		zoom_out_event.keycode = KEY_MINUS
		zoom_out_event.unicode = 45
		zoom_out_event.pressed = true
		app._input(zoom_out_event)
		if live_4d_camera != null and live_4d_camera.size <= zoomed_in_camera_size:
			failures.append("Live 4D - zoom should increase orthographic size")
		app._refresh_live_4d_snapshot()
		await tree.process_frame
		if live_4d_camera != null and app._camera_rig._current_fit_state != "manual":
			failures.append("Live 4D snapshot refresh should not continuously reapply Fit View after zoom")
		if live_4d_camera != null and live_4d_camera.size <= zoomed_in_camera_size:
			failures.append("Live 4D manual zoom should survive a live snapshot refresh")
		var focused_zoom_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var plus_event := InputEventKey.new()
		plus_event.keycode = KEY_PLUS
		plus_event.unicode = 43
		plus_event.pressed = true
		app._input(plus_event)
		if live_4d_camera != null and live_4d_camera.size >= focused_zoom_size:
			failures.append("Live 4D zoom should still work through pre-UI input capture")
		var yaw_before: float = app._camera_rig._current_yaw
		var camera_event := InputEventKey.new()
		camera_event.keycode = KEY_O
		camera_event.pressed = true
		app._unhandled_input(camera_event)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Live 4D camera keys should not mutate gameplay state")
		if app._camera_rig._current_yaw >= yaw_before:
			failures.append("Live 4D O camera key should adjust yaw left")
		if app._camera_rig._current_fit_state != "manual":
			failures.append("Live 4D camera adjustment should mark the view manual")
		var roll_before: float = app._camera_rig._current_roll
		var roll_event := InputEventKey.new()
		roll_event.keycode = KEY_PERIOD
		roll_event.pressed = true
		app._unhandled_input(roll_event)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Live 4D roll keys should not mutate gameplay state")
		if app._camera_rig._current_roll <= roll_before:
			failures.append("Live 4D period camera key should roll right")
		var roll_left_event := InputEventKey.new()
		roll_left_event.keycode = KEY_COMMA
		roll_left_event.pressed = true
		app._unhandled_input(roll_left_event)
		if app._camera_rig._current_fit_state != "manual":
			failures.append("Live 4D camera roll should mark the view manual")
		app._fit_view()
		if app._camera_rig._current_view_preset != "LIVE_4D_FITTED_W_SLICE_VIEW" or app._camera_rig._current_fit_state != "fit OK":
			failures.append("Fit View should restore the full Live 4D W-slice layout")
		if absf(app._camera_rig._current_roll) > 0.001:
			failures.append("Fit View should reset Live 4D camera roll")
		var wheel_fit_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var wheel_up_event := InputEventMouseButton.new()
		wheel_up_event.button_index = MOUSE_BUTTON_WHEEL_UP
		wheel_up_event.pressed = true
		app._handle_camera_input(wheel_up_event)
		if live_4d_camera != null and live_4d_camera.size >= wheel_fit_size:
			failures.append("Mouse wheel up should zoom in by reducing orthographic size")
		var wheel_zoomed_in_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var wheel_down_event := InputEventMouseButton.new()
		wheel_down_event.button_index = MOUSE_BUTTON_WHEEL_DOWN
		wheel_down_event.pressed = true
		app._handle_camera_input(wheel_down_event)
		if live_4d_camera != null and live_4d_camera.size <= wheel_zoomed_in_size:
			failures.append("Mouse wheel down should zoom out by increasing orthographic size")
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Mouse wheel zoom should not mutate Live 4D gameplay state")
		var scroll_focus_before: Vector3 = app._camera_rig._target_focus
		var scroll_size_before: float = live_4d_camera.size if live_4d_camera != null else 0.0
		var shift_wheel := InputEventMouseButton.new()
		shift_wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
		shift_wheel.pressed = true
		shift_wheel.shift_pressed = true
		app._handle_camera_input(shift_wheel)
		if app._camera_rig._target_focus == scroll_focus_before or app._camera_rig._current_fit_state != "matrix scroll":
			failures.append("Shift+wheel should scroll the Live 4D layer matrix")
		if live_4d_camera != null and absf(live_4d_camera.size - scroll_size_before) > 0.001:
			failures.append("Matrix scrolling should pan rather than zoom")
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Matrix scrolling should not dispatch a gameplay command")
		var drag_event := InputEventMouseButton.new()
		drag_event.button_index = MOUSE_BUTTON_LEFT
		drag_event.pressed = true
		app._handle_camera_input(drag_event)
		var yaw_before_drag: float = app._camera_rig._target_yaw
		var motion_event := InputEventMouseMotion.new()
		motion_event.relative = Vector2(12.0, 0.0)
		app._handle_camera_input(motion_event)
		if app._camera_rig._target_yaw >= yaw_before_drag:
			failures.append("Mouse drag should orbit camera view")
		drag_event.pressed = false
		app._handle_camera_input(drag_event)
		var shift_drag_event := InputEventMouseButton.new()
		shift_drag_event.button_index = MOUSE_BUTTON_LEFT
		shift_drag_event.pressed = true
		shift_drag_event.shift_pressed = true
		app._handle_camera_input(shift_drag_event)
		var roll_before_drag: float = app._camera_rig._target_roll
		var roll_motion_event := InputEventMouseMotion.new()
		roll_motion_event.relative = Vector2(12.0, 0.0)
		app._handle_camera_input(roll_motion_event)
		if app._camera_rig._target_roll <= roll_before_drag:
			failures.append("Shift-drag should roll camera view")
		shift_drag_event.pressed = false
		app._handle_camera_input(shift_drag_event)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Mouse camera controls should not mutate Live 4D gameplay state")
		app._fit_view()
		app._camera_rig.zoom(-1.0)
		var double_click_event := InputEventMouseButton.new()
		double_click_event.button_index = MOUSE_BUTTON_LEFT
		double_click_event.pressed = true
		double_click_event.double_click = true
		app._handle_camera_input(double_click_event)
		if app._camera_rig._current_fit_state != "fit OK":
			failures.append("Double-click should route to Fit View")
		if app._hud._reset_button != null and app._hud._reset_button.focus_mode != Control.FOCUS_NONE:
			failures.append("live viewer buttons should not keep keyboard focus while live gameplay captures Space")
		if app._hud._reset_button != null:
			app._hud._reset_button.focus_mode = Control.FOCUS_ALL
			app._hud._reset_button.grab_focus()
			app._input(zoom_in_event)
			if live_4d_camera != null and app._camera_rig._current_fit_state != "manual":
				failures.append("Live 4D zoom should still work after a visible button is clicked or focused")
			app._hud._reset_button.focus_mode = Control.FOCUS_NONE
			app._fit_view()
		var space_event := InputEventKey.new()
		space_event.keycode = KEY_SPACE
		space_event.pressed = true
		var hash_before_space := str(app._live_bridge.live_4d_state_hash())
		app._input(space_event)
		if str(app._live_bridge.live_4d_state_hash()) == hash_before_space:
			failures.append("Space should dispatch Live 4D hard_drop before UI accept handling")
		if str(app._current_snapshot.get("last_command", "")) != "hard_drop":
			failures.append("Space should map to Live 4D hard_drop")
		if str(app._current_snapshot.get("current_piece", "")) != "STAIR4":
			failures.append("Space hard drop should spawn the next Live 4D piece")
		app._current_snapshot["game_over"] = true
		app._current_snapshot["game_over_reason"] = "out_of_bounds"
		var endgame_hash := str(app._live_bridge.live_4d_state_hash())
		var viewport_rect: Rect2 = app._hud.game_viewport_global_rect()
		var viewport_center := viewport_rect.position + (viewport_rect.size * 0.5)
		var endgame_drag_start := InputEventMouseButton.new()
		endgame_drag_start.button_index = MOUSE_BUTTON_LEFT
		endgame_drag_start.pressed = true
		endgame_drag_start.position = viewport_center
		app._input(endgame_drag_start)
		var endgame_yaw_before: float = app._camera_rig._target_yaw
		var endgame_motion := InputEventMouseMotion.new()
		endgame_motion.position = viewport_center + Vector2(10.0, 0.0)
		endgame_motion.relative = Vector2(10.0, 0.0)
		app._input(endgame_motion)
		if app._camera_rig._target_yaw >= endgame_yaw_before:
			failures.append("Mouse drag over the live viewport should orbit camera after game over")
		var endgame_drag_end := InputEventMouseButton.new()
		endgame_drag_end.button_index = MOUSE_BUTTON_LEFT
		endgame_drag_end.pressed = false
		endgame_drag_end.position = viewport_center + Vector2(10.0, 0.0)
		app._input(endgame_drag_end)
		var endgame_wheel_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var endgame_wheel := InputEventMouseButton.new()
		endgame_wheel.button_index = MOUSE_BUTTON_WHEEL_UP
		endgame_wheel.pressed = true
		endgame_wheel.position = viewport_center
		app._input(endgame_wheel)
		if live_4d_camera != null and live_4d_camera.size >= endgame_wheel_size:
			failures.append("Mouse wheel over the live viewport should zoom camera after game over")
		if str(app._live_bridge.live_4d_state_hash()) != endgame_hash:
			failures.append("Endgame mouse camera controls should not mutate Live 4D gameplay state")
		app._reset_live_4d()
		var live_4d_initial_hash := str(app._live_bridge.live_4d_state_hash())
		app._dispatch_live_4d_gameplay_command("move_w_pos")
		if str(app._live_bridge.live_4d_state_hash()) == live_4d_initial_hash:
			failures.append("live 4D W movement should route to C++")
		if int(app._current_snapshot.get("active_w", -1)) != 2:
			failures.append("live 4D W movement should update active W context")
		app._dispatch_live_4d_gameplay_command("rotate_xw_pos")
		if str(app._current_snapshot.get("last_rotation_plane", "")) != "XW":
			failures.append("live 4D XW rotation should route through C++")
		if str(app._current_snapshot.get("last_rotation_label", "")) != "XW+":
			failures.append("live 4D XW rotation should expose a signed HUD rotation label")
		app._dispatch_live_4d_gameplay_command("rotate_yw_neg")
		if str(app._current_snapshot.get("last_rotation_label", "")) != "YW-":
			failures.append("live 4D YW rotation should expose a signed HUD rotation label")
		app._dispatch_live_4d_gameplay_command("rotate_zw_pos")
		if str(app._current_snapshot.get("last_rotation_label", "")) != "ZW+":
			failures.append("live 4D ZW rotation should expose a signed HUD rotation label")
		app._dispatch_live_4d_gameplay_command("hard_drop")
		if str(app._current_snapshot.get("current_piece", "")) != "STAIR4":
			failures.append("live 4D hard drop should route to C++ and spawn STAIR4")
		if str(app._hud._summary_label.text).find("SCORE 5") == -1 or str(app._hud._summary_label.text).find("LOCKED") == -1:
			failures.append("Live 4D HUD should expose score and lock feedback after hard drop")
		var q_event := InputEventKey.new()
		q_event.keycode = KEY_Q
		q_event.pressed = true
		var hash_before_q := str(app._live_bridge.live_4d_state_hash())
		app._unhandled_input(q_event)
		if app._mode != TraceReplayAppScript.MODE_LIVE_4D:
			failures.append("Q should not leave Live 4D because Q maps to W-")
		if str(app._live_bridge.live_4d_state_hash()) == hash_before_q:
			failures.append("Q should dispatch Live 4D W- movement")
		var h_event := InputEventKey.new()
		h_event.keycode = KEY_H
		h_event.pressed = true
		app._unhandled_input(h_event)
		if str(app._current_snapshot.get("last_rotation_label", "")) != "YW-":
			failures.append("H should dispatch Live 4D YW- rotation instead of Help")
		app._enter_replay_mode()
		await tree.process_frame
		app._enter_live_4d_mode()
		await tree.process_frame
		if app._live_4d_paused:
			failures.append("switching back to Live 4D should resume the selected live mode")
		var switched_fit_size := live_4d_camera.size if live_4d_camera != null else 0.0
		app._input(zoom_out_event)
		if live_4d_camera != null and live_4d_camera.size <= switched_fit_size:
			failures.append("Live 4D zoom should work after switching away and back")
	for action_name in [
		"live_move_left",
		"live_move_right",
		"live_rotate_cw",
		"live_rotate_ccw",
		"live_soft_drop",
		"live_hard_drop",
		"live_pause",
		"live_reset",
		"live_3d_move_x_neg",
		"live_3d_move_x_pos",
		"live_3d_move_z_neg",
		"live_3d_move_z_pos",
		"live_3d_soft_drop",
		"live_3d_hard_drop",
		"live_3d_rotate_xy_neg",
		"live_3d_rotate_xy_pos",
		"live_3d_rotate_xz_neg",
		"live_3d_rotate_xz_pos",
		"live_3d_rotate_yz_neg",
		"live_3d_rotate_yz_pos",
		"live_3d_pause",
		"live_3d_reset",
		"live_4d_move_x_neg",
		"live_4d_move_x_pos",
		"live_4d_move_z_neg",
		"live_4d_move_z_pos",
		"live_4d_move_w_neg",
		"live_4d_move_w_pos",
		"live_4d_soft_drop",
		"live_4d_hard_drop",
		"live_4d_rotate_xy_neg",
		"live_4d_rotate_xy_pos",
		"live_4d_rotate_xz_neg",
		"live_4d_rotate_xz_pos",
		"live_4d_rotate_yz_neg",
		"live_4d_rotate_yz_pos",
		"live_4d_rotate_xw_neg",
		"live_4d_rotate_xw_pos",
		"live_4d_rotate_yw_neg",
		"live_4d_rotate_yw_pos",
		"live_4d_rotate_zw_neg",
		"live_4d_rotate_zw_pos",
		"live_4d_pause",
		"live_4d_reset",
		"live_4d_camera_pitch_up",
		"live_4d_camera_pitch_down",
		"live_4d_camera_yaw_left",
		"live_4d_camera_yaw_right",
		"live_4d_camera_roll_left",
		"live_4d_camera_roll_right",
		"live_4d_camera_zoom_in",
		"live_4d_camera_zoom_out",
		"mode_toggle_replay_live",
		"quit",
	]:
		if not InputMap.has_action(action_name):
			failures.append("InputMap missing %s" % action_name)
	root.queue_free()
	await tree.process_frame
	return failures


func _assert_live_gameplay_hud_copy(failures: Array) -> void:
	var live_snapshot := {
		"current_piece": "O3",
		"next_piece": "L3",
		"score": 45,
		"lines": 1,
		"last_command": "hard_drop",
		"last_command_status": "accepted",
		"paused": false,
		"game_over": false,
		"dimension": 3,
		"board_shape": [6, 10, 6],
		"piece_set_id": "native_3d",
		"effective_seed": 1337,
		"initial_speed_level": 1,
	}
	var summary := ReplayHudScript.live_gameplay_summary_text(live_snapshot, "Live Plain 3D")
	if summary != "Live Plain 3D | Board 6 × 10 × 6 | True 3D | Speed 1 | Seed 1337 | SCORE 45 | CLEARS 1 | O3 > L3 | LOCKED":
		failures.append("live gameplay summary should prioritize score, clears, and piece queue, got %s" % summary)
	var feedback := ReplayHudScript.live_command_feedback_text(live_snapshot)
	if feedback != "Piece locked":
		failures.append("accepted hard drop should produce decisive lock feedback, got %s" % feedback)
	live_snapshot["last_command"] = "move_w_pos"
	live_snapshot["last_command_status"] = "rejected"
	feedback = ReplayHudScript.live_command_feedback_text(live_snapshot)
	if feedback != "Cannot move there":
		failures.append("rejected live command should remain visible, got %s" % feedback)
	live_snapshot["paused"] = true
	if ReplayHudScript.live_command_feedback_text(live_snapshot) != "Paused · P — Resume · Esc — Main Menu":
		failures.append("paused live HUD should explain that gameplay input is held")
	live_snapshot["paused"] = false
	live_snapshot["game_over"] = true
	live_snapshot["game_over_reason"] = "spawn_blocked"
	if ReplayHudScript.live_command_feedback_text(live_snapshot) != "Game over · Spawn blocked · Restart Game or Main Menu":
		failures.append("game-over HUD should expose the native reason and restart action")
