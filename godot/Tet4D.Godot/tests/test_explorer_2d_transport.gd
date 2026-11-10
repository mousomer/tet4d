extends RefCounted

const Bridge = preload("res://scripts/native/tet4d_core_bridge.gd")
const Adapter = preload("res://scripts/presentation/explorer_2d_adapter.gd")
var failures: Array = []

# Expected wrapping axes are specified by the four T2B presets, not a movement simulation.
func run() -> Array:
	var bridge = Bridge.new()
	if not bridge.is_available():
		return ["2D transport requires actual GDExtension"]
	var model = Adapter.new(bridge)
	_check(model.begin([10, 12]), "begin bounded production piece")
	if model.current.is_empty():
		return failures
	var play := [bridge.live_2d_state_hash(), bridge.live_3d_state_hash(), bridge.live_4d_state_hash()]
	for topology in 4:
		_check(model.select_topology(topology), "profile %d" % topology)
		_check(model.replace_piece(2), "production T piece")
		var initial: Dictionary = model.current.piece.duplicate(true)
		for axis in 2:
			for direction in [-1, 1]:
				model.retry()
				# tet4d-semantic-boundary: allow test-fixture
				var wraps := topology == 3 or topology == axis + 1
				var seams := 0
				var blocks := 0
				for step in 27:
					var before: Dictionary = bridge.explorer_2d({"op": "snapshot"})
					var command := "move_%s_%s" % ["x" if axis == 0 else "y", "neg" if direction == -1 else "pos"]
					var accepted: bool = model.command(command)
					if not accepted:
						blocks += 1
						_check(bridge.explorer_2d({"op": "snapshot"}) == before, "blocked preserves full envelope")
					else:
						if "seam" in model.feedback:
							seams += 1
						_check(model.current.piece.rest_cells == initial.rest_cells, "rest IDs conserved")
						_check(model.current.piece.object_key == initial.object_key, "object identity conserved")
						var occupied: Array = []
						for cell in model.current.piece.cells:
							_check(cell.coordinate not in occupied, "injective canonical occupancy")
							occupied.append(cell.coordinate)
							_check(cell.frame == initial.cells[cell.id].frame, "frame preserved")
						var inv: Dictionary = bridge.explorer_2d({"op": "inverse", "revision": model.current.revision, "inverse": model.current.undo.back()})
						_check(inv.get("ok", false), "recorded inverse proposal")
						if inv.get("ok", false):
							var recovered: Dictionary = bridge.explorer_2d({"op": "apply", "candidate": inv.candidate})
							_check(recovered.get("piece") == before.piece and recovered.get("undo") == before.undo, "exact inverse semantic and undo recovery")
							model.current = recovered
							_check(model.command(command), "reapply after inverse")
				_check(seams >= 2 if wraps else blocks > 0, "correct seam/wall classification")
				_check(blocks == 0 if wraps else seams == 0, "profile controls transport")
		_check(model.retry() and model.current.piece == initial and model.current.undo.is_empty(), "Retry exact restoration")
	_atomic_failures(bridge, model)
	_hostile_variants(bridge, model)
	_replacement_clears_rejection(model)
	_check(play == [bridge.live_2d_state_hash(), bridge.live_3d_state_hash(), bridge.live_4d_state_hash()], "all Play hashes isolated")
	return failures

