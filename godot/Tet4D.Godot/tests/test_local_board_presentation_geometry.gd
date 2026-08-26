extends RefCounted

const LocalBoardPresentationGeometryScript = preload("res://scripts/presentation/local_board_presentation_geometry.gd")
const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")
const TraceCoordinateMapperScript = preload("res://scripts/rendering/trace_coordinate_mapper.gd")


func run() -> Array:
	var failures: Array = []
	_test_canonical_contract(failures)
	_test_odd_even_and_degenerate_centering(failures)
	_test_dimensional_chain(failures)
	_test_exact_basis_adaptation(failures)
	_test_signed_basis_orientation(failures)
	return failures


func _test_canonical_contract(failures: Array) -> void:
	var geometry := LocalBoardPresentationGeometryScript.new()
	if not geometry.configure([4, 7, 11], [1, 2, 3]):
		failures.append("canonical geometry should accept positive local dimensions and authoritative axes")
		return
	if geometry.local_dimensions != [4, 7, 11] or geometry.axis_mapping != [1, 2, 3]:
		failures.append("canonical geometry must retain local dimensions and authoritative axis mapping")
	_assert_vector(failures, geometry.local_extent, Vector3(4.0, 7.0, 11.0), "asymmetric local extent")
	_assert_vector(failures, geometry.center, Vector3.ZERO, "canonical local center")
	if geometry.cell_size != 1.0 or geometry.cell_count() != 308:
		failures.append("canonical unit cell convention should determine the asymmetric cell count")
	_assert_vector(failures, geometry.cell_transform([0, 0, 0]).origin, Vector3(-1.5, 3.0, -5.0), "minimum asymmetric cell center")
	_assert_vector(failures, geometry.cell_transform([3, 6, 10]).origin, Vector3(1.5, -3.0, 5.0), "maximum asymmetric cell center")
	var first_bounds: Dictionary = geometry.cell_bounds([0, 0, 0])
	_assert_vector(failures, first_bounds.get("min", Vector3.ZERO), Vector3(-2.0, 2.5, -5.5), "first cell lower bounds")
	_assert_vector(failures, first_bounds.get("max", Vector3.ZERO), Vector3(-1.0, 3.5, -4.5), "first cell upper bounds")
	var local_bounds: Dictionary = geometry.local_bounds()
	_assert_vector(failures, local_bounds.get("min", Vector3.ZERO), Vector3(-2.0, -3.5, -5.5), "asymmetric board minimum")
	_assert_vector(failures, local_bounds.get("max", Vector3.ZERO), Vector3(2.0, 3.5, 5.5), "asymmetric board maximum")
	if geometry.boundary_geometry().size() != 12:
		failures.append("canonical boundary must contain exactly twelve outer segments")
	var face_sets := geometry.grid_geometry()
	if face_sets.size() != 6:
		failures.append("canonical grid must expose all six local boundary faces")
	for face in face_sets:
		var face_axis := int(face.get("face_axis", -1))
		var expected := 0
		for division_axis in range(3):
			if division_axis != face_axis:
				expected += int(geometry.local_dimensions[division_axis]) - 1
		if face.get("segments", []).size() != expected:
			failures.append("face %d should contain %d canonical interior grid segments" % [face_axis, expected])
	var invalid := LocalBoardPresentationGeometryScript.new()
	if invalid.configure([4, 0, 7], [1, 2, 3]) or invalid.is_configured():
		failures.append("presentation geometry must not invent validity for zero semantic extents")


func _test_odd_even_and_degenerate_centering(failures: Array) -> void:
	for dimensions in [[4, 6, 8], [5, 7, 9], [4, 7, 10], [1, 5, 8], [1, 1, 1]]:
		var geometry := LocalBoardPresentationGeometryScript.new()
		geometry.configure(dimensions, [1, 2, 3])
		var min_coordinate := [0, 0, 0]
		var max_coordinate := [int(dimensions[0]) - 1, int(dimensions[1]) - 1, int(dimensions[2]) - 1]
		_assert_vector(
			failures,
			(geometry.cell_position(min_coordinate) + geometry.cell_position(max_coordinate)) * 0.5,
			Vector3.ZERO,
			"odd/even centered endpoints %s" % str(dimensions)
		)
		_assert_vector(failures, geometry.local_extent, Vector3(dimensions[0], dimensions[1], dimensions[2]), "odd/even extent %s" % str(dimensions))
	var unit_geometry := LocalBoardPresentationGeometryScript.new()
	unit_geometry.configure([1, 1, 1], [1, 2, 3])
	var unit_bounds: Dictionary = unit_geometry.local_bounds()
	_assert_vector(failures, unit_bounds.get("min", Vector3.ZERO), Vector3(-0.5, -0.5, -0.5), "single-cell minimum retains physical extent")
	_assert_vector(failures, unit_bounds.get("max", Vector3.ZERO), Vector3(0.5, 0.5, 0.5), "single-cell maximum retains physical extent")


