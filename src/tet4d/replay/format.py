from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from tet4d.engine import api


def _json_safe_config_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, list):
        return [_json_safe_config_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_safe_config_value(item) for key, item in value.items()
        }
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"Replay config field is not JSON-serializable: {type(value)!r}")


def _config_to_dict(config: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(config):
        value = getattr(config, field.name)
        payload[field.name] = _json_safe_config_value(value)
    return payload


def _edge_rules_or_none(value: object) -> tuple[tuple[str, str], ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        return None
    return tuple(tuple(str(part) for part in rule) for rule in value)


def _game_config_2d_from_payload(payload: dict[str, Any]) -> api.GameConfig:
    kwargs = dict(payload)
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(kwargs["topology_edge_rules"])
    return api.GameConfig(**kwargs)


def _game_config_nd_from_payload(payload: dict[str, Any]) -> api.GameConfigND:
    kwargs = dict(payload)
    if "dims" in kwargs:
        kwargs["dims"] = tuple(int(v) for v in kwargs["dims"])
    if "topology_edge_rules" in kwargs:
        kwargs["topology_edge_rules"] = _edge_rules_or_none(kwargs["topology_edge_rules"])
    return api.GameConfigND(**kwargs)


@dataclass(frozen=True)
class ReplayEvent2D:
    action: str

    def to_dict(self) -> dict[str, str]:
        return {"action": self.action}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayEvent2D":
        return cls(action=str(payload["action"]))


@dataclass(frozen=True)
class ReplayScript2D:
    seed: int
    config: api.GameConfig
    events: tuple[ReplayEvent2D, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "2d",
            "seed": int(self.seed),
            "config": _config_to_dict(self.config),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayScript2D":
        cfg_payload = payload["config"]
        cfg = _game_config_2d_from_payload(dict(cfg_payload))
        events = tuple(
            ReplayEvent2D.from_dict(item) for item in payload.get("events", ())
        )
        return cls(seed=int(payload.get("seed", 0)), config=cfg, events=events)


@dataclass(frozen=True)
class ReplayTickScriptND:
    seed: int
    config: api.GameConfigND
    ticks: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "nd_ticks",
            "seed": int(self.seed),
            "ticks": int(self.ticks),
            "config": _config_to_dict(self.config),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayTickScriptND":
        cfg_payload = payload["config"]
        cfg = _game_config_nd_from_payload(dict(cfg_payload))
        return cls(
            seed=int(payload.get("seed", 0)),
            config=cfg,
            ticks=int(payload.get("ticks", 0)),
        )
