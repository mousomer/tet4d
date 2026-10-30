extends RefCounted

const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(await _assert_inactive_fit_cancellation())
	failures.append_array(await _assert_existing_content_refit())
	failures.append_array(await _assert_component_grammar())
	failures.append_array(await _assert_metrics_signal_during_visibility_propagation())
	failures.append_array(await _check_production_extraction())
	return failures


func _assert_existing_content_refit() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var cockpit = _content_fixture(tree, 40)
	await _settle_fit(tree, cockpit)
	var before := float(cockpit.deterministic_snapshot()["deck_fit_scale"])
	var label: Label = cockpit.piece_controls.get_child(0)
	# Edit the same node, at the same host constraints, in both directions.
	for lines in [16, 48, 16]:
		label.text = "Existing content\n".repeat(lines)
		await _settle_fit(tree, cockpit)
		var clean = _content_fixture(tree, lines)
		await _settle_fit(tree, clean)
		var actual: Dictionary = cockpit.deterministic_snapshot()
		var expected: Dictionary = clean.deterministic_snapshot()
		if not cockpit.fit_settled() or not clean.fit_settled():
			failures.append("content fits must converge without repeated invalidation")
		if absf(float(actual["deck_fit_scale"]) - float(expected["deck_fit_scale"])) > 0.001:
			failures.append("existing-label edit must match clean-entry scale for %s lines" % lines)
		if lines == 16 and float(actual["deck_fit_scale"]) <= before:
			failures.append("shorter existing content must recover a larger scale")
		clean.queue_free()
		await tree.process_frame
	for font_size in [32, 16]:
		label.add_theme_font_size_override("font_size", font_size)
		await _settle_fit(tree, cockpit)
		var clean = _content_fixture(tree, 16, font_size)
		await _settle_fit(tree, clean)
		if not cockpit.fit_settled() or absf(float(cockpit.deterministic_snapshot()["deck_fit_scale"]) - float(clean.deterministic_snapshot()["deck_fit_scale"])) > 0.001:
			failures.append("existing font-metric changes must match clean entry")
		clean.queue_free()
		await tree.process_frame
	cockpit.queue_free()
	await tree.process_frame
	return failures


func _content_fixture(tree: SceneTree, lines: int, font_size: int = 16):
	var cockpit = LiveCockpitScript.new()
	tree.root.add_child(cockpit)
	cockpit.size = Vector2(900, 500)
	var label := Label.new()
	label.text = "Existing content\n".repeat(lines)
	label.add_theme_font_size_override("font_size", font_size)
	cockpit.piece_controls.add_child(label)
	cockpit.set_available_size(Vector2(900, 500), Vector2(900, 500))
	cockpit.set_deck_placement(LiveCockpitScript.PLACEMENT_SIDE)
	cockpit.set_control_deck_visible(true)
	return cockpit


func _settle_fit(tree: SceneTree, cockpit) -> void:
	# Let minimum-size signals enqueue their first pass before checking idle.
	for _frame in range(4):
		await tree.process_frame
	for _frame in range(160):
		if cockpit.fit_settled():
			return
		await tree.process_frame


# Showing the viewer screen propagates visibility down the cockpit, and Godot
# refuses add_child on a node while it notifies its children. A module metric
# signal emitted then must not reparent the deck mid-propagation: reparent()
# removes it first, so a refused add leaves the deck with no parent at all
# (Live 4D reached after 2D/3D showed no lower helper panel).
func _assert_metrics_signal_during_visibility_propagation() -> Array:
	var failures: Array = []
	var cockpit = LiveCockpitScript.new()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(cockpit)
	cockpit.set_available_size(Vector2(1600.0, 960.0), Vector2(1600.0, 960.0), "standard")
	cockpit.set_control_deck_visible(true)
	cockpit.set_deck_placement(LiveCockpitScript.PLACEMENT_SIDE)
	await tree.process_frame
	await tree.process_frame
	# A mode switch that requested the split before its first layout pass.
	cockpit._requested_placement = LiveCockpitScript.PLACEMENT_SPLIT
	var probe := Control.new()
	cockpit.board_column.add_child(probe)
	# A shown module re-measures; the changed minimum is what makes the policy act.
	probe.visibility_changed.connect(func() -> void:
		cockpit.piece_controls.custom_minimum_size.y += 1.0
		cockpit.piece_controls.minimum_size_changed.emit())
	cockpit.board_column.visible = false
	cockpit.board_column.visible = true
	await tree.process_frame
	await tree.process_frame
	if cockpit.control_deck.get_parent() == null:
		failures.append("a metrics signal during visibility propagation must not orphan the control deck")
	elif cockpit.deck_placement() != LiveCockpitScript.PLACEMENT_SPLIT:
		failures.append("the deferred metrics pass must still apply the requested split, got %s" % cockpit.deck_placement())
	cockpit.queue_free()
	await tree.process_frame
	return failures


func _assert_component_grammar() -> Array:
	var failures: Array = []
	var cockpit = LiveCockpitScript.new()
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(cockpit)
	await tree.process_frame
	# Packing assertions describe an active cockpit, not an invisible deck.
	cockpit.set_control_deck_visible(true)
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
	# Rows pack NEXT/HOLD first, as in the rail and the split column.
	if flattened != ["PieceState", "PieceControls", "ViewControls"]:
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
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _assert_inactive_fit_cancellation() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var cockpit = _content_fixture(tree, 40)
	await tree.process_frame
	cockpit.set_control_deck_visible(false)
	if not cockpit.fit_settled():
		failures.append("hiding a cockpit must cancel all probes and queued work synchronously")
	for _frame in range(10):
		await tree.process_frame
	if not cockpit.fit_settled():
		failures.append("inactive cockpit metric signals must not restart hidden fitting")
	cockpit.set_control_deck_visible(true)
	await _settle_fit(tree, cockpit)
	if not cockpit.fit_settled():
		failures.append("reactivated cockpit must obtain fresh measurements and settle")
	cockpit.queue_free()
	await tree.process_frame
	return failures
