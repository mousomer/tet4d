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
		hud.set_camera_status("View: ortho · size 16.00 · zoom 1.00x · outer view · yaw 32 deg · pitch above 26 deg · roll 0 deg · fit OK")
		await tree.process_frame
		failures.append_array(_check_layout(hud, viewport_size))
		failures.append_array(await _check_keyboard_hint_visibility_setting(hud))
		var replay_snapshot: Dictionary = hud.layout_contract_snapshot()
		var replay_game_rect: Rect2 = replay_snapshot.get("game_area", Rect2())
		if bool(replay_snapshot.get("next_piece_panel", {}).get("visible", true)):
			failures.append("replay mode must not expose the live NEXT panel")
		hud.set_next_piece_preview({
			"ok": true,
			"status": "piece",
			"dimension": 4,
			"piece_set_id": "standard_4d_5",
			"piece_name": "CROSS4",
			"color_id": 1,
			"cells": [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
		})
		hud.set_live_4d_mode(false, true, "move_w_negative", "out_of_bounds", 0.5)
		hud.set_snapshot({
			"trace_type": "live_4d",
			"dimension": 4,
			"board_shape": [5, 10, 4, 4],
			"piece_set_id": "standard_4d_5",
			"effective_seed": 1337,
			"score": 45,
			"lines": 1,
			"initial_speed_level": 1,
			"paused": false,
			"game_over": true,
			"game_over_reason": "out_of_bounds",
			"current_piece": {"name": "CROSS4"},
			"next_piece": {"name": "STAIR4"},
			"last_command": "move_w_negative",
			"last_command_status": "locked",
		}, true)
		await tree.process_frame
		var terminal_preview: Dictionary = hud.layout_contract_snapshot().get("next_piece_panel", {})
		if terminal_preview.get("piece_name_text") != "CROSS4":
			failures.append("ordinary game over should retain the last authoritative NEXT preview")
		var geometry_revision := int(terminal_preview.get("thumbnail", {}).get("geometry_revision", -1))
		hud.set_live_4d_basis_snapshot({
			"text": "View: +W · +Y · +Z\nSlice: -X · Gravity: Y down",
			"slice_axis": "x",
		})
		var basis_preview: Dictionary = hud.layout_contract_snapshot().get("next_piece_panel", {})
		if int(basis_preview.get("thumbnail", {}).get("geometry_revision", -2)) != geometry_revision or basis_preview.get("piece_name_text") != "CROSS4":
			failures.append("Stage 54C basis changes must not rebuild or reorient canonical NEXT geometry")
		if str(hud.layout_contract_snapshot().get("top_summary_title", "")) != "Live Session":
			failures.append("live 4D must not retain the Replay summary heading")
		hud._apply_hud_density("standard")
		hud._set_keyboard_hints_visible(true)
		await tree.process_frame
		failures.append_array(_check_live_4d_cockpit_contract(hud, viewport_size, replay_game_rect.size.x))
		failures.append_array(await _check_live_mode_progression(hud, viewport_size))
		failures.append_array(await _check_true_random_action_layout(hud, viewport_size))
		hud.set_replay_mode_labels(false, 1.0, false)
		await tree.process_frame
		var restored_snapshot: Dictionary = hud.layout_contract_snapshot()
		if str(restored_snapshot.get("top_summary_title", "")) != "Replay":
			failures.append("replay mode should restore the Replay summary heading")
		if str(restored_snapshot.get("bundle_status_text", "")).find("Bundle: OK") == -1:
			failures.append("replay mode should restore bundle status after live mode")
		if bool(restored_snapshot.get("next_piece_panel", {}).get("visible", true)):
			failures.append("returning to replay must hide the NEXT panel")
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
	if not camera_status_text.begins_with("View:") or camera_status_text.find("above") == -1 or camera_status_text.find("Camera:") != -1:
		failures.append("%s: inspector should expose numeric view diagnostics without preset identity" % label)
	if viewport_hint_text.find("Quick") == -1 or viewport_hint_text.find("Space") == -1 or viewport_hint_text.find("Play / Pause") == -1:
		failures.append("%s: viewport should expose structured replay quick keycap/action hints" % label)
	if bottom_hint_text.find("Quick") == -1 or bottom_hint_text.find("Esc") == -1 or bottom_hint_text.find("Main Menu") == -1:
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


func _check_true_random_action_layout(hud: Node, viewport_size: Vector2i) -> Array:
	var failures: Array = []
	hud.set_snapshot({
		"trace_type": "live_4d",
		"random_mode": "true_random",
		"paused": false,
		"game_over": false,
		"last_command": "none",
		"last_command_status": "none",
		"state_hash": "manual-layout",
	}, false)
	await Engine.get_main_loop().process_frame
	var snapshot: Dictionary = hud.layout_contract_snapshot()
	var button_rect: Rect2 = snapshot.get("new_random_game_button_rect", Rect2())
	var body_rect: Rect2 = snapshot.get("body", Rect2())
	if not bool(snapshot.get("new_random_game_button_visible", false)):
		failures.append("live 4D viewport %s: true-random setup should expose New Random Game" % str(viewport_size))
	if button_rect.size.x <= 0.0 or button_rect.end.y > body_rect.position.y + 0.5:
		failures.append("live 4D viewport %s: visible New Random Game action should fit above the live body, button=%s body=%s" % [str(viewport_size), button_rect, body_rect])
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
	var restart_game_button_rect: Rect2 = snapshot.get("restart_game_button_rect", Rect2())
	var change_setup_button_visible := bool(snapshot.get("change_setup_button_visible", false))
	var change_setup_button_rect: Rect2 = snapshot.get("change_setup_button_rect", Rect2())
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
	var body_rect: Rect2 = snapshot.get("body", Rect2())
	var status_badge_color: Color = snapshot.get("top_status_badge_color", Color.TRANSPARENT)
	var status_badge_border_color: Color = snapshot.get("top_status_badge_border_color", Color.TRANSPARENT)
	var style_manager = hud.style_manager()
	if bool(snapshot.get("top_bundle_panel_visible", true)) or bool(snapshot.get("top_authority_panel_visible", true)):
		failures.append("%s: ordinary live play must hide replay bundle and implementation-authority chrome" % label)
	if bool(snapshot.get("integrity_panel_visible", true)) or bool(snapshot.get("bundle_detail_panel_visible", true)):
		failures.append("%s: ordinary live play must hide raw session/bundle diagnostics" % label)
	if authority_text.find("C++ PlainNDSession") == -1 or inspector_status_text.find("Engine      C++ PlainNDSession") == -1:
		failures.append("%s: hidden diagnostic routes should retain scoped implementation evidence" % label)
	if top_detail_text != "" or viewport_detail_text.find("Godot command/render shell") != -1:
		failures.append("%s: live shell detail should not dangle in top or viewport chrome" % label)
	if top_status_badge_text.find("[ GAME OVER ]") == -1 or top_status_badge_text.find("Piece out of bounds") == -1:
		failures.append("%s: top status badge should expose user-facing game-over reason" % label)
	if status_badge_color != style_manager.get_color("state.error") or status_badge_border_color != style_manager.get_color("state.error"):
		failures.append("%s: game-over status badge should use error styling" % label)
	if not restart_game_button_visible or restart_game_button_text != "Restart Game":
		failures.append("%s: live game-over status should expose a Restart Game button" % label)
	if restart_game_button_rect.size.x <= 0.0 or restart_game_button_rect.end.y > body_rect.position.y + 0.5:
		failures.append("%s: visible Restart Game action should fit above the live body, button=%s body=%s" % [label, restart_game_button_rect, body_rect])
	if not change_setup_button_visible or change_setup_button_rect.size.x <= 0.0 or change_setup_button_rect.end.y > body_rect.position.y + 0.5:
		failures.append("%s: visible Change Setup action should fit above the live body, button=%s body=%s" % [label, change_setup_button_rect, body_rect])
	if top_status_badge_text.find("out_of_bounds") != -1 or top_summary_text.find("out_of_bounds") != -1 or inspector_status_text.find("out_of_bounds") != -1:
		failures.append("%s: user-facing live status should not expose raw out_of_bounds reason" % label)
	if top_summary_text.find("SCORE") == -1 or top_summary_text.find("CLEARS") == -1 or top_summary_text.find("Active") == -1:
		failures.append("%s: concise live summary should expose score, clears, and active piece" % label)
	for diagnostic_copy in ["C++ PlainNDSession", "Godot shell", "Seed", "Topology", "Last input"]:
		if top_summary_text.find(diagnostic_copy) != -1:
			failures.append("%s: ordinary live summary should omit %s" % [label, diagnostic_copy])
	if viewport_hints_visible or viewport_hint_text != "":
		failures.append("%s: central board should not repeat partial Live 4D quick controls" % label)
	if bottom_bar_visible or bottom_hint_text != "":
		failures.append("%s: live bottom controls should be hidden or reduced without repeated hints" % label)
	if bottom_hint_text.find("Quit Replay") != -1 or viewport_hint_text.find("Quit Replay") != -1 or left_panel_text.find("Replay Cases") != -1:
		failures.append("%s: Live 4D mode should not show Quit Replay wording" % label)
	if left_panel_visible:
		failures.append("%s: Live 4D mode should hide the Replay Cases side panel" % label)
	if inspector_hint_text.find("Piece movement") == -1 or inspector_hint_text.find("Piece rotation") == -1 or inspector_hint_text.find("Slice orientation") == -1 or inspector_hint_text.find("Framing") == -1 or inspector_hint_text.find("Pointer") == -1 or inspector_hint_text.find("Session") == -1:
		failures.append("%s: inspector should expose mode-appropriate grouped Live 4D guidance" % label)
	for required in ["A / D", "W / S", "Q / E", "R / T", "F / G", "V / B", "Y / U", "H / J", "N / M", "I / K", "O / L", "- / = / +", "Left Drag", "Right Drag", "Wheel", "P"]:
		if inspector_hint_text.find(required) == -1:
			failures.append("%s: Live 4D cockpit guidance should include %s" % [label, required])
	for duplicated in ["90° View Rotation", "Reset View", "Fit View", "Restart Game", "Navigation", "Backspace", "Tab", "Esc"]:
		if inspector_hint_text.find(duplicated) != -1:
			failures.append("%s: visible action families should keep %s out of passive cockpit help" % [label, duplicated])
	if inspector_hint_text.find("Roll left / right") != -1:
		failures.append("%s: normal Live 4D controls must not advertise gameplay roll" % label)
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
	for required_surface in ["PiecePreviewRow", "LivePieceControlStrip", "Live4DBasisPanel", "InspectorSectionHeader__VIEW", "InspectorCameraPanel", "InspectorControlHints"]:
		if not right_inspector_order.has(required_surface):
			failures.append("%s: live right inspector should retain %s, order=%s" % [label, required_surface, str(right_inspector_order)])
	if (
		right_inspector_order.find("PiecePreviewRow") > right_inspector_order.find("LivePieceControlStrip")
		or right_inspector_order.find("LivePieceControlStrip") > right_inspector_order.find("Live4DBasisPanel")
		or right_inspector_order.find("Live4DBasisPanel") > right_inspector_order.find("InspectorCameraPanel")
	):
		failures.append("%s: preview, piece controls, basis, and camera guidance must follow gameplay priority, order=%s" % [label, str(right_inspector_order)])
	var next_piece_panel: Dictionary = snapshot.get("next_piece_panel", {})
	if not bool(next_piece_panel.get("visible", false)) or next_piece_panel.get("piece_name_text") != "CROSS4":
		failures.append("%s: live right inspector should expose the authoritative NEXT piece" % label)
	if float(next_piece_panel.get("minimum_height", 0.0)) > inspector_rect.size.y:
		failures.append("%s: NEXT panel should remain bounded within the scrollable inspector viewport" % label)
	var hold_piece_panel: Dictionary = snapshot.get("hold_piece_panel", {})
	if not bool(hold_piece_panel.get("visible", false)) or hold_piece_panel.get("piece_name_text") != "EMPTY" or hold_piece_panel.get("status_text") != "Available · C":
		failures.append("%s: live right inspector should expose intentional authoritative HOLD state" % label)
	if float(hold_piece_panel.get("minimum_height", 0.0)) > inspector_rect.size.y:
		failures.append("%s: HOLD panel should remain bounded within the scrollable inspector viewport" % label)
	var view_actions := hud.find_child("CockpitButtonPanel", true, false) as Control
	var live_view_row := hud.find_child("LiveViewActions", true, false) as Control
	var quick_settings := hud.find_child("QuickSettingsToggle", true, false) as Button
	var grid_toggle := hud.find_child("GridVisibilityToggle", true, false) as Button
	if view_actions == null or not view_actions.visible or view_actions.get_meta("semantic_role", "") != "interactive_button_panel":
		failures.append("%s: live navigation should expose persistent action buttons" % label)
	if not bool(snapshot.get("live_fit_view_button_visible", false)) or not bool(snapshot.get("live_reset_view_button_visible", false)):
		failures.append("%s: live View family should expose distinct Fit View and Reset View actions" % label)
	if not bool(snapshot.get("camera_panel_visible", false)) or bool(snapshot.get("camera_status_visible", true)):
		failures.append("%s: Standard live HUD should expose compact camera guidance without numeric camera diagnostics" % label)
	if not bool(snapshot.get("view_action_menu_visible", false)) or str(snapshot.get("view_action_menu_text", "")) != "View Actions" or str(snapshot.get("view_action_menu_parent", "")) != "SecondaryViewControls":
		failures.append("%s: Live 4D should expose stateless View Actions below primary piece controls" % label)
	if quick_settings == null or quick_settings.text.find("Quick Settings") == -1:
		failures.append("%s: action row should expose a discoverable Quick Settings toggle" % label)
	elif quick_settings.text == "Show Quick Settings":
		quick_settings.pressed.emit()
		if quick_settings.text != "Hide Quick Settings":
			failures.append("%s: Quick Settings action should expose and report the detailed inspector" % label)
		quick_settings.pressed.emit()
	if grid_toggle == null or grid_toggle.text != "Grid: On":
		failures.append("%s: action row should expose the current grid state" % label)
	else:
		grid_toggle.pressed.emit()
		if grid_toggle.text != "Grid: Off":
			failures.append("%s: grid action should report the hidden-detail state" % label)
		grid_toggle.pressed.emit()
	if quick_settings != null and (quick_settings.get_parent() != live_view_row or quick_settings.get_meta("semantic_role", "") != "action_button" or quick_settings.get_theme_stylebox("normal") == null):
		failures.append("%s: Quick Settings should be an unmistakable styled action button" % label)
	if grid_toggle != null and (grid_toggle.get_parent() != live_view_row or grid_toggle.get_meta("semantic_role", "") != "action_button" or grid_toggle.get_theme_stylebox("normal") == null):
		failures.append("%s: Grid should be an unmistakable styled action button" % label)
	if live_view_row == null:
		failures.append("%s: live cockpit should keep one compact recovery/display row" % label)
	return failures


func _check_live_mode_progression(hud: Node, viewport_size: Vector2i) -> Array:
	var failures: Array = []
	hud.set_control_frame_snapshot({
		"translation_frame": "relative",
		"rotation_frame": "relative",
		"horizontal_axis": "+X",
		"depth_axis": "+Z",
		"slice_axis": "+W",
	})
	hud._apply_hud_density("standard")
	hud._set_keyboard_hints_visible(true)
	hud.set_live_2d_mode(false, false, "none")
	await Engine.get_main_loop().process_frame
	var two_d: Dictionary = hud.layout_contract_snapshot()
	var two_d_hints := str(two_d.get("inspector_hint_text", ""))
	if bool(two_d.get("view_action_menu_visible", true)) or bool(two_d.get("basis_panel_visible", true)) or not bool(two_d.get("camera_panel_visible", false)) or bool(two_d.get("camera_status_visible", true)):
		failures.append("live 2D viewport %s: named views, basis, and numeric diagnostics must be absent while secondary Reset remains available" % str(viewport_size))
	for leaked_copy in ["Forward / Back", "Slice", "View gestures", "90° View Rotation"]:
		if two_d_hints.find(leaked_copy) != -1:
			failures.append("live 2D viewport %s: cockpit must not leak %s" % [str(viewport_size), leaked_copy])
	if two_d_hints.find("Piece movement") == -1 or two_d_hints.find("Piece rotation") == -1 or two_d_hints.find("Drop") == -1:
		failures.append("live 2D viewport %s: minimal gameplay guidance must remain visible" % str(viewport_size))

	hud.set_live_3d_mode(false, false, "none")
	await Engine.get_main_loop().process_frame
	var three_d: Dictionary = hud.layout_contract_snapshot()
	var three_d_hints := str(three_d.get("inspector_hint_text", ""))
	if not bool(three_d.get("view_action_menu_visible", false)) or str(three_d.get("view_action_menu_parent", "")) != "SecondaryViewControls":
		failures.append("live 3D viewport %s: stateless View Actions must remain available below piece controls" % str(viewport_size))
	if bool(three_d.get("basis_panel_visible", true)) or not bool(three_d.get("camera_panel_visible", false)) or bool(three_d.get("camera_status_visible", true)):
		failures.append("live 3D viewport %s: 4D basis and Standard numeric camera diagnostics must stay hidden while compact view guidance remains" % str(viewport_size))
	for required_copy in ["Forward / Back", "Forward recedes and Back approaches", "View gestures", "Left Drag", "Right Drag", "Wheel"]:
		if three_d_hints.find(required_copy) == -1:
			failures.append("live 3D viewport %s: cockpit should explain %s" % [str(viewport_size), required_copy])
	if three_d_hints.find("Slice") != -1 or three_d_hints.find("W−") != -1:
		failures.append("live 3D viewport %s: 4D slice concepts must stay hidden" % str(viewport_size))

	var popup := hud._camera_view_action_menu.get_popup() as PopupMenu
	popup.popup()
	await Engine.get_main_loop().process_frame
	if not hud.live_interaction_owns_input():
		failures.append("live 3D View Actions popup must own keyboard input while open")
	popup.hide()
	await Engine.get_main_loop().process_frame
	if hud.live_interaction_owns_input():
		failures.append("closing View Actions must restore ordinary live input ownership")

	hud._apply_hud_density("compact")
	await Engine.get_main_loop().process_frame
	var compact: Dictionary = hud.layout_contract_snapshot()
	if bool(compact.get("controls_panel_visible", true)) or not bool(compact.get("next_piece_panel", {}).get("visible", false)) or not bool(compact.get("live_view_actions_visible", false)) or not bool(compact.get("piece_control_strip", {}).get("visible", false)):
		failures.append("live compact density must reduce detailed help while retaining NEXT, piece controls, and action families")
	hud._apply_hud_density("detailed")
	await Engine.get_main_loop().process_frame
	var detailed: Dictionary = hud.layout_contract_snapshot()
	if not bool(detailed.get("camera_panel_visible", false)) or bool(detailed.get("integrity_panel_visible", true)) or bool(detailed.get("bundle_detail_panel_visible", true)):
		failures.append("live detailed density should add view detail without restoring engine/bundle diagnostics")
	hud._apply_hud_density("standard")
	return failures


func _check_keyboard_hint_visibility_setting(hud: Node) -> Array:
	var failures: Array = []
	hud._set_keyboard_hints_visible(false)
	await Engine.get_main_loop().process_frame
	var replay_hidden: Dictionary = hud.layout_contract_snapshot()
	if bool(replay_hidden.get("viewport_hints_visible", true)) or bool(replay_hidden.get("bottom_hints_visible", true)):
		failures.append("keyboard hint setting should hide replay hint strips")
	hud.set_live_4d_mode(false, false, "none", "", 0.5)
	await Engine.get_main_loop().process_frame
	hud._set_keyboard_hints_visible(false)
	hud.set_replay_mode_labels(false, 1.0, false)
	await Engine.get_main_loop().process_frame
	var replay_restored_hidden: Dictionary = hud.layout_contract_snapshot()
	if bool(replay_restored_hidden.get("viewport_hints_visible", true)) or bool(replay_restored_hidden.get("bottom_hints_visible", true)):
		failures.append("live-mode declutter should not forget hidden keyboard hints")
	hud._set_keyboard_hints_visible(true)
	await Engine.get_main_loop().process_frame
	var replay_visible: Dictionary = hud.layout_contract_snapshot()
	if not bool(replay_visible.get("viewport_hints_visible", false)) or not bool(replay_visible.get("bottom_hints_visible", false)):
		failures.append("keyboard hint setting should restore replay hint strips")
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
	for required_group in ["Piece movement", "Piece rotation", "90° View Rotation", "Drop", "Slice orientation", "Framing", "Pointer", "Session", "Navigation"]:
		if not group_names.has(required_group):
			failures.append("Live 4D controls should include %s group" % required_group)
	for required in ["A / D", "W / S", "Q / E", "R / T", "F / G", "V / B", "Y / U", "H / J", "N / M", "I / K", "O / L", "- / = / +", "Left Drag", "Right Drag", "Wheel"]:
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
		"Piece movement",
		[["A / D", "Visible X - / +"], ["W / S", "Visible Z - / +"], ["Q / E", "Slice W - / +"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"90° View Rotation",
		[["1 / 2", "XW - / + (re-slice)"], ["; / '", "ZW - / + (re-slice)"], ["[ / ]", "ZX - / +"], ["0", "Reset View (basis, slice orientation, framing)"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"Piece rotation",
		[["R / T", "XY"], ["F / G", "XZ"], ["V / B", "YZ"], ["Y / U", "XW"], ["H / J", "YW"], ["N / M", "ZW"]]
	)
	if str(group_notes.get("Piece rotation", "")).find("Left: CCW") == -1 or str(group_notes.get("Piece rotation", "")).find("Right: CW") == -1:
		failures.append("Live 4D rotation group should include one section-level CCW/CW note")
	for item in group_items.get("Piece rotation", []):
		if str(item[1]).find("Rotate") != -1:
			failures.append("Live 4D rotation row should not repeat Rotate wording: %s" % str(item))
	_assert_group_items(
		failures,
		group_items,
		"Slice orientation",
		[["I / K", "Pitch up / down"], ["O / L", "Yaw left / right"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"Framing",
		[["- / = / +", "Zoom out / in"], ["Double-click", "Fit View (framing only)"]]
	)
	_assert_group_items(
		failures,
		group_items,
		"Pointer",
		[["Left Drag", "Orient slices"], ["Right Drag", "Translate framing"], ["Wheel", "Zoom"]]
	)
	_assert_group_items(failures, group_items, "Drop", [["Ctrl", "Soft Drop"], ["Space", "Hard Drop"]])
	_assert_group_items(
		failures,
		group_items,
		"Session",
		[["P", "Pause"], ["Backspace", "Restart Game"]]
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
