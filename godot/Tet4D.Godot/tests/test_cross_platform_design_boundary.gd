extends RefCounted

# Proves that the Design Laboratory means the same thing on every distribution
# target. Windows, Android tablet, and iPadOS share one catalogue, one scenario
# system, one comparison model, one evaluation schema, and one nomination
# schema; platform appears in an exported bundle only as provenance.

const RegistryScript = preload("res://scripts/ui/settings/settings_registry.gd")
const CatalogScript = preload("res://scripts/presentation/built_in_style_catalog.gd")
const LibraryScript = preload("res://scripts/presentation/presentation_profile_library.gd")
const ScenarioCatalogScript = preload("res://scripts/design_lab/design_scenario_catalog.gd")
const PresetResolverScript = preload("res://scripts/design_lab/design_preset_resolver.gd")
const ExportBundleScript = preload("res://scripts/design_lab/design_export_bundle.gd")
const ExportTransportScript = preload("res://scripts/design_lab/design_export_transport.gd")
const PlatformProfileScript = preload("res://scripts/platform/design_platform_profile.gd")
const PhysicalKeyFallbackScript = preload("res://scripts/input/physical_key_fallback.gd")
const SafeAreaInsetsScript = preload("res://scripts/ui/safe_area_insets.gd")
const LiveInputContractScript = preload("res://scripts/input/live_input_contract.gd")

const ROOT := "user://test_cross_platform_design_boundary"
const PROFILE_DIRECTORY := ROOT + "/profiles"

# The platform names Godot reports for the three supported distribution
# targets, plus the desktop reference platform.
const PLATFORM_CASES := [
	["Windows", PlatformProfileScript.PLATFORM_DESKTOP, PlatformProfileScript.TRANSPORT_FILE_MANAGER],
	["Android", PlatformProfileScript.PLATFORM_ANDROID, PlatformProfileScript.TRANSPORT_SYSTEM_DOCUMENT_PICKER],
	["iOS", PlatformProfileScript.PLATFORM_IOS, PlatformProfileScript.TRANSPORT_FILES_APP_DOCUMENTS],
]


func run() -> Array:
	_cleanup()
	var failures: Array = []
	failures.append_array(_test_platform_profiles())
	failures.append_array(_test_safe_area_insets())
	failures.append_array(_test_physical_key_fallback())
	failures.append_array(_test_identical_nomination_semantics())
	failures.append_array(_test_portable_archive())
	_cleanup()
	return failures


func _test_platform_profiles() -> Array:
	var failures: Array = []
	for platform_case in PLATFORM_CASES:
		var profile = PlatformProfileScript.for_os_name(str(platform_case[0]))
		if profile.platform_id() != str(platform_case[1]):
			failures.append("%s should resolve to platform %s" % [platform_case[0], platform_case[1]])
		if profile.export_transport_id() != str(platform_case[2]):
			failures.append("%s should externalise through %s" % [platform_case[0], platform_case[2]])
		if profile.provenance().get("platform") != str(platform_case[1]):
			failures.append("%s provenance should name its own platform" % platform_case[0])
	var desktop = PlatformProfileScript.for_os_name("Windows")
	var android = PlatformProfileScript.for_os_name("Android")
	var ipados = PlatformProfileScript.for_os_name("iOS")
	if desktop.is_handheld() or not android.is_handheld() or not ipados.is_handheld():
		failures.append("only Android and iPadOS are handheld targets")
	if desktop.requires_portable_archive() or not android.requires_portable_archive():
		failures.append("only handheld targets need the single-file portable archive")
	if not android.has_system_back_gesture() or ipados.has_system_back_gesture() or desktop.has_system_back_gesture():
		failures.append("only Android delivers a system Back gesture")
	if desktop.requires_safe_area_insets() or not ipados.requires_safe_area_insets():
		failures.append("only handheld targets need safe-area insets")
	# An unknown platform name must degrade to the desktop reference rather
	# than inventing a fourth behaviour.
	if PlatformProfileScript.resolve_platform_id("Haiku") != PlatformProfileScript.PLATFORM_DESKTOP:
		failures.append("unknown platforms should fall back to the desktop reference target")
	return failures


