#include "tet4d_core/plain_nd_session.hpp"

#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <utility>

namespace tet4d::core {
namespace {

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

std::string coords_json(const std::vector<CoordND> &coords) {
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

std::string render_cells_json(const std::vector<CoordND> &coords, int color_id, bool locked) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < coords.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << "{\"color_id\":" << color_id
			<< ",\"label\":\"" << (locked ? "Locked" : "Active") << "\""
			<< ",\"locked\":" << bool_json(locked)
			<< ",\"position\":" << coord_json(coords[index]) << "}";
	}
	out << "]";
	return out.str();
}

std::string render_locked_cells_json(const BoardND &board) {
	std::ostringstream out;
	out << "[";
	std::size_t index = 0;
	for (const auto &[coord, value] : board.cells()) {
		if (index != 0) {
			out << ",";
		}
		out << "{\"color_id\":" << value
			<< ",\"label\":\"Locked\""
			<< ",\"locked\":true"
			<< ",\"position\":" << coord_json(coord) << "}";
		++index;
	}
	out << "]";
	return out.str();
}

std::string board_shape_json(const BoardShapeND &shape) {
	return int_array_json(shape.dims);
}

std::string rotation_plane_name(const std::optional<ActivePieceND> &piece) {
	if (!piece.has_value() || !piece->last_rotation_plane.has_value() || piece->last_rotation_plane->size() != 2) {
		return "none";
	}
	const int axis_a = (*piece->last_rotation_plane)[0];
	const int axis_b = (*piece->last_rotation_plane)[1];
	if (axis_a == 0 && axis_b == 1) {
		return "XY";
	}
	if (axis_a == 0 && axis_b == 2) {
		return "XZ";
	}
	if (axis_a == 1 && axis_b == 2) {
		return "YZ";
	}
	if (axis_a == 0 && axis_b == 3) {
		return "XW";
	}
	if (axis_a == 1 && axis_b == 3) {
		return "YW";
	}
	if (axis_a == 2 && axis_b == 3) {
		return "ZW";
	}
	std::ostringstream out;
	out << axis_a << ":" << axis_b;
	return out.str();
}

std::string live_mode_label(int dimension) {
	return dimension == 4 ? "Live 4D" : "Live 3D";
}

std::string live_trace_type(int dimension) {
	return dimension == 4 ? "live_4d" : "live_3d";
}

std::string live_case_id(int dimension) {
	return dimension == 4 ? "live_plain_4d" : "live_plain_3d";
}

int active_w_index(const std::optional<ActivePieceND> &piece) {
	if (!piece.has_value() || piece->pos.values.size() <= 3) {
		return 0;
	}
	return piece->pos.values[3];
}

PieceShapeND live_o_shape_3d() {
	return {"O3", {{{0, 0, 0}}, {{1, 0, 0}}, {{0, 1, 0}}, {{1, 1, 0}}}, 2};
}

PieceShapeND live_l_shape_3d() {
	return {"L3", {{{-1, 0, 0}}, {{0, 0, 0}}, {{1, 0, 0}}, {{1, 1, 0}}}, 3};
}

PieceShapeND live_t_shape_3d() {
	return {"T3", {{{-1, 0, 0}}, {{0, 0, 0}}, {{1, 0, 0}}, {{0, 1, 0}}}, 4};
}

PieceShapeND live_s_shape_3d() {
	return {"S3", {{{0, 0, 0}}, {{1, 0, 0}}, {{-1, 1, 0}}, {{0, 1, 0}}}, 5};
}

PieceShapeND live_j_shape_3d() {
	return {"J3D", {{{0, 0, 0}}, {{1, 0, 0}}, {{0, 1, 0}}, {{0, 0, 1}}}, 6};
}

PieceShapeND live_screw_shape_3d() {
	return {"SCREW3", {{{0, 0, 0}}, {{1, 0, 0}}, {{1, 1, 0}}, {{1, 1, 1}}}, 7};
}

std::vector<PieceShapeND> live_piece_sequence_for_dimension(int dimension) {
	if (dimension == 4) {
		return {
			trace_shape_4d(),
			standard_stair_shape_4d(),
			trace_rotation_shape_4d(),
			trace_single_shape_4d(),
			trace_spawn_blocked_shape_4d(),
		};
	}
	if (dimension == 3) {
		return {
			native_i_shape_3d(),
			live_o_shape_3d(),
			live_l_shape_3d(),
			live_t_shape_3d(),
			live_s_shape_3d(),
			live_j_shape_3d(),
			live_screw_shape_3d(),
		};
	}
	return {};
}

BoardShapeND live_board_shape_for_dimension(int dimension) {
	if (dimension == 4) {
		return {{5, 10, 4, 4}};
	}
	if (dimension == 3) {
		return {{6, 10, 6}};
	}
	return {{6, 10, 6}};
}

std::string hash_payload_json(
		const GameStateND &state,
		const BoardShapeND &shape,
		std::size_t next_piece_index) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":" << board_shape_json(shape)
		<< ",\"dimension\":" << shape.dimension()
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"game_over_reason\":\"" << state.game_over_reason << "\""
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"next_piece_index\":" << next_piece_index
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

} // namespace

