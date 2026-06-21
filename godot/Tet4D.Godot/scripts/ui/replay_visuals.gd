extends RefCounted

class_name ReplayVisuals

const DIAGNOSTIC_THEME_PATH := "res://themes/replay_diagnostic_theme.tres"
const TRON_THEME_PATH := "res://themes/replay_tron_theme.tres"
const PLAIN_THEME_PATH := "res://themes/replay_theme.tres"

const DISPLAY_MODE_DIAGNOSTIC := "diagnostic"
const DISPLAY_MODE_TRON := "tron"
const DISPLAY_MODE_PLAIN := "plain"
const DISPLAY_MODES := [
	DISPLAY_MODE_DIAGNOSTIC,
	DISPLAY_MODE_TRON,
	DISPLAY_MODE_PLAIN,
]

const OUTER_MARGIN := 12
const BODY_GAP := 10
const PANEL_GAP := 12
const TOP_BAR_HEIGHT := 80
const TIMELINE_HEIGHT := 104
const LEFT_PANEL_WIDTH := 300
const RIGHT_INSPECTOR_WIDTH := 360
const RIGHT_PANEL_WIDTH := RIGHT_INSPECTOR_WIDTH
const RIGHT_PANEL_MIN_WIDTH := RIGHT_INSPECTOR_WIDTH
const RIGHT_PANEL_COMPACT_WIDTH := RIGHT_INSPECTOR_WIDTH
const GAME_AREA_MIN_WIDTH := 120
const VIEWPORT_PANEL_MIN_WIDTH := GAME_AREA_MIN_WIDTH
const VIEWPORT_PANEL_COMPACT_MIN_WIDTH := GAME_AREA_MIN_WIDTH
const BODY_MIN_HEIGHT := 400
const BODY_MIN_WIDTH := LEFT_PANEL_WIDTH + GAME_AREA_MIN_WIDTH + RIGHT_PANEL_MIN_WIDTH + (BODY_GAP * 2)
const SHELL_MIN_WIDTH := BODY_MIN_WIDTH + (OUTER_MARGIN * 2)
const SHELL_MIN_HEIGHT := TOP_BAR_HEIGHT + BODY_MIN_HEIGHT + TIMELINE_HEIGHT + (OUTER_MARGIN * 2)
const PANEL_SECTION_GAP := 10
const CONTROL_GAP := 8
const TOP_STATUS_PANEL_WIDTH := 300
const AUTHORITY_PANEL_WIDTH := 280
const VIEWPORT_FRAME_PADDING := 12
const SPEED_SLIDER_WIDTH := 120
const SPEED_GROUP_GAP := 6
const CASE_BROWSER_MIN_HEIGHT := 340
const DIAGNOSTICS_MIN_HEIGHT := 260
const EVENTS_MIN_HEIGHT := 170
const SETTINGS_MIN_HEIGHT := 112

const CELL_SCALE := 0.9
const ACTIVE_GAMEPLAY_CELL_SCALE := 0.72
const LIVE_ACTIVE_CELL_SCALE := 0.86
const LIVE_LOCKED_CELL_SCALE := 0.82
const LIVE_CELL_DEPTH := 0.08
const LIVE_CELL_BORDER_DELTA := 0.055
const LIVE_3D_ACTIVE_CELL_SCALE := 0.86
const LIVE_3D_LOCKED_CELL_SCALE := 0.78
const LIVE_3D_CELL_BORDER_DELTA := 0.045
const LIVE_3D_ACTIVE_CELL_BORDER_DELTA := 0.07
const LIVE_3D_LOCKED_CELL_BORDER_DELTA := 0.032
const LIVE_3D_ORIGIN_MARKER_SCALE := 0.18
const PARTICLE_SCALE := 0.24
const EVENT_SCALE := 0.5
const SLICE_PADDING := 2.0
const GRID_LINE_THICKNESS := 0.045
const W_SLICE_LABEL_FONT_SIZE := 86
const W_SLICE_LABEL_OUTLINE_SIZE := 28
const W_SLICE_LABEL_CHIP_WIDTH := 4.85
const W_SLICE_LABEL_CHIP_HEIGHT := 0.88
const W_SLICE_LABEL_CHIP_DEPTH := 0.045
const W_SLICE_LABEL_VERTICAL_OFFSET := 1.12
const W_SLICE_LABEL_BOUNDS_PAD := 1.72
const PROBE_MARKER_HEIGHT := 0.32
const EVENT_MARKER_HEIGHT := 0.62
const PARTICLE_TRAIL_HISTORY := 14

