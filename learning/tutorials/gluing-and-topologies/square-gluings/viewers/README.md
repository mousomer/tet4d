# Square gluing viewers

Interactive versions of the tutorial's six square gluings, plus the classic glass Klein bottle and Boy's
surface exactly as in the Boy's surface viewer. Each page glues one square into its closed surface; [index.html](index.html) is the menu.

| Page | Word | Result | Cone points |
|---|---|---|---|
| [sphere.html](sphere.html) | a b b⁻¹ a⁻¹ | sphere, χ = 2 | A (90°), B=D (180°), C (90°) |
| [rp2-adjacent.html](rp2-adjacent.html) | a b b a⁻¹ | projective plane, χ = 1 | A (90°), B=C=D (270°) |
| [rp2-opposite.html](rp2-opposite.html) | a b a b | projective plane, χ = 1 | A=C, B=D (180° each) |
| [torus.html](torus.html) | a b a⁻¹ b⁻¹ | torus, χ = 0 | none (360°) |
| [klein-adjacent.html](klein-adjacent.html) | a b b a | Klein bottle, χ = 0 | none (360°) |
| [klein-opposite.html](klein-opposite.html) | a b a⁻¹ b | Klein bottle, χ = 0 | none (360°) |
| [klein-bottle.html](klein-bottle.html) | a b a⁻¹ b | Klein bottle (the glass bottle), χ = 0 | none (360°) |
| [rp2-boy.html](rp2-boy.html) | a b a b | Boy's surface (Bryant–Kusner), χ = 1 | none: smooth (A=C, B=D at 180°) |

Each page is one self-contained HTML file (WebGL2, no network). Open it in a browser.

## Controls

- **Glue**: 0 is the flat square, 1 the closed surface. ▶ plays from wherever the slider is; Space
  plays or pauses.
- **Duration**: seconds for a full run, 3–30. Playback follows the clock, so a run takes this long at
  any frame rate.
- **Step**: the size of one step for the step buttons and the ← → keys.
- **Motion**:
  - *Two stages* (default) is the tutorial's construction: the orange edges a close first, then the
    cyan edges b.
  - *One stretch* moves every point at once from the flat square to its place on the surface, centre
    first and edges last, so all edges meet at the end.
- **Cone Points** (sphere and both projective planes):
  - *On*: corners whose angles sum to less than 360° stay sharp tips, as in the tutorial.
  - *Off*: the same gluing, smoothed. The sphere becomes round and the projective planes become the
    smooth Boy's surface.
  - The torus and Klein bottles have no cone point (their four corners meet at 360°), so the switch is
    disabled there.
