#include "tet4d_core/sha256.hpp"

#include <array>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <vector>

namespace tet4d::core {
namespace {

constexpr std::array<std::uint32_t, 64> K = {
	0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
	0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
	0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
	0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
	0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
	0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
	0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
	0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
	0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
	0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
	0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
	0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
	0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
	0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
	0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
	0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
};

std::uint32_t rotate_right(std::uint32_t value, std::uint32_t bits) {
	return (value >> bits) | (value << (32U - bits));
}

std::uint32_t read_be32(const std::vector<std::uint8_t> &bytes, std::size_t offset) {
	return (static_cast<std::uint32_t>(bytes[offset]) << 24U)
		| (static_cast<std::uint32_t>(bytes[offset + 1]) << 16U)
		| (static_cast<std::uint32_t>(bytes[offset + 2]) << 8U)
		| static_cast<std::uint32_t>(bytes[offset + 3]);
}

} // namespace

std::string sha256_hex(std::string_view text) {
	std::vector<std::uint8_t> bytes(text.begin(), text.end());
	const std::uint64_t bit_len = static_cast<std::uint64_t>(bytes.size()) * 8ULL;
	bytes.push_back(0x80);
	while ((bytes.size() % 64U) != 56U) {
		bytes.push_back(0);
	}
	for (int shift = 56; shift >= 0; shift -= 8) {
		bytes.push_back(static_cast<std::uint8_t>((bit_len >> shift) & 0xffU));
	}

	std::array<std::uint32_t, 8> hash = {
		0x6a09e667,
		0xbb67ae85,
		0x3c6ef372,
		0xa54ff53a,
		0x510e527f,
		0x9b05688c,
		0x1f83d9ab,
		0x5be0cd19,
	};

	for (std::size_t chunk = 0; chunk < bytes.size(); chunk += 64) {
		std::array<std::uint32_t, 64> words = {};
		for (std::size_t index = 0; index < 16; ++index) {
			words[index] = read_be32(bytes, chunk + index * 4);
		}
		for (std::size_t index = 16; index < 64; ++index) {
			const std::uint32_t s0 = rotate_right(words[index - 15], 7)
				^ rotate_right(words[index - 15], 18)
				^ (words[index - 15] >> 3U);
			const std::uint32_t s1 = rotate_right(words[index - 2], 17)
				^ rotate_right(words[index - 2], 19)
				^ (words[index - 2] >> 10U);
			words[index] = words[index - 16] + s0 + words[index - 7] + s1;
		}

		std::uint32_t a = hash[0];
		std::uint32_t b = hash[1];
		std::uint32_t c = hash[2];
		std::uint32_t d = hash[3];
		std::uint32_t e = hash[4];
		std::uint32_t f = hash[5];
		std::uint32_t g = hash[6];
		std::uint32_t h = hash[7];

		for (std::size_t index = 0; index < 64; ++index) {
			const std::uint32_t s1 = rotate_right(e, 6) ^ rotate_right(e, 11) ^ rotate_right(e, 25);
			const std::uint32_t choice = (e & f) ^ ((~e) & g);
			const std::uint32_t temp1 = h + s1 + choice + K[index] + words[index];
			const std::uint32_t s0 = rotate_right(a, 2) ^ rotate_right(a, 13) ^ rotate_right(a, 22);
			const std::uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
			const std::uint32_t temp2 = s0 + majority;

			h = g;
			g = f;
			f = e;
			e = d + temp1;
			d = c;
			c = b;
			b = a;
			a = temp1 + temp2;
		}

		hash[0] += a;
		hash[1] += b;
		hash[2] += c;
		hash[3] += d;
		hash[4] += e;
		hash[5] += f;
		hash[6] += g;
		hash[7] += h;
	}

	std::ostringstream out;
	out << std::hex << std::setfill('0');
	for (const std::uint32_t value : hash) {
		out << std::setw(8) << value;
	}
	return out.str();
}

} // namespace tet4d::core
