# Learning

Educational material accompanying Tet4D. These are learning resources, not engine or gameplay authorities.

- [Tutorials](tutorials/README.md) — guided mathematical and computational lessons.
- [From a square to Boy's surface](projective-plane-sequence/README.md) — illustrated sequence gluing a square into an immersion of the projective plane.
- [Gluing a square into closed surfaces](surface-sequences/README.md) — the same kind of sequence for the sphere, torus and Klein bottle, with the four gluing diagrams side by side.
- [Boy's surface viewer](boys-surface-viewer/README.md) — interactive frosted-glass Boy's surface: glue the square into it with a slider, rotate it at any moment, show its self-intersections and membranes.

- [Offline browser edition](released/index.html) — open this file in a browser, or copy the entire `released/` folder to another device. Rebuild from the tutorial sources with `python3 learning/build_release.py` from the repository root (requires Pandoc).

The browser edition renders inline TeX, display math, and fenced `math` blocks as offline MathML. The build fails if Pandoc warns that an equation could not be converted.

- [Embed on a website](released/embed.html) — install the complete release folder and paste the JavaScript or iframe snippet.
