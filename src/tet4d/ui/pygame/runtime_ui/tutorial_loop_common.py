from __future__ import annotations

import pygame


def tutorial_action_delay_ms(
    action_id: str,
    *,
    soft_drop_delay_ms: int,
    hard_drop_delay_ms: int,
    rotate_delay_ms: int,
    move_delay_ms: int,
) -> int:
    if action_id == "soft_drop":
        return int(soft_drop_delay_ms)
    if action_id == "hard_drop":
        return int(hard_drop_delay_ms)
    if action_id.startswith("rotate_"):
        return int(rotate_delay_ms)
    if action_id.startswith("move_"):
        return int(move_delay_ms)
    return 0


def tutorial_overlay_start_from_setup(payload: dict[str, object]) -> float | None:
    setup_payload = payload.get("setup")
    if not isinstance(setup_payload, dict):
        return None
    raw_percent = setup_payload.get("overlay_start_percent")
    if isinstance(raw_percent, bool) or not isinstance(raw_percent, int):
        return None
    return float(max(0, min(100, int(raw_percent)))) / 100.0


def running_tutorial_session(loop, *, tutorial_is_running):
    session = loop.tutorial_session
    if session is None or not tutorial_is_running(session):
        return None
    return session


def redo_tutorial_stage(loop, session, *, redo_stage, apply_pending_setup) -> None:
    if redo_stage(session):
        apply_pending_setup(loop)


def tutorial_required_action_blocked(
    session,
    *,
    required_action_runtime,
    required_action_legal,
) -> bool:
    required = required_action_runtime(session)
    return bool(required) and (not required_action_legal(required))


def tutorial_allowed_actions_blocked(
    session,
    *,
    allowed_actions_runtime,
    has_legal_action,
) -> bool:
    allowed_actions = allowed_actions_runtime(session)
    return bool(allowed_actions) and (not has_legal_action(allowed_actions))


def maintain_tutorial_runtime_safety(
    loop,
    *,
    min_visible_layer: int,
    running_tutorial_session,
    completion_ready,
    transition_pending,
    redo_tutorial_stage,
    tutorial_ensure_piece_visibility,
    tutorial_allowed_actions_blocked,
    tutorial_required_action_blocked,
) -> None:
    session = running_tutorial_session(loop)
    if session is None or completion_ready(session) or transition_pending(session):
        return
    if loop.state.game_over:
        redo_tutorial_stage(loop, session)
        return
    if not tutorial_ensure_piece_visibility(loop, int(min_visible_layer)):
        redo_tutorial_stage(loop, session)
        return
    if tutorial_allowed_actions_blocked(loop, session):
        redo_tutorial_stage(loop, session)
        return
    if tutorial_required_action_blocked(loop, session):
        redo_tutorial_stage(loop, session)


def handle_tutorial_hotkey(
    *,
    key: int,
    session,
    previous_stage,
    next_stage,
    redo_stage,
    skip_tutorial,
    restart_tutorial,
    apply_pending_setup,
    on_restart_loop,
    reset_cooldown,
    play_sfx,
) -> str | None:
    if session is None:
        return None
    stage_nav = {
        pygame.K_F5: previous_stage,
        pygame.K_F6: next_stage,
        pygame.K_F7: redo_stage,
    }
    step_action = stage_nav.get(key)
    if step_action is not None:
        if step_action(session):
            apply_pending_setup()
            reset_cooldown()
            play_sfx("menu_confirm" if key == pygame.K_F7 else "menu_move")
        return "continue"
    if key == pygame.K_F8:
        skip_tutorial(session)
        play_sfx("menu_move")
        return "menu"
    if key == pygame.K_F9:
        if restart_tutorial(session):
            apply_pending_setup()
            reset_cooldown()
        else:
            on_restart_loop()
        play_sfx("menu_confirm")
        return "continue"
    return None


def restart_loop_runtime_state(
    loop,
    *,
    create_initial_state,
    refresh_score_multiplier,
) -> None:
    loop.cfg.speed_level = int(loop.base_speed_level)
    loop.state = create_initial_state(loop.cfg)
    loop.gravity_accumulator = 0
    loop.clear_anim = None
    loop.last_lines_cleared = loop.state.lines_cleared
    loop.was_game_over = loop.state.game_over
    loop.mouse_orbit.reset()
    loop.bot.reset_runtime()
    loop.rotation_anim.reset()
    loop.tutorial_action_cooldown_ms = 0
    refresh_score_multiplier()


def refresh_score_multiplier_state(
    loop,
    *,
    off_mode,
    combined_score_multiplier,
) -> None:
    loop.state.score_multiplier = combined_score_multiplier(
        bot_mode=loop.bot.mode,
        grid_mode=loop.grid_mode,
        speed_level=loop.cfg.speed_level,
    )
    mode_name = loop.bot.mode.value
    loop.state.analysis_actor_mode = "human" if loop.bot.mode == off_mode else mode_name
    loop.state.analysis_bot_mode = mode_name
    loop.state.analysis_grid_mode = loop.grid_mode.value


def tutorial_sync(
    loop,
    *,
    lines_cleared: int,
    grid_mode_off,
    sync_and_advance,
    apply_pending_setup,
    tutorial_is_running,
) -> bool:
    session = loop.tutorial_session
    if session is None:
        return False
    progressed = sync_and_advance(
        session,
        lines_cleared=lines_cleared,
        overlay_transparency=float(loop.overlay_transparency),
        grid_visible=bool(loop.grid_mode != grid_mode_off),
        grid_mode=str(loop.grid_mode.value),
        board_cell_count=len(loop.state.board.cells),
    )
    apply_pending_setup(loop)
    if not tutorial_is_running(session):
        loop.tutorial_session = None
        loop.tutorial_action_cooldown_ms = 0
    return bool(progressed)
