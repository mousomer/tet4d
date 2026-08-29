extends PanelContainer

class_name DesignLaboratoryPanel

const BuiltInStyleCatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const PresentationProfileLibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const PresentationProfileScript = preload("res://scripts/presentation/presentation_profile.gd")
const DesignScenarioCatalogScript = preload("res://scripts/design_lab/design_scenario_catalog.gd")
const DesignPresetResolverScript = preload("res://scripts/design_lab/design_preset_resolver.gd")
const DesignComparisonSessionScript = preload("res://scripts/design_lab/design_comparison_session.gd")
const DesignEvaluationStoreScript = preload("res://scripts/design_lab/design_evaluation_store.gd")
const DesignCaptureStoreScript = preload("res://scripts/design_lab/design_capture_store.gd")
const DesignExportBundleScript = preload("res://scripts/design_lab/design_export_bundle.gd")

signal close_requested()

const DEFAULT_EXPORT_DIRECTORY := "user://design_lab/exports"

var _registry
var _catalog
var _library
var _scenarios
var _resolver
var _comparison = DesignComparisonSessionScript.new()
var _evaluations = DesignEvaluationStoreScript.new()
var _captures = DesignCaptureStoreScript.new()
var _exporter
var _load_scenario: Callable
var _apply_profile: Callable
var _current_fingerprint: Callable
var _capture_image: Callable
var _build_identity: Callable
var _edit_candidate: Callable

var _scenario_select: OptionButton
var _preset_a_select: OptionButton
var _preset_b_select: OptionButton
var _blind_check: CheckBox
var _arm_a_button: Button
var _arm_b_button: Button
var _toggle_button: Button
var _status: Label
var _preset_detail: Label
var _preference_select: OptionButton
var _rating_inputs: Dictionary = {}
var _notes: TextEdit
var _nominate_select: OptionButton


func configure(registry, callbacks: Dictionary) -> bool:
	_registry = registry
	if _registry == null:
		return false
	_catalog = BuiltInStyleCatalogScript.new(_registry)
	_library = PresentationProfileLibraryScript.new(_registry)
	_scenarios = DesignScenarioCatalogScript.new(_registry)
	_resolver = DesignPresetResolverScript.new(_catalog, _library)
	_exporter = DesignExportBundleScript.new(_registry)
	_load_scenario = callbacks.get("load_scenario", Callable())
	_apply_profile = callbacks.get("apply_profile", Callable())
	_current_fingerprint = callbacks.get("current_fingerprint", Callable())
	_capture_image = callbacks.get("capture_image", Callable())
	_build_identity = callbacks.get("build_identity", Callable())
	_edit_candidate = callbacks.get("edit_candidate", Callable())
	if [_load_scenario, _apply_profile, _current_fingerprint, _capture_image, _build_identity, _edit_candidate].any(func(callback: Callable) -> bool: return not callback.is_valid()):
		return false
	_build_ui()
	_refresh_catalogs()
	return _catalog.diagnostics().is_empty() and _scenarios.diagnostics().is_empty()


func open() -> void:
	visible = true
	_refresh_catalogs()
	if _scenario_select != null:
		_scenario_select.grab_focus()


func close() -> void:
	visible = false


func interaction_owns_input() -> bool:
	return visible


func deterministic_snapshot() -> Dictionary:
	return {
		"visible": visible,
		"scenario_count": _scenarios.list_scenarios().size() if _scenarios != null else 0,
		"preset_count": _resolver.list_presets().size() if _resolver != null else 0,
		"comparison": _comparison.snapshot(),
		"status": _status.text if _status != null else "",
	}


