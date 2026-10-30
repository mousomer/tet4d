extends RefCounted

# Coordinate conversions only. Preferences, OS queries, UI application, camera
# semantics and native commands stay with their existing owners.
const DESIGN_MINIMUM := Vector2(640, 480)
const MENU_REFERENCE := Vector2(1280, 720)
const LIVE_REFERENCE := Vector2(1280, 800)
const MAX_WINDOW_SCALE := 2.0


static func available_size(canvas_size: Vector2, ui_scale: float) -> Vector2:
	return canvas_size / maxf(ui_scale, 0.01)


static func local_insets(canvas_insets: Dictionary, ui_scale: float) -> Dictionary:
	var result: Dictionary = {}
	for side in ["left", "top", "right", "bottom"]:
		result[side] = float(canvas_insets.get(side, 0)) / maxf(ui_scale, 0.01)
	return result


static func usable_rect(canvas_size: Vector2, canvas_insets: Dictionary, ui_scale: float, inset: float) -> Rect2:
	var margins := local_insets(canvas_insets, ui_scale)
	var origin := Vector2(margins["left"], margins["top"])
	var far := available_size(canvas_size, ui_scale) - Vector2(margins["right"], margins["bottom"])
	return Rect2(origin, (far - origin).max(Vector2.ZERO)).grow(-inset)


static func local_rect(root_rect: Rect2, local_to_root: Transform2D) -> Rect2:
	var inverse := local_to_root.affine_inverse()
	var origin: Vector2 = inverse * root_rect.position
	return Rect2(origin, inverse * root_rect.end - origin)


# Mouse relative is already in root-viewport units, before the surface's local
# transform. Do not apply window stretch a second time. Use actual render size
# including rounding, never an assumed display-density multiplier.
static func render_delta(root_delta: Vector2, local_to_root: Transform2D, logical_size: Vector2, render_size: Vector2) -> Vector2:
	if logical_size.x <= 0.0 or logical_size.y <= 0.0 or render_size.x <= 0.0 or render_size.y <= 0.0 or is_zero_approx(local_to_root.determinant()):
		return Vector2.ZERO
	var inverse := local_to_root.affine_inverse()
	var local_delta: Vector2 = inverse * root_delta - inverse * Vector2.ZERO
	return local_delta * render_size / logical_size


static func window_scale(points: Vector2, reference: Vector2, minimum: float) -> float:
	if points.x <= 0.0 or points.y <= 0.0:
		return 1.0
	return clampf(minf(points.x / reference.x, points.y / reference.y), minimum, MAX_WINDOW_SCALE)


static func design_resolution(pixels: Vector2, display_scale: float, menu: bool, menu_minimum: float) -> Vector2i:
	var points := pixels / maxf(display_scale, 0.01)
	var factor := window_scale(points, MENU_REFERENCE if menu else LIVE_REFERENCE, menu_minimum if menu else 1.0)
	var logical := points / factor
	return Vector2i(int(ceilf(maxf(logical.x, DESIGN_MINIMUM.x))), int(ceilf(maxf(logical.y, DESIGN_MINIMUM.y))))


static func apparent_size(pixels: Vector2, display_scale: float, ui_scale: float, menu: bool, menu_minimum: float) -> Vector2:
	var points := pixels / maxf(display_scale, 0.01)
	return points / window_scale(points, MENU_REFERENCE if menu else LIVE_REFERENCE, menu_minimum if menu else 1.0) / maxf(ui_scale, 0.01)
