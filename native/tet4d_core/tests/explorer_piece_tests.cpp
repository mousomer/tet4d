#include "explorer_piece_assertions.hpp"

#include <array>
#include <functional>
#include <limits>
#include <random>
#include <thread>

using namespace explorer_test;

namespace {
#include "explorer_piece_fixtures.hpp"

std::size_t translations = 0, rejected_translations = 0, inverses = 0, sequences = 0, states = 0;

ExplorerPiece make_piece(const std::vector<CoordND>& geometry, int width, int height, bool torus) {
    ExplorerPiece piece;
    piece.object_namespace = "00000000000000000000000000000001";
    piece.object_ordinal = 1;
    piece.profile = {1, 2, {width, height}, {}};
    if (torus)
        piece.profile.seams = {{"seam_000", {0, "-"}, {0, "+"}, {{0}, {1}}, true},
                               {"seam_001", {1, "-"}, {1, "+"}, {{0}, {1}}, true}};
    auto ordered = geometry;
    std::sort(ordered.begin(), ordered.end());
    for (std::size_t i = 0; i < ordered.size(); ++i) {
        piece.rest_cells.push_back({static_cast<std::int64_t>(i), ordered[i]});
        piece.cells.push_back({static_cast<std::int64_t>(i), 0, ordered[i], {}});
    }
    return piece;
}
PieceCandidate proposal(const PieceEnvelope& state, MoveStepQuery action) {
    auto result = propose_piece_translation(state.piece, state.revision, action);
    require(result.candidate.has_value(),
            std::string("expected proposal: ") + piece_failure_name(result.failure));
    return *result.candidate;
}
void commit(ExplorerPieceRuntime& runtime, const PieceCandidate& candidate) {
    const auto before = runtime.snapshot();
    require(runtime.apply(candidate) == PieceFailure::none, "commit succeeds");
    const auto after = runtime.snapshot();
    assert_piece_preserved(before.piece, after.piece);
    require(after.revision == before.revision + 1, "revision increases");
    require(after.initial_piece == before.initial_piece, "baseline immutable");
    if (candidate.is_inverse) {
        ++inverses;
        assert_exact_semantic_recovery(candidate.inverse.source, after.piece);
    } else
        ++translations;
}
void undo(ExplorerPieceRuntime& runtime, const PieceInverse& descriptor) {
    const auto before = runtime.snapshot();
    auto result = propose_piece_inverse(before.piece, before.revision, descriptor);
    require(result.candidate.has_value(), "recorded inverse proposal");
    require(runtime.snapshot() == before, "inverse proposal pure");
    commit(runtime, *result.candidate);
}
void reject_apply(ExplorerPieceRuntime& runtime, const PieceCandidate& candidate,
                  PieceFailure expected) {
    const auto before = runtime.snapshot();
    require(runtime.apply(candidate) == expected, "application rejection reason");
    assert_atomic_noop(before, runtime.snapshot());
}
void fixture_cases() {
    for (const auto& f : reviewed_cases()) {
        context = f.id;
        ++states;
        ExplorerPieceRuntime runtime({f.revision, f.source, f.source, {}});
        const auto before = runtime.snapshot();
        auto result = propose_piece_translation(before.piece, before.revision, f.action);
        require(before == runtime.snapshot(), "fixture proposal pure");
        assert_deterministic_proposal(f.source, f.action);
        if (!f.failure.empty()) {
            ++rejected_translations;
            require(!result.candidate, "blocked has no applicable candidate");
            require(piece_failure_name(result.failure) == f.failure, "reviewed failure reason");
            assert_atomic_noop(before, runtime.snapshot());
            continue;
        }
        require(result.candidate.has_value(), "reviewed candidate exists");
        const auto& candidate = *result.candidate;
        require(candidate.target == f.target && candidate.witnesses == f.witnesses,
                "reviewed full target/witnesses");
        require(candidate.classification == f.classification, "reviewed classification");
        require(candidate.inverse == PieceInverse{f.inverse_version, f.source, f.action},
                "reviewed inverse descriptor");
        commit(runtime, candidate);
        undo(runtime, candidate.inverse);
        assert_exact_semantic_recovery(f.source, runtime.snapshot().piece);
        require(runtime.snapshot().undo.empty(), "forward push/inverse pop cancels");
        if (f.id == "E8_proposal") {
            ExplorerPieceRuntime aba(before);
            auto intervening = proposal(before, E8_INTERVENING);
            commit(aba, intervening);
            require(aba.snapshot().piece.cells == E8_CURRENT &&
                        aba.snapshot().revision == E8_REVISION,
                    "E8 intervening fixture");
            reject_apply(aba, candidate, PieceFailure::stale_candidate);
            undo(aba, intervening.inverse);
            require(aba.snapshot().revision == E8_ABA_REVISION, "E8 inverse revision");
            reject_apply(aba, candidate, PieceFailure::stale_candidate);
        }
    }
}
void negative_cases() {
    context = "negative state/action/proposal";
    const auto base = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, true);
    using Mutation = std::function<void(ExplorerPiece&)>;
    const std::vector<std::pair<Mutation, PieceFailure>> mutations = {
        {[](auto& p) { p.version = "unknown"; }, PieceFailure::unsupported_representation},
        {[](auto& p) { p.profile.rank = 3; }, PieceFailure::unsupported_representation},
        {[](auto& p) { p.profile.contract_version = 2; }, PieceFailure::unsupported_representation},
        {[](auto& p) { p.profile.dimensions = {0, 4}; }, PieceFailure::invalid_profile},
        {[](auto& p) { p.profile.dimensions = {1000001, 4}; }, PieceFailure::invalid_profile},
        {[](auto& p) { p.profile.seams.push_back(p.profile.seams.front()); },
         PieceFailure::invalid_profile},
        {[](auto& p) { p.profile.seams[0].source.axis = std::numeric_limits<std::int64_t>::max(); },
         PieceFailure::invalid_profile},
        {[](auto& p) { p.profile.seams = {{"cross_axis", {0, "-"}, {1, "-"}, {{0}, {1}}, true}}; },
         PieceFailure::unsupported_representation},
        {[](auto& p) { p.profile.seams[0].transform.signs = {-1}; },
         PieceFailure::unsupported_representation},
        {[](auto& p) { p.cells[1].id = 0; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[1].coordinate = p.cells[0].coordinate; },
         PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].frame.signs = {0, 1}; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].frame.permutation = {1, 1}; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].coordinate.values = {0}; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].coordinate.values[0] = -1; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].coordinate.values[0] = 4; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells[0].domain = 1; }, PieceFailure::unsupported_representation},
        {[](auto& p) { p.rest_cells[0].id = 2; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.rest_cells[1].coordinate = {{2, 0}}; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.rest_cells[0].coordinate = {{1, 0}}; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.rest_cells[1].coordinate = {{1000000, 0}}; },
         PieceFailure::invalid_piece_state},
        {[](auto& p) { p.rest_cells.clear(); }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.object_namespace = "bad"; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.object_ordinal = -1; }, PieceFailure::invalid_piece_state},
        {[](auto& p) { p.cells.resize(EXPLORER_MAX_CELLS + 1); }, PieceFailure::resource_limit}};
    for (std::size_t i = 0; i < mutations.size(); ++i) {
        context = "invalid source " + std::to_string(i);
        auto changed = base;
        mutations[i].first(changed);
        ExplorerPieceRuntime runtime({0, changed, changed, {}});
        auto before = runtime.snapshot();
        auto result = propose_piece_translation(before.piece, 0, {0, 1});
        require(!result.candidate && result.failure == mutations[i].second,
                "invalid source reason");
        ++rejected_translations;
        assert_atomic_noop(before, runtime.snapshot());
    }
    ExplorerPieceRuntime runtime({0, base, base, {}});
    auto before = runtime.snapshot();
    for (MoveStepQuery action : std::vector<MoveStepQuery>{
             {-1, 1}, {2, 1}, {0, 0}, {0, 2}, {0, std::numeric_limits<int>::min()}}) {
        auto result = propose_piece_translation(base, 0, action);
        require(!result.candidate && result.failure == PieceFailure::invalid_action,
                "invalid action");
        ++rejected_translations;
        assert_atomic_noop(before, runtime.snapshot());
    }
    const auto valid = proposal(before, {0, 1});
    using CandidateMutation = std::function<void(PieceCandidate&)>;
    const std::vector<CandidateMutation> tamper = {
        [](auto& c) { c.target.cells[1].coordinate = c.target.cells[0].coordinate; },
        [](auto& c) { c.target.cells[0].id = 7; },
        [](auto& c) { c.target.cells[0].frame.signs[0] = -1; },
        [](auto& c) { c.target.rest_cells[0].coordinate.values[0] = 2; },
        [](auto& c) { c.target.object_ordinal++; },
        [](auto& c) { c.target.profile.dimensions[0]++; },
        [](auto& c) { c.witnesses[0].reverse.delta *= -1; },
        [](auto& c) { c.witnesses[0].transport.signs[0] = -1; },
        [](auto& c) { c.witnesses[0].seam = "forged"; },
        [](auto& c) { c.classification = PieceClassification::cellwise_deformation; },
        [](auto& c) { c.inverse.forward.delta *= -1; },
        [](auto& c) { c.inverse.version = "bad"; },
        [](auto& c) { c.action.axis = 1; },
        [](auto& c) { c.is_inverse = true; }};
    for (const auto& mutation : tamper) {
        auto forged = valid;
        mutation(forged);
        reject_apply(runtime, forged, PieceFailure::candidate_mismatch);
    }
    auto changed_source = valid;
    changed_source.source.cells[0].frame.signs[0] = -1;
    reject_apply(runtime, changed_source, PieceFailure::stale_candidate);
    commit(runtime, valid);
    for (int type = 0; type < 5; ++type) {
        auto descriptor = valid.inverse;
        if (type == 0)
            descriptor.version = "bad";
        if (type == 1)
            descriptor.source.object_ordinal++;
        if (type == 2)
            descriptor.source.cells[0].frame.signs[0] = -1;
        if (type == 3)
            descriptor.forward.delta *= -1;
        if (type == 4)
            descriptor.source.rest_cells[1].id = 8;
        const auto state = runtime.snapshot();
        require(!propose_piece_inverse(state.piece, state.revision, descriptor).candidate,
                "tampered inverse rejected");
        assert_atomic_noop(state, runtime.snapshot());
    }
    auto inverse =
        propose_piece_inverse(runtime.snapshot().piece, runtime.snapshot().revision, valid.inverse);
    auto forged_inverse = *inverse.candidate;
    forged_inverse.target.cells[0].coordinate.values[0]++;
    reject_apply(runtime, forged_inverse, PieceFailure::candidate_mismatch);
    undo(runtime, valid.inverse);
    context = "Retry and resource boundaries";
    auto old = proposal(runtime.snapshot(), {1, 1});
    commit(runtime, old);
    auto revision = runtime.snapshot().revision;
    require(runtime.retry() == PieceFailure::none, "Retry success");
    require(runtime.snapshot().revision == revision + 1 && runtime.snapshot().undo.empty(),
            "Retry monotonic/empty history baseline");
    assert_exact_semantic_recovery(base, runtime.snapshot().piece);
    reject_apply(runtime, old, PieceFailure::stale_candidate);
    for (int kind = 0; kind < 4; ++kind) {
        auto envelope = before;
        if (kind == 0)
            envelope.initial_piece.profile.dimensions[0]++;
        if (kind == 1)
            envelope.initial_piece.object_ordinal++;
        if (kind == 2)
            envelope.revision = std::numeric_limits<std::int64_t>::max();
        if (kind == 3)
            envelope.initial_piece.cells[0].frame.signs[0] = 0;
        ExplorerPieceRuntime rejected(envelope);
        const auto saved = rejected.snapshot();
        require(rejected.retry() ==
                    (kind == 2 ? PieceFailure::resource_limit : PieceFailure::invalid_piece_state),
                "Retry rejects incompatible/exhausted baseline");
        assert_atomic_noop(saved, rejected.snapshot());
        if (kind == 2) {
            auto forged = valid;
            forged.source_revision = envelope.revision;
            reject_apply(rejected, forged, PieceFailure::resource_limit);
            require(propose_piece_translation(base, envelope.revision, {0, 1}).failure ==
                        PieceFailure::resource_limit,
                    "exhausted proposal");
            ++rejected_translations;
            assert_atomic_noop(saved, rejected.snapshot());
        }
    }
    auto full_history = before;
    full_history.undo.resize(EXPLORER_MAX_UNDO, valid.inverse);
    ExplorerPieceRuntime full(full_history);
    reject_apply(full, valid, PieceFailure::resource_limit);
    // Equivalent authored labels, order and seam directions normalize before witnesses bind.
    auto equivalent = base;
    std::reverse(equivalent.profile.seams.begin(), equivalent.profile.seams.end());
    for (auto& seam : equivalent.profile.seams) {
        seam.id = "label_" + std::to_string(seam.source.axis);
        std::swap(seam.source, seam.target);
    }
    require(propose_piece_translation(equivalent, 0, {0, -1}).candidate ==
                propose_piece_translation(base, 0, {0, -1}).candidate,
            "canonical profile invariance");
    // Noncommuting frame composition protects the future twisted-seam extension architecture.
    require(compose_piece_frames({{0, 1}, {1, -1}}, {{1, 0}, {-1, 1}}) ==
                PieceFrame{{1, 0}, {1, 1}},
            "T F composition order");
}
void fixed_seed_sequences() {
    const std::vector<std::vector<CoordND>> shapes = {
        {{{0, 0}}},
        {{{0, 0}}, {{1, 0}}},
        {{{0, 0}}, {{1, 0}}, {{2, 0}}},
        {{{0, 0}}, {{1, 0}}, {{2, 0}}, {{3, 0}}},
        {{{0, 0}}, {{0, 1}}, {{1, 0}}},
        {{{0, 0}}, {{0, 1}}, {{0, 2}}, {{1, 0}}},
        {{{0, 0}}, {{1, 0}}, {{1, 1}}, {{2, 1}}},
        {{{0, 0}}, {{1, 0}}, {{1, 1}}, {{2, 0}}},
        {{{0, 0}}, {{0, 1}}, {{1, 1}}, {{2, 1}}, {{2, 2}}}};
    const std::array<std::array<int, 2>, 7> boards{
        {{1, 1}, {1, 3}, {2, 2}, {2, 3}, {4, 4}, {4, 5}, {8, 8}}};
    for (std::size_t shape = 0; shape < shapes.size(); ++shape)
        for (auto board : boards)
            for (int wrapped_axes : {0, 1, 2, 3}) {
                auto initial = make_piece(shapes[shape], board[0], board[1], wrapped_axes != 0);
                if (wrapped_axes == 1)
                    initial.profile.seams.pop_back();
                if (wrapped_axes == 2) {
                    initial.profile.seams.erase(initial.profile.seams.begin());
                    initial.profile.seams.front().id = "seam_000";
                }
                ExplorerPiece checked;
                if (validate_explorer_piece(initial, checked) != PieceFailure::none)
                    continue;
                for (int orientation = 0; orientation < 8; ++orientation)
                    for (std::uint32_t seed : {172U, 176U, 20261106U}) {
                        for (auto& cell : initial.cells)
                            cell.frame = {orientation & 4 ? std::vector<int>{1, 0}
                                                          : std::vector<int>{0, 1},
                                          {orientation & 1 ? -1 : 1, orientation & 2 ? -1 : 1}};
                        context =
                            "seed=" + std::to_string(seed) + " shape=" + std::to_string(shape) +
                            " board=" + std::to_string(board[0]) + "x" + std::to_string(board[1]) +
                            " wrapped_axes=" + std::to_string(wrapped_axes) +
                            " frame=" + std::to_string(orientation) + " actions=";
                        ++states;
                        ++sequences;
                        std::mt19937 random(seed);
                        ExplorerPieceRuntime runtime({0, initial, initial, {}});
                        std::vector<PieceInverse> history;
                        for (int step = 0; step < 32; ++step) {
                            const auto draw = random();
                            const MoveStepQuery action{static_cast<int>(draw % 2),
                                                       draw & 2 ? 1 : -1};
                            context +=
                                std::to_string(action.axis) + (action.delta > 0 ? "+," : "-,");
                            const auto before = runtime.snapshot();
                            assert_deterministic_proposal(before.piece, action);
                            auto result =
                                propose_piece_translation(before.piece, before.revision, action);
                            require(before == runtime.snapshot(), "sequence proposal pure");
                            if (!result.candidate) {
                                require((wrapped_axes & (1 << action.axis)) == 0 &&
                                            result.failure == PieceFailure::unconnected_boundary,
                                        "valid translation rejects only at bounded wall");
                                ++rejected_translations;
                                assert_atomic_noop(before, runtime.snapshot());
                                continue;
                            }
                            require(result.candidate->classification ==
                                        PieceClassification::plain_translation,
                                    "periodic coherent classification");
                            history.push_back(result.candidate->inverse);
                            commit(runtime, *result.candidate);
                        }
                        for (auto it = history.rbegin(); it != history.rend(); ++it)
                            undo(runtime, *it);
                        assert_exact_semantic_recovery(initial, runtime.snapshot().piece);
                        require(runtime.snapshot().undo.empty() &&
                                    runtime.snapshot().revision ==
                                        static_cast<std::int64_t>(2 * history.size()),
                                "sequence history/revision");
                    }
            }
}
void serialized_commit_and_boundaries() {
    context = "serialized competing commits";
    auto initial = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, true);
    initial.cells[0].coordinate = {{3, 3}};
    initial.cells[1].coordinate = {{0, 3}};
    initial.cells[1].frame = {{1, 0}, {-1, 1}};
    ExplorerPieceRuntime runtime({0, initial, initial, {}});
    const auto candidate = proposal(runtime.snapshot(), {0, 1});
    std::array<PieceFailure, 8> outcomes{};
    std::vector<std::thread> workers;
    for (std::size_t i = 0; i < outcomes.size(); ++i)
        workers.emplace_back([&, i] { outcomes[i] = runtime.apply(candidate); });
    for (auto& worker : workers)
        worker.join();
    require(std::count(outcomes.begin(), outcomes.end(), PieceFailure::none) == 1 &&
                std::count(outcomes.begin(), outcomes.end(), PieceFailure::stale_candidate) == 7,
            "one publication, seven stale competing requests");
    ++translations;
    auto committed = runtime.snapshot();
    require(committed.revision == 1 && committed.undo.size() == 1 &&
                committed.piece == candidate.target,
            "one complete envelope published");
    assert_piece_preserved(initial, committed.piece);
    undo(runtime, candidate.inverse);
    assert_exact_semantic_recovery(initial, runtime.snapshot().piece);

    context = "partially resolved bounded wall";
    auto bounded = make_piece({{{0, 0}}, {{1, 0}}}, 4, 4, false);
    bounded.cells[0].coordinate = {{2, 0}};
    bounded.cells[1].coordinate = {{3, 0}};
    ExplorerPieceRuntime wall({0, bounded, bounded, {}});
    auto before = wall.snapshot();
    auto rejected = propose_piece_translation(bounded, 0, {0, 1});
    require(!rejected.candidate && rejected.failure == PieceFailure::unconnected_boundary,
            "second cell blocks after first resolves");
    ++rejected_translations;
    assert_atomic_noop(before, wall.snapshot());

    context = "last representable revision";
    const auto last = std::numeric_limits<std::int64_t>::max();
    ExplorerPieceRuntime exhausted({last - 1, initial, initial, {}});
    const auto final_candidate = proposal(exhausted.snapshot(), {1, 1});
    commit(exhausted, final_candidate);
    auto final_state = exhausted.snapshot();
    require(final_state.revision == last, "last revision commits without overflow");
    require(propose_piece_inverse(final_state.piece, last, final_candidate.inverse).failure ==
                PieceFailure::resource_limit,
            "inverse cannot wrap revision");
    assert_atomic_noop(final_state, exhausted.snapshot());
    require(exhausted.retry() == PieceFailure::resource_limit, "Retry cannot wrap revision");
    assert_atomic_noop(final_state, exhausted.snapshot());
    // Semantic inverse remains reconstructible at an admissible revision; live exhaustion stays
    // final.
    auto recovered = propose_piece_inverse(final_state.piece, 0, final_candidate.inverse);
    require(recovered.candidate.has_value(), "recorded inverse is independent of old revision");
    assert_exact_semantic_recovery(initial, recovered.candidate->target);
}
} // namespace

int main() {
    fixture_cases();
    negative_cases();
    serialized_commit_and_boundaries();
    fixed_seed_sequences();
    std::cout << "explorer_piece_conformance: "
                 "{\"shapes\":9,\"boards\":7,\"topologies\":3,\"profile_variants\":4,\"frames\":8,"
                 "\"seeds\":[172,176,20261106],"
              << "\"initial_states\":" << states << ",\"successful_translations\":" << translations
              << ",\"rejected_translations\":" << rejected_translations
              << ",\"inverse_recoveries\":" << inverses << ",\"sequences\":" << sequences
              << ",\"atomic_rejections\":" << atomic_rejections << ",\"fixture_sha256\":\""
              << FIXTURE_SHA256 << "\"}\n";
}
