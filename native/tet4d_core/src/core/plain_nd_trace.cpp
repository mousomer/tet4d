#include "tet4d_core/plain_nd_trace.hpp"

#include "tet4d_core/plain_nd.hpp"
#include "tet4d_core/sha256.hpp"

#include <algorithm>
#include <optional>
#include <sstream>
#include <utility>
#include <vector>

namespace tet4d::core {
namespace {

struct PlainNDCase {
	std::string case_id;
	int dimension = 0;
	int seed = 0;
	BoardShapeND board_shape;
	int gravity_axis = 1;
	std::string piece_set;
	PieceShapeND active_shape;
	CoordND active_pos;
	std::vector<CellND> initial_locked_cells;
	std::vector<GameCommandND> commands;
	std::optional<PieceShapeND> post_lock_spawn_shape;
	std::vector<std::string> notes;
};

std::string stable_hash(std::string_view compact_canonical_json) {
	return sha256_hex(compact_canonical_json);
}

std::string bool_json(bool value) {
	return value ? "true" : "false";
}

std::string coord_json(const CoordND &coord) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < coord.values.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << coord.values[index];
	}
	out << "]";
	return out.str();
}

std::string coords_json(std::vector<CoordND> coords) {
	std::sort(coords.begin(), coords.end());
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

std::string int_array_json(const std::vector<int> &items) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < items.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << items[index];
	}
	out << "]";
	return out.str();
}

std::string string_array_json(const std::vector<std::string> &items) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < items.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << "\"" << items[index] << "\"";
	}
	out << "]";
	return out.str();
}

std::string active_piece_json(const std::optional<ActivePieceND> &piece) {
	if (!piece.has_value()) {
		return "null";
	}
	std::ostringstream out;
	out << "{\"cells\":" << coords_json(piece->cells())
		<< ",\"color_id\":" << piece->shape.color_id
		<< ",\"last_rotation_plane\":";
	if (piece->last_rotation_plane.has_value()) {
		out << int_array_json(*piece->last_rotation_plane);
	} else {
		out << "null";
	}
	out << ",\"last_rotation_steps\":" << piece->last_rotation_steps
		<< ",\"pos\":" << coord_json(piece->pos)
		<< ",\"rel_blocks\":" << coords_json(piece->rel_blocks)
		<< ",\"shape\":\"" << piece->shape.name << "\"}";
	return out.str();
}

