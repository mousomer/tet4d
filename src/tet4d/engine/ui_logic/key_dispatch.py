from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from tet4d.ui.pygame.keybindings import key_matches


KeyTuple = tuple[int, ...]


ActionHandler = Callable[[], None]


def match_bound_action(
    key: int,
    bindings: Mapping[str, KeyTuple],
    ordered_actions: Sequence[str],
) -> str | None:
    for action in ordered_actions:
        if key_matches(bindings, action, key):
            return action
    return None


def dispatch_bound_action(
    key: int,
    bindings: Mapping[str, KeyTuple],
    handlers: Mapping[str, ActionHandler],
) -> str | None:
    for action, handler in handlers.items():
        if key_matches(bindings, action, key):
            handler()
            return action
    return None
