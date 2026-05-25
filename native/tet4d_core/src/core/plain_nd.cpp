#include "tet4d_core/plain_nd.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <set>
#include <utility>

namespace tet4d::core {
namespace {

bool coord_dimension_matches(const CoordND &coord, int dimension) {
	return static_cast<int>(coord.values.size()) == dimension;
}

int positive_modulo_quarter_turns(int value) {
	const int remainder = value % 4;
	return remainder < 0 ? remainder + 4 : remainder;
}

int python_round_to_int(double value) {
	const double lower = std::floor(value);
	const double fraction = value - lower;
	constexpr double EPSILON = 1e-9;
	if (fraction < 0.5 - EPSILON) {
		return static_cast<int>(lower);
	}
	if (fraction > 0.5 + EPSILON) {
		return static_cast<int>(std::ceil(value));
	}
	const int lower_int = static_cast<int>(lower);
	if (lower_int % 2 == 0) {
		return lower_int;
	}
	return static_cast<int>(std::ceil(value));
}

std::vector<CoordND> rotate_blocks_nd(
		const std::vector<CoordND> &blocks,
		int axis_a,
		int axis_b,
		int delta_steps) {
	if (blocks.empty()) {
		return {};
	}
	const int dimension = blocks.front().dimension();
	if (axis_a == axis_b || axis_a < 0 || axis_b < 0 || axis_a >= dimension || axis_b >= dimension) {
		return blocks;
	}
	for (const CoordND &block : blocks) {
		if (block.dimension() != dimension) {
			return blocks;
		}
	}
	std::vector<CoordND> rotated = blocks;
	const int steps = positive_modulo_quarter_turns(delta_steps);
	for (int step = 0; step < steps; ++step) {
		int min_a = rotated.front().values[static_cast<std::size_t>(axis_a)];
		int max_a = min_a;
		int min_b = rotated.front().values[static_cast<std::size_t>(axis_b)];
		int max_b = min_b;
		for (const CoordND &block : rotated) {
			const int value_a = block.values[static_cast<std::size_t>(axis_a)];
			const int value_b = block.values[static_cast<std::size_t>(axis_b)];
			min_a = std::min(min_a, value_a);
			max_a = std::max(max_a, value_a);
			min_b = std::min(min_b, value_b);
			max_b = std::max(max_b, value_b);
		}

		const bool a_even = ((max_a - min_a) % 2) == 0;
		const bool b_even = ((max_b - min_b) % 2) == 0;
		double pivot_a = 0.0;
		double pivot_b = 0.0;
		if (a_even == b_even) {
			pivot_a = (static_cast<double>(min_a) + static_cast<double>(max_a)) / 2.0;
			pivot_b = (static_cast<double>(min_b) + static_cast<double>(max_b)) / 2.0;
		} else {
			double center_mass_a = 0.0;
			double center_mass_b = 0.0;
			for (const CoordND &block : rotated) {
				center_mass_a += block.values[static_cast<std::size_t>(axis_a)];
				center_mass_b += block.values[static_cast<std::size_t>(axis_b)];
			}
			center_mass_a /= static_cast<double>(rotated.size());
			center_mass_b /= static_cast<double>(rotated.size());

			double min_dist_sq = std::numeric_limits<double>::infinity();
			CoordND pivot_block = rotated.front();
			for (const CoordND &block : rotated) {
				const double da = static_cast<double>(block.values[static_cast<std::size_t>(axis_a)]) - center_mass_a;
				const double db = static_cast<double>(block.values[static_cast<std::size_t>(axis_b)]) - center_mass_b;
				const double dist_sq = da * da + db * db;
				if (dist_sq < min_dist_sq) {
					min_dist_sq = dist_sq;
					pivot_block = block;
				}
			}
			pivot_a = static_cast<double>(pivot_block.values[static_cast<std::size_t>(axis_a)]);
			pivot_b = static_cast<double>(pivot_block.values[static_cast<std::size_t>(axis_b)]);
		}

		std::vector<CoordND> step_blocks;
		step_blocks.reserve(rotated.size());
		for (const CoordND &block : rotated) {
			CoordND next = block;
			const double rel_a = static_cast<double>(block.values[static_cast<std::size_t>(axis_a)]) - pivot_a;
			const double rel_b = static_cast<double>(block.values[static_cast<std::size_t>(axis_b)]) - pivot_b;
			next.values[static_cast<std::size_t>(axis_a)] = python_round_to_int(rel_b + pivot_a);
			next.values[static_cast<std::size_t>(axis_b)] = python_round_to_int(-rel_a + pivot_b);
			step_blocks.push_back(next);
		}
		rotated = std::move(step_blocks);
	}
	return rotated;
}

int score_for_clear(int cleared_count) {
	if (cleared_count <= 0) {
		return 0;
	}
	if (cleared_count == 1) {
		return 40;
	}
	if (cleared_count == 2) {
		return 100;
	}
	if (cleared_count == 3) {
		return 300;
	}
	if (cleared_count == 4) {
		return 1200;
	}
	return 1200 + (cleared_count - 4) * 400;
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

int BoardND::clear_planes(int gravity_axis) {
	const int dimension = shape_.dimension();
	if (gravity_axis < 0 || gravity_axis >= dimension || cells_.empty()) {
		return 0;
	}
	const int axis_size = shape_.dims[static_cast<std::size_t>(gravity_axis)];
	int max_per_level = 1;
	for (int axis = 0; axis < dimension; ++axis) {
		if (axis != gravity_axis) {
			max_per_level *= shape_.dims[static_cast<std::size_t>(axis)];
		}
	}
	std::vector<int> level_counts(static_cast<std::size_t>(axis_size), 0);
	for (const auto &[coord, _value] : cells_) {
		const int level = coord.values[static_cast<std::size_t>(gravity_axis)];
		if (level >= 0 && level < axis_size) {
			level_counts[static_cast<std::size_t>(level)] += 1;
		}
	}
	std::set<int> full_levels;
	for (int level = 0; level < axis_size; ++level) {
		if (level_counts[static_cast<std::size_t>(level)] == max_per_level) {
			full_levels.insert(level);
		}
	}
	if (full_levels.empty()) {
		return 0;
	}

	std::map<CoordND, int> compacted;
	for (const auto &[coord, value] : cells_) {
		const int level = coord.values[static_cast<std::size_t>(gravity_axis)];
		if (full_levels.find(level) != full_levels.end()) {
			continue;
		}
		int shift = 0;
		for (const int cleared_level : full_levels) {
			if (cleared_level > level) {
				++shift;
			}
		}
		CoordND next = coord;
		next.values[static_cast<std::size_t>(gravity_axis)] = level + shift;
		if (next.values[static_cast<std::size_t>(gravity_axis)] < axis_size) {
			compacted[next] = value;
		}
	}
	cells_ = std::move(compacted);
	return static_cast<int>(full_levels.size());
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

ActivePieceND ActivePieceND::rotated(int axis_a, int axis_b, int delta_steps) const {
	ActivePieceND result = *this;
	result.rel_blocks = rotate_blocks_nd(rel_blocks, axis_a, axis_b, delta_steps);
	result.last_rotation_plane = std::vector<int>{axis_a, axis_b};
	result.last_rotation_steps = delta_steps;
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

bool GameStateND::try_rotate(int axis_a, int axis_b, int delta_steps) {
	if (game_over) {
		return false;
	}
	if (!active_piece.has_value()) {
		game_over = true;
		game_over_reason = "no_active_piece";
		return false;
	}
	const int dimension = board.shape().dimension();
	if (axis_a == axis_b || axis_a < 0 || axis_b < 0 || axis_a >= dimension || axis_b >= dimension) {
		game_over_reason = "invalid_rotation_axis";
		return false;
	}
	const ActivePieceND rotated = active_piece->rotated(axis_a, axis_b, delta_steps);
	if (!can_exist(rotated)) {
		return false;
	}
	active_piece = rotated;
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
	for (const CoordND &cell : active_piece->cells()) {
		if (cell.values[static_cast<std::size_t>(gravity_axis)] < 0) {
			game_over = true;
			game_over_reason = "out_of_bounds";
			return 0;
		}
		board.set_cell(cell, color_id);
	}
	const int cleared = board.clear_planes(gravity_axis);
	lines += cleared;
	score += lock_piece_points + score_for_clear(cleared);
	return cleared;
}

void GameStateND::spawn_piece(const PieceShapeND &shape) {
	if (game_over) {
		return;
	}
	active_piece = ActivePieceND::from_shape(shape, spawn_pos_for_shape(board.shape(), gravity_axis, shape));
	if (!can_exist(*active_piece)) {
		game_over = true;
		game_over_reason = "spawn_blocked";
	}
}

CommandResultND GameStepperND::apply(GameStateND &state, const GameCommandND &command) {
	CommandResultND result;
	result.active_cells_before = state.active_cells();
	const int locked_before = static_cast<int>(state.board.cells().size());
	if (command.kind == GameCommandKindND::MoveAxis) {
		result.return_value = state.try_move_axis(command.axis, command.delta);
	} else if (command.kind == GameCommandKindND::Rotate) {
		result.return_value = state.try_rotate(command.axis, command.axis_b, command.delta);
	} else if (command.kind == GameCommandKindND::SoftDrop) {
		result.return_value = state.try_soft_drop();
	} else if (command.kind == GameCommandKindND::HardDrop) {
		state.hard_drop();
		result.return_value = std::nullopt;
	} else if (command.kind == GameCommandKindND::LockCurrentPiece) {
		result.return_int_value = state.lock_current_piece();
	} else if (command.kind == GameCommandKindND::SpawnNewPiece) {
		if (state.post_lock_spawn_shape.has_value()) {
			state.spawn_piece(*state.post_lock_spawn_shape);
		}
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

PieceShapeND trace_single_shape_3d() {
	return {"TRACE_3D", {{{0, 0, 0}}}, 8};
}

PieceShapeND trace_single_shape_4d() {
	return {"TRACE_4D", {{{0, 0, 0, 0}}}, 8};
}

PieceShapeND trace_spawn_blocked_shape_3d() {
	return {"TRACE_3D_NEXT", {{{0, 0, 0}}, {{0, 2, 0}}}, 7};
}

PieceShapeND trace_spawn_blocked_shape_4d() {
	return {"TRACE_4D_NEXT", {{{0, 0, 0, 0}}, {{0, 2, 0, 0}}}, 7};
}

PieceShapeND trace_rotation_shape_3d() {
	return {"TRACE_3D", {{{0, 0, 0}}, {{1, 0, 0}}, {{0, 1, 0}}, {{0, 0, 1}}}, 8};
}

PieceShapeND trace_rotation_shape_4d() {
	return {
		"TRACE_4D",
		{
			{{0, 0, 0, 0}},
			{{1, 0, 0, 0}},
			{{0, 1, 0, 0}},
			{{0, 0, 1, 0}},
		},
		8,
	};
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
