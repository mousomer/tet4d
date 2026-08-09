extends RefCounted

class_name SliceBasis4D

const AXIS_X := 0
const AXIS_Y := 1
const AXIS_Z := 2
const AXIS_W := 3

const PLANE_XW := "xw"
const PLANE_ZW := "zw"
const PLANE_ZX := "zx"

# Signed axes use +/- (axis + 1), avoiding a negative-zero representation.
const IDENTITY_SLOTS := [AXIS_X + 1, AXIS_Y + 1, AXIS_Z + 1, AXIS_W + 1]

var _slots: Array = IDENTITY_SLOTS.duplicate()


func _init(slots: Array = []) -> void:
	if slots.is_empty():
		return
	if not is_valid_slots(slots):
		push_error("Invalid 4D slice basis: %s" % str(slots))
		return
	_slots = slots.duplicate()


static func identity():
	return new(IDENTITY_SLOTS)


static func from_slots(slots: Array):
	return new(slots)


static func is_valid_slots(slots: Array) -> bool:
	if slots.size() != 4 or int(slots[1]) != AXIS_Y + 1:
		return false
	var seen := {}
	for raw_axis in slots:
		if typeof(raw_axis) != TYPE_INT:
			return false
		var absolute_axis := absi(int(raw_axis))
		if absolute_axis < 1 or absolute_axis > 4 or seen.has(absolute_axis):
			return false
		seen[absolute_axis] = true
	return seen.size() == 4


func slots() -> Array:
	return _slots.duplicate()


func key() -> String:
	return ",".join(_slots.map(func(value) -> String: return str(int(value))))


func equals(other) -> bool:
	return other != null and other.has_method("slots") and _slots == other.slots()


func is_identity() -> bool:
	return _slots == IDENTITY_SLOTS


func turned(plane: String, quarter_turn: int):
	if quarter_turn not in [-1, 1]:
		push_error("4D basis turns must be exact +/-90-degree turns")
		return get_script().new(_slots)
	var axes := _plane_axes(plane)
	if axes.is_empty():
		push_error("Unsupported 4D basis plane: %s" % plane)
		return get_script().new(_slots)
	var result := []
	for signed_axis in _slots:
		result.append(_turn_signed_axis(int(signed_axis), int(axes[0]), int(axes[1]), quarter_turn))
	return get_script().new(result)


func presentation_coordinate(
	canonical_coordinate: Array,
	canonical_dimensions: Array,
	allow_above_board_y: bool = false
) -> Dictionary:
	if not _valid_coordinate(canonical_coordinate, canonical_dimensions, allow_above_board_y):
		return {"ok": false}
	var visible := []
	for slot_index in range(3):
		visible.append(_coordinate_for_signed_axis(canonical_coordinate, canonical_dimensions, int(_slots[slot_index])))
	return {
		"ok": true,
		"layer_index": _coordinate_for_signed_axis(canonical_coordinate, canonical_dimensions, int(_slots[3])),
		"visible_cell_3d": visible,
		"visible_dimensions": visible_dimensions(canonical_dimensions),
		"layer_count": layer_count(canonical_dimensions),
	}


func canonical_coordinate(layer_index: int, visible_cell_3d: Array, canonical_dimensions: Array) -> Array:
	if canonical_dimensions.size() != 4 or visible_cell_3d.size() != 3:
		return []
	if layer_index < 0 or layer_index >= layer_count(canonical_dimensions):
		return []
	var visible_dims := visible_dimensions(canonical_dimensions)
	for index in range(3):
		if int(visible_cell_3d[index]) < 0 or int(visible_cell_3d[index]) >= int(visible_dims[index]):
			return []
	var canonical := [0, 0, 0, 0]
	for slot_index in range(4):
		var presentation_value := layer_index if slot_index == 3 else int(visible_cell_3d[slot_index])
		var signed_axis := int(_slots[slot_index])
		var axis := absi(signed_axis) - 1
		canonical[axis] = presentation_value if signed_axis > 0 else int(canonical_dimensions[axis]) - 1 - presentation_value
	return canonical


func visible_dimensions(canonical_dimensions: Array) -> Array:
	if canonical_dimensions.size() != 4:
		return []
	return [
		int(canonical_dimensions[absi(int(_slots[0])) - 1]),
		int(canonical_dimensions[AXIS_Y]),
		int(canonical_dimensions[absi(int(_slots[2])) - 1]),
	]