std::string locked_cells_json(const BoardND &board) {
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

std::string locked_cell_digest(const BoardND &board) {
	return stable_hash(locked_cells_json(board));
}

std::string legal_moves_json(const GameStateND &state) {
	if (!state.active_piece.has_value()) {
		return "{\"has_active_piece\":false}";
	}
	std::ostringstream out;
	out << "{\"has_active_piece\":true,\"moves\":{";
	bool first = true;
	for (int axis = 0; axis < state.board.shape().dimension(); ++axis) {
		for (const int delta : {-1, 1}) {
			GameStateND probe = state;
			const bool can_move = probe.try_move_axis(axis, delta);
			if (!first) {
				out << ",";
			}
			first = false;
			out << "\"" << axis << ":" << delta << "\":" << bool_json(can_move);
		}
	}
	GameStateND soft = state;
	out << ",\"soft_drop\":" << bool_json(soft.try_soft_drop()) << "}}";
	return out.str();
}

std::string command_json(const GameCommandND &command) {
	std::ostringstream out;
	if (command.kind == GameCommandKindND::MoveAxis) {
		out << "{\"action\":\"move_axis\",\"axis\":" << command.axis
			<< ",\"delta\":" << command.delta
			<< ",\"id\":\"" << command.id << "\"}";
	} else if (command.kind == GameCommandKindND::Rotate) {
		out << "{\"action\":\"rotate\",\"axis_a\":" << command.axis
			<< ",\"axis_b\":" << command.axis_b
			<< ",\"delta\":" << command.delta
			<< ",\"id\":\"" << command.id << "\"}";
	} else if (command.kind == GameCommandKindND::SoftDrop) {
		out << "{\"action\":\"soft_drop\",\"id\":\"" << command.id << "\"}";
	} else if (command.kind == GameCommandKindND::HardDrop) {
		out << "{\"action\":\"hard_drop\",\"id\":\"" << command.id << "\"}";
	} else if (command.kind == GameCommandKindND::LockCurrentPiece) {
		out << "{\"action\":\"lock_current_piece\",\"id\":\"" << command.id << "\"}";
	} else {
		out << "{\"action\":\"noop\",\"id\":\"" << command.id << "\"}";
	}
	return out.str();
}

std::string return_value_json(const std::optional<bool> &value) {
	if (!value.has_value()) {
		return "null";
	}
	return bool_json(*value);
}

std::string drop_lock_status_json(const CommandResultND &result, const GameStateND &state) {
	std::ostringstream out;
	out << "{\"game_over\":" << bool_json(state.game_over)
		<< ",\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"soft_drop_legal_after\":";
	if (state.active_piece.has_value()) {
		GameStateND soft = state;
		out << bool_json(soft.try_soft_drop());
	} else {
		out << "null";
	}
	out << "}";
	return out.str();
}

std::string command_result_json(const CommandResultND &result) {
	std::ostringstream out;
	out << "{\"active_cells_before\":" << coords_json(result.active_cells_before)
		<< ",\"locked_cell_delta\":" << result.locked_cell_delta
		<< ",\"return_value\":";
	if (result.return_int_value.has_value()) {
		out << *result.return_int_value;
	} else {
		out << return_value_json(result.return_value);
	}
	out << "}";
	return out.str();
}

std::string frame_payload_json(
		int frame_index,
		const GameCommandND &command,
		const CommandResultND &result,
		const GameStateND &state,
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

std::string commands_json(const std::vector<GameCommandND> &commands) {
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

std::string settings_json(const PlainNDCase &trace_case) {
	std::ostringstream out;
	out << "{\"axis_sizes\":" << int_array_json(trace_case.board_shape.dims)
		<< ",\"exploration_mode\":false"
		<< ",\"explorer_profile_digest\":null"
		<< ",\"explorer_rigid_play_enabled\":null"
		<< ",\"gravity_axis\":" << trace_case.gravity_axis
		<< ",\"piece_set\":\"" << trace_case.piece_set << "\""
		<< ",\"topology_mode\":\"bounded\""
		<< ",\"wrap_gravity_axis\":false}";
	return out.str();
}

std::string initial_json(const PlainNDCase &trace_case, const GameStateND &state) {
	const std::string settings = settings_json(trace_case);
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":" << int_array_json(trace_case.board_shape.dims)
		<< ",\"launch_parity\":null"
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"notes\":" << string_array_json(trace_case.notes)
		<< ",\"settings\":" << settings
		<< ",\"settings_digest\":\"" << stable_hash(settings) << "\"}";
	return out.str();
}

std::string piece_frame_json(int dimension) {
	std::vector<int> permutation;
	std::vector<int> signs;
	for (int axis = 0; axis < dimension; ++axis) {
		permutation.push_back(axis);
		signs.push_back(1);
	}
	std::ostringstream out;
	out << "{\"permutation\":" << int_array_json(permutation)
		<< ",\"signs\":" << int_array_json(signs) << "}";
	return out.str();
}

std::string final_snapshot_json(const GameStateND &state) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"legal_moves\":" << legal_moves_json(state)
		<< ",\"level\":null"
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cell_count\":" << state.board.cells().size()
		<< ",\"locked_cell_digest\":\"" << locked_cell_digest(state.board) << "\""
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"piece_frame\":" << piece_frame_json(state.board.shape().dimension())
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

std::vector<PlainNDCase> plain_nd_cases() {
	return {
		{
			"gameplay_plain_3d_short",
			3,
			2002,
			{{5, 5, 5}},
			1,
			"native_3d",
			trace_shape_3d(),
			{{2, 2, 2}},
			{},
			{
				{"move_z", GameCommandKindND::MoveAxis, 2, 1},
				{"soft_drop", GameCommandKindND::SoftDrop, 0, 0},
				{"hard_drop", GameCommandKindND::HardDrop, 0, 0},
			},
			native_i_shape_3d(),
			{},
		},
		{
			"gameplay_plain_4d_short",
			4,
			2003,
			{{5, 5, 4, 4}},
			1,
			"standard_4d_5",
			trace_shape_4d(),
			{{2, 2, 1, 1}},
			{},
			{
				{"move_w", GameCommandKindND::MoveAxis, 3, 1},
				{"soft_drop", GameCommandKindND::SoftDrop, 0, 0},
				{"hard_drop", GameCommandKindND::HardDrop, 0, 0},
			},
			standard_stair_shape_4d(),
			{},
		},
		{
			"gameplay_plain_3d_rotation_short",
			3,
			2021,
			{{5, 5, 5}},
			1,
			"native_3d",
			trace_rotation_shape_3d(),
			{{2, 2, 2}},
			{},
			{
				{"rotate_xz_cw", GameCommandKindND::Rotate, 0, 1, 2},
			},
			std::nullopt,
			{"Stage 17 plain 3D rotation oracle trace."},
		},
		{
			"gameplay_plain_4d_rotation_short",
			4,
			2022,
			{{5, 5, 5, 5}},
			1,
			"standard_4d_5",
			trace_rotation_shape_4d(),
			{{2, 2, 2, 2}},
			{},
			{
				{"rotate_xw_cw", GameCommandKindND::Rotate, 0, 1, 3},
			},
			std::nullopt,
			{"Stage 17 plain 4D rotation oracle trace."},
		},
		{
			"gameplay_plain_3d_plane_clear_short",
			3,
			2023,
			{{2, 3, 2}},
			1,
			"native_3d",
			trace_single_shape_3d(),
			{{0, 2, 0}},
			{
				{{{1, 2, 0}}, 1},
				{{{0, 2, 1}}, 1},
				{{{1, 2, 1}}, 1},
				{{{1, 1, 1}}, 2},
			},
			{
				{"lock_plane_clear", GameCommandKindND::LockCurrentPiece, 0, 0},
			},
			std::nullopt,
			{"Stage 17 plain 3D single-plane clear oracle trace."},
		},
		{
			"gameplay_plain_4d_plane_clear_short",
			4,
			2024,
			{{2, 3, 1, 2}},
			1,
			"embedded_2d",
			trace_single_shape_4d(),
			{{0, 2, 0, 0}},
			{
				{{{1, 2, 0, 0}}, 1},
				{{{0, 2, 0, 1}}, 1},
				{{{1, 2, 0, 1}}, 1},
				{{{1, 1, 0, 1}}, 2},
			},
			{
				{"lock_hyperplane_clear", GameCommandKindND::LockCurrentPiece, 0, 0},
			},
			std::nullopt,
			{"Stage 17 plain 4D single-hyperplane clear oracle trace."},
		},
	};
}

const PlainNDCase *find_case(const std::string &case_id) {
	static const std::vector<PlainNDCase> cases = plain_nd_cases();
	for (const PlainNDCase &trace_case : cases) {
		if (trace_case.case_id == case_id) {
			return &trace_case;
		}
	}
	return nullptr;
}

GameStateND make_state(const PlainNDCase &trace_case) {
	GameStateND state(trace_case.board_shape, trace_case.gravity_axis);
	state.active_piece = ActivePieceND::from_shape(trace_case.active_shape, trace_case.active_pos);
	state.post_lock_spawn_shape = trace_case.post_lock_spawn_shape;
	for (const CellND &cell : trace_case.initial_locked_cells) {
		state.board.set_cell(cell.coord, cell.value);
	}
	return state;
}

std::string export_case_trace_json(const PlainNDCase &trace_case) {
	GameStateND state = make_state(trace_case);
	const GameStateND initial_state = state;
	std::vector<std::string> frames;
	frames.reserve(trace_case.commands.size());
	for (std::size_t index = 0; index < trace_case.commands.size(); ++index) {
		CommandResultND result = GameStepperND::apply(state, trace_case.commands[index]);
		const std::string frame_without_hash = frame_payload_json(
			static_cast<int>(index),
			trace_case.commands[index],
			result,
			state
		);
		const std::string frame_hash = stable_hash(frame_without_hash);
		frames.push_back(frame_payload_json(
			static_cast<int>(index),
			trace_case.commands[index],
			result,
			state,
			&frame_hash
		));
	}
	const std::string final_snapshot = final_snapshot_json(state);
	const std::string final_state_hash = stable_hash(
		final_hash_input_json(trace_case.case_id, final_snapshot, frames)
	);

	std::ostringstream out;
	out << "{\"case_id\":\"" << trace_case.case_id << "\""
		<< ",\"commands\":" << commands_json(trace_case.commands)
		<< ",\"dimension\":" << trace_case.dimension
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
		<< ",\"initial\":" << initial_json(trace_case, initial_state)
		<< ",\"seed\":" << trace_case.seed
		<< ",\"topology_id\":\"plain\""
		<< ",\"trace_type\":\"gameplay\""
		<< ",\"trace_version\":1"
		<< "}";
	return out.str();
}

} // namespace

std::vector<std::string> list_plain_nd_parity_cases() {
	std::vector<std::string> case_ids;
	for (const PlainNDCase &trace_case : plain_nd_cases()) {
		case_ids.push_back(trace_case.case_id);
	}
	return case_ids;
}

std::string export_plain_nd_trace_json(const std::string &case_id) {
	const PlainNDCase *trace_case = find_case(case_id);
	if (trace_case == nullptr) {
		return "{\"error\":\"unsupported plain ND parity case\",\"case_id\":\"" + case_id + "\"}";
	}
	return export_case_trace_json(*trace_case);
}

bool run_builtin_plain_nd_smoke_case() {
	for (const std::string &case_id : list_plain_nd_parity_cases()) {
		if (!get_plain_nd_required_field_parity(case_id)) {
			return false;
		}
	}
	return true;
}

std::string get_plain_nd_parity_status() {
	if (!run_builtin_plain_nd_smoke_case()) {
		return "plain_nd parity smoke failed";
	}
	return "plain_nd Stage 19 3D/4D movement, rotation, and clear/scoring traces export required fields and state_hash";
}

bool get_plain_nd_required_field_parity(const std::string &case_id) {
	if (find_case(case_id) == nullptr) {
		return false;
	}
	const std::string trace = export_plain_nd_trace_json(case_id);
	return trace.find("\"case_id\":\"" + case_id + "\"") != std::string::npos
		&& trace.find("\"trace_type\":\"gameplay\"") != std::string::npos
		&& trace.find("\"state_hash\"") != std::string::npos;
}

} // namespace tet4d::core