const ROLE_ACTIVE_CELL := "active_cell"
const ROLE_LOCKED_CELL := "locked_cell"
const ROLE_PROBE_BEFORE := "probe_before"
const ROLE_PROBE_AFTER := "probe_after"
const ROLE_PARTICLE := "particle"
const ROLE_PARTICLE_ESCAPED := "particle_escaped"
const ROLE_PARTICLE_CORE := "particle_core"
const ROLE_PARTICLE_CORE_ESCAPED := "particle_core_escaped"
const ROLE_BOARD_OUTLINE := "board_outline"
const ROLE_LIVE_CELL_ACTIVE_BORDER := "live_cell_active_border"
const ROLE_LIVE_CELL_LOCKED_BORDER := "live_cell_locked_border"
const ROLE_LIVE_3D_ACTIVE := "live_3d_active"
const ROLE_LIVE_3D_LOCKED := "live_3d_locked"
const ROLE_LIVE_3D_OUTLINE := "live_3d_outline"
const ROLE_LIVE_3D_ACTIVE_OUTLINE := "live_3d_active_outline"
const ROLE_LIVE_3D_LOCKED_OUTLINE := "live_3d_locked_outline"
const ROLE_LIVE_3D_FACE_HIGHLIGHT := "live_3d_face_highlight"
const ROLE_LIVE_3D_ORIGIN_MARKER := "live_3d_origin_marker"
const ROLE_LIVE_BOARD_FILL := "live_board_fill"
const ROLE_LIVE_BOARD_GRID := "live_board_grid"
const ROLE_W_SLICE_OUTLINE := "w_slice_outline"
const ROLE_W_SLICE_LABEL := "w_slice_label"
const ROLE_EVENT_MARKER := "event_marker"
const ROLE_BACKGROUND := "background"
const ROLE_PANEL_BACKGROUND := "panel_background"
const ROLE_PANEL_QUIET := "panel_quiet"
const ROLE_PANEL_ALT := "panel_alt"
const ROLE_BORDER := "border"
const ROLE_BORDER_SOFT := "border_soft"
const ROLE_TEXT := "text"
const ROLE_TEXT_SECONDARY := "text_secondary"
const ROLE_TEXT_DIM := "text_dim"
const ROLE_ACCENT := "accent"
const ROLE_ACCENT_SOFT := "accent_soft"
const ROLE_SUCCESS := "success"
const ROLE_WARNING := "warning"
const ROLE_VIEWPORT_FRAME := "viewport_frame"

const TRACE_COLOR_PALETTE := [
	Color(0.78, 0.78, 0.78, 1.0),
	Color(0.0, 1.0, 1.0, 1.0),
	Color(1.0, 1.0, 0.0, 1.0),
	Color(0.63, 0.0, 0.94, 1.0),
	Color(0.0, 1.0, 0.0, 1.0),
	Color(1.0, 0.0, 0.0, 1.0),
	Color(0.0, 0.0, 1.0, 1.0),
	Color(1.0, 0.65, 0.0, 1.0),
	Color(0.32, 0.92, 0.65, 1.0),
]


static func default_display_mode() -> String:
	return DISPLAY_MODE_DIAGNOSTIC


static func supported_shell_minimum_size() -> Vector2:
	return Vector2(SHELL_MIN_WIDTH, SHELL_MIN_HEIGHT)


static func normalize_display_mode(mode: String) -> String:
	return mode if DISPLAY_MODES.has(mode) else DISPLAY_MODE_DIAGNOSTIC


static func display_mode_label(mode: String) -> String:
	match normalize_display_mode(mode):
		DISPLAY_MODE_DIAGNOSTIC:
			return "Diagnostic High Contrast"
		DISPLAY_MODE_TRON:
			return "Tron"
		DISPLAY_MODE_PLAIN:
			return "Plain"
		_:
			return DISPLAY_MODE_DIAGNOSTIC.capitalize()


static func authority_label(mode: String) -> String:
	return "REPLAY · PYTHON ORACLE · %s DISPLAY" % normalize_display_mode(mode).to_upper()


