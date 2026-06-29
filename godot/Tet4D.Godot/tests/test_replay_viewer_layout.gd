extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const ReplayHud = preload("res://scripts/ui/replay_hud.gd")

const VIEWPORT_SIZES := [
	Vector2i(1600, 960),
	Vector2i(1180, 760),
	Vector2i(960, 640),
]


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		return ["trace replay scene should load for layout contract"]
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["layout contract test requires SceneTree"]
	for viewport_size in VIEWPORT_SIZES:
		var root := scene.instantiate() as Control
		if root == null:
			failures.append("trace replay root should instantiate for %s" % str(viewport_size))
			continue
		tree.root.add_child(root)
		root.set_anchors_preset(Control.PRESET_TOP_LEFT)
		root.size = Vector2(viewport_size)
		var hud := root.get_node_or_null("ReplayHud")
		if hud == null:
			failures.append("ReplayHud should exist for layout contract")
			root.queue_free()
			continue
		hud.show_replay_viewer()
		await tree.process_frame
		await tree.process_frame
		hud.set_bundle_status("Bundle: OK · 12 cases", "Bundle: exported_bundle · digest abc123")
		hud.set_camera_status("Camera: LIVE_3D_EXTERNAL_DIAGRAM_VIEW · ortho · above exterior · yaw 32 deg · pitch above 26 deg · roll 0 deg · fit OK")
		await tree.process_frame
		failures.append_array(_check_layout(hud, viewport_size))
		var replay_snapshot: Dictionary = hud.layout_contract_snapshot()
		var replay_game_rect: Rect2 = replay_snapshot.get("game_area", Rect2())
		hud.set_live_4d_mode(false, true, "move_w_negative", "out_of_bounds", 0.5)
		await tree.process_frame
		failures.append_array(_check_live_4d_cockpit_contract(hud, viewport_size, replay_game_rect.size.x))
		root.queue_free()
		await tree.process_frame
	failures.append_array(_check_live_control_maps())
	return failures