func _atomic_failures(bridge, model) -> void:
	var before: Dictionary = bridge.explorer_2d({"op": "snapshot"})
	var request := {"op": "propose", "revision": before.revision, "source": before.piece, "action": {"axis": 0, "delta": 1}}
	var invalid: Array = [null, [], {"op": "snapshot", "extra": 0}, {"op": "replace", "index": 2.0}, {"op": "replace", "index": -1}, {"op": "profile", "profile": {}}, {"op": "inverse", "revision": before.revision, "inverse": {}}]
	var twisted: Dictionary = model._profile([10, 12], 1)
	twisted.seams[0].transform.signs = [-1]
	invalid.append({"op": "profile", "profile": twisted})
	var bad_id := request.duplicate(true)
	bad_id.source.object_key.ordinal = -1
	invalid.append(bad_id)
	var extra_state := request.duplicate(true)
	extra_state.source.extra = 1
	invalid.append(extra_state)
	var wrong_revision := request.duplicate(true)
	wrong_revision.revision = float(before.revision)
	invalid.append(wrong_revision)
	for value in [0.0, "0", 2, -1, true]:
		var bad := request.duplicate(true)
		bad.action.axis = value
		invalid.append(bad)
	for path in ["version", "object_key", "profile", "rest_cells", "cells"]:
		var bad := request.duplicate(true)
		bad.source.erase(path)
		invalid.append(bad)
	var bad_frame := request.duplicate(true)
	bad_frame.source.cells[0].frame.signs[0] = 1.0
	invalid.append(bad_frame)
	var stale := request.duplicate(true)
	stale.revision -= 1
	invalid.append(stale)
	var proposal: Dictionary = bridge.explorer_2d(request)
	_check(proposal.get("ok", false), "valid proposal before corruption")
	if proposal.get("ok", false):
		var tampered: Dictionary = proposal.candidate.duplicate(true)
		tampered.target.cells[0].coordinate[0] += 1
		invalid.append({"op": "apply", "candidate": tampered})
	for bad in invalid:
		var result: Dictionary = bridge.explorer_2d(bad)
		_check(not result.get("ok", true), "malformed request rejected")
		_check(bridge.explorer_2d({"op": "snapshot"}) == before, "failure preserves complete native state")
	_check(model.replace_piece(2), "replace same shape")
	_check(model.current.piece.object_key != before.piece.object_key, "replacement fresh identity")
	if proposal.get("ok", false):
		var after: Dictionary = bridge.explorer_2d({"op": "snapshot"})
		_check(not bridge.explorer_2d({"op": "apply", "candidate": proposal.candidate}).ok, "replacement invalidates old candidate")
		_check(bridge.explorer_2d({"op": "snapshot"}) == after, "old candidate atomic")
	bridge.explorer_2d({"op": "close"})
	_check(not bridge.explorer_2d(request).ok, "closed provider unavailable")
	_check(model.begin([10, 12]), "reentry")
	_check(model.current.piece.object_key.namespace != before.piece.object_key.namespace, "new session namespace")

# Regression: a self-referential profile once recursed past the native stack
# (signal 11) before schema validation could reject it. Aliased containers must
# come back as a structured resource_limit failure on every converter entry.
func _hostile_variants(bridge, model) -> void:
	var cyclic: Dictionary = model._profile([10, 12], 0)
	cyclic["self"] = cyclic
	var looped: Array = []
	looped.append(looped)
	var looped_profile: Dictionary = model._profile([10, 12], 0)
	looped_profile.seams = looped
	# Twenty levels of a container shared by two keys: tiny in memory, about a
	# million values when walked, still shallower than the depth bound.
	var diamond: Variant = 0
	for level in 20:
		diamond = {"left": diamond, "right": diamond}
	var wide: Dictionary = model._profile([10, 12], 0)
	wide["extra"] = diamond
	var before: Dictionary = bridge.explorer_2d({"op": "snapshot"})
	for hostile in [cyclic, looped_profile, wide]:
		for op in ["profile", "begin"]:
			var result: Dictionary = bridge.explorer_2d({"op": op, "profile": hostile})
			_check(not result.get("ok", true), "hostile %s rejected" % op)
			_check(str(result.get("error", {}).get("code", "")) == "resource_limit", "hostile %s reports resource_limit" % op)
			_check(bridge.explorer_2d({"op": "snapshot"}) == before, "hostile %s preserves native state" % op)
		_check(str(bridge.topology_transport_profile(hostile).get("error", {}).get("code", "")) == "resource_limit", "shared converter bounded")
	var setup := {"contract_version": 1, "mode": "live_2d", "board_shape": [10, 20], "piece_set_id": "classic", "topology_profile": cyclic}
	_check(not bridge.validate_live_board_setup(setup).get("ok", true), "cyclic live setup rejected")
	# Break the reference cycles so the test leaks nothing.
	cyclic.erase("self")
	looped.clear()

# Regression: a successful replacement left "Movement blocked" on screen.
func _replacement_clears_rejection(model) -> void:
	_check(model.select_topology(0), "bounded profile for recovery")
	var blocked := false
	for step in 27:
		if not model.command("move_x_neg"):
			blocked = true
			break
	_check(blocked and "blocked" in model.feedback, "wall rejection shown before replacement")
	_check(model.replace_piece(2), "replacement after rejection")
	_check(model.feedback == "Replaced piece: %s. View unchanged." % model.current.piece_name, "replacement clears stale rejection")

func _check(condition: bool, message: String) -> void:
	if not condition:
		failures.append("2D Explorer: " + message)
