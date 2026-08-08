extends RefCounted

const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")


func run() -> Array:
	var failures: Array = []
	_test_identity_and_yaw(failures)
	_test_signed_slice_bases(failures)
	_test_rotation_canonicalization(failures)
	_test_absolute_compatibility(failures)
	return failures


func _test_identity_and_yaw(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	var mapping = ControlFrameMappingScript.for_4d(identity, 0.0)
	_assert_equal(failures, mapping.translation_command("move_x_pos", "relative"), "move_x_pos", "identity right")
	_assert_equal(failures, mapping.translation_command("move_z_neg", "relative"), "move_z_pos", "identity forward is canonical +Z")
	_assert_equal(failures, mapping.translation_command("move_w_neg", "relative"), "move_w_neg", "identity slice")
	var yaw_180 = ControlFrameMappingScript.for_3d(PI)
	_assert_equal(failures, yaw_180.translation_command("move_z_neg", "relative"), "move_z_neg", "180 degree forward")
	_assert_equal(failures, yaw_180.translation_command("move_x_pos", "relative"), "move_x_neg", "180 degree right")
	_assert_equal(failures, ControlFrameMappingScript.nearest_yaw_quarter_turn(PI * 0.25 - 0.001), 0, "yaw below 45 degrees")
	_assert_equal(failures, ControlFrameMappingScript.nearest_yaw_quarter_turn(PI * 0.25 + 0.001), 1, "yaw above 45 degrees")


func _test_signed_slice_bases(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	var xw = ControlFrameMappingScript.for_4d(identity.turned("xw", 1), 0.0)
	_assert_equal(failures, xw.translation_command("move_x_pos", "relative"), "move_w_pos", "XW+ horizontal")
	_assert_equal(failures, xw.translation_command("move_w_pos", "relative"), "move_x_neg", "XW+ signed slice")
	var zw = ControlFrameMappingScript.for_4d(identity.turned("zw", 1), 0.0)
	_assert_equal(failures, zw.translation_command("move_z_neg", "relative"), "move_w_pos", "ZW+ forward")
	_assert_equal(failures, zw.translation_command("move_w_pos", "relative"), "move_z_neg", "ZW+ signed slice")
	var zx = ControlFrameMappingScript.for_4d(identity.turned("zx", 1), 0.0)
	_assert_equal(failures, zx.translation_command("move_x_pos", "relative"), "move_z_neg", "ZX+ right")
	_assert_equal(failures, zx.translation_command("move_z_neg", "relative"), "move_x_pos", "ZX+ forward")


func _test_rotation_canonicalization(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	var mapping = ControlFrameMappingScript.for_4d(identity.turned("zx", 1), 0.0)
	_assert_equal(failures, mapping.rotation_command("rotate_xy_pos", "relative"), "rotate_yz_pos", "signed ZX local XY rotation")
	for action in ["rotate_xy_neg", "rotate_xy_pos", "rotate_xz_neg", "rotate_xz_pos", "rotate_yz_neg", "rotate_yz_pos", "rotate_xw_neg", "rotate_xw_pos", "rotate_yw_neg", "rotate_yw_pos", "rotate_zw_neg", "rotate_zw_pos"]:
		var resolved: String = mapping.rotation_command(action, "relative")
		if not resolved in ["rotate_xy_neg", "rotate_xy_pos", "rotate_xz_neg", "rotate_xz_pos", "rotate_yz_neg", "rotate_yz_pos", "rotate_xw_neg", "rotate_xw_pos", "rotate_yw_neg", "rotate_yw_pos", "rotate_zw_neg", "rotate_zw_pos"]:
			failures.append("relative rotation must resolve to a canonical native command: %s -> %s" % [action, resolved])


func _test_absolute_compatibility(failures: Array) -> void:
	var mapping = ControlFrameMappingScript.for_4d(SliceBasis4DScript.identity().turned("xw", -1), PI)
	for action in ["move_x_neg", "move_x_pos", "move_z_neg", "move_z_pos", "move_w_neg", "move_w_pos"]:
		_assert_equal(failures, mapping.translation_command(action, "absolute"), action, "absolute translation %s" % action)
	for action in ["rotate_xy_neg", "rotate_xy_pos", "rotate_xw_neg", "rotate_xw_pos", "rotate_zw_neg", "rotate_zw_pos"]:
		_assert_equal(failures, mapping.rotation_command(action, "absolute"), action, "absolute rotation %s" % action)


func _assert_equal(failures: Array, actual, expected, label: String) -> void:
	if actual != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
