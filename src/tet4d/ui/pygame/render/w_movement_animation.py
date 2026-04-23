from __future__ import annotations


def layer_transition_scale_for_distance(layer_distance: float) -> float:
    distance = max(0.0, float(layer_distance))
    if distance >= 1.0:
        return 0.0
    return 1.0 - distance


__all__ = ["layer_transition_scale_for_distance"]
