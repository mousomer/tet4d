# Blog material

Two pieces made for the blog on 2026-11-25, from early versions of the
[Boy's surface viewer](../boys-surface-viewer/README.md). Each folder holds a turntable animation for the post
and the three panes of an interactive CodePen pen. These are publishing material: they are not part of the
offline edition, and the current viewer supersedes their code.

| Piece | Folder | Turntable | Pen |
|---|---|---|---|
| **Boy's Surface** — the Bryant–Kusner immersion of ℝP² in ℝ³ in frosted glass | [`boys-surface/`](boys-surface/) | [WebP](boys-surface/boys-surface-turntable.webp) 600 × 600, 72 frames, 407 KB · [GIF](boys-surface/boys-surface-turntable.gif) 480 × 480, 4.5 MB | HTML 55 lines, CSS 89, JS 968 |
| **Three Rings — after Boy's Surface** — a three-ring sculpture of the surface, switchable to the true surface | [`three-rings/`](three-rings/) | [WebP](three-rings/three-rings-turntable.webp) 600 × 600, 72 frames, 506 KB · [GIF](three-rings/three-rings-turntable.gif) 480 × 480, 5.4 MB | HTML 76 lines, CSS 89, JS 1,136 |

## The pens

Each pen is plain WebGL2 with no libraries and no network requests:

- Boy's Surface has Shape sliders (lobe length, width, thickness, swell, twist), Material sliders (opacity,
  center clarity, frost, glossiness, edge depth) and lobe colours.
- Its Scene section sets spin speed, spin axis (symmetry axis or turntable), shadow and a parameter-grid
  overlay.
- Three Rings adds a Model switch (the three-ring sculpture or the true Boy's surface) and ring controls:
  tube diameter, ring tilt and center web.

To publish a pen, create one on [codepen.io](https://codepen.io), paste `codepen-HTML.html`, `codepen-CSS.css`
and `codepen-JS.js` into the HTML, CSS and JS panes, and save. Pens can also be opened locally: put the HTML
pane in a page that links the CSS and loads the JS.

## In a post

The free WordPress.com plan does not run custom scripts, so the turntable is what goes into the post itself:

- Use the WebP. It is about a tenth of the GIF's size.
- Keep the GIF for places that do not show animated WebP.
- Link the image to the pen for the interactive version.

For the current, fuller interactive version, link the Boy's surface viewer or the gluing viewers instead.
