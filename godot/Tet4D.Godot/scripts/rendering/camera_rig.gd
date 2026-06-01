extends Node3D

class_name CameraRig

const PYTHON_DISPLAY_YAW_RAD := 0.5585053606381855  # 32 degrees.
const PYTHON_DISPLAY_PITCH_RAD := -0.4537856055185257  # -26 degrees.
const LIVE_3D_DISPLAY_YAW_RAD := 0.6981317007977318  # 40 degrees.
const LIVE_3D_DISPLAY_PITCH_RAD := -0.5585053606381855  # -32 degrees.
const DEFAULT_ORTHOGRAPHIC_SIZE := 16.0

@export var min_distance := 8.0
@export var max_distance := 80.0
@export var orbit_sensitivity := 0.01
@export var pan_sensitivity := 0.015
@export var zoom_sensitivity := 1.1

var _target_focus := Vector3.ZERO
var _current_focus := Vector3.ZERO
var _target_distance := 22.0
var _current_distance := 22.0
var _target_yaw := PYTHON_DISPLAY_YAW_RAD
var _current_yaw := PYTHON_DISPLAY_YAW_RAD
var _target_pitch := PYTHON_DISPLAY_PITCH_RAD
var _current_pitch := PYTHON_DISPLAY_PITCH_RAD
var _base_distance := 22.0
var _zoom_multiplier := 1.0
var _last_frame_signature := ""

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = DEFAULT_ORTHOGRAPHIC_SIZE
	_update_camera()


func _process(delta: float) -> void:
	var t: float = clampf(delta * 8.0, 0.0, 1.0)
	_current_focus = _current_focus.lerp(_target_focus, t)
	_current_distance = lerpf(_current_distance, _target_distance, t)
	_current_yaw = lerpf(_current_yaw, _target_yaw, t)
	_current_pitch = lerpf(_current_pitch, _target_pitch, t)
	_update_camera()


func frame_board(board_shape: Array, dimension: int, slice_stride: float) -> void:
	if board_shape.is_empty():
		return
	var signature := "%s|%d|%.4f" % [str(board_shape), dimension, slice_stride]
	var x_extent := float(board_shape[0]) if board_shape.size() > 0 else 4.0
	var y_extent := float(board_shape[1]) if board_shape.size() > 1 else 4.0
	var z_extent := float(board_shape[2]) if board_shape.size() > 2 else 1.0
	var w_extent := float(board_shape[3]) if dimension >= 4 and board_shape.size() > 3 else 1.0
	if dimension >= 4:
		x_extent += max(w_extent - 1.0, 0.0) * slice_stride
	var x_center: float = maxf(w_extent - 1.0, 0.0) * slice_stride * 0.5 if dimension >= 4 else 0.0
	_target_focus = Vector3(x_center, 0.0, 0.0)
	var framed_distance := clampf(max(x_extent, y_extent, z_extent * 2.0) * 1.6 + 4.0, min_distance, max_distance)
	if signature != _last_frame_signature:
		_base_distance = framed_distance
		_last_frame_signature = signature
	_target_distance = clampf(_base_distance * _zoom_multiplier, min_distance, max_distance)
	_target_yaw = PYTHON_DISPLAY_YAW_RAD
	_target_pitch = PYTHON_DISPLAY_PITCH_RAD


func fit_bounds(
	bounds: Dictionary,
	margin: float = 1.14,
	yaw: float = PYTHON_DISPLAY_YAW_RAD,
	pitch: float = PYTHON_DISPLAY_PITCH_RAD
) -> void:
	if not bounds.get("ok", false):
		return
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var size := max_pos - min_pos
	_target_focus = (min_pos + max_pos) * 0.5
	_target_yaw = yaw
	_target_pitch = pitch
	var max_extent := maxf(size.x, maxf(size.y, maxf(size.z, 1.0)))
	_base_distance = clampf(max_extent * 1.45 + 6.0, min_distance, max_distance)
	_zoom_multiplier = 1.0
	_target_distance = _base_distance
	_camera.size = maxf(_projected_orthographic_size(min_pos, max_pos, _target_yaw, _target_pitch, margin), 4.0)
	_snap_to_targets()


