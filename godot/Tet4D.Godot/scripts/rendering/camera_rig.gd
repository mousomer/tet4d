extends Node3D

class_name CameraRig

@export var min_distance := 8.0
@export var max_distance := 80.0
@export var orbit_sensitivity := 0.01
@export var pan_sensitivity := 0.015
@export var zoom_sensitivity := 1.1

var _target_focus := Vector3.ZERO
var _current_focus := Vector3.ZERO
var _target_distance := 18.0
var _current_distance := 18.0
var _target_yaw := -0.65
var _current_yaw := -0.65
var _target_pitch := -0.38
var _current_pitch := -0.38

@onready var _camera: Camera3D = $Camera3D


func _process(delta: float) -> void:
	var t := clamp(delta * 8.0, 0.0, 1.0)
	_current_focus = _current_focus.lerp(_target_focus, t)
	_current_distance = lerpf(_current_distance, _target_distance, t)
	_current_yaw = lerpf(_current_yaw, _target_yaw, t)
	_current_pitch = lerpf(_current_pitch, _target_pitch, t)
	_update_camera()


func frame_board(board_shape: Array, dimension: int, slice_stride: float) -> void:
	if board_shape.is_empty():
		return
	var x_extent := float(board_shape[0]) if board_shape.size() > 0 else 4.0
	var y_extent := float(board_shape[1]) if board_shape.size() > 1 else 4.0
	var z_extent := float(board_shape[2]) if board_shape.size() > 2 else 1.0
	var w_extent := float(board_shape[3]) if dimension >= 4 and board_shape.size() > 3 else 1.0
	if dimension >= 4:
		x_extent += max(w_extent - 1.0, 0.0) * slice_stride
	_target_focus = Vector3((x_extent - 1.0) * 0.5, -(y_extent - 1.0) * 0.5, (z_extent - 1.0) * 0.5)
	_target_distance = clampf(max(x_extent, y_extent, z_extent * 2.0) * 1.6 + 4.0, min_distance, max_distance)


func orbit(delta: Vector2) -> void:
	_target_yaw -= delta.x * orbit_sensitivity
	_target_pitch = clampf(_target_pitch - delta.y * orbit_sensitivity, -1.2, 0.25)


func pan(delta: Vector2) -> void:
	var right := Basis(Vector3.UP, _target_yaw).x
	var up := Vector3.UP
	_target_focus += (-right * delta.x + up * delta.y) * pan_sensitivity * _target_distance


func zoom(step: float) -> void:
	var multiplier := pow(zoom_sensitivity, step)
	_target_distance = clampf(_target_distance * multiplier, min_distance, max_distance)


func _update_camera() -> void:
	var horizontal_radius := _current_distance * cos(_current_pitch)
	var offset := Vector3(
		sin(_current_yaw) * horizontal_radius,
		_current_distance * sin(_current_pitch),
		cos(_current_yaw) * horizontal_radius
	)
	_camera.global_position = _current_focus + offset
	_camera.look_at(_current_focus, Vector3.UP)
