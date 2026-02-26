from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .core.model import (
    Action,
    BoardND,
    GameConfig2DCoreView,
    GameConfigNDCoreView,
    GameState2DCoreView,
    GameStateNDCoreView,
)
from .core.rules.state_queries import (
    board_cells as core_board_cells,
    current_piece_cells as core_current_piece_cells,
    is_game_over as core_is_game_over,
)
from .core.step.reducer import step_2d as core_step_2d
from .core.step.reducer import step_nd as core_step_nd
from .gameplay.game2d import GameConfig, GameState
from .gameplay.game_nd import GameConfigND, GameStateND
from .gameplay.pieces2d import (
    PIECE_SET_2D_CLASSIC,
    PIECE_SET_2D_DEBUG,
    ActivePiece2D,
    PieceShape2D,
    rotate_point_2d,
)
from .gameplay.pieces_nd import (
    ActivePieceND,
    PIECE_SET_3D_DEBUG,
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_DEBUG,
    PIECE_SET_4D_STANDARD,
    PieceShapeND,
    rotate_point_nd,
)
from tet4d.ai.playbot.types import (
    BOT_MODE_OPTIONS,
    BOT_PLANNER_ALGORITHM_OPTIONS,
    BOT_PLANNER_PROFILE_OPTIONS,
    BotMode,
    BotPlannerAlgorithm,
    BotPlannerProfile,
    DryRunReport,
    bot_mode_from_index,
    bot_mode_label,
    bot_planner_algorithm_from_index,
    bot_planner_algorithm_label,
    bot_planner_profile_from_index,
    bot_planner_profile_label,
    default_planning_budget_ms,
)
from .core.rng import EngineRNG, coerce_random
from .runtime.runtime_config import (
    playbot_benchmark_history_file,
    playbot_benchmark_p95_thresholds,
)
from .runtime.project_config import project_constant_int as _project_constant_int
from .ui_logic.view_modes import GridMode

if TYPE_CHECKING:  # pragma: no cover
    from tet4d.ai.playbot import PlayBotController as PlayBotController


# Stable aliases for callers that want explicit dimensional naming.
Action2D = Action
GameConfig2D = GameConfig
GameState2D = GameState


def new_game_state_2d(
    config: GameConfig,
    *,
    board: BoardND | None = None,
    rng: random.Random | None = None,
    seed: int | None = None,
) -> GameState:
    rng = coerce_random(rng=rng, seed=seed)
    if board is None:
        board = BoardND((config.width, config.height))
    return GameState(config=config, board=board, rng=rng)


def new_game_state_nd(
    config: GameConfigND,
    *,
    board: BoardND | None = None,
    rng: random.Random | None = None,
    seed: int | None = None,
) -> GameStateND:
    rng = coerce_random(rng=rng, seed=seed)
    if board is None:
        board = BoardND(config.dims)
    return GameStateND(config=config, board=board, rng=rng)


def new_rng(seed: int | float | str | bytes | bytearray | None = None) -> EngineRNG:
    return EngineRNG(seed)


