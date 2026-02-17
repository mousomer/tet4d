from __future__ import annotations


def gravity_interval_ms(speed_level: int, *, dimension: int) -> int:
    """
    Convert speed level (1..10) to gravity interval (ms), scaled by dimension.

    Higher dimensions start slower at the same speed level:
      - 2D: baseline
      - 3D: slower than 2D
      - 4D+: slower than 3D
    """
    level = max(1, min(10, int(speed_level)))

    if dimension <= 2:
        base_ms = 1000
        min_ms = 80
    elif dimension == 3:
        base_ms = 1350
        min_ms = 110
    else:
        base_ms = 1700
        min_ms = 140

    return max(min_ms, base_ms // level)
