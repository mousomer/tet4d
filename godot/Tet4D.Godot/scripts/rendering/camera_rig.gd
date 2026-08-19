extends Node3D

class_name CameraRig

const PYTHON_DISPLAY_YAW_RAD := 0.5585053606381855  # 32 degrees.
const PYTHON_DISPLAY_PITCH_RAD := -0.4537856055185257  # -26 degrees.
const LIVE_3D_DISPLAY_YAW_RAD := 0.5585053606381855  # 32 degrees.
const LIVE_3D_DISPLAY_PITCH_RAD := 0.4537856055185257  # +26 degrees above the board.
# The fitted gameplay mount sits 25 degrees past the board's far side. A fixed
# outer rendered-world reflection preserves board-frame +X as screen-right
# while board-frame +Z recedes into the scene.
const LIVE_4D_DISPLAY_YAW_RAD := 3.5779249665883754  # 205 degrees.
const LIVE_4D_DISPLAY_PITCH_RAD := 0.3490658503988659  # +20 degrees above the board.
const LIVE_2D_FIT_MARGIN := 1.32
const LIVE_3D_FIT_MARGIN := 1.38
const LIVE_4D_FIT_MARGIN := 1.32
const DEFAULT_ORTHOGRAPHIC_SIZE := 16.0
const MIN_ORTHOGRAPHIC_SIZE := 2.0
const MAX_ORTHOGRAPHIC_SIZE := 96.0
const LIVE_4D_CAMERA_YAW_STEP_RAD := 0.08726646259971647  # 5 degrees.
const LIVE_4D_MATRIX_SCROLL_STEP := 4.0
const LIVE_4D_CAMERA_PITCH_STEP_RAD := 0.06981317007977318  # 4 degrees.
const LIVE_4D_CAMERA_ROLL_STEP_RAD := 0.08726646259971647  # 5 degrees.
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")
const CameraPresetScript = preload("res://scripts/presentation/camera_preset.gd")
const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const ORIENTATION_GIZMO_SCREEN_SCALE := 0.060
const ORIENTATION_GIZMO_EDGE_OFFSET := 0.41
const ORIENTATION_GIZMO_CAMERA_DEPTH := 2.0

@export var min_distance := 8.0
@export var max_distance := 80.0
@export var orbit_sensitivity := 0.01
@export var zoom_sensitivity := 1.1

var _target_focus := Vector3.ZERO
var _current_focus := Vector3.ZERO
var _fit_focus := Vector3.ZERO
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
var _view_context := "replay view"
var _framing_status := "initial"
var _sensitivity_factor := 1.0
var _invert_y := false
var _interpolation_scale := 1.0
var _horizontal_reflection_active := false
var _world_presentation_root: Node3D
var _orientation_gizmo: Node3D
var _orientation_basis_snapshot := {
	"visible_axes": ["+X", "+Y", "+Z"],
	"gravity_axis": "+Y",
}

@onready var _camera: Camera3D = $Camera3D


func _ready() -> void:
	_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	_camera.size = DEFAULT_ORTHOGRAPHIC_SIZE
	_base_orthographic_size = _camera.size
	_build_orientation_gizmo()
	_update_camera()


func _process(delta: float) -> void:
	var t: float = 1.0 if _interpolation_scale <= 0.0 else clampf(delta * 8.0 * _interpolation_scale, 0.0, 1.0)
	_current_focus = _current_focus.lerp(_target_focus, t)
	_current_distance = lerpf(_current_distance, _target_distance, t)
	_current_yaw = lerpf(_current_yaw, _target_yaw, t)
	_current_pitch = lerpf(_current_pitch, _target_pitch, t)
	_current_roll = lerpf(_current_roll, _target_roll, t)
	_update_camera()


func establish_canonical_projection() -> void:
	if _camera != null:
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL


