#include "tet4d_core/plain_nd_session.hpp"

#include "plain_session_serialization.hpp"
#include "plain_session_setup.hpp"
#include "tet4d_core/plain_piece_catalog.hpp"
#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <utility>

namespace tet4d::core {
namespace {

using detail::bool_json;
using detail::CommandOutcome;
using detail::held_piece_json;
using detail::render_cells_json;
using detail::render_locked_cells_json;

std::string board_shape_json(const BoardShapeND &shape) {
	return detail::int_array_json(shape.dims);
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

} // namespace

PlainNDSession::PlainNDSession(int dimension) :
		PlainNDSession(
				dimension,
				BoardShapeND{canonical_live_board_shape(dimension == 4 ? "live_4d" : "live_3d")}) {
}

PlainNDSession::PlainNDSession(int dimension, BoardShapeND board_shape) :
		PlainSessionLifecycle({
			PLAIN_SETUP_SCHEMA_VERSION,
			dimension == 4 ? "live_4d" : "live_3d",
			"standard",
			board_shape.dims,
			dimension == 4 ? "standard_4d_5" : "native_3d",
			RANDOM_MODE_FIXED_SEED,
			1337,
			1337,
			1,
			false,
		}),
		dimension_(dimension),
		board_shape_(std::move(board_shape)),
		state_(board_shape_, 1),
		piece_sequence_(legacy_live_piece_sequence_for_dimension(dimension)) {
	reset();
}

std::optional<PlainNDSession> PlainNDSession::create_validated(
		int dimension,
		BoardShapeND board_shape) {
	if (!is_supported_live_nd_board_shape(dimension, board_shape)) {
		return std::nullopt;
	}
	return PlainNDSession(dimension, std::move(board_shape));
}

bool PlainNDSession::configure(const BoardShapeND &board_shape) {
	if (!is_supported_live_nd_board_shape(dimension_, board_shape)) {
		return false;
	}
	board_shape_ = board_shape;
	setup_.board_shape = board_shape.dims;
	reset();
	return true;
}

bool PlainNDSession::configure(const PlainGameSetup &requested_setup) {
	const std::string expected_mode = live_trace_type(dimension_);
	auto validated = detail::prepare_setup(requested_setup, expected_mode);
	if (!validated.has_value()) {
		return false;
	}
	board_shape_ = BoardShapeND{validated->board_shape};
	setup_ = std::move(*validated);
	reset();
	return true;
}

void PlainNDSession::reset() {
	state_ = GameStateND(board_shape_, 1);
	piece_sequence_ = setup_.shuffle_bag ?
			plain_piece_catalog_nd(dimension_, setup_.piece_set_id) :
			legacy_live_piece_sequence_for_dimension(dimension_);
	reset_lifecycle([this] { spawn_next_piece(); });
}

std::string PlainNDSession::apply_command(const std::string &command) {
	return route_command(*this, command, state_.game_over, [&] { return play_command(command); });
}

CommandOutcome PlainNDSession::play_command(const std::string &command) {
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
	} else if (command == "hold") {
		accepted = hold(state_, [this] { return draw_next_piece_shape(); });
	} else if (command == "hard_drop") {
		state_.post_lock_spawn_shape = draw_next_piece_shape();
		GameStepperND::apply(state_, {"hard_drop", GameCommandKindND::HardDrop, 0, 0});
		accepted = true;
		hold_available_ = !state_.game_over && state_.active_piece.has_value();
	} else {
		return CommandOutcome::Unsupported;
	}
	return accepted ? CommandOutcome::Accepted : CommandOutcome::Rejected;
}

std::string PlainNDSession::tick() {
	tick_lifecycle(state_, [this] {
		state_.post_lock_spawn_shape = draw_next_piece_shape();
		state_.lock_current_piece();
		if (!state_.game_over && state_.post_lock_spawn_shape.has_value()) {
			state_.spawn_piece(*state_.post_lock_spawn_shape);
		}
	});
	return command_status(*this, "tick");
}

std::string PlainNDSession::snapshot_json() const {
	const std::string hash = state_hash();
	const std::string active_cells = render_cells_json(
		state_.active_cells(),
		state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0
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
		<< "\"piece_set: " << setup_.piece_set_id << "\","
		<< "\"random_mode: " << setup_.random_mode << "\","
		<< "\"effective_seed: " << setup_.effective_seed << "\","
		<< "\"initial_speed_level: " << setup_.initial_speed_level << "\","
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
		<< ",\"held_piece\":" << held_piece_json(held_piece_)
		<< ",\"hold_available\":" << bool_json(hold_available())
		<< ",\"configured_seed\":";
	if (setup_.configured_seed.has_value()) {
		out << *setup_.configured_seed;
	} else {
		out << "null";
	}
	out << ",\"effective_seed\":" << setup_.effective_seed
		<< ",\"initial_speed_level\":" << setup_.initial_speed_level
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
		<< ",\"piece_set_id\":\"" << setup_.piece_set_id << "\""
		<< ",\"particles\":[]"
		<< ",\"paused\":false"
		<< ",\"probe_markers\":[]"
		<< ",\"random_mode\":\"" << setup_.random_mode << "\""
		<< ",\"score\":" << state_.score
		<< ",\"state_hash\":\"" << hash << "\""
		<< ",\"trace_name\":\"" << live_case_id(dimension_) << "\""
		<< ",\"trace_type\":\"" << live_trace_type(dimension_) << "\""
		<< ",\"w_slice_count\":" << w_slice_count
		<< "}";
	return out.str();
}

std::string PlainNDSession::status() const {
	return detail::session_status(live_case_id(dimension_), state_, setup_, current_piece_name(), next_piece_name(),
			held_piece_, hold_available(), last_command_, last_command_status_, [this](std::ostream &out) {
				const int w_slice_count = dimension_ >= 4 && board_shape_.dims.size() > 3 ? board_shape_.dims[3] : 1;
				out << " last_rotation_plane=" << rotation_plane_name(state_.active_piece)
					<< " active_w=" << active_w_index(state_.active_piece)
					<< " w_slices=" << w_slice_count;
			});
}

std::string PlainNDSession::state_hash() const {
	const bool include_hold = held_piece_.has_value() || !hold_available_;
	const std::string shape = board_shape_json(board_shape_);
	if (!setup_.shuffle_bag) {
		return sha256_hex(detail::legacy_hash_payload_json(
				state_, shape, board_shape_.dimension(), next_piece_index_, held_piece_, hold_available_, include_hold));
	}
	return sha256_hex(detail::hash_payload_json(
			state_, shape, board_shape_.dimension(), setup_, piece_bag_, next_piece_index_,
			rng_.words_consumed(), held_piece_, hold_available_, include_hold));
}

PieceShapeND PlainNDSession::peek_next_piece_shape() const {
	return peek_piece(piece_sequence_);
}

std::optional<PieceShapeND> PlainNDSession::held_piece_shape() const {
	return held_piece_;
}

bool PlainNDSession::hold_available() const {
	return can_hold(state_);
}

std::optional<ActivePieceND> PlainNDSession::hard_drop_destination() const {
	return state_.hard_drop_destination();
}

const std::string &PlainNDSession::piece_set_id() const {
	return setup_.piece_set_id;
}

PieceShapeND PlainNDSession::draw_next_piece_shape() {
	return piece_sequence_.empty() ? trace_shape_3d() : draw_piece(piece_sequence_);
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
	return next_name(piece_sequence_);
}

bool is_supported_live_nd_board_shape(int dimension, const BoardShapeND &board_shape) {
	const std::string mode = dimension == 3 ? "live_3d" : (dimension == 4 ? "live_4d" : "");
	return detail::has_valid_extent(mode, board_shape.dims, dimension == 4 ? "standard_4d_5" : "native_3d");
}

bool is_supported_live_nd_piece_set(int dimension, const std::string &piece_set_id) {
	return is_supported_live_piece_set(dimension, piece_set_id);
}

} // namespace tet4d::core
