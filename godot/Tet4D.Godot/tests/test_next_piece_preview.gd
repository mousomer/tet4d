extends RefCounted

const PieceThumbnailModelScript = preload("res://scripts/ui/pieces/piece_thumbnail_model.gd")
const NextPiecePanelScript = preload("res://scripts/ui/pieces/next_piece_panel.gd")


func run() -> Array:
	var failures: Array = []
	_test_model_validation_and_dimensions(failures)
	_test_shared_panel_renderer(failures)
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
