extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const ShellStyleManagerScript = preload("res://scripts/ui/style/shell_style_manager.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")


func run() -> Array:
	var failures: Array = []
	_assert_equal(
		failures,
		ReplayVisuals.default_display_mode(),
		ReplayVisuals.DISPLAY_MODE_PLAIN,
		"Instrument should be the startup display mode"
	)
	_assert_equal(
		failures,
		ReplayVisuals.display_mode_label(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC),
		"Diagnostic",
		"diagnostic display label"
	)
	_assert_equal(
		failures,
		ReplayVisuals.display_mode_label(ReplayVisuals.DISPLAY_MODE_PLAIN),
		"Instrument",
		"plain should present as Instrument"
	)
	_assert_equal(
		failures,
		ReplayVisuals.display_mode_label(ReplayVisuals.DISPLAY_MODE_TRON),
		"Vector Arcade",
		"tron should present as Vector Arcade"
	)
	_assert_theme_loads(failures, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	_assert_theme_loads(failures, ReplayVisuals.DISPLAY_MODE_TRON)
	_assert_theme_loads(failures, ReplayVisuals.DISPLAY_MODE_PLAIN)
	_assert_plain_theme_is_visible_choice(failures)
	var cyan_active := ReplayVisuals.active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 1)
	var yellow_active := ReplayVisuals.active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 2)
	var gameplay_active := ReplayVisuals.gameplay_active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_active := ReplayVisuals.live_active_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 2)
	var live_locked := ReplayVisuals.live_locked_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4)
	var ghost := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 2)
	var ghost_border := ReplayVisuals.ghost_cell_border_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_active_border := ReplayVisuals.live_active_cell_border_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_locked_border := ReplayVisuals.live_locked_cell_border_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_3d_active_faces := ReplayVisuals.live_3d_active_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 6)
	var live_3d_locked_faces := ReplayVisuals.live_3d_locked_face_materials(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4)
	var live_3d_active_border := ReplayVisuals.live_3d_active_cell_border_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_3d_locked_border := ReplayVisuals.live_3d_locked_cell_border_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_3d_origin_marker := ReplayVisuals.live_3d_origin_marker_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_board_fill := ReplayVisuals.live_board_fill_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var live_board_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	_assert_material_alpha(failures, "diagnostic active cell", cyan_active, 0.95)
	_assert_color_close(failures, "diagnostic active role hue", cyan_active.albedo_color, ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACTIVE_CELL, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC))
	_assert_color_close(failures, "diagnostic active role ignores trace color id", yellow_active.albedo_color, ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACTIVE_CELL, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC))
	_assert_color_close(failures, "gameplay active role hue", gameplay_active.albedo_color, ReplayVisuals.color_for_role(ReplayVisuals.ROLE_ACTIVE_CELL, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC))
	_assert_material_alpha(failures, "live active cell", live_active, 0.95)
	_assert_material_alpha(failures, "live locked cell", live_locked, ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY)
	_assert_material_alpha(failures, "ghost fill", ghost, 0.46)
	_assert_material_alpha(failures, "ghost outline", ghost_border, 0.88)
	_assert_material_alpha(failures, "live active border", live_active_border, 0.95)
	_assert_material_alpha(failures, "live locked border", live_locked_border, 0.95)
	_assert_material_alpha(failures, "live 3D active border", live_3d_active_border, 0.95)
	_assert_material_alpha(failures, "live 3D locked border", live_3d_locked_border, 0.95)
	_assert_material_alpha(failures, "live 3D origin marker", live_3d_origin_marker, 0.95)
	_assert_material_alpha(failures, "live board fill", live_board_fill, 0.80)
	_assert_material_alpha(failures, "live board grid", live_board_grid, ReplayVisuals.GRID_STANDARD_ALPHA)
	if live_active.albedo_color == gameplay_active.albedo_color:
		failures.append("live active cells should preserve piece color instead of using the replay role color")
	if live_active.albedo_color == Color.WHITE:
		failures.append("live active cells should not use flat white diagnostic blocks")
	if ghost.albedo_color.a >= live_active.albedo_color.a or ghost_border.emission_energy_multiplier <= ghost.emission_energy_multiplier:
		failures.append("ghost should retain a stronger outline while remaining weaker than the active piece")
	var high_contrast_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, true)
	var high_contrast_ghost := ReplayVisuals.ghost_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 2, true)
	if high_contrast_grid.albedo_color.a <= live_board_grid.albedo_color.a or high_contrast_ghost.albedo_color.a <= ghost.albedo_color.a:
		failures.append("High Contrast must strengthen grid and ghost roles")
	var normal_grid := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var normal_wireframe := ReplayVisuals.board_outline_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var normal_active_frame := ReplayVisuals.board_active_frame_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var high_contrast_grid_plain := ReplayVisuals.live_board_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN, true)
	var high_contrast_wireframe := ReplayVisuals.board_outline_material(ReplayVisuals.DISPLAY_MODE_PLAIN, true)
	var high_contrast_active_frame := ReplayVisuals.board_active_frame_material(ReplayVisuals.DISPLAY_MODE_PLAIN, true)
	var floor_fill := ReplayVisuals.live_board_floor_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var floor_lattice := ReplayVisuals.live_board_floor_grid_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	if ReplayVisuals.ROLE_BOARD_GRID == ReplayVisuals.ROLE_BOARD_WIREFRAME or ReplayVisuals.ROLE_BOARD_GRID == ReplayVisuals.ROLE_BOARD_FRAME_ACTIVE or ReplayVisuals.ROLE_BOARD_WIREFRAME == ReplayVisuals.ROLE_BOARD_FRAME_ACTIVE:
		failures.append("grid, ordinary wireframe, and active frame must remain distinct semantic roles")
	if normal_grid.albedo_color.r >= 0.72 or normal_grid.albedo_color.g >= 0.72 or normal_grid.albedo_color.b >= 0.86:
		failures.append("normal live grid must remain a dark desaturated blue, not near-white")
	if normal_wireframe.albedo_color == normal_grid.albedo_color or normal_wireframe.emission_energy_multiplier <= normal_grid.emission_energy_multiplier:
		failures.append("wireframe must remain a distinct, stronger role than the internal grid")
	if normal_active_frame.emission_energy_multiplier <= normal_wireframe.emission_energy_multiplier:
		failures.append("active frame must remain stronger than the ordinary wireframe")
	if high_contrast_wireframe.albedo_color.a <= high_contrast_grid_plain.albedo_color.a or high_contrast_wireframe.emission_energy_multiplier <= high_contrast_grid_plain.emission_energy_multiplier:
		failures.append("High Contrast wireframe must remain stronger than its grid")
	if high_contrast_active_frame.emission_energy_multiplier <= high_contrast_wireframe.emission_energy_multiplier:
		failures.append("High Contrast active frame must remain stronger than its ordinary wireframe")
	if floor_fill.albedo_color.a >= normal_grid.albedo_color.a or floor_fill.albedo_color.a >= normal_wireframe.albedo_color.a or floor_lattice.albedo_color.a <= floor_fill.albedo_color.a:
		failures.append("floor plane must remain weaker than wireframe, grid, and the separate useful floor lattice")
	if ReplayVisuals.GRID_STANDARD_ALPHA > 0.33 or ReplayVisuals.GRID_STANDARD_ALPHA < 0.29:
		failures.append("ordinary internal grid strength should be approximately 60–65 percent of the rejected calibration")
	if ReplayVisuals.axis_color("+W") != ReplayVisuals.axis_color("-W"):
		failures.append("axis sign must not change W's semantic colour")
	var live_3d_active_top := live_3d_active_faces.get("top") as StandardMaterial3D
	var live_3d_locked_top := live_3d_locked_faces.get("top") as StandardMaterial3D
	if _color_brightness(live_3d_active_top.albedo_color) <= _color_brightness(live_3d_locked_top.albedo_color) + 0.18:
		failures.append("live 3D active faces should be materially brighter than locked faces")
	if live_3d_active_border.albedo_color == live_3d_locked_border.albedo_color:
		failures.append("live 3D active and locked outlines should use distinct roles")
	if live_3d_active_border.emission_energy_multiplier <= live_3d_locked_border.emission_energy_multiplier:
		failures.append("live 3D active outline should have stronger emphasis than locked outline")
	if ReplayVisuals.slice_outline_thickness(ReplayVisuals.DISPLAY_MODE_TRON) <= ReplayVisuals.GRID_LINE_THICKNESS:
		failures.append("W-slice card outline should be stronger than internal grid thickness")
	if ReplayVisuals.grid_internal_thickness(true) <= ReplayVisuals.grid_internal_thickness(false):
		failures.append("High Contrast grid lines should be thicker than the standard grid")
	if ReplayVisuals.grid_internal_thickness(false) >= ReplayVisuals.slice_outline_thickness(ReplayVisuals.DISPLAY_MODE_PLAIN):
		failures.append("ordinary board wireframes should be thicker than internal grids")
	var wireframe_grid_width_ratio := ReplayVisuals.slice_outline_thickness(ReplayVisuals.DISPLAY_MODE_PLAIN) / ReplayVisuals.grid_internal_thickness(false)
	if wireframe_grid_width_ratio < 1.5 or wireframe_grid_width_ratio > 2.0:
		failures.append("ordinary wireframe/grid width ratio should remain in the calibrated 1.5–2.0 range")
	if ReplayVisuals.ACTIVE_SLICE_FRAME_HIGH_CONTRAST_MULTIPLIER <= 1.20:
		failures.append("High Contrast active frame should remain thicker than its ordinary wireframe")
	if ReplayVisuals.W_SLICE_LABEL_FONT_SIZE < 44 or ReplayVisuals.W_SLICE_LABEL_FONT_SIZE >= 60:
		failures.append("W-slice labels should remain readable without becoming scene headers")
	if ReplayVisuals.W_SLICE_LABEL_CHIP_WIDTH != 0.0 or ReplayVisuals.W_SLICE_LABEL_CHIP_HEIGHT != 0.0:
		failures.append("W-slice labels should not use large backing chips by default")
	if ReplayVisuals.slice_label_color("tron").a < 0.85:
		failures.append("W-slice labels should retain readable opacity at fitted overview scale")
	var axis_manager = ShellStyleManagerScript.new()
	axis_manager.set_theme(ReplayVisuals.DISPLAY_MODE_PLAIN)
	if ReplayVisuals.axis_color("+W") != axis_manager.get_color(ShellStyleRolesScript.AXIS_W):
		failures.append("W axis should use the dedicated semantic axis.w style role")
	var instrument_outline := ReplayVisuals.live_3d_active_cell_border_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var instrument_locked_outline := ReplayVisuals.live_3d_locked_cell_border_material(ReplayVisuals.DISPLAY_MODE_PLAIN)
	var instrument_active_faces := ReplayVisuals.live_3d_active_face_materials(ReplayVisuals.DISPLAY_MODE_PLAIN, 5)
	var instrument_active_front := instrument_active_faces.get("front") as StandardMaterial3D
	var arcade_outline := ReplayVisuals.live_3d_active_cell_border_material(ReplayVisuals.DISPLAY_MODE_TRON)
	if instrument_outline.emission_energy_multiplier >= arcade_outline.emission_energy_multiplier:
		failures.append("Instrument should remain calmer than Vector Arcade emission")
	if _color_brightness(instrument_outline.albedo_color) <= _color_brightness(instrument_active_front.albedo_color) + 0.20:
		failures.append("Instrument active boxes should use a crisp high-contrast edge")
	if _color_brightness(instrument_locked_outline.albedo_color) >= _color_brightness(instrument_outline.albedo_color):
		failures.append("Instrument locked boxes should remain quieter than active boxes")
	if ReplayVisuals.LIVE_CELL_BORDER_DELTA < 0.07 or ReplayVisuals.LIVE_3D_ACTIVE_CELL_BORDER_DELTA < 0.05:
		failures.append("live box edges should remain legible at overview scale")
	if ReplayVisuals.LIVE_3D_ACTIVE_CELL_SCALE != ReplayVisuals.LIVE_3D_LOCKED_CELL_SCALE:
		failures.append("locking should preserve the live exterior cell body scale")
	if ReplayVisuals.LIVE_3D_ACTIVE_CELL_BORDER_DELTA != ReplayVisuals.LIVE_3D_LOCKED_CELL_BORDER_DELTA:
		failures.append("locking should preserve the live exterior wireframe envelope")
	_assert_material_alpha(failures, "diagnostic locked cell", ReplayVisuals.locked_cell_material(), ReplayVisuals.DEFAULT_LOCKED_CELL_OPACITY)
	var low_opacity_locked := ReplayVisuals.live_locked_cell_material(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC, 4, 0.60)
	_assert_material_alpha(failures, "configured locked cell opacity", low_opacity_locked, 0.60)
	if ReplayVisuals.normalize_locked_cell_opacity(0.0) != ReplayVisuals.MIN_LOCKED_CELL_OPACITY or ReplayVisuals.normalize_locked_cell_opacity(2.0) != ReplayVisuals.MAX_LOCKED_CELL_OPACITY:
		failures.append("locked-cell opacity should remain bounded by its presentation preference range")
	_assert_material_alpha(failures, "diagnostic particle", ReplayVisuals.particle_material(), 0.95)
	_assert_material_alpha(failures, "diagnostic board outline", ReplayVisuals.board_outline_material(), 0.90)
	_assert_material_alpha(
		failures,
		"diagnostic W-slice outline",
		ReplayVisuals.slice_outline_material(),
		0.90
	)
	_assert_material_alpha(
		failures,
		"tron active cell",
		ReplayVisuals.active_cell_material(ReplayVisuals.DISPLAY_MODE_TRON),
		0.95
	)
	_assert_material_alpha(
		failures,
		"tron particle",
		ReplayVisuals.particle_material(ReplayVisuals.DISPLAY_MODE_TRON),
		0.95
	)
	return failures


