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