- **Shape** (Boy's surface page): Length, Width, Protrusion and Twist, with presets, as in the Boy's
  surface viewer (where Protrusion is called Thickness). They change the finished surface, so the run is
  re-paced when they change.
- **Lines**: the square's grid, the edges, the arrows, the corner discs and the corner labels.
- **Material** and **Scene**: the glass, a turntable, the floor shadow.
- **View**: drag to rotate, right-drag or Shift-drag to move, scroll to zoom, double-click to recentre.
  H hides the panel. Reset restores everything, including the view.
- **Link parameters**: `?glue=0.5&motion=stretch&cones=0&play=0` open a page at a given state. A page
  opened without `glue` plays once on load.

## What the pages show

The pages follow the tutorial's conventions:

- **Corners**: A–D run clockwise from the upper left.
- **Edges**: edge a is orange and edge b is cyan, and each word is read clockwise.
- **Arrows**: one arrow sits at the middle of each edge. The two sheets meeting at an edge each paint
  their own half of the band and of the arrow. On the flat square you see half-arrows; once two edges
  meet, the halves join into one band and one whole arrow.
- **Corner discs**: each corner gets a disc coloured by the point it becomes, so corners that will meet
  share a colour.
- **Labels** follow the corners and merge (B=D) once their edges are glued. When every edge at a point is
  glued, the label shows the angle sum: 90° per corner, a cone below 360°, "smoothed" with cone points
  off.
- **Status**: the panel tracks what the glued square is at each moment.
  - Each seam: open, closing (with its progress), or glued.
  - The space's name, from disk through cylinder or Möbius band to the closed surface.
  - χ = V − E + F, with F = 1, E = 1 per glued pair and 2 per open pair, and V = the corner classes.
  - Orientability: a glued pair with the same exponent reverses orientation.
  - The number of boundary circles.

## How it works

- **[src/surfaces.js](src/surfaces.js)**: the eight surfaces.
  - Each module is a line-for-line port of the tutorial's Python homotopy in [../rebuild/](../rebuild/):
    `tet4d_sphere_revised.py`, `directboy.py`, `orp.py`, `torus_direct.py`, `klein_direct.py`,
    `opklein.py`.
  - A module evaluates `point(X, Y, params(t), cone)` on the square [−1, 1]², along with its stage
    schedule (`fold` closes a, `puff` closes b), its edge pairing and its home pose.
  - The cone factor scales the cone-tip bumps of the two projective planes. On the sphere it blends the
    pillow toward a round sphere.
  - The projective planes' finished Boy surface (the expensive part) is cached per cone setting.
- **[src/template.html](src/template.html)**: the engine.
  - It reuses the [Boy's surface viewer](../../../../boys-surface-viewer/README.md) renderer unchanged:
    depth-peeled glass, frost, studio lighting, coloured floor shadow, FXAA.
  - On top of that it adds a 241 × 241 square mesh, painting in square coordinates, the motion and
    pacing, seam welding, the topology readout, the labels and the playback controls.
  - Once a seam closes, its two sides are welded: shared positions, averaged normals.
- **Pacing**: the slider is re-timed by how far the surface travels (70%) and by schedule time (30%).
  Equal slider steps make similar amounts of change, and the short pause between the two stages stays
  visible.
- **Scale**: fixed for a whole run, chosen from the largest extent over the run. The surface never
  "breathes"; on the sphere this means the flat diamond is larger than the finished pillow.
- **The glass bottle** ([klein-bottle.html](klein-bottle.html)) is this repo's own construction; the
  tutorial has no glass-bottle version. It has three stages:
  1. The square rolls into a cylinder (orange a), as on the torus page.
  2. The cylinder stands up and takes the shape of a bulb and a neck.
  3. The neck's open end travels along the bottle's core: up, over, down outside, through the wall and
     down inside. It flares to meet the bulb's bottom rim from inside (cyan b), while the bulb's half of
     the square stays put.

  The finished bottle is a tube around a periodic cubic B-spline core with a B-spline radius. The core
  has a cusp at the join: its control polygon is symmetric there, so the core arrives going down and
  leaves going up. That flip of the tube's direction is the Klein identification (−1, Y) ~ (1, −Y), and
  because the radius keeps growing through the join, the surface is smooth there.
- **Boy's surface** ([rp2-boy.html](rp2-boy.html)) ends on exactly the surface of the
  [Boy's surface viewer](../../../../boys-surface-viewer/README.md).
  - The surface is Bryant–Kusner with c = 0.95, at w = Fong's elliptical map of the square (the viewer's
    Square grid). The boundary of that disk is glued antipodally, which is the word a b a b.
  - The shape sliders are the viewer's map of space about the 3-fold axis: radial stretch, angular lobe
    width, axial stretch and a twist growing with height. Every setting is still an immersion.
  - The colours are the viewer's lobe colours, and the home pose is its view from the pole side.
  - The two stages are a staged stretch: each point moves straight from a flat square to its place on the
    surface, arriving at T(X, Y) = 0.35 (1 − ab) + 0.65 (1 − b) a, with a = 1 − Y² and b = 1 − X².
    - The centre arrives first.
    - The top and bottom edges arrive together at T = 0.35. The first stage ends there, as a Möbius band.
    - The left and right edges arrive last, closing the surface.
  - The flat square lies in the least-squares plane of the surface, scaled to the surface's size, so it
    stretches rather than inflates.
  - Slimming and Gap Width are not included. They are fields computed for the viewer's mesh, and could be
    ported the same way.
- **[build.py](build.py)**: inlines the modules into the template and writes the pages and the menu.
  It also holds the menu's table, which the checks compare with the modules.

## Rebuild, render, check

From the repository root:

```sh
PY=$(./scripts/resolve_python_env.sh)
$PY learning/tutorials/gluing-and-topologies/square-gluings/viewers/build.py   # pages + menu
cd learning/tutorials/gluing-and-topologies/square-gluings/viewers
python3 tools/render_gluing.py --surface all --glue 0:1:25 --anim     # frames, strips, animated WebP
python3 tools/render_gluing.py --surface sphere --cones both --view home --view 30,60
python3 tools/render_gluing.py --thumbs                                # img/<id>.webp for the menu (not kept in git)
python3 tools/check_viewers.py                                         # browser checks for all pages
```

The two tools need playwright and pillow, with playwright's Chromium or `--chrome /path/to/chrome`.

### render_gluing.py

It renders any glue values (`START:END:COUNT` or a list) from any views:

- **Views** are named (home, back, top, side) or given as tilt,turn in degrees, added to the page's
  default view.
- **Settings**: either motion (`--motion`), and with, without or both cone settings (`--cones`).
- **Output**: per surface and setting, the PNG frames, a strip, and with `--anim` an animated WebP per
  view.

### check_viewers.py

It checks each page:

- It loads with WebGL2 and no page errors.
- Its title, word and cone switch match `build.py`.
- **Seams**: the module's seams close exactly at the end (relative gap below 10⁻⁶, measured at 1001
  points per seam, with and without cones). The square starts flat.
- **Stages**: in two-stage motion seam a closes before seam b, and a closed seam stays closed.
- **Endpoints**: glue 0 is a disk. Glue 1 is the expected surface, with the right corner classes, χ and
  orientability, in both motions and both cone settings.
- **Painting**: edges and arrows paint visible pixels.
- **Playback**: a run takes its set duration. The step buttons step by the set size, and link
  parameters are read.

It also checks that the menu links every page and that its cards work without the thumbnails, which are
generated and not kept in the repository.

## Limits

- **Labels** are drawn over the surface, so a label stays visible even when its corner is behind a
  sheet.
- **Speed**: software rendering (no GPU) runs at a few frames per second. Playback keeps its duration
  but skips frames.
