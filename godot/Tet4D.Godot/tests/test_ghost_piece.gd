extends RefCounted

const GhostPieceModelScript = preload("res://scripts/presentation/ghost_piece_model.gd")
const TraceReplayAppScript = preload("res://scripts/app/trace_replay_app.gd")
const TraceSceneRendererScript = preload("res://scripts/rendering/trace_scene_renderer.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")

class FakeBridge:
	extends RefCounted
	var query_count := 0
	var payload := {"ok": true, "status": "destination", "dimension": 2, "piece_name": "O", "color_id": 2, "cells": [[1, 4], [2, 4]]}
	func live_2d_hard_drop_destination() -> Dictionary:
		query_count += 1
		return payload
	func live_3d_hard_drop_destination() -> Dictionary:
		query_count += 1
		return payload
	func live_4d_hard_drop_destination() -> Dictionary:
		query_count += 1
		return payload


func run() -> Array:
	var failures: Array = []
	_test_model_and_coincident_visibility(failures)
	_test_semantic_revision_cache(failures)
	_test_live_lifecycle_and_presentation_only_cache(failures)
	await _test_immediate_renderer_replacement(failures)
	await _test_live_4d_lock_spawn_renderer_lifecycle(failures)
	await _test_renderer_and_4d_basis(failures)
	return failures


func _test_model_and_coincident_visibility(failures: Array) -> void:
	var model = GhostPieceModelScript.new()
	var payload := {"ok": true, "status": "destination", "dimension": 4, "piece_name": "FORK4", "color_id": 5, "cells": [[2, 8, 1, 1], [1, 8, 1, 1]]}
	if not model.configure(payload, "revision-a"):
		failures.append("ghost model should accept exact native 4D destination cells")
	if model.canonical_cells != [[1, 8, 1, 1], [2, 8, 1, 1]]:
		failures.append("ghost model should deterministically retain canonical board coordinates")
	var revision: int = model.geometry_revision
	model.configure(payload, "revision-b")
	if model.geometry_revision != revision:
		failures.append("unchanged ghost geometry should reuse its geometry revision")
	var active := [{"position": [1, 8, 1, 1]}, {"position": [2, 8, 1, 1]}]
	if not model.render_cells(active).is_empty():
		failures.append("ghost must hide when its landing cells coincide with the active piece")
	if model.configure({"ok": false, "status": "unavailable"}, "terminal"):
		failures.append("terminal native payload should not produce a ghost")
	if bool(model.deterministic_snapshot().get("available", true)):
		failures.append("provider failure must clear stale ghost geometry")


func _test_semantic_revision_cache(failures: Array) -> void:
	var app = TraceReplayAppScript.new()
	var bridge = FakeBridge.new()
	app._live_bridge = bridge
	app._mode = app.MODE_LIVE_2D
	app._current_snapshot = {
		"trace_type": "live_2d", "state_hash": "state-a", "game_over": false,
		"active_cells": [{"position": [1, 0], "color_id": 2}],
	}
	app._refresh_ghost_cache()
	app._refresh_ghost_cache()
	if bridge.query_count != 1 or int(app.ghost_cache_snapshot().get("query_count", 0)) != 1:
		failures.append("stable frames must not repeat the native landing query")
	app._current_snapshot["state_hash"] = "state-b"
	app._refresh_ghost_cache()
	if bridge.query_count != 2:
		failures.append("authoritative state revision should refresh the native landing query once")
	app._current_snapshot["game_over"] = true
	app._current_snapshot["state_hash"] = "terminal"
	app._refresh_ghost_cache()
	if bridge.query_count != 2 or bool(app.ghost_cache_snapshot().get("available", true)):
		failures.append("terminal states should clear the ghost without querying native semantics")
	app.free()


