extends RefCounted


func run() -> Array:
	var failures: Array = []
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		failures.append("trace replay scene should load")
		return failures
	var root := scene.instantiate()
	if root == null:
		failures.append("trace replay scene should instantiate")
		return failures
	if not (root is Control):
		failures.append("trace replay root should be a full-rect Control")
	if root.get_node_or_null("UILayer") != null:
		failures.append("trace replay scene should not use a CanvasLayer for viewer layout")
	var hud := root.get_node_or_null("ReplayHud")
	if hud == null:
		failures.append("trace replay scene should include ReplayHud at the root layout level")
	else:
		if not hud.has_method("set_world_root"):
			failures.append("ReplayHud should own the GameArea SubViewport install path")
		if not hud.has_method("game_viewport"):
			failures.append("ReplayHud should expose its game SubViewport for layout tests")
		if not hud.has_method("layout_contract_snapshot"):
			failures.append("ReplayHud should expose layout contract diagnostics")
	if root.get_node_or_null("WorldRoot") != null:
		failures.append("WorldRoot should not be a root-level scene sibling")
	root.queue_free()
	return failures
