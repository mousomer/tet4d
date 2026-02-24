from __future__ import annotations

import random


class EngineRNG(random.Random):
    """Seedable RNG wrapper with a stable engine-facing type."""

    def __init__(self, seed: int | float | str | bytes | bytearray | None = None) -> None:
        super().__init__(seed)

    def fork(self) -> EngineRNG:
        clone = EngineRNG()
        clone.setstate(self.getstate())
        return clone


def coerce_random(
    *,
    rng: random.Random | None = None,
    seed: int | float | str | bytes | bytearray | None = None,
) -> random.Random:
    if rng is not None and seed is not None:
        raise ValueError("provide either rng or seed, not both")
    if rng is not None:
        return rng
    return EngineRNG(seed)


__all__ = ["EngineRNG", "coerce_random"]
