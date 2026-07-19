extends Node3D

class_name CameraRig

const PYTHON_DISPLAY_YAW_RAD := 0.5585053606381855  # 32 degrees.
const PYTHON_DISPLAY_PITCH_RAD := -0.4537856055185257  # -26 degrees.
const REPLAY_DISPLAY_VIEW_PRESET_NAME := "PYTHON_DIAGRAM_REPLAY_VIEW"
const LIVE_3D_VIEW_PRESET_NAME := "LIVE_3D_EXTERNAL_DIAGRAM_VIEW"
const LIVE_4D_VIEW_PRESET_NAME := "LIVE_4D_FITTED_W_SLICE_VIEW"
const LIVE_3D_DISPLAY_YAW_RAD := 0.5585053606381855  # 32 degrees.
const LIVE_3D_DISPLAY_PITCH_RAD := 0.4537856055185257  # +26 degrees above the board.
const LIVE_4D_DISPLAY_YAW_RAD := 0.4363323129985824  # 25 degrees for side-by-side W slices.
const LIVE_4D_DISPLAY_PITCH_RAD := 0.3490658503988659  # +20 degrees above the board.
const LIVE_2D_FIT_MARGIN := 1.32
const LIVE_3D_FIT_MARGIN := 1.38
const LIVE_4D_FIT_MARGIN := 1.52
const DEFAULT_ORTHOGRAPHIC_SIZE := 16.0
const MIN_ORTHOGRAPHIC_SIZE := 2.0
const MAX_ORTHOGRAPHIC_SIZE := 96.0
const LIVE_4D_CAMERA_YAW_STEP_RAD := 0.08726646259971647  # 5 degrees.
const LIVE_4D_MATRIX_SCROLL_STEP := 4.0
const LIVE_4D_CAMERA_PITCH_STEP_RAD := 0.06981317007977318  # 4 degrees.
const LIVE_4D_CAMERA_ROLL_STEP_RAD := 0.08726646259971647  # 5 degrees.

@export var min_distance := 8.0
@export var max_distance := 80.0
@export var orbit_sensitivity := 0.01
@export var zoom_sensitivity := 1.1

var _target_focus := Vector3.ZERO
var _current_focus := Vector3.ZERO
var _target_distance := 22.0
var _current_distance := 22.0
var _target_yaw := PYTHON_DISPLAY_YAW_RAD
var _current_yaw := PYTHON_DISPLAY_YAW_RAD
var _target_pitch := PYTHON_DISPLAY_PITCH_RAD
var _current_pitch := PYTHON_DISPLAY_PITCH_RAD
var _target_roll := 0.0
var _current_roll := 0.0
var _base_distance := 22.0
var _base_orthographic_size := DEFAULT_ORTHOGRAPHIC_SIZE
var _zoom_multiplier := 1.0
var _last_frame_signature := ""
var _current_view_preset := REPLAY_DISPLAY_VIEW_PRESET_NAME
var _current_view_octant := "python replay"
var _current_fit_state := "initial"
var _sensitivity_factor := 1.0
var _invert_y := false
var _reduced_motion := false

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = DEFAULT_ORTHOGRAPHIC_SIZE
	_base_orthographic_size = _camera.size
	_update_camera()


func _process(delta: float) -> void:
	var t: float = 1.0 if _reduced_motion else clampf(delta * 8.0, 0.0, 1.0)
	_current_focus = _current_focus.lerp(_target_focus, t)
	_current_distance = lerpf(_current_distance, _target_distance, t)
	_current_yaw = lerpf(_current_yaw, _target_yaw, t)
	_current_pitch = lerpf(_current_pitch, _target_pitch, t)
	_current_roll = lerpf(_current_roll, _target_roll, t)
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
	_target_roll = 0.0
	_current_view_preset = REPLAY_DISPLAY_VIEW_PRESET_NAME
	_current_view_octant = "python replay"
	_current_fit_state = "framed"


func fit_bounds(
	bounds: Dictionary,
	margin: float = 1.14,
	yaw: float = PYTHON_DISPLAY_YAW_RAD,
	pitch: float = PYTHON_DISPLAY_PITCH_RAD,
	view_preset: String = REPLAY_DISPLAY_VIEW_PRESET_NAME,
	view_octant: String = "python replay"
) -> void:
	if not bounds.get("ok", false):
		return
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var size := max_pos - min_pos
	_target_focus = (min_pos + max_pos) * 0.5
	_target_yaw = yaw
	_target_pitch = pitch
	_target_roll = 0.0
	_current_view_preset = view_preset
	_current_view_octant = view_octant
	_current_fit_state = "fit OK"
	var max_extent := maxf(size.x, maxf(size.y, maxf(size.z, 1.0)))
	_base_distance = clampf(max_extent * 1.45 + 6.0, min_distance, max_distance)
	_zoom_multiplier = 1.0
	_target_distance = _base_distance
	_base_orthographic_size = maxf(_projected_orthographic_size(min_pos, max_pos, _target_yaw, _target_pitch, margin), 4.0)
	_camera.size = _base_orthographic_size
	_snap_to_targets()


