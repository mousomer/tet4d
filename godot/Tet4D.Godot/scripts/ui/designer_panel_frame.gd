extends PanelContainer

const ResponsivePanelPolicy = preload("res://scripts/ui/responsive_panel_policy.gd")
# Runtime-only cockpit geometry. This component never applies profiles or Fit.
signal geometry_edited(rect: Rect2)
var content: Control
var move_handle: Button
var resize_handle: Button
var minimum_extent := Vector2(300, 160)
var _gesture := ""
var _start_pointer := Vector2.ZERO
var _start_rect := Rect2()
var _detached_controls: Array[WeakRef] = []
var _scroll_content := false


func configure(title: String, panel: Control, scroll_content: bool) -> void:
	name = "DesignerPanel__%s" % panel.name
	content = panel
	_scroll_content = scroll_content
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
		for control in panel.find_children("*", "Control", true, false):
			if control.has_method("set_detached_layout"):
				control.set_detached_layout(true)
				_detached_controls.append(weakref(control))
		var scroll := ScrollContainer.new()
		ResponsivePanelPolicy.configure_scroll(scroll)
		# Reflow detached guidance before retaining horizontal scrolling as the
		# final fallback for a frame smaller than its readable keycap minimum.
		scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
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
	tree_exiting.connect(_restore_detached_layout)


func constrain(rect: Rect2) -> void:
	var host := get_parent() as Control
	if host == null or host.size.x <= 0 or host.size.y <= 0:
		return
	var usable := Rect2(Vector2.ZERO, host.size)
	if _scroll_content:
		var inverse := host.get_global_transform().affine_inverse()
		var viewport := get_viewport_rect()
		var origin: Vector2 = inverse * viewport.position
		var far: Vector2 = inverse * viewport.end
		usable = usable.intersection(Rect2(origin, far - origin))
	var fitted := ResponsivePanelPolicy.fit_rect(rect, usable, minimum_extent.max(get_combined_minimum_size()))
	size = fitted.size
	position = fitted.position


func _restore_detached_layout() -> void:
	for reference in _detached_controls:
		var control = reference.get_ref()
		if control != null:
			control.set_detached_layout(false)


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