func establish_outer_view(
	yaw: float,
	pitch: float,
	roll_radians: float,
	horizontal_reflection_active: bool
) -> void:
	_target_yaw = yaw
	_target_pitch = pitch
	_target_roll = roll_radians
	_set_horizontal_reflection(horizontal_reflection_active)
	_view_context = "outer view"
	_snap_orientation_to_targets()


func fit_current_bounds(bounds: Dictionary, margin: float = 1.14) -> void:
	if not bounds.get("ok", false):
		return
	var min_pos: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_pos: Vector3 = bounds.get("max", Vector3.ZERO)
	var size := max_pos - min_pos
	_target_focus = (min_pos + max_pos) * 0.5
	_fit_focus = _target_focus
	_framing_status = "fit OK"
	var max_extent := maxf(size.x, maxf(size.y, maxf(size.z, 1.0)))
	_base_distance = clampf(max_extent * 1.45 + 6.0, min_distance, max_distance)
	_zoom_multiplier = 1.0
	_target_distance = _base_distance
	_base_orthographic_size = maxf(_projected_orthographic_size(min_pos, max_pos, _current_yaw, _current_pitch, margin), 4.0)
	if _camera != null and _camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		_camera.size = _base_orthographic_size
	_snap_framing_to_targets()


func restore_fitted_framing() -> void:
	_target_focus = _fit_focus
	_zoom_multiplier = 1.0
	_target_distance = _base_distance
	if _camera != null and _camera.projection == Camera3D.PROJECTION_ORTHOGONAL:
		_camera.size = _base_orthographic_size
	_framing_status = "fitted baseline"
	_snap_framing_to_targets()


# Clears mode-owned framing/reflection/interpolation state without touching
# persisted sensitivity, invert-Y, or reduced-motion preferences.
func clear_presentation_state() -> void:
	_target_focus = Vector3.ZERO
	_current_focus = Vector3.ZERO
	_fit_focus = Vector3.ZERO
	_target_distance = 22.0
	_current_distance = 22.0
	_base_distance = 22.0
	_target_yaw = PYTHON_DISPLAY_YAW_RAD
	_current_yaw = PYTHON_DISPLAY_YAW_RAD
	_target_pitch = PYTHON_DISPLAY_PITCH_RAD
	_current_pitch = PYTHON_DISPLAY_PITCH_RAD
	_target_roll = 0.0
	_current_roll = 0.0
	_zoom_multiplier = 1.0
	_base_orthographic_size = DEFAULT_ORTHOGRAPHIC_SIZE
	_view_context = "cleared"
	_framing_status = "cleared"
	_set_horizontal_reflection(false)
	set_orientation_gizmo_visible(false)
	if _camera != null:
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		_camera.size = DEFAULT_ORTHOGRAPHIC_SIZE
		_update_camera()


func orbit(delta: Vector2) -> void:
	_target_yaw -= delta.x * orbit_sensitivity * _sensitivity_factor
	var vertical_direction := 1.0 if _invert_y else -1.0
	_target_pitch = clampf(_target_pitch + delta.y * orbit_sensitivity * _sensitivity_factor * vertical_direction, -1.2, 1.2)
	_mark_manual_view("manual")


func nudge_yaw(delta_radians: float) -> void:
	_target_yaw += delta_radians * _sensitivity_factor
	_current_yaw = _target_yaw
	_mark_manual_view("manual")
	_update_camera()


func nudge_pitch(delta_radians: float) -> void:
	var vertical_direction := -1.0 if _invert_y else 1.0
	_target_pitch = clampf(_target_pitch + delta_radians * _sensitivity_factor * vertical_direction, -1.2, 1.2)
	_current_pitch = _target_pitch
	_mark_manual_view("manual")
	_update_camera()


func nudge_roll(delta_radians: float) -> void:
	_target_roll += delta_radians * _sensitivity_factor
	_current_roll = _target_roll
	_mark_manual_view("manual")
	_update_camera()


