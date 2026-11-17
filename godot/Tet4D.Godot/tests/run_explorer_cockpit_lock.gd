extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var test = load("res://tests/test_explorer_cockpit_lock.gd").new()
	var failures: Array = await test.run()
	if not test.completed:
		failures.append("Explorer cockpit lock aborted before completion")
	for failure in failures:
		printerr(failure)
	print("Explorer cockpit lock: %d failures" % failures.size())
	quit(0 if failures.is_empty() else 1)
