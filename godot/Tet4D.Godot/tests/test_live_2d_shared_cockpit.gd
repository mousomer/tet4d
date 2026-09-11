extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")


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
	await tree.process_frame
	await tree.process_frame
	var hash_before := str(app._live_bridge.live_2d_state_hash())
	var layout: Dictionary = hud.layout_contract_snapshot()
	var board: Rect2 = layout.get("game_area", Rect2())
	if not layout.get("live_cockpit", {}).get("deck_visible", false) or layout.get("right_inspector", Rect2()).size.y > 0.0:
		failures.append("Live 2D must use the shared cockpit deck without the legacy right inspector")
	if board.size.x < 1575.0 or board.size.x * board.size.y <= 887.0 * 836.0:
		failures.append("Live-2D primary board area must not regress from the legacy 887x836 allocation, got %s" % board)
	var piece_ids: Array = layout.get("piece_control_strip", {}).get("row_ids", [])
	for required in ["translate:X", "drop:Soft", "drop:Hard", "rotate:clockwise", "rotate:counter-clockwise"]:
		if required not in piece_ids:
			failures.append("Live-2D PIECE must include %s" % required)
	for forbidden in ["translate:Z", "translate:W", "rotate:XY", "rotate:XZ", "rotate:XW"]:
		if forbidden in piece_ids:
			failures.append("Live-2D PIECE must omit higher-dimensional row %s" % forbidden)
	var view_ids: Array = layout.get("view_control_strip", {}).get("row_ids", [])
	if view_ids != ["view_framing:Fit", "view_framing:Reset"]:
		failures.append("Live-2D VIEW must remain minimal Fit/Reset guidance, got %s" % view_ids)
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
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
