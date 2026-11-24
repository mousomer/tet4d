# Graphical language P2: shell skin captures

These were captured with `godot/Tet4D.Godot/tests/run_graphical_language_capture.gd`
through normal startup at a 1440×900 window, using the default `luminous`
theme and registry defaults. They show the same seeded game as the P1
captures in `docs/design/screenshots/graphical_language_p1/`, so comparing `live_*d.png` with
`docs/design/screenshots/graphical_language_p1/live_*d_default.png` isolates the shell skin:

- Panels and controls have rounder corners (panel 10, control 6, keycap 5).
- Panel borders are soft, one step above the elevated surface, instead of the
  bright grid colour that P1 gave the board's glass edges.
- Cockpit cards (NEXT, HOLD, control strips) sit on the lifted panel fill;
  the board frame keeps the board fill.
- Section titles are white. Amber marks only selection: a dark amber fill,
  an amber border and light text.

Layout is unchanged. `test_locked_shell_layouts.gd` and
`test_typography_lock.gd` pass without edits.
