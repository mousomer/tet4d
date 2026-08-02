#include "topology_transport_variant.h"

#include "tet4d_core/generated/topology_contract_v1.hpp"

#include <godot_cpp/variant/array.hpp>
#include <godot_cpp/variant/char_string.hpp>
#include <godot_cpp/variant/string.hpp>

#include <utility>

namespace godot {
namespace {

std::string to_std_string(const String &text) {
	const CharString utf8 = text.utf8();
	return std::string(utf8.get_data());
}

String to_godot_string(const std::string &text) {
	return String::utf8(text.c_str());
}

template <typename T>
tet4d::core::TopologyTransportResult<T> failure(
		std::string code,
		std::string path,
		std::string expected,
		std::string actual,
		std::string message) {
	tet4d::core::TopologyTransportResult<T> result;
	result.error = tet4d::core::TopologyTransportError{
			std::move(code),
			std::move(path),
			std::move(expected),
			std::move(actual),
			std::move(message)};
	return result;
}

template <typename T>
tet4d::core::TopologyTransportResult<T> success(T value) {
	tet4d::core::TopologyTransportResult<T> result;
	result.value = std::move(value);
	return result;
}

std::string variant_category(Variant::Type type) {
	switch (type) {
		case Variant::NIL: return "null";
		case Variant::BOOL: return "boolean";
		case Variant::INT: return "integer";
		case Variant::FLOAT: return "float";
		case Variant::STRING: return "string";
		case Variant::ARRAY: return "array";
		case Variant::DICTIONARY: return "object";
		default: return "godot_type_" + std::to_string(static_cast<int>(type));
	}
}

Array integers_to_array(const std::vector<std::int64_t> &values) {
	Array result;
	for (const std::int64_t value : values) {
		result.push_back(value);
	}
	return result;
}

Dictionary boundary_to_dictionary(const tet4d::core::TopologyTransportBoundary &boundary) {
	Dictionary result;
	result["axis"] = to_godot_string(std::string(tet4d::core::generated::AXIS_NAMES[static_cast<std::size_t>(boundary.axis)]));
	result["side"] = to_godot_string(boundary.side);
	return result;
}

} // namespace

tet4d::core::TopologyTransportResult<tet4d::core::TransportValue>
topology_transport_value_from_variant(
		const Variant &value,
		const std::string &path) {
	using tet4d::core::TransportValue;
	switch (value.get_type()) {
		case Variant::NIL:
			return success(TransportValue{});
		case Variant::BOOL:
			return success(TransportValue(static_cast<bool>(value)));
		case Variant::INT:
			return success(TransportValue(static_cast<std::int64_t>(value)));
		case Variant::FLOAT:
			return success(TransportValue(static_cast<double>(value)));
		case Variant::STRING:
			return success(TransportValue(to_std_string(static_cast<String>(value))));
		case Variant::ARRAY: {
			const Array input = value;
			TransportValue::Array output;
			output.reserve(static_cast<std::size_t>(input.size()));
			for (int64_t index = 0; index < input.size(); ++index) {
				auto item = topology_transport_value_from_variant(
						input[index], path + "[" + std::to_string(index) + "]");
				if (!item.ok()) {
					return item;
				}
				output.push_back(std::move(*item.value));
			}
			return success(TransportValue(std::move(output)));
		}
		case Variant::DICTIONARY: {
			const Dictionary input = value;
			TransportValue::Object output;
			const Array keys = input.keys();
			for (int64_t index = 0; index < keys.size(); ++index) {
				const Variant key = keys[index];
				if (key.get_type() != Variant::STRING) {
					return failure<TransportValue>(
							"wrong_type", path, "object with string keys",
							variant_category(key.get_type()), path + " keys must be strings");
				}
				const std::string field = to_std_string(static_cast<String>(key));
				auto item = topology_transport_value_from_variant(
						input[key], path + "." + field);
				if (!item.ok()) {
					return item;
				}
				output.emplace(field, std::move(*item.value));
			}
			return success(TransportValue(std::move(output)));
		}
		default:
			return success(TransportValue(tet4d::core::UnsupportedTransportValue{
					variant_category(value.get_type())}));
	}
}

Dictionary topology_transport_error_dictionary(
		const tet4d::core::TopologyTransportError &error) {
	Dictionary detail;
	detail["code"] = to_godot_string(error.code);
	detail["path"] = to_godot_string(error.path);
	detail["expected"] = to_godot_string(error.expected);
	detail["actual"] = to_godot_string(error.actual);
	detail["message"] = to_godot_string(error.message);
	Dictionary result;
	result["ok"] = false;
	result["error"] = detail;
	return result;
}

Dictionary topology_transport_profile_dictionary(
		const tet4d::core::TopologyTransportProfile &profile) {
	Dictionary normalized;
	normalized["contract_version"] = profile.contract_version;
	normalized["rank"] = profile.rank;
	normalized["dimensions"] = integers_to_array(profile.dimensions);
	Array seams;
	for (const tet4d::core::TopologyTransportSeam &seam : profile.seams) {
		Dictionary row;
		row["id"] = to_godot_string(seam.id);
		row["source"] = boundary_to_dictionary(seam.source);
		row["target"] = boundary_to_dictionary(seam.target);
		Dictionary transform;
		transform["permutation"] = integers_to_array(seam.transform.permutation);
		transform["signs"] = integers_to_array(seam.transform.signs);
		row["transform"] = transform;
		row["enabled"] = seam.enabled;
		seams.push_back(row);
	}
	normalized["seams"] = seams;
	Dictionary result;
	result["ok"] = true;
	result["profile"] = normalized;
	return result;
}

Dictionary topology_transport_query_dictionary(
		const tet4d::core::TopologyTransportQuery &query) {
	Dictionary result;
	result["dimensions"] = integers_to_array(query.dimensions);
	result["coordinate"] = integers_to_array(query.coordinate);
	result["axis"] = query.axis;
	result["delta"] = query.delta;
	return result;
}

} // namespace godot
