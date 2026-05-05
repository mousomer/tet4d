from __future__ import annotations

import ast
from pathlib import Path

from tet4d.ui.pygame.locked_cell_explosion.model import ExplosionSeedCell
from tet4d.ui.pygame.locked_cell_explosion.simulation import build_endgame_state


ROOT = Path(__file__).resolve().parents[3]


def _imports_for(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return imports


def test_model_and_simulation_do_not_import_pygame() -> None:
    package = ROOT / "src/tet4d/ui/pygame/locked_cell_explosion"

    assert "pygame" not in _imports_for(package / "model.py")
    assert "pygame" not in _imports_for(package / "simulation.py")


def test_headless_endgame_state_construction_works_without_renderer() -> None:
    state = build_endgame_state(
        locked_cells=(
            ExplosionSeedCell((0, 1, 1, 1), 2, "A"),
            ExplosionSeedCell((1, 1, 1, 1), 3, "A"),
        ),
        board_shape=(4, 4, 4, 4),
        dimension=4,
        preset="classic",
        seed=9001,
        settings={"endgame_live_cell_fraction": 1.0, "sound_enabled": False},
    )

    assert state.dimension == 4
    assert state.board_dims == (4, 4, 4, 4)
    assert len(state.particles) == 2
    assert all(len(particle.position_nd) == 4 for particle in state.particles)
    assert all(len(particle.velocity_nd) == 4 for particle in state.particles)
