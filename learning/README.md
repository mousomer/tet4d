# Learning

Educational material accompanying Tet4D. These are learning resources, not engine or gameplay authorities.

This material lives on the **`learning-surfaces`** branch and is not merged into master; master keeps only
chapters 1 and 2 and the interactive Earth. [manifest.json](manifest.json) locks the branch and lists every
component with its entry page, generator scripts, docs and checks; [INDEX.md](INDEX.md) is the index
generated from it. `python3 learning/check_manifest.py` checks the manifest, the index, the links in the docs
and the offline edition. [SECURITY.md](SECURITY.md) records the security review and how to repeat it.

## Tutorials

- [Tutorials](tutorials/README.md) — guided mathematical and computational lessons (chapters 1–3; see each
  chapter's README: [1](tutorials/gluing-and-topologies/README.md), [2](tutorials/curvature-seams-and-mercator/README.md),
  [3](tutorials/seam-comparisons/README.md)).
- [Six square gluings](tutorials/gluing-and-topologies/square-gluings/index.html) — chapter 1's gluings built
  step by step, with stills, rotatable models and a [rebuild guide](tutorials/gluing-and-topologies/square-gluings/REBUILD.md).
- [Square gluing viewers](tutorials/gluing-and-topologies/square-gluings/viewers/index.html) — the six gluings,
  the classic glass Klein bottle and the Bryant–Kusner Boy's surface (with the Boy viewer's shape controls) as
  interactive pages: glue in two stages or one stretch, set the speed, step, rotate, with or without cone points.

## Surfaces

- [Boy's surface viewer](boys-surface-viewer/README.md) — interactive frosted-glass Boy's surface: glue the
  square into it with a slider, rotate it at any moment, show its self-intersections and membranes.
- [From a square to Boy's surface](projective-plane-sequence/README.md) — illustrated sequence gluing a square
  into an immersion of the projective plane.
- [Gluing a square into closed surfaces](surface-sequences/README.md) — the same kind of sequence for the
  [sphere](sphere-sequence/README.md), [torus](torus-sequence/README.md) and
  [Klein bottle](klein-bottle-sequence/README.md), with the four gluing diagrams side by side.

## Offline edition

- [Offline browser edition](released/index.html) — open this file in a browser, or copy the entire `released/`
  folder to another device. It carries the tutorials, the viewers and the sequences listed in the manifest.
  Rebuild with `python3 learning/build_release.py` from the repository root (requires Pandoc); after
  committing source changes, `python3 learning/build_release.py --lock` first pins the commit the edition
  links to for files it does not copy.

The browser edition renders inline TeX, display math, and fenced `math` blocks as offline MathML. The build fails if Pandoc warns that an equation could not be converted.

- [Embed on a website](released/embed.html) — install the complete release folder and paste the JavaScript or iframe snippet.
