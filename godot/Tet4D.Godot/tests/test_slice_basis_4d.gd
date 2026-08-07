extends RefCounted

const SliceBasis4DScript = preload("res://scripts/presentation/slice_basis_4d.gd")


func run() -> Array:
	var failures: Array = []
	_test_exact_turns(failures)
	_test_group_laws(failures)
	_test_mapping_bijection(failures)
	_test_signed_order_and_movement(failures)
	return failures


func _test_exact_turns(failures: Array) -> void:
	var identity = SliceBasis4DScript.identity()
	_assert_slots(failures, identity, [1, 2, 3, 4], "initial basis")
	_assert_slots(failures, identity.turned("xw", 1), [4, 2, 3, -1], "XW+")
	_assert_slots(failures, identity.turned("xw", -1), [-4, 2, 3, 1], "XW-")
	_assert_slots(failures, identity.turned("zw", 1), [1, 2, 4, -3], "ZW+")
	_assert_slots(failures, identity.turned("zw", -1), [1, 2, -4, 3], "ZW-")
	if SliceBasis4DScript.is_valid_slots([1, 2, 1, 4]):
		failures.append("duplicate axes must be rejected")
	if SliceBasis4DScript.is_valid_slots([1, -2, 3, 4]):
		failures.append("negative Y must be rejected")
	if SliceBasis4DScript.is_valid_slots([1, 4, 3, 2]):
		failures.append("Y as slice axis must be rejected")


func _test_group_laws(failures: Array) -> void:
	for plane in ["xw", "zw"]:
		var identity = SliceBasis4DScript.identity()
		if not identity.turned(plane, 1).turned(plane, -1).equals(identity):
			failures.append("%s positive/negative turns must cancel" % plane)
		if not identity.turned(plane, -1).turned(plane, 1).equals(identity):
			failures.append("%s negative/positive turns must cancel" % plane)
		for direction in [-1, 1]:
			var result = identity
			for _index in range(4):
				result = result.turned(plane, direction)
			if not result.equals(identity):
				failures.append("four %s %s turns must be identity" % [plane, direction])
	var mixed = SliceBasis4DScript.identity()
	for operation in [["xw", 1], ["zw", 1], ["xw", -1], ["zw", -1]]:
		mixed = mixed.turned(str(operation[0]), int(operation[1]))
	_assert_slots(failures, mixed, [4, 2, 1, 3], "mixed exact sequence")


func _test_mapping_bijection(failures: Array) -> void:
	var dimensions := [5, 4, 3, 2]
	for basis in _reachable_bases():
		var seen := {}
		var visible_dims: Array = basis.visible_dimensions(dimensions)
		for x in range(dimensions[0]):
			for y in range(dimensions[1]):
				for z in range(dimensions[2]):
					for w in range(dimensions[3]):
						var canonical := [x, y, z, w]
						var mapped: Dictionary = basis.presentation_coordinate(canonical, dimensions)
						if not bool(mapped.get("ok", false)):
							failures.append("valid cell failed to map for %s" % basis.key())
							continue
						var cell: Array = mapped.get("visible_cell_3d", [])
						var layer := int(mapped.get("layer_index", -1))
						if layer < 0 or layer >= basis.layer_count(dimensions):
							failures.append("mapped layer out of bounds for %s" % basis.key())
						for axis in range(3):
							if int(cell[axis]) < 0 or int(cell[axis]) >= int(visible_dims[axis]):
								failures.append("mapped visible cell out of bounds for %s" % basis.key())
						var presentation_key := "%d|%s" % [layer, str(cell)]
						if seen.has(presentation_key):
							failures.append("mapping collision for %s at %s" % [basis.key(), presentation_key])
						seen[presentation_key] = true
						if basis.canonical_coordinate(layer, cell, dimensions) != canonical:
							failures.append("mapping inverse mismatch for %s at %s" % [basis.key(), canonical])
		if seen.size() != 5 * 4 * 3 * 2:
			failures.append("basis %s did not map every cell exactly once" % basis.key())
	var identity = SliceBasis4DScript.identity()
	if identity.visible_dimensions(dimensions) != [5, 4, 3] or identity.layer_count(dimensions) != 2:
		failures.append("identity decomposition dimensions are wrong")
	var xw = identity.turned("xw", 1)
	if xw.visible_dimensions(dimensions) != [2, 4, 3] or xw.layer_count(dimensions) != 5:
		failures.append("X/W decomposition dimensions are wrong")
	var zw = identity.turned("zw", 1)
	if zw.visible_dimensions(dimensions) != [5, 4, 2] or zw.layer_count(dimensions) != 3:
		failures.append("Z/W decomposition dimensions are wrong")
	var thin_dimensions := [4, 6, 2, 1]
	for basis in _reachable_bases():
		var mapped: Dictionary = basis.presentation_coordinate([3, 5, 1, 0], thin_dimensions)
		if not bool(mapped.get("ok", false)) or basis.canonical_coordinate(int(mapped["layer_index"]), mapped["visible_cell_3d"], thin_dimensions) != [3, 5, 1, 0]:
			failures.append("W=1 must remain bijective for %s" % basis.key())
	var decoded_json_mapping: Dictionary = identity.presentation_coordinate([1.0, 2.0, 2.0, 0.0], [5.0, 10.0, 4.0, 1.0])
	if not bool(decoded_json_mapping.get("ok", false)):
		failures.append("integral JSON numbers should normalize into exact presentation coordinates")
	if bool(identity.presentation_coordinate([1.5, 2, 2, 0], [5, 10, 4, 1]).get("ok", false)):
		failures.append("fractional coordinates must not enter the exact basis mapper")


func _test_signed_order_and_movement(failures: Array) -> void:
	var dimensions := [5, 4, 3, 2]
	var xw_positive = SliceBasis4DScript.identity().turned("xw", 1)
	if xw_positive.slice_axis_label() != "-X":
		failures.append("XW+ slice label must preserve -X orientation")
	if xw_positive.semantic_slice_coordinate(0, dimensions) != 4 or xw_positive.semantic_slice_coordinate(4, dimensions) != 0:
		failures.append("negative slice ordering must reverse semantic coordinates")
	if xw_positive.canonical_movement_command("move_x_pos") != "move_w_pos":
		failures.append("visible horizontal movement must map through +W")
	if xw_positive.canonical_movement_command("move_w_pos") != "move_x_neg":
		failures.append("positive layer movement must map through -X")
	var zw_negative = SliceBasis4DScript.identity().turned("zw", -1)
	if zw_negative.canonical_movement_command("move_z_pos") != "move_w_neg":
		failures.append("visible depth movement must map through -W")
	if zw_negative.canonical_movement_command("move_w_neg") != "move_z_neg":
		failures.append("negative layer movement must map through +Z")
	if zw_negative.canonical_movement_command("hard_drop") != "hard_drop":
		failures.append("drop commands must remain canonical Y gameplay commands")


func _reachable_bases() -> Array:
	var result := []
	var queue := [SliceBasis4DScript.identity()]
	var seen := {}
	while not queue.is_empty():
		var basis = queue.pop_front()
		if seen.has(basis.key()):
			continue
		seen[basis.key()] = true
		result.append(basis)
		for plane in ["xw", "zw"]:
			for direction in [-1, 1]:
				queue.append(basis.turned(plane, direction))
	return result


func _assert_slots(failures: Array, basis, expected: Array, label: String) -> void:
	if basis.slots() != expected:
		failures.append("%s: expected %s, got %s" % [label, expected, basis.slots()])
