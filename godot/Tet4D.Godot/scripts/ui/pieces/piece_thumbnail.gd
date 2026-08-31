extends Control

class_name PieceThumbnail

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const ShellStyleRolesScript = preload("res://scripts/ui/style/shell_style_roles.gd")

const LABEL_HEIGHT := 18.0
const GROUP_GAP := 8.0
const OUTER_PAD := 6.0
const ISOMETRIC_HALF_WIDTH := 0.46
const ISOMETRIC_HALF_HEIGHT := 0.25
const ISOMETRIC_DEPTH := 0.48
const STANDARD_MIN_HEIGHT := 104.0
const STANDARD_4D_MIN_HEIGHT := 132.0
const COMPACT_MIN_HEIGHT := 72.0
const COMPACT_4D_MIN_HEIGHT := 88.0

var _model
var _style_manager
var _geometry_revision := 0
var _style_revision := 0
var _compact_cockpit := false


func _init() -> void:
	name = "PieceThumbnail"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(0, STANDARD_MIN_HEIGHT)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL


func set_model(model) -> void:
	_model = model
	_geometry_revision += 1
	_apply_minimum_height()
	queue_redraw()


func clear() -> void:
	if _model != null:
		_geometry_revision += 1
	_model = null
	_apply_minimum_height()
	queue_redraw()


func set_compact_cockpit(enabled: bool) -> void:
	_compact_cockpit = enabled
	_apply_minimum_height()
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
		"compact_cockpit": _compact_cockpit,
	}


func _apply_minimum_height() -> void:
	var four_d := _model != null and int(_model.dimension) == 4
	if _compact_cockpit:
		custom_minimum_size.y = COMPACT_4D_MIN_HEIGHT if four_d else COMPACT_MIN_HEIGHT
	else:
		custom_minimum_size.y = STANDARD_4D_MIN_HEIGHT if four_d else STANDARD_MIN_HEIGHT


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED or what == NOTIFICATION_THEME_CHANGED:
		queue_redraw()


func _draw() -> void:
	if _model == null or not _model.is_available():
		return
	var plan: Dictionary = renderer_plan(size)
	for group_plan in plan.get("groups", []):
		_draw_group_plan(group_plan, int(plan.get("dimension", 0)))


func renderer_plan(target_size: Vector2) -> Dictionary:
	if _model == null or not _model.is_available():
		return {"available": false, "dimension": 0, "groups": []}
	var groups: Array = _model.drawing_groups()
	var content := Rect2(
		Vector2(OUTER_PAD, OUTER_PAD),
		Vector2(max(target_size.x - OUTER_PAD * 2.0, 1.0), max(target_size.y - OUTER_PAD * 2.0, 1.0))
	)
	var width := (content.size.x - GROUP_GAP * float(max(groups.size() - 1, 0))) / float(max(groups.size(), 1))
	var group_plans: Array = []
	for index in range(groups.size()):
		var group: Dictionary = groups[index]
		var group_rect := Rect2(
			Vector2(content.position.x + float(index) * (width + GROUP_GAP), content.position.y),
			Vector2(width, content.size.y)
		)
		var drawing_rect := group_rect.grow(-5.0)
		if not str(group.get("label", "")).is_empty():
			drawing_rect.position.y += LABEL_HEIGHT
			drawing_rect.size.y -= LABEL_HEIGHT
		group_plans.append({
			"slice_coordinate": int(group.get("slice_coordinate", 0)),
			"label": str(group.get("label", "")),
			"cells": group.get("cells", []).duplicate(true),
			"rect": group_rect,
			"drawing_rect": drawing_rect,
			"rendered_cells": [],
		})
	var projection_frame: Dictionary = {}
	if int(_model.dimension) == 2:
		_plan_2d_cells(group_plans[0])
	else:
		projection_frame = _shared_isometric_frame(group_plans)
		for group_plan in group_plans:
			_plan_isometric_cells(group_plan, projection_frame)
	return {
		"available": true,
		"dimension": int(_model.dimension),
		"projection_frame": projection_frame,
		"groups": group_plans,
	}


func _draw_group_plan(group: Dictionary, dimension_value: int) -> void:
	var rect: Rect2 = group.get("rect", Rect2())
	var border := _role_color(ShellStyleRolesScript.GRID_MINOR, Color(0.35, 0.4, 0.48, 1.0))
	var background := _role_color(ShellStyleRolesScript.BACKGROUND_BOARD, Color(0.04, 0.05, 0.07, 1.0))
	draw_rect(rect, background, true)
	draw_rect(rect, border, false, 1.0)
	var label := str(group.get("label", ""))
	if not label.is_empty():
		var label_rect := rect.grow(-5.0)
		draw_string(_font(), label_rect.position + Vector2(0.0, 13.0), label, HORIZONTAL_ALIGNMENT_LEFT, label_rect.size.x, 12, _role_color(ShellStyleRolesScript.LABEL_W_LAYER, Color.WHITE))
	var rendered_cells: Array = group.get("rendered_cells", [])
	if dimension_value == 2:
		var fill: Color = ReplayVisuals.preview_piece_color(int(_model.color_id))
		var outline: Color = _outline_color()
		for rendered_cell in rendered_cells:
			var cell_rect: Rect2 = rendered_cell.get("rect", Rect2())
			draw_rect(cell_rect, fill, true)
			draw_rect(cell_rect, outline, false, _outline_width())
	else:
		for rendered_cell in rendered_cells:
			_draw_cube(
				rendered_cell.get("center", Vector2.ZERO),
				float(rendered_cell.get("unit", 0.0)),
				ReplayVisuals.preview_piece_color(int(_model.color_id))
			)


