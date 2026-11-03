extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var test = load("res://tests/test_practice_explorer.gd").new()
	var failures: Array = await test.run()
	if not test.completed:
		failures.append("Practice Explorer aborted before completion")
	for failure in failures:
		printerr(failure)
	print("Practice Explorer: %d failures" % failures.size())
	quit(0 if failures.is_empty() else 1)
