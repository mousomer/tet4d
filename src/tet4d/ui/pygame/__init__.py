"""pygame UI adapters."""


def run_2d() -> None:
    from tet4d.ui.pygame.front2d_game import run

    run()


def run_3d() -> None:
    from tet4d.ui.pygame.front3d_game import run

    run()


def run_4d() -> None:
    from tet4d.ui.pygame.front4d_game import run

    run()


__all__ = ["run_2d", "run_3d", "run_4d"]
