extends RefCounted

class_name SafeAreaInsets

# Window-relative insets for displays whose usable area is smaller than the
# window: notches, camera housings, rounded corners, and home indicators on
# Android tablets and iPads.
#
# The shell keeps one cockpit layout for every platform. Handheld adaptation is
# expressed purely as additional outer margin, so nothing about the relative
# priority of the board, NEXT/HOLD, piece controls, or Design Laboratory
# changes. On desktop the safe area equals the window and every inset is zero,
# which makes this inert there by construction.

const ZERO := {"left": 0, "top": 0, "right": 0, "bottom": 0}


# Pure resolution so every device geometry can be asserted headlessly.
static func resolve(safe_area: Rect2i, window_size: Vector2i) -> Dictionary:
	if window_size.x <= 0 or window_size.y <= 0:
		return ZERO.duplicate()
	if safe_area.size.x <= 0 or safe_area.size.y <= 0:
		return ZERO.duplicate()
	# A safe area larger than the window (or reported in a different space)
	# cannot be interpreted as an inset; treat it as no inset at all.
	if safe_area.size.x > window_size.x or safe_area.size.y > window_size.y:
		return ZERO.duplicate()
	return {
		"left": maxi(safe_area.position.x, 0),
		"top": maxi(safe_area.position.y, 0),
		"right": maxi(window_size.x - (safe_area.position.x + safe_area.size.x), 0),
		"bottom": maxi(window_size.y - (safe_area.position.y + safe_area.size.y), 0),
	}


static func current() -> Dictionary:
	return resolve(DisplayServer.get_display_safe_area(), DisplayServer.window_get_size())


# The display reports insets in window pixels; layout runs in canvas units,
# which canvas_items stretch scales away from window pixels. A macOS notch is
# 78 backing pixels but only ~24 units of a 1280-unit canvas at 4112 pixels,
# so applying pixels directly left a ~54-unit dead band above the cockpit.
static func to_canvas(insets: Dictionary, window_size: Vector2i, canvas_size: Vector2) -> Dictionary:
	if window_size.x <= 0 or window_size.y <= 0 or canvas_size.x <= 0.0 or canvas_size.y <= 0.0:
		return ZERO.duplicate()
	var factor := canvas_size / Vector2(window_size)
	return {
		"left": int(ceilf(float(insets.get("left", 0)) * factor.x)),
		"top": int(ceilf(float(insets.get("top", 0)) * factor.y)),
		"right": int(ceilf(float(insets.get("right", 0)) * factor.x)),
		"bottom": int(ceilf(float(insets.get("bottom", 0)) * factor.y)),
	}


static func current_in_canvas(canvas_size: Vector2) -> Dictionary:
	return to_canvas(current(), DisplayServer.window_get_size(), canvas_size)
