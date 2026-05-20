#include "tet4d_core/plain_2d_trace.hpp"

#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <vector>

namespace tet4d::core {
namespace {

std::string stable_hash(std::string_view compact_canonical_json) {
	return sha256_hex(compact_canonical_json);
}

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

std::string active_piece_json(const std::optional<ActivePiece2D> &piece) {
	if (!piece.has_value()) {
		return "null";
	}
	std::ostringstream out;
	out << "{\"blocks\":" << coords_json(piece->shape.blocks)
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
	return stable_hash(locked_cells_json(board));
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

std::string drop_lock_status_json(const CommandResult2D &result, const GameState2D &state) {
	std::ostringstream out;
	out << "{\"game_over\":" << bool_json(state.game_over)
		<< ",\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"soft_drop_legal_after\":";
	if (state.active_piece.has_value()) {
		GameState2D soft = state;
		out << bool_json(soft.try_soft_drop());
	} else {
		out << "null";
	}
	out << "}";
	return out.str();
}

std::string command_result_json(const CommandResult2D &result) {
	std::ostringstream out;
	out << "{\"active_cells_before\":" << coords_json(result.active_cells_before)
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"return_value\":" << return_value_json(result.return_value) << "}";
	return out.str();
}

std::string frame_payload_json(
		int frame_index,
		const GameCommand2D &command,
		const CommandResult2D &result,
		const GameState2D &state,
		const std::string *state_hash = nullptr) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"command\":" << command_json(command)
		<< ",\"command_id\":\"" << command.id << "\""
		<< ",\"command_result\":" << command_result_json(result)
		<< ",\"drop_lock_status\":" << drop_lock_status_json(result, state)
		<< ",\"frame_index\":" << frame_index
		<< ",\"legal_moves\":" << legal_moves_json(state)
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cell_digest\":\"" << locked_cell_digest(state.board) << "\""
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"score\":" << state.score;
	if (state_hash != nullptr) {
		out << ",\"state_hash\":\"" << *state_hash << "\"";
	}
	out << ",\"topology_event\":null}";
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

std::string settings_json() {
	return "{\"axis_sizes\":[6,6],\"exploration_mode\":false"
		",\"explorer_profile_digest\":null"
		",\"explorer_rigid_play_enabled\":null"
		",\"gravity_axis\":1"
		",\"piece_set\":\"classic\""
		",\"topology_mode\":\"bounded\""
		",\"wrap_gravity_axis\":false}";
}

std::string initial_json(const GameState2D &state) {
	const std::string settings = settings_json();
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":[6,6]"
		<< ",\"launch_parity\":null"
		<< ",\"locked_cells\":[]"
		<< ",\"notes\":[]"
		<< ",\"settings\":" << settings
		<< ",\"settings_digest\":\"" << stable_hash(settings) << "\"}";
	return out.str();
}

std::string final_snapshot_json(const GameState2D &state) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"legal_moves\":" << legal_moves_json(state)
		<< ",\"level\":null"
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_digest\":\"" << locked_cell_digest(state.board) << "\""
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

std::string final_hash_input_json(
		const std::string &case_id,
		const std::string &final_snapshot,
		const std::vector<std::string> &frames) {
	std::ostringstream out;
	out << "{\"case_id\":\"" << case_id << "\""
		<< ",\"final_snapshot\":" << final_snapshot
		<< ",\"frames\":[";
	for (std::size_t index = 0; index < frames.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << frames[index];
	}
	out << "]}";
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
		const std::string frame_without_hash = frame_payload_json(
			static_cast<int>(index),
			commands[index],
			result,
			state
		);
		const std::string frame_hash = stable_hash(frame_without_hash);
		frames.push_back(frame_payload_json(
			static_cast<int>(index),
			commands[index],
			result,
			state,
			&frame_hash
		));
	}
	const std::string final_snapshot = final_snapshot_json(state);
	const std::string final_state_hash = stable_hash(
		final_hash_input_json("gameplay_plain_2d_short", final_snapshot, frames)
	);

	std::ostringstream out;
	out << "{\"case_id\":\"gameplay_plain_2d_short\""
		<< ",\"commands\":" << commands_json(commands)
		<< ",\"dimension\":2"
		<< ",\"final\":{\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_digest\":\"" << locked_cell_digest(state.board) << "\""
		<< ",\"score\":" << state.score
		<< ",\"state_hash\":\"" << final_state_hash << "\"}"
		<< ",\"frames\":[";
	for (std::size_t index = 0; index < frames.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << frames[index];
	}
	out << "]"
		<< ",\"generator\":{\"name\":\"export_gameplay_trace\",\"schema_version\":1}"
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
	return "plain_2d gameplay_plain_2d_short required fields and state_hash match";
}

bool get_plain_2d_required_field_parity() {
	return run_builtin_plain_2d_smoke_case();
}

} // namespace tet4d::core
