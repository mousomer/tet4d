#include "tet4d_core/plain_2d.hpp"

#include <algorithm>
#include <set>

namespace tet4d::core {

bool Coord2D::operator<(const Coord2D &other) const {
	if (x != other.x) {
		return x < other.x;
	}
	return y < other.y;
}

bool Coord2D::operator==(const Coord2D &other) const {
	return x == other.x && y == other.y;
}

std::vector<Coord2D> ActivePiece2D::cells() const {
	std::vector<Coord2D> result;
	result.reserve(shape.blocks.size());
	for (const Coord2D &block : shape.blocks) {
		// Stage 9 only needs rotation=0 for gameplay_plain_2d_short.
		result.push_back({pos.x + block.x, pos.y + block.y});
	}
	std::sort(result.begin(), result.end());
	return result;
}

ActivePiece2D ActivePiece2D::moved(int dx, int dy) const {
	ActivePiece2D result = *this;
	result.pos.x += dx;
	result.pos.y += dy;
	return result;
}

Board2D::Board2D(int width, int height) : width_(width), height_(height) {
}

int Board2D::width() const {
	return width_;
}

int Board2D::height() const {
	return height_;
}

const std::map<Coord2D, int> &Board2D::cells() const {
	return cells_;
}

bool Board2D::has_cell(const Coord2D &coord) const {
	return cells_.find(coord) != cells_.end();
}

void Board2D::set_cell(const Coord2D &coord, int value) {
	cells_[coord] = value;
}

int Board2D::clear_full_lines() {
	std::set<int> full_rows;
	for (int y = 0; y < height_; ++y) {
		bool full = true;
		for (int x = 0; x < width_; ++x) {
			if (!has_cell({x, y})) {
				full = false;
				break;
			}
		}
		if (full) {
			full_rows.insert(y);
		}
	}
	if (full_rows.empty()) {
		return 0;
	}

	std::map<Coord2D, int> shifted;
	for (const auto &[coord, value] : cells_) {
		if (full_rows.find(coord.y) != full_rows.end()) {
			continue;
		}
		int drop = 0;
		for (const int full_y : full_rows) {
			if (coord.y < full_y) {
				++drop;
			}
		}
		shifted[{coord.x, coord.y + drop}] = value;
	}
	cells_ = shifted;
	return static_cast<int>(full_rows.size());
}

GameState2D::GameState2D(int width, int height) : board(width, height) {
}

std::vector<Coord2D> GameState2D::active_cells() const {
	if (!active_piece.has_value()) {
		return {};
	}
	return active_piece->cells();
}

bool GameState2D::can_exist(const ActivePiece2D &piece) const {
	for (const Coord2D &cell : piece.cells()) {
		if (cell.x < 0 || cell.x >= board.width() || cell.y >= board.height()) {
			return false;
		}
		if (cell.y >= 0 && board.has_cell(cell)) {
			return false;
		}
	}
	return true;
}

bool GameState2D::try_move(int dx, int dy) {
	if (!active_piece.has_value()) {
		return false;
	}
	const ActivePiece2D moved = active_piece->moved(dx, dy);
	if (!can_exist(moved)) {
		return false;
	}
	active_piece = moved;
	return true;
}

bool GameState2D::try_soft_drop() {
	return try_move(0, 1);
}

void GameState2D::hard_drop() {
	while (try_move(0, 1)) {
	}
	lock_current_piece();
	spawn_i_piece();
}

int GameState2D::lock_current_piece() {
	if (!active_piece.has_value()) {
		return 0;
	}

	for (const Coord2D &cell : active_piece->cells()) {
		if (cell.y < 0) {
			game_over = true;
			continue;
		}
		board.set_cell(cell, active_piece->shape.color_id);
	}

	const int cleared = board.clear_full_lines();
	lines += cleared;
	score += lock_piece_points;
	// gameplay_plain_2d_short does not clear a line. Later stages should port
	// Python's full score table before expanding the trace surface.
	return cleared;
}

void GameState2D::spawn_i_piece() {
	active_piece = ActivePiece2D{classic_i_shape_2d(), {2, -2}, 0};
	if (!can_exist(*active_piece)) {
		game_over = true;
	}
}

CommandResult2D GameStepper2D::apply(GameState2D &state, const GameCommand2D &command) {
	CommandResult2D result;
	result.active_cells_before = state.active_cells();
	const int locked_before = static_cast<int>(state.board.cells().size());
	if (command.kind == GameCommandKind2D::Move) {
		result.return_value = state.try_move(command.dx, command.dy);
	} else if (command.kind == GameCommandKind2D::SoftDrop) {
		result.return_value = state.try_soft_drop();
	} else if (command.kind == GameCommandKind2D::HardDrop) {
		state.hard_drop();
		result.return_value = std::nullopt;
	}
	const int locked_after = static_cast<int>(state.board.cells().size());
	result.locked_cell_delta = locked_after - locked_before;
	return result;
}

PieceShape2D trace_domino_shape_2d() {
	return {"TRACE_2D", {{0, 0}, {1, 0}}, 8};
}

PieceShape2D classic_i_shape_2d() {
	return {"I", {{-1, 0}, {0, 0}, {1, 0}, {2, 0}}, 1};
}

GameState2D make_builtin_plain_2d_initial_state() {
	GameState2D state(6, 6);
	state.active_piece = ActivePiece2D{trace_domino_shape_2d(), {2, 3}, 0};
	return state;
}

std::vector<GameCommand2D> builtin_plain_2d_commands() {
	return {
		{"move_right", GameCommandKind2D::Move, 1, 0},
		{"soft_drop", GameCommandKind2D::SoftDrop, 0, 1},
		{"hard_drop", GameCommandKind2D::HardDrop, 0, 0},
	};
}

} // namespace tet4d::core