func roll(delta: Vector2) -> void:
	_target_roll += delta.x * orbit_sensitivity * _sensitivity_factor
	_mark_manual_view("manual")


func pan_focus(offset: Vector3) -> void:
	_target_focus += offset
	_mark_manual_view("matrix scroll")
	if _camera != null:
		_update_camera()


func pan_screen(delta: Vector2) -> void:
	if _camera == null:
		return
	var viewport := _camera.get_viewport()
	var viewport_height := 1.0
	if viewport != null:
		viewport_height = maxf(viewport.get_visible_rect().size.y, 1.0)
	var world_units_per_pixel := _camera.size / viewport_height
	var effective_camera_basis := _camera.get_camera_transform().basis
	var offset := (
		-effective_camera_basis.x * delta.x
		+ effective_camera_basis.y * delta.y
	) * world_units_per_pixel
	_target_focus += offset
	_current_focus = _target_focus
	_mark_manual_view("manual pan")
	_update_camera()


func set_orientation_gizmo_visible(visible: bool) -> void:
	if _orientation_gizmo != null:
		_orientation_gizmo.visible = visible
		if visible:
			_update_orientation_gizmo()


func set_world_presentation_root(world_presentation_root: Node3D) -> void:
	_world_presentation_root = world_presentation_root
	_apply_world_presentation_transform()


func set_orientation_basis(basis) -> void:
	if basis == null or not basis.has_method("indicator_snapshot"):
		return
	_orientation_basis_snapshot = basis.indicator_snapshot()
	_update_gizmo_axes()


func set_control_frame_mapping(mapping: Dictionary) -> void:
	if mapping.is_empty():
		return
	_orientation_basis_snapshot["visible_axes"] = [str(mapping.get("horizontal_axis", "+X")), "+Y", str(mapping.get("depth_axis", "+Z"))]
	_orientation_basis_snapshot["slice_axis"] = str(mapping.get("slice_axis", "+W"))
	_update_gizmo_axes()


func control_frame_yaw() -> float:
	return _target_yaw


func apply_outer_view_action(id: String) -> bool:
	if not CameraPresetScript.is_known(id):
		return false
	var preset := CameraPresetScript.definition(id)
	establish_outer_view(
		float(preset.get("yaw", _target_yaw)),
		float(preset.get("pitch", _target_pitch)),
		0.0,
		false
	)
	_view_context = "view action"
	restore_fitted_framing()
	return true


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
	_mark_manual_view("manual")


func view_status_text() -> String:
	if _camera == null:
		return "View: pending"
	var projection_label := "ortho" if _camera.projection == Camera3D.PROJECTION_ORTHOGONAL else "perspective"
	var yaw_degrees := rad_to_deg(_current_yaw)
	var pitch_degrees := rad_to_deg(_current_pitch)
	var roll_degrees := rad_to_deg(_current_roll)
	var pitch_label := "above %.0f deg" % pitch_degrees if pitch_degrees >= 0.0 else "below %.0f deg" % absf(pitch_degrees)
	return "View: %s · size %.2f · zoom %.2fx · %s · yaw %.0f deg · pitch %s · roll %.0f deg · %s" % [
		projection_label,
		_camera.size,
		_zoom_multiplier,
		_view_context,
		yaw_degrees,
		pitch_label,
		roll_degrees,
		_framing_status,
	]


func set_presentation_preferences(sensitivity_factor: float, invert_y: bool, interpolation_scale: float = 1.0) -> void:
	_sensitivity_factor = clampf(sensitivity_factor, 0.25, 2.0)
	_invert_y = invert_y
	_interpolation_scale = clampf(interpolation_scale, 0.0, 1.0)


