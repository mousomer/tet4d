extends RefCounted

const BoardPresentationModelScript = preload("res://scripts/presentation/board_presentation_model.gd")


func run() -> Array:
	var failures: Array = []
	var model := BoardPresentationModelScript.new()
	model.configure({
		"trace_type": "live_3d",
		"dimension": 3,
		"board_shape": [4, 5, 6],
		"locked_cells": [{"position": [1, 4, 2]}],
		"active_cells": [{"position": [2, 1, 3]}],
		"probe_markers": [{"position": [0, 0, 0]}],
		"event_markers": [{"position": [3, 4, 5]}],
		"particles": [{"position": [1, 2, 3]}],
	})
	if not model.is_live:
		failures.append("presentation model should classify live snapshots")
	if not model.is_live_3d:
		failures.append("presentation model should classify live 3D snapshots")
	if not model.current_bounds().get("ok", false):
		failures.append("presentation model should expose projected board bounds")
	if model.locked_cells().size() != 1 or model.active_cells().size() != 1:
		failures.append("presentation model should expose renderable cell collections")
	var position := model.world_position([0, 0, 0])
	if position.distance_to(Vector3(-1.5, 2.0, -2.5)) > 0.001:
		failures.append("presentation model should use the canonical mapper, got %s" % str(position))
	var live_4d_model := BoardPresentationModelScript.new()
	live_4d_model.configure({
		"trace_type": "live_4d",
		"dimension": 4,
		"board_shape": [5, 10, 4, 4],
		"locked_cells": [{"position": [1, 4, 2, 0]}],
		"active_cells": [{"position": [2, 1, 3, 1]}],
		"probe_markers": [],
		"event_markers": [],
		"particles": [],
	})
	if not live_4d_model.is_live:
		failures.append("presentation model should classify live 4D snapshots as live")
	if live_4d_model.is_live_3d:
		failures.append("presentation model should not classify live 4D snapshots as live 3D")
	if not live_4d_model.is_live_4d:
		failures.append("presentation model should classify live 4D snapshots as live 4D")
	if not live_4d_model.uses_live_exterior_cells:
		failures.append("presentation model should give live 4D exterior cell grammar")
	if not live_4d_model.current_bounds().get("ok", false):
		failures.append("presentation model should expose projected live 4D board bounds")
	var w0_position := live_4d_model.world_position([0, 0, 0, 0])
	var w1_position := live_4d_model.world_position([0, 0, 0, 1])
	if w1_position.x <= w0_position.x:
		failures.append("presentation model should separate W slices side-by-side")
	return failures
