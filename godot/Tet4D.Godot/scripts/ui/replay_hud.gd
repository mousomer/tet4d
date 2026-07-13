extends Control

class_name ReplayHud

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const CaseBrowserScript = preload("res://scripts/ui/case_browser.gd")
const DiagnosticsPanelScript = preload("res://scripts/ui/diagnostics_panel.gd")
const EventListPanelScript = preload("res://scripts/ui/event_list_panel.gd")
const SettingsPanelScript = preload("res://scripts/ui/settings_panel.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellControlStyleApplierScript = preload("res://scripts/ui/style/shell_control_style_applier.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")
const LiveOnboardingModelScript = preload("res://scripts/ui/onboarding/live_onboarding_model.gd")
const LiveOnboardingPanelScript = preload("res://scripts/ui/onboarding/live_onboarding_panel.gd")
const SettingsRegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const SettingsStoreScript = preload("res://scripts/ui/settings/settings_store.gd")

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
signal replay_loop_changed(enabled: bool)
signal display_w_labels_changed(visible: bool)
signal projection_strength_changed(value: float)
signal fit_view_requested()
signal quit_requested()
signal replay_mode_requested()
signal live_2d_requested()
signal live_3d_requested()
signal live_4d_requested()
signal main_menu_requested()

const SCREEN_MAIN_MENU := "main_menu"
const SCREEN_BROWSER := "browser"
const SCREEN_VIEWER := "viewer"
const SCREEN_SETTINGS := "settings"
const SCREEN_CONTROLS := "controls"
const SCREEN_DIAGNOSTICS := "diagnostics"
const SCREEN_ABOUT := "about"
const REPLAY_HELP_TEXT := "Replay controls only: Space toggles replay playback, arrows browse exported frames/cases, 1/2/3 switch trace families, F fits the current trace bounds, Q quits the replay shell. These controls do not move gameplay pieces."
const LIVE_2D_HELP_TEXT := "Move, rotate, and drop the piece with the controls shown here. Camera controls change the view; movement controls move the piece. Esc returns to the Main Menu."
const LIVE_3D_HELP_TEXT := "Move on X and Z, drop separately, and rotate in the XY, XZ, or YZ plane. Camera controls change the view; movement controls move the piece. Esc returns to the Main Menu."
const LIVE_4D_HELP_TEXT := "The board uses W slices; Q/E moves the piece between them. Start with one or two of the six rotation planes. Camera controls change the view; movement controls move the piece. Esc returns to the Main Menu."
const ABOUT_DEMO_TEXT := """Tet4D is a 2D/3D/4D Tetris project. This Godot front end lets you inspect replay demos and play the plain-board 2D, 3D, and 4D modes.

Choose a mode:
Replay Demos - inspect exported gameplay, topology, and endgame traces.
Live Plain 2D - the easiest first play mode.
Live Plain 3D - direct plane rotations on a readable 3D board.
Live Plain 4D - side-by-side W slices with camera recovery.
Topology Playground - still launches from the Python tools, not this Godot shell.

Demo tour:
1. Open Replay Demos and scrub a gameplay or topology case.
2. Return to Main Menu and play Live Plain 2D.
3. Try Live Plain 3D for direct XY/XZ/YZ rotations.
4. Inspect Live Plain 4D with Q/E W movement and Fit View.

Known limitations:
- The Python version currently contains the full topology tools.
- Topology Playground and broader topology editing are not yet available in this front end.
- Settings persistence and keybinding editing are not available yet."""

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
var _restart_game_button: Button
var _quit_button: Button
var _hint_label: VBoxContainer
var _mode_hint_strip: VBoxContainer
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
var _background_rect: ColorRect
var _main_menu_screen: Control
var _browser_screen: Control
var _viewer_screen: Control
var _settings_screen: Control
var _controls_screen: Control
var _diagnostics_screen: Control
var _about_screen: Control
var _screens: Dictionary = {}
var _replay_note: Label
var _help_panel: PanelContainer
var _trace_integrity_label: Label
var _bundle_detail_label: Label
var _camera_status_label: Label
var _help_label: Label
var _top_state_badge_label: Label
var _inspector_hint_panel: VBoxContainer
var _inspector_header: Label
var _view_header: Label
var _controls_header: Label
var _diagnostics_header: Label
var _quick_settings_header: Label
var _integrity_panel: PanelContainer
var _bundle_detail_panel: PanelContainer
var _camera_panel: PanelContainer
var _current_display_mode := ReplayVisuals.default_display_mode()
var _style_manager = ShellStyleManagerScript.new()
var _style_applier = ShellControlStyleApplierScript.new()
var _current_screen := SCREEN_MAIN_MENU
var _geometry_diagnostics_enabled := false
var _keyboard_hints_visible := true
var _bundle_status_text := ""
var _bundle_status_detail := ""
var _live_2d_paused := false
var _live_2d_game_over := false
var _live_3d_paused := false
var _live_3d_game_over := false
var _live_4d_paused := false
var _live_4d_game_over := false
var _onboarding_model = LiveOnboardingModelScript.new()
var _onboarding_panel: PanelContainer
var _last_onboarding_result_signature := ""
var _screen_focus_targets := {}
var _main_menu_scroll: ScrollContainer
var _controls_scroll: ScrollContainer
var _about_scroll: ScrollContainer
var _settings_registry = SettingsRegistryScript.new()
var _settings_store


static func replay_hint_text() -> String:
	return _control_groups_text(replay_control_hint_groups())


static func live_2d_hint_text() -> String:
	return _control_groups_text(live_2d_control_hint_groups())


static func live_3d_hint_text() -> String:
	return _control_groups_text(live_3d_control_hint_groups())


static func live_4d_hint_text() -> String:
	return _control_groups_text(live_4d_control_hint_groups())


static func replay_control_hint_groups() -> Array:
	return [
		{"group": "Replay", "items": [["Space", "Play / Pause"], ["Left/Right", "Previous / Next frame"], ["Up/Down", "Previous / Next case"], ["1/2/3", "Trace family"]]},
		{"group": "Navigation", "items": [["F", "Fit View"], ["H", "How to Play"], ["Tab", "Play 2D"], ["Esc", "Main Menu"]]},
	]


static func live_2d_control_hint_groups() -> Array:
	return [
		{"group": "Piece movement", "items": [["A/D", "Move left / right"], ["Left/Right", "Move left / right"]]},
		{"group": "Piece rotation", "items": [["W/Up/X", "Rotate clockwise"], ["Z", "Rotate counter-clockwise"]]},
		{"group": "Drop", "items": [["S/Down", "Soft Drop"], ["Space", "Hard Drop"]]},
		{"group": "Camera", "items": [["F", "Fit View"]]},
		{"group": "Session", "items": [["P", "Pause"], ["R", "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Play 3D"], ["Esc", "Main Menu"]]},
	]


static func live_3d_control_hint_groups() -> Array:
	return [
		{"group": "Piece movement", "items": [["A/D", "Move X- / X+"], ["W/S", "Move Z+ / Z-"]]},
		{"group": "Piece rotation", "items": [["R/T", "Rotate XY- / XY+"], ["F/G", "Rotate XZ- / XZ+"], ["V/B", "Rotate YZ- / YZ+"]]},
		{"group": "Drop", "items": [["Shift", "Soft Drop"], ["Space", "Hard Drop"]]},
		{"group": "Camera", "items": [["Mouse", "Orbit / zoom"], ["F", "Fit View"]]},
		{"group": "Session", "items": [["P", "Pause"], ["Backspace", "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Play 4D"], ["Esc", "Main Menu"]]},
	]


static func live_4d_control_hint_groups() -> Array:
	return [
		{"group": "Piece movement", "items": [["A / D", "X- / X+"], ["W / S", "Z+ / Z-"], ["Q / E", "W- / W+"]]},
		{
			"group": "Plane Rotation",
			"note": "Left: CCW · Right: CW",
			"items": [["R / T", "XY"], ["F / G", "XZ"], ["V / B", "YZ"], ["Y / U", "XW"], ["H / J", "YW"], ["N / M", "ZW"]],
		},
		{"group": "Camera", "items": [["I / K", "Pitch up / down"], ["O / L", "Yaw left / right"], [", / .", "Roll left / right"], ["- / = / +", "Zoom out / in"]]},
		{"group": "Mouse Camera", "items": [["Drag", "Orbit"], ["Shift Drag", "Roll"], ["Wheel", "Zoom"], ["Double-click", "Fit View"]]},
		{"group": "Drop", "items": [["Shift", "Soft Drop"], ["Space", "Hard Drop"]]},
		{"group": "Session", "items": [["P", "Pause"], ["Backspace", "Restart Game"]]},
		{"group": "Navigation", "items": [["Tab", "Replay Demos"], ["Esc", "Main Menu"]]},
	]


static func quick_control_hint_groups(mode: String) -> Array:
	match mode:
		"live_2d", "live_3d", "live_4d":
			return []
		_:
			return [{"group": "Quick", "items": [["Space", "Play / Pause"], ["Left/Right", "Frame"], ["Up/Down", "Case"], ["1/2/3", "Family"], ["F", "Fit View"], ["Tab", "Play 2D"], ["Esc", "Main Menu"]]}]


static func _control_groups_text(groups: Array) -> String:
	var parts: Array = []
	for group in groups:
		for item in group.get("items", []):
			parts.append("%s %s" % [str(item[0]), str(item[1])])
	return " · ".join(parts)


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_PASS
	_settings_registry.load_from_path(SettingsRegistryScript.REGISTRY_PATH)
	_settings_store = SettingsStoreScript.new(_settings_registry)
	_style_manager.set_theme(_current_display_mode)
	_style_manager.theme_changed.connect(func(theme_id: String) -> void:
		_apply_shell_style()
	)
	theme = ReplayVisuals.build_theme(_current_display_mode)
	_install_shell_layout_contract()
	_build_layout()
	_apply_shell_style()
	call_deferred("_log_geometry_diagnostics", "ready")


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED and is_inside_tree():
		call_deferred("_log_geometry_diagnostics", "resize")


func set_bundle_status(text: String, detail: String = "") -> void:
	_bundle_status_text = text
	_bundle_status_detail = detail if detail != "" else text
	_bundle_status_label.text = text
	if _bundle_detail_label != null:
		_bundle_detail_label.text = _bundle_status_detail


func set_camera_status(text: String) -> void:
	if _camera_status_label != null:
		_camera_status_label.text = text


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
		var trace_type := str(snapshot.get("trace_type", ""))
		if trace_type == "live_2d" or trace_type == "live_3d" or trace_type == "live_4d":
			_onboarding_model.select_mode(trace_type)
			var result_signature := "%s|%s|%s|%s" % [trace_type, str(snapshot.get("last_command", "")), str(snapshot.get("last_command_status", "")), str(snapshot.get("state_hash", ""))]
			if result_signature != _last_onboarding_result_signature:
				_last_onboarding_result_signature = result_signature
				_onboarding_model.consume_command_result(str(snapshot.get("last_command", "")), str(snapshot.get("last_command_status", "")))
			_render_onboarding()
			var mode_label := "Live Plain 4D" if trace_type == "live_4d" else ("Live Plain 3D" if trace_type == "live_3d" else "Live Plain 2D")
			var game_over := bool(snapshot.get("game_over", false))
			var paused_fallback := _live_4d_paused if trace_type == "live_4d" else (_live_3d_paused if trace_type == "live_3d" else _live_2d_paused)
			var state_label := "Game Over" if game_over else ("Paused" if bool(snapshot.get("paused", paused_fallback)) else "Running")
			var reason := str(snapshot.get("game_over_reason", ""))
			var last_input := "%s / %s" % [str(snapshot.get("last_command", "none")), str(snapshot.get("last_command_status", "unknown"))]
			var rotation_text := "Last rotation %s / %s" % [
				str(snapshot.get("last_rotation_label", "none")),
				str(snapshot.get("last_rotation_status", "none")),
			]
			if trace_type == "live_3d" or trace_type == "live_4d":
				rotation_text = "Last rotation %s / %s · plane %s" % [
					str(snapshot.get("last_rotation_label", "none")),
					str(snapshot.get("last_rotation_status", "none")),
					str(snapshot.get("last_rotation_plane", "none")),
				]
			var layout_text := "Board view"
			if trace_type == "live_4d":
				layout_text = "W slices side-by-side · W %d/%d" % [
					int(snapshot.get("active_w", 0)),
					int(snapshot.get("w_slice_count", 1)),
				]
			_update_live_status_strip(mode_label, state_label, reason, trace_type)
			_update_live_gameplay_summary(snapshot, mode_label)
			_trace_integrity_label.text = _format_live_inspector_text(
				mode_label,
				state_label,
				reason,
				last_input,
				layout_text,
				rotation_text
			)
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
	_settings_panel.set_playback_speed(speed)
	if _settings_screen_panel != null:
		_settings_screen_panel.set_playback_speed(speed)
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
	_onboarding_model.select_mode("live_2d")
	_render_onboarding()
	_set_live_declutter_mode(true)
	_play_button.text = "Resume Live" if paused else "Pause Live"
	if _reset_button != null:
		_reset_button.text = "Reset Live"
	_speed_value.text = "Game Over" if game_over else ("Paused Live" if paused else "Running Live")
	var state_text := "Game Over" if game_over else ("Paused" if paused else "Running")
	_update_live_status_strip("Live Plain 2D", state_text, game_over_reason, "live_2d")
	if _viewport_title != null:
		_viewport_title.text = "Live Plain 2D"
	if _viewport_hint != null:
		_viewport_hint.text = "C++ PlainNDSession · Godot command/render shell · gravity %.2fs" % gravity_interval_seconds
	if _mode_hint_strip != null:
		_mode_hint_strip.visible = false
	if _replay_note != null:
		_replay_note.text = "GAME OVER · %s. R restarts Live 2D." % _game_over_reason_label(game_over_reason) if game_over else "Play 2D. Camera controls change the view; movement controls move the piece. P pauses; Esc opens the Main Menu."
	if _hint_label != null:
		_hint_label.visible = false
	if _inspector_hint_panel != null:
		_update_control_hint_panel(_inspector_hint_panel, "live_2d", game_over, game_over_reason)
	if _help_label != null:
		_help_label.text = LIVE_2D_HELP_TEXT
	if _trace_integrity_label != null:
		_trace_integrity_label.text = _format_live_inspector_text(
			"Live Plain 2D",
			state_text,
			game_over_reason,
			last_command,
			"Flat board",
			"Rotation XY"
		)


func set_live_3d_mode(
	paused: bool,
	game_over: bool,
	last_command: String,
	game_over_reason: String = "",
	gravity_interval_seconds: float = 0.5
) -> void:
	_live_3d_paused = paused
	_live_3d_game_over = game_over
	_onboarding_model.select_mode("live_3d")
	_render_onboarding()
	_set_live_declutter_mode(true)
	_play_button.text = "Resume Live" if paused else "Pause Live"
	if _reset_button != null:
		_reset_button.text = "Reset Live 3D"
	_speed_value.text = "Game Over" if game_over else ("Paused Live 3D" if paused else "Running Live 3D")
	var state_text := "Game Over" if game_over else ("Paused" if paused else "Running")
	_update_live_status_strip("Live Plain 3D", state_text, game_over_reason, "live_3d")
	if _viewport_title != null:
		_viewport_title.text = "Live Plain 3D"
	if _viewport_hint != null:
		_viewport_hint.text = "C++ PlainNDSession · Godot command/render shell · gravity %.2fs" % gravity_interval_seconds
	if _mode_hint_strip != null:
		_mode_hint_strip.visible = false
	if _replay_note != null:
		_replay_note.text = "GAME OVER · %s. Backspace restarts Live 3D." % _game_over_reason_label(game_over_reason) if game_over else "Play 3D. Movement uses X/Z while falling remains separate. Camera controls change only the view."
	if _hint_label != null:
		_hint_label.visible = false
	if _inspector_hint_panel != null:
		_update_control_hint_panel(_inspector_hint_panel, "live_3d", game_over, game_over_reason)
	if _help_label != null:
		_help_label.text = LIVE_3D_HELP_TEXT
	if _trace_integrity_label != null:
		_trace_integrity_label.text = _format_live_inspector_text(
			"Live Plain 3D",
			state_text,
			game_over_reason,
			last_command,
			"External diagram board",
			"Last rotation pending snapshot"
		)


func set_live_4d_mode(
	paused: bool,
	game_over: bool,
	last_command: String,
	game_over_reason: String = "",
	gravity_interval_seconds: float = 0.5
) -> void:
	_live_4d_paused = paused
	_live_4d_game_over = game_over
	_onboarding_model.select_mode("live_4d")
	_render_onboarding()
	_set_live_declutter_mode(true)
	_play_button.text = "Resume Live" if paused else "Pause Live"
	if _reset_button != null:
		_reset_button.text = "Reset Live 4D"
	_speed_value.text = "Game Over" if game_over else ("Paused Live 4D" if paused else "Running Live 4D")
	var state_text := "Game Over" if game_over else ("Paused" if paused else "Running")
	_update_live_status_strip("Live Plain 4D", state_text, game_over_reason, "live_4d")
	if _viewport_title != null:
		_viewport_title.text = "Live Plain 4D"
	if _viewport_hint != null:
		_viewport_hint.text = "C++ PlainNDSession · Godot command/render shell · W slice cards · gravity %.2fs" % gravity_interval_seconds
	if _mode_hint_strip != null:
		_mode_hint_strip.visible = false
	if _replay_note != null:
		_replay_note.text = "GAME OVER · %s. Backspace restarts Live 4D." % _game_over_reason_label(game_over_reason) if game_over else "Play 4D uses W slices. Q/E move the piece across W; camera controls change only the view; double-click or Fit View restores it."
	if _hint_label != null:
		_hint_label.visible = false
	if _inspector_hint_panel != null:
		_update_control_hint_panel(_inspector_hint_panel, "live_4d", game_over, game_over_reason)
	if _help_label != null:
		_help_label.text = LIVE_4D_HELP_TEXT
	if _trace_integrity_label != null:
		_trace_integrity_label.text = _format_live_inspector_text(
			"Live Plain 4D",
			state_text,
			game_over_reason,
			last_command,
			"W slices side-by-side",
			"Last rotation pending snapshot"
		)


func set_replay_mode_labels(is_playing: bool, speed: float, diagnostics_visible: bool) -> void:
	_set_live_declutter_mode(false)
	set_playback_state(is_playing, speed, diagnostics_visible)
	if _authority_label != null:
		_authority_label.text = ReplayVisuals.authority_label(_current_display_mode)
	if _top_state_badge_label != null:
		_top_state_badge_label.text = "[ PAUSED ]" if not is_playing else "[ RUNNING ]"
		_top_state_badge_label.theme_type_variation = "StatusAccentLabel"
		_style_applier.apply_to_tree(_top_state_badge_label, _style_manager)
	if _reset_button != null:
		_reset_button.text = "Reset Replay"
	if _viewport_title != null:
		_viewport_title.text = "Trace Replay View"
	if _viewport_hint != null:
		_viewport_hint.text = "Replay-only viewport with diagnostic-first 4D W slices"
	if _mode_hint_strip != null:
		_update_control_hint_panel(_mode_hint_strip, "replay")
	if _replay_note != null:
		_replay_note.text = "Replay shell only. Vector Arcade is the product display default; Godot does not implement gameplay."
	if _hint_label != null:
		_update_control_hint_panel(_hint_label, "replay")
	if _inspector_hint_panel != null:
		_update_control_hint_panel(_inspector_hint_panel, "replay")
	if _help_label != null:
		_help_label.text = REPLAY_HELP_TEXT


func set_display_mode(mode: String) -> void:
	_current_display_mode = ReplayVisuals.normalize_display_mode(mode)
	_style_manager.set_theme(_current_display_mode)
	theme = ReplayVisuals.build_theme(_current_display_mode)
	if _authority_label != null:
		_authority_label.text = ReplayVisuals.authority_label(_current_display_mode)
	if _replay_note != null:
		_replay_note.text = "Replay shell only. Vector Arcade is the product display default; Godot does not implement gameplay."
	if _settings_panel != null:
		_settings_panel.set_display_mode(_current_display_mode)
	if _settings_screen_panel != null:
		_settings_screen_panel.set_display_mode(_current_display_mode)
	_apply_shell_style()


func show_screen(screen_name: String) -> void:
	_current_screen = screen_name if _screens.has(screen_name) else SCREEN_MAIN_MENU
	for key in _screens.keys():
		var screen := _screens.get(key) as Control
		if screen != null:
			screen.visible = key == _current_screen
	call_deferred("_log_geometry_diagnostics", "screen:%s" % _current_screen)
	call_deferred("_focus_current_screen")


func _focus_current_screen() -> void:
	var target = _screen_focus_targets.get(_current_screen)
	if not (target is Control):
		var screen := _screens.get(_current_screen) as Control
		var buttons := screen.find_children("*", "Button", true, false) if screen != null else []
		target = buttons[0] if not buttons.is_empty() else null
	if target is Control and is_instance_valid(target) and (target as Control).is_visible_in_tree() and (target as Control).focus_mode != Control.FOCUS_NONE:
		(target as Control).grab_focus()


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
	var settings_rect := _control_rect(_settings_panel)
	var bottom_rect := _control_rect(_bottom_panel)
	return {
		"root": root_rect,
		"left_panel": left_rect,
		"left_panel_visible": _left_panel.visible if _left_panel != null else false,
		"left_panel_text": _collect_label_text(_left_panel),
		"body": body_rect,
		"game_area": game_rect,
		"game_viewport": viewport_rect,
		"right_inspector": inspector_rect,
		"settings_panel": settings_rect,
		"bottom_bar": bottom_rect,
		"current_screen": _current_screen,
		"bottom_bar_visible": _bottom_panel.visible if _bottom_panel != null else false,
		"viewport_hints_visible": _mode_hint_strip.visible if _mode_hint_strip != null else false,
		"bottom_hints_visible": _hint_label.visible if _hint_label != null else false,
		"viewport_size": get_viewport_rect().size,
		"supported_minimum_size": ReplayVisuals.supported_shell_minimum_size(),
		"world_parent": _game_viewport.get_node_or_null("WorldRoot") if _game_viewport != null else null,
		"bundle_status_text": _bundle_status_label.text if _bundle_status_label != null else "",
		"top_summary_text": _summary_label.text if _summary_label != null else "",
		"bundle_detail_text": _bundle_detail_label.text if _bundle_detail_label != null else "",
		"camera_status_text": _camera_status_label.text if _camera_status_label != null else "",
		"top_detail_text": _hash_label.text if _hash_label != null and _hash_label.visible else "",
		"viewport_detail_text": _viewport_hint.text if _viewport_hint != null and _viewport_hint.visible else "",
		"viewport_hint_text": _collect_label_text(_mode_hint_strip),
		"bottom_hint_text": _collect_label_text(_hint_label),
		"inspector_hint_text": _collect_label_text(_inspector_hint_panel),
		"onboarding": _onboarding_model.snapshot(),
		"onboarding_panel": _onboarding_panel.deterministic_snapshot() if _onboarding_panel != null else {},
		"focused_control": get_viewport().gui_get_focus_owner().name if get_viewport() != null and get_viewport().gui_get_focus_owner() != null else "",
		"main_menu_scroll": _scroll_contract(_main_menu_scroll),
		"controls_scroll": _scroll_contract(_controls_scroll),
		"about_scroll": _scroll_contract(_about_scroll),
		"right_inspector_order": _visible_direct_child_names(_right_column),
		"top_status_badge_text": _top_state_badge_label.text if _top_state_badge_label != null else "",
		"top_status_badge_color": _top_state_badge_label.get_theme_color("font_color") if _top_state_badge_label != null else Color.TRANSPARENT,
		"top_status_badge_border_color": _label_style_border_color(_top_state_badge_label),
		"restart_game_button_visible": _restart_game_button.visible if _restart_game_button != null else false,
		"restart_game_button_text": _restart_game_button.text if _restart_game_button != null else "",
		"authority_text": _authority_label.text if _authority_label != null else "",
		"inspector_status_text": _trace_integrity_label.text if _trace_integrity_label != null else "",
		"main_menu_text": _collect_label_text(_main_menu_screen),
		"about_text": _collect_label_text(_about_screen),
		"style_theme_id": _style_manager.get_theme_id(),
		"background_color": _style_manager.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY),
		"board_background_color": _style_manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD),
		"hint_color": _style_manager.get_color(ShellStyleRolesScript.LABEL_HINT),
		"game_area_panel_color": _panel_style_color(_game_area),
		"game_area_border_color": _panel_style_border_color(_game_area),
		"bottom_bar_border_color": _panel_style_border_color(_bottom_panel),
	}


