from __future__ import annotations

from copy import deepcopy

import pytest

from tet4d.engine import api
from tet4d.replay import (
    REPLAY_SCHEMA_VERSION,
    ReplayFormatError,
    play_replay_2d,
    play_replay_nd_ticks,
    record_replay_2d,
    record_replay_nd_ticks,
)
from tet4d.replay.format import ReplayScript2D, ReplayTickScriptND


def _sig_2d(state: api.GameState2D) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (piece.shape.name, tuple(piece.pos), int(piece.rotation))
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        tuple(sorted(api.board_cells(state).items())),
        piece_sig,
        tuple(shape.name for shape in state.next_bag),
    )


def _sig_nd(state: api.GameStateND) -> tuple[object, ...]:
    piece = state.current_piece
    piece_sig = None
    if piece is not None:
        piece_sig = (
            piece.shape.name,
            tuple(piece.pos),
            tuple(sorted(piece.rel_blocks)),
        )
    return (
        state.score,
        state.lines_cleared,
        state.game_over,
        tuple(sorted(api.board_cells(state).items())),
        piece_sig,
        tuple(shape.name for shape in state.next_bag),
    )


def test_replay_2d_record_and_payload_roundtrip() -> None:
    cfg = api.GameConfig(
        width=8,
        height=16,
        speed_level=2,
        topology_mode="wrap_all",
        piece_set="debug_rectangles_2d",
        kick_level="light",
        random_cell_count=5,
        challenge_layers=2,
        lock_piece_points=9,
        rng_mode="fixed_seed",
        rng_seed=12345,
    )
    actions = (
        api.Action.MOVE_LEFT,
        api.Action.ROTATE_POSITIVE,
        api.Action.SOFT_DROP,
        api.Action.NONE,
    )
    script = record_replay_2d(config=cfg, seed=55, actions=actions)

    payload = script.to_dict()
    restored = ReplayScript2D.from_dict(payload)

    assert payload["replay_schema_version"] == REPLAY_SCHEMA_VERSION
    assert restored.seed == 55
    assert restored.config.width == cfg.width
    assert restored.config.topology_mode == cfg.topology_mode
    assert restored.config.wrap_gravity_axis == cfg.wrap_gravity_axis
    assert restored.config.piece_set == cfg.piece_set
    assert restored.config.kick_level == cfg.kick_level
    assert restored.config.random_cell_count == cfg.random_cell_count
    assert restored.config.challenge_layers == cfg.challenge_layers
    assert restored.config.lock_piece_points == cfg.lock_piece_points
    assert restored.config.exploration_mode == cfg.exploration_mode
    assert restored.config.rng_mode == cfg.rng_mode
    assert restored.config.rng_seed == cfg.rng_seed
    assert tuple(event.action for event in restored.events) == tuple(
        a.name for a in actions
    )


def test_replay_2d_playback_matches_direct_api_execution() -> None:
    cfg = api.GameConfig(width=8, height=16, speed_level=2)
    actions = (
        api.Action.MOVE_LEFT,
        api.Action.ROTATE_POSITIVE,
        api.Action.SOFT_DROP,
        api.Action.MOVE_RIGHT,
        api.Action.NONE,
        api.Action.ROTATE_NEGATIVE,
    )
    script = record_replay_2d(config=cfg, seed=101, actions=actions)

    direct = api.new_game_state_2d(cfg, seed=101)
    for action in actions:
        api.step_2d(direct, action)

    replayed = play_replay_2d(script)
    assert _sig_2d(replayed) == _sig_2d(direct)


def test_replay_nd_tick_playback_matches_direct_api_execution() -> None:
    cfg = api.GameConfigND(
        dims=(6, 14, 4),
        gravity_axis=1,
        speed_level=1,
        topology_mode="wrap_all",
        wrap_gravity_axis=True,
        piece_set_id="native_3d",
        kick_level="standard",
        random_cell_count=6,
        challenge_layers=2,
        lock_piece_points=11,
        exploration_mode=True,
        rng_mode="fixed_seed",
        rng_seed=98765,
    )
    script = record_replay_nd_ticks(config=cfg, seed=202, ticks=6)

    payload = script.to_dict()
    restored = ReplayTickScriptND.from_dict(payload)
    replayed = play_replay_nd_ticks(restored)
    assert payload["replay_schema_version"] == REPLAY_SCHEMA_VERSION
    assert restored.config.kick_level == cfg.kick_level
    assert restored.config.topology_mode == cfg.topology_mode
    assert restored.config.wrap_gravity_axis == cfg.wrap_gravity_axis
    assert restored.config.piece_set_id == cfg.piece_set_id
    assert restored.config.random_cell_count == cfg.random_cell_count
    assert restored.config.challenge_layers == cfg.challenge_layers
    assert restored.config.lock_piece_points == cfg.lock_piece_points
    assert restored.config.exploration_mode == cfg.exploration_mode
    assert restored.config.rng_mode == cfg.rng_mode
    assert restored.config.rng_seed == cfg.rng_seed

    direct = api.new_game_state_nd(cfg, seed=202)
    for _ in range(6):
        api.step_nd(direct)

    assert _sig_nd(replayed) == _sig_nd(direct)


def test_replay_loader_rejects_missing_required_fields_readably() -> None:
    payload = {
        "mode": "2d",
        "replay_schema_version": REPLAY_SCHEMA_VERSION,
        "seed": 7,
        "events": [],
    }

    with pytest.raises(ReplayFormatError, match="replay.config is required"):
        ReplayScript2D.from_dict(payload)


