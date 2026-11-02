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
const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")

# Resize-history cases: short and narrow+short force the deck to give up
# height; narrow selects the reflowing deck below the board.
# The supported opening window: the whole 4D legend must fit here unscrolled.
const HISTORY_REFERENCE := Vector2i(1280, 720)
const HISTORY_LARGE := Vector2i(1600, 960)
const HISTORY_SHORT := Vector2i(1600, 640)
const HISTORY_NARROW := Vector2i(1100, 960)
const HISTORY_NARROW_SHORT := Vector2i(1100, 600)

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
	failures.append_array(await _check_resize_history(tree, scene))
	return failures


# History independence: the Live 4D legend deck is a function of the current
# size, style and content only. Every comparison is against a separately
# created instance opened directly at that size, so a deck that keeps a
# constraint from an earlier, smaller size cannot match it.
func _check_resize_history(tree: SceneTree, scene: PackedScene) -> Array:
	var failures: Array = []
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var catalog = CatalogScript.new(registry)
	var looks: Array = []
	for record in catalog.list_styles():
		looks.append({"style": str(record.get("style_id", "")), "theme": ReplayVisuals.DISPLAY_MODE_PLAIN})
	if looks.size() < 4 or not catalog.diagnostics().is_empty():
		return ["resize-history acceptance requires a healthy built-in style catalog"]
	# Display themes change shell fonts and padding independently of the style.
	for theme in ReplayVisuals.DISPLAY_MODES:
		if theme != ReplayVisuals.DISPLAY_MODE_PLAIN:
			looks.append({"style": str(looks[0]["style"]), "theme": theme})
	for look in looks:
		var label := "Live 4D %s/%s" % [look["style"], look["theme"]]
		var clean_large := await _open_live_4d(tree, scene, catalog, look, HISTORY_LARGE)
		var reference := _deck_geometry(clean_large["hud"])
		_assert_legend_fits(failures, reference, "%s clean large" % label)
		clean_large["viewport"].queue_free()
		await tree.process_frame
		var clean_opening := await _open_live_4d(tree, scene, catalog, look, HISTORY_REFERENCE)
		var opening := _deck_geometry(clean_opening["hud"])
		_assert_legend_fits(failures, opening, "%s clean 1280x720" % label)
		_assert_opening_window_legend(failures, clean_opening["hud"], opening, "%s clean 1280x720" % label)
		clean_opening["viewport"].queue_free()
		await tree.process_frame
		var resized := await _open_live_4d(tree, scene, catalog, look, HISTORY_REFERENCE)
		var viewport: SubViewport = resized["viewport"]
		var hud = resized["hud"]
		_compare_geometry(failures, opening, _deck_geometry(hud), "%s second clean 1280x720 instance" % label)
		await _resize_case(tree, viewport, HISTORY_SHORT, hud)
		var short_first := _deck_geometry(hud)
		_assert_legend_compacts(failures, short_first, "%s short" % label)
		await _resize_case(tree, viewport, HISTORY_REFERENCE, hud)
		_compare_geometry(failures, opening, _deck_geometry(hud), "%s 1280x720->short->1280x720" % label)
		await _resize_case(tree, viewport, HISTORY_LARGE, hud)
		_compare_geometry(failures, reference, _deck_geometry(hud), "%s 1280x720->short->1280x720->large" % label)
		await _resize_case(tree, viewport, HISTORY_SHORT, hud)
		await _resize_case(tree, viewport, HISTORY_LARGE, hud)
		_compare_geometry(failures, reference, _deck_geometry(hud), "%s large->short->large" % label)
		for step in [HISTORY_NARROW, HISTORY_SHORT, HISTORY_NARROW_SHORT, HISTORY_LARGE]:
			await _resize_case(tree, viewport, step, hud)
		_compare_geometry(failures, reference, _deck_geometry(hud), "%s large->narrow->short->narrow+short->large" % label)
		if look == looks[0]:
			# Repeated cycling must neither drift nor accumulate.
			for cycle in range(2):
				await _resize_case(tree, viewport, HISTORY_SHORT, hud)
				_compare_geometry(failures, short_first, _deck_geometry(hud), "%s short after cycle %d" % [label, cycle + 1])
				await _resize_case(tree, viewport, HISTORY_LARGE, hud)
				_compare_geometry(failures, reference, _deck_geometry(hud), "%s large after cycle %d" % [label, cycle + 1])
		viewport.queue_free()
		await tree.process_frame
		if look == looks[0]:
			# Opened alone: two live shells in one real window would fight over
			# its content scale, a state production never has.
			# An open guide takes header height; the deck must yield it, not
			# push past the window or squeeze the board below its guard.
			var guided := await _open_live_4d(tree, scene, catalog, {"style": look["style"], "theme": look["theme"], "guide": true}, HISTORY_REFERENCE)
			var guided_geometry := _deck_geometry(guided["hud"])
			_assert_deck_safe(failures, guided_geometry, HISTORY_REFERENCE, "%s 1280x720 with guide open" % label)
			guided["hud"]._set_onboarding_visible(false)
			await _settle(tree, guided["hud"])
			_compare_geometry(failures, opening, _deck_geometry(guided["hud"]), "%s 1280x720 after closing the guide" % label)
			guided["viewport"].queue_free()
			await tree.process_frame
	return failures


