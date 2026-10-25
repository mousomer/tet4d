extends SceneTree

# Geometry can run headless; screenshots and fullscreen acceptance require a
# real DisplayServer. Usage: Godot --path godot/Tet4D.Godot --script
# tests/run_panel_responsive_acceptance.gd -- capture_dir=/absolute/path fullscreen
const Test = preload("res://tests/test_panel_responsiveness.gd")


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var test := Test.new()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("capture_dir="):
			test.capture_dir = argument.trim_prefix("capture_dir=")
		elif argument == "fullscreen":
			test.exercise_fullscreen = true
		elif argument.begins_with("size="):
			var axes := argument.trim_prefix("size=").split("x")
			if axes.size() == 2 and axes[0].is_valid_int() and axes[1].is_valid_int():
				test.sizes = [Vector2i(int(axes[0]), int(axes[1]))]
		elif argument.begins_with("scale="):
			test.scales = [argument.trim_prefix("scale=")]
	if DisplayServer.get_name() == "headless" and (test.exercise_fullscreen or not test.capture_dir.is_empty()):
		push_error("Rendered capture/fullscreen acceptance requires a real DisplayServer")
		quit(2)
		return
	var failures: Array = await test.run()
	if not test.completed:
		failures.append("panel responsiveness test aborted before completing its matrix")
	if not test.capture_dir.is_empty():
		DirAccess.make_dir_recursive_absolute(test.capture_dir)
		var file := FileAccess.open(test.capture_dir.path_join("observations.json"), FileAccess.WRITE)
		file.store_string(JSON.stringify({"display_server": DisplayServer.get_name(), "observations": test.observations, "failures": failures}, "\t"))
	for failure in failures:
		push_error(str(failure))
	print("PANEL_RESPONSIVE_ACCEPTANCE %s (%s findings)" % ["PASS" if failures.is_empty() else "FAIL", failures.size()])
	quit(0 if failures.is_empty() else 1)
