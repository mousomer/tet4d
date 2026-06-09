extends Control

class_name ReplayHud

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const CaseBrowserScript = preload("res://scripts/ui/case_browser.gd")
const DiagnosticsPanelScript = preload("res://scripts/ui/diagnostics_panel.gd")
const EventListPanelScript = preload("res://scripts/ui/event_list_panel.gd")
const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")

signal trace_family_selected(trace_type: String)
signal case_selected(case_id: String)
signal previous_frame_requested()
signal next_frame_requested()
signal play_pause_requested()
signal reset_requested()
signal frame_scrub_requested(frame_index: int)
signal playback_speed_changed(value: float)
signal diagnostics_visibility_changed(visible: bool)
signal display_mode_changed(mode: String)
signal fit_view_requested()
signal quit_requested()
signal replay_mode_requested()
signal live_2d_requested()
signal live_3d_requested()

const SCREEN_MAIN_MENU := "main_menu"
const SCREEN_BROWSER := "browser"
const SCREEN_VIEWER := "viewer"
const SCREEN_SETTINGS := "settings"
const SCREEN_CONTROLS := "controls"
const SCREEN_DIAGNOSTICS := "diagnostics"
const REPLAY_HINT_TEXT := "Space Play/Pause Replay · ←/→ Frame · ↑/↓ Case · 1/2/3 Family · F Fit · H Help · Tab Live 2D · Q/Esc Quit"
const REPLAY_HELP_TEXT := "Replay controls only: Space toggles replay playback, arrows browse exported frames/cases, 1/2/3 switch trace families, F fits the current trace bounds, Q quits the replay shell. These controls do not move gameplay pieces."
const LIVE_2D_HINT_TEXT := "A/D or ←/→ Move · W/↑/X Rotate · Z Rotate CCW · S/↓ Soft Drop · Space Hard Drop · P Pause · R Reset · F Fit · Tab Live 3D · Q/Esc Quit"
const LIVE_2D_HELP_TEXT := "Live 2D controls only: A/D or arrows move, W/Up/X rotates clockwise, Z rotates counter-clockwise, S/Down soft drops, Space hard drops, P pauses, R resets, F fits the board, Tab switches to Live 3D, and Q/Esc quits. Godot sends commands only."
const LIVE_3D_HINT_TEXT := "A/D or ←/→ X Move · W/S or ↑/↓ Z Move · Shift Soft Drop · Space Hard Drop · R/T: XY Rotate · F/G: XZ Rotate · V/B: YZ Rotate · P Pause · Backspace Reset · Tab Replay · Q/Esc Quit"
const LIVE_3D_HELP_TEXT := "Live 3D controls only: A/D or arrows move on X, W/S or Up/Down move on Z, Shift soft drops, Space hard drops, R/T rotates XY, F/G rotates XZ, V/B rotates YZ, P pauses, Backspace resets, Tab returns to Replay, and Q/Esc quits. Godot sends commands only."

var _bundle_status_label: Label
var _summary_label: Label
var _authority_label: Label
var _case_browser: CaseBrowser
var _diagnostics_panel: DiagnosticsPanel
var _event_panel: EventListPanel
var _diagnostics_screen_panel: DiagnosticsPanel
var _event_screen_panel: EventListPanel
var _settings_panel: SettingsPanel
var _settings_screen_panel: SettingsPanel
var _play_button: Button
var _reset_button: Button
var _hint_label: Label
var _mode_hint_strip: Label
var _viewport_title: Label
var _viewport_hint: Label
var _frame_slider: HSlider
var _frame_label: Label
var _hash_label: Label
var _speed_select: OptionButton
var _speed_value: Label
var _viewport_frame: PanelContainer
var _body_container: HBoxContainer
var _left_panel: PanelContainer
var _viewer_case_browser: CaseBrowser
var _game_area: PanelContainer
var _game_viewport_container: SubViewportContainer
var _game_viewport: SubViewport
var _right_scroll: ScrollContainer
var _right_column: VBoxContainer
var _bottom_panel: PanelContainer
var _top_status_panel: PanelContainer
var _authority_panel: PanelContainer
var _main_menu_screen: Control
var _browser_screen: Control
var _viewer_screen: Control
var _settings_screen: Control
var _controls_screen: Control
var _diagnostics_screen: Control
var _screens: Dictionary = {}
var _replay_note: Label
var _help_panel: PanelContainer
var _trace_integrity_label: Label
var _help_label: Label
var _current_display_mode := ReplayVisuals.default_display_mode()
var _current_screen := SCREEN_MAIN_MENU
var _geometry_diagnostics_enabled := false
var _live_2d_paused := false
var _live_2d_game_over := false
var _live_3d_paused := false
var _live_3d_game_over := false


static func replay_hint_text() -> String:
	return REPLAY_HINT_TEXT


static func live_2d_hint_text() -> String:
	return LIVE_2D_HINT_TEXT


static func live_3d_hint_text() -> String:
	return LIVE_3D_HINT_TEXT


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_PASS
	theme = ReplayVisuals.build_theme(_current_display_mode)
	_build_layout()
	call_deferred("_log_geometry_diagnostics", "ready")


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED and is_inside_tree():
		call_deferred("_log_geometry_diagnostics", "resize")


func set_bundle_status(text: String) -> void:
	_bundle_status_label.text = text