func _test_live_lifecycle_and_presentation_only_cache(failures: Array) -> void:
	var app = TraceReplayAppScript.new()
	var bridge = FakeBridge.new()
	app._live_bridge = bridge
	app._mode = app.MODE_LIVE_2D
	app._current_snapshot = {
		"trace_type": "live_2d", "state_hash": "before-hard-drop", "game_over": false,
		"active_cells": [{"position": [1, 0], "color_id": 2}],
	}
	bridge.payload = {"ok": true, "status": "destination", "dimension": 2, "piece_name": "O", "color_id": 2, "cells": [[1, 4], [2, 4]]}
	app._refresh_ghost_cache()
	var before_drop: Array = app._presentation_snapshot_for_render().get("ghost_cells", [])
	if before_drop.size() != 2 or not (before_drop[0].get("position", []) as Array) in [[1, 4], [2, 4]]:
		failures.append("live ghost should expose the current hard-drop destination before lock")

	# A hard drop publishes its locked result and newly spawned active piece as one
	# native snapshot.  The next semantic revision must replace, never retain, its old ghost.
	app._current_snapshot = {
		"trace_type": "live_2d", "state_hash": "after-hard-drop-new-spawn", "game_over": false,
		"active_cells": [{"position": [3, 0], "color_id": 3}],
	}
	bridge.payload = {"ok": true, "status": "destination", "dimension": 2, "piece_name": "T", "color_id": 3, "cells": [[3, 5], [4, 5]]}
	app._refresh_ghost_cache()
	var after_drop: Array = app._presentation_snapshot_for_render().get("ghost_cells", [])
	if after_drop.size() != 2 or (after_drop[0].get("position", []) as Array) in [[1, 4], [2, 4]]:
		failures.append("post-hard-drop ghost must not retain any old-piece destination cells")
	var replacement_revision := int(app.ghost_cache_snapshot().get("geometry_revision", -1))

	# Rejected gameplay commands preserve the authoritative state hash and pose, so
	# the correct existing ghost must remain visible without a replacement query.
	app._current_snapshot["last_command"] = "move_left"
	app._current_snapshot["last_command_status"] = "rejected"
	app._refresh_ghost_cache()
	if bridge.query_count != 2 or not bool(app.ghost_cache_snapshot().get("available", false)):
		failures.append("rejected movement must retain the correct cached ghost without a native requery")
	app._current_snapshot["last_command"] = "rotate_cw"
	app._refresh_ghost_cache()
	if bridge.query_count != 2 or not bool(app.ghost_cache_snapshot().get("available", false)):
		failures.append("rejected rotation must retain the correct cached ghost without a native requery")

	# A semantic state change can retain the same destination.  It still queries
	# native authority once, but must not advance ghost geometry identity.
	app._current_snapshot["state_hash"] = "after-soft-drop-same-destination"
	app._refresh_ghost_cache()
	if bridge.query_count != 3 or int(app.ghost_cache_snapshot().get("geometry_revision", -1)) != replacement_revision:
		failures.append("unchanged authoritative destination cells must not rebuild ghost geometry")

	# The visibility preference is Godot-shell presentation only: hiding it must
	# neither mutate the live snapshot nor invoke gameplay authority.
	var state_hash_before_hide := str(app._current_snapshot.get("state_hash", ""))
	app._ghost_enabled = false
	app._refresh_ghost_cache()
	if not app._presentation_snapshot_for_render().get("ghost_cells", []).is_empty() or bridge.query_count != 3 or str(app._current_snapshot.get("state_hash", "")) != state_hash_before_hide:
		failures.append("ghost.enabled must only suppress presentation, without changing gameplay state")
	app._ghost_enabled = true
	app._ghost_semantic_revision = ""
	app._refresh_ghost_cache()
	if bridge.query_count != 4 or not bool(app.ghost_cache_snapshot().get("available", false)):
		failures.append("re-enabling ghost presentation should refresh from native authority")
	app.free()


func _test_renderer_and_4d_basis(failures: Array) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		failures.append("ghost renderer test requires SceneTree")
		return
	var renderer = TraceSceneRendererScript.new()
	tree.root.add_child(renderer)
	await tree.process_frame
	var app = TraceReplayAppScript.new()
	var bridge = FakeBridge.new()
	app._live_bridge = bridge
	app._mode = app.MODE_LIVE_4D
	app._current_snapshot = {
		"case_id": "ghost_live_4d", "trace_type": "live_4d", "frame_index": 0,
		"dimension": 4, "board_shape": [5, 10, 4, 4], "locked_cells": [],
		"active_cells": [{"position": [1, 1, 1, 2], "color_id": 5}],
	}
	bridge.payload = {"ok": true, "status": "destination", "dimension": 4, "piece_name": "FORK4", "color_id": 5, "cells": [[1, 8, 1, 2]]}
	app._refresh_ghost_cache()
	var snapshot := app._presentation_snapshot_for_render()
	snapshot["probe_markers"] = []
	snapshot["event_markers"] = []
	snapshot["particles"] = []
	renderer.render_snapshot(snapshot)
	var ghost = _find_ghost(renderer)
	if ghost == null:
		failures.append("shared renderer should create presentation-only ghost geometry")
	else:
		var identity_basis = SliceBasis4DScript.identity()
		var identity_mapping: Dictionary = identity_basis.presentation_coordinate([1, 8, 1, 2], [5, 10, 4, 4])
		for plane in ["xw", "zw", "zx"]:
			var turned_basis = identity_basis.turned(plane, 1)
			var turned_mapping: Dictionary = turned_basis.presentation_coordinate([1, 8, 1, 2], [5, 10, 4, 4])
			renderer.set_live_4d_basis(turned_basis, false)
			renderer.render_snapshot(snapshot)
			ghost = _find_ghost(renderer)
			if ghost == null or identity_mapping == turned_mapping or bridge.query_count != 1 or app.ghost_cache_snapshot().get("canonical_cells", []) != [[1, 8, 1, 2]]:
				failures.append("%s view rotation should reproject cached 4D ghost geometry without a native landing query" % plane)
	app.free()
	renderer.queue_free()
	await tree.process_frame


