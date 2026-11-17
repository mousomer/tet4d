extends Node3D

# Presentation only: native has already mapped domain cells into display coordinates.
const Grid = preload("res://scripts/rendering/grid_renderer.gd")
const Model = preload("res://scripts/presentation/board_presentation_model.gd")
const Visuals = preload("res://scripts/ui/replay_visuals.gd")
var charts: Array = []
var labels: Array = []


func rebuild(snapshot: Dictionary, presentation, rebuild_grid: Callable, display_mode: String) -> void:
	while charts.size() < 2:
		var grid = Grid.new()
		grid.name = "ExplorerChart" + ("A" if charts.is_empty() else "B")
		add_child(grid)
		charts.append(grid)
		var label := Label3D.new()
		label.text = "Chart A" if labels.is_empty() else "Chart B"
		label.font_size = Visuals.BOARD_LABEL_FONT_SIZE
		label.pixel_size = Visuals.BOARD_LABEL_PIXEL_SIZE
		label.outline_size = Visuals.BOARD_LABEL_OUTLINE_SIZE
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		add_child(label)
		labels.append(label)
	var shape: Array = snapshot.explorer_charts.shape
	var local_snapshot := snapshot.duplicate(true)
	local_snapshot.board_shape = shape
	local_snapshot.active_cells = []
	local_snapshot.probe_markers = []
	var local = Model.new()
	local.configure(local_snapshot)
	for domain in 2:
		var display_origin: Array = snapshot.explorer_charts.origins[domain]
		charts[domain].position = presentation.render_cell_world_position(display_origin) - local.render_cell_world_position([0, 0])
		rebuild_grid.call(charts[domain], local)
		# The label follows each chart's top edge and uses existing board typography tokens.
		labels[domain].position = charts[domain].position + local.render_world_position([float(shape[0] - 1) / 2.0, -1])
		labels[domain].modulate = Visuals.color_for_role(Visuals.ROLE_TEXT, display_mode)
