extends SceneTree


func _initialize() -> void:
	var failures: Array = []
	for script_path in [
		"res://tests/test_bundle_loader.gd",
		"res://tests/test_trace_snapshot_extractor.gd",
	]:
		var test_case = load(script_path).new()
		failures.append_array(test_case.run())
	if failures.is_empty():
		print("Godot replay tests passed.")
		quit(0)
		return
	for failure in failures:
		push_error(str(failure))
		print(str(failure))
	quit(1)
