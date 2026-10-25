extends RefCounted

# Presentation-only fitting. Board allocation and font sizes remain with their
# existing owners; overflowing content belongs in a bounded, focus-aware scroll.
const Tokens = preload("res://scripts/ui/style/shell_design_tokens.gd")


static func bounded_width(available_width: float, preferred_width: float) -> float:
	return clampf(preferred_width, 0.0, maxf(available_width, 0.0))


static func is_compact(available: Vector2) -> bool:
	return available.x <= Tokens.PANEL_COMPACT_SIZE.x or available.y <= Tokens.PANEL_COMPACT_SIZE.y


static func fit_rect(preferred: Rect2, usable: Rect2, minimum: Vector2 = Vector2.ZERO) -> Rect2:
	var extent := preferred.size.max(minimum).min(usable.size.max(Vector2.ZERO))
	var origin := preferred.position.clamp(usable.position, usable.position + (usable.size - extent).max(Vector2.ZERO))
	return Rect2(origin, extent)


static func configure_scroll(scroll: ScrollContainer) -> void:
	# DISABLED propagates child minimum widths to every ancestor. SHOW_NEVER
	# decouples that minimum; consumers must reflow to the allocated width.
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.follow_focus = true
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL


static func compact_spacing(container: BoxContainer, available: Vector2) -> void:
	container.add_theme_constant_override("separation", Tokens.SPACE_2 if is_compact(available) else Tokens.SPACE_4)


# The step before a scrollbar: halve every vertical gap and margin under root.
# Relaxed values are kept as metadata so disabling restores them;
# freshly rebuilt children carry none and are left as built. Returns how many
# containers were compacted for the first time, so a caller can tell a rebuilt
# subtree from one it already compacted. Unchanged constants are not rewritten:
# every override write re-notifies the theme and re-queues minimum sizes.
const _RELAXED_META := "fit_compact_relaxed"


static func compact_vertical_gaps(root: Node, enabled: bool) -> int:
	var fresh := 0
	var targets: Array[Control] = []
	if root is Control:
		targets.append(root)
	for node in root.find_children("*", "Container", true, false):
		targets.append(node as Control)
	for control in targets:
		var names: Array[String] = []
		if control is BoxContainer and (control as BoxContainer).vertical:
			names = ["separation"]
		elif control is GridContainer or control is FlowContainer:
			names = ["v_separation"]
		elif control is MarginContainer:
			names = ["margin_top", "margin_bottom"]
		if names.is_empty():
			continue
		# [had_override, relaxed, compact]: a themed default is removed, not
		# pinned. The owner may set a constant while it is compacted (a strip
		# switching layout sets its own margins); a value that is no longer the
		# compact one is the owner's, so it becomes the relaxed value on the next
		# compaction and is never overwritten on restore.
		if enabled:
			var stored: Dictionary = control.get_meta(_RELAXED_META) if control.has_meta(_RELAXED_META) else {}
			if stored.is_empty():
				fresh += 1
			for constant in names:
				var current := control.get_theme_constant(constant)
				if not stored.has(constant) or current != int(stored[constant][2]):
					stored[constant] = [control.has_theme_constant_override(constant), current, floori(float(current) * 0.5)]
				if current != int(stored[constant][2]):
					control.add_theme_constant_override(constant, int(stored[constant][2]))
			control.set_meta(_RELAXED_META, stored)
		elif control.has_meta(_RELAXED_META):
			var stored: Dictionary = control.get_meta(_RELAXED_META)
			for constant in stored:
				if control.get_theme_constant(constant) != int(stored[constant][2]):
					continue
				if bool(stored[constant][0]):
					control.add_theme_constant_override(constant, int(stored[constant][1]))
				else:
					control.remove_theme_constant_override(constant)
			control.remove_meta(_RELAXED_META)
	return fresh