func _build_ui() -> void:
	for child in get_children():
		remove_child(child)
		child.queue_free()
	name = "DesignLaboratoryPanel"
	custom_minimum_size = Vector2(440, 560)
	var margin := MarginContainer.new()
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 16)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	margin.add_child(root)
	var header := HBoxContainer.new()
	root.add_child(header)
	var title := Label.new()
	title.text = "DESIGN LABORATORY"
	title.theme_type_variation = "AccentLabel"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title)
	var close_button := Button.new()
	close_button.text = "Close"
	close_button.pressed.connect(func() -> void: close_requested.emit())
	header.add_child(close_button)
	var subtitle := Label.new()
	subtitle.text = "Compare frozen presentation presets on one deterministic state. Production defaults never change."
	subtitle.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	subtitle.theme_type_variation = "SecondaryLabel"
	root.add_child(subtitle)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(scroll)
	var form := VBoxContainer.new()
	form.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	form.add_theme_constant_override("separation", 8)
	scroll.add_child(form)
	form.add_child(_section_label("SCENARIO"))
	_scenario_select = OptionButton.new()
	_scenario_select.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	form.add_child(_scenario_select)
	form.add_child(_section_label("PRESET CATALOG"))
	_preset_a_select = OptionButton.new()
	_preset_b_select = OptionButton.new()
	form.add_child(_labeled_control("A", _preset_a_select))
	form.add_child(_labeled_control("B", _preset_b_select))
	_preset_a_select.item_selected.connect(func(_index: int) -> void: _update_preset_detail())
	_preset_b_select.item_selected.connect(func(_index: int) -> void: _update_preset_detail())
	_preset_detail = Label.new()
	_preset_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_preset_detail.theme_type_variation = "SecondaryLabel"
	form.add_child(_preset_detail)
	var catalog_actions := HBoxContainer.new()
	var apply_button := Button.new()
	apply_button.text = "Apply"
	apply_button.pressed.connect(_apply_selected_b)
	catalog_actions.add_child(apply_button)
	var duplicate_button := Button.new()
	duplicate_button.text = "Duplicate / Edit"
	duplicate_button.pressed.connect(_duplicate_selected_b)
	catalog_actions.add_child(duplicate_button)
	form.add_child(catalog_actions)
	form.add_child(_section_label("A/B COMPARISON"))
	_blind_check = CheckBox.new()
	_blind_check.text = "Blind labels"
	_blind_check.button_pressed = true
	_blind_check.toggled.connect(func(enabled: bool) -> void:
		if _comparison.active():
			_comparison.set_blind(enabled)
			_refresh_arm_labels()
	)
	form.add_child(_blind_check)
	var start_button := Button.new()
	start_button.text = "Start comparison"
	start_button.pressed.connect(_start_comparison)
	form.add_child(start_button)
	var arm_row := HBoxContainer.new()
	_arm_a_button = Button.new()
	_arm_a_button.text = "A"
	_arm_a_button.pressed.connect(func() -> void: _activate_arm("A"))
	arm_row.add_child(_arm_a_button)
	_arm_b_button = Button.new()
	_arm_b_button.text = "B"
	_arm_b_button.pressed.connect(func() -> void: _activate_arm("B"))
	arm_row.add_child(_arm_b_button)
	_toggle_button = Button.new()
	_toggle_button.text = "Toggle"
	_toggle_button.pressed.connect(_toggle_arm)
	arm_row.add_child(_toggle_button)
	var reset_button := Button.new()
	reset_button.text = "Reset scenario"
	reset_button.pressed.connect(_reset_scenario)
	arm_row.add_child(reset_button)
	form.add_child(arm_row)
	var capture_row := HBoxContainer.new()
	for arm in ["A", "B"]:
		var capture_button := Button.new()
		capture_button.text = "Capture %s" % arm
		capture_button.pressed.connect(_capture_arm.bind(arm))
		capture_row.add_child(capture_button)
	var pair_button := Button.new()
	pair_button.text = "Capture pair"
	pair_button.pressed.connect(_capture_pair)
	capture_row.add_child(pair_button)
	form.add_child(capture_row)
	form.add_child(_section_label("EVALUATION"))
	_preference_select = OptionButton.new()
	for preference in ["Prefer A", "Prefer B", "No preference"]:
		_preference_select.add_item(preference)
	form.add_child(_labeled_control("Preference", _preference_select))
	for rating_id in DesignEvaluationStoreScript.RATING_IDS:
		var rating := SpinBox.new()
		rating.min_value = 0
		rating.max_value = 5
		rating.step = 1
		rating.value = 0
		rating.allow_greater = false
		rating.tooltip_text = "0 = not rated; 1-5 = ordinal judgment"
		_rating_inputs[rating_id] = rating
		form.add_child(_labeled_control(str(rating_id).replace("_", " ").capitalize(), rating))
	_notes = TextEdit.new()
	_notes.custom_minimum_size = Vector2(0, 84)
	_notes.placeholder_text = "Optional observations and tradeoffs"
	form.add_child(_notes)
	var save_evaluation := Button.new()
	save_evaluation.text = "Save evaluation"
	save_evaluation.pressed.connect(_save_evaluation)
	form.add_child(save_evaluation)
	form.add_child(_section_label("NOMINATION / EXPORT"))
	_nominate_select = OptionButton.new()
	form.add_child(_labeled_control("Candidate", _nominate_select))
	var export_button := Button.new()
	export_button.text = "Nominate and export proposal"
	export_button.pressed.connect(_export_nomination)
	form.add_child(export_button)
	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.theme_type_variation = "SecondaryLabel"
	root.add_child(_status)


func _refresh_catalogs() -> void:
	if _resolver == null:
		return
	_fill_scenarios()
	_fill_presets()
	_update_preset_detail()


func _fill_scenarios() -> void:
	_scenario_select.clear()
	for record in _scenarios.list_scenarios():
		_scenario_select.add_item(str(record.get("display_name", "Scenario")))
		_scenario_select.set_item_metadata(_scenario_select.item_count - 1, record.duplicate(true))


