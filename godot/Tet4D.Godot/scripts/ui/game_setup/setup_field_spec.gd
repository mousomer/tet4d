extends RefCounted

class_name SetupFieldSpec

const CATEGORY_GAME_DEFINITION := "game_definition"
const CATEGORY_CONTEXTUAL_GAME_DEFINITION := "contextual_game_definition"
const CATEGORY_ADVANCED_GAMEPLAY_INPUT := "advanced_gameplay_input"
const CATEGORY_PRESENTATION_PREFERENCE := "presentation_preference"

const ALLOWED_CATEGORIES := [
	CATEGORY_GAME_DEFINITION,
	CATEGORY_CONTEXTUAL_GAME_DEFINITION,
	CATEGORY_ADVANCED_GAMEPLAY_INPUT,
	CATEGORY_PRESENTATION_PREFERENCE,
]

# Presentation placement. This is where the product shell renders a field, and
# it is deliberately independent of the semantic category above: reproducibility
# is game definition that the RDS requires to be presented secondarily, and
# board dimensions are game definition presented behind board customization.
# Deriving placement from category would make the declaration disagree with the
# rendered surface.
const SECTION_ORDINARY := "ordinary"
const SECTION_BOARD := "board"
const SECTION_ADVANCED := "advanced_game"
const SECTION_CONTROLS := "controls"
const ALLOWED_SECTIONS := [
	SECTION_ORDINARY,
	SECTION_BOARD,
	SECTION_ADVANCED,
	SECTION_CONTROLS,
]

# Disclosure level is derived from placement and conditionality rather than
# declared, so it can never contradict where the field is actually rendered.
const DISCLOSURE_ORDINARY := "ordinary"
const DISCLOSURE_CONTEXTUAL := "contextual"
const DISCLOSURE_SECONDARY := "secondary"
const ALLOWED_DISCLOSURES := [DISCLOSURE_ORDINARY, DISCLOSURE_CONTEXTUAL, DISCLOSURE_SECONDARY]

# Categories that the RDS forbids from dominating the ordinary path.
const CATEGORIES_FORBIDDEN_IN_ORDINARY := [
	CATEGORY_ADVANCED_GAMEPLAY_INPUT,
	CATEGORY_PRESENTATION_PREFERENCE,
]

const IDENTITY_SESSION := "session_identity"
const IDENTITY_INPUT_PREFERENCE := "input_preference"
const IDENTITY_PRESENTATION_PREFERENCE := "presentation_preference"
const ALLOWED_IDENTITIES := [
	IDENTITY_SESSION,
	IDENTITY_INPUT_PREFERENCE,
	IDENTITY_PRESENTATION_PREFERENCE,
]

const IDENTITY_BY_CATEGORY := {
	CATEGORY_GAME_DEFINITION: IDENTITY_SESSION,
	CATEGORY_CONTEXTUAL_GAME_DEFINITION: IDENTITY_SESSION,
	CATEGORY_ADVANCED_GAMEPLAY_INPUT: IDENTITY_INPUT_PREFERENCE,
	CATEGORY_PRESENTATION_PREFERENCE: IDENTITY_PRESENTATION_PREFERENCE,
}

const ALLOWED_VALUE_TYPES := ["int", "enum", "shape_axis"]
const ALLOWED_CONTROL_TYPES := ["selector", "stepper", "numeric_entry"]
const CONTROL_TYPES_BY_VALUE_TYPE := {
	"int": ["selector", "stepper", "numeric_entry"],
	"enum": ["selector"],
	"shape_axis": ["stepper"],
}

const ALLOWED_SPEC_FIELDS := [
	"id", "label", "description", "category", "section", "identity",
	"value_type", "control_type", "modes", "visible_when", "options",
	"min", "max", "axis_index", "session_key",
]

var data: Dictionary


func _init(spec_data: Dictionary = {}) -> void:
	data = spec_data.duplicate(true)


func id() -> String:
	return str(data.get("id", ""))


func label() -> String:
	return str(data.get("label", id()))


func description() -> String:
	return str(data.get("description", ""))


func category() -> String:
	return str(data.get("category", ""))


func section() -> String:
	return str(data.get("section", ""))


func disclosure() -> String:
	if not visible_when().is_empty():
		return DISCLOSURE_CONTEXTUAL
	return DISCLOSURE_ORDINARY if section() == SECTION_ORDINARY else DISCLOSURE_SECONDARY


func identity() -> String:
	return str(data.get("identity", IDENTITY_BY_CATEGORY.get(category(), "")))


func value_type() -> String:
	return str(data.get("value_type", ""))


func control_type() -> String:
	return str(data.get("control_type", ""))


func modes() -> Array:
	return (data.get("modes", []) as Array).duplicate()


func applies_to_mode(mode: String) -> bool:
	return modes().has(mode)


func defines_session_identity() -> bool:
	return identity() == IDENTITY_SESSION


func session_key() -> String:
	return str(data.get("session_key", ""))


func is_always_visible() -> bool:
	return disclosure() == DISCLOSURE_ORDINARY


func visible_when() -> Dictionary:
	var condition = data.get("visible_when", {})
	return (condition as Dictionary).duplicate(true) if condition is Dictionary else {}


func is_visible_for(mode: String, entry: Dictionary) -> bool:
	if not applies_to_mode(mode):
		return false
	var condition := visible_when()
	if condition.is_empty():
		return true
	var field := str(condition.get("field", ""))
	return str(entry.get(field, "")) == str(condition.get("equals", ""))


