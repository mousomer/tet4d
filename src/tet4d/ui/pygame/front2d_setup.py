from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

import pygame

from tet4d.ai.playbot import run_dry_run_2d
from tet4d.ai.playbot.types import (
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from tet4d.engine.runtime.menu_settings_state import (
    default_mode_shared_gameplay_settings,
    get_overlay_transparency,
    mode_speedup_settings,
)
from tet4d.engine.gameplay.exploration_mode import minimal_exploration_dims_2d
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_OPTIONS, piece_set_2d_label
from tet4d.engine.gameplay.topology import topology_mode_from_index, topology_mode_label
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_NORMAL,
    designer_profile_label_for_index,
    designer_profiles_for_dimension,
    export_resolved_topology_profile,
    resolve_topology_designer_selection,
)
from tet4d.engine.runtime.topology_explorer_runtime import (
    resolve_direct_explorer_launch_profile,
)
from tet4d.engine.runtime.topology_profile_store import load_topology_profile
from tet4d.engine.runtime.menu_config import (
    default_settings_payload,
    kick_level_name_for_index,
    random_mode_id_from_index,
    random_mode_label_for_index,
    setup_fields_for_settings,
    setup_hints_for_dimension,
)
from tet4d.ui.pygame.keybindings import active_key_profile
from tet4d.ui.pygame.menu.menu_controls import FieldSpec
from tet4d.ui.pygame.menu.setup_menu_runner import run_setup_menu_loop
from tet4d.ui.pygame.render.gfx_game import GfxFonts, draw_menu

_DEFAULT_MODE_2D = default_settings_payload()["settings"]["2d"]
_MODE_GAMEPLAY_DEFAULTS = default_mode_shared_gameplay_settings("2d")
_AUTO_SPEEDUP_ENABLED_DEFAULT = int(_MODE_GAMEPLAY_DEFAULTS["auto_speedup_enabled"])
_LINES_PER_LEVEL_DEFAULT = int(_MODE_GAMEPLAY_DEFAULTS["lines_per_level"])


@dataclass
class GameSettings:
    width: int = _DEFAULT_MODE_2D["width"]
    height: int = _DEFAULT_MODE_2D["height"]
    random_mode_index: int = _DEFAULT_MODE_2D["random_mode_index"]
    game_seed: int = _DEFAULT_MODE_2D["game_seed"]
    piece_set_index: int = _DEFAULT_MODE_2D["piece_set_index"]
    topology_mode: int = _DEFAULT_MODE_2D["topology_mode"]
    topology_advanced: int = _DEFAULT_MODE_2D["topology_advanced"]
    topology_profile_index: int = _DEFAULT_MODE_2D["topology_profile_index"]
    kick_level_index: int = _DEFAULT_MODE_2D["kick_level_index"]
    bot_mode_index: int = _DEFAULT_MODE_2D["bot_mode_index"]
    bot_algorithm_index: int = _DEFAULT_MODE_2D["bot_algorithm_index"]
    bot_profile_index: int = _DEFAULT_MODE_2D["bot_profile_index"]
    bot_speed_level: int = _DEFAULT_MODE_2D["bot_speed_level"]
    bot_budget_ms: int = _DEFAULT_MODE_2D["bot_budget_ms"]
    challenge_layers: int = _DEFAULT_MODE_2D["challenge_layers"]
    exploration_mode: int = _DEFAULT_MODE_2D["exploration_mode"]
    speed_level: int = _DEFAULT_MODE_2D["speed_level"]


@dataclass
class MenuState:
    settings: GameSettings = field(default_factory=GameSettings)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False
    active_profile: str = field(default_factory=active_key_profile)
    rebind_mode: bool = False
    rebind_index: int = 0
    rebind_targets: list[tuple[str, str]] = field(default_factory=list)
    rebind_conflict_mode: str = "replace"
    run_dry_run: bool = False
    numeric_text_mode: bool = False
    numeric_text_attr_name: str = ""
    numeric_text_label: str = ""
    numeric_text_buffer: str = ""
    numeric_text_replace_on_type: bool = False


_TOPOLOGY_PROFILE_LABELS_2D = tuple(
    profile.label for profile in designer_profiles_for_dimension(2)
)


def menu_fields(settings: GameSettings) -> list[FieldSpec]:
    return setup_fields_for_settings(
        2,
        piece_set_max=len(PIECE_SET_2D_OPTIONS) - 1,
        topology_profile_max=max(0, len(_TOPOLOGY_PROFILE_LABELS_2D) - 1),
        topology_advanced=bool(settings.topology_advanced),
        exploration_mode=bool(settings.exploration_mode),
    )


def _freeze_play_menu_state(state: MenuState) -> None:
    state.settings.exploration_mode = 0


def _play_menu_settings(settings: GameSettings) -> GameSettings:
    return replace(
        settings,
        exploration_mode=0,
        topology_advanced=0,
        topology_profile_index=0,
    )


def piece_set_index_to_id(index: int) -> str:
    safe_index = max(0, min(len(PIECE_SET_2D_OPTIONS) - 1, int(index)))
    return PIECE_SET_2D_OPTIONS[safe_index]


def random_mode_index_to_id(index: int) -> str:
    return random_mode_id_from_index(index)


def random_mode_label(index: int) -> str:
    return random_mode_label_for_index(index)


def load_speedup_settings_for_mode(mode_key: str) -> tuple[int, int]:
    return mode_speedup_settings(mode_key)


def kick_level_name(index: int) -> str:
    return kick_level_name_for_index(index)


def load_overlay_transparency_for_runtime_2d() -> float:
    return get_overlay_transparency()


