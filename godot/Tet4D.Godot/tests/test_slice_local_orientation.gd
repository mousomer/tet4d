extends RefCounted

const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const ProjectionLayoutScript = preload("res://scripts/presentation/projection_layout.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const SliceLocalOrientationScript = preload("res://scripts/presentation/slice_local_orientation.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")

const DISPLAYED_RIGHT := Vector3(1.0, 0.0, 0.0)
const DISPLAYED_FORWARD := Vector3(0.0, 0.0, 1.0)
const DIMENSIONS := [5, 7, 3, 2]
const INTERIOR_POINT := [2, 3, 1, 0]


func run() -> Array:
	var failures: Array = []
	_test_active_passive_yaw(failures)
	_test_continuous_non_quarter_yaw(failures)
	_test_yaw_pitch_and_anchor_isolation(failures)
	_test_identity_yaw_matrix(failures)
	_test_negative_signed_basis_yaw_matrix(failures)
	_test_w_one_and_reslicing(failures)
	_test_renderer_composition_and_oriented_bounds(failures)
	return failures


func _test_active_passive_yaw(failures: Array) -> void:
	var godot_positive_yaw := Basis(Vector3.UP, PI * 0.5)
	_assert_vector(failures, godot_positive_yaw * Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, -1.0), "Godot R(+90) maps +X to -Z")
	_assert_vector(failures, godot_positive_yaw * Vector3(0.0, 0.0, 1.0), DISPLAYED_RIGHT, "Godot R(+90) maps +Z to +X")

	var orientation = SliceLocalOrientationScript.new(PI * 0.5, 0.0)
	_assert_vector(failures, orientation.active_yaw_basis() * DISPLAYED_RIGHT, Vector3(0.0, 0.0, 1.0), "F(+90) expresses Right as pre-L +Z")
	_assert_vector(failures, orientation.active_yaw_basis() * DISPLAYED_FORWARD, Vector3(-1.0, 0.0, 0.0), "F(+90) expresses Forward as pre-L -X")
	_assert_basis(failures, orientation.active_yaw_basis().inverse(), orientation.passive_yaw_basis(), "R must be inverse of F")
	_assert_vector(failures, orientation.passive_yaw_basis() * Vector3(0.0, 0.0, 1.0), DISPLAYED_RIGHT, "R(+90) restores displayed Right")
	_assert_vector(failures, orientation.passive_yaw_basis() * Vector3(-1.0, 0.0, 0.0), DISPLAYED_FORWARD, "R(+90) restores displayed Forward")


func _test_continuous_non_quarter_yaw(failures: Array) -> void:
	var theta := PI / 6.0
	var orientation = SliceLocalOrientationScript.new(theta, 0.0)
	var root_three_over_two := sqrt(3.0) * 0.5
	_assert_vector(
		failures,
		orientation.passive_yaw_basis() * DISPLAYED_FORWARD,
		Vector3(0.5, 0.0, root_three_over_two),
		"R(pi/6) maps +Z continuously"
	)
	_assert_vector(
		failures,
		orientation.passive_yaw_basis() * DISPLAYED_RIGHT,
		Vector3(root_three_over_two, 0.0, -0.5),
		"R(pi/6) maps +X continuously"
	)
	_assert_basis(failures, orientation.active_yaw_basis().inverse(), orientation.passive_yaw_basis(), "F(pi/6)^-1 equals R(pi/6)")