func _test_safe_area_insets() -> Array:
	var failures: Array = []
	# Desktop: the safe area is the whole window, so the shell is untouched.
	var desktop := SafeAreaInsetsScript.resolve(Rect2i(0, 0, 1600, 960), Vector2i(1600, 960))
	if desktop != SafeAreaInsetsScript.ZERO:
		failures.append("a full-window safe area must produce no insets: %s" % str(desktop))
	# Landscape iPad with a home indicator and a camera housing on the left.
	var handheld := SafeAreaInsetsScript.resolve(Rect2i(59, 0, 2100, 1620), Vector2i(2160, 1640))
	if handheld != {"left": 59, "top": 0, "right": 1, "bottom": 20}:
		failures.append("landscape handheld insets should follow the reported safe area: %s" % str(handheld))
	# Degenerate or larger-than-window reports must not shrink the cockpit.
	if SafeAreaInsetsScript.resolve(Rect2i(0, 0, 4000, 4000), Vector2i(1600, 960)) != SafeAreaInsetsScript.ZERO:
		failures.append("a safe area larger than the window must be ignored")
	if SafeAreaInsetsScript.resolve(Rect2i(0, 0, 0, 0), Vector2i(1600, 960)) != SafeAreaInsetsScript.ZERO:
		failures.append("an empty safe area report must be ignored")
	return failures


func _test_physical_key_fallback() -> Array:
	var failures: Array = []
	var bound := PhysicalKeyFallbackScript.bound_keycodes(LiveInputContractScript.action_specs())
	if not bound.has(KEY_A) or not bound.has(KEY_ESCAPE) or not bound.has(KEY_Q):
		failures.append("the bound-keycode set should cover both the live contract and the shell keys")
	# A desktop US-layout keyboard reports identical logical and physical
	# keycodes, so the fallback never engages and Windows behaviour is unchanged.
	if PhysicalKeyFallbackScript.synthesize(_key_event(KEY_A, KEY_A), bound) != null:
		failures.append("matching logical and physical keycodes must not synthesize a fallback")
	# AZERTY: the key at the US 'A' position types 'Q'. 'Q' is itself bound
	# (4D W-axis), so the printed character wins and one press can never
	# dispatch two actions.
	if PhysicalKeyFallbackScript.synthesize(_key_event(KEY_Q, KEY_A), bound) != null:
		failures.append("a typed key that the contract already claims must not be reinterpreted positionally")
	# Dvorak: the key at the US 'W' position types ','. The contract claims no
	# comma, so the press falls back to its physical position and WASD keeps
	# working on an external keyboard.
	var positional := PhysicalKeyFallbackScript.synthesize(_key_event(KEY_COMMA, KEY_W), bound)
	if positional == null or positional.keycode != KEY_W:
		failures.append("an unclaimed typed character should resolve through its physical position")
	# Modifiers survive the fallback: 4D soft drop is Ctrl and must not be
	# confused with Shift+Ctrl.
	var modified := PhysicalKeyFallbackScript.synthesize(_key_event(KEY_COMMA, KEY_W, true), bound)
	if modified == null or not modified.ctrl_pressed:
		failures.append("modifier state must survive positional fallback")
	# A physical position the contract does not claim is left alone entirely.
	if PhysicalKeyFallbackScript.synthesize(_key_event(KEY_COMMA, KEY_F13), bound) != null:
		failures.append("an unbound physical position must not synthesize an action")
	return failures


func _test_identical_nomination_semantics() -> Array:
	var failures: Array = []
	var registry = RegistryScript.new()
	registry.load_from_path(RegistryScript.REGISTRY_PATH)
	var catalog = CatalogScript.new(registry)
	var library = LibraryScript.new(registry, PROFILE_DIRECTORY)
	var scenarios = ScenarioCatalogScript.new(registry)
	var resolver = PresetResolverScript.new(catalog, library)
	var built_ins: Array = catalog.list_styles()
	if built_ins.size() < 2:
		return ["built-in style catalog should expose comparable presets"]
	var candidate: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, str(built_ins[0].get("style_id")))
	var reference: Dictionary = resolver.resolve(PresetResolverScript.SOURCE_BUILT_IN, str(built_ins[1].get("style_id")))
	var exporter = ExportBundleScript.new(registry)
	var documents: Array = []
	for platform_case in PLATFORM_CASES:
		var profile = PlatformProfileScript.for_os_name(str(platform_case[0]))
		var identity := {
			"application_name": "Tet4D",
			"application_version": "0.9.0",
			"engine_build": "4.7.2.stable",
			"design_lab_schema_version": 1,
		}
		identity.merge(profile.provenance(), true)
		var destination := "%s/export_%s" % [ROOT, profile.platform_id()]
		var exported: Dictionary = exporter.export_candidate(candidate, reference, [], destination, identity, CatalogScript.CATALOG_SCHEMA_VERSION)
		if not bool(exported.get("ok", false)):
			failures.append("%s nomination export should succeed: %s" % [platform_case[0], exported.get("error", "")])
			continue
		documents.append([str(platform_case[1]), _read_json(str(exported.get("preset_path", ""))), _read_json(str(exported.get("summary_path", "")))])
	if documents.size() != PLATFORM_CASES.size():
		return failures
	var reference_preset: Dictionary = documents[0][1]
	for entry in documents:
		var platform_id := str(entry[0])
		var preset: Dictionary = entry[1]
		var summary: Dictionary = entry[2]
		# Provenance is recorded ...
		if str(preset.get("build_identity", {}).get("platform", "")) != platform_id:
			failures.append("%s preset.json should record its authoring platform as provenance" % platform_id)
		# ... and it changes nothing else about the design.
		for field in ["preset_type", "preset_schema_version", "preset_id", "presentation_profile_schema_version", "properties", "semantic_owners", "snapshot_hash"]:
			if preset.get(field) != reference_preset.get(field):
				failures.append("%s preset.json field %s must not vary by platform" % [platform_id, field])
		for field in ["summary_type", "summary_schema_version", "nominated_preset_id", "catalog_schema_version"]:
			if summary.get(field) != documents[0][2].get(field):
				failures.append("%s comparison_summary.json field %s must not vary by platform" % [platform_id, field])
	return failures


