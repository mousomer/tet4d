extends RefCounted

class_name ReplayVisuals

const DIAGNOSTIC_THEME_PATH := "res://themes/replay_diagnostic_theme.tres"
const TRON_THEME_PATH := "res://themes/replay_tron_theme.tres"
const PLAIN_THEME_PATH := "res://themes/replay_theme.tres"
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")

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
const TOP_BAR_HEIGHT := 132
const TIMELINE_HEIGHT := 104
const LEFT_PANEL_WIDTH := 210
const RIGHT_INSPECTOR_WIDTH := 260
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
const GRID_LINE_THICKNESS := 0.058
const W_SLICE_LABEL_FONT_SIZE := 34
const W_SLICE_LABEL_OUTLINE_SIZE := 7
const W_SLICE_LABEL_CHIP_WIDTH := 0.0
const W_SLICE_LABEL_CHIP_HEIGHT := 0.0
const W_SLICE_LABEL_CHIP_DEPTH := 0.0
const W_SLICE_LABEL_VERTICAL_OFFSET := 0.42
const W_SLICE_LABEL_EDGE_OFFSET := 0.34
const W_SLICE_LABEL_BOUNDS_PAD := 0.68
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

static var _palette_cache := {}


static func default_display_mode() -> String:
	return DISPLAY_MODE_TRON


static func supported_shell_minimum_size() -> Vector2:
	return Vector2(SHELL_MIN_WIDTH, SHELL_MIN_HEIGHT)


static func normalize_display_mode(mode: String) -> String:
	return mode if DISPLAY_MODES.has(mode) else DISPLAY_MODE_TRON


static func display_mode_label(mode: String) -> String:
	match normalize_display_mode(mode):
		DISPLAY_MODE_DIAGNOSTIC:
			return "Diagnostic"
		DISPLAY_MODE_TRON:
			return "Vector Arcade"
		DISPLAY_MODE_PLAIN:
			return "Plain"
		_:
			return DISPLAY_MODE_DIAGNOSTIC.capitalize()


static func authority_label(mode: String) -> String:
	return "REPLAY · PYTHON ORACLE · %s DISPLAY" % display_mode_label(mode).to_upper()


static func color_for_role(role: String, mode: String = DISPLAY_MODE_TRON) -> Color:
	var palette := _palette(normalize_display_mode(mode))
	return palette.get(role, palette.get(ROLE_TEXT, Color.WHITE))


static func build_theme(mode: String = DISPLAY_MODE_TRON) -> Theme:
	var display_mode := normalize_display_mode(mode)
	var theme_path := DIAGNOSTIC_THEME_PATH
	match display_mode:
		DISPLAY_MODE_TRON:
			theme_path = TRON_THEME_PATH
		DISPLAY_MODE_PLAIN:
			theme_path = PLAIN_THEME_PATH
	return load(theme_path).duplicate() as Theme


static func active_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	return _role_material(ROLE_ACTIVE_CELL, mode, _role_emission(ROLE_ACTIVE_CELL, mode))


static func gameplay_active_cell_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_ACTIVE_CELL, mode, _role_emission(ROLE_ACTIVE_CELL, mode))


static func live_active_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.08)
	return _make_material(base, _role_emission(ROLE_ACTIVE_CELL, mode) + 0.1, false)


static func live_3d_active_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.14)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_ACTIVE, mode), false)


static func live_4d_active_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.12).lerp(Color.WHITE, 0.06)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_ACTIVE, mode) * 0.72, false)


static func live_3d_active_face_materials(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).lerp(Color.WHITE, 0.13)
	return _live_3d_face_materials(base, mode, true)


static func live_4d_active_face_materials(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).darkened(0.12).lerp(Color.WHITE, 0.06)
	return _live_3d_face_materials(base, mode, true, _role_emission(ROLE_LIVE_3D_ACTIVE, mode) * 0.72)


static func locked_cell_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LOCKED_CELL, mode, _role_emission(ROLE_LOCKED_CELL, mode))


static func live_locked_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.22).lerp(color_for_role(ROLE_LOCKED_CELL, mode), 0.18)
	return _make_material(base, _role_emission(ROLE_LOCKED_CELL, mode), false)


