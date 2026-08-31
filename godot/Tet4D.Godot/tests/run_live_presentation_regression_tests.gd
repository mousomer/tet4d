extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failures: Array = await load("res://tests/test_live_presentation_regressions.gd").new().run()
	if failures.is_empty():
		print("Live presentation regression tests passed.")
		quit(0)
		return
	for failure in failures:
		push_error(str(failure))
		print(str(failure))
	quit(1)