func orbit(delta: Vector2) -> void:
	_target_yaw -= delta.x * orbit_sensitivity * _sensitivity_factor
	var vertical_direction := 1.0 if _invert_y else -1.0
	_target_pitch = clampf(_target_pitch + delta.y * orbit_sensitivity * _sensitivity_factor * vertical_direction, -1.2, 1.2)
	_current_fit_state = "manual"


func nudge_yaw(delta_radians: float) -> void:
	_target_yaw += delta_radians * _sensitivity_factor
	_current_yaw = _target_yaw
	_current_fit_state = "manual"
	_update_camera()


func nudge_pitch(delta_radians: float) -> void:
	var vertical_direction := -1.0 if _invert_y else 1.0
	_target_pitch = clampf(_target_pitch + delta_radians * _sensitivity_factor * vertical_direction, -1.2, 1.2)
	_current_pitch = _target_pitch
	_current_fit_state = "manual"
	_update_camera()


func nudge_roll(delta_radians: float) -> void:
	_target_roll += delta_radians * _sensitivity_factor
	_current_roll = _target_roll
	_current_fit_state = "manual"
	_update_camera()


func roll(delta: Vector2) -> void:
	_target_roll += delta.x * orbit_sensitivity * _sensitivity_factor
	_current_fit_state = "manual"


func pan_focus(offset: Vector3) -> void:
	_target_focus += offset
	_current_fit_state = "matrix scroll"
	_update_camera()


func zoom(step: float) -> void:
	var multiplier: float = pow(zoom_sensitivity, step)
	if _camera != null and _camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		var orthographic_multiplier: float = clampf(
			_camera.size * multiplier / maxf(_base_orthographic_size, 0.001),
			MIN_ORTHOGRAPHIC_SIZE / maxf(_base_orthographic_size, 0.001),
			MAX_ORTHOGRAPHIC_SIZE / maxf(_base_orthographic_size, 0.001)
		)
		_zoom_multiplier = orthographic_multiplier
		_camera.size = clampf(_base_orthographic_size * _zoom_multiplier, MIN_ORTHOGRAPHIC_SIZE, MAX_ORTHOGRAPHIC_SIZE)
	else:
		_zoom_multiplier = clampf(_zoom_multiplier * multiplier, min_distance / maxf(_base_distance, 0.001), max_distance / maxf(_base_distance, 0.001))
		_target_distance = clampf(_base_distance * _zoom_multiplier, min_distance, max_distance)
	_current_fit_state = "manual"


func view_status_text() -> String:
	if _camera == null:
		return "Camera: %s · pending" % _current_view_preset
	var projection_label := "ortho" if _camera.projection == Camera3D.PROJECTION_ORTHOGONAL else "perspective"
	var yaw_degrees := rad_to_deg(_current_yaw)
	var pitch_degrees := rad_to_deg(_current_pitch)
	var roll_degrees := rad_to_deg(_current_roll)
	var pitch_label := "above %.0f deg" % pitch_degrees if pitch_degrees >= 0.0 else "below %.0f deg" % absf(pitch_degrees)
	return "Camera: %s · %s · size %.2f · zoom %.2fx · %s · yaw %.0f deg · pitch %s · roll %.0f deg · %s" % [
		_current_view_preset,
		projection_label,
		_camera.size,
		_zoom_multiplier,
		_current_view_octant,
		yaw_degrees,
		pitch_label,
		roll_degrees,
		_current_fit_state,
	]


func set_presentation_preferences(sensitivity_factor: float, invert_y: bool, reduced_motion: bool) -> void:
	_sensitivity_factor = clampf(sensitivity_factor, 0.25, 2.0)
	_invert_y = invert_y
	_reduced_motion = reduced_motion


func presentation_snapshot() -> Dictionary:
	return {
		"sensitivity_factor": _sensitivity_factor,
		"invert_y": _invert_y,
		"reduced_motion": _reduced_motion,
		"target_yaw": _target_yaw,
		"target_pitch": _target_pitch,
		"target_roll": _target_roll,
	}


func _snap_to_targets() -> void:
	_current_focus = _target_focus
	_current_distance = _target_distance
	_current_yaw = _target_yaw
	_current_pitch = _target_pitch
	_current_roll = _target_roll
	_update_camera()


func _update_camera() -> void:
	var horizontal_radius: float = _current_distance * cos(_current_pitch)
	var offset: Vector3 = Vector3(
		sin(_current_yaw) * horizontal_radius,
		_current_distance * sin(_current_pitch),
		cos(_current_yaw) * horizontal_radius
	)
	_camera.global_position = _current_focus + offset
	var forward := (_current_focus - _camera.global_position).normalized()
	var rolled_up := Basis(forward, _current_roll) * Vector3.UP
	_camera.look_at(_current_focus, rolled_up)


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