func set_trace_families(families: Array, selected: String) -> void:
	if _case_browser != null:
		_case_browser.set_trace_families(families, selected)
	if _viewer_case_browser != null:
		_viewer_case_browser.set_trace_families(families, selected)


func set_cases(cases: Array, selected_case_id: String) -> void:
	if _case_browser != null:
		_case_browser.set_cases(cases, selected_case_id)
	if _viewer_case_browser != null:
		_viewer_case_browser.set_cases(cases, selected_case_id)


func set_summary(trace_type: String, case_id: String, dimension: int, frame_index: int, next_frame_index: int, frame_count: int, state_hash: String) -> void:
	_summary_label.text = "%s  •  %s  •  %dD  •  next %d" % [
		trace_type,
		case_id,
		dimension,
		next_frame_index,
	]
	_frame_label.text = "Frame %d / %d" % [frame_index, max(frame_count - 1, 0)]
	_hash_label.text = "state %s" % state_hash.left(16)
	_frame_slider.max_value = max(frame_count - 1, 0)
	_frame_slider.set_value_no_signal(frame_index)


func set_snapshot(snapshot: Dictionary, diagnostics_visible: bool) -> void:
	_diagnostics_panel.visible = diagnostics_visible
	_diagnostics_panel.set_snapshot(snapshot)
	_event_panel.set_events(snapshot.get("event_lines", []))
	if _diagnostics_screen_panel != null:
		_diagnostics_screen_panel.set_snapshot(snapshot)
	if _event_screen_panel != null:
		_event_screen_panel.set_events(snapshot.get("event_lines", []))
	if _trace_integrity_label != null:
		if str(snapshot.get("trace_type", "")) == "live_2d" or str(snapshot.get("trace_type", "")) == "live_3d":
			var mode_label := "LIVE 3D" if str(snapshot.get("trace_type", "")) == "live_3d" else "LIVE 2D"
			var game_over := bool(snapshot.get("game_over", false))
			var paused_fallback := _live_3d_paused if str(snapshot.get("trace_type", "")) == "live_3d" else _live_2d_paused
			var state_label := "GAME OVER" if game_over else ("paused" if bool(snapshot.get("paused", paused_fallback)) else "running")
			var reason := str(snapshot.get("game_over_reason", ""))
			var rotation_text := ""
			if str(snapshot.get("trace_type", "")) == "live_3d":
				rotation_text = " · Last rotation: %s/%s · active plane %s" % [
					str(snapshot.get("last_rotation_label", "none")),
					str(snapshot.get("last_rotation_status", "none")),
					str(snapshot.get("last_rotation_plane", "none")),
				]
			_trace_integrity_label.text = "%s · C++ CORE · piece %s · next %s · score %d · lines %d · state_hash %s · last command %s/%s%s · %s%s" % [
				mode_label,
				str(snapshot.get("current_piece", "none")),
				str(snapshot.get("next_piece", "none")),
				int(snapshot.get("score", 0)),
				int(snapshot.get("lines", 0)),
				str(snapshot.get("state_hash", "")).left(12),
				str(snapshot.get("last_command", "none")),
				str(snapshot.get("last_command_status", "unknown")),
				rotation_text,
				state_label,
				(" · reason " + reason) if reason != "" else "",
			]
			return
		_trace_integrity_label.text = "Trace %s · frame %d/%d · entities %d · frame metadata %s · entity metadata %s" % [
			str(snapshot.get("trace_name", snapshot.get("case_id", ""))),
			int(snapshot.get("frame_index", 0)),
			max(int(snapshot.get("frame_count", 0)) - 1, 0),
			int(snapshot.get("entity_count", 0)),
			"OK" if bool(snapshot.get("frame_count_matches_metadata", false)) else "MISMATCH",
			"OK" if bool(snapshot.get("entity_count_matches_metadata", true)) else "MISMATCH",
		]


func set_playback_state(is_playing: bool, speed: float, diagnostics_visible: bool) -> void:
	_play_button.text = "Pause Replay" if is_playing else "Play Replay"
	_settings_panel.set_diagnostics_visible(diagnostics_visible)
	if _settings_screen_panel != null:
		_settings_screen_panel.set_diagnostics_visible(diagnostics_visible)
	_select_speed_no_signal(speed)
	_speed_value.text = "%s Replay" % ("Playing" if is_playing else "Paused")