static func color_for_role(role: String, mode: String = DISPLAY_MODE_DIAGNOSTIC) -> Color:
	var palette := _palette(normalize_display_mode(mode))
	return palette.get(role, palette.get(ROLE_TEXT, Color.WHITE))


static func build_theme(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> Theme:
	var display_mode := normalize_display_mode(mode)
	var theme_path := DIAGNOSTIC_THEME_PATH
	match display_mode:
		DISPLAY_MODE_TRON:
			theme_path = TRON_THEME_PATH
		DISPLAY_MODE_PLAIN:
			theme_path = PLAIN_THEME_PATH
	return load(theme_path).duplicate() as Theme


static func active_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	return _make_material(_trace_color(color_id, false), _role_emission(ROLE_ACTIVE_CELL, mode), false)


static func gameplay_active_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_ACTIVE_CELL, mode, _role_emission(ROLE_ACTIVE_CELL, mode))


static func live_active_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.08)
	return _make_material(base, _role_emission(ROLE_ACTIVE_CELL, mode) + 0.1, false)


static func live_3d_active_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.14)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_ACTIVE, mode), false)


static func live_4d_active_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.12).lerp(Color.WHITE, 0.06)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_ACTIVE, mode) * 0.72, false)


static func live_3d_active_face_materials(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.13)
	return _live_3d_face_materials(base, mode, true)


static func live_4d_active_face_materials(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).darkened(0.12).lerp(Color.WHITE, 0.06)
	return _live_3d_face_materials(base, mode, true, _role_emission(ROLE_LIVE_3D_ACTIVE, mode) * 0.72)


static func locked_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LOCKED_CELL, mode, _role_emission(ROLE_LOCKED_CELL, mode))


static func live_locked_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.22).lerp(color_for_role(ROLE_LOCKED_CELL, mode), 0.18)
	return _make_material(base, _role_emission(ROLE_LOCKED_CELL, mode), false)


static func live_3d_locked_cell_material(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.42).lerp(color_for_role(ROLE_LIVE_3D_LOCKED, mode), 0.28)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_LOCKED, mode), false)


static func live_3d_locked_face_materials(mode: String = DISPLAY_MODE_DIAGNOSTIC, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).darkened(0.42).lerp(color_for_role(ROLE_LIVE_3D_LOCKED, mode), 0.28)
	return _live_3d_face_materials(base, mode, false)


static func live_active_cell_border_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_CELL_ACTIVE_BORDER, mode, _role_emission(ROLE_LIVE_CELL_ACTIVE_BORDER, mode))


static func live_locked_cell_border_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_CELL_LOCKED_BORDER, mode, _role_emission(ROLE_LIVE_CELL_LOCKED_BORDER, mode))


static func live_3d_active_cell_border_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_ACTIVE_OUTLINE, mode, _role_emission(ROLE_LIVE_3D_ACTIVE_OUTLINE, mode))


static func live_3d_locked_cell_border_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_LOCKED_OUTLINE, mode, _role_emission(ROLE_LIVE_3D_LOCKED_OUTLINE, mode))


static func live_3d_origin_marker_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_ORIGIN_MARKER, mode, _role_emission(ROLE_LIVE_3D_ORIGIN_MARKER, mode))


static func live_board_fill_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	var material := _role_material(ROLE_LIVE_BOARD_FILL, mode, _role_emission(ROLE_LIVE_BOARD_FILL, mode))
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(material.albedo_color, 0.88)
	return material


static func live_board_grid_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_BOARD_GRID, mode, _role_emission(ROLE_LIVE_BOARD_GRID, mode))


static func probe_before_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_PROBE_BEFORE, mode, _role_emission(ROLE_PROBE_BEFORE, mode))


static func probe_after_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_PROBE_AFTER, mode, _role_emission(ROLE_PROBE_AFTER, mode))


static func particle_material(
	mode: String = DISPLAY_MODE_DIAGNOSTIC,
	escaped: bool = false,
	color_id: int = 0
) -> StandardMaterial3D:
	return _make_material(
		_trace_color(color_id, escaped),
		_role_emission(ROLE_PARTICLE_ESCAPED if escaped else ROLE_PARTICLE, mode),
		false
	)


static func particle_core_material(
	mode: String = DISPLAY_MODE_DIAGNOSTIC,
	escaped: bool = false,
	color_id: int = 0
) -> StandardMaterial3D:
	var base := _trace_color(color_id, escaped).lerp(Color.WHITE, 0.32)
	return _make_material(
		base,
		_role_emission(ROLE_PARTICLE_CORE_ESCAPED if escaped else ROLE_PARTICLE_CORE, mode),
		false
	)


