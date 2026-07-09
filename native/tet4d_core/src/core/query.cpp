#include "tet4d_core/query.hpp"

#include "tet4d_core/geometry.hpp"

#include <algorithm>
#include <map>
#include <set>
#include <utility>

namespace tet4d::core {
namespace {

constexpr int MIN_QUERY_DIMENSION = 2;
constexpr int MAX_QUERY_DIMENSION = 4;

bool dimension_is_valid(int dimension) {
	return dimension >= MIN_QUERY_DIMENSION && dimension <= MAX_QUERY_DIMENSION;
}

bool shape_is_valid_for_query(const BoardShapeND &shape) {
	return dimension_is_valid(shape.dimension()) && shape.is_valid();
}

bool coord_dimension_matches(const CoordND &coord, int dimension) {
	return coord.dimension() == dimension;
}

bool coord_in_bounds(const BoardShapeND &shape, const CoordND &coord) {
	if (!coord_dimension_matches(coord, shape.dimension())) {
		return false;
	}
	for (int axis = 0; axis < shape.dimension(); ++axis) {
		const int value = coord.values[static_cast<std::size_t>(axis)];
		if (value < 0 || value >= shape.dims[static_cast<std::size_t>(axis)]) {
			return false;
		}
	}
	return true;
}

std::set<CoordND> coord_set(const std::vector<CoordND> &coords) {
	return std::set<CoordND>(coords.begin(), coords.end());
}

LegalityQueryResult legality_result(bool legal, const std::string &reason) {
	return LegalityQueryResult{legal, reason};
}

int side_fixed_value(const BoardShapeND &shape, const BoundaryQueryRef &boundary) {
	return boundary.side < 0 ? 0 : shape.dims[static_cast<std::size_t>(boundary.axis)] - 1;
}

bool boundary_is_valid(const BoundaryQueryRef &boundary, int dimension) {
	return boundary.dimension == dimension && boundary.axis >= 0 && boundary.axis < dimension && (boundary.side == -1 || boundary.side == 1);
}

std::vector<int> tangent_axes_for_boundary(const BoundaryQueryRef &boundary) {
	std::vector<int> axes;
	for (int axis = 0; axis < boundary.dimension; ++axis) {
		if (axis != boundary.axis) {
			axes.push_back(axis);
		}
	}
	return axes;
}

bool transform_is_valid(const BoundaryQueryTransform &transform, int tangent_dimension) {
	if (static_cast<int>(transform.permutation.size()) != tangent_dimension ||
			static_cast<int>(transform.signs.size()) != tangent_dimension) {
		return false;
	}
	std::vector<int> sorted = transform.permutation;
	std::sort(sorted.begin(), sorted.end());
	for (int index = 0; index < tangent_dimension; ++index) {
		if (sorted[static_cast<std::size_t>(index)] != index) {
			return false;
		}
		if (transform.signs[static_cast<std::size_t>(index)] != -1 && transform.signs[static_cast<std::size_t>(index)] != 1) {
			return false;
		}
	}
	return true;
}

BoundaryQueryTransform inverse_transform(const BoundaryQueryTransform &transform) {
	BoundaryQueryTransform inverse;
	inverse.permutation.resize(transform.permutation.size());
	inverse.signs.resize(transform.signs.size(), 1);
	for (std::size_t source_index = 0; source_index < transform.permutation.size(); ++source_index) {
		const int target_index = transform.permutation[source_index];
		inverse.permutation[static_cast<std::size_t>(target_index)] = static_cast<int>(source_index);
		inverse.signs[static_cast<std::size_t>(target_index)] = transform.signs[source_index];
	}
	return inverse;
}

std::vector<int> boundary_extents(const BoardShapeND &shape, const BoundaryQueryRef &boundary) {
	std::vector<int> extents;
	for (const int axis : tangent_axes_for_boundary(boundary)) {
		extents.push_back(shape.dims[static_cast<std::size_t>(axis)]);
	}
	return extents;
}

std::vector<int> apply_boundary_transform(
		const std::vector<int> &source_values,
		const std::vector<int> &target_extents,
		const BoundaryQueryTransform &transform) {
	std::vector<int> mapped(source_values.size(), 0);
	for (std::size_t source_index = 0; source_index < source_values.size(); ++source_index) {
		const int target_index = transform.permutation[source_index];
		const int source_value = source_values[source_index];
		if (transform.signs[source_index] < 0) {
			mapped[static_cast<std::size_t>(target_index)] = target_extents[static_cast<std::size_t>(target_index)] - 1 - source_value;
		} else {
			mapped[static_cast<std::size_t>(target_index)] = source_value;
		}
	}
	return mapped;
}

std::optional<BoundaryQueryRef> boundary_for_exit(
		const BoardShapeND &shape,
		const CoordND &coord,
		MoveStepQuery step) {
	if (step.axis < 0 || step.axis >= shape.dimension()) {
		return std::nullopt;
	}
	const int value = coord.values[static_cast<std::size_t>(step.axis)];
	if (step.delta < 0) {
		if (value != 0) {
			return std::nullopt;
		}
		return BoundaryQueryRef{shape.dimension(), step.axis, -1};
	}
	if (value != shape.dims[static_cast<std::size_t>(step.axis)] - 1) {
		return std::nullopt;
	}
	return BoundaryQueryRef{shape.dimension(), step.axis, 1};
}

MoveStepQuery inward_step(const BoundaryQueryRef &boundary) {
	return MoveStepQuery{boundary.axis, boundary.side < 0 ? 1 : -1};
}

bool same_boundary(const BoundaryQueryRef &left, const BoundaryQueryRef &right) {
	return left.dimension == right.dimension && left.axis == right.axis && left.side == right.side;
}

const GluingQueryDescriptor *glue_for_source_boundary(
		const TopologyQueryProfile &profile,
		const BoundaryQueryRef &boundary,
		bool &forward) {
	for (const GluingQueryDescriptor &glue : profile.gluings) {
		if (!glue.enabled) {
			continue;
		}
		if (same_boundary(glue.source, boundary)) {
			forward = true;
			return &glue;
		}
		if (same_boundary(glue.target, boundary)) {
			forward = false;
			return &glue;
		}
	}
	return nullptr;
}

std::optional<std::string> validate_topology_query_inputs(
		const TopologyQueryProfile &profile,
		const BoardShapeND &shape,
		const CoordND &coord,
		MoveStepQuery step) {
	const int dimension = shape.dimension();
	if (!shape_is_valid_for_query(shape)) {
		return "invalid_board_shape";
	}
	if (profile.dimension != dimension) {
		return "profile_dimension_mismatch";
	}
	if (!coord_dimension_matches(coord, dimension)) {
		return "coord_dimension_mismatch";
	}
	if (!coord_in_bounds(shape, coord)) {
		return "coord_out_of_bounds";
	}
	if (step.axis < 0 || step.axis >= dimension || (step.delta != -1 && step.delta != 1)) {
		return "invalid_step";
	}
	const int tangent_dimension = dimension - 1;
	std::set<std::pair<int, int>> used_boundaries;
	for (const GluingQueryDescriptor &glue : profile.gluings) {
		if (glue.glue_id.empty()) {
			return "empty_glue_id";
		}
		if (!boundary_is_valid(glue.source, dimension) || !boundary_is_valid(glue.target, dimension)) {
			return "invalid_boundary";
		}
		if (same_boundary(glue.source, glue.target)) {
			return "self_boundary_glue";
		}
		if (!transform_is_valid(glue.transform, tangent_dimension)) {
			return "invalid_transform";
		}
		if (glue.enabled) {
			const auto source_key = std::make_pair(glue.source.axis, glue.source.side);
			const auto target_key = std::make_pair(glue.target.axis, glue.target.side);
			if (used_boundaries.count(source_key) != 0 || used_boundaries.count(target_key) != 0) {
				return "duplicate_active_boundary";
			}
			used_boundaries.insert(source_key);
			used_boundaries.insert(target_key);
		}
	}
	return std::nullopt;
}

TopologyCellStepQueryResult error_result(
		const CoordND &coord,
		MoveStepQuery step,
		const std::string &error) {
	TopologyCellStepQueryResult result;
	result.source = coord;
	result.step = step;
	result.entry_step = step;
	result.ok = false;
	result.error = error;
	return result;
}

} // namespace

LegalityQueryResult piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells) {
	if (!shape_is_valid_for_query(shape)) {
		return legality_result(false, "invalid_board_shape");
	}
	if (piece_cells.empty()) {
		return legality_result(false, "empty_piece");
	}
	const int dimension = shape.dimension();
	for (const CoordND &coord : piece_cells) {
		if (!coord_dimension_matches(coord, dimension)) {
			return legality_result(false, "piece_dimension_mismatch");
		}
	}
	if (coord_set(piece_cells).size() != piece_cells.size()) {
		return legality_result(false, "duplicate_piece_cell");
	}
	for (const CoordND &coord : piece_cells) {
		if (!coord_in_bounds(shape, coord)) {
			return legality_result(false, "out_of_bounds");
		}
	}
	for (const CoordND &coord : occupied_cells) {
		if (!coord_dimension_matches(coord, dimension)) {
			return legality_result(false, "occupied_dimension_mismatch");
		}
	}
	for (const CoordND &coord : ignore_cells) {
		if (!coord_dimension_matches(coord, dimension)) {
			return legality_result(false, "ignore_dimension_mismatch");
		}
	}
	const std::set<CoordND> occupied = coord_set(occupied_cells);
	const std::set<CoordND> ignored = coord_set(ignore_cells);
	for (const CoordND &coord : piece_cells) {
		if (occupied.count(coord) != 0 && ignored.count(coord) == 0) {
			return legality_result(false, "occupied");
		}
	}
	return legality_result(true, "legal");
}

