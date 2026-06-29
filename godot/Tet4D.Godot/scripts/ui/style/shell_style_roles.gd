extends RefCounted

class_name ShellStyleRoles

const BACKGROUND_PRIMARY := "background.primary"
const BACKGROUND_PANEL := "background.panel"
const BACKGROUND_BOARD := "background.board"
const BACKGROUND_ELEVATED := "background.elevated"
const TEXT_PRIMARY := "text.primary"
const TEXT_SECONDARY := "text.secondary"
const TEXT_MUTED := "text.muted"
const TEXT_INVERSE := "text.inverse"
const ACCENT_PRIMARY := "accent.primary"
const ACCENT_SOFT := "accent.soft"
const ACCENT_SECONDARY := "accent.secondary"
const ACCENT_FOCUS := "accent.focus"
const GRID_MAJOR := "grid.major"
const GRID_MINOR := "grid.minor"
const GRID_AXIS := "grid.axis"
const CELL_ACTIVE := "cell.active"
const CELL_LOCKED := "cell.locked"
const CELL_SECONDARY := "cell.secondary"
const CELL_GHOST := "cell.ghost"
const CELL_PREVIEW := "cell.preview"
const TRACE_CURRENT := "trace.current"
const TRACE_PAST := "trace.past"
const TRACE_FUTURE := "trace.future"
const LABEL_W_LAYER := "label.w_layer"
const LABEL_AXIS := "label.axis"
const LABEL_HINT := "label.hint"
const HINT_SECTION := "hint.section"
const HINT_KEYCAP_BORDER := "hint.keycap.border"
const HINT_KEYCAP_TEXT := "hint.keycap.text"
const HINT_ACTION := "hint.action"
const HINT_NOTE := "hint.note"
const HINT_ERROR := "hint.error"
const DIAGNOSTIC_BOUNDS := "diagnostic.bounds"
const DIAGNOSTIC_METADATA := "diagnostic.metadata"
const STATE_WARNING := "state.warning"
const STATE_ERROR := "state.error"
const STATE_SUCCESS := "state.success"

const REQUIRED_COLOR_ROLES := [
	BACKGROUND_PRIMARY,
	BACKGROUND_PANEL,
	BACKGROUND_BOARD,
	BACKGROUND_ELEVATED,
	TEXT_PRIMARY,
	TEXT_SECONDARY,
	TEXT_MUTED,
	TEXT_INVERSE,
	ACCENT_PRIMARY,
	ACCENT_SOFT,
	ACCENT_SECONDARY,
	ACCENT_FOCUS,
	GRID_MAJOR,
	GRID_MINOR,
	GRID_AXIS,
	CELL_ACTIVE,
	CELL_LOCKED,
	CELL_SECONDARY,
	CELL_GHOST,
	CELL_PREVIEW,
	TRACE_CURRENT,
	TRACE_PAST,
	TRACE_FUTURE,
	LABEL_W_LAYER,
	LABEL_AXIS,
	LABEL_HINT,
	HINT_SECTION,
	HINT_KEYCAP_BORDER,
	HINT_KEYCAP_TEXT,
	HINT_ACTION,
	HINT_NOTE,
	HINT_ERROR,
	DIAGNOSTIC_BOUNDS,
	DIAGNOSTIC_METADATA,
	STATE_WARNING,
	STATE_ERROR,
	STATE_SUCCESS,
]


static func required_color_roles() -> Array:
	return REQUIRED_COLOR_ROLES.duplicate()


static func is_known_color_role(role: String) -> bool:
	return REQUIRED_COLOR_ROLES.has(role)
