extends RefCounted

const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const LivePieceControlStripScript = preload("res://scripts/ui/live_piece_control_strip.gd")
const LiveViewControlStripScript = preload("res://scripts/ui/live_view_control_strip.gd")


class InjectedAuthority:
	extends RefCounted
	var piece_groups: Array = []
	var view_groups: Array = []

	func piece_control_groups(_mode: String, _basis: Dictionary = {}, _frame: Dictionary = {}) -> Array:
		return piece_groups.duplicate(true)

	func view_control_groups(_mode: String, _basis: Dictionary = {}, _frame: Dictionary = {}) -> Array:
		return view_groups.duplicate(true)


func run() -> Array:
	var failures: Array = []
	failures.append_array(_check_semantic_rows_and_density())
	failures.append_array(_check_binding_authority_injection())
	failures.append_array(await _check_production_deck())
	return failures


func _check_semantic_rows_and_density() -> Array:
	var failures: Array = []
	var piece_ids: Array = []
	var view_ids: Array = []
	for density in ["detailed", "standard", "compact"]:
		var piece = LivePieceControlStripScript.new()
		piece.configure("live_4d", {}, {}, density)
		var piece_snapshot: Dictionary = piece.deterministic_snapshot()
		var next_piece_ids: Array = piece_snapshot.get("row_ids", [])
		if piece_ids.is_empty():
			piece_ids = next_piece_ids
		elif next_piece_ids != piece_ids:
			failures.append("PIECE density %s must preserve identical semantic row ids" % density)
		for required in ["translate:X", "translate:Z", "translate:W", "drop:Soft", "drop:Hard", "rotate:XY", "rotate:XW", "rotate:ZW"]:
			if required not in next_piece_ids:
				failures.append("PIECE must include semantic row %s at %s density" % [required, density])
		if not piece.find_children("*", "BaseButton", true, false).is_empty():
			failures.append("PIECE keycaps must remain passive labels at %s density" % density)
		var view = LiveViewControlStripScript.new()
		view.configure({}, {}, density)
		var view_snapshot: Dictionary = view.deterministic_snapshot()
		var next_view_ids: Array = view_snapshot.get("row_ids", [])
		if view_ids.is_empty():
			view_ids = next_view_ids
		elif next_view_ids != view_ids:
			failures.append("VIEW density %s must preserve identical semantic row ids" % density)
		for required in ["view_exact:XZ", "view_exact:XW", "view_exact:ZW", "view_orient:Pitch", "view_orient:Yaw", "view_framing:Zoom", "view_framing:Fit", "view_framing:Reset", "view_pointer:Orient", "view_pointer:Translate"]:
			if required not in next_view_ids:
				failures.append("VIEW must include semantic row %s at %s density" % [required, density])
		if not view.find_children("*", "BaseButton", true, false).is_empty():
			failures.append("VIEW keycaps must remain passive labels at %s density" % density)
		piece.free()
		view.free()
	return failures


func _check_binding_authority_injection() -> Array:
	var failures: Array = []
	var fixture := InjectedAuthority.new()
	fixture.piece_groups = LiveInputContractScript.piece_control_groups("live_4d")
	fixture.view_groups = LiveInputContractScript.view_control_groups("live_4d")
	fixture.piece_groups[0]["items"][0][0] = "Injected Move"
	fixture.view_groups[0]["items"][0][0] = "Injected View"
	var piece = LivePieceControlStripScript.new()
	piece.configure("live_4d", {}, {}, "standard", fixture)
	var view = LiveViewControlStripScript.new()
	view.configure({}, {}, "standard", "live_4d", fixture)
	var piece_rows: Array = piece.deterministic_snapshot().get("rows", [])
	var view_rows: Array = view.deterministic_snapshot().get("rows", [])
	if piece_rows.is_empty() or piece_rows[0].get("binding") != "Injected Move":
		failures.append("PIECE rendered binding must change with the injected authority fixture")
	if view_rows.is_empty() or view_rows[0].get("binding") != "Injected View":
		failures.append("VIEW rendered binding must change with the injected authority fixture")
	if piece.deterministic_snapshot().get("source") != "injected_fixture" or view.deterministic_snapshot().get("source") != "injected_fixture":
		failures.append("semantic strips must disclose injected test authority")
	for strip in [piece, view]:
		if not strip.find_children("*", "BaseButton", true, false).is_empty():
			failures.append("an injected binding must not turn passive keycaps into gameplay buttons")
	piece.free()
	view.free()
	return failures


func _check_production_deck() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["semantic helper production check requires the trace replay scene"]
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
	var state_hash := str(app._live_bridge.live_4d_state_hash())
	var piece_row_ids: Array = []
	var view_row_ids: Array = []
	for density in ["detailed", "standard", "compact"]:
		hud._apply_hud_density(density)
		await tree.process_frame
		await tree.process_frame
		var snapshot: Dictionary = hud.layout_contract_snapshot()
		var deck: Rect2 = snapshot.get("live_4d_deck", Rect2())
		var board: Rect2 = snapshot.get("game_area", Rect2())
		var piece: Rect2 = snapshot.get("piece_module_rect", Rect2())
		var view: Rect2 = snapshot.get("view_module_rect", Rect2())
		var state: Rect2 = snapshot.get("piece_state_module_rect", Rect2())
		if not snapshot.get("live_4d_deck_visible", false) or not _contains(deck, piece) or not _contains(deck, view) or not _contains(deck, state):
			failures.append("%s density must contain PIECE, VIEW, and PIECE STATE in the Live-4D deck" % density)
		if board.intersects(deck) or piece.intersects(view) or view.intersects(state):
			failures.append("%s density semantic modules must not overlap board or neighbouring deck modules" % density)
		var next_piece_ids: Array = snapshot.get("piece_control_strip", {}).get("row_ids", [])
		var next_view_ids: Array = snapshot.get("view_control_strip", {}).get("row_ids", [])
		if piece_row_ids.is_empty():
			piece_row_ids = next_piece_ids
			view_row_ids = next_view_ids
		elif piece_row_ids != next_piece_ids or view_row_ids != next_view_ids:
			failures.append("%s density must preserve the production semantic row inventory" % density)
	if str(app._live_bridge.live_4d_state_hash()) != state_hash:
		failures.append("semantic guidance construction and density changes must not mutate Live-4D state")
	if not hud._piece_control_strip.find_children("*", "BaseButton", true, false).is_empty() or not hud._live_view_control_strip.find_children("*", "BaseButton", true, false).is_empty():
		failures.append("production PIECE and VIEW keycaps must remain passive")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	return failures


func _contains(outer: Rect2, inner: Rect2) -> bool:
	return inner.size.x > 0.0 and inner.size.y > 0.0 and outer.encloses(inner)
