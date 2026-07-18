#include "tet4d_core/plain_game_setup.hpp"

#include <atomic>
#include <chrono>
#include <random>

namespace tet4d::core {
namespace {

int bit_length(std::uint32_t value) {
	int result = 0;
	while (value != 0) {
		++result;
		value >>= 1U;
	}
	return result;
}

} // namespace

PythonRandom::PythonRandom(std::uint32_t seed_value) {
	seed(seed_value);
}

void PythonRandom::init_genrand(std::uint32_t seed_value) {
	state_[0] = seed_value;
	for (std::size_t index = 1; index < STATE_SIZE; ++index) {
		state_[index] = 1812433253U *
				(state_[index - 1] ^ (state_[index - 1] >> 30U)) +
				static_cast<std::uint32_t>(index);
	}
	index_ = STATE_SIZE;
}

void PythonRandom::seed(std::uint32_t value) {
	// CPython's _randommodule seeds integer inputs through init_by_array.
	init_genrand(19650218U);
	const std::array<std::uint32_t, 1> key = {value};
	std::size_t state_index = 1;
	std::size_t key_index = 0;
	for (std::size_t remaining = STATE_SIZE; remaining > 0; --remaining) {
		state_[state_index] =
				(state_[state_index] ^
				 ((state_[state_index - 1] ^ (state_[state_index - 1] >> 30U)) * 1664525U)) +
				key[key_index] + static_cast<std::uint32_t>(key_index);
		++state_index;
		++key_index;
		if (state_index >= STATE_SIZE) {
			state_[0] = state_[STATE_SIZE - 1];
			state_index = 1;
		}
		if (key_index >= key.size()) {
			key_index = 0;
		}
	}
	for (std::size_t remaining = STATE_SIZE - 1; remaining > 0; --remaining) {
		state_[state_index] =
				(state_[state_index] ^
				 ((state_[state_index - 1] ^ (state_[state_index - 1] >> 30U)) * 1566083941U)) -
				static_cast<std::uint32_t>(state_index);
		++state_index;
		if (state_index >= STATE_SIZE) {
			state_[0] = state_[STATE_SIZE - 1];
			state_index = 1;
		}
	}
	state_[0] = 0x80000000U;
	index_ = STATE_SIZE;
	words_consumed_ = 0;
}

void PythonRandom::twist() {
	static constexpr std::uint32_t MATRIX_A = 0x9908b0dfU;
	static constexpr std::uint32_t UPPER_MASK = 0x80000000U;
	static constexpr std::uint32_t LOWER_MASK = 0x7fffffffU;
	for (std::size_t index = 0; index < STATE_SIZE; ++index) {
		const std::uint32_t value =
				(state_[index] & UPPER_MASK) |
				(state_[(index + 1) % STATE_SIZE] & LOWER_MASK);
		state_[index] =
				state_[(index + STATE_MIDDLE) % STATE_SIZE] ^
				(value >> 1U) ^
				((value & 1U) == 0U ? 0U : MATRIX_A);
	}
	index_ = 0;
}

std::uint32_t PythonRandom::next_word() {
	if (index_ >= STATE_SIZE) {
		twist();
	}
	std::uint32_t value = state_[index_++];
	value ^= value >> 11U;
	value ^= (value << 7U) & 0x9d2c5680U;
	value ^= (value << 15U) & 0xefc60000U;
	value ^= value >> 18U;
	++words_consumed_;
	return value;
}

std::uint32_t PythonRandom::getrandbits(int bit_count) {
	if (bit_count < 1 || bit_count > 32) {
		return 0U;
	}
	return next_word() >> (32 - bit_count);
}

std::uint32_t PythonRandom::randbelow(std::uint32_t upper_bound) {
	if (upper_bound == 0U) {
		return 0U;
	}
	const int bits = bit_length(upper_bound);
	std::uint32_t value = getrandbits(bits);
	while (value >= upper_bound) {
		value = getrandbits(bits);
	}
	return value;
}

std::size_t PythonRandom::words_consumed() const {
	return words_consumed_;
}

int generate_effective_seed() {
	static std::atomic<std::uint32_t> counter{0};
	static std::atomic<int> previous{-1};
	std::random_device device;
	const std::uint64_t now = static_cast<std::uint64_t>(
		std::chrono::high_resolution_clock::now().time_since_epoch().count()
	);
	const std::uint64_t entropy =
			(static_cast<std::uint64_t>(device()) << 32U) ^
			static_cast<std::uint64_t>(device()) ^
			now ^
			static_cast<std::uint64_t>(counter.fetch_add(1));
	int seed = static_cast<int>(entropy % static_cast<std::uint64_t>(PLAIN_SETUP_SEED_MAX + 1));
	const int last = previous.load();
	if (seed == last) {
		seed = (seed + 1) % (PLAIN_SETUP_SEED_MAX + 1);
	}
	previous.store(seed);
	return seed;
}

bool is_valid_plain_random_mode(const std::string &random_mode) {
	return random_mode == RANDOM_MODE_FIXED_SEED ||
			random_mode == RANDOM_MODE_TRUE_RANDOM;
}

bool is_valid_plain_seed(int seed) {
	return seed >= PLAIN_SETUP_SEED_MIN && seed <= PLAIN_SETUP_SEED_MAX;
}

bool is_valid_plain_speed(int speed_level) {
	return speed_level >= PLAIN_SETUP_SPEED_MIN &&
			speed_level <= PLAIN_SETUP_SPEED_MAX;
}

} // namespace tet4d::core