func _check_layout(hud: Node, viewport_size: Vector2i) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var root_rect: Rect2 = snapshot.get("root", Rect2())
	var left_rect: Rect2 = snapshot.get("left_panel", Rect2())
	var body_rect: Rect2 = snapshot.get("body", Rect2())
	var game_rect: Rect2 = snapshot.get("game_area", Rect2())
	var game_viewport_rect: Rect2 = snapshot.get("game_viewport", Rect2())
	var inspector_rect: Rect2 = snapshot.get("right_inspector", Rect2())
	var settings_rect: Rect2 = snapshot.get("settings_panel", Rect2())
	var bottom_rect: Rect2 = snapshot.get("bottom_bar", Rect2())
	var supported_minimum_size: Vector2 = snapshot.get("supported_minimum_size", Vector2())
	var bundle_status_text := str(snapshot.get("bundle_status_text", ""))
	var bundle_detail_text := str(snapshot.get("bundle_detail_text", ""))
	var camera_status_text := str(snapshot.get("camera_status_text", ""))
	var viewport_hint_text := str(snapshot.get("viewport_hint_text", ""))
	var bottom_hint_text := str(snapshot.get("bottom_hint_text", ""))
	var left_panel_visible := bool(snapshot.get("left_panel_visible", false))
	var left_panel_text := str(snapshot.get("left_panel_text", ""))
	var game_area_panel_color: Color = snapshot.get("game_area_panel_color", Color.TRANSPARENT)
	var game_area_border_color: Color = snapshot.get("game_area_border_color", Color.TRANSPARENT)
	var bottom_bar_border_color: Color = snapshot.get("bottom_bar_border_color", Color.TRANSPARENT)
	var label := "viewport %s" % str(viewport_size)
	if root_rect.size.x <= 0.0 or root_rect.size.y <= 0.0:
		failures.append("%s: root rect should be nonzero" % label)
	if body_rect.size.x <= 0.0 or body_rect.size.y <= 0.0:
		failures.append("%s: body rect should be nonzero" % label)
	if left_rect.size.x <= 0.0 or left_rect.size.y <= 0.0:
		failures.append("%s: left case browser rect should be nonzero" % label)
	if not left_panel_visible or left_panel_text.find("Replay Cases") == -1:
		failures.append("%s: replay mode should keep Replay Cases browser available" % label)
	if game_rect.size.x <= 0.0 or game_rect.size.y <= 0.0:
		failures.append("%s: game area rect should be nonzero" % label)
	if game_viewport_rect.size.x <= 0.0 or game_viewport_rect.size.y <= 0.0:
		failures.append("%s: game viewport rect should be nonzero" % label)
	if inspector_rect.size.x <= 0.0 or inspector_rect.size.y <= 0.0:
		failures.append("%s: right inspector rect should be nonzero" % label)
	if settings_rect.size.x <= 0.0 or settings_rect.size.y <= 0.0:
		failures.append("%s: settings panel rect should be nonzero" % label)
	if bottom_rect.size.x <= 0.0 or bottom_rect.size.y <= 0.0:
		failures.append("%s: bottom bar rect should be nonzero" % label)
	if supported_minimum_size != ReplayVisuals.supported_shell_minimum_size():
		failures.append("%s: HUD should report the supported shell minimum size" % label)
	if root_rect.size.x < supported_minimum_size.x - 0.5:
		failures.append("%s: root should satisfy supported shell minimum width, root=%s minimum=%s" % [label, root_rect, supported_minimum_size])
	if root_rect.size.y < supported_minimum_size.y - 0.5:
		failures.append("%s: root should satisfy supported shell minimum height, root=%s minimum=%s" % [label, root_rect, supported_minimum_size])
	if left_rect.size.x < ReplayVisuals.LEFT_PANEL_WIDTH - 0.5:
		failures.append("%s: left case browser should keep its reserved width, left=%s" % [label, left_rect])
	if inspector_rect.size.x < ReplayVisuals.RIGHT_PANEL_MIN_WIDTH - 0.5:
		failures.append("%s: right inspector should keep its reserved width, inspector=%s" % [label, inspector_rect])
	if settings_rect.size.x > inspector_rect.size.x + 0.5:
		failures.append("%s: settings panel should stay within inspector width, inspector=%s settings=%s" % [label, inspector_rect, settings_rect])
	if game_rect.size.x < ReplayVisuals.GAME_AREA_MIN_WIDTH - 0.5:
		failures.append("%s: game area should keep its minimum width, game=%s" % [label, game_rect])
	if not _contains_rect(root_rect, body_rect):
		failures.append("%s: body should be inside root, root=%s body=%s left=%s game=%s inspector=%s" % [label, root_rect, body_rect, left_rect, game_rect, inspector_rect])
	if not _contains_rect(body_rect, game_rect):
		failures.append("%s: game area should be inside body, body=%s game=%s" % [label, body_rect, game_rect])
	if not _contains_rect(body_rect, left_rect):
		failures.append("%s: left case browser should be inside body, body=%s left=%s" % [label, body_rect, left_rect])
	if not _contains_rect(body_rect, inspector_rect):
		failures.append("%s: inspector should be inside body, body=%s inspector=%s" % [label, body_rect, inspector_rect])
	if not _contains_rect(game_rect, game_viewport_rect):
		failures.append("%s: game viewport should be inside game area, game=%s viewport=%s" % [label, game_rect, game_viewport_rect])
	if inspector_rect.end.x > root_rect.end.x + 0.5:
		failures.append("%s: inspector right edge should stay inside root, root=%s inspector=%s" % [label, root_rect, inspector_rect])
	if settings_rect.position.x < inspector_rect.position.x - 0.5 or settings_rect.end.x > inspector_rect.end.x + 0.5:
		failures.append("%s: settings panel should be horizontally reachable inside inspector, inspector=%s settings=%s" % [label, inspector_rect, settings_rect])
	if game_rect.end.x > inspector_rect.position.x + 0.5:
		failures.append("%s: game area should not overlap inspector, game=%s inspector=%s" % [label, game_rect, inspector_rect])
	if left_rect.end.x > game_rect.position.x + 0.5:
		failures.append("%s: left case browser should not overlap game area, left=%s game=%s" % [label, left_rect, game_rect])
	if bundle_status_text.find("Bundle: OK") == -1:
		failures.append("%s: top bundle status should stay compact and readable" % label)
	if bundle_detail_text.find("digest abc123") == -1:
		failures.append("%s: inspector should preserve detailed bundle status" % label)
	if camera_status_text.find("LIVE_3D_EXTERNAL_DIAGRAM_VIEW") == -1 or camera_status_text.find("above") == -1:
		failures.append("%s: inspector should expose Live 3D camera preset diagnostics" % label)
	if viewport_hint_text.find("Quick") == -1 or viewport_hint_text.find("Space") == -1 or viewport_hint_text.find("Play / Pause") == -1:
		failures.append("%s: viewport should expose structured replay quick keycap/action hints" % label)
	if bottom_hint_text.find("Quick") == -1 or bottom_hint_text.find("Q/Esc") == -1 or bottom_hint_text.find("Quit") == -1:
		failures.append("%s: bottom controls should expose structured replay quick keycap/action hints" % label)
	if game_area_panel_color != snapshot.get("board_background_color", Color.TRANSPARENT):
		failures.append("%s: game area shell should use board background colour" % label)
	if game_area_border_color == Color.TRANSPARENT:
		failures.append("%s: game area shell should expose a grid border colour" % label)
	if bottom_bar_border_color == Color.TRANSPARENT:
		failures.append("%s: bottom replay controls should expose a cockpit border colour" % label)
	var game_viewport: SubViewport = hud.game_viewport()
	if game_viewport == null:
		failures.append("%s: HUD should expose a game SubViewport" % label)
	elif game_viewport.get_node_or_null("WorldRoot") == null:
		failures.append("%s: WorldRoot should live inside HUD game SubViewport" % label)
	return failures


