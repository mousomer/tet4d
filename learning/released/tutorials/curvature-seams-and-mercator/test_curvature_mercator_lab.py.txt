"""Regression tests for Chapter 2's educational calculations."""

import math
import unittest
from itertools import pairwise

from curvature_mercator_lab import (
    SURFACES,
    cone_defects,
    left_cell,
    mercator_distortion_samples,
    mercator_scale,
    mercator_y,
    quotient_summary,
    sphere_seam_map,
    sphere_seam_vector,
    vertex_classes,
)

SPHERE = "LB+ RT+"
PROJECTIVE = "LR- BT-"
ADJACENT_PROJECTIVE = "LB- RT+"

# Four-by-four edge adjacencies for the two selected presets. Each pair
# describes an undirected bond, independently of any board command.
SPHERE_BONDS = {frozenset(((0, t), (t, 0))) for t in range(4)} | {
    frozenset(((3, t), (t, 3))) for t in range(4)
}
PROJECTIVE_BONDS = {frozenset(((0, t), (3, 3 - t))) for t in range(4)} | {
    frozenset(((t, 0), (3 - t, 3))) for t in range(4)
}


DOMINO = ((0, 1), (1, 1))
DOMINO_TRACES = (
    (SPHERE, SPHERE_BONDS, ((1, 0), (0, 1)), ((2, 0), (1, 1)), False),
    (PROJECTIVE, PROJECTIVE_BONDS, ((3, 2), (0, 1)), DOMINO, True),
)


def right_cell(cell, size, projective):
    x, y = cell
    if x < size - 1:
        return x + 1, y
    if projective:
        return 0, size - 1 - y
    raise ValueError("the sphere Right witness takes interior steps only")


def bonded(first, second, seam_bonds):
    x, y = first
    u, v = second
    return abs(x - u) + abs(y - v) == 1 or frozenset((first, second)) in seam_bonds


def neighbors(cell, seam_bonds):
    return {
        (x, y) for x in range(4) for y in range(4) if bonded(cell, (x, y), seam_bonds)
    }


def path_bonds(pose, seam_bonds):
    return tuple(bonded(a, b, seam_bonds) for a, b in pairwise(pose))


