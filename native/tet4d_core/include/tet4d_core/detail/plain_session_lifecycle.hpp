#pragma once

#include "tet4d_core/plain_game_setup.hpp"

#include <utility>

namespace tet4d::core::detail {

enum class CommandOutcome { Accepted, Rejected, RejectedWithPrefix, Unsupported };

template <typename Piece>
class PlainSessionLifecycle {
protected:
	explicit PlainSessionLifecycle(PlainGameSetup setup) :
			setup_(std::move(setup)), rng_(static_cast<std::uint32_t>(setup_.effective_seed)) {}

	PlainGameSetup setup_;
	PythonRandom rng_;
	std::vector<Piece> piece_bag_;
	std::string last_command_;
	std::string last_command_status_;
	int command_count_ = 0;
	std::size_t next_piece_index_ = 0;
	std::optional<Piece> held_piece_;
	bool hold_available_ = true;

	template <typename Spawn>
	void reset_lifecycle(Spawn spawn) {
		next_piece_index_ = 0;
		piece_bag_.clear();
		rng_.seed(static_cast<std::uint32_t>(setup_.effective_seed));
		held_piece_.reset();
		hold_available_ = true;
		spawn();
		last_command_ = "reset";
		last_command_status_ = "reset";
		command_count_ = 0;
	}

	Piece peek_piece(const std::vector<Piece> &sequence) const {
		if (sequence.empty()) {
			return {};
		}
		if (!setup_.shuffle_bag) {
			return sequence[next_piece_index_ % sequence.size()];
		}
		if (!piece_bag_.empty()) {
			return piece_bag_.back();
		}
		PythonRandom preview_rng = rng_;
		return build_shuffled_piece_bag(sequence, preview_rng).back();
	}

	// Callers handle an absent catalog according to their existing session contract.
	Piece draw_piece(const std::vector<Piece> &sequence) {
		if (!setup_.shuffle_bag) {
			const Piece shape = sequence[next_piece_index_ % sequence.size()];
			++next_piece_index_;
			return shape;
		}
		if (piece_bag_.empty()) {
			piece_bag_ = build_shuffled_piece_bag(sequence, rng_);
		}
		Piece shape = piece_bag_.back();
		piece_bag_.pop_back();
		return shape;
	}

	std::string next_name(const std::vector<Piece> &sequence) const {
		if (sequence.empty()) {
			return "none";
		}
		if (setup_.shuffle_bag) {
			return piece_bag_.empty() ? "pending_bag" : piece_bag_.back().name;
		}
		return sequence[next_piece_index_ % sequence.size()].name;
	}

	template <typename State>
	bool can_hold(const State &state) const {
		return hold_available_ && !state.game_over && state.active_piece.has_value();
	}

	template <typename State, typename Draw>
	bool hold(State &state, Draw draw) {
		if (!can_hold(state)) {
			return false;
		}
		const Piece outgoing = state.active_piece->shape;
		const Piece incoming = held_piece_.has_value() ? *held_piece_ : draw();
		held_piece_ = outgoing;
		hold_available_ = false;
		state.spawn_piece(incoming);
		return true;
	}

	template <typename State, typename Lock>
	void tick_lifecycle(State &state, Lock lock_and_spawn) {
		if (!state.game_over && !state.try_soft_drop()) {
			lock_and_spawn();
			hold_available_ = !state.game_over && state.active_piece.has_value();
		}
		last_command_ = "tick";
		last_command_status_ = state.game_over ? "game_over" : "accepted";
		++command_count_;
	}

	template <typename Session, typename Play>
	std::string route_command(
			Session &session, const std::string &command, bool game_over, Play play) {
		if (command == "reset") {
			session.reset();
		} else if (game_over) {
			last_command_ = "rejected:" + command;
			last_command_status_ = "rejected";
		} else if (command == "tick") {
			return session.tick();
		} else {
			const auto outcome = play();
			if (outcome == CommandOutcome::Unsupported) {
				last_command_ = "unsupported:" + command;
				last_command_status_ = "unsupported";
			} else {
				const bool accepted = outcome == CommandOutcome::Accepted;
				last_command_ = outcome == CommandOutcome::RejectedWithPrefix ? "rejected:" + command : command;
				last_command_status_ = accepted ? "accepted" : "rejected";
				++command_count_;
			}
		}
		return command_status(session, command);
	}

	template <typename Session>
	static std::string command_status(const Session &session, const std::string &command) {
		return "command=" + command + " " + session.status();
	}
};

} // namespace tet4d::core::detail