static func validate(spec_data: Dictionary, known_modes: Array) -> Array:
	return _validate(spec_data, known_modes, true)


static func validate_declaration(spec_data: Dictionary, known_modes: Array) -> Array:
	return _validate(spec_data, known_modes, false)


static func _validate(spec_data: Dictionary, known_modes: Array, require_resolved_options: bool) -> Array:
	var failures: Array = []
	var field_id := str(spec_data.get("id", ""))
	var category_id := str(spec_data.get("category", ""))
	if field_id.is_empty():
		failures.append("setup field id is required")
	if category_id.is_empty():
		failures.append("%s: category is required" % field_id)
		return failures
	if not ALLOWED_CATEGORIES.has(category_id):
		failures.append("%s: unknown category %s" % [field_id, category_id])
		return failures
	_validate_taxonomy(failures, spec_data, field_id, category_id)
	_validate_control(failures, spec_data, field_id, require_resolved_options)
	_validate_modes(failures, spec_data, field_id, known_modes)
	for field in spec_data.keys():
		if not ALLOWED_SPEC_FIELDS.has(str(field)):
			failures.append("%s: unsupported setup field %s" % [field_id, str(field)])
	return failures


static func _validate_taxonomy(failures: Array, spec_data: Dictionary, field_id: String, category_id: String) -> void:
	var declared_section := str(spec_data.get("section", ""))
	if declared_section.is_empty():
		failures.append("%s: section is required" % field_id)
	elif not ALLOWED_SECTIONS.has(declared_section):
		failures.append("%s: unknown section %s" % [field_id, declared_section])
	elif declared_section == SECTION_ORDINARY and CATEGORIES_FORBIDDEN_IN_ORDINARY.has(category_id):
		failures.append("%s: category %s must not be presented in the ordinary path" % [field_id, category_id])
	var declared_identity := str(spec_data.get("identity", ""))
	var required_identity := str(IDENTITY_BY_CATEGORY.get(category_id, ""))
	if declared_identity.is_empty():
		failures.append("%s: identity is required" % field_id)
	elif not ALLOWED_IDENTITIES.has(declared_identity):
		failures.append("%s: unknown identity %s" % [field_id, declared_identity])
	elif declared_identity != required_identity:
		failures.append("%s: category %s requires identity %s" % [field_id, category_id, required_identity])
	var declared_session_key := str(spec_data.get("session_key", ""))
	if declared_identity == IDENTITY_SESSION and declared_session_key.is_empty():
		failures.append("%s: session identity requires session_key" % field_id)
	elif declared_identity != IDENTITY_SESSION and not declared_session_key.is_empty():
		failures.append("%s: only session identity may declare session_key" % field_id)
	var condition = spec_data.get("visible_when", {})
	var has_condition := condition is Dictionary and not (condition as Dictionary).is_empty()
	if category_id == CATEGORY_CONTEXTUAL_GAME_DEFINITION:
		if not has_condition:
			failures.append("%s: contextual game definition requires visible_when" % field_id)
		elif str((condition as Dictionary).get("field", "")).is_empty() or not (condition as Dictionary).has("equals"):
			failures.append("%s: visible_when requires field and equals" % field_id)
	elif has_condition:
		failures.append("%s: only contextual game definition may declare visible_when" % field_id)


static func _validate_control(
	failures: Array,
	spec_data: Dictionary,
	field_id: String,
	require_resolved_options: bool
) -> void:
	var value_type := str(spec_data.get("value_type", ""))
	var control_type := str(spec_data.get("control_type", ""))
	if not ALLOWED_VALUE_TYPES.has(value_type):
		failures.append("%s: unknown value_type %s" % [field_id, value_type])
		return
	if not ALLOWED_CONTROL_TYPES.has(control_type):
		failures.append("%s: unknown control_type %s" % [field_id, control_type])
		return
	if not (CONTROL_TYPES_BY_VALUE_TYPE.get(value_type, []) as Array).has(control_type):
		failures.append("%s: invalid value/control pair %s/%s" % [field_id, value_type, control_type])
	if value_type == "enum" and require_resolved_options and (spec_data.get("options", []) as Array).is_empty():
		failures.append("%s: enum setup field requires options" % field_id)
	if value_type == "shape_axis" and typeof(spec_data.get("axis_index")) != TYPE_INT:
		failures.append("%s: shape_axis setup field requires axis_index" % field_id)
	_validate_range(failures, spec_data, field_id, value_type)


static func _validate_range(failures: Array, spec_data: Dictionary, field_id: String, value_type: String) -> void:
	if value_type == "enum":
		if spec_data.has("min") or spec_data.has("max"):
			failures.append("%s: enum setup field must not declare min/max" % field_id)
		return
	if not _is_number(spec_data.get("min")) or not _is_number(spec_data.get("max")):
		failures.append("%s: numeric setup field requires numeric min and max" % field_id)
		return
	if float(spec_data.get("min")) > float(spec_data.get("max")):
		failures.append("%s: min must be less than or equal to max" % field_id)


static func _is_number(value) -> bool:
	return typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT


static func _validate_modes(failures: Array, spec_data: Dictionary, field_id: String, known_modes: Array) -> void:
	var declared_modes = spec_data.get("modes", [])
	if not (declared_modes is Array) or (declared_modes as Array).is_empty():
		failures.append("%s: modes must be a non-empty list" % field_id)
		return
	for mode in declared_modes as Array:
		if not known_modes.has(str(mode)):
			failures.append("%s: unknown mode %s" % [field_id, str(mode)])
