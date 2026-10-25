extends RefCounted

# Observe sorted production controls. A child outside a scroll surface is
# legitimate only when focus can bring the whole control into that surface.
var observations: Array = []
var capture_dir := ""


func inspect(tree: SceneTree, host: Control, context: String) -> Array:
	var failures: Array = []
	await capture(tree, context)
	var controls: Array[Control] = []
	_collect(host, controls)
	var usable := host.get_viewport_rect().grow(1.0)
	var interactive_controls: Array[Control] = []
	for control in controls:
		if control is ScrollContainer:
			_check_scroll(control, context, failures)
		_check_text_and_rows(control, host, usable, context, failures)
		var interactive := control is BaseButton or control is Range or control is LineEdit or control is TextEdit or control is ItemList
		if (not interactive and control.focus_mode not in [Control.FOCUS_ALL, Control.FOCUS_CLICK]) or control is ScrollBar:
			continue
		if control is BaseButton and control.disabled:
			continue
		if control is ScrollContainer:
			continue
		interactive_controls.append(control)
	for control in interactive_controls:
		if not is_instance_valid(control) or not control.is_visible_in_tree():
			continue
		if control.focus_mode in [Control.FOCUS_ALL, Control.FOCUS_CLICK]:
			control.grab_focus()
			await tree.process_frame
			await tree.process_frame
		else:
			# SpinBox exposes focus on its child LineEdit; pointer-only live
			# buttons deliberately retain gameplay focus. Exercise their scroll
			# reachability without changing that input-ownership contract.
			var ancestor := control.get_parent()
			while ancestor != null and ancestor != host.get_parent():
				if ancestor is ScrollContainer:
					ancestor.ensure_control_visible(control)
				ancestor = ancestor.get_parent()
			await tree.process_frame
			await tree.process_frame
		var rect := control.get_global_rect()
		var visible := usable
		var ancestor := control.get_parent()
		while ancestor != null and ancestor != host.get_parent():
			if ancestor is Control and ancestor.clip_contents:
				visible = visible.intersection(ancestor.get_global_rect().grow(1.0))
			ancestor = ancestor.get_parent()
		# Scroll offsets are integer pixels; scaled canvases can round the
		# exposed edge by another fraction of a logical pixel.
		if rect.size.x <= 0 or rect.size.y <= 0 or not visible.grow(1.0).encloses(rect):
			failures.append("%s control %s is clipped after navigation: %s inside %s" % [context, host.get_path_to(control), rect, visible])
		if control.get_combined_minimum_size().x > control.size.x + 1.0:
			failures.append("%s %s is narrower than its readable minimum: %s < %s" % [context, host.get_path_to(control), control.size, control.get_combined_minimum_size()])
	observations.append({"case": context, "viewport": str(usable), "interactive_controls_checked": interactive_controls.size(), "findings": failures.size()})
	if not failures.is_empty():
		print("Panel findings %s: %s" % [context, failures])
	return failures