func _plan_2d_cells(group_plan: Dictionary) -> void:
	var cells: Array = group_plan.get("cells", [])
	if cells.is_empty():
		return
	var rect: Rect2 = group_plan.get("drawing_rect", Rect2())
	var bounds: Array = _coordinate_bounds(cells, 2)
	var span_x: int = int(bounds[1]) - int(bounds[0]) + 1
	var span_y: int = int(bounds[3]) - int(bounds[2]) + 1
	var cell_size: float = minf(rect.size.x / float(maxi(span_x, 1)), rect.size.y / float(maxi(span_y, 1))) * 0.82
	cell_size = clamp(cell_size, 8.0, 28.0)
	var used := Vector2(float(span_x) * cell_size, float(span_y) * cell_size)
	var origin: Vector2 = rect.position + (rect.size - used) * 0.5
	var rendered_cells: Array = []
	for cell in cells:
		var position: Vector2 = origin + Vector2(float(int(cell[0]) - int(bounds[0])), float(int(cell[1]) - int(bounds[2]))) * cell_size
		rendered_cells.append({
			"coordinate": cell.duplicate(),
			"rect": Rect2(position + Vector2.ONE, Vector2.ONE * maxf(cell_size - 2.0, 1.0)),
		})
	group_plan["rendered_cells"] = rendered_cells


func _shared_isometric_frame(group_plans: Array) -> Dictionary:
	var projected: Array = []
	var available_size := Vector2(INF, INF)
	for group_plan in group_plans:
		var drawing_rect: Rect2 = group_plan.get("drawing_rect", Rect2())
		available_size.x = minf(available_size.x, drawing_rect.size.x)
		available_size.y = minf(available_size.y, drawing_rect.size.y)
		for cell in group_plan.get("cells", []):
			projected.append(isometric_cell_center(cell))
	if projected.is_empty():
		return {"minimum": Vector2.ZERO, "maximum": Vector2.ZERO, "projected_size": Vector2.ZERO, "unit": 0.0}
	var min_point: Vector2 = projected[0]
	var max_point: Vector2 = projected[0]
	for point: Vector2 in projected:
		min_point.x = minf(min_point.x, point.x)
		min_point.y = minf(min_point.y, point.y)
		max_point.x = maxf(max_point.x, point.x)
		max_point.y = maxf(max_point.y, point.y)
	var span: float = maxf(maxf(max_point.x - min_point.x, max_point.y - min_point.y), 1.0)
	var unit: float = clampf(minf(available_size.x, available_size.y) / (span + 1.8), 9.0, 25.0)
	return {
		"minimum": min_point,
		"maximum": max_point,
		"projected_size": (max_point - min_point) * unit,
		"unit": unit,
	}


func _plan_isometric_cells(group_plan: Dictionary, frame: Dictionary) -> void:
	var cells: Array = group_plan.get("cells", [])
	var rect: Rect2 = group_plan.get("drawing_rect", Rect2())
	var min_point: Vector2 = frame.get("minimum", Vector2.ZERO)
	var projected_size: Vector2 = frame.get("projected_size", Vector2.ZERO)
	var unit := float(frame.get("unit", 0.0))
	var pane_local_origin: Vector2 = (rect.size - projected_size) * 0.5 - min_point * unit + Vector2(0.0, unit * 0.12)
	var order: Array = range(cells.size())
	order.sort_custom(func(left: int, right: int) -> bool:
		var a: Array = cells[left]
		var b: Array = cells[right]
		var a_depth := int(a[0]) + int(a[1]) + int(a[2])
		var b_depth := int(b[0]) + int(b[1]) + int(b[2])
		return a_depth < b_depth if a_depth != b_depth else _coord_less(a, b)
	)
	var rendered_cells: Array = []
	for index in order:
		var projected_center := isometric_cell_center(cells[index])
		var pane_local_center := pane_local_origin + projected_center * unit
		rendered_cells.append({
			"coordinate": cells[index].duplicate(),
			"projected_coordinate": projected_center,
			"pane_local_center": pane_local_center,
			"center": rect.position + pane_local_center,
			"unit": unit,
		})
	group_plan["rendered_cells"] = rendered_cells


func _draw_cube(center: Vector2, unit: float, base: Color) -> void:
	var half_w := unit * ISOMETRIC_HALF_WIDTH
	var half_h := unit * ISOMETRIC_HALF_HEIGHT
	var depth := unit * ISOMETRIC_DEPTH
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


func isometric_cell_center(cell: Array) -> Vector2:
	var x := float(int(cell[0]))
	var y := float(int(cell[1]))
	var z := float(int(cell[2])) if cell.size() > 2 else 0.0
	# Each canonical unit advances by the matching cube-face edge. This makes
	# adjacent cells read as one face-connected polycube rather than separate
	# miniature cubes with background gaps.
	return Vector2(
		(x - z) * ISOMETRIC_HALF_WIDTH,
		y * ISOMETRIC_DEPTH + (x + z) * ISOMETRIC_HALF_HEIGHT
	)


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


func _coord_less(left: Array, right: Array) -> bool:
	for index in range(min(left.size(), right.size())):
		if int(left[index]) != int(right[index]):
			return int(left[index]) < int(right[index])
	return left.size() < right.size()


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