func _open_live_4d(tree: SceneTree, scene: PackedScene, catalog, look: Dictionary, size: Vector2i) -> Dictionary:
	var viewport := SubViewport.new()
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.size = size
	tree.root.add_child(viewport)
	var root := scene.instantiate() as Control
	viewport.add_child(root)
	var hud = root.get_node("ReplayHud")
	await tree.process_frame
	await tree.process_frame
	hud._apply_ui_scale("standard")
	hud._apply_hud_density("standard")
	hud._set_onboarding_visible(false)
	hud.set_display_mode(str(look["theme"]))
	hud.apply_presentation_profile(hud.presentation_profile().with_style_of(catalog.style_profile(str(look["style"])).get("profile")))
	root.get_node("App")._enter_live_4d_mode()
	# Live entry may reopen the guide from persisted settings; normal play hides it.
	hud._set_onboarding_visible(bool(look.get("guide", false)))
	await _settle(tree, hud)
	return {"viewport": viewport, "hud": hud}


func _resize_case(tree: SceneTree, viewport: SubViewport, size: Vector2i, hud) -> void:
	viewport.size = size
	# The shell listens to the root Window's size_changed, which a SubViewport
	# resize never emits; deliver the same production callback it would.
	hud._on_shell_window_size_changed()
	await _settle(tree, hud)


# The cockpit fits its helpers over several frames (compact, then a scale
# search); with a HUD, also wait, bounded, for that fit to settle.
func _settle(tree: SceneTree, hud = null) -> void:
	for frame in range(10):
		await tree.process_frame
	if hud == null:
		return
	for frame in range(120):
		if hud._live_cockpit.fit_settled():
			return
		await tree.process_frame


func _deck_geometry(hud) -> Dictionary:
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var cockpit: Dictionary = snapshot.get("live_cockpit", {})
	var deck_scroll := hud._live_cockpit.deck_scroll as ScrollContainer
	var legend_scroll := hud.find_child("PieceHelpScroll", true, false) as ScrollContainer
	return {
		"deck_rect": snapshot.get("live_4d_deck", Rect2()),
		"deck_scroll_rect": deck_scroll.get_global_rect(),
		"deck_scrollbar_visible": deck_scroll.get_v_scroll_bar().visible,
		"deck_minimum_height": float(cockpit.get("deck_minimum_height", 0.0)),
		"deck_natural_height": float(cockpit.get("deck_natural_height", 0.0)),
		"deck_scroll_required": bool(cockpit.get("deck_scroll_required", false)),
		"deck_fit_scale": float(cockpit.get("deck_fit_scale", 1.0)),
		"deck_rows_rect": cockpit.get("deck_rows_rect", Rect2()),
		"deck_placement": str(cockpit.get("deck_placement", "")),
		"deck_row_assignment": str(cockpit.get("deck_row_assignment", [])),
		"legend_rect": legend_scroll.get_global_rect(),
		"legend_scrollbar_visible": legend_scroll.get_v_scroll_bar().visible,
		"legend_content_minimum": (legend_scroll.get_child(0) as Control).get_combined_minimum_size(),
		"piece_module_rect": snapshot.get("piece_module_rect", Rect2()),
		"side_column_rect": cockpit.get("side_column_rect", Rect2()),
		"game_area": snapshot.get("game_area", Rect2()),
		"game_viewport": snapshot.get("game_viewport", Rect2()),
	}


func _assert_legend_fits(failures: Array, geometry: Dictionary, label: String) -> void:
	var deck: Rect2 = geometry["deck_rect"]
	if geometry["deck_natural_height"] <= 0.0 or absf(deck.size.y - geometry["deck_natural_height"]) > 0.5:
		failures.append("%s must give the legend deck its measured content height %s, got %s" % [label, geometry["deck_natural_height"], deck.size.y])
	if geometry["deck_scroll_required"] or geometry["deck_scrollbar_visible"] or geometry["legend_scrollbar_visible"]:
		failures.append("%s must show the whole legend without a scrollbar" % label)
	if not _contains_rect(deck, geometry["piece_module_rect"]):
		failures.append("%s must show the legend module inside the deck: %s in %s" % [label, geometry["piece_module_rect"], deck])