static func particle_trail_material(
	mode: String = DISPLAY_MODE_DIAGNOSTIC,
	escaped: bool = false,
	color_id: int = 0
) -> StandardMaterial3D:
	var color := _trace_color(color_id, escaped).darkened(0.25)
	var material := _make_material(color, 0.75, false)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(color, 0.72)
	return material


static func board_outline_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_BOARD_OUTLINE, mode, _role_emission(ROLE_BOARD_OUTLINE, mode))


static func slice_outline_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_W_SLICE_OUTLINE, mode, _role_emission(ROLE_W_SLICE_OUTLINE, mode))


static func event_marker_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	return _role_material(ROLE_EVENT_MARKER, mode, _role_emission(ROLE_EVENT_MARKER, mode))


static func slice_label_color(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> Color:
	return color_for_role(ROLE_W_SLICE_LABEL, mode)


static func slice_label_chip_material(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> StandardMaterial3D:
	var material := _role_material(ROLE_PANEL_QUIET, mode, 0.18)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(color_for_role(ROLE_PANEL_QUIET, mode), 0.94)
	return material


static func slice_outline_thickness(mode: String = DISPLAY_MODE_DIAGNOSTIC) -> float:
	return GRID_LINE_THICKNESS


static func _palette(mode: String) -> Dictionary:
	var normalized_mode := normalize_display_mode(mode)
	if normalized_mode == DISPLAY_MODE_TRON:
		return {
			ROLE_BACKGROUND: _html("071018"),
			ROLE_PANEL_BACKGROUND: _html("0D1720"),
			ROLE_PANEL_QUIET: _html("0A131B"),
			ROLE_PANEL_ALT: _html("122230"),
			ROLE_BORDER: _html("2E6F82"),
			ROLE_BORDER_SOFT: _html("214E5C"),
			ROLE_TEXT: _html("EAF8FF"),
			ROLE_TEXT_SECONDARY: _html("9CC8D6"),
			ROLE_TEXT_DIM: _html("7EA6B4"),
			ROLE_ACCENT: _html("19D7FF"),
			ROLE_ACCENT_SOFT: _html("103C49"),
			ROLE_SUCCESS: _html("00FFAA"),
			ROLE_WARNING: _html("FFD166"),
			ROLE_EVENT_MARKER: Color(1.0, 0.82, 0.28, 1.0),
			ROLE_ACTIVE_CELL: TRACE_COLOR_PALETTE[1],
			ROLE_LOCKED_CELL: Color(0.36, 0.39, 0.45, 1.0),
			ROLE_PROBE_BEFORE: Color(0.22, 0.94, 0.95, 1.0),
			ROLE_PROBE_AFTER: Color(0.32, 0.92, 0.65, 1.0),
			ROLE_PARTICLE: TRACE_COLOR_PALETTE[2],
			ROLE_PARTICLE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.35),
			ROLE_PARTICLE_CORE: TRACE_COLOR_PALETTE[0].lerp(Color.WHITE, 0.32),
			ROLE_PARTICLE_CORE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.55),
			ROLE_BOARD_OUTLINE: Color(0.38, 0.41, 0.48, 1.0),
			ROLE_LIVE_CELL_ACTIVE_BORDER: Color(0.95, 0.98, 1.0, 1.0),
			ROLE_LIVE_CELL_LOCKED_BORDER: Color(0.04, 0.06, 0.09, 1.0),
			ROLE_LIVE_3D_ACTIVE: Color(0.0, 1.0, 1.0, 1.0),
			ROLE_LIVE_3D_LOCKED: Color(0.32, 0.36, 0.44, 1.0),
			ROLE_LIVE_3D_OUTLINE: Color(0.015, 0.02, 0.03, 1.0),
			ROLE_LIVE_3D_ACTIVE_OUTLINE: Color(0.95, 0.99, 1.0, 1.0),
			ROLE_LIVE_3D_LOCKED_OUTLINE: Color(0.025, 0.035, 0.055, 1.0),
			ROLE_LIVE_3D_FACE_HIGHLIGHT: Color(1.0, 1.0, 1.0, 1.0),
			ROLE_LIVE_3D_ORIGIN_MARKER: Color(1.0, 0.95, 0.28, 1.0),
			ROLE_LIVE_BOARD_FILL: _html("081322"),
			ROLE_LIVE_BOARD_GRID: _html("283B55"),
			ROLE_W_SLICE_OUTLINE: Color(0.38, 0.41, 0.48, 1.0),
			ROLE_W_SLICE_LABEL: Color(0.86, 0.89, 0.94, 1.0),
			ROLE_VIEWPORT_FRAME: _html("0D1720"),
		}
	if normalized_mode == DISPLAY_MODE_PLAIN:
		return {
			ROLE_BACKGROUND: _html("111316"),
			ROLE_PANEL_BACKGROUND: _html("1B1E22"),
			ROLE_PANEL_QUIET: _html("15181C"),
			ROLE_PANEL_ALT: _html("24282E"),
			ROLE_BORDER: _html("C9A45B"),
			ROLE_BORDER_SOFT: _html("6D6554"),
			ROLE_TEXT: _html("F2F0EA"),
			ROLE_TEXT_SECONDARY: _html("C9C2B2"),
			ROLE_TEXT_DIM: _html("A79F8F"),
			ROLE_ACCENT: _html("E4B85F"),
			ROLE_ACCENT_SOFT: _html("3C3322"),
			ROLE_SUCCESS: _html("78D6A3"),
			ROLE_WARNING: _html("E4B85F"),
			ROLE_EVENT_MARKER: Color(0.89, 0.72, 0.37, 1.0),
			ROLE_ACTIVE_CELL: TRACE_COLOR_PALETTE[1],
			ROLE_LOCKED_CELL: Color(0.45, 0.45, 0.48, 1.0),
			ROLE_PROBE_BEFORE: Color(0.40, 0.80, 0.88, 1.0),
			ROLE_PROBE_AFTER: Color(0.47, 0.84, 0.64, 1.0),
			ROLE_PARTICLE: TRACE_COLOR_PALETTE[2],
			ROLE_PARTICLE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.35),
			ROLE_PARTICLE_CORE: TRACE_COLOR_PALETTE[0].lerp(Color.WHITE, 0.32),
			ROLE_PARTICLE_CORE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.55),
			ROLE_BOARD_OUTLINE: Color(0.54, 0.52, 0.48, 1.0),
			ROLE_LIVE_CELL_ACTIVE_BORDER: Color(0.98, 0.96, 0.90, 1.0),
			ROLE_LIVE_CELL_LOCKED_BORDER: Color(0.06, 0.06, 0.07, 1.0),
			ROLE_LIVE_3D_ACTIVE: Color(0.19, 0.82, 0.92, 1.0),
			ROLE_LIVE_3D_LOCKED: Color(0.43, 0.45, 0.48, 1.0),
			ROLE_LIVE_3D_OUTLINE: Color(0.08, 0.08, 0.09, 1.0),
			ROLE_LIVE_3D_ACTIVE_OUTLINE: Color(0.98, 0.96, 0.90, 1.0),
			ROLE_LIVE_3D_LOCKED_OUTLINE: Color(0.07, 0.07, 0.08, 1.0),
			ROLE_LIVE_3D_FACE_HIGHLIGHT: Color(1.0, 0.95, 0.82, 1.0),
			ROLE_LIVE_3D_ORIGIN_MARKER: Color(0.95, 0.78, 0.30, 1.0),
			ROLE_LIVE_BOARD_FILL: _html("16191E"),
			ROLE_LIVE_BOARD_GRID: _html("3A414A"),
			ROLE_W_SLICE_OUTLINE: Color(0.54, 0.52, 0.48, 1.0),
			ROLE_W_SLICE_LABEL: Color(0.91, 0.88, 0.80, 1.0),
			ROLE_VIEWPORT_FRAME: _html("1B1E22"),
		}
	return {
		ROLE_BACKGROUND: _html("05070A"),
		ROLE_PANEL_BACKGROUND: _html("111820"),
		ROLE_PANEL_QUIET: _html("0D141B"),
		ROLE_PANEL_ALT: _html("16212B"),
		ROLE_BORDER: _html("00E5FF"),
		ROLE_BORDER_SOFT: _html("2F6172"),
		ROLE_TEXT: _html("EAF8FF"),
		ROLE_TEXT_SECONDARY: _html("9BB7C4"),
		ROLE_TEXT_DIM: _html("85A2B0"),
		ROLE_ACCENT: _html("00E5FF"),
		ROLE_ACCENT_SOFT: _html("1B3642"),
		ROLE_SUCCESS: _html("00FFAA"),
		ROLE_WARNING: _html("FFD166"),
		ROLE_EVENT_MARKER: Color(1.0, 0.82, 0.28, 1.0),
		ROLE_ACTIVE_CELL: TRACE_COLOR_PALETTE[1],
		ROLE_LOCKED_CELL: Color(0.36, 0.39, 0.45, 1.0),
		ROLE_PROBE_BEFORE: Color(0.22, 0.94, 0.95, 1.0),
		ROLE_PROBE_AFTER: Color(0.32, 0.92, 0.65, 1.0),
		ROLE_PARTICLE: TRACE_COLOR_PALETTE[2],
		ROLE_PARTICLE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.35),
		ROLE_PARTICLE_CORE: TRACE_COLOR_PALETTE[0].lerp(Color.WHITE, 0.32),
		ROLE_PARTICLE_CORE_ESCAPED: TRACE_COLOR_PALETTE[4].lerp(Color.WHITE, 0.55),
		ROLE_BOARD_OUTLINE: Color(0.38, 0.41, 0.48, 1.0),
		ROLE_LIVE_CELL_ACTIVE_BORDER: Color(0.95, 0.98, 1.0, 1.0),
		ROLE_LIVE_CELL_LOCKED_BORDER: Color(0.04, 0.06, 0.09, 1.0),
		ROLE_LIVE_3D_ACTIVE: Color(0.0, 1.0, 1.0, 1.0),
		ROLE_LIVE_3D_LOCKED: Color(0.32, 0.36, 0.44, 1.0),
		ROLE_LIVE_3D_OUTLINE: Color(0.015, 0.02, 0.03, 1.0),
		ROLE_LIVE_3D_ACTIVE_OUTLINE: Color(0.95, 0.99, 1.0, 1.0),
		ROLE_LIVE_3D_LOCKED_OUTLINE: Color(0.025, 0.035, 0.055, 1.0),
		ROLE_LIVE_3D_FACE_HIGHLIGHT: Color(1.0, 1.0, 1.0, 1.0),
		ROLE_LIVE_3D_ORIGIN_MARKER: Color(1.0, 0.95, 0.28, 1.0),
		ROLE_LIVE_BOARD_FILL: _html("080E18"),
		ROLE_LIVE_BOARD_GRID: _html("26364F"),
		ROLE_W_SLICE_OUTLINE: Color(0.38, 0.41, 0.48, 1.0),
		ROLE_W_SLICE_LABEL: Color(0.86, 0.89, 0.94, 1.0),
		ROLE_VIEWPORT_FRAME: _html("111820"),
	}


