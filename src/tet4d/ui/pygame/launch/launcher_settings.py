from __future__ import annotations

from dataclasses import dataclass

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.runtime_ui.app_runtime import capture_windowed_display_settings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings, play_sfx, set_audio_settings
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    apply_display_mode,
    normalize_display_settings,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text


BG_TOP = (14, 18, 44)
BG_BOTTOM = (4, 7, 20)
TEXT_COLOR = (232, 232, 240)
HIGHLIGHT_COLOR = (255, 224, 128)
MUTED_COLOR = (192, 200, 228)
_RANDOM_MODE_LABELS = ("Fixed seed", "True random")


@dataclass
class SettingsHubResult:
    screen: pygame.Surface
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    keep_running: bool


@dataclass
class _UnifiedSettingsState:
    audio_settings: AudioSettings
    display_settings: DisplaySettings
    overlay_transparency: float
    game_seed: int
    random_mode_index: int
    topology_advanced: int
    score_logging_enabled: bool
    original_audio: AudioSettings
    original_display: DisplaySettings
    original_overlay_transparency: float
    original_game_seed: int
    original_random_mode_index: int
    original_topology_advanced: int
    original_score_logging_enabled: bool
    selected: int = 0
    status: str = ""
    status_error: bool = False
    pending_reset_confirm: bool = False
    saved: bool = False
    running: bool = True


_UNIFIED_SETTINGS_ROWS: tuple[tuple[str, str, str], ...] = (
    engine_api.settings_hub_layout_rows_runtime()
)
_UNIFIED_SELECTABLE = tuple(
    idx for idx, row in enumerate(_UNIFIED_SETTINGS_ROWS) if row[0] == "item"
)


def _configured_top_level_labels() -> tuple[str, ...]:
    entries = engine_api.settings_top_level_categories_runtime()
    return tuple(entry["label"] for entry in entries)


def _layout_top_level_labels() -> tuple[str, ...]:
    return tuple(
        label
        for row_kind, label, _row_key in _UNIFIED_SETTINGS_ROWS
        if row_kind == "header"
    )


def _validate_unified_layout_against_policy() -> tuple[bool, str]:
    expected = _configured_top_level_labels()
    actual = _layout_top_level_labels()
    if expected == actual:
        return True, "Settings layout policy verified"
    return False, (
        "Settings layout mismatch: expected top-level categories "
        f"{', '.join(expected)} but UI renders {', '.join(actual)}"
    )


def _draw_gradient(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, BG_TOP, BG_BOTTOM)


def _audio_defaults() -> AudioSettings:
    defaults = engine_api.default_settings_payload_runtime().get("audio", {})
    master = 0.8
    sfx = 0.7
    mute = False
    if isinstance(defaults, dict):
        raw_master = defaults.get("master_volume")
        raw_sfx = defaults.get("sfx_volume")
        if isinstance(raw_master, (int, float)) and not isinstance(raw_master, bool):
            master = float(raw_master)
        if isinstance(raw_sfx, (int, float)) and not isinstance(raw_sfx, bool):
            sfx = float(raw_sfx)
        mute = bool(defaults.get("mute", False))
    return AudioSettings(master_volume=master, sfx_volume=sfx, mute=mute)


def _display_defaults() -> DisplaySettings:
    defaults = engine_api.default_settings_payload_runtime().get("display", {})
    fullscreen = False
    windowed_size = engine_api.default_windowed_size_runtime()
    if isinstance(defaults, dict):
        fullscreen = bool(defaults.get("fullscreen", False))
        raw_size = defaults.get("windowed_size")
        if (
            isinstance(raw_size, list)
            and len(raw_size) == 2
            and all(isinstance(v, int) and not isinstance(v, bool) for v in raw_size)
        ):
            windowed_size = (raw_size[0], raw_size[1])
    return DisplaySettings(fullscreen=fullscreen, windowed_size=windowed_size)


def _analytics_defaults() -> bool:
    defaults = engine_api.default_settings_payload_runtime().get("analytics", {})
    if isinstance(defaults, dict):
        return bool(defaults.get("score_logging_enabled", False))
    return False


def _overlay_transparency_default() -> float:
    return engine_api.default_overlay_transparency_runtime()


