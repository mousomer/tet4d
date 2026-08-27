extends PanelContainer

class_name PresentationDesigner

const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")

signal profile_preview_requested(profile)
signal state_changed(state: String)

const STATE_HIDDEN := "hidden"
const STATE_COMPACT := "compact"
const STATE_FULL := "full"
const SLOT_REFERENCE := "A"
const SLOT_WORKING := "B"

var _registry
var _runtime_context := "live_2d"
var _opening_profile
var _reference_profile
var _working_profile
var _displayed_slot := SLOT_WORKING
var _state := STATE_HIDDEN
var _syncing_controls := false

var _full_root: VBoxContainer
var _compact_root: HBoxContainer
var _groups_box: VBoxContainer
var _slot_state_label: Label
var _status_label: Label
var _compact_state_label: Label
var _reference_button: Button
var _compact_reference_button: Button
var _working_button: Button
var _compact_working_button: Button
var _first_full_focus: Control
var _controls_by_id: Dictionary = {}
var _owner_order: Array = []
var _applicable_ids: Array = []


func _ready() -> void:
	name = "PresentationDesigner"
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_meta("semantic_role", "interactive_button_panel")
	_build_surface()
	_refresh_state_visibility()


func configure(registry) -> bool:
	if registry == null or not registry.has_method("validate") or not registry.validate().is_empty():
		return false
	_registry = registry
	_rebuild_registry_controls()
	return true


func open_with_profile(active_profile, runtime_context: String) -> bool:
	if _registry == null or not _valid_profile(active_profile) or not _valid_runtime_context(runtime_context):
		return false
	_runtime_context = runtime_context
	if _opening_profile == null:
		_opening_profile = active_profile.detached_copy()
		_working_profile = active_profile.detached_copy()
		_displayed_slot = SLOT_WORKING
	_rebuild_registry_controls()
	_set_state(STATE_FULL)
	_refresh_all_text("Live edits preview B only; nothing is saved.")
	_sync_controls_from_working()
	return true


func set_runtime_context(runtime_context: String) -> bool:
	if not _valid_runtime_context(runtime_context):
		return false
	if _runtime_context == runtime_context:
		return true
	_runtime_context = runtime_context
	_rebuild_registry_controls()
	return true


func hide_preserving_preview() -> void:
	_set_state(STATE_HIDDEN)


func collapse_to_compact() -> void:
	if _opening_profile != null:
		_set_state(STATE_COMPACT)


func expand_to_full() -> void:
	if _opening_profile != null:
		_set_state(STATE_FULL)


func revert_and_hide() -> void:
	if _opening_profile == null:
		return
	_working_profile = _opening_profile.detached_copy()
	_displayed_slot = SLOT_WORKING
	_emit_preview(_working_profile, "Reverted B to the opening baseline.")
	_set_state(STATE_HIDDEN)


func keep_working_and_hide() -> void:
	if _working_profile == null:
		return
	_displayed_slot = SLOT_WORKING
	_emit_preview(_working_profile, "Keeping detached B for this run; nothing was saved.")
	_set_state(STATE_HIDDEN)


func end_session() -> void:
	_set_state(STATE_HIDDEN)
	_opening_profile = null
	_reference_profile = null
	_working_profile = null
	_displayed_slot = SLOT_WORKING
	_sync_controls_from_working()
	_refresh_all_text("Open the Designer to begin a detached preview session.")


func capture_reference() -> bool:
	if _working_profile == null:
		return false
	_reference_profile = _working_profile.detached_copy()
	_refresh_all_text("Captured immutable reference A from working B.")
	return true


func show_slot(slot: String) -> bool:
	var profile = _profile_for_slot(slot)
	if profile == null:
		_refresh_all_text("Capture A before selecting the reference slot.")
		return false
	_displayed_slot = slot
	_emit_preview(profile, "Showing %s · detached preview · not saved." % slot)
	return true


