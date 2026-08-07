extends Control

class_name PieceThumbnail

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")

const LABEL_HEIGHT := 18.0
const GROUP_GAP := 8.0
const OUTER_PAD := 6.0

var _model
var _style_manager
var _geometry_revision := 0
var _style_revision := 0


func _init() -> void:
	name = "PieceThumbnail"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(0, 104)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL


func set_model(model) -> void:
	_model = model
	_geometry_revision += 1
	custom_minimum_size.y = 132.0 if _model != null and int(_model.dimension) == 4 else 104.0
	queue_redraw()


func clear() -> void:
	if _model != null:
		_geometry_revision += 1
	_model = null
	custom_minimum_size.y = 104.0
	queue_redraw()


func set_style_manager(style_manager) -> void:
	_style_manager = style_manager
	_style_revision += 1
	queue_redraw()


func deterministic_snapshot() -> Dictionary:
	return {
		"available": _model != null and _model.is_available(),
		"minimum_height": custom_minimum_size.y,
		"group_count": _model.drawing_groups().size() if _model != null else 0,
		"geometry_revision": _geometry_revision,
		"style_revision": _style_revision,
		"render_mode": _render_mode(),
	}


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED or what == NOTIFICATION_THEME_CHANGED:
		queue_redraw()


func _draw() -> void:
	if _model == null or not _model.is_available():
		return
	var groups: Array = _model.drawing_groups()
	var content := Rect2(
		Vector2(OUTER_PAD, OUTER_PAD),
		Vector2(max(size.x - OUTER_PAD * 2.0, 1.0), max(size.y - OUTER_PAD * 2.0, 1.0))
	)
	var width := (content.size.x - GROUP_GAP * float(max(groups.size() - 1, 0))) / float(max(groups.size(), 1))
	for index in range(groups.size()):
		var group: Dictionary = groups[index]
		var group_rect := Rect2(
			Vector2(content.position.x + float(index) * (width + GROUP_GAP), content.position.y),
			Vector2(width, content.size.y)
		)
		_draw_group(group, group_rect, int(_model.dimension))


func _draw_group(group: Dictionary, rect: Rect2, dimension_value: int) -> void:
	var border := _role_color(ShellStyleRolesScript.GRID_MINOR, Color(0.35, 0.4, 0.48, 1.0))
	var background := _role_color(ShellStyleRolesScript.BACKGROUND_BOARD, Color(0.04, 0.05, 0.07, 1.0))
	draw_rect(rect, background, true)
	draw_rect(rect, border, false, 1.0)
	var label := str(group.get("label", ""))
	var draw_rect_value := rect.grow(-5.0)
	if not label.is_empty():
		draw_string(_font(), draw_rect_value.position + Vector2(0.0, 13.0), label, HORIZONTAL_ALIGNMENT_LEFT, draw_rect_value.size.x, 12, _role_color(ShellStyleRolesScript.LABEL_W_LAYER, Color.WHITE))
		draw_rect_value.position.y += LABEL_HEIGHT
		draw_rect_value.size.y -= LABEL_HEIGHT
	var cells: Array = group.get("cells", [])
	if dimension_value == 2:
		_draw_2d_cells(cells, draw_rect_value)
	else:
		_draw_isometric_cells(cells, draw_rect_value)


func _draw_2d_cells(cells: Array, rect: Rect2) -> void:
	if cells.is_empty():
		return
	var bounds: Array = _coordinate_bounds(cells, 2)
	var span_x: int = int(bounds[1]) - int(bounds[0]) + 1
	var span_y: int = int(bounds[3]) - int(bounds[2]) + 1
	var cell_size: float = minf(rect.size.x / float(maxi(span_x, 1)), rect.size.y / float(maxi(span_y, 1))) * 0.82
	cell_size = clamp(cell_size, 8.0, 28.0)
	var used := Vector2(float(span_x) * cell_size, float(span_y) * cell_size)
	var origin: Vector2 = rect.position + (rect.size - used) * 0.5
	var fill: Color = ReplayVisuals.preview_piece_color(int(_model.color_id))
	var outline: Color = _outline_color()
	for cell in cells:
		var position: Vector2 = origin + Vector2(float(int(cell[0]) - int(bounds[0])), float(int(cell[1]) - int(bounds[2]))) * cell_size
		var cell_rect := Rect2(position + Vector2.ONE, Vector2.ONE * maxf(cell_size - 2.0, 1.0))
		draw_rect(cell_rect, fill, true)
		draw_rect(cell_rect, outline, false, _outline_width())


