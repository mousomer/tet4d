from __future__ import annotations

from typing import Any

from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_EXPLORER
from tet4d.engine.runtime.api import topology_lab_menu_payload_runtime
from tet4d.engine.runtime.topology_profile_store import topology_profile_note

from .scene_state import uses_general_explorer_editor


def _safe_lab_payload() -> dict[str, Any]:
    fallback = {
        "title": "Explorer Playground",
        "subtitle": "Scene-first explorer playground with synchronized 2D coordinate-plane projections for live traversal, presets, sandbox play, and seam editing.",
        "hints": (
            "Up/Down select row",
            "Left/Right change values",
            "Enter triggers Save/Export/Back",
            "Normal Game locks Y boundaries",
            "Explorer Playground keeps presets, board size, seam editing, and play on one screen",
        ),
        "status_copy": {
            "saved": "Saved topology profile for {mode_label} {dimension}D",
            "save_failed": "Failed saving topology profile: {message}",
            "updated": "Topology profile updated (not saved yet)",
            "locked": "Y boundaries are fixed in Normal Game",
            "export_ok": "{message}",
            "export_error": "{message}",
        },
    }
    try:
        payload = topology_lab_menu_payload_runtime()
    except (OSError, ValueError, RuntimeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    return {
        "title": str(payload.get("title", fallback["title"])),
        "subtitle": str(payload.get("subtitle", fallback["subtitle"])),
        "hints": tuple(payload.get("hints", fallback["hints"])),
        "status_copy": dict(payload.get("status_copy", fallback["status_copy"])),
    }


_LAB_COPY = _safe_lab_payload()
LAB_TITLE = str(_LAB_COPY["title"])
LAB_SUBTITLE = str(_LAB_COPY["subtitle"])
LAB_HINTS = tuple(str(hint) for hint in _LAB_COPY["hints"])
LAB_STATUS_COPY = dict(_LAB_COPY["status_copy"])


def display_title_for_state(state: Any) -> str:
    if state.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
        return f"Explorer Playground {state.dimension}D"
    return f"{LAB_TITLE} (Legacy Compatibility)"


def topology_note_text(state: Any) -> str:
    if uses_general_explorer_editor(state):
        return (
            f"Explorer Playground {state.dimension}D is the live shell for seam editing, piece movement, probe traversal, and play from the current draft topology. "
            "For 3D and 4D, the primary scene now uses synchronized 2D coordinate-plane projections with explicit hidden-coordinate slices so selection and sandbox movement stay readable across panels."
        )
    return (
        "Legacy compatibility surface: retained Normal Game profile rows and the resolved-profile export bridge live here. "
        "Use Explorer Playground for the current seam editor, sandbox workflow, and direct play launch. "
        f"{topology_profile_note(state.gameplay_mode)}"
    )


__all__ = [
    "LAB_HINTS",
    "LAB_STATUS_COPY",
    "LAB_SUBTITLE",
    "LAB_TITLE",
    "display_title_for_state",
    "topology_note_text",
]