func set_live_2d_mode(
	paused: bool,
	game_over: bool,
	last_command: String,
	game_over_reason: String = "",
	gravity_interval_seconds: float = 0.5
) -> void:
	_live_2d_paused = paused
	_live_2d_game_over = game_over
	_play_button.text = "Resume Live" if paused else "Pause Live"
	if _reset_button != null:
		_reset_button.text = "Reset Live"
	_speed_value.text = "Game Over" if game_over else ("Paused Live" if paused else "Running Live")
	if _authority_label != null:
		_authority_label.text = "LIVE 2D · C++ CORE"
	if _viewport_title != null:
		_viewport_title.text = "Live Plain 2D"
	if _viewport_hint != null:
		_viewport_hint.text = "Native C++ owns movement, lock, clear, score, and hash · gravity %.2fs" % gravity_interval_seconds
	if _mode_hint_strip != null:
		var reason_text := game_over_reason if game_over_reason != "" else "stopped"
		_mode_hint_strip.text = ("GAME OVER · %s · %s" % [reason_text, LIVE_2D_HINT_TEXT]) if game_over else LIVE_2D_HINT_TEXT
		_mode_hint_strip.theme_type_variation = "WarningLabel" if game_over else "AccentLabel"
	if _replay_note != null:
		_replay_note.text = "GAME OVER: %s. R resets Live 2D." % (game_over_reason if game_over_reason != "" else "stopped") if game_over else "Live Plain 2D. Godot sends commands only; C++ owns gameplay state. P pauses; paused mode blocks gameplay commands."
	if _hint_label != null:
		_hint_label.text = LIVE_2D_HINT_TEXT
	if _help_label != null:
		_help_label.text = LIVE_2D_HELP_TEXT
	if _trace_integrity_label != null:
		_trace_integrity_label.text = "LIVE 2D · C++ CORE · last command %s · %s%s" % [
			last_command,
			"game over" if game_over else ("paused" if paused else "running"),
			(" · reason " + game_over_reason) if game_over_reason != "" else "",
		]


func set_live_3d_mode(
	paused: bool,
	game_over: bool,
	last_command: String,
	game_over_reason: String = "",
	gravity_interval_seconds: float = 0.5
) -> void:
	_live_3d_paused = paused
	_live_3d_game_over = game_over
	_play_button.text = "Resume Live" if paused else "Pause Live"
	if _reset_button != null:
		_reset_button.text = "Reset Live 3D"
	_speed_value.text = "Game Over" if game_over else ("Paused Live 3D" if paused else "Running Live 3D")
	if _authority_label != null:
		_authority_label.text = "LIVE 3D · C++ CORE"
	if _viewport_title != null:
		_viewport_title.text = "Live Plain 3D"
	if _viewport_hint != null:
		_viewport_hint.text = "Native C++ owns movement, rotation, lock, clear, score, spawn, and hash · gravity %.2fs" % gravity_interval_seconds
	if _mode_hint_strip != null:
		var reason_text := game_over_reason if game_over_reason != "" else "stopped"
		_mode_hint_strip.text = ("GAME OVER · %s · %s" % [reason_text, LIVE_3D_HINT_TEXT]) if game_over else LIVE_3D_HINT_TEXT
		_mode_hint_strip.theme_type_variation = "WarningLabel" if game_over else "AccentLabel"
	if _replay_note != null:
		_replay_note.text = "GAME OVER: %s. Backspace resets Live 3D." % (game_over_reason if game_over_reason != "" else "stopped") if game_over else "Live Plain 3D. Godot sends commands only; C++ owns gameplay state. P pauses; paused mode blocks gameplay commands."
	if _hint_label != null:
		_hint_label.text = LIVE_3D_HINT_TEXT
	if _help_label != null:
		_help_label.text = LIVE_3D_HELP_TEXT
	if _trace_integrity_label != null:
		_trace_integrity_label.text = "LIVE 3D · C++ CORE · last command %s · Last rotation: pending snapshot · %s%s" % [
			last_command,
			"game over" if game_over else ("paused" if paused else "running"),
			(" · reason " + game_over_reason) if game_over_reason != "" else "",
		]


func set_replay_mode_labels(is_playing: bool, speed: float, diagnostics_visible: bool) -> void:
	set_playback_state(is_playing, speed, diagnostics_visible)
	if _authority_label != null:
		_authority_label.text = ReplayVisuals.authority_label(_current_display_mode)
	if _reset_button != null:
		_reset_button.text = "Reset Replay"
	if _viewport_title != null:
		_viewport_title.text = "Trace Replay View"
	if _viewport_hint != null:
		_viewport_hint.text = "Replay-only viewport with diagnostic-first 4D W slices"
	if _mode_hint_strip != null:
		_mode_hint_strip.text = REPLAY_HINT_TEXT
		_mode_hint_strip.theme_type_variation = "DimLabel"
	if _replay_note != null:
		_replay_note.text = "Replay shell only. Diagnostic display is the default readability mode; Godot does not implement gameplay."
	if _hint_label != null:
		_hint_label.text = REPLAY_HINT_TEXT
	if _help_label != null:
		_help_label.text = REPLAY_HELP_TEXT


func set_display_mode(mode: String) -> void:
	_current_display_mode = ReplayVisuals.normalize_display_mode(mode)
	theme = ReplayVisuals.build_theme(_current_display_mode)
	if _authority_label != null:
		_authority_label.text = ReplayVisuals.authority_label(_current_display_mode)
	if _replay_note != null:
		_replay_note.text = "Replay shell only. Diagnostic display is the default readability mode; Godot does not implement gameplay."
	if _settings_panel != null:
		_settings_panel.set_display_mode(_current_display_mode)
	if _settings_screen_panel != null:
		_settings_screen_panel.set_display_mode(_current_display_mode)


func show_screen(screen_name: String) -> void:
	_current_screen = screen_name if _screens.has(screen_name) else SCREEN_MAIN_MENU
	for key in _screens.keys():
		var screen := _screens.get(key) as Control
		if screen != null:
			screen.visible = key == _current_screen
	call_deferred("_log_geometry_diagnostics", "screen:%s" % _current_screen)