func _test_yaw_pitch_and_anchor_isolation(failures: Array) -> void:
	var orientation = SliceLocalOrientationScript.new(PI * 0.5, 0.0)
	# Pre-L -X becomes displayed +Z at +90 yaw, so pitch must tilt it while
	# remaining absent from the yaw-only command projection.
	var pre_l_forward := Vector3(-1.0, 0.0, 0.0)
	var yaw_only := orientation.passive_render_basis() * pre_l_forward
	orientation.local_pitch = PI / 6.0
	var pitched := orientation.passive_render_basis() * pre_l_forward
	if pitched.distance_to(yaw_only) <= 0.001:
		failures.append("local pitch must be independently represented in L")
	if not is_equal_approx(orientation.local_yaw, PI * 0.5):
		failures.append("changing local pitch must not change local yaw")

	var basis = SliceBasis4DScript.from_slots([-3, 2, 1, 4])
	var projection = ProjectionLayoutScript.new()
	projection.configure({"dimension": 4, "board_shape": DIMENSIONS}, basis, orientation)
	var basis_before: Array = basis.slots()
	var anchors_before: Array = [projection.slice_anchor(0), projection.slice_anchor(1)]
	orientation.set_angles(-PI * 0.5, -PI / 8.0)
	var anchors_after: Array = [projection.slice_anchor(0), projection.slice_anchor(1)]
	if anchors_after != anchors_before:
		failures.append("changing shared L must not move slice anchors")
	if basis.slots() != basis_before:
		failures.append("changing shared L must not mutate exact B")
	var local_point := Vector3(0.5, 1.0, -0.5)
	var oriented: Vector3 = projection.oriented_local_point(local_point)
	for layer_index in [0, 1]:
		var anchor: Vector3 = projection.slice_anchor(layer_index)
		_assert_vector(failures, oriented + anchor - anchor, oriented, "L is uniform for slice %d" % layer_index)


