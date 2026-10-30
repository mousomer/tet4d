extends RefCounted

const Operation = preload("res://scripts/design_lab/design_capture_operation.gd")

class CaptureHarness extends RefCounted:
	var session := {"session_id": "frozen", "assignment_revision": 0, "scenario": {"id": "fixed"}, "non_style_hash": "native", "non_style_fingerprint": {"native": "unchanged"}, "arms": {"A": {"snapshot_hash": "a"}, "B": {"snapshot_hash": "b"}}, "blind": true, "blind_labels": {"A": "Option 1", "B": "Option 2"}, "shown_arm": "B"}
	var fingerprint := {"native": "unchanged"}
	var calls := 0
	var pending := 4
	var token := "layout"
	var profile_override := ""
	var draw := true
	var image_failure := false
	var store_failure := ""
	var apply_failure := ""
	var fail_restore := false
	var invalidate_at := 0
	var invalidation := ""
	var stored: Array = []
	var activations: Array = []
	var operation

	func snapshot() -> Dictionary:
		return session.duplicate(true)

	func activate(arm: String) -> bool:
		activations.append(arm)
		if arm == apply_failure or (fail_restore and activations.size() == 3):
			return false
		session.shown_arm = arm
		calls = 0
		return true

	func readiness() -> Dictionary:
		calls += 1
		if invalidate_at == calls:
			match invalidation:
				"session": session.session_id = "replacement"
				"assignment": session.arms.A.snapshot_hash = "replacement"
				"fingerprint": fingerprint.native = "changed"
				"shown": session.shown_arm = "B" if session.shown_arm == "A" else "A"
				"cancel": operation.cancel()
				"profile": profile_override = "external"
				"layout": token = "new-layout"
		return {"ready": calls > pending, "token": token, "drawn_frame": Engine.get_process_frames() if draw else 0, "profile_hash": profile_override if not profile_override.is_empty() else session.arms[session.shown_arm].snapshot_hash}

	func image():
		if image_failure:
			return null
		return Image.create(2, 2, false, Image.FORMAT_RGBA8)

	func store(image_value, frozen: Dictionary, arm: String) -> Dictionary:
		if image_value == null or arm == store_failure:
			return {"ok": false, "error": "simulated image/store failure"}
		stored.append({"arm": arm, "session": frozen, "calls": calls, "token": token})
		return {"ok": true}

	func callbacks() -> Dictionary:
		return {"snapshot": snapshot, "activate": activate, "fingerprint": func(): return fingerprint.duplicate(true), "readiness": readiness, "image": image, "store": store}


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var harness := CaptureHarness.new()
	var operation = Operation.new()
	harness.operation = operation
	var result: Dictionary = await operation.run(tree, harness.callbacks(), ["A", "B"], true, 30)
	if not result.ok or result.captured_arms != ["A", "B"] or harness.session.shown_arm != "B" or operation.busy():
		failures.append("settled pair must capture both frozen arms, restore B and release busy state")
	for record in harness.stored:
		if record.calls <= harness.pending + 2 or record.session.arms[record.arm].snapshot_hash != record.arm.to_lower() or record.session.non_style_hash != "native":
			failures.append("capture must wait through multiple layout passes and preserve exact frozen provenance")
	for mutation in ["session", "assignment", "fingerprint", "shown", "cancel", "profile"]:
		harness = CaptureHarness.new()
		operation = Operation.new()
		harness.operation = operation
		harness.invalidate_at = 3
		harness.invalidation = mutation
		result = await operation.run(tree, harness.callbacks(), ["A"], false, 30)
		if result.ok or not harness.stored.is_empty() or operation.busy():
			failures.append("%s during wait must abort without storage and release busy" % mutation)
	# Mutation after readiness / before readback must be rejected as well.
	harness = CaptureHarness.new()
	operation = Operation.new()
	harness.operation = operation
	harness.pending = 0
	harness.invalidate_at = 3
	harness.invalidation = "assignment"
	result = await operation.run(tree, harness.callbacks(), ["A"], false, 30)
	if result.ok or not harness.stored.is_empty():
		failures.append("identity mutation in the drawn-frame boundary must not reach storage")
	for failure in ["timeout", "no_draw", "apply", "image", "store", "layout"]:
		harness = CaptureHarness.new()
		operation = Operation.new()
		harness.operation = operation
		match failure:
			"timeout": harness.pending = 100
			"no_draw": harness.draw = false
			"apply": harness.apply_failure = "A"
			"image": harness.image_failure = true
			"store": harness.store_failure = "A"
			"layout":
				harness.invalidate_at = 6
				harness.invalidation = "layout"
		result = await operation.run(tree, harness.callbacks(), ["A"], false, 15)
		if failure == "layout":
			if not result.ok or harness.stored.size() != 1 or harness.stored[0].token != "new-layout":
				failures.append("changed layout must settle and draw its replacement token before storage")
		elif result.ok or operation.busy() or not harness.stored.is_empty():
			failures.append("%s must fail safely without a published capture" % failure)
		# A failed request cannot poison subsequent work.
		harness.pending = 0
		harness.draw = true
		harness.apply_failure = ""
		harness.image_failure = false
		harness.store_failure = ""
		harness.invalidate_at = 0
		result = await operation.run(tree, harness.callbacks(), ["A"], false, 15)
		if not result.ok:
			failures.append("valid request after %s must succeed" % failure)
	# Start two requests without awaiting the first: the second must be rejected.
	harness = CaptureHarness.new()
	operation = Operation.new()
	harness.operation = operation
	var completed: Array = []
	_collect(operation, tree, harness.callbacks(), completed)
	result = await operation.run(tree, harness.callbacks(), ["B"], true, 30)
	if result.ok or not operation.busy():
		failures.append("duplicate request must be rejected without cancelling the first")
	while completed.is_empty():
		await tree.process_frame
	if not completed[0].ok or harness.stored.size() != 1:
		failures.append("first request must survive duplicate rejection")
	harness = CaptureHarness.new()
	operation = Operation.new()
	harness.operation = operation
	harness.store_failure = "B"
	result = await operation.run(tree, harness.callbacks(), ["A", "B"], true, 30)
	if result.ok or result.captured_arms != ["A"] or harness.session.shown_arm != "B":
		failures.append("pair partial failure must report only A and restore the original shown arm")
	harness = CaptureHarness.new()
	operation = Operation.new()
	harness.operation = operation
	harness.fail_restore = true
	result = await operation.run(tree, harness.callbacks(), ["A", "B"], true, 30)
	if result.ok or result.captured_arms != ["A", "B"] or str(result.get("restoration_error", "")).is_empty() or operation.busy():
		failures.append("restoration failure must retain both valid captures and report a separate error")
	result = await Operation.new().run(tree, harness.callbacks(), ["A"], false, 0)
	if result.ok:
		failures.append("zero frame budget must fail immediately")
	failures.append_array(await _test_panel(tree))
	return failures


