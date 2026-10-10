extends RefCounted

# Presentation-only lattice/boundary selection. Registry strings are the
# serialization boundary; renderers consume this enum.
enum Mode { FULL, BORDER, NONE }
const VALUES := ["full", "border", "none"]

static func from_value(value) -> int:
	var index := VALUES.find(str(value))
	return index if index >= 0 else Mode.FULL

static func to_value(mode: int) -> String:
	return VALUES[clampi(mode, Mode.FULL, Mode.NONE)]

static func next(mode: int) -> int:
	return (mode + 1) % VALUES.size()
