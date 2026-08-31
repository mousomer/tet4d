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
		if groups.size() != 2 or str(groups[0].get("cockpit_role", "")) != "translate" or str(groups[1].get("cockpit_role", "")) != "rotate":
			failures.append("%s piece strip must select exactly authoritative translate and rotate groups" % mode)
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
	if not _same_rect(collapsed_designer, expanded_designer):
		failures.append("Profile Library expansion must consume internal Designer space without enlarging its cockpit footprint")
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer library expanded"))
	if not hud._basis_panel.is_visible_in_tree() or str(hud.layout_contract_snapshot().get("basis_indicator_text", "")).find("Slice:") == -1:
		failures.append("expanded Profile Library must preserve visible Live 4D basis/slice state")
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
	if not _same_rect(collapsed_designer, hud._presentation_designer.get_global_rect()):
		failures.append("Built-in Styles expansion must consume internal Designer space without enlarging its cockpit footprint")
	failures.append_array(_check_primary_surfaces(hud, "live_4d", "Designer built-in styles expanded"))
	if not hud._basis_panel.is_visible_in_tree() or str(hud.layout_contract_snapshot().get("basis_indicator_text", "")).find("Slice:") == -1:
		failures.append("expanded Built-in Styles must preserve visible Live 4D basis/slice state")
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
	var inspector: Rect2 = hud._right_scroll.get_global_rect()
	var viewport: Rect2 = hud._game_viewport_container.get_global_rect()
	var preview: Rect2 = hud._piece_preview_row.get_global_rect()
	var next_rect: Rect2 = hud._next_piece_panel.get_global_rect()
	var hold_rect: Rect2 = hud._hold_piece_panel.get_global_rect()
	var piece_rect: Rect2 = hud._piece_control_strip.get_global_rect()
	var camera_rect: Rect2 = hud._camera_panel.get_global_rect()
	if viewport.size.x <= 0.0 or viewport.size.y <= 0.0:
		failures.append("%s %s board must remain visible" % [label, mode])
	for surface in [[preview, "preview row"], [next_rect, "NEXT"], [hold_rect, "HOLD"], [piece_rect, "piece controls"]]:
		if not _contains_rect(inspector, surface[0]):
			failures.append("%s %s %s must be wholly visible without inspector scroll" % [label, mode, surface[1]])
	if next_rect.intersects(hold_rect) or next_rect.end.x > hold_rect.position.x + 0.5:
		failures.append("%s %s NEXT and HOLD must be compact side-by-side non-overlapping surfaces" % [label, mode])
	if preview.size.y > inspector.size.y * 0.34:
		failures.append("%s %s NEXT/HOLD row must not dominate inspector height" % [label, mode])
	if piece_rect.position.y < preview.end.y - 0.5:
		failures.append("%s %s piece guidance must follow compact NEXT/HOLD" % [label, mode])
	if camera_rect.position.y < piece_rect.end.y - 0.5:
		failures.append("%s %s camera guidance must appear below primary piece guidance" % [label, mode])
	var strip: Dictionary = hud._piece_control_strip.deterministic_snapshot()
	if strip.get("source") != "LiveInputContract" or strip.get("roles", []) != ["translate", "rotate"]:
		failures.append("%s %s piece surface must report authoritative translate/rotate consumption" % [label, mode])
	if hud._piece_control_strip.mouse_filter != Control.MOUSE_FILTER_IGNORE or not hud._piece_control_strip.find_children("*", "BaseButton", true, false).is_empty():
		failures.append("%s %s piece surface must remain passive guidance, not a gameplay input modality" % [label, mode])
	if hud._right_scroll.scroll_vertical != 0:
		failures.append("%s %s primary surfaces must be visible at the initial inspector position" % [label, mode])
	return failures


func _projected_bounds_height_share(app) -> float:
	var bounds: Dictionary = app._renderer.current_bounds()
	if not bounds.get("ok", false):
		return 0.0
	var minimum: Vector3 = bounds.get("min", Vector3.ZERO)
	var maximum: Vector3 = bounds.get("max", Vector3.ZERO)
	var screen_min := Vector2(INF, INF)
	var screen_max := Vector2(-INF, -INF)
	for x in [minimum.x, maximum.x]:
		for y in [minimum.y, maximum.y]:
			for z in [minimum.z, maximum.z]:
				var world: Vector3 = app._renderer.to_global(Vector3(x, y, z))
				var point: Vector2 = app._camera_rig.project_world_point(world)
				screen_min.y = minf(screen_min.y, point.y)
				screen_max.y = maxf(screen_max.y, point.y)
	var viewport_height: float = app._camera_rig._camera.get_viewport().get_visible_rect().size.y
	return (screen_max.y - screen_min.y) / viewport_height if viewport_height > 0.0 else 0.0


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
