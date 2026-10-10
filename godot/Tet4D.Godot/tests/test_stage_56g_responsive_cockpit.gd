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
const LiveCockpitScript = preload("res://scripts/ui/live_cockpit.gd")

# Absolute collapse guard only. This is not a legibility criterion: a 120x120
# gameplay surface inside a desktop window is plainly unplayable, which is why
# the proportional occupancy bars below carry the real acceptance.
const COLLAPSE_GUARD_PX := float(ReplayVisuals.GAME_AREA_MIN_WIDTH)
const MIN_GAME_WIDTH_SHARE := 0.60
const MIN_GAME_HEIGHT_SHARE := 0.30

const VIEWPORT_CASES := [
	{"name": "wide desktop", "size": Vector2i(1920, 1080), "next_hold_without_scroll": true},
	{"name": "standard desktop", "size": Vector2i(1440, 900), "next_hold_without_scroll": true},
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
	# Placement follows the board's shape: 2D and 3D wells take a side rail;
	# Live 4D keeps its legend in the deck and moves NEXT/HOLD + VIEW to a side
	# column, falling back to the reflowing deck in narrow and small shells.
	var placement := str(cockpit.get("deck_placement", ""))
	var profile := str(cockpit.get("responsive_profile", ""))
	var expected_placement := LiveCockpitScript.PLACEMENT_SIDE
	if mode == "4D":
		expected_placement = LiveCockpitScript.PLACEMENT_SPLIT if profile in [LiveCockpitScript.PROFILE_WIDE, LiveCockpitScript.PROFILE_STANDARD] else LiveCockpitScript.PLACEMENT_BELOW
	if placement != expected_placement:
		failures.append("%s at profile %s must use placement %s, got %s" % [label, profile, expected_placement, placement])
	var side_rail := placement == LiveCockpitScript.PLACEMENT_SIDE
	var split := placement == LiveCockpitScript.PLACEMENT_SPLIT
	var side_column: Rect2 = cockpit.get("side_column_rect", Rect2())
	if cockpit.get("deck_modules") != ["PieceControls", "ViewControls", "PieceState"]:
		failures.append("%s must retain the shared PIECE / VIEW / PIECE STATE identity" % label)
	var flattened: Array = []
	for row in cockpit.get("deck_row_assignment", []):
		for module_name in row:
			flattened.append(str(module_name))
	var expected_order := ["PieceControls", "ViewControls", "PieceState"]
	if side_rail:
		expected_order = ["PieceState", "PieceControls"]
	elif split:
		expected_order = ["PieceControls"]
	if flattened != expected_order:
		failures.append("%s must preserve semantic module order %s, got %s" % [label, str(expected_order), str(flattened)])
	# Rail modes omit VIEW (index 1). In the split, NEXT/HOLD and VIEW live in a
	# scrolling side column: NEXT/HOLD must be fully visible at its top, VIEW
	# reachable below it.
	for index in range(modules.size()):
		if side_rail and index == 1:
			continue
		if split and index > 0:
			continue
		if not _contains_rect(rows_rect, modules[index]):
			failures.append("%s must keep semantic module %d inside the scroll-reachable row host: %s in %s" % [label, index, modules[index], rows_rect])
	if split:
		if not _contains_rect(usable, side_column) or side_column.position.x < board.end.x:
			failures.append("%s must keep the side column inside the window, right of the board: %s board %s" % [label, side_column, board])
		if not _contains_rect(side_column, modules[2]):
			failures.append("%s must show PIECE STATE fully at the top of the side column: %s in %s" % [label, modules[2], side_column])
		if modules[1].position.y < modules[2].end.y - 0.5 or modules[1].position.x < side_column.position.x - 0.5:
			failures.append("%s must stack VIEW below PIECE STATE in the side column: %s" % [label, modules[1]])
	if not bool(cockpit.get("deck_visible", false)):
		failures.append("%s must keep the shared control deck reachable" % label)
	if board.intersects(deck):
		failures.append("%s must keep the game surface and control deck separate" % label)

	if game_viewport.size.x < COLLAPSE_GUARD_PX or game_viewport.size.y < COLLAPSE_GUARD_PX:
		failures.append("%s collapsed the gameplay surface entirely, got %s" % [label, game_viewport])
	var width_share := game_viewport.size.x / maxf(viewport_size.x, 1.0)
	var height_share := game_viewport.size.y / maxf(viewport_size.y, 1.0)
	# A rail or side column spends width the board's fit does not use, so width
	# share is not the measure there; it must simply sit right of the board.
	if side_rail and deck.position.x < board.end.x:
		failures.append("%s must place the rail to the right of the board: board %s rail %s" % [label, board, deck])
	if not side_rail and not split and width_share < MIN_GAME_WIDTH_SHARE:
		failures.append("%s must leave the gameplay surface at least %d%% of the viewport width, got %d%%" % [label, int(MIN_GAME_WIDTH_SHARE * 100.0), int(width_share * 100.0)])
	if height_share < MIN_GAME_HEIGHT_SHARE:
		failures.append("%s must leave the gameplay surface at least %d%% of the viewport height, got %d%%" % [label, int(MIN_GAME_HEIGHT_SHARE * 100.0), int(height_share * 100.0)])

	for first in range(modules.size()):
		for second in range(first + 1, modules.size()):
			# Omitted VIEW, and side-column content clipped by its scroll, are not
			# visible geometry that could overlap anything.
			if (side_rail or split) and (first == 1 or second == 1):
				continue
			if modules[first].intersects(modules[second]):
				failures.append("%s must not overlap semantic modules %d/%d" % [label, first, second])
	var preview_row: Rect2 = snapshot.get("piece_preview_row_rect", Rect2())
	if not bool(snapshot.get("piece_preview_row_visible", false)) or not _contains_rect(modules[2], preview_row):
		failures.append("%s must keep HOLD and NEXT grouped inside PIECE STATE" % label)
	# Stage 56H-R3.1: scrolling is the constrained-size escape hatch only. At the
	# standard window NEXT and HOLD must be on screen without scrolling.
	if bool(viewport_case.get("next_hold_without_scroll", false)):
		if bool(cockpit.get("deck_scroll_required", false)) or (not side_rail and int(cockpit.get("deck_row_count", 0)) != 1):
			failures.append("%s must fit its deck on one unscrolled row, got rows %s" % [label, str(cockpit.get("deck_row_assignment", []))])
		var visible_host := side_column if split else deck
		if not _contains_rect(visible_host, preview_row) or not _contains_rect(usable, preview_row):
			failures.append("%s must show NEXT and HOLD without scrolling: %s in %s" % [label, preview_row, visible_host])
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
