from __future__ import annotations

from tet4d.engine.runtime.topology_cache import (
    read_cached_playability_analysis,
    write_cached_playability_analysis,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    basis_arrow_payload,
    compile_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_playability_signal import (
    update_topology_playability_analysis,
)

from .common import boundaries_for_dimension
from .scene_state import (
    ExplorerPlayabilityArtifacts,
    ExplorerPreviewCompileArtifacts,
    ExplorerPreviewCompileSignature,
    TopologyLabState,
    canonical_playground_state,
    current_explorer_profile,
    playground_dims_for_state,
    uses_general_explorer_editor,
)


def clear_explorer_scene_state(state: TopologyLabState) -> None:
    state.scene_boundaries = ()
    state.scene_preview_dims = ()
    state.scene_active_glue_ids = {}
    state.scene_basis_arrows = ()
    state.scene_preview = None
    state.scene_preview_error = None
    state.scene_preview_signature = None
    state.scene_preview_cache = None
    state.scene_playability_cache = None
    state.scene_pending_playability_signature = None
    state.scene_pending_playability_delay_frames = 0
    state.experiment_batch = None


def preview_signature_for_state(
    state: TopologyLabState,
) -> ExplorerPreviewCompileSignature | None:
    profile = current_explorer_profile(state)
    if profile is None:
        return None
    return ExplorerPreviewCompileSignature(
        profile=profile,
        dims=tuple(int(value) for value in playground_dims_for_state(state)),
    )


def _compile_explorer_preview_payload(
    signature: ExplorerPreviewCompileSignature,
) -> tuple[dict[str, object] | None, str | None]:
    try:
        from . import controls_panel as controls_panel_module

        compile_preview = getattr(
            controls_panel_module,
            "compile_explorer_topology_preview",
            compile_explorer_topology_preview,
        )
        return (
            compile_preview(
                signature.profile,
                dims=signature.dims,
                source="topology_lab_live_preview",
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _preview_compile_artifacts(
    state: TopologyLabState,
    *,
    signature: ExplorerPreviewCompileSignature,
) -> ExplorerPreviewCompileArtifacts:
    cached = state.scene_preview_cache
    if cached is not None and cached.signature == signature:
        return cached
    preview, preview_error = _compile_explorer_preview_payload(signature)
    artifacts = ExplorerPreviewCompileArtifacts(
        signature=signature,
        preview=preview,
        preview_error=preview_error,
    )
    state.scene_preview_cache = artifacts
    return artifacts


def _cached_playability_artifacts(
    state: TopologyLabState,
    *,
    signature: ExplorerPreviewCompileSignature,
) -> ExplorerPlayabilityArtifacts | None:
    cached = state.scene_playability_cache
    if cached is None or cached.signature != signature:
        return None
    return cached


def _apply_playability_analysis(
    state: TopologyLabState,
    *,
    signature: ExplorerPreviewCompileSignature,
    include_rigid_scan: bool,
) -> None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        state.scene_pending_playability_signature = None
        state.scene_pending_playability_delay_frames = 0
        return
    if include_rigid_scan:
        cached = _cached_playability_artifacts(state, signature=signature)
        if cached is not None:
            runtime_state.playability_analysis = cached.analysis
            state.scene_pending_playability_signature = None
            state.scene_pending_playability_delay_frames = 0
            return
        persistent = read_cached_playability_analysis(
            signature.profile,
            dims=signature.dims,
        )
        if persistent is not None:
            runtime_state.playability_analysis = persistent
            state.scene_playability_cache = ExplorerPlayabilityArtifacts(
                signature=signature,
                analysis=persistent,
            )
            state.scene_pending_playability_signature = None
            state.scene_pending_playability_delay_frames = 0
            return
    analysis = update_topology_playability_analysis(
        runtime_state,
        preview=state.scene_preview,
        preview_error=state.scene_preview_error,
        include_rigid_scan=include_rigid_scan,
    )
    if include_rigid_scan:
        state.scene_playability_cache = ExplorerPlayabilityArtifacts(
            signature=signature,
            analysis=analysis,
        )
        try:
            write_cached_playability_analysis(
                signature.profile,
                dims=signature.dims,
                analysis=analysis,
            )
        except OSError:
            pass
        state.scene_pending_playability_signature = None
        state.scene_pending_playability_delay_frames = 0
        return
    state.scene_pending_playability_signature = signature
    state.scene_pending_playability_delay_frames = 1


def refresh_explorer_scene_state(state: TopologyLabState) -> None:
    if not uses_general_explorer_editor(state):
        clear_explorer_scene_state(state)
        return
    signature = preview_signature_for_state(state)
    if signature is None:
        clear_explorer_scene_state(state)
        return
    boundaries = boundaries_for_dimension(signature.profile.dimension)
    active_glue_ids = {boundary.label: "free" for boundary in boundaries}
    for glue in signature.profile.gluings:
        active_glue_ids[glue.source.label] = glue.glue_id
        active_glue_ids[glue.target.label] = glue.glue_id
    state.scene_boundaries = boundaries
    state.scene_preview_dims = signature.dims
    state.scene_active_glue_ids = active_glue_ids
    if state.scene_preview_signature != signature:
        state.experiment_batch = None
    state.scene_preview_signature = signature
    cached = state.scene_preview_cache
    if cached is not None and cached.signature == signature:
        state.scene_preview = cached.preview
        state.scene_preview_error = cached.preview_error
        state.scene_basis_arrows = (
            ()
            if cached.preview is None
            else tuple(cached.preview.get("basis_arrows", ()))
        )
        if _cached_playability_artifacts(state, signature=signature) is not None:
            _apply_playability_analysis(
                state,
                signature=signature,
                include_rigid_scan=True,
            )
            return
        _apply_playability_analysis(
            state,
            signature=signature,
            include_rigid_scan=False,
        )
        return
    preview_artifacts = _preview_compile_artifacts(state, signature=signature)
    state.scene_preview = preview_artifacts.preview
    state.scene_preview_error = preview_artifacts.preview_error
    state.scene_basis_arrows = (
        tuple(basis_arrow_payload(signature.profile))
        if preview_artifacts.preview is None
        else tuple(preview_artifacts.preview.get("basis_arrows", ()))
    )
    _apply_playability_analysis(
        state,
        signature=signature,
        include_rigid_scan=False,
    )


def advance_pending_explorer_playability_analysis(state: TopologyLabState) -> None:
    signature = state.scene_pending_playability_signature
    if signature is None:
        return
    if state.scene_preview_signature != signature:
        state.scene_pending_playability_signature = None
        state.scene_pending_playability_delay_frames = 0
        return
    if state.scene_pending_playability_delay_frames > 0:
        state.scene_pending_playability_delay_frames -= 1
        return
    _apply_playability_analysis(
        state,
        signature=signature,
        include_rigid_scan=True,
    )


def ensure_explorer_playability_analysis(state: TopologyLabState) -> None:
    signature = state.scene_preview_signature
    if signature is None:
        return
    _apply_playability_analysis(
        state,
        signature=signature,
        include_rigid_scan=True,
    )