func presentation_snapshot() -> Dictionary:
	return {
		"sensitivity_factor": _sensitivity_factor,
		"invert_y": _invert_y,
		"interpolation_scale": _interpolation_scale,
		"target_yaw": _target_yaw,
		"target_pitch": _target_pitch,
		"target_roll": _target_roll,
		"current_yaw": _current_yaw,
		"current_pitch": _current_pitch,
		"current_roll": _current_roll,
		"target_focus": _target_focus,
		"current_focus": _current_focus,
		"fit_focus": _fit_focus,
		"target_distance": _target_distance,
		"current_distance": _current_distance,
		"zoom_multiplier": _zoom_multiplier,
		"projection": _camera.projection if _camera != null else -1,
		"orthographic_size": _camera.size if _camera != null else 0.0,
		"horizontal_reflection_active": _horizontal_reflection_active,
		"view_context": _view_context,
		"framing_status": _framing_status,
		"orientation_gizmo_visible": _orientation_gizmo != null and _orientation_gizmo.visible,
	}


func project_world_point(world_point: Vector3) -> Vector2:
	return Vector2.ZERO if _camera == null else _camera.unproject_position(world_point)


func camera_space_point(world_point: Vector3) -> Vector3:
	if _camera == null:
		return Vector3.ZERO
	return _camera.get_camera_transform().affine_inverse() * world_point


func is_world_point_behind(world_point: Vector3) -> bool:
	return true if _camera == null else _camera.is_position_behind(world_point)


static func live_4d_semantic_forward_residual_yaw(local_yaw: float) -> float:
	var quarter_turn := ControlFrameMappingScript.nearest_yaw_quarter_turn(local_yaw)
	var resolved_yaw := float(quarter_turn) * PI * 0.5
	return wrapf(local_yaw - resolved_yaw, -PI, PI)


static func live_4d_semantic_forward_direction(local_yaw: float, local_pitch: float) -> Vector3:
	# The resolver selects pre-L Forward at theta_q = Q(theta) * pi/2. The
	# passive continuous render yaw then leaves only delta = theta - theta_q;
	# pitch acts last about displayed-local Right.
	var residual_yaw := live_4d_semantic_forward_residual_yaw(local_yaw)
	return Basis(Vector3.RIGHT, local_pitch) * Basis(Vector3.UP, residual_yaw) * Vector3.BACK


static func live_4d_semantic_forward_away_depth(local_yaw: float, local_pitch: float) -> float:
	return -_live_4d_fitted_camera_outward().dot(
		live_4d_semantic_forward_direction(local_yaw, local_pitch)
	)


static func live_4d_all_yaw_safe_pitch_domain() -> Vector2:
	# Across nearest-quarter resolution, delta spans [-pi/4, +pi/4]. With the
	# accepted fitted mount, the lower away-depth endpoint is delta=-pi/4, so
	# safety reduces to b*sin(p) + c*cos(p) > a, where a/b/c are derived from
	# the actual camera outward vector below.
	var camera_outward := _live_4d_fitted_camera_outward()
	var residual_horizontal_coefficient := -camera_outward.x
	var vertical_coefficient := camera_outward.y
	var depth_coefficient := -camera_outward.z
	var pitch_magnitude := sqrt(
		vertical_coefficient * vertical_coefficient
		+ depth_coefficient * depth_coefficient
	)
	var safe_domain_center := atan2(vertical_coefficient, depth_coefficient)
	var safe_domain_half_width := acos(
		clampf(residual_horizontal_coefficient / pitch_magnitude, -1.0, 1.0)
	)
	return Vector2(
		safe_domain_center - safe_domain_half_width,
		safe_domain_center + safe_domain_half_width
	)


static func live_4d_worst_case_semantic_forward_away_depth(local_pitch: float) -> float:
	return minf(
		live_4d_semantic_forward_away_depth(-PI * 0.25, local_pitch),
		live_4d_semantic_forward_away_depth(PI * 0.25, local_pitch)
	)


