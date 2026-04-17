from __future__ import annotations

import pygame

from .interaction_audit import (
    record_interaction_handler,
    record_interaction_phase,
)
from .scene_preview_state import (
    ensure_explorer_playability_analysis as _ensure_explorer_playability_analysis,
    preview_signature_for_state as _preview_signature_for_state,
    refresh_explorer_scene_state as _refresh_explorer_scene_state,
)
from .scene_state import (
    TopologyLabState,
    canonical_playground_state,
    current_explorer_profile,
    playground_dims_for_state,
    sync_canonical_playground_state,
    uses_general_explorer_editor,
)


def _board_dims_for_state(state: TopologyLabState) -> tuple[int, ...]:
    return playground_dims_for_state(state)


def launch_play_preview(
    state: TopologyLabState,
    screen: pygame.Surface,
    fonts_nd,
    *,
    launch_playground_state_gameplay,
    set_status,
    display_title_for_state,
    fonts_2d=None,
    display_settings=None,
    exploration_mode=False,
) -> tuple[pygame.Surface, object | None]:
    profile = current_explorer_profile(state)
    with record_interaction_handler(
        state,
        "play_preview_launch",
        dimension=state.dimension,
        glue_count=0 if profile is None else len(profile.gluings),
    ):
        runtime_state = canonical_playground_state(state)
        if uses_general_explorer_editor(state):
            if runtime_state is None:
                with record_interaction_phase(
                    state,
                    "canonical_sync",
                    source="play_preview_launch",
                    dimension=state.dimension,
                ):
                    sync_canonical_playground_state(state)
                runtime_state = canonical_playground_state(state)
            expected_signature = _preview_signature_for_state(state)
            if runtime_state is not None and (
                state.scene_preview_signature != expected_signature
                or state.scene_preview_error is not None
            ):
                with record_interaction_phase(
                    state,
                    "scene_refresh",
                    source="play_preview_launch",
                    dimension=state.dimension,
                ):
                    _refresh_explorer_scene_state(state)
                runtime_state = canonical_playground_state(state)
        if not uses_general_explorer_editor(state) or runtime_state is None:
            set_status(
                state,
                "Play preview is unavailable until the canonical playground state is ready",
                is_error=True,
            )
            return screen, display_settings
        if state.scene_preview_error:
            set_status(
                state,
                f"Cannot play current topology: {state.scene_preview_error}",
                is_error=True,
            )
            return screen, display_settings
        with record_interaction_phase(
            state,
            "playability_analysis",
            source="play_preview_launch",
            dimension=state.dimension,
        ):
            _ensure_explorer_playability_analysis(state)
        try:
            with record_interaction_phase(
                state,
                "play_launch",
                dimension=state.dimension,
                dims=_board_dims_for_state(state),
                glue_count=len(runtime_state.explorer_profile.gluings),
            ):
                screen, display_settings = launch_playground_state_gameplay(
                    runtime_state,
                    screen,
                    fonts_nd,
                    return_caption=display_title_for_state(state),
                    fonts_2d=fonts_2d,
                    display_settings=display_settings,
                    exploration_mode=exploration_mode,
                )
        except Exception as exc:
            set_status(state, f"Play preview failed: {exc}", is_error=True)
            return screen, display_settings
        set_status(state, f"Returned from Explorer {state.dimension}D play preview")
        return screen, display_settings