static func _role_material(role: String, mode: String, emission_strength: float) -> StandardMaterial3D:
	return _make_material(color_for_role(role, mode), emission_strength, false)


static func _role_emission(role: String, mode: String) -> float:
	var normalized_mode := normalize_display_mode(mode)
	var tron_boost := 0.12 if normalized_mode == DISPLAY_MODE_TRON else 0.0
	match role:
		ROLE_ACTIVE_CELL:
			return 1.2 + tron_boost
		ROLE_LOCKED_CELL:
			return 0.82 + tron_boost
		ROLE_PARTICLE, ROLE_PARTICLE_ESCAPED:
			return 1.05 + tron_boost
		ROLE_PARTICLE_CORE, ROLE_PARTICLE_CORE_ESCAPED:
			return 1.3 + tron_boost
		ROLE_PROBE_BEFORE, ROLE_PROBE_AFTER:
			return 1.05 + tron_boost
		ROLE_EVENT_MARKER:
			return 1.08 + tron_boost
		ROLE_BOARD_OUTLINE, ROLE_W_SLICE_OUTLINE:
			return 0.72 + tron_boost
		ROLE_LIVE_CELL_ACTIVE_BORDER:
			return 1.0 + tron_boost
		ROLE_LIVE_CELL_LOCKED_BORDER:
			return 0.5 + tron_boost
		ROLE_LIVE_3D_ACTIVE:
			return 0.34 + tron_boost
		ROLE_LIVE_3D_LOCKED:
			return 0.04 + tron_boost
		ROLE_LIVE_3D_OUTLINE:
			return 0.18 + tron_boost
		ROLE_LIVE_3D_ACTIVE_OUTLINE:
			return 0.9 + tron_boost
		ROLE_LIVE_3D_LOCKED_OUTLINE:
			return 0.1 + tron_boost
		ROLE_LIVE_3D_FACE_HIGHLIGHT:
			return 0.2 + tron_boost
		ROLE_LIVE_3D_ORIGIN_MARKER:
			return 1.1 + tron_boost
		ROLE_LIVE_BOARD_FILL:
			return 0.2 + tron_boost
		ROLE_LIVE_BOARD_GRID:
			return 0.58 + tron_boost
		_:
			return 0.9 + tron_boost


