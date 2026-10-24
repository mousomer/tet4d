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
	hud._apply_hud_density("standard")
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
	# The 4D split puts NEXT/HOLD + VIEW in a side column; board and column
	# still account for the whole accepted width.
	var side: Rect2 = cockpit.get("side_column_rect", Rect2())
	var stage_width := game.size.x + (side.size.x + float(LiveCockpitScript.SIDE_RAIL_GAP) if side.size.x > 0.0 else 0.0)
	# The legend deck takes its measured height unscrolled; the board keeps the rest.
	if not is_equal_approx(stage_width, 1576.0) or game.size.y < 550.0 or absf(deck.size.y - float(cockpit.get("deck_natural_height", 0.0))) > 0.5 or bool(cockpit.get("deck_scroll_required", true)):
		failures.append("LiveCockpit extraction must show the whole 4D legend and keep the 1600x960 board allocation, got game=%s deck=%s natural=%s" % [game, deck, cockpit.get("deck_natural_height")])
	if game.intersects(deck):
		failures.append("LiveCockpit extraction must keep primary board and control deck non-overlapping")
	if str(app._live_bridge.live_4d_state_hash()) != hash_before:
		failures.append("LiveCockpit extraction must not mutate deterministic gameplay state")
	failures.append_array(_check_4d_panel_structure(hud))
	app._enter_live_3d_mode()
	await tree.process_frame
	await tree.process_frame
	failures.append_array(_check_3d_panel_structure(hud))
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


# The 4D helper set is the reference the 3D rail mirrors; pin it so the shared
# rail work cannot reshape it.
func _check_4d_panel_structure(hud) -> Array:
	var failures: Array = []
	var cockpit: Dictionary = hud.layout_contract_snapshot().get("live_cockpit", {})
	if cockpit.get("deck_placement") != LiveCockpitScript.PLACEMENT_SPLIT or bool(cockpit.get("wide_rail", true)):
		failures.append("Live 4D must keep its split side column, got %s" % cockpit.get("deck_placement"))
	if hud._piece_preview_row.columns != 1:
		failures.append("Live 4D must keep NEXT and HOLD stacked in its side column")
	if hud._piece_control_strip.deterministic_snapshot().get("layout") != "wide":
		failures.append("Live 4D must keep the wide MOVE / ROTATE / GAME legend")
	var view: Dictionary = hud._live_view_control_strip.deterministic_snapshot()
	if view.get("layout") != "wide" or view.get("roles") != ["view_exact", "view_orient"]:
		failures.append("Live 4D VIEW must keep only TURN VIEW and LOOK, got %s" % str(view.get("roles")))
	return failures


# Live 3D shows the 4D helper set on the right: NEXT and HOLD as separate
# panels, the wide legend, then VIEW, all visible without a toggle.
func _check_3d_panel_structure(hud) -> Array:
	var failures: Array = []
	var layout: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = layout.get("live_cockpit", {})
	if cockpit.get("deck_placement") != LiveCockpitScript.PLACEMENT_SIDE or not bool(cockpit.get("wide_rail", false)) or not bool(cockpit.get("deck_visible", false)):
		failures.append("Live 3D must show its helpers in the wide side rail, got %s" % cockpit.get("deck_placement"))
	if cockpit.get("deck_row_assignment") != [["PieceState"], ["PieceControls"], ["ViewControls"]]:
		failures.append("Live 3D rail must stack NEXT/HOLD, the legend, then VIEW, got %s" % str(cockpit.get("deck_row_assignment")))
	var board: Rect2 = layout.get("game_area", Rect2())
	var rail: Rect2 = layout.get("live_4d_deck", Rect2())
	if rail.position.x < board.end.x:
		failures.append("Live 3D rail must sit right of the board: board %s rail %s" % [board, rail])
	if rail.size.x < LiveCockpitScript.WIDE_RAIL_MIN_WIDTH - 0.5:
		failures.append("Live 3D rail must keep its wide-legend width, got %s" % rail.size.x)
	for module in [hud._live_cockpit.piece_state, hud._live_cockpit.piece_controls, hud._live_cockpit.view_controls]:
		if not (module as Control).is_visible_in_tree():
			failures.append("Live 3D rail module %s must be visible by default" % module.name)
	var next_rect: Rect2 = hud._next_piece_panel.get_global_rect()
	var hold_rect: Rect2 = hud._hold_piece_panel.get_global_rect()
	if hud._piece_preview_row.get_parent() != hud._live_cockpit.piece_state or next_rect.intersects(hold_rect) or next_rect.size.x <= 0.0 or hold_rect.size.x <= 0.0:
		failures.append("Live 3D must show NEXT and HOLD as separate PIECE STATE panels")
	if hud._piece_control_strip.deterministic_snapshot().get("layout") != "wide":
		failures.append("Live 3D must use the 4D wide MOVE / ROTATE / GAME legend")
	var view: Dictionary = hud._live_view_control_strip.deterministic_snapshot()
	if view.get("layout") != "wide" or view.get("row_ids") != ["view_framing:Fit", "view_framing:Reset", "view_pointer:Orient", "view_pointer:Translate", "view_pointer:Zoom"]:
		failures.append("Live 3D VIEW must list framing and pointer controls, got %s" % str(view.get("row_ids")))
	return failures
