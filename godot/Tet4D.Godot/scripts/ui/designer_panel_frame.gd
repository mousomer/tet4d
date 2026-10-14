extends PanelContainer

# Runtime-only cockpit geometry. This component never applies profiles or Fit.
signal geometry_edited(rect: Rect2)
var content: Control
var move_handle: Button
var resize_handle: Button
var minimum_extent := Vector2(300, 160)
var _gesture := ""
var _start_pointer := Vector2.ZERO
var _start_rect := Rect2()


func configure(title: String, panel: Control, scroll_content: bool) -> void:
	name = "DesignerPanel__%s" % panel.name
	content = panel
	mouse_filter = Control.MOUSE_FILTER_STOP
	var column := VBoxContainer.new()
	add_child(column)
	move_handle = Button.new()
	move_handle.name = "MoveHandle"
	move_handle.size_flags_horizontal = Control.SIZE_SHRINK_END
	move_handle.text = "Move · %s" % title
	move_handle.tooltip_text = "Drag to move this panel within the cockpit"
	move_handle.mouse_default_cursor_shape = Control.CURSOR_MOVE
	move_handle.gui_input.connect(_handle_input.bind("move"))
	column.add_child(move_handle)
	if scroll_content:
		var scroll := ScrollContainer.new()
		scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
		scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
		scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
		column.add_child(scroll)
		panel.reparent(scroll, false)
	else:
		minimum_extent = Vector2(320, 360)
		panel.reparent(column, false)
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	resize_handle = Button.new()
	resize_handle.name = "ResizeHandle"
	resize_handle.size_flags_horizontal = Control.SIZE_SHRINK_END
	resize_handle.text = "Resize ↘"
	resize_handle.tooltip_text = "Drag to resize; minimum size keeps the panel usable"
	resize_handle.mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
	resize_handle.gui_input.connect(_handle_input.bind("resize"))
	column.add_child(resize_handle)


func constrain(rect: Rect2) -> void:
	var host := get_parent() as Control
	if host == null or host.size.x <= 0 or host.size.y <= 0:
		return
	var floor_size := minimum_extent.max(get_combined_minimum_size()).min(host.size)
	var extent := rect.size.max(floor_size).min(host.size)
	size = extent
	position = rect.position.clamp(Vector2.ZERO, (host.size - size).max(Vector2.ZERO))


func set_geometry(rect: Rect2) -> void:
	constrain(rect)
	geometry_edited.emit(Rect2(position, size))


func _handle_input(event: InputEvent, operation: String) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_gesture = operation
			_start_pointer = _pointer_in_host(event)
			_start_rect = Rect2(position, size)
			get_parent().move_child(self, get_parent().get_child_count() - 1)
		else:
			_gesture = ""
		accept_event()
	elif event is InputEventMouseMotion and not _gesture.is_empty():
		var delta := _pointer_in_host(event) - _start_pointer
		var rect := _start_rect
		if _gesture == "move":
			rect.position += delta
		else:
			rect.size += delta
		set_geometry(rect)
		accept_event()


func _pointer_in_host(event: InputEventMouse) -> Vector2:
	return (get_parent() as Control).get_global_transform_with_canvas().affine_inverse() * event.global_position
