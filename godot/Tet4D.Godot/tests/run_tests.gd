extends SceneTree


func _initialize() -> void:
	call_deferred("_run_all")


func _run_all() -> void:
	var failures: Array = []
	for script_path in [
		"res://tests/test_bundle_loader.gd",
		"res://tests/test_trace_snapshot_extractor.gd",
		"res://tests/test_replay_visuals.gd",
		"res://tests/test_coordinate_mapper.gd",
		"res://tests/test_scene_integrity.gd",
		"res://tests/test_replay_viewer_layout.gd",
		"res://tests/test_particle_renderer.gd",
	]:
		var test_case = load(script_path).new()
		if script_path == "res://tests/test_replay_viewer_layout.gd":
			failures.append_array(await test_case.run())
		else:
			failures.append_array(test_case.run())
	if failures.is_empty():
		print("Godot replay tests passed.")
		quit(0)
		return
	for failure in failures:
		push_error(str(failure))
		print(str(failure))
	quit(1)
