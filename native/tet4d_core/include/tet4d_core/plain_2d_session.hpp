#pragma once

#include "tet4d_core/plain_2d.hpp"

#include <cstddef>
#include <string>

namespace tet4d::core {

class Plain2DSession {
public:
	Plain2DSession();

	void reset();
	std::string apply_command(const std::string &command);
	std::string tick();
	std::string snapshot_json() const;
	std::string status() const;
	std::string state_hash() const;

private:
	GameState2D state_;
	std::string last_command_;
	std::string last_command_status_;
	int command_count_ = 0;
	std::size_t next_piece_index_ = 0;

	PieceShape2D draw_next_piece_shape();
	void spawn_next_piece();
	std::string current_piece_name() const;
	std::string next_piece_name() const;
	std::string command_status(const std::string &command) const;
};

} // namespace tet4d::core
