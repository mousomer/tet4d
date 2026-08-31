extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var script = load("res://tests/test_cross_platform_design_boundary.gd")
	if script == null or not script.can_instantiate():
		print("Cross-platform Design Laboratory test script could not be instantiated.")
		quit(1)
		return
	var failures: Array = script.new().run()
	if failures.is_empty():
		print("Cross-platform Design Laboratory tests passed.")
		quit(0)
		return
	for failure in failures:
		print(str(failure))
	quit(1)
