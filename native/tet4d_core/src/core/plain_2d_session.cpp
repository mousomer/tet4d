#include "tet4d_core/plain_2d_session.hpp"

#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <utility>
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
		int width,
		int height,
		const PlainGameSetup &setup,
		const std::vector<PieceShape2D> &piece_bag,
		std::size_t next_piece_index,
		std::size_t rng_words_consumed) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":[" << width << "," << height << "]"
		<< ",\"dimension\":2"
		<< ",\"effective_seed\":" << setup.effective_seed
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"game_over_reason\":\"" << state.game_over_reason << "\""
		<< ",\"initial_speed_level\":" << setup.initial_speed_level
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"next_piece_index\":" << next_piece_index
		<< ",\"piece_bag\":[";
	for (std::size_t index = 0; index < piece_bag.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << "\"" << piece_bag[index].name << "\"";
	}
	out << "]"
		<< ",\"piece_set_id\":\"" << setup.piece_set_id << "\""
		<< ",\"random_mode\":\"" << setup.random_mode << "\""
		<< ",\"rng_words_consumed\":" << rng_words_consumed
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

std::string legacy_hash_payload_json(
		const GameState2D &state,
		int width,
		int height,
		std::size_t next_piece_index) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":[" << width << "," << height << "]"
		<< ",\"dimension\":2"
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"game_over_reason\":\"" << state.game_over_reason << "\""
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"next_piece_index\":" << next_piece_index
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

} // namespace

Plain2DSession::Plain2DSession() : Plain2DSession(6, 6) {
}

Plain2DSession::Plain2DSession(int width, int height) :
		width_(is_supported_live_2d_board_shape(width, height) ? width : 6),
		height_(is_supported_live_2d_board_shape(width, height) ? height : 6),
		setup_({
			PLAIN_SETUP_SCHEMA_VERSION,
			"live_2d",
			"standard",
			{width_, height_},
			"classic",
			RANDOM_MODE_FIXED_SEED,
			1337,
			1337,
			1,
			false,
		}),
		rng_(static_cast<std::uint32_t>(setup_.effective_seed)),
		state_(width_, height_) {
	reset();
}

bool Plain2DSession::configure(int width, int height) {
	if (!is_supported_live_2d_board_shape(width, height)) {
		return false;
	}
	width_ = width;
	height_ = height;
	setup_.board_shape = {width, height};
	reset();
	return true;
}

bool Plain2DSession::configure(const PlainGameSetup &requested_setup) {
	if (requested_setup.schema_version != PLAIN_SETUP_SCHEMA_VERSION ||
			requested_setup.mode != "live_2d" ||
			requested_setup.board_shape.size() != 2 ||
			requested_setup.piece_set_id != "classic" ||
			!is_valid_plain_random_mode(requested_setup.random_mode) ||
			!is_valid_plain_speed(requested_setup.initial_speed_level)) {
		return false;
	}
	const int width = requested_setup.board_shape[0];
	const int height = requested_setup.board_shape[1];
	if (!is_supported_live_2d_board_shape(width, height)) {
		return false;
	}
	if (requested_setup.random_mode == RANDOM_MODE_FIXED_SEED &&
			(!requested_setup.configured_seed.has_value() ||
			 !is_valid_plain_seed(*requested_setup.configured_seed))) {
		return false;
	}
	PlainGameSetup validated = requested_setup;
	validated.shuffle_bag = true;
	if (validated.random_mode == RANDOM_MODE_TRUE_RANDOM) {
		validated.configured_seed.reset();
		validated.effective_seed = generate_effective_seed();
	} else {
		validated.effective_seed = *validated.configured_seed;
	}
	width_ = width;
	height_ = height;
	setup_ = std::move(validated);
	reset();
	return true;
}

void Plain2DSession::reset() {
	state_ = GameState2D(width_, height_);
	next_piece_index_ = 0;
	piece_bag_.clear();
	rng_.seed(static_cast<std::uint32_t>(setup_.effective_seed));
	spawn_next_piece();
	last_command_ = "reset";
	last_command_status_ = "reset";
	command_count_ = 0;
}

std::string Plain2DSession::apply_command(const std::string &command) {
	if (command == "reset") {
		reset();
		return command_status(command);
	}
	if (state_.game_over) {
		last_command_ = "rejected:" + command;
		last_command_status_ = "rejected";
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
		last_command_status_ = "unsupported";
		return command_status(command);
	}

	last_command_ = command;
	last_command_status_ = "accepted";
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
	last_command_status_ = state_.game_over ? "game_over" : "accepted";
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
		<< ",\"board_shape\":[" << width_ << "," << height_ << "]"
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
		<< "\"next_piece: " << next_piece_name() << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"last_command_status: " << last_command_status_ << "\","
		<< "\"piece_set: " << setup_.piece_set_id << "\","
		<< "\"random_mode: " << setup_.random_mode << "\","
		<< "\"effective_seed: " << setup_.effective_seed << "\","
		<< "\"initial_speed_level: " << setup_.initial_speed_level << "\","
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
		<< "\"next_piece: " << next_piece_name() << "\","
		<< "\"last_command: " << last_command_ << "\","
		<< "\"state_hash: " << hash << "\""
		<< "]"
		<< ",\"particles\":[]"
		<< ",\"probe_markers\":[]"
		<< ",\"game_over\":" << bool_json(state_.game_over)
		<< ",\"game_over_reason\":\"" << state_.game_over_reason << "\""
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
		<< ",\"lines\":" << state_.lines
		<< ",\"next_piece\":\"" << next_piece_name() << "\""
		<< ",\"piece_set_id\":\"" << setup_.piece_set_id << "\""
		<< ",\"paused\":false"
		<< ",\"random_mode\":\"" << setup_.random_mode << "\""
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
		<< " next_piece=" << next_piece_name()
		<< " piece_set=" << setup_.piece_set_id
		<< " random_mode=" << setup_.random_mode
		<< " effective_seed=" << setup_.effective_seed
		<< " initial_speed_level=" << setup_.initial_speed_level
		<< " game_over=" << bool_json(state_.game_over)
		<< " game_over_reason=" << state_.game_over_reason
		<< " paused=false"
		<< " last_command=" << last_command_
		<< " last_command_status=" << last_command_status_;
	return out.str();
}

std::string Plain2DSession::state_hash() const {
	if (!setup_.shuffle_bag) {
		return sha256_hex(legacy_hash_payload_json(state_, width_, height_, next_piece_index_));
	}
	return sha256_hex(hash_payload_json(
		state_,
		width_,
		height_,
		setup_,
		piece_bag_,
		next_piece_index_,
		rng_.words_consumed()
	));
}

void Plain2DSession::refill_piece_bag() {
	piece_bag_ = live_piece_sequence();
	rng_.shuffle(piece_bag_);
}

PieceShape2D Plain2DSession::draw_next_piece_shape() {
	if (setup_.shuffle_bag) {
		if (piece_bag_.empty()) {
			refill_piece_bag();
		}
		PieceShape2D shape = piece_bag_.back();
		piece_bag_.pop_back();
		return shape;
	}
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

std::string Plain2DSession::next_piece_name() const {
	if (setup_.shuffle_bag) {
		return piece_bag_.empty() ? "pending_bag" : piece_bag_.back().name;
	}
	const std::vector<PieceShape2D> &sequence = live_piece_sequence();
	return sequence[next_piece_index_ % sequence.size()].name;
}

std::string Plain2DSession::command_status(const std::string &command) const {
	std::ostringstream out;
	out << "command=" << command << " " << status();
	return out.str();
}

bool is_supported_live_2d_board_shape(int width, int height) {
	constexpr int MIN_WIDTH = 4;
	constexpr int MIN_HEIGHT = 6;
	constexpr int MAX_WIDTH = 16;
	constexpr int MAX_HEIGHT = 30;
	return width >= MIN_WIDTH && width <= MAX_WIDTH && height >= MIN_HEIGHT && height <= MAX_HEIGHT;
}

} // namespace tet4d::core
