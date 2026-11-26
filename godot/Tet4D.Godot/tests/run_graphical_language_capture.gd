extends SceneTree

# Graphical-language acceptance captures through normal startup.
#
#   godot --path godot/Tet4D.Godot --script tests/run_graphical_language_capture.gd -- <absolute_output_dir>
#
# Add p3 after the output directory for full-size Ready and midgame evidence.
# Needs a windowed display server and an isolated HOME whose
# Tet4D/shell_settings.json sets the window (1440x900 points = [2880, 1800] on
# Retina) and interface.show_onboarding false; theme.name selects the theme or
# is left out for the default. Boots res://scenes/game_bootstrap.tscn with that
# settings store, then plays the same fixed-seed game and the same scripted
# drops in Live 2D, 3D and 4D and saves the window. Gravity is paused so the
# drops alone build the stacks; every run sees identical game state.
const SEED := 1337
const PLAN_2D := [["move_left", 3], ["move_right", 3], ["", 0], ["move_left", 1], ["move_right", 1], ["move_left", 4], ["move_right", 4], ["move_left", 2], ["move_right", 2], ["", 0], ["move_left", 3], ["move_right", 3]]
const PLAN_ND := [["move_x_neg", 2], ["move_x_pos", 2], ["move_z_neg", 2], ["move_z_pos", 2], ["", 0], ["move_x_neg", 1], ["move_z_pos", 1], ["move_x_pos", 1], ["move_z_neg", 1], ["move_x_neg", 2], ["move_z_neg", 1], ["move_x_pos", 2]]
func _initialize() -> void:
	call_deferred("_go")
func _go() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty() or args.size() > 2 or not DirAccess.dir_exists_absolute(args[0]) or (args.size() == 2 and args[1] != "p3"):
		push_error("Pass an existing screenshot output directory after --.")
		quit(1)
		return
	var out := args[0]
	var p3 := args.size() == 2
	var root_node = load("res://scenes/game_bootstrap.tscn").instantiate()
	root.add_child(root_node)
	for i in 12: await process_frame
	var app = root_node.get_node("App")
	var hud = root_node.get_node("ReplayHud")
	print("startup theme=", app._state.display_mode, " window=", DisplayServer.window_get_size())
	if p3:
		await RenderingServer.frame_post_draw
		if root.get_texture().get_image().save_png(out.path_join("ready.png")) != OK:
			quit(1)
			return
	for mode in ["live_2d", "live_3d", "live_4d"]:
		var setup: Dictionary = hud.configured_live_setup(mode)
		setup["random_mode"] = "fixed_seed"
		setup["seed"] = SEED
		app._start_configured_live_game(setup)
		app.set_process(false)
		for i in 6: await process_frame
		var plan: Array = PLAN_2D if mode == "live_2d" else PLAN_ND
		for step in (plan.slice(0, 6) if p3 else plan):
			for n in int(step[1]):
				app._dispatch_live_control_intent(mode, step[0])
			app._dispatch_live_command(mode, "hard_drop")
			await process_frame
		if p3:
			app._dispatch_live_command(mode, "hold")
			for i in 3:
				app._dispatch_live_command(mode, "tick")
			print(mode, " state hash=", app._live_bridge.live_state_hash(app._live_dimension(mode)))
		for i in 30: await process_frame
		app._publish_legend_screen_directions()
		await RenderingServer.frame_post_draw
		var path := out.path_join(mode + ".png")
		var save_error := root.get_texture().get_image().save_png(path)
		if save_error != OK:
			push_error("Could not save screenshot %s: %s" % [path, error_string(save_error)])
			quit(1)
			return
		print(mode, " theme=", app._state.display_mode, " locked=", app._renderer._presentation.locked_cells().size())
	quit()
