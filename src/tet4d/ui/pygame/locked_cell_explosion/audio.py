from __future__ import annotations

from .model import ExplosionAudioEvent, ExplosionAudioState

_FAMILY_EVENT_NAMES = {
    "bounce": ("explosion_bounce_soft", "explosion_bounce_dense"),
    "collision": ("explosion_collision_cluster", "explosion_collision_cluster"),
    "seam": ("explosion_seam_soft", "explosion_seam_dense"),
}
_FAMILY_COOLDOWN_MS = {
    "bounce": 120.0,
    "collision": 260.0,
    "seam": 75.0,
}


def aggregate_audio_events(
    raw_events: tuple[ExplosionAudioEvent, ...],
    *,
    elapsed_ms: float,
    sound_enabled: bool,
    state: ExplosionAudioState,
) -> tuple[str, ...]:
    if not sound_enabled or not raw_events:
        return tuple()
    family_counts: dict[str, int] = {}
    family_strengths: dict[str, float] = {}
    family_max_strengths: dict[str, float] = {}
    for event in raw_events:
        family = str(event.family)
        family_counts[family] = family_counts.get(family, 0) + 1
        strength = float(event.strength)
        family_strengths[family] = family_strengths.get(family, 0.0) + strength
        family_max_strengths[family] = max(
            family_max_strengths.get(family, 0.0),
            strength,
        )
    playback: list[str] = []
    for family in ("seam", "bounce", "collision"):
        count = family_counts.get(family, 0)
        if count <= 0:
            continue
        last_emit_ms = float(state.last_emit_ms_by_family.get(family, -10_000.0))
        if (float(elapsed_ms) - last_emit_ms) < float(_FAMILY_COOLDOWN_MS[family]):
            continue
        if family == "collision":
            strong_enough = (
                family_max_strengths.get(family, 0.0) >= 1.8
                or count >= 3
                or family_strengths.get(family, 0.0) >= 4.8
            )
            if not strong_enough:
                continue
            dense = True
        else:
            dense = count >= 3 or family_strengths.get(family, 0.0) >= 3.2
        playback.append(_FAMILY_EVENT_NAMES[family][1 if dense else 0])
        state.last_emit_ms_by_family[family] = float(elapsed_ms)
    return tuple(playback[:2])
