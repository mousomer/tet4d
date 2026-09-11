extends RefCounted

const ControlFrameMappingScript = preload("res://scripts/presentation/control_frame_mapping.gd")


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		return ["Stage 56A rosette test requires the trace replay scene"]
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return ["Stage 56A rosette test requires SceneTree"]
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		root.queue_free()
		await tree.process_frame
		return ["Stage 56A rosette test requires the live app"]

	app._enter_live_4d_mode()
	await tree.process_frame
	var native_snapshot: String = app._live_bridge.live_4d_snapshot_json()
	var native_hash: String = str(app._live_bridge.live_4d_state_hash())
	_assert_live_4d_state(failures, app, "initial")

	for basis_case in [
		{"plane": "xz", "label": "XZ exact turn"},
		{"plane": "xw", "label": "XW exact turn / re-slice"},
		{"plane": "zw", "label": "ZW exact turn / re-slice"},
	]:
		app._reset_view()
		app._apply_live_4d_basis_turn(str(basis_case["plane"]), 1)
		_assert_live_4d_state(failures, app, str(basis_case["label"]))
		_assert_native_unchanged(failures, app, native_snapshot, native_hash, str(basis_case["label"]))

	app._reset_view()
	app._set_live_4d_local_orientation(0.31, 0.0)
	_assert_live_4d_state(failures, app, "yaw")
	_assert_native_unchanged(failures, app, native_snapshot, native_hash, "yaw")

	app._set_live_4d_local_orientation(0.31, 0.22)
	_assert_live_4d_state(failures, app, "pitch")
	_assert_native_unchanged(failures, app, native_snapshot, native_hash, "pitch")

	var basis_before_draw: Array = app._live_4d_basis.slots()
	var local_before_draw: Dictionary = app._live_4d_local_orientation.snapshot()
	app._camera_rig._update_gizmo_axes()
	app._camera_rig._update_orientation_gizmo()
	if app._live_4d_basis.slots() != basis_before_draw or app._live_4d_local_orientation.snapshot() != local_before_draw:
		failures.append("drawing the rosette must not mutate authoritative presentation state")
	_assert_native_unchanged(failures, app, native_snapshot, native_hash, "rosette draw")

	app._reset_view()
	_assert_live_4d_state(failures, app, "Reset View")
	if not app._live_4d_basis.is_identity() or app._live_4d_local_orientation.snapshot() != {"local_yaw": 0.0, "local_pitch": 0.0}:
		failures.append("Reset View must restore both authoritative and rosette orientation state")
	_assert_native_unchanged(failures, app, native_snapshot, native_hash, "Reset View")

	app._enter_live_3d_mode()
	await tree.process_frame
	var three_d_snapshot: Dictionary = app._camera_rig.orientation_indicator_snapshot()
	if str(three_d_snapshot.get("source", "")) != "camera":
		failures.append("Live 3D rosette must remain on its existing camera-driven path")
	if three_d_snapshot.get("local_orientation", {}) != {"local_yaw": 0.0, "local_pitch": 0.0}:
		failures.append("Live 3D must not inherit Live-4D slice-local orientation")
	var expected_3d = ControlFrameMappingScript.for_3d(app._camera_rig.control_frame_yaw())
	var expected_3d_snapshot: Dictionary = expected_3d.effective_translation_snapshot(app._translation_frame)
	var actual_3d_frame: Dictionary = three_d_snapshot.get("control_frame", {})
	if str(actual_3d_frame.get("horizontal_axis", "")) != str(expected_3d_snapshot.get("horizontal_axis", "")) or str(actual_3d_frame.get("depth_axis", "")) != str(expected_3d_snapshot.get("depth_axis", "")):
		failures.append("Live 3D rosette labels must retain the camera-yaw control-frame mapping")

	root.queue_free()
	await tree.process_frame
	return failures


func _assert_live_4d_state(failures: Array, app, label: String) -> void:
	var actual: Dictionary = app._camera_rig.orientation_indicator_snapshot()
	var control_frame: Dictionary = app._control_frame_mapping(4).effective_translation_snapshot(app._translation_frame)
	control_frame["rotation_frame"] = app._rotation_frame
	if str(actual.get("source", "")) != "live_4d_presentation":
		failures.append("%s rosette must identify the authoritative Live-4D presentation source" % label)
	if str(actual.get("basis_key", "")) != app._live_4d_basis.key() or actual.get("basis_slots", []) != app._live_4d_basis.slots():
		failures.append("%s rosette exact basis must equal authoritative B" % label)
	if actual.get("local_orientation", {}) != app._live_4d_local_orientation.snapshot():
		failures.append("%s rosette local orientation must equal authoritative L" % label)
	if actual.get("control_frame", {}) != control_frame:
		failures.append("%s rosette control labels must equal the resolved presentation frame" % label)
	var reflection := Basis.IDENTITY
	if app._live_4d_presentation_root != null:
		reflection = app._live_4d_presentation_root.transform.basis
	var render_basis: Basis = app._live_4d_local_orientation.passive_render_basis()
	var axes: Dictionary = actual.get("axes", {})
	_assert_axis(
		failures,
		axes.get("horizontal", {}),
		str(control_frame.get("horizontal_axis", "")),
		reflection * render_basis * _pre_local_direction(app._live_4d_basis, str(control_frame.get("horizontal_axis", ""))),
		"%s horizontal" % label
	)
	_assert_axis(
		failures,
		axes.get("gravity", {}),
		"+Y",
		reflection * render_basis * Vector3.DOWN,
		"%s gravity" % label
	)
	_assert_axis(
		failures,
		axes.get("depth", {}),
		str(control_frame.get("depth_axis", "")),
		reflection * render_basis * _pre_local_direction(app._live_4d_basis, str(control_frame.get("depth_axis", ""))),
		"%s depth" % label
	)


func _assert_axis(failures: Array, actual: Dictionary, signed_axis: String, direction: Vector3, label: String) -> void:
	if str(actual.get("signed_axis", "")) != signed_axis:
		failures.append("%s label must equal %s" % [label, signed_axis])
	var actual_direction: Vector3 = actual.get("presented_direction", Vector3.ZERO)
	if actual_direction.distance_to(direction) > 0.0001:
		failures.append("%s direction must equal authoritative rendered axis" % label)


func _pre_local_direction(basis, signed_axis: String) -> Vector3:
	var visible_axes: Array = basis.indicator_snapshot().get("visible_axes", [])
	var horizontal := str(visible_axes[0])
	var depth := str(visible_axes[2])
	if signed_axis == horizontal:
		return Vector3.RIGHT
	if signed_axis == _opposite(horizontal):
		return Vector3.LEFT
	if signed_axis == depth:
		return Vector3.BACK
	if signed_axis == _opposite(depth):
		return Vector3.FORWARD
	return Vector3.ZERO


func _opposite(signed_axis: String) -> String:
	return ("-" if signed_axis.begins_with("+") else "+") + signed_axis.substr(1)


func _assert_native_unchanged(failures: Array, app, snapshot: String, state_hash: String, label: String) -> void:
	if app._live_bridge.live_4d_snapshot_json() != snapshot or str(app._live_bridge.live_4d_state_hash()) != state_hash:
		failures.append("%s must not mutate Live-4D gameplay state" % label)
