extends RefCounted

# Pure decisions from measured values. No scene-tree reads or scheduling.
const WIDE_MIN_WIDTH := 1680.0
const STANDARD_MIN_WIDTH := 1180.0
const NARROW_MIN_WIDTH := 800.0


static func profile(apparent: Vector2) -> String:
	if apparent.x >= WIDE_MIN_WIDTH:
		return "wide"
	if apparent.x >= STANDARD_MIN_WIDTH:
		return "standard"
	if apparent.x >= NARROW_MIN_WIDTH:
		return "narrow"
	return "small"


static func placement(requested: String, responsive_profile: String) -> String:
	if requested == "split" and responsive_profile in ["narrow", "small"]:
		return "below"
	return requested


static func row_height(responsive_profile: String, density: String) -> float:
	var base := 150.0 if density == "compact" else 220.0
	if responsive_profile == "narrow":
		return minf(base, 170.0)
	if responsive_profile == "small":
		return minf(base, 150.0)
	return base


static func row_separation(responsive_profile: String) -> int:
	return 8 if responsive_profile == "narrow" else (6 if responsive_profile == "small" else 10)


static func pack_rows(modules: Array, available: float, gap: int) -> Array:
	if available <= 0.0:
		return [modules.map(func(module): return str(module["name"]))]
	var rows: Array = []
	var current: Array = []
	var width := 0.0
	for module in modules:
		var minimum := float(module["width"])
		var addition := minimum if current.is_empty() else minimum + float(gap)
		if not current.is_empty() and width + addition > available:
			rows.append(current)
			current = [str(module["name"])]
			width = minimum
		else:
			current.append(str(module["name"]))
			width += addition
	if not current.is_empty():
		rows.append(current)
	return rows


static func rail_width(base: float, preferred: float, spare: float) -> float:
	return base if preferred <= base else clampf(preferred, base, maxf(base, spare))


static func stage_height(height: float, header: float, inset: float, gap: float) -> float:
	return maxf(height - inset - header - gap * 2.0, 0.0) if height > 1.0 else 0.0


static func below_deck_room(cap: float, row_floor: float, spare: float, remaining: float, constrained: bool, scale_floor: float) -> float:
	var room := maxf(maxf(cap, row_floor), spare)
	if constrained:
		room = minf(room, maxf(remaining, 0.0))
	return maxf(room, row_floor * scale_floor)


static func split_deck_room(relaxed: float, shortfall: float, cap: float) -> float:
	return maxf(relaxed - shortfall, minf(relaxed, cap))


static func rows_height(rows: Array, heights: Dictionary, floor_height: float, gap: int) -> float:
	var height := 0.0
	for names in rows:
		var row_height := floor_height
		for module in names:
			row_height = maxf(row_height, float(heights[str(module)]))
		height += row_height
	return height + float(gap * maxi(rows.size() - 1, 0))


static func rail_room(width: float, stage: float, inset: Vector2, aspect: float, minimum: float, chrome: float) -> float:
	var board_width := maxf(maxf(stage - inset.y, 0.0) * aspect + inset.x, minimum)
	return width - chrome - board_width
