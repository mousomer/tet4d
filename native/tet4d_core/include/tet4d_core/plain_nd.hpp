#pragma once

#include <map>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

struct CoordND {
	std::vector<int> values;

	int dimension() const;
	bool operator<(const CoordND &other) const;
	bool operator==(const CoordND &other) const;
};

struct BoardShapeND {
	std::vector<int> dims;

	int dimension() const;
	bool is_valid() const;
	bool matches(const CoordND &coord) const;
};

struct CellND {
	CoordND coord;
	int value = 0;
};

class BoardND {
public:
	explicit BoardND(BoardShapeND shape);

	const BoardShapeND &shape() const;
	const std::map<CoordND, int> &cells() const;
	bool has_cell(const CoordND &coord) const;
	void set_cell(const CoordND &coord, int value);
	int clear_planes(int gravity_axis);

private:
	BoardShapeND shape_;
	std::map<CoordND, int> cells_;
};

struct PieceShapeND {
	std::string name;
	std::vector<CoordND> blocks;
	int color_id = 0;
};

struct ActivePieceND {
	PieceShapeND shape;
	CoordND pos;
	std::vector<CoordND> rel_blocks;
	std::optional<std::vector<int>> last_rotation_plane;
	int last_rotation_steps = 0;

	static ActivePieceND from_shape(const PieceShapeND &shape, const CoordND &pos);
	std::vector<CoordND> cells() const;
	ActivePieceND moved_axis(int axis, int delta) const;
	ActivePieceND rotated(int axis_a, int axis_b, int delta_steps) const;
};

struct GameStateND {
	BoardND board;
	int gravity_axis = 1;
	std::optional<ActivePieceND> active_piece;
	std::optional<PieceShapeND> post_lock_spawn_shape;
	int score = 0;
	int lines = 0;
	bool game_over = false;
	std::string game_over_reason;
	int lock_piece_points = 5;

	explicit GameStateND(BoardShapeND shape, int gravity_axis = 1);
	std::vector<CoordND> active_cells() const;
	bool can_exist(const ActivePieceND &piece) const;
	bool try_move_axis(int axis, int delta);
	bool try_rotate(int axis_a, int axis_b, int delta_steps);
	bool try_soft_drop();
	void hard_drop();
	int lock_current_piece();
	void spawn_piece(const PieceShapeND &shape);
};

enum class GameCommandKindND {
	MoveAxis,
	Rotate,
	SoftDrop,
	HardDrop,
	LockCurrentPiece,
	Noop,
};

struct GameCommandND {
	std::string id;
	GameCommandKindND kind = GameCommandKindND::Noop;
	int axis = 0;
	int delta = 0;
	int axis_b = 0;
};

struct CommandResultND {
	std::vector<CoordND> active_cells_before;
	int locked_cell_delta = 0;
	std::optional<bool> return_value;
	std::optional<int> return_int_value;
};

class GameStepperND {
public:
	static CommandResultND apply(GameStateND &state, const GameCommandND &command);
};

PieceShapeND trace_shape_3d();
PieceShapeND trace_shape_4d();
PieceShapeND trace_single_shape_3d();
PieceShapeND trace_single_shape_4d();
PieceShapeND trace_rotation_shape_3d();
PieceShapeND trace_rotation_shape_4d();
PieceShapeND native_i_shape_3d();
PieceShapeND standard_stair_shape_4d();
CoordND spawn_pos_for_shape(const BoardShapeND &shape, int gravity_axis, const PieceShapeND &piece_shape);

} // namespace tet4d::core