func layer_count(canonical_dimensions: Array) -> int:
	if canonical_dimensions.size() != 4:
		return 1
	return int(canonical_dimensions[absi(int(_slots[3])) - 1])


func semantic_slice_coordinate(layer_index: int, canonical_dimensions: Array) -> int:
	var signed_axis := int(_slots[3])
	var extent := layer_count(canonical_dimensions)
	return layer_index if signed_axis > 0 else extent - 1 - layer_index


func slice_axis_label() -> String:
	return signed_axis_label(int(_slots[3]))


func indicator_snapshot() -> Dictionary:
	return {
		"slots": slots(),
		"key": key(),
		"visible_axes": [signed_axis_label(int(_slots[0])), "+Y", signed_axis_label(int(_slots[2]))],
		"slice_axis": signed_axis_label(int(_slots[3])),
		"gravity_axis": "+Y",
		"text": "View: %s · +Y · %s\nSlice: %s · Gravity: Y down" % [
			signed_axis_label(int(_slots[0])),
			signed_axis_label(int(_slots[2])),
			signed_axis_label(int(_slots[3])),
		],
	}


func canonical_movement_command(presentation_intent: String) -> String:
	var slot_index := -1
	var direction := 0
	match presentation_intent:
		"move_x_neg":
			slot_index = 0
			direction = -1
		"move_x_pos":
			slot_index = 0
			direction = 1
		"move_z_neg":
			slot_index = 2
			direction = -1
		"move_z_pos":
			slot_index = 2
			direction = 1
		"move_w_neg":
			slot_index = 3
			direction = -1
		"move_w_pos":
			slot_index = 3
			direction = 1
		_:
			return presentation_intent
	var signed_axis := int(_slots[slot_index])
	var canonical_direction := direction * (1 if signed_axis > 0 else -1)
	return "move_%s_%s" % [axis_name(absi(signed_axis) - 1).to_lower(), "pos" if canonical_direction > 0 else "neg"]


static func signed_axis_label(signed_axis: int) -> String:
	var label := axis_name(absi(signed_axis) - 1)
	return "+%s" % label if signed_axis > 0 else "-%s" % label


static func axis_name(axis: int) -> String:
	match axis:
		AXIS_X:
			return "X"
		AXIS_Y:
			return "Y"
		AXIS_Z:
			return "Z"
		AXIS_W:
			return "W"
		_:
			return "?"


static func _plane_axes(plane: String) -> Array:
	match plane.to_lower():
		PLANE_XW:
			return [AXIS_X, AXIS_W]
		PLANE_ZW:
			return [AXIS_Z, AXIS_W]
		PLANE_ZX:
			return [AXIS_Z, AXIS_X]
		_:
			return []


static func _turn_signed_axis(signed_axis: int, axis_a: int, axis_b: int, quarter_turn: int) -> int:
	var sign_value := 1 if signed_axis > 0 else -1
	var axis := absi(signed_axis) - 1
	if axis == axis_a:
		return (axis_b + 1) * sign_value * (1 if quarter_turn > 0 else -1)
	if axis == axis_b:
		return (axis_a + 1) * sign_value * (-1 if quarter_turn > 0 else 1)
	return signed_axis


static func _coordinate_for_signed_axis(coordinate: Array, dimensions: Array, signed_axis: int) -> int:
	var axis := absi(signed_axis) - 1
	var semantic := int(coordinate[axis])
	return semantic if signed_axis > 0 else int(dimensions[axis]) - 1 - semantic


static func _valid_coordinate(coordinate: Array, dimensions: Array, allow_above_board_y: bool = false) -> bool:
	if coordinate.size() != 4 or dimensions.size() != 4:
		return false
	for axis in range(4):
		if not _is_integral_number(coordinate[axis]) or not _is_integral_number(dimensions[axis]):
			return false
		var extent := int(dimensions[axis])
		var value := int(coordinate[axis])
		if extent < 1 or value >= extent:
			return false
		if value < 0 and not (allow_above_board_y and axis == AXIS_Y):
			return false
	return true


static func _is_integral_number(value) -> bool:
	if typeof(value) == TYPE_INT:
		return true
	return typeof(value) == TYPE_FLOAT and is_finite(float(value)) and float(value) == float(int(value))
