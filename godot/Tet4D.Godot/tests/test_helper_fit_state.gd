extends RefCounted

const FitState = preload("res://scripts/ui/helper_fit_state.gd")
const Policy = preload("res://scripts/ui/responsive_panel_policy.gd")


func run() -> Array:
	var failures: Array = []
	for reason in ["larger room", "rebuilt content", "constraint change"]:
		var state = FitState.new()
		var room := func(_height: float) -> float: return 120.0
		for frame in range(4):
			state.observe(300.0, room, 400.0, true, frame, 0.0, false, ["content"])
		if not state.snapshot()["searching"]:
			failures.append("cancellation fixture must reach an active search")
		if reason == "larger room":
			state.observe(300.0, func(_h: float) -> float: return 400.0, 400.0, true, 5, 0.0, false, ["content"])
		elif reason == "rebuilt content":
			state.observe(300.0, room, 400.0, true, 5, 0.0, true, ["content"])
		else:
			state.observe(300.0, room, 500.0, true, 5, 0.0, false, ["content"])
		var snapshot: Dictionary = state.snapshot()
		if snapshot["searching"] or not snapshot["settled"] or snapshot["scale"] != 1.0:
			failures.append("%s must clear search and pending samples at full scale" % reason)
	for height in [220.0, 500.0]:
		var state = FitState.new()
		_solve(state, 350.0, "old", 0)
		var changed: Dictionary = state.observe(height, func(_h: float) -> float: return 200.0, 400.0, true, 100, 0.0, false, ["new"])
		if changed["compact"] or changed["scale"] != 1.0 or not changed["remeasure"]:
			failures.append("new intrinsic content must discard the old sample and restart relaxed")
		var after := _solve(state, height, "new", 101)
		var clean := _solve(FitState.new(), height, "new", 101)
		if after < FitState.SCALE_FLOOR or clean < FitState.SCALE_FLOOR or not is_equal_approx(after, clean) or not state.settled():
			failures.append("changed content must converge like clean entry, height %s" % height)
	# A new piece name in a fixed-width label: new content, same measurements.
	var renamed = FitState.new()
	var settled_scale := _solve(renamed, 350.0, "old", 0)
	var kept: Dictionary = renamed.observe(350.0, func(_h: float) -> float: return 200.0, 400.0, true, 100, 0.0, false, ["new"])
	if not kept["compact"] or not is_equal_approx(float(kept["scale"]), settled_scale):
		failures.append("a height-neutral edit must keep a settled fit, not replay its search")
	if not is_equal_approx(_solve(renamed, 350.0, "new", 101), settled_scale):
		failures.append("a height-neutral edit must stay at the settled scale")
	for frame in range(200, 210):
		var repeated: Dictionary = renamed.observe(350.0, func(_h: float) -> float: return 200.0, 400.0, true, frame, 0.0, false, ["new"])
		if not renamed.settled() or bool(repeated["remeasure"]) or not is_equal_approx(float(repeated["scale"]), settled_scale):
			failures.append("unchanged settled fit must stay idle under repeated layout observations")
			break
	var same_frame = FitState.new()
	var room := func(_h: float) -> float: return 100.0
	same_frame.observe(300.0, room, 400.0, true, 1, 0.0, false, ["x"])
	same_frame.observe(300.0, room, 400.0, true, 1, 0.0, false, ["x"])
	if same_frame.is_compact():
		failures.append("same-frame measurements must not advance compaction")
	var panel := VBoxContainer.new()
	panel.add_theme_constant_override("separation", 10)
	var label := Label.new()
	label.text = "Available · C"
	panel.add_child(label)
	var before := Policy.fit_content_key(panel)
	Policy.compact_vertical_gaps(panel, true)
	panel.size = Vector2(500, 300)
	panel.scale = Vector2(0.8, 0.8)
	if Policy.fit_content_key(panel) != before:
		failures.append("allocation, scaling and own compaction must not invalidate intrinsic content")
	label.text = "Used until lock"
	if Policy.fit_content_key(panel) == before:
		failures.append("editing an existing label must invalidate its fit")
	var edited := Policy.fit_content_key(panel)
	label.add_theme_font_size_override("font_size", 32)
	if Policy.fit_content_key(panel) == edited:
		failures.append("font metrics on existing controls must invalidate the fit")
	panel.free()
	return failures


func _solve(state, height: float, key: String, start: int) -> float:
	var result: Dictionary = {}
	for frame in range(start, start + 80):
		result = state.observe(height, func(_h: float) -> float: return 200.0, 400.0, true, frame, 0.0, false, [key])
		if state.settled() and not result["remeasure"]:
			return float(result["scale"])
	return -1.0
