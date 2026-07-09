#pragma once

#include "tet4d_core/plain_nd.hpp"

#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

struct LegalityQueryResult {
	bool legal = false;
	std::string reason;
};

LegalityQueryResult piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells = {});
LegalityQueryResult translated_piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		const CoordND &delta,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells = {});
LegalityQueryResult rotated_piece_pose_legal_query(
		const BoardShapeND &shape,
		const std::vector<CoordND> &piece_cells,
		int axis_a,
		int axis_b,
		int quarter_turns,
		const std::vector<CoordND> &occupied_cells,
		const std::vector<CoordND> &ignore_cells = {});

struct BoundaryQueryRef {
	int dimension = 0;
	int axis = 0;
	int side = 1;
};

struct BoundaryQueryTransform {
	std::vector<int> permutation;
	std::vector<int> signs;
};

struct GluingQueryDescriptor {
	std::string glue_id;
	BoundaryQueryRef source;
	BoundaryQueryRef target;
	BoundaryQueryTransform transform;
	bool enabled = true;
};

struct TopologyQueryProfile {
	int dimension = 0;
	std::vector<GluingQueryDescriptor> gluings;
};

struct MoveStepQuery {
	int axis = 0;
	int delta = 0;
};

struct TopologyCellStepQueryResult {
	CoordND source;
	MoveStepQuery step;
	std::optional<CoordND> target;
	std::optional<std::string> glue_id;
	std::optional<BoundaryQueryRef> source_boundary;
	std::optional<BoundaryQueryRef> target_boundary;
	MoveStepQuery entry_step;
	bool ok = true;
	std::string error;
};

TopologyQueryProfile axis_wrap_topology_profile(int dimension, const std::vector<int> &wrapped_axes);
TopologyCellStepQueryResult resolve_topology_cell_step_query(
		const TopologyQueryProfile &profile,
		const BoardShapeND &shape,
		const CoordND &coord,
		MoveStepQuery step);
std::vector<TopologyCellStepQueryResult> topology_neighbor_query(
		const TopologyQueryProfile &profile,
		const BoardShapeND &shape,
		const CoordND &coord);

} // namespace tet4d::core
