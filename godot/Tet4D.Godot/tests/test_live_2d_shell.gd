extends RefCounted

const ReplayHudScript = preload("res://scripts/ui/replay_hud.gd")


func run() -> Array:
	var failures: Array = []
	var replay_hint := ReplayHudScript.replay_hint_text()
	var live_hint := ReplayHudScript.live_2d_hint_text()
	var expected_live_hint := "A/D or ←/→ Move · W/↑/X Rotate · Z Rotate CCW · S/↓ Soft Drop · Space Hard Drop · P Pause · R Reset · Tab Replay · Q/Esc Quit"
	var expected_replay_hint := "Space Play/Pause Replay · ←/→ Frame · ↑/↓ Case · 1/2/3 Family · F Fit · H Help · Tab Live 2D · Q/Esc Quit"
	if live_hint != expected_live_hint:
		failures.append("live 2D hint text should match the Stage 12 visible control strip")
	if replay_hint != expected_replay_hint:
		failures.append("replay hint text should match the replay control strip")
	if not live_hint.contains("A/D") or not live_hint.contains("Hard Drop") or not live_hint.contains("Tab Replay"):
		failures.append("live 2D hint text should expose movement, drop, and Tab-to-replay controls")
	if live_hint.contains("Frame"):
		failures.append("live 2D hint text should not expose replay frame controls")
	if replay_hint.contains("Hard Drop") or replay_hint.contains("Rotate CW"):
		failures.append("replay hint text should not expose live gameplay controls")

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
	for action_name in [
		"live_move_left",
		"live_move_right",
		"live_rotate_cw",
		"live_rotate_ccw",
		"live_soft_drop",
		"live_hard_drop",
		"live_pause",
		"live_reset",
		"mode_toggle_replay_live",
		"quit",
	]:
		if not InputMap.has_action(action_name):
			failures.append("InputMap missing %s" % action_name)
	root.queue_free()
	await tree.process_frame
	return failures
