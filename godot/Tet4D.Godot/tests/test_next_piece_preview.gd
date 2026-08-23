extends RefCounted

const PieceThumbnailModelScript = preload("res://scripts/ui/pieces/piece_thumbnail_model.gd")
const PieceThumbnailScript = preload("res://scripts/ui/pieces/piece_thumbnail.gd")
const NextPiecePanelScript = preload("res://scripts/ui/pieces/next_piece_panel.gd")
const HoldPiecePanelScript = preload("res://scripts/ui/pieces/hold_piece_panel.gd")
const Tet4DCoreBridgeScript = preload("res://scripts/native/tet4d_core_bridge.gd")
const GameSetupSpecScript = preload("res://scripts/ui/game_setup/game_setup_spec.gd")


func run() -> Array:
	var failures: Array = []
	_test_model_validation_and_dimensions(failures)
	_test_isometric_face_adjacency(failures)
	_test_shared_panel_renderer(failures)
	_test_hold_panel_reuses_preview_pipeline(failures)
	_test_exhaustive_production_geometry(failures)
	_test_queue_identity_and_update(failures)
	return failures


func _test_model_validation_and_dimensions(failures: Array) -> void:
	var model = PieceThumbnailModelScript.new()
	if not model.configure({
		"ok": true,
		"status": "piece",
		"dimension": 2,
		"piece_set_id": "classic",
		"piece_name": "T",
		"color_id": 3,
		"cells": [[-1, 0], [0, 0], [1, 0], [0, 1]],
	}):
		failures.append("2D native preview payload should configure the shared thumbnail model")
	var snapshot: Dictionary = model.deterministic_snapshot()
	if snapshot.get("canonical_cells") != [[-1, 0], [0, 0], [0, 1], [1, 0]]:
		failures.append("thumbnail model should retain deterministic canonical 2D cells")
	if snapshot.get("drawing_groups", []).size() != 1:
		failures.append("2D thumbnail should use one shared drawing group")

	if not model.configure({
		"ok": true,
		"status": "piece",
		"dimension": 3,
		"piece_set_id": "native_3d",
		"piece_name": "SCREW3",
		"color_id": 7,
		"cells": [[0, 0, 0], [1, 0, 0], [1, 1, 0], [1, 1, 1]],
	}):
		failures.append("3D native preview payload should configure the shared thumbnail model")
	if model.drawing_groups().size() != 1 or model.canonical_cells[3].size() != 3:
		failures.append("3D thumbnail should retain XYZ geometry in one isometric group")

	if not model.configure({
		"ok": true,
		"status": "piece",
		"dimension": 4,
		"piece_set_id": "standard_4d_5",
		"piece_name": "CROSS4",
		"color_id": 1,
		"cells": [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
	}):
		failures.append("4D native preview payload should configure the shared thumbnail model")
	var groups: Array = model.drawing_groups()
	if groups.size() != 2:
		failures.append("4D thumbnail should decompose geometry into ordered W slices")
	elif str(groups[0].get("label")) != "W=+0" or str(groups[1].get("label")) != "W=+1":
		failures.append("4D thumbnail W slices should retain explicit signed canonical labels")
	if model.deterministic_snapshot().get("canonical_cells", []).size() != 5:
		failures.append("4D thumbnail should retain all canonical four-coordinate cells")

	for invalid in [
		{},
		{"ok": false, "status": "failure"},
		{"ok": true, "status": "piece", "dimension": 5, "piece_set_id": "bad", "piece_name": "bad", "color_id": 1, "cells": [[0, 0, 0, 0, 0]]},
		{"ok": true, "status": "piece", "dimension": 3, "piece_set_id": "native_3d", "piece_name": "bad", "color_id": 1, "cells": [[0, 0]]},
		{"ok": true, "status": "piece", "dimension": 2, "piece_set_id": "classic", "piece_name": "bad", "color_id": 1, "cells": [[0, 0], [0, 0]]},
	]:
		if model.configure(invalid):
			failures.append("thumbnail model should reject malformed or duplicate native geometry")


func _test_shared_panel_renderer(failures: Array) -> void:
	var panel = NextPiecePanelScript.new()
	var renderer = panel.find_child("PieceThumbnail", true, false)
	if renderer == null:
		failures.append("NEXT panel should contain the shared PieceThumbnail renderer")
		return
	var preview_2d := {"ok": true, "status": "piece", "dimension": 2, "piece_set_id": "classic", "piece_name": "O", "color_id": 2, "cells": [[0, 0], [1, 0], [0, 1], [1, 1]]}
	if not panel.set_preview(preview_2d):
		failures.append("NEXT panel should accept a valid 2D preview")
	var snapshot: Dictionary = panel.deterministic_snapshot()
	if snapshot.get("piece_name_text") != "O" or snapshot.get("thumbnail", {}).get("render_mode") != "xy":
		failures.append("NEXT panel should label and render the exact 2D piece")
	var stable_geometry_revision := int(snapshot.get("thumbnail", {}).get("geometry_revision", -1))
	if not panel.set_preview(preview_2d) or int(panel.deterministic_snapshot().get("thumbnail", {}).get("geometry_revision", -2)) != stable_geometry_revision:
		failures.append("identical preview refreshes should reuse cached thumbnail geometry")
	var style_revision := int(panel.deterministic_snapshot().get("thumbnail", {}).get("style_revision", -1))
	panel.set_style_manager(null)
	snapshot = panel.deterministic_snapshot()
	if int(snapshot.get("thumbnail", {}).get("style_revision", -2)) <= style_revision or int(snapshot.get("thumbnail", {}).get("geometry_revision", -2)) != stable_geometry_revision:
		failures.append("style/accessibility invalidation should redraw without rebuilding geometry")
	var renderer_id := renderer.get_instance_id()
	if not panel.set_preview({"ok": true, "status": "piece", "dimension": 4, "piece_set_id": "standard_4d_5", "piece_name": "CROSS4", "color_id": 1, "cells": [[0, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]}):
		failures.append("NEXT panel should accept a valid 4D preview")
	snapshot = panel.deterministic_snapshot()
	if renderer.get_instance_id() != renderer_id:
		failures.append("2D and 4D previews should reuse one renderer instance suitable for Hold")
	if snapshot.get("thumbnail", {}).get("render_mode") != "w_sliced_xyz_isometric" or snapshot.get("thumbnail", {}).get("group_count") != 2:
		failures.append("NEXT panel should render compact W-sliced 4D geometry")
	if not str(snapshot.get("status_text", "")).contains("5 cells"):
		failures.append("NEXT panel should retain a non-colour cell-count cue")
	if panel.set_preview({"ok": false, "status": "failure"}):
		failures.append("provider failure should not report a usable NEXT preview")
	snapshot = panel.deterministic_snapshot()
	if bool(snapshot.get("model", {}).get("available", true)) or snapshot.get("piece_name_text") != "—" or snapshot.get("status_text") != "Preview unavailable":
		failures.append("provider failure should clear stale geometry and show bounded unavailable state")
	panel.free()


func _test_hold_panel_reuses_preview_pipeline(failures: Array) -> void:
	var panel = HoldPiecePanelScript.new()
	if not panel.set_hold_state({}, true):
		failures.append("intentional empty HOLD state should be valid")
	var snapshot: Dictionary = panel.deterministic_snapshot()
	if snapshot.get("piece_name_text") != "EMPTY" or snapshot.get("status_text") != "Available · C":
		failures.append("empty HOLD must use intentional product language and the shared binding")
	var fork4 := {"ok": true, "status": "piece", "dimension": 4, "piece_set_id": "standard_4d_5", "piece_name": "FORK4", "color_id": 7, "cells": [[0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]]}
	if not panel.set_hold_state(fork4, false):
		failures.append("HOLD must accept authoritative production preview payloads")
	snapshot = panel.deterministic_snapshot()
	if snapshot.get("piece_name_text") != "FORK4" or snapshot.get("status_text") != "Used until lock" or bool(snapshot.get("available", true)):
		failures.append("populated unavailable HOLD must expose identity and redundant text status")
	if snapshot.get("thumbnail", {}).get("render_mode") != "w_sliced_xyz_isometric" or snapshot.get("thumbnail", {}).get("group_count") != 2:
		failures.append("HOLD must reuse the accepted shared cross-W thumbnail renderer")
	panel.free()


func _test_isometric_face_adjacency(failures: Array) -> void:
	var renderer = PieceThumbnailScript.new()
	var origin: Vector2 = renderer.isometric_cell_center([0, 0, 0])
	var x_step: Vector2 = renderer.isometric_cell_center([1, 0, 0]) - origin
	var y_step: Vector2 = renderer.isometric_cell_center([0, 1, 0]) - origin
	var z_step: Vector2 = renderer.isometric_cell_center([0, 0, 1]) - origin
	var expected_x := Vector2(PieceThumbnailScript.ISOMETRIC_HALF_WIDTH, PieceThumbnailScript.ISOMETRIC_HALF_HEIGHT)
	var expected_y := Vector2(0.0, PieceThumbnailScript.ISOMETRIC_DEPTH)
	var expected_z := Vector2(-PieceThumbnailScript.ISOMETRIC_HALF_WIDTH, PieceThumbnailScript.ISOMETRIC_HALF_HEIGHT)
	if not x_step.is_equal_approx(expected_x):
		failures.append("isometric NEXT X-neighbours must share one cube-face edge")
	if not y_step.is_equal_approx(expected_y):
		failures.append("isometric NEXT Y-neighbours must stack without a background gap")
	if not z_step.is_equal_approx(expected_z):
		failures.append("isometric NEXT Z-neighbours must share one cube-face edge")
	renderer.free()


func _test_exhaustive_production_geometry(failures: Array) -> void:
	var bridge = Tet4DCoreBridgeScript.new()
	var catalog: Array = bridge.live_nd_production_piece_catalog()
	if catalog.is_empty():
		failures.append("production NEXT geometry catalogue must be observable for exhaustive conformance")
		return
	var seen: Dictionary = {}
	var counts := {3: 0, 4: 0}
	var fork_payload: Dictionary = {}
	for value in catalog:
		if not value is Dictionary:
			failures.append("production NEXT catalogue entries must be structured preview payloads")
			continue
		var payload: Dictionary = value
		var dimension := int(payload.get("dimension", 0))
		var identity := "%d:%s:%s" % [dimension, str(payload.get("piece_set_id", "")), str(payload.get("piece_name", ""))]
		if seen.has(identity):
			failures.append("production NEXT catalogue identity must be unique: %s" % identity)
			continue
		seen[identity] = true
		if not counts.has(dimension):
			failures.append("production NEXT catalogue contains unsupported dimension: %s" % identity)
			continue
		counts[dimension] = int(counts[dimension]) + 1
		_assert_production_payload_geometry(failures, payload, identity)
		if identity == "4:standard_4d_5:FORK4":
			fork_payload = payload
	if int(counts[3]) == 0 or int(counts[4]) == 0:
		failures.append("exhaustive NEXT conformance must enumerate both 3D and 4D production geometry")
	if fork_payload.is_empty():
		failures.append("FORK4 must remain present in the production registry")
	else:
		_assert_fork4_regression(failures, fork_payload)


func _assert_production_payload_geometry(failures: Array, payload: Dictionary, identity: String) -> void:
	var dimension := int(payload.get("dimension", 0))
	var authoritative := _canonical_cells(payload.get("cells", []), dimension)
	if authoritative.size() != payload.get("cells", []).size():
		failures.append("%s authoritative cells must be unique and rank-correct" % identity)
		return
	var model = PieceThumbnailModelScript.new()
	if not model.configure(payload):
		failures.append("%s must configure the production thumbnail model" % identity)
		return
	var modeled := _canonical_cells(model.canonical_cells, dimension)
	if model.canonical_cells.size() != authoritative.size():
		failures.append("%s model must retain exactly one entry per authoritative cell" % identity)
	_assert_same_geometry(failures, authoritative, modeled, dimension, "%s model" % identity)
	_assert_embedding(failures, authoritative, dimension, str(payload.get("piece_set_id", "")), identity)

	var groups: Array = model.drawing_groups()
	var modeled_from_groups: Array = []
	var occupied_w: Dictionary = {}
	for group in groups:
		var w := int(group.get("slice_coordinate", 0))
		if dimension == 4:
			occupied_w[w] = true
		for cell in group.get("cells", []):
			var reconstructed: Array = _integer_cell(cell)
			if dimension == 4:
				reconstructed.append(w)
			modeled_from_groups.append(reconstructed)
	var authoritative_w: Dictionary = {}
	if dimension == 4:
		for cell in authoritative:
			authoritative_w[int(cell[3])] = true
	if dimension == 4 and (groups.size() != occupied_w.size() or groups.size() != authoritative_w.size()):
		failures.append("%s must instantiate exactly one group per occupied W coordinate" % identity)
	if modeled_from_groups.size() != authoritative.size():
		failures.append("%s grouped model must retain exactly one entry per authoritative cell" % identity)
	_assert_same_geometry(failures, authoritative, _canonical_cells(modeled_from_groups, dimension), dimension, "%s grouped model" % identity)

	var renderer = PieceThumbnailScript.new()
	renderer.set_model(model)
	var plan: Dictionary = renderer.renderer_plan(Vector2(360.0, 160.0 if dimension == 4 else 132.0))
	var rendered: Array = []
	var shared_origin_set := false
	var shared_origin := Vector2.ZERO
	var shared_unit := -1.0
	for group in plan.get("groups", []):
		var w := int(group.get("slice_coordinate", 0))
		var drawing_rect: Rect2 = group.get("drawing_rect", Rect2())
		for rendered_cell in group.get("rendered_cells", []):
			var reconstructed: Array = _integer_cell(rendered_cell.get("coordinate", []))
			if dimension == 4:
				reconstructed.append(w)
			rendered.append(reconstructed)
			var unit := float(rendered_cell.get("unit", -1.0))
			if shared_unit < 0.0:
				shared_unit = unit
			elif not is_equal_approx(unit, shared_unit):
				failures.append("%s renderer must apply one uniform scale to the complete piece" % identity)
			var projected: Vector2 = rendered_cell.get("projected_coordinate", Vector2.ZERO)
			var pane_local_center: Vector2 = rendered_cell.get("pane_local_center", Vector2.ZERO)
			var origin := pane_local_center - projected * unit
			if not shared_origin_set:
				shared_origin = origin
				shared_origin_set = true
			elif not origin.is_equal_approx(shared_origin):
				failures.append("%s renderer must not independently re-center W groups" % identity)
			_assert_cube_visible(failures, rendered_cell, drawing_rect, identity)
	if rendered.size() != authoritative.size():
		failures.append("%s renderer must instantiate exactly one entry per authoritative cell" % identity)
	_assert_same_geometry(failures, authoritative, _canonical_cells(rendered, dimension), dimension, "%s renderer" % identity)
	if plan.get("groups", []).size() != groups.size():
		failures.append("%s renderer must instantiate every structural group" % identity)
	renderer.free()


func _assert_fork4_regression(failures: Array, payload: Dictionary) -> void:
	var expected := _canonical_cells([
		[-1, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0],
		[0, 0, 1, 1], [0, 1, 0, 1],
	], 4)
	var actual := _canonical_cells(payload.get("cells", []), 4)
	if actual != expected:
		failures.append("FORK4 production coordinates changed; NEXT must not substitute display geometry")
		return
	var model = PieceThumbnailModelScript.new()
	if not model.configure(payload):
		failures.append("FORK4 must configure the thumbnail model")
		return
	var groups: Array = model.drawing_groups()
	if groups.size() != 2:
		failures.append("FORK4 must retain its two authoritative W groups")
		return
	if _canonical_cells(groups[0].get("cells", []), 3) != [[-1, 0, 0], [0, 0, 0], [1, 0, 0]]:
		failures.append("FORK4 W=0 must retain the authoritative X bar")
	if _canonical_cells(groups[1].get("cells", []), 3) != [[0, 0, 1], [0, 1, 0]]:
		failures.append("FORK4 W=1 must retain its authoritative shared-origin Z/Y offset coordinates")


func _test_queue_identity_and_update(failures: Array) -> void:
	var bridge = Tet4DCoreBridgeScript.new()
	var catalog_by_identity: Dictionary = {}
	for value in bridge.live_nd_production_piece_catalog():
		if value is Dictionary:
			var payload: Dictionary = value
			catalog_by_identity[_payload_identity(payload)] = payload
	var cases := [
		[3, "embedded_2d", [6, 10, 6]],
		[3, "native_3d", [6, 10, 6]],
		[4, "embedded_2d", [5, 10, 4, 4]],
		[4, "embedded_3d", [5, 10, 4, 4]],
		[4, "standard_4d_5", [5, 10, 4, 4]],
	]
	for case in cases:
		var dimension := int(case[0])
		var piece_set_id := str(case[1])
		var shape: Array = case[2]
		var mode := "live_%dd" % dimension
		var setup := _setup(mode, "next_geometry_test", shape, piece_set_id, 1337, 1)
		var configured: bool = bridge.live_3d_configure(setup) if dimension == 3 else bridge.live_4d_configure(setup)
		if not configured:
			failures.append("%s queue-identity fixture must configure" % piece_set_id)
			continue
		_assert_live_queue_preview(failures, bridge, catalog_by_identity, dimension, piece_set_id, "initial")
		var initial_snapshot = JSON.parse_string(bridge.live_3d_snapshot_json() if dimension == 3 else bridge.live_4d_snapshot_json())
		var initial_active := str(initial_snapshot.get("current_piece", "")) if initial_snapshot is Dictionary else ""
		var first_next: Dictionary = bridge.live_3d_next_piece_preview() if dimension == 3 else bridge.live_4d_next_piece_preview()
		if dimension == 3:
			bridge.live_3d_apply_command("hold")
		else:
			bridge.live_4d_apply_command("hold")
		var held: Dictionary = bridge.live_3d_held_piece_preview() if dimension == 3 else bridge.live_4d_held_piece_preview()
		var available: bool = bridge.live_3d_hold_available() if dimension == 3 else bridge.live_4d_hold_available()
		var after_hold = JSON.parse_string(bridge.live_3d_snapshot_json() if dimension == 3 else bridge.live_4d_snapshot_json())
		if str(held.get("piece_name", "")) != initial_active or not after_hold is Dictionary or str(after_hold.get("current_piece", "")) != str(first_next.get("piece_name", "")) or available:
			failures.append("%dD %s first Hold transport must synchronize active, HOLD, NEXT, and availability" % [dimension, piece_set_id])
		var rejected_hash: String = bridge.live_3d_state_hash() if dimension == 3 else bridge.live_4d_state_hash()
		if dimension == 3:
			bridge.live_3d_apply_command("hold")
		else:
			bridge.live_4d_apply_command("hold")
		var after_rejected_hash: String = bridge.live_3d_state_hash() if dimension == 3 else bridge.live_4d_state_hash()
		if after_rejected_hash != rejected_hash:
			failures.append("%dD %s rejected Hold transport must be a deterministic no-op" % [dimension, piece_set_id])
		if dimension == 3:
			bridge.live_3d_apply_command("hard_drop")
		else:
			bridge.live_4d_apply_command("hard_drop")
		available = bridge.live_3d_hold_available() if dimension == 3 else bridge.live_4d_hold_available()
		if not available:
			failures.append("%dD %s successful lock must reset authoritative Hold availability" % [dimension, piece_set_id])
		_assert_live_queue_preview(failures, bridge, catalog_by_identity, dimension, piece_set_id, "post-lock")
		var occupied_next: Dictionary = bridge.live_3d_next_piece_preview() if dimension == 3 else bridge.live_4d_next_piece_preview()
		if dimension == 3:
			bridge.live_3d_apply_command("hold")
		else:
			bridge.live_4d_apply_command("hold")
		var next_after_swap: Dictionary = bridge.live_3d_next_piece_preview() if dimension == 3 else bridge.live_4d_next_piece_preview()
		if _payload_identity(occupied_next) != _payload_identity(next_after_swap):
			failures.append("%dD %s occupied Hold transport must not consume NEXT" % [dimension, piece_set_id])


func _assert_live_queue_preview(failures: Array, bridge, catalog_by_identity: Dictionary, dimension: int, piece_set_id: String, phase: String) -> void:
	var before_hash: String = bridge.live_3d_state_hash() if dimension == 3 else bridge.live_4d_state_hash()
	var snapshot_text: String = bridge.live_3d_snapshot_json() if dimension == 3 else bridge.live_4d_snapshot_json()
	var preview: Dictionary = bridge.live_3d_next_piece_preview() if dimension == 3 else bridge.live_4d_next_piece_preview()
	var after_hash: String = bridge.live_3d_state_hash() if dimension == 3 else bridge.live_4d_state_hash()
	var snapshot = JSON.parse_string(snapshot_text)
	var context := "%dD %s %s NEXT" % [dimension, piece_set_id, phase]
	if not snapshot is Dictionary:
		failures.append("%s snapshot must parse" % context)
		return
	if str(snapshot.get("next_piece", "")) != str(preview.get("piece_name", "")):
		failures.append("%s must render authoritative queue[0] identity" % context)
	if str(preview.get("piece_set_id", "")) != piece_set_id:
		failures.append("%s must retain authoritative piece-set identity" % context)
	if before_hash != after_hash:
		failures.append("%s observation must not mutate session or RNG state" % context)
	var identity := _payload_identity(preview)
	if not catalog_by_identity.has(identity):
		failures.append("%s must resolve to production geometry" % context)
		return
	var authoritative: Dictionary = catalog_by_identity[identity]
	if _canonical_cells(preview.get("cells", []), dimension) != _canonical_cells(authoritative.get("cells", []), dimension):
		failures.append("%s must expose exact queued-piece production cells" % context)
	var model = PieceThumbnailModelScript.new()
	if not model.configure(preview) or _canonical_cells(model.canonical_cells, dimension) != _canonical_cells(authoritative.get("cells", []), dimension):
		failures.append("%s must reach the thumbnail model without stale or substituted geometry" % context)


func _assert_same_geometry(failures: Array, authoritative: Array, candidate: Array, dimension: int, context: String) -> void:
	if candidate != authoritative:
		failures.append("%s must preserve exact canonical coordinates" % context)
	if _extents(candidate, dimension) != _extents(authoritative, dimension):
		failures.append("%s must preserve dimensional extents without axis collapse" % context)
	if _face_adjacency(candidate, dimension) != _face_adjacency(authoritative, dimension):
		failures.append("%s must preserve the exact face-adjacency graph" % context)


func _assert_embedding(failures: Array, cells: Array, dimension: int, piece_set_id: String, identity: String) -> void:
	if piece_set_id == "embedded_2d":
		for cell in cells:
			if int(cell[2]) != 0 or (dimension == 4 and int(cell[3]) != 0):
				failures.append("%s must preserve the production XY-plane embedding" % identity)
				return
	if dimension == 4 and piece_set_id == "embedded_3d":
		for cell in cells:
			if int(cell[3]) != 0:
				failures.append("%s must preserve the production W=0 embedding" % identity)
				return


func _assert_cube_visible(failures: Array, rendered_cell: Dictionary, rect: Rect2, identity: String) -> void:
	var center: Vector2 = rendered_cell.get("center", Vector2.ZERO)
	var unit := float(rendered_cell.get("unit", 0.0))
	var minimum := center + Vector2(-unit * PieceThumbnailScript.ISOMETRIC_HALF_WIDTH, -unit * PieceThumbnailScript.ISOMETRIC_DEPTH)
	var maximum := center + Vector2(unit * PieceThumbnailScript.ISOMETRIC_HALF_WIDTH, unit * PieceThumbnailScript.ISOMETRIC_HALF_HEIGHT * 2.0)
	if minimum.x < rect.position.x - 0.01 or minimum.y < rect.position.y - 0.01 or maximum.x > rect.end.x + 0.01 or maximum.y > rect.end.y + 0.01:
		failures.append("%s renderer must not clip a production preview cell" % identity)


func _canonical_cells(cells: Array, dimension: int) -> Array:
	var result: Array = []
	var seen: Dictionary = {}
	for value in cells:
		var cell := _integer_cell(value)
		if cell.size() != dimension:
			continue
		var key := JSON.stringify(cell)
		if seen.has(key):
			continue
		seen[key] = true
		result.append(cell)
	result.sort_custom(_coord_less)
	return result


func _integer_cell(value) -> Array:
	var result: Array = []
	if value is Array:
		for coordinate in value:
			result.append(int(coordinate))
	return result


func _coord_less(left: Array, right: Array) -> bool:
	for index in range(mini(left.size(), right.size())):
		if int(left[index]) != int(right[index]):
			return int(left[index]) < int(right[index])
	return left.size() < right.size()


func _extents(cells: Array, dimension: int) -> Array:
	if cells.is_empty():
		return []
	var result: Array = []
	for axis in range(dimension):
		var minimum := int(cells[0][axis])
		var maximum := minimum
		for cell in cells:
			minimum = mini(minimum, int(cell[axis]))
			maximum = maxi(maximum, int(cell[axis]))
		result.append(maximum - minimum)
	return result


func _face_adjacency(cells: Array, dimension: int) -> Array:
	var edges: Array = []
	for left in range(cells.size()):
		for right in range(left + 1, cells.size()):
			var distance := 0
			for axis in range(dimension):
				distance += absi(int(cells[left][axis]) - int(cells[right][axis]))
			if distance == 1:
				edges.append("%s--%s" % [JSON.stringify(cells[left]), JSON.stringify(cells[right])])
	edges.sort()
	return edges


func _payload_identity(payload: Dictionary) -> String:
	return "%d:%s:%s" % [int(payload.get("dimension", 0)), str(payload.get("piece_set_id", "")), str(payload.get("piece_name", ""))]


func _setup(mode: String, preset_id: String, shape: Array, piece_set_id: String, seed: int, speed: int) -> Dictionary:
	return {
		"schema_version": 2,
		"contract_version": GameSetupSpecScript.BoardExtentContractScript.CONTRACT_VERSION,
		"mode": mode,
		"board_preset_id": preset_id,
		"board_shape": shape,
		"piece_set_id": piece_set_id,
		"random_mode": "fixed_seed",
		"seed": seed,
		"initial_speed_level": speed,
		"topology_profile": GameSetupSpecScript.bounded_topology_profile(shape),
	}
