extends RefCounted

const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(_check_component_boundary())
	failures.append_array(await _check_production_extraction())
	return failures


func _check_component_boundary() -> Array:
	var failures: Array = []
	var cockpit = LiveCockpitScript.new()
	var snapshot: Dictionary = cockpit.deterministic_snapshot()
	if snapshot.get("slots") != ["Header", "PrimaryBoardSurface", "ControlDeck"]:
		failures.append("LiveCockpit must expose the shared header/primary/deck grammar")
	if snapshot.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("LiveCockpit must expose the three semantic deck modules")
	if snapshot.get("deck_ratios") != [42.0, 33.0, 25.0]:
		failures.append("LiveCockpit must preserve the accepted 42/33/25 allocation")
	var source := FileAccess.get_file_as_string("res://scripts/ui/live_cockpit.gd")
	for forbidden in ["TraceSceneRenderer", "LiveInputContract", "CameraRig", "render_snapshot", "InputMap", "piece_control_groups"]:
		if source.contains(forbidden):
			failures.append("LiveCockpit must not acquire renderer/input authority: %s" % forbidden)
	cockpit.free()
	return failures


func _check_production_extraction() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["LiveCockpit production check requires the trace replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	app._enter_live_4d_mode()
	await tree.process_frame
	await tree.process_frame
	var hash_before := str(app._live_bridge.live_4d_state_hash())
	var layout: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = layout.get("live_cockpit", {})
	if cockpit.get("slots") != ["Header", "PrimaryBoardSurface", "ControlDeck"] or not cockpit.get("deck_visible", false):
		failures.append("production Live 4D must use the extracted LiveCockpit grammar")
	if hud._piece_control_strip.get_parent() != hud._live_cockpit.piece_controls or hud._live_view_control_strip.get_parent() != hud._live_cockpit.view_controls or hud._piece_preview_row.get_parent() != hud._live_cockpit.piece_state:
		failures.append("production helper and piece-state consumers must occupy their named LiveCockpit slots")
	var game: Rect2 = layout.get("game_area", Rect2())
	var deck: Rect2 = layout.get("live_4d_deck", Rect2())
	if not is_equal_approx(game.size.x, 1576.0) or not is_equal_approx(game.size.y, 604.0) or not is_equal_approx(deck.size.y, 228.0):
		failures.append("LiveCockpit extraction must preserve the accepted 1600x960 Live-4D rectangles, got game=%s deck=%s" % [game, deck])
	if game.intersects(deck):
		failures.append("LiveCockpit extraction must keep primary board and control deck non-overlapping")
	if str(app._live_bridge.live_4d_state_hash()) != hash_before:
		failures.append("LiveCockpit extraction must not mutate deterministic gameplay state")
	for enter_mode in [Callable(app, "_enter_live_2d_mode"), Callable(app, "_enter_live_3d_mode")]:
		enter_mode.call()
		await tree.process_frame
		await tree.process_frame
		if hud._live_cockpit.control_deck.visible:
			failures.append("unmigrated Live 2D/3D must retain their legacy outer layout with the shared deck hidden")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
