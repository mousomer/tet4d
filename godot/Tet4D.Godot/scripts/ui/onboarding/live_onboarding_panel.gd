extends PanelContainer

class_name LiveOnboardingPanel

signal dismiss_requested()

const ShellDesignTokensScript = preload("res://scripts/ui/style/shell_design_tokens.gd")
const ResponsivePanelPolicy = preload("res://scripts/ui/responsive_panel_policy.gd")

var _title: Label
var _body: Label
var _progress: Label
var _margin: MarginContainer
var _header: HFlowContainer
var _body_content: VBoxContainer
var _content: VBoxContainer

func _init() -> void:
	name = "LiveOnboardingPanel"
	set_meta("readable_guidance", true)
	size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	custom_minimum_size = Vector2(0, ShellDesignTokensScript.GUIDANCE_MIN_HEIGHT)
	theme_type_variation = "ViewportFrame"
	var margin := MarginContainer.new()
	_margin = margin
	margin.add_theme_constant_override("margin_left", 16)
	margin.add_theme_constant_override("margin_top", ShellDesignTokensScript.SPACE_2)
	margin.add_theme_constant_override("margin_right", 16)
	margin.add_theme_constant_override("margin_bottom", ShellDesignTokensScript.SPACE_2)
	add_child(margin)
	var content := VBoxContainer.new()
	_content = content
	content.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	margin.add_child(content)
	var header := HFlowContainer.new()
	_header = header
	content.add_child(header)
	_title = Label.new()
	_title.name = "OnboardingTitle"
	_title.theme_type_variation = "AccentLabel"
	_title.add_theme_font_size_override("font_size", 18)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	header.add_child(_title)
	var dismiss_button := Button.new()
	dismiss_button.name = "DismissOnboardingButton"
	dismiss_button.text = "Hide Guide"
	dismiss_button.tooltip_text = "Hide onboarding until it is re-enabled in Settings"
	dismiss_button.pressed.connect(func() -> void: dismiss_requested.emit())
	header.add_child(dismiss_button)
	var scroll := ScrollContainer.new()
	scroll.name = "GuideContentScroll"
	ResponsivePanelPolicy.configure_scroll(scroll)
	scroll.focus_mode = Control.FOCUS_ALL
	content.add_child(scroll)
	_body_content = VBoxContainer.new()
	_body_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_body_content.add_theme_constant_override("separation", ShellDesignTokensScript.SPACE_2)
	scroll.add_child(_body_content)
	_body = Label.new()
	_body.name = "OnboardingBody"
	_body.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body.theme_type_variation = "SecondaryLabel"
	_body.add_theme_font_size_override("font_size", 16)
	_body.custom_minimum_size = Vector2(0, 48)
	_body_content.add_child(_body)
	_progress = Label.new()
	_progress.name = "OnboardingProgress"
	_progress.theme_type_variation = "DimLabel"
	_progress.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_body_content.add_child(_progress)


func _process(_delta: float) -> void:
	if not is_visible_in_tree():
		return
	# Header reflow can change the guide's origin without resizing the guide.
	# Retain its natural measured height whenever it fits; only the body scrolls
	# below that floor, with Hide Guide pinned above it.
	var panel_scale := maxf(get_global_transform().get_scale().y, 0.01)
	var available_width := maxf(0.0, (get_viewport_rect().end.x - global_position.x) / panel_scale - ShellDesignTokensScript.COMPACT_PADDING)
	var available := maxf(0.0, (get_viewport_rect().end.y - global_position.y) / panel_scale)
	var chrome := get_theme_stylebox("panel").get_minimum_size().y
	chrome += _margin.get_theme_constant("margin_top") + _margin.get_theme_constant("margin_bottom")
	chrome += _header.get_combined_minimum_size().y + _content.get_theme_constant("separation")
	var natural := maxf(ShellDesignTokensScript.GUIDANCE_MIN_HEIGHT, chrome + _body_content.get_combined_minimum_size().y)
	var wanted := minf(natural, available)
	var minimum := Vector2(available_width, wanted)
	if not custom_minimum_size.is_equal_approx(minimum):
		custom_minimum_size = minimum

func render(snapshot: Dictionary) -> void:
	visible = bool(snapshot.get("visible", false))
	_title.text = "Getting Started — %d of %d" % [int(snapshot.get("step_index", 0)) + 1, int(snapshot.get("step_count", 0))]
	var body := str(snapshot.get("body", ""))
	var target_coordinate: Array = snapshot.get("target_coordinate", [])
	if not target_coordinate.is_empty():
		body += "\nMarked target: (%s)" % ", ".join(target_coordinate)
	_body.text = body
	_progress.text = str(snapshot.get("title", ""))

func deterministic_snapshot() -> Dictionary:
	return {"visible": visible, "title": _title.text, "body": _body.text, "progress": _progress.text, "minimum_height": custom_minimum_size.y, "hide_action": "Hide Guide"}
