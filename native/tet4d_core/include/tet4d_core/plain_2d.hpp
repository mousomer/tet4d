#pragma once

#include <map>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

struct Coord2D {
	int x = 0;
	int y = 0;

	bool operator<(const Coord2D &other) const;
	bool operator==(const Coord2D &other) const;
};

struct PieceShape2D {
	std::string name;
	std::vector<Coord2D> blocks;
	int color_id = 0;
};

struct ActivePiece2D {
	PieceShape2D shape;
	Coord2D pos;
	int rotation = 0;

	std::vector<Coord2D> cells() const;
	ActivePiece2D moved(int dx, int dy) const;
	ActivePiece2D rotated(int delta_steps) const;
};

class Board2D {
public:
	Board2D(int width, int height);

	int width() const;
	int height() const;
	const std::map<Coord2D, int> &cells() const;
	bool has_cell(const Coord2D &coord) const;
	void set_cell(const Coord2D &coord, int value);
	int clear_full_lines();

private:
	int width_;
	int height_;
	std::map<Coord2D, int> cells_;
};

struct GameState2D {
	Board2D board;
	std::optional<ActivePiece2D> active_piece;
	std::optional<PieceShape2D> post_lock_spawn_shape;
	int score = 0;
	int lines = 0;
	bool game_over = false;
	std::string game_over_reason;
	int lock_piece_points = 5;

	GameState2D(int width, int height);
	std::vector<Coord2D> active_cells() const;
	bool can_exist(const ActivePiece2D &piece) const;
	bool try_move(int dx, int dy);
	bool try_soft_drop();
	void try_rotate(int delta_steps);
	void hard_drop();
	int lock_current_piece();
	void spawn_piece(const PieceShape2D &shape);
};

enum class GameCommandKind2D {
	Move,
	SoftDrop,
	HardDrop,
	Rotate,
};

struct GameCommand2D {
	std::string id;
	GameCommandKind2D kind = GameCommandKind2D::Move;
	int dx = 0;
	int dy = 0;
};

struct CommandResult2D {
	std::vector<Coord2D> active_cells_before;
	int locked_cell_delta = 0;
	std::optional<bool> return_value;
};

class GameStepper2D {
public:
	static CommandResult2D apply(GameState2D &state, const GameCommand2D &command);
};

PieceShape2D trace_domino_shape_2d();
PieceShape2D trace_dot_shape_2d();
PieceShape2D trace_t_shape_2d();
PieceShape2D classic_i_shape_2d();
PieceShape2D classic_s_shape_2d();
GameState2D make_builtin_plain_2d_initial_state();
std::vector<GameCommand2D> builtin_plain_2d_commands();

} // namespace tet4d::core
