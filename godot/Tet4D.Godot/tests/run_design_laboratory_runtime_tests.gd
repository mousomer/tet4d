extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var script = load("res://tests/test_design_laboratory_runtime.gd")
	if script == null or not script.can_instantiate():
		print("Design Laboratory runtime test script could not be instantiated.")
		quit(1)
		return
	var failures: Array = await script.new().run()
	if failures.is_empty():
		print("Design Laboratory runtime tests passed.")
		quit(0)
		return
	for failure in failures:
		print(str(failure))
	quit(1)