def _game_seed_default() -> int:
    return int(engine_api.default_game_seed_runtime())


def _random_mode_default() -> int:
    defaults = engine_api.default_settings_payload_runtime().get("settings", {})
    if isinstance(defaults, dict):
        mode_2d = defaults.get("2d")
        if isinstance(mode_2d, dict):
            return _clamp_toggle_index(mode_2d.get("random_mode_index"), default=0)
    return 0


def _topology_advanced_default() -> int:
    defaults = engine_api.default_settings_payload_runtime().get("settings", {})
    if isinstance(defaults, dict):
        mode_2d = defaults.get("2d")
        if isinstance(mode_2d, dict):
            return _clamp_toggle_index(mode_2d.get("topology_advanced"), default=0)
    return 0


def _clamp_toggle_index(value: object, *, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return 0 if int(value) <= 0 else 1


def _load_overlay_transparency_setting() -> float:
    payload = engine_api.get_display_settings_runtime()
    if isinstance(payload, dict):
        return engine_api.clamp_overlay_transparency_runtime(
            payload.get("overlay_transparency"),
            default=_overlay_transparency_default(),
        )
    return _overlay_transparency_default()


def _load_game_seed_setting() -> int:
    return int(
        engine_api.clamp_game_seed_runtime(
            engine_api.get_global_game_seed_runtime(),
            default=_game_seed_default(),
        )
    )


def _load_random_mode_setting() -> int:
    payload = engine_api.load_menu_payload_runtime()
    settings = payload.get("settings", {}) if isinstance(payload, dict) else {}
    mode_2d = settings.get("2d") if isinstance(settings, dict) else None
    if isinstance(mode_2d, dict):
        return _clamp_toggle_index(
            mode_2d.get("random_mode_index"),
            default=_random_mode_default(),
        )
    return _random_mode_default()


def _load_topology_advanced_setting() -> int:
    payload = engine_api.load_menu_payload_runtime()
    settings = payload.get("settings", {}) if isinstance(payload, dict) else {}
    mode_2d = settings.get("2d") if isinstance(settings, dict) else None
    if isinstance(mode_2d, dict):
        return _clamp_toggle_index(
            mode_2d.get("topology_advanced"),
            default=_topology_advanced_default(),
        )
    return _topology_advanced_default()


def _save_shared_gameplay_settings(
    random_mode_index: int,
    topology_advanced: int,
) -> tuple[bool, str]:
    payload = engine_api.load_menu_payload_runtime()
    if not isinstance(payload, dict):
        payload = {}
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}
        payload["settings"] = settings
    for mode_key in ("2d", "3d", "4d"):
        mode_settings = settings.get(mode_key)
        if not isinstance(mode_settings, dict):
            mode_settings = {}
            settings[mode_key] = mode_settings
        mode_settings["random_mode_index"] = _clamp_toggle_index(
            random_mode_index,
            default=_random_mode_default(),
        )
        mode_settings["topology_advanced"] = _clamp_toggle_index(
            topology_advanced,
            default=_topology_advanced_default(),
        )
    return engine_api.save_menu_payload_runtime(payload)


def _load_score_logging_setting() -> bool:
    payload = engine_api.load_analytics_payload_runtime()
    if isinstance(payload, dict):
        return bool(payload.get("score_logging_enabled", _analytics_defaults()))
    return _analytics_defaults()


def _clone_audio_settings(settings: AudioSettings) -> AudioSettings:
    return AudioSettings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _clone_display_settings(settings: DisplaySettings) -> DisplaySettings:
    return DisplaySettings(
        fullscreen=settings.fullscreen, windowed_size=settings.windowed_size
    )


def _sync_audio_preview(settings: AudioSettings) -> None:
    set_audio_settings(
        master_volume=settings.master_volume,
        sfx_volume=settings.sfx_volume,
        mute=settings.mute,
    )


def _sync_analytics_preview(score_logging_enabled: bool) -> None:
    engine_api.set_score_analyzer_logging_enabled_runtime(bool(score_logging_enabled))


def _unified_row_key(state: _UnifiedSettingsState) -> str:
    row_idx = _UNIFIED_SELECTABLE[state.selected]
    return _UNIFIED_SETTINGS_ROWS[row_idx][2]


