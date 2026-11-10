extends RefCounted

# Presentation copy only. Every state transition is a checked native request.
var bridge
var current: Dictionary = {}
var feedback := "Object ready · no gravity."
var topology := 0

func _init(provider) -> void:
	bridge = provider

func begin(shape: Array) -> bool:
	return _accept(bridge.explorer_2d({"op": "begin", "profile": _profile(shape, 0)}))

func _profile(shape: Array, index: int) -> Dictionary:
	# Canonical v1 declarative axis pairings; the provider validates and executes.
	var seams: Array = []
	for axis in 2:
		if index == 3 or index == axis + 1:
			seams.append({"id": "wrap_%d" % axis, "source": {"axis": "x" if axis == 0 else "y", "side": "-"}, "target": {"axis": "x" if axis == 0 else "y", "side": "+"}, "transform": {"permutation": [0], "signs": [1]}, "enabled": true})
	var profile: Dictionary = preload("res://scripts/ui/game_setup/game_setup_spec.gd").bounded_topology_profile(shape)
	profile.seams = seams
	return profile

func select_topology(index: int) -> bool:
	if index < 0 or index > 3:
		return false
	if not _accept(bridge.explorer_2d({"op": "profile", "profile": _profile(current.piece.profile.dimensions, index)})):
		return false
	topology = index
	feedback = "Topology changed. Object reset; view unchanged."
	return true

func command(command_name: String) -> bool:
	var commands := ["move_x_neg", "move_x_pos", "move_y_neg", "move_y_pos"]
	var index := commands.find(command_name)
	if index < 0:
		return false
	var proposal: Dictionary = bridge.explorer_2d({"op": "propose", "revision": current.revision, "source": current.piece, "action": {"axis": index / 2, "delta": -1 if index % 2 == 0 else 1}})
	if not proposal.get("ok", false):
		return _accept(proposal)
	var crossed := false
	for witness in proposal.candidate.witnesses:
		crossed = crossed or witness.seam != null
	if not _accept(bridge.explorer_2d({"op": "apply", "candidate": proposal.candidate})):
		return false
	feedback = "Moved across the %s seam." % ("X" if index < 2 else "Y") if crossed else "Moved. View unchanged."
	return true

func retry() -> bool:
	if not _accept(bridge.explorer_2d({"op": "retry"})):
		return false
	feedback = "Object restored exactly. View unchanged."
	return true

func replace_piece(index: int) -> bool:
	if not _accept(bridge.explorer_2d({"op": "replace", "index": index})):
		return false
	feedback = "Replaced piece: %s. View unchanged." % str(current.get("piece_name", ""))
	return true

func _accept(result: Dictionary) -> bool:
	if result.get("ok", false):
		current = result
		return true
	var code := str(result.get("error", {}).get("code", "missing_provider"))
	match code:
		"unconnected_boundary":
			feedback = "Movement blocked: board boundary." if topology == 0 else "Movement blocked: this edge is not connected."
		"stale_candidate":
			feedback = "Movement could not be applied: state changed."
		_:
			feedback = "Movement unavailable for this piece."
	return false