func _assert_theme_loads(failures: Array, display_mode: String) -> void:
	var theme := ReplayVisuals.build_theme(display_mode)
	if theme == null:
		failures.append("%s theme did not load" % display_mode)


func _assert_plain_theme_is_visible_choice(failures: Array) -> void:
	var diagnostic_theme := ReplayVisuals.build_theme(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var plain_theme := ReplayVisuals.build_theme(ReplayVisuals.DISPLAY_MODE_PLAIN)
	if diagnostic_theme == null or plain_theme == null:
		return
	var diagnostic_accent := diagnostic_theme.get_color("font_color", "AccentLabel")
	var plain_accent := plain_theme.get_color("font_color", "AccentLabel")
	if diagnostic_accent == plain_accent:
		failures.append("plain theme should use a visibly distinct accent color")
	var diagnostic_background := ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC)
	var plain_background := ReplayVisuals.color_for_role(ReplayVisuals.ROLE_BACKGROUND, ReplayVisuals.DISPLAY_MODE_PLAIN)
	if diagnostic_background == plain_background:
		failures.append("plain display palette should be distinct from diagnostic")


func _assert_material_alpha(
	failures: Array,
	label: String,
	material: StandardMaterial3D,
	minimum_alpha: float
) -> void:
	if material == null:
		failures.append("%s material missing" % label)
		return
	var alpha := material.albedo_color.a
	if alpha + 0.001 < minimum_alpha:
		failures.append("%s alpha %.2f is below %.2f" % [label, alpha, minimum_alpha])


func _assert_color_close(failures: Array, label: String, actual: Color, expected: Color) -> void:
	var tolerance := 0.01
	if (
		absf(actual.r - expected.r) > tolerance
		or absf(actual.g - expected.g) > tolerance
		or absf(actual.b - expected.b) > tolerance
		or absf(actual.a - expected.a) > tolerance
	):
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _color_brightness(color: Color) -> float:
	return (color.r + color.g + color.b) / 3.0