static func _trace_color(color_id: int, escaped: bool) -> Color:
	var palette_index := int(color_id)
	if palette_index < 0 or palette_index >= TRACE_COLOR_PALETTE.size():
		palette_index = 0
	var base: Color = TRACE_COLOR_PALETTE[palette_index]
	return base.lerp(Color.WHITE, 0.35) if escaped else base


static func _make_material(color: Color, emission_strength: float, use_alpha: bool) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if use_alpha else BaseMaterial3D.TRANSPARENCY_DISABLED
	material.albedo_color = _with_alpha(color, maxf(color.a, 0.85) if use_alpha else 1.0)
	material.emission_enabled = true
	material.emission = Color(material.albedo_color.r, material.albedo_color.g, material.albedo_color.b, 1.0) * emission_strength
	material.emission_energy_multiplier = emission_strength
	return material


static func _make_lit_material(color: Color, emission_strength: float, use_alpha: bool) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA if use_alpha else BaseMaterial3D.TRANSPARENCY_DISABLED
	material.albedo_color = _with_alpha(color, maxf(color.a, 0.9) if use_alpha else 1.0)
	material.emission_enabled = true
	material.emission = Color(material.albedo_color.r, material.albedo_color.g, material.albedo_color.b, 1.0) * emission_strength
	material.emission_energy_multiplier = emission_strength
	material.roughness = 0.62
	return material


