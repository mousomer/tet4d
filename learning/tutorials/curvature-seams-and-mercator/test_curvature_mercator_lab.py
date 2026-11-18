"""Regression tests for Chapter 2's educational calculations."""

import math
import unittest

from curvature_mercator_lab import (
    SURFACES,
    cone_defects,
    mercator_distortion_samples,
    mercator_scale,
    mercator_y,
    quotient_summary,
    sphere_seam_map,
    sphere_seam_vector,
    vertex_classes,
)


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
