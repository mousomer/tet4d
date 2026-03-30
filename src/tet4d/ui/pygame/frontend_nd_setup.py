from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional, Tuple

import pygame

from tet4d.ui.pygame.render.font_profiles import (
    GfxFonts,
    init_fonts as init_fonts_for_profile,
)
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.runtime.api import active_key_profile_runtime
from tet4d.ui.pygame.menu.menu_controls import FieldSpec
from tet4d.engine.runtime.menu_config import (
    default_settings_payload,
    kick_level_name_for_index,
    random_mode_id_from_index,
    random_mode_label_for_index,
    setup_fields_for_settings,
    setup_hints_for_dimension,
    ui_copy_section,
)
from tet4d.ui.pygame.menu.menu_keybinding_shortcuts import menu_binding_status_color
from tet4d.ui.pygame.menu.setup_menu_runner import run_setup_menu_loop
from tet4d.engine.gameplay.pieces_nd import (
    piece_set_label,
    piece_set_options_for_dimension,
)
from tet4d.engine.gameplay.exploration_mode import minimal_exploration_dims_nd
from tet4d.ai.playbot import run_dry_run_nd
from tet4d.ai.playbot.types import (
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from tet4d.engine.gameplay.speed_curve import gravity_interval_ms
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
from tet4d.engine.topology_explorer.transport_resolver import (
    build_explorer_transport_resolver,
)
from tet4d.engine.runtime.topology_profile_store import load_topology_profile
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text


TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0)
RANDOM_MODE_FIXED_INDEX = 0
RANDOM_MODE_TRUE_RANDOM_INDEX = 1
_DEFAULT_MODE_4D = default_settings_payload()["settings"]["4d"]
_SETUP_MENU_COPY = ui_copy_section("setup_menu")


def init_fonts() -> GfxFonts:
    return init_fonts_for_profile("nd")


def draw_gradient_background(
    surface: pygame.Surface,
    top_color: Tuple[int, int, int],
    bottom_color: Tuple[int, int, int],
) -> None:
    draw_vertical_gradient(surface, top_color, bottom_color)


@dataclass
class GameSettingsND:
    width: int = _DEFAULT_MODE_4D["width"]
    height: int = _DEFAULT_MODE_4D["height"]
    depth: int = _DEFAULT_MODE_4D["depth"]
    fourth: int = _DEFAULT_MODE_4D["fourth"]
    speed_level: int = _DEFAULT_MODE_4D["speed_level"]
    random_mode_index: int = _DEFAULT_MODE_4D["random_mode_index"]
    game_seed: int = _DEFAULT_MODE_4D["game_seed"]
    piece_set_index: int = _DEFAULT_MODE_4D["piece_set_index"]
    topology_mode: int = _DEFAULT_MODE_4D["topology_mode"]
    topology_advanced: int = _DEFAULT_MODE_4D["topology_advanced"]
    topology_profile_index: int = _DEFAULT_MODE_4D.get("topology_profile_index", 0)
    kick_level_index: int = _DEFAULT_MODE_4D["kick_level_index"]
    bot_mode_index: int = _DEFAULT_MODE_4D["bot_mode_index"]
    bot_algorithm_index: int = _DEFAULT_MODE_4D["bot_algorithm_index"]
    bot_profile_index: int = _DEFAULT_MODE_4D["bot_profile_index"]
    bot_speed_level: int = _DEFAULT_MODE_4D["bot_speed_level"]
    bot_budget_ms: int = _DEFAULT_MODE_4D["bot_budget_ms"]
    challenge_layers: int = _DEFAULT_MODE_4D["challenge_layers"]
    exploration_mode: int = _DEFAULT_MODE_4D["exploration_mode"]


_PIECE_SET_CHOICES = {
    3: tuple(piece_set_options_for_dimension(3)),
    4: tuple(piece_set_options_for_dimension(4)),
}
_PIECE_SET_LABELS = {
    dimension: tuple(piece_set_label(piece_set_id) for piece_set_id in choices)
    for dimension, choices in _PIECE_SET_CHOICES.items()
}
_TOPOLOGY_PROFILE_LABELS = {
    dimension: tuple(
        profile.label for profile in designer_profiles_for_dimension(dimension)
    )
    for dimension in (2, 3, 4)
}


def _piece_set_index_to_id(dimension: int, index: int) -> str:
    choices = _PIECE_SET_CHOICES.get(dimension, _PIECE_SET_CHOICES[4])
    safe_index = max(0, min(len(choices) - 1, int(index)))
    return choices[safe_index]


def _random_mode_index_to_id(index: int) -> str:
    return random_mode_id_from_index(index)


def _random_mode_label(index: int) -> str:
    return random_mode_label_for_index(index)


def _kick_level_name(index: int) -> str:
    return kick_level_name_for_index(index)


def piece_set_4d_label(piece_set_4d: str) -> str:
    return piece_set_label(piece_set_4d)


@dataclass
class MenuState:
    settings: GameSettingsND = field(default_factory=GameSettingsND)
    selected_index: int = 0
    running: bool = True
    start_game: bool = False
    bindings_status: str = ""
    bindings_status_error: bool = False
    active_profile: str = field(default_factory=active_key_profile_runtime)
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


