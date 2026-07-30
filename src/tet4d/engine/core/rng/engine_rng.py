from __future__ import annotations

import random

RNG_MODE_FIXED_SEED = "fixed_seed"
RNG_MODE_TRUE_RANDOM = "true_random"
RNG_MODE_OPTIONS = (RNG_MODE_FIXED_SEED, RNG_MODE_TRUE_RANDOM)


class EngineRNG(random.Random):
    """Seedable RNG wrapper with a stable engine-facing type."""

    def __init__(self, seed: float | str | bytes | bytearray | None = None) -> None:
        super().__init__(seed)

    def fork(self) -> EngineRNG:
        clone = EngineRNG()
        clone.setstate(self.getstate())
        return clone


def coerce_random(
    *,
    rng: random.Random | None = None,
    seed: float | str | bytes | bytearray | None = None,
) -> random.Random:
    if rng is not None and seed is not None:
        raise ValueError("provide either rng or seed, not both")
    if rng is not None:
        return rng
    return EngineRNG(seed)


def normalize_rng_mode(mode: str | None) -> str:
    if mode is None:
        return RNG_MODE_FIXED_SEED
    value = mode.strip().lower()
    if value in RNG_MODE_OPTIONS:
        return value
    raise ValueError(f"unsupported rng mode: {mode}")


__all__ = [
    "RNG_MODE_FIXED_SEED",
    "RNG_MODE_OPTIONS",
    "RNG_MODE_TRUE_RANDOM",
    "EngineRNG",
    "coerce_random",
    "normalize_rng_mode",
]
