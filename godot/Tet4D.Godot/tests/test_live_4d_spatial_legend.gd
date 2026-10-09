extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")
const LegendDirectionProbeScript = preload("res://tests/support/legend_direction_probe.gd")


# Live 4D legend: movement drawn where each key moves the piece, rotations and
# view turns drawn as the on-screen directions they mix. The old deck labelled
# moves with axis names that changed after a view turn (A/D: X -> Z) while the
# keys' on-screen effect did not; this test pins the opposite.
func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Live-4D legend acceptance requires the trace replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	app._enter_live_4d_mode()
	hud._set_onboarding_visible(false)
	for i in range(4):
		await tree.process_frame

	var layout: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = layout.get("live_cockpit", {})
	if cockpit.get("deck_placement") != LiveCockpitScript.PLACEMENT_SPLIT:
		failures.append("Live 4D must keep the legend in the deck and NEXT/HOLD + VIEW in a side column, got %s" % cockpit.get("deck_placement"))
	if cockpit.get("deck_row_assignment") != [["PieceControls"]] or bool(cockpit.get("deck_scroll_required", true)):
		failures.append("Live 4D legend must fill one unscrolled deck row, got %s scroll=%s" % [cockpit.get("deck_row_assignment"), cockpit.get("deck_scroll_required")])
	var side: Rect2 = cockpit.get("side_column_rect", Rect2())
	var preview: Rect2 = layout.get("piece_preview_row_rect", Rect2())
	if not side.encloses(preview) or hud._live_cockpit.piece_state.get_parent() != hud._live_cockpit.side_column:
		failures.append("Live 4D NEXT/HOLD must be visible at the top of the side column: %s in %s" % [preview, side])
	if hud._live_cockpit.view_controls.get_parent() != hud._live_cockpit.side_column:
		failures.append("Live 4D VIEW must sit in the side column")

	var piece: Dictionary = hud._piece_control_strip.deterministic_snapshot()
	if piece.get("layout") != "wide" or not bool(piece.get("spatial", false)):
		failures.append("Live 4D must use the wide spatial legend, got %s" % piece.get("layout"))
	var row_ids_before: Array = piece.get("row_ids", [])
	for required in ["translate:Sideways", "translate:Near/far", "translate:Slice", "drop:Soft drop", "drop:Hard drop", "rotate:Spin", "rotate:Turn", "rotate:Tip", "rotate:Side↔W", "rotate:Up↔W", "rotate:Depth↔W", "hold:Hold", "session:Pause", "session:Restart"]:
		if required not in row_ids_before:
			failures.append("Live 4D legend must include %s, got %s" % [required, row_ids_before])
	if piece.get("plane_glyphs", []) != [["x", "y"], ["x", "z"], ["y", "z"], ["x", "w"], ["y", "w"], ["z", "w"]]:
		failures.append("Live 4D rotation rows must carry one plane glyph per plane, got %s" % str(piece.get("plane_glyphs", [])))
	var compass: Dictionary = piece.get("compass_keys", {})
	for pair in [["move_x_neg", "live_4d_move_x_neg"], ["move_x_pos", "live_4d_move_x_pos"], ["move_z_neg", "live_4d_move_z_neg"], ["move_z_pos", "live_4d_move_z_pos"]]:
		if compass.get(pair[0]) != LiveInputContractScript.display_key(pair[1]):
			failures.append("Live 4D compass must key %s from the input contract, got %s" % [pair[0], compass.get(pair[0])])
	var view: Dictionary = hud._live_view_control_strip.deterministic_snapshot()
	if view.get("layout") != "wide" or view.get("plane_glyphs", []) != [["x", "z"], ["x", "w"], ["z", "w"]]:
		failures.append("Live 4D view turns must use the same plane glyphs as rotations, got %s %s" % [view.get("layout"), str(view.get("plane_glyphs", []))])
	if view.get("row_ids", []).any(func(row_id): return str(row_id).begins_with("view_pointer") or str(row_id).begins_with("view_framing")):
		failures.append("Live 4D side column must keep only view turns and look, got %s" % str(view.get("row_ids", [])))

	failures.append_array(await LegendDirectionProbeScript.check_compass_matches_moves(app, hud, tree, 4, "Live-4D"))
	# After a view turn the keys keep their on-screen effect; the legend must
	# keep its words and its arrows must still tell the truth.
	app._apply_live_4d_basis_turn("xz", 1)
	for i in range(6):
		await tree.process_frame
	if hud._piece_control_strip.deterministic_snapshot().get("row_ids", []) != row_ids_before:
		failures.append("Live 4D legend wording must not change after a view turn, got %s" % str(hud._piece_control_strip.deterministic_snapshot().get("row_ids", [])))
	failures.append_array(await LegendDirectionProbeScript.check_compass_matches_moves(app, hud, tree, 4, "Live-4D after view turn"))
	# The row of the plane just used lights up.
	if not hud._piece_control_strip.flash_plane("XW") or not hud._live_view_control_strip.flash_plane("ZW"):
		failures.append("Live 4D must be able to flash the legend row of the plane just used")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
