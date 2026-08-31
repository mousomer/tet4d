extends RefCounted

const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")
const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const SCREEN_RIGHT_TOLERANCE_PX := 0.5
const AWAY_DEPTH_TOLERANCE := 0.0001


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
	if not live_4d_hint.contains("Q / E Slice W - / +") or not live_4d_hint.contains("Y / U XW") or not live_4d_hint.contains("H / J YW") or not live_4d_hint.contains("N / M ZW") or not live_4d_hint.contains("1 / 2 XW - / + (re-slice)") or not live_4d_hint.contains("; / ' ZW - / + (re-slice)") or not live_4d_hint.contains("[ / ] ZX - / +") or not live_4d_hint.contains("I / K") or live_4d_hint.contains("Roll left / right") or not live_4d_hint.contains("Left Drag Orient slices") or not live_4d_hint.contains("Right Drag Translate framing") or live_4d_hint.contains("Shift + Left Drag") or not live_4d_hint.contains("Tab Replay Demos") or live_4d_hint.contains("Q/Esc Quit"):
		failures.append("live 4D hint text should expose separated slice orientation, framing, exact basis, piece rotation, and Esc-only quit")
	_assert_camera_command_help_is_executable_truth(live_hint, live_3d_hint, live_4d_hint, failures)
	for roll_action in ["live_4d_camera_roll_left", "live_4d_camera_roll_right"]:
		if LiveInputContractScript.ACTION_SPECS.has(roll_action):
			failures.append("normal Live 4D action contract must omit %s" % roll_action)
	for action_name in LiveInputContractScript.ACTION_SPECS:
		var spec: Dictionary = LiveInputContractScript.ACTION_SPECS.get(action_name, {})
		if not spec.get("keys", []).has(spec.get("display_key")):
			failures.append("%s helper display key must come from its registered binding list" % action_name)
		for forbidden_key in spec.get("forbidden_keys", []):
			if spec.get("keys", []).has(forbidden_key):
				failures.append("%s must not register a forbidden helper/input key" % action_name)
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
	for action_name in [
		"mode_toggle_replay_live",
		"replay_prev_frame",
		"replay_next_frame",
		"replay_play_pause",
		"replay_reset",
		"replay_prev_case",
		"replay_next_case",
		"replay_topology_family",
		"replay_gameplay_family",
		"replay_endgame_family",
		"replay_fit_view",
		"replay_toggle_help",
		"replay_quit",
		"quit",
	]:
		if not InputMap.has_action(action_name):
			failures.append("InputMap action %s must exist before deferred startup" % action_name)
	await tree.process_frame
	await tree.process_frame
	var app := root.get_node_or_null("App")
	if app == null:
		failures.append("trace replay scene should include App for live shell checks")
	else:
		app._enter_live_2d_mode()
		await tree.process_frame
		var live_camera := app._camera_rig.get_node_or_null("Camera3D") as Camera3D
		if not is_equal_approx(app._camera_rig._current_yaw, 0.0) or not is_equal_approx(app._camera_rig._current_pitch, 0.0) or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("Live 2D must open with exact flat front-on outer orientation")
		if live_camera == null or live_camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
			failures.append("Live 2D must open with orthographic projection")
		if app._hud._camera_view_action_menu == null or app._hud._camera_view_action_menu.visible:
			failures.append("ordinary Live 2D must not expose named view actions")
		app._camera_rig._current_yaw = PI
		app._camera_rig._target_yaw = PI
		app._camera_rig._update_camera()
		app._refresh_hud()
		app._dispatch_live_2d_control_intent("move_right")
		if str(app._current_snapshot.get("last_command", "")) != "move_left":
			failures.append("Live 2D Relative Right must dispatch canonical Left from the rear view")
		if not str(LiveInputContractScript.control_hint_groups("live_2d", {}, app._hud._control_frame_snapshot)).contains("Left / Right [-X]"):
			failures.append("Live 2D helper must share the rear-view Relative Right mapping")
		app._reset_live_2d()
		app._process_live_repeat_action("move_right", true, "move_right", 0.0, 0.0, 0.0)
		app._process_live_repeat_action("move_right", true, "move_right", 0.0, 0.0, 0.01)
		if str(app._current_snapshot.get("last_command", "")) != "move_left":
			failures.append("held Live 2D Relative Right must use the same rear-view mapping")
		app._reset_live_repeat_state()
		app._reset_live_2d()
		app._camera_rig.nudge_yaw(0.25)
		app._camera_rig.zoom(-1.0)
		app._hud._settings_store.set_value("display.ui_scale", "large")
		var live_2d_view_before_restart: Dictionary = app._camera_rig.presentation_snapshot()
		app._reset_live_2d()
		if app._camera_rig.presentation_snapshot() != live_2d_view_before_restart:
			failures.append("Live 2D Restart Game must preserve the current view")
		if app._hud._settings_store.value("display.ui_scale") != "large":
			failures.append("Restart Game must preserve UI scale")
		var live_2d_hash_before_reset_view := str(app._live_bridge.live_2d_state_hash())
		app._reset_view()
		if not is_equal_approx(app._camera_rig._current_yaw, 0.0) or not is_equal_approx(app._camera_rig._current_pitch, 0.0) or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("Live 2D Reset View must restore exact flat orientation")
		if str(app._live_bridge.live_2d_state_hash()) != live_2d_hash_before_reset_view:
			failures.append("Live 2D Reset View must preserve deterministic gameplay")
		if app._hud._settings_store.value("display.ui_scale") != "large":
			failures.append("Reset View must preserve UI scale")
		var live_snapshot: Dictionary = app._current_snapshot
		if str(live_snapshot.get("trace_type", "")) != "live_2d":
			failures.append("live mode should create a live snapshot")
		var initial_piece := str(live_snapshot.get("current_piece", ""))
		if initial_piece != "I":
			failures.append("live mode should start with native I piece, got %s" % initial_piece)
		var hold_panel_snapshot: Dictionary = app._hud._hold_piece_panel.deterministic_snapshot()
		if hold_panel_snapshot.get("piece_name_text") != "EMPTY" or hold_panel_snapshot.get("status_text") != "Available · C":
			failures.append("Live 2D cockpit must begin with an intentional available HOLD state")
		var hold_event := InputEventKey.new()
		hold_event.keycode = KEY_C
		hold_event.pressed = true
		app._unhandled_input(hold_event)
		if str(app._current_snapshot.get("current_piece", "")) != "O" or str(app._current_snapshot.get("held_piece", {}).get("shape", "")) != "I":
			failures.append("one physical C press must dispatch the native first-Hold transition")
		hold_panel_snapshot = app._hud._hold_piece_panel.deterministic_snapshot()
		if hold_panel_snapshot.get("piece_name_text") != "I" or hold_panel_snapshot.get("status_text") != "Used until lock":
			failures.append("Live cockpit HOLD preview must follow authoritative populated/unavailable state")
		var hash_after_hold := str(app._live_bridge.live_2d_state_hash())
		var repeated_hold_event := InputEventKey.new()
		repeated_hold_event.keycode = KEY_C
		repeated_hold_event.pressed = true
		repeated_hold_event.echo = true
		app._unhandled_input(repeated_hold_event)
		if str(app._live_bridge.live_2d_state_hash()) != hash_after_hold:
			failures.append("held C key repeat must not dispatch another Hold attempt")
		app._toggle_live_2d_pause()
		var paused_hold_hash := str(app._live_bridge.live_2d_state_hash())
		app._unhandled_input(hold_event)
		if str(app._live_bridge.live_2d_state_hash()) != paused_hold_hash:
			failures.append("paused gameplay ownership must suppress Hold")
		app._toggle_live_2d_pause()
		app._reset_live_2d()
		app._dispatch_live_gameplay_command("hard_drop")
		live_snapshot = app._current_snapshot
		if str(live_snapshot.get("current_piece", "")) != "O":
			failures.append("live hard drop should route to C++ and spawn O")
		if str(app._hud._summary_label.text).find("SCORE 5") == -1 or str(app._hud._summary_label.text).find("LOCKED") == -1:
			failures.append("Live 2D HUD should expose score and lock feedback after hard drop")
		app._enter_replay_mode()
		await tree.process_frame
		app._camera_rig.nudge_yaw(0.2)
		app._camera_rig.nudge_roll(0.1)
		var replay_orientation_before_fit: Dictionary = app._camera_rig.presentation_snapshot()
		app._fit_view()
		for key in ["current_yaw", "current_pitch", "current_roll", "projection", "horizontal_reflection_active"]:
			if app._camera_rig.presentation_snapshot().get(key) != replay_orientation_before_fit.get(key):
				failures.append("Replay Fit View must preserve %s" % key)
		var replay_content_before_reset := str(app._current_snapshot.get("state_hash", ""))
		app._reset_view()
		if not is_equal_approx(app._camera_rig._current_yaw, CameraRigScript.PYTHON_DISPLAY_YAW_RAD) or not is_equal_approx(app._camera_rig._current_pitch, CameraRigScript.PYTHON_DISPLAY_PITCH_RAD) or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("Replay Reset View must restore canonical replay orientation")
		if str(app._current_snapshot.get("state_hash", "")) != replay_content_before_reset:
			failures.append("Replay Reset View must preserve replay content")
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
		if bool(app._camera_rig.presentation_snapshot().get("horizontal_reflection_active", false)) or app._live_4d_presentation_root.transform != Transform3D.IDENTITY:
			failures.append("Live 3D must not inherit the fitted Live-4D presentation reflection")
		if not is_equal_approx(app._camera_rig._current_yaw, CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD) or not is_equal_approx(app._camera_rig._current_pitch, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD) or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("Live 3D must open with its canonical outer orientation")
		if app._hud._camera_view_action_menu == null or not app._hud._camera_view_action_menu.visible:
			failures.append("Live 3D must expose named view actions as stateless actions")
		app._camera_rig.nudge_yaw(0.3)
		var live_3d_hash_before_reset_view := str(app._live_bridge.live_3d_state_hash())
		app._reset_view()
		if not is_equal_approx(app._camera_rig._current_yaw, CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD) or not is_equal_approx(app._camera_rig._current_pitch, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD) or not is_equal_approx(app._camera_rig._current_roll, 0.0):
			failures.append("Live 3D Reset View must restore canonical outer orientation")
		if str(app._live_bridge.live_3d_state_hash()) != live_3d_hash_before_reset_view:
			failures.append("Live 3D Reset View must preserve deterministic gameplay")
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
		app._camera_rig._current_yaw = PI * 0.5
		app._camera_rig._target_yaw = PI * 0.5
		app._camera_rig._update_camera()
		app._refresh_hud()
		app._dispatch_live_3d_control_intent("move_x_pos")
		if str(app._current_snapshot.get("last_command", "")) != "move_z_neg":
			failures.append("Live 3D Relative Right must dispatch canonical -Z at +90 yaw")
		var live_3d_control_help := str(LiveInputContractScript.control_hint_groups("live_3d", {}, app._hud._control_frame_snapshot))
		if not live_3d_control_help.contains("Left / Right [-Z]") or not live_3d_control_help.contains("Forward / Back [-X]"):
			failures.append("Live 3D helper must share the +90 yaw Right/Forward mapping")
		app._reset_live_3d()
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
		if str(app._hud._summary_label.text).find("Active O3") == -1 or str(app._hud._summary_label.text).find("LOCKED") == -1:
			failures.append("Live 3D HUD should expose the active piece and lock feedback while NEXT owns queue presentation")
		var popup_owned_hash := str(app._live_bridge.live_3d_state_hash())
		app._hud._live_interaction_owns_input = true
		var popup_move_event := InputEventAction.new()
		popup_move_event.action = "live_3d_move_x_pos"
		popup_move_event.pressed = true
		app._unhandled_input(popup_move_event)
		var popup_space_event := InputEventKey.new()
		popup_space_event.keycode = KEY_SPACE
		popup_space_event.pressed = true
		app._input(popup_space_event)
		var popup_hold_event := InputEventKey.new()
		popup_hold_event.keycode = KEY_C
		popup_hold_event.pressed = true
		app._input(popup_hold_event)
		if str(app._live_bridge.live_3d_state_hash()) != popup_owned_hash:
			failures.append("cockpit popup ownership must suppress movement, Space hard drop, and Hold")
		app._hud._live_interaction_owns_input = false
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
		if app._current_document != null:
			failures.append("live 4D entry must discard the retained replay document before rendering")
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
		if not is_equal_approx(app._camera_rig._current_yaw, CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD) or not is_equal_approx(app._camera_rig._current_pitch, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD):
			failures.append("live 4D should open in the canonical W-slice outer mount")
		if app._camera_rig._framing_status != "fit OK":
			failures.append("live 4D should open already fitted")
		if not bool(app._camera_rig.presentation_snapshot().get("horizontal_reflection_active", false)):
			failures.append("live 4D fitted view should use the accepted board-depth mount")
		if app._live_4d_presentation_root == null or app._renderer.get_parent() != app._live_4d_presentation_root:
			failures.append("Live 4D renderer should be isolated under one fixed presentation root")
		elif app._live_4d_presentation_root.transform.basis.determinant() >= 0.0:
			failures.append("Live 4D presentation root should carry the render-effective horizontal reflection")
		if app._live_4d_presentation_root != null and app._live_4d_presentation_root.is_ancestor_of(app._camera_rig):
			failures.append("Live 4D presentation reflection must not contain CameraRig")
		if app._live_4d_presentation_root != null and app._live_4d_presentation_root.is_ancestor_of(app._hud):
			failures.append("Live 4D presentation reflection must not inherit from HUD")
		var orientation_gizmo := app._camera_rig.get_node_or_null("OrientationGizmo") as Node3D
		if orientation_gizmo == null or not orientation_gizmo.visible or orientation_gizmo.get_child_count() < 10:
			failures.append("Live 4D should show a compact basis-driven ball-and-arrow orientation marker")
		elif orientation_gizmo.get_node_or_null("HorizontalArrow") == null or orientation_gizmo.get_node_or_null("GravityArrow") == null or orientation_gizmo.get_node_or_null("DepthArrow") == null:
			failures.append("orientation marker should expose horizontal, gravity, and depth arrowheads")
		else:
			var gizmo_origin := orientation_gizmo.get_node_or_null("AxisOrigin") as MeshInstance3D
			var gizmo_horizontal := orientation_gizmo.get_node_or_null("HorizontalArrow") as MeshInstance3D
			if gizmo_origin != null and gizmo_horizontal != null:
				var gizmo_origin_screen: Vector2 = app._camera_rig.project_world_point(gizmo_origin.global_position)
				var gizmo_horizontal_screen: Vector2 = app._camera_rig.project_world_point(gizmo_horizontal.global_position)
				if gizmo_horizontal_screen.x - gizmo_origin_screen.x <= SCREEN_RIGHT_TOLERANCE_PX:
					failures.append("orientation gizmo horizontal arrow should agree with reflected board screen-right")
			var gizmo_position_before: Vector3 = orientation_gizmo.global_position
			app._camera_rig.orbit(Vector2(8.0, -4.0))
			app._camera_rig._process(1.0)
			if orientation_gizmo.global_position == gizmo_position_before:
				failures.append("orientation marker should update with camera movement in real time")
			app._fit_view()
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
		if live_4d_camera != null and app._camera_rig._framing_status != "manual":
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
		var outer_yaw_before: float = app._camera_rig._current_yaw
		var local_yaw_before: float = app._live_4d_local_orientation.local_yaw
		var camera_event := InputEventKey.new()
		camera_event.keycode = KEY_O
		camera_event.pressed = true
		app._unhandled_input(camera_event)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Live 4D orientation keys should not mutate gameplay state")
		if app._live_4d_local_orientation.local_yaw >= local_yaw_before:
			failures.append("Live 4D O key should adjust shared L yaw left")
		if not is_equal_approx(app._camera_rig._current_yaw, outer_yaw_before):
			failures.append("Live 4D keyboard yaw must not rotate the outer rig")
		if app._renderer.live_4d_local_orientation_snapshot() != app._live_4d_local_orientation.snapshot():
			failures.append("Live 4D renderer and resolver must observe the same shared L")
		if app._renderer._live_4d_fit_reference != app._renderer.current_bounds():
			failures.append("Live 4D L mutation must refresh oriented bounds and fit reference")
		var outer_pitch_before: float = app._camera_rig._current_pitch
		var local_pitch_before: float = app._live_4d_local_orientation.local_pitch
		var pitch_event := InputEventKey.new()
		pitch_event.keycode = KEY_I
		pitch_event.pressed = true
		app._unhandled_input(pitch_event)
		if is_equal_approx(app._live_4d_local_orientation.local_pitch, local_pitch_before):
			failures.append("Live 4D I key should adjust shared L pitch using the active invert-Y preference")
		if not is_equal_approx(app._camera_rig._current_pitch, outer_pitch_before):
			failures.append("Live 4D keyboard pitch must not rotate the outer rig")
		var roll_before: float = app._camera_rig._current_roll
		var local_before_roll: Dictionary = app._live_4d_local_orientation.snapshot()
		var roll_event := InputEventKey.new()
		roll_event.keycode = KEY_PERIOD
		roll_event.pressed = true
		app._unhandled_input(roll_event)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Live 4D roll keys should not mutate gameplay state")
		if not is_equal_approx(app._camera_rig._current_roll, roll_before) or app._live_4d_local_orientation.snapshot() != local_before_roll:
			failures.append("normal Live 4D roll input must not rotate outer framing or shared L")
		var roll_left_event := InputEventKey.new()
		roll_left_event.keycode = KEY_COMMA
		roll_left_event.pressed = true
		app._unhandled_input(roll_left_event)
		if not is_equal_approx(app._camera_rig._current_roll, roll_before):
			failures.append("normal Live 4D roll-left input must remain detached")
		app._fit_view()
		if app._camera_rig._framing_status != "fit OK":
			failures.append("Fit View should restore fitted Live 4D framing")
		var wheel_fit_size := live_4d_camera.size if live_4d_camera != null else 0.0
		var wheel_orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var wheel_basis_before: Array = app._live_4d_basis.slots()
		var wheel_right_before: String = app._control_frame_mapping(4).translation_command("move_x_pos", "relative")
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
		var shifted_wheel_focus_before: Vector3 = app._camera_rig._target_focus
		var shifted_wheel_size_before: float = live_4d_camera.size if live_4d_camera != null else 0.0
		var shift_wheel := InputEventMouseButton.new()
		shift_wheel.button_index = MOUSE_BUTTON_WHEEL_DOWN
		shift_wheel.pressed = true
		shift_wheel.shift_pressed = true
		app._handle_camera_input(shift_wheel)
		if app._camera_rig._target_focus != shifted_wheel_focus_before:
			failures.append("Shift+wheel should not translate the view; pointer drag owns pan")
		if live_4d_camera != null and live_4d_camera.size <= shifted_wheel_size_before:
			failures.append("Wheel should remain zoom even when Shift is held")
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Shift+wheel zoom should not dispatch a gameplay command")
		if app._live_4d_local_orientation.snapshot() != wheel_orientation_before or app._live_4d_basis.slots() != wheel_basis_before or app._control_frame_mapping(4).translation_command("move_x_pos", "relative") != wheel_right_before:
			failures.append("wheel zoom must not change B, L, or relative command mapping")
		var drag_event := InputEventMouseButton.new()
		drag_event.button_index = MOUSE_BUTTON_LEFT
		drag_event.pressed = true
		app._handle_camera_input(drag_event)
		var outer_yaw_before_drag: float = app._camera_rig._target_yaw
		var orientation_before_drag: Dictionary = app._live_4d_local_orientation.snapshot()
		var anchor_before_drag: Vector3 = app._renderer._presentation.projection.slice_anchor(0)
		var bounds_before_drag: Dictionary = app._renderer.current_bounds().duplicate(true)
		var motion_event := InputEventMouseMotion.new()
		motion_event.relative = Vector2(12.0, -6.0)
		app._handle_camera_input(motion_event)
		if app._live_4d_local_orientation.snapshot() == orientation_before_drag:
			failures.append("Live 4D left drag should mutate shared L yaw/pitch")
		if not is_equal_approx(app._camera_rig._target_yaw, outer_yaw_before_drag):
			failures.append("Live 4D left drag must not rotate the outer rig")
		if app._renderer._presentation.projection.slice_anchor(0) != anchor_before_drag:
			failures.append("Live 4D left drag must not move slice anchors")
		if app._renderer.current_bounds() == bounds_before_drag or app._renderer._live_4d_fit_reference != app._renderer.current_bounds():
			failures.append("Live 4D left drag must refresh oriented bounds and fit reference")
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
		if app._camera_rig._target_roll != roll_before_drag:
			failures.append("Shift-drag must not introduce an undocumented camera action")
		shift_drag_event.pressed = false
		app._handle_camera_input(shift_drag_event)
		var pan_button := InputEventMouseButton.new()
		pan_button.button_index = MOUSE_BUTTON_RIGHT
		pan_button.pressed = true
		app._handle_camera_input(pan_button)
		var focus_before_pan: Vector3 = app._camera_rig._target_focus
		var orientation_before_pan: Dictionary = app._live_4d_local_orientation.snapshot()
		var basis_before_pan: Array = app._live_4d_basis.slots()
		var command_before_pan: String = app._control_frame_mapping(4).translation_command("move_z_neg", "relative")
		var anchor_before_pan: Vector3 = app._renderer._presentation.projection.slice_anchor(0)
		var pan_motion := InputEventMouseMotion.new()
		pan_motion.relative = Vector2(18.0, -9.0)
		app._handle_camera_input(pan_motion)
		if app._camera_rig._target_focus == focus_before_pan or app._camera_rig._framing_status != "manual pan":
			failures.append("Right-drag should pan the gameboard view")
		if app._live_4d_local_orientation.snapshot() != orientation_before_pan or app._live_4d_basis.slots() != basis_before_pan or app._control_frame_mapping(4).translation_command("move_z_neg", "relative") != command_before_pan or app._renderer._presentation.projection.slice_anchor(0) != anchor_before_pan:
			failures.append("Right-drag pan must not change B, L, resolver mapping, or anchors")
		pan_button.pressed = false
		app._handle_camera_input(pan_button)
		if str(app._live_bridge.live_4d_state_hash()) != camera_hash_before:
			failures.append("Mouse camera controls should not mutate Live 4D gameplay state")
		app._set_live_4d_local_orientation(deg_to_rad(44.0), 0.0)
		if app._control_frame_mapping(4).yaw_quarter_turn != 0:
			failures.append("Live 4D resolver should remain at q=0 below the 45-degree boundary")
		var rendered_yaw_44: float = float(app._renderer.live_4d_local_orientation_snapshot().get("local_yaw", 0.0))
		app._set_live_4d_local_orientation(deg_to_rad(46.0), 0.0)
		if app._control_frame_mapping(4).yaw_quarter_turn != 1:
			failures.append("Live 4D resolver should switch to q=1 above the 45-degree boundary")
		if is_equal_approx(float(app._renderer.live_4d_local_orientation_snapshot().get("local_yaw", 0.0)), rendered_yaw_44):
			failures.append("Live 4D renderer yaw should remain continuous across resolver thresholds")
		var lower_clamp_native_snapshot: String = app._live_bridge.live_4d_snapshot_json()
		var lower_clamp_hash: String = str(app._live_bridge.live_4d_state_hash())
		var lower_clamp_mapping: Dictionary = app._control_frame_mapping(4).snapshot()
		for _request_index in range(3):
			app._set_live_4d_local_orientation(
				deg_to_rad(46.0),
				SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD - PI
			)
		if not is_equal_approx(app._live_4d_local_orientation.local_pitch, SliceLocalOrientationScript.NORMAL_GAMEPLAY_MIN_PITCH_RAD):
			failures.append("repeated unsafe negative pitch requests must clamp at the corrected product minimum")
		if app._renderer.live_4d_local_orientation_snapshot() != app._live_4d_local_orientation.snapshot():
			failures.append("lower pitch clamp must propagate through actual renderer-owned L")
		if app._control_frame_mapping(4).snapshot() != lower_clamp_mapping:
			failures.append("lower pitch clamp must leave the app-owned resolver mapping unchanged")
		if app._live_bridge.live_4d_snapshot_json() != lower_clamp_native_snapshot or str(app._live_bridge.live_4d_state_hash()) != lower_clamp_hash:
			failures.append("lower pitch clamp must not change native snapshot or state hash")
		_assert_app_live_4d_semantic_directions(failures, app, "yaw 46 corrected minimum clamp")
		var mapping_before_outer_yaw: Dictionary = app._control_frame_mapping(4).snapshot()
		app._camera_rig.nudge_yaw(PI * 0.5)
		if app._control_frame_mapping(4).snapshot() != mapping_before_outer_yaw:
			failures.append("outer camera yaw must not influence Live 4D relative controls")
		var mapping_before_pitch: Dictionary = app._control_frame_mapping(4).snapshot()
		app._set_live_4d_local_orientation(
			app._live_4d_local_orientation.local_yaw,
			SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD + PI
		)
		if not is_equal_approx(app._live_4d_local_orientation.local_pitch, SliceLocalOrientationScript.NORMAL_GAMEPLAY_MAX_PITCH_RAD):
			failures.append("Live 4D orientation seam must clamp pitch to the declared gameplay maximum")
		if app._control_frame_mapping(4).snapshot() != mapping_before_pitch:
			failures.append("Live 4D pitch must not affect discrete relative controls")
		app._fit_view()
		var preset_outer_yaw: float = app._camera_rig._current_yaw
		var preset_outer_pitch: float = app._camera_rig._current_pitch
		var preset_native_snapshot: String = app._live_bridge.live_4d_snapshot_json()
		var preset_hash: String = str(app._live_bridge.live_4d_state_hash())
		if not app._apply_live_4d_view_action(CameraPresetScript.SIDE):
			failures.append("Live 4D Side preset should apply through the compatibility adapter")
		elif not is_equal_approx(app._live_4d_local_orientation.local_yaw, PI * 0.5) or app._control_frame_mapping(4).yaw_quarter_turn != 1:
			failures.append("Live 4D Side preset yaw should reach shared L and its quantized resolver")
		if not is_equal_approx(app._camera_rig._current_yaw, preset_outer_yaw) or not is_equal_approx(app._camera_rig._current_pitch, preset_outer_pitch):
			failures.append("Live 4D presets must not rotate the outer rig")
		if app._renderer._live_4d_fit_reference != app._renderer.current_bounds():
			failures.append("Live 4D preset orientation must leave bounds and fit reference coherent")
		if app._live_bridge.live_4d_snapshot_json() != preset_native_snapshot or str(app._live_bridge.live_4d_state_hash()) != preset_hash:
			failures.append("Live 4D presentation presets must not mutate canonical gameplay state")
		if not app._apply_live_4d_view_action(CameraPresetScript.TOP) or not is_equal_approx(app._live_4d_local_orientation.local_pitch, float(CameraPresetScript.definition(CameraPresetScript.TOP).get("pitch", 0.0))):
			failures.append("Live 4D Top preset should retain its established +60-degree shared-L action inside the expanded range")
		if not is_equal_approx(float(app._camera_rig.presentation_snapshot().get("zoom_multiplier", 0.0)), 1.0):
			failures.append("Live 4D view action should restore fitted framing without action-owned zoom")
		app._set_live_4d_local_orientation(0.0, 0.0)
		var fit_orientation_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var fit_basis_before: Array = app._live_4d_basis.slots()
		var fit_mapping_before: Dictionary = app._control_frame_mapping(4).snapshot()
		var fit_outer_before: Dictionary = app._camera_rig.presentation_snapshot()
		app._fit_view()
		if app._live_4d_local_orientation.snapshot() != fit_orientation_before or app._live_4d_basis.slots() != fit_basis_before or app._control_frame_mapping(4).snapshot() != fit_mapping_before:
			failures.append("Fit must not change B, L, or relative command mapping")
		for key in ["current_yaw", "current_pitch", "current_roll", "projection", "horizontal_reflection_active"]:
			if app._camera_rig.presentation_snapshot().get(key) != fit_outer_before.get(key):
				failures.append("Fit must preserve Live-4D outer %s" % key)
		app._camera_rig.zoom(-1.0)
		var double_click_event := InputEventMouseButton.new()
		double_click_event.button_index = MOUSE_BUTTON_LEFT
		double_click_event.pressed = true
		double_click_event.double_click = true
		app._handle_camera_input(double_click_event)
		if app._camera_rig._framing_status != "fit OK":
			failures.append("Double-click should route to Fit View")
		if app._hud._reset_button != null and app._hud._reset_button.focus_mode != Control.FOCUS_NONE:
			failures.append("live viewer buttons should not keep keyboard focus while live gameplay captures Space")
		if app._hud._reset_button != null:
			app._hud._reset_button.focus_mode = Control.FOCUS_ALL
			app._hud._reset_button.grab_focus()
			app._input(zoom_in_event)
			if live_4d_camera != null and app._camera_rig._framing_status != "manual":
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
		var endgame_outer_yaw_before: float = app._camera_rig._target_yaw
		var endgame_local_yaw_before: float = app._live_4d_local_orientation.local_yaw
		var endgame_motion := InputEventMouseMotion.new()
		endgame_motion.position = viewport_center + Vector2(10.0, 0.0)
		endgame_motion.relative = Vector2(10.0, 0.0)
		app._input(endgame_motion)
		if app._live_4d_local_orientation.local_yaw <= endgame_local_yaw_before:
			failures.append("Live 4D left drag should continue to orient shared L after game over")
		if not is_equal_approx(app._camera_rig._target_yaw, endgame_outer_yaw_before):
			failures.append("Live 4D post-game left drag must not rotate outer framing")
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
		var restart_basis_before: Array = app._live_4d_basis.slots()
		var restart_local_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var restart_camera_before: Dictionary = app._camera_rig.presentation_snapshot()
		app._reset_live_4d()
		if app._live_4d_basis.slots() != restart_basis_before or app._live_4d_local_orientation.snapshot() != restart_local_before or app._camera_rig.presentation_snapshot() != restart_camera_before:
			failures.append("Restart Game must preserve B, L, layout-facing camera state, and framing")
		app._set_live_4d_local_orientation(0.7, 0.2)
		app._apply_live_4d_basis_turn("xw", 1)
		var reset_view_native_snapshot: String = app._live_bridge.live_4d_snapshot_json()
		var reset_view_hash: String = str(app._live_bridge.live_4d_state_hash())
		app._reset_view()
		if not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0}:
			failures.append("Reset View should coherently restore identity B and default shared L")
		if app._renderer._live_4d_fit_reference != app._renderer.current_bounds() or app._camera_rig._framing_status != "fit OK":
			failures.append("Reset View should refresh oriented bounds and fitted framing")
		if app._live_bridge.live_4d_snapshot_json() != reset_view_native_snapshot or str(app._live_bridge.live_4d_state_hash()) != reset_view_hash:
			failures.append("Reset View must remain presentation-only")
		var basis_native_snapshot_before: String = str(app._live_bridge.live_4d_snapshot_json())
		var basis_hash_before := str(app._live_bridge.live_4d_state_hash())
		var basis_camera_before: Dictionary = app._camera_rig.presentation_snapshot()
		var local_orientation_before_basis: Dictionary = app._live_4d_local_orientation.snapshot()
		app._apply_live_4d_basis_turn("xw", 1)
		if app._live_4d_basis.slots() != [4, 2, 3, -1]:
			failures.append("XW+ should commit the exact presentation basis immediately")
		if app._live_bridge.live_4d_snapshot_json() != basis_native_snapshot_before or str(app._live_bridge.live_4d_state_hash()) != basis_hash_before:
			failures.append("basis-only actions must not change native snapshot or state hash")
		if app._camera_rig.presentation_snapshot() != basis_camera_before:
			failures.append("basis turns must not change camera orientation, zoom intent, or translation")
		if app._live_4d_local_orientation.snapshot() != local_orientation_before_basis:
			failures.append("exact B turns must not mutate shared L")
		var horizontal_arrow := app._camera_rig.get_node_or_null("OrientationGizmo/HorizontalArrow") as MeshInstance3D
		var depth_arrow := app._camera_rig.get_node_or_null("OrientationGizmo/DepthArrow") as MeshInstance3D
		var gravity_arrow := app._camera_rig.get_node_or_null("OrientationGizmo/GravityArrow") as MeshInstance3D
		if horizontal_arrow == null or str(horizontal_arrow.get_meta("signed_axis", "")) != "+W" or depth_arrow == null or str(depth_arrow.get_meta("signed_axis", "")) != "+Z" or gravity_arrow == null or str(gravity_arrow.get_meta("signed_axis", "")) != "+Y":
			failures.append("basis-driven orientation arrows should expose XW visible axes with stable gravity")
		app._dispatch_live_4d_control_intent("move_x_pos")
		if str(app._current_snapshot.get("last_command", "")) != "move_w_pos":
			failures.append("visible +W horizontal intent should route to canonical W+")
		var basis_only_native_before: String = app._live_bridge.live_4d_snapshot_json()
		var basis_only_hash_before: String = str(app._live_bridge.live_4d_state_hash())
		app._set_live_4d_local_orientation(0.31, -0.17)
		app._camera_rig.pan_focus(Vector3(1.5, -0.5, 0.0))
		app._camera_rig.zoom(-1.0)
		var basis_only_l_before: Dictionary = app._live_4d_local_orientation.snapshot()
		var basis_only_camera_before: Dictionary = app._camera_rig.presentation_snapshot()
		app._reset_live_4d_basis_only()
		if not app._live_4d_basis.is_identity():
			failures.append("basis-only reset must restore identity B")
		if app._live_4d_local_orientation.snapshot() != basis_only_l_before or app._camera_rig.presentation_snapshot() != basis_only_camera_before:
			failures.append("basis-only reset must preserve L, pan/focus, zoom, projection, and preferences")
		if app._live_bridge.live_4d_snapshot_json() != basis_only_native_before or str(app._live_bridge.live_4d_state_hash()) != basis_only_hash_before:
			failures.append("basis-only reset must remain outside deterministic identity")
		app._reset_live_4d()
		app._reset_view()
		app._apply_live_4d_basis_turn("zx", 1)
		if app._live_4d_basis.slots() != [-3, 2, 1, 4]:
			failures.append("ZX+ should commit the exact visible X/Z basis rotation")
		var zx_horizontal_arrow := app._camera_rig.get_node_or_null("OrientationGizmo/HorizontalArrow") as MeshInstance3D
		var zx_depth_arrow := app._camera_rig.get_node_or_null("OrientationGizmo/DepthArrow") as MeshInstance3D
		if zx_horizontal_arrow == null or str(zx_horizontal_arrow.get_meta("signed_axis", "")) != "-Z" or zx_depth_arrow == null or str(zx_depth_arrow.get_meta("signed_axis", "")) != "+X":
			failures.append("ZX+ arrows should derive swapped signed visible axes from BasisState")
		app._dispatch_live_4d_control_intent("move_x_pos")
		if str(app._current_snapshot.get("last_command", "")) != "move_z_neg":
			failures.append("ZX viewer-relative movement should agree with the basis-driven horizontal arrow")
		app._reset_live_4d()
		app._reset_view()
		for _turn_index in range(4):
			app._apply_live_4d_basis_turn("xw", 1)
		if app._live_4d_basis.slots() != [1, 2, 3, 4]:
			failures.append("rapid four-turn basis input must compose exactly to identity")
		app._renderer._process(0.2)
		if float(app._renderer.live_4d_basis_snapshot().get("transition_progress", 0.0)) < 1.0:
			failures.append("basis transition should settle without a stuck intermediate state")
		app._reset_live_4d()
		app._reset_view()
		app._dispatch_live_4d_gameplay_command("hard_drop")
		var identity_drop_hash := str(app._live_bridge.live_4d_state_hash())
		app._reset_live_4d()
		app._reset_view()
		app._apply_live_4d_basis_turn("zw", -1)
		app._dispatch_live_4d_gameplay_command("hard_drop")
		if str(app._live_bridge.live_4d_state_hash()) != identity_drop_hash:
			failures.append("hard drop after a basis turn must preserve canonical Y-gravity outcome")
		app._reset_live_4d()
		app._reset_view()
		for canonical_command in ["move_x_pos", "move_z_neg", "move_w_pos"]:
			app._dispatch_live_4d_gameplay_command(canonical_command)
		var canonical_sequence_hash := str(app._live_bridge.live_4d_state_hash())
		app._reset_live_4d()
		app._reset_view()
		app._apply_live_4d_basis_turn("xw", 1)
		app._dispatch_live_4d_gameplay_command("move_x_pos")
		app._apply_live_4d_basis_turn("zw", -1)
		app._dispatch_live_4d_gameplay_command("move_z_neg")
		app._apply_live_4d_basis_turn("xw", -1)
		app._dispatch_live_4d_gameplay_command("move_w_pos")
		if str(app._live_bridge.live_4d_state_hash()) != canonical_sequence_hash:
			failures.append("basis events interleaved with canonical commands must preserve replay identity")
		app._reset_live_4d()
		app._reset_view()
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
		app._set_live_4d_local_orientation(0.42, 0.18)
		app._apply_live_4d_basis_turn("zw", 1)
		app._camera_rig.zoom(-1.0)
		app._enter_replay_mode()
		await tree.process_frame
		app._enter_live_4d_mode()
		await tree.process_frame
		if app._live_4d_paused:
			failures.append("switching back to Live 4D should resume the selected live mode")
		if not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0} or app._camera_rig._framing_status != "fit OK" or not bool(app._camera_rig.presentation_snapshot().get("horizontal_reflection_active", false)):
			failures.append("re-entering Live 4D must use fresh B, L, V/P, and reflection defaults")
		var switched_fit_size := live_4d_camera.size if live_4d_camera != null else 0.0
		app._input(zoom_out_event)
		if live_4d_camera != null and live_4d_camera.size <= switched_fit_size:
			failures.append("Live 4D zoom should work after switching away and back")
		app._set_live_4d_local_orientation(0.28, -0.12)
		app._apply_live_4d_basis_turn("xw", 1)
		app._enter_live_3d_mode()
		if str(app._current_snapshot.get("trace_type", "")) != "live_3d" or not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0}:
			failures.append("4D to 3D transition must clear Live-4D presentation state before the 3D frame")
		if bool(app._camera_rig.presentation_snapshot().get("horizontal_reflection_active", false)) or app._live_4d_presentation_root.transform != Transform3D.IDENTITY:
			failures.append("Live 3D must not inherit Live-4D reflection authority")
		app._enter_live_4d_mode()
		app._set_live_4d_local_orientation(0.2, 0.1)
		app._apply_live_4d_basis_turn("zw", -1)
		app._change_live_setup(TraceReplayAppScript.MODE_LIVE_4D)
		_assert_live_4d_teardown(failures, app, "Change Setup")
		if app._live_4d_session_started:
			failures.append("Change Setup must end the current Live-4D session ownership")
		app._enter_live_4d_mode()
		if not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0} or app._camera_rig._framing_status != "fit OK":
			failures.append("Live-4D relaunch after Change Setup must start from coherent defaults")
		app._return_to_main_menu()
		_assert_live_4d_teardown(failures, app, "Main Menu")
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
		"live_4d_camera_zoom_in",
		"live_4d_camera_zoom_out",
		"mode_toggle_replay_live",
		"quit",
	]:
		if not InputMap.has_action(action_name):
			failures.append("InputMap missing %s" % action_name)
	for obsolete_action in ["live_4d_camera_roll_left", "live_4d_camera_roll_right"]:
		if InputMap.has_action(obsolete_action):
			failures.append("normal Live 4D InputMap must not register %s" % obsolete_action)
	for soft_drop_action in ["live_3d_soft_drop", "live_4d_soft_drop"]:
		var has_ctrl := false
		var has_shift := false
		for binding in InputMap.action_get_events(soft_drop_action):
			if binding is InputEventKey:
				has_ctrl = has_ctrl or (binding as InputEventKey).keycode == KEY_CTRL
				has_shift = has_shift or (binding as InputEventKey).keycode == KEY_SHIFT
		if not has_ctrl or has_shift:
			failures.append("%s should bind Ctrl and must not bind Shift" % soft_drop_action)
	for action_name in LiveInputContractScript.ACTION_SPECS:
		var spec: Dictionary = LiveInputContractScript.ACTION_SPECS.get(action_name, {})
		for required_key in spec.get("keys", []):
			var expected_event := InputEventKey.new()
			expected_event.keycode = int(required_key)
			if not InputMap.action_has_event(str(action_name), expected_event):
				failures.append("InputMap %s should consume the shared contract binding %s" % [action_name, str(required_key)])
	if app != null and app._hud != null:
		app._hud._settings_store.set_value("display.ui_scale", "standard")
	root.queue_free()
	await tree.process_frame
	return failures