func _check_live_4d_cockpit_contract(hud: Node, viewport_size: Vector2i, replay_game_width: float) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var label := "live 4D viewport %s" % str(viewport_size)
	var viewport_hint_text := str(snapshot.get("viewport_hint_text", ""))
	var viewport_detail_text := str(snapshot.get("viewport_detail_text", ""))
	var bottom_hint_text := str(snapshot.get("bottom_hint_text", ""))
	var inspector_hint_text := str(snapshot.get("inspector_hint_text", ""))
	var top_status_badge_text := str(snapshot.get("top_status_badge_text", ""))
	var top_summary_text := str(snapshot.get("top_summary_text", ""))
	var restart_game_button_visible := bool(snapshot.get("restart_game_button_visible", false))
	var restart_game_button_text := str(snapshot.get("restart_game_button_text", ""))
	var top_detail_text := str(snapshot.get("top_detail_text", ""))
	var authority_text := str(snapshot.get("authority_text", ""))
	var inspector_status_text := str(snapshot.get("inspector_status_text", ""))
	var bottom_bar_visible := bool(snapshot.get("bottom_bar_visible", true))
	var viewport_hints_visible := bool(snapshot.get("viewport_hints_visible", true))
	var left_panel_visible := bool(snapshot.get("left_panel_visible", true))
	var left_panel_text := str(snapshot.get("left_panel_text", ""))
	var right_inspector_order: Array = snapshot.get("right_inspector_order", [])
	var game_rect: Rect2 = snapshot.get("game_area", Rect2())
	var inspector_rect: Rect2 = snapshot.get("right_inspector", Rect2())
	if authority_text.find("Native C++ owns gameplay") != -1 or inspector_status_text.find("Native C++ owns gameplay") != -1:
		failures.append("%s: broad native gameplay ownership wording should not appear" % label)
	if authority_text.find("Live Plain 4D") == -1 or authority_text.find("C++ PlainNDSession") == -1 or authority_text.find("Godot shell") == -1:
		failures.append("%s: authority wording should be scoped to the Live Plain 4D C++ session" % label)
	if top_detail_text != "" or viewport_detail_text.find("Godot command/render shell") != -1:
		failures.append("%s: live shell detail should not dangle in top or viewport chrome" % label)
	if top_status_badge_text.find("[ GAME OVER ]") == -1 or top_status_badge_text.find("Piece out of bounds") == -1:
		failures.append("%s: top status badge should expose user-facing game-over reason" % label)
	if not restart_game_button_visible or restart_game_button_text != "Restart Game":
		failures.append("%s: live game-over status should expose a Restart Game button" % label)
	if top_status_badge_text.find("out_of_bounds") != -1 or top_summary_text.find("out_of_bounds") != -1 or inspector_status_text.find("out_of_bounds") != -1:
		failures.append("%s: user-facing live status should not expose raw out_of_bounds reason" % label)
	if inspector_status_text.find("SESSION") == -1 or inspector_status_text.find("STATUS") == -1 or inspector_status_text.find("VIEW") == -1:
		failures.append("%s: inspector should use structured sections" % label)
	if inspector_status_text.find("Mode        Live Plain 4D") == -1 or inspector_status_text.find("Engine      C++ PlainNDSession") == -1:
		failures.append("%s: inspector should expose aligned session rows" % label)
	if inspector_status_text.find("Reason      Piece out of bounds") == -1:
		failures.append("%s: inspector should expose user-facing game-over reason" % label)
	if viewport_hints_visible or viewport_hint_text != "":
		failures.append("%s: central board should not repeat partial Live 4D quick controls" % label)
	if bottom_bar_visible or bottom_hint_text != "":
		failures.append("%s: live bottom controls should be hidden or reduced without repeated hints" % label)
	if bottom_hint_text.find("Quit Replay") != -1 or viewport_hint_text.find("Quit Replay") != -1 or left_panel_text.find("Replay Cases") != -1:
		failures.append("%s: Live 4D mode should not show Quit Replay wording" % label)
	if left_panel_visible:
		failures.append("%s: Live 4D mode should hide the Replay Cases side panel" % label)
	if inspector_hint_text.find("Movement") == -1 or inspector_hint_text.find("Plane Rotation") == -1 or inspector_hint_text.find("Camera") == -1 or inspector_hint_text.find("Mouse Camera") == -1 or inspector_hint_text.find("System") == -1:
		failures.append("%s: inspector should expose full grouped Live 4D controls" % label)
	for required in ["A / D", "W / S", "Q / E", "R / T", "F / G", "V / B", "Y / U", "H / J", "N / M", "I / K", "O / L", ", / .", "- / = / +", "Drag", "Shift Drag", "Wheel", "Double-click", "Backspace", "Esc", "Fit View"]:
		if inspector_hint_text.find(required) == -1:
			failures.append("%s: Live 4D full controls should include %s" % [label, required])
	if inspector_hint_text.find("Left: CCW") == -1 or inspector_hint_text.find("Right: CW") == -1:
		failures.append("%s: Live 4D rotation controls should include a section-level CCW/CW hint" % label)
	if inspector_hint_text.find("Move:") != -1 or inspector_hint_text.find("Rotate:") != -1:
		failures.append("%s: common controls should not collapse into prose hint strings" % label)
	if inspector_hint_text.find("Rotate XY") != -1 or inspector_hint_text.find("Rotate XZ") != -1:
		failures.append("%s: rotation rows should avoid repeated Rotate wording" % label)
	if inspector_rect.size.x <= 0.0:
		failures.append("%s: right inspector should remain visible" % label)
	if game_rect.size.x <= inspector_rect.size.x:
		failures.append("%s: game area should remain larger than the inspector column, game=%s inspector=%s" % [label, game_rect, inspector_rect])
	if replay_game_width > 0.0 and game_rect.size.x <= replay_game_width + 0.5:
		failures.append("%s: live game area should gain width after hiding the left replay panel, live=%s replay=%s" % [label, game_rect.size.x, replay_game_width])
	if right_inspector_order.size() < 2 or str(right_inspector_order[0]) != "InspectorSectionHeader__CONTROLS" or str(right_inspector_order[1]) != "InspectorControlHints":
		failures.append("%s: live right inspector should present controls before diagnostics/settings, order=%s" % [label, str(right_inspector_order)])
	return failures


