#include "tet4d_core/plain_2d_session.hpp"

#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <vector>

namespace tet4d::core {
namespace {

std::string bool_json(bool value) {
	return value ? "true" : "false";
}

PieceShape2D classic_o_shape_2d() {
	return {"O", {{0, 0}, {1, 0}, {0, 1}, {1, 1}}, 2};
}

PieceShape2D classic_t_shape_2d() {
	return {"T", {{-1, 0}, {0, 0}, {1, 0}, {0, 1}}, 3};
}

PieceShape2D classic_z_shape_2d() {
	return {"Z", {{-1, 0}, {0, 0}, {0, 1}, {1, 1}}, 5};
}

PieceShape2D classic_j_shape_2d() {
	return {"J", {{-1, 0}, {-1, 1}, {0, 0}, {1, 0}}, 6};
}

PieceShape2D classic_l_shape_2d() {
	return {"L", {{-1, 0}, {0, 0}, {1, 0}, {1, 1}}, 7};
}

const std::vector<PieceShape2D> &live_piece_sequence() {
	static const std::vector<PieceShape2D> sequence = {
		classic_i_shape_2d(),
		classic_o_shape_2d(),
		classic_t_shape_2d(),
		classic_s_shape_2d(),
		classic_z_shape_2d(),
		classic_j_shape_2d(),
		classic_l_shape_2d(),
	};
	return sequence;
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

std::string render_cells_json(const std::vector<Coord2D> &coords, int color_id, bool locked) {
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

std::string render_locked_cells_json(const Board2D &board) {
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

std::string hash_payload_json(
		const GameState2D &state,
		std::size_t next_piece_index) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"game_over_reason\":\"" << state.game_over_reason << "\""
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"next_piece_index\":" << next_piece_index
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

} // namespace

Plain2DSession::Plain2DSession() : state_(6, 6) {
	reset();
}

void Plain2DSession::reset() {
	state_ = GameState2D(6, 6);
	next_piece_index_ = 0;
	spawn_next_piece();
	last_command_ = "reset";
	command_count_ = 0;
}

std::string Plain2DSession::apply_command(const std::string &command) {
	if (command == "reset") {
		reset();
		return command_status(command);
	}
	if (state_.game_over) {
		last_command_ = "rejected:" + command;
		return command_status(command);
	}

	if (command == "move_left") {
		GameStepper2D::apply(state_, {"move_left", GameCommandKind2D::Move, -1, 0});
	} else if (command == "move_right") {
		GameStepper2D::apply(state_, {"move_right", GameCommandKind2D::Move, 1, 0});
	} else if (command == "rotate_cw") {
		GameStepper2D::apply(state_, {"rotate_cw", GameCommandKind2D::Rotate, 1, 0});
	} else if (command == "rotate_ccw") {
		GameStepper2D::apply(state_, {"rotate_ccw", GameCommandKind2D::Rotate, -1, 0});
	} else if (command == "soft_drop") {
		GameStepper2D::apply(state_, {"soft_drop", GameCommandKind2D::SoftDrop, 0, 1});
	} else if (command == "hard_drop") {
		state_.post_lock_spawn_shape = draw_next_piece_shape();
		GameStepper2D::apply(state_, {"hard_drop", GameCommandKind2D::HardDrop, 0, 0});
	} else if (command == "tick") {
		tick();
		return command_status(command);
	} else {
		last_command_ = "unsupported:" + command;
		return command_status(command);
	}

	last_command_ = command;
	++command_count_;
	return command_status(command);
}

std::string Plain2DSession::tick() {
	if (!state_.game_over) {
		const bool moved = state_.try_soft_drop();
		if (!moved) {
			state_.lock_current_piece();
			if (!state_.game_over) {
				spawn_next_piece();
			}
		}
	}
	last_command_ = "tick";
	++command_count_;
	return command_status("tick");
}

std::string Plain2DSession::snapshot_json() const {
	const std::string hash = state_hash();
	const std::string active_cells = render_cells_json(
		state_.active_cells(),
		state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0,
		false
	);
	const std::string locked_cells = render_locked_cells_json(state_.board);
	const int entity_count = static_cast<int>(state_.active_cells().size() + state_.board.cells().size());
	std::ostringstream out;
	out << "{\"active_cells\":" << active_cells
		<< ",\"board_shape\":[6,6]"
		<< ",\"case_id\":\"live_plain_2d\""
		<< ",\"current_piece\":\"" << current_piece_name() << "\""
		<< ",\"current_piece_color_id\":" << (state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0)
		<< ",\"diagnostics_lines\":["
		<< "\"score: " << state_.score << "\","
		<< "\"lines: " << state_.lines << "\","
		<< "\"game_over: " << bool_json(state_.game_over) << "\","
		<< "\"game_over_reason: " << state_.game_over_reason << "\","
		<< "\"paused: false\","
		<< "\"current_piece: " << current_piece_name() << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"locked_count: " << state_.board.cells().size() << "\""
		<< "]"
		<< ",\"dimension\":2"
		<< ",\"energy_lines\":[]"
		<< ",\"entity_count\":" << entity_count
		<< ",\"entity_count_matches_metadata\":true"
		<< ",\"event_lines\":[]"
		<< ",\"event_markers\":[]"
		<< ",\"frame_count\":" << (command_count_ + 1)
		<< ",\"frame_count_matches_metadata\":true"
		<< ",\"frame_index\":" << command_count_
		<< ",\"locked_cells\":" << locked_cells
		<< ",\"metadata_lines\":["
		<< "\"mode: Live 2D\","
		<< "\"authority: C++ GDExtension\","
		<< "\"current_piece: " << current_piece_name() << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"state_hash: " << hash << "\""
		<< "]"
		<< ",\"particles\":[]"
		<< ",\"probe_markers\":[]"
		<< ",\"game_over\":" << bool_json(state_.game_over)
		<< ",\"game_over_reason\":\"" << state_.game_over_reason << "\""
		<< ",\"last_command\":\"" << last_command_ << "\""
		<< ",\"lines\":" << state_.lines
		<< ",\"paused\":false"
		<< ",\"score\":" << state_.score
		<< ",\"state_hash\":\"" << hash << "\""
		<< ",\"trace_name\":\"live_plain_2d\""
		<< ",\"trace_type\":\"live_2d\""
		<< "}";
	return out.str();
}

std::string Plain2DSession::status() const {
	std::ostringstream out;
	out << "live_plain_2d score=" << state_.score
		<< " lines=" << state_.lines
		<< " current_piece=" << current_piece_name()
		<< " game_over=" << bool_json(state_.game_over)
		<< " game_over_reason=" << state_.game_over_reason
		<< " paused=false"
		<< " last_command=" << last_command_;
	return out.str();
}

std::string Plain2DSession::state_hash() const {
	return sha256_hex(hash_payload_json(state_, next_piece_index_));
}

PieceShape2D Plain2DSession::draw_next_piece_shape() {
	const std::vector<PieceShape2D> &sequence = live_piece_sequence();
	const PieceShape2D shape = sequence[next_piece_index_ % sequence.size()];
	++next_piece_index_;
	return shape;
}

void Plain2DSession::spawn_next_piece() {
	state_.spawn_piece(draw_next_piece_shape());
}

std::string Plain2DSession::current_piece_name() const {
	if (!state_.active_piece.has_value()) {
		return "none";
	}
	return state_.active_piece->shape.name;
}

std::string Plain2DSession::command_status(const std::string &command) const {
	std::ostringstream out;
	out << "command=" << command << " " << status();
	return out.str();
}

} // namespace tet4d::core
