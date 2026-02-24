from __future__ import annotations

import unittest

from tetris_nd.topology import (
    TOPOLOGY_INVERT_ALL,
    TOPOLOGY_WRAP_ALL,
    TopologyPolicy,
    map_overlay_cells,
    map_piece_cells,
    normalize_topology_mode,
)


class TestTopology(unittest.TestCase):
    def test_normalize_mode(self) -> None:
        self.assertEqual(normalize_topology_mode(" bounded "), "bounded")
        self.assertEqual(normalize_topology_mode("wrap_all"), "wrap_all")
        with self.assertRaises(ValueError):
            normalize_topology_mode("unknown")

    def test_wrap_all_maps_non_gravity_axes(self) -> None:
        policy = TopologyPolicy(dims=(4, 8, 4), gravity_axis=1, mode=TOPOLOGY_WRAP_ALL)
        self.assertEqual(policy.map_coord((-1, 3, 4), allow_above_gravity=True), (3, 3, 0))
        self.assertIsNone(policy.map_coord((1, 8, 1), allow_above_gravity=True))

    def test_invert_all_mirrors_other_wrapped_axes(self) -> None:
        policy = TopologyPolicy(dims=(4, 8, 4), gravity_axis=1, mode=TOPOLOGY_INVERT_ALL)
        # Crossing x edge wraps x and mirrors z.
        self.assertEqual(policy.map_coord((-1, 2, 1), allow_above_gravity=True), (3, 2, 2))

    def test_piece_mapping_rejects_duplicate_wrapped_cells(self) -> None:
        policy = TopologyPolicy(dims=(2, 6, 2), gravity_axis=1, mode=TOPOLOGY_WRAP_ALL)
        mapped = map_piece_cells(
            policy,
            ((-1, 2, 0), (1, 2, 0)),
            allow_above_gravity=True,
        )
        self.assertIsNone(mapped)

    def test_invert_piece_mapping_keeps_seam_straddling_piece_unique(self) -> None:
        policy = TopologyPolicy(dims=(6, 14, 4, 3), gravity_axis=1, mode=TOPOLOGY_INVERT_ALL)
        mapped = map_piece_cells(
            policy,
            (
                (0, 1, 3, 2),
                (-1, 1, 3, 2),
                (1, 1, 3, 2),
                (0, 2, 3, 3),
                (0, 1, 4, 3),
            ),
            allow_above_gravity=True,
        )
        self.assertIsNotNone(mapped)
        assert mapped is not None
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_overlay_mapping_wraps_visual_cells(self) -> None:
        policy = TopologyPolicy(dims=(4, 8, 4), gravity_axis=1, mode=TOPOLOGY_WRAP_ALL)
        mapped = map_overlay_cells(
            policy,
            ((-0.25, 3.0, 1.5), (4.10, 3.0, 1.5)),
            allow_above_gravity=False,
        )
        self.assertEqual(len(mapped), 2)
        for x, y, z in mapped:
            self.assertTrue(0.0 <= x < 4.0)
            self.assertTrue(0.0 <= y < 8.0)
            self.assertTrue(0.0 <= z < 4.0)


if __name__ == "__main__":
    unittest.main()
