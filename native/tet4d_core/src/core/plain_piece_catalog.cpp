#include "tet4d_core/plain_piece_catalog.hpp"

#include <initializer_list>
#include <utility>

namespace tet4d::core {
namespace {

PieceShape2D classic_o_shape_2d() {
	return {"O", {{0, 0}, {1, 0}, {0, 1}, {1, 1}}, 2};
}

PieceShape2D classic_t_shape_2d() {
	return {"T", {{-1, 0}, {0, 0}, {1, 0}, {0, 1}}, 3};
}

PieceShape2D classic_z_shape_2d() {
	return {"Z", {{-1, 0}, {0, 0}, {0, 1}, {1, 1}}, 5};
}

PieceShape2D classic_j_shape_2d() {
	return {"J", {{-1, 0}, {-1, 1}, {0, 0}, {1, 0}}, 6};
}

PieceShape2D classic_l_shape_2d() {
	return {"L", {{-1, 0}, {0, 0}, {1, 0}, {1, 1}}, 7};
}

CoordND embedded_coord(int dimension, std::initializer_list<int> values) {
	std::vector<int> result(values);
	result.resize(static_cast<std::size_t>(dimension), 0);
	return {std::move(result)};
}

std::vector<PieceShapeND> embedded_2d_catalog(int dimension) {
	const auto coord = [dimension](std::initializer_list<int> values) {
		return embedded_coord(dimension, values);
	};
	return {
		{"I_E2", {coord({-1, 0}), coord({0, 0}), coord({1, 0}), coord({2, 0})}, 1},
		{"O_E2", {coord({0, 0}), coord({1, 0}), coord({0, 1}), coord({1, 1})}, 2},
		{"T_E2", {coord({-1, 0}), coord({0, 0}), coord({1, 0}), coord({0, 1})}, 3},
		{"S_E2", {coord({0, 0}), coord({1, 0}), coord({-1, 1}), coord({0, 1})}, 4},
		{"Z_E2", {coord({-1, 0}), coord({0, 0}), coord({0, 1}), coord({1, 1})}, 5},
		{"J_E2", {coord({-1, 0}), coord({-1, 1}), coord({0, 0}), coord({1, 0})}, 6},
		{"L_E2", {coord({-1, 0}), coord({0, 0}), coord({1, 0}), coord({1, 1})}, 7},
	};
}

std::vector<PieceShapeND> native_3d_catalog(int dimension) {
	const auto coord = [dimension](std::initializer_list<int> values) {
		return embedded_coord(dimension, values);
	};
	return {
		{"I3", {coord({-1, 0, 0}), coord({0, 0, 0}), coord({1, 0, 0}), coord({2, 0, 0})}, 1},
		{"O3", {coord({0, 0, 0}), coord({1, 0, 0}), coord({0, 1, 0}), coord({1, 1, 0})}, 2},
		{"L3", {coord({-1, 0, 0}), coord({0, 0, 0}), coord({1, 0, 0}), coord({1, 1, 0})}, 3},
		{"T3", {coord({-1, 0, 0}), coord({0, 0, 0}), coord({1, 0, 0}), coord({0, 1, 0})}, 4},
		{"S3", {coord({0, 0, 0}), coord({1, 0, 0}), coord({-1, 1, 0}), coord({0, 1, 0})}, 5},
		{"J3D", {coord({0, 0, 0}), coord({1, 0, 0}), coord({0, 1, 0}), coord({0, 0, 1})}, 6},
		{"SCREW3", {coord({0, 0, 0}), coord({1, 0, 0}), coord({1, 1, 0}), coord({1, 1, 1})}, 7},
	};
}

std::vector<PieceShapeND> standard_4d_5_catalog() {
	const auto coord = [](std::initializer_list<int> values) {
		return CoordND{std::vector<int>(values)};
	};
	return {
		{"CROSS4", {coord({0, 0, 0, 0}), coord({1, 0, 0, 0}), coord({0, 1, 0, 0}), coord({0, 0, 1, 0}), coord({0, 0, 0, 1})}, 1},
		{"SKEW4_A", {coord({0, 0, 0, 0}), coord({-1, 0, 0, 0}), coord({0, 1, 0, 0}), coord({0, 1, 1, 0}), coord({0, 1, 1, 1})}, 2},
		{"SKEW4_B", {coord({0, 0, 0, 0}), coord({1, 0, 0, 0}), coord({1, -1, 0, 0}), coord({1, -1, 1, 0}), coord({1, -1, 1, 1})}, 3},
		{"TEE4", {coord({-1, 0, 0, 0}), coord({0, 0, 0, 0}), coord({1, 0, 0, 0}), coord({0, 1, 1, 0}), coord({0, 1, 1, 1})}, 4},
		{"CORK4", {coord({0, 0, 0, 0}), coord({1, 0, 0, 0}), coord({0, 1, 0, 0}), coord({1, 1, 1, 0}), coord({1, 1, 1, 1})}, 5},
		{"STAIR4", {coord({0, 0, 0, 0}), coord({0, 1, 0, 0}), coord({1, 1, 0, 0}), coord({1, 1, 1, 0}), coord({1, 1, 1, 1})}, 6},
		{"FORK4", {coord({0, 0, 0, 0}), coord({-1, 0, 0, 0}), coord({1, 0, 0, 0}), coord({0, 1, 0, 1}), coord({0, 0, 1, 1})}, 7},
	};
}

} // namespace

const std::vector<PieceShape2D> &plain_piece_catalog_2d(std::string_view piece_set_id) {
	static const std::vector<PieceShape2D> classic = {
		classic_i_shape_2d(), classic_o_shape_2d(), classic_t_shape_2d(),
		classic_s_shape_2d(), classic_z_shape_2d(), classic_j_shape_2d(), classic_l_shape_2d(),
	};
	static const std::vector<PieceShape2D> empty;
	return piece_set_id == "classic" ? classic : empty;
}

const std::vector<ProductionPieceSetND> &production_piece_catalogs_nd() {
	static const std::vector<ProductionPieceSetND> catalogs = {
		{3, "embedded_2d", embedded_2d_catalog(3)},
		{3, "native_3d", native_3d_catalog(3)},
		{4, "embedded_2d", embedded_2d_catalog(4)},
		{4, "embedded_3d", native_3d_catalog(4)},
		{4, "standard_4d_5", standard_4d_5_catalog()},
	};
	return catalogs;
}

std::vector<PieceShapeND> plain_piece_catalog_nd(int dimension, std::string_view piece_set_id) {
	for (const ProductionPieceSetND &catalog : production_piece_catalogs_nd()) {
		if (catalog.dimension == dimension && catalog.piece_set_id == piece_set_id) {
			return catalog.pieces;
		}
	}
	return {};
}

std::vector<PieceShapeND> legacy_live_piece_sequence_for_dimension(int dimension) {
	if (dimension == 4) {
		return {trace_shape_4d(), standard_stair_shape_4d(), trace_rotation_shape_4d(), trace_single_shape_4d(), trace_spawn_blocked_shape_4d()};
	}
	return dimension == 3 ? native_3d_catalog(3) : std::vector<PieceShapeND>{};
}

bool is_supported_live_piece_set(int dimension, std::string_view piece_set_id) {
	if (dimension == 2) {
		return piece_set_id == "classic";
	}
	return !plain_piece_catalog_nd(dimension, piece_set_id).empty();
}

bool is_known_live_piece_set(std::string_view piece_set_id) {
	if (piece_set_id == "classic") {
		return true;
	}
	for (const ProductionPieceSetND &catalog : production_piece_catalogs_nd()) {
		if (catalog.piece_set_id == piece_set_id) {
			return true;
		}
	}
	return false;
}

} // namespace tet4d::core