func toggle_slots() -> bool:
	return show_slot(SLOT_REFERENCE if _displayed_slot == SLOT_WORKING else SLOT_WORKING)


func set_parameter_value(setting_id: String, value) -> bool:
	if _working_profile == null or _registry == null or not _applicable_ids.has(setting_id):
		return false
	var spec = _registry.get_spec(setting_id)
	if spec == null:
		return false
	var validated: Dictionary = spec.validated_value(value)
	if not bool(validated.get("ok", false)):
		return false
	var next_profile = _working_profile.with_overrides({setting_id: validated.get("value")})
	if not _valid_profile(next_profile):
		return false
	_working_profile = next_profile.detached_copy()
	_displayed_slot = SLOT_WORKING
	_sync_controls_from_working()
	_emit_preview(_working_profile, "Updated B · %s · not saved." % spec.label())
	return true


func reset_parameter(setting_id: String) -> bool:
	if _opening_profile == null or not _applicable_ids.has(setting_id):
		return false
	return set_parameter_value(setting_id, _opening_profile.value(setting_id))


func reset_owner(owner: String) -> bool:
	if _opening_profile == null or _registry == null:
		return false
	var overrides: Dictionary = {}
	for spec in _registry.settings_for_semantic_owner(owner):
		if _applicable_ids.has(spec.id()):
			overrides[spec.id()] = _opening_profile.value(spec.id())
	return _replace_working_values(overrides, "Reset %s to the opening baseline." % _owner_label(owner))


func reset_working_to_opening() -> bool:
	if _opening_profile == null:
		return false
	_working_profile = _opening_profile.detached_copy()
	_displayed_slot = SLOT_WORKING
	_sync_controls_from_working()
	_emit_preview(_working_profile, "Reset B to the opening baseline.")
	return true


func reset_working_to_factory_defaults() -> bool:
	if _registry == null or _working_profile == null:
		return false
	var profile = PresentationProfileScript.from_snapshot(_registry, {
		"schema_version": PresentationProfileScript.SCHEMA_VERSION,
		"values": _registry.default_values(),
	})
	if not _valid_profile(profile):
		return false
	_working_profile = profile.detached_copy()
	_displayed_slot = SLOT_WORKING
	_sync_controls_from_working()
	_emit_preview(_working_profile, "Reset B to registry factory defaults; nothing was saved.")
	return true


func state() -> String:
	return _state


func full_editor_visible() -> bool:
	return visible and _state == STATE_FULL


func contains_global_point(point: Vector2) -> bool:
	return visible and get_global_rect().has_point(point)


func working_profile():
	return _working_profile.detached_copy() if _working_profile != null else null


func reference_profile():
	return _reference_profile.detached_copy() if _reference_profile != null else null


func opening_profile():
	return _opening_profile.detached_copy() if _opening_profile != null else null


func control_for_setting(setting_id: String) -> Control:
	var entry = _controls_by_id.get(setting_id, {})
	return entry.get("primary") as Control if entry is Dictionary else null


func deterministic_snapshot() -> Dictionary:
	var control_types: Dictionary = {}
	for setting_id in _controls_by_id.keys():
		control_types[setting_id] = str(_controls_by_id.get(setting_id, {}).get("value_type", ""))
	return {
		"state": _state,
		"runtime_context": _runtime_context,
		"displayed_slot": _displayed_slot,
		"has_opening": _opening_profile != null,
		"has_reference": _reference_profile != null,
		"applicable_ids": _applicable_ids.duplicate(),
		"owner_order": _owner_order.duplicate(),
		"control_types": control_types,
		"opening": _opening_profile.snapshot() if _opening_profile != null else {},
		"reference": _reference_profile.snapshot() if _reference_profile != null else {},
		"working": _working_profile.snapshot() if _working_profile != null else {},
		"slot_text": _slot_state_label.text if _slot_state_label != null else "",
		"status_text": _status_label.text if _status_label != null else "",
		"compact_text": _compact_state_label.text if _compact_state_label != null else "",
		"full_visible": _full_root.visible if _full_root != null else false,
		"compact_visible": _compact_root.visible if _compact_root != null else false,
		"rect": get_global_rect(),
	}