static func live_3d_locked_cell_material(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> StandardMaterial3D:
	var base := _trace_color(color_id, false).darkened(0.42).lerp(color_for_role(ROLE_LIVE_3D_LOCKED, mode), 0.28)
	return _make_lit_material(base, _role_emission(ROLE_LIVE_3D_LOCKED, mode), false)


static func live_3d_locked_face_materials(mode: String = DISPLAY_MODE_TRON, color_id: int = 1) -> Dictionary:
	var base := _trace_color(color_id, false).darkened(0.42).lerp(color_for_role(ROLE_LIVE_3D_LOCKED, mode), 0.28)
	return _live_3d_face_materials(base, mode, false)


static func live_active_cell_border_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_CELL_ACTIVE_BORDER, mode, _role_emission(ROLE_LIVE_CELL_ACTIVE_BORDER, mode))


static func live_locked_cell_border_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_CELL_LOCKED_BORDER, mode, _role_emission(ROLE_LIVE_CELL_LOCKED_BORDER, mode))


static func live_3d_active_cell_border_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_ACTIVE_OUTLINE, mode, _role_emission(ROLE_LIVE_3D_ACTIVE_OUTLINE, mode))


static func live_3d_locked_cell_border_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_LOCKED_OUTLINE, mode, _role_emission(ROLE_LIVE_3D_LOCKED_OUTLINE, mode))


static func live_3d_origin_marker_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_LIVE_3D_ORIGIN_MARKER, mode, _role_emission(ROLE_LIVE_3D_ORIGIN_MARKER, mode))


static func live_board_fill_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	var material := _role_material(ROLE_LIVE_BOARD_FILL, mode, _role_emission(ROLE_LIVE_BOARD_FILL, mode))
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(material.albedo_color, 0.80)
	return material


static func live_board_grid_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	var material := _role_material(ROLE_LIVE_BOARD_GRID, mode, _role_emission(ROLE_LIVE_BOARD_GRID, mode))
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(material.albedo_color.darkened(0.18), 0.64)
	return material


static func probe_before_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_PROBE_BEFORE, mode, _role_emission(ROLE_PROBE_BEFORE, mode))


static func probe_after_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_PROBE_AFTER, mode, _role_emission(ROLE_PROBE_AFTER, mode))


static func particle_material(
	mode: String = DISPLAY_MODE_TRON,
	escaped: bool = false,
	color_id: int = 0
) -> StandardMaterial3D:
	return _make_material(
		color_for_role(ROLE_PARTICLE_ESCAPED if escaped else ROLE_PARTICLE, mode),
		_role_emission(ROLE_PARTICLE_ESCAPED if escaped else ROLE_PARTICLE, mode),
		false
	)


static func particle_core_material(
	mode: String = DISPLAY_MODE_TRON,
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
	mode: String = DISPLAY_MODE_TRON,
	escaped: bool = false,
	color_id: int = 0
) -> StandardMaterial3D:
	var color := color_for_role(ROLE_PARTICLE_ESCAPED if escaped else ROLE_PARTICLE, mode).darkened(0.25)
	var material := _make_material(color, 0.75, false)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(color, 0.72)
	return material


static func board_outline_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_BOARD_OUTLINE, mode, _role_emission(ROLE_BOARD_OUTLINE, mode))


static func slice_outline_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_W_SLICE_OUTLINE, mode, _role_emission(ROLE_W_SLICE_OUTLINE, mode))


static func event_marker_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	return _role_material(ROLE_EVENT_MARKER, mode, _role_emission(ROLE_EVENT_MARKER, mode))


static func slice_label_color(mode: String = DISPLAY_MODE_TRON) -> Color:
	return color_for_role(ROLE_W_SLICE_LABEL, mode)


static func slice_label_chip_material(mode: String = DISPLAY_MODE_TRON) -> StandardMaterial3D:
	var material := _role_material(ROLE_PANEL_ALT, mode, 0.28)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = _with_alpha(color_for_role(ROLE_PANEL_ALT, mode), 0.96)
	return material


static func slice_outline_thickness(mode: String = DISPLAY_MODE_TRON) -> float:
	return GRID_LINE_THICKNESS * 1.45