func set_world_root(world_root: Node3D) -> void:
	if _game_viewport == null or world_root == null:
		return
	if world_root.get_parent() != _game_viewport:
		_game_viewport.add_child(world_root)
	call_deferred("_log_geometry_diagnostics", "world-installed")


func game_viewport() -> SubViewport:
	return _game_viewport


func layout_contract_snapshot() -> Dictionary:
	var root_rect := Rect2(global_position, size)
	var left_rect := _control_rect(_left_panel)
	var body_rect := _control_rect(_body_container)
	var game_rect := _control_rect(_game_area)
	var viewport_rect := _control_rect(_game_viewport_container)
	var inspector_rect := _control_rect(_right_scroll)
	var bottom_rect := _control_rect(_bottom_panel)
	return {
		"root": root_rect,
		"left_panel": left_rect,
		"body": body_rect,
		"game_area": game_rect,
		"game_viewport": viewport_rect,
		"right_inspector": inspector_rect,
		"bottom_bar": bottom_rect,
		"viewport_size": get_viewport_rect().size,
		"world_parent": _game_viewport.get_node_or_null("WorldRoot") if _game_viewport != null else null,
	}


func show_replay_viewer() -> void:
	show_screen(SCREEN_VIEWER)


func _build_layout() -> void:
	var root := MarginContainer.new()
	_fill_parent(root)
	root.add_theme_constant_override("margin_left", ReplayVisuals.OUTER_MARGIN)
	root.add_theme_constant_override("margin_top", ReplayVisuals.OUTER_MARGIN)
	root.add_theme_constant_override("margin_right", ReplayVisuals.OUTER_MARGIN)
	root.add_theme_constant_override("margin_bottom", ReplayVisuals.OUTER_MARGIN)
	add_child(root)

	var screen_stack := Control.new()
	_fill_parent(screen_stack)
	screen_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	screen_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(screen_stack)

	_main_menu_screen = _make_screen()
	screen_stack.add_child(_main_menu_screen)
	_build_main_menu_screen(_main_menu_screen)

	_browser_screen = _make_screen()
	screen_stack.add_child(_browser_screen)
	_build_browser_screen(_browser_screen)

	_viewer_screen = _make_screen()
	screen_stack.add_child(_viewer_screen)
	var outer := VBoxContainer.new()
	_fill_parent(outer)
	outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_viewer_screen.add_child(outer)

	var top_bar := HBoxContainer.new()
	top_bar.custom_minimum_size = Vector2(0, ReplayVisuals.TOP_BAR_HEIGHT)
	top_bar.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	outer.add_child(top_bar)

	var viewer_nav := VBoxContainer.new()
	viewer_nav.custom_minimum_size = Vector2(220, ReplayVisuals.TOP_BAR_HEIGHT)
	top_bar.add_child(viewer_nav)
	var nav_row_a := HBoxContainer.new()
	nav_row_a.add_theme_constant_override("separation", 6)
	viewer_nav.add_child(nav_row_a)
	var nav_row_b := HBoxContainer.new()
	nav_row_b.add_theme_constant_override("separation", 6)
	viewer_nav.add_child(nav_row_b)
	var menu_button := Button.new()
	menu_button.text = "Main Menu"
	menu_button.pressed.connect(func() -> void:
		show_screen(SCREEN_MAIN_MENU)
	)
	nav_row_a.add_child(menu_button)
	var browser_button := Button.new()
	browser_button.text = "Browser"
	browser_button.pressed.connect(func() -> void:
		show_screen(SCREEN_BROWSER)
	)
	nav_row_a.add_child(browser_button)
	var replay_button := Button.new()
	replay_button.text = "Replay"
	replay_button.pressed.connect(func() -> void:
		replay_mode_requested.emit()
	)
	nav_row_b.add_child(replay_button)
	var live_button := Button.new()
	live_button.text = "Live 2D"
	live_button.pressed.connect(func() -> void:
		live_2d_requested.emit()
	)
	nav_row_b.add_child(live_button)
	var live_3d_button := Button.new()
	live_3d_button.text = "Live 3D"
	live_3d_button.pressed.connect(func() -> void:
		live_3d_requested.emit()
	)
	nav_row_b.add_child(live_3d_button)

	_top_status_panel = PanelContainer.new()
	_top_status_panel.custom_minimum_size = Vector2(ReplayVisuals.TOP_STATUS_PANEL_WIDTH, ReplayVisuals.TOP_BAR_HEIGHT)
	_top_status_panel.size_flags_horizontal = Control.SIZE_FILL
	top_bar.add_child(_top_status_panel)
	var top_status_root := Control.new()
	_fill_parent(top_status_root)
	_top_status_panel.add_child(top_status_root)
	var top_status_box := VBoxContainer.new()
	_fill_parent(top_status_box)
	top_status_root.add_child(top_status_box)
	var status_title := Label.new()
	status_title.text = "Bundle"
	status_title.theme_type_variation = "SecondaryLabel"
	top_status_box.add_child(status_title)
	_bundle_status_label = Label.new()
	_bundle_status_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_bundle_status_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_bundle_status_label.text = "Bundle status: loading"
	top_status_box.add_child(_bundle_status_label)

	var top_summary_panel := PanelContainer.new()
	top_summary_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_bar.add_child(top_summary_panel)
	var top_summary_root := Control.new()
	_fill_parent(top_summary_root)
	top_summary_panel.add_child(top_summary_root)
	var top_summary_box := VBoxContainer.new()
	_fill_parent(top_summary_box)
	top_summary_root.add_child(top_summary_box)
	var summary_title := Label.new()
	summary_title.text = "Replay"
	summary_title.theme_type_variation = "SecondaryLabel"
	top_summary_box.add_child(summary_title)
	_summary_label = Label.new()
	_summary_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_summary_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	top_summary_box.add_child(_summary_label)
	_hash_label = Label.new()
	_hash_label.theme_type_variation = "DimLabel"
	_hash_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	top_summary_box.add_child(_hash_label)

	_authority_panel = PanelContainer.new()
	_authority_panel.custom_minimum_size = Vector2(ReplayVisuals.AUTHORITY_PANEL_WIDTH, ReplayVisuals.TOP_BAR_HEIGHT)
	top_bar.add_child(_authority_panel)
	var authority_root := Control.new()
	_fill_parent(authority_root)
	_authority_panel.add_child(authority_root)
	var authority_box := VBoxContainer.new()
	_fill_parent(authority_box)
	authority_root.add_child(authority_box)
	var authority_title := Label.new()
	authority_title.text = "Authority"
	authority_title.theme_type_variation = "SecondaryLabel"
	authority_box.add_child(authority_title)
	_authority_label = Label.new()
	_authority_label.text = ReplayVisuals.authority_label(_current_display_mode)
	_authority_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_authority_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_authority_label.theme_type_variation = "AccentLabel"
	authority_box.add_child(_authority_label)

	var body := HBoxContainer.new()
	_body_container = body
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", ReplayVisuals.BODY_GAP)
	outer.add_child(body)

	_left_panel = PanelContainer.new()
	_left_panel.name = "LeftCaseBrowserSlot"
	_left_panel.custom_minimum_size = Vector2(ReplayVisuals.LEFT_PANEL_WIDTH, 0)
	_left_panel.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	_left_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_child(_left_panel)

	_viewer_case_browser = CaseBrowserScript.new()
	_viewer_case_browser.name = "ViewerCaseBrowser"
	_viewer_case_browser.trace_family_selected.connect(func(trace_type: String) -> void:
		trace_family_selected.emit(trace_type)
	)
	_viewer_case_browser.case_selected.connect(func(case_id: String) -> void:
		case_selected.emit(case_id)
	)
	_left_panel.add_child(_viewer_case_browser)

	_game_area = PanelContainer.new()
	_game_area.name = "GameArea"
	_game_area.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_game_area.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_game_area.custom_minimum_size = Vector2(ReplayVisuals.GAME_AREA_MIN_WIDTH, 0)
	_game_area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_game_area.theme_type_variation = "ViewportFrame"
	body.add_child(_game_area)
	_viewport_frame = _game_area
	var viewport_inner := MarginContainer.new()
	viewport_inner.add_theme_constant_override("margin_left", ReplayVisuals.VIEWPORT_FRAME_PADDING)
	viewport_inner.add_theme_constant_override("margin_top", ReplayVisuals.VIEWPORT_FRAME_PADDING)
	viewport_inner.add_theme_constant_override("margin_right", ReplayVisuals.VIEWPORT_FRAME_PADDING)
	viewport_inner.add_theme_constant_override("margin_bottom", ReplayVisuals.VIEWPORT_FRAME_PADDING)
	_game_area.add_child(viewport_inner)
	var viewport_box := VBoxContainer.new()
	viewport_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	viewport_inner.add_child(viewport_box)
	_viewport_title = Label.new()
	_viewport_title.text = "Trace Replay View"
	viewport_box.add_child(_viewport_title)
	_viewport_hint = Label.new()
	_viewport_hint.text = "Replay-only viewport with diagnostic-first 4D W slices"
	_viewport_hint.theme_type_variation = "SecondaryLabel"
	_viewport_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_viewport_hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_box.add_child(_viewport_hint)
	_mode_hint_strip = Label.new()
	_mode_hint_strip.text = REPLAY_HINT_TEXT
	_mode_hint_strip.theme_type_variation = "DimLabel"
	_mode_hint_strip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_mode_hint_strip.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	viewport_box.add_child(_mode_hint_strip)
	_game_viewport_container = SubViewportContainer.new()
	_game_viewport_container.name = "GameViewportContainer"
	_game_viewport_container.custom_minimum_size = Vector2(ReplayVisuals.GAME_AREA_MIN_WIDTH, 0)
	_game_viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_game_viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_game_viewport_container.stretch = true
	_game_viewport_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	viewport_box.add_child(_game_viewport_container)
	_game_viewport = SubViewport.new()
	_game_viewport.name = "GameViewport"
	_game_viewport.size = Vector2i(ReplayVisuals.GAME_AREA_MIN_WIDTH, 240)
	_game_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	_game_viewport_container.add_child(_game_viewport)

	_right_scroll = ScrollContainer.new()
	_right_scroll.name = "RightInspectorSlot"
	_right_scroll.size_flags_horizontal = Control.SIZE_SHRINK_END
	_right_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_right_scroll.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_INSPECTOR_WIDTH, 0)
	_right_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(_right_scroll)

	_right_column = VBoxContainer.new()
	_right_column.name = "RightInspectorContent"
	_right_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_right_column.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_INSPECTOR_WIDTH, 0)
	_right_column.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	_right_scroll.add_child(_right_column)

	var integrity_panel := PanelContainer.new()
	integrity_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.add_child(integrity_panel)
	_trace_integrity_label = Label.new()
	_trace_integrity_label.text = "Trace metadata pending"
	_trace_integrity_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_trace_integrity_label.theme_type_variation = "AccentLabel"
	integrity_panel.add_child(_trace_integrity_label)

	_diagnostics_panel = DiagnosticsPanelScript.new()
	_diagnostics_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.DIAGNOSTICS_MIN_HEIGHT)
	_right_column.add_child(_diagnostics_panel)
	_event_panel = EventListPanelScript.new()
	_event_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.EVENTS_MIN_HEIGHT)
	_right_column.add_child(_event_panel)
	_settings_panel = SettingsPanelScript.new()
	_settings_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.SETTINGS_MIN_HEIGHT)
	_settings_panel.diagnostics_visibility_changed.connect(func(visible: bool) -> void:
		diagnostics_visibility_changed.emit(visible)
	)
	_settings_panel.display_mode_changed.connect(func(mode: String) -> void:
		display_mode_changed.emit(mode)
	)
	_right_column.add_child(_settings_panel)

	var bottom_panel := PanelContainer.new()
	_bottom_panel = bottom_panel
	bottom_panel.custom_minimum_size = Vector2(0, ReplayVisuals.TIMELINE_HEIGHT)
	outer.add_child(bottom_panel)
	var bottom_content_root := Control.new()
	_fill_parent(bottom_content_root)
	bottom_panel.add_child(bottom_content_root)
	var bottom_stack := VBoxContainer.new()
	_fill_parent(bottom_stack)
	bottom_stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom_stack.size_flags_vertical = Control.SIZE_EXPAND_FILL
	bottom_content_root.add_child(bottom_stack)
	var bottom := HBoxContainer.new()
	bottom.custom_minimum_size = Vector2(0, ReplayVisuals.TIMELINE_HEIGHT)
	bottom.add_theme_constant_override("separation", ReplayVisuals.CONTROL_GAP)
	bottom_stack.add_child(bottom)

	var control_group := HBoxContainer.new()
	control_group.add_theme_constant_override("separation", ReplayVisuals.CONTROL_GAP)
	bottom.add_child(control_group)

	var prev_button := Button.new()
	prev_button.text = "Prev"
	prev_button.pressed.connect(func() -> void:
		previous_frame_requested.emit()
	)
	control_group.add_child(prev_button)

	_play_button = Button.new()
	_play_button.text = "Play Replay"
	_play_button.pressed.connect(func() -> void:
		play_pause_requested.emit()
	)
	control_group.add_child(_play_button)

	var next_button := Button.new()
	next_button.text = "Next"
	next_button.pressed.connect(func() -> void:
		next_frame_requested.emit()
	)
	control_group.add_child(next_button)

	_reset_button = Button.new()
	_reset_button.text = "Reset Replay"
	_reset_button.pressed.connect(func() -> void:
		reset_requested.emit()
	)
	control_group.add_child(_reset_button)
	var fit_button := Button.new()
	fit_button.text = "Fit View"
	fit_button.pressed.connect(func() -> void:
		fit_view_requested.emit()
	)
	control_group.add_child(fit_button)
	var quit_button := Button.new()
	quit_button.text = "Quit Replay"
	quit_button.pressed.connect(func() -> void:
		quit_requested.emit()
	)
	control_group.add_child(quit_button)
	var geometry_toggle := CheckBox.new()
	geometry_toggle.text = "Geom"
	geometry_toggle.tooltip_text = "Print viewer layout rectangles"
	geometry_toggle.toggled.connect(func(visible: bool) -> void:
		_geometry_diagnostics_enabled = visible
		_log_geometry_diagnostics("toggle")
	)
	control_group.add_child(geometry_toggle)

	_replay_note = Label.new()
	_replay_note.text = "Replay shell only. Diagnostic display is the default readability mode; Godot does not implement gameplay."
	_replay_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_replay_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_replay_note.theme_type_variation = "SecondaryLabel"

	_frame_slider = HSlider.new()
	_frame_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_frame_slider.step = 1.0
	_frame_slider.value_changed.connect(func(value: float) -> void:
		frame_scrub_requested.emit(int(value))
	)
	bottom.add_child(_frame_slider)
	bottom_stack.add_child(_replay_note)

	var speed_group := HBoxContainer.new()
	speed_group.add_theme_constant_override("separation", ReplayVisuals.SPEED_GROUP_GAP)
	bottom.add_child(speed_group)
	var speed_label := Label.new()
	speed_label.text = "Speed"
	speed_label.theme_type_variation = "SecondaryLabel"
	speed_group.add_child(speed_label)
	_speed_select = OptionButton.new()
	_speed_select.custom_minimum_size = Vector2(ReplayVisuals.SPEED_SLIDER_WIDTH, 0)
	for speed in [0.25, 0.5, 1.0, 2.0, 4.0]:
		_speed_select.add_item("%sx" % speed)
		_speed_select.set_item_metadata(_speed_select.item_count - 1, speed)
	_speed_select.item_selected.connect(func(index: int) -> void:
		playback_speed_changed.emit(float(_speed_select.get_item_metadata(index)))
	)
	speed_group.add_child(_speed_select)
	_speed_value = Label.new()
	_speed_value.text = "Paused Replay"
	speed_group.add_child(_speed_value)

	_frame_label = Label.new()
	_frame_label.text = "Frame 0 / 0"
	_frame_label.theme_type_variation = "AccentLabel"
	bottom.add_child(_frame_label)
	_hint_label = Label.new()
	_hint_label.text = REPLAY_HINT_TEXT
	_hint_label.theme_type_variation = "DimLabel"
	_hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bottom_stack.add_child(_hint_label)
	_help_panel = PanelContainer.new()
	_help_panel.visible = false
	_help_label = Label.new()
	_help_label.text = REPLAY_HELP_TEXT
	_help_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_help_label.theme_type_variation = "SecondaryLabel"
	_help_panel.add_child(_help_label)
	bottom_stack.add_child(_help_panel)
	_settings_panel.set_display_mode(_current_display_mode)

	_settings_screen = _make_screen()
	screen_stack.add_child(_settings_screen)
	_build_settings_screen(_settings_screen)
	_controls_screen = _make_screen()
	screen_stack.add_child(_controls_screen)
	_build_controls_screen(_controls_screen)
	_diagnostics_screen = _make_screen()
	screen_stack.add_child(_diagnostics_screen)
	_build_diagnostics_screen(_diagnostics_screen)
	_screens = {
		SCREEN_MAIN_MENU: _main_menu_screen,
		SCREEN_BROWSER: _browser_screen,
		SCREEN_VIEWER: _viewer_screen,
		SCREEN_SETTINGS: _settings_screen,
		SCREEN_CONTROLS: _controls_screen,
		SCREEN_DIAGNOSTICS: _diagnostics_screen,
	}
	show_screen(SCREEN_MAIN_MENU)