# Normal-play helper panels: a scroll surface is legitimate only after every
# cheaper step was taken. The deck/rail and the 4D split column must compact
# before they scroll, the split column must use the whole stage whenever it
# spans it, and a deck under the board must take its full allowance before
# scrolling. Nested helper scrollbars inside a scrolling host are never needed.
func inspect_cockpit(cockpit: Control, context: String) -> Array:
	var failures: Array = []
	var snapshot: Dictionary = cockpit.deterministic_snapshot()
	if not bool(snapshot.get("deck_visible", false)):
		return failures
	var compacted: Array = snapshot.get("compacted_modules", [])
	var placement := str(snapshot.get("deck_placement", ""))
	var deck_scroll: ScrollContainer = cockpit.deck_scroll
	var side_scroll: ScrollContainer = cockpit.side_scroll
	if deck_scroll.get_v_scroll_bar().visible:
		for row in snapshot.get("deck_row_assignment", []):
			for module_name in row:
				if not compacted.has(str(module_name)):
					failures.append("%s deck scrolls before compacting %s (%s in %s)" % [context, module_name, snapshot.get("deck_natural_height"), deck_scroll.size.y])
		# Text and content shrink together before any scrollbar appears.
		if float(snapshot.get("deck_fit_scale", 1.0)) > cockpit.FIT_SCALE_FLOOR + 0.001:
			failures.append("%s deck scrolls at scale %s above the floor %s" % [context, snapshot.get("deck_fit_scale"), cockpit.FIT_SCALE_FLOOR])
		if placement == "below":
			# The allowance is the board's spare height, capped by what the
			# window leaves under the board's minimum.
			var allowance := float(snapshot.get("deck_room", 0.0))
			if cockpit.control_deck.size.y + 1.0 < minf(allowance, float(snapshot.get("deck_natural_height", 0.0))):
				failures.append("%s deck scrolls at %s within an allowance of %s" % [context, cockpit.control_deck.size.y, allowance])
	if placement == "split":
		if bool(snapshot.get("split_column_full_height", false)) and absf(side_scroll.size.y - cockpit.board_stage.size.y) > 1.0:
			failures.append("%s full-height split column is %s of a %s stage" % [context, side_scroll.size.y, cockpit.board_stage.size.y])
		if side_scroll.get_v_scroll_bar().visible:
			for module_name in ["PieceState", "ViewControls"]:
				if not compacted.has(module_name):
					failures.append("%s split column scrolls before compacting %s (%s in %s)" % [context, module_name, snapshot.get("side_column_natural_height"), side_scroll.size.y])
			if float(snapshot.get("side_fit_scale", 1.0)) > cockpit.FIT_SCALE_FLOOR + 0.001:
				failures.append("%s split column scrolls at scale %s above the floor %s" % [context, snapshot.get("side_fit_scale"), cockpit.FIT_SCALE_FLOOR])
	if placement == "side":
		# The rail may grow into width the right-anchored board leaves unused;
		# trimming a piece name or wrapping MOVE while that width sits idle is
		# the inconsistency this guards against.
		var rail_width: float = cockpit.control_deck.size.x
		var preferred: float = cockpit._rail_preferred_width()
		var room: float = cockpit._rail_room_beside_board()
		var idle := room > rail_width + 1.0
		if idle and preferred > rail_width + 1.0:
			failures.append("%s rail is %s wide although its content asks %s and the board leaves %s" % [context, rail_width, preferred, room])
		for node in cockpit.piece_state.find_children("*", "Label", true, false):
			var label := node as Label
			if not label.is_visible_in_tree() or label.text_overrun_behavior == TextServer.OVERRUN_NO_TRIMMING:
				continue
			var text_width := label.get_theme_font("font").get_string_size(label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, label.get_theme_font_size("font_size")).x
			if idle and text_width > label.size.x + 1.0:
				failures.append("%s trims '%s' to %s of %s while the board leaves room" % [context, label.text, label.size.x, text_width])
	for host in [deck_scroll, side_scroll]:
		if not (host as Control).is_visible_in_tree():
			continue
		for nested in (host as Node).find_children("*", "ScrollContainer", true, false):
			if (nested as ScrollContainer).is_visible_in_tree() and (nested as ScrollContainer).get_v_scroll_bar().visible:
				failures.append("%s helper %s scrolls inside %s" % [context, nested.name, host.name])
	observations.append({"case": context, "cockpit": {
		"placement": placement,
		"rail_width": cockpit.control_deck.size.x if placement == "side" else 0.0,
		"board_content_aspect": float(snapshot.get("board_content_aspect", 0.0)),
		"compacted": compacted,
		"deck_fit_scale": float(snapshot.get("deck_fit_scale", 1.0)),
		"side_fit_scale": float(snapshot.get("side_fit_scale", 1.0)),
		"split_column_full_height": bool(snapshot.get("split_column_full_height", false)),
		"deck_scroll": deck_scroll.get_v_scroll_bar().visible,
		"deck_content_height": float(snapshot.get("deck_natural_height", 0.0)),
		"deck_box_height": deck_scroll.size.y,
		"side_scroll": side_scroll.get_v_scroll_bar().visible,
		"side_content_height": float(snapshot.get("side_column_natural_height", 0.0)),
		"side_box_height": side_scroll.size.y if side_scroll.is_visible_in_tree() else 0.0,
	}, "findings": failures.size()})
	if not failures.is_empty():
		print("Cockpit findings %s: %s" % [context, failures])
	return failures


func capture(tree: SceneTree, context: String) -> void:
	if capture_dir.is_empty() or DisplayServer.get_name() == "headless":
		return
	DirAccess.make_dir_recursive_absolute(capture_dir)
	await RenderingServer.frame_post_draw
	var filename := context
	for token in ["/", "\\", " ", "(", ")", ","]:
		filename = filename.replace(token, "_")
	tree.root.get_texture().get_image().save_png(capture_dir.path_join(filename + ".png"))