func style_manager():
	return _style_manager


func show_replay_viewer() -> void:
	show_screen(SCREEN_VIEWER)


func current_screen() -> String:
	return _current_screen


func game_viewport_global_rect() -> Rect2:
	if _game_viewport_container == null or not _game_viewport_container.is_inside_tree():
		return Rect2()
	return _game_viewport_container.get_global_rect()


func set_live_keyboard_capture(enabled: bool) -> void:
	_set_focus_mode_recursive(_viewer_screen, Control.FOCUS_NONE if enabled else Control.FOCUS_ALL)
	var viewport := get_viewport()
	if enabled and viewport != null:
		var focus_owner := viewport.gui_get_focus_owner()
		if focus_owner != null and _viewer_screen != null and _viewer_screen.is_ancestor_of(focus_owner):
			focus_owner.release_focus()


func apply_shell_settings() -> void:
	if _settings_panel != null:
		_settings_panel.apply_initial_settings()


func _wire_settings_panel(panel: SettingsPanel) -> void:
	panel.setting_changed.connect(func(setting_id: String, value) -> void:
		_sync_setting_controls(panel, setting_id)
	)
	panel.playback_speed_changed.connect(func(value: float) -> void:
		playback_speed_changed.emit(value)
	)
	panel.replay_loop_changed.connect(func(enabled: bool) -> void:
		replay_loop_changed.emit(enabled)
	)
	panel.display_w_labels_changed.connect(func(visible: bool) -> void:
		display_w_labels_changed.emit(visible)
	)
	panel.projection_strength_changed.connect(func(value: float) -> void:
		projection_strength_changed.emit(value)
	)
	panel.display_mode_changed.connect(func(mode: String) -> void:
		display_mode_changed.emit(mode)
	)
	panel.layout_bounds_visibility_changed.connect(func(visible: bool) -> void:
		_set_layout_bounds_visible(visible)
	)
	panel.keyboard_hints_visibility_changed.connect(func(visible: bool) -> void:
		_set_keyboard_hints_visible(visible)
	)
	panel.onboarding_visibility_changed.connect(func(visible: bool) -> void:
		_set_onboarding_visible(visible)
	)
	panel.settings_reset.connect(func() -> void:
		_sync_all_setting_controls(panel)
	)


