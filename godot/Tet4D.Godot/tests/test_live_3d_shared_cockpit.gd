extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")
const LegendDirectionProbeScript = preload("res://tests/support/legend_direction_probe.gd")

# The Python client drew a 6x10x6 well at about 67 px per cell in a 1440x900
# window; Godot drew 29 px with the deck under the board. The rail layout
# measures about 46 px; 55% of the window height is the floor.
const MIN_BOARD_HEIGHT_SHARE := 0.55


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Live-3D cockpit acceptance requires the trace replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	# Compare board allocation with guidance hidden; guide layout has separate
	# acceptance. Hide it before entry: a resize inside the post-entry layout
	# guard deliberately does not refit.
	hud._set_onboarding_visible(false)
	await tree.process_frame
	app._enter_live_3d_mode()
	for i in range(4):
		await tree.process_frame
	var hash_before := str(app._live_bridge.live_3d_state_hash())
	var layout: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = layout.get("live_cockpit", {})
	var game_area: Rect2 = layout.get("game_area", Rect2())
	var deck: Rect2 = layout.get("live_4d_deck", Rect2())
	if not cockpit.get("deck_visible", false) or layout.get("right_inspector", Rect2()).size.y > 0.0:
		failures.append("Live 3D must use the shared cockpit deck without the legacy right inspector")
	# The well is taller than wide, so its controls go beside it, as in 2D.
	if cockpit.get("deck_placement") != LiveCockpitScript.PLACEMENT_SIDE or deck.position.x < game_area.end.x:
		failures.append("Live 3D must place the control rail to the right of the board: board %s rail %s placement %s" % [game_area, deck, cockpit.get("deck_placement")])
	if hud._live_cockpit.view_controls.visible:
		failures.append("Live-3D rail must omit the VIEW module; mouse orbit and the Fit View button cover it")
	# Measure the board itself, not its container.
	var board_height := LegendDirectionProbeScript.projected_content_height(app)
	if board_height / float(tree.root.size.y) < MIN_BOARD_HEIGHT_SHARE:
		failures.append("Live-3D board must fill at least %d%% of the window height, got %.0fpx of %d" % [int(MIN_BOARD_HEIGHT_SHARE * 100.0), board_height, tree.root.size.y])

	var piece: Dictionary = layout.get("piece_control_strip", {})
	if piece.get("layout") != "rail" or not bool(piece.get("spatial", false)):
		failures.append("Live-3D controls must use the spatial key-first rail legend, got layout %s" % piece.get("layout"))
	var piece_ids: Array = piece.get("row_ids", [])
	for required in ["translate:Sideways", "translate:Near/far", "drop:Soft drop", "drop:Hard drop", "rotate:Spin", "rotate:Turn", "rotate:Tip", "hold:Hold", "session:Pause", "session:Restart"]:
		if required not in piece_ids:
			failures.append("Live-3D legend must include %s, got %s" % [required, piece_ids])
	for forbidden in ["translate:Slice", "rotate:Side↔W", "rotate:Up↔W", "rotate:Depth↔W"]:
		if forbidden in piece_ids:
			failures.append("Live-3D legend must omit 4D row %s" % forbidden)
	# Rotation rows carry a glyph lighting the two on-screen directions they mix.
	if piece.get("plane_glyphs", []) != [["x", "y"], ["x", "z"], ["y", "z"]]:
		failures.append("Live-3D rotation rows must carry Spin/Turn/Tip plane glyphs, got %s" % str(piece.get("plane_glyphs", [])))
	var expected_compass := {
		"move_x_neg": LiveInputContractScript.display_key("live_3d_move_x_neg"),
		"move_x_pos": LiveInputContractScript.display_key("live_3d_move_x_pos"),
		"move_z_neg": LiveInputContractScript.display_key("live_3d_move_z_neg"),
		"move_z_pos": LiveInputContractScript.display_key("live_3d_move_z_pos"),
	}
	if piece.get("compass_keys", {}) != expected_compass:
		failures.append("Live-3D compass must key each arrow from the input contract, got %s" % str(piece.get("compass_keys", {})))
	# The compass must point where each key actually moves the piece on screen.
	failures.append_array(await LegendDirectionProbeScript.check_compass_matches_moves(app, hud, tree, 3, "Live-3D"))

	if hud._piece_preview_row.get_parent() != hud._live_cockpit.piece_state:
		failures.append("Live-3D Piece State must reuse the shared NEXT/HOLD consumers")
	var orientation_gizmo := app._camera_rig.get_node_or_null("OrientationGizmo") as Node3D
	if orientation_gizmo == null or not orientation_gizmo.visible:
		failures.append("Live-3D migration must retain the state-driven orientation marker")
	for action_id in ["live_3d_move_x_neg", "live_3d_move_x_pos", "live_3d_rotate_xy_neg", "live_3d_rotate_yz_pos", "live_3d_soft_drop", "live_3d_hard_drop"]:
		if not LiveInputContractScript.action_specs().has(action_id):
			failures.append("Live-3D migration must retain input authority action %s" % action_id)
	hud._apply_hud_density("compact")
	await tree.process_frame
	app._reset_live_3d()
	await tree.process_frame
	hash_before = str(app._live_bridge.live_3d_state_hash())
	hud._apply_hud_density("standard")
	await tree.process_frame
	if str(app._live_bridge.live_3d_state_hash()) != hash_before:
		failures.append("Live-3D cockpit density changes must not mutate deterministic gameplay state")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
