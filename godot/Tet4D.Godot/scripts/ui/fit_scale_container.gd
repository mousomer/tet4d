extends Container

# Shows its single child uniformly scaled by fit_scale, laid out at this
# container's width divided by that scale. Text, keycaps, glyphs and previews
# shrink together, so a helper panel can fit its box instead of scrolling. The
# reported minimum is the scaled one, so an enclosing scroll still takes over
# for whatever cannot fit at the readability floor.
#
# Container.fit_child_in_rect resets a child's scale to one, so the child is
# placed by hand.

var fit_scale := 1.0: set = set_fit_scale


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func set_fit_scale(value: float) -> void:
	var next := clampf(value, 0.01, 1.0)
	if is_equal_approx(next, fit_scale):
		return
	fit_scale = next
	update_minimum_size()
	queue_sort()


func content() -> Control:
	for child in get_children():
		if child is Control and not (child as Control).is_set_as_top_level():
			return child
	return null


func _get_minimum_size() -> Vector2:
	var child := content()
	if child == null or not child.visible:
		return Vector2.ZERO
	return child.get_combined_minimum_size() * fit_scale


func _notification(what: int) -> void:
	if what != NOTIFICATION_SORT_CHILDREN:
		return
	var child := content()
	if child == null:
		return
	var minimum := child.get_combined_minimum_size()
	child.position = Vector2.ZERO
	child.size = (size / fit_scale).max(minimum)
	child.scale = Vector2(fit_scale, fit_scale)
	# A sort during a resize can read a transient minimum: wrapped text still
	# measured at the old width. When it settles back, the child's minimum has
	# not changed since its last report, so no re-sort is queued and the child
	# keeps the stale size. Re-check an oversized placement once settled.
	if minimum.x > size.x / fit_scale + 0.5 or minimum.y > size.y / fit_scale + 0.5:
		_queue_placement_check()


func _queue_placement_check() -> void:
	if not is_inside_tree() or get_tree().process_frame.is_connected(_check_placement):
		return
	get_tree().process_frame.connect(_check_placement, CONNECT_ONE_SHOT)


func _check_placement() -> void:
	var child := content()
	if child != null and not child.size.is_equal_approx((size / fit_scale).max(child.get_combined_minimum_size())):
		queue_sort()
