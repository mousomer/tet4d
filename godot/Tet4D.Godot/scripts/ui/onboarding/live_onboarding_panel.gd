extends PanelContainer

class_name LiveOnboardingPanel

signal dismiss_requested()

var _title: Label
var _body: Label
var _progress: Label

func _init() -> void:
	name = "LiveOnboardingPanel"
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	custom_minimum_size = Vector2(0, 176)
	theme_type_variation = "ViewportFrame"
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 16)
	margin.add_theme_constant_override("margin_top", 14)
	margin.add_theme_constant_override("margin_right", 16)
	margin.add_theme_constant_override("margin_bottom", 14)
	add_child(margin)
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 10)
	margin.add_child(content)
	var header := HBoxContainer.new()
	content.add_child(header)
	_title = Label.new()
	_title.name = "OnboardingTitle"
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", 18)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(_title)
	var dismiss_button := Button.new()
	dismiss_button.name = "DismissOnboardingButton"
	dismiss_button.text = "Hide Guide"
	dismiss_button.tooltip_text = "Hide onboarding until it is re-enabled in Settings"
	dismiss_button.pressed.connect(func() -> void: dismiss_requested.emit())
	header.add_child(dismiss_button)
	_body = Label.new()
	_body.name = "OnboardingBody"
	_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.theme_type_variation = "SecondaryLabel"
	_body.add_theme_font_size_override("font_size", 16)
	_body.custom_minimum_size = Vector2(0, 48)
	content.add_child(_body)
	_progress = Label.new()
	_progress.name = "OnboardingProgress"
	_progress.theme_type_variation = "DimLabel"
	content.add_child(_progress)

func render(snapshot: Dictionary) -> void:
	visible = bool(snapshot.get("visible", false))
	_title.text = "Getting Started — %d of %d" % [int(snapshot.get("step_index", 0)) + 1, int(snapshot.get("step_count", 0))]
	_body.text = str(snapshot.get("body", ""))
	_progress.text = str(snapshot.get("title", ""))

func deterministic_snapshot() -> Dictionary:
	return {"visible": visible, "title": _title.text, "body": _body.text, "progress": _progress.text, "minimum_height": custom_minimum_size.y, "hide_action": "Hide Guide"}
