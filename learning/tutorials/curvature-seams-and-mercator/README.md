# Chapter 2 — Curvature, Seam Traversal, and Mercator Maps

[Read Chapter 2](chapter_02_curvature_seams_and_mercator.md) or [return to the tutorial index](../README.md).

This chapter distinguishes the topology of a quotient from the metric on it, the coordinate atlas used to display it, and the discrete movement operator. It derives the cone-angle defects of Tet4D's single-square sphere, explores seam direction changes, and derives spherical Mercator projection and its distortion.

## Interactive Earth on the S² square

Get the repository checkout and open `learning/tutorials/curvature-seams-and-mercator/interactive-earth/index.html` in a browser. Keep the adjacent JavaScript, CSS and generated land mask together. The [HTML link](interactive-earth/index.html) on GitHub shows the source. See the [demo guide and dataset attribution](interactive-earth/README.md).

## Reproducible Python laboratory

- `curvature_mercator_lab.py` — vertex equivalence, cone defects, discrete Gauss–Bonnet checks, illustrative sphere seam mappings, three educational Left maps, Mercator projection and scale.
- `test_curvature_mercator_lab.py` — 20 standard-library regression tests.

From the repository root:

~~~sh
PY="$(./scripts/resolve_python_env.sh)"
"$PY" learning/tutorials/curvature-seams-and-mercator/curvature_mercator_lab.py
"$PY" -m unittest discover -s learning/tutorials/curvature-seams-and-mercator -p 'test_curvature_mercator_lab.py' -v
~~~

The independent script requires Python 3.10+ and no third-party packages. Expected totals are: sphere `χ=2`, angular defect `4π`; projective plane `χ=1`, defect `2π`; torus and Klein bottle `χ=0`, defect zero.

**Limits:** The lab assumes its four named complete square-pairing examples already satisfy the local vertex-link tests. It does not prove manifold status for arbitrary user-entered gluing data. The continuous seam examples are local planar unfoldings. The Left examples model one board command on three specified square presentations.

## Regenerate the seam animations

The chapter includes the GIFs and a static transcript. To regenerate the GIFs, install Pillow in a Python 3.9+ environment and make DejaVu Sans or Arial (regular and bold) available. From the repository root, run:

~~~sh
PY="$(./scripts/resolve_python_env.sh)"
cd learning/tutorials/curvature-seams-and-mercator/animations
"$PY" animate_seams.py --out .
~~~

[animate_seams.py](animations/animate_seams.py) renders the two matched boards using the educational paths and quotient neighbors in [seam_paths.py](animations/seam_paths.py). Each translation uses 40 eased samples at 25 fps. The piece rotation shows the native-verified before and after poses. The chapter lab tests independently check the coordinates, bonds and collision.

From the repository root, \`./scripts/test_godot_tet4d_core.sh --explorer-piece-conformance\` checks both domino sequences through the native Explorer proposal and commit path.
