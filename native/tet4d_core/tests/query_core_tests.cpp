#include "tet4d_core/query.hpp"

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

using tet4d::core::BoardShapeND;
using tet4d::core::BoundaryQueryRef;
using tet4d::core::BoundaryQueryTransform;
using tet4d::core::CoordND;
using tet4d::core::GluingQueryDescriptor;
using tet4d::core::MoveStepQuery;
using tet4d::core::TopologyQueryProfile;

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << message << "\n";
		std::exit(1);
	}
}

std::string coord_json(const CoordND &coord) {
	std::ostringstream stream;
	stream << "[";
	for (std::size_t axis = 0; axis < coord.values.size(); ++axis) {
		if (axis > 0) {
			stream << ",";
		}
		stream << coord.values[axis];
	}
	stream << "]";
	return stream.str();
}

std::string optional_coord_json(const std::optional<CoordND> &coord) {
	return coord.has_value() ? coord_json(*coord) : "null";
}

std::string boundary_label(const BoundaryQueryRef &boundary) {
	const char *names[] = {"x", "y", "z", "w"};
	return std::string(names[boundary.axis]) + (boundary.side < 0 ? "-" : "+");
}

std::string optional_boundary_label_json(const std::optional<BoundaryQueryRef> &boundary) {
	return boundary.has_value() ? "\"" + boundary_label(*boundary) + "\"" : "null";
}

std::string optional_string_json(const std::optional<std::string> &value) {
	return value.has_value() ? "\"" + *value + "\"" : "null";
}

std::string step_label(MoveStepQuery step) {
	const char *names[] = {"x", "y", "z", "w"};
	return std::string(names[step.axis]) + (step.delta < 0 ? "-" : "+");
}

TopologyQueryProfile swapped_xz_profile_3d() {
	return TopologyQueryProfile{
		3,
		{
			GluingQueryDescriptor{
				"xz_swap",
				BoundaryQueryRef{3, 0, -1},
				BoundaryQueryRef{3, 2, 1},
				BoundaryQueryTransform{{1, 0}, {1, 1}},
				true,
			},
		},
	};
}

void print_legality_case(
		const std::string &name,
		const tet4d::core::LegalityQueryResult &result,
		bool last) {
	std::cout << "    {\"name\":\"" << name << "\",\"legal\":" << (result.legal ? "true" : "false")
			  << ",\"reason\":\"" << result.reason << "\"}";
	if (!last) {
		std::cout << ",";
	}
	std::cout << "\n";
}

void print_topology_case(
		const std::string &name,
		const tet4d::core::TopologyCellStepQueryResult &result,
		bool last) {
	std::cout << "    {\"name\":\"" << name << "\",\"ok\":" << (result.ok ? "true" : "false")
			  << ",\"target\":" << optional_coord_json(result.target)
			  << ",\"glue_id\":" << optional_string_json(result.glue_id)
			  << ",\"source_boundary\":" << optional_boundary_label_json(result.source_boundary)
			  << ",\"target_boundary\":" << optional_boundary_label_json(result.target_boundary)
			  << ",\"entry_step\":\"" << step_label(result.entry_step) << "\""
			  << ",\"error\":\"" << result.error << "\"}";
	if (!last) {
		std::cout << ",";
	}
	std::cout << "\n";
}

void test_legality_queries() {
	const BoardShapeND shape_2d{{4, 5}};
	const BoardShapeND shape_3d{{4, 5, 3}};
	require(
		tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}, {{2, 1}}}, {}).legal,
		"piece pose should accept empty bounded cells");
	require(
		!tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}, {{1, 1}}}, {}).legal,
		"piece pose should reject duplicate candidate cells");
	require(
		!tet4d::core::piece_pose_legal_query(shape_2d, {{{-1, 1}}}, {}).legal,
		"piece pose should reject out-of-bounds cells");
	require(
		!tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}}, {{{1, 1}}}).legal,
		"piece pose should reject occupied cells");
	require(
		tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}}, {{{1, 1}}}, {{{1, 1}}}).legal,
		"piece pose should allow ignored occupied self cells");
	require(
		tet4d::core::translated_piece_pose_legal_query(shape_3d, {{{1, 1, 1}}}, {{1, 0, 0}}, {}).legal,
		"translated pose should accept bounded movement");
	require(
		!tet4d::core::translated_piece_pose_legal_query(shape_3d, {{{3, 1, 1}}}, {{1, 0, 0}}, {}).legal,
		"translated pose should reject boundary overflow");
	require(
		tet4d::core::rotated_piece_pose_legal_query(shape_3d, {{{1, 1, 1}}, {{1, 1, 2}}}, 0, 2, 1, {}).legal,
		"rotated pose should accept bounded rotation");
}

