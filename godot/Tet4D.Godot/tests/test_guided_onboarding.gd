extends RefCounted

const Model = preload("res://scripts/ui/onboarding/live_onboarding_model.gd")

func run() -> Array:
	var failures: Array = []
	var model = Model.new()
	model.select_mode("live_2d")
	if str(model.snapshot().get("step_id")) != "move": failures.append("2D onboarding should begin with movement")
	if model.consume_command_result("move_left", "blocked"): failures.append("rejected movement must not advance onboarding")
	if not model.consume_command_result("move_left", "accepted"): failures.append("accepted movement should advance onboarding")
	if str(model.snapshot().get("step_id")) != "rotate": failures.append("2D movement should advance to rotation")
	model.consume_command_result("rotate_cw", "accepted")
	model.consume_command_result("hard_drop", "accepted")
	if str(model.snapshot().get("step_id")) != "system": failures.append("accepted rotation and drop should reach system guidance")
	model.select_mode("live_4d")
	if str(model.snapshot().get("step_id")) != "slices": failures.append("4D onboarding should explain W slices first")
	model.dismiss()
	if model.is_visible(): failures.append("dismissal should hide guidance for the current launch")
	return failures
