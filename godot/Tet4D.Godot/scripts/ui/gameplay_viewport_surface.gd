extends TextureRect

# Layout uses logical points. The texture renders at the displayed pixel extent,
# including canvas scaling and the window stretch transform (HiDPI/UI scaling).
var render_viewport: SubViewport


static func render_size(logical_size: Vector2, display_scale: Vector2) -> Vector2i:
	return Vector2i(maxi(2, int(ceil(logical_size.x * display_scale.x))), maxi(2, int(ceil(logical_size.y * display_scale.y))))


func attach(viewport: SubViewport) -> void:
	render_viewport = viewport
	add_child(viewport)
	texture = viewport.get_texture()
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_SCALE
	viewport.msaa_3d = Viewport.MSAA_4X
	resized.connect(sync_resolution)
	sync_resolution()


func _process(_delta: float) -> void:
	# Display/UI scale can change without a logical Control resize.
	sync_resolution()


func sync_resolution() -> void:
	if render_viewport == null or not is_inside_tree() or size.x <= 0.0 or size.y <= 0.0:
		return
	var transform := get_viewport().get_stretch_transform() * get_global_transform_with_canvas()
	var pixels := render_size(size, Vector2(transform.x.length(), transform.y.length()))
	if render_viewport.size != pixels:
		render_viewport.size = pixels