func _check_scroll(scroll: ScrollContainer, context: String, failures: Array) -> void:
	var ancestor := scroll.get_parent()
	var nested := false
	while ancestor != null:
		if ancestor is ScrollContainer:
			nested = true
			break
		ancestor = ancestor.get_parent()
	# A nested scroll can legitimately be below its outer content's fold.
	# Focus reachability above checks both clipping surfaces after navigation.
	if not nested and not scroll.get_viewport_rect().grow(1.0).encloses(scroll.get_global_rect()):
		failures.append("%s scroll surface %s escapes viewport: %s" % [context, scroll.name, scroll.get_global_rect()])
	var content: Control
	for child in scroll.get_children():
		if child is Control and not child is ScrollBar:
			content = child
			break
	if content == null:
		return
	var bar := scroll.get_v_scroll_bar()
	var content_height := content.get_combined_minimum_size().y
	if bar.visible and content_height <= scroll.size.y - 1.0:
		failures.append("%s %s has a vertical scrollbar although its minimum content fits (%s in %s)" % [context, scroll.name, content_height, scroll.size.y])
	if not bar.visible and content_height > scroll.size.y + 1.0 and scroll.vertical_scroll_mode != ScrollContainer.SCROLL_MODE_DISABLED:
		failures.append("%s %s conceals overflow without a scrollbar (%s in %s)" % [context, scroll.name, content_height, scroll.size.y])
	if scroll.horizontal_scroll_mode in [ScrollContainer.SCROLL_MODE_DISABLED, ScrollContainer.SCROLL_MODE_SHOW_NEVER] and content.size.x > scroll.size.x + 1.0:
		failures.append("%s %s clips its content horizontally (%s in %s)" % [context, scroll.name, content.size.x, scroll.size.x])


func _check_text_and_rows(control: Control, host: Control, usable: Rect2, context: String, failures: Array) -> void:
	var rect := control.get_global_rect()
	var scroll_ancestor := false
	var ancestor := control.get_parent()
	var clipped := usable
	while ancestor != null and ancestor != host.get_parent():
		if ancestor is ScrollContainer:
			scroll_ancestor = true
		if ancestor is Control and ancestor.clip_contents:
			clipped = clipped.intersection(ancestor.get_global_rect().grow(1.0))
		ancestor = ancestor.get_parent()
	if control is PanelContainer and not scroll_ancestor and not usable.encloses(rect):
		failures.append("%s panel boundary %s escapes viewport: %s in %s" % [context, control.name, rect, usable])
	if control is Label and rect.intersects(clipped):
		if rect.position.x < clipped.position.x - 1.0 or rect.end.x > clipped.end.x + 1.0:
			failures.append("%s label %s crosses horizontal clip bounds: %s in %s" % [context, control.name, rect, clipped])
		if control.get_minimum_size().y > control.size.y + 1.0:
			failures.append("%s label %s clips wrapped lines (%s in %s)" % [context, control.name, control.get_minimum_size(), control.size])
	if control is BoxContainer or control is FlowContainer or control is GridContainer:
		var children: Array[Control] = []
		for child in control.get_children():
			if child is Control and child.is_visible_in_tree() and not child.is_set_as_top_level():
				if child.size.x > 2.0 and child.size.y > 2.0:
					children.append(child)
		for index in range(children.size()):
			for other_index in range(index + 1, children.size()):
				var first := children[index].get_global_rect().grow(-1.0)
				var second := children[other_index].get_global_rect().grow(-1.0)
				if first.intersects(second):
					failures.append("%s row siblings %s/%s overlap" % [context, children[index].name, children[other_index].name])


func _collect(node: Node, controls: Array[Control]) -> void:
	if node is Control:
		if not node.is_visible_in_tree():
			return
		controls.append(node)
	for child in node.get_children(true):
		if child is Window:
			continue
		_collect(child, controls)


func settle(tree: SceneTree, count: int = 10) -> void:
	for _frame in range(count):
		await tree.process_frame


func resize(tree: SceneTree, logical_size: Vector2i) -> void:
	if DisplayServer.get_name() == "headless":
		tree.root.size = logical_size
		tree.root.content_scale_size = logical_size
	else:
		DisplayServer.window_set_size(Vector2i(Vector2(logical_size) * DisplayServer.screen_get_scale()))
	await settle(tree)


# Cockpit helpers fit over several frames (compact, then a scale search), so a
# fixed frame count can sample a step in progress. Waits for the fit to settle,
# bounded so a fit that never settles fails its checks instead of hanging.
func settle_cockpit(tree: SceneTree, cockpit: Control, limit: int = 120) -> void:
	for _frame in range(limit):
		if cockpit.fit_settled():
			return
		await tree.process_frame
