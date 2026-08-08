extends RefCounted

class_name ControlFrameMapping

const FRAME_RELATIVE := "relative"
const FRAME_ABSOLUTE := "absolute"
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")

var dimension := 4
var yaw_quarter_turn := 0
var horizontal := {"axis": 0, "sign": 1}
var vertical := {"axis": 1, "sign": 1}
var depth := {"axis": 2, "sign": 1}
var slice := {"axis": 3, "sign": 1}


static func for_3d(yaw_radians: float):
	return new(null, yaw_radians, 3)


static func for_4d(basis, yaw_radians: float):
	return new(basis, yaw_radians, 4)


func _init(basis = null, yaw_radians: float = 0.0, requested_dimension: int = 4) -> void:
	dimension = requested_dimension
	yaw_quarter_turn = nearest_yaw_quarter_turn(yaw_radians)
	var slots := [1, 2, 3, 4]
	if basis != null and basis.has_method("slots"):
		slots = basis.slots()
	var presentation_horizontal := _signed_axis(int(slots[0]))
	var presentation_depth := _signed_axis(int(slots[2]))
	slice = _signed_axis(int(slots[3])) if dimension >= 4 else {"axis": -1, "sign": 0}
	match yaw_quarter_turn:
		0:
			horizontal = presentation_horizontal
			depth = presentation_depth
		1:
			horizontal = presentation_depth
			depth = _flipped(presentation_horizontal)
		2:
			horizontal = _flipped(presentation_horizontal)
			depth = _flipped(presentation_depth)
		_:
			horizontal = _flipped(presentation_depth)
			depth = presentation_horizontal
	vertical = {"axis": SliceBasis4DScript.AXIS_Y, "sign": 1}


static func normalize_frame(value: String) -> String:
	return FRAME_ABSOLUTE if value == FRAME_ABSOLUTE else FRAME_RELATIVE


# Mirrors Python round(yaw / 90): nearest, ties-to-even, then modulo four.
static func nearest_yaw_quarter_turn(yaw_radians: float) -> int:
	var turns := yaw_radians / (PI * 0.5)
	var lower := floori(turns)
	var fraction := turns - float(lower)
	var rounded := lower
	if is_equal_approx(fraction, 0.5):
		rounded = lower if posmod(lower, 2) == 0 else lower + 1
	elif fraction > 0.5:
		rounded = lower + 1
	return posmod(rounded, 4)


func translation_command(intent: String, frame: String) -> String:
	if normalize_frame(frame) == FRAME_ABSOLUTE:
		return intent
	match intent:
		"move_x_neg": return _move_command(horizontal, -1)
		"move_x_pos": return _move_command(horizontal, 1)
		# Z-negative is the physical Forward/Away intent; depth's positive sign is away.
		"move_z_neg": return _move_command(depth, 1)
		"move_z_pos": return _move_command(depth, -1)
		"move_w_neg": return _move_command(slice, -1)
		"move_w_pos": return _move_command(slice, 1)
		_: return intent


func rotation_command(action: String, frame: String) -> String:
	if normalize_frame(frame) == FRAME_ABSOLUTE:
		return action
	var local := _rotation_spec(action)
	if local.is_empty():
		return action
	var a: Dictionary = axis_for_local(str(local[0]))
	var b: Dictionary = axis_for_local(str(local[1]))
	if int(a.get("axis", -1)) < 0 or int(b.get("axis", -1)) < 0 or int(a["axis"]) == int(b["axis"]):
		return action
	var direction := int(local[2]) * int(a["sign"]) * int(b["sign"])
	var axis_a := int(a["axis"])
	var axis_b := int(b["axis"])
	if axis_a > axis_b:
		var swap := axis_a
		axis_a = axis_b
		axis_b = swap
		direction *= -1
	return "rotate_%s_%s" % [_plane_name(axis_a, axis_b), "pos" if direction > 0 else "neg"]


func axis_for_local(label: String) -> Dictionary:
	match label:
		"x": return horizontal.duplicate()
		"y": return vertical.duplicate()
		"z": return depth.duplicate()
		"w": return slice.duplicate()
		_: return {"axis": -1, "sign": 0}


func snapshot() -> Dictionary:
	return {
		"yaw_quarter_turn": yaw_quarter_turn,
		"horizontal": horizontal.duplicate(), "vertical": vertical.duplicate(),
		"depth": depth.duplicate(), "slice": slice.duplicate(),
		"horizontal_axis": signed_label(horizontal), "depth_axis": signed_label(depth),
		"slice_axis": signed_label(slice), "gravity_axis": "+Y",
	}


func signed_label(axis: Dictionary) -> String:
	var index := int(axis.get("axis", -1))
	if index < 0:
		return "-"
	return ("+" if int(axis.get("sign", 1)) > 0 else "-") + SliceBasis4DScript.axis_name(index)


func opposite_label(axis: Dictionary) -> String:
	var copy := axis.duplicate()
	copy["sign"] = -int(copy.get("sign", 1))
	return signed_label(copy)


func relative_plane_annotation(action: String) -> String:
	var local := _rotation_spec(action)
	if local.is_empty():
		return ""
	return "%s%s" % [SliceBasis4DScript.axis_name(int(axis_for_local(str(local[0]))["axis"])), SliceBasis4DScript.axis_name(int(axis_for_local(str(local[1]))["axis"]))]


func _move_command(axis: Dictionary, local_direction: int) -> String:
	var canonical_axis := int(axis.get("axis", -1))
	if canonical_axis < 0:
		return ""
	var direction := local_direction * int(axis.get("sign", 1))
	return "move_%s_%s" % [SliceBasis4DScript.axis_name(canonical_axis).to_lower(), "pos" if direction > 0 else "neg"]


static func _signed_axis(value: int) -> Dictionary:
	return {"axis": absi(value) - 1, "sign": 1 if value > 0 else -1}


static func _flipped(axis: Dictionary) -> Dictionary:
	return {"axis": int(axis["axis"]), "sign": -int(axis["sign"])}


static func _rotation_spec(action: String) -> Array:
	var direction := 1 if action.ends_with("_pos") else -1
	var plane := action.trim_prefix("rotate_").trim_suffix("_pos").trim_suffix("_neg")
	if plane.length() != 2:
		return []
	return [plane.substr(0, 1), plane.substr(1, 1), direction]


static func _plane_name(axis_a: int, axis_b: int) -> String:
	return "%s%s" % [SliceBasis4DScript.axis_name(axis_a).to_lower(), SliceBasis4DScript.axis_name(axis_b).to_lower()]
