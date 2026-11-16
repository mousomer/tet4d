extends RefCounted

var failures: Array = []


func check(condition: bool, message: String) -> void:
	if not condition: failures.append("Explorer surfaces: " + message)


func run() -> Array:
	var bridge = preload("res://scripts/native/tet4d_core_bridge.gd").new()
	var profile: Dictionary = preload("res://scripts/input/live_input_contract.gd").explorer_profile(2)
	var spheres: Array = profile.topologies.filter(func(item): return item.label == "Sphere")
	check(spheres.size() == 1 and spheres[0].id == "sphere_adjacent_positive" and not spheres[0].disabled, "normal Sphere selector uses positive adjacent-edge profile")
	_check_named_seams(bridge)
	_check_board_axis_trajectories(bridge)
	_check_surface_annotations(bridge)
	var original := [[0, 1], [0, 2]]
	for preset in ["mobius", "klein", "projective", "sphere_double_2d"]:
		var admitted: Dictionary = bridge.explorer_begin([4, 4], original, original, preset)
		check(admitted.get("ok", false), preset + " admitted")
		var moved: Dictionary = bridge.explorer_move(0, -1)
		check(moved.get("ok", false) and moved.cell_ids == [0, 1], preset + " stable IDs across seam")
		if preset == "sphere_double_2d":
			check(moved.cells == original and moved.domains == [1, 1], "sphere crossing changes domain without inventing coordinates")
			check(moved.display_cells == [[5, 1], [5, 2]] and moved.display_shape == [9, 4], "sphere charts have distinct native display positions")
			check(moved.version == "explorer-piece-domains/2", "sphere version is distinct from historical single-domain profiles")
		elif preset == "klein":
			check(moved.cells == [[3, 1], [3, 2]], "Klein X pair preserves tangent")
		else:
			check(moved.cells == [[3, 2], [3, 1]], preset + " X pair reverses tangent")
		var neighbors: Dictionary = bridge.explorer_neighbors(0)
		check(neighbors.get("ok", false) and neighbors.neighbors.size() == 4, preset + " native directional neighbors")
		var undone: Dictionary = bridge.explorer_undo()
		check(undone.get("ok", false) and undone.cells == original and undone.domains == [0, 0] and undone.pristine, preset + " recorded undo restores complete material baseline")
		check(undone.frames == admitted.frames, preset + " inverse restores all frames")
		# Result arrays are detached; corrupting one cannot mutate the runtime.
		undone.cells[0][0] = 99
		check(bridge.explorer_retry().cells == original, preset + " bridge returns detached values")
		var interior := [[1, 1], [1, 2]]
		bridge.explorer_begin([4, 4], interior, interior, preset)
		for turn in 4:
			check(bridge.explorer_rotate(1).get("ok", false), preset + " coherent rotation")
		var restored: Dictionary = bridge.explorer_undo()
		check(restored.get("ok", false), preset + " recorded rotation inverse")
		check(bridge.explorer_retry().cells == interior, preset + " Retry after rotations")
	check(not bridge.explorer_neighbors(-1).get("ok", true), "invalid neighbor ID rejected")
	check(not bridge.explorer_rotate(0).get("ok", true), "invalid rotation rejected")
	var Practice = preload("res://scripts/presentation/practice_explorer.gd")
	var model = Practice.new(bridge)
	check(model.begin({"board_shape": [4, 4], "active_cells": [{"position": [0, 1]}, {"position": [0, 2]}]}), "model initializes")
	check(model.select_topology("sphere_double_2d"), "model selects genuine sphere")
	for step in 4:
		if model.domains == [1, 1]: break
		check(model.command("move_x_neg"), "model crosses spherical boundary")
	var sphere_pose: Array = model.cells.duplicate(true)
	check(not model.select_topology("unknown") and model.topology == "sphere_double_2d" and model.cells == sphere_pose, "rejected profile selection preserves domain pose")
	var baseline: Array = model._initial.duplicate(true)
	check(model.select_topology("klein") and model.topology == "klein" and model.cells == baseline and model.domains == [0, 0], "cross-domain selection atomically restores the Retry baseline")
	check(model.feedback.contains("Retry pose restored"), "cross-domain recovery explains the pose restoration")
	check(model.select_topology("sphere_double_2d"), "surface selection remains available after recovery")
	for step in 4:
		if model.domains == [1, 1]: break
		model.command("move_x_neg")
	var snapshot: Dictionary = model.snapshot(true, 2, -1)
	check(snapshot.board_shape == [9, 4] and snapshot.explorer_charts.count == 2, "sphere snapshot exposes both chart bounds")
	check(snapshot.active_cells[0].position[0] >= 5, "sphere cell is drawn in chart B")
	model.retry()
	check(model.command("move_x_neg") and model.command("undo"), "model exposes recorded undo")
	check(model.select_topology("projective"), "pristine profile may switch")
	check("experimental" in model.topology_note(), "projective name retains certification boundary")
	_check_move_rules(bridge)
	return failures


