extends RefCounted

# Stage 58C spatial-readability weights. Presentation only: inputs are camera
# direction and board geometry, never simulation state or frame time.
#
# A weight in (0, 1] scales a settled cell's colour toward the dark board
# background, so the cell recedes while hue, opacity, topology and draw order
# stay unchanged. Active pieces are never weighted.

# Settled weight at the far side of a board box along the view direction; the
# near side keeps 1.0. Supported range [0.6, 1.0]: rear cells stay readable.
const DEPTH_WEIGHT_REAR := 0.75
# Weights move in steps of this size, so camera motion rewrites a cell's
# materials only when its weight visibly changes.
const WEIGHT_QUANTUM := 1.0 / 128.0


# 1.0 at the near side of the box, DEPTH_WEIGHT_REAR at the far side, linear.
static func depth_weight(normalized_depth: float) -> float:
	return lerpf(1.0, DEPTH_WEIGHT_REAR, clampf(normalized_depth, 0.0, 1.0))


# Nearest and farthest projections of a box's corners on a view direction.
static func depth_range(corners: Array, forward: Vector3) -> Vector2:
	var near := INF
	var far := -INF
	for corner in corners:
		var depth: float = (corner as Vector3).dot(forward)
		near = minf(near, depth)
		far = maxf(far, depth)
	return Vector2(near, far)


# 0 at the box's nearest corner and 1 at its farthest, along the view
# direction. Translation and uniform scale of the scene leave it unchanged.
static func normalized_depth(point: Vector3, forward: Vector3, range: Vector2) -> float:
	if range.y - range.x <= 0.0001:
		return 0.0
	return clampf((point.dot(forward) - range.x) / (range.y - range.x), 0.0, 1.0)


static func quantized(weight: float) -> float:
	return snappedf(clampf(weight, 0.0, 1.0), WEIGHT_QUANTUM)
