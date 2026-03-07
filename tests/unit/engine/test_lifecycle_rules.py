import unittest

from tet4d.engine.core.rules.lifecycle import (
    advance_or_lock_and_respawn,
    lock_and_respawn,
    run_hard_drop,
)


class _StubConfig:
    def __init__(self, exploration_mode: bool = False):
        self.exploration_mode = exploration_mode


class _StubState:
    def __init__(
        self,
        *,
        game_over_after_lock: bool = False,
        exploration_mode: bool = False,
        has_piece: bool = True,
    ):
        self.config = _StubConfig(exploration_mode=exploration_mode)
        self.game_over = False
        self.current_piece = object() if has_piece else None
        self.lock_calls = 0
        self.spawn_calls = 0
        self.game_over_after_lock = game_over_after_lock

    def lock_current_piece(self) -> int:
        self.lock_calls += 1
        if self.game_over_after_lock:
            self.game_over = True
        return 2

    def spawn_new_piece(self) -> None:
        self.spawn_calls += 1


class TestLifecycleRules(unittest.TestCase):
    def test_lock_and_respawn_spawns_when_lock_survives(self):
        state = _StubState()

        cleared = lock_and_respawn(state)

        self.assertEqual(cleared, 2)
        self.assertEqual(state.lock_calls, 1)
        self.assertEqual(state.spawn_calls, 1)

    def test_lock_and_respawn_skips_spawn_on_game_over(self):
        state = _StubState(game_over_after_lock=True)

        cleared = lock_and_respawn(state)

        self.assertEqual(cleared, 2)
        self.assertEqual(state.lock_calls, 1)
        self.assertEqual(state.spawn_calls, 0)

    def test_advance_or_lock_and_respawn_does_not_lock_when_advance_succeeds(self):
        state = _StubState()
        calls = {"advance": 0}

        def _advance() -> bool:
            calls["advance"] += 1
            return True

        result = advance_or_lock_and_respawn(state, try_advance=_advance)

        self.assertIs(result, state)
        self.assertEqual(calls["advance"], 1)
        self.assertEqual(state.lock_calls, 0)
        self.assertEqual(state.spawn_calls, 0)

    def test_run_hard_drop_uses_exploration_respawn(self):
        state = _StubState(exploration_mode=True)
        advanced = {"count": 0}

        def _advance() -> bool:
            advanced["count"] += 1
            return True

        run_hard_drop(state, try_advance=_advance)

        self.assertEqual(advanced["count"], 0)
        self.assertEqual(state.lock_calls, 0)
        self.assertEqual(state.spawn_calls, 1)

    def test_run_hard_drop_advances_until_blocked_then_locks(self):
        state = _StubState()
        attempts = {"count": 0}

        def _advance() -> bool:
            attempts["count"] += 1
            return attempts["count"] < 4

        run_hard_drop(state, try_advance=_advance)

        self.assertEqual(attempts["count"], 4)
        self.assertEqual(state.lock_calls, 1)
        self.assertEqual(state.spawn_calls, 1)


if __name__ == "__main__":
    unittest.main()
