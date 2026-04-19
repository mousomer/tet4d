from __future__ import annotations

import unittest

from tet4d.engine.runtime.topology_playground_state import (
    PRESET_SOURCE_EXPLORER,
)
from tet4d.engine.topology_explorer.presets import (
    explorer_preset_sections_for_dimension,
    explorer_presets_for_dimension,
    preset_display_label,
)
from tet4d.ui.pygame.topology_lab import scene_state_canonical


class TestTopologyPresetGroups(unittest.TestCase):
    def test_registry_metadata_marks_sphere_like_presets_honestly(self) -> None:
        sphere = next(
            preset
            for preset in explorer_presets_for_dimension(3)
            if preset.preset_id == "sphere_3d"
        )

        self.assertEqual(sphere.group, "sphere_like")
        self.assertEqual(sphere.mathematical_status, "transport_heuristic")
        self.assertEqual(sphere.recommended_for, "explorer")
        self.assertFalse(sphere.gravity_safe)
        self.assertIn("Sphere-Like", sphere.label)

    def test_sections_keep_sphere_like_family_out_of_clean_quotient_groups(self) -> None:
        sections = explorer_preset_sections_for_dimension(4)
        grouped_ids = {
            section.group: {preset.preset_id for preset in section.presets}
            for section in sections
        }

        self.assertIn("sphere_4d", grouped_ids["sphere_like"])
        self.assertIn("full_wrap_4d", grouped_ids["quotient_core"])
        self.assertIn("projective_4d", grouped_ids["quotient_advanced"])
        self.assertNotIn("sphere_4d", grouped_ids["quotient_core"])
        self.assertNotIn("sphere_4d", grouped_ids["quotient_advanced"])

    def test_flat_list_reuses_grouped_section_authority(self) -> None:
        sections = explorer_preset_sections_for_dimension(2)
        flattened = tuple(
            preset
            for section in sections
            for preset in section.presets
        )

        self.assertEqual(flattened, explorer_presets_for_dimension(2))

    def test_grouped_display_label_surfaces_family_in_ui_text(self) -> None:
        sphere = next(
            preset
            for preset in explorer_presets_for_dimension(2)
            if preset.preset_id == "sphere_2d"
        )

        self.assertEqual(
            preset_display_label(sphere, include_group=True, include_unsafe=True),
            "Sphere-Like / Compactified Transport: Sphere-Like Transport [unsafe]",
        )

    def test_grouped_display_label_marks_advanced_quotient_presets_separately(self) -> None:
        projective = next(
            preset
            for preset in explorer_presets_for_dimension(2)
            if preset.preset_id == "projective_2d"
        )

        self.assertEqual(
            preset_display_label(projective, include_group=True, include_unsafe=True),
            "Advanced Quotient Topologies: Projective Plane [unsafe]",
        )

    def test_canonical_preset_selection_preserves_group_metadata(self) -> None:
        sphere = next(
            preset
            for preset in explorer_presets_for_dimension(3)
            if preset.preset_id == "sphere_3d"
        )

        selection = scene_state_canonical._runtime_explorer_preset_selection_from_value(
            3,
            sphere.profile,
        )

        self.assertEqual(selection.source, PRESET_SOURCE_EXPLORER)
        self.assertEqual(selection.preset_id, sphere.preset_id)
        self.assertEqual(selection.group, sphere.group)
        self.assertEqual(
            selection.mathematical_status,
            sphere.mathematical_status,
        )
        self.assertEqual(selection.recommended_for, sphere.recommended_for)
        self.assertEqual(selection.gravity_safe, sphere.gravity_safe)


if __name__ == "__main__":
    unittest.main()
