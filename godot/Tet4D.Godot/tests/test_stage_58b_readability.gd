extends RefCounted

const Surface = preload("res://scripts/ui/gameplay_viewport_surface.gd")
const Catalog = preload("res://scripts/presentation/built_in_style_catalog.gd")
const Profile = preload("res://scripts/presentation/presentation_profile.gd")
const LegendDirectionProbeScript = preload("res://tests/support/legend_direction_probe.gd")

# The upright 3D well fits by height, so viewport width beyond it is empty and
# its rail spends that width on the 4D helper set. Guard the rendered board.
const MIN_3D_BOARD_HEIGHT_SHARE := 0.55


func run() -> Array:
	var failures: Array = []
	for scale in [Vector2.ONE, Vector2(2, 2), Vector2(2.5, 2.5), Vector2(1.25, 1.5)]:
		var logical := Vector2(970.25, 444.5)
		var pixels := Surface.render_size(logical, scale)
		if pixels.x < logical.x * scale.x or pixels.y < logical.y * scale.y or pixels.x >= logical.x * scale.x + 1 or pixels.y >= logical.y * scale.y + 1:
			failures.append("render pixels must cover the displayed area with only rounding overhead")
	var tree := Engine.get_main_loop() as SceneTree
	var original_size := tree.root.size
	var original_scale := tree.root.content_scale_size
	var root = load("res://scenes/game_bootstrap.tscn").instantiate()
	tree.root.add_child(root)
	await _frames(tree, 8)
	var app = root.get_node("App")
	var hud = root.get_node("ReplayHud")
	app.set_process(false)
	var registry = preload("res://scripts/ui/settings/settings_registry.gd").new()
	registry.load_from_path(registry.REGISTRY_PATH)
	var catalog := Catalog.new(registry)
	if catalog.list_styles().size() != 6 or not catalog.diagnostics().is_empty():
		return ["58B style matrix requires all six healthy built-in styles"]
	for mode in ["live_3d", "live_4d"]:
		app._start_configured_live_game(hud.configured_live_setup(mode))
		app.apply_presentation_profile(Profile.canonical_defaults().with_overrides({"interface.show_onboarding": false}))
		tree.root.size = Vector2i(1280, 720)
		tree.root.content_scale_size = Vector2i(1280, 720)
		await _frames(tree, 12)
		app._fit_view()
		await _frames(tree, 4)
		var geometry: Vector2 = hud.board_viewport_size()
		if mode == "live_3d":
			# Projection is in rendered pixels; convert to logical before sharing.
			var board_height := LegendDirectionProbeScript.projected_content_height(app) * geometry.y / maxf(float(hud.game_viewport().size.y), 1.0)
			if board_height / 720.0 < MIN_3D_BOARD_HEIGHT_SHARE:
				failures.append("live_3d must retain the reclaimed board height, got %.0f of 720 (viewport %s)" % [board_height, geometry])
		# Live 4D shows its whole legend at this opening window, which outranks
		# the earlier 45% target; its floor now guards only pathological shrink.
		elif geometry.x * geometry.y / (1280 * 720) < 0.35:
			failures.append("%s must retain the reclaimed gameplay allocation, got %s" % [mode, geometry])
		var anchors: Dictionary = app._renderer._presentation.projection.mapper.layer_layout.snapshot()
		var camera: Dictionary = app._camera_rig.presentation_snapshot()
		for record in catalog.list_styles():
			var style = catalog.style_profile(str(record["style_id"]))["profile"]
			app.apply_presentation_profile(app._presentation_profile.with_style_of(style))
			await _frames(tree, 8)
			if hud.board_viewport_size().distance_to(geometry) > 0.1:
				failures.append("%s / %s must preserve viewport allocation" % [mode, record["style_id"]])
			if mode == "live_4d" and app._renderer._presentation.projection.mapper.layer_layout.snapshot() != anchors:
				failures.append("%s / %s must preserve slice positions and spacing" % [mode, record["style_id"]])
			var after: Dictionary = app._camera_rig.presentation_snapshot()
			if after["target_focus"] != camera["target_focus"] or after["orthographic_size"] != camera["orthographic_size"]:
				failures.append("%s / %s must preserve camera fitting" % [mode, record["style_id"]])
			var surface = hud._game_viewport_container
			var transform: Transform2D = surface.get_viewport().get_stretch_transform() * surface.get_global_transform_with_canvas()
			var expected := Surface.render_size(surface.size, Vector2(transform.x.length(), transform.y.length()))
			if hud.game_viewport().size != expected or hud.game_viewport().msaa_3d != Viewport.MSAA_4X:
				failures.append("gameplay must render at displayed pixel extent with 4x MSAA")
		# Retina-style backing pixels change resolution, never logical allocation.
		tree.root.size = Vector2i(2560, 1440)
		await _frames(tree, 8)
		if hud.board_viewport_size().distance_to(geometry) > 0.1 or hud.game_viewport().size != Vector2i(geometry * 2.0):
			failures.append("doubling backing pixels must double rendering without resizing the board")
		tree.root.size = Vector2i(1280, 720)
		await _frames(tree, 4)
	root.queue_free()
	await tree.process_frame
	tree.root.size = original_size
	tree.root.content_scale_size = original_scale
	return failures


func _frames(tree: SceneTree, count: int) -> void:
	for _index in range(count):
		await tree.process_frame
