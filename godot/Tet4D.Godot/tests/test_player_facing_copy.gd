extends RefCounted

const Hud = preload("res://scripts/ui/replay_hud.gd")

func run() -> Array:
	var failures: Array = []
	var player_copy := "\n".join([Hud.LIVE_2D_HELP_TEXT, Hud.LIVE_3D_HELP_TEXT, Hud.LIVE_4D_HELP_TEXT, Hud.ABOUT_DEMO_TEXT])
	for forbidden in ["semantic authority", "oracle", "governance", "migration bundle", "parity schema", "GDExtension", "Godot sends commands only"]:
		if player_copy.find(forbidden) != -1: failures.append("player-facing copy should not contain %s" % forbidden)
	for required in ["W slices", "XY, XZ, or YZ", "Camera controls change the view", "topology tools", "Main Menu"]:
		if player_copy.find(required) == -1: failures.append("player-facing copy should explain %s" % required)
	return failures
