"""The scaffold migration must retain shared palette ownership for every role."""

import pytest

from tools.governance import validate_live_board_visual_roles as validator


def test_current_renderer_uses_all_shared_scaffold_materials() -> None:
    assert validator._grid_issues(validator.GRID.read_text()) == []


@pytest.mark.parametrize(
    "consumer",
    [
        "board_scaffold_material",
        "board_enclosure_material",
        "board_internal_scaffold_material",
        "board_active_frame_material",
    ],
)
def test_missing_semantic_material_consumer_is_rejected(consumer: str) -> None:
    source = validator.GRID.read_text().replace(
        f"ReplayVisuals.{consumer}", "local_unowned_material"
    )
    assert any(consumer in issue for issue in validator._grid_issues(source))
