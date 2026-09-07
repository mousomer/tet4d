extends SceneTree

const SCENE := preload("res://scenes/trace_replay.tscn")

func _initialize() -> void:
	call_deferred("_capture")

func _capture() -> void:
	var target := OS.get_cmdline_user_args()[0]
	var root := SCENE.instantiate() as Control
	get_root().add_child(root)
	await process_frame
	await process_frame
	var app := root.get_node("App")
	for mode in ["2d", "3d", "4d"]:
		app.call("_enter_live_%s_mode" % mode)
		await process_frame
		await process_frame
		var payload := {"probe": "godot_runtime_v2", "implementation": "godot", "mode": mode, "capture_state": "plain_initial", "source": "res://scenes/trace_replay.tscn live shell", "viewport": [int(root.get_viewport_rect().size.x), int(root.get_viewport_rect().size.y)], "root": _export_control(root)}
		var file := FileAccess.open(target.path_join("game_%s.probe.json" % mode), FileAccess.WRITE)
		file.store_string(JSON.stringify(payload, "\t") + "\n")
		var image := root.get_viewport().get_texture().get_image()
		if image == null:
			push_error("Runtime viewport image unavailable; use a non-headless renderer for PNG capture")
		else:
			image.save_png(target.path_join("game_%s.png" % mode))
	root.queue_free(); quit()

func _export_control(control: Control) -> Dictionary:
	var rect := control.get_global_rect()
	var node := {"semantic_id": _semantic_id(control), "kind": _kind(control), "semantic_role": str(control.get_meta("semantic_role", _kind(control))), "bounds": [roundi(rect.position.x), roundi(rect.position.y), roundi(rect.size.x), roundi(rect.size.y)], "visible": control.is_visible_in_tree(), "style": _style(control)}
	if control is Label or control is Button:
		node["text"] = control.text
	var children: Array = []
	for child in control.get_children():
		if child is Control:
			children.append(_export_control(child as Control))
	if not children.is_empty():
		node["children"] = children
	return node

func _semantic_id(control: Control) -> String:
	if control.name == "TraceReplayRoot":
		return "game_screen"
	return str(control.get_path()).trim_prefix("/root/TraceReplayRoot/").replace("/", "__").replace("@", "generated_").to_snake_case()

func _kind(control: Control) -> String:
	if control is Label or control is Button:
		return "text"
	if control is SubViewportContainer:
		return "viewport"
	return "frame"

func _style(control: Control) -> Dictionary:
	var style := {}
	if control is ColorRect:
		style["fill"] = _hex(control.color)
	if control is Label or control is Button:
		style["color"] = _hex(control.get_theme_color("font_color"))
		style["font_size"] = control.get_theme_font_size("font_size")
	if control is PanelContainer:
		var box := control.get_theme_stylebox("panel")
		if box is StyleBoxFlat:
			style["fill"] = _hex(box.bg_color)
			style["radius"] = box.corner_radius_top_left
	return style

func _hex(color: Color) -> String:
	return "#%02x%02x%02x" % [roundi(color.r * 255.0), roundi(color.g * 255.0), roundi(color.b * 255.0)]
