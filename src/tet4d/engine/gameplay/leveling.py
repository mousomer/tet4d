from __future__ import annotations


def _clamp(value: int, *, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, int(value)))


def compute_speed_level(
    *,
    start_level: int,
    lines_cleared: int,
    enabled: bool,
    lines_per_level: int,
    min_level: int = 1,
    max_level: int = 10,
) -> int:
    start_level_clamped = _clamp(
        int(start_level),
        min_value=int(min_level),
        max_value=int(max_level),
    )
    if not bool(enabled):
        return start_level_clamped
    safe_lines_per_level = max(1, int(lines_per_level))
    safe_lines_cleared = max(0, int(lines_cleared))
    delta = safe_lines_cleared // safe_lines_per_level
    return _clamp(
        start_level_clamped + delta,
        min_value=int(min_level),
        max_value=int(max_level),
    )
