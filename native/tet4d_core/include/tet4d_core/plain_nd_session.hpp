#pragma once

#include "tet4d_core/plain_nd.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace tet4d::core {

class PlainNDSession {
public:
	explicit PlainNDSession(int dimension);

	void reset();
	std::string apply_command(const std::string &command);
	std::string tick();
	std::string snapshot_json() const;
	std::string status() const;
	std::string state_hash() const;

private:
	int dimension_ = 3;
	BoardShapeND board_shape_;
	GameStateND state_;
	std::vector<PieceShapeND> piece_sequence_;
	std::string last_command_;
	std::string last_command_status_;
	int command_count_ = 0;
	std::size_t next_piece_index_ = 0;

	PieceShapeND draw_next_piece_shape();
	void spawn_next_piece();
	std::string current_piece_name() const;
	std::string next_piece_name() const;
	std::string command_status(const std::string &command) const;
};

} // namespace tet4d::core