func _collect(operation, tree, callbacks: Dictionary, completed: Array) -> void:
	completed.append(await operation.run(tree, callbacks, ["A"], false, 30))


func _test_panel(tree: SceneTree) -> Array:
	var failures: Array = []
	var registry = load("res://scripts/ui/settings/settings_registry.gd").new()
	registry.load_from_path(registry.REGISTRY_PATH)
	var panel = load("res://scripts/ui/design_laboratory_panel.gd").new()
	tree.root.add_child(panel)
	var state := {"samples": 0, "images": 0, "early": false, "profile_hash": ""}
	var configured: bool = panel.configure(registry, {
		"load_scenario": func(_scenario): return {"ok": true, "fingerprint": {}},
		"apply_profile": func(profile):
			state.profile_hash = load("res://scripts/design_lab/design_value.gd").canonical_hash(profile.snapshot())
			return true,
		"current_fingerprint": func(): return {},
		"capture_readiness": func():
			state.samples += 1
			return {"ready": state.samples > 5, "token": "settled", "drawn_frame": Engine.get_process_frames(), "profile_hash": state.profile_hash},
		"capture_image": func():
			state.images += 1
			state.early = state.samples <= 7
			return Image.create(2, 2, false, Image.FORMAT_RGBA8),
		"build_identity": func(): return {"test": true},
		"edit_candidate": func(_id): pass,
	})
	if not configured:
		panel.queue_free()
		await tree.process_frame
		return ["capture integration requires a configured production laboratory"]
	panel.open()
	panel.find_child("StartComparisonButton", true, false).pressed.emit()
	var capture_button: Button
	for button in panel.find_children("*", "Button", true, false):
		if button.text == "Capture A":
			capture_button = button
	if capture_button == null:
		failures.append("production laboratory must expose Capture A")
	else:
		capture_button.pressed.emit()
		for _frame in range(25):
			await tree.process_frame
			# Drive a draw boundary even in the headless test. Readiness remains
			# deliberately false for several passes, so one draw is insufficient.
			RenderingServer.frame_post_draw.emit()
		if state.images != 1 or state.early:
			failures.append("production capture must wait for layout completion, not just one drawn frame")
		if bool(panel.deterministic_snapshot().get("capture_busy", false)) or capture_button.disabled:
			failures.append("production capture must release busy controls after completion")
		state.samples = -100
		capture_button.pressed.emit()
		await tree.process_frame
		panel.close()
		panel.open()
		state.samples = 0
		capture_button.pressed.emit()
		for _frame in range(25):
			await tree.process_frame
			RenderingServer.frame_post_draw.emit()
		if state.images != 2 or bool(panel.deterministic_snapshot().get("capture_busy", false)):
			failures.append("close/reopen must cancel old capture without blocking or publishing over the new request")
	if capture_button != null:
		state.samples = -100
		capture_button.pressed.emit()
		await tree.process_frame
	panel.queue_free()
	for _frame in range(3):
		await tree.process_frame
	if state.images != 2:
		failures.append("panel teardown during capture must not publish or resume against freed controls")
	return failures