def _set_unified_status(
    state: _UnifiedSettingsState, message: str, *, is_error: bool = False
) -> None:
    state.status = message
    state.status_error = is_error


def _mark_unified_dirty(state: _UnifiedSettingsState) -> None:
    state.saved = False


def _save_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.display_settings = normalize_display_settings(state.display_settings)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    ok_audio, msg_audio = engine_api.persist_audio_payload_runtime(
        master_volume=state.audio_settings.master_volume,
        sfx_volume=state.audio_settings.sfx_volume,
        mute=state.audio_settings.mute,
    )
    ok_display, msg_display = engine_api.persist_display_payload_runtime(
        fullscreen=state.display_settings.fullscreen,
        windowed_size=state.display_settings.windowed_size,
        overlay_transparency=state.overlay_transparency,
    )
    ok_analytics, msg_analytics = engine_api.persist_analytics_payload_runtime(
        score_logging_enabled=state.score_logging_enabled,
    )
    ok_game_seed, msg_game_seed = engine_api.save_global_game_seed_runtime(
        int(state.game_seed)
    )
    ok_gameplay_shared, msg_gameplay_shared = _save_shared_gameplay_settings(
        int(state.random_mode_index),
        int(state.topology_advanced),
    )
    if ok_audio and ok_display and ok_analytics and ok_game_seed and ok_gameplay_shared:
        state.original_audio = _clone_audio_settings(state.audio_settings)
        state.original_display = _clone_display_settings(state.display_settings)
        state.original_overlay_transparency = float(state.overlay_transparency)
        state.original_game_seed = int(state.game_seed)
        state.original_random_mode_index = int(state.random_mode_index)
        state.original_topology_advanced = int(state.topology_advanced)
        state.original_score_logging_enabled = bool(state.score_logging_enabled)
        state.saved = True
        _set_unified_status(state, "Saved audio/display/gameplay/analytics settings")
        play_sfx("menu_confirm")
        return screen

    error = msg_audio
    if ok_audio:
        error = msg_display
    if ok_audio and ok_display:
        error = msg_analytics
    if ok_audio and ok_display and ok_analytics:
        error = msg_game_seed
    if ok_audio and ok_display and ok_analytics and ok_game_seed:
        error = msg_gameplay_shared
    _set_unified_status(state, error, is_error=True)
    return screen


