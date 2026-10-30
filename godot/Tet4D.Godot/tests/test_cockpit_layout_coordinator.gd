extends RefCounted

const Coordinator = preload("res://scripts/ui/cockpit_layout_coordinator.gd")
const Policy = preload("res://scripts/ui/cockpit_layout_policy.gd")


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var coordinator = Coordinator.new()
	var applied: Array = []
	var measured: Array = []
	coordinator.configure(func() -> void: applied.append(coordinator.generation()),
		func() -> void: measured.append(coordinator.generation()))
	tree.root.add_child(coordinator)
	for _burst in range(8):
		coordinator.request_metrics()
	if coordinator.idle():
		failures.append("queued metrics must keep completion pending")
	await tree.process_frame
	if measured.size() != 1 or not coordinator.idle():
		failures.append("one frame must coalesce a metrics burst into one observation")
	coordinator.request_metrics()
	coordinator.request_fit()
	await tree.process_frame
	if applied.size() != 1 or measured.size() != 1:
		failures.append("a required fit must consume the coalesced metrics request")
	var previous: int = coordinator.generation()
	coordinator.request_fit()
	coordinator.apply_now()
	var count := applied.size()
	if coordinator.generation() <= previous or count != 2:
		failures.append("new context must apply synchronously and advance its generation")
	await tree.process_frame
	if applied.size() != count or not coordinator.idle():
		failures.append("superseded queued work must not apply after the new context")
	coordinator.request_fit()
	coordinator.invalidate()
	await tree.process_frame
	if applied.size() != count or not coordinator.idle():
		failures.append("ownership invalidation must discard old work without applying layout")
	coordinator.configure(func() -> void:
		applied.append(coordinator.generation())
		if applied.size() == count + 1:
			coordinator.request_fit(), func() -> void: measured.append(coordinator.generation()))
	coordinator.apply_now()
	if coordinator.idle():
		failures.append("a fit requested during application must remain pending")
	await tree.process_frame
	if applied.size() != count + 2 or not coordinator.idle():
		failures.append("application continuation must run once and become idle")
	count = applied.size()
	coordinator.request_fit()
	coordinator.free()
	await tree.process_frame
	if applied.size() != count:
		failures.append("leaving the tree must cancel queued work")
	var modules := [{"name": "NEXT", "width": 100.0}, {"name": "PIECE", "width": 200.0}, {"name": "VIEW", "width": 80.0}]
	if Policy.pack_rows(modules, 310, 10) != [["NEXT", "PIECE"], ["VIEW"]]:
		failures.append("packing must include measured gaps and preserve module order")
	if Policy.pack_rows(modules, 0, 10) != [["NEXT", "PIECE", "VIEW"]]:
		failures.append("unknown width must preserve the initial row")
	if Policy.placement("split", Policy.profile(Vector2(799, 500))) != "below" or Policy.placement("side", "small") != "side":
		failures.append("split fallback must not alter side-rail semantics")
	if Policy.below_deck_room(100, 220, 200, 10, true, 0.6) != 132.0:
		failures.append("constrained deck must retain its existing readable row floor")
	return failures
