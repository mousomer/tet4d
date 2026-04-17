from __future__ import annotations

from tet4d.engine.gameplay.topology_designer import topology_gameplay_mode_label

from .copy import LAB_STATUS_COPY as _LAB_STATUS_COPY
from .interaction_audit import (
    record_interaction_handler,
    record_interaction_phase,
)
from .scene_preview_state import preview_signature_for_state as _preview_signature_for_state
from .scene_state import (
    TopologyLabState,
    current_explorer_profile,
    playground_dims_for_state,
    set_dirty,
    uses_general_explorer_editor,
)


def _board_dims_for_state(state: TopologyLabState) -> tuple[int, ...]:
    return playground_dims_for_state(state)


def save_profile(
    state: TopologyLabState,
    *,
    save_explorer_topology_profile,
    save_topology_profile,
    set_status,
) -> tuple[bool, str]:
    if uses_general_explorer_editor(state):
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = save_explorer_topology_profile(profile)
    else:
        ok, message = save_topology_profile(state.profile)
    if ok:
        set_dirty(state, False)
        set_status(
            state,
            str(_LAB_STATUS_COPY["saved"]).format(
                mode_label=topology_gameplay_mode_label(state.gameplay_mode),
                dimension=state.dimension,
            ),
        )
        return True, message
    set_status(
        state,
        str(_LAB_STATUS_COPY["save_failed"]).format(message=message),
        is_error=True,
    )
    return False, message


def run_export(
    state: TopologyLabState,
    *,
    export_explorer_topology_preview,
    export_topology_profile_state,
    play_sfx,
    set_status,
) -> None:
    with record_interaction_handler(
        state,
        "preview_export",
        dimension=state.dimension,
        gameplay_mode=state.gameplay_mode,
    ):
        if uses_general_explorer_editor(state):
            profile = current_explorer_profile(state)
            assert profile is not None
            if state.scene_preview_error is not None:
                set_status(state, state.scene_preview_error, is_error=True)
                return
            live_preview_payload = None
            export_signature = _preview_signature_for_state(state)
            if (
                export_signature is not None
                and state.scene_preview_signature == export_signature
                and state.scene_preview_error is None
                and state.scene_preview is not None
            ):
                live_preview_payload = state.scene_preview
            with record_interaction_phase(
                state,
                "preview_export_call",
                dimension=state.dimension,
                dims=_board_dims_for_state(state),
                glue_count=len(profile.gluings),
            ):
                ok, message, _path = export_explorer_topology_preview(
                    profile,
                    dims=_board_dims_for_state(state),
                    source=f"topology_lab_{state.dimension}d_mvp",
                    preview_payload=live_preview_payload,
                )
            if not ok:
                set_status(
                    state,
                    str(_LAB_STATUS_COPY["export_error"]).format(message=message),
                    is_error=True,
                )
                return
            set_status(
                state,
                str(_LAB_STATUS_COPY["export_ok"]).format(message=message),
            )
            play_sfx("menu_confirm")
            return

        with record_interaction_phase(
            state,
            "legacy_export_call",
            dimension=state.dimension,
            gameplay_mode=state.gameplay_mode,
        ):
            ok, message, _path = export_topology_profile_state(
                profile=state.profile,
                gravity_axis=1,
            )
        if not ok:
            set_status(
                state,
                str(_LAB_STATUS_COPY["export_error"]).format(message=message),
                is_error=True,
            )
            return

        set_status(
            state,
            str(_LAB_STATUS_COPY["export_ok"]).format(message=message),
        )
        play_sfx("menu_confirm")


def run_experiments(
    state: TopologyLabState,
    *,
    compile_runtime_explorer_experiments,
    export_runtime_explorer_experiments,
    play_sfx,
    set_status,
) -> None:
    with record_interaction_handler(
        state,
        "experiment_pack_generation",
        dimension=state.dimension,
        gameplay_mode=state.gameplay_mode,
    ):
        if not uses_general_explorer_editor(state):
            set_status(
                state,
                "Experiment packs are only available in Topology Playground",
                is_error=True,
            )
            return
        profile = current_explorer_profile(state)
        assert profile is not None
        if state.scene_preview_error is not None:
            set_status(state, state.scene_preview_error, is_error=True)
            return
        dims = _board_dims_for_state(state)
        with record_interaction_phase(
            state,
            "experiment_compile",
            dimension=state.dimension,
            dims=dims,
            glue_count=len(profile.gluings),
        ):
            batch = compile_runtime_explorer_experiments(
                profile,
                dims=dims,
                source=f"topology_lab_{state.dimension}d_experiments",
            )
        state.experiment_batch = batch
        with record_interaction_phase(
            state,
            "experiment_export",
            dimension=state.dimension,
            dims=dims,
            glue_count=len(profile.gluings),
        ):
            ok, message, _path = export_runtime_explorer_experiments(
                profile,
                dims=dims,
                source=f"topology_lab_{state.dimension}d_experiments",
                batch_payload=batch,
            )
        recommendation = batch.get("recommendation")
        if not ok:
            set_status(
                state,
                str(
                    _LAB_STATUS_COPY.get(
                        "experiments_error",
                        "Failed exporting explorer experiment pack: {message}",
                    )
                ).format(message=message),
                is_error=True,
            )
            return
        status = str(
            _LAB_STATUS_COPY.get(
                "experiments_ok",
                "Explorer experiment pack ready: {message}",
            )
        ).format(message=message)
        if isinstance(recommendation, dict):
            status += (
                f" | Next: {recommendation.get('label', 'n/a')}"
                f" ({recommendation.get('reason', 'no reason')})"
            )
        set_status(state, status)
        play_sfx("menu_confirm")