PlainNDSession::PlainNDSession(int dimension) :
		PlainNDSession(dimension, live_board_shape_for_dimension(dimension)) {
}

PlainNDSession::PlainNDSession(int dimension, BoardShapeND board_shape) :
		dimension_(dimension),
		board_shape_(is_supported_live_nd_board_shape(dimension, board_shape) ? std::move(board_shape) : live_board_shape_for_dimension(dimension)),
		state_(board_shape_, 1),
		piece_sequence_(live_piece_sequence_for_dimension(dimension)) {
	reset();
}

bool PlainNDSession::configure(const BoardShapeND &board_shape) {
	if (!is_supported_live_nd_board_shape(dimension_, board_shape)) {
		return false;
	}
	board_shape_ = board_shape;
	reset();
	return true;
}

void PlainNDSession::reset() {
	state_ = GameStateND(board_shape_, 1);
	piece_sequence_ = live_piece_sequence_for_dimension(dimension_);
	next_piece_index_ = 0;
	spawn_next_piece();
	last_command_ = "reset";
	last_command_status_ = "reset";
	command_count_ = 0;
}

std::string PlainNDSession::apply_command(const std::string &command) {
	if (command == "reset") {
		reset();
		return command_status(command);
	}
	if (state_.game_over) {
		last_command_ = "rejected:" + command;
		last_command_status_ = "rejected";
		return command_status(command);
	}

	bool accepted = true;
	if (command == "move_x_neg") {
		accepted = state_.try_move_axis(0, -1);
	} else if (command == "move_x_pos") {
		accepted = state_.try_move_axis(0, 1);
	} else if (command == "move_z_neg") {
		accepted = state_.try_move_axis(2, -1);
	} else if (command == "move_z_pos") {
		accepted = state_.try_move_axis(2, 1);
	} else if (command == "move_w_neg") {
		accepted = state_.try_move_axis(3, -1);
	} else if (command == "move_w_pos") {
		accepted = state_.try_move_axis(3, 1);
	} else if (command == "rotate_xy_neg") {
		accepted = state_.try_rotate(0, 1, -1);
	} else if (command == "rotate_xy_pos") {
		accepted = state_.try_rotate(0, 1, 1);
	} else if (command == "rotate_xz_neg") {
		accepted = state_.try_rotate(0, 2, -1);
	} else if (command == "rotate_xz_pos") {
		accepted = state_.try_rotate(0, 2, 1);
	} else if (command == "rotate_yz_neg") {
		accepted = state_.try_rotate(1, 2, -1);
	} else if (command == "rotate_yz_pos") {
		accepted = state_.try_rotate(1, 2, 1);
	} else if (command == "rotate_xw_neg") {
		accepted = state_.try_rotate(0, 3, -1);
	} else if (command == "rotate_xw_pos") {
		accepted = state_.try_rotate(0, 3, 1);
	} else if (command == "rotate_yw_neg") {
		accepted = state_.try_rotate(1, 3, -1);
	} else if (command == "rotate_yw_pos") {
		accepted = state_.try_rotate(1, 3, 1);
	} else if (command == "rotate_zw_neg") {
		accepted = state_.try_rotate(2, 3, -1);
	} else if (command == "rotate_zw_pos") {
		accepted = state_.try_rotate(2, 3, 1);
	} else if (command == "soft_drop") {
		accepted = state_.try_soft_drop();
	} else if (command == "hard_drop") {
		state_.post_lock_spawn_shape = draw_next_piece_shape();
		GameStepperND::apply(state_, {"hard_drop", GameCommandKindND::HardDrop, 0, 0});
		accepted = true;
	} else if (command == "tick") {
		tick();
		return command_status(command);
	} else {
		last_command_ = "unsupported:" + command;
		last_command_status_ = "unsupported";
		return command_status(command);
	}

	last_command_ = command;
	last_command_status_ = accepted ? "accepted" : "rejected";
	++command_count_;
	return command_status(command);
}

std::string PlainNDSession::tick() {
	if (!state_.game_over) {
		const bool moved = state_.try_soft_drop();
		if (!moved) {
			state_.post_lock_spawn_shape = draw_next_piece_shape();
			state_.lock_current_piece();
			if (!state_.game_over && state_.post_lock_spawn_shape.has_value()) {
				state_.spawn_piece(*state_.post_lock_spawn_shape);
			}
		}
	}
	last_command_ = "tick";
	last_command_status_ = state_.game_over ? "game_over" : "accepted";
	++command_count_;
	return command_status("tick");
}

std::string PlainNDSession::snapshot_json() const {
	const std::string hash = state_hash();
	const std::string active_cells = render_cells_json(
		state_.active_cells(),
		state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0,
		false
	);
	const std::string locked_cells = render_locked_cells_json(state_.board);
	const int entity_count = static_cast<int>(state_.active_cells().size() + state_.board.cells().size());
	const std::string rotation_plane = rotation_plane_name(state_.active_piece);
	const int last_rotation_steps = state_.active_piece.has_value() ? state_.active_piece->last_rotation_steps : 0;
	const int w_slice_count = dimension_ >= 4 && board_shape_.dims.size() > 3 ? board_shape_.dims[3] : 1;
	const int active_w = active_w_index(state_.active_piece);
	std::ostringstream out;
	out << "{\"active_cells\":" << active_cells
		<< ",\"board_shape\":" << board_shape_json(board_shape_)
		<< ",\"case_id\":\"" << live_case_id(dimension_) << "\""
		<< ",\"active_w\":" << active_w
		<< ",\"current_piece\":\"" << current_piece_name() << "\""
		<< ",\"current_piece_color_id\":" << (state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0)
		<< ",\"diagnostics_lines\":["
		<< "\"score: " << state_.score << "\","
		<< "\"lines: " << state_.lines << "\","
		<< "\"game_over: " << bool_json(state_.game_over) << "\","
		<< "\"game_over_reason: " << state_.game_over_reason << "\","
		<< "\"paused: false\","
		<< "\"current_piece: " << current_piece_name() << "\","
		<< "\"next_piece: " << next_piece_name() << "\","
		<< "\"last_rotation_plane: " << rotation_plane << "\","
		<< "\"last_rotation_steps: " << last_rotation_steps << "\","
		<< "\"w_slices: " << w_slice_count << "\","
		<< "\"active_w: " << active_w << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"last_command_status: " << last_command_status_ << "\","
		<< "\"locked_count: " << state_.board.cells().size() << "\""
		<< "]"
		<< ",\"dimension\":" << dimension_
		<< ",\"energy_lines\":[]"
		<< ",\"entity_count\":" << entity_count
		<< ",\"entity_count_matches_metadata\":true"
		<< ",\"event_lines\":[]"
		<< ",\"event_markers\":[]"
		<< ",\"frame_count\":" << (command_count_ + 1)
		<< ",\"frame_count_matches_metadata\":true"
		<< ",\"frame_index\":" << command_count_
		<< ",\"game_over\":" << bool_json(state_.game_over)
		<< ",\"game_over_reason\":\"" << state_.game_over_reason << "\""
		<< ",\"last_command\":\"" << last_command_ << "\""
		<< ",\"last_command_status\":\"" << last_command_status_ << "\""
		<< ",\"last_rotation_plane\":\"" << rotation_plane << "\""
		<< ",\"last_rotation_steps\":" << last_rotation_steps
		<< ",\"lines\":" << state_.lines
		<< ",\"locked_cells\":" << locked_cells
		<< ",\"metadata_lines\":["
		<< "\"mode: " << live_mode_label(dimension_) << "\","
		<< "\"authority: C++ GDExtension\","
		<< "\"current_piece: " << current_piece_name() << "\","
		<< "\"next_piece: " << next_piece_name() << "\","
		<< "\"last_rotation_plane: " << rotation_plane << "\","
		<< "\"last_rotation_steps: " << last_rotation_steps << "\","
		<< "\"w_slices: " << w_slice_count << "\","
		<< "\"active_w: " << active_w << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"state_hash: " << hash << "\""
		<< "]"
		<< ",\"next_piece\":\"" << next_piece_name() << "\""
		<< ",\"particles\":[]"
		<< ",\"paused\":false"
		<< ",\"probe_markers\":[]"
		<< ",\"score\":" << state_.score
		<< ",\"state_hash\":\"" << hash << "\""
		<< ",\"trace_name\":\"" << live_case_id(dimension_) << "\""
		<< ",\"trace_type\":\"" << live_trace_type(dimension_) << "\""
		<< ",\"w_slice_count\":" << w_slice_count
		<< "}";
	return out.str();
}

std::string PlainNDSession::status() const {
	const int w_slice_count = dimension_ >= 4 && board_shape_.dims.size() > 3 ? board_shape_.dims[3] : 1;
	std::ostringstream out;
	out << live_case_id(dimension_) << " score=" << state_.score
		<< " lines=" << state_.lines
		<< " current_piece=" << current_piece_name()
		<< " next_piece=" << next_piece_name()
		<< " last_rotation_plane=" << rotation_plane_name(state_.active_piece)
		<< " active_w=" << active_w_index(state_.active_piece)
		<< " w_slices=" << w_slice_count
		<< " game_over=" << bool_json(state_.game_over)
		<< " game_over_reason=" << state_.game_over_reason
		<< " paused=false"
		<< " last_command=" << last_command_
		<< " last_command_status=" << last_command_status_;
	return out.str();
}

std::string PlainNDSession::state_hash() const {
	return sha256_hex(hash_payload_json(state_, board_shape_, next_piece_index_));
}

PieceShapeND PlainNDSession::draw_next_piece_shape() {
	if (piece_sequence_.empty()) {
		return trace_shape_3d();
	}
	const PieceShapeND shape = piece_sequence_[next_piece_index_ % piece_sequence_.size()];
	++next_piece_index_;
	return shape;
}

void PlainNDSession::spawn_next_piece() {
	state_.spawn_piece(draw_next_piece_shape());
}

std::string PlainNDSession::current_piece_name() const {
	if (!state_.active_piece.has_value()) {
		return "none";
	}
	return state_.active_piece->shape.name;
}

std::string PlainNDSession::next_piece_name() const {
	if (piece_sequence_.empty()) {
		return "none";
	}
	return piece_sequence_[next_piece_index_ % piece_sequence_.size()].name;
}

std::string PlainNDSession::command_status(const std::string &command) const {
	std::ostringstream out;
	out << "command=" << command << " " << status();
	return out.str();
}

bool is_supported_live_nd_board_shape(int dimension, const BoardShapeND &board_shape) {
	if (!board_shape.is_valid() || board_shape.dimension() != dimension) {
		return false;
	}
	if (dimension == 3) {
		return board_shape.dims[0] >= 4 && board_shape.dims[0] <= 10 &&
				board_shape.dims[1] >= 6 && board_shape.dims[1] <= 24 &&
				board_shape.dims[2] >= 2 && board_shape.dims[2] <= 10;
	}
	if (dimension == 4) {
		return board_shape.dims[0] >= 4 && board_shape.dims[0] <= 12 &&
				board_shape.dims[1] >= 6 && board_shape.dims[1] <= 24 &&
				board_shape.dims[2] >= 2 && board_shape.dims[2] <= 8 &&
				board_shape.dims[3] >= 1 && board_shape.dims[3] <= 12;
	}
	return false;
}

} // namespace tet4d::core
