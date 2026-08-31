#pragma once

#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/plain_nd.hpp"

#include <string>
#include <string_view>
#include <vector>

namespace tet4d::core {

struct ProductionPieceSetND {
	int dimension;
	std::string piece_set_id;
	std::vector<PieceShapeND> pieces;
};

// The production piece catalogues are shared by session construction and the
// pre-construction board-extent validator.  Callers must not duplicate them.
const std::vector<PieceShape2D> &plain_piece_catalog_2d(std::string_view piece_set_id);
const std::vector<ProductionPieceSetND> &production_piece_catalogs_nd();
std::vector<PieceShapeND> plain_piece_catalog_nd(int dimension, std::string_view piece_set_id);
std::vector<PieceShapeND> legacy_live_piece_sequence_for_dimension(int dimension);
bool is_supported_live_piece_set(int dimension, std::string_view piece_set_id);
bool is_known_live_piece_set(std::string_view piece_set_id);

} // namespace tet4d::core