func _assert_live_4d_teardown(failures: Array, app, label: String) -> void:
	for root_name in ["GridRoot", "CellRoot", "ParticleRoot", "MarkerRoot"]:
		var presentation_root: Node = app._renderer.get_node_or_null(root_name)
		if presentation_root == null or presentation_root.get_child_count() != 0:
			failures.append("%s must synchronously clear %s" % [label, root_name])
	if bool(app._renderer.current_bounds().get("ok", true)) or not app._renderer._live_4d_fit_reference.is_empty():
		failures.append("%s must clear bounds and fit-reference authority" % label)
	if bool(app._camera_rig.presentation_snapshot().get("horizontal_reflection_active", true)) or app._live_4d_presentation_root.transform != Transform3D.IDENTITY:
		failures.append("%s must clear reflection authority" % label)
	if not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0}:
		failures.append("%s must clear B and L" % label)


func _assert_app_live_4d_semantic_directions(failures: Array, app, label: String) -> void:
	var mapping = app._control_frame_mapping(4)
	var projection = app._renderer._presentation.projection
	var origin := [2, 3, 1, 0]
	for intent in ["move_x_pos", "move_z_neg"]:
		var command: String = mapping.translation_command(intent, "relative")
		var delta := _canonical_4d_delta(command)
		var destination := origin.duplicate()
		for axis in range(4):
			destination[axis] = int(destination[axis]) + int(delta[axis])
		var origin_world: Vector3 = app._renderer.to_global(projection.oriented_world_position(origin))
		var destination_world: Vector3 = app._renderer.to_global(projection.oriented_world_position(destination))
		if app._camera_rig.is_world_point_behind(origin_world) or app._camera_rig.is_world_point_behind(destination_world):
			failures.append("%s: production projection points must be in front of Camera3D" % label)
			continue
		if intent == "move_x_pos":
			var origin_screen: Vector2 = app._camera_rig.project_world_point(origin_world)
			var destination_screen: Vector2 = app._camera_rig.project_world_point(destination_world)
			if destination_screen.x - origin_screen.x <= SCREEN_RIGHT_TOLERANCE_PX:
				failures.append("%s: actual app-owned Right must increase Camera3D screen X" % label)
		if intent == "move_z_neg":
			var origin_view: Vector3 = app._camera_rig.camera_space_point(origin_world)
			var destination_view: Vector3 = app._camera_rig.camera_space_point(destination_world)
			if origin_view.z - destination_view.z <= AWAY_DEPTH_TOLERANCE:
				failures.append("%s: actual app-owned Forward must remain strictly receding" % label)