def menu_fields_for_settings(
    settings: GameSettingsND, dimension: int
) -> list[FieldSpec]:
    choices = _PIECE_SET_CHOICES.get(dimension)
    piece_set_max = 0 if choices is None else max(0, len(choices) - 1)
    topology_profile_max = max(0, len(_TOPOLOGY_PROFILE_LABELS.get(dimension, ())) - 1)
    return setup_fields_for_settings(
        dimension,
        piece_set_max=piece_set_max,
        topology_profile_max=topology_profile_max,
        topology_advanced=bool(settings.topology_advanced),
        exploration_mode=bool(settings.exploration_mode),
    )


def _freeze_play_menu_state(state: MenuState) -> None:
    state.settings.exploration_mode = 0


def _play_menu_settings(settings: GameSettingsND) -> GameSettingsND:
    return replace(
        settings,
        exploration_mode=0,
        topology_advanced=0,
        topology_profile_index=0,
    )


def _menu_value_text(dimension: int, attr_name: str, value: object) -> str:
    if attr_name == "piece_set_index":
        labels = _PIECE_SET_LABELS.get(dimension, _PIECE_SET_LABELS[4])
        safe_index = max(0, min(len(labels) - 1, int(value)))
        return labels[safe_index]
    if attr_name == "random_mode_index":
        return _random_mode_label(int(value))
    if attr_name == "game_seed":
        return str(max(0, int(value)))
    if attr_name == "topology_mode":
        return topology_mode_label(topology_mode_from_index(int(value)))
    if attr_name == "topology_advanced":
        return "ON" if int(value) else "OFF"
    if attr_name == "topology_profile_index":
        return designer_profile_label_for_index(dimension, int(value))
    if attr_name == "exploration_mode":
        return "ON" if int(value) else "OFF"
    return str(value)