def menu_value_formatter(attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        return piece_set_2d_label(piece_set_index_to_id(int(value)))
    if attr_name == "random_mode_index":
        return random_mode_label(int(value))
    if attr_name == "game_seed":
        return str(max(0, int(value)))
    if attr_name == "topology_mode":
        return topology_mode_label(topology_mode_from_index(int(value)))
    if attr_name == "topology_advanced":
        return "ON" if int(value) else "OFF"
    if attr_name == "topology_profile_index":
        return designer_profile_label_for_index(2, int(value))
    if attr_name == "challenge_layers":
        return str(value)
    if attr_name == "exploration_mode":
        return "ON" if int(value) else "OFF"
    if attr_name == "speed_level":
        return f"{value}   (1 = slow, 10 = fast)"
    return str(value)


def config_from_settings(
    settings: GameSettings,
    *,
    explorer_topology_profile_override=None,
) -> GameConfig:
    piece_set_id = piece_set_index_to_id(settings.piece_set_index)
    topology_mode = topology_mode_from_index(settings.topology_mode)
    exploration_enabled = bool(settings.exploration_mode)
    explorer_topology_profile = None
    if bool(settings.topology_advanced) and not exploration_enabled:
        topology_profile = load_topology_profile(GAMEPLAY_MODE_NORMAL, 2)
        resolved_mode = topology_profile.topology_mode
        topology_edge_rules = topology_profile.edge_rules
    else:
        if exploration_enabled:
            resolved_mode, topology_edge_rules, explorer_topology_profile = (
                resolve_direct_explorer_launch_profile(
                    dimension=2,
                    gravity_axis=1,
                    topology_mode=topology_mode,
                    explorer_topology_profile_override=explorer_topology_profile_override,
                )
            )
        else:
            resolved_mode, topology_edge_rules, _legacy_profile = resolve_topology_designer_selection(
                dimension=2,
                gravity_axis=1,
                topology_mode=topology_mode,
                topology_advanced=bool(settings.topology_advanced),
                profile_index=settings.topology_profile_index,
                gameplay_mode="normal",
            )
    width = settings.width
    height = settings.height
    if exploration_enabled:
        width, height = minimal_exploration_dims_2d(
            piece_set_id,
            random_cell_count=4,
        )
    return GameConfig(
        width=width,
        height=height,
        gravity_axis=1,
        speed_level=settings.speed_level,
        topology_mode=resolved_mode,
        topology_edge_rules=topology_edge_rules,
        piece_set=piece_set_id,
        kick_level=kick_level_name(settings.kick_level_index),
        rng_mode=random_mode_index_to_id(settings.random_mode_index),
        rng_seed=max(0, int(settings.game_seed)),
        challenge_layers=0 if exploration_enabled else settings.challenge_layers,
        exploration_mode=exploration_enabled,
        explorer_topology_profile=explorer_topology_profile,
    )


def build_play_menu_config(settings: GameSettings) -> GameConfig:
    return config_from_settings(_play_menu_settings(settings))


def _run_dry_run(state: MenuState) -> None:
    report = run_dry_run_2d(
        build_play_menu_config(state.settings),
        planner_profile=bot_planner_profile_from_index(
            state.settings.bot_profile_index
        ),
        planning_budget_ms=state.settings.bot_budget_ms,
        planner_algorithm=bot_planner_algorithm_from_index(
            state.settings.bot_algorithm_index
        ),
    )
    state.bindings_status = report.reason
    state.bindings_status_error = not report.passed


def _export_topology_profile(state: MenuState) -> None:
    safe_settings = _play_menu_settings(state.settings)
    topology_mode = topology_mode_from_index(safe_settings.topology_mode)
    export_resolved_topology_profile(
        dimension=2,
        gravity_axis=1,
        topology_mode=topology_mode,
        topology_advanced=False,
        profile_index=0,
        gameplay_mode="normal",
    )


def run_menu(screen: pygame.Surface, fonts: GfxFonts) -> Optional[GameSettings]:
    state = MenuState()

    def _draw_frame(
        current_screen: pygame.Surface,
        current_state: MenuState,
        fields: list[FieldSpec],
    ) -> None:
        draw_menu(
            current_screen,
            fonts,
            current_state.settings,
            current_state.selected_index,
            bindings_file_hint=None,
            extra_hint_lines=tuple(setup_hints_for_dimension(2))
            or (
                "F7 dry-run verify (bot, no graphics)",
                "Use Main Menu -> Settings for Random type.",
                "Use Play -> Open Explorer Playground or Play Last Custom Topology for custom topology.",
                "Use Main Menu -> Bot Options / Keybindings for shared controls.",
            ),
            bindings_status=current_state.bindings_status,
            bindings_status_error=current_state.bindings_status_error,
            menu_fields=fields,
            value_formatter=menu_value_formatter,
        )

    result = run_setup_menu_loop(
        screen=screen,
        state=state,
        dimension=2,
        fields_for_state=menu_fields,
        draw_frame=_draw_frame,
        run_dry_run=_run_dry_run,
        on_start_saved=_export_topology_profile,
        after_load=_freeze_play_menu_state,
    )
    return result


__all__ = [
    "_AUTO_SPEEDUP_ENABLED_DEFAULT",
    "_LINES_PER_LEVEL_DEFAULT",
    "GameSettings",
    "MenuState",
    "build_play_menu_config",
    "config_from_settings",
    "kick_level_name",
    "load_overlay_transparency_for_runtime_2d",
    "load_speedup_settings_for_mode",
    "menu_fields",
    "menu_value_formatter",
    "piece_set_index_to_id",
    "run_menu",
]