func _test_dimensional_chain(failures: Array) -> void:
	var mapper_2d := TraceCoordinateMapperScript.new()
	var mapper_3d := TraceCoordinateMapperScript.new()
	var mapper_4d := TraceCoordinateMapperScript.new()
	mapper_2d.configure([4, 7])
	mapper_3d.configure([4, 7, 1])
	mapper_4d.configure([4, 7, 1, 1], SliceBasis4DScript.identity())
	var geometry_2d = mapper_2d.local_geometry()
	var geometry_3d = mapper_3d.local_geometry()
	var geometry_4d = mapper_4d.local_geometry()
	if geometry_2d.local_dimensions != [4, 7, 1] or geometry_2d.axis_mapping != [1, 2, 0]:
		failures.append("2D semantic extents must adapt explicitly to presentation [X,Y,1]")
	if geometry_2d.structural_snapshot() != geometry_3d.structural_snapshot():
		failures.append("2D [4,7] and direct 3D [4,7,1] must share identical canonical geometry")
	if geometry_3d.structural_snapshot() != geometry_4d.structural_snapshot():
		failures.append("direct 3D and one-slice 4D [4,7,1] must share identical canonical geometry")
	for local_coordinate in [[0, 0, 0], [1, 3, 0], [3, 6, 0]]:
		var position_2d := mapper_2d.centered_local_point(local_coordinate.slice(0, 2))
		var position_3d := mapper_3d.centered_local_point(local_coordinate)
		var mapped_4d: Dictionary = mapper_4d.presentation_coordinate([local_coordinate[0], local_coordinate[1], local_coordinate[2], 0])
		var position_4d := mapper_4d.centered_local_point(mapped_4d.get("visible_cell_3d", []))
		_assert_vector(failures, position_2d, position_3d, "2D/3D cell transform %s" % str(local_coordinate))
		_assert_vector(failures, position_3d, position_4d, "3D/4D cell transform %s" % str(local_coordinate))
	if mapper_4d.current_layer_count() != 1:
		failures.append("4D single-slice equivalence fixture should expose exactly one separate slice anchor")


func _test_exact_basis_adaptation(failures: Array) -> void:
	var semantic_dimensions := [4, 7, 11, 3]
	var cases := [
		{"basis": SliceBasis4DScript.identity(), "dimensions": [4, 7, 11], "axes": [1, 2, 3], "layers": 3},
		{"basis": SliceBasis4DScript.identity().turned("xw", 1), "dimensions": [3, 7, 11], "axes": [4, 2, 3], "layers": 4},
		{"basis": SliceBasis4DScript.identity().turned("xw", -1), "dimensions": [3, 7, 11], "axes": [-4, 2, 3], "layers": 4},
		{"basis": SliceBasis4DScript.identity().turned("zw", 1), "dimensions": [4, 7, 3], "axes": [1, 2, 4], "layers": 11},
		{"basis": SliceBasis4DScript.identity().turned("zw", -1), "dimensions": [4, 7, 3], "axes": [1, 2, -4], "layers": 11},
		{"basis": SliceBasis4DScript.identity().turned("zx", 1), "dimensions": [11, 7, 4], "axes": [-3, 2, 1], "layers": 3},
		{"basis": SliceBasis4DScript.identity().turned("zx", -1), "dimensions": [11, 7, 4], "axes": [3, 2, -1], "layers": 3},
	]
	for basis_case in cases:
		var mapper := TraceCoordinateMapperScript.new()
		mapper.configure(semantic_dimensions, basis_case["basis"])
		var geometry = mapper.local_geometry()
		if geometry.local_dimensions != basis_case["dimensions"]:
			failures.append("basis %s must derive visible semantic extents %s, got %s" % [basis_case["basis"].key(), basis_case["dimensions"], geometry.local_dimensions])
		if geometry.axis_mapping != basis_case["axes"]:
			failures.append("basis %s must preserve signed authoritative axes %s, got %s" % [basis_case["basis"].key(), basis_case["axes"], geometry.axis_mapping])
		if mapper.current_layer_count() != int(basis_case["layers"]):
			failures.append("basis %s must keep slice-axis extent outside local geometry" % basis_case["basis"].key())
		var first_snapshot: Dictionary = geometry.structural_snapshot()
		for _layer_index in range(mapper.current_layer_count()):
			if mapper.local_geometry().structural_snapshot() != first_snapshot:
				failures.append("slice index must not alter canonical local geometry for basis %s" % basis_case["basis"].key())


func _test_signed_basis_orientation(failures: Array) -> void:
	var dimensions := [4, 7, 11, 3]
	var positive_mapper := TraceCoordinateMapperScript.new()
	var negative_mapper := TraceCoordinateMapperScript.new()
	positive_mapper.configure(dimensions, SliceBasis4DScript.identity())
	negative_mapper.configure(dimensions, SliceBasis4DScript.identity().turned("zx", -1))
	var negative_geometry = negative_mapper.local_geometry()
	if negative_geometry.local_dimensions != [11, 7, 4] or negative_geometry.axis_mapping != [3, 2, -1]:
		failures.append("ZX- basis must expose Z,Y,-X without changing signed-axis extents")
	var canonical_min_x := [0, 3, 5, 1]
	var canonical_max_x := [3, 3, 5, 1]
	var mapped_min: Dictionary = negative_mapper.presentation_coordinate(canonical_min_x)
	var mapped_max: Dictionary = negative_mapper.presentation_coordinate(canonical_max_x)
	if mapped_min.get("visible_cell_3d", []) != [5, 3, 3] or mapped_max.get("visible_cell_3d", []) != [5, 3, 0]:
		failures.append("negative visible X must reverse basis-local coordinates before canonical geometry")
	var local_delta := negative_mapper.centered_local_point(mapped_max.get("visible_cell_3d", [])) - negative_mapper.centered_local_point(mapped_min.get("visible_cell_3d", []))
	_assert_vector(failures, local_delta, Vector3(0.0, 0.0, -3.0), "negative visible axis reverses local direction")
	if positive_mapper.local_geometry().local_extent != Vector3(4.0, 7.0, 11.0):
		failures.append("identity basis extent regression")


func _assert_vector(failures: Array, actual: Vector3, expected: Vector3, label: String) -> void:
	if actual.distance_to(expected) > 0.001:
		failures.append("%s: expected %s, got %s" % [label, expected, actual])