def draw_menu(
    screen: pygame.Surface, fonts: GfxFonts, state: MenuState, dimension: int
) -> None:
    draw_gradient_background(screen, (15, 15, 60), (2, 2, 20))
    width, height = screen.get_size()
    fields = menu_fields_for_settings(state.settings, dimension)

    title_text = _SETUP_MENU_COPY["title_template"].format(dimension=dimension)
    subtitle_text = fit_text(
        fonts.hint_font,
        _SETUP_MENU_COPY["subtitle_template"],
        width - 28,
    )

    title_surf = fonts.title_font.render(title_text, True, TEXT_COLOR)
    subtitle_surf = fonts.hint_font.render(subtitle_text, True, (200, 200, 220))

    title_y = 48
    title_x = (width - title_surf.get_width()) // 2
    screen.blit(title_surf, (title_x, title_y))
    subtitle_y = title_y + title_surf.get_height() + 8
    subtitle_x = (width - subtitle_surf.get_width()) // 2
    screen.blit(subtitle_surf, (subtitle_x, subtitle_y))

    panel_w = min(max(360, int(width * 0.65)), width - 24)
    hint_line_h = fonts.hint_font.get_height() + 4
    bottom_lines = 4 + (1 if state.bindings_status else 0)
    panel_top = subtitle_y + subtitle_surf.get_height() + 12
    panel_max_h = max(140, height - panel_top - (bottom_lines * hint_line_h) - 10)
    row_h = min(
        44,
        max(
            fonts.menu_font.get_height() + 8, (panel_max_h - 40) // max(1, len(fields))
        ),
    )
    panel_h = min(panel_max_h, 40 + len(fields) * row_h)
    panel_x = (width - panel_w) // 2
    panel_y = max(
        panel_top,
        min(
            (height - panel_h) // 2, height - panel_h - (bottom_lines * hint_line_h) - 8
        ),
    )

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(
        panel_surf, (0, 0, 0, 140), panel_surf.get_rect(), border_radius=16
    )
    screen.blit(panel_surf, (panel_x, panel_y))

    y = panel_y + 20
    option_x = panel_x + 24
    option_w = panel_w - 48
    option_bottom = panel_y + panel_h - 10
    for idx, (label, attr_name, _, _) in enumerate(fields):
        if y + fonts.menu_font.get_height() > option_bottom:
            break
        value = getattr(state.settings, attr_name)
        value_text = _menu_value_text(dimension, attr_name, value)
        text = f"{label}: {value_text}"
        selected = idx == state.selected_index
        txt_color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        text_fit = fit_text(fonts.menu_font, text, option_w - 6)
        text_surf = fonts.menu_font.render(text_fit, True, txt_color)
        text_rect = text_surf.get_rect(topleft=(option_x, y))
        if selected:
            highlight_rect = pygame.Rect(
                option_x - 8, y - 4, option_w + 16, text_rect.height + 10
            )
            highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(
                highlight_surf,
                (255, 255, 255, 40),
                highlight_surf.get_rect(),
                border_radius=10,
            )
            screen.blit(highlight_surf, highlight_rect.topleft)
        screen.blit(text_surf, text_rect.topleft)
        y += row_h

    hint_lines = list(setup_hints_for_dimension(dimension))
    hint_y = panel_y + panel_h + 8
    max_hint_lines = max(1, (height - hint_y - 6) // max(1, hint_line_h))
    hint_budget = max(1, max_hint_lines - (1 if state.bindings_status else 0))
    for line in hint_lines[:hint_budget]:
        line_fit = fit_text(fonts.hint_font, line, width - 28)
        surf = fonts.hint_font.render(line_fit, True, (210, 210, 230))
        hint_x = (width - surf.get_width()) // 2
        screen.blit(surf, (hint_x, hint_y))
        hint_y += surf.get_height() + 4

    if state.bindings_status and hint_y + hint_line_h <= height - 6:
        status_color = menu_binding_status_color(state.bindings_status_error)
        status_text = fit_text(fonts.hint_font, state.bindings_status, width - 28)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        status_x = (width - status_surf.get_width()) // 2
        screen.blit(status_surf, (status_x, hint_y))


def _run_dry_run(state: MenuState, dimension: int) -> None:
    report = run_dry_run_nd(
        build_play_menu_config(state.settings, dimension),
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


def _export_topology_profile(state: MenuState, dimension: int) -> None:
    safe_settings = _play_menu_settings(state.settings)
    topology_mode = topology_mode_from_index(safe_settings.topology_mode)
    export_resolved_topology_profile(
        dimension=dimension,
        gravity_axis=1,
        topology_mode=topology_mode,
        topology_advanced=False,
        profile_index=0,
    )


def run_menu(
    screen: pygame.Surface, fonts: GfxFonts, dimension: int
) -> Optional[GameSettingsND]:
    state = MenuState()
    return run_setup_menu_loop(
        screen=screen,
        state=state,
        dimension=dimension,
        fields_for_state=lambda settings: menu_fields_for_settings(settings, dimension),
        draw_frame=lambda current_screen, current_state, _fields: draw_menu(
            current_screen,
            fonts,
            current_state,
            dimension,
        ),
        run_dry_run=lambda current_state: _run_dry_run(current_state, dimension),
        on_start_saved=lambda current_state: _export_topology_profile(
            current_state, dimension
        ),
        after_load=_freeze_play_menu_state,
    )


def build_config(
    settings: GameSettingsND,
    dimension: int,
    *,
    explorer_topology_profile_override=None,
) -> GameConfigND:
    piece_set_id = _piece_set_index_to_id(dimension, settings.piece_set_index)
    topology_mode = topology_mode_from_index(settings.topology_mode)
    exploration_enabled = bool(settings.exploration_mode)
    explorer_topology_profile = None
    if bool(settings.topology_advanced) and dimension >= 3 and not exploration_enabled:
        topology_profile = load_topology_profile(GAMEPLAY_MODE_NORMAL, dimension)
        resolved_mode = topology_profile.topology_mode
        topology_edge_rules = topology_profile.edge_rules
    else:
        if exploration_enabled:
            resolved_mode, topology_edge_rules, explorer_topology_profile = (
                resolve_direct_explorer_launch_profile(
                    dimension=dimension,
                    gravity_axis=1,
                    topology_mode=topology_mode,
                    explorer_topology_profile_override=explorer_topology_profile_override,
                )
            )
        else:
            resolved_mode, topology_edge_rules, _legacy_profile = (
                resolve_topology_designer_selection(
                    dimension=dimension,
                    gravity_axis=1,
                    topology_mode=topology_mode,
                    topology_advanced=bool(settings.topology_advanced),
                    profile_index=settings.topology_profile_index,
                    gameplay_mode=GAMEPLAY_MODE_NORMAL,
                )
            )
    dims = [settings.width, settings.height]
    if dimension >= 3:
        dims.append(settings.depth)
    if dimension >= 4:
        dims.append(settings.fourth)
    if exploration_enabled:
        dims = list(minimal_exploration_dims_nd(dimension, piece_set_id))
    explorer_transport = None
    if explorer_topology_profile is not None:
        explorer_transport = build_explorer_transport_resolver(
            explorer_topology_profile,
            tuple(dims),
        )
    return GameConfigND(
        dims=tuple(dims),
        gravity_axis=1,
        speed_level=settings.speed_level,
        topology_mode=resolved_mode,
        topology_edge_rules=topology_edge_rules,
        explorer_topology_profile=explorer_topology_profile,
        explorer_transport=explorer_transport,
        piece_set_id=piece_set_id,
        kick_level=_kick_level_name(settings.kick_level_index),
        rng_mode=_random_mode_index_to_id(settings.random_mode_index),
        rng_seed=max(0, int(settings.game_seed)),
        challenge_layers=0 if exploration_enabled else settings.challenge_layers,
        exploration_mode=exploration_enabled,
    )


def build_play_menu_config(
    settings: GameSettingsND,
    dimension: int,
) -> GameConfigND:
    return build_config(_play_menu_settings(settings), dimension)


def gravity_interval_ms_from_config(cfg: GameConfigND) -> int:
    return gravity_interval_ms(cfg.speed_level, dimension=max(2, cfg.ndim))