func _sync_setting_controls(source: SettingsPanel, setting_id: String) -> void:
	for panel in [_settings_panel, _settings_screen_panel]:
		if panel != null and panel != source:
			panel.refresh_setting_value(setting_id)


func _sync_all_setting_controls(source: SettingsPanel = null) -> void:
	for panel in [_settings_panel, _settings_screen_panel]:
		if panel != null and panel != source:
			panel.refresh_all_controls()


func _set_persistent_setting(setting_id: String, value) -> void:
	if _settings_store != null and _settings_store.set_value(setting_id, value):
		_sync_all_setting_controls()
	if setting_id == "interface.show_onboarding":
		_set_onboarding_visible(bool(_settings_store.value(setting_id)))


func _update_live_status_strip(mode_label: String, state_label: String, reason: String, mode: String) -> void:
	if _bundle_status_label != null:
		_bundle_status_label.text = "TET4D"
	if _summary_label != null:
		var state_part := "GAME OVER · %s" % _game_over_reason_label(reason) if state_label == "Game Over" else state_label
		_summary_label.text = "%s | C++ Session | %s | Fit View | Reset | Esc" % [mode_label, state_part]
	if _authority_label != null:
		_authority_label.text = "%s | C++ PlainNDSession | Godot shell" % mode_label
	if _top_state_badge_label != null:
		_top_state_badge_label.text = _status_badge_text(state_label, reason)
		_top_state_badge_label.theme_type_variation = "StatusErrorLabel" if state_label == "Game Over" else "StatusAccentLabel"
		_style_applier.apply_to_tree(_top_state_badge_label, _style_manager)
	if _restart_game_button != null:
		_restart_game_button.visible = state_label == "Game Over"
		_restart_game_button.text = "Restart Game"


