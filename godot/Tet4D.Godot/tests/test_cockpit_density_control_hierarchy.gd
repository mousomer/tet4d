extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")
const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")
const LivePieceControlStripScript = preload("res://scripts/ui/live_piece_control_strip.gd")
const DesignerScript = preload("res://scripts/ui/presentation_designer.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(_check_authoritative_piece_sets())
	failures.append_array(await _check_production_layout())
	return failures


func _check_authoritative_piece_sets() -> Array:
	var failures: Array = []
	var cases := {
		"live_2d": {
			"rotation": ["Rotate clockwise", "Rotate counter-clockwise"],
			"bindings": ["A/D", "Left/Right", "Up/W/X", "Z"],
			"forbidden": ["XY", "XZ", "XW", "Q / E"],
		},
		"live_3d": {
			"rotation": ["Rotate XY", "Rotate XZ", "Rotate YZ"],
			"bindings": ["A/D", "W/S", "R/T", "F/G", "V/B"],
			"forbidden": ["XW", "YW", "ZW", "Q / E"],
		},
		"live_4d": {
			"rotation": ["XY", "XZ", "YZ", "XW", "YW", "ZW"],
			"bindings": ["A / D", "W / S", "Q / E", "R / T", "F / G", "V / B", "Y / U", "H / J", "N / M"],
			"forbidden": [],
		},
	}
	for mode in cases:
		var groups := LiveInputContractScript.piece_control_groups(mode)
		if groups.size() != 5 or groups.map(func(group): return str(group.get("cockpit_role", ""))) != ["translate", "drop", "rotate", "hold", "session"]:
			failures.append("%s piece strip must select authoritative movement, rotation, drop, hold and session groups" % mode)
			continue
		var text := str(groups)
		for rotation_label in cases[mode]["rotation"]:
			if text.find(str(rotation_label)) == -1:
				failures.append("%s piece strip must expose applicable rotation %s" % [mode, rotation_label])
		for binding in cases[mode]["bindings"]:
			if text.find(str(binding)) == -1:
				failures.append("%s piece strip binding must match LiveInputContract: %s" % [mode, binding])
		for forbidden in cases[mode]["forbidden"]:
			if text.find(str(forbidden)) != -1:
				failures.append("%s piece strip must omit inapplicable control %s" % [mode, forbidden])
	var strip_source := FileAccess.get_file_as_string("res://scripts/ui/live_piece_control_strip.gd")
	for forbidden_inventory in ["live_2d_move", "live_3d_rotate", "live_4d_rotate", "KEY_A", "KEY_R", "Slice Down / Up", "begins_with(\"Left / Right\")", "begins_with(\"Forward / Back\")"]:
		if strip_source.find(forbidden_inventory) != -1:
			failures.append("piece-control presentation must not maintain action/binding inventory %s" % forbidden_inventory)
	failures.append_array(_check_semantic_compaction())
	return failures


func _check_semantic_compaction() -> Array:
	var failures: Array = []
	var cases := {
		"live_2d": {
			"frame": {"translation_frame": "relative", "horizontal_axis": "-X"},
			"expected": [["horizontal", "-X", "← → [-X]", "A/D · Left/Right"]],
		},
		"live_3d": {
			"frame": {"translation_frame": "relative", "horizontal_axis": "+X", "depth_axis": "-Z"},
			"expected": [["horizontal", "+X", "← → [+X]", "A/D"], ["depth", "-Z", "↑ ↓ [-Z]", "W/S"]],
		},
		"live_4d": {
			"frame": {"translation_frame": "relative", "horizontal_axis": "+X", "depth_axis": "+Z", "slice_axis": "+W"},
			"expected": [["horizontal", "+X", "← → [+X]", "A / D"], ["depth", "+Z", "↑ ↓ [+Z]", "W / S"], ["slice", "+W", "W− W+ [+W]", "Q / E"]],
		},
	}
	for mode in cases:
		var strip = LivePieceControlStripScript.new()
		strip.configure(mode, {}, cases[mode]["frame"])
		var compact_items: Array = strip.deterministic_snapshot().get("compact_items", [])
		var translations: Array = compact_items.filter(func(item: Dictionary) -> bool: return item.get("role") == "translate")
		var expected: Array = cases[mode]["expected"]
		if translations.size() != expected.size():
			failures.append("%s must expose %d semantic compact translation rows exactly once, got %s" % [mode, expected.size(), translations])
			strip.free()
			continue
		for index in range(expected.size()):
			var semantic: Dictionary = translations[index].get("semantic", {})
			if (
				semantic.get("cockpit_direction") != expected[index][0]
				or semantic.get("signed_axis") != expected[index][1]
				or translations[index].get("compact_label") != expected[index][2]
				or translations[index].get("binding") != expected[index][3]
			):
				failures.append("%s semantic compact row %d should be %s, got %s" % [mode, index, expected[index], translations[index]])
		strip.free()
	return failures


func _check_production_layout() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if tree == null or scene == null:
		return ["cockpit hierarchy test requires the production trace replay scene"]
	var original_root_size := tree.root.size
	# Product windows scale this fixed logical canvas; pin it so earlier headless
	# tests or host display defaults cannot alter the ratio contract under test.
	tree.root.size = Vector2i(1600, 960)
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	await tree.process_frame
	var hud = root.get_node_or_null("ReplayHud")
	var app = root.get_node_or_null("App")
	if hud == null or app == null:
		root.queue_free()
		tree.root.size = original_root_size
		return ["cockpit hierarchy test requires ReplayHud and TraceReplayApp"]
	# Earlier integration tests deliberately exercise global UI-scale changes.
	# Establish this test's documented standard-density baseline explicitly.
	hud._apply_ui_scale("standard")
	hud._set_onboarding_visible(false)
	await tree.process_frame
	await tree.process_frame
	for mode in ["live_2d", "live_3d", "live_4d"]:
		match mode:
			"live_2d": app._enter_live_2d_mode()
			"live_3d": app._enter_live_3d_mode()
			"live_4d": app._enter_live_4d_mode()
		await tree.process_frame
		await tree.process_frame
		failures.append_array(_check_primary_surfaces(hud, mode, "normal"))

	app._enter_live_4d_mode()
	await tree.process_frame
	await tree.process_frame
	var layout: Dictionary = hud.layout_contract_snapshot()
	var body: Rect2 = layout.get("body", Rect2())
	var game: Rect2 = layout.get("game_area", Rect2())
	var viewport: Rect2 = layout.get("game_viewport", Rect2())
	var game_width_share := game.size.x / body.size.x
	var viewport_area_share := (viewport.size.x * viewport.size.y) / (body.size.x * body.size.y)
	# The full suite intentionally leaves enlarged shared font resources cached;
	# these lower bounds cover that supported accessibility extreme. The clean
	# standard-density production values are 79.6% width and 72.2% body area.
	if game_width_share < 0.70:
		failures.append("Live 4D game area must retain at least 70%% of live body width, got %.4f in %s / %s" % [game_width_share, game, body])
	if viewport_area_share < 0.63:
		failures.append("Live 4D gameplay viewport must retain at least 63%% of live body area, got %.4f in %s / %s" % [viewport_area_share, viewport, body])
	if body.position.y > 120.0:
		failures.append("compact live top cockpit must return vertical space to the board")
	if absf(CameraRigScript.LIVE_4D_FIT_MARGIN - 1.05) > 0.0001:
		failures.append("Live 4D fit must retain the documented modest clearance beyond required bounds")
	var projected_share := _projected_bounds_height_share(app)
	if projected_share < 0.94 or projected_share > 0.96:
		failures.append("authoritative Live 4D bounds should use about 95 percent of the limiting viewport dimension, got %.4f" % projected_share)

	var deterministic_before := str(app._live_bridge.live_4d_state_hash())
	hud._open_presentation_designer()
	await tree.process_frame
	await tree.process_frame
	if hud._presentation_designer.state() != DesignerScript.STATE_FULL:
		failures.append("Designer should open full for coexistence evidence")
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer full"))
	hud._presentation_designer.set_library_expanded(false)
	await tree.process_frame
	await tree.process_frame
	var collapsed_viewport: Rect2 = hud._game_viewport_container.get_global_rect()
	var collapsed_designer: Rect2 = hud._presentation_designer.get_global_rect()
	hud._presentation_designer.set_library_expanded(true)
	await tree.process_frame
	await tree.process_frame
	var expanded_viewport: Rect2 = hud._game_viewport_container.get_global_rect()
	var expanded_designer: Rect2 = hud._presentation_designer.get_global_rect()
	if not _same_rect(collapsed_viewport, expanded_viewport):
		failures.append("expanding the Profile Library must not change Live 4D gameplay viewport allocation: %s -> %s" % [collapsed_viewport, expanded_viewport])
	if expanded_designer.position.x < game.position.x - 0.5 or expanded_designer.end.x > game.end.x + 0.5 or expanded_designer.size.x >= game.size.x * 0.65:
		failures.append("Profile Library expansion must retain a bounded Designer column within the board")
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer library expanded"))
	if not _orientation_indicator_is_available(app):
		failures.append("expanded Profile Library must preserve the visible Live 4D orientation indicator")
	hud._presentation_designer.set_library_expanded(false)
	await tree.process_frame
	await tree.process_frame
	if not _same_rect(expanded_viewport, hud._game_viewport_container.get_global_rect()):
		failures.append("collapsing the Profile Library must retain the same Live 4D gameplay viewport allocation")

	hud._presentation_designer.set_built_in_styles_expanded(true)
	await tree.process_frame
	await tree.process_frame
	if not _same_rect(collapsed_viewport, hud._game_viewport_container.get_global_rect()):
		failures.append("expanding Built-in Styles must not change Live 4D gameplay viewport allocation")
	var styles_designer_rect: Rect2 = hud._presentation_designer.get_global_rect()
	if styles_designer_rect.position.x < game.position.x - 0.5 or styles_designer_rect.end.x > game.end.x + 0.5 or styles_designer_rect.size.x >= game.size.x * 0.65:
		failures.append("Built-in Styles expansion must retain a bounded Designer column within the board")
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer built-in styles expanded"))
	if not _orientation_indicator_is_available(app):
		failures.append("expanded Built-in Styles must preserve the visible Live 4D orientation indicator")
	hud._presentation_designer.set_built_in_styles_expanded(false)
	await tree.process_frame
	await tree.process_frame
	if not _same_rect(collapsed_viewport, hud._game_viewport_container.get_global_rect()):
		failures.append("collapsing Built-in Styles must retain the same Live 4D gameplay viewport allocation")
	hud._presentation_designer.collapse_to_compact()
	await tree.process_frame
	await tree.process_frame
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer compact"))
	if str(app._live_bridge.live_4d_state_hash()) != deterministic_before:
		failures.append("cockpit/Designer presentation must not mutate deterministic Live 4D state")

	for scale_id in ["large", "extra_large"]:
		hud._apply_ui_scale(scale_id)
		await tree.process_frame
		await tree.process_frame
		failures.append_array(_check_primary_surfaces(hud, "live_4d", "%s UI scale" % scale_id))
	hud._apply_ui_scale("standard")
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_root_size
	return failures


func _check_primary_surfaces(hud, mode: String, label: String) -> Array:
	var failures: Array = []
	var layout: Dictionary = hud.layout_contract_snapshot()
	var viewport: Rect2 = hud._game_viewport_container.get_global_rect()
	var deck: Rect2 = layout.get("live_4d_deck", Rect2())
	var piece_module: Rect2 = layout.get("piece_module_rect", Rect2())
	var view_module: Rect2 = layout.get("view_module_rect", Rect2())
	var state_module: Rect2 = layout.get("piece_state_module_rect", Rect2())
	var preview: Rect2 = hud._piece_preview_row.get_global_rect()
	var next_rect: Rect2 = hud._next_piece_panel.get_global_rect()
	var hold_rect: Rect2 = hud._hold_piece_panel.get_global_rect()
	var piece_rect: Rect2 = hud._piece_control_strip.get_global_rect()
	var view_rect: Rect2 = hud._live_view_control_strip.get_global_rect()
	if viewport.size.x <= 0.0 or viewport.size.y <= 0.0:
		failures.append("%s %s board must remain visible" % [label, mode])
	var strict_containment := label.find("UI scale") == -1
	# The deck scrolls when constrained, so the modules' containing object is the
	# deck's row host, not the deck's visible rect. A module below the fold is
	# reachable by scrolling, which is the accepted constrained-size tradeoff;
	# a module outside the row host would be genuinely lost.
	var rows_rect: Rect2 = (layout.get("live_cockpit", {}) as Dictionary).get("deck_rows_rect", deck)
	var frames: Dictionary = hud._live_cockpit.designer_panels()
	var floating := not frames.is_empty()
	var split := mode == "live_4d" and str((layout.get("live_cockpit", {}) as Dictionary).get("deck_placement", "")) == "split"
	var rail := mode in ["live_2d", "live_3d"]
	if floating:
		# The requested full Designer mode has free rectangles, not dock slots.
		# Verify its geometry and scrolling, then retain shared content checks.
		var host: Rect2 = hud._live_cockpit._designer_host.get_global_rect()
		if frames.size() != 4:
			failures.append("Full Designer must expose all four cockpit panels")
		for key in frames:
			var frame = frames[key]
			if not _contains_rect(host, frame.get_global_rect()) or not frame.move_handle.is_visible_in_tree() or not frame.resize_handle.is_visible_in_tree():
				failures.append("Designer %s must retain bounded geometry and visible handles" % key)
		for module in [hud._live_cockpit.piece_controls, hud._live_cockpit.view_controls, hud._live_cockpit.piece_state]:
			if not module.is_visible_in_tree() or not (module.get_parent() is ScrollContainer):
				failures.append("Designer modules must remain visible and scrollable")
	else:
		if viewport.intersects(deck):
			failures.append("%s %s board and shared deck must not overlap" % [label, mode])
		if split:
			var side: Rect2 = (layout.get("live_cockpit", {}) as Dictionary).get("side_column_rect", Rect2())
			if not layout.get("live_4d_deck_visible", false) or (strict_containment and (not _contains_rect(rows_rect, piece_module) or not _contains_rect(side, state_module))):
				failures.append("%s %s must show the legend in the deck and NEXT/HOLD in the side column" % [label, mode])
			if viewport.intersects(side) or not _precedes(state_module, view_module):
				failures.append("%s %s side column must sit beside the board with NEXT/HOLD above VIEW" % [label, mode])
		elif rail:
			if not layout.get("live_4d_deck_visible", false) or (strict_containment and (not _contains_rect(rows_rect, piece_module) or not _contains_rect(rows_rect, state_module))):
				failures.append("%s %s rail must visibly contain NEXT/HOLD and the key legend" % [label, mode])
			if not _precedes(state_module, piece_module):
				failures.append("%s %s rail must stack NEXT/HOLD above the key legend" % [label, mode])
			# The 3D rail carries the 4D panel set: VIEW sits below the legend.
			if mode == "live_3d" and (not hud._live_view_control_strip.is_visible_in_tree() or (strict_containment and not _contains_rect(rows_rect, view_module)) or not _precedes(piece_module, view_module)):
				failures.append("%s %s rail must show VIEW below the key legend" % [label, mode])
		else:
			if not layout.get("live_4d_deck_visible", false) or (strict_containment and (not _contains_rect(rows_rect, piece_module) or not _contains_rect(rows_rect, view_module) or not _contains_rect(rows_rect, state_module))):
				failures.append("%s %s shared deck must visibly contain all three semantic modules" % [label, mode])
			# Reading order, not a single line: the deck reflows into rows when the
			# modules' measured minimum widths exceed the available width, so modules on
			# different rows legitimately share an X range. Identity and order survive;
			# "one HBox at every width" is deliberately not an invariant.
			if not _modules_in_reading_order(piece_module, view_module, state_module):
				failures.append("%s %s deck modules must follow Piece, View, Piece State order without overlap" % [label, mode])
	for surface in [[piece_rect, piece_module, "piece controls"], [view_rect, view_module, "view controls"], [preview, state_module, "preview row"], [next_rect, state_module, "NEXT"], [hold_rect, state_module, "HOLD"]]:
		if surface[2] == "view controls" and not hud._live_view_control_strip.is_visible_in_tree():
			continue
		if surface[0].size.x <= 0.0 or surface[0].size.y <= 0.0 or (strict_containment and not _contains_rect(surface[1], surface[0])):
			failures.append("%s %s %s must be contained by its semantic deck module" % [label, mode, surface[2]])
	var stacked_previews: bool = hud._piece_preview_row.columns == 1
	if next_rect.intersects(hold_rect) or (next_rect.end.y > hold_rect.position.y + 0.5 if stacked_previews else next_rect.end.x > hold_rect.position.x + 0.5):
		failures.append("%s %s NEXT and HOLD must follow the preview grid without overlap" % [label, mode])
	var strip: Dictionary = hud._piece_control_strip.deterministic_snapshot()
	if strip.get("source") != "LiveInputContract" or strip.get("roles", []) != ["translate", "drop", "rotate", "hold", "session"]:
		failures.append("%s %s piece surface must report authoritative translate/rotate/drop consumption" % [label, mode])
	var view_strip: Dictionary = hud._live_view_control_strip.deterministic_snapshot()
	if view_strip.get("source") != "LiveInputContract" or view_strip.get("roles", []).is_empty():
		failures.append("%s %s view surface must report authoritative LiveInputContract consumption" % [label, mode])
	if hud._piece_control_strip.mouse_filter != Control.MOUSE_FILTER_IGNORE or not hud._piece_control_strip.find_children("*", "BaseButton", true, false).is_empty():
		failures.append("%s %s piece surface must remain passive guidance, not a gameplay input modality" % [label, mode])
	return failures


func _orientation_indicator_is_available(app) -> bool:
	var snapshot: Dictionary = app._camera_rig.orientation_indicator_snapshot()
	return snapshot.get("source") == "live_4d_presentation" and not snapshot.get("basis_slots", []).is_empty() and not str(snapshot.get("control_frame", {}).get("slice_axis", "")).is_empty()


# Measured against the per-slice content boxes, not the collection AABB. The
# slice row is counter-rotated so it presents level, so the AABB's extreme
# corners are occupied by nothing; requiring THOSE to fill 95% of the limiting
# dimension is what held the flagship mode to roughly half its available size.
# The boxes carry each slice's own label and active-piece clearance, so this
# still asserts that every drawn attachment stays on screen.
func _projected_bounds_height_share(app) -> float:
	var boxes: Array = app._renderer.current_content_boxes()
	if boxes.is_empty():
		return 0.0
	var screen_min := Vector2(INF, INF)
	var screen_max := Vector2(-INF, -INF)
	for box in boxes:
		var minimum: Vector3 = box.get("min", Vector3.ZERO)
		var maximum: Vector3 = box.get("max", Vector3.ZERO)
		for x in [minimum.x, maximum.x]:
			for y in [minimum.y, maximum.y]:
				for z in [minimum.z, maximum.z]:
					var point: Vector2 = app._camera_rig.project_world_point(Vector3(x, y, z))
					screen_min = screen_min.min(point)
					screen_max = screen_max.max(point)
	# The limiting dimension is whichever the fit filled: height when the slice
	# row has width to spare, width once a side column narrows the viewport.
	var viewport_size: Vector2 = app._camera_rig._camera.get_viewport().get_visible_rect().size
	if viewport_size.x <= 0.0 or viewport_size.y <= 0.0:
		return 0.0
	var span := screen_max - screen_min
	return maxf(span.x / viewport_size.x, span.y / viewport_size.y)


func _modules_in_reading_order(first: Rect2, second: Rect2, third: Rect2) -> bool:
	return _precedes(first, second) and _precedes(second, third)


func _precedes(earlier: Rect2, later: Rect2) -> bool:
	if earlier.end.y <= later.position.y + 0.5:
		return true
	if later.end.y <= earlier.position.y + 0.5:
		return false
	return earlier.end.x <= later.position.x + 0.5


func _contains_rect(outer: Rect2, inner: Rect2) -> bool:
	return (
		inner.size.x > 0.0
		and inner.size.y > 0.0
		and inner.position.x >= outer.position.x - 0.5
		and inner.position.y >= outer.position.y - 0.5
		and inner.end.x <= outer.end.x + 0.5
		and inner.end.y <= outer.end.y + 0.5
	)


func _same_rect(left: Rect2, right: Rect2) -> bool:
	return left.position.is_equal_approx(right.position) and left.size.is_equal_approx(right.size)
