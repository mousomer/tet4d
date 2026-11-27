"""Chapter 1, Example 1: enumerate all disjoint square-edge gluings."""

from collections import Counter

from square_gluings import all_gluings, label

for complete in (True, False):
    gluings = all_gluings(complete=complete)
    print(f"\n{'COMPLETE' if complete else 'INCLUDING FREE EDGES'}: {len(gluings)}")
    print(
        "Number of pairs -> configurations:",
        dict(sorted(Counter(len(g) for g in gluings).items())),
    )
    for g in gluings:
        print("  ", label(g))

assert len(all_gluings(True)) == 12
assert len(all_gluings(False)) == 25