func _update_live_gameplay_summary(snapshot: Dictionary, mode_label: String) -> void:
	if _summary_label != null:
		_summary_label.text = live_gameplay_summary_text(snapshot, mode_label)


static func live_gameplay_summary_text(snapshot: Dictionary, mode_label: String) -> String:
	var current_piece := str(snapshot.get("current_piece", "-")).strip_edges()
	var next_piece := str(snapshot.get("next_piece", "-")).strip_edges()
	return "%s | SCORE %d | CLEARS %d | %s > %s | %s" % [
		mode_label,
		int(snapshot.get("score", 0)),
		int(snapshot.get("lines", 0)),
		current_piece if not current_piece.is_empty() else "-",
		next_piece if not next_piece.is_empty() else "-",
		_live_feedback_short(snapshot),
	]


static func live_command_feedback_text(snapshot: Dictionary) -> String:
	if bool(snapshot.get("game_over", false)):
		return "Game over · %s · Restart Game or Main Menu" % _game_over_reason_label(str(snapshot.get("game_over_reason", "")))
	if bool(snapshot.get("paused", false)):
		return "Paused · P — Resume · Esc — Main Menu"
	var command := str(snapshot.get("last_command", "none"))
	var status := str(snapshot.get("last_command_status", "unknown"))
	if command == "hard_drop" and status == "accepted":
		return "Piece locked"
	if status not in ["accepted", "reset"]:
		return _blocked_command_feedback(command)
	return "%s · %s" % [_command_display_name(command), status.to_upper()]


static func _command_display_name(command: String) -> String:
	var normalized := command.strip_edges()
	if normalized.is_empty() or normalized == "none":
		return "READY"
	return normalized.replace("_", " ").to_upper()


static func _blocked_command_feedback(command: String) -> String:
	if command.begins_with("rotate"):
		return "Cannot rotate there"
	if command in ["soft_drop", "hard_drop", "tick"]:
		return "Piece cannot drop further"
	return "Cannot move there"


static func _live_feedback_short(snapshot: Dictionary) -> String:
	if bool(snapshot.get("game_over", false)):
		return "GAME OVER"
	if bool(snapshot.get("paused", false)):
		return "PAUSED"
	var command := str(snapshot.get("last_command", "none"))
	var status := str(snapshot.get("last_command_status", "unknown"))
	if command == "hard_drop" and status == "accepted":
		return "LOCKED"
	if status not in ["accepted", "reset"]:
		return "BLOCKED"
	return "READY" if status == "reset" else _command_display_name(command)


