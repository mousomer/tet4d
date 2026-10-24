extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var test = load("res://tests/test_live_relative_translation.gd").new()
	var failures: Array = await test.run()
	if not test.completed:
		failures.append("Live relative translation test aborted before completion")
	for failure in failures:
		printerr(failure)
	if failures.is_empty():
		print("Live relative translation focused runner passed (3D + 4D).")
	quit(0 if failures.is_empty() else 1)