func _test_portable_archive() -> Array:
	var failures: Array = []
	var bundle := "%s/portable" % ROOT
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(bundle))
	for member in ["preset.json", "comparison_summary.json", "DESIGN_PROPOSAL.md"]:
		var handle := FileAccess.open(bundle.path_join(member), FileAccess.WRITE)
		if handle == null:
			return ["portable archive fixture could not be written"]
		handle.store_string("%s fixture\n" % member)
		handle.close()
	var android = ExportTransportScript.new(PlatformProfileScript.for_os_name("Android"))
	var archived: Dictionary = android.portable_archive(bundle, "%s/portable.zip" % ROOT)
	if not bool(archived.get("ok", false)):
		return ["portable archive should be produced for handheld targets: %s" % archived.get("error", "")]
	if archived.get("members") != ["DESIGN_PROPOSAL.md", "comparison_summary.json", "preset.json"]:
		failures.append("portable archive membership must be deterministic and sorted: %s" % str(archived.get("members")))
	var reader := ZIPReader.new()
	if reader.open(ProjectSettings.globalize_path(str(archived.get("archive_path", "")))) != OK:
		failures.append("portable archive should be a readable zip")
	else:
		var members: Array = []
		for name in reader.get_files():
			if not str(name).ends_with("/"):
				members.append(str(name))
		if members != ["portable/DESIGN_PROPOSAL.md", "portable/comparison_summary.json", "portable/preset.json"]:
			failures.append("portable archive should carry the bundle directory name: %s" % str(members))
		reader.close()
	# Every platform must reach the bundle without repository access.
	for platform_case in PLATFORM_CASES:
		var transport = ExportTransportScript.new(PlatformProfileScript.for_os_name(str(platform_case[0])))
		var plan: Dictionary = transport.share_plan("%s/portable.zip" % ROOT, bundle)
		if plan.get("transport") != str(platform_case[2]):
			failures.append("%s share plan should use %s" % [platform_case[0], platform_case[2]])
		if not bool(plan.get("user_accessible_without_repository", false)):
			failures.append("%s must expose the nominated bundle without repository access" % platform_case[0])
		if str(plan.get("hint", "")).is_empty():
			failures.append("%s share plan should explain the mechanism to the designer" % platform_case[0])
	return failures


static func _key_event(keycode: int, physical_keycode: int, ctrl: bool = false) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = keycode
	event.physical_keycode = physical_keycode
	event.pressed = true
	event.ctrl_pressed = ctrl
	return event


static func _read_json(path: String) -> Dictionary:
	if path.is_empty() or not FileAccess.file_exists(path):
		return {}
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if parsed is Dictionary else {}


static func _cleanup() -> void:
	_remove_tree(ProjectSettings.globalize_path(ROOT))


static func _remove_tree(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null:
		return
	directory.list_dir_begin()
	var name := directory.get_next()
	while not name.is_empty():
		var child := path.path_join(name)
		if directory.current_is_dir():
			_remove_tree(child)
		else:
			DirAccess.remove_absolute(child)
		name = directory.get_next()
	directory.list_dir_end()
	DirAccess.remove_absolute(path)
