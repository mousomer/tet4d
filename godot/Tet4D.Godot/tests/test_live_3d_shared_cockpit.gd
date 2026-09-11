extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")


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
	app._enter_live_3d_mode()
	await tree.process_frame
	await tree.process_frame
	var hash_before := str(app._live_bridge.live_3d_state_hash())
	var layout: Dictionary = hud.layout_contract_snapshot()
	var board: Rect2 = layout.get("game_area", Rect2())
	var old_board_area := 910.0 * 836.0
	if not layout.get("live_cockpit", {}).get("deck_visible", false) or layout.get("right_inspector", Rect2()).size.y > 0.0:
		failures.append("Live 3D must use the shared cockpit deck without the legacy right inspector")
	if board.size.x < 1575.0 or board.size.x * board.size.y <= old_board_area:
		failures.append("Live-3D primary board area must not regress from the legacy 910x836 allocation, got %s" % board)
	var piece: Dictionary = layout.get("piece_control_strip", {})
	var piece_ids: Array = piece.get("row_ids", [])
	for required in ["translate:X", "translate:-Z", "drop:Soft", "drop:Hard", "rotate:XY", "rotate:XZ", "rotate:YZ"]:
		if required not in piece_ids:
			failures.append("Live-3D PIECE must include %s" % required)
	for forbidden in ["translate:W", "rotate:XW", "rotate:YW", "rotate:ZW"]:
		if forbidden in piece_ids:
			failures.append("Live-3D PIECE must omit 4D row %s" % forbidden)
	var view: Dictionary = layout.get("view_control_strip", {})
	var expected_view := ["view_framing:Fit", "view_framing:Reset", "view_pointer:Orient", "view_pointer:Translate", "view_pointer:Zoom"]
	if view.get("row_ids", []) != expected_view:
		failures.append("Live-3D VIEW must expose only legitimate framing/pointer rows, got %s" % view.get("row_ids", []))
	var orientation_gizmo := app._camera_rig.get_node_or_null("OrientationGizmo") as Node3D
	if orientation_gizmo == null or not orientation_gizmo.visible:
		failures.append("Live-3D migration must retain the state-driven orientation marker")
	if hud._piece_preview_row.get_parent() != hud._live_cockpit.piece_state:
		failures.append("Live-3D Piece State must reuse the shared NEXT/HOLD consumers")
	for action_id in ["live_3d_move_x_neg", "live_3d_move_x_pos", "live_3d_rotate_xy_neg", "live_3d_rotate_yz_pos", "live_3d_soft_drop", "live_3d_hard_drop"]:
		if not LiveInputContractScript.action_specs().has(action_id):
			failures.append("Live-3D migration must retain input authority action %s" % action_id)
	hud._apply_hud_density("compact")
	await tree.process_frame
	if str(app._live_bridge.live_3d_state_hash()) != hash_before:
		failures.append("Live-3D cockpit migration must not mutate deterministic gameplay state")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures
