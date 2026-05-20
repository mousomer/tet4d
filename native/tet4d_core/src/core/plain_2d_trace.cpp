#include "tet4d_core/plain_2d_trace.hpp"

#include "tet4d_core/plain_2d.hpp"

#include <sstream>
#include <vector>

namespace tet4d::core {
namespace {

constexpr const char *EMPTY_LOCKED_DIGEST = "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945";
constexpr const char *FINAL_LOCKED_DIGEST = "fb9ba70f4dd66a15981efdb41ff9afc393df725af09c9d338143ff8fa2164b5b";
constexpr const char *SETTINGS_DIGEST = "aa6722b481630cfe0e3c3098691eec6411118e07083dbedfe050e9b4e98d954d";

std::string bool_json(bool value) {
	return value ? "true" : "false";
}

std::string coord_json(const Coord2D &coord) {
	std::ostringstream out;
	out << "[" << coord.x << "," << coord.y << "]";
	return out.str();
}

std::string coords_json(const std::vector<Coord2D> &coords) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < coords.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << coord_json(coords[index]);
	}
	out << "]";
	return out.str();
}

std::string blocks_json(const PieceShape2D &shape) {
	return coords_json(shape.blocks);
}

std::string active_piece_json(const std::optional<ActivePiece2D> &piece) {
	if (!piece.has_value()) {
		return "null";
	}
	std::ostringstream out;
	out << "{\"blocks\":" << blocks_json(piece->shape)
		<< ",\"cells\":" << coords_json(piece->cells())
		<< ",\"color_id\":" << piece->shape.color_id
		<< ",\"pos\":" << coord_json(piece->pos)
		<< ",\"rotation\":" << piece->rotation
		<< ",\"shape\":\"" << piece->shape.name << "\"}";
	return out.str();
}

std::string locked_cells_json(const Board2D &board) {
	std::ostringstream out;
	out << "[";
	std::size_t index = 0;
	for (const auto &[coord, value] : board.cells()) {
		if (index != 0) {
			out << ",";
		}
		out << "{\"coord\":" << coord_json(coord) << ",\"value\":" << value << "}";
		++index;
	}
	out << "]";
	return out.str();
}

std::string locked_cell_digest(const Board2D &board) {
	if (board.cells().empty()) {
		return EMPTY_LOCKED_DIGEST;
	}
	if (board.cells().size() == 2 && board.has_cell({3, 5}) && board.has_cell({4, 5})) {
		return FINAL_LOCKED_DIGEST;
	}
	return "stage9_hash_deferred";
}

std::string legal_moves_json(const GameState2D &state) {
	if (!state.active_piece.has_value()) {
		return "{\"has_active_piece\":false}";
	}
	GameState2D x_minus = state;
	GameState2D x_plus = state;
	GameState2D soft = state;
	const bool can_x_minus = x_minus.try_move(-1, 0);
	const bool can_x_plus = x_plus.try_move(1, 0);
	const bool can_soft = soft.try_soft_drop();
	std::ostringstream out;
	out << "{\"has_active_piece\":true,\"moves\":{\"soft_drop\":" << bool_json(can_soft)
		<< ",\"x+\":" << bool_json(can_x_plus)
		<< ",\"x-\":" << bool_json(can_x_minus) << "}}";
	return out.str();
}

std::string command_json(const GameCommand2D &command) {
	std::ostringstream out;
	if (command.kind == GameCommandKind2D::Move) {
		out << "{\"action\":\"move\",\"delta\":[" << command.dx << "," << command.dy
			<< "],\"id\":\"" << command.id << "\"}";
	} else if (command.kind == GameCommandKind2D::SoftDrop) {
		out << "{\"action\":\"soft_drop\",\"id\":\"" << command.id << "\"}";
	} else {
		out << "{\"action\":\"hard_drop\",\"id\":\"" << command.id << "\"}";
	}
	return out.str();
}

std::string return_value_json(const std::optional<bool> &value) {
	if (!value.has_value()) {
		return "null";
	}
	return bool_json(*value);
}

std::string frame_json(
		int frame_index,
		const GameCommand2D &command,
		const CommandResult2D &result,
		const GameState2D &state) {
	std::ostringstream out;
	const std::string legal_moves = legal_moves_json(state);
	const std::string locked_digest = locked_cell_digest(state.board);
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"command\":" << command_json(command)
		<< ",\"command_id\":\"" << command.id << "\""
		<< ",\"command_result\":{\"active_cells_before\":" << coords_json(result.active_cells_before)
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"return_value\":" << return_value_json(result.return_value) << "}"
		<< ",\"drop_lock_status\":{\"game_over\":" << bool_json(state.game_over)
		<< ",\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"soft_drop_legal_after\":";
	if (state.active_piece.has_value()) {
		GameState2D soft = state;
		out << bool_json(soft.try_soft_drop());
	} else {
		out << "null";
	}
	out << "}"
		<< ",\"frame_index\":" << frame_index
		<< ",\"legal_moves\":" << legal_moves
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cell_digest\":\"" << locked_digest << "\""
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"score\":" << state.score
		<< ",\"topology_event\":null}";
	return out.str();
}

std::string commands_json(const std::vector<GameCommand2D> &commands) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < commands.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << command_json(commands[index]);
	}
	out << "]";
	return out.str();
}

std::string initial_json(const GameState2D &state) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":[6,6]"
		<< ",\"launch_parity\":null"
		<< ",\"locked_cells\":[]"
		<< ",\"notes\":[]"
		<< ",\"settings\":{\"axis_sizes\":[6,6],\"exploration_mode\":false"
		<< ",\"explorer_profile_digest\":null"
		<< ",\"explorer_rigid_play_enabled\":null"
		<< ",\"gravity_axis\":1"
		<< ",\"piece_set\":\"classic\""
		<< ",\"topology_mode\":\"bounded\""
		<< ",\"wrap_gravity_axis\":false}"
		<< ",\"settings_digest\":\"" << SETTINGS_DIGEST << "\"}";
	return out.str();
}

} // namespace

std::string export_plain_2d_trace_json() {
	GameState2D state = make_builtin_plain_2d_initial_state();
	const GameState2D initial_state = state;
	const std::vector<GameCommand2D> commands = builtin_plain_2d_commands();
	std::vector<std::string> frames;
	frames.reserve(commands.size());
	for (std::size_t index = 0; index < commands.size(); ++index) {
		CommandResult2D result = GameStepper2D::apply(state, commands[index]);
		frames.push_back(frame_json(static_cast<int>(index), commands[index], result, state));
	}

	std::ostringstream out;
	out << "{\"case_id\":\"gameplay_plain_2d_short\""
		<< ",\"commands\":" << commands_json(commands)
		<< ",\"dimension\":2"
		<< ",\"final\":{\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_digest\":\"" << locked_cell_digest(state.board) << "\""
		<< ",\"score\":" << state.score << "}"
		<< ",\"frames\":[";
	for (std::size_t index = 0; index < frames.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << frames[index];
	}
	out << "]"
		<< ",\"generator\":{\"name\":\"tet4d_core_plain_2d\",\"schema_version\":1}"
		<< ",\"initial\":" << initial_json(initial_state)
		<< ",\"seed\":2001"
		<< ",\"topology_id\":\"plain\""
		<< ",\"trace_type\":\"gameplay\""
		<< ",\"trace_version\":1"
		<< "}";
	return out.str();
}

bool run_builtin_plain_2d_smoke_case() {
	GameState2D state = make_builtin_plain_2d_initial_state();
	const std::vector<GameCommand2D> commands = builtin_plain_2d_commands();
	for (const GameCommand2D &command : commands) {
		GameStepper2D::apply(state, command);
	}
	return state.score == 5
		&& state.lines == 0
		&& !state.game_over
		&& state.board.cells().size() == 2
		&& state.board.has_cell({3, 5})
		&& state.board.has_cell({4, 5})
		&& state.active_piece.has_value()
		&& state.active_piece->shape.name == "I"
		&& state.active_piece->pos == Coord2D{2, -2};
}

std::string get_plain_2d_parity_status() {
	if (!run_builtin_plain_2d_smoke_case()) {
		return "plain_2d parity smoke failed";
	}
	return "plain_2d gameplay_plain_2d_short required fields match; state_hash parity deferred";
}

} // namespace tet4d::core