static func _palette(mode: String) -> Dictionary:
	var normalized_mode := normalize_display_mode(mode)
	if _palette_cache.has(normalized_mode):
		return _palette_cache.get(normalized_mode)
	var manager = ShellStyleManagerScript.new()
	manager.set_theme(normalized_mode)
	var palette := {
		ROLE_BACKGROUND: manager.get_color(ShellStyleRolesScript.BACKGROUND_PRIMARY),
		ROLE_PANEL_BACKGROUND: manager.get_color(ShellStyleRolesScript.BACKGROUND_PANEL),
		ROLE_PANEL_QUIET: manager.get_color(ShellStyleRolesScript.BACKGROUND_PANEL),
		ROLE_PANEL_ALT: manager.get_color(ShellStyleRolesScript.BACKGROUND_ELEVATED),
		ROLE_BORDER: manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY),
		ROLE_BORDER_SOFT: manager.get_color(ShellStyleRolesScript.GRID_MINOR),
		ROLE_TEXT: manager.get_color(ShellStyleRolesScript.TEXT_PRIMARY),
		ROLE_TEXT_SECONDARY: manager.get_color(ShellStyleRolesScript.TEXT_SECONDARY),
		ROLE_TEXT_DIM: manager.get_color(ShellStyleRolesScript.TEXT_MUTED),
		ROLE_ACCENT: manager.get_color(ShellStyleRolesScript.ACCENT_PRIMARY),
		ROLE_ACCENT_SOFT: manager.get_color(ShellStyleRolesScript.ACCENT_SOFT),
		ROLE_SUCCESS: manager.get_color(ShellStyleRolesScript.STATE_SUCCESS),
		ROLE_WARNING: manager.get_color(ShellStyleRolesScript.STATE_WARNING),
		ROLE_EVENT_MARKER: manager.get_color(ShellStyleRolesScript.DIAGNOSTIC_BOUNDS),
		ROLE_ACTIVE_CELL: manager.get_color(ShellStyleRolesScript.CELL_ACTIVE),
		ROLE_LOCKED_CELL: manager.get_color(ShellStyleRolesScript.CELL_LOCKED),
		ROLE_PROBE_BEFORE: manager.get_color(ShellStyleRolesScript.TRACE_PAST),
		ROLE_PROBE_AFTER: manager.get_color(ShellStyleRolesScript.TRACE_CURRENT),
		ROLE_PARTICLE: manager.get_color(ShellStyleRolesScript.TRACE_CURRENT),
		ROLE_PARTICLE_ESCAPED: manager.get_color(ShellStyleRolesScript.STATE_SUCCESS),
		ROLE_PARTICLE_CORE: manager.get_color(ShellStyleRolesScript.CELL_PREVIEW),
		ROLE_PARTICLE_CORE_ESCAPED: manager.get_color(ShellStyleRolesScript.STATE_SUCCESS),
		ROLE_BOARD_OUTLINE: manager.get_color(ShellStyleRolesScript.GRID_MAJOR),
		ROLE_LIVE_CELL_ACTIVE_BORDER: manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS),
		ROLE_LIVE_CELL_LOCKED_BORDER: manager.get_color(ShellStyleRolesScript.GRID_MINOR),
		ROLE_LIVE_3D_ACTIVE: manager.get_color(ShellStyleRolesScript.CELL_ACTIVE),
		ROLE_LIVE_3D_LOCKED: manager.get_color(ShellStyleRolesScript.CELL_LOCKED),
		ROLE_LIVE_3D_OUTLINE: manager.get_color(ShellStyleRolesScript.GRID_MINOR),
		ROLE_LIVE_3D_ACTIVE_OUTLINE: manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS),
		ROLE_LIVE_3D_LOCKED_OUTLINE: manager.get_color(ShellStyleRolesScript.GRID_MINOR),
		ROLE_LIVE_3D_FACE_HIGHLIGHT: manager.get_color(ShellStyleRolesScript.ACCENT_FOCUS),
		ROLE_LIVE_3D_ORIGIN_MARKER: manager.get_color(ShellStyleRolesScript.GRID_AXIS),
		ROLE_LIVE_BOARD_FILL: manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD),
		ROLE_LIVE_BOARD_GRID: manager.get_color(ShellStyleRolesScript.GRID_MINOR),
		ROLE_W_SLICE_OUTLINE: manager.get_color(ShellStyleRolesScript.GRID_MAJOR),
		ROLE_W_SLICE_LABEL: manager.get_color(ShellStyleRolesScript.LABEL_W_LAYER),
		ROLE_VIEWPORT_FRAME: manager.get_color(ShellStyleRolesScript.BACKGROUND_BOARD),
	}
	_palette_cache[normalized_mode] = palette
	return palette


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
			return 0.74 + tron_boost
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