func _set_live_declutter_mode(live_mode: bool) -> void:
	if _left_panel != null:
		_left_panel.visible = not live_mode
		_left_panel.custom_minimum_size = Vector2(0, 0) if live_mode else Vector2(ReplayVisuals.LEFT_PANEL_WIDTH, 0)
	if _bottom_panel != null:
		_bottom_panel.visible = not live_mode
	if _restart_game_button != null and not live_mode:
		_restart_game_button.visible = false
	if _mode_hint_strip != null:
		_mode_hint_strip.visible = (not live_mode) and _keyboard_hints_visible
	if _hint_label != null:
		_hint_label.visible = (not live_mode) and _keyboard_hints_visible
	if not live_mode and _bundle_status_label != null:
		_bundle_status_label.text = _bundle_status_text if _bundle_status_text != "" else "Bundle"
	if not live_mode and _bundle_detail_label != null:
		_bundle_detail_label.text = _bundle_status_detail if _bundle_status_detail != "" else _bundle_status_text
	if _viewport_hint != null:
		_viewport_hint.visible = not live_mode
		if live_mode:
			_viewport_hint.text = ""
	if _hash_label != null:
		_hash_label.visible = not live_mode
		if live_mode:
			_hash_label.text = ""
	if _quit_button != null:
		_quit_button.text = "Quit Application"
	if _diagnostics_panel != null:
		_diagnostics_panel.set_title("Diagnostics" if live_mode else "Replay Diagnostics")
	_set_live_inspector_density(live_mode)
	if not live_mode and _onboarding_panel != null:
		_onboarding_panel.visible = false


func _render_onboarding() -> void:
	if _onboarding_panel != null:
		_onboarding_panel.render(_onboarding_model.snapshot())


func _set_onboarding_visible(visible: bool) -> void:
	_onboarding_model.set_enabled(visible)
	_render_onboarding()


func _set_live_inspector_density(live_mode: bool) -> void:
	if _right_column == null:
		return
	if live_mode:
		_move_right_column_child(_onboarding_panel, 0)
		_move_right_column_child(_controls_header, 1)
		_move_right_column_child(_inspector_hint_panel, 2)
		_move_right_column_child(_inspector_header, 3)
		_move_right_column_child(_integrity_panel, 4)
		_move_right_column_child(_bundle_detail_panel, 5)
		_move_right_column_child(_view_header, 6)
		_move_right_column_child(_camera_panel, 7)
		_move_right_column_child(_diagnostics_header, 8)
		_move_right_column_child(_diagnostics_panel, 9)
		_move_right_column_child(_event_panel, 10)
		_move_right_column_child(_quick_settings_header, 11)
		_move_right_column_child(_settings_panel, 12)
		return
	_move_right_column_child(_inspector_header, 0)
	_move_right_column_child(_integrity_panel, 1)
	_move_right_column_child(_bundle_detail_panel, 2)
	_move_right_column_child(_view_header, 3)
	_move_right_column_child(_camera_panel, 4)
	_move_right_column_child(_controls_header, 5)
	_move_right_column_child(_inspector_hint_panel, 6)
	_move_right_column_child(_onboarding_panel, 7)
	_move_right_column_child(_diagnostics_header, 8)
	_move_right_column_child(_diagnostics_panel, 9)
	_move_right_column_child(_event_panel, 10)
	_move_right_column_child(_quick_settings_header, 11)
	_move_right_column_child(_settings_panel, 12)


func _move_right_column_child(node: Node, index: int) -> void:
	if node != null and node.get_parent() == _right_column:
		_right_column.move_child(node, index)


func _status_badge_text(state_label: String, reason: String) -> String:
	if state_label == "Game Over":
		return "[ GAME OVER ] %s" % _game_over_reason_label(reason)
	if state_label == "Paused":
		return "[ PAUSED ]"
	return "[ RUNNING ]"


static func game_over_reason_label(reason: String) -> String:
	return _game_over_reason_label(reason)


static func _game_over_reason_label(reason: String) -> String:
	var normalized := reason.strip_edges()
	match normalized:
		"", "stopped":
			return "Stopped"
		"out_of_bounds":
			return "Piece out of bounds"
		"spawn_blocked":
			return "Spawn blocked"
		"locked_above_top":
			return "Locked above board"
		_:
			var words := normalized.replace("_", " ")
			return words.capitalize() if not words.is_empty() else "Stopped"


func _format_live_inspector_text(
	mode_label: String,
	state_label: String,
	reason: String,
	last_input: String,
	layout_text: String,
	camera_text: String
) -> String:
	return "\n".join([
		"SESSION",
		"Mode        %s" % mode_label,
		"Engine      C++ PlainNDSession",
		"Shell       Godot command/render",
		"Topology    Plain bounded",
		"",
		"STATUS",
		"State       %s" % _status_badge_text(state_label, reason),
		"Reason      %s" % _game_over_reason_label(reason),
		"Last input  %s" % (last_input if last_input != "" else "none"),
		"",
		"VIEW",
		"Layout      %s" % layout_text,
		"Fit         Restored / Manual",
		"Camera      %s" % camera_text,
	])


func _set_layout_bounds_visible(visible: bool) -> void:
	_geometry_diagnostics_enabled = visible
	_log_geometry_diagnostics("settings")


func _set_keyboard_hints_visible(visible: bool) -> void:
	_keyboard_hints_visible = visible
	if _mode_hint_strip != null:
		_mode_hint_strip.visible = visible and (_bottom_panel == null or _bottom_panel.visible)
	if _hint_label != null:
		_hint_label.visible = visible and (_bottom_panel == null or _bottom_panel.visible)
	if _help_panel != null and not visible:
		_help_panel.visible = false


func _install_shell_layout_contract() -> void:
	var minimum_size := ReplayVisuals.supported_shell_minimum_size()
	custom_minimum_size = minimum_size
	var parent_control := get_parent() as Control
	if parent_control != null:
		parent_control.custom_minimum_size = minimum_size
	var window := get_window()
	if window != null:
		window.min_size = Vector2i(int(minimum_size.x), int(minimum_size.y))


