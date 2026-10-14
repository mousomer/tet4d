extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")

# The Python client drew 10x20 at 30px in a 760px window: 79% of its height.
# Before the side rail Godot reached 36% at that size; 60% is the floor for the
# 1600x960 design size, where the rail layout measures about 70%.
const MIN_BOARD_HEIGHT_SHARE := 0.60


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["Live-2D cockpit acceptance requires the trace replay scene"]
	var original_size := tree.root.size
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	app._enter_live_2d_mode()
	# Compare board allocation with guidance hidden; guide layout has separate acceptance.
	hud._set_onboarding_visible(false)
	await tree.process_frame
	await tree.process_frame
	var hash_before := str(app._live_bridge.live_2d_state_hash())
	var layout: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = layout.get("live_cockpit", {})
	var game_area: Rect2 = layout.get("game_area", Rect2())
	var deck: Rect2 = layout.get("live_4d_deck", Rect2())
	if not cockpit.get("deck_visible", false) or layout.get("right_inspector", Rect2()).size.y > 0.0:
		failures.append("Live 2D must use the shared cockpit deck without the legacy right inspector")
	# A tall board needs height, so its controls go beside it, not under it.
	if cockpit.get("deck_placement") != LiveCockpitScript.PLACEMENT_SIDE:
		failures.append("Live 2D must place the control deck beside the board, got %s" % cockpit.get("deck_placement"))
	if game_area.intersects(deck) or deck.position.x < game_area.end.x:
		failures.append("Live-2D control rail must sit to the right of the board: board %s rail %s" % [game_area, deck])
	if cockpit.get("deck_row_assignment") != [["PieceState"], ["PieceControls"]]:
		failures.append("Live-2D rail must stack NEXT/HOLD above the key legend, got %s" % str(cockpit.get("deck_row_assignment")))
	# Measure the board itself, not its container: the old container check passed
	# while the board filled a third of the window height.
	var game_viewport: Rect2 = layout.get("game_viewport", Rect2())
	var camera: Camera3D = app._camera_rig._camera
	var board_height := game_viewport.size.y * 20.0 / maxf(camera.size, 0.001)
	if board_height / float(tree.root.size.y) < MIN_BOARD_HEIGHT_SHARE:
		failures.append("Live-2D board must fill at least %d%% of the window height, got %.0fpx of %d" % [int(MIN_BOARD_HEIGHT_SHARE * 100.0), board_height, tree.root.size.y])
	var piece: Dictionary = layout.get("piece_control_strip", {})
	if piece.get("layout") != "rail":
		failures.append("Live-2D controls must use the key-first rail legend")
	var piece_ids: Array = piece.get("row_ids", [])
	# Hold, pause and restart are what a player hunts for mid-game; the deck
	# variant left them to buttons that never showed their keys.
	var expected_ids := ["translate:Move", "drop:Soft drop", "drop:Hard drop", "rotate:Right (CW)", "rotate:Left (CCW)", "hold:Hold", "session:Pause", "session:Restart"]
	if piece_ids != expected_ids:
		failures.append("Live-2D legend must list %s, got %s" % [expected_ids, piece_ids])
	var bindings := {}
	for item in piece.get("compact_items", []):
		bindings[str(item.get("source_label"))] = str(item.get("binding"))
	if bindings.get("Restart Game") != "R" or bindings.get("Pause") != "P" or bindings.get("Hold") != "C":
		failures.append("Live-2D legend must show the R / P / C keys from the input contract, got %s" % bindings)
	# Flat 2D framing rarely changes and Fit View stays a header button.
	if hud._live_cockpit.view_controls.visible:
		failures.append("Live-2D rail must omit the VIEW framing module")
	if hud._piece_preview_row.get_parent() != hud._live_cockpit.piece_state:
		failures.append("Live-2D Piece State must reuse the shared NEXT/HOLD consumers")
	var orientation: Dictionary = app._camera_rig.orientation_indicator_snapshot()
	if orientation.get("axes", {}).get("depth", {}).get("available", true):
		failures.append("Live-2D presentation must represent unavailable depth without a zero-vector rosette arrow")
	for action_id in ["live_move_left", "live_move_right", "live_rotate_cw", "live_rotate_ccw", "live_soft_drop", "live_hard_drop"]:
		if not LiveInputContractScript.action_specs().has(action_id):
			failures.append("Live-2D migration must retain input authority action %s" % action_id)
	hud._apply_hud_density("compact")
	await tree.process_frame
	if str(app._live_bridge.live_2d_state_hash()) != hash_before:
		failures.append("Live-2D cockpit migration must not mutate deterministic gameplay state")
	# Regression: the board anchor toward the rail was once baked from the
	# previous mode's viewport aspect, which threw the whole 2D board off-screen
	# after a 4D -> 2D switch. Every board corner must project into the viewport.
	app._enter_live_4d_mode()
	for i in range(6):
		await tree.process_frame
	app._enter_live_2d_mode()
	hud._set_onboarding_visible(false)
	for i in range(6):
		await tree.process_frame
	var board_bounds: Dictionary = app._renderer.current_bounds()
	var viewport_size := Vector2(hud.game_viewport().size)
	for corner in [Vector3(board_bounds["min"].x, board_bounds["min"].y, 0.0), Vector3(board_bounds["max"].x, board_bounds["max"].y, 0.0)]:
		var projected: Vector2 = camera.unproject_position(corner)
		if projected.x < 0.0 or projected.y < 0.0 or projected.x > viewport_size.x or projected.y > viewport_size.y:
			failures.append("Live-2D board must stay on screen after a 4D -> 2D switch: corner %s projects to %s in %s" % [corner, projected, viewport_size])
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
