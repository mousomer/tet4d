#pragma once

#include "tet4d_core/plain_game_setup.hpp"
#include "tet4d_core/plain_nd.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

class PlainNDSession {
public:
	explicit PlainNDSession(int dimension);
	// The only public parameterized construction path. Returns nullopt when the
	// board fails the shared board-extent contract; it never substitutes a
	// canonical board for an invalid request.
	static std::optional<PlainNDSession> create_validated(int dimension, BoardShapeND board_shape);

	bool configure(const BoardShapeND &board_shape);
	bool configure(const PlainGameSetup &setup);
	void reset();
	std::string apply_command(const std::string &command);
	std::string tick();
	std::string snapshot_json() const;
	std::string status() const;
	std::string state_hash() const;
	// Observational queue query. The returned production shape is the next real
	// draw and querying never mutates the bag or RNG, including at refill.
	PieceShapeND peek_next_piece_shape() const;
	// Exact read-only destination used by the next hard drop, or nullopt when
	// the session is terminal or has no active piece.
	std::optional<ActivePieceND> hard_drop_destination() const;
	// Borrowed setup identifier; valid until the session is destroyed.
	const std::string &piece_set_id() const;

private:
	// Internal precondition: dimensions have already passed create_validated or
	// are the generated canonical default used by the dimension constructor.
	PlainNDSession(int dimension, BoardShapeND board_shape);

	int dimension_ = 3;
	BoardShapeND board_shape_;
	PlainGameSetup setup_;
	PythonRandom rng_;
	GameStateND state_;
	std::vector<PieceShapeND> piece_sequence_;
	std::vector<PieceShapeND> piece_bag_;
	std::string last_command_;
	std::string last_command_status_;
	int command_count_ = 0;
	std::size_t next_piece_index_ = 0;

	void refill_piece_bag();
	PieceShapeND draw_next_piece_shape();
	void spawn_next_piece();
	std::string current_piece_name() const;
	std::string next_piece_name() const;
	std::string command_status(const std::string &command) const;
};

bool is_supported_live_nd_board_shape(int dimension, const BoardShapeND &board_shape);
bool is_supported_live_nd_piece_set(int dimension, const std::string &piece_set_id);

} // namespace tet4d::core