static func _live_4d_fitted_camera_outward() -> Vector3:
	return Vector3(
		sin(LIVE_4D_DISPLAY_YAW_RAD) * cos(LIVE_4D_DISPLAY_PITCH_RAD),
		sin(LIVE_4D_DISPLAY_PITCH_RAD),
		cos(LIVE_4D_DISPLAY_YAW_RAD) * cos(LIVE_4D_DISPLAY_PITCH_RAD)
	)


func _snap_orientation_to_targets() -> void:
	_current_yaw = _target_yaw
	_current_pitch = _target_pitch
	_current_roll = _target_roll
	_update_camera()


func _snap_framing_to_targets() -> void:
	_current_focus = _target_focus
	_current_distance = _target_distance
	_update_camera()


func _mark_manual_view(framing_status: String) -> void:
	_view_context = "free view"
	_framing_status = framing_status


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
	_apply_world_presentation_transform()
	_update_orientation_gizmo()


func _set_horizontal_reflection(active: bool) -> void:
	_horizontal_reflection_active = active
	_apply_world_presentation_transform()
	_update_gizmo_axes()


func _apply_world_presentation_transform() -> void:
	if _world_presentation_root == null:
		return
	if not _horizontal_reflection_active:
		_world_presentation_root.transform = Transform3D.IDENTITY
		return
	if _camera == null:
		return
	# Reflect across the fitted camera's vertical/depth plane. Its normal is
	# effective camera-right, so this reverses rendered screen X without
	# changing camera-space Y or Z.
	var screen_right := _camera.get_camera_transform().basis.x.normalized()
	var reflection_basis := Basis(
		_reflect_direction(Vector3.RIGHT, screen_right),
		_reflect_direction(Vector3.UP, screen_right),
		_reflect_direction(Vector3.BACK, screen_right)
	)
	_world_presentation_root.transform = Transform3D(
		reflection_basis,
		_current_focus - reflection_basis * _current_focus
	)


func _reflect_direction(direction: Vector3, plane_normal: Vector3) -> Vector3:
	return direction - plane_normal * (2.0 * plane_normal.dot(direction))


func _build_orientation_gizmo() -> void:
	_orientation_gizmo = Node3D.new()
	_orientation_gizmo.name = "OrientationGizmo"
	_orientation_gizmo.top_level = true
	_orientation_gizmo.visible = false
	add_child(_orientation_gizmo)

	var center := MeshInstance3D.new()
	center.name = "AxisOrigin"
	var sphere := SphereMesh.new()
	sphere.radius = 0.13
	sphere.height = 0.26
	center.mesh = sphere
	center.material_override = _gizmo_material(Color("d8dde3"))
	_orientation_gizmo.add_child(center)

	_add_gizmo_axis("Horizontal", "+X", Vector3.RIGHT, ReplayVisuals.axis_color("+X"))
	_add_gizmo_axis("Gravity", "+Y", Vector3.DOWN, ReplayVisuals.axis_color("+Y"))
	_add_gizmo_axis("Depth", "+Z", Vector3.BACK, ReplayVisuals.axis_color("+Z"))
	_update_gizmo_axes()


func _add_gizmo_axis(slot: String, label_text: String, direction: Vector3, color: Color) -> void:
	var material := _gizmo_material(color)
	var shaft := MeshInstance3D.new()
	shaft.name = "%sAxis" % slot
	var shaft_mesh := CylinderMesh.new()
	shaft_mesh.top_radius = 0.035
	shaft_mesh.bottom_radius = 0.035
	shaft_mesh.height = 0.58
	shaft.mesh = shaft_mesh
	shaft.material_override = material
	shaft.position = direction * 0.35
	shaft.quaternion = _axis_quaternion(direction)
	_orientation_gizmo.add_child(shaft)

	var arrow := MeshInstance3D.new()
	arrow.name = "%sArrow" % slot
	var arrow_mesh := CylinderMesh.new()
	arrow_mesh.top_radius = 0.0
	arrow_mesh.bottom_radius = 0.10
	arrow_mesh.height = 0.22
	arrow.mesh = arrow_mesh
	arrow.material_override = material
	arrow.position = direction * 0.75
	arrow.quaternion = _axis_quaternion(direction)
	_orientation_gizmo.add_child(arrow)

	var label := Label3D.new()
	label.name = "%sLabel" % slot
	label.text = label_text
	label.font_size = 36
	label.pixel_size = 0.006
	label.modulate = color
	label.outline_modulate = Color("10151b")
	label.outline_size = 8
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.position = direction * 1.02
	_orientation_gizmo.add_child(label)