func _build_layout() -> void:
	_background_rect = ColorRect.new()
	_background_rect.name = "ShellBackground"
	_background_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fill_parent(_background_rect)
	add_child(_background_rect)

	var root := MarginContainer.new()
	_fill_parent(root)
	root.custom_minimum_size = ReplayVisuals.supported_shell_minimum_size()
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
	_viewer_screen.custom_minimum_size = ReplayVisuals.supported_shell_minimum_size()
	screen_stack.add_child(_viewer_screen)
	var outer := VBoxContainer.new()
	_fill_parent(outer)
	outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.custom_minimum_size = ReplayVisuals.supported_shell_minimum_size()
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
	var live_4d_button := Button.new()
	live_4d_button.text = "Live 4D"
	live_4d_button.pressed.connect(func() -> void:
		live_4d_requested.emit()
	)
	nav_row_b.add_child(live_4d_button)

	_top_status_panel = PanelContainer.new()
	_top_status_panel.name = "TopStatusPanel"
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
	top_summary_panel.name = "TopReplaySummaryPanel"
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
	_top_state_badge_label = Label.new()
	_top_state_badge_label.name = "TopStatusBadgeLabel"
	_top_state_badge_label.text = "[ PAUSED ]"
	_top_state_badge_label.theme_type_variation = "StatusAccentLabel"
	_top_state_badge_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	top_summary_box.add_child(_top_state_badge_label)
	_restart_game_button = Button.new()
	_restart_game_button.name = "RestartGameButton"
	_restart_game_button.text = "Restart Game"
	_restart_game_button.visible = false
	_restart_game_button.pressed.connect(func() -> void:
		reset_requested.emit()
	)
	top_summary_box.add_child(_restart_game_button)

	_authority_panel = PanelContainer.new()
	_authority_panel.name = "AuthorityPanel"
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
	body.custom_minimum_size = Vector2(ReplayVisuals.BODY_MIN_WIDTH, ReplayVisuals.BODY_MIN_HEIGHT)
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
	_mode_hint_strip = _make_control_hint_panel("replay", true)
	_mode_hint_strip.name = "ViewportControlHints"
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
	_right_scroll.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_MIN_WIDTH, 0)
	_right_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(_right_scroll)

	_right_column = VBoxContainer.new()
	_right_column.name = "RightInspectorContent"
	_right_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_right_column.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_MIN_WIDTH, 0)
	_right_column.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	_right_scroll.add_child(_right_column)

	_inspector_header = _inspector_section_header("INSPECTOR")
	_right_column.add_child(_inspector_header)
	_integrity_panel = PanelContainer.new()
	_integrity_panel.name = "InspectorTracePanel"
	_integrity_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.add_child(_integrity_panel)
	_trace_integrity_label = Label.new()
	_trace_integrity_label.name = "InspectorTraceValueLabel"
	_trace_integrity_label.text = "Trace metadata pending"
	_trace_integrity_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_trace_integrity_label.theme_type_variation = "AccentLabel"
	_integrity_panel.add_child(_trace_integrity_label)

	_bundle_detail_panel = PanelContainer.new()
	_bundle_detail_panel.name = "InspectorBundlePanel"
	_bundle_detail_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.add_child(_bundle_detail_panel)
	var bundle_detail_box := VBoxContainer.new()
	_bundle_detail_panel.add_child(bundle_detail_box)
	var bundle_detail_title := Label.new()
	bundle_detail_title.name = "InspectorSectionHeader__Bundle"
	bundle_detail_title.text = "Bundle Detail"
	bundle_detail_title.theme_type_variation = "SecondaryLabel"
	bundle_detail_box.add_child(bundle_detail_title)
	_bundle_detail_label = Label.new()
	_bundle_detail_label.name = "InspectorMetadataValueLabel"
	_bundle_detail_label.text = "Bundle detail pending"
	_bundle_detail_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_bundle_detail_label.theme_type_variation = "DimLabel"
	bundle_detail_box.add_child(_bundle_detail_label)

	_view_header = _inspector_section_header("VIEW")
	_right_column.add_child(_view_header)
	_camera_panel = PanelContainer.new()
	_camera_panel.name = "InspectorCameraPanel"
	_camera_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_right_column.add_child(_camera_panel)
	var camera_box := VBoxContainer.new()
	_camera_panel.add_child(camera_box)
	var camera_title := Label.new()
	camera_title.name = "InspectorSectionHeader__Camera"
	camera_title.text = "Camera"
	camera_title.theme_type_variation = "SecondaryLabel"
	camera_box.add_child(camera_title)
	_camera_status_label = Label.new()
	_camera_status_label.name = "InspectorCameraValueLabel"
	_camera_status_label.text = "Camera: pending"
	_camera_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_camera_status_label.theme_type_variation = "AccentLabel"
	camera_box.add_child(_camera_status_label)

	_controls_header = _inspector_section_header("CONTROLS")
	_right_column.add_child(_controls_header)
	_inspector_hint_panel = _make_control_hint_panel("replay", false)
	_inspector_hint_panel.name = "InspectorControlHints"
	_right_column.add_child(_inspector_hint_panel)
	_onboarding_panel = LiveOnboardingPanelScript.new()
	_onboarding_panel.visible = false
	_onboarding_panel.dismiss_requested.connect(func() -> void:
		_set_persistent_setting("interface.show_onboarding", false)
	)
	_right_column.add_child(_onboarding_panel)
	_diagnostics_header = _inspector_section_header("DIAGNOSTICS")
	_right_column.add_child(_diagnostics_header)
	_diagnostics_panel = DiagnosticsPanelScript.new()
	_diagnostics_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.DIAGNOSTICS_MIN_HEIGHT)
	_right_column.add_child(_diagnostics_panel)
	_event_panel = EventListPanelScript.new()
	_event_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.EVENTS_MIN_HEIGHT)
	_right_column.add_child(_event_panel)
	_settings_panel = SettingsPanelScript.new()
	_settings_panel.custom_minimum_size = Vector2(ReplayVisuals.RIGHT_PANEL_WIDTH, ReplayVisuals.SETTINGS_MIN_HEIGHT)
	_settings_panel.registry = _settings_registry
	_settings_panel.set_store(_settings_store)
	_settings_panel.set_style_manager(_style_manager)
	_wire_settings_panel(_settings_panel)
	_quick_settings_header = _inspector_section_header("QUICK SETTINGS")
	_right_column.add_child(_quick_settings_header)
	_right_column.add_child(_settings_panel)

	var bottom_panel := PanelContainer.new()
	_bottom_panel = bottom_panel
	bottom_panel.name = "BottomReplayControls"
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
	var footer_menu_button := Button.new()
	footer_menu_button.text = "Main Menu"
	footer_menu_button.pressed.connect(func() -> void:
		main_menu_requested.emit()
	)
	control_group.add_child(footer_menu_button)
	_quit_button = _make_quit_button("Quit Application")
	control_group.add_child(_quit_button)
	var geometry_toggle := CheckBox.new()
	geometry_toggle.text = "Geom"
	geometry_toggle.tooltip_text = "Print viewer layout rectangles"
	geometry_toggle.toggled.connect(func(visible: bool) -> void:
		_geometry_diagnostics_enabled = visible
		_log_geometry_diagnostics("toggle")
	)
	control_group.add_child(geometry_toggle)

	_replay_note = Label.new()
	_replay_note.text = "Replay shell only. Vector Arcade is the product display default; Godot does not implement gameplay."
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
	for speed in [0.25, 0.5, 1.0, 2.0, 3.0]:
		_speed_select.add_item("%sx" % speed)
		_speed_select.set_item_metadata(_speed_select.item_count - 1, speed)
	_speed_select.item_selected.connect(func(index: int) -> void:
		playback_speed_changed.emit(float(_speed_select.get_item_metadata(index)))
	)
	speed_group.add_child(_speed_select)
	_speed_value = Label.new()
	_speed_value.name = "PlaybackStateValueLabel"
	_speed_value.text = "Paused Replay"
	speed_group.add_child(_speed_value)

	_frame_label = Label.new()
	_frame_label.name = "FrameValueLabel"
	_frame_label.text = "Frame 0 / 0"
	_frame_label.theme_type_variation = "AccentLabel"
	bottom.add_child(_frame_label)
	_hint_label = _make_control_hint_panel("replay", true)
	_hint_label.name = "BottomControlHints"
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
	_about_screen = _make_screen()
	screen_stack.add_child(_about_screen)
	_build_about_screen(_about_screen)
	_screens = {
		SCREEN_MAIN_MENU: _main_menu_screen,
		SCREEN_BROWSER: _browser_screen,
		SCREEN_VIEWER: _viewer_screen,
		SCREEN_SETTINGS: _settings_screen,
		SCREEN_CONTROLS: _controls_screen,
		SCREEN_DIAGNOSTICS: _diagnostics_screen,
		SCREEN_ABOUT: _about_screen,
	}
	show_screen(SCREEN_MAIN_MENU)


func _make_screen() -> Control:
	var screen := Control.new()
	screen.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_fill_parent(screen)
	return screen