func _canonical_4d_delta(command: String) -> Array:
	match command:
		"move_x_neg": return [-1, 0, 0, 0]
		"move_x_pos": return [1, 0, 0, 0]
		"move_z_neg": return [0, 0, -1, 0]
		"move_z_pos": return [0, 0, 1, 0]
		_: return [0, 0, 0, 0]


# Player-facing camera help must be executable truth: every listed command has
# to name the binding the runtime actually routes. Live 3D binds F/G to Rotate
# XZ, so its Fit affordance is the viewport double-click, not F.
func _assert_camera_command_help_is_executable_truth(
	live_2d_hint: String,
	live_3d_hint: String,
	live_4d_hint: String,
	failures: Array
) -> void:
	var reset_key := LiveInputContractScript.display_key("reset")
	if reset_key != "0":
		failures.append("Reset View helper key should resolve from the reset action contract, got %s" % reset_key)
	if not live_2d_hint.contains("%s Reset View" % reset_key):
		failures.append("live 2D hint text should advertise Reset View by its real key binding")
	if not live_2d_hint.contains("F Fit View (framing only)"):
		failures.append("live 2D hint text should advertise the F Fit View binding it actually routes")
	if not live_3d_hint.contains("%s Reset View" % reset_key):
		failures.append("live 3D hint text should advertise Reset View by its real key binding")
	if not live_3d_hint.contains("Double-click Fit View (framing only)"):
		failures.append("live 3D hint text should advertise the double-click Fit View affordance it actually routes")
	if live_3d_hint.contains("F Fit View"):
		failures.append("live 3D hint text must not advertise F as Fit View; F is Rotate XZ in Live 3D")
	if not live_3d_hint.contains("F/G Rotate XZ"):
		failures.append("live 3D hint text should keep F/G documented as Rotate XZ")
	if not live_4d_hint.contains("%s Reset View" % reset_key):
		failures.append("live 4D hint text should keep advertising Reset View by its real key binding")
	if not live_4d_hint.contains("Double-click Fit View (framing only)"):
		failures.append("live 4D hint text should keep advertising the double-click Fit View affordance")
	for hint in [live_2d_hint, live_3d_hint, live_4d_hint]:
		if hint.contains("Reset View button"):
			failures.append("live control hints must not point at a Reset View button that live modes do not present")


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
	if summary != "Live Plain 3D | SCORE 45 | CLEARS 1 | Active O3 | Speed 1 | LOCKED":
		failures.append("ordinary live summary should prioritize actionable gameplay state and leave NEXT to its panel, got %s" % summary)
	var detailed_summary := ReplayHudScript.live_gameplay_summary_text(live_snapshot, "Live Plain 3D", {}, true)
	if detailed_summary.find("Board 6 × 10 × 6") == -1 or detailed_summary.find("Seed 1337") == -1 or detailed_summary.find("O3 > L3") != -1:
		failures.append("detailed live summary should add setup detail without duplicating the NEXT queue")
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
