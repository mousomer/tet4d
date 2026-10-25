extends SceneTree

func _initialize() -> void:
	call_deferred("_execute")

func _execute() -> void:
	var scenario = load("res://tests/test_live_relative_translation.gd").new()
	var errors: Array = await scenario.run()
	if not scenario.completed:
		errors.append("Regression suite did not finish")
	for item in errors:
		printerr(item)
	if errors.is_empty():
		print("Live relative translation focused runner passed (3D + 4D).")
	quit(0 if errors.is_empty() else 1)