def _reset_unified_settings(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    state.audio_settings = _audio_defaults()
    state.display_settings = _display_defaults()
    state.overlay_transparency = _overlay_transparency_default()
    state.game_seed = _game_seed_default()
    state.random_mode_index = _random_mode_default()
    state.topology_advanced = _topology_advanced_default()
    state.score_logging_enabled = _analytics_defaults()
    state.pending_reset_confirm = False
    _mark_unified_dirty(state)
    _sync_audio_preview(state.audio_settings)
    _sync_analytics_preview(state.score_logging_enabled)
    screen = apply_display_mode(
        state.display_settings,
        preferred_windowed_size=state.display_settings.windowed_size,
    )
    _set_unified_status(state, "Reset to defaults (not saved yet)")
    play_sfx("menu_move")
    return screen


def _adjust_unified_audio_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "audio_master":
        state.audio_settings.master_volume = max(
            0.0, min(1.0, state.audio_settings.master_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
        return True
    if row_key == "audio_sfx":
        state.audio_settings.sfx_volume = max(
            0.0, min(1.0, state.audio_settings.sfx_volume + delta_sign * 0.05)
        )
        _sync_audio_preview(state.audio_settings)
        return True
    if row_key == "audio_mute":
        state.audio_settings.mute = not state.audio_settings.mute
        _sync_audio_preview(state.audio_settings)
        return True
    return False


def _adjust_unified_display_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "display_fullscreen":
        state.display_settings = DisplaySettings(
            not state.display_settings.fullscreen, state.display_settings.windowed_size
        )
        return True
    if row_key == "display_width":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (max(640, width + delta_sign * 40), height),
        )
        return True
    if row_key == "display_height":
        width, height = state.display_settings.windowed_size
        state.display_settings = DisplaySettings(
            state.display_settings.fullscreen,
            (width, max(480, height + delta_sign * 40)),
        )
        return True
    if row_key == "display_overlay_transparency":
        state.overlay_transparency = engine_api.clamp_overlay_transparency_runtime(
            state.overlay_transparency
            + delta_sign * engine_api.overlay_transparency_step_runtime(),
            default=_overlay_transparency_default(),
        )
        return True
    return False


def _adjust_unified_gameplay_row(
    state: _UnifiedSettingsState, row_key: str, delta_sign: int
) -> bool:
    if row_key == "game_seed":
        state.game_seed = int(
            engine_api.clamp_game_seed_runtime(
                int(state.game_seed)
                + delta_sign * int(engine_api.game_seed_step_runtime()),
                default=_game_seed_default(),
            )
        )
        return True
    if row_key == "game_random_mode":
        state.random_mode_index = (int(state.random_mode_index) + delta_sign) % len(
            _RANDOM_MODE_LABELS
        )
        return True
    if row_key == "game_topology_advanced":
        state.topology_advanced = 0 if int(state.topology_advanced) else 1
        return True
    return False


def _adjust_unified_analytics_row(state: _UnifiedSettingsState, row_key: str) -> bool:
    if row_key != "analytics_score_logging":
        return False
    state.score_logging_enabled = not state.score_logging_enabled
    _sync_analytics_preview(state.score_logging_enabled)
    return True


def _adjust_unified_with_arrows(state: _UnifiedSettingsState, key: int) -> bool:
    if key not in (pygame.K_LEFT, pygame.K_RIGHT):
        return False
    delta_sign = -1 if key == pygame.K_LEFT else 1
    row_key = _unified_row_key(state)
    handled = (
        _adjust_unified_audio_row(state, row_key, delta_sign)
        or _adjust_unified_display_row(state, row_key, delta_sign)
        or _adjust_unified_gameplay_row(state, row_key, delta_sign)
        or _adjust_unified_analytics_row(state, row_key)
    )
    if not handled:
        return False
    _mark_unified_dirty(state)
    state.pending_reset_confirm = False
    play_sfx("menu_move")
    return True


def _handle_unified_enter(
    screen: pygame.Surface, state: _UnifiedSettingsState
) -> pygame.Surface:
    row_key = _unified_row_key(state)
    if row_key in {
        "audio_mute",
        "display_fullscreen",
        "analytics_score_logging",
        "game_random_mode",
        "game_topology_advanced",
    }:
        state.pending_reset_confirm = False
        _adjust_unified_with_arrows(state, pygame.K_RIGHT)
        return screen
    if row_key == "display_apply":
        state.display_settings = normalize_display_settings(state.display_settings)
        screen = apply_display_mode(
            state.display_settings,
            preferred_windowed_size=state.display_settings.windowed_size,
        )
        _mark_unified_dirty(state)
        state.pending_reset_confirm = False
        _set_unified_status(state, "Applied display mode")
        play_sfx("menu_confirm")
        return screen
    if row_key == "save":
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if row_key == "reset":
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press Enter on Reset defaults again to confirm")
            return screen
        return _reset_unified_settings(screen, state)
    if row_key == "back":
        state.pending_reset_confirm = False
        state.running = False
    return screen


def _unified_value_text(state: _UnifiedSettingsState, row_key: str) -> str:
    static_values = {
        "audio_master": f"{int(state.audio_settings.master_volume * 100)}%",
        "audio_sfx": f"{int(state.audio_settings.sfx_volume * 100)}%",
        "audio_mute": "ON" if state.audio_settings.mute else "OFF",
        "display_fullscreen": "ON" if state.display_settings.fullscreen else "OFF",
        "display_width": str(state.display_settings.windowed_size[0]),
        "display_height": str(state.display_settings.windowed_size[1]),
        "display_overlay_transparency": (
            f"{int(round(state.overlay_transparency * 100.0))}%"
        ),
        "game_seed": str(int(state.game_seed)),
        "analytics_score_logging": "ON" if state.score_logging_enabled else "OFF",
    }
    value = static_values.get(row_key)
    if value is not None:
        return value
    if row_key == "game_random_mode":
        safe_index = max(
            0,
            min(len(_RANDOM_MODE_LABELS) - 1, int(state.random_mode_index)),
        )
        return _RANDOM_MODE_LABELS[safe_index]
    if row_key == "game_topology_advanced":
        return "ON" if int(state.topology_advanced) else "OFF"
    return ""


def _draw_unified_settings_menu(
    screen: pygame.Surface, fonts, state: _UnifiedSettingsState
) -> None:
    _draw_gradient(screen)
    width, height = screen.get_size()
    title = fonts.title_font.render("Settings", True, TEXT_COLOR)
    categories = ", ".join(_configured_top_level_labels())
    subtitle_text = fit_text(
        fonts.hint_font,
        f"Top-level categories: {categories}",
        width - 28,
    )
    subtitle = fonts.hint_font.render(
        subtitle_text,
        True,
        MUTED_COLOR,
    )
    title_y = 44
    subtitle_y = title_y + title.get_height() + 8
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, subtitle_y))

    panel_w = min(700, max(360, width - 40))
    line_h = fonts.hint_font.get_height() + 3
    panel_top = subtitle_y + subtitle.get_height() + 10
    bottom_lines = 2 + (1 if state.status else 0)
    panel_max_h = max(180, height - panel_top - (bottom_lines * line_h) - 10)
    header_count = sum(
        1 for kind, _label, _row_key in _UNIFIED_SETTINGS_ROWS if kind == "header"
    )
    item_count = sum(
        1 for kind, _label, _row_key in _UNIFIED_SETTINGS_ROWS if kind == "item"
    )
    header_step_default = fonts.hint_font.get_height() + 10
    item_step_default = 46
    required_default = (
        18 + (header_count * header_step_default) + (item_count * item_step_default)
    )
    scale = min(1.0, panel_max_h / max(1, required_default))
    header_step = max(
        fonts.hint_font.get_height() + 4, int(header_step_default * scale)
    )
    item_step = max(fonts.menu_font.get_height() + 8, int(item_step_default * scale))
    panel_h = min(
        panel_max_h, 18 + (header_count * header_step) + (item_count * item_step) + 8
    )
    panel_x = (width - panel_w) // 2
    panel_y = max(
        panel_top,
        min((height - panel_h) // 2, height - panel_h - (bottom_lines * line_h) - 8),
    )
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    selected_row_idx = _UNIFIED_SELECTABLE[state.selected]
    y = panel_y + 14
    panel_bottom = panel_y + panel_h - 8
    label_left = panel_x + 22
    label_right = panel_x + panel_w - 22
    for idx, (row_kind, label, row_key) in enumerate(_UNIFIED_SETTINGS_ROWS):
        if y > panel_bottom:
            break
        if row_kind == "header":
            header_text = fit_text(fonts.hint_font, label, panel_w - 44)
            header = fonts.hint_font.render(header_text, True, (182, 206, 255))
            screen.blit(header, (panel_x + 22, y + 3))
            y += header_step
            continue

        if y + fonts.menu_font.get_height() > panel_bottom:
            break
        selected = idx == selected_row_idx
        color = HIGHLIGHT_COLOR if selected else TEXT_COLOR
        if selected:
            hi = pygame.Surface(
                (panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA
            )
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 4))
        value = _unified_value_text(state, row_key)
        value_width = int(panel_w * 0.34) if value else 0
        value_draw = fit_text(fonts.menu_font, value, value_width)
        value_surf = (
            fonts.menu_font.render(value_draw, True, color) if value_draw else None
        )
        value_x = label_right - (
            value_surf.get_width() if value_surf is not None else 0
        )
        label_width = max(
            80, value_x - label_left - 10 if value_surf is not None else panel_w - 44
        )
        label_draw = fit_text(fonts.menu_font, label, label_width)
        label_surf = fonts.menu_font.render(label_draw, True, color)
        screen.blit(label_surf, (label_left, y))
        if value_surf is not None:
            screen.blit(value_surf, (value_x, y))
        y += item_step

    hints = (
        "Up/Down select   Left/Right adjust   Enter activate",
        "F5 save   F8 reset defaults   Esc back",
    )
    hy = panel_y + panel_h + 8
    max_hint_lines = max(0, (height - hy - 6) // max(1, line_h))
    hint_budget = max(0, max_hint_lines - (1 if state.status else 0))
    for line in hints[:hint_budget]:
        line_text = fit_text(fonts.hint_font, line, width - 28)
        surf = fonts.hint_font.render(line_text, True, MUTED_COLOR)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3

    if state.status and hy + line_h <= height - 6:
        color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 28)
        surf = fonts.hint_font.render(status_text, True, color)
        screen.blit(surf, ((width - surf.get_width()) // 2, hy + 2))


def _dispatch_unified_key(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
    key: int,
) -> pygame.Surface:
    if key == pygame.K_ESCAPE:
        state.running = False
        return screen
    if key == pygame.K_UP:
        state.pending_reset_confirm = False
        state.selected = (state.selected - 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_DOWN:
        state.pending_reset_confirm = False
        state.selected = (state.selected + 1) % len(_UNIFIED_SELECTABLE)
        play_sfx("menu_move")
        return screen
    if key == pygame.K_F5:
        state.pending_reset_confirm = False
        return _save_unified_settings(screen, state)
    if key == pygame.K_F8:
        if not state.pending_reset_confirm:
            state.pending_reset_confirm = True
            _set_unified_status(state, "Press F8 again to confirm reset defaults")
            return screen
        return _reset_unified_settings(screen, state)
    if _adjust_unified_with_arrows(state, key):
        return screen
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return _handle_unified_enter(screen, state)
    return screen


def _process_unified_events(
    screen: pygame.Surface,
    state: _UnifiedSettingsState,
) -> tuple[pygame.Surface, bool]:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return screen, False
        if event.type != pygame.KEYDOWN:
            continue
        screen = _dispatch_unified_key(screen, state, event.key)
        if not state.running:
            break
    return screen, True


def run_settings_hub_menu(
    screen: pygame.Surface,
    fonts,
    *,
    audio_settings: AudioSettings,
    display_settings: DisplaySettings,
) -> SettingsHubResult:
    score_logging_enabled = _load_score_logging_setting()
    overlay_transparency = _load_overlay_transparency_setting()
    game_seed = _load_game_seed_setting()
    random_mode_index = _load_random_mode_setting()
    topology_advanced = _load_topology_advanced_setting()
    state = _UnifiedSettingsState(
        audio_settings=_clone_audio_settings(audio_settings),
        display_settings=_clone_display_settings(display_settings),
        overlay_transparency=overlay_transparency,
        game_seed=game_seed,
        random_mode_index=random_mode_index,
        topology_advanced=topology_advanced,
        score_logging_enabled=score_logging_enabled,
        original_audio=_clone_audio_settings(audio_settings),
        original_display=_clone_display_settings(display_settings),
        original_overlay_transparency=overlay_transparency,
        original_game_seed=game_seed,
        original_random_mode_index=random_mode_index,
        original_topology_advanced=topology_advanced,
        original_score_logging_enabled=score_logging_enabled,
    )
    ok_layout, msg_layout = _validate_unified_layout_against_policy()
    if not ok_layout:
        _set_unified_status(state, msg_layout, is_error=True)
    _sync_audio_preview(state.audio_settings)
    _sync_analytics_preview(state.score_logging_enabled)

    clock = pygame.time.Clock()
    keep_running = True
    while state.running:
        _dt = clock.tick(60)
        screen, keep_running = _process_unified_events(screen, state)
        if not keep_running or not state.running:
            break
        _draw_unified_settings_menu(screen, fonts, state)
        pygame.display.flip()

    if not state.saved:
        _sync_audio_preview(state.original_audio)
        _sync_analytics_preview(state.original_score_logging_enabled)
        restored_display = normalize_display_settings(state.original_display)
        screen = apply_display_mode(
            restored_display, preferred_windowed_size=restored_display.windowed_size
        )
        return SettingsHubResult(
            screen=screen,
            audio_settings=state.original_audio,
            display_settings=restored_display,
            keep_running=keep_running,
        )

    final_display = capture_windowed_display_settings(
        normalize_display_settings(state.display_settings)
    )
    return SettingsHubResult(
        screen=screen,
        audio_settings=state.audio_settings,
        display_settings=final_display,
        keep_running=keep_running,
    )
