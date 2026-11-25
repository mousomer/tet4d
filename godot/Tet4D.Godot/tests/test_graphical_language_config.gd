extends RefCounted

# config/graphical_language.json holds every Luminous tuning value; code holds
# none. The shipped file must validate, the validator must catch broken
# documents, and the renderer must use the configured values.

const ConfigScript = preload("res://scripts/ui/style/graphical_language_config.gd")
const ReplayVisuals = preload("res://scripts/ui/replay_visuals.gd")


func run() -> Array:
	var failures: Array = []
	failures.append_array(ConfigScript.validate())
	var shipped: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ConfigScript.CONFIG_PATH))
	for broken in [
		["drop a number", func(doc: Dictionary) -> void: doc["luminous"]["board"]["halo"].erase("alpha"), "luminous.board.halo.alpha"],
		["number as text", func(doc: Dictionary) -> void: doc["luminous"]["board"]["active"]["cell_emission"] = "bright", "luminous.board.active.cell_emission"],
		["drop a face", func(doc: Dictionary) -> void: doc["luminous"]["board"]["locked"]["face_shades"].erase("top"), "luminous.board.locked.face_shades.top"],
		["uneven gradient", func(doc: Dictionary) -> void: doc["luminous"]["board"]["halo"]["gradient_alphas"].pop_back(), "gradient_offsets"],
	]:
		var document: Dictionary = shipped.duplicate(true)
		(broken[1] as Callable).call(document)
		var found := ConfigScript.validate(document)
		if not found.any(func(message: String) -> bool: return message.contains(str(broken[2]))):
			failures.append("validate() should report '%s' (%s), got %s" % [broken[2], broken[0], found])
	var luminous := ReplayVisuals.DISPLAY_MODE_LUMINOUS
	var halo := ReplayVisuals.live_active_halo_material(luminous, 3)
	if not is_equal_approx(halo.albedo_color.a, ConfigScript.number("luminous.board.halo.alpha")):
		failures.append("halo alpha should come from config")
	if not is_equal_approx(ReplayVisuals.luminous_halo_scale(), ConfigScript.number("luminous.board.halo.scale_cells")):
		failures.append("halo scale should come from config")
	var front := (ReplayVisuals.live_3d_active_face_materials(luminous, 3, 1.0)["front"] as StandardMaterial3D)
	if not is_equal_approx(front.emission_energy_multiplier, ConfigScript.number("luminous.board.active.face_emission")):
		failures.append("active face emission should come from config")
	var bevel := ReplayVisuals.live_cell_bevel_materials(luminous, 3, false)
	if not is_equal_approx(float(bevel["width"]), ConfigScript.number("luminous.board.bevel.width_cells")):
		failures.append("bevel width should come from config")
	var edge := ReplayVisuals.board_edge_material(luminous, 0.3, 0.8)
	if edge.render_priority != ConfigScript.integer("luminous.board.edges.render_priority"):
		failures.append("board edge render priority should come from config")
	return failures