func _build_main_menu_screen(screen: Control) -> void:
	_main_menu_scroll = ScrollContainer.new()
	_main_menu_scroll.name = "MainMenuScroll"
	_main_menu_scroll.focus_mode = Control.FOCUS_ALL
	_main_menu_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_main_menu_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_main_menu_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_main_menu_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_fill_parent(_main_menu_scroll)
	screen.add_child(_main_menu_scroll)
	var center := CenterContainer.new()
	center.custom_minimum_size = Vector2(720, 0)
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	_main_menu_scroll.add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(720, 0)
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
	title.name = "MainMenuTitle"
	title.text = "Tet4D Vector Arcade Cockpit"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.theme_type_variation = "AccentLabel"
	title.add_theme_font_size_override("font_size", 32)
	layout.add_child(title)
	var subtitle := Label.new()
	subtitle.name = "MainMenuSubtitle"
	subtitle.text = "Start with 2D, then explore playable plain-board 3D and 4D modes."
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.theme_type_variation = "SecondaryLabel"
	subtitle.add_theme_font_size_override("font_size", 18)
	layout.add_child(subtitle)
	layout.add_child(_menu_group_header("PLAY"))
	var live_button := _make_command_card("Play 2D", "Plain bounded board · best place to start", "2D")
	live_button.pressed.connect(func() -> void:
		live_2d_requested.emit()
	)
	layout.add_child(live_button)
	var live_3d_button := _make_command_card("Play 3D", "Plain bounded board · direct XY, XZ, and YZ rotations", "3D")
	live_3d_button.pressed.connect(func() -> void:
		live_3d_requested.emit()
	)
	layout.add_child(live_3d_button)
	var live_4d_button := _make_command_card("Play 4D", "Plain bounded board · W-slice view and camera recovery", "4D")
	live_4d_button.pressed.connect(func() -> void:
		live_4d_requested.emit()
	)
	layout.add_child(live_4d_button)
	layout.add_child(_menu_group_header("EXPLORE"))
	var browser_button := _make_command_card("Replay Demos", "Inspect exported gameplay, topology, and endgame traces", "Enter")
	browser_button.pressed.connect(func() -> void:
		show_screen(SCREEN_BROWSER)
	)
	layout.add_child(browser_button)
	layout.add_child(_menu_group_header("LEARN"))
	var controls_button := _make_command_card("How to Play", "Mode-specific piece, camera, session, and navigation controls", "H")
	controls_button.pressed.connect(func() -> void:
		show_screen(SCREEN_CONTROLS)
	)
	layout.add_child(controls_button)
	var about_button := _make_command_card("About Tet4D", "What is playable, where topology lives, and current limits", "A")
	about_button.pressed.connect(func() -> void:
		show_screen(SCREEN_ABOUT)
	)
	layout.add_child(about_button)
	layout.add_child(_menu_group_header("SYSTEM"))
	var settings_button := _make_command_card("Settings", "Display, replay, diagnostics, and shell options", "S")
	settings_button.pressed.connect(func() -> void:
		show_screen(SCREEN_SETTINGS)
	)
	layout.add_child(settings_button)
	var quit_button := _make_command_card("Quit", "Close the Godot product shell", "Esc")
	quit_button.pressed.connect(_emit_quit_requested)
	layout.add_child(quit_button)
	var focus_order: Array[Control] = [live_button, live_3d_button, live_4d_button, browser_button, controls_button, about_button, settings_button, quit_button]
	_configure_linear_focus(focus_order)
	_screen_focus_targets[SCREEN_MAIN_MENU] = live_button


func _build_browser_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	var nav := _screen_nav("Replay Demos")
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
	_settings_screen_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_settings_screen_panel.registry = _settings_registry
	_settings_screen_panel.set_store(_settings_store)
	_settings_screen_panel.set_style_manager(_style_manager)
	_wire_settings_panel(_settings_screen_panel)
	layout.add_child(_settings_screen_panel)
	_screen_focus_targets[SCREEN_SETTINGS] = _settings_screen_panel.first_focus_control()


func _build_controls_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	layout.add_child(_screen_nav("Controls / Keyboard Hints"))
	_controls_scroll = ScrollContainer.new()
	_controls_scroll.name = "ControlsHelpScroll"
	_controls_scroll.focus_mode = Control.FOCUS_ALL
	_controls_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_controls_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_controls_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_controls_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(_controls_scroll)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	grid.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	grid.add_theme_constant_override("h_separation", ReplayVisuals.PANEL_GAP)
	grid.add_theme_constant_override("v_separation", ReplayVisuals.PANEL_GAP)
	_controls_scroll.add_child(grid)
	grid.add_child(_control_mode_card("Replay", "Inspect exported traces frame by frame without moving pieces.", "replay"))
	grid.add_child(_control_mode_card("Live Plain 2D", "Best first play mode with classic movement, rotation, and drop.", "live_2d"))
	grid.add_child(_control_mode_card("Live Plain 3D", "Playable plain 3D with direct XY, XZ, and YZ plane rotations.", "live_3d"))
	grid.add_child(_control_mode_card("Live Plain 4D", "Playable plain 4D with W movement, six rotation planes, and camera recovery.", "live_4d"))
	_screen_focus_targets[SCREEN_CONTROLS] = _controls_scroll


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


func _build_about_screen(screen: Control) -> void:
	var layout := VBoxContainer.new()
	_fill_parent(layout)
	layout.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	layout.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_theme_constant_override("separation", ReplayVisuals.PANEL_GAP)
	screen.add_child(layout)
	layout.add_child(_screen_nav("About / Demo Path"))
	_about_scroll = ScrollContainer.new()
	_about_scroll.name = "AboutScroll"
	_about_scroll.focus_mode = Control.FOCUS_ALL
	_about_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_about_scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	_about_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_about_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	layout.add_child(_about_scroll)
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	_about_scroll.add_child(panel)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_bottom", 20)
	panel.add_child(margin)
	var label := Label.new()
	label.name = "AboutDemoLabel"
	label.text = ABOUT_DEMO_TEXT
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(label)
	_screen_focus_targets[SCREEN_ABOUT] = _about_scroll


func _screen_nav(title_text: String) -> HFlowContainer:
	var nav := HFlowContainer.new()
	nav.add_theme_constant_override("h_separation", ReplayVisuals.CONTROL_GAP)
	nav.add_theme_constant_override("v_separation", ReplayVisuals.CONTROL_GAP)
	var title := Label.new()
	title.text = title_text
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title.theme_type_variation = "AccentLabel"
	nav.add_child(title)
	var menu_button := Button.new()
	menu_button.text = "Back to Main Menu"
	menu_button.pressed.connect(func() -> void:
		show_screen(SCREEN_MAIN_MENU)
	)
	nav.add_child(menu_button)
	var browser_button := Button.new()
	browser_button.text = "Replay Demos"
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
	var live_4d_button := Button.new()
	live_4d_button.text = "Live 4D"
	live_4d_button.pressed.connect(func() -> void:
		live_4d_requested.emit()
	)
	nav.add_child(live_4d_button)
	var diagnostics_button := Button.new()
	diagnostics_button.text = "Diagnostics"
	diagnostics_button.pressed.connect(func() -> void:
		show_screen(SCREEN_DIAGNOSTICS)
	)
	nav.add_child(diagnostics_button)
	var about_button := Button.new()
	about_button.text = "About"
	about_button.pressed.connect(func() -> void:
		show_screen(SCREEN_ABOUT)
	)
	nav.add_child(about_button)
	var settings_button := Button.new()
	settings_button.text = "Settings"
	settings_button.pressed.connect(func() -> void:
		show_screen(SCREEN_SETTINGS)
	)
	nav.add_child(settings_button)
	nav.add_child(_make_quit_button("Quit Application"))
	return nav


func _make_command_card(label_text: String, description: String, shortcut: String) -> Button:
	var button := Button.new()
	button.name = "CommandCard__%s" % label_text.replace(" ", "_")
	button.text = "%s        %s\n%s" % [label_text, shortcut, description]
	button.custom_minimum_size = Vector2(480, 54)
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT
	button.add_theme_font_size_override("font_size", 17)
	button.tooltip_text = "%s - %s" % [label_text, description]
	return button


func _make_quit_button(label_text: String) -> Button:
	var button := Button.new()
	button.name = "QuitApplicationButton"
	button.text = label_text
	button.pressed.connect(_emit_quit_requested)
	return button


func _emit_quit_requested() -> void:
	quit_requested.emit()


