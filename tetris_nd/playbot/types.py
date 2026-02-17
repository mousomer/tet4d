from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BotMode(str, Enum):
    OFF = "off"
    ASSIST = "assist"
    AUTO = "auto"
    STEP = "step"


BOT_MODE_OPTIONS: tuple[BotMode, ...] = (
    BotMode.OFF,
    BotMode.ASSIST,
    BotMode.AUTO,
    BotMode.STEP,
)


def bot_mode_label(mode: BotMode) -> str:
    return mode.value.upper()


def bot_mode_from_index(index: int) -> BotMode:
    safe_index = max(0, min(len(BOT_MODE_OPTIONS) - 1, int(index)))
    return BOT_MODE_OPTIONS[safe_index]


@dataclass(frozen=True)
class PlanStats:
    candidate_count: int
    expected_clears: int
    heuristic_score: float
    planning_ms: float


@dataclass(frozen=True)
class DryRunReport:
    passed: bool
    reason: str
    pieces_dropped: int
    clears_observed: int
    game_over: bool