func _fill_presets() -> void:
	var presets: Array = _resolver.list_presets()
	for select in [_preset_a_select, _preset_b_select, _nominate_select]:
		select.clear()
		for descriptor in presets:
			var prefix := "BUILT-IN" if bool(descriptor.get("read_only", false)) else "USER"
			select.add_item("%s · %s" % [prefix, str(descriptor.get("display_name", "Preset"))])
			select.set_item_metadata(select.item_count - 1, descriptor.duplicate(true))
	if _preset_b_select.item_count > 1:
		_preset_b_select.select(1)
		_nominate_select.select(1)


func _selected_descriptor(select: OptionButton) -> Dictionary:
	if select == null or select.selected < 0:
		return {}
	var metadata = select.get_item_metadata(select.selected)
	return metadata.duplicate(true) if metadata is Dictionary else {}


func _resolve_selected(select: OptionButton) -> Dictionary:
	var descriptor := _selected_descriptor(select)
	return _resolver.resolve(str(descriptor.get("source_kind", "")), str(descriptor.get("preset_id", "")))


func _start_comparison() -> void:
	var scenario := _selected_scenario()
	var loaded: Dictionary = _load_scenario.call(scenario)
	if not bool(loaded.get("ok", false)):
		_set_status(str(loaded.get("error", "Scenario could not be loaded.")), true)
		return
	var started := _comparison.start(scenario, _resolve_selected(_preset_a_select), _resolve_selected(_preset_b_select), loaded.get("fingerprint", {}), _blind_check.button_pressed)
	if not bool(started.get("ok", false)):
		_set_status(str(started.get("error", "Comparison could not start.")), true)
		return
	_apply_snapshot(started.get("profile", {}))
	_refresh_arm_labels()
	_set_status("Comparison %s started on %s." % [_comparison.session_id(), scenario.get("display_name", "scenario")])


func _activate_arm(arm: String) -> bool:
	if not _comparison.active():
		_set_status("Start a comparison first.", true)
		return false
	var result := _comparison.activate(arm, _current_fingerprint.call())
	if not bool(result.get("ok", false)):
		_set_status(str(result.get("error", "Arm switch failed.")), true)
		return false
	_apply_snapshot(result.get("profile", {}))
	_refresh_arm_labels()
	return true


func _toggle_arm() -> void:
	if not _comparison.active():
		_set_status("Start a comparison first.", true)
		return
	_activate_arm("B" if _comparison.active_arm() == "A" else "A")


func _reset_scenario() -> void:
	if not _comparison.active():
		_set_status("Start a comparison first.", true)
		return
	var session := _comparison.snapshot()
	var loaded: Dictionary = _load_scenario.call(session.get("scenario", {}))
	if not bool(loaded.get("ok", false)) or str(loaded.get("fingerprint_hash", "")) != str(session.get("non_style_hash", "")):
		_set_status("Scenario reset did not reproduce the frozen deterministic identity.", true)
		return
	_comparison.activate("A", loaded.get("fingerprint", {}))
	_apply_snapshot(_comparison.arm_profile_snapshot("A"))
	_refresh_arm_labels()
	_set_status("Scenario reset to canonical state and arm A.")


func _apply_selected_b() -> void:
	var resolved := _resolve_selected(_preset_b_select)
	if not bool(resolved.get("ok", false)) or not _apply_snapshot(resolved.get("snapshot", {})):
		_set_status(str(resolved.get("error", "Preset could not be applied.")), true)
		return
	_set_status("Applied %s without changing gameplay state." % resolved.get("descriptor", {}).get("display_name", "preset"))


func _duplicate_selected_b() -> void:
	var descriptor := _selected_descriptor(_preset_b_select)
	var result: Dictionary = _resolver.duplicate_as_candidate(str(descriptor.get("source_kind", "")), str(descriptor.get("preset_id", "")))
	if not bool(result.get("ok", false)):
		_set_status(str(result.get("error", "Candidate could not be duplicated.")), true)
		return
	var profile_id := str(result.get("record", {}).get("profile_id", ""))
	var resolved: Dictionary = _resolver.resolve(DesignPresetResolverScript.SOURCE_USER, profile_id)
	if not bool(resolved.get("ok", false)) or not _apply_snapshot(resolved.get("snapshot", {})):
		_set_status(str(resolved.get("error", "Candidate could not be opened for editing.")), true)
		return
	_refresh_catalogs()
	_edit_candidate.call(profile_id)
	_set_status("Created mutable user candidate %s and opened it in the live Designer." % result.get("record", {}).get("display_name", "candidate"))


