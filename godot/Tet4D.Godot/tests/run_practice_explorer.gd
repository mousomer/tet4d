extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var test = load("res://tests/test_practice_explorer.gd").new()
	var dispatch = preload("res://tests/test_explorer_input_dispatch.gd").new()
	var dispatch_failures: Array = await dispatch.run()
	if not dispatch.completed: dispatch_failures.append("Explorer dispatch aborted before completion")
	var failures: Array = preload("res://tests/test_explorer_surfaces.gd").new().run()
	failures.append_array(dispatch_failures)
	failures.append_array(await test.run())
	if not test.completed:
		failures.append("Practice Explorer aborted before completion")
	for failure in failures:
		printerr(failure)
	print("Practice Explorer: %d failures" % failures.size())
	quit(0 if failures.is_empty() else 1)