func _menu_group_header(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.theme_type_variation = "SecondaryLabel"
	label.add_theme_font_size_override("font_size", 12)
	return label


func _configure_linear_focus(controls: Array[Control]) -> void:
	if controls.is_empty():
		return
	for index in range(controls.size()):
		var control := controls[index]
		var previous := controls[(index - 1 + controls.size()) % controls.size()]
		var next := controls[(index + 1) % controls.size()]
		control.focus_mode = Control.FOCUS_ALL
		control.focus_neighbor_top = control.get_path_to(previous)
		control.focus_neighbor_left = control.get_path_to(previous)
		control.focus_neighbor_bottom = control.get_path_to(next)
		control.focus_neighbor_right = control.get_path_to(next)


func _inspector_section_header(label_text: String) -> Label:
	var label := Label.new()
	label.name = "InspectorSectionHeader__%s" % label_text.replace(" ", "_")
	label.text = label_text
	label.theme_type_variation = "AccentLabel"
	label.add_theme_font_size_override("font_size", 13)
	return label


func _control_mode_card(title_text: String, subtitle: String, mode: String) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.name = "ControlModeCard__%s" % mode
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.size_flags_vertical = Control.SIZE_FILL
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", ReplayVisuals.CONTROL_GAP)
	panel.add_child(content)
	var title := Label.new()
	title.text = title_text
	title.theme_type_variation = "AccentLabel"
	content.add_child(title)
	var description := Label.new()
	description.text = subtitle
	description.theme_type_variation = "SecondaryLabel"
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(description)
	content.add_child(_make_control_hint_panel(mode, false))
	return panel


func _make_control_hint_panel(mode: String, compact: bool = false) -> VBoxContainer:
	var panel := VBoxContainer.new()
	panel.name = "ControlHintPanel__%s" % mode
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_theme_constant_override("separation", ReplayVisuals.SPEED_GROUP_GAP)
	panel.set_meta("hint_compact", compact)
	_update_control_hint_panel(panel, mode, false, "", compact)
	return panel


func _update_control_hint_panel(
	panel: VBoxContainer,
	mode: String,
	warning: bool = false,
	warning_text: String = "",
	compact: bool = false
) -> void:
	if panel == null:
		return
	compact = bool(panel.get_meta("hint_compact", compact))
	var cache_key := "%s|%s|%s|%s" % [mode, str(warning), warning_text, str(compact)]
	if str(panel.get_meta("hint_cache_key", "")) == cache_key:
		return
	panel.set_meta("hint_cache_key", cache_key)
	panel.set_meta("hint_mode", mode)
	panel.set_meta("hint_warning", warning)
	panel.set_meta("hint_compact", compact)
	for child in panel.get_children():
		panel.remove_child(child)
		child.queue_free()
	if warning and warning_text != "":
		var warning_label := Label.new()
		warning_label.name = "ControlHintWarning"
		warning_label.text = "GAME OVER · %s" % _game_over_reason_label(warning_text)
		warning_label.theme_type_variation = "WarningLabel"
		panel.add_child(warning_label)
	var groups := quick_control_hint_groups(mode) if compact else _control_hint_groups_for_mode(mode)
	for group in groups:
		panel.add_child(_control_hint_group(group, compact))
	if is_inside_tree():
		_style_applier.apply_to_tree(panel, _style_manager)


func _control_hint_groups_for_mode(mode: String) -> Array:
	match mode:
		"live_2d":
			return live_2d_control_hint_groups()
		"live_3d":
			return live_3d_control_hint_groups()
		"live_4d":
			return live_4d_control_hint_groups()
		_:
			return replay_control_hint_groups()


func _control_hint_group(group: Dictionary, compact: bool) -> Control:
	if compact:
		var compact_row := HFlowContainer.new()
		compact_row.name = "ControlHintGroup__%s" % str(group.get("group", "")).replace(" ", "_")
		compact_row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		compact_row.add_theme_constant_override("h_separation", 6)
		compact_row.add_theme_constant_override("v_separation", 4)
		var compact_title := Label.new()
		compact_title.name = "ControlHintSectionHeader"
		compact_title.text = str(group.get("group", ""))
		compact_title.theme_type_variation = "SecondaryLabel"
		compact_title.custom_minimum_size = Vector2(56, 20)
		compact_row.add_child(compact_title)
		for item in group.get("items", []):
			var keycap := Label.new()
			keycap.name = "ControlHintKeycap"
			keycap.text = str(item[0])
			keycap.custom_minimum_size = Vector2(52, 20)
			keycap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			keycap.theme_type_variation = "KeycapLabel"
			compact_row.add_child(keycap)
			var action := Label.new()
			action.name = "ControlHintAction"
			action.text = str(item[1])
			action.theme_type_variation = "DimLabel"
			compact_row.add_child(action)
		return compact_row
	var box := VBoxContainer.new()
	box.name = "ControlHintGroup__%s" % str(group.get("group", "")).replace(" ", "_")
	box.add_theme_constant_override("separation", 3)
	var title := Label.new()
	title.name = "ControlHintSectionHeader"
	title.text = str(group.get("group", ""))
	title.theme_type_variation = "SecondaryLabel"
	title.add_theme_font_size_override("font_size", 12 if compact else 13)
	box.add_child(title)
	if group.has("note"):
		var note := Label.new()
		note.name = "ControlHintNote"
		note.text = str(group.get("note", ""))
		note.theme_type_variation = "DimLabel"
		note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		box.add_child(note)
	for item in group.get("items", []):
		var row := HBoxContainer.new()
		row.name = "ControlHintRow"
		row.add_theme_constant_override("separation", 6)
		var keycap := Label.new()
		keycap.name = "ControlHintKeycap"
		keycap.text = str(item[0])
		keycap.custom_minimum_size = Vector2(70 if compact else 82, 20)
		keycap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		keycap.theme_type_variation = "KeycapLabel"
		row.add_child(keycap)
		var action := Label.new()
		action.name = "ControlHintAction"
		action.text = str(item[1])
		action.theme_type_variation = "DimLabel" if compact else "SecondaryLabel"
		action.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		action.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(action)
		box.add_child(row)
	return box


func _fill_parent(control: Control) -> void:
	control.set_anchors_preset(Control.PRESET_FULL_RECT)
	control.offset_left = 0.0
	control.offset_top = 0.0
	control.offset_right = 0.0
	control.offset_bottom = 0.0


func _apply_shell_style() -> void:
	if _background_rect != null:
		_background_rect.color = _style_manager.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY)
	if _game_viewport != null:
		_game_viewport.transparent_bg = false
		_game_viewport.get_world_3d()
	_style_applier.apply_to_tree(self, _style_manager)
	if _settings_panel != null:
		_settings_panel.apply_shell_style()
	if _settings_screen_panel != null:
		_settings_screen_panel.apply_shell_style()


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


func _scroll_contract(scroll: ScrollContainer) -> Dictionary:
	if scroll == null:
		return {}
	var content := scroll.get_child(0) as Control if scroll.get_child_count() > 0 else null
	return {
		"visible": scroll.visible,
		"rect": _control_rect(scroll),
		"content_height": content.size.y if content != null else 0.0,
		"viewport_height": scroll.size.y,
		"vertical_scroll_enabled": scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED,
	}


func _panel_style_color(node: Control) -> Color:
	var style := _panel_style_box(node)
	return style.bg_color if style != null else Color.TRANSPARENT


func _panel_style_border_color(node: Control) -> Color:
	var style := _panel_style_box(node)
	return style.border_color if style != null else Color.TRANSPARENT


func _label_style_border_color(node: Control) -> Color:
	var style := node.get_theme_stylebox("normal") as StyleBoxFlat if node != null else null
	return style.border_color if style != null else Color.TRANSPARENT


func _panel_style_box(node: Control) -> StyleBoxFlat:
	if node == null:
		return null
	return node.get_theme_stylebox("panel") as StyleBoxFlat


func _collect_label_text(node: Node) -> String:
	if node == null:
		return ""
	var parts: Array = []
	_collect_label_text_into(node, parts)
	return " ".join(parts)


func _visible_direct_child_names(node: Node) -> Array:
	var names: Array = []
	if node == null:
		return names
	for child in node.get_children():
		if child is CanvasItem and not (child as CanvasItem).visible:
			continue
		names.append(str(child.name))
	return names


func _collect_label_text_into(node: Node, parts: Array) -> void:
	if node is CanvasItem and not (node as CanvasItem).visible:
		return
	if node is Label:
		parts.append((node as Label).text)
	for child in node.get_children():
		_collect_label_text_into(child, parts)


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


func _set_focus_mode_recursive(node: Node, focus_mode: FocusMode) -> void:
	if node == null:
		return
	if node is Button or node is OptionButton or node is HSlider:
		(node as Control).focus_mode = focus_mode
	for child in node.get_children():
		_set_focus_mode_recursive(child, focus_mode)
