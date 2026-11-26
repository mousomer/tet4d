# Tet4D Graphical Language

Role: authority for the target look of the Godot board, cockpit and menus
Status: active (owner decision 2026-11-24)
Plan: `docs/plans/graphical_language_adoption.md`

## The target is the images

The three concept images in this folder are the target. Real captures are
compared against them side by side. Prose in this file or any other doc
describes them. It never overrides them; where the two disagree, the images
win.

| File | What it contributes |
| --- | --- |
| `concept_a_right_column_footer_controls.webp` | **Accepted layout**: board at full height, right column with NEXT / HOLD / Score / Lines / Level, controls in a footer bar, top bar with the 2D/3D/4D switch |
| `concept_b_header_stats_status_footer.webp` | **Accepted status footer** ("Active: Play 4D · Objective…" plus V View / F Focus / H Hints / Esc Pause); ghost piece style; translucent locked cells in 3D/4D |
| `concept_c_left_rail_4d_view_selector.webp` | Cell and board material reference; the "4D View" selector is **deferred** (see below) |

The images are collages comparing three dimensions. They are not one screen:
normal play shows the selected dimension only. Their scores, key bindings,
board sizes, stack shapes and tesseract-style 4D boxes are illustration, not
data. The running game supplies every value.

## Owner tuning relative to the images

- **Active piece:** a bit *more* luminous than in the images. Brighter body,
  a glow in its own hue, and clearly the brightest object on screen.
- **Locked cells:** keep their full piece hue, with *higher transparency*
  than the images, so the active piece and the inner layers of 3D/4D stay
  readable. Locked cells are never darkened or desaturated toward grey; that
  muting is what the current game does and is rejected.
- Overall the result must sit **closer to the images than to the current
  game**.

## Visual tokens

Tuning values for the Luminous board (and, from P2, the shell skin) live in
`godot/Tet4D.Godot/config/graphical_language.json`. To change how bright,
translucent or rounded something is, edit that file; no code holds these
numbers.

The swatches were sampled from the concept images and are approximate. A
P1/P2 capture is accepted on side-by-side comparison, not on hex equality.

**Surfaces**
- App background: deep navy-black, about `#091728`.
- Panels: a step lighter, about `#0F2036`. Thin soft border, about 10px
  corner radius, no bright frames.
- Text: values near white, about `#F6F8F8`; labels muted blue-grey.

**Accent**
- One amber/gold, about `#F0C56A`, used only for the selected item: the
  active nav tab, the active dimension button, the primary key chip (Space).
  Its button fill is a dark amber, about `#5C472B`.

**Pieces** (saturated, one hue per piece family)
- Cyan `#22D8F8`, yellow `#FDC72E`, purple `#9D4AEA`, green `#34C53F`,
  orange `#FC7A25`, red, blue.
- These match the existing `ReplayVisuals.TRACE_COLOR_PALETTE` hue set. What
  changes is the treatment, not the palette.

**Cells**
- 2D: a bevelled square. The top and left edges are lighter, the bottom
  edge is darker, and a thin dark seam separates cells. A multi-cell piece
  reads as one shape *and* as individual cells.
- 3D/4D: a solid cube with distinct top, front and side shading and crisp
  edges; locked cubes are translucent per the owner tuning.
- Active piece: a glow in its own hue (emission plus bloom). Nothing else
  glows except rare action feedback.
- Ghost: a translucent grey form of the piece, outline first
  (concept B).

**Board**
- 2D: a dark board with a low-contrast grid inside a bright, slightly
  glowing frame.
- 3D/4D: a glass volume. Bright wireframe edges, faintly tinted faces, and
  an internal grid quieter than the edges.
- Axis gizmo: X red, Y green, Z blue, W violet.

**Typography**
- Bold geometric sans for titles and values; small muted labels above large
  white values; tabular figures for numbers.
- Dimension subtitles carry real board data, for example
  `Classic · 10 × 20`, `Cube · 6 × 6 × 12`, `Hypercube · 6 × 6 × 6 × 6`.

**Components**
- Top bar: brand, Play / Explore / Settings / Help (icon plus label), and a
  2D/3D/4D button group with icons.
- Stat card: a label above a value.
- NEXT and HOLD cards: HOLD shows `—` when empty.
- Keycap chip: a rounded outline with a centred glyph. Control rows pair an
  icon or chips with a label.
- Footer: the controls legend (concept A) plus the status line (concept B).
- Play shows no debug or diagnostic text. "Live Plain 2D | … | BLOCKED",
  Recover, Fit View and "Designer: Open" move to Settings or the
  `diagnostic` theme.

## 4D

4D is the existing **W-slice matrix**, with every slice drawn in the glass-cube
language above. The tesseract (all-W overlay) and projection views in
concept C's "4D View" selector are deferred to a later stage. They are not
part of this adoption.

## Launch screen

Open directly into the cockpit. A fresh profile opens Play · 2D.
Later launches restore the last Play or Explore view and the selected
2D, 3D or 4D dimension. Play shows the ready board with a Start action.
Gravity and piece actions begin only after Start. The saved selection
contains the view and dimension.

## What stays fixed

Game semantics, replay and native hashes, board coordinates, 4D slice
membership and order, camera and basis, and input action semantics. This is a
look-and-layout change.