# Free-cellwise board-axis traversal supersedes material-frame rigidity expectations.
# tet4d-semantic-boundary: allow test-fixture
func _check_move_rules(bridge) -> void:
	var fold := [[0, 0], [1, 0]]
	check(bridge.explorer_begin([4, 4], fold, fold, "sphere_adjacent_positive").get("ok", false), "sphere fold admits a corner domino")
	var collapsed: Dictionary = bridge.explorer_move(0, -1)
	check(not collapsed.get("ok", true) and collapsed.get("reason", "") == "destination_collision", "sphere corner refuses two cells on one site")
	var straddle := [[0, 1], [1, 1]]
	check(bridge.explorer_begin([4, 4], straddle, straddle, "mobius").get("ok", false), "Mobius admits a horizontal domino")
	var across: Dictionary = bridge.explorer_move(0, -1)
	check(across.get("ok", false) and across.cells == [[3, 2], [0, 1]], "domino straddles the flipped seam")
	var up: Dictionary = bridge.explorer_move(1, -1)
	check(up.get("ok", false) and up.cells == [[3, 1], [0, 0]], "straddling domino follows the same board Up on both sides")
	var turned: Dictionary = bridge.explorer_rotate(1)
	check(turned.get("ok", false), "straddling domino turns across the seam")
	var open_edge := [[1, 0], [2, 0]]
	check(bridge.explorer_begin([4, 4], open_edge, open_edge, "mobius").get("ok", false), "Mobius admits a top-row domino")
	var blocked: Dictionary = bridge.explorer_move(1, -1)
	check(not blocked.get("ok", true) and blocked.get("reason", "") == "unconnected_boundary", "Mobius open edge refuses the move")
	for preset in ["klein", "projective", "sphere_adjacent_positive"]:
		var interior := [[1, 1], [2, 1], [1, 2]]
		check(bridge.explorer_begin([4, 4], interior, interior, preset).get("ok", false), preset + " admits an L")
		for step in 6:
			var moved: Dictionary = bridge.explorer_move(0, -1)
			if moved.get("ok", false):
				var sites := {}
				for index in moved.cells.size():
					sites["%d:%s" % [moved.domains[index], str(moved.cells[index])]] = true
				check(sites.size() == moved.cells.size(), preset + " never stacks cells")
			else:
				check(moved.get("reason", "") in ["destination_collision", "unconnected_boundary"], preset + " refuses only overlap or open edges")


# Expected coordinates come directly from the prescribed natural edge parameters.
# Each signed boundary exercises the actual native bridge used by Explorer.
# tet4d-semantic-boundary: allow test-fixture
func _check_named_seams(bridge) -> void:
	for preset in ["klein", "projective", "sphere_adjacent_positive"]:
		for axis in [0, 1]:
			for delta in [-1, 1]:
				for tangent in [0, 1, 2, 3]:
					var source := [0, 0]
					source[axis] = 0 if delta < 0 else 3
					source[1 - axis] = tangent
					var admitted: Dictionary = bridge.explorer_begin([4, 4], [source], [source], preset)
					check(admitted.get("ok", false), preset + " signed boundary admitted")
					if not admitted.get("ok", false): continue
					var expected := [0, 0]
					var expected_permutation := [0, 1]
					var expected_signs := [1, 1]
					if preset == "sphere_adjacent_positive":
						expected[axis] = tangent
						expected[1 - axis] = 0 if delta < 0 else 3
						expected_permutation = [1, 0]
						expected_signs[axis] = -1
					else:
						expected[axis] = 3 if delta < 0 else 0
						var reversed_tangent: bool = preset == "projective" or axis == 1
						expected[1 - axis] = 3 - tangent if reversed_tangent else tangent
						if reversed_tangent: expected_signs[1 - axis] = -1
					var moved: Dictionary = bridge.explorer_move(axis, delta)
					check(moved.get("ok", false), preset + " signed seam traversed")
					if not moved.get("ok", false): continue
					check(moved.cells == [expected] and moved.domains == [0], preset + " quotient boundary coordinate")
					check(moved.frames[0].permutation == expected_permutation and moved.frames[0].signs == expected_signs, preset + " seam tangent/frame agrees")
	var Practice = preload("res://scripts/presentation/practice_explorer.gd")
	for preset in ["klein", "projective", "sphere_adjacent_positive"]:
		var model = Practice.new(bridge)
		check(model.begin({"board_shape": [4, 4], "active_cells": [{"position": [1, 1]}]}), "selected-profile model begins")
		check(model.select_topology(preset) and model.topology == preset, preset + " selected by Explorer")
		check(model.command("move_x_neg") and model.command("move_x_neg"), preset + " Explorer command reaches selected seam")
		var expected: Array = [[1, 0]] if preset == "sphere_adjacent_positive" else ([[3, 2]] if preset == "projective" else [[3, 1]])
		check(model.cells == expected, preset + " Explorer selected-profile destination")


