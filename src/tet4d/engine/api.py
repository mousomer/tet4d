from __future__ import annotations

import random
from functools import partial
from importlib import import_module
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
from .runtime.settings_schema import (
    MIN_WINDOW_HEIGHT,  # noqa: F401 (re-exported for UI/runtime consumers)
    MIN_WINDOW_WIDTH,  # noqa: F401 (re-exported for UI/runtime consumers)
    normalize_windowed_size,  # noqa: F401 (re-exported for UI/runtime consumers)
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
    from tet4d.ai.playbot.planner_nd_core import (
        simulate_lock_board as _simulate_lock_board,
    )

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
    return _call_runtime_runtime_config("playbot_dry_run_defaults")


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
    return _call_runtime_project_config("project_root_path")


def keybindings_dir_path_runtime() -> Path:
    return _call_runtime_project_config("keybindings_dir_path")


def keybindings_profiles_dir_path_runtime() -> Path:
    return _call_runtime_project_config("keybindings_profiles_dir_path")


def keybindings_defaults_path_runtime() -> Path:
    return _call_runtime_project_config("keybindings_defaults_path")


def keybindings_load_json_file_runtime(path: Path) -> Any:
    return _call_runtime_settings_schema("read_json_value_or_raise", path)


def keybindings_atomic_write_text_runtime(path: Path, payload: str) -> None:
    _call_runtime_settings_schema("atomic_write_text", path, payload)


def keybindings_copy_text_file_runtime(src_path: Path, dst_path: Path) -> None:
    _call_runtime_settings_schema("copy_text_file", src_path, dst_path)


def open_display_runtime(*args: Any, **kwargs: Any) -> Any:
    from tet4d.ui.pygame.runtime_ui.app_runtime import open_display as _open_display

    return _open_display(*args, **kwargs)


def capture_windowed_display_settings_runtime(display_settings: Any) -> Any:
    from tet4d.ui.pygame.runtime_ui.app_runtime import (
        capture_windowed_display_settings as _capture_windowed_display_settings,
    )

    return _capture_windowed_display_settings(display_settings)


def capture_windowed_display_settings_from_event_runtime(
    display_settings: Any,
    *,
    event: Any,
) -> Any:
    from tet4d.ui.pygame.runtime_ui.app_runtime import (
        capture_windowed_display_settings_from_event as _capture_windowed_display_settings_from_event,
    )

    return _capture_windowed_display_settings_from_event(display_settings, event=event)


def advance_gravity_runtime(
    state: Any, accumulator_ms: int, gravity_interval_ms: int
) -> int:
    while not state.game_over and accumulator_ms >= gravity_interval_ms:
        state.step_gravity()
        accumulator_ms -= gravity_interval_ms
    return accumulator_ms


def tick_animation_runtime(animation: Any, dt_ms: int) -> Any:
    if animation is None:
        return None
    animation.step(dt_ms)
    if getattr(animation, "done", False):
        return None
    return animation


def initialize_keybinding_files_runtime() -> None:
    _call_ui_keybindings("initialize_keybinding_files")


def get_audio_settings_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("get_audio_settings")


def get_display_settings_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("get_display_settings")


def get_analytics_settings_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("get_analytics_settings")


def save_display_settings_runtime(*, windowed_size: tuple[int, int]) -> None:
    _call_runtime_menu_settings_state(
        "save_display_settings", windowed_size=windowed_size
    )


def set_score_analyzer_logging_enabled_runtime(enabled: bool | None) -> None:
    from .runtime.score_analyzer import (
        set_score_analyzer_logging_enabled as _set_score_analyzer_logging_enabled,
    )

    _set_score_analyzer_logging_enabled(enabled)


def leaderboard_top_entries_runtime(
    *,
    limit: int = 20,
) -> tuple[dict[str, object], ...]:
    from .runtime.leaderboard import leaderboard_top_entries as _leaderboard_top_entries

    return _leaderboard_top_entries(limit=int(limit))


def leaderboard_entry_would_enter_runtime(
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    exploration_mode: bool,
) -> tuple[bool, int]:
    from .runtime.leaderboard import (
        leaderboard_entry_would_enter as _leaderboard_entry_would_enter,
    )

    return _leaderboard_entry_would_enter(
        dimension=int(dimension),
        score=int(score),
        lines_cleared=int(lines_cleared),
        start_speed_level=int(start_speed_level),
        end_speed_level=int(end_speed_level),
        duration_seconds=float(duration_seconds),
        outcome=str(outcome),
        bot_mode=str(bot_mode),
        grid_mode=str(grid_mode),
        random_mode=str(random_mode),
        topology_mode=str(topology_mode),
        exploration_mode=bool(exploration_mode),
    )


def record_leaderboard_entry_runtime(
    *,
    dimension: int,
    score: int,
    lines_cleared: int,
    start_speed_level: int,
    end_speed_level: int,
    duration_seconds: float,
    outcome: str,
    bot_mode: str,
    grid_mode: str,
    random_mode: str,
    topology_mode: str,
    exploration_mode: bool,
    player_name: str = "Player",
) -> dict[str, object]:
    from .runtime.leaderboard import (
        record_leaderboard_entry as _record_leaderboard_entry,
    )

    return _record_leaderboard_entry(
        dimension=int(dimension),
        score=int(score),
        lines_cleared=int(lines_cleared),
        start_speed_level=int(start_speed_level),
        end_speed_level=int(end_speed_level),
        duration_seconds=float(duration_seconds),
        outcome=str(outcome),
        bot_mode=str(bot_mode),
        grid_mode=str(grid_mode),
        random_mode=str(random_mode),
        topology_mode=str(topology_mode),
        exploration_mode=bool(exploration_mode),
        player_name=str(player_name),
    )


def leaderboard_page_rows_runtime() -> int:
    from .runtime.project_config import project_constant_int as _project_constant_int

    return int(
        _project_constant_int(
            ("analytics", "leaderboard_page_rows"),
            12,
            min_value=5,
            max_value=40,
        )
    )


def leaderboard_name_max_length_runtime() -> int:
    from .runtime.project_config import project_constant_int as _project_constant_int

    return int(
        _project_constant_int(
            ("analytics", "leaderboard_name_max_length"),
            24,
            min_value=3,
            max_value=64,
        )
    )


def settings_hub_layout_rows_runtime():
    return _call_runtime_menu_config("settings_hub_layout_rows")


def settings_top_level_categories_runtime():
    return _call_runtime_menu_config("settings_top_level_categories")


def settings_option_labels_runtime():
    return _call_runtime_menu_config("settings_option_labels")


def default_settings_payload_runtime():
    return _call_runtime_menu_config("default_settings_payload")


def load_analytics_payload_runtime():
    return _call_runtime_menu_settings_state("get_analytics_settings")


def persist_audio_payload_runtime(
    *, master_volume: float, sfx_volume: float, mute: bool
):
    return _call_runtime_menu_settings_state(
        "save_audio_settings",
        master_volume=master_volume,
        sfx_volume=sfx_volume,
        mute=mute,
    )


def persist_display_payload_runtime(
    *,
    fullscreen: bool,
    windowed_size: tuple[int, int],
    overlay_transparency: float | None = None,
):
    return _call_runtime_menu_settings_state(
        "save_display_settings",
        fullscreen=fullscreen,
        windowed_size=windowed_size,
        overlay_transparency=overlay_transparency,
    )


def persist_analytics_payload_runtime(*, score_logging_enabled: bool):
    return _call_runtime_menu_settings_state(
        "save_analytics_settings",
        score_logging_enabled=score_logging_enabled,
    )


def default_windowed_size_runtime() -> tuple[int, int]:
    return _call_runtime_menu_settings_state("_runtime_defaults").windowed_size


def default_overlay_transparency_runtime() -> float:
    return float(_call_runtime_menu_settings_state("_default_overlay_transparency"))


def overlay_transparency_step_runtime() -> float:
    return float(_call_runtime_menu_settings_state("OVERLAY_TRANSPARENCY_STEP"))


def clamp_overlay_transparency_runtime(
    value: Any, *, default: float | None = None
) -> float:
    fallback = (
        float(_call_runtime_menu_settings_state("_default_overlay_transparency"))
        if default is None
        else float(default)
    )
    return float(
        _call_runtime_menu_settings_state(
            "clamp_overlay_transparency", value, default=fallback
        )
    )


def default_game_seed_runtime() -> int:
    return int(_call_runtime_menu_settings_state("_default_game_seed"))


def game_seed_step_runtime() -> int:
    return int(_call_runtime_menu_settings_state("GAME_SEED_STEP"))


def clamp_game_seed_runtime(value: Any, *, default: int | None = None) -> int:
    fallback = (
        int(_call_runtime_menu_settings_state("DEFAULT_GAME_SEED"))
        if default is None
        else int(default)
    )
    return int(
        _call_runtime_menu_settings_state("clamp_game_seed", value, default=fallback)
    )


def clamp_toggle_index_runtime(value: Any, *, default: int = 0) -> int:
    return int(
        _call_runtime_settings_schema(
            "clamp_toggle_index",
            value,
            default=int(default),
        )
    )


def clamp_lines_per_level_runtime(value: Any, *, default: int = 10) -> int:
    return int(
        _call_runtime_settings_schema(
            "clamp_lines_per_level",
            value,
            default=int(default),
        )
    )


def sanitize_text_runtime(value: Any, *, max_length: int = 256) -> str:
    return str(
        _call_runtime_settings_schema(
            "sanitize_text",
            value,
            max_length=max_length,
        )
    )


def get_global_game_seed_runtime() -> int:
    return int(_call_runtime_menu_settings_state("get_global_game_seed"))


def save_global_game_seed_runtime(seed: int):
    return _call_runtime_menu_settings_state("save_global_game_seed", seed)


def gameplay_default_mode_shared_settings_runtime(mode_key: str) -> dict[str, int]:
    return _call_runtime_menu_settings_state(
        "default_mode_shared_gameplay_settings",
        mode_key,
    )


def gameplay_mode_shared_settings_runtime(mode_key: str) -> dict[str, int]:
    return _call_runtime_menu_settings_state(
        "mode_shared_gameplay_settings",
        mode_key,
    )


def gameplay_mode_speedup_settings_runtime(mode_key: str) -> tuple[int, int]:
    return _call_runtime_menu_settings_state("mode_speedup_settings", mode_key)


def gameplay_save_shared_settings_runtime(
    *,
    random_mode_index: int,
    topology_advanced: int,
    auto_speedup_enabled: int,
    lines_per_level: int,
) -> tuple[bool, str]:
    return _call_runtime_menu_settings_state(
        "save_shared_gameplay_settings",
        random_mode_index=int(random_mode_index),
        topology_advanced=int(topology_advanced),
        auto_speedup_enabled=int(auto_speedup_enabled),
        lines_per_level=int(lines_per_level),
    )


def _call_module_attr(
    module_path: str,
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    return getattr(import_module(module_path), name)(*args, **kwargs)


def _get_module_attr(module_path: str, name: str) -> Any:
    return getattr(import_module(module_path), name)


def _call_or_get_module_attr(
    module_path: str,
    name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    attr = _get_module_attr(module_path, name)
    if callable(attr):
        return attr(*args, **kwargs)
    if args or kwargs:
        raise TypeError(f"{name} is not callable")
    return attr


_call_frontend_nd = partial(_call_module_attr, "tet4d.engine.frontend_nd")
_get_frontend_nd_attr = partial(_get_module_attr, "tet4d.engine.frontend_nd")
_call_ui_front3d_game = partial(_call_module_attr, "tet4d.ui.pygame.front3d_game")
_call_ui_front4d_game = partial(_call_module_attr, "tet4d.ui.pygame.front4d_game")
_get_ui_front4d_game_attr = partial(_get_module_attr, "tet4d.ui.pygame.front4d_game")
_call_ui_key_display = partial(_call_module_attr, "tet4d.ui.pygame.input.key_display")
_call_ui_logic_keybindings_catalog = partial(
    _call_module_attr,
    "tet4d.engine.ui_logic.keybindings_catalog",
)
_call_runtime_runtime_config = partial(
    _call_module_attr,
    "tet4d.engine.runtime.runtime_config",
)
_call_ui_keybindings = partial(_call_module_attr, "tet4d.ui.pygame.keybindings")
_call_ui_keybindings_menu_model = partial(
    _call_or_get_module_attr,
    "tet4d.ui.pygame.menu.keybindings_menu_model",
)
_call_ui_keybindings_menu_shortcuts = partial(
    _call_module_attr,
    "tet4d.ui.pygame.menu.menu_keybinding_shortcuts",
)
_call_runtime_menu_config = partial(_call_module_attr, "tet4d.engine.runtime.menu_config")
_call_runtime_project_config = partial(
    _call_module_attr,
    "tet4d.engine.runtime.project_config",
)
_call_runtime_settings_schema = partial(
    _call_module_attr,
    "tet4d.engine.runtime.settings_schema",
)
_call_runtime_menu_settings_state = partial(
    _call_or_get_module_attr,
    "tet4d.engine.runtime.menu_settings_state",
)
_call_runtime_help_topics = partial(_call_module_attr, "tet4d.engine.runtime.help_topics")
_call_help_text = partial(_call_module_attr, "tet4d.engine.help_text")
_call_gameplay_pieces2d = partial(_call_module_attr, "tet4d.engine.gameplay.pieces2d")
_call_gameplay_pieces_nd = partial(
    _call_module_attr,
    "tet4d.engine.gameplay.pieces_nd",
)
_call_gameplay_leveling = partial(_call_module_attr, "tet4d.engine.gameplay.leveling")
_call_gameplay_topology = partial(_call_module_attr, "tet4d.engine.gameplay.topology")
_call_gameplay_topology_designer = partial(
    _call_module_attr,
    "tet4d.engine.gameplay.topology_designer",
)
_call_front4d_render = partial(_call_module_attr, "tet4d.engine.front4d_render")
_get_front4d_render_attr = partial(_get_module_attr, "tet4d.engine.front4d_render")
_call_front3d_render = partial(_call_module_attr, "tet4d.engine.front3d_render")
_get_front3d_render_attr = partial(_get_module_attr, "tet4d.engine.front3d_render")


def front3d_setup_game_settings_type() -> Any:
    return _get_frontend_nd_attr("GameSettingsND")


def front3d_setup_run_menu_nd(screen: Any, fonts: Any, dimension: int) -> Any:
    return _call_frontend_nd("run_menu", screen, fonts, max(2, min(4, int(dimension))))


def front3d_setup_build_config_nd(settings: Any, dimension: int) -> GameConfigND:
    return _call_frontend_nd("build_config", settings, max(2, min(4, int(dimension))))


def front3d_setup_create_initial_state_nd(cfg: GameConfigND) -> GameStateND:
    return _call_frontend_nd("create_initial_state", cfg)


def front3d_setup_gravity_interval_ms_from_config_nd(cfg: GameConfigND) -> int:
    return _call_frontend_nd("gravity_interval_ms_from_config", cfg)


def launcher_play_run_menu_3d(screen: Any, fonts: Any) -> Any:
    return front3d_setup_run_menu_nd(screen, fonts, 3)


def launcher_play_build_config_3d(settings: Any) -> Any:
    return front3d_setup_build_config_nd(settings, 3)


def launcher_play_suggested_window_size_3d(cfg: Any) -> tuple[int, int]:
    return _call_ui_front3d_game("suggested_window_size", cfg)


def launcher_play_run_game_loop_3d(
    screen: Any, cfg: Any, fonts: Any, **kwargs: Any
) -> Any:
    return _call_ui_front3d_game("run_game_loop", screen, cfg, fonts, **kwargs)


def launcher_play_run_game_loop_4d(
    screen: Any, cfg: Any, fonts: Any, **kwargs: Any
) -> Any:
    return _call_ui_front4d_game("run_game_loop", screen, cfg, fonts, **kwargs)


def launcher_play_suggested_window_size_4d(cfg: Any) -> tuple[int, int]:
    return _call_ui_front4d_game("suggested_window_size", cfg)


def launcher_play_run_menu_nd(screen: Any, fonts: Any, dimension: int) -> Any:
    return _call_frontend_nd("run_menu", screen, fonts, dimension)


def launcher_play_build_config_nd(settings: Any, dimension: int) -> Any:
    return _call_frontend_nd("build_config", settings, dimension)


def gravity_interval_ms_gameplay(speed_level: int, *, dimension: int) -> int:
    from .gameplay.speed_curve import gravity_interval_ms as _gravity_interval_ms

    return _gravity_interval_ms(speed_level, dimension=dimension)


def map_overlay_cells_gameplay(*args: Any, **kwargs: Any) -> Any:
    from .gameplay.topology import map_overlay_cells as _map_overlay_cells

    return _map_overlay_cells(*args, **kwargs)


def topology_mode_from_index_runtime(index: int) -> str:
    return str(_call_gameplay_topology("topology_mode_from_index", index))


def topology_mode_label_runtime(mode: str | None) -> str:
    return str(_call_gameplay_topology("topology_mode_label", mode))


def topology_mode_options_runtime() -> tuple[str, ...]:
    options = _get_module_attr("tet4d.engine.gameplay.topology", "TOPOLOGY_MODE_OPTIONS")
    return tuple(str(option) for option in options)


def topology_designer_profiles_runtime(dimension: int):
    return _call_gameplay_topology_designer("designer_profiles_for_dimension", dimension)


def topology_designer_profile_label_runtime(dimension: int, index: int) -> str:
    return str(
        _call_gameplay_topology_designer(
            "designer_profile_label_for_index",
            dimension,
            index,
        )
    )


def topology_designer_resolve_runtime(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
):
    return _call_gameplay_topology_designer(
        "resolve_topology_designer_selection",
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
    )


def topology_designer_export_runtime(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    topology_advanced: bool,
    profile_index: int,
):
    return _call_gameplay_topology_designer(
        "export_resolved_topology_profile",
        dimension=dimension,
        gravity_axis=gravity_axis,
        topology_mode=topology_mode,
        topology_advanced=topology_advanced,
        profile_index=profile_index,
    )


def topology_lab_menu_payload_runtime() -> dict[str, Any]:
    path = project_root_path() / "config" / "topology" / "lab_menu.json"
    payload = _call_runtime_settings_schema("read_json_object_or_raise", path)
    return dict(payload)


def format_key_tuple(keys):
    return _call_ui_key_display("format_key_tuple", keys)


def runtime_binding_groups_for_dimension(dimension: int):
    return _call_ui_keybindings("runtime_binding_groups_for_dimension", dimension)


def audio_event_specs_runtime() -> dict[str, tuple[float, int, float]]:
    return _call_runtime_runtime_config("audio_event_specs")


def binding_action_description(action: str) -> str:
    return _call_ui_logic_keybindings_catalog("binding_action_description", action)


def binding_group_label(group: str) -> str:
    return _call_ui_logic_keybindings_catalog("binding_group_label", group)


def binding_group_description(group: str) -> str:
    return _call_ui_logic_keybindings_catalog("binding_group_description", group)


def keybindings_rebind_conflict_replace() -> str:
    from tet4d.ui.pygame import keybindings as _keybindings

    return _keybindings.REBIND_CONFLICT_REPLACE


def _proxy_ui_keybindings(method_name: str):
    def _dispatch(*args: Any, **kwargs: Any) -> Any:
        return _call_ui_keybindings(method_name, *args, **kwargs)

    return _dispatch


keybindings_active_key_profile = _proxy_ui_keybindings("active_key_profile")
keybindings_clone_key_profile = _proxy_ui_keybindings("clone_key_profile")
keybindings_cycle_key_profile = _proxy_ui_keybindings("cycle_key_profile")
keybindings_cycle_rebind_conflict_mode = _proxy_ui_keybindings(
    "cycle_rebind_conflict_mode"
)
keybindings_normalize_rebind_conflict_mode = _proxy_ui_keybindings(
    "normalize_rebind_conflict_mode"
)
keybindings_delete_key_profile = _proxy_ui_keybindings("delete_key_profile")
keybindings_create_auto_profile = _proxy_ui_keybindings("create_auto_profile")
keybindings_load_active_profile_bindings = _proxy_ui_keybindings(
    "load_active_profile_bindings"
)
keybindings_load_keybindings_file = _proxy_ui_keybindings("load_keybindings_file")
keybindings_next_auto_profile_name = _proxy_ui_keybindings("next_auto_profile_name")
keybindings_rebind_action_key = _proxy_ui_keybindings("rebind_action_key")
keybindings_rename_key_profile = _proxy_ui_keybindings("rename_key_profile")
keybindings_reset_active_profile_bindings = _proxy_ui_keybindings(
    "reset_active_profile_bindings"
)
keybindings_save_keybindings_file = _proxy_ui_keybindings("save_keybindings_file")
keybindings_set_active_key_profile = _proxy_ui_keybindings(
    "set_active_key_profile"
)
keybindings_binding_actions_for_dimension = _proxy_ui_keybindings(
    "binding_actions_for_dimension"
)


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


def _proxy_ui_keybindings_menu_shortcuts(method_name: str):
    def _dispatch(*args: Any, **kwargs: Any) -> Any:
        return _call_ui_keybindings_menu_shortcuts(method_name, *args, **kwargs)

    return _dispatch


keybindings_menu_shortcut_action_for_key = _proxy_ui_keybindings_menu_shortcuts(
    "menu_binding_action_for_key"
)
keybindings_apply_menu_shortcut_action = _proxy_ui_keybindings_menu_shortcuts(
    "apply_menu_binding_action"
)
keybindings_menu_status_color = _proxy_ui_keybindings_menu_shortcuts(
    "menu_binding_status_color"
)


def keybindings_partition_gameplay_actions_ui_logic(action_names):
    return _call_ui_logic_keybindings_catalog(
        "partition_gameplay_actions",
        action_names,
    )


def keybinding_category_docs_runtime():
    from .runtime.menu_config import (
        keybinding_category_docs as _keybinding_category_docs,
    )

    return _keybinding_category_docs()


def _proxy_ui_keybindings_menu_model(method_name: str):
    def _dispatch(*args: Any, **kwargs: Any) -> Any:
        return _call_ui_keybindings_menu_model(method_name, *args, **kwargs)

    return _dispatch


def _proxy_ui_logic_keybindings_catalog(method_name: str):
    def _dispatch(*args: Any, **kwargs: Any) -> Any:
        return _call_ui_logic_keybindings_catalog(method_name, *args, **kwargs)

    return _dispatch


keybindings_menu_section_menu = _proxy_ui_keybindings_menu_model("SECTION_MENU")
keybindings_menu_resolve_initial_scope = _proxy_ui_keybindings_menu_model(
    "resolve_initial_scope"
)
keybindings_menu_rows_for_scope = _proxy_ui_keybindings_menu_model("rows_for_scope")
keybindings_menu_scope_dimensions = _proxy_ui_keybindings_menu_model(
    "scope_dimensions"
)
keybindings_menu_scope_file_hint = _proxy_ui_keybindings_menu_model(
    "scope_file_hint"
)
keybindings_menu_scope_label = _proxy_ui_keybindings_menu_model("scope_label")
keybindings_menu_binding_keys = _proxy_ui_keybindings_menu_model("binding_keys")
keybindings_menu_binding_title = _proxy_ui_keybindings_menu_model("binding_title")
gameplay_action_category_ui_logic = _proxy_ui_logic_keybindings_catalog(
    "gameplay_action_category"
)


def compute_menu_layout_zones_ui_logic(*args: Any, **kwargs: Any) -> Any:
    from .ui_logic.menu_layout import compute_menu_layout_zones as _compute_zones

    return _compute_zones(*args, **kwargs)


def bot_options_rows_runtime() -> tuple[str, ...]:
    return _call_runtime_menu_config("bot_options_rows")


def bot_defaults_by_mode_runtime() -> dict[str, dict[str, int]]:
    return _call_runtime_menu_config("bot_defaults_by_mode")


def settings_category_docs_runtime():
    return _call_runtime_menu_config("settings_category_docs")


def pause_menu_id_runtime() -> str:
    return _call_runtime_menu_config("pause_menu_id")


def menu_items_runtime(menu_id: str):
    return _call_runtime_menu_config("menu_items", menu_id)


def pause_copy_runtime() -> dict[str, Any]:
    return _call_runtime_menu_config("pause_copy")


def branding_copy_runtime() -> dict[str, str]:
    return _call_runtime_menu_config("branding_copy")


def ui_copy_payload_runtime() -> dict[str, Any]:
    return _call_runtime_menu_config("ui_copy_payload")


def ui_copy_section_runtime(section: str) -> dict[str, Any]:
    return _call_runtime_menu_config("ui_copy_section", section)


def load_menu_payload_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("load_app_settings_payload")


def save_menu_payload_runtime(payload: dict[str, Any]) -> tuple[bool, str]:
    return _call_runtime_menu_settings_state("save_app_settings_payload", payload)


def load_audio_payload_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("get_audio_settings")


def load_display_payload_runtime() -> dict[str, Any]:
    return _call_runtime_menu_settings_state("get_display_settings")


def help_action_topic_registry_runtime() -> dict[str, str]:
    return _call_runtime_help_topics("help_action_topic_registry")


def help_topics_for_context_runtime(*args: Any, **kwargs: Any):
    return _call_runtime_help_topics("help_topics_for_context", *args, **kwargs)


def help_topic_block_lines_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_topic_block_lines", *args, **kwargs)


def help_topic_compact_limit_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_topic_compact_limit", *args, **kwargs)


def help_topic_compact_overflow_line_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_topic_compact_overflow_line", *args, **kwargs)


def help_value_template_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_value_template", *args, **kwargs)


def help_action_group_heading_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_action_group_heading", *args, **kwargs)


def help_fallback_topic_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_fallback_topic", *args, **kwargs)


def help_layout_payload_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_layout_payload", *args, **kwargs)


def help_action_layout_payload_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_action_layout_payload", *args, **kwargs)


def help_action_panel_specs_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_action_panel_specs", *args, **kwargs)


def help_topic_media_rule_runtime(*args: Any, **kwargs: Any):
    return _call_help_text("help_topic_media_rule", *args, **kwargs)


def piece_set_2d_options_gameplay():
    from .gameplay import pieces2d as _pieces2d

    return _pieces2d.PIECE_SET_2D_OPTIONS


def piece_set_2d_label_gameplay(piece_set_id: str) -> str:
    return _call_gameplay_pieces2d("piece_set_2d_label", piece_set_id)


def piece_set_label_gameplay(piece_set_id: str) -> str:
    return _call_gameplay_pieces_nd("piece_set_label", piece_set_id)


def piece_set_options_for_dimension_gameplay(dimension: int):
    return _call_gameplay_pieces_nd("piece_set_options_for_dimension", dimension)


def compute_speed_level_runtime(*args: Any, **kwargs: Any) -> int:
    return int(_call_gameplay_leveling("compute_speed_level", *args, **kwargs))


def run_front3d_ui() -> None:
    _call_ui_front3d_game("run")


def run_front4d_ui() -> None:
    _call_ui_front4d_game("run")


def profile_4d_new_layer_view_3d(*, xw_deg: float = 0.0, zw_deg: float = 0.0) -> Any:
    layer_view_3d = _get_ui_front4d_game_attr("LayerView3D")
    return layer_view_3d(xw_deg=xw_deg, zw_deg=zw_deg)


def profile_4d_draw_game_frame(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render("draw_game_frame", *args, **kwargs)


def profile_4d_create_initial_state(cfg: GameConfigND) -> GameStateND:
    return _call_frontend_nd("create_initial_state", cfg)


def profile_4d_init_fonts() -> Any:
    return _call_frontend_nd("init_fonts")


def profile_4d_grid_mode_full() -> Any:
    from .ui_logic.view_modes import GridMode as _GridMode

    return _GridMode.FULL


def hud_analysis_lines_runtime(event: dict[str, object] | None) -> tuple[str, ...]:
    from .runtime.score_analyzer import hud_analysis_lines as _hud_analysis_lines

    return _hud_analysis_lines(event)


def runtime_assist_combined_score_multiplier(*args: Any, **kwargs: Any) -> Any:
    from .runtime.runtime_config import (
        assist_bot_factor,
        assist_combined_bounds,
        assist_grid_factor,
        assist_speed_formula,
    )

    bot_mode = kwargs.get("bot_mode") if kwargs else args[0]
    grid_mode = kwargs.get("grid_mode") if kwargs else args[1]
    speed_level = kwargs.get("speed_level") if kwargs else args[2]
    bot_name = getattr(bot_mode, "value", bot_mode)
    grid_name = getattr(grid_mode, "value", grid_mode)
    base, per_level, min_level, max_level = assist_speed_formula()
    level = max(min_level, min(max_level, int(speed_level)))
    speed_factor = min(1.0, base + (per_level * level))
    combined = (
        assist_bot_factor(str(bot_name))
        * assist_grid_factor(str(grid_name))
        * speed_factor
    )
    min_factor, max_factor = assist_combined_bounds()
    return max(min_factor, min(max_factor, combined))


def runtime_collect_cleared_ghost_cells(*args: Any, **kwargs: Any) -> Any:
    state = kwargs.get("state") if kwargs else args[0]
    expected_coord_len = kwargs.get("expected_coord_len") if kwargs else args[1]
    color_for_cell = kwargs.get("color_for_cell") if kwargs else args[2]
    ghost_cells: list[tuple[tuple[int, ...], tuple[int, int, int]]] = []
    for coord, cell_id in state.board.last_cleared_cells:
        if len(coord) != int(expected_coord_len):
            continue
        ghost_cells.append((tuple(coord), color_for_cell(cell_id)))
    return tuple(ghost_cells)


def frontend_nd_route_keydown(*args: Any, **kwargs: Any) -> Any:
    return _call_frontend_nd("route_nd_keydown", *args, **kwargs)


def front3d_render_camera_type() -> Any:
    return _get_front3d_render_attr("Camera3D")


def front3d_render_clear_animation_type() -> Any:
    return _get_front3d_render_attr("ClearAnimation3D")


def front3d_render_color_for_cell_3d(*args: Any, **kwargs: Any) -> Any:
    return _call_front3d_render("color_for_cell_3d", *args, **kwargs)


def front3d_render_draw_game_frame(*args: Any, **kwargs: Any) -> Any:
    return _call_front3d_render("draw_game_frame", *args, **kwargs)


def front3d_render_init_fonts(*args: Any, **kwargs: Any) -> Any:
    return _call_front3d_render("init_fonts", *args, **kwargs)


def front3d_render_suggested_window_size(*args: Any, **kwargs: Any) -> Any:
    return _call_front3d_render("suggested_window_size", *args, **kwargs)


def front4d_render_margin() -> int:
    return _get_front4d_render_attr("MARGIN")


def front4d_render_layer_gap() -> int:
    return _get_front4d_render_attr("LAYER_GAP")


def front4d_render_side_panel() -> int:
    return _get_front4d_render_attr("SIDE_PANEL")


def front4d_render_layer_view3d_type() -> Any:
    return _get_front4d_render_attr("LayerView3D")


def front4d_render_clear_animation_type() -> Any:
    return _get_front4d_render_attr("ClearAnimation4D")


def front4d_render_draw_game_frame_api(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render("draw_game_frame", *args, **kwargs)


def front4d_render_handle_view_key(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render("handle_view_key", *args, **kwargs)


def front4d_render_movement_axis_overrides(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render(
        "movement_axis_overrides_for_view",
        *args,
        **kwargs,
    )


def front4d_render_viewer_axes_for_view(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render(
        "viewer_axes_for_view",
        *args,
        **kwargs,
    )


def front4d_render_spawn_clear_anim(*args: Any, **kwargs: Any) -> Any:
    return _call_front4d_render(
        "spawn_clear_animation_if_needed",
        *args,
        **kwargs,
    )


def rotation_anim_piece_rotation_animator_nd_type() -> Any:
    from .gameplay.rotation_anim import (
        PieceRotationAnimatorND as _PieceRotationAnimatorND,
    )

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
    "capture_windowed_display_settings_from_event_runtime",
    "compute_speed_level_runtime",
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
