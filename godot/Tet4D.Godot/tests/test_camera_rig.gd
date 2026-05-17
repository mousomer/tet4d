extends RefCounted

const CameraRigScript = preload("res://scripts/rendering/camera_rig.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["camera rig test requires SceneTree"]
	var rig := CameraRigScript.new()
	var camera := Camera3D.new()
	camera.name = "Camera3D"
	rig.add_child(camera)
	tree.root.add_child(rig)
	await tree.process_frame

	rig.fit_bounds({"ok": true, "min": Vector3(-2.0, -2.5, -1.5), "max": Vector3(8.0, 2.5, 1.5)}, 1.14)
	_assert_vector(failures, rig._current_focus, Vector3(3.0, 0.0, 0.0), "fit snaps current focus")
	_assert_float(failures, rig._current_yaw, CameraRigScript.PYTHON_DISPLAY_YAW_RAD, "fit uses Python display yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.PYTHON_DISPLAY_PITCH_RAD, "fit uses Python display pitch")
	if camera.projection != Camera3D.PROJECTION_ORTHOGONAL:
		failures.append("camera should use orthographic projection")
	if camera.size <= 5.0 or camera.size >= 10.5:
		failures.append("camera fit should use projected bounds with margin, got size %.3f" % camera.size)

	rig.queue_free()
	await tree.process_frame
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_float(failures: Array, actual: float, expected: float, label: String) -> void:
	if absf(actual - expected) > 0.001:
		failures.append("%s: expected %.4f, got %.4f" % [label, expected, actual])