def test_replay_loader_rejects_unknown_top_level_fields() -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    payload["semantic_surprise"] = True

    with pytest.raises(ReplayFormatError, match="unknown field"):
        ReplayScript2D.from_dict(payload)


def test_replay_loader_rejects_unknown_semantic_config_fields() -> None:
    payload = record_replay_nd_ticks(
        config=api.GameConfigND(dims=(6, 12, 4), gravity_axis=1),
        seed=7,
        ticks=1,
    ).to_dict()
    payload["config"]["piece_set"] = "classic"

    with pytest.raises(ReplayFormatError, match="replay.config contains unknown"):
        ReplayTickScriptND.from_dict(payload)


def test_replay_loader_rejects_malformed_config_payload_readably() -> None:
    payload = record_replay_nd_ticks(
        config=api.GameConfigND(dims=(6, 12, 4), gravity_axis=1),
        seed=7,
        ticks=1,
    ).to_dict()
    payload["config"]["dims"] = "not-dimensions"

    with pytest.raises(ReplayFormatError, match="replay.config"):
        ReplayTickScriptND.from_dict(payload)


def test_replay_loader_rejects_missing_or_unknown_schema_version() -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    del payload["replay_schema_version"]

    with pytest.raises(ReplayFormatError, match="replay.replay_schema_version"):
        ReplayScript2D.from_dict(payload)

    payload["replay_schema_version"] = REPLAY_SCHEMA_VERSION + 1
    with pytest.raises(ReplayFormatError, match="not supported"):
        ReplayScript2D.from_dict(payload)


@pytest.mark.parametrize("near_miss", [True, 7.0, "7"])
def test_replay_loader_rejects_seed_near_misses(near_miss: object) -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    payload["seed"] = near_miss

    with pytest.raises(ReplayFormatError, match="replay.seed must be an integer"):
        ReplayScript2D.from_dict(payload)


@pytest.mark.parametrize("near_miss", [1, 0, "false", None])
def test_replay_loader_rejects_boolean_near_misses(near_miss: object) -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    payload["config"]["wrap_gravity_axis"] = near_miss

    with pytest.raises(ReplayFormatError, match="must be a boolean"):
        ReplayScript2D.from_dict(payload)


@pytest.mark.parametrize("near_miss", [True, 12.0, "12"])
def test_replay_loader_rejects_dimension_member_near_misses(
    near_miss: object,
) -> None:
    payload = record_replay_nd_ticks(
        config=api.GameConfigND(dims=(6, 12, 4), gravity_axis=1),
        seed=7,
        ticks=1,
    ).to_dict()
    payload["config"]["dims"][1] = near_miss

    with pytest.raises(ReplayFormatError, match="must be an integer"):
        ReplayTickScriptND.from_dict(payload)


@pytest.mark.parametrize(
    "malformed_rules",
    [
        "bounded",
        [["bounded"]],
        [["bounded", True], ["bounded", "bounded"]],
    ],
)
def test_replay_loader_rejects_malformed_edge_rules(
    malformed_rules: object,
) -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    payload["config"]["topology_edge_rules"] = malformed_rules

    with pytest.raises(ReplayFormatError, match="topology_edge_rules"):
        ReplayScript2D.from_dict(payload)


@pytest.mark.parametrize("near_miss", [1, True, None, "MOVE_SIDEWAYS"])
def test_replay_loader_rejects_invalid_actions(near_miss: object) -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(api.Action.NONE,),
    ).to_dict()
    payload["events"][0]["action"] = near_miss

    with pytest.raises(ReplayFormatError):
        ReplayScript2D.from_dict(payload)


def test_replay_loader_rejects_missing_current_config_field() -> None:
    payload = record_replay_2d(
        config=api.GameConfig(width=8, height=16),
        seed=7,
        actions=(),
    ).to_dict()
    del payload["config"]["rng_seed"]

    with pytest.raises(ReplayFormatError, match="missing required field"):
        ReplayScript2D.from_dict(payload)


@pytest.mark.parametrize("near_miss", [True, 7.0, "7"])
def test_replay_recorders_reject_seed_near_misses(near_miss: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        record_replay_2d(
            config=api.GameConfig(),
            seed=near_miss,
            actions=(),
        )

    with pytest.raises((TypeError, ValueError)):
        record_replay_nd_ticks(
            config=api.GameConfigND(),
            seed=near_miss,
            ticks=0,
        )


@pytest.mark.parametrize("near_miss", [True, -1, 1.0, "1"])
def test_replay_tick_recorder_rejects_invalid_ticks(near_miss: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        record_replay_nd_ticks(
            config=api.GameConfigND(),
            seed=7,
            ticks=near_miss,
        )


@pytest.mark.parametrize("near_miss", ["NONE", 0, None])
def test_replay_action_recorder_rejects_non_action_values(
    near_miss: object,
) -> None:
    with pytest.raises((TypeError, ValueError)):
        record_replay_2d(
            config=api.GameConfig(),
            seed=7,
            actions=(near_miss,),
        )


def test_replay_loader_rejects_one_malformed_event_without_partial_repair() -> None:
    payload = record_replay_2d(
        config=api.GameConfig(),
        seed=7,
        actions=(api.Action.NONE, api.Action.MOVE_LEFT),
    ).to_dict()
    malformed = deepcopy(payload)
    malformed["events"][1]["action"] = "MOVE_SIDEWAYS"

    with pytest.raises(ReplayFormatError, match="unsupported replay action"):
        ReplayScript2D.from_dict(malformed)

    assert ReplayScript2D.from_dict(payload).to_dict() == payload
