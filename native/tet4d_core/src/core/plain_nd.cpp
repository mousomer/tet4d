#include "tet4d_core/plain_nd.hpp"

#include <algorithm>
#include <utility>

namespace tet4d::core {
namespace {

bool coord_dimension_matches(const CoordND &coord, int dimension) {
	return static_cast<int>(coord.values.size()) == dimension;
}

} // namespace

int CoordND::dimension() const {
	return static_cast<int>(values.size());
}

bool CoordND::operator<(const CoordND &other) const {
	return values < other.values;
}

bool CoordND::operator==(const CoordND &other) const {
	return values == other.values;
}

int BoardShapeND::dimension() const {
	return static_cast<int>(dims.size());
}

bool BoardShapeND::is_valid() const {
	if (dims.empty()) {
		return false;
	}
	for (const int dim : dims) {
		if (dim <= 0) {
			return false;
		}
	}
	return true;
}

bool BoardShapeND::matches(const CoordND &coord) const {
	return coord_dimension_matches(coord, dimension());
}

BoardND::BoardND(BoardShapeND shape) : shape_(std::move(shape)) {
}

const BoardShapeND &BoardND::shape() const {
	return shape_;
}

const std::map<CoordND, int> &BoardND::cells() const {
	return cells_;
}

bool BoardND::has_cell(const CoordND &coord) const {
	return cells_.find(coord) != cells_.end();
}

void BoardND::set_cell(const CoordND &coord, int value) {
	cells_[coord] = value;
}

ActivePieceND ActivePieceND::from_shape(const PieceShapeND &shape, const CoordND &pos) {
	return ActivePieceND{shape, pos, shape.blocks, std::nullopt, 0};
}

std::vector<CoordND> ActivePieceND::cells() const {
	std::vector<CoordND> result;
	result.reserve(rel_blocks.size());
	for (const CoordND &block : rel_blocks) {
		CoordND cell;
		cell.values.reserve(pos.values.size());
		for (std::size_t index = 0; index < pos.values.size(); ++index) {
			cell.values.push_back(pos.values[index] + block.values[index]);
		}
		result.push_back(cell);
	}
	std::sort(result.begin(), result.end());
	return result;
}

ActivePieceND ActivePieceND::moved_axis(int axis, int delta) const {
	ActivePieceND result = *this;
	result.pos.values[static_cast<std::size_t>(axis)] += delta;
	return result;
}

GameStateND::GameStateND(BoardShapeND shape, int gravity_axis) :
		board(std::move(shape)),
		gravity_axis(gravity_axis) {
}

std::vector<CoordND> GameStateND::active_cells() const {
	if (!active_piece.has_value()) {
		return {};
	}
	return active_piece->cells();
}

bool GameStateND::can_exist(const ActivePieceND &piece) const {
	const BoardShapeND &shape = board.shape();
	if (!shape.is_valid() || !shape.matches(piece.pos) || gravity_axis < 0 || gravity_axis >= shape.dimension()) {
		return false;
	}
	for (const CoordND &block : piece.rel_blocks) {
		if (!shape.matches(block)) {
			return false;
		}
	}
	for (const CoordND &cell : piece.cells()) {
		if (!shape.matches(cell)) {
			return false;
		}
		for (int axis = 0; axis < shape.dimension(); ++axis) {
			const int value = cell.values[static_cast<std::size_t>(axis)];
			const int size = shape.dims[static_cast<std::size_t>(axis)];
			if (axis == gravity_axis) {
				if (value >= size) {
					return false;
				}
			} else if (value < 0 || value >= size) {
				return false;
			}
		}
		if (cell.values[static_cast<std::size_t>(gravity_axis)] >= 0 && board.has_cell(cell)) {
			return false;
		}
	}
	return true;
}

bool GameStateND::try_move_axis(int axis, int delta) {
	if (game_over) {
		return false;
	}
	if (!active_piece.has_value()) {
		game_over = true;
		game_over_reason = "no_active_piece";
		return false;
	}
	if (axis < 0 || axis >= board.shape().dimension()) {
		return false;
	}
	const ActivePieceND moved = active_piece->moved_axis(axis, delta);
	if (!can_exist(moved)) {
		return false;
	}
	active_piece = moved;
	return true;
}

bool GameStateND::try_soft_drop() {
	return try_move_axis(gravity_axis, 1);
}

void GameStateND::hard_drop() {
	if (game_over) {
		return;
	}
	while (try_soft_drop()) {
	}
	lock_current_piece();
	if (!game_over && post_lock_spawn_shape.has_value()) {
		spawn_piece(*post_lock_spawn_shape);
	}
}

int GameStateND::lock_current_piece() {
	if (!active_piece.has_value()) {
		game_over = true;
		game_over_reason = "no_active_piece";
		return 0;
	}

	const int color_id = active_piece->shape.color_id;
	int locked = 0;
	for (const CoordND &cell : active_piece->cells()) {
		if (cell.values[static_cast<std::size_t>(gravity_axis)] < 0) {
			game_over = true;
			game_over_reason = "out_of_bounds";
			active_piece.reset();
			return 0;
		}
		board.set_cell(cell, color_id);
		++locked;
	}
	active_piece.reset();
	score += lock_piece_points;
	return locked;
}

void GameStateND::spawn_piece(const PieceShapeND &shape) {
	if (game_over) {
		return;
	}
	active_piece = ActivePieceND::from_shape(shape, spawn_pos_for_shape(board.shape(), gravity_axis, shape));
	if (!can_exist(*active_piece)) {
		game_over = true;
		game_over_reason = "spawn_blocked";
		active_piece.reset();
	}
}

CommandResultND GameStepperND::apply(GameStateND &state, const GameCommandND &command) {
	CommandResultND result;
	result.active_cells_before = state.active_cells();
	const int locked_before = static_cast<int>(state.board.cells().size());
	if (command.kind == GameCommandKindND::MoveAxis) {
		result.return_value = state.try_move_axis(command.axis, command.delta);
	} else if (command.kind == GameCommandKindND::SoftDrop) {
		result.return_value = state.try_soft_drop();
	} else if (command.kind == GameCommandKindND::HardDrop) {
		state.hard_drop();
		result.return_value = std::nullopt;
	} else if (command.kind == GameCommandKindND::Noop) {
		result.return_value = true;
	}
	const int locked_after = static_cast<int>(state.board.cells().size());
	result.locked_cell_delta = locked_after - locked_before;
	return result;
}

PieceShapeND trace_shape_3d() {
	return {"TRACE_3D", {{{0, 0, 0}}, {{1, 0, 0}}}, 8};
}

PieceShapeND trace_shape_4d() {
	return {"TRACE_4D", {{{0, 0, 0, 0}}, {{1, 0, 0, 0}}}, 8};
}

PieceShapeND native_i_shape_3d() {
	return {"I3", {{{-1, 0, 0}}, {{0, 0, 0}}, {{1, 0, 0}}, {{2, 0, 0}}}, 1};
}

PieceShapeND standard_stair_shape_4d() {
	return {
		"STAIR4",
		{
			{{0, 0, 0, 0}},
			{{0, 1, 0, 0}},
			{{1, 1, 0, 0}},
			{{1, 1, 1, 0}},
			{{1, 1, 1, 1}},
		},
		6,
	};
}

CoordND spawn_pos_for_shape(const BoardShapeND &shape, int gravity_axis, const PieceShapeND &piece_shape) {
	CoordND result;
	result.values.resize(shape.dims.size(), 0);
	for (int axis = 0; axis < shape.dimension(); ++axis) {
		int min_axis = piece_shape.blocks.front().values[static_cast<std::size_t>(axis)];
		int max_axis = min_axis;
		for (const CoordND &block : piece_shape.blocks) {
			const int value = block.values[static_cast<std::size_t>(axis)];
			min_axis = std::min(min_axis, value);
			max_axis = std::max(max_axis, value);
		}
		if (axis == gravity_axis) {
			result.values[static_cast<std::size_t>(axis)] = -2 - min_axis;
		} else {
			const int span = max_axis - min_axis + 1;
			const int start = (shape.dims[static_cast<std::size_t>(axis)] - span) / 2;
			result.values[static_cast<std::size_t>(axis)] = start - min_axis;
		}
	}
	return result;
}

} // namespace tet4d::core
