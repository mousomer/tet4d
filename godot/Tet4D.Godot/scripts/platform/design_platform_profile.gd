extends RefCounted

class_name DesignPlatformProfile

# Canonical platform identity for the Design Laboratory.
#
# The Design Laboratory itself is platform independent: one catalogue, one
# scenario system, one A/B model, one evaluation schema, and one nomination
# schema. This profile exists so the few genuinely platform-specific concerns
# (export transport, lifecycle, window adaptation) resolve from a single named
# authority instead of scattered `OS.get_name()` comparisons. Platform is
# recorded as provenance only; it never participates in design semantics.

const PLATFORM_DESKTOP := "desktop"
const PLATFORM_ANDROID := "android"
const PLATFORM_IOS := "ios"

const PLATFORM_IDS := [PLATFORM_DESKTOP, PLATFORM_ANDROID, PLATFORM_IOS]

# Externalisation mechanism used to move a nominated bundle out of application
# storage and into somewhere a human can actually reach it.
const TRANSPORT_FILE_MANAGER := "file_manager"
const TRANSPORT_SYSTEM_DOCUMENT_PICKER := "system_document_picker"
const TRANSPORT_FILES_APP_DOCUMENTS := "files_app_documents"

const TRANSPORT_IDS := [
	TRANSPORT_FILE_MANAGER,
	TRANSPORT_SYSTEM_DOCUMENT_PICKER,
	TRANSPORT_FILES_APP_DOCUMENTS,
]

var _platform_id := PLATFORM_DESKTOP


func _init(platform_id: String = "") -> void:
	_platform_id = platform_id if PLATFORM_IDS.has(platform_id) else resolve_platform_id(OS.get_name())


# `OS.get_name()` is the only runtime input. Keeping resolution static and pure
# lets every platform branch be exercised from one headless host.
static func resolve_platform_id(os_name: String) -> String:
	match os_name:
		"Android":
			return PLATFORM_ANDROID
		"iOS", "iPadOS", "visionOS":
			return PLATFORM_IOS
		_:
			return PLATFORM_DESKTOP


static func for_os_name(os_name: String):
	return load("res://scripts/platform/design_platform_profile.gd").new(resolve_platform_id(os_name))


func platform_id() -> String:
	return _platform_id


func is_handheld() -> bool:
	return _platform_id == PLATFORM_ANDROID or _platform_id == PLATFORM_IOS


# The transport that externalises a nominated bundle on this platform.
func export_transport_id() -> String:
	match _platform_id:
		PLATFORM_ANDROID:
			return TRANSPORT_SYSTEM_DOCUMENT_PICKER
		PLATFORM_IOS:
			return TRANSPORT_FILES_APP_DOCUMENTS
		_:
			return TRANSPORT_FILE_MANAGER


# Handheld targets have no reliable desktop file manager, so the nominated
# bundle is additionally emitted as one portable archive that the platform
# share/document mechanism can hand to another application.
func requires_portable_archive() -> bool:
	return is_handheld()


# Android delivers a system Back gesture that would otherwise quit the process
# and discard an in-flight comparison session.
func has_system_back_gesture() -> bool:
	return _platform_id == PLATFORM_ANDROID


# Handheld windows are display-sized and may be inset by a notch, home
# indicator, or camera housing.
func requires_safe_area_insets() -> bool:
	return is_handheld()


func user_facing_export_hint() -> String:
	match export_transport_id():
		TRANSPORT_SYSTEM_DOCUMENT_PICKER:
			return "Use Share bundle to copy the archive through the Android document picker."
		TRANSPORT_FILES_APP_DOCUMENTS:
			return "The archive is in the Tet4D Designer folder of the Files app."
		_:
			return "The bundle directory has been revealed in your file manager."


# Provenance only. Consumers must never branch design meaning on these values.
func provenance() -> Dictionary:
	return {
		"platform": _platform_id,
		"export_transport": export_transport_id(),
	}