func _make_screen() -> Control:
	var screen := Control.new()
	screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_fill_parent(screen)
	return screen


func _build_main_menu_screen(screen: Control) -> void:
	var center := CenterContainer.new()
	_fill_parent(center)
	screen.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720, 520)
	center.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 48)
	margin.add_theme_constant_override("margin_top", 44)
	margin.add_theme_constant_override("margin_right", 48)
	margin.add_theme_constant_override("margin_bottom", 44)
	panel.add_child(margin)
	var layout := VBoxContainer.new()
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.alignment = BoxContainer.ALIGNMENT_CENTER
	layout.add_theme_constant_override("separation", 18)
	margin.add_child(layout)
	var title := Label.new()
	title.text = "Tet4D Godot Transition Spike"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 32)
	layout.add_child(title)
	var subtitle := Label.new()
	subtitle.text = "Replay-only shell. Python remains the semantic authority."
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.theme_type_variation = "SecondaryLabel"
	subtitle.add_theme_font_size_override("font_size", 18)
	layout.add_child(subtitle)
	var browser_button := Button.new()
	browser_button.text = "Open Trace Replay Browser"
	browser_button.custom_minimum_size = Vector2(420, 54)
	browser_button.add_theme_font_size_override("font_size", 18)
	browser_button.pressed.connect(func() -> void:
		show_screen(SCREEN_BROWSER)
	)
	layout.add_child(browser_button)
	var live_button := Button.new()
	live_button.text = "Start Live Plain 2D"
	live_button.custom_minimum_size = Vector2(420, 54)
	live_button.add_theme_font_size_override("font_size", 18)
	live_button.pressed.connect(func() -> void:
		live_2d_requested.emit()
	)
	layout.add_child(live_button)
	var live_3d_button := Button.new()
	live_3d_button.text = "Start Live Plain 3D"
	live_3d_button.custom_minimum_size = Vector2(420, 54)
	live_3d_button.add_theme_font_size_override("font_size", 18)
	live_3d_button.pressed.connect(func() -> void:
		live_3d_requested.emit()
	)
	layout.add_child(live_3d_button)
	var controls_button := Button.new()
	controls_button.text = "Controls / Keyboard Hints"
	controls_button.custom_minimum_size = Vector2(420, 50)
	controls_button.add_theme_font_size_override("font_size", 17)
	controls_button.pressed.connect(func() -> void:
		show_screen(SCREEN_CONTROLS)
	)
	layout.add_child(controls_button)
	var settings_button := Button.new()
	settings_button.text = "Settings"
	settings_button.custom_minimum_size = Vector2(420, 50)
	settings_button.add_theme_font_size_override("font_size", 17)
	settings_button.pressed.connect(func() -> void:
		show_screen(SCREEN_SETTINGS)
	)
	layout.add_child(settings_button)
	var quit_button := Button.new()
	quit_button.text = "Quit Replay Shell"
	quit_button.custom_minimum_size = Vector2(420, 50)
	quit_button.add_theme_font_size_override("font_size", 17)
	quit_button.pressed.connect(func() -> void:
		quit_requested.emit()
	)
	layout.add_child(quit_button)


