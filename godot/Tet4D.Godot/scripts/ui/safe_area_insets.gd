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
