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

	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.0, -2.5, -1.5), "max": Vector3(8.0, 2.5, 1.5)},
		1.2,
		CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD,
		CameraRigScript.LIVE_3D_VIEW_PRESET_NAME,
		"above exterior"
	)
	_assert_float(failures, rig._current_yaw, CameraRigScript.LIVE_3D_DISPLAY_YAW_RAD, "live 3D fit uses canonical yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.LIVE_3D_DISPLAY_PITCH_RAD, "live 3D fit uses above-board pitch")
	if rig._current_pitch <= 0.0:
		failures.append("live 3D canonical pitch should be above the board, got %.4f" % rig._current_pitch)
	if camera.global_position.y <= rig._current_focus.y:
		failures.append("live 3D camera should sit above the fit focus")
	var status := rig.view_status_text()
	if status.find(CameraRigScript.LIVE_3D_VIEW_PRESET_NAME) == -1:
		failures.append("live 3D camera status should name the canonical preset")
	if status.find("above") == -1 or status.find("fit OK") == -1 or status.find("ortho") == -1:
		failures.append("live 3D camera status should show orthographic above-board fit state: %s" % status)

	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)},
		1.34,
		CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
		CameraRigScript.LIVE_4D_VIEW_PRESET_NAME,
		"fitted W slices"
	)
	_assert_float(failures, rig._current_yaw, CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD, "live 4D fit uses W-slice yaw")
	_assert_float(failures, rig._current_pitch, CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD, "live 4D fit uses W-slice pitch")
	if camera.size <= 20.0:
		failures.append("live 4D camera fit should frame the full W-slice layout, got size %.3f" % camera.size)
	status = rig.view_status_text()
	if status.find(CameraRigScript.LIVE_4D_VIEW_PRESET_NAME) == -1 or status.find("fitted W slices") == -1:
		failures.append("live 4D camera status should name the fitted W-slice preset: %s" % status)
	var yaw_before := rig._current_yaw
	rig.nudge_yaw(CameraRigScript.LIVE_4D_CAMERA_YAW_STEP_RAD)
	if rig._current_yaw <= yaw_before:
		failures.append("live 4D camera yaw nudge should adjust the view")
	if rig.view_status_text().find("manual") == -1:
		failures.append("live 4D camera nudge should mark the view as manual")
	rig.fit_bounds(
		{"ok": true, "min": Vector3(-2.5, -5.0, -2.0), "max": Vector3(23.5, 6.72, 2.0)},
		1.34,
		CameraRigScript.LIVE_4D_DISPLAY_YAW_RAD,
		CameraRigScript.LIVE_4D_DISPLAY_PITCH_RAD,
		CameraRigScript.LIVE_4D_VIEW_PRESET_NAME,
		"fitted W slices"
	)
	if rig.view_status_text().find("fit OK") == -1:
		failures.append("live 4D Fit View should restore fitted state")

	rig.queue_free()
	await tree.process_frame
	return failures


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])


func _assert_float(failures: Array, actual: float, expected: float, label: String) -> void:
	if absf(actual - expected) > 0.001:
		failures.append("%s: expected %.4f, got %.4f" % [label, expected, actual])
