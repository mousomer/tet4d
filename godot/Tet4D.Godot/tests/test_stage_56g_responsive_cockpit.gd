extends RefCounted

# Structural responsive acceptance.
#
# SCOPE LIMIT, stated so it is not mistaken for production equivalence: a
# SubViewport has no content scale, so the scene root here genuinely takes the
# case size. The shipped shell does not behave this way - canvas_items stretch
# pins the logical viewport to the design resolution and a small window
# downscales rather than reflowing. This file therefore proves the cockpit's
# structure and packing given a width; it cannot prove which profile the
# shipped window selects. That claim requires a windowed DisplayServer run,
# because the headless server reports window_get_size() == (0, 0) and ignores
# resize requests.

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

# Absolute collapse guard only. This is not a legibility criterion: a 120x120
# gameplay surface inside a desktop window is plainly unplayable, which is why
# the proportional occupancy bars below carry the real acceptance.
const COLLAPSE_GUARD_PX := float(ReplayVisuals.GAME_AREA_MIN_WIDTH)
const MIN_GAME_WIDTH_SHARE := 0.60
const MIN_GAME_HEIGHT_SHARE := 0.30

const VIEWPORT_CASES := [
	{"name": "wide desktop", "size": Vector2i(1920, 1080)},
	{"name": "standard desktop", "size": Vector2i(1440, 900)},
	{"name": "narrow window", "size": Vector2i(960, 640)},
	{"name": "small viewport", "size": Vector2i(800, 700)},
]


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	var tree := Engine.get_main_loop() as SceneTree
	if scene == null or tree == null:
		return ["Stage 56G responsive acceptance requires the production scene and SceneTree"]
	for viewport_case in VIEWPORT_CASES:
		failures.append_array(await _check_viewport_case(tree, scene, viewport_case))
	return failures


func _check_viewport_case(tree: SceneTree, scene: PackedScene, viewport_case: Dictionary) -> Array:
	var failures: Array = []
	var requested_size: Vector2i = viewport_case["size"]
	var viewport := SubViewport.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.size = requested_size
	tree.root.add_child(viewport)
	var root := scene.instantiate() as Control
	viewport.add_child(root)
	var hud = root.get_node("ReplayHud")
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node("App")
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	hud._set_onboarding_visible(false)
	hud._apply_responsive_layout()
	for mode in ["2D", "3D", "4D"]:
		match mode:
			"2D": app._enter_live_2d_mode()
			"3D": app._enter_live_3d_mode()
			"4D": app._enter_live_4d_mode()
		await tree.process_frame
		await tree.process_frame
		failures.append_array(_assert_live_geometry(hud, viewport_case, mode, Vector2(requested_size)))
	viewport.queue_free()
	await tree.process_frame
	return failures


func _assert_live_geometry(hud: Node, viewport_case: Dictionary, mode: String, viewport_size: Vector2) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = snapshot.get("live_cockpit", {})
	var label := "%s Live %s" % [viewport_case["name"], mode]
	var usable := Rect2(Vector2.ZERO, viewport_size)
	var deck: Rect2 = snapshot.get("live_4d_deck", Rect2())
	var board: Rect2 = snapshot.get("game_area", Rect2())
	var game_viewport: Rect2 = snapshot.get("game_viewport", Rect2())
	var rows_rect: Rect2 = cockpit.get("deck_rows_rect", deck)
	var modules: Array[Rect2] = [
		snapshot.get("piece_module_rect", Rect2()),
		snapshot.get("view_module_rect", Rect2()),
		snapshot.get("piece_state_module_rect", Rect2()),
	]

	# The defect this file replaces: the previous gate checked only that modules
	# sat inside the deck, so a deck hanging 837px outside the viewport passed.
	if not _contains_rect(usable, deck):
		failures.append("%s must keep the whole control deck inside the usable viewport: deck %s in %s" % [label, deck, usable])
	if not _contains_rect(usable, game_viewport):
		failures.append("%s must keep the gameplay surface inside the usable viewport: %s in %s" % [label, game_viewport, usable])
	for index in range(modules.size()):
		if not _contains_rect(rows_rect, modules[index]):
			failures.append("%s must keep semantic module %d inside the scroll-reachable row host: %s in %s" % [label, index, modules[index], rows_rect])

	if cockpit.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("%s must retain the shared PIECE / VIEW / PIECE STATE identity" % label)
	var flattened: Array = []
	for row in cockpit.get("deck_row_assignment", []):
		for module_name in row:
			flattened.append(str(module_name))
	if flattened != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("%s must preserve semantic module order across reflow rows, got %s" % [label, str(flattened)])
	if not bool(cockpit.get("deck_visible", false)):
		failures.append("%s must keep the shared control deck reachable" % label)
	if board.intersects(deck):
		failures.append("%s must keep the game surface and control deck separate" % label)

	if game_viewport.size.x < COLLAPSE_GUARD_PX or game_viewport.size.y < COLLAPSE_GUARD_PX:
		failures.append("%s collapsed the gameplay surface entirely, got %s" % [label, game_viewport])
	var width_share := game_viewport.size.x / maxf(viewport_size.x, 1.0)
	var height_share := game_viewport.size.y / maxf(viewport_size.y, 1.0)
	if width_share < MIN_GAME_WIDTH_SHARE:
		failures.append("%s must leave the gameplay surface at least %d%% of the viewport width, got %d%%" % [label, int(MIN_GAME_WIDTH_SHARE * 100.0), int(width_share * 100.0)])
	if height_share < MIN_GAME_HEIGHT_SHARE:
		failures.append("%s must leave the gameplay surface at least %d%% of the viewport height, got %d%%" % [label, int(MIN_GAME_HEIGHT_SHARE * 100.0), int(height_share * 100.0)])

	for first in range(modules.size()):
		for second in range(first + 1, modules.size()):
			if modules[first].intersects(modules[second]):
				failures.append("%s must not overlap semantic modules %d/%d" % [label, first, second])
	var preview_row: Rect2 = snapshot.get("piece_preview_row_rect", Rect2())
	if not bool(snapshot.get("piece_preview_row_visible", false)) or not _contains_rect(modules[2], preview_row):
		failures.append("%s must keep HOLD and NEXT grouped inside PIECE STATE" % label)
	return failures


func _contains_rect(outer: Rect2, inner: Rect2) -> bool:
	return (
		inner.size.x > 0.0
		and inner.size.y > 0.0
		and inner.position.x >= outer.position.x - 0.5
		and inner.position.y >= outer.position.y - 0.5
		and inner.end.x <= outer.end.x + 0.5
		and inner.end.y <= outer.end.y + 0.5
	)
