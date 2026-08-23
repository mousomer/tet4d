#pragma once

#include "tet4d_core/plain_2d.hpp"
#include "tet4d_core/plain_game_setup.hpp"

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

class Plain2DSession {
public:
	Plain2DSession();
	// The only public parameterized construction path. Returns nullopt when the
	// board fails the shared board-extent contract; it never substitutes a
	// canonical board for an invalid request.
	static std::optional<Plain2DSession> create_validated(int width, int height);

	bool configure(int width, int height);
	bool configure(const PlainGameSetup &setup);
	void reset();
	std::string apply_command(const std::string &command);
	std::string tick();
	std::string snapshot_json() const;
	std::string status() const;
	std::string state_hash() const;
	// Observational queue query. The returned production shape is the next real
	// draw and querying never mutates the bag or RNG, including at refill.
	PieceShape2D peek_next_piece_shape() const;
	// Authoritative Hold queries. Empty means the one slot is intentionally
	// empty; availability also requires a live active-piece lifecycle.
	std::optional<PieceShape2D> held_piece_shape() const;
	bool hold_available() const;
	// Exact read-only destination used by the next hard drop, or nullopt when
	// the session is terminal or has no active piece.
	std::optional<ActivePiece2D> hard_drop_destination() const;
	// Borrowed setup identifier; valid until the session is destroyed.
	const std::string &piece_set_id() const;

private:
	// Internal precondition: dimensions have already passed create_validated or
	// are the generated canonical default used by the no-argument constructor.
	Plain2DSession(int width, int height);

	int width_ = 6;
	int height_ = 6;
	PlainGameSetup setup_;
	PythonRandom rng_;
	GameState2D state_;
	std::vector<PieceShape2D> piece_bag_;
	std::string last_command_;
	std::string last_command_status_;
	int command_count_ = 0;
	std::size_t next_piece_index_ = 0;
	std::optional<PieceShape2D> held_piece_;
	bool hold_available_ = true;

	void refill_piece_bag();
	PieceShape2D draw_next_piece_shape();
	void spawn_next_piece();
	bool apply_hold();
	std::string current_piece_name() const;
	std::string next_piece_name() const;
	std::string command_status(const std::string &command) const;
};

bool is_supported_live_2d_board_shape(int width, int height);

} // namespace tet4d::core
