# Chapter 2 — Curvature, Seam Traversal, and Mercator Maps

[Read Chapter 2](chapter_02_curvature_seams_and_mercator.md) or [return to the tutorial index](../README.md).

This chapter distinguishes the topology of a quotient from the metric on it, the coordinate atlas used to display it, and the discrete movement operator. It derives the cone-angle defects of Tet4D's single-square sphere, explores seam direction changes, and derives spherical Mercator projection and its distortion.

## Reproducible Python laboratory

- `curvature_mercator_lab.py` — vertex equivalence, cone defects, discrete Gauss–Bonnet checks, illustrative sphere seam mappings, Mercator projection and scale.
- `test_curvature_mercator_lab.py` — ten standard-library regression tests.

From the repository root:

~~~sh
PY="$(./scripts/resolve_python_env.sh)"
"$PY" learning/tutorials/curvature-seams-and-mercator/curvature_mercator_lab.py
"$PY" -m unittest discover -s learning/tutorials/curvature-seams-and-mercator -p 'test_curvature_mercator_lab.py' -v
~~~

The independent script requires Python 3.10+ and no third-party packages. Expected totals are: sphere `χ=2`, angular defect `4π`; projective plane `χ=1`, defect `2π`; torus and Klein bottle `χ=0`, defect zero.

**Limits:** The lab assumes its four named complete square-pairing examples already satisfy the local vertex-link tests. It does not prove manifold status for arbitrary user-entered gluing data. Seam maps are local planar unfoldings, not the game's C++/Godot cell-step resolver. The tutorial creates no runtime, engine, certification, or authority change.
