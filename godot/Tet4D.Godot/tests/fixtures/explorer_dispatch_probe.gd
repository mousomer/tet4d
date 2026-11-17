extends "res://scripts/app/trace_replay_app.gd"

var observed: Array = []
var live_handler_calls := 0

func _practice_action(action: String) -> void:
	observed.append(action)
	super._practice_action(action)

func _handle_live_2d_input(event: InputEvent) -> bool:
	live_handler_calls += 1
	return super._handle_live_2d_input(event)

func _handle_live_3d_input(event: InputEvent) -> bool:
	live_handler_calls += 1
	return super._handle_live_3d_input(event)

func _handle_live_4d_input(event: InputEvent) -> bool:
	live_handler_calls += 1
	return super._handle_live_4d_input(event)
