from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tet4d.engine import api


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
            "config": {
                "width": self.config.width,
                "height": self.config.height,
                "gravity_axis": self.config.gravity_axis,
                "speed_level": self.config.speed_level,
            },
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayScript2D":
        cfg_payload = payload["config"]
        cfg = api.GameConfig(
            width=int(cfg_payload["width"]),
            height=int(cfg_payload["height"]),
            gravity_axis=int(cfg_payload.get("gravity_axis", 1)),
            speed_level=int(cfg_payload.get("speed_level", 1)),
        )
        events = tuple(ReplayEvent2D.from_dict(item) for item in payload.get("events", ()))
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
            "config": {
                "dims": tuple(int(v) for v in self.config.dims),
                "gravity_axis": int(self.config.gravity_axis),
                "speed_level": int(self.config.speed_level),
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReplayTickScriptND":
        cfg_payload = payload["config"]
        cfg = api.GameConfigND(
            dims=tuple(int(v) for v in cfg_payload["dims"]),
            gravity_axis=int(cfg_payload.get("gravity_axis", 1)),
            speed_level=int(cfg_payload.get("speed_level", 1)),
        )
        return cls(seed=int(payload.get("seed", 0)), config=cfg, ticks=int(payload.get("ticks", 0)))
