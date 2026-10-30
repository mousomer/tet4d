extends RefCounted

const FitScaleContainerScript = preload("res://scripts/ui/fit_scale_container.gd")


# Stands in for wrapped text: its minimum follows a value that can change and
# change back before Godot reports it.
class MeasuredChild extends Control:
	var measured := Vector2.ZERO

	func _get_minimum_size() -> Vector2:
		return measured

	func measure(value: Vector2) -> void:
		measured = value
		update_minimum_size()


func run() -> Array:
	var failures: Array = []
	var tree := Engine.get_main_loop() as SceneTree
	var fit = FitScaleContainerScript.new()
	var child := MeasuredChild.new()
	fit.add_child(child)
	tree.root.add_child(fit)
	fit.size = Vector2(100.0, 50.0)
	await tree.process_frame
	if not child.size.is_equal_approx(Vector2(100.0, 50.0)):
		failures.append("the child must fill the box at scale one, got %s" % child.size)
	# A sort reads a transient minimum that settles back within the frame. The
	# reported minimum never changes, so Godot queues no re-sort of its own.
	child.measure(Vector2(0.0, 80.0))
	fit.notification(Container.NOTIFICATION_SORT_CHILDREN)
	child.measure(Vector2.ZERO)
	for _frame in range(3):
		await tree.process_frame
	if not child.size.is_equal_approx(Vector2(100.0, 50.0)):
		failures.append("a placement from a transient minimum must not persist, got %s" % child.size)
	# Content genuinely taller than the box keeps its minimum, and the check
	# that follows an oversized placement does not repeat once it agrees.
	child.measure(Vector2(0.0, 80.0))
	for _frame in range(3):
		await tree.process_frame
	if not child.size.is_equal_approx(Vector2(100.0, 80.0)):
		failures.append("oversized content must keep its minimum, got %s" % child.size)
	if tree.process_frame.is_connected(fit._check_placement):
		failures.append("a settled oversized placement must not re-check every frame")
	fit.free()
	return failures
