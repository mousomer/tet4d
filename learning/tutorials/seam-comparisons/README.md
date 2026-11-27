# Lesson 3 — Can you come home mirrored?

[Read the lesson](chapter_03_seam_comparisons.md).

Three 5 × 5 square gluings side by side: A, an adjacent-edge sphere; B, an adjacent-edge projective
plane; C, the opposite-edge projective plane. The lesson traces one loop on two boards to see a frame
come home mirrored, moves a two-cell piece through the same commands on all three boards to see bonds
break and rejoin, and counts blocked moves and lost bonds on an 8 × 8 board to give "worse" a
denominator. Follow Chapter 2's introduction to transported frames first; allow 15–20 minutes.

## Files

- `chapter_03_seam_comparisons.md` — the lesson, its worked comparisons, the benchmark table and teaching notes.
- `interactive/index.html` — the interactive comparison: a shared step control for boards A and B
  (part 1), the domino on all three boards (part 2), and the 8 × 8 benchmark (part 3, `#benchmark`).
  The page loads the scripts and stylesheet beside it:
  - `seam_comparison.js` — the two-board loop and frame transport.
  - `board_rules.js` — the three gluings and the board-axis move rule.
  - `controls_and_bonds.js` — the domino comparison and its bond display.
  - `domino_traces.js` — the native traces the domino clips are checked against.
  - `benchmark.js` — the 8 × 8 enumeration of blocked moves and lost bonds.
  - `styles.css`.
- `interactive/smoke_browser.py` — browser smoke test of the interactive page (Playwright, Chromium).
- `domino-comparisons/` — five animated GIFs of the two-cell piece on the three boards, the generator
  `domino.py`, the native trace `native_traces.txt` and the C++ program `verify_native.cpp` that
  regenerates it from Tet4D's native core. See its [README](domino-comparisons/README.md).

## Run from the repository root

Open `learning/tutorials/seam-comparisons/interactive/index.html` in a browser; keep the adjacent
JavaScript and CSS files together. The smoke test and the clip generator:

```bash
python3 learning/tutorials/seam-comparisons/interactive/smoke_browser.py        # needs Playwright + Chromium
cd learning/tutorials/seam-comparisons/domino-comparisons
python3 domino.py --out rendered                                                 # needs Pillow, DejaVu Sans
```

`domino.py` checks every clip's end pose against `native_traces.txt`. To regenerate the trace from
Tet4D's native core, see the domino README.

## Scope

The lesson uses its own board-axis rule (up increases y) and documents how to convert to Explorer's
engine coordinates. The counts are reference results for the stated presets, not global rankings of
topologies, and the lesson does not establish authority over the native or Godot implementations; see
the [Explorer requirements](../../../docs/rds/RDS_EXPLORER_TOPOLOGIES.md) for the engine's movement and
occupancy rules.
