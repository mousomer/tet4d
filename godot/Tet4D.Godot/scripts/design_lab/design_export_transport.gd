extends RefCounted

class_name DesignExportTransport

# Platform transport for an already generated nomination bundle.
#
#     DesignExportBundle  ->  preset.json / comparison_summary.json /
#                             DESIGN_PROPOSAL.md   (platform neutral)
#                       |
#     DesignExportTransport
#                       +-- desktop  : reveal the directory in the file manager
#                       +-- Android  : system document picker
#                       +-- iPadOS   : Files-app visible Documents directory
#
# This class never inspects, rewrites, or re-schemas bundle contents. It only
# moves the finished bundle somewhere a human can reach on the current
# platform, so an installed application never requires repository access to
# retrieve a nominated design.

const DesignPlatformProfileScript = preload("res://scripts/platform/design_platform_profile.gd")

const ARCHIVE_EXTENSION := ".tet4ddesign.zip"

var _profile


func _init(profile = null) -> void:
	_profile = profile if profile != null else DesignPlatformProfileScript.new()


func profile():
	return _profile


# Deterministic single-file archive of the bundle directory. Entry order is
# sorted and relative, so two hosts archiving identical bundle contents produce
# byte-comparable member lists.
func portable_archive(bundle_directory: String, archive_path: String = "") -> Dictionary:
	var source := bundle_directory.trim_suffix("/")
	if source.is_empty() or not DirAccess.dir_exists_absolute(ProjectSettings.globalize_path(source)):
		return _failure("A generated bundle directory is required before it can be shared.")
	var members := _collect_members(source)
	if members.is_empty():
		return _failure("The bundle directory contains no files to share.")
	var destination := archive_path if not archive_path.is_empty() else "%s%s" % [source, ARCHIVE_EXTENSION]
	var packer := ZIPPacker.new()
	var open_error := packer.open(ProjectSettings.globalize_path(destination), ZIPPacker.APPEND_CREATE)
	if open_error != OK:
		return _failure("Portable design archive could not be created (error %s)." % open_error)
	var bundle_name := source.get_file()
	for member in members:
		var bytes := FileAccess.get_file_as_bytes(source.path_join(str(member)))
		if bytes.is_empty() and FileAccess.get_open_error() != OK:
			packer.close()
			return _failure("Portable design archive could not read %s." % str(member))
		packer.start_file("%s/%s" % [bundle_name, str(member)])
		packer.write_file(bytes)
		packer.close_file()
	var close_error := packer.close()
	if close_error != OK:
		return _failure("Portable design archive could not be finalised (error %s)." % close_error)
	return _success({
		"archive_path": destination,
		"members": members,
		"entry_count": members.size(),
	})


# What externalisation will do on this platform, resolved without performing
# any OS call so it can be asserted headlessly.
func share_plan(archive_path: String, bundle_directory: String) -> Dictionary:
	var transport := str(_profile.export_transport_id())
	var target := archive_path if _profile.requires_portable_archive() else bundle_directory
	return {
		"transport": transport,
		"target": target,
		"requires_native_dialog": transport == DesignPlatformProfileScript.TRANSPORT_SYSTEM_DOCUMENT_PICKER,
		"user_accessible_without_repository": true,
		"hint": str(_profile.user_facing_export_hint()),
	}


# Documents root that the platform exposes to the user. On iOS the exported
# Info.plist marks this directory as file-sharing enabled, which is what makes
# it visible in the Files app without any native plugin.
func user_visible_root() -> String:
	if str(_profile.export_transport_id()) == DesignPlatformProfileScript.TRANSPORT_FILES_APP_DOCUMENTS:
		var documents := OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)
		if not documents.strip_edges().is_empty():
			return documents
	return ProjectSettings.globalize_path("user://")


func publish(bundle_directory: String) -> Dictionary:
	if not _profile.requires_portable_archive():
		return _success({
			"archive_path": "",
			"plan": share_plan("", bundle_directory),
		})
	var archived := portable_archive(bundle_directory)
	if not bool(archived.get("ok", false)):
		return archived
	var archive_path := str(archived.get("archive_path", ""))
	var visible := _install_into_user_visible_root(archive_path)
	if not bool(visible.get("ok", false)):
		return visible
	var published := str(visible.get("archive_path", archive_path))
	return _success({
		"archive_path": published,
		"entry_count": archived.get("entry_count", 0),
		"plan": share_plan(published, bundle_directory),
	})


# Performs the actual OS handoff. Returns a structured refusal rather than
# failing hard when the mechanism is unavailable (headless CI, for example), so
# nomination itself is never blocked by transport.
func execute_share(archive_path: String, bundle_directory: String) -> Dictionary:
	var plan := share_plan(archive_path, bundle_directory)
	var transport := str(plan.get("transport", ""))
	var target := str(plan.get("target", ""))
	if transport == DesignPlatformProfileScript.TRANSPORT_SYSTEM_DOCUMENT_PICKER:
		if not DisplayServer.has_feature(DisplayServer.FEATURE_NATIVE_DIALOG_FILE):
			return _failure("This device has no system document picker; the archive is at %s." % target)
		DisplayServer.file_dialog_show(
			"Save Tet4D design nomination",
			target.get_base_dir(),
			target.get_file(),
			false,
			DisplayServer.FILE_DIALOG_MODE_SAVE_FILE,
			["*.zip"],
			Callable()
		)
		return _success({"mechanism": transport, "target": target})
	if transport == DesignPlatformProfileScript.TRANSPORT_FILES_APP_DOCUMENTS:
		# The archive already lives in the file-sharing enabled Documents
		# directory; no further OS call is needed to make it reachable.
		return _success({"mechanism": transport, "target": target})
	if OS.has_method("shell_show_in_file_manager"):
		OS.shell_show_in_file_manager(ProjectSettings.globalize_path(target), true)
		return _success({"mechanism": transport, "target": target})
	OS.shell_open("file://%s" % ProjectSettings.globalize_path(target))
	return _success({"mechanism": transport, "target": target})


func _install_into_user_visible_root(archive_path: String) -> Dictionary:
	var root := user_visible_root()
	var absolute_archive := ProjectSettings.globalize_path(archive_path)
	if root.is_empty() or absolute_archive.get_base_dir() == root.trim_suffix("/"):
		return _success({"archive_path": archive_path})
	var destination := root.trim_suffix("/").path_join(absolute_archive.get_file())
	if DirAccess.copy_absolute(absolute_archive, destination) != OK:
		# A non-writable documents root is not a nomination failure; the caller
		# still has the application-private archive.
		return _success({"archive_path": archive_path})
	return _success({"archive_path": destination})


static func _collect_members(directory: String) -> Array:
	var members: Array = []
	var listing := DirAccess.open(directory)
	if listing == null:
		return members
	listing.list_dir_begin()
	var entry := listing.get_next()
	while not entry.is_empty():
		if not listing.current_is_dir():
			members.append(entry)
		entry = listing.get_next()
	listing.list_dir_end()
	members.sort()
	return members


static func _success(extra: Dictionary = {}) -> Dictionary:
	var result := {"ok": true, "error": ""}
	result.merge(extra, true)
	return result


static func _failure(error: String) -> Dictionary:
	return {"ok": false, "error": error}