func orbit(delta: Vector2) -> void:
	_target_yaw -= delta.x * orbit_sensitivity
	_target_pitch = clampf(_target_pitch - delta.y * orbit_sensitivity, -1.2, 0.25)


func pan(delta: Vector2) -> void:
	var right: Vector3 = Basis(Vector3.UP, _target_yaw).x
	var up: Vector3 = Vector3.UP
	_target_focus += (-right * delta.x + up * delta.y) * pan_sensitivity * _target_distance


func zoom(step: float) -> void:
	var multiplier: float = pow(zoom_sensitivity, step)
	_zoom_multiplier = clampf(_zoom_multiplier * multiplier, min_distance / maxf(_base_distance, 0.001), max_distance / maxf(_base_distance, 0.001))
	_target_distance = clampf(_base_distance * _zoom_multiplier, min_distance, max_distance)


func _snap_to_targets() -> void:
	_current_focus = _target_focus
	_current_distance = _target_distance
	_current_yaw = _target_yaw
	_current_pitch = _target_pitch
	_update_camera()


func _update_camera() -> void:
	var horizontal_radius: float = _current_distance * cos(_current_pitch)
	var offset: Vector3 = Vector3(
		sin(_current_yaw) * horizontal_radius,
		_current_distance * sin(_current_pitch),
		cos(_current_yaw) * horizontal_radius
	)
	_camera.global_position = _current_focus + offset
	_camera.look_at(_current_focus, Vector3.UP)


func _projected_orthographic_size(min_pos: Vector3, max_pos: Vector3, yaw: float, pitch: float, margin: float) -> float:
	var projected_min := Vector2(INF, INF)
	var projected_max := Vector2(-INF, -INF)
	for corner in _box_corners(min_pos, max_pos):
		var projected := _project_for_fit(corner, yaw, pitch)
		projected_min.x = minf(projected_min.x, projected.x)
		projected_min.y = minf(projected_min.y, projected.y)
		projected_max.x = maxf(projected_max.x, projected.x)
		projected_max.y = maxf(projected_max.y, projected.y)
	var span := projected_max - projected_min
	var aspect := _viewport_aspect()
	return maxf(span.y, span.x / maxf(aspect, 0.001)) * margin


func _box_corners(min_pos: Vector3, max_pos: Vector3) -> Array:
	return [
		Vector3(min_pos.x, min_pos.y, min_pos.z),
		Vector3(min_pos.x, min_pos.y, max_pos.z),
		Vector3(min_pos.x, max_pos.y, min_pos.z),
		Vector3(min_pos.x, max_pos.y, max_pos.z),
		Vector3(max_pos.x, min_pos.y, min_pos.z),
		Vector3(max_pos.x, min_pos.y, max_pos.z),
		Vector3(max_pos.x, max_pos.y, min_pos.z),
		Vector3(max_pos.x, max_pos.y, max_pos.z),
	]


func _project_for_fit(point: Vector3, yaw: float, pitch: float) -> Vector2:
	var yaw_cos := cos(yaw)
	var yaw_sin := sin(yaw)
	var pitch_cos := cos(pitch)
	var pitch_sin := sin(pitch)
	var x_after_yaw := yaw_cos * point.x + yaw_sin * point.z
	var z_after_yaw := -yaw_sin * point.x + yaw_cos * point.z
	var y_after_pitch := pitch_cos * point.y - pitch_sin * z_after_yaw
	return Vector2(x_after_yaw, y_after_pitch)


func _viewport_aspect() -> float:
	var viewport := _camera.get_viewport()
	if viewport == null:
		return 16.0 / 9.0
	var rect := viewport.get_visible_rect()
	if rect.size.y <= 0.0:
		return 16.0 / 9.0
	return maxf(rect.size.x / rect.size.y, 0.1)
