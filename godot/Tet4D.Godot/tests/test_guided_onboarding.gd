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
	if str(model.snapshot().get("step_id")) != "same_object": failures.append("4D basis instruction should begin with object invariance")
	model.consume_basis_state({"key": "1,2,3,4", "slots": [1, 2, 3, 4], "slice_axis": "+W"})
	if not model.consume_basis_state({"key": "4,2,3,-1", "slots": [4, 2, 3, -1], "slice_axis": "-X"}): failures.append("a basis turn should complete object invariance")
	if str(model.snapshot().get("step_id")) != "useful_slice": failures.append("object invariance should advance to useful slicing")
	if not model.consume_basis_state({"key": "-4,2,3,1", "slots": [-4, 2, 3, 1], "slice_axis": "+X"}): failures.append("a non-W slice should complete useful slicing")
	if model.consume_command_result("move_w_pos", "accepted"): failures.append("coordinate guidance must require navigation along the current signed slice axis")
	if not model.consume_command_result("move_x_pos", "accepted"): failures.append("accepted current-slice navigation should find the coordinate")
	if str(model.snapshot().get("step_id")) != "match_basis": failures.append("coordinate navigation should advance to exact basis matching")
	if not model.consume_basis_state({"key": "4,2,3,-1", "slots": [4, 2, 3, -1], "slice_axis": "-X"}): failures.append("exact target basis should complete target matching")
	if str(model.snapshot().get("step_id")) != "inspect_placement": failures.append("basis match should advance to placement inspection")
	if not model.consume_basis_state({"key": "1,2,3,4", "slots": [1, 2, 3, 4], "slice_axis": "+W"}): failures.append("another exact basis turn should complete placement inspection")
	model.dismiss()
	if model.is_visible(): failures.append("dismissal should hide guidance for the current launch")
	return failures
