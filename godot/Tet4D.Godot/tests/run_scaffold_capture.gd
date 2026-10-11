extends SceneTree

# Real-window fixed-state matrix. Run with an absolute output directory:
# Godot --path godot/Tet4D.Godot --script tests/run_scaffold_capture.gd -- /private/tmp/scaffold-captures
# Uses the production renderer, camera-relative faces and environmental backdrop.
# Every case has the same window, view, board and piece state within a dimension.
const Renderer = preload("res://scripts/rendering/trace_scene_renderer.gd")
const Catalog = preload("res://scripts/presentation/built_in_style_catalog.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")
const Background = preload("res://scripts/rendering/animated_background.gd")
const Registry = preload("res://scripts/ui/settings/settings_registry.gd")
var records: Array = []
func _initialize():
	call_deferred("capture")
func collect(node: Node, result: Dictionary):
	var role = str(node.get_meta("presentation_role", ""))
	if not role.is_empty(): result[role] = int(result.get(role, 0)) + 1
	for child in node.get_children(): collect(child, result)
func capture():
	var destination = OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(destination)
	root.size = Vector2i(1200, 900)
	var registry = Registry.new()
	registry.load_from_path(Registry.REGISTRY_PATH)
	var catalog = Catalog.new(registry)
	var world = Node3D.new()
	root.add_child(world)
	var renderer = Renderer.new()
	world.add_child(renderer)
	var camera = Camera3D.new()
	world.add_child(camera)
	camera.current = true
	camera.far = 1000
	var background = Background.new()
	camera.add_child(background)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	var environment = WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_energy = 0.65
	world.add_child(environment)
	var light = DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-45, -35, 0)
	light.shadow_enabled = false
	world.add_child(light)
	var label = Label.new()
	label.position = Vector2(20, 20)
	label.add_theme_font_size_override("font_size", 24)
	root.add_child(label)
	await process_frame
	for dimension in [2, 3, 4]:
		var shape = [4, 6] if dimension == 2 else ([4, 6, 3] if dimension == 3 else [4, 6, 3, 3])
		var coord = [1, 4] if dimension == 2 else ([1, 4, 1] if dimension == 3 else [1, 4, 1, 1])
		var active = coord.duplicate(); active[1] = 1
		var ghost = coord.duplicate(); ghost[1] = 3
		var snapshot = {"case_id": "scaffold_acceptance", "trace_type": "live_%dd" % dimension, "dimension": dimension, "board_shape": shape, "frame_index": 0,
			"locked_cells": [{"position": coord, "color_id": 4}], "active_cells": [{"position": active, "color_id": 2}], "ghost_cells": [{"position": ghost, "color_id": 2}], "probe_markers": [], "event_markers": [], "particles": []}
		for style in catalog.list_styles():
			for mode in ["none", "border", "full"]:
				var profile = catalog.style_profile(style.style_id).profile.with_overrides({"display.grid_mode": mode})
				renderer.apply_presentation_profile(profile)
				renderer.render_snapshot(snapshot)
				var bounds = renderer.current_bounds()
				var center = (bounds.min + bounds.max) * 0.5
				camera.size = 10 if dimension < 4 else 20
				camera.position = center + (Vector3(0, 0, 22) if dimension == 2 else Vector3(12, 9, 18))
				camera.look_at(center)
				var color = Visuals.color_for_role(Visuals.ROLE_BACKGROUND, str(profile.value("theme.name")))
				color = Color(color.r * float(profile.value("environment.background_intensity")), color.g * float(profile.value("environment.background_intensity")), color.b * float(profile.value("environment.background_intensity")))
				environment.environment.background_color = color
				background.apply_presentation_profile(profile)
				background.set_display_mode(str(profile.value("theme.name")))
				background.set_base_color(color)
				background.reset_phase()
				background.set_process(false)
				var name = "%dd_%s_%s" % [dimension, style.style_id, mode]
				label.text = name
				for frame in range(3): await process_frame
				await RenderingServer.frame_post_draw
				root.get_texture().get_image().save_png(destination.path_join(name + ".png"))
				var roles = {}; collect(renderer.get_node("GridRoot"), roles)
				records.append({"case": name, "roles": roles, "snapshot": snapshot})
	var file = FileAccess.open(destination.path_join("structural.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(records, "\t"));file.close()
	world.queue_free();label.queue_free()
	await process_frame
	print("Captured ", records.size(), " scaffold cases to ", destination)
	quit()