func _build_surface() -> void:
	_full_root = VBoxContainer.new()
	_full_root.name = "DesignerFull"
	_full_root.add_theme_constant_override("separation", 7)
	add_child(_full_root)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 6)
	_full_root.add_child(header)
	var title := Label.new()
	title.text = "LIVE PRESENTATION DESIGNER"
	title.theme_type_variation = "AccentLabel"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var compact_button := Button.new()
	compact_button.name = "DesignerCompactButton"
	compact_button.text = "Compact"
	compact_button.tooltip_text = "Collapse to the A/B comparison strip and release gameplay keys"
	compact_button.pressed.connect(collapse_to_compact)
	header.add_child(compact_button)
	_first_full_focus = compact_button
	var hide_button := Button.new()
	hide_button.text = "Hide"
	hide_button.tooltip_text = "Hide without discarding A, B, or the current preview"
	hide_button.pressed.connect(hide_preserving_preview)
	header.add_child(hide_button)

	var detached_note := Label.new()
	detached_note.text = "DETACHED PREVIEW · Current run only · Settings are never saved"
	detached_note.theme_type_variation = "DimLabel"
	detached_note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_full_root.add_child(detached_note)

	var slot_row := HBoxContainer.new()
	slot_row.add_theme_constant_override("separation", 5)
	_full_root.add_child(slot_row)
	var capture_button := Button.new()
	capture_button.name = "DesignerCaptureAButton"
	capture_button.text = "Capture B as A"
	capture_button.tooltip_text = "Replace reference A with an immutable snapshot of working B"
	capture_button.pressed.connect(capture_reference)
	slot_row.add_child(capture_button)
	_reference_button = Button.new()
	_reference_button.name = "DesignerReferenceAButton"
	_reference_button.text = "Show A"
	_reference_button.pressed.connect(show_slot.bind(SLOT_REFERENCE))
	slot_row.add_child(_reference_button)
	_working_button = Button.new()
	_working_button.name = "DesignerWorkingBButton"
	_working_button.text = "Show B"
	_working_button.pressed.connect(show_slot.bind(SLOT_WORKING))
	slot_row.add_child(_working_button)
	var toggle_button := Button.new()
	toggle_button.name = "DesignerToggleABButton"
	toggle_button.text = "Toggle A/B"
	toggle_button.pressed.connect(toggle_slots)
	slot_row.add_child(toggle_button)

	_slot_state_label = Label.new()
	_slot_state_label.name = "DesignerSlotState"
	_slot_state_label.theme_type_variation = "SecondaryLabel"
	_slot_state_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_full_root.add_child(_slot_state_label)

	var scroll := ScrollContainer.new()
	scroll.name = "DesignerParameterScroll"
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_full_root.add_child(scroll)
	_groups_box = VBoxContainer.new()
	_groups_box.name = "DesignerGroups"
	_groups_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_groups_box.add_theme_constant_override("separation", 8)
	scroll.add_child(_groups_box)

	_status_label = Label.new()
	_status_label.name = "DesignerStatus"
	_status_label.theme_type_variation = "DimLabel"
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_full_root.add_child(_status_label)

	var reset_row := HBoxContainer.new()
	reset_row.add_theme_constant_override("separation", 5)
	_full_root.add_child(reset_row)
	var reset_b := Button.new()
	reset_b.text = "Reset B to Opened"
	reset_b.tooltip_text = "Restore every B value to the profile captured when this Designer session opened"
	reset_b.pressed.connect(reset_working_to_opening)
	reset_row.add_child(reset_b)
	var factory_button := Button.new()
	factory_button.text = "Factory Defaults"
	factory_button.tooltip_text = "Replace B with registry defaults without saving them"
	factory_button.pressed.connect(reset_working_to_factory_defaults)
	reset_row.add_child(factory_button)

	var finish_row := HBoxContainer.new()
	finish_row.add_theme_constant_override("separation", 5)
	_full_root.add_child(finish_row)
	var keep_button := Button.new()
	keep_button.text = "Keep B & Hide"
	keep_button.pressed.connect(keep_working_and_hide)
	finish_row.add_child(keep_button)
	var revert_button := Button.new()
	revert_button.text = "Revert & Hide"
	revert_button.tooltip_text = "Restore the opening profile, discard B edits, and hide"
	revert_button.pressed.connect(revert_and_hide)
	finish_row.add_child(revert_button)

	_compact_root = HBoxContainer.new()
	_compact_root.name = "DesignerCompact"
	_compact_root.add_theme_constant_override("separation", 5)
	add_child(_compact_root)
	_compact_state_label = Label.new()
	_compact_state_label.name = "DesignerCompactState"
	_compact_state_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_compact_state_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_compact_root.add_child(_compact_state_label)
	_compact_reference_button = Button.new()
	_compact_reference_button.text = "A"
	_compact_reference_button.tooltip_text = "Show immutable reference A"
	_compact_reference_button.pressed.connect(show_slot.bind(SLOT_REFERENCE))
	_compact_root.add_child(_compact_reference_button)
	_compact_working_button = Button.new()
	_compact_working_button.text = "B"
	_compact_working_button.tooltip_text = "Show detached working B"
	_compact_working_button.pressed.connect(show_slot.bind(SLOT_WORKING))
	_compact_root.add_child(_compact_working_button)
	var compact_toggle := Button.new()
	compact_toggle.text = "A ↔ B"
	compact_toggle.tooltip_text = "Toggle between reference A and working B"
	compact_toggle.pressed.connect(toggle_slots)
	_compact_root.add_child(compact_toggle)
	var expand_button := Button.new()
	expand_button.text = "Expand"
	expand_button.pressed.connect(expand_to_full)
	_compact_root.add_child(expand_button)
	var compact_hide := Button.new()
	compact_hide.text = "Hide"
	compact_hide.pressed.connect(hide_preserving_preview)
	_compact_root.add_child(compact_hide)
	_refresh_all_text("Open the Designer to begin a detached preview session.")


