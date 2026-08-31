extends SceneTree


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var script = load("res://tests/test_design_evaluation_laboratory.gd")
	if script == null or not script.can_instantiate():
		print("Design Laboratory test script could not be instantiated.")
		quit(1)
		return
	var test_case = script.new()
	var failures: Array = test_case.run()
	if failures.is_empty():
		print("Design Laboratory tests passed.")
		quit(0)
		return
	for failure in failures:
		print(str(failure))
	quit(1)
