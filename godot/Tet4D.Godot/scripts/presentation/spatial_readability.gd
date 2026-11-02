extends RefCounted

# Stage 58C spatial-readability weights. Presentation only: inputs are camera
# direction, board geometry and which slices hold the active piece, never
# simulation state or frame time.
#
# A weight in (0, 1] scales a settled cell's colour toward the dark board
# background, so the cell recedes while hue, opacity, topology and draw order
# stay unchanged. Active pieces are never weighted.
#
# These are presentation-only tunings of the existing visual language with no
# player control (the Designer opacity settings keep their meaning), like the
# face factors in ReplayVisuals, so they stay script constants rather than
# registry settings. Tests pin their bounds and orderings, not their values.

# Settled weight at the far side of a board box along the view direction; the
# near side keeps 1.0. Supported range [0.6, 1.0]: rear cells stay readable.
const DEPTH_WEIGHT_REAR := 0.75
# Inactive 4D slices recede with distance from the nearest active slice:
# weight = floor + (1 - floor) * decay^distance. The active slice keeps 1.0;
# distant slices approach the floor and never disappear. Supported floor
# range [0.4, 0.9].
const SLICE_WEIGHT_FLOOR := 0.6
const SLICE_WEIGHT_DECAY := 0.5
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


# Slice steps to the nearest active slice; 0 when no slice is active, so
# nothing recedes without an active piece (matching the active-slice frame).
static func slice_distance(layer: int, active_layers: Array) -> int:
	var distance := -1
	for active_layer in active_layers:
		var step := absi(layer - int(active_layer))
		distance = step if distance < 0 else mini(distance, step)
	return maxi(distance, 0)


# Slices that settled cells and scaffold recede from. Only live boards recede:
# their cells own their materials, while replay cells share one settled
# material per board and keep their baseline presentation.
static func recession_layers(active_layers: Array, is_live: bool) -> Array:
	return active_layers if is_live else []


static func slice_weight(distance: int) -> float:
	return SLICE_WEIGHT_FLOOR + (1.0 - SLICE_WEIGHT_FLOOR) * pow(SLICE_WEIGHT_DECAY, absi(distance))


static func quantized(weight: float) -> float:
	return snappedf(clampf(weight, 0.0, 1.0), WEIGHT_QUANTUM)