func _rebuild_registry_controls() -> void:
	if _groups_box == null:
		return
	for child in _groups_box.get_children():
		child.queue_free()
	_controls_by_id.clear()
	_owner_order.clear()
	_applicable_ids.clear()
	if _registry == null:
		return
	var specs_by_owner: Dictionary = {}
	for spec in _registry.settings:
		if not spec.applies_at_runtime(_runtime_context):
			continue
		var owner: String = spec.semantic_owner()
		if not specs_by_owner.has(owner):
			specs_by_owner[owner] = []
			_owner_order.append(owner)
		specs_by_owner[owner].append(spec)
		_applicable_ids.append(spec.id())
	for owner in _owner_order:
		_build_owner_group(str(owner), specs_by_owner.get(owner, []))
	_sync_controls_from_working()
	_refresh_all_text("Editing %d live-applicable parameters for %s." % [_applicable_ids.size(), _runtime_context.replace("_", " ").to_upper()])


func _build_owner_group(owner: String, specs: Array) -> void:
	var panel := PanelContainer.new()
	panel.name = "DesignerGroup__%s" % owner
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_groups_box.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 5)
	panel.add_child(box)
	var header := HBoxContainer.new()
	box.add_child(header)
	var title := Label.new()
	title.text = _owner_label(owner).to_upper()
	title.theme_type_variation = "SecondaryLabel"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var reset_button := Button.new()
	reset_button.text = "Reset group"
	reset_button.tooltip_text = "Restore this group to the opening profile"
	reset_button.pressed.connect(reset_owner.bind(owner))
	header.add_child(reset_button)
	for spec in specs:
		_build_parameter_row(box, spec)