static func _live_3d_face_materials(base: Color, mode: String, active: bool, emission_override: float = -1.0) -> Dictionary:
	var emission_role := ROLE_LIVE_3D_ACTIVE if active else ROLE_LIVE_3D_LOCKED
	var emission := emission_override if emission_override >= 0.0 else _role_emission(emission_role, mode)
	var active_boost := 0.14 if emission_override >= 0.0 else 0.18
	var top_factor := 1.1 if emission_override >= 0.0 else 1.18
	var front_factor := 0.96 if emission_override >= 0.0 else 1.02
	var right_factor := 0.86 if emission_override >= 0.0 else 0.92
	var left_factor := 0.78 if emission_override >= 0.0 else 0.82
	var back_factor := 0.72 if emission_override >= 0.0 else 0.76
	var bottom_factor := 0.64 if emission_override >= 0.0 else 0.68
	var top := _shade_color(base.lerp(color_for_role(ROLE_LIVE_3D_FACE_HIGHLIGHT, mode), active_boost if active else 0.04), top_factor if active else 0.9)
	var front := _shade_color(base, front_factor if active else 0.8)
	var right := _shade_color(base, right_factor if active else 0.72)
	var left := _shade_color(base, left_factor if active else 0.66)
	var back := _shade_color(base, back_factor if active else 0.6)
	var bottom := _shade_color(base, bottom_factor if active else 0.54)
	return {
		"base": _make_lit_material(base, emission, false),
		"top": _make_lit_material(top, emission, false),
		"front": _make_lit_material(front, emission, false),
		"right": _make_lit_material(right, emission, false),
		"left": _make_lit_material(left, emission, false),
		"back": _make_lit_material(back, emission, false),
		"bottom": _make_lit_material(bottom, emission, false),
	}


static func _shade_color(color: Color, factor: float) -> Color:
	return Color(
		clampf(color.r * factor, 0.0, 1.0),
		clampf(color.g * factor, 0.0, 1.0),
		clampf(color.b * factor, 0.0, 1.0),
		color.a
	)


static func _with_alpha(color: Color, alpha: float) -> Color:
	return Color(color.r, color.g, color.b, alpha)


static func _html(value: String) -> Color:
	return Color.html(value)
