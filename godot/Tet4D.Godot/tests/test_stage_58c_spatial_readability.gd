extends RefCounted

# Stage 58C presentation hierarchy: active > settled > contextual > grid.
# Assertions compare roles against each other, so they fail when the hierarchy
# inverts rather than when a tuned constant moves.

const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")

const FACES := ["top", "front", "right", "left", "back", "bottom"]
const THEMES := ["plain", "diagnostic", "tron"]
# Material lightness (OKHSL) the active face must keep over the same face of a
# same-colour settled cell, for every palette colour, face and theme.
const ACTIVE_OVER_SETTLED_MIN_MARGIN := 0.08


func run() -> Array:
	var failures: Array = []
	_test_active_over_settled(failures)
	return failures


func _test_active_over_settled(failures: Array) -> void:
	for theme in THEMES:
		for color_id in range(ReplayVisuals.TRACE_COLOR_PALETTE.size()):
			var active: Dictionary = ReplayVisuals.live_3d_active_face_materials(theme, color_id, 1.0)
			var settled: Dictionary = ReplayVisuals.live_3d_locked_face_materials(theme, color_id, 1.0)
			for face in FACES:
				var margin := _lightness(active[face]) - _lightness(settled[face])
				if margin < ACTIVE_OVER_SETTLED_MIN_MARGIN:
					failures.append("%s colour %d %s: active face must stay lighter than settled (margin %.3f)" % [theme, color_id, face, margin])


static func _lightness(material: StandardMaterial3D) -> float:
	return material.albedo_color.ok_hsl_l
