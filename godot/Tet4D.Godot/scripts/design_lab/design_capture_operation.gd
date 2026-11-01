extends RefCounted

# Owns async request lifetime only. Comparison, rendering and storage retain
# their existing owners and are supplied through bounded public callbacks.
var _revision := 0
var _busy := false


func busy() -> bool:
	return _busy


func cancel() -> void:
	_revision += 1
	_busy = false


func run(tree: SceneTree, callbacks: Dictionary, arms: Array, restore: bool, budget: int) -> Dictionary:
	if _busy:
		return _failure("A capture is already in progress.")
	if tree == null or budget <= 0:
		return _failure("Capture requires a tree and a positive settle budget.")
	for name in ["snapshot", "fingerprint", "activate", "readiness", "image", "store"]:
		if not (callbacks.get(name, Callable()) as Callable).is_valid():
			return _failure("Capture callback is unavailable: %s." % name)
	var frozen: Dictionary = callbacks.snapshot.call().duplicate(true)
	if frozen.is_empty():
		return _failure("Start a comparison before capturing.")
	_revision += 1
	var revision := _revision
	_busy = true
	var original_arm := str(frozen.get("shown_arm", ""))
	var captured: Array = []
	var owned_arm := ""
	var error := ""
	for arm in arms:
		if not _same_comparison(callbacks, frozen, revision) or not bool(callbacks.activate.call(arm)):
			error = "Capture cancelled or arm could not be applied."
			break
		owned_arm = str(arm)
		var settled: Dictionary = await _settle(tree, callbacks, frozen, str(arm), revision, budget)
		if not bool(settled.get("ok", false)):
			error = str(settled.get("error", "Capture did not settle."))
			break
		var image = callbacks.image.call()
		if not _matches(callbacks, frozen, str(arm), revision) or not _same_ready(callbacks, str(settled.get("token", "")), str(frozen.get("arms", {}).get(arm, {}).get("snapshot_hash", ""))):
			error = "Capture identity or layout changed before storage."
			break
		var metadata := frozen.duplicate(true)
		metadata["shown_arm"] = arm
		var stored: Dictionary = callbacks.store.call(image, metadata, arm)
		if not bool(stored.get("ok", false)):
			error = str(stored.get("error", "Capture could not be saved."))
			break
		captured.append(arm)
	var restoration_error := ""
	if restore and _matches(callbacks, frozen, owned_arm, revision) and str(callbacks.readiness.call().get("profile_hash", "")) == str(frozen.get("arms", {}).get(owned_arm, {}).get("snapshot_hash", "")):
		if bool(callbacks.activate.call(original_arm)):
			var restored: Dictionary = await _settle(tree, callbacks, frozen, original_arm, revision, budget)
			if not bool(restored.get("ok", false)):
				restoration_error = str(restored.get("error", "Shown arm did not settle after restoration."))
		else:
			restoration_error = "Original shown arm could not be restored."
	if revision == _revision:
		_busy = false
	return {"ok": error.is_empty() and restoration_error.is_empty(), "error": error, "restoration_error": restoration_error, "captured_arms": captured}


func _settle(tree: SceneTree, callbacks: Dictionary, frozen: Dictionary, arm: String, revision: int, budget: int) -> Dictionary:
	var previous := ""
	var waiting_token := ""
	var drawn_frame := -1
	for _frame in range(budget):
		await tree.process_frame
		if not _matches(callbacks, frozen, arm, revision):
			return _failure("Capture cancelled because comparison identity changed.")
		var observation: Dictionary = callbacks.readiness.call()
		if str(observation.get("profile_hash", "")) != str(frozen.get("arms", {}).get(arm, {}).get("snapshot_hash", "")):
			return _failure("The displayed profile no longer matches the frozen capture arm.")
		var token := str(observation.get("token", ""))
		if not bool(observation.get("ready", false)) or token.is_empty():
			previous = ""
			waiting_token = ""
			continue
		if token != waiting_token:
			waiting_token = ""
		if token == waiting_token and int(observation.get("drawn_frame", 0)) > drawn_frame:
			return {"ok": true, "token": token}
		if token == previous and waiting_token.is_empty():
			waiting_token = token
			drawn_frame = int(observation.get("drawn_frame", 0))
		previous = token
	return _failure("Capture timed out waiting for stable layout and a matching drawn frame.")


func _same_ready(callbacks: Dictionary, token: String, profile_hash: String) -> bool:
	if not callbacks.readiness.is_valid():
		return false
	var observation: Dictionary = callbacks.readiness.call()
	return bool(observation.get("ready", false)) and str(observation.get("token", "")) == token and str(observation.get("profile_hash", "")) == profile_hash


func _same_comparison(callbacks: Dictionary, frozen: Dictionary, revision: int) -> bool:
	if revision != _revision or not _busy:
		return false
	for name in ["snapshot", "fingerprint", "activate", "readiness", "image", "store"]:
		if not callbacks[name].is_valid():
			return false
	var current: Dictionary = callbacks.snapshot.call()
	# Shown arm and toggle count may change as this operation visits its arms.
	for key in ["session_id", "assignment_revision", "scenario", "non_style_hash", "arms", "blind", "blind_labels"]:
		if current.get(key) != frozen.get(key):
			return false
	var fingerprint: Dictionary = callbacks.fingerprint.call()
	return fingerprint == frozen.get("non_style_fingerprint", {})


func _matches(callbacks: Dictionary, frozen: Dictionary, arm: String, revision: int) -> bool:
	if not _same_comparison(callbacks, frozen, revision):
		return false
	return str(callbacks.snapshot.call().get("shown_arm", "")) == arm


func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error, "captured_arms": []}