func _build_browser_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	var nav := _screen_nav("Trace Replay Browser")
	layout.add_child(nav)
	_case_browser = CaseBrowserScript.new()
	_case_browser.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_case_browser.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_case_browser.trace_family_selected.connect(func(trace_type: String) -> void:
		trace_family_selected.emit(trace_type)
	)
	_case_browser.case_selected.connect(func(case_id: String) -> void:
		case_selected.emit(case_id)
	)
	layout.add_child(_case_browser)


func _build_settings_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	layout.add_child(_screen_nav("Settings"))
	_settings_screen_panel = SettingsPanelScript.new()
	_settings_screen_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_settings_screen_panel.size_flags_vertical = Control.SIZE_FILL
	_settings_screen_panel.diagnostics_visibility_changed.connect(func(visible: bool) -> void:
		diagnostics_visibility_changed.emit(visible)
	)
	_settings_screen_panel.display_mode_changed.connect(func(mode: String) -> void:
		display_mode_changed.emit(mode)
	)
	layout.add_child(_settings_screen_panel)


func _build_controls_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	layout.add_child(_screen_nav("Controls / Keyboard Hints"))
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.add_child(panel)
	var text := Label.new()
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.text = "Replay: %s. Live 2D: %s. Live 3D: %s. Godot routes live commands only; C++ owns gameplay state." % [
		REPLAY_HINT_TEXT,
		LIVE_2D_HINT_TEXT,
		LIVE_3D_HINT_TEXT,
	]
	text.theme_type_variation = "SecondaryLabel"
	panel.add_child(text)


