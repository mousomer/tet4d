extends RefCounted

const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")


func run() -> Array:
	var failures: Array = []
	var replay_hint := ReplayHudScript.replay_hint_text()
	var live_hint := ReplayHudScript.live_2d_hint_text()
	var live_3d_hint := ReplayHudScript.live_3d_hint_text()
	var expected_live_hint := "A/D or ←/→ Move · W/↑/X Rotate · Z Rotate CCW · S/↓ Soft Drop · Space Hard Drop · P Pause · R Reset · F Fit · Tab Live 3D · Q/Esc Quit"
	var expected_live_3d_hint := "A/D or ←/→ X Move · W/S or ↑/↓ Z Move · Shift Soft Drop · Space Hard Drop · R/T XY Rotate · F/G XZ Rotate · V/B YZ Rotate · P Pause · Backspace Reset · Tab Replay · Q/Esc Quit"
	var expected_replay_hint := "Space Play/Pause Replay · ←/→ Frame · ↑/↓ Case · 1/2/3 Family · F Fit · H Help · Tab Live 2D · Q/Esc Quit"
	if live_hint != expected_live_hint:
		failures.append("live 2D hint text should match the Stage 12 visible control strip")
	if replay_hint != expected_replay_hint:
		failures.append("replay hint text should match the replay control strip")
	if live_3d_hint != expected_live_3d_hint:
		failures.append("live 3D hint text should match the Stage 22 visible control strip")
	if not live_hint.contains("A/D") or not live_hint.contains("Hard Drop") or not live_hint.contains("Tab Live 3D"):
		failures.append("live 2D hint text should expose movement, drop, and Tab-to-Live-3D controls")
	if live_hint.contains("Frame"):
		failures.append("live 2D hint text should not expose replay frame controls")
	if replay_hint.contains("Hard Drop") or replay_hint.contains("Rotate CW"):
		failures.append("replay hint text should not expose live gameplay controls")
	if not live_3d_hint.contains("R/T XY") or not live_3d_hint.contains("Backspace Reset"):
		failures.append("live 3D hint text should expose direct rotation and reset controls")
	if absf(TraceReplayAppScript.LIVE_GRAVITY_INTERVAL_SECONDS - 0.5) > 0.001:
		failures.append("live gravity shell interval should default to 0.5 seconds")
	if TraceReplayAppScript.LIVE_HORIZONTAL_REPEAT_INTERVAL_SECONDS <= 0.0:
		failures.append("live horizontal repeat interval should be configured")

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
		if str(live_snapshot.get("current_piece", "")) != "O":
			failures.append("switching back to Live 2D should preserve the native live session")
		var paused_hash := str(live_snapshot.get("state_hash", ""))
		if app._dispatch_live_gameplay_command("move_left"):
			failures.append("paused live mode should block gameplay command dispatch")
		if str(app._current_snapshot.get("state_hash", "")) != paused_hash:
			failures.append("blocked paused command should not mutate the live snapshot")
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
		app._dispatch_live_3d_gameplay_command("hard_drop")
		if str(app._current_snapshot.get("current_piece", "")) != "O3":
			failures.append("live 3D hard drop should route to C++ and spawn O3")
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
		if str(app._current_snapshot.get("current_piece", "")) != "O3":
			failures.append("switching back to Live 3D should preserve the native live session")
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
		"mode_toggle_replay_live",
		"quit",
	]:
		if not InputMap.has_action(action_name):
			failures.append("InputMap missing %s" % action_name)
	root.queue_free()
	await tree.process_frame
	return failures