func _draw_isometric_cells(cells: Array, rect: Rect2) -> void:
	if cells.is_empty():
		return
	var projected: Array = []
	for cell in cells:
		var x := float(int(cell[0]))
		var y := float(int(cell[1]))
		var z := float(int(cell[2])) if cell.size() > 2 else 0.0
		projected.append(Vector2((x - z) * 0.86, y * 0.92 + (x + z) * 0.42))
	var min_point: Vector2 = projected[0]
	var max_point: Vector2 = projected[0]
	for point: Vector2 in projected:
		min_point.x = min(min_point.x, point.x)
		min_point.y = min(min_point.y, point.y)
		max_point.x = max(max_point.x, point.x)
		max_point.y = max(max_point.y, point.y)
	var span: float = maxf(maxf(max_point.x - min_point.x, max_point.y - min_point.y), 1.0)
	var unit: float = clampf(minf(rect.size.x, rect.size.y) / (span + 1.8), 9.0, 25.0)
	var projected_size: Vector2 = (max_point - min_point) * unit
	var origin: Vector2 = rect.position + (rect.size - projected_size) * 0.5 - min_point * unit + Vector2(0.0, unit * 0.12)
	var order: Array = range(cells.size())
	order.sort_custom(func(left: int, right: int) -> bool:
		var a: Array = cells[left]
		var b: Array = cells[right]
		return int(a[0]) + int(a[1]) + int(a[2]) < int(b[0]) + int(b[1]) + int(b[2])
	)
	for index in order:
		_draw_cube(origin + projected[index] * unit, unit, ReplayVisuals.preview_piece_color(int(_model.color_id)))


func _draw_cube(center: Vector2, unit: float, base: Color) -> void:
	var half_w := unit * 0.46
	var half_h := unit * 0.25
	var depth := unit * 0.48
	var top := PackedVector2Array([
		center + Vector2(0.0, -depth),
		center + Vector2(half_w, -depth + half_h),
		center + Vector2(0.0, -depth + half_h * 2.0),
		center + Vector2(-half_w, -depth + half_h),
	])
	var left := PackedVector2Array([
		top[3], top[2], top[2] + Vector2(0.0, depth), top[3] + Vector2(0.0, depth),
	])
	var right := PackedVector2Array([
		top[2], top[1], top[1] + Vector2(0.0, depth), top[2] + Vector2(0.0, depth),
	])
	draw_colored_polygon(left, base.darkened(0.30))
	draw_colored_polygon(right, base.darkened(0.15))
	draw_colored_polygon(top, base.lightened(0.10))
	var outline := _outline_color()
	for polygon in [top, left, right]:
		var closed := PackedVector2Array(polygon)
		closed.append(polygon[0])
		draw_polyline(closed, outline, _outline_width(), true)


func _coordinate_bounds(cells: Array, count: int) -> Array:
	var result: Array = []
	for axis in range(count):
		var minimum := int(cells[0][axis])
		var maximum := minimum
		for cell in cells:
			minimum = min(minimum, int(cell[axis]))
			maximum = max(maximum, int(cell[axis]))
		result.append(minimum)
		result.append(maximum)
	return result


func _render_mode() -> String:
	if _model == null:
		return "unavailable"
	return "xy" if int(_model.dimension) == 2 else ("xyz_isometric" if int(_model.dimension) == 3 else "w_sliced_xyz_isometric")


func _font() -> Font:
	return get_theme_default_font()


func _role_color(role: String, fallback: Color) -> Color:
	return _style_manager.get_color(role) if _style_manager != null else fallback


func _outline_color() -> Color:
	return _role_color(ShellStyleRolesScript.TEXT_PRIMARY, Color.WHITE)


func _outline_width() -> float:
	return 2.0 if _style_manager != null and _style_manager.is_high_contrast_enabled() else 1.0
