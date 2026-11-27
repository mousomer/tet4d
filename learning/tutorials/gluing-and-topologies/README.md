# Chapter 1 — Gluing Edges and Recognizing Topological Surfaces

[Read the chapter](chapter_01_gluing_and_topologies.md).

This is the editable Markdown edition of the tutorial with a source SVG figure and the accompanying Python laboratory. The chapter's Appendix A contains complete copies of the five standalone Python files. The separate files are authoritative for execution; the appendix is for reading.

## Files

- `chapter_01_gluing_and_topologies.md` — mathematical chapter and fully explained code listings.
- `square_edge_parameters.svg` — source vector illustration referenced by the chapter.
- `square_gluings.py` — enumerator, dihedral-group action, quotient invariants and classifier.
- `01_enumerate.py` — enumerate all complete and partial edge gluings.
- `02_d4_orbits.py` — reduce by square symmetry and check Burnside's lemma.
- `03_classify.py` — classify representative quotient surfaces.
- `test_square_gluings.py` — eight regression tests.

## Run from the repository root

Uses Python 3.10+ and only the standard library. Use the repository-resolved interpreter:

```bash
PY="$(./scripts/resolve_python_env.sh)"
"$PY" learning/tutorials/gluing-and-topologies/01_enumerate.py
"$PY" learning/tutorials/gluing-and-topologies/02_d4_orbits.py
"$PY" learning/tutorials/gluing-and-topologies/03_classify.py
"$PY" -m unittest discover -s learning/tutorials/gluing-and-topologies -p 'test_square_gluings.py' -v
```

Expected summary: 12 complete gluings, 6 classes under `D4`, and 4 closed-surface classes; with unglued edges, 25 configurations, 11 symmetry orbits, 7 surface classes.

## Scope

This chapter studies **continuous quotients of one square**, not Tet4D's runtime cell movement. It neither replaces the [Explorer topology certification contract](../../../docs/architecture/explorer_topology_catalog_certification_contract.md) nor establishes authority over native/Godot implementations. Python source and Markdown are versioned here; the previously produced Word edition is not a required execution artifact.