void test_topology_queries() {
	const BoardShapeND shape_2d{{3, 4}};
	const TopologyQueryProfile torus = tet4d::core::axis_wrap_topology_profile(2, {0, 1});
	const auto wrap_x = tet4d::core::resolve_topology_cell_step_query(torus, shape_2d, {{2, 2}}, {0, 1});
	require(wrap_x.target == CoordND{{0, 2}}, "torus x+ should wrap to x- target");
	const auto wrap_y = tet4d::core::resolve_topology_cell_step_query(torus, shape_2d, {{1, 3}}, {1, 1});
	require(wrap_y.target == CoordND{{1, 0}}, "torus y+ should wrap to y- target");
	const TopologyQueryProfile bounded{2, {}};
	const auto blocked_y = tet4d::core::resolve_topology_cell_step_query(bounded, shape_2d, {{1, 3}}, {1, 1});
	require(!blocked_y.target.has_value(), "bounded y+ should block at boundary");
	const auto cross_axis = tet4d::core::resolve_topology_cell_step_query(
			swapped_xz_profile_3d(),
			BoardShapeND{{4, 4, 4}},
			{{0, 1, 2}},
			{0, -1});
	require(cross_axis.target == CoordND{{2, 1, 3}}, "cross-axis seam should match resolver target");
	require(cross_axis.entry_step.axis == 2 && cross_axis.entry_step.delta == -1, "cross-axis seam should report inward entry step");
}

void print_query_parity_json() {
	const BoardShapeND shape_2d{{4, 5}};
	const BoardShapeND shape_3d{{4, 5, 3}};
	const TopologyQueryProfile torus = tet4d::core::axis_wrap_topology_profile(2, {0, 1});
	const TopologyQueryProfile bounded{2, {}};
	std::cout << "{\n";
	std::cout << "  \"legality_cases\": [\n";
	print_legality_case("bounded_2d_legal", tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}, {{2, 1}}}, {}), false);
	print_legality_case("bounded_2d_occupied", tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}}, {{{1, 1}}}), false);
	print_legality_case("bounded_2d_boundary", tet4d::core::piece_pose_legal_query(shape_2d, {{{-1, 1}}}, {}), false);
	print_legality_case("bounded_2d_duplicate", tet4d::core::piece_pose_legal_query(shape_2d, {{{1, 1}}, {{1, 1}}}, {}), false);
	print_legality_case("bounded_3d_translate", tet4d::core::translated_piece_pose_legal_query(shape_3d, {{{1, 1, 1}}}, {{1, 0, 0}}, {}), false);
	print_legality_case("bounded_3d_translate_boundary", tet4d::core::translated_piece_pose_legal_query(shape_3d, {{{3, 1, 1}}}, {{1, 0, 0}}, {}), false);
	print_legality_case("bounded_3d_rotate", tet4d::core::rotated_piece_pose_legal_query(shape_3d, {{{1, 1, 1}}, {{1, 1, 2}}}, 0, 2, 1, {}), true);
	std::cout << "  ],\n";
	std::cout << "  \"topology_cases\": [\n";
	print_topology_case("bounded_2d_y_plus_blocked", tet4d::core::resolve_topology_cell_step_query(bounded, BoardShapeND{{3, 4}}, {{1, 3}}, {1, 1}), false);
	print_topology_case("torus_2d_x_plus", tet4d::core::resolve_topology_cell_step_query(torus, BoardShapeND{{3, 4}}, {{2, 2}}, {0, 1}), false);
	print_topology_case("torus_2d_y_plus", tet4d::core::resolve_topology_cell_step_query(torus, BoardShapeND{{3, 4}}, {{1, 3}}, {1, 1}), false);
	print_topology_case("cross_axis_x_minus_to_z_plus", tet4d::core::resolve_topology_cell_step_query(swapped_xz_profile_3d(), BoardShapeND{{4, 4, 4}}, {{0, 1, 2}}, {0, -1}), false);
	print_topology_case("cross_axis_reverse_z_plus", tet4d::core::resolve_topology_cell_step_query(swapped_xz_profile_3d(), BoardShapeND{{4, 4, 4}}, {{2, 1, 3}}, {2, 1}), true);
	std::cout << "  ]\n";
	std::cout << "}\n";
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--query-parity") {
		print_query_parity_json();
		return 0;
	}
	test_legality_queries();
	test_topology_queries();
	std::cout << "tet4d_core query tests passed\n";
	return 0;
}
