from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from tet4d.engine import api

REPLAY_SCHEMA_VERSION = 1


class ReplayFormatError(ValueError):
    """Raised when a replay payload does not match the accepted schema."""


def _json_safe_config_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe_config_value(item) for key, item in value.items()}
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
    if not isinstance(payload, dict):
        raise ReplayFormatError(f"{path} must be an object")
    return payload


def _require_int(payload: dict[str, Any], key: str, *, path: str) -> int:
    if key not in payload:
        raise ReplayFormatError(f"{path}.{key} is required")
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReplayFormatError(f"{path}.{key} must be an integer")
    return int(value)


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
    return dict(payload)


def _config_error(exc: Exception, *, path: str) -> ReplayFormatError:
    return ReplayFormatError(f"{path} is invalid: {exc}")


def _edge_rules_or_none(value: object) -> tuple[tuple[str, str], ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        return None
    return tuple(tuple(str(part) for part in rule) for rule in value)


def _game_config_2d_from_payload(payload: dict[str, Any]) -> api.GameConfig:
    kwargs = _validate_config_payload(
        payload,
        config_type=api.GameConfig,
        path="replay.config",
    )
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(
            kwargs["topology_edge_rules"]
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
    if "dims" in kwargs:
        try:
            kwargs["dims"] = tuple(int(v) for v in kwargs["dims"])
        except (TypeError, ValueError) as exc:
            raise _config_error(exc, path="replay.config.dims")
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(
            kwargs["topology_edge_rules"]
        )
    try:
        return api.GameConfigND(**kwargs)
    except (TypeError, ValueError) as exc:
        raise _config_error(exc, path="replay.config")


@dataclass(frozen=True)
class ReplayEvent2D:
    action: str

    def to_dict(self) -> dict[str, str]:
        return {"action": self.action}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayEvent2D":
        event = _require_object(payload, path="replay.events[]")
        _reject_unknown_fields(event, allowed={"action"}, path="replay.events[]")
        if "action" not in event:
            raise ReplayFormatError("replay.events[].action is required")
        return cls(action=str(event["action"]))


@dataclass(frozen=True)
class ReplayScript2D:
    seed: int
    config: api.GameConfig
    events: tuple[ReplayEvent2D, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "2d",
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "seed": int(self.seed),
            "config": _config_to_dict(self.config),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayScript2D":
        replay = _require_object(payload, path="replay")
        _reject_unknown_fields(
            replay,
            allowed={"mode", "replay_schema_version", "seed", "config", "events"},
            path="replay",
        )
        _require_schema_version(replay, path="replay")
        if replay.get("mode") != "2d":
            raise ReplayFormatError("replay.mode must be '2d'")
        cfg = _game_config_2d_from_payload(
            _require_config_payload(replay, path="replay")
        )
        if "events" not in replay:
            raise ReplayFormatError("replay.events is required")
        if not isinstance(replay["events"], list):
            raise ReplayFormatError("replay.events must be a list")
        events = tuple(ReplayEvent2D.from_dict(item) for item in replay["events"])
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "nd_ticks",
            "replay_schema_version": REPLAY_SCHEMA_VERSION,
            "seed": int(self.seed),
            "ticks": int(self.ticks),
            "config": _config_to_dict(self.config),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayTickScriptND":
        replay = _require_object(payload, path="replay")
        _reject_unknown_fields(
            replay,
            allowed={"mode", "replay_schema_version", "seed", "ticks", "config"},
            path="replay",
        )
        _require_schema_version(replay, path="replay")
        if replay.get("mode") != "nd_ticks":
            raise ReplayFormatError("replay.mode must be 'nd_ticks'")
        cfg = _game_config_nd_from_payload(
            _require_config_payload(replay, path="replay")
        )
        return cls(
            seed=_require_int(replay, "seed", path="replay"),
            config=cfg,
            ticks=_require_int(replay, "ticks", path="replay"),
        )
