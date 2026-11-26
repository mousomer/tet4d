# Boy's surface viewer: design

The viewer is one self-contained HTML file (`boys-surface-viewer.html`, about 1,700 lines, 290 KB). It
combines inline CSS, the WebGL2 renderer in plain JavaScript, and three embedded, compressed data
fields (the slimming flow, the membrane map and the gap map). It has no build step, makes no network requests and has no dependencies, so the file can be
opened locally or hosted as is.

## 1. Goals

1. **Correct topology.** Show Boy's surface as an immersion of ℝP² in ℝ³: one-sided, closed and
   without boundary. It passes through itself along a triple-point curve system, and it has no
   handles. The three "holes" are the entry points of three tubes, which all lead into the same
   central region.
2. **A frosted-glass look.** Match a reference render of translucent, frosted, coloured glass
   lobes with a soft floor shadow.
3. **Playable shape and material.** Let the reader change lobe length, width, thickness, interior
   slimming and twist, plus opacity, frost, gloss and colours, without ever breaking the topology.
4. **A link to the learning sequences.** Show on the finished surface the same square grid, glued
   edges and corner points that [the square-to-Boy's-surface sequence](../projective-plane-sequence/)
   builds step by step.
5. **A clear view down the tubes.** Draw the three pass-throughs the way a glass Klein bottle shows
   its neck passing through the wall: the tube continues, and the small disc of wall it passes
   through is removed (§4.4).

## 2. Geometry

### 2.1 Parametrization

The surface is the **Bryant–Kusner parametrization** on the closed unit disk
(complex parameter *w*, |*w*| ≤ 1), with antipodal boundary points identified
(*w* ~ −*w* on |*w*| = 1). That identification makes the disk ℝP².

- The textbook form is X = (g₁, g₂, g₃) / |g|². It is evaluated in the algebraically identical
  form **X = H·|d|² / |H|²**, where d = w⁶ + √5·w³ − 1 and H is g multiplied by |d|². This form
  stays finite at the three zeros of *d* inside the disk, which all map to the triple point.
- The family parameter *c* (the "−c" in the third component) is fixed at **c = 0.95**. The
  embedded slimming field (§2.4) was computed for that member of the family.
- The mesh is a polar grid of 129 × 721 vertices. Normals come from central differences, with the
  angle wrapping and one-sided differences at the rim seam.

Bryant–Kusner is a **conformal** parametrization, so small circles in the disk become small circles
on the surface. The edge and corner paint in §4 relies on this.

### 2.2 Shape controls are deformations of space

Every shape control acts on **space** (ℝ³), never on the surface's parameter domain. The chain,
applied per vertex in this order:

1. **Slimming:** the flow of an embedded smooth velocity field (§2.4) for time *t* = slider value,
   integrated with RK4 (10 steps) and cached per slider value.
2. **Lobe width:** a rotation about the symmetry axis whose angle depends on the azimuth through a
   threefold term (Im z³-type).
3. **Lobe length:** a radial stretch away from the axis.
4. **Lobe thickness:** a stretch along the axis that grows with distance from the axis.
5. **Twist:** a rotation about the symmetry axis that grows linearly with height.

The flow in step 1 is a diffeomorphism of ℝ³, so it preserves the immersion exactly. Steps 2–5
are one smooth map of space. Composing an immersion with a local diffeomorphism gives an immersion,
so the surface stays immersed wherever that map's Jacobian determinant stays positive.
[`tools/fold_check.py`](tools/fold_check.py) checks this numerically.
- It ports the page's flow and map line for line, and reads the flow field from the page itself.
- It evaluates det J at all 93,000 mesh vertices, for 5 values of each of the five shape sliders
  across their full ranges: 3,125 combinations.
- The determinant never reaches zero. Its minimum is **0.028**, at the most compressed corner
  (length 0.5, width 0.4, thickness 0.2). It is small there only because space is squashed.

The determinant is checked on a grid of slider values, not proven for every value in between. It
moves smoothly and its margins stay well clear of zero.

This is a local check. It shows no slider folds the surface, but not that the map is one-to-one on
the whole surface. Deforming space rather than the surface means no slider can tear the surface. The
membrane and self-intersection data assume the self-intersections stay where they are (§4.4).

The three lobe tips are found on the flowed surface. One is chosen in a fixed 120° window, so the
lobe colours never jump as the sliders move.

### 2.3 Gluing the square (the Glue slider)

The **Glue** slider stretches the flat square into Boy's surface. The whole square, its grid, its four
edges and its corners are present at every value, and the edges meet in pairs only at the end. You
can rotate the shape and change the material at any point.

**Construction.** Write S(w) for the finished surface (after every shape control) and F(w) for the
flat square:
- **The flat square:** F(w) = m + (x − x̄) A₀ + (y − ȳ) A₁, where (x, y) are the square
  coordinates of the disk point w (the inverse Fong map, §4.1). The plane map A is the least-squares
  fit of the finished surface against the square coordinates. So the square starts in the surface's
  best-fitting plane, at the surface's size, and keeps its orientation as the shape sliders change.
- **The stretch:** X(w, t) = (1 − b) F(w) + b S(w), with b = smoothstep(1.6 t − 0.6 |w|).
  - The centre of the square (|w| = 0) moves first, over t ∈ [0, 0.625].
  - The edges (|w| = 1) move last, over t ∈ [0.375, 1].
  - So the lobes bulge out of the square, the edges lift off and wrap round, and the two copies of
    each edge meet exactly at t = 1.

**Even pacing.** Moving every point at the same rate looked wrong: little happens for a long stretch
of the slider, then the edges wrap round in a jump.
- The viewer measures the distance the surface travels: the arc length of the motion,
  Σᵥ |∂b/∂t| · |S(w) − F(w)|, summed on every 7th vertex at 200 values of t.
- It then re-times the slider so that g ∈ [0, 1] is that distance's fraction.
- Equal slider steps therefore make equally large changes. It's recomputed whenever the shape
  changes.

**What exists only once glued.** The membranes, the self-intersection curve and the triple point
belong to the finished surface, so they are drawn only at g = 1. Until then the four corners are four
separate points; at g = 1 they merge into two.

**Cost:** about 20–40 ms per rebuild, smooth enough for the ▶ button, which plays the gluing in
about 7 s.

**Rendering any moment.** [`tools/render_gluing.py`](tools/render_gluing.py) renders any glue values
from any view angles, using the viewer page itself in headless Chrome, so frames match it exactly.
It writes single frames, a labelled strip and optional animations. See the README for examples.

**History.** Until v18 the slider *grew* the square instead. It showed the image of a growing
sub-disk of the finished surface, the construction of the learning sequences, with the square
rescaled to fit. That reads as expanding, not stretching, so v19 replaced it.

### 2.4 The slimming field

**Problem:** in the classic surface the lobe interiors are inflated like balloons, while the slits
from outside into the central cavity are hairlines.

**Approach:** the velocity field is computed offline.
1. Voxelize the surface (140³ grid) and take its distance field.
2. Classify air as exterior, or as the central chamber (the largest enclosed region).
3. Measure local thickness: the radius of the largest ball that fits at each point.
4. Build the field from two parts:
   - **(a) Thinning:** where the chamber is thicker than a target radius *r_t*, push the walls
     inward along the distance gradient.
   - **(b) Opening:** push the walls apart in narrow exterior passages deep inside the shape.
5. Blur the result, downsample it to 40³, and quantize it to int8.
6. Embed it as zlib + base64 (about 50 KB), decoded with the browser's `DecompressionStream`.

**Status:**
- **Thinning works.** At slider value 1 the lobe interiors are clearly slimmer. The slider stops
  at 1.3, because ripples from the field's grid show beyond that.
- **Opening barely works.** The slits are about 0.06 units wide, roughly one voxel, so the field
  cannot resolve them. The Gap Width control (§2.5) does this job instead.

**Reproducibility.** [`tools/slimming_field.py`](tools/slimming_field.py) builds the field from
scratch in about two minutes, and `--embed` rewrites the page. It regenerates the embedded field byte
for byte.
- **The original field can't be rebuilt.** The field first shipped in v9 came from exploratory
  scripts whose last smoothing pass was never saved. Fitting the pipeline's settings to it
  recovered it only approximately.
- **The committed recipe is the closest fit:** blur 4.0 voxels, interior gain 1.08, gap speed
  0.135. Its surface differs from the original by at most 0.019 at slimming 1 and 0.031 at 1.3, on
  an object about 2.6 wide. Rendered side by side, the two are indistinguishable by eye; about 3% of
  pixels shift slightly at edges.
- **From v17 on,** the committed recipe defines the field. The fold check (§2.2) and the browser
  checks pass with it.

### 2.5 Gap Width

**Problem:** the slits between the tubes and the central area are hairlines, about 0.074 wide at the
median. The tubes are about 0.26 across.

**Ruled out: pushing the surface directly.** A first prototype pushed each slit's two walls apart,
as a displacement stored per point of the disk. It failed for three reasons:
- **The slits hug the self-intersection curve.** Freezing a buffer around the curve, to keep it in
  place, also froze most of each slit.
- **Collisions:** pushed walls collided with other sheets.
- **Shape dependence:** a displacement computed on the default shape created new contacts at other
  slimming values.

**The approach that works: a map of space.** Like every other shape control, the gap is a map of
space, x ↦ x + g·Δ(x), applied after slimming. Built by
[`tools/gap_field.py`](tools/gap_field.py), in about eight minutes:
1. **Slit walls:** on the slimmed surface, pairs of points under 0.10 apart, far apart on the disk,
   with facing normals, away from the self-intersection curve. There are 6,068 pairs.
2. **Stretchers:** 589 of them along the slits' mid-surface, one per 0.025 cell. Each sits at the
   mean midpoint and points across the slit (the dominant eigenvector of the pair directions).
3. **The velocity field** V(x) = A Σₖ gₖ(x) ((x − mₖ)·nₖ) nₖ / (Σₖ gₖ + 0.05) · min(1, Σₖ gₖ/0.5):
   - The gₖ are anisotropic Gaussians, 0.10 across a slit and 0.07 along it.
   - V stretches space across each slit.
   - It is quadratic in nₖ, so the normals' signs don't matter.
   - Being analytic, it resolves slits far thinner than any voxel grid.
4. **Δ** is the time-1 flow of V minus the identity, with A = 1.4. It is sampled on a 96³ grid
   around the surface and is zero away from the slits, so it packs to 123 KB. The slits open from a
   median width of 0.074 to 0.26.

**Why it is safe.**
- **A true map of space:** det(I + g ∇Δ) > 0 holds for g from 0.05 to 1 over the whole grid, with
  minimum 0.045 on the packed 8-bit grid. So x + gΔ(x) is a map of space at every slider value.
- **No new crossings, on any shape.** Because it is a map of space, the surface gains no new
  self-intersections, and the self-intersection curve stays on the same disk points.
- **Shared data stays exact:** the membrane and curve data, the glue slider and the fold check all
  remain valid.
- **Checked numerically:** with the viewer's interpolation, the surface stays an immersion and gains
  no new contacts at slimming 0, 0.65, 1 and 1.3, each at half and full gap. The one exception is a
  single near-touch at maximum slimming and full gap.
- **The fold check includes it:** the gap at 0 and 1, across all the other sliders.

**Presets:** *Classic* sets the gap to 0; *Reference look* and *Slim tubes* set it to 1.

**Cost:** at full strength, nearby sheets crease gently (§7).

## 3. Rendering

Glass that is translucent, frosted and coloured, and that passes through itself several times,
needs correct ordering of many overlapping layers. The pipeline is:

1. **Shadow map:** a 256² coloured shadow map (tinted by the glass colour along each light path),
   blurred and projected onto the floor.
2. **Backdrop:** a studio gradient plus the floor shadow, found by casting a ray from the camera to
   the floor plane.
3. **Depth peeling:** the front layer, then 8 inner layers, composited front to back. Each layer is
   shaded as a thin slab of coloured glass:
   - Beer–Lambert absorption, with extra absorption at grazing angles for darker rims.
   - Fresnel reflection of a studio environment built from spherical Gaussians (key, fill and rim
     lights plus a sky/ground gradient).
   - Roughness driven by the Glossiness slider.
4. **Frost:** what is seen through the glass is blurred, and internal scattering is added.
5. **Tone mapping:** Khronos PBR Neutral, then sRGB.
6. **Finish:** FXAA plus a little grain and dither.

**Performance:** the renderer only draws when something has changed. If frames stay slow, it lowers
its internal resolution, down to 55% at most.

## 4. Lines: grid, glued edges and corners

All line work is painted in the fragment shader of the depth-peeled layers. It is opaque paint, so
it hides what lies behind it, as ink on glass would.

### 4.1 Square grid

The learning sequences map the square [−1, 1]² to the disk with **Fong's elliptical map**:
- u = x·√(1 − y²/2)
- v = y·√(1 − x²/2)

For every vertex the viewer stores the inverse, which takes the disk back to the square:
- x = ½√(2 + u² − v² + 2√2·u) − ½√(2 + u² − v² − 2√2·u)
- y = ½√(2 − u² + v² + 2√2·v) − ½√(2 − u² + v² − 2√2·v)

These square coordinates are computed once, in a static vertex buffer. Grid lines sit at x, y =
−1 + 2k/n (n = Density) and are antialiased with screen-space derivatives. The square's boundary
is left to the glued-edge paint.

Lines placed symmetrically about 0 meet themselves across the antipodal seam, because the gluing
sends (x, y) to (−x, −y).

**Polar** keeps the rings and spokes of the parameter disk: n rings and 2n spokes, an even number,
so the spokes also meet across the seam.

### 4.2 Glued edges

The square's boundary is the disk's rim |*w*| = 1. The rim's antipodal halves meet on the surface,
so the four edges become **one closed curve**:
- the top and bottom edges (edge *a*, orange) fill the 45°–135° and 225°–315° arcs;
- the left and right edges (edge *b*, blue) fill the other two arcs.

Each sheet paints a band from its side of the rim. Because the two antipodal sheets meet along the
same curve, the band ends up centred on it.

- **Band width:** taken in disk units per pixel, |∇r|. Because the parametrization is conformal,
  that width looks the same in every direction on screen.
- **Edge-on views:** |∇r| blows up there, so the band's reach is also capped at 0.03–0.045 disk
  units from the rim. Without the cap, a dark outline smears across distant parts of the surface
  in edge-on views.

### 4.3 Corner points

The four corners meet in pairs: (1, 1) ~ (−1, −1) give the **white** point, and (1, −1) ~ (−1, 1)
give the **black** one.

The black point lies in a compressed region near the centre. There, a marker sized in pixels and
measured in disk units would need more reach on the surface than the cap allows, and would be
clipped to a sliver. So each corner is drawn as a disc of **fixed radius in 3D** around the
corner's world position. That position is the deformed rim vertex at 45° (white) or 135° (black),
passed in as a uniform every frame. This works from every viewpoint, at every slider setting.

### 4.4 Membranes (pass-throughs drawn as in a Klein bottle)

**The convention.** In the usual model of a Klein bottle, the neck passes through the wall. The tube
stays whole, and the small disc of wall it passes through is removed, leaving a hole with the tube
running through it. The viewer draws Boy's surface the same way. The **Membranes** menu offers
*Removed* (the default), *Faded* (a faint ghost) and *Shown* (the complete surface). In *Removed*
mode the floor shadow drops the membranes too.

**Which discs.** The self-intersection curve of Boy's surface is three loops through the triple
point. On the parameter disk, with the antipodal rim points identified, its preimage has 3 vertices
(the triple point's preimages) and 6 arcs. Since χ(ℝP²) = 1 = V − E + F, the disk splits into exactly
**F = 4 regions**: one big region (the outer skin and the tube walls) and three small ones.
[`tools/membranes.py`](tools/membranes.py) finds the curve numerically:
1. Sample the surface on a 900² grid over the disk.
2. Mark grid points with a partner far away on the disk at the same place in space.
3. Label the regions between the marked curves, joining across the rim.
4. Check that each small region is a single disc, with no holes, whose whole boundary lies on the
   curve. All three pass, so these are the membranes.

**An earlier attempt that tore.** v12–v13 instead removed every sheet that rays from outside could
not reach. Because the big region is both outer skin and tube wall, that boundary is not a curve of
the surface: the cut wandered and tore the tubes. Cutting only along the self-intersection curve
avoids this. It also keeps the tubes continuous, which is the point of the convention.

**Exact cut.**
- The field is stored as a **signed distance** on the disk to the membranes' boundary (positive
  inside). It is lightly smoothed to remove the pixel staircase, sampled to 512², and stored as
  8-bit, zlib + base64 (about 15 KB).
- The fragment shader reads it **per pixel** from the fragment's disk point and discards membrane
  fragments. The cut therefore lies on the self-intersection curve, independent of the mesh.
- A dark ring, about 2 pixels wide, is drawn just outside the cut: the rim of the hole.
- The shape sliders deform space, so the curve stays on the same disk points, and the cut is right
  at every slider setting.

### 4.5 Self-intersection curve and triple point

The *Self-Intersections* toggle (off by default) draws the self-intersection curve in gold. It is
painted on every sheet that passes through it, so it stays visible whichever sheets the membrane
setting removes. A gold disc marks the triple point.

- **Data:** `tools/membranes.py` also stores the distance on the disk to the curve. This is a second
  channel of the same 512² texture, capped at 0.02 disk units and about 24 KB.
- **Constant line width on screen.**
  - The disk-units-per-pixel scale used for the edges (§4.2) measures stretch in the *radial*
    direction. That is right for the rim, but the curve runs across the disk at every angle.
  - So the line width uses the stretch *across the line*. The field's direction on the disk comes
    from texture taps two texels apart. It is combined with the smooth screen-space derivative of
    the disk point: |(∂w/∂x · n, ∂w/∂y · n)|.
  - That keeps the width constant at any viewing angle. With the radial scale, the line bloated into
    wedges wherever the surface is seen edge-on.
  - It is not taken from the 8-bit field's own slope, which is too coarse and gave a speckled outline.
- **The triple point** is the image of the three zeros of d inside the disk:
  w = r₃^(1/3)·e^(2πik/3), with r₃ = (3 − √5)/2. The marker sits at the average of the nearest
  mesh vertex for each zero, and the test checks that the three agree to mesh resolution.
- **The ring:** when the curve is shown, it replaces the dark ring at the membrane holes, since it
  marks the same rim.

### 4.6 Colour conventions

Edge *a* (top and bottom) is orange, edge *b* (left and right) is blue, and the corners are white
for (1, 1) and black for (1, −1). These follow the 14-stage projective-plane sequence, and the shared
`surface_sequences.py` now uses the same convention, so all of them match. The black corner has a
light outline so it stays visible on dark glass.

## 5. Interaction and panel

- **Rotate:** one-pointer drag.
- **Move:** right, middle or Shift-drag, or two fingers.
  - Implemented as a **lens shift**: a translation in clip space, x′ = x + panX·w.
  - The object, the floor and the shadow move together, and the perspective stays the same.
  - The backdrop shader undoes the shift when it casts its floor rays, so the shadow stays under
    the object.
  - The offset is clamped to ±0.95 of the half-screen.
- **Zoom:** scroll or pinch.
- **Recentre:** double-click.
- **Hide or show the panel:** the round button or the H key.

**Panel sections:** Shape, Lines, Material and Scene. They are collapsible `<details>` elements,
and each section's open state is remembered in `localStorage`, as is whether the panel is hidden.
Every storage access is wrapped in try/catch, so the viewer works where storage is blocked.

**Presets** set only the five shape sliders:

| Preset | Length | Width | Thickness | Slimming | Twist |
|---|---|---|---|---|---|
| Classic Bryant–Kusner (no deformation) | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 |
| Reference look (default) | 1.3 | 0.92 | 1.0 | 1.0 | 1.6 |
| Slim tubes | 1.4 | 0.85 | 0.9 | 1.3 | 1.6 |

The menu shows "Custom" whenever the sliders match no preset. Reset restores every default,
including the view.

## 6. Testing

[`tools/check_viewer.py`](tools/check_viewer.py) runs the checks below in headless Chrome with
SwiftShader, so no GPU is needed. It runs 26 checks and exits non-zero on any failure.

The page exposes a small hook, `window.__boy`, with these members:
- `set(params)` and `pose({rotX, rotY, spin, panX, panY})` change parameters and the view.
- `renderNow()` draws a frame immediately.
- `stats` and `internals()` expose frame and geometry state for inspection.

It covers:
- **Shader compilation:** checked with no console errors.
- **Panel:** presets and Custom detection, every menu and toggle, collapsing a section and remembering
  it after a reload, Reset, the panel toggle and the H key.
- **Rendering:** each visual switch (membranes, self-intersections, grid, glued edges) changes the
  image.
- **Gluing:** the Glue slider stretches the flat square into the surface. The membranes, the curve
  and the triple point appear only once it is glued, and ▶ completes the gluing.
- **Moving the shape:** right-drag moves it, and double-click recentres it.
- **Corner gluing:** the antipodal corner pairs land on identical 3D positions, and the three preimages
  of the triple point meet.
- **Membranes:** `tools/membranes.py` reports 4 regions, and three discs bounded only by the curve.
  It regenerates the embedded field identically, byte for byte.
- **Images:** screenshots of the default view and of each line mode were inspected by eye during
  development. These visual checks are not part of the script.

## 7. Known limitations and next steps

- **Wrinkles at full Gap Width:** stretching slits that hug the self-intersection curve to about four
  times their width leaves gentle creases on nearby sheets, and the glued-edge paint breaks up where
  the stretch is strongest. Wider, smoother stretchers did not help and thinned the determinant
  margin (§2.5). A cleaner result would need a different construction, for example moving the
  self-intersection curve too and recomputing the membrane data for each gap value.
- **Membrane rings near the triple point:** the smoothing rounds the cut slightly where the three
  curves meet.
- **Blog version:** the CodePen panes used for embedding on a blog were made from an earlier
  version. They lack slimming, the panel toggle, moving the shape, the line controls and the
  membranes.

## 8. Version history

| Version | Change |
|---|---|
| v5 (input) | Not Boy's surface: an open tube. The glossiness slider was bound to the wrong object. |
| v6 | Rewrite: Bryant–Kusner surface, depth-peeled glass, frost, studio lighting. |
| v7–v8 | Material fitted to the reference render. The incorrect torus-based lobe model was removed. |
| v9 | Lobe Slimming as the flow of an embedded field. |
| v10 | Panel toggle button. Moving the shape (lens shift), two-finger move and pinch, double-click recentre. |
| v11 | Collapsible sections, shape presets, square/polar grid controls, glued edges and corner points. |
| v12–v13 | Inner-sheet cutaway based on visibility from outside. Superseded: the cut tore the tubes (§4.4). |
| v14 | Membranes removed along the self-intersection curves, as in a Klein bottle. Per-pixel cut, rim ring, `tools/membranes.py`. |
| v15 | Self-intersection curve and triple point toggle. Light outline on the black corner. Committed browser checks (`tools/check_viewer.py`). |
| v16 | Glue slider and ▶: the square-to-Boy's construction on the live surface. Numerical fold check of the shape controls (`tools/fold_check.py`). |
| v17 | Slimming field rebuilt by a committed, reproducible generator (`tools/slimming_field.py`), visually identical to v16. |
| v18 | Gap Width: an analytic map of space that opens the slits to about the tubes' width (`tools/gap_field.py`). Fold check and browser checks extended. |
| v19 | Glue slider stretches the whole square into the surface (centre first, edges last), evenly paced by arc length. `tools/render_gluing.py` renders any glue values from any view. |