# Stage 57 made these primary actions discoverable; at the opening window every
# legend label, including every rotation group, must sit in the visible deck.
func _assert_opening_window_legend(failures: Array, hud, geometry: Dictionary, label: String) -> void:
	_assert_deck_safe(failures, geometry, HISTORY_REFERENCE, label)
	var visible_area: Rect2 = geometry["deck_scroll_rect"]
	var shown := {}
	for node in hud._piece_control_strip.find_children("*", "Label", true, false):
		var text_label := node as Label
		if not text_label.is_visible_in_tree() or text_label.text.strip_edges().is_empty():
			continue
		shown[text_label.text] = true
		if not _contains_rect(visible_area, text_label.get_global_rect()):
			failures.append("%s must show legend label '%s' without scrolling: %s in %s" % [label, text_label.text, text_label.get_global_rect(), visible_area])
	for required in ["MOVE", "ROTATE", "GAME", "Hold", "Pause", "Restart", "Hard drop", "Tip"]:
		if not shown.has(required):
			failures.append("%s must show '%s' in the legend, got %s" % [label, required, shown.keys()])


func _assert_deck_safe(failures: Array, geometry: Dictionary, window: Vector2i, label: String) -> void:
	var usable := Rect2(Vector2.ZERO, Vector2(window))
	var deck: Rect2 = geometry["deck_rect"]
	var board: Rect2 = geometry["game_area"]
	var game_viewport: Rect2 = geometry["game_viewport"]
	if not _contains_rect(usable, deck) or board.intersects(deck):
		failures.append("%s must keep the deck inside the window and clear of the board: deck %s board %s" % [label, deck, board])
	# Pathological-shrink guard only; the legend outranks the old area target.
	if game_viewport.size.x < COLLAPSE_GUARD_PX or game_viewport.size.y / usable.size.y < MIN_GAME_HEIGHT_SHARE:
		failures.append("%s must keep the board usable beside the legend, got %s" % [label, game_viewport])


# A short window still takes deck height for the board. The legend then fits
# by shrinking, compacting and then scaling uniformly, and scrolls only once
# it is at the cockpit's scale floor.
func _assert_legend_compacts(failures: Array, geometry: Dictionary, label: String) -> void:
	var deck: Rect2 = geometry["deck_rect"]
	var usable := Rect2(Vector2.ZERO, Vector2(HISTORY_SHORT))
	var unscaled_legend: float = (geometry["legend_content_minimum"] as Vector2).y
	if deck.size.y >= unscaled_legend - 0.5:
		failures.append("%s must give up deck height below the full legend: deck %s legend %s" % [label, deck.size.y, unscaled_legend])
	var at_floor: bool = float(geometry["deck_fit_scale"]) <= LiveCockpitScript.FIT_SCALE_FLOOR + 0.001
	if float(geometry["deck_fit_scale"]) >= 1.0:
		failures.append("%s must shrink the legend to fit the short deck" % label)
	if (geometry["deck_scrollbar_visible"] or geometry["deck_scroll_required"]) and not at_floor:
		failures.append("%s must not scroll the legend above the scale floor (scale %s)" % [label, geometry["deck_fit_scale"]])
	if not _contains_rect(usable, deck) or (geometry["game_area"] as Rect2).intersects(deck):
		failures.append("%s must keep the compact deck inside the window and clear of the board: %s" % [label, deck])


func _compare_geometry(failures: Array, expected: Dictionary, actual: Dictionary, label: String) -> void:
	for key in expected:
		var want = expected[key]
		var got = actual.get(key)
		var same: bool
		if want is Rect2:
			same = got is Rect2 and want.position.distance_to(got.position) <= 0.5 and want.size.distance_to(got.size) <= 0.5
		elif want is Vector2:
			same = got is Vector2 and want.distance_to(got) <= 0.5
		elif want is float:
			same = got is float and absf(want - got) <= 0.5
		else:
			same = want == got
		if not same:
			failures.append("%s must restore %s: expected %s, got %s" % [label, key, want, got])


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
		# A windowed run takes the breakpoint from the real window, not this
		# SubViewport (see the header). A case whose size selects a different
		# profile is geometry production cannot reach here; headless never skips.
		var selected := str(hud.layout_contract_snapshot().get("live_cockpit", {}).get("responsive_profile", ""))
		if selected != hud._live_cockpit.responsive_profile_for_size(Vector2(requested_size)):
			if DisplayServer.get_name() == "headless":
				failures.append("%s Live %s must select its own profile headless, got %s" % [viewport_case["name"], mode, selected])
			else:
				print("skipped unreachable %s Live %s: window profile %s" % [viewport_case["name"], mode, selected])
			continue
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
	# Below the board NEXT/HOLD come first, as in the rail and the split column.
	var expected_order := ["PieceState", "PieceControls", "ViewControls"]
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
		# The 4D split legend must fit too; only the side rail may scroll here.
		if not side_rail and (bool(cockpit.get("deck_scroll_required", false)) or int(cockpit.get("deck_row_count", 0)) != 1):
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