LegalityQueryResult translated_piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		const CoordND &delta,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells) {
	if (delta.dimension() != shape.dimension()) {
		return legality_result(false, "delta_dimension_mismatch");
	}
	return piece_pose_legal_query(
			shape,
			translate_blocks_nd(piece_cells, delta),
			occupied_cells,
			ignore_cells);
}

LegalityQueryResult rotated_piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		int axis_a,
		int axis_b,
		int quarter_turns,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells) {
	return piece_pose_legal_query(
			shape,
			rotate_blocks_nd(piece_cells, axis_a, axis_b, quarter_turns),
			occupied_cells,
			ignore_cells);
}

TopologyQueryProfile axis_wrap_topology_profile(int dimension, const std::vector<int> &wrapped_axes) {
	TopologyQueryProfile profile;
	profile.dimension = dimension;
	const BoundaryQueryTransform identity{
		[dimension]() {
			std::vector<int> values;
			for (int index = 0; index < dimension - 1; ++index) {
				values.push_back(index);
			}
			return values;
		}(),
		std::vector<int>(static_cast<std::size_t>(std::max(0, dimension - 1)), 1),
	};
	for (const int axis : wrapped_axes) {
		profile.gluings.push_back(GluingQueryDescriptor{
				"wrap_" + std::to_string(axis),
				BoundaryQueryRef{dimension, axis, -1},
				BoundaryQueryRef{dimension, axis, 1},
				identity,
				true});
	}
	return profile;
}