func _build_parameter_row(parent: VBoxContainer, spec) -> void:
	var row := VBoxContainer.new()
	row.name = "DesignerParameter__%s" % spec.id().replace(".", "__")
	row.tooltip_text = spec.description()
	parent.add_child(row)
	var label_row := HBoxContainer.new()
	row.add_child(label_row)
	var label := Label.new()
	label.text = spec.label()
	label.tooltip_text = spec.description()
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label_row.add_child(label)
	var reset_button := Button.new()
	reset_button.text = "Reset"
	reset_button.tooltip_text = "Restore %s to its opening value" % spec.label()
	reset_button.pressed.connect(reset_parameter.bind(spec.id()))
	label_row.add_child(reset_button)
	var entry: Dictionary = {"value_type": spec.value_type(), "spec": spec}
	match spec.value_type():
		"bool":
			var checkbox := CheckBox.new()
			checkbox.text = "Enabled"
			checkbox.tooltip_text = spec.description()
			checkbox.toggled.connect(_on_bool_changed.bind(spec.id()))
			row.add_child(checkbox)
			entry["primary"] = checkbox
		"int", "float":
			var numeric_row := HBoxContainer.new()
			numeric_row.add_theme_constant_override("separation", 6)
			row.add_child(numeric_row)
			var slider := HSlider.new()
			slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			slider.min_value = float(spec.data.get("min", 0.0))
			slider.max_value = float(spec.data.get("max", 1.0))
			slider.step = float(spec.data.get("step", 0.01))
			slider.allow_greater = false
			slider.allow_lesser = false
			slider.tooltip_text = spec.description()
			slider.value_changed.connect(_on_numeric_changed.bind(spec.id()))
			numeric_row.add_child(slider)
			var exact := SpinBox.new()
			exact.name = "ExactValue"
			exact.custom_minimum_size = Vector2(92, 0)
			exact.min_value = slider.min_value
			exact.max_value = slider.max_value
			exact.step = slider.step
			exact.allow_greater = false
			exact.allow_lesser = false
			exact.update_on_text_changed = true
			exact.value_changed.connect(_on_numeric_changed.bind(spec.id()))
			numeric_row.add_child(exact)
			var unit := str(spec.data.get("unit", ""))
			if not unit.is_empty():
				var unit_label := Label.new()
				unit_label.text = unit
				unit_label.theme_type_variation = "DimLabel"
				numeric_row.add_child(unit_label)
			entry["primary"] = slider
			entry["exact"] = exact
		"enum":
			var options := OptionButton.new()
			options.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			options.tooltip_text = spec.description()
			for option in spec.data.get("options", []):
				if option is Dictionary:
					options.add_item(str(option.get("label", option.get("value", ""))))
					options.set_item_metadata(options.item_count - 1, str(option.get("value", "")))
			options.item_selected.connect(_on_enum_selected.bind(spec.id(), options))
			row.add_child(options)
			entry["primary"] = options
		_:
			var unsupported := Label.new()
			unsupported.text = "Unsupported live registry type: %s" % spec.value_type()
			unsupported.theme_type_variation = "DimLabel"
			row.add_child(unsupported)
			entry["primary"] = unsupported
	_controls_by_id[spec.id()] = entry


func _on_bool_changed(value: bool, setting_id: String) -> void:
	if not _syncing_controls:
		set_parameter_value(setting_id, value)


func _on_numeric_changed(value: float, setting_id: String) -> void:
	if _syncing_controls:
		return
	var entry: Dictionary = _controls_by_id.get(setting_id, {})
	var spec = entry.get("spec")
	set_parameter_value(setting_id, int(round(value)) if spec != null and spec.value_type() == "int" else value)


func _on_enum_selected(index: int, setting_id: String, options: OptionButton) -> void:
	if _syncing_controls or index < 0 or index >= options.item_count:
		return
	set_parameter_value(setting_id, str(options.get_item_metadata(index)))


