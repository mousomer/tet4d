#include "tet4d_core/plain_2d_session.hpp"

#include "plain_session_serialization.hpp"
#include "plain_session_setup.hpp"
#include "tet4d_core/plain_piece_catalog.hpp"
#include "tet4d_core/sha256.hpp"

#include <sstream>
#include <utility>
#include <vector>

namespace tet4d::core {
namespace {

using detail::bool_json;
using detail::CommandOutcome;
using detail::held_piece_json;
using detail::render_cells_json;
using detail::render_locked_cells_json;

std::string board_shape_json(int width, int height) {
	return detail::coord_json(Coord2D{width, height});
}

const std::vector<PieceShape2D> &live_piece_sequence() {
	return plain_piece_catalog_2d("classic");
}

} // namespace

Plain2DSession::Plain2DSession() :
		Plain2DSession(canonical_live_board_shape("live_2d")[0], canonical_live_board_shape("live_2d")[1]) {
}

Plain2DSession::Plain2DSession(int width, int height) :
		PlainSessionLifecycle({
			PLAIN_SETUP_SCHEMA_VERSION,
			"live_2d",
			"standard",
			{width, height},
			"classic",
			RANDOM_MODE_FIXED_SEED,
			1337,
			1337,
			1,
			false,
		}),
		width_(width),
		height_(height),
		state_(width_, height_) {
	reset();
}

std::optional<Plain2DSession> Plain2DSession::create_validated(int width, int height) {
	if (!is_supported_live_2d_board_shape(width, height)) {
		return std::nullopt;
	}
	return Plain2DSession(width, height);
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
	if (requested_setup.board_shape.size() != 2 || requested_setup.piece_set_id != "classic") {
		return false;
	}
	auto validated = detail::prepare_setup(requested_setup, "live_2d");
	if (!validated.has_value()) {
		return false;
	}
	width_ = validated->board_shape[0];
	height_ = validated->board_shape[1];
	setup_ = std::move(*validated);
	reset();
	return true;
}

void Plain2DSession::reset() {
	state_ = GameState2D(width_, height_);
	reset_lifecycle([this] { spawn_next_piece(); });
}

std::string Plain2DSession::apply_command(const std::string &command) {
	return route_command(*this, command, state_.game_over, [&] { return play_command(command); });
}

CommandOutcome Plain2DSession::play_command(const std::string &command) {
	if (command == "move_left") {
		GameStepper2D::apply(state_, {"move_left", GameCommandKind2D::Move, -1, 0});
	} else if (command == "move_right") {
		GameStepper2D::apply(state_, {"move_right", GameCommandKind2D::Move, 1, 0});
	} else if (command == "rotate_cw") {
		GameStepper2D::apply(state_, {"rotate_cw", GameCommandKind2D::Rotate, 1, 0});
	} else if (command == "rotate_ccw") {
		GameStepper2D::apply(state_, {"rotate_ccw", GameCommandKind2D::Rotate, -1, 0});
	} else if (command == "soft_drop") {
		const CommandResult2D result = GameStepper2D::apply(state_, {"soft_drop", GameCommandKind2D::SoftDrop, 0, 1});
		return result.return_value.value_or(false) ? CommandOutcome::Accepted : CommandOutcome::Rejected;
	} else if (command == "hold") {
		return hold(state_, [this] { return draw_next_piece_shape(); }) ?
				CommandOutcome::Accepted : CommandOutcome::RejectedWithPrefix;
	} else if (command == "hard_drop") {
		state_.post_lock_spawn_shape = draw_next_piece_shape();
		GameStepper2D::apply(state_, {"hard_drop", GameCommandKind2D::HardDrop, 0, 0});
		hold_available_ = !state_.game_over && state_.active_piece.has_value();
	} else {
		return CommandOutcome::Unsupported;
	}
	return CommandOutcome::Accepted;
}

std::string Plain2DSession::tick() {
	tick_lifecycle(state_, [this] {
		state_.lock_current_piece();
		if (!state_.game_over) {
			spawn_next_piece();
		}
	});
	return command_status(*this, "tick");
}

std::string Plain2DSession::snapshot_json() const {
	const std::string hash = state_hash();
	const std::string active_cells = render_cells_json(
		state_.active_cells(),
		state_.active_piece.has_value() ? state_.active_piece->shape.color_id : 0
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
	return detail::session_status("live_plain_2d", state_, setup_, current_piece_name(), next_piece_name(),
			held_piece_, hold_available(), last_command_, last_command_status_, [](std::ostream &) {});
}

std::string Plain2DSession::state_hash() const {
	const bool include_hold = held_piece_.has_value() || !hold_available_;
	const std::string shape = board_shape_json(width_, height_);
	if (!setup_.shuffle_bag) {
		return sha256_hex(detail::legacy_hash_payload_json(
				state_, shape, 2, next_piece_index_, held_piece_, hold_available_, include_hold));
	}
	return sha256_hex(detail::hash_payload_json(
			state_, shape, 2, setup_, piece_bag_, next_piece_index_,
			rng_.words_consumed(), held_piece_, hold_available_, include_hold));
}

PieceShape2D Plain2DSession::peek_next_piece_shape() const {
	return peek_piece(live_piece_sequence());
}

std::optional<PieceShape2D> Plain2DSession::held_piece_shape() const {
	return held_piece_;
}

bool Plain2DSession::hold_available() const {
	return can_hold(state_);
}

std::optional<ActivePiece2D> Plain2DSession::hard_drop_destination() const {
	return state_.hard_drop_destination();
}

const std::string &Plain2DSession::piece_set_id() const {
	return setup_.piece_set_id;
}

PieceShape2D Plain2DSession::draw_next_piece_shape() {
	return draw_piece(live_piece_sequence());
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
	return next_name(live_piece_sequence());
}

bool is_supported_live_2d_board_shape(int width, int height) {
	return detail::has_valid_extent("live_2d", {width, height}, "classic");
}

} // namespace tet4d::core
