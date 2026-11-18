"""Chapter 1, Example 3: quotient vertices, Euler characteristic, topology."""
from collections import Counter
from square_gluings import all_gluings, classify, label, orbits, vertex_classes

for complete in (True, False):
    gluings = all_gluings(complete=complete)
    counts = Counter(classify(g)["name"] for g in gluings)
    print(f"\nSURFACES ({'complete' if complete else 'partial + complete'})")
    for topology, count in sorted(counts.items()):
        print(f"  {topology:25s}: {count} raw gluings")
    print("\nRepresentative of each D4 orbit:")
    for members in orbits(gluings):
        g = members[0]
        data = classify(g)
        print(f"  {label(g):16s} | orbit={len(members)} "
              f"| V={data['V']} E={data['E']} F={data['F']} "
              f"| chi={data['chi']:2d} b={data['boundary']} "
              f"| orientable={str(data['orientable']):5s} | {data['name']}")
        assert all(classify(member) == data for member in members)
    assert len(counts) == (4 if complete else 7)
