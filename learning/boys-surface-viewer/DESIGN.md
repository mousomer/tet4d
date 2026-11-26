# Boy's surface viewer: design

The viewer is one self-contained HTML file (`boys-surface-viewer.html`, about 1,400 lines). It
combines inline CSS, the WebGL2 renderer in plain JavaScript, and one embedded, compressed data
field. It has no build step, makes no network requests and has no dependencies, so the file can be
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

## 2. Geometry

### 2.1 Parametrization

The surface is the **Bryant–Kusner parametrization** on the closed unit disk
(complex parameter *w*, |*w*| ≤ 1), with antipodal boundary points identified
(*w* ~ −*w* on |*w*| = 1). That identification makes the disk ℝP².

- The textbook form is X = (g₁, g₂, g₃) / |g|². It is evaluated in the algebraically identical
  form **X = H·|d|² / |H|²**, where d = w⁶ + √5·w³ − 1 and H is g multiplied by |d|². This form
  stays finite at the three zeros of *d* inside the disk, which all map to the triple point.
- The family parameter *c* (the "−c" in the third component) is fixed at **c = 0.95**. The
  embedded slimming field (§2.3) was computed for that member of the family.
- The mesh is a polar grid of 129 × 721 vertices. Normals come from central differences, with the
  angle wrapping and one-sided differences at the rim seam.

Bryant–Kusner is a **conformal** parametrization, so small circles in the disk become small circles
on the surface. The edge and corner paint in §4 relies on this.

### 2.2 Shape controls are deformations of space

Every shape control acts on **space** (ℝ³), never on the surface's parameter domain. The chain,
applied per vertex in this order:

1. **Slimming:** the flow of an embedded smooth velocity field (§2.3) for time *t* = slider value,
   integrated with RK4 (10 steps) and cached per slider value.
2. **Lobe width:** a rotation about the symmetry axis whose angle depends on the azimuth through a
   threefold term (Im z³-type).
3. **Lobe length:** a radial stretch away from the axis.
4. **Lobe thickness:** a stretch along the axis that grows with distance from the axis.
5. **Twist:** a rotation about the symmetry axis that grows linearly with height.

The flow in step 1 is a diffeomorphism of ℝ³, so it preserves the immersion exactly. Steps 2–5
are smooth maps of space. They keep the immersion while they stay invertible, which held across the
slider ranges in testing but is not proven in general. Deforming space rather than the surface
means no slider can tear the surface or change where it meets itself.

The three lobe tips are found on the flowed surface. One is chosen in a fixed 120° window, so the
lobe colours never jump as the sliders move.

### 2.3 The slimming field

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
- **Opening does not work yet.** The slits are about 0.06 units wide, roughly one voxel, so the
  field cannot resolve them. Widening the gaps to tube width needs a different method (§7).

The offline generator was a set of exploratory scripts, and its final smoothing pass was never
kept as a script. So the embedded field is the reference artefact, and this section records how it
was made.

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

### 4.4 Colour conventions

Edge *a* (top and bottom) is orange, edge *b* (left and right) is blue, and the corners are white
for (1, 1) and black for (1, −1). These follow the 14-stage projective-plane sequence, so the
viewer matches that sequence's final frame. The shared `surface_sequences.py` script colours
top/bottom blue instead. Bringing the two into line is an open item (§7).

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

The page exposes a small hook, `window.__boy`, with these members:
- `set(params)` and `pose({rotX, rotY, spin, panX, panY})` change parameters and the view.
- `renderNow()` draws a frame immediately.
- `stats` and `internals()` expose frame and geometry state for inspection.

Checks were run with headless Chrome (Playwright, SwiftShader WebGL):
- **Shader compilation:** checked with no console errors.
- **Panel:** presets and Custom detection, grid type, edge and corner toggles, collapsing a section
  and remembering it after a reload, Reset, the panel toggle and the H key.
- **Moving the shape:** right-drag moves it, and double-click recentres it.
- **Corner gluing:** the antipodal corner pairs land on identical 3D positions.
- **Images:** screenshots of the default view and of each line mode were inspected.

## 7. Known limitations and next steps

- **Gap widening:** the slits are still hairlines (§2.3). The planned method works on the surface,
  not the voxel grid:
  1. Find pairs of points that are close in space but far apart in the domain, with near-parallel
     facing normals. That condition excludes the genuine self-crossings, which must stay.
  2. Push each pair apart toward tube width.
  3. Smooth the push on the disk while respecting the antipodal seam.
  4. Apply it in small steps, checking after each that the surface still never folds or pinches.
  5. Expose it as a Gap Width slider.
- **Black corner contrast:** the black corner is dark on dark glass. A light outline would help.
- **Edge colour conventions** differ between the two sequence scripts (§4.4).
- **Blog version:** the CodePen panes used for embedding on a blog were made from an earlier
  version. They lack slimming, the panel toggle, moving the shape and the line controls.

## 8. Version history

| Version | Change |
|---|---|
| v5 (input) | Not Boy's surface: an open tube. The glossiness slider was bound to the wrong object. |
| v6 | Rewrite: Bryant–Kusner surface, depth-peeled glass, frost, studio lighting. |
| v7–v8 | Material fitted to the reference render. The incorrect torus-based lobe model was removed. |
| v9 | Lobe Slimming as the flow of an embedded field. |
| v10 | Panel toggle button. Moving the shape (lens shift), two-finger move and pinch, double-click recentre. |
| v11 | Collapsible sections, shape presets, square/polar grid controls, glued edges and corner points. |