# Upper bound on the height compact_vertical_gaps saved under root: every
# halved gap counted as if stacked. A caller holding a compact measurement can
# bound the relaxed height without relaxing, which would take a layout pass.
static func compact_savings_bound(root: Node) -> float:
	var targets: Array[Node] = [root]
	targets.append_array(root.find_children("*", "Container", true, false))
	var bound := 0.0
	for node in targets:
		if not node.has_meta(_RELAXED_META) or not (node as Control).is_visible_in_tree():
			continue
		var visible_children := 0
		for child in node.get_children():
			if child is Control and (child as Control).visible:
				visible_children += 1
		var stored: Dictionary = node.get_meta(_RELAXED_META)
		for constant in stored:
			var saved := float(int(stored[constant][1]) - int(stored[constant][2]))
			var gaps := 1
			if constant == "separation" or node is FlowContainer:
				gaps = maxi(visible_children - 1, 0)
			elif node is GridContainer:
				gaps = maxi(ceili(float(visible_children) / float(maxi((node as GridContainer).columns, 1))) - 1, 0)
			bound += saved * float(gaps)
	return bound


static func button_padding(button: Button, padding: float) -> void:
	for state in ["normal", "hover", "focus", "pressed", "disabled"]:
		var style := button.get_theme_stylebox(state).duplicate() as StyleBox
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			style.set_content_margin(side, padding)
		button.add_theme_stylebox_override(state, style)


static func reflow_row(row: BoxContainer, available_width: float) -> void:
	var required := 0.0
	var count := 0
	for child in row.get_children():
		if child is Control and child.visible:
			required += child.get_combined_minimum_size().x
			count += 1
	required += maxf(count - 1, 0) * row.get_theme_constant("separation")
	row.vertical = required > available_width


static func bind_popup(popup: Window, owner: Control) -> void:
	# Use the current application client area, never a nominal display size.
	# Generated controls are rebuilt while their window survives. Weak captures
	# avoid retaining callbacks to freed OptionButton popups after a rebuild.
	var popup_ref: WeakRef = weakref(popup)
	var owner_ref: WeakRef = weakref(owner)
	var update := func() -> void:
		var current_popup = popup_ref.get_ref()
		var current_owner = owner_ref.get_ref()
		if current_popup != null and current_owner != null and current_popup.visible:
			clamp_popup(current_popup, current_owner)
	var schedule := func() -> void: update.call_deferred()
	popup.about_to_popup.connect(schedule)
	popup.visibility_changed.connect(schedule)
	popup.size_changed.connect(schedule)
	owner.resized.connect(schedule)
	owner.theme_changed.connect(schedule)
	var window_ref: WeakRef = weakref(owner.get_window())
	owner.get_window().size_changed.connect(schedule)
	popup.tree_exiting.connect(func() -> void:
		var current_owner = owner_ref.get_ref()
		var current_window = window_ref.get_ref()
		if current_owner != null:
			if current_owner.resized.is_connected(schedule):
				current_owner.resized.disconnect(schedule)
			if current_owner.theme_changed.is_connected(schedule):
				current_owner.theme_changed.disconnect(schedule)
		if current_window != null and current_window.size_changed.is_connected(schedule):
			current_window.size_changed.disconnect(schedule)
	)


static func clamp_popup(popup: Window, owner: Control) -> void:
	var parent_window := owner.get_window()
	var usable := Rect2(Vector2.ZERO, parent_window.get_visible_rect().size)
	if not popup.is_embedded():
		usable = Rect2(Vector2(parent_window.position), Vector2(parent_window.size))
	var inset := float(Tokens.SPACE_2)
	usable = usable.grow(-minf(inset, minf(usable.size.x, usable.size.y) * 0.5))
	popup.max_size = Vector2i(usable.size)
	popup.min_size = popup.min_size.min(popup.max_size)
	var fitted := fit_rect(Rect2(Vector2(popup.position), Vector2(popup.size)), usable)
	popup.size = Vector2i(fitted.size)
	popup.position = Vector2i(fitted.position)