def plan_best_2d_move(
    state: GameState,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> Any:
    from tet4d.ai.playbot.planner_2d import plan_best_2d_move as _plan_best_2d_move

    return _plan_best_2d_move(
        state,
        profile=profile,
        budget_ms=budget_ms,
        algorithm=algorithm,
    )


def plan_best_nd_move(
    state: GameStateND,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> Any:
    from tet4d.ai.playbot.planner_nd import plan_best_nd_move as _plan_best_nd_move

    return _plan_best_nd_move(
        state,
        profile=profile,
        budget_ms=budget_ms,
        algorithm=algorithm,
    )


def plan_best_nd_with_budget(
    state: GameStateND,
    *,
    profile: BotPlannerProfile,
    planning_budget_ms: int,
    algorithm: BotPlannerAlgorithm,
) -> Any:
    from tet4d.ai.playbot.planner_nd_search import (
        plan_best_nd_with_budget as _plan_best_nd_with_budget,
    )

    return _plan_best_nd_with_budget(
        state,
        profile=profile,
        planning_budget_ms=planning_budget_ms,
        algorithm=algorithm,
    )


def simulate_lock_board(
    state: GameStateND, piece: Any
) -> tuple[dict[tuple[int, ...], int], int, bool]:
    from tet4d.ai.playbot.planner_nd_core import simulate_lock_board as _simulate_lock_board

    return _simulate_lock_board(state, piece)


def playbot_rotation_planes_nd(
    ndim: int, gravity_axis: int
) -> tuple[tuple[int, int], ...]:
    from tet4d.ai.playbot.planner_nd_core import rotation_planes as _rotation_planes

    return _rotation_planes(ndim, gravity_axis)


def playbot_canonical_blocks_nd(blocks: Any) -> tuple[tuple[int, ...], ...]:
    from tet4d.ai.playbot.planner_nd_core import canonical_blocks as _canonical_blocks

    return _canonical_blocks(blocks)


def playbot_enumerate_orientations_nd(
    start_blocks: tuple[tuple[int, ...], ...],
    ndim: int,
    gravity_axis: int,
) -> tuple[tuple[tuple[int, ...], ...], ...]:
    from tet4d.ai.playbot.planner_nd_core import (
        enumerate_orientations as _enumerate_orientations,
    )

    return _enumerate_orientations(start_blocks, ndim, gravity_axis)


def playbot_build_column_levels_nd(
    cells: dict[tuple[int, ...], int],
    *,
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
) -> dict[tuple[int, ...], list[int]]:
    from tet4d.ai.playbot.planner_nd_core import (
        build_column_levels as _build_column_levels,
    )

    return _build_column_levels(
        cells,
        lateral_axes=lateral_axes,
        gravity_axis=gravity_axis,
    )


def playbot_evaluate_nd_board(
    cells: dict[tuple[int, ...], int],
    dims: tuple[int, ...],
    gravity_axis: int,
    cleared: int,
    game_over: bool,
) -> float:
    from tet4d.ai.playbot.planner_nd_core import evaluate_nd_board as _evaluate_nd_board

    return _evaluate_nd_board(
        cells,
        dims,
        gravity_axis,
        cleared,
        game_over,
    )


def playbot_default_hard_drop_after_soft_drops_runtime() -> int:
    from .runtime.runtime_config import (
        playbot_default_hard_drop_after_soft_drops as _soft_drop_default,
    )

    return _soft_drop_default()


def greedy_key_4d(
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    cleared: int,
    game_over: bool,
) -> tuple[int, int, int, int]:
    from tet4d.ai.playbot.planner_nd_core import greedy_key_4d as _greedy_key_4d

    return _greedy_key_4d(
        cells,
        dims=dims,
        gravity_axis=gravity_axis,
        cleared=cleared,
        game_over=game_over,
    )


def playbot_greedy_score_4d(greedy_key: tuple[int, int, int, int]) -> float:
    from tet4d.ai.playbot.planner_nd_core import greedy_score_4d as _greedy_score_4d

    return _greedy_score_4d(greedy_key)


def playbot_iter_settled_candidates_nd(
    state: GameStateND,
    *,
    piece: ActivePieceND,
    orientations: tuple[tuple[tuple[int, ...], ...], ...],
    ndim: int,
    dims: tuple[int, ...],
    gravity_axis: int,
    lateral_axes: tuple[int, ...],
    column_levels: dict[tuple[int, ...], list[int]],
) -> Any:
    from tet4d.ai.playbot.planner_nd_core import (
        iter_settled_candidates as _iter_settled_candidates,
    )

    return _iter_settled_candidates(
        state,
        piece=piece,
        orientations=orientations,
        ndim=ndim,
        dims=dims,
        gravity_axis=gravity_axis,
        lateral_axes=lateral_axes,
        column_levels=column_levels,
    )


def apply_challenge_prefill_2d(state: GameState, *, layers: int) -> None:
    from .gameplay.challenge_mode import apply_challenge_prefill_2d as _apply

    _apply(state, layers=layers)


def apply_challenge_prefill_nd(state: GameStateND, *, layers: int) -> None:
    from .gameplay.challenge_mode import apply_challenge_prefill_nd as _apply

    _apply(state, layers=layers)


def playbot_dry_run_defaults() -> tuple[int, int]:
    from .runtime.runtime_config import playbot_dry_run_defaults as _defaults

    return _defaults()


def run_dry_run_2d(
    cfg: GameConfig,
    *,
    max_pieces: int = 64,
    seed: int = 1337,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    from tet4d.ai.playbot.dry_run import run_dry_run_2d as _run_dry_run_2d

    return _run_dry_run_2d(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=planner_profile,
        planning_budget_ms=planning_budget_ms,
        planner_algorithm=planner_algorithm,
    )


def run_dry_run_nd(
    cfg: GameConfigND,
    *,
    max_pieces: int = 64,
    seed: int = 1337,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    from tet4d.ai.playbot.dry_run import run_dry_run_nd as _run_dry_run_nd

    return _run_dry_run_nd(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=planner_profile,
        planning_budget_ms=planning_budget_ms,
        planner_algorithm=planner_algorithm,
    )


def step_2d(state: GameState, action: Action = Action.NONE) -> GameState:
    return core_step_2d(state, action)


def step_nd(state: GameStateND) -> GameStateND:
    return core_step_nd(state)


def step(
    state: GameState | GameStateND, action: Action | None = None
) -> GameState | GameStateND:
    if isinstance(state, GameState):
        return core_step_2d(state, Action.NONE if action is None else action)
    if action is not None:
        raise TypeError("ND engine step does not accept a 2D Action")
    return core_step_nd(state)


def legal_actions_2d(_: GameState | None = None) -> tuple[Action, ...]:
    del _
    return tuple(Action)


def legal_actions(state: GameState | GameStateND) -> tuple[Action, ...]:
    if isinstance(state, GameState):
        return legal_actions_2d(state)
    return ()


def board_cells(state: GameState | GameStateND) -> dict[tuple[int, ...], int]:
    return core_board_cells(state)


def current_piece_cells(
    state: GameState | GameStateND, *, include_above: bool = False
) -> tuple[tuple[int, ...], ...]:
    return core_current_piece_cells(state, include_above=include_above)


def is_game_over(state: GameState | GameStateND) -> bool:
    return core_is_game_over(state)


def config_view_2d(config: GameConfig) -> GameConfig2DCoreView:
    return config.to_core_view()


def state_view_2d(state: GameState) -> GameState2DCoreView:
    return state.to_core_view()


def config_view_nd(config: GameConfigND) -> GameConfigNDCoreView:
    return config.to_core_view()


def state_view_nd(state: GameStateND) -> GameStateNDCoreView:
    return state.to_core_view()


def project_constant_int(
    path: tuple[str, ...],
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    return _project_constant_int(
        path,
        default,
        min_value=min_value,
        max_value=max_value,
    )


def project_root_path():
    from .runtime.project_config import project_root_path as _project_root_path

    return _project_root_path()


def keybindings_dir_path_runtime() -> Path:
    from .runtime.project_config import keybindings_dir_path as _keybindings_dir_path

    return _keybindings_dir_path()


def keybindings_profiles_dir_path_runtime() -> Path:
    from .runtime.project_config import (
        keybindings_profiles_dir_path as _keybindings_profiles_dir_path,
    )

    return _keybindings_profiles_dir_path()


def keybindings_load_json_file_runtime(path: Path) -> Any:
    from .runtime.keybindings_storage import load_json_file as _load_json_file

    return _load_json_file(path)


def keybindings_atomic_write_text_runtime(path: Path, payload: str) -> None:
    from .runtime.keybindings_storage import atomic_write_text as _atomic_write_text

    _atomic_write_text(path, payload)


def keybindings_copy_text_file_runtime(src_path: Path, dst_path: Path) -> None:
    from .runtime.keybindings_storage import copy_text_file as _copy_text_file

    _copy_text_file(src_path, dst_path)


def open_display_runtime(*args: Any, **kwargs: Any) -> Any:
    from tet4d.ui.pygame.app_runtime import open_display as _open_display

    return _open_display(*args, **kwargs)


def capture_windowed_display_settings_runtime(display_settings: Any) -> Any:
    from tet4d.ui.pygame.app_runtime import (
        capture_windowed_display_settings as _capture_windowed_display_settings,
    )

    return _capture_windowed_display_settings(display_settings)


def advance_gravity_runtime(state: Any, accumulator_ms: int, gravity_interval_ms: int) -> int:
    from .runtime.runtime_helpers import advance_gravity as _advance_gravity

    return _advance_gravity(state, accumulator_ms, gravity_interval_ms)


def tick_animation_runtime(animation: Any, dt_ms: int) -> Any:
    from .runtime.runtime_helpers import tick_animation as _tick_animation

    return _tick_animation(animation, dt_ms)


def initialize_keybinding_files_runtime() -> None:
    from tet4d.ui.pygame.keybindings import initialize_keybinding_files as _initialize_keybinding_files

    _initialize_keybinding_files()


def get_audio_settings_runtime() -> dict[str, Any]:
    from .runtime.menu_settings_state import get_audio_settings as _get_audio_settings

    return _get_audio_settings()


def get_display_settings_runtime() -> dict[str, Any]:
    from .runtime.menu_settings_state import get_display_settings as _get_display_settings

    return _get_display_settings()


def get_analytics_settings_runtime() -> dict[str, Any]:
    from .runtime.menu_settings_state import (
        get_analytics_settings as _get_analytics_settings,
    )

    return _get_analytics_settings()


def save_display_settings_runtime(*, windowed_size: tuple[int, int]) -> None:
    from .runtime.menu_settings_state import save_display_settings as _save_display_settings

    _save_display_settings(windowed_size=windowed_size)


def set_score_analyzer_logging_enabled_runtime(enabled: bool | None) -> None:
    from .runtime.score_analyzer import (
        set_score_analyzer_logging_enabled as _set_score_analyzer_logging_enabled,
    )

    _set_score_analyzer_logging_enabled(enabled)


def settings_hub_layout_rows_runtime():
    from .runtime.menu_config import settings_hub_layout_rows as _settings_hub_layout_rows

    return _settings_hub_layout_rows()


def settings_top_level_categories_runtime():
    from .runtime.menu_config import (
        settings_top_level_categories as _settings_top_level_categories,
    )

    return _settings_top_level_categories()


def default_settings_payload_runtime():
    from .runtime.menu_config import default_settings_payload as _default_settings_payload

    return _default_settings_payload()


def load_analytics_payload_runtime():
    from .runtime.menu_persistence import (
        load_analytics_payload as _load_analytics_payload,
    )

    return _load_analytics_payload()


def persist_audio_payload_runtime(*, master_volume: float, sfx_volume: float, mute: bool):
    from .runtime.menu_persistence import persist_audio_payload as _persist_audio_payload

    return _persist_audio_payload(
        master_volume=master_volume,
        sfx_volume=sfx_volume,
        mute=mute,
    )


def persist_display_payload_runtime(*, fullscreen: bool, windowed_size: tuple[int, int]):
    from .runtime.menu_persistence import (
        persist_display_payload as _persist_display_payload,
    )

    return _persist_display_payload(
        fullscreen=fullscreen,
        windowed_size=windowed_size,
    )


def persist_analytics_payload_runtime(*, score_logging_enabled: bool):
    from .runtime.menu_persistence import (
        persist_analytics_payload as _persist_analytics_payload,
    )

    return _persist_analytics_payload(score_logging_enabled=score_logging_enabled)


def default_windowed_size_runtime() -> tuple[int, int]:
    from .runtime.menu_settings_state import DEFAULT_WINDOWED_SIZE as _DEFAULT_WINDOWED_SIZE

    return _DEFAULT_WINDOWED_SIZE


def front3d_setup_game_settings_type() -> Any:
    from .frontend_nd import GameSettingsND as _GameSettingsND

    return _GameSettingsND


def front3d_setup_run_menu_nd(screen: Any, fonts: Any, dimension: int) -> Any:
    from .frontend_nd import run_menu as _run_menu

    return _run_menu(screen, fonts, dimension)


def front3d_setup_build_config_nd(settings: Any, dimension: int) -> GameConfigND:
    from .frontend_nd import build_config as _build_config

    return _build_config(settings, dimension)


def front3d_setup_create_initial_state_nd(cfg: GameConfigND) -> GameStateND:
    from .frontend_nd import create_initial_state as _create_initial_state

    return _create_initial_state(cfg)


def front3d_setup_gravity_interval_ms_from_config_nd(cfg: GameConfigND) -> int:
    from .frontend_nd import (
        gravity_interval_ms_from_config as _gravity_interval_ms_from_config,
    )

    return _gravity_interval_ms_from_config(cfg)


def launcher_play_run_menu_3d(screen: Any, fonts: Any) -> Any:
    from tet4d.ui.pygame.front3d_game import run_menu as _run_menu

    return _run_menu(screen, fonts)


def launcher_play_build_config_3d(settings: Any) -> Any:
    from tet4d.ui.pygame.front3d_game import build_config as _build_config

    return _build_config(settings)


def launcher_play_suggested_window_size_3d(cfg: Any) -> tuple[int, int]:
    from tet4d.ui.pygame.front3d_game import suggested_window_size as _suggested_window_size

    return _suggested_window_size(cfg)


def launcher_play_run_game_loop_3d(screen: Any, cfg: Any, fonts: Any, **kwargs: Any) -> Any:
    from tet4d.ui.pygame.front3d_game import run_game_loop as _run_game_loop

    return _run_game_loop(screen, cfg, fonts, **kwargs)


def launcher_play_run_game_loop_4d(screen: Any, cfg: Any, fonts: Any, **kwargs: Any) -> Any:
    from tet4d.ui.pygame.front4d_game import run_game_loop as _run_game_loop

    return _run_game_loop(screen, cfg, fonts, **kwargs)


def launcher_play_suggested_window_size_4d(cfg: Any) -> tuple[int, int]:
    from tet4d.ui.pygame.front4d_game import suggested_window_size as _suggested_window_size

    return _suggested_window_size(cfg)


def launcher_play_run_menu_nd(screen: Any, fonts: Any, dimension: int) -> Any:
    from .frontend_nd import run_menu as _run_menu

    return _run_menu(screen, fonts, dimension)


def launcher_play_build_config_nd(settings: Any, dimension: int) -> Any:
    from .frontend_nd import build_config as _build_config

    return _build_config(settings, dimension)


def gravity_interval_ms_gameplay(speed_level: int, *, dimension: int) -> int:
    from .gameplay.speed_curve import gravity_interval_ms as _gravity_interval_ms

    return _gravity_interval_ms(speed_level, dimension=dimension)


def map_overlay_cells_gameplay(*args: Any, **kwargs: Any) -> Any:
    from .gameplay.topology import map_overlay_cells as _map_overlay_cells

    return _map_overlay_cells(*args, **kwargs)


def format_key_tuple(keys):
    from tet4d.ui.pygame.input.key_display import format_key_tuple as _format_key_tuple

    return _format_key_tuple(keys)


def runtime_binding_groups_for_dimension(dimension: int):
    from tet4d.ui.pygame.keybindings import (
        runtime_binding_groups_for_dimension as _runtime_binding_groups_for_dimension,
    )

    return _runtime_binding_groups_for_dimension(dimension)


def audio_event_specs_runtime() -> dict[str, tuple[float, int, float]]:
    from .runtime.runtime_config import audio_event_specs as _audio_event_specs

    return _audio_event_specs()


def binding_action_description(action: str) -> str:
    from .ui_logic.keybindings_catalog import (
        binding_action_description as _binding_action_description,
    )

    return _binding_action_description(action)


def binding_group_label(group: str) -> str:
    from .ui_logic.keybindings_catalog import binding_group_label as _binding_group_label

    return _binding_group_label(group)


def binding_group_description(group: str) -> str:
    from .ui_logic.keybindings_catalog import (
        binding_group_description as _binding_group_description,
    )

    return _binding_group_description(group)


def keybindings_rebind_conflict_replace() -> str:
    from tet4d.ui.pygame.keybindings import REBIND_CONFLICT_REPLACE as _REPLACE

    return _REPLACE


def keybindings_active_key_profile() -> str:
    from tet4d.ui.pygame.keybindings import active_key_profile as _active_key_profile

    return _active_key_profile()


def keybindings_clone_key_profile(
    profile_name: str, *, source_profile: str | None = None
) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import clone_key_profile as _clone_key_profile

    return _clone_key_profile(profile_name, source_profile=source_profile)


def keybindings_cycle_key_profile(step: int) -> tuple[bool, str, str]:
    from tet4d.ui.pygame.keybindings import cycle_key_profile as _cycle_key_profile

    return _cycle_key_profile(step)


def keybindings_cycle_rebind_conflict_mode(mode: str, step: int) -> str:
    from tet4d.ui.pygame.keybindings import (
        cycle_rebind_conflict_mode as _cycle_rebind_conflict_mode,
    )

    return _cycle_rebind_conflict_mode(mode, step)


def keybindings_normalize_rebind_conflict_mode(mode: str | None) -> str:
    from tet4d.ui.pygame.keybindings import (
        normalize_rebind_conflict_mode as _normalize_rebind_conflict_mode,
    )

    return _normalize_rebind_conflict_mode(mode)


def keybindings_delete_key_profile(profile_name: str) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import delete_key_profile as _delete_key_profile

    return _delete_key_profile(profile_name)


def keybindings_create_auto_profile() -> tuple[bool, str, str | None]:
    from tet4d.ui.pygame.keybindings import create_auto_profile as _create_auto_profile

    return _create_auto_profile()


def keybindings_load_active_profile_bindings() -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import load_active_profile_bindings as _load_active_profile_bindings

    return _load_active_profile_bindings()


def keybindings_load_keybindings_file(dimension: int) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import load_keybindings_file as _load_keybindings_file

    return _load_keybindings_file(dimension)


def keybindings_next_auto_profile_name(prefix: str = "custom") -> str:
    from tet4d.ui.pygame.keybindings import next_auto_profile_name as _next_auto_profile_name

    return _next_auto_profile_name(prefix)


def keybindings_rebind_action_key(
    dimension: int,
    group: str,
    action: str,
    key: int,
    *,
    conflict_mode: str,
) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import rebind_action_key as _rebind_action_key

    return _rebind_action_key(
        dimension, group, action, key, conflict_mode=conflict_mode
    )


def keybindings_rename_key_profile(
    old_name: str, new_name: str
) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import rename_key_profile as _rename_key_profile

    return _rename_key_profile(old_name, new_name)


def keybindings_reset_active_profile_bindings(dimension: int) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import (
        reset_active_profile_bindings as _reset_active_profile_bindings,
    )

    return _reset_active_profile_bindings(dimension)


def keybindings_save_keybindings_file(dimension: int) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import save_keybindings_file as _save_keybindings_file

    return _save_keybindings_file(dimension)


def keybindings_set_active_key_profile(profile_name: str) -> tuple[bool, str]:
    from tet4d.ui.pygame.keybindings import set_active_key_profile as _set_active_key_profile

    return _set_active_key_profile(profile_name)


def keybindings_binding_actions_for_dimension(dimension: int):
    from tet4d.ui.pygame.keybindings import (
        binding_actions_for_dimension as _binding_actions_for_dimension,
    )

    return _binding_actions_for_dimension(dimension)


def menu_settings_load(state: Any, dimension: int) -> tuple[bool, str]:
    from .runtime.menu_settings_state import load_menu_settings as _load_menu_settings

    return _load_menu_settings(state, dimension)


def menu_settings_save(state: Any, dimension: int) -> tuple[bool, str]:
    from .runtime.menu_settings_state import save_menu_settings as _save_menu_settings

    return _save_menu_settings(state, dimension)


def menu_settings_reset_to_defaults(state: Any, dimension: int) -> tuple[bool, str]:
    from .runtime.menu_settings_state import (
        reset_menu_settings_to_defaults as _reset_menu_settings_to_defaults,
    )

    return _reset_menu_settings_to_defaults(state, dimension)


def keybindings_menu_shortcut_action_for_key(
    key: int, load_action: Any, save_action: Any
) -> Any | None:
    from tet4d.ui.pygame.menu.menu_keybinding_shortcuts import (
        menu_binding_action_for_key as _menu_binding_action_for_key,
    )

    return _menu_binding_action_for_key(key, load_action, save_action)


def keybindings_apply_menu_shortcut_action(
    action: Any,
    load_action: Any,
    save_action: Any,
    dimension: int,
    state: Any,
) -> bool:
    from tet4d.ui.pygame.menu.menu_keybinding_shortcuts import (
        apply_menu_binding_action as _apply_menu_binding_action,
    )

    return _apply_menu_binding_action(action, load_action, save_action, dimension, state)


def keybindings_menu_status_color(is_error: bool) -> tuple[int, int, int]:
    from tet4d.ui.pygame.menu.menu_keybinding_shortcuts import (
        menu_binding_status_color as _menu_binding_status_color,
    )

    return _menu_binding_status_color(is_error)


def keybindings_partition_gameplay_actions_ui_logic(action_names):
    from .ui_logic.keybindings_catalog import (
        partition_gameplay_actions as _partition_gameplay_actions,
    )

    return _partition_gameplay_actions(action_names)


def keybinding_category_docs_runtime():
    from .runtime.menu_config import keybinding_category_docs as _keybinding_category_docs

    return _keybinding_category_docs()


def keybindings_menu_section_menu() -> tuple[tuple[str, str, str], ...]:
    from tet4d.ui.pygame.menu.keybindings_menu_model import SECTION_MENU as _SECTION_MENU

    return _SECTION_MENU


def keybindings_menu_resolve_initial_scope(dimension: int, scope: str | None) -> str:
    from tet4d.ui.pygame.menu.keybindings_menu_model import (
        resolve_initial_scope as _resolve_initial_scope,
    )

    return _resolve_initial_scope(dimension, scope)


def keybindings_menu_rows_for_scope(scope: str):
    from tet4d.ui.pygame.menu.keybindings_menu_model import rows_for_scope as _rows_for_scope

    return _rows_for_scope(scope)


def keybindings_menu_scope_dimensions(scope: str) -> tuple[int, ...]:
    from tet4d.ui.pygame.menu.keybindings_menu_model import (
        scope_dimensions as _scope_dimensions,
    )

    return _scope_dimensions(scope)


def keybindings_menu_scope_file_hint(scope: str) -> str:
    from tet4d.ui.pygame.menu.keybindings_menu_model import (
        scope_file_hint as _scope_file_hint,
    )

    return _scope_file_hint(scope)


def keybindings_menu_scope_label(scope: str) -> str:
    from tet4d.ui.pygame.menu.keybindings_menu_model import scope_label as _scope_label

    return _scope_label(scope)


def keybindings_menu_binding_keys(row):
    from tet4d.ui.pygame.menu.keybindings_menu_model import binding_keys as _binding_keys

    return _binding_keys(row)


def keybindings_menu_binding_title(row, scope: str) -> str:
    from tet4d.ui.pygame.menu.keybindings_menu_model import binding_title as _binding_title

    return _binding_title(row, scope)


def gameplay_action_category_ui_logic(action: str) -> str:
    from .ui_logic.keybindings_catalog import (
        gameplay_action_category as _gameplay_action_category,
    )

    return _gameplay_action_category(action)


def compute_menu_layout_zones_ui_logic(*args: Any, **kwargs: Any) -> Any:
    from .ui_logic.menu_layout import compute_menu_layout_zones as _compute_zones

    return _compute_zones(*args, **kwargs)


def bot_options_rows_runtime() -> tuple[str, ...]:
    from .runtime.menu_config import bot_options_rows as _bot_options_rows

    return _bot_options_rows()


def bot_defaults_by_mode_runtime() -> dict[str, dict[str, int]]:
    from .runtime.menu_config import bot_defaults_by_mode as _bot_defaults_by_mode

    return _bot_defaults_by_mode()


def settings_category_docs_runtime():
    from .runtime.menu_config import settings_category_docs as _settings_category_docs

    return _settings_category_docs()


def pause_menu_id_runtime() -> str:
    from .runtime.menu_config import pause_menu_id as _pause_menu_id

    return _pause_menu_id()


def menu_items_runtime(menu_id: str):
    from .runtime.menu_config import menu_items as _menu_items

    return _menu_items(menu_id)


def load_menu_payload_runtime() -> dict[str, Any]:
    from .runtime.menu_persistence import load_menu_payload as _load_menu_payload

    return _load_menu_payload()


def save_menu_payload_runtime(payload: dict[str, Any]) -> tuple[bool, str]:
    from .runtime.menu_persistence import save_menu_payload as _save_menu_payload

    return _save_menu_payload(payload)


def load_audio_payload_runtime() -> dict[str, Any]:
    from .runtime.menu_persistence import load_audio_payload as _load_audio_payload

    return _load_audio_payload()


def load_display_payload_runtime() -> dict[str, Any]:
    from .runtime.menu_persistence import load_display_payload as _load_display_payload

    return _load_display_payload()


def help_action_topic_registry_runtime() -> dict[str, str]:
    from .runtime.help_topics import help_action_topic_registry as _registry

    return _registry()


def help_topics_for_context_runtime(*args: Any, **kwargs: Any):
    from .runtime.help_topics import help_topics_for_context as _help_topics_for_context

    return _help_topics_for_context(*args, **kwargs)


def piece_set_2d_options_gameplay():
    from .gameplay.pieces2d import PIECE_SET_2D_OPTIONS as _PIECE_SET_2D_OPTIONS

    return _PIECE_SET_2D_OPTIONS


def piece_set_2d_label_gameplay(piece_set_id: str) -> str:
    from .gameplay.pieces2d import piece_set_2d_label as _piece_set_2d_label

    return _piece_set_2d_label(piece_set_id)


def piece_set_label_gameplay(piece_set_id: str) -> str:
    from .gameplay.pieces_nd import piece_set_label as _piece_set_label

    return _piece_set_label(piece_set_id)


def piece_set_options_for_dimension_gameplay(dimension: int):
    from .gameplay.pieces_nd import (
        piece_set_options_for_dimension as _piece_set_options_for_dimension,
    )

    return _piece_set_options_for_dimension(dimension)


def run_front3d_ui() -> None:
    from tet4d.ui.pygame.front3d_game import run as _run_front3d

    _run_front3d()


def run_front4d_ui() -> None:
    from tet4d.ui.pygame.front4d_game import run as _run_front4d

    _run_front4d()


def profile_4d_new_layer_view_3d(*, xw_deg: float = 0.0, zw_deg: float = 0.0) -> Any:
    from tet4d.ui.pygame.front4d_game import LayerView3D as _LayerView3D

    return _LayerView3D(xw_deg=xw_deg, zw_deg=zw_deg)


def profile_4d_draw_game_frame(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import draw_game_frame as _draw_game_frame

    return _draw_game_frame(*args, **kwargs)


def profile_4d_create_initial_state(cfg: GameConfigND) -> GameStateND:
    from .frontend_nd import create_initial_state as _create_initial_state

    return _create_initial_state(cfg)


def profile_4d_init_fonts() -> Any:
    from .frontend_nd import init_fonts as _init_fonts

    return _init_fonts()


def profile_4d_grid_mode_full() -> Any:
    from .ui_logic.view_modes import GridMode as _GridMode

    return _GridMode.FULL


def hud_analysis_lines_runtime(event: dict[str, object] | None) -> tuple[str, ...]:
    from .runtime.score_analyzer import hud_analysis_lines as _hud_analysis_lines

    return _hud_analysis_lines(event)


def runtime_assist_combined_score_multiplier(*args: Any, **kwargs: Any) -> Any:
    from .runtime.assist_scoring import combined_score_multiplier as _combined_score_multiplier

    return _combined_score_multiplier(*args, **kwargs)


def runtime_collect_cleared_ghost_cells(*args: Any, **kwargs: Any) -> Any:
    from .runtime.runtime_helpers import collect_cleared_ghost_cells as _collect

    return _collect(*args, **kwargs)


def frontend_nd_route_keydown(*args: Any, **kwargs: Any) -> Any:
    from .frontend_nd import route_nd_keydown as _route_nd_keydown

    return _route_nd_keydown(*args, **kwargs)


def front3d_render_camera_type() -> Any:
    from .front3d_render import Camera3D as _Camera3D

    return _Camera3D


def front3d_render_clear_animation_type() -> Any:
    from .front3d_render import ClearAnimation3D as _ClearAnimation3D

    return _ClearAnimation3D


def front3d_render_color_for_cell_3d(*args: Any, **kwargs: Any) -> Any:
    from .front3d_render import color_for_cell_3d as _color_for_cell_3d

    return _color_for_cell_3d(*args, **kwargs)


def front3d_render_draw_game_frame(*args: Any, **kwargs: Any) -> Any:
    from .front3d_render import draw_game_frame as _draw_game_frame

    return _draw_game_frame(*args, **kwargs)


def front3d_render_init_fonts(*args: Any, **kwargs: Any) -> Any:
    from .front3d_render import init_fonts as _init_fonts

    return _init_fonts(*args, **kwargs)


def front3d_render_suggested_window_size(*args: Any, **kwargs: Any) -> Any:
    from .front3d_render import suggested_window_size as _suggested_window_size

    return _suggested_window_size(*args, **kwargs)


def front4d_render_margin() -> int:
    from .front4d_render import MARGIN as _MARGIN

    return _MARGIN


def front4d_render_layer_gap() -> int:
    from .front4d_render import LAYER_GAP as _LAYER_GAP

    return _LAYER_GAP


def front4d_render_side_panel() -> int:
    from .front4d_render import SIDE_PANEL as _SIDE_PANEL

    return _SIDE_PANEL


def front4d_render_layer_view3d_type() -> Any:
    from .front4d_render import LayerView3D as _LayerView3D

    return _LayerView3D


def front4d_render_clear_animation_type() -> Any:
    from .front4d_render import ClearAnimation4D as _ClearAnimation4D

    return _ClearAnimation4D


def front4d_render_draw_game_frame_api(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import draw_game_frame as _draw_game_frame

    return _draw_game_frame(*args, **kwargs)


def front4d_render_handle_view_key(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import handle_view_key as _handle_view_key

    return _handle_view_key(*args, **kwargs)


def front4d_render_movement_axis_overrides(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import (
        movement_axis_overrides_for_view as _movement_axis_overrides_for_view,
    )

    return _movement_axis_overrides_for_view(*args, **kwargs)


def front4d_render_spawn_clear_anim(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import (
        spawn_clear_animation_if_needed as _spawn_clear_animation_if_needed,
    )

    return _spawn_clear_animation_if_needed(*args, **kwargs)


def rotation_anim_piece_rotation_animator_nd_type() -> Any:
    from .gameplay.rotation_anim import PieceRotationAnimatorND as _PieceRotationAnimatorND

    return _PieceRotationAnimatorND


def grid_mode_cycle_view(mode: GridMode) -> GridMode:
    from .ui_logic.view_modes import cycle_grid_mode as _cycle_grid_mode

    return _cycle_grid_mode(mode)


def grid_mode_label_view(mode: GridMode) -> str:
    from .ui_logic.view_modes import grid_mode_label as _grid_mode_label

    return _grid_mode_label(mode)


def __getattr__(name: str) -> Any:
    if name == "PlayBotController":
        from tet4d.ai.playbot import PlayBotController as _PlayBotController

        return _PlayBotController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Action",
    "Action2D",
    "ActivePiece2D",
    "ActivePieceND",
    "BoardND",
    "BOT_MODE_OPTIONS",
    "BOT_PLANNER_ALGORITHM_OPTIONS",
    "BOT_PLANNER_PROFILE_OPTIONS",
    "BotMode",
    "BotPlannerAlgorithm",
    "BotPlannerProfile",
    "DryRunReport",
    "PlayBotController",
    "GameConfig",
    "GameConfig2D",
    "GameConfigND",
    "GameState",
    "GameState2D",
    "GameStateND",
    "EngineRNG",
    "GridMode",
    "board_cells",
    "bot_mode_from_index",
    "bot_mode_label",
    "bot_planner_algorithm_from_index",
    "bot_planner_algorithm_label",
    "bot_planner_profile_from_index",
    "bot_planner_profile_label",
    "current_piece_cells",
    "capture_windowed_display_settings_runtime",
    "apply_challenge_prefill_2d",
    "apply_challenge_prefill_nd",
    "config_view_2d",
    "config_view_nd",
    "front3d_setup_build_config_nd",
    "front3d_setup_create_initial_state_nd",
    "front3d_setup_game_settings_type",
    "front3d_setup_gravity_interval_ms_from_config_nd",
    "front3d_setup_run_menu_nd",
    "default_planning_budget_ms",
    "greedy_key_4d",
    "is_game_over",
    "legal_actions",
    "legal_actions_2d",
    "new_game_state_2d",
    "new_game_state_nd",
    "new_rng",
    "open_display_runtime",
    "PIECE_SET_2D_CLASSIC",
    "PIECE_SET_2D_DEBUG",
    "PieceShape2D",
    "PIECE_SET_3D_DEBUG",
    "PIECE_SET_3D_STANDARD",
    "PIECE_SET_4D_DEBUG",
    "PIECE_SET_4D_STANDARD",
    "PieceShapeND",
    "plan_best_2d_move",
    "plan_best_nd_with_budget",
    "plan_best_nd_move",
    "playbot_benchmark_history_file",
    "playbot_benchmark_p95_thresholds",
    "playbot_build_column_levels_nd",
    "playbot_canonical_blocks_nd",
    "playbot_default_hard_drop_after_soft_drops_runtime",
    "playbot_enumerate_orientations_nd",
    "playbot_evaluate_nd_board",
    "playbot_dry_run_defaults",
    "playbot_greedy_score_4d",
    "playbot_iter_settled_candidates_nd",
    "playbot_rotation_planes_nd",
    "profile_4d_create_initial_state",
    "profile_4d_draw_game_frame",
    "profile_4d_grid_mode_full",
    "profile_4d_init_fonts",
    "profile_4d_new_layer_view_3d",
    "run_dry_run_2d",
    "run_dry_run_nd",
    "run_front3d_ui",
    "run_front4d_ui",
    "rotate_point_2d",
    "rotate_point_nd",
    "simulate_lock_board",
    "state_view_2d",
    "state_view_nd",
    "step",
    "step_2d",
    "step_nd",
]
