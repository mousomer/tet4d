from __future__ import annotations


def scaled_span(
    axis_size: int,
    ratio: float,
    min_size: int,
    max_cap: int | None = None,
) -> int:
    clamped_axis = max(1, int(axis_size))
    scaled = max(min_size, int(round(clamped_axis * ratio)))
    scaled = min(scaled, clamped_axis)
    if max_cap is not None:
        scaled = min(scaled, max_cap)
    return max(1, scaled)

