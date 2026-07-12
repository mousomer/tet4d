extends RefCounted

const Hud = preload("res://scripts/ui/replay_hud.gd")

func run() -> Array:
	var failures: Array = []
	for groups in [Hud.live_2d_control_hint_groups(), Hud.live_3d_control_hint_groups(), Hud.live_4d_control_hint_groups()]:
		var text := Hud._control_groups_text(groups)
		if text.find("Esc Main Menu") == -1: failures.append("live controls should map Esc to Main Menu")
		if text.find("Back / Quit") != -1: failures.append("live controls should distinguish Main Menu from Quit")
	var four_d := Hud._control_groups_text(Hud.live_4d_control_hint_groups())
	if four_d.find("Q / E W- / W+") == -1: failures.append("4D Q/E should remain W movement")
	var hud := Hud.new()
	var quit_count := [0]
	hud.quit_requested.connect(func() -> void: quit_count[0] += 1)
	var quit_button := hud._make_quit_button("Quit Application")
	quit_button.pressed.emit()
	if quit_count[0] != 1: failures.append("every Quit Application button should emit the application quit request")
	return failures
