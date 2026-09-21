extends RefCounted

const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(await _assert_component_grammar())
	failures.append_array(await _check_production_extraction())
	return failures


func _assert_component_grammar() -> Array:
	var failures: Array = []
	var cockpit = LiveCockpitScript.new()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(cockpit)
	await tree.process_frame
	var snapshot: Dictionary = cockpit.deterministic_snapshot()
	if snapshot.get("slots") != ["Header", "PrimaryBoardSurface", "ControlDeck"]:
		failures.append("LiveCockpit must expose the shared header/primary/deck grammar")
	if snapshot.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("LiveCockpit must expose the three semantic deck modules")
	# Breakpoints classify APPARENT size (window client pixels / display scale /
	# UI scale), never the logical viewport, which is pinned to the design
	# resolution by canvas_items stretch and cannot express shell size.
	var expected_profiles := {
		Vector2(1920.0, 1080.0): "wide",
		Vector2(1440.0, 900.0): "standard",
		Vector2(960.0, 640.0): "narrow",
		Vector2(634.0, 624.0): "small",
	}
	for apparent_size in expected_profiles:
		cockpit.set_available_size(Vector2(1600.0, 960.0), apparent_size, "standard")
		var responsive: Dictionary = cockpit.deterministic_snapshot()
		if responsive.get("responsive_profile") != expected_profiles[apparent_size]:
			failures.append("LiveCockpit must deterministically classify %s as %s" % [apparent_size, expected_profiles[apparent_size]])
		if responsive.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
			failures.append("responsive policy must not fork or reorder the semantic modules")
	# Packing is driven by measured minimum width, so a layout narrower than the
	# three-across minimum must reflow into rows instead of overflowing. Stretch
	# ratios only distribute surplus and cannot prevent overflow on their own.
	for module in [cockpit.piece_controls, cockpit.view_controls, cockpit.piece_state]:
		module.custom_minimum_size = Vector2(400.0, 40.0)
	await tree.process_frame
	cockpit.set_available_size(Vector2(1600.0, 960.0), Vector2(1600.0, 960.0), "standard")
	var roomy: Dictionary = cockpit.deterministic_snapshot()
	if int(roomy.get("deck_row_count", 0)) != 1:
		failures.append("a layout wider than the deck minimum must stay on one row")
	cockpit.set_available_size(Vector2(900.0, 960.0), Vector2(900.0, 960.0), "standard")
	var packed: Dictionary = cockpit.deterministic_snapshot()
	if int(packed.get("deck_row_count", 0)) < 2:
		failures.append("a layout narrower than the deck minimum must reflow into rows")
	if float(packed.get("deck_minimum_width", 0.0)) > 900.0:
		failures.append("reflow must eliminate horizontal overflow, got minimum width %s" % packed.get("deck_minimum_width"))
	var flattened: Array = []
	for row in packed.get("deck_row_assignment", []):
		for module_name in row:
			flattened.append(str(module_name))
	if flattened != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("reflow must preserve semantic module order across rows, got %s" % str(flattened))
	var source := FileAccess.get_file_as_string("res://scripts/ui/live_cockpit.gd")
	for forbidden in ["TraceSceneRenderer", "LiveInputContract", "CameraRig", "render_snapshot", "InputMap", "piece_control_groups"]:
		if source.contains(forbidden):
			failures.append("LiveCockpit must not acquire renderer/input authority: %s" % forbidden)
	cockpit.queue_free()
	await tree.process_frame
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
	# Other in-process tests exercise global accessibility and onboarding state.
	# This geometry contract has a standard-density, no-overlay precondition.
	hud._apply_ui_scale("standard")
	hud._set_onboarding_visible(false)
	await tree.process_frame
	await tree.process_frame
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
	# Shared font resources can retain an accessibility scale across the complete
	# in-process suite. Preserve the accepted horizontal allocation and require
	# the board/deck split to stay within the supported scaled range.
	if not is_equal_approx(game.size.x, 1576.0) or game.size.y < 550.0 or deck.size.y < 210.0 or deck.size.y > 230.0:
		failures.append("LiveCockpit extraction must preserve the accepted 1600x960 allocation envelope, got game=%s deck=%s" % [game, deck])
	if game.intersects(deck):
		failures.append("LiveCockpit extraction must keep primary board and control deck non-overlapping")
	if str(app._live_bridge.live_4d_state_hash()) != hash_before:
		failures.append("LiveCockpit extraction must not mutate deterministic gameplay state")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
