extends RefCounted

# Presentation-only cumulative spatial scaffold selection. Registry strings are the
# serialization boundary; renderers consume this enum.
enum Mode { FULL, BORDER, NONE }
const VALUES := ["full", "border", "none"]

static func from_value(value) -> int:
	var index := VALUES.find(str(value))
	return index if index >= 0 else Mode.BORDER

static func to_value(mode: int) -> String:
	return VALUES[clampi(mode, Mode.FULL, Mode.NONE)]

static func next(mode: int) -> int:
	return (mode + 1) % VALUES.size()


const ENCLOSURE := "board.enclosure"
const FLOOR := "board.floor"
# Board-lattice line classes, keyed by how many boundary planes a maximal line
# lies on: 2 = outer box edge, 1 = boundary face, 0 = volume interior.
const GRID_EDGE := "board.grid_edge"
const GRID_FACE := "board.grid_face"
const GRID_INTERIOR := "board.grid_interior"
const LATTICE_ROLE_BY_BOUNDARY_PLANES := [GRID_INTERIOR, GRID_FACE, GRID_EDGE]

# NONE draws no lattice; BORDER the 12 outer edges plus boundary-face lines,
# showing only camera-relative rear faces; FULL the complete lattice.
static func lattice_roles(mode: int) -> Array:
	match mode:
		Mode.FULL: return [GRID_EDGE, GRID_FACE, GRID_INTERIOR]
		Mode.BORDER: return [GRID_EDGE, GRID_FACE]
	return []

# Camera selection changes face visibility only, never the built lattice.
static func shows_rear_faces_only(mode: int) -> bool:
	return mode == Mode.BORDER

static func roles(mode: int) -> Array:
	return [ENCLOSURE, FLOOR] + lattice_roles(mode)

static func lattice_role(line: Dictionary) -> String:
	return LATTICE_ROLE_BY_BOUNDARY_PLANES[int(line.get("boundary_planes", 0))]

# The grid topology for a mode is a pure filter of the canonical lattice.
static func select_lines(lattice: Array, mode: int) -> Array:
	var included := lattice_roles(mode)
	return lattice.filter(func(line: Dictionary) -> bool: return included.has(lattice_role(line)))
