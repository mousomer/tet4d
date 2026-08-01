#pragma once

#include "tet4d_core/topology_transport.hpp"

#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/variant.hpp>

namespace godot {

tet4d::core::TopologyTransportResult<tet4d::core::TransportValue>
topology_transport_value_from_variant(
		const Variant &value,
		const std::string &path);
Dictionary topology_transport_error_dictionary(
		const tet4d::core::TopologyTransportError &error);
Dictionary topology_transport_profile_dictionary(
		const tet4d::core::TopologyTransportProfile &profile);
Dictionary topology_transport_query_dictionary(
		const tet4d::core::TopologyTransportQuery &query);

} // namespace godot
