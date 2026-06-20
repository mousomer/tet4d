#include "tet4d_core/sha256.hpp"

#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

namespace {

struct TraceMetadataCase {
	const char *name;
	int dimension;
	const char *mode;
	const char *topology;
	int schema_version;
	const char *trace_id;
};

void require(bool condition, const std::string &message) {
	if (!condition) {
		std::cerr << message << "\n";
		std::exit(1);
	}
}

std::string escape_json(const std::string &text) {
	std::string escaped;
	escaped.reserve(text.size() + 8);
	for (const char ch : text) {
		switch (ch) {
			case '\\':
				escaped += "\\\\";
				break;
			case '"':
				escaped += "\\\"";
				break;
			default:
				escaped += ch;
				break;
		}
	}
	return escaped;
}

std::string identity_for(const TraceMetadataCase &item) {
	return std::string("{\"dimension\":") + std::to_string(item.dimension) +
		",\"mode\":\"" + item.mode +
		"\",\"schema_version\":" + std::to_string(item.schema_version) +
		",\"topology\":\"" + item.topology +
		"\",\"trace_id\":\"" + item.trace_id + "\"}";
}

void test_trace_metadata_identity_digest() {
	const std::vector<TraceMetadataCase> cases = {
		{"plain-2d-minimal", 2, "2d", "plain", 1, "plain_2d_spawn_001"},
		{"plain-3d-minimal", 3, "3d", "plain", 1, "plain_3d_spawn_001"},
		{"wrapped-4d-minimal", 4, "4d", "wrapped", 1, "wrapped_4d_spawn_001"},
	};

	std::cout << "{\"cases\":[";
	for (std::size_t index = 0; index < cases.size(); ++index) {
		const TraceMetadataCase &item = cases[index];
		const std::string identity = identity_for(item);
		const std::string digest = tet4d::core::sha256_hex(identity);
		std::cout << "{\"name\":\"" << item.name
		          << "\",\"identity\":\"" << escape_json(identity)
		          << "\",\"digest\":\"" << digest << "\"}";
		if (index + 1 < cases.size()) {
			std::cout << ",";
		}
	}
	std::cout << "]}\n";
}

} // namespace

int main(int argc, char **argv) {
	if (argc >= 2 && std::string(argv[1]) == "--trace-metadata-identity-digest") {
		test_trace_metadata_identity_digest();
		return 0;
	}
	require(false, "trace metadata identity/digest tests require --trace-metadata-identity-digest");
	return 1;
}
