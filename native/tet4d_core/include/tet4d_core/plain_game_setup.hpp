#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace tet4d::core {

inline constexpr int PLAIN_SETUP_SCHEMA_VERSION = 2;
inline constexpr int PLAIN_SETUP_SEED_MIN = 0;
inline constexpr int PLAIN_SETUP_SEED_MAX = 999999999;
inline constexpr int PLAIN_SETUP_SPEED_MIN = 1;
inline constexpr int PLAIN_SETUP_SPEED_MAX = 10;
inline constexpr const char *RANDOM_MODE_FIXED_SEED = "fixed_seed";
inline constexpr const char *RANDOM_MODE_TRUE_RANDOM = "true_random";

struct PlainGameSetup {
	int schema_version = PLAIN_SETUP_SCHEMA_VERSION;
	std::string mode;
	std::string board_preset_id = "standard";
	std::vector<int> board_shape;
	std::string piece_set_id;
	std::string random_mode = RANDOM_MODE_FIXED_SEED;
	std::optional<int> configured_seed = 1337;
	int effective_seed = 1337;
	int initial_speed_level = 1;
	bool shuffle_bag = true;
};

class PythonRandom {
public:
	explicit PythonRandom(std::uint32_t seed = 0);

	void seed(std::uint32_t value);
	std::uint32_t getrandbits(int bit_count);
	std::uint32_t randbelow(std::uint32_t upper_bound);
	std::size_t words_consumed() const;

	template <typename T>
	void shuffle(std::vector<T> &items) {
		if (items.size() < 2) {
			return;
		}
		for (std::size_t index = items.size() - 1; index > 0; --index) {
			const std::size_t selected = static_cast<std::size_t>(
				randbelow(static_cast<std::uint32_t>(index + 1))
			);
			std::swap(items[index], items[selected]);
		}
	}

private:
	static constexpr std::size_t STATE_SIZE = 624;
	static constexpr std::size_t STATE_MIDDLE = 397;
	std::array<std::uint32_t, STATE_SIZE> state_{};
	std::size_t index_ = STATE_SIZE;
	std::size_t words_consumed_ = 0;

	void init_genrand(std::uint32_t seed);
	void twist();
	std::uint32_t next_word();
};

int generate_effective_seed();
bool is_valid_plain_random_mode(const std::string &random_mode);
bool is_valid_plain_seed(int seed);
bool is_valid_plain_speed(int speed_level);

} // namespace tet4d::core
