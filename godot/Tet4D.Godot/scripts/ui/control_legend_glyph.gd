extends Control

class_name ControlLegendGlyph

# Spatial glyphs for the active-play legend. Both are drawn from the screen
# directions the app measures by projecting a board cell and its neighbour
# along each command's real axis, so a glyph cannot disagree with what its key
# does on screen, whatever the camera or 4D basis.
#
# "compass": an arrow per movement key pointing where that key moves the piece,
#   with the keycap at the arrow's tip.
# "plane": a small tripod of the on-screen right / up / away directions plus a
#   slice-row marker for W, with the two directions a rotation mixes lit.

const KIND_COMPASS := "compass"
const KIND_PLANE := "plane"
const COMPASS_ARROW := 34.0
const PLANE_SIZE := 30.0

var kind := KIND_PLANE
# Compass: [{"intent": String, "key": String}] in display order.
var compass_keys: Array = []
# Plane: lowercase local axes the rotation mixes, e.g. ["x", "w"].
var plane_axes: Array = []
var _directions: Dictionary = {}
var _keycaps := {}
var _color_source: Label


static func compass(keys: Array, color_source_factory: Callable) -> ControlLegendGlyph:
	var glyph := ControlLegendGlyph.new()
	glyph.name = "LegendCompass"
	glyph.kind = KIND_COMPASS
	glyph.compass_keys = keys.duplicate(true)
	glyph.custom_minimum_size = Vector2(COMPASS_ARROW * 2.0 + 84.0, COMPASS_ARROW * 2.0 + 64.0)
	for entry in keys:
		var cap: Label = color_source_factory.call(str(entry["key"]))
		glyph._keycaps[str(entry["intent"])] = cap
		glyph.add_child(cap)
		if glyph._color_source == null:
			glyph._color_source = cap
	return glyph


static func plane(axes: Array, color_source: Label) -> ControlLegendGlyph:
	var glyph := ControlLegendGlyph.new()
	glyph.name = "LegendPlaneGlyph"
	glyph.kind = KIND_PLANE
	glyph.plane_axes = axes.duplicate()
	glyph.custom_minimum_size = Vector2(PLANE_SIZE + 8.0, PLANE_SIZE)
	glyph._color_source = color_source
	return glyph


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


# directions: intent or local axis -> normalized screen Vector2 (y down).
func set_directions(directions: Dictionary) -> void:
	_directions = directions.duplicate()
	_place_keycaps()
	queue_redraw()


func directions() -> Dictionary:
	return _directions.duplicate()


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED:
		_place_keycaps()


func _place_keycaps() -> void:
	if kind != KIND_COMPASS:
		return
	var center := size * 0.5
	for intent in _keycaps:
		var cap: Label = _keycaps[intent]
		var direction: Vector2 = _directions.get(intent, Vector2.ZERO)
		cap.visible = direction != Vector2.ZERO
		var cap_size := cap.get_combined_minimum_size()
		cap.size = cap_size
		# Past the arrow tip, pushed out by half the cap so it never covers the arrow.
		var reach := COMPASS_ARROW + 6.0 + 0.5 * absf(direction.x) * cap_size.x + 0.5 * absf(direction.y) * cap_size.y
		cap.position = center + direction * reach - cap_size * 0.5


func _lit_color() -> Color:
	return _color_source.get_theme_color("font_color") if _color_source != null else Color(0.9, 0.9, 0.9)


func _draw() -> void:
	var lit := _lit_color()
	if kind == KIND_COMPASS:
		var center := size * 0.5
		draw_circle(center, 3.0, lit)
		for intent in _keycaps:
			var direction: Vector2 = _directions.get(intent, Vector2.ZERO)
			if direction != Vector2.ZERO:
				_arrow(center, center + direction * COMPASS_ARROW, lit, 2.5)
		return
	var dim := Color(lit, 0.28)
	var center := Vector2(PLANE_SIZE * 0.5, PLANE_SIZE * 0.5)
	var reach := PLANE_SIZE * 0.42
	for axis in ["x", "y", "z"]:
		var direction: Vector2 = _directions.get(axis, Vector2.ZERO)
		if direction == Vector2.ZERO:
			continue
		var on: bool = axis in plane_axes
		# Rotations have no single direction here, so lit axes are two-sided lines.
		draw_line(center - direction * reach, center + direction * reach, lit if on else dim, 3.0 if on else 1.5, true)
	if _directions.has("w"):
		# W has no screen direction of its own: it is the row of slice boards.
		var on: bool = "w" in plane_axes
		for index in range(3):
			var box := Rect2(Vector2(PLANE_SIZE + 1.0, 6.0 + float(index) * 7.0), Vector2(6.0, 5.0))
			if on:
				draw_rect(box, lit, true)
			else:
				draw_rect(box, dim, false, 1.0)


func plane_name() -> String:
	return "".join(PackedStringArray(plane_axes)).to_upper()


# Briefly brightens the glyph's legend row after its key was used.
static func flash_matching(glyphs: Array, plane: String) -> bool:
	for glyph in glyphs:
		var candidate := glyph as ControlLegendGlyph
		if candidate.kind != KIND_PLANE or candidate.plane_name() != plane:
			continue
		var row := candidate.get_parent() as CanvasItem
		if row == null or not row.is_inside_tree():
			return false
		row.set_meta("legend_flash_count", int(row.get_meta("legend_flash_count", 0)) + 1)
		row.modulate = Color(1.7, 1.55, 0.8)
		var tween := row.create_tween()
		tween.tween_property(row, "modulate", Color.WHITE, 0.7)
		return true
	return false


func _arrow(from: Vector2, to: Vector2, color: Color, width: float) -> void:
	draw_line(from, to, color, width, true)
	var direction := (to - from).normalized()
	var side := Vector2(-direction.y, direction.x)
	draw_colored_polygon(PackedVector2Array([to + direction * 2.0, to - direction * 8.0 + side * 5.0, to - direction * 8.0 - side * 5.0]), color)
