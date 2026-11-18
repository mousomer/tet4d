"""Standard-library regression tests for Chapter 1's examples."""
import unittest
from collections import Counter

from square_gluings import (
    D4, all_gluings, classify, normalize, orbit, orbits,
    transform, vertex_classes,
)


class SquareGluingTests(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(len(all_gluings(True)), 12)
        self.assertEqual(len(all_gluings(False)), 25)
        self.assertEqual(len(orbits(all_gluings(True))), 6)
        self.assertEqual(len(orbits(all_gluings(False))), 11)

    def test_closed_surface_distribution(self):
        counts = Counter(classify(g)['name'] for g in all_gluings(True))
        self.assertEqual(counts, {
            'torus': 1, 'Klein bottle': 4,
            'projective plane (RP²)': 5, 'sphere': 2,
        })

    def test_partial_surface_set(self):
        got = {classify(g)['name'] for g in all_gluings(False)}
        self.assertEqual(got, {
            'disk', 'annulus / cylinder', 'Möbius strip', 'sphere',
            'torus', 'Klein bottle', 'projective plane (RP²)',
        })

    def test_torus_and_sphere_examples(self):
        torus = normalize([('L', 'R', 1), ('B', 'T', 1)])
        sphere = normalize([('L', 'B', 1), ('R', 'T', 1)])
        self.assertEqual(classify(torus)['chi'], 0)
        self.assertEqual(classify(torus)['name'], 'torus')
        self.assertEqual(classify(sphere)['chi'], 2)
        self.assertEqual(classify(sphere)['name'], 'sphere')
        self.assertEqual(len(vertex_classes(sphere)), 3)

    def test_legacy_negative_adjacent_is_klein(self):
        legacy = normalize([('L', 'B', -1), ('R', 'T', -1)])
        self.assertEqual(classify(legacy)['name'], 'Klein bottle')
        self.assertFalse(classify(legacy)['orientable'])

    def test_action_preserves_topology(self):
        for g in all_gluings(False):
            original = classify(g)
            for s in D4:
                self.assertEqual(classify(transform(g, s)), original)

    def test_burnside(self):
        for complete, expected in ((True, 6), (False, 11)):
            gluings = all_gluings(complete)
            self.assertEqual(
                sum(sum(transform(g, s) == g for g in gluings) for s in D4),
                8 * expected,
            )

    def test_orbits_are_disjoint(self):
        for complete in (True, False):
            groups = orbits(all_gluings(complete))
            flattened = [g for o in groups for g in o]
            self.assertEqual(len(flattened), len(set(flattened)))
            self.assertEqual(set(flattened), set(all_gluings(complete)))


if __name__ == '__main__':
    unittest.main()
