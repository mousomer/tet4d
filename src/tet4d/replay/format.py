from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from tet4d.engine import api
from tet4d.engine.topology_explorer.domain_validation import (
    require_instance,
    require_instance_sequence,
    require_integral,
    require_non_negative_integral,
    require_string,
)

REPLAY_SCHEMA_VERSION = 1


class ReplayFormatError(ValueError):
    """Raised when a replay payload does not match the accepted schema."""


def _json_safe_config_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("Replay config mapping keys must be strings")
        return {key: _json_safe_config_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Replay config field is not JSON-serializable: {type(value)!r}")


def _config_to_dict(config: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(config):
        value = getattr(config, field.name)
        payload[field.name] = _json_safe_config_value(value)
    return payload


def _require_object(payload: Any, *, path: str) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ReplayFormatError(f"{path} must be an object")
    return payload


def _require_list(payload: Any, *, path: str) -> list[Any]:
    if type(payload) is not list:
        raise ReplayFormatError(f"{path} must be a list")
    return payload


def _require_int(payload: dict[str, Any], key: str, *, path: str) -> int:
    if key not in payload:
        raise ReplayFormatError(f"{path}.{key} is required")
    value = payload[key]
    if type(value) is not int:
        raise ReplayFormatError(f"{path}.{key} must be an integer")
    return value


def _require_string_value(value: object, *, path: str) -> str:
    if type(value) is not str:
        raise ReplayFormatError(f"{path} must be a string")
    return value


def _require_bool_value(value: object, *, path: str) -> bool:
    if type(value) is not bool:
        raise ReplayFormatError(f"{path} must be a boolean")
    return value


def _require_schema_version(payload: dict[str, Any], *, path: str) -> None:
    version = _require_int(payload, "replay_schema_version", path=path)
    if version != REPLAY_SCHEMA_VERSION:
        raise ReplayFormatError(
            f"{path}.replay_schema_version {version!r} is not supported; "
            f"expected {REPLAY_SCHEMA_VERSION}"
        )


def _reject_unknown_fields(
    payload: dict[str, Any],
    *,
    allowed: set[str],
    path: str,
) -> None:
    if any(type(key) is not str for key in payload):
        raise ReplayFormatError(f"{path} field names must be strings")
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ReplayFormatError(
            f"{path} contains unknown field(s): {', '.join(unknown)}"
        )


def _require_config_payload(payload: dict[str, Any], *, path: str) -> dict[str, Any]:
    if "config" not in payload:
        raise ReplayFormatError(f"{path}.config is required")
    return _require_object(payload["config"], path=f"{path}.config")


def _config_field_names(config_type: type[Any]) -> set[str]:
    return {field.name for field in fields(config_type)}


def _validate_config_payload(
    payload: dict[str, Any],
    *,
    config_type: type[Any],
    path: str,
) -> dict[str, Any]:
    allowed = _config_field_names(config_type)
    _reject_unknown_fields(payload, allowed=allowed, path=path)
    missing = sorted(allowed - set(payload))
    if missing:
        raise ReplayFormatError(
            f"{path} is missing required field(s): {', '.join(missing)}"
        )
    return dict(payload)


def _config_error(exc: Exception, *, path: str) -> ReplayFormatError:
    return ReplayFormatError(f"{path} is invalid: {exc}")


def _edge_rules_or_none(
    value: object,
    *,
    path: str,
) -> tuple[tuple[str, str], ...] | None:
    if value is None:
        return None
    rules = _require_list(value, path=path)
    normalized: list[tuple[str, str]] = []
    for axis, raw_rule in enumerate(rules):
        rule_path = f"{path}[{axis}]"
        rule = _require_list(raw_rule, path=rule_path)
        if len(rule) != 2:
            raise ReplayFormatError(f"{rule_path} must contain two edge behaviors")
        normalized.append(
            (
                _require_string_value(rule[0], path=f"{rule_path}[0]"),
                _require_string_value(rule[1], path=f"{rule_path}[1]"),
            )
        )
    return tuple(normalized)


_CONFIG_INT_FIELDS = frozenset(
    {
        "width",
        "height",
        "gravity_axis",
        "speed_level",
        "random_cell_count",
        "challenge_layers",
        "lock_piece_points",
        "rng_seed",
    }
)
_CONFIG_BOOL_FIELDS = frozenset({"wrap_gravity_axis", "exploration_mode"})
_CONFIG_STRING_FIELDS = frozenset(
    {"topology_mode", "piece_set", "kick_level", "rng_mode", "piece_set_4d"}
)


def _validate_current_config_scalars(
    payload: dict[str, Any],
    *,
    path: str,
) -> None:
    for key in _CONFIG_INT_FIELDS.intersection(payload):
        _require_int(payload, key, path=path)
    for key in _CONFIG_BOOL_FIELDS.intersection(payload):
        _require_bool_value(payload[key], path=f"{path}.{key}")
    for key in _CONFIG_STRING_FIELDS.intersection(payload):
        _require_string_value(payload[key], path=f"{path}.{key}")
    rigid_play = payload.get("explorer_rigid_play_enabled")
    if rigid_play is not None:
        _require_bool_value(rigid_play, path=f"{path}.explorer_rigid_play_enabled")
    piece_set_id = payload.get("piece_set_id")
    if piece_set_id is not None:
        _require_string_value(piece_set_id, path=f"{path}.piece_set_id")
    for key in ("explorer_topology_profile", "explorer_transport"):
        if payload.get(key) is not None:
            raise ReplayFormatError(f"{path}.{key} is not supported in replay v1")


def _game_config_2d_from_payload(payload: dict[str, Any]) -> api.GameConfig:
    kwargs = _validate_config_payload(
        payload,
        config_type=api.GameConfig,
        path="replay.config",
    )
    _validate_current_config_scalars(kwargs, path="replay.config")
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(
            kwargs["topology_edge_rules"],
            path="replay.config.topology_edge_rules",
        )
    try:
        return api.GameConfig(**kwargs)
    except (TypeError, ValueError) as exc:
        raise _config_error(exc, path="replay.config")


def _game_config_nd_from_payload(payload: dict[str, Any]) -> api.GameConfigND:
    kwargs = _validate_config_payload(
        payload,
        config_type=api.GameConfigND,
        path="replay.config",
    )
    _validate_current_config_scalars(kwargs, path="replay.config")
    if "dims" in kwargs:
        raw_dims = _require_list(kwargs["dims"], path="replay.config.dims")
        dims_payload = {str(index): value for index, value in enumerate(raw_dims)}
        kwargs["dims"] = tuple(
            _require_int(dims_payload, str(index), path="replay.config.dims")
            for index in range(len(raw_dims))
        )
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(
            kwargs["topology_edge_rules"],
            path="replay.config.topology_edge_rules",
        )
    try:
        return api.GameConfigND(**kwargs)
    except (TypeError, ValueError) as exc:
        raise _config_error(exc, path="replay.config")


@dataclass(frozen=True)
class ReplayEvent2D:
    action: str

    def __post_init__(self) -> None:
        action = require_string(self.action, "replay event action")
        if action not in api.Action.__members__:
            raise ValueError(f"unsupported replay action: {action!r}")
        object.__setattr__(self, "action", action)

    def to_dict(self) -> dict[str, str]:
        return {"action": self.action}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReplayEvent2D:
        event = _require_object(payload, path="replay.events[]")
        _reject_unknown_fields(event, allowed={"action"}, path="replay.events[]")
        if "action" not in event:
            raise ReplayFormatError("replay.events[].action is required")
        action = _require_string_value(
            event["action"],
            path="replay.events[].action",
        )
        try:
            return cls(action=action)
        except ValueError as exc:
            raise ReplayFormatError(str(exc)) from exc


@dataclass(frozen=True)
class ReplayScript2D:
    seed: int
    config: api.GameConfig
    events: tuple[ReplayEvent2D, ...]

    def __post_init__(self) -> None:
        seed = require_integral(self.seed, "replay seed")
        config = require_instance(self.config, "replay config", api.GameConfig)
        events = require_instance_sequence(
            self.events,
            "replay events",
            ReplayEvent2D,
        )
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "config", config)
        object.__setattr__(self, "events", events)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "2d",
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "seed": self.seed,
            "config": _config_to_dict(self.config),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReplayScript2D:
        replay = _require_object(payload, path="replay")
        _reject_unknown_fields(
            replay,
            allowed={"mode", "replay_schema_version", "seed", "config", "events"},
            path="replay",
        )
        _require_schema_version(replay, path="replay")
        mode = _require_string_value(replay.get("mode"), path="replay.mode")
        if mode != "2d":
            raise ReplayFormatError("replay.mode must be '2d'")
        cfg = _game_config_2d_from_payload(
            _require_config_payload(replay, path="replay")
        )
        if "events" not in replay:
            raise ReplayFormatError("replay.events is required")
        events_payload = _require_list(replay["events"], path="replay.events")
        events = tuple(ReplayEvent2D.from_dict(item) for item in events_payload)
        return cls(
            seed=_require_int(replay, "seed", path="replay"),
            config=cfg,
            events=events,
        )


@dataclass(frozen=True)
class ReplayTickScriptND:
    seed: int
    config: api.GameConfigND
    ticks: int

    def __post_init__(self) -> None:
        seed = require_integral(self.seed, "replay seed")
        ticks = require_non_negative_integral(self.ticks, "replay ticks")
        config = require_instance(self.config, "replay config", api.GameConfigND)
        object.__setattr__(self, "seed", seed)
        object.__setattr__(self, "ticks", ticks)
        object.__setattr__(self, "config", config)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "nd_ticks",
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "seed": self.seed,
            "ticks": self.ticks,
            "config": _config_to_dict(self.config),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ReplayTickScriptND:
        replay = _require_object(payload, path="replay")
        _reject_unknown_fields(
            replay,
            allowed={"mode", "replay_schema_version", "seed", "ticks", "config"},
            path="replay",
        )
        _require_schema_version(replay, path="replay")
        mode = _require_string_value(replay.get("mode"), path="replay.mode")
        if mode != "nd_ticks":
            raise ReplayFormatError("replay.mode must be 'nd_ticks'")
        cfg = _game_config_nd_from_payload(
            _require_config_payload(replay, path="replay")
        )
        return cls(
            seed=_require_int(replay, "seed", path="replay"),
            config=cfg,
            ticks=_require_int(replay, "ticks", path="replay"),
        )
