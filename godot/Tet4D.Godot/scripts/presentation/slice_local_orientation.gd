extends RefCounted

class_name SliceLocalOrientation

# The actual fitted-view semantic-Forward proof includes the residual yaw
# between continuous L.local_yaw and its nearest-quarter resolver frame. Its
# strict all-yaw pitch interval is approximately (-42.480, +86.240) degrees.
# The asymmetric product range retains Top at +60 degrees and selects a round
# -40-degree lower limit, leaving 2.480 degrees (and positive normalized away
# depth) before the worst-case inversion boundary. Explorer/free-inspection
# code may continue to use the unconstrained set_angles() primitive.
const NORMAL_GAMEPLAY_MIN_PITCH_RAD := -PI * 2.0 / 9.0  # -40 degrees.
const NORMAL_GAMEPLAY_MAX_PITCH_RAD := PI / 3.0  # +60 degrees.

# Shared, presentation-only orientation for the centred contents of every 4D
# slice. This state is deliberately independent of exact SliceBasis4D state,
# layout anchors, CameraRig framing, and deterministic gameplay identity.
var local_yaw := 0.0
var local_pitch := 0.0


func _init(yaw_radians: float = 0.0, pitch_radians: float = 0.0) -> void:
	local_yaw = yaw_radians
	local_pitch = pitch_radians


func set_angles(yaw_radians: float, pitch_radians: float) -> void:
	local_yaw = yaw_radians
	local_pitch = pitch_radians


func set_normal_gameplay_angles(yaw_radians: float, pitch_radians: float) -> void:
	local_yaw = wrapf(yaw_radians, -PI, PI)
	local_pitch = clampf(
		pitch_radians,
		NORMAL_GAMEPLAY_MIN_PITCH_RAD,
		NORMAL_GAMEPLAY_MAX_PITCH_RAD
	)


func active_yaw_basis() -> Basis:
	# F(theta): continuous active orientation of the semantic displayed local
	# frame, expressed in pre-L coordinates.
	return Basis(Vector3.UP, -local_yaw)


func passive_yaw_basis() -> Basis:
	# R(theta) = F(theta)^-1: continuous passive transform from pre-L
	# coordinates into the fixed displayed local board frame.
	return Basis(Vector3.UP, local_yaw)


func pitch_basis() -> Basis:
	# Pitch is a visual tilt about displayed local Right. It remains separate
	# from the yaw-only command frame.
	return Basis(Vector3.RIGHT, local_pitch)


func passive_render_basis() -> Basis:
	# Coordinates are first transformed by passive yaw, then tilted about the
	# already selected displayed-local horizontal axis.
	return pitch_basis() * passive_yaw_basis()


func orient_local_point(centered_local_point: Vector3) -> Vector3:
	return passive_render_basis() * centered_local_point


func snapshot() -> Dictionary:
	return {
		"local_yaw": local_yaw,
		"local_pitch": local_pitch,
	}