func _check_live_control_maps() -> Array:
	var failures: Array = []
	var live_4d_groups := ReplayHud.live_4d_control_hint_groups()
	var group_names: Array = []
	var flattened := ""
	for group in live_4d_groups:
		group_names.append(str(group.get("group", "")))
		for item in group.get("items", []):
			flattened += "%s %s\n" % [str(item[0]), str(item[1])]
	for required_group in ["Movement", "Plane Rotation", "Camera", "Mouse Camera", "System"]:
		if not group_names.has(required_group):
			failures.append("Live 4D controls should include %s group" % required_group)
	for required in ["A / D", "W / S", "Q / E", "R / T", "F / G", "V / B", "Y / U", "H / J", "N / M", "I / K", "O / L", ", / .", "- / = / +", "Drag", "Shift Drag", "Wheel", "Double-click"]:
		if flattened.find(required) == -1:
			failures.append("Live 4D control map should include %s" % required)
	var group_items := {}
	var group_notes := {}
	for group in live_4d_groups:
		group_items[str(group.get("group", ""))] = group.get("items", [])
		group_notes[str(group.get("group", ""))] = str(group.get("note", ""))
	_assert_group_items(
		failures,
		group_items,
		"Movement",
		[["A / D", "X- / X+"], ["W / S", "Z+ / Z-"], ["Q / E", "W- / W+"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"Plane Rotation",
		[["R / T", "XY"], ["F / G", "XZ"], ["V / B", "YZ"], ["Y / U", "XW"], ["H / J", "YW"], ["N / M", "ZW"]]
	)
	if str(group_notes.get("Plane Rotation", "")).find("Left: CCW") == -1 or str(group_notes.get("Plane Rotation", "")).find("Right: CW") == -1:
		failures.append("Live 4D rotation group should include one section-level CCW/CW note")
	for item in group_items.get("Plane Rotation", []):
		if str(item[1]).find("Rotate") != -1:
			failures.append("Live 4D rotation row should not repeat Rotate wording: %s" % str(item))
	_assert_group_items(
		failures,
		group_items,
		"Camera",
		[["I / K", "Pitch up / down"], ["O / L", "Yaw left / right"], [", / .", "Roll left / right"], ["- / = / +", "Zoom out / in"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"Mouse Camera",
		[["Drag", "Orbit"], ["Shift Drag", "Roll"], ["Wheel", "Zoom"], ["Double-click", "Fit View"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"System",
		[["P", "Pause"], ["Backspace", "Reset"], ["Esc", "Back / Quit"], ["Fit View", "Fit View"]]
	)
	if not ReplayHud.quick_control_hint_groups("live_4d").is_empty():
		failures.append("Live 4D should not expose a partial quick-control map")
	return failures


func _assert_group_items(failures: Array, group_items: Dictionary, group_name: String, expected_items: Array) -> void:
	var actual_items: Array = group_items.get(group_name, [])
	if actual_items.size() != expected_items.size():
		failures.append("%s controls should have %d compact rows, got %d" % [group_name, expected_items.size(), actual_items.size()])
		return
	for index in range(expected_items.size()):
		if str(actual_items[index][0]) != str(expected_items[index][0]) or str(actual_items[index][1]) != str(expected_items[index][1]):
			failures.append("%s controls row %d should be %s, got %s" % [group_name, index, str(expected_items[index]), str(actual_items[index])])


func _contains_rect(container: Rect2, child: Rect2) -> bool:
	return (
		child.position.x >= container.position.x - 0.5
		and child.position.y >= container.position.y - 0.5
		and child.end.x <= container.end.x + 0.5
		and child.end.y <= container.end.y + 0.5
	)
