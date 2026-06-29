extends RefCounted

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")


func run() -> Array:
	var failures: Array = []
	_assert_equal(
		failures,
		ReplayVisuals.default_display_mode(),
		ReplayVisuals.DISPLAY_MODE_TRON,
		"tron should be the startup display mode"
	)
	_assert_equal(
		failures,
		ReplayVisuals.display_mode_label(ReplayVisuals.DISPLAY_MODE_DIAGNOSTIC),
		"Diagnostic",
		"diagnostic display label"
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
	_assert_material_alpha(failures, "live locked cell", live_locked, 0.95)
	_assert_material_alpha(failures, "live active border", live_active_border, 0.95)
	_assert_material_alpha(failures, "live locked border", live_locked_border, 0.95)
	_assert_material_alpha(failures, "live 3D active border", live_3d_active_border, 0.95)
	_assert_material_alpha(failures, "live 3D locked border", live_3d_locked_border, 0.95)
	_assert_material_alpha(failures, "live 3D origin marker", live_3d_origin_marker, 0.95)
	_assert_material_alpha(failures, "live board fill", live_board_fill, 0.80)
	_assert_material_alpha(failures, "live board grid", live_board_grid, 0.60)
	if live_active.albedo_color == gameplay_active.albedo_color:
		failures.append("live active cells should preserve piece color instead of using the replay role color")
	if live_active.albedo_color == Color.WHITE:
		failures.append("live active cells should not use flat white diagnostic blocks")
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
	if ReplayVisuals.W_SLICE_LABEL_FONT_SIZE < 100:
		failures.append("W-slice headers should use large readable slice-card labels")
	_assert_material_alpha(failures, "diagnostic locked cell", ReplayVisuals.locked_cell_material(), 0.90)
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
	if alpha < minimum_alpha:
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