func _build_diagnostics_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	layout.add_child(_screen_nav("Diagnostics"))
	_diagnostics_screen_panel = DiagnosticsPanelScript.new()
	_diagnostics_screen_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_diagnostics_screen_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(_diagnostics_screen_panel)
	_event_screen_panel = EventListPanelScript.new()
	_event_screen_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_event_screen_panel.size_flags_vertical = Control.SIZE_FILL
	layout.add_child(_event_screen_panel)


func _screen_nav(title_text: String) -> HBoxContainer:
	var nav := HBoxContainer.new()
	nav.add_theme_constant_override("separation", ReplayVisuals.CONTROL_GAP)
	var title := Label.new()
	title.text = title_text
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.theme_type_variation = "AccentLabel"
	nav.add_child(title)
	var menu_button := Button.new()
	menu_button.text = "Main Menu"
	menu_button.pressed.connect(func() -> void:
		show_screen(SCREEN_MAIN_MENU)
	)
	nav.add_child(menu_button)
	var browser_button := Button.new()
	browser_button.text = "Browser"
	browser_button.pressed.connect(func() -> void:
		show_screen(SCREEN_BROWSER)
	)
	nav.add_child(browser_button)
	var viewer_button := Button.new()
	viewer_button.text = "Viewer"
	viewer_button.pressed.connect(func() -> void:
		show_screen(SCREEN_VIEWER)
	)
	nav.add_child(viewer_button)
	var live_button := Button.new()
	live_button.text = "Live 2D"
	live_button.pressed.connect(func() -> void:
		live_2d_requested.emit()
	)
	nav.add_child(live_button)
	var live_3d_button := Button.new()
	live_3d_button.text = "Live 3D"
	live_3d_button.pressed.connect(func() -> void:
		live_3d_requested.emit()
	)
	nav.add_child(live_3d_button)
	var diagnostics_button := Button.new()
	diagnostics_button.text = "Diagnostics"
	diagnostics_button.pressed.connect(func() -> void:
		show_screen(SCREEN_DIAGNOSTICS)
	)
	nav.add_child(diagnostics_button)
	var settings_button := Button.new()
	settings_button.text = "Settings"
	settings_button.pressed.connect(func() -> void:
		show_screen(SCREEN_SETTINGS)
	)
	nav.add_child(settings_button)
	return nav


