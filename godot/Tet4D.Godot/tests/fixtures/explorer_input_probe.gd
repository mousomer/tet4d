extends "res://scripts/app/trace_replay_app.gd"

# Observe the production dispatch seam without moving a piece or navigating.
var observing := false
var observed: Array = []

func _practice_action(action: String) -> void:
	if observing:
		observed.append(action)
	else:
		super._practice_action(action)
