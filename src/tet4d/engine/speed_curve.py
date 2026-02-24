from __future__ import annotations

from .runtime_config import speed_curve_for_dimension


def gravity_interval_ms(speed_level: int, *, dimension: int) -> int:
    """
    Convert speed level (1..10) to gravity interval (ms), scaled by dimension.

    Higher dimensions start slower at the same speed level:
      - 2D: baseline
      - 3D: slower than 2D
      - 4D+: slower than 3D
    """
    level = max(1, min(10, int(speed_level)))

    base_ms, min_ms = speed_curve_for_dimension(dimension)

    return max(min_ms, base_ms // level)
