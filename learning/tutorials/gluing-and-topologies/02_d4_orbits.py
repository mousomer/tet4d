"""Chapter 1, Example 2: D4 action and Burnside's lemma."""

from square_gluings import D4, all_gluings, label, orbits, symmetry_name, transform

for complete in (True, False):
    gluings = all_gluings(complete=complete)
    symmetry_orbits = orbits(gluings)
    fixed = [(symmetry_name(s), sum(transform(g, s) == g for g in gluings)) for s in D4]
    print(f"\n{len(gluings)} gluings -> {len(symmetry_orbits)} D4 orbits")
    for representative_orbit in symmetry_orbits:
        print(
            f"  {label(representative_orbit[0]):16s} "
            f"orbit size = {len(representative_orbit)}"
        )
    print("Fixed configurations:")
    for name, count in fixed:
        print(f"  {name:24s}: {count}")
    assert sum(count for _, count in fixed) == 8 * len(symmetry_orbits)
    assert sum(map(len, symmetry_orbits)) == len(gluings)
    assert len(symmetry_orbits) == (6 if complete else 11)