func _test_identity_yaw_matrix(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	var cases := [
		{"yaw": 0.0, "right": "move_x_pos", "forward": "move_z_pos", "label": "0"},
		{"yaw": PI * 0.5, "right": "move_z_pos", "forward": "move_x_neg", "label": "+90"},
		{"yaw": PI, "right": "move_x_neg", "forward": "move_z_neg", "label": "180"},
		{"yaw": -PI * 0.5, "right": "move_z_neg", "forward": "move_x_pos", "label": "-90"},
	]
	_assert_yaw_matrix(failures, identity, cases, "identity B")


func _test_negative_signed_basis_yaw_matrix(failures: Array) -> void:
	# Accepted adversarial B = [-Z,+Y,+X,+W]. These expected canonical commands
	# are independent constants, not derived from the implementation under test.
	var signed_basis = SliceBasis4DScript.from_slots([-3, 2, 1, 4])
	var cases := [
		{"yaw": 0.0, "right": "move_z_neg", "forward": "move_x_pos", "label": "0"},
		{"yaw": PI * 0.5, "right": "move_x_pos", "forward": "move_z_pos", "label": "+90"},
		{"yaw": PI, "right": "move_z_pos", "forward": "move_x_neg", "label": "180"},
		{"yaw": -PI * 0.5, "right": "move_x_neg", "forward": "move_z_neg", "label": "-90"},
	]
	_assert_yaw_matrix(failures, signed_basis, cases, "negative signed B")


func _assert_yaw_matrix(failures: Array, basis, cases: Array, basis_label: String) -> void:
	var mapper = TraceCoordinateMapperScript.new()
	mapper.configure(DIMENSIONS, basis)
	# These cases sample continuous R(theta) at theta_q = q*pi/2 selected by
	# Q(q), where visual and discrete command frames coincide exactly.
	for yaw_case in cases:
		var yaw := float(yaw_case["yaw"])
		var label := "%s yaw %s" % [basis_label, str(yaw_case["label"])]
		var resolver = ControlFrameMappingScript.for_4d(basis, yaw)
		var right_command: String = resolver.translation_command("move_x_pos", "relative")
		var forward_command: String = resolver.translation_command("move_z_neg", "relative")
		_assert_equal(failures, right_command, str(yaw_case["right"]), "%s Right canonical command" % label)
		_assert_equal(failures, forward_command, str(yaw_case["forward"]), "%s Forward canonical command" % label)
		var orientation = SliceLocalOrientationScript.new(yaw, 0.0)
		_assert_point_difference(failures, mapper, orientation, INTERIOR_POINT, right_command, DISPLAYED_RIGHT, "%s displayed Right" % label)
		_assert_point_difference(failures, mapper, orientation, INTERIOR_POINT, forward_command, DISPLAYED_FORWARD, "%s displayed Forward" % label)


func _assert_point_difference(
	failures: Array,
	mapper,
	orientation,
	origin: Array,
	command: String,
	expected_displayed: Vector3,
	label: String
) -> void:
	var delta: Array = _canonical_delta(command)
	if delta.is_empty():
		failures.append("%s: unsupported canonical command %s" % [label, command])
		return
	var destination := origin.duplicate()
	for axis in range(4):
		destination[axis] = int(destination[axis]) + int(delta[axis])
	var mapped_origin: Dictionary = mapper.presentation_coordinate(origin)
	var mapped_destination: Dictionary = mapper.presentation_coordinate(destination)
	if not bool(mapped_origin.get("ok", false)) or not bool(mapped_destination.get("ok", false)):
		failures.append("%s: point pair must remain valid" % label)
		return
	if int(mapped_origin["layer_index"]) != int(mapped_destination["layer_index"]):
		failures.append("%s: point pair must remain in one slice" % label)
		return
	var origin_point: Vector3 = mapper.centered_local_point(mapped_origin["visible_cell_3d"])
	var destination_point: Vector3 = mapper.centered_local_point(mapped_destination["visible_cell_3d"])
	var pre_l_difference: Vector3 = destination_point - origin_point
	var displayed_difference: Vector3 = orientation.passive_yaw_basis() * pre_l_difference
	_assert_vector(failures, displayed_difference, expected_displayed, label)


func _test_w_one_and_reslicing(failures: Array) -> void:
	var dimensions := [5, 7, 3, 1]
	var identity = SliceBasis4DScript.identity()
	var orientation = SliceLocalOrientationScript.new(PI * 0.5, 0.0)
	var projection = ProjectionLayoutScript.new()
	projection.configure({"dimension": 4, "board_shape": dimensions}, identity, orientation)
	if projection.mapper.current_layer_count() != 1 or projection.slice_anchor(0) != Vector3.ZERO:
		failures.append("W=1 identity basis must use exactly anchor_0")
	var decomposition: Dictionary = projection.decompose_position([3, 3, 1, 0])
	_assert_vector(failures, decomposition.get("centered_local_point", Vector3.ZERO), DISPLAYED_RIGHT, "W=1 retains centred local volume")
	_assert_vector(failures, projection.oriented_local_point(decomposition.get("centered_local_point", Vector3.ZERO)), Vector3(0.0, 0.0, -1.0), "W=1 L still orients the local volume")

	projection.mapper.configure(dimensions, identity.turned("xw", 1))
	if projection.mapper.current_layer_count() != 5 or projection.mapper.visible_board_shape() != [1, 7, 3]:
		failures.append("W=1 XW turn must make X the extent-aware slice axis")
	projection.mapper.configure(dimensions, identity.turned("zw", 1))
	if projection.mapper.current_layer_count() != 3 or projection.mapper.visible_board_shape() != [5, 7, 1]:
		failures.append("W=1 ZW turn must make Z the extent-aware slice axis")


# Requirement/invariant coverage for Stage 54E-2b composition, transformed
# corner AABBs, signed B, continuous yaw, pitch, and uniform multi-slice L.
func _test_renderer_composition_and_oriented_bounds(failures: Array) -> void:
	var signed_basis = SliceBasis4DScript.from_slots([-3, 2, 1, 4])
	var orientation = SliceLocalOrientationScript.new(PI / 6.0, PI / 8.0)
	var projection = ProjectionLayoutScript.new()
	projection.configure({"dimension": 4, "board_shape": DIMENSIONS}, signed_basis, orientation)
	if projection.oriented_world_position([]) != Vector3.ZERO:
		failures.append("invalid renderer mapping must fail safely to the neutral position")
	var canonical_point := [1, 2, 2, 1]
	var decomposition: Dictionary = projection.decompose_position(canonical_point)
	if not bool(decomposition.get("ok", false)):
		failures.append("signed-B renderer point must decompose before L")
		return
	var local_point: Vector3 = decomposition.get("centered_local_point", Vector3.ZERO)
	var anchor: Vector3 = decomposition.get("anchor", Vector3.ZERO)
	var rendered := projection.oriented_world_position(canonical_point)
	_assert_vector(
		failures,
		rendered,
		orientation.orient_local_point(local_point) + anchor,
		"renderer composition is L(G_D(p)) plus anchor"
	)
	if rendered.distance_to(orientation.orient_local_point(local_point + anchor)) <= 0.001:
		failures.append("renderer composition must not rotate the slice anchor")

	var local_delta := Vector3(1.0, 0.0, 0.0)
	var expected_delta := orientation.orient_local_point(local_delta)
	for layer_index in [0, 1]:
		var origin := [1, 2, 2, layer_index]
		var destination := [1, 2, 1, layer_index]
		var actual_delta := projection.oriented_world_position(destination) - projection.oriented_world_position(origin)
		_assert_vector(failures, actual_delta, expected_delta, "shared L rendered delta in slice %d" % layer_index)

	var local_bounds: Dictionary = projection.local_slice_bounds()
	var min_local: Vector3 = local_bounds.get("min", Vector3.ZERO)
	var max_local: Vector3 = local_bounds.get("max", Vector3.ZERO)
	var collection_bounds: Dictionary = projection.bounds
	for layer_index in [0, 1]:
		var slice_anchor: Vector3 = projection.slice_anchor(layer_index)
		for x in [min_local.x, max_local.x]:
			for y in [min_local.y, max_local.y]:
				for z in [min_local.z, max_local.z]:
					var corner := orientation.orient_local_point(Vector3(x, y, z)) + slice_anchor
					_assert_point_in_bounds(failures, corner, collection_bounds, "oriented corner layer %d" % layer_index)

	var identity_projection = ProjectionLayoutScript.new()
	identity_projection.configure(
		{"dimension": 4, "board_shape": DIMENSIONS},
		signed_basis,
		SliceLocalOrientationScript.new()
	)
	var identity_size: Vector3 = identity_projection.bounds.get("max", Vector3.ZERO) - identity_projection.bounds.get("min", Vector3.ZERO)
	var oriented_size: Vector3 = collection_bounds.get("max", Vector3.ZERO) - collection_bounds.get("min", Vector3.ZERO)
	if identity_size.distance_to(oriented_size) <= 0.001:
		failures.append("asymmetric non-quarter yaw/pitch must change the oriented collection AABB")


func _assert_point_in_bounds(failures: Array, point: Vector3, bounds: Dictionary, label: String) -> void:
	var min_point: Vector3 = bounds.get("min", Vector3.ZERO)
	var max_point: Vector3 = bounds.get("max", Vector3.ZERO)
	var tolerance := 0.001
	if (
		point.x < min_point.x - tolerance
		or point.y < min_point.y - tolerance
		or point.z < min_point.z - tolerance
		or point.x > max_point.x + tolerance
		or point.y > max_point.y + tolerance
		or point.z > max_point.z + tolerance
	):
		failures.append("%s must lie inside oriented bounds: %s not in %s..%s" % [label, point, min_point, max_point])


func _canonical_delta(command: String) -> Array:
	match command:
		"move_x_neg": return [-1, 0, 0, 0]
		"move_x_pos": return [1, 0, 0, 0]
		"move_z_neg": return [0, 0, -1, 0]
		"move_z_pos": return [0, 0, 1, 0]
		_: return []


func _assert_basis(failures: Array, actual: Basis, expected: Basis, label: String) -> void:
	_assert_vector(failures, actual.x, expected.x, "%s X" % label)
	_assert_vector(failures, actual.y, expected.y, "%s Y" % label)
	_assert_vector(failures, actual.z, expected.z, "%s Z" % label)


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
