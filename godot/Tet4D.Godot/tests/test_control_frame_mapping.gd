extends RefCounted

const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")


func run() -> Array:
	var failures: Array = []
	_test_2d_relative_screen_mapping(failures)
	_test_3d_relative_view_mapping(failures)
	_test_identity_and_yaw(failures)
	_test_signed_slice_bases(failures)
	_test_rotation_canonicalization(failures)
	_test_absolute_compatibility(failures)
	return failures


func _test_2d_relative_screen_mapping(failures: Array) -> void:
	var cases := [
		{"yaw": 0.0, "right": "move_right", "half": 0},
		{"yaw": PI * 0.5, "right": "move_right", "half": 0},
		{"yaw": PI * 0.5 + 0.001, "right": "move_left", "half": 1},
		{"yaw": PI, "right": "move_left", "half": 1},
		{"yaw": -PI * 0.5, "right": "move_right", "half": 0},
		{"yaw": -PI * 0.5 - 0.001, "right": "move_left", "half": 1},
	]
	for test_case in cases:
		var mapping = ControlFrameMappingScript.for_2d(float(test_case["yaw"]))
		var right: String = mapping.translation_command("move_right", "relative")
		var left: String = mapping.translation_command("move_left", "relative")
		_assert_equal(failures, right, test_case["right"], "2D relative Right yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, left, "move_left" if right == "move_right" else "move_right", "2D relative inverse yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, mapping.yaw_half_turn, test_case["half"], "2D half turn yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, mapping.translation_command("move_right", "absolute"), "move_right", "2D absolute Right yaw %.3f" % float(test_case["yaw"]))
		var effective: Dictionary = mapping.effective_translation_snapshot("relative")
		_assert_equal(failures, effective.get("horizontal_axis"), "+X" if right == "move_right" else "-X", "2D effective guidance yaw %.3f" % float(test_case["yaw"]))


func _test_3d_relative_view_mapping(failures: Array) -> void:
	var cases := [
		{"yaw": 0.0, "right": "move_x_pos", "forward": "move_z_neg"},
		{"yaw": PI * 0.5, "right": "move_z_neg", "forward": "move_x_neg"},
		{"yaw": PI, "right": "move_x_neg", "forward": "move_z_pos"},
		{"yaw": -PI * 0.5, "right": "move_z_pos", "forward": "move_x_pos"},
	]
	for test_case in cases:
		var mapping = ControlFrameMappingScript.for_3d(float(test_case["yaw"]))
		_assert_equal(failures, mapping.translation_command("move_x_pos", "relative"), test_case["right"], "3D relative Right yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, mapping.translation_command("move_z_neg", "relative"), test_case["forward"], "3D relative Forward yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, mapping.translation_command("move_x_neg", "relative"), _opposite_command(str(test_case["right"])), "3D relative Left inverse yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, mapping.translation_command("move_z_pos", "relative"), _opposite_command(str(test_case["forward"])), "3D relative Back inverse yaw %.3f" % float(test_case["yaw"]))
		var effective: Dictionary = mapping.effective_translation_snapshot("relative")
		_assert_equal(failures, effective.get("horizontal_axis"), ControlFrameMappingScript._command_axis_label(str(test_case["right"])), "3D effective Right guidance yaw %.3f" % float(test_case["yaw"]))
		_assert_equal(failures, effective.get("depth_axis"), ControlFrameMappingScript._command_axis_label(str(test_case["forward"])), "3D effective Forward guidance yaw %.3f" % float(test_case["yaw"]))
	for boundary in [PI * 0.25, PI * 0.75, PI * 1.25, PI * 1.75]:
		var at_boundary := ControlFrameMappingScript.nearest_yaw_quarter_turn(boundary)
		var below := ControlFrameMappingScript.nearest_yaw_quarter_turn(boundary - 0.001)
		var above := ControlFrameMappingScript.nearest_yaw_quarter_turn(boundary + 0.001)
		if below == above or at_boundary not in [below, above]:
			failures.append("3D quarter-turn boundary %.3f must be deterministic and separate adjacent frames" % boundary)


func _test_identity_and_yaw(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	var mapping = ControlFrameMappingScript.for_4d(identity, 0.0)
	_assert_equal(failures, mapping.translation_command("move_x_pos", "relative"), "move_x_pos", "identity right")
	_assert_equal(failures, mapping.translation_command("move_z_neg", "relative"), "move_z_pos", "identity forward is canonical +Z")
	_assert_equal(failures, mapping.translation_command("move_w_neg", "relative"), "move_w_neg", "identity slice")
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


func _opposite_command(command: String) -> String:
	return command.trim_suffix("_neg") + "_pos" if command.ends_with("_neg") else command.trim_suffix("_pos") + "_neg"