func _save_evaluation() -> void:
	if not _comparison.active():
		_set_status("Start a comparison before saving an evaluation.", true)
		return
	var ratings: Dictionary = {}
	for rating_id in _rating_inputs.keys():
		var value := int((_rating_inputs.get(rating_id) as SpinBox).value)
		if value > 0:
			ratings[rating_id] = value
	var preference: String = ["prefer_a", "prefer_b", "no_preference"][_preference_select.selected]
	var created := _evaluations.create_record(_comparison.snapshot(), preference, ratings, _notes.text, _build_identity.call(), BuiltInStyleCatalogScript.CATALOG_SCHEMA_VERSION)
	var saved := _evaluations.save_record(created.get("record", {})) if bool(created.get("ok", false)) else created
	if not bool(saved.get("ok", false)):
		_set_status(str(saved.get("error", "Evaluation could not be saved.")), true)
		return
	_set_status("Evaluation saved with immutable preset provenance.")


func _capture_arm(arm: String) -> void:
	if not await _activate_and_settle(arm):
		return
	var image = _capture_image.call()
	var result := _captures.capture_arm(image, _comparison.snapshot(), arm, _build_identity.call(), BuiltInStyleCatalogScript.CATALOG_SCHEMA_VERSION)
	_set_status("Captured %s at %s." % [arm, result.get("directory", "")]) if bool(result.get("ok", false)) else _set_status(str(result.get("error", "Capture failed.")), true)


func _capture_pair() -> void:
	if not _comparison.active():
		_set_status("Start a comparison before capturing.", true)
		return
	var restore_arm := _comparison.active_arm()
	for arm in ["A", "B"]:
		if not await _activate_and_settle(arm):
			return
		var result := _captures.capture_arm(_capture_image.call(), _comparison.snapshot(), arm, _build_identity.call(), BuiltInStyleCatalogScript.CATALOG_SCHEMA_VERSION)
		if not bool(result.get("ok", false)):
			_set_status(str(result.get("error", "Pair capture failed.")), true)
			return
	await _activate_and_settle(restore_arm)
	_set_status("Captured blind-safe A/B pair with separate provenance metadata.")


func _activate_and_settle(arm: String) -> bool:
	if not _activate_arm(arm):
		return false
	await RenderingServer.frame_post_draw
	return true


func _export_nomination() -> void:
	var candidate := _resolve_selected(_nominate_select)
	var reference := _resolve_selected(_preset_a_select)
	var evaluations := _evaluations.records_for_preset(str(candidate.get("descriptor", {}).get("source_kind", "")), str(candidate.get("descriptor", {}).get("preset_id", ""))) if bool(candidate.get("ok", false)) else []
	var result: Dictionary = _exporter.export_candidate(candidate, reference, evaluations, DEFAULT_EXPORT_DIRECTORY, _build_identity.call(), BuiltInStyleCatalogScript.CATALOG_SCHEMA_VERSION)
	if not bool(result.get("ok", false)):
		_set_status(str(result.get("error", "Nomination export failed.")), true)
		return
	_set_status("Nominated proposal exported to %s" % ProjectSettings.globalize_path(str(result.get("directory", ""))))


func _apply_snapshot(snapshot: Dictionary) -> bool:
	var profile = PresentationProfileScript.from_snapshot(_registry, snapshot)
	return profile != null and profile.contract_conforms() and bool(_apply_profile.call(profile.detached_copy()))


func _selected_scenario() -> Dictionary:
	if _scenario_select == null or _scenario_select.selected < 0:
		return {}
	var metadata = _scenario_select.get_item_metadata(_scenario_select.selected)
	return metadata.duplicate(true) if metadata is Dictionary else {}


func _refresh_arm_labels() -> void:
	_arm_a_button.text = _comparison.arm_label("A")
	_arm_b_button.text = _comparison.arm_label("B")
	_arm_a_button.disabled = not _comparison.active()
	_arm_b_button.disabled = not _comparison.active()
	_toggle_button.disabled = not _comparison.active()


func _update_preset_detail() -> void:
	if _preset_detail == null:
		return
	var descriptor := _selected_descriptor(_preset_b_select)
	_preset_detail.text = "%s · %s · %s\n%s" % [
		str(descriptor.get("preset_id", "")),
		str(descriptor.get("status", "candidate")),
		str(descriptor.get("provenance", "")),
		str(descriptor.get("description", "")),
	]


func _set_status(text: String, error: bool = false) -> void:
	if _status != null:
		_status.text = ("ERROR · " if error else "OK · ") + text


static func _section_label(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.theme_type_variation = "AccentLabel"
	return label


static func _labeled_control(text: String, control: Control) -> HBoxContainer:
	var row := HBoxContainer.new()
	var label := Label.new()
	label.text = text
	label.custom_minimum_size = Vector2(138, 0)
	row.add_child(label)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(control)
	return row
