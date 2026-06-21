extends RefCounted

class_name SettingSpec

const ALLOWED_CATEGORIES := [
	"replay",
	"display",
	"theme",
	"diagnostics",
	"controls_help",
]
const FORBIDDEN_CATEGORY_TOKENS := [
	"gameplay",
	"topology",
	"movement",
	"rotation",
	"drop",
	"collision",
	"lock",
	"clear",
	"spawn",
	"piece",
	"keyboard_rebinding",
]
const ALLOWED_VALUE_TYPES := ["bool", "int", "float", "enum", "string", "action", "readonly"]
const ALLOWED_CONTROL_TYPES := ["checkbox", "slider", "dropdown", "text_field", "button", "label"]
const ALLOWED_AUTHORITIES := ["godot_shell", "python_oracle", "future_parity", "forbidden"]
const ALLOWED_PERSISTENCE := ["none", "session", "local_shell"]
const CONTROL_TYPE_BY_VALUE_TYPE := {
	"bool": "checkbox",
	"int": "slider",
	"float": "slider",
	"enum": "dropdown",
	"string": "text_field",
	"action": "button",
	"readonly": "label",
}

var data: Dictionary


func _init(spec_data: Dictionary = {}) -> void:
	data = spec_data.duplicate(true)


func id() -> String:
	return str(data.get("id", ""))


func category() -> String:
	return str(data.get("category", ""))


func label() -> String:
	return str(data.get("label", id()))


func description() -> String:
	return str(data.get("description", ""))


func value_type() -> String:
	return str(data.get("value_type", ""))


func control_type() -> String:
	return str(data.get("control_type", ""))


func authority() -> String:
	return str(data.get("authority", ""))


func persistence() -> String:
	return str(data.get("persistence", "none"))


func default_value():
	return data.get("default")


func is_editable() -> bool:
	return authority() == "godot_shell"


static func validate(spec_data: Dictionary, known_categories: Array) -> Array:
	var failures: Array = []
	var setting_id := str(spec_data.get("id", ""))
	var category_id := str(spec_data.get("category", ""))
	var value_type := str(spec_data.get("value_type", ""))
	var control_type := str(spec_data.get("control_type", ""))
	var authority := str(spec_data.get("authority", ""))
	var persistence := str(spec_data.get("persistence", ""))
	if setting_id.is_empty():
		failures.append("setting id is required")
	if category_id.is_empty():
		failures.append("%s: category is required" % setting_id)
	elif not known_categories.has(category_id):
		failures.append("%s: unknown category %s" % [setting_id, category_id])
	if not ALLOWED_VALUE_TYPES.has(value_type):
		failures.append("%s: unknown value_type %s" % [setting_id, value_type])
	if not ALLOWED_CONTROL_TYPES.has(control_type):
		failures.append("%s: unknown control_type %s" % [setting_id, control_type])
	if CONTROL_TYPE_BY_VALUE_TYPE.get(value_type, "") != control_type:
		failures.append("%s: invalid value/control pair %s/%s" % [setting_id, value_type, control_type])
	if not ALLOWED_AUTHORITIES.has(authority):
		failures.append("%s: unknown authority %s" % [setting_id, authority])
	if authority != "godot_shell":
		failures.append("%s: Stage 29 registry may only expose godot_shell editable settings" % setting_id)
	if not ALLOWED_PERSISTENCE.has(persistence):
		failures.append("%s: unknown persistence %s" % [setting_id, persistence])
	for token in FORBIDDEN_CATEGORY_TOKENS:
		if setting_id.find(token) >= 0 or category_id.find(token) >= 0:
			failures.append("%s: forbidden semantic token %s in id/category" % [setting_id, token])
	_validate_default_and_shape(failures, spec_data, setting_id, value_type)
	return failures


static func _validate_default_and_shape(failures: Array, spec_data: Dictionary, setting_id: String, value_type: String) -> void:
	var default_value = spec_data.get("default")
	if value_type == "bool":
		if typeof(default_value) != TYPE_BOOL:
			failures.append("%s: bool default must be bool" % setting_id)
	elif value_type == "string":
		if typeof(default_value) != TYPE_STRING:
			failures.append("%s: string default must be string" % setting_id)
	elif value_type == "int" or value_type == "float":
		for field in ["min", "max", "step"]:
			if not spec_data.has(field):
				failures.append("%s: numeric setting missing %s" % [setting_id, field])
		if not _is_number(default_value):
			failures.append("%s: numeric default must be numeric" % setting_id)
			return
		if not _is_number(spec_data.get("min")) or not _is_number(spec_data.get("max")) or not _is_number(spec_data.get("step")):
			failures.append("%s: numeric min/max/step must be numeric" % setting_id)
			return
		var minimum := float(spec_data.get("min"))
		var maximum := float(spec_data.get("max"))
		var step := float(spec_data.get("step"))
		var default_float := float(default_value)
		if minimum > maximum:
			failures.append("%s: numeric min must be <= max" % setting_id)
		if step <= 0.0:
			failures.append("%s: numeric step must be positive" % setting_id)
		if default_float < minimum or default_float > maximum:
			failures.append("%s: numeric default outside range" % setting_id)
	elif value_type == "enum":
		var options: Array = spec_data.get("options", [])
		if options.is_empty():
			failures.append("%s: enum options must be non-empty" % setting_id)
			return
		var values: Array = []
		for option in options:
			if option is Dictionary:
				values.append(str(option.get("value", "")))
		if not values.has(str(default_value)):
			failures.append("%s: enum default must be in options" % setting_id)
	elif value_type == "action":
		if str(spec_data.get("action_id", "")).is_empty():
			failures.append("%s: action setting missing action_id" % setting_id)


static func _is_number(value) -> bool:
	return typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT
