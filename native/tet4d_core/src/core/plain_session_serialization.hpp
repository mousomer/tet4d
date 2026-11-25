#pragma once

#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/plain_game_setup.hpp"
#include "tet4d_core/plain_nd.hpp"

#include <sstream>

namespace tet4d::core::detail {

inline const char *bool_json(bool value) {
	return value ? "true" : "false";
}

inline std::string coord_json(const Coord2D &coord) {
	std::ostringstream out;
	out << "[" << coord.x << "," << coord.y << "]";
	return out.str();
}

inline std::string int_array_json(const std::vector<int> &items) {
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

inline std::string coord_json(const CoordND &coord) {
	return int_array_json(coord.values);
}

template <typename Coord>
std::string coords_json(const std::vector<Coord> &coords) {
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

inline std::string active_piece_json(const std::optional<ActivePiece2D> &piece) {
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

inline std::string active_piece_json(const std::optional<ActivePieceND> &piece) {
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

template <typename Piece>
std::string held_piece_json(const std::optional<Piece> &piece) {
	if (!piece.has_value()) {
		return "null";
	}
	std::ostringstream out;
	out << "{\"blocks\":" << coords_json(piece->blocks)
		<< ",\"color_id\":" << piece->color_id
		<< ",\"shape\":\"" << piece->name << "\"}";
	return out.str();
}

template <typename Board>
std::string locked_cells_json(const Board &board) {
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

template <typename Coord>
std::string render_cells_json(const std::vector<Coord> &coords, int color_id) {
	std::ostringstream out;
	out << "[";
	for (std::size_t index = 0; index < coords.size(); ++index) {
		if (index != 0) {
			out << ",";
		}
		out << "{\"color_id\":" << color_id
			<< ",\"label\":\"Active\""
			<< ",\"locked\":false"
			<< ",\"position\":" << coord_json(coords[index]) << "}";
	}
	out << "]";
	return out.str();
}

template <typename Board>
std::string render_locked_cells_json(const Board &board) {
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

// Field order and the placement of optional Hold data are part of the hash contract.
template <typename State, typename Piece>
std::string hash_payload_json(
		const State &state,
		const std::string &shape_json,
		int dimension,
		const PlainGameSetup &setup,
		const std::vector<Piece> &piece_bag,
		std::size_t next_piece_index,
		std::size_t rng_words_consumed,
		const std::optional<Piece> &held_piece,
		bool hold_available,
		bool include_hold) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":" << shape_json
		<< ",\"dimension\":" << dimension
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
	out << "]";
	if (include_hold) {
		out << ",\"held_piece\":" << held_piece_json(held_piece)
			<< ",\"hold_available\":" << bool_json(hold_available);
	}
	out
		<< ",\"piece_set_id\":\"" << setup.piece_set_id << "\""
		<< ",\"random_mode\":\"" << setup.random_mode << "\""
		<< ",\"rng_words_consumed\":" << rng_words_consumed
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

template <typename State, typename Piece>
std::string legacy_hash_payload_json(
		const State &state,
		const std::string &shape_json,
		int dimension,
		std::size_t next_piece_index,
		const std::optional<Piece> &held_piece,
		bool hold_available,
		bool include_hold) {
	std::ostringstream out;
	out << "{\"active_piece\":" << active_piece_json(state.active_piece)
		<< ",\"board_shape\":" << shape_json
		<< ",\"dimension\":" << dimension
		<< ",\"game_over\":" << bool_json(state.game_over)
		<< ",\"game_over_reason\":\"" << state.game_over_reason << "\"";
	if (include_hold) {
		out << ",\"held_piece\":" << held_piece_json(held_piece)
			<< ",\"hold_available\":" << bool_json(hold_available);
	}
	out
		<< ",\"lines\":" << state.lines
		<< ",\"locked_cells\":" << locked_cells_json(state.board)
		<< ",\"next_piece_index\":" << next_piece_index
		<< ",\"score\":" << state.score << "}";
	return out.str();
}

template <typename State, typename Piece, typename Extra>
std::string session_status(
		const std::string &case_id, const State &state, const PlainGameSetup &setup,
		const std::string &current, const std::string &next, const std::optional<Piece> &held,
		bool hold_available, const std::string &command, const std::string &command_result,
		Extra append_dimension_status) {
	std::ostringstream out;
	out << case_id << " score=" << state.score
		<< " lines=" << state.lines
		<< " current_piece=" << current
		<< " next_piece=" << next
		<< " held_piece=" << (held.has_value() ? held->name : "empty")
		<< " hold_available=" << bool_json(hold_available)
		<< " piece_set=" << setup.piece_set_id
		<< " random_mode=" << setup.random_mode
		<< " effective_seed=" << setup.effective_seed
		<< " initial_speed_level=" << setup.initial_speed_level;
	append_dimension_status(out);
	out << " game_over=" << bool_json(state.game_over)
		<< " game_over_reason=" << state.game_over_reason
		<< " paused=false"
		<< " last_command=" << command
		<< " last_command_status=" << command_result;
	return out.str();
}

} // namespace tet4d::core::detail