func _test_immediate_renderer_replacement(failures: Array) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		failures.append("immediate Ghost replacement test requires SceneTree")
		return
	var renderer = TraceSceneRendererScript.new()
	tree.root.add_child(renderer)
	await tree.process_frame
	var before_lock := _renderer_snapshot(
		"before-lock",
		[],
		[[1, 7, 1, 0], [2, 7, 1, 0]],
		[[1, 2, 1, 0], [2, 2, 1, 0]],
		2
	)
	renderer.render_snapshot(before_lock)
	await tree.process_frame
	var obsolete_natural_ghosts := _nodes_for_role(renderer, "ghost")
	var after_natural_lock := _renderer_snapshot(
		"after-natural-lock",
		[[1, 8, 1, 0], [2, 8, 1, 0]],
		[[2, 6, 1, 0], [3, 6, 1, 0]],
		[[2, 1, 1, 0], [3, 1, 1, 0]],
		3
	)
	renderer.render_snapshot(after_natural_lock)
	_assert_obsolete_nodes_detached(failures, obsolete_natural_ghosts, "natural lock")
	_assert_renderer_roles_match(failures, renderer, after_natural_lock, "natural lock")
	await tree.process_frame

	var obsolete_hard_drop_ghosts := _nodes_for_role(renderer, "ghost")
	var after_hard_drop := _renderer_snapshot(
		"after-hard-drop",
		[[1, 8, 1, 0], [2, 8, 1, 0], [2, 7, 1, 0], [3, 7, 1, 0]],
		[[0, 5, 2, 1], [1, 5, 2, 1]],
		[[0, 1, 2, 1], [1, 1, 2, 1]],
		5
	)
	renderer.render_snapshot(after_hard_drop)
	_assert_obsolete_nodes_detached(failures, obsolete_hard_drop_ghosts, "hard drop")
	_assert_renderer_roles_match(failures, renderer, after_hard_drop, "hard drop")
	renderer.queue_free()
	await tree.process_frame


func _test_live_4d_lock_spawn_renderer_lifecycle(failures: Array) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		failures.append("Live-4D Ghost lifecycle test requires SceneTree")
		return
	var scene := load("res://scenes/trace_replay.tscn") as PackedScene
	if scene == null:
		failures.append("Live-4D Ghost lifecycle test requires the product scene")
		return
	var root := scene.instantiate() as Control
	tree.root.add_child(root)
	await tree.process_frame
	await tree.process_frame
	var app = root.get_node_or_null("App")
	if app == null:
		failures.append("Live-4D Ghost lifecycle test requires the app node")
		root.queue_free()
		await tree.process_frame
		return
	app._enter_live_4d_mode()
	app._live_4d_paused = true
	_assert_above_board_active_projection(failures, app, "native initial spawn")

	var natural_lock_seen := false
	for _tick_index in range(32):
		var locked_before := int(app._current_snapshot.get("locked_cells", []).size())
		var obsolete_ghosts := _nodes_for_role(app._renderer, "ghost")
		app._live_4d_command("tick")
		if app._current_snapshot.get("locked_cells", []).size() > locked_before:
			natural_lock_seen = true
			_assert_obsolete_nodes_detached(failures, obsolete_ghosts, "native natural lock")
			var natural_snapshot: Dictionary = app._presentation_snapshot_for_render()
			_assert_renderer_roles_match(failures, app._renderer, natural_snapshot, "native natural lock")
			_assert_above_board_active_projection(failures, app, "native natural spawn")
			if natural_snapshot.get("ghost_cells", []).is_empty():
				failures.append("native natural lock must publish the new piece's authoritative Ghost")
			break
	if not natural_lock_seen:
		failures.append("Live-4D natural gravity ticks must reach a lock/spawn transition")

	var hard_drop_obsolete_ghosts := _nodes_for_role(app._renderer, "ghost")
	var hard_drop_locked_before := int(app._current_snapshot.get("locked_cells", []).size())
	app._live_4d_command("hard_drop")
	if app._current_snapshot.get("locked_cells", []).size() <= hard_drop_locked_before:
		failures.append("Live-4D hard drop must publish its locked piece before renderer assertions")
	_assert_obsolete_nodes_detached(failures, hard_drop_obsolete_ghosts, "native hard drop")
	var hard_drop_snapshot: Dictionary = app._presentation_snapshot_for_render()
	_assert_renderer_roles_match(failures, app._renderer, hard_drop_snapshot, "native hard drop")
	_assert_above_board_active_projection(failures, app, "native hard-drop spawn")
	if hard_drop_snapshot.get("ghost_cells", []).is_empty():
		failures.append("native hard drop must publish the new piece's authoritative Ghost")

	var native_snapshot_before_rerender: String = app._live_bridge.live_4d_snapshot_json()
	var native_hash_before_rerender: String = str(app._live_bridge.live_4d_state_hash())
	app._renderer.render_snapshot(hard_drop_snapshot)
	if app._live_bridge.live_4d_snapshot_json() != native_snapshot_before_rerender or str(app._live_bridge.live_4d_state_hash()) != native_hash_before_rerender:
		failures.append("renderer Ghost replacement must not mutate native snapshot or state hash")
	root.queue_free()
	await tree.process_frame


