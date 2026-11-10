#include "tet4d_core/plain_piece_catalog.hpp"
#include "tet4d_core_api.h"
#include "topology_transport_variant.h"
#include <algorithm>
#include <godot_cpp/classes/crypto.hpp>
#include <limits>
#include <stdexcept>

namespace godot {
namespace {
using namespace tet4d::core;
Dictionary failure(const char* code) {
    Dictionary error;
    error["code"] = code;
    Dictionary result;
    result["ok"] = false;
    result["error"] = error;
    return result;
}
// Exact recursive equality deliberately rejects Variant's numeric coercions.
// Depth is bounded for hostile/cyclic dictionaries; expected DTOs are acyclic.
bool exact(const Variant& a, const Variant& b, int depth = 0) {
    if (depth > 32 || a.get_type() != b.get_type())
        return false;
    if (a.get_type() == Variant::DICTIONARY) {
        Dictionary x = a, y = b;
        if (x.size() != y.size())
            return false;
        Array keys = x.keys();
        for (int i = 0; i < keys.size(); ++i)
            if (keys[i].get_type() != Variant::STRING || !y.has(keys[i]) ||
                !exact(x[keys[i]], y[keys[i]], depth + 1))
                return false;
        return true;
    }
    if (a.get_type() == Variant::ARRAY) {
        Array x = a, y = b;
        if (x.size() != y.size())
            return false;
        for (int i = 0; i < x.size(); ++i)
            if (!exact(x[i], y[i], depth + 1))
                return false;
        return true;
    }
    return a == b;
}
bool fields(const Dictionary& d, std::initializer_list<const char*> names) {
    if (d.size() != static_cast<int64_t>(names.size()))
        return false;
    for (auto name : names)
        if (!d.has(name))
            return false;
    return true;
}
template <typename T> Array ints(const T& values) {
    Array a;
    for (auto v : values)
        a.push_back(static_cast<int64_t>(v));
    return a;
}
Dictionary state(const ExplorerPiece& p) {
    Dictionary d, key;
    key["namespace"] = String(p.object_namespace.c_str());
    key["ordinal"] = p.object_ordinal;
    d["version"] = String(p.version.c_str());
    d["object_key"] = key;
    d["profile"] = topology_transport_profile_dictionary(p.profile)["profile"];
    Array rest, cells;
    for (const auto& c : p.rest_cells) {
        Dictionary row;
        row["id"] = c.id;
        row["coordinate"] = ints(c.coordinate.values);
        rest.push_back(row);
    }
    for (const auto& c : p.cells) {
        Dictionary row, frame;
        frame["permutation"] = ints(c.frame.permutation);
        frame["signs"] = ints(c.frame.signs);
        row["id"] = c.id;
        row["domain"] = c.domain;
        row["coordinate"] = ints(c.coordinate.values);
        row["frame"] = frame;
        cells.push_back(row);
    }
    d["rest_cells"] = rest;
    d["cells"] = cells;
    return d;
}
Dictionary action(MoveStepQuery a) {
    Dictionary d;
    d["axis"] = a.axis;
    d["delta"] = a.delta;
    return d;
}
Dictionary inverse(const PieceInverse& v) {
    Dictionary d;
    d["version"] = String(v.version.c_str());
    d["source"] = state(v.source);
    d["forward"] = action(v.forward);
    return d;
}
Dictionary candidate(const PieceCandidate& c) {
    Dictionary d;
    d["version"] = String(c.version.c_str());
    d["source_revision"] = c.source_revision;
    d["source"] = state(c.source);
    d["target"] = state(c.target);
    d["action"] = action(c.action);
    d["inverse"] = inverse(c.inverse);
    d["is_inverse"] = c.is_inverse;
    const char* names[] = {"plain_translation", "rigid_transform", "cellwise_deformation",
                           "blocked"};
    d["classification"] = names[static_cast<int>(c.classification)];
    Array witnesses;
    for (const auto& w : c.witnesses) {
        Dictionary row, frame;
        frame["permutation"] = ints(w.transport.permutation);
        frame["signs"] = ints(w.transport.signs);
        row["id"] = w.id;
        row["source"] = ints(w.source.values);
        row["target"] = ints(w.target.values);
        row["transport"] = frame;
        row["step"] = action(w.step);
        row["reverse"] = action(w.reverse);
        row["seam"] = w.seam ? Variant(String(w.seam->c_str())) : Variant();
        witnesses.push_back(row);
    }
    d["witnesses"] = witnesses;
    return d;
}
Dictionary snapshot(const PieceEnvelope& e, int index) {
    Dictionary d;
    d["ok"] = true;
    d["revision"] = e.revision;
    d["piece"] = state(e.piece);
    d["initial_piece"] = state(e.initial_piece);
    Array undo;
    for (const auto& v : e.undo)
        undo.push_back(inverse(v));
    d["undo"] = undo;
    Array names;
    const auto& catalog = plain_piece_catalog_2d("classic");
    for (const auto& p : catalog)
        names.push_back(String(p.name.c_str()));
    d["piece_names"] = names;
    d["selected_piece"] = index;
    d["piece_name"] = String(catalog[index].name.c_str());
    d["color_id"] = catalog[index].color_id;
    return d;
}
bool read_action(const Variant& v, MoveStepQuery& a) {
    if (v.get_type() != Variant::DICTIONARY)
        return false;
    Dictionary d = v;
    if (!fields(d, {"axis", "delta"}) || d["axis"].get_type() != Variant::INT ||
        d["delta"].get_type() != Variant::INT)
        return false;
    int64_t axis = d["axis"], delta = d["delta"];
    if (axis < 0 || axis > 1 || (delta != -1 && delta != 1))
        return false;
    a = {static_cast<int>(axis), static_cast<int>(delta)};
    return true;
}
PieceFailure baseline(const TopologyTransportProfile& profile, const std::string& ns,
                      int64_t ordinal, int index, ExplorerPiece& out) {
    const auto& catalog = plain_piece_catalog_2d("classic");
    if (index < 0 || index >= static_cast<int>(catalog.size()))
        return PieceFailure::invalid_piece_state;
    if (profile.rank != 2 || profile.dimensions.size() != 2)
        return PieceFailure::invalid_profile;
    ExplorerPiece p;
    p.profile = profile;
    p.object_namespace = ns;
    p.object_ordinal = ordinal;
    auto blocks = catalog[index].blocks;
    int min_x = blocks[0].x, min_y = blocks[0].y, max_x = min_x, max_y = min_y;
    for (auto c : blocks) {
        min_x = std::min(min_x, c.x);
        min_y = std::min(min_y, c.y);
        max_x = std::max(max_x, c.x);
        max_y = std::max(max_y, c.y);
    }
    for (auto& c : blocks) {
        c.x -= min_x;
        c.y -= min_y;
    }
    std::sort(blocks.begin(), blocks.end(),
              [](auto a, auto b) { return std::tie(a.x, a.y) < std::tie(b.x, b.y); });
    const int64_t ox = (profile.dimensions[0] - (max_x - min_x + 1)) / 2;
    const int64_t oy = (profile.dimensions[1] - (max_y - min_y + 1)) / 2;
    for (size_t i = 0; i < blocks.size(); ++i) {
        auto c = blocks[i];
        p.rest_cells.push_back({static_cast<int64_t>(i), {{c.x, c.y}}});
        p.cells.push_back({static_cast<int64_t>(i),
                           0,
                           {{static_cast<int>(c.x + ox), static_cast<int>(c.y + oy)}},
                           {}});
    }
    return validate_explorer_piece(p, out);
}
} // namespace

Dictionary Tet4DCoreApi::explorer_2d(const Variant& request) {
    try {
        if (request.get_type() != Variant::DICTIONARY)
            return failure("wrong_type");
        Dictionary r = request;
        if (!r.has("op") || r["op"].get_type() != Variant::STRING)
            return failure("invalid_request");
        String op = r["op"];
        if (op == "close" && fields(r, {"op"})) {
            explorer_runtime_.reset();
            Dictionary d;
            d["ok"] = true;
            return d;
        }
        if (op == "begin" || op == "profile" || op == "replace") {
            if (!fields(r, op == "replace" ? std::initializer_list<const char*>{"op", "index"}
                                           : std::initializer_list<const char*>{"op", "profile"}))
                return failure("invalid_request");
            if (op != "begin" && !explorer_runtime_)
                return failure("missing_provider");
            TopologyTransportProfile profile;
            if (op == "replace")
                profile = explorer_runtime_->snapshot().piece.profile;
            else {
                auto value = topology_transport_value_from_variant(r["profile"], "profile");
                if (!value.ok())
                    return topology_transport_error_dictionary(*value.error);
                auto decoded = decode_topology_transport_profile(*value.value);
                if (!decoded.ok())
                    return topology_transport_error_dictionary(*decoded.error);
                profile = *decoded.value;
            }
            int index = op == "begin" ? 0 : explorer_catalog_index_;
            if (op == "replace") {
                if (r["index"].get_type() != Variant::INT)
                    return failure("wrong_type");
                int64_t requested = r["index"];
                if (requested < 0 ||
                    requested >= static_cast<int64_t>(plain_piece_catalog_2d("classic").size()))
                    return failure("invalid_piece_state");
                index = static_cast<int>(requested);
            }
            std::string ns;
            int64_t ordinal = 0, revision = 0;
            if (op == "begin") {
                Ref<Crypto> crypto;
                crypto.instantiate();
                ns = crypto->generate_random_bytes(16).hex_encode().utf8().get_data();
            } else {
                auto old = explorer_runtime_->snapshot();
                ns = old.piece.object_namespace;
                if (old.revision == std::numeric_limits<int64_t>::max() ||
                    explorer_ordinal_ == std::numeric_limits<int64_t>::max())
                    return failure("resource_limit");
                ordinal = op == "replace" ? explorer_ordinal_ + 1 : explorer_ordinal_;
                revision = old.revision + 1;
            }
            ExplorerPiece p;
            PieceFailure error;
            if (op == "profile") {
                auto initial = explorer_runtime_->snapshot().initial_piece;
                initial.profile = profile;
                error = validate_explorer_piece(initial, p);
            } else {
                error = baseline(profile, ns, ordinal, index, p);
            }
            if (error != PieceFailure::none)
                return failure(piece_failure_name(error));
            PieceEnvelope envelope{revision, p, p, {}};
            auto next = std::make_unique<ExplorerPieceRuntime>(envelope);
            Dictionary response = snapshot(envelope, index); // allocate before commit
            explorer_runtime_.swap(next);
            explorer_ordinal_ = ordinal;
            explorer_catalog_index_ = index;
            return response;
        }
        if (!explorer_runtime_)
            return failure("missing_provider");
        auto before = explorer_runtime_->snapshot();
        if (op == "snapshot" && fields(r, {"op"}))
            return snapshot(before, explorer_catalog_index_);
        if (op == "retry" && fields(r, {"op"})) {
            auto next = std::make_unique<ExplorerPieceRuntime>(before);
            auto error = next->retry();
            if (error != PieceFailure::none)
                return failure(piece_failure_name(error));
            Dictionary response = snapshot(next->snapshot(), explorer_catalog_index_);
            explorer_runtime_.swap(next);
            return response;
        }
        PieceProposal proposed;
        if (op == "propose") {
            if (!fields(r, {"op", "revision", "source", "action"}) ||
                r["revision"].get_type() != Variant::INT)
                return failure("invalid_request");
            if (static_cast<int64_t>(r["revision"]) != before.revision)
                return failure("stale_candidate");
            if (!exact(r["source"], state(before.piece)))
                return failure("invalid_piece_state");
            MoveStepQuery a;
            if (!read_action(r["action"], a))
                return failure("invalid_action");
            proposed = propose_piece_translation(before.piece, before.revision, a);
        } else if (op == "inverse") {
            if (!fields(r, {"op", "revision", "inverse"}) ||
                r["revision"].get_type() != Variant::INT)
                return failure("invalid_request");
            if (static_cast<int64_t>(r["revision"]) != before.revision)
                return failure("stale_candidate");
            if (before.undo.empty() || !exact(r["inverse"], inverse(before.undo.back())))
                return failure("inverse_mismatch");
            proposed = propose_piece_inverse(before.piece, before.revision, before.undo.back());
        } else if (op == "apply") {
            if (!fields(r, {"op", "candidate"}) || r["candidate"].get_type() != Variant::DICTIONARY)
                return failure("invalid_request");
            Dictionary c = r["candidate"];
            if (!c.has("source_revision") || c["source_revision"].get_type() != Variant::INT)
                return failure("candidate_mismatch");
            if (static_cast<int64_t>(c["source_revision"]) != before.revision)
                return failure("stale_candidate");
            MoveStepQuery a;
            if (!c.has("is_inverse") || c["is_inverse"].get_type() != Variant::BOOL)
                return failure("candidate_mismatch");
            if (static_cast<bool>(c["is_inverse"])) {
                if (before.undo.empty())
                    return failure("inverse_mismatch");
                proposed = propose_piece_inverse(before.piece, before.revision, before.undo.back());
            } else {
                if (!c.has("action") || !read_action(c["action"], a))
                    return failure("invalid_action");
                proposed = propose_piece_translation(before.piece, before.revision, a);
            }
            if (!proposed.candidate || !exact(c, candidate(*proposed.candidate)))
                return failure("candidate_mismatch");
            auto next = std::make_unique<ExplorerPieceRuntime>(before);
            auto error = next->apply(*proposed.candidate);
            if (error != PieceFailure::none)
                return failure(piece_failure_name(error));
            Dictionary response = snapshot(next->snapshot(), explorer_catalog_index_);
            explorer_runtime_.swap(next);
            return response;
        } else
            return failure("invalid_request");
        if (!proposed.candidate)
            return failure(piece_failure_name(proposed.failure));
        Dictionary d;
        d["ok"] = true;
        d["candidate"] = candidate(*proposed.candidate);
        return d;
    } catch (const std::bad_alloc&) {
        return failure("resource_limit");
    } catch (const std::exception&) {
        return failure("invalid_request");
    } catch (...) {
        return failure("invalid_request");
    }
}
} // namespace godot