func _fill_parent(control: Control) -> void:
	control.set_anchors_preset(Control.PRESET_FULL_RECT)
	control.offset_left = 0.0
	control.offset_top = 0.0
	control.offset_right = 0.0
	control.offset_bottom = 0.0


func _apply_responsive_layout() -> void:
	_log_geometry_diagnostics("responsive-compat")


func _log_geometry_diagnostics(reason: String) -> void:
	if not _geometry_diagnostics_enabled and reason != "toggle":
		return
	var viewport_size := get_viewport_rect().size
	var parts := [
		"[ReplayHud geometry:%s]" % reason,
		"root=%s" % str(Rect2(global_position, size)),
		"left_panel=%s" % _rect_text(_left_panel),
		"body=%s" % _rect_text(_body_container),
		"game_area=%s" % _rect_text(_game_area),
		"right_inspector=%s" % _rect_text(_right_scroll),
		"bottom_bar=%s" % _rect_text(_bottom_panel),
		"viewport=%s" % str(viewport_size),
	]
	print(" ".join(parts))


func _rect_text(node: Control) -> String:
	if node == null:
		return "<null>"
	return str(_control_rect(node))


func _control_rect(node: Control) -> Rect2:
	if node == null:
		return Rect2()
	return Rect2(node.global_position, node.size)


func _select_speed_no_signal(speed: float) -> void:
	if _speed_select == null:
		return
	for index in range(_speed_select.item_count):
		if absf(float(_speed_select.get_item_metadata(index)) - speed) < 0.01:
			_speed_select.select(index)
			return


func toggle_help() -> void:
	if _help_panel != null:
		_help_panel.visible = not _help_panel.visible