# Normative pairings are supplied by the bridge, independently of UI preset names.
# tet4d-semantic-boundary: allow test-fixture
func _check_surface_annotations(bridge) -> void:
	var expected := {
		"sphere_adjacent_positive": [[0, -1, 1, -1, 1], [0, 1, 1, 1, 1]],
		"projective": [[0, -1, 0, 1, -1], [1, -1, 1, 1, -1]],
	}
	for side in [5, 6]:
		for preset in expected:
			var admitted: Dictionary = bridge.explorer_begin([side, side], [[1, 1]], [[1, 1]], preset)
			check(admitted.get("ok", false), "square surface admits odd/even extents")
			if not admitted.get("ok", false): continue
			check(not bridge.explorer_begin([side, side + 1], [[1, 1]], [[1, 1]], preset).get("ok", true), "native named surface rejects a rectangle")
			check(bridge.explorer_retry().cells == admitted.cells, "rejected rectangle preserves native state")
			var snapshot := {"dimension": 2, "trace_type": "live_2d", "board_shape": [side, side], "explorer_seams": admitted.seams}
			var model = preload("res://scripts/presentation/board_presentation_model.gd").new()
			model.configure(snapshot)
			var annotations = preload("res://scripts/rendering/explorer_seam_annotations.gd").new()
			annotations.rebuild(snapshot, model, "plain")
			check(annotations.visible and annotations.get_child_count() == 4, "all four paired edges stay annotated without crossing or diagnostics")
			for index in admitted.seams.size():
				var seam: Dictionary = admitted.seams[index]
				check([seam.source_axis, seam.source_side, seam.target_axis, seam.target_side, seam.tangent_sign] == expected[preset][index], preset + " annotations use exact native directed pairing")
				var source = annotations.get_node("Seam_%d_source" % index)
				var destination = annotations.get_node("Seam_%d_target" % index)
				check(source.get_node("PairLabel").text == destination.get_node("PairLabel").text, "pair labels remain identifiable without colour")
				check(destination.get_meta("tangent_sign") == seam.tangent_sign, "arrow direction reads native tangent sign")
				check(source.get_child(0).mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].size() == 8, "edge and arrowhead geometry is present")
			var generation: int = annotations.generation
			annotations.rebuild(snapshot, model, "plain")
			check(annotations.generation == generation, "normal movement retains annotation nodes")
			annotations.rebuild({"dimension": 2, "board_shape": [side, side]}, model, "plain")
			check(not annotations.visible and annotations.get_child_count() == 0, "leaving identified surfaces removes annotations")
			annotations.free()


# Owner reference coordinates: 1-based Sphere (3,1)->(1,3)->(1,2),
# RP2 (3,1)->(6,8)->(6,7); tests below are engine coordinates.
# tet4d-semantic-boundary: allow test-fixture
func _check_board_axis_trajectories(bridge) -> void:
	var expectations := {
		"sphere_adjacent_positive": [[0, 2], [0, 1]],
		"projective": [[5, 7], [5, 6]],
	}
	for preset in expectations:
		var start := [[2, 0], [2, 1]]
		var admitted: Dictionary = bridge.explorer_begin([8, 8], start, start, preset)
		check(admitted.get("ok", false), preset + " reference domino admitted")
		var first: Dictionary = bridge.explorer_move(1, -1)
		check(first.get("ok", false) and first.get("classification") == "cellwise_deformation" and first.cells == [expectations[preset][0], [2, 0]], preset + " mixed seam/interior Up deforms independently")
		var second: Dictionary = bridge.explorer_move(1, -1)
		check(second.get("ok", false) and second.cells == [expectations[preset][1], expectations[preset][0]], preset + " second Up remains board Y minus")
		bridge.explorer_undo()
		var restored: Dictionary = bridge.explorer_undo()
		check(restored.get("ok", false) and restored.cells == admitted.cells and restored.frames == admitted.frames and restored.cell_ids == admitted.cell_ids, preset + " deformation Undo restores positions, frames and IDs")
		# Production model forwards and renders native coordinates without shape repair.
		var model = preload("res://scripts/presentation/practice_explorer.gd").new(bridge)
		check(model.begin({"dimension": 2, "board_shape": [8, 8], "active_cells": [{"position": [2, 0]}, {"position": [2, 1]}]}), "reference model begins")
		check(model.select_topology(preset), "reference surface selectable")
		# Native begin establishes the literal reference pose; accept its detached result.
		model._accept_transport(bridge.explorer_begin([8, 8], start, start, preset))
		check(model.command("move_y_neg") and model.command("move_y_neg"), "model uses canonical board action")
		var snapshot: Dictionary = model.snapshot(false, 2, -1)
		check(snapshot.active_cells.map(func(cell): return cell.position) == [expectations[preset][1], expectations[preset][0]], "renderer snapshot exposes deformed cell coordinates directly")