func _update_gizmo_axes() -> void:
	if _orientation_gizmo == null:
		return
	var visible_axes: Array = _orientation_basis_snapshot.get("visible_axes", ["+X", "+Y", "+Z"])
	var horizontal := str(visible_axes[0]) if visible_axes.size() > 0 else "+X"
	var depth := str(visible_axes[2]) if visible_axes.size() > 2 else "+Z"
	_update_gizmo_axis("Horizontal", horizontal, _presented_direction(_signed_direction(Vector3.RIGHT, horizontal)))
	# +Y is fixed as the gravity/down direction in every valid presentation basis.
	_update_gizmo_axis("Gravity", str(_orientation_basis_snapshot.get("gravity_axis", "+Y")), Vector3.DOWN)
	_update_gizmo_axis("Depth", depth, _presented_direction(_signed_direction(Vector3.BACK, depth)))


func _presented_direction(direction: Vector3) -> Vector3:
	if not _horizontal_reflection_active or _world_presentation_root == null:
		return direction
	return _world_presentation_root.transform.basis * direction


func _update_gizmo_axis(slot: String, label_text: String, direction: Vector3) -> void:
	var shaft := _orientation_gizmo.get_node_or_null("%sAxis" % slot) as MeshInstance3D
	var arrow := _orientation_gizmo.get_node_or_null("%sArrow" % slot) as MeshInstance3D
	var label := _orientation_gizmo.get_node_or_null("%sLabel" % slot) as Label3D
	var color := ReplayVisuals.axis_color(label_text)
	if shaft != null:
		shaft.position = direction * 0.35
		shaft.quaternion = _axis_quaternion(direction)
		shaft.material_override = _gizmo_material(color)
		shaft.set_meta("signed_axis", label_text)
	if arrow != null:
		arrow.position = direction * 0.75
		arrow.quaternion = _axis_quaternion(direction)
		arrow.material_override = _gizmo_material(color)
		arrow.set_meta("signed_axis", label_text)
	if label != null:
		label.text = label_text
		label.modulate = color
		label.position = direction * 1.02
		label.set_meta("signed_axis", label_text)


func _signed_direction(base: Vector3, signed_axis: String) -> Vector3:
	return -base if signed_axis.begins_with("-") else base


func _axis_quaternion(direction: Vector3) -> Quaternion:
	return Quaternion(Vector3.RIGHT, PI) if direction.dot(Vector3.UP) < -0.999 else Quaternion(Vector3.UP, direction)


func _gizmo_material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	material.no_depth_test = true
	return material


func _update_orientation_gizmo() -> void:
	if _orientation_gizmo == null or _camera == null or not _orientation_gizmo.visible:
		return
	var aspect := _viewport_aspect()
	var camera_transform := _camera.get_camera_transform()
	var right := camera_transform.basis.x
	var up := camera_transform.basis.y
	var forward := -camera_transform.basis.z
	_orientation_gizmo.global_position = (
		camera_transform.origin
		+ forward * ORIENTATION_GIZMO_CAMERA_DEPTH
		- right * _camera.size * aspect * ORIENTATION_GIZMO_EDGE_OFFSET
		- up * _camera.size * ORIENTATION_GIZMO_EDGE_OFFSET
	)
	_orientation_gizmo.global_basis = Basis.IDENTITY.scaled(Vector3.ONE * _camera.size * ORIENTATION_GIZMO_SCREEN_SCALE)


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