TopologyCellStepQueryResult resolve_topology_cell_step_query(
		const TopologyQueryProfile &profile,
		const BoardShapeND &shape,
		const CoordND &coord,
		MoveStepQuery step) {
	if (const std::optional<std::string> error = validate_topology_query_inputs(profile, shape, coord, step)) {
		return error_result(coord, step, *error);
	}

	TopologyCellStepQueryResult result;
	result.source = coord;
	result.step = step;
	result.entry_step = step;
	CoordND translated = coord;
	translated.values[static_cast<std::size_t>(step.axis)] += step.delta;
	if (coord_in_bounds(shape, translated)) {
		result.target = translated;
		result.entry_step = step;
		return result;
	}

	const std::optional<BoundaryQueryRef> source_boundary = boundary_for_exit(shape, coord, step);
	if (!source_boundary.has_value()) {
		return result;
	}

	bool forward = true;
	const GluingQueryDescriptor *glue = glue_for_source_boundary(profile, *source_boundary, forward);
	if (glue == nullptr) {
		return result;
	}
	const BoundaryQueryRef target_boundary = forward ? glue->target : glue->source;
	const BoundaryQueryTransform transform = forward ? glue->transform : inverse_transform(glue->transform);
	const std::vector<int> source_axes = tangent_axes_for_boundary(*source_boundary);
	const std::vector<int> target_axes = tangent_axes_for_boundary(target_boundary);
	std::vector<int> source_values;
	for (const int axis : source_axes) {
		source_values.push_back(coord.values[static_cast<std::size_t>(axis)]);
	}
	const std::vector<int> target_values = apply_boundary_transform(
			source_values,
			boundary_extents(shape, target_boundary),
			transform);
	CoordND target;
	target.values = std::vector<int>(static_cast<std::size_t>(shape.dimension()), 0);
	for (std::size_t index = 0; index < target_axes.size(); ++index) {
		target.values[static_cast<std::size_t>(target_axes[index])] = target_values[index];
	}
	target.values[static_cast<std::size_t>(target_boundary.axis)] = side_fixed_value(shape, target_boundary);
	result.target = target;
	result.glue_id = glue->glue_id;
	result.source_boundary = *source_boundary;
	result.target_boundary = target_boundary;
	result.entry_step = inward_step(target_boundary);
	return result;
}

std::vector<TopologyCellStepQueryResult> topology_neighbor_query(
		const TopologyQueryProfile &profile,
		const BoardShapeND &shape,
		const CoordND &coord) {
	std::vector<TopologyCellStepQueryResult> results;
	for (int axis = 0; axis < shape.dimension(); ++axis) {
		results.push_back(resolve_topology_cell_step_query(profile, shape, coord, MoveStepQuery{axis, -1}));
		results.push_back(resolve_topology_cell_step_query(profile, shape, coord, MoveStepQuery{axis, 1}));
	}
	return results;
}

} // namespace tet4d::core