class ChapterTwoTests(unittest.TestCase):
    def test_sphere_vertex_classes(self):
        self.assertEqual(
            vertex_classes(SURFACES["sphere"]), (("A",), ("B", "D"), ("C",))
        )

    def test_sphere_defects(self):
        d = cone_defects(SURFACES["sphere"])
        self.assertAlmostEqual(d[("A",)], 1.5 * math.pi)
        self.assertAlmostEqual(d[("B", "D")], math.pi)
        self.assertAlmostEqual(d[("C",)], 1.5 * math.pi)

    def test_gauss_bonnet_all_four(self):
        expected = {"sphere": 2, "projective": 1, "klein": 0, "torus": 0}
        for name, chi_expected in expected.items():
            with self.subTest(surface=name):
                chi, total = quotient_summary(SURFACES[name])
                self.assertEqual(chi, chi_expected)
                self.assertAlmostEqual(total, 2 * math.pi * chi)

    def test_flat_torus_and_klein(self):
        for name in ("torus", "klein"):
            self.assertTrue(
                all(abs(a) < 1e-12 for a in cone_defects(SURFACES[name]).values())
            )

    def test_sphere_seam_endpoints(self):
        for t in (0, 0.23, 0.77, 1):
            self.assertEqual(sphere_seam_map("L", 0, t), (t, 0))
            self.assertEqual(sphere_seam_map("R", 1, t), (t, 1))

    def test_sphere_seam_isometry(self):
        vx, vy = (3.0, -4.0)
        ux, uy = sphere_seam_vector(vx, vy)
        self.assertAlmostEqual(vx * vx + vy * vy, ux * ux + uy * uy)
        self.assertEqual(sphere_seam_vector(1, 0), (0, -1))

    def test_left_destinations_and_image_sizes(self):
        for size, counts in ((4, (13, 13, 16)), (8, (57, 57, 64))):
            for presentation, count in zip(
                (SPHERE, ADJACENT_PROJECTIVE, PROJECTIVE), counts
            ):
                with self.subTest(size=size, presentation=presentation):
                    image = {
                        left_cell(presentation, size, (x, y))
                        for x in range(size)
                        for y in range(size)
                    }
                    self.assertEqual(len(image), count)
        for presentation, target in (
            (SPHERE, (1, 0)),
            (ADJACENT_PROJECTIVE, (2, 0)),
            (PROJECTIVE, (3, 2)),
        ):
            self.assertEqual(left_cell(presentation, 4, (0, 1)), target)
            self.assertEqual(left_cell(presentation, 4, (2, 0)), (1, 0))

    def test_projective_right_is_left_inverse(self):
        for size in (4, 8):
            for x in range(size):
                for y in range(size):
                    source = (x, y)
                    # Compose both orders with Right derived from the paired edges.
                    self.assertEqual(
                        left_cell(PROJECTIVE, size, right_cell(source, size, True)),
                        source,
                    )
                    self.assertEqual(
                        right_cell(left_cell(PROJECTIVE, size, source), size, True),
                        source,
                    )

    def test_sphere_seam_return_uses_bottom_edge(self):
        start = (0, 1)
        target = left_cell(SPHERE, 4, start)
        self.assertEqual(target, (1, 0))
        inward = sphere_seam_vector(-1, 0)
        self.assertEqual(inward, (0, 1))
        x, y = target
        self.assertEqual(y, 0)
        self.assertIn(frozenset((target, (0, x))), SPHERE_BONDS)
        self.assertEqual((0, x), start)
        self.assertEqual(right_cell(target, 4, False), (2, 0))

    def test_reverse_clip_and_sphere_four_neighbors(self):
        for preset, seams, after_left, final, final_bond in DOMINO_TRACES:
            with self.subTest(preset=preset):
                proposed = tuple(left_cell(preset, 4, cell) for cell in DOMINO)
                self.assertEqual(proposed, after_left)
                self.assertEqual(path_bonds(DOMINO, seams), (True,))
                self.assertEqual(path_bonds(proposed, seams), (True,))
                after_right = tuple(
                    right_cell(cell, 4, preset == PROJECTIVE) for cell in proposed
                )
                self.assertEqual(after_right, final)
                self.assertEqual(len(set(after_right)), 2)
                self.assertEqual(path_bonds(after_right, seams), (final_bond,))
        self.assertEqual(
            neighbors((2, 0), SPHERE_BONDS), {(1, 0), (3, 0), (2, 1), (0, 2)}
        )
        self.assertNotIn((1, 1), neighbors((2, 0), SPHERE_BONDS))

    def test_left_up_right_clip(self):
        for preset, seams, after_left, expected, final in (
            (
                SPHERE,
                SPHERE_BONDS,
                ((1, 0), (0, 1)),
                ((1, 1), (0, 2)),
                ((2, 1), (1, 2)),
            ),
            (
                PROJECTIVE,
                PROJECTIVE_BONDS,
                ((3, 2), (0, 1)),
                ((3, 3), (0, 2)),
                ((0, 0), (1, 2)),
            ),
        ):
            with self.subTest(preset=preset):
                proposed = tuple(left_cell(preset, 4, cell) for cell in DOMINO)
                self.assertEqual(proposed, after_left)
                self.assertEqual(path_bonds(proposed, seams), (True,))
                after_up = tuple((x, y + 1) for x, y in proposed)
                self.assertEqual(after_up, expected)
                self.assertEqual(len(set(after_up)), 2)
                self.assertEqual(path_bonds(after_up, seams), (False,))

                after_right = tuple(
                    right_cell(cell, 4, preset == PROJECTIVE) for cell in after_up
                )
                self.assertEqual(after_right, final)
                self.assertEqual(path_bonds(after_right, seams), (False,))

    def test_left_rotate_right_clip(self):
        # The native conformance suite verifies the rotation proposals and commits.
        # Here, check bond preservation and the following independent board Right step.
        for preset, seams, before, rotated, final in (
            (
                SPHERE,
                SPHERE_BONDS,
                ((1, 0), (0, 1)),
                ((1, 0), (2, 0)),
                ((2, 0), (3, 0)),
            ),
            (
                PROJECTIVE,
                PROJECTIVE_BONDS,
                ((3, 2), (0, 1)),
                ((3, 2), (3, 3)),
                ((0, 1), (0, 0)),
            ),
        ):
            with self.subTest(preset=preset):
                self.assertEqual(
                    tuple(left_cell(preset, 4, cell) for cell in DOMINO), before
                )
                self.assertEqual(rotated[0], before[0])
                self.assertEqual(path_bonds(rotated, seams), (True,))
                after_right = tuple(
                    right_cell(cell, 4, preset == PROJECTIVE) for cell in rotated
                )
                self.assertEqual(after_right, final)
                self.assertEqual(path_bonds(after_right, seams), (True,))

    def test_projective_bijection_can_break_a_quotient_bond(self):
        source = ((1, 0), (2, 3))
        self.assertEqual(path_bonds(source, PROJECTIVE_BONDS), (True,))
        targets = tuple(left_cell(PROJECTIVE, 4, cell) for cell in source)
        self.assertEqual(targets, ((0, 0), (1, 3)))
        self.assertEqual(
            neighbors(targets[0], PROJECTIVE_BONDS), {(1, 0), (0, 1), (3, 3)}
        )
        self.assertEqual(path_bonds(targets, PROJECTIVE_BONDS), (False,))

    def test_collision_clip_commits_atomically(self):
        source = ((0, 1), (1, 1), (2, 1), (2, 0))
        for presentation, proposal, committed, seam_bonds in (
            (SPHERE, ((1, 0), (0, 1), (1, 1), (1, 0)), source, SPHERE_BONDS),
            (
                PROJECTIVE,
                ((3, 2), (0, 1), (1, 1), (1, 0)),
                ((3, 2), (0, 1), (1, 1), (1, 0)),
                PROJECTIVE_BONDS,
            ),
        ):
            targets = tuple(left_cell(presentation, 4, cell) for cell in source)
            self.assertEqual(targets, proposal)
            if presentation == SPHERE:
                self.assertEqual(targets[0], targets[3])
            result = targets if len(set(targets)) == len(source) else source
            self.assertEqual(result, committed)
            self.assertEqual(path_bonds(source, seam_bonds), (True, True, True))
            self.assertEqual(path_bonds(result, seam_bonds), (True, True, True))

    def test_mercator_equator_and_symmetry(self):
        self.assertAlmostEqual(mercator_y(0), 0)
        self.assertAlmostEqual(
            mercator_y(math.radians(60)), -mercator_y(math.radians(-60))
        )
        self.assertAlmostEqual(mercator_scale(0), 1)
        self.assertAlmostEqual(mercator_scale(math.radians(60)), 2)

    def test_mercator_distortion_increases(self):
        samples = mercator_distortion_samples()
        scales = [s for _, s, _ in samples]
        self.assertEqual(scales, sorted(scales))
        self.assertTrue(all(abs(a - s * s) < 1e-12 for _, s, a in samples))

    def test_mercator_nearest_latitudes_to_poles(self):
        pole_neighbor = math.nextafter(math.pi / 2, 0.0)
        north = mercator_y(pole_neighbor)
        south = mercator_y(-pole_neighbor)
        self.assertTrue(math.isfinite(north) and math.isfinite(south))
        self.assertGreater(north, 0)
        self.assertLess(south, 0)
        self.assertAlmostEqual(north, -south, delta=1e-12)
        self.assertAlmostEqual(north, 36.493254, delta=1e-6)
        self.assertAlmostEqual(south, -36.493254, delta=1e-6)

    def test_mercator_textbook_formula_and_radius(self):
        latitude = math.radians(35)
        expected = math.log(math.tan(math.pi / 4 + latitude / 2))
        self.assertAlmostEqual(mercator_y(latitude), expected)
        self.assertAlmostEqual(mercator_y(latitude, radius=3.5), 3.5 * expected)

    def test_mercator_pole_exclusion(self):
        for lat in (-math.pi / 2, math.pi / 2, math.nan):
            with self.assertRaises(ValueError):
                mercator_y(lat)

    def test_malformed_pairings_rejected(self):
        with self.assertRaises(ValueError):
            vertex_classes((("L", "R", +1), ("L", "T", +1)))
        with self.assertRaises(ValueError):
            vertex_classes((("L", "R", 0), ("B", "T", +1)))


if __name__ == "__main__":
    unittest.main()
