extends RefCounted

const Layout = preload("res://scripts/ui/shell_viewport_layout.gd")
const Surface = preload("res://scripts/ui/gameplay_viewport_surface.gd")
const Rig = preload("res://scripts/rendering/camera_rig.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")


func run() -> Array:
	var failures: Array = []
	var rect := Layout.usable_rect(Vector2(1280, 800), {"left": 20, "top": 30, "right": 40, "bottom": 10}, 1.5, 8)
	if not rect.position.is_equal_approx(Vector2(20.0 / 1.5 + 8, 28)) or not rect.size.is_equal_approx(Vector2(1220.0 / 1.5 - 16, 760.0 / 1.5 - 16)):
		failures.append("safe area and UI scale must be converted once into local layout units")
	if Layout.design_resolution(Vector2(2560, 1600), 2.0, false, 0.75) != Vector2i(1280, 800):
		failures.append("HiDPI design resolution must retain the existing live reference")
	if Layout.render_delta(Vector2.ONE, Transform2D.IDENTITY, Vector2.ZERO, Vector2(100, 100)) != Vector2.ZERO:
		failures.append("unallocated surfaces must not produce a pan delta")
	failures.append_array(await _assert_projected_pan())
	failures.append_array(await _assert_app_pan_boundary())
	return failures


func _root_point(surface, viewport, rig, marker: Node3D) -> Vector2:
	var pixel: Vector2 = rig.project_world_point(marker.global_position)
	return surface.get_global_transform_with_canvas() * (pixel / Vector2(viewport.size) * surface.size)


func _assert_projected_pan() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var host := Control.new()
	host.position = Vector2(37, 29)
	tree.root.add_child(host)
	var surface = Surface.new()
	host.add_child(surface)
	surface.size = Vector2(640, 360)
	var viewport := SubViewport.new()
	surface.attach(viewport)
	surface.set_process(false)
	var world := Node3D.new()
	viewport.add_child(world)
	var presentation := Node3D.new()
	world.add_child(presentation)
	var marker := Node3D.new()
	marker.position = Vector3(1, 2, 0.5)
	presentation.add_child(marker)
	var rig = Rig.new()
	var camera := Camera3D.new()
	camera.name = "Camera3D"
	rig.add_child(camera)
	world.add_child(rig)
	await tree.process_frame
	rig.set_process(false)
	rig.set_world_presentation_root(presentation)
	var delta := Vector2(12, -7)
	for reflected in [false, true]:
		for ui_scale in [Vector2.ONE, Vector2(1.15, 1.15), Vector2(1.5, 1.25)]:
			host.scale = ui_scale
			for density in [Vector2.ONE, Vector2(2, 2), Vector2(2.5, 2.5), Vector2(1.25, 1.5)]:
				viewport.size = Surface.render_size(surface.size, density)
				rig.establish_outer_view(0.5, 0.3, 0, reflected)
				rig.fit_current_bounds({"ok": true, "min": Vector3(-4, -6, -2), "max": Vector3(4, 6, 2)})
				var before := _root_point(surface, viewport, rig, marker)
				rig.pan_screen(surface.root_delta_to_render(delta))
				var moved := _root_point(surface, viewport, rig, marker) - before
				if moved.distance_to(delta) > 0.02:
					failures.append("projected pan must follow root delta at UI %s / render %s / reflected %s, got %s" % [ui_scale, density, reflected, moved])
	host.queue_free()
	await tree.process_frame
	return failures


func _assert_app_pan_boundary() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var root = load("res://scenes/game_bootstrap.tscn").instantiate()
	tree.root.add_child(root)
	for _frame in range(8):
		await tree.process_frame
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	app.set_process(false)
	for mode in ["live_3d", "live_4d"]:
		hud.start_current_validated_setup(mode)
		for ui_scale in ["standard", "large"]:
			app.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"interface.show_onboarding": false, "display.ui_scale": ui_scale}))
			for _frame in range(12):
				await tree.process_frame
			var viewport: SubViewport = hud.game_viewport()
			var surface = viewport.get_parent()
			surface.set_process(false)
			viewport.size = Surface.render_size(surface.size, Vector2(2, 2))
			await tree.process_frame
			var rig = viewport.get_node("WorldRoot/CameraRig")
			var marker := Node3D.new()
			viewport.get_node("WorldRoot/Live4DPresentationRoot").add_child(marker)
			var before := _root_point(surface, viewport, rig, marker)
			var point: Vector2 = hud.game_viewport_global_rect().get_center()
			var press := InputEventMouseButton.new()
			press.button_index = MOUSE_BUTTON_RIGHT
			press.pressed = true
			press.position = point
			# Invoke the engine callback with root-space events, as _input receives.
			app._input(press)
			var motion := InputEventMouseMotion.new()
			motion.relative = Vector2(12, -7)
			motion.position = point + motion.relative
			app._input(motion)
			press.pressed = false
			app._input(press)
			var moved := _root_point(surface, viewport, rig, marker) - before
			if moved.distance_to(motion.relative) > 0.02:
				failures.append("app pan must convert root input once for %s / %s, got %s" % [mode, ui_scale, moved])
			marker.queue_free()
			surface.set_process(true)
	root.queue_free()
	await tree.process_frame
	return failures