func _replace_working_values(overrides: Dictionary, message: String) -> bool:
	if overrides.is_empty() or _working_profile == null:
		return false
	var next_profile = _working_profile.with_overrides(overrides)
	if not _valid_profile(next_profile):
		return false
	_working_profile = next_profile.detached_copy()
	_displayed_slot = SLOT_WORKING
	_sync_controls_from_working()
	_emit_preview(_working_profile, message)
	return true


func _sync_controls_from_working() -> void:
	_syncing_controls = true
	for setting_id in _controls_by_id.keys():
		var entry: Dictionary = _controls_by_id.get(setting_id, {})
		var value = _working_profile.value(setting_id) if _working_profile != null else null
		match str(entry.get("value_type", "")):
			"bool":
				var checkbox := entry.get("primary") as CheckBox
				if checkbox != null:
					checkbox.set_pressed_no_signal(value == true)
			"int", "float":
				var slider := entry.get("primary") as HSlider
				var exact := entry.get("exact") as SpinBox
				if slider != null and value != null:
					slider.set_value_no_signal(float(value))
				if exact != null and value != null:
					exact.set_value_no_signal(float(value))
			"enum":
				var options := entry.get("primary") as OptionButton
				if options != null:
					for index in range(options.item_count):
						if str(options.get_item_metadata(index)) == str(value):
							options.select(index)
							break
	_syncing_controls = false


func _emit_preview(profile, message: String) -> void:
	_refresh_all_text(message)
	profile_preview_requested.emit(profile.detached_copy())


func _profile_for_slot(slot: String):
	if slot == SLOT_REFERENCE:
		return _reference_profile
	if slot == SLOT_WORKING:
		return _working_profile
	return null


func _set_state(next_state: String) -> void:
	if not [STATE_HIDDEN, STATE_COMPACT, STATE_FULL].has(next_state):
		return
	_state = next_state
	_refresh_state_visibility()
	if _state == STATE_FULL:
		call_deferred("_focus_full_editor")
	else:
		_release_designer_focus()
	state_changed.emit(_state)


func _refresh_state_visibility() -> void:
	visible = _state != STATE_HIDDEN
	if _full_root != null:
		_full_root.visible = _state == STATE_FULL
	if _compact_root != null:
		_compact_root.visible = _state == STATE_COMPACT


func _focus_full_editor() -> void:
	if full_editor_visible() and _first_full_focus != null:
		_first_full_focus.grab_focus()


func _release_designer_focus() -> void:
	var viewport := get_viewport()
	var focus_owner := viewport.gui_get_focus_owner() if viewport != null else null
	if focus_owner is Control and is_ancestor_of(focus_owner):
		(focus_owner as Control).release_focus()


func _refresh_all_text(message: String) -> void:
	var has_a := _reference_profile != null
	var slot_description := "Showing %s · %s · Not saved" % [
		_displayed_slot,
		"immutable reference" if _displayed_slot == SLOT_REFERENCE else "detached working profile",
	]
	if _slot_state_label != null:
		_slot_state_label.text = slot_description
	if _compact_state_label != null:
		_compact_state_label.text = "%s shown · Designer · Not saved" % _displayed_slot
	if _status_label != null:
		_status_label.text = message
	for button in [_reference_button, _compact_reference_button]:
		if button != null:
			button.disabled = not has_a
	for button in [_working_button, _compact_working_button]:
		if button != null:
			button.disabled = _working_profile == null


func _valid_profile(profile) -> bool:
	return profile != null and profile.has_method("contract_conforms") and profile.contract_conforms()


func _valid_runtime_context(runtime_context: String) -> bool:
	return ["live_2d", "live_3d", "live_4d"].has(runtime_context)


func _owner_label(owner: String) -> String:
	return owner.trim_suffix("_PRESENTATION").to_lower().replace("_", " ").capitalize()