func _renderer_snapshot(
	case_id: String,
	locked_positions: Array,
	ghost_positions: Array,
	active_positions: Array,
	color_id: int
) -> Dictionary:
	return {
		"case_id": case_id,
		"trace_type": "live_4d",
		"frame_index": 0,
		"dimension": 4,
		"board_shape": [5, 10, 4, 4],
		"locked_cells": _cells(locked_positions, color_id),
		"ghost_cells": _cells(ghost_positions, color_id),
		"active_cells": _cells(active_positions, color_id),
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	}


func _cells(positions: Array, color_id: int) -> Array:
	var cells: Array = []
	for position in positions:
		cells.append({"position": position.duplicate(), "color_id": color_id})
	return cells


func _nodes_for_role(renderer, role: String) -> Array:
	var nodes: Array = []
	var root = renderer.get_node_or_null("CellRoot")
	if root == null:
		return nodes
	for child in root.get_children():
		if str(child.get_meta("presentation_role", "")) == role:
			nodes.append(child)
	return nodes


func _assert_obsolete_nodes_detached(failures: Array, obsolete_nodes: Array, label: String) -> void:
	for node in obsolete_nodes:
		if is_instance_valid(node) and node.get_parent() != null:
			failures.append("%s must synchronously detach obsolete Ghost geometry" % label)
			return


func _assert_renderer_roles_match(failures: Array, renderer, snapshot: Dictionary, label: String) -> void:
	for role in ["locked", "ghost", "active"]:
		var expected_key := "%s_cells" % role
		var expected := _canonical_position_keys(snapshot.get(expected_key, []))
		var actual: Array = []
		for node in _nodes_for_role(renderer, role):
			actual.append(str(node.get_meta("canonical_position", [])))
		actual.sort()
		if actual != expected:
			failures.append("%s rendered %s set must immediately match authoritative presentation: expected %s got %s" % [label, role, expected, actual])


func _canonical_position_keys(cells: Array) -> Array:
	var keys: Array = []
	for cell in cells:
		keys.append(str(cell.get("position", [])))
	keys.sort()
	return keys


func _assert_above_board_active_projection(failures: Array, app, label: String) -> void:
	var above_board_nodes: Array = []
	var rendered_positions := {}
	for node in _nodes_for_role(app._renderer, "active"):
		var canonical: Array = node.get_meta("canonical_position", [])
		if canonical.size() < 4 or float(canonical[1]) >= 0.0:
			continue
		above_board_nodes.append(node)
		if node.position.is_equal_approx(Vector3.ZERO):
			failures.append("%s must not collapse an above-board active cell to the renderer origin" % label)
		rendered_positions[str(node.position)] = true
	if above_board_nodes.is_empty():
		failures.append("%s must exercise native above-board active coordinates" % label)
	elif rendered_positions.size() != above_board_nodes.size():
		failures.append("%s must map distinct above-board active cells to distinct rendered points" % label)


func _find_ghost(renderer) -> Node3D:
	var root = renderer.get_node_or_null("CellRoot")
	if root == null:
		return null
	for child in root.get_children():
		if child.has_meta("presentation_role") and str(child.get_meta("presentation_role")) == "ghost":
			return child as Node3D
	return null
