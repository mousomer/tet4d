# Godot Vector Arcade Cockpit Overhaul

Status: active Godot product-shell visual UX stage  
Date: 2026-06-22  
Scope: Godot UI shell, visual presentation, menus, settings, inspector, hints

## Purpose

This stage refines the implemented Godot visual style foundation into the
Vector Arcade Cockpit product-shell direction. The goal is a stronger,
faster-reading Godot shell that preserves the operational convenience of the
Python/pygame UI without copying pygame as an authority.

Python/pygame remains evidence for readability and control convenience only.
Python remains the semantic oracle for gameplay, topology, movement, collision,
rotation, scoring, replay correctness, trace semantics, and configuration
defaults.

## Source Of Truth Comparison

This stage extends:

- `docs/architecture/godot_visual_style_authority.md`
- `docs/architecture/godot_visual_style_foundation.md`
- `docs/architecture/authority_map.md`
- `godot/AGENTS.md`

The existing Stage 32 foundation already routes Godot shell controls and
board/replay visuals through semantic style roles. This stage keeps that
architecture and tightens the presentation:

- `tron` remains the internal default theme ID.
- `tron` presents to users as `Vector Arcade`.
- keyboard hints render as grouped keycap/action rows instead of wrapped prose.
- menu entries present as command-card buttons with label, description, and
  shortcut text.
- settings rows present as compact cards while preserving generated controls.
- inspector sections are explicit and persistent.
- board grid and W-label presentation are strengthened through existing
  visual-role constants and materials.

## Boundaries

Allowed:

- Godot shell layout and visual hierarchy.
- menu, settings, inspector, and control-hint presentation.
- theme labels and visual-role styling.
- board/replay material emphasis and W-label readability.
- Godot-facing tests for layout and style contracts.

Forbidden:

- gameplay implementation in GDScript.
- topology implementation in GDScript.
- movement, collision, drop, lock, scoring, trace, replay-frame, or fixture
  semantic changes.
- Python oracle authority transfer.
- C++/native authority expansion.
- parity expansion.

## Acceptance Criteria

- The main menu presents command-card entries with shortcut text.
- Viewer, inspector, bottom controls, and controls screen expose structured
  keycap/action hints.
- The right inspector remains persistent and inside the layout contract.
- Settings rows remain generated from the Stage 29 registry and render as
  compact cards with correct control types.
- The internal theme ID remains `tron`, but the displayed product label is
  `Vector Arcade`.
- Board grid and W-label visuals remain routed through existing style roles and
  are stronger than the prior Stage 32b baseline.
- Godot-facing tests pass.
- `CODEX_MODE=1 ./scripts/verify.sh` passes, or any environment limitation is
  explicitly recorded.

## Manual Acceptance

Manual GUI acceptance should compare current Godot, Python/pygame, and this
Godot shell for:

- board readability;
- cell and grid contrast;
- W/layer label readability;
- keyboard-hint decipherability;
- menu/settings richness;
- inspector usefulness;
- operational convenience;
- visual consistency.

Minimum target score remains 4/5 for board readability, convenience,
menus/settings, and style consistency, with 5/5 for keyboard-hint
decipherability.

## Stage 33a Live Acceptance Repair

Stage 33 headless validation passed, but manual screenshot review did not
accept the live-mode screen. The rejected live screen still read as styled
debug output: top-left prose was diagnostic, the authority text was too broad,
keyboard hints were too sparse, W slices still looked like raw wireframe boxes,
and game-over state was presented as text instead of a cockpit status badge.

Stage 33a is a corrective Godot product-shell repair only. It keeps the Stage
32 style-token architecture and does not change gameplay, topology, movement,
collision, drop, lock, scoring, trace semantics, replay-frame semantics,
fixtures, parity logic, native C++ semantics, or authority transfer.

### Scoped C++ Session Wording

Visible live wording must scope native authority to the current live plain
bounded session. Acceptable wording includes `Live Plain 4D | C++ Session |
Godot shell` and `C++ PlainNDSession | Godot command/render shell`.

Forbidden visible wording:

- `Native C++ owns gameplay`
- `C++ owns all gameplay`
- `Godot owns gameplay`
- `Godot owns rules`

The reason is that C++ owns only documented live plain bounded sessions while
broader semantic authority remains governed by parity and authority-transfer
rules.

### Structured Status Strip

Live mode must render a structured top status instead of one wrapped diagnostic
sentence. The status strip must expose:

- `TET4D`
- current mode, such as `Live Plain 4D`
- scoped engine/session, such as `C++ Session`
- state, such as `Running`, `Paused`, or `Game Over`
- game-over reason when present
- immediate controls, such as `Fit View`, `Reset`, and `Esc`

Game-over state should render as a badge, for example `[ GAME OVER ]
out_of_bounds`, using the shell error/status visual role.

### Inspector Sections

Detailed live metadata belongs in the persistent inspector, formatted as
aligned key-value sections:

- `SESSION`: mode, engine, shell, topology.
- `STATUS`: state badge, reason, last input.
- `VIEW`: layout, fit state, camera/status summary.

The inspector must not collapse live metadata into prose paragraphs.

### Full And Quick Controls

Live and replay controls use two layers:

- Quick controls stay visible in compact viewport/bottom strips.
- Full controls stay visible in the right inspector and controls screen.

Live 4D full controls must include movement, rotation, camera, and system
groups; Q/E W movement; all six rotation pairs (`R/T`, `F/G`, `V/B`, `Y/U`,
`H/J`, `N/M`); camera pitch/yaw/zoom; pause/reset/back; and Fit View recovery.
Hints must render as keycap/action rows, not comma-separated prose.

### W-Slice Card Direction

W slices should move toward slice cards:

- stronger outer boundary than internal grid;
- dimmer internal grid;
- large stable `W SLICE n/N` headers;
- backed header chips;
- active, locked, and empty states remaining visually distinct.

Stage 33a does not require perfect 3D card meshes; readable headers, stronger
slice boundaries, and filled slice-card planes are sufficient for this repair.

### Acceptance Checklist

- Live Plain 4D opens with structured status, not diagnostic prose.
- C++ wording is scoped to the current live plain session.
- Game-over state appears as a clear badge.
- Full controls are readable and grouped.
- Quick controls remain visible.
- W slices read closer to slice cards than raw wireframes.
- Board hierarchy is stronger than the rejected Stage 33 live screenshot.
- Right inspector remains visible and the board area is not starved.
- Headless tests cover the visible contract.
- Manual GUI acceptance remains required before merge acceptance.

## Stage 33b Live Cockpit Declutter

Stage 33a moved the live cockpit in the right direction, but manual inspection
found two overcorrections: W-slice labels became title-like banners, and live
controls were repeated across the top, central board area, right inspector, and
bottom bar. Stage 33b is a reduction pass. It keeps the Stage 33a scoped status
and right-panel controls while removing visual noise from the central play
area.

Stage 33b remains Godot product-shell visual UX only. It does not change
gameplay, topology, movement, drop, collision, lock behavior, trace semantics,
replay-frame semantics, fixtures, parity logic, native C++ semantics, or
authority transfer.

### W Labels As Orientation Aids

W labels are orientation markers, not slice titles. They should use subtle
`w1`, `w2`, `w3`, `w4` style markers near a slice edge or corner. They should
be smaller and dimmer than active cells, locked cells, and board/slice
outlines, and they should not use large header chips by default.

The intended visual hierarchy is:

- active cells;
- locked cells;
- board/slice outlines;
- grid;
- W labels.

### One Primary Control Map

Live mode should have one primary visible control map: the full grouped
controls in the right inspector. The central board area must not repeat partial
samples such as `[A/D] X`, `[Q/E] W`, or `[R/T] XY`, because partial hints imply
those are the only important controls.

The top bar may continue to show mode, status, and immediate actions such as
Fit View, Reset, and Esc, but it should not become a second keycap control map.

### Live Bottom Bar

Live modes should hide or reduce the replay bottom bar so it does not compete
with the board. Replay-only actions such as `Prev`, `Next`, and `Quit Replay`
must not dominate live mode. If a live bottom action is ever shown, it must use
live wording such as Back, Quit Live, or Esc rather than `Quit Replay`.

### Right Inspector Controls

The right inspector remains the complete discoverable control surface. It must
retain movement, rotation, camera, and system groups, including Q/E W movement
and all six Live 4D rotation pairs (`R/T`, `F/G`, `V/B`, `Y/U`, `H/J`, `N/M`).

### Stage 33b Acceptance Checklist

- W labels are subtle orientation markers and no longer dominate the board.
- The central board area does not show partial quick-control rows in live mode.
- Controls are not repeated across board, right panel, and bottom bar.
- The right inspector remains the single complete live control map.
- The live bottom bar is hidden or reduced and does not show `Quit Replay`.
- The board has more visual priority than in Stage 33a.
- No gameplay, topology, replay, trace, parity, fixture, native semantic, or
  authority-transfer behavior changes.

## Stage 33c Live Cockpit Layout Consolidation

Manual review accepted the Stage 33b direction with remaining layout issues:
the live top status still had a dangling `Godot command/render shell` detail
line, Live Plain 4D still showed the replay case browser, and diagnostics /
quick settings competed with the full live controls in the right inspector.
Stage 33c consolidates those live-mode layout details without changing the
Stage 33b visual direction.

Stage 33c remains Godot product-shell visual UX only. It does not change
gameplay, topology, movement, drop, collision, lock behavior, trace semantics,
replay-frame semantics, fixtures, parity logic, native C++ semantics, or
authority transfer.

### Top Status Cleanup

Live modes keep the structured product status strip, including mode, scoped C++
session, state, game-over reason where present, and immediate actions such as
Fit View, Reset, and Esc. Detailed `Godot command/render shell` wording belongs
in the inspector session metadata, not as a dangling top-status or viewport
subline.

Top status text must trim safely when narrow and must not overlap panel
borders.

### Live Side Panel And Board Priority

Replay mode keeps the `Replay Cases` browser. Live Plain 2D, Live Plain 3D, and
Live Plain 4D hide the replay case-browser slot so the central board receives
the recovered horizontal space. Live mode must not show a left panel titled
`Replay Cases`.

The board remains the primary live visual element. Shell layout constants may
be adjusted or panel visibility may change to avoid starving the board, but
coordinate projection and board-state derivation semantics remain unchanged.

### Inspector Density

Live mode presents the full grouped controls first in the right inspector.
Diagnostics, events, and quick settings are secondary and appear after the
control map. Replay mode may keep replay diagnostics and case browsing in its
normal replay-oriented positions.

The right inspector remains the single complete live control map. It must
retain Q/E W movement and all six Live 4D rotation pairs (`R/T`, `F/G`, `V/B`,
`Y/U`, `H/J`, `N/M`). The central board, bottom bar, and top bar must not
reintroduce partial keycap samples such as `[A/D] X`, `[Q/E] W`, or `[R/T] XY`.

### Live Labels

Live mode must avoid replay-specific labels in visible live chrome. The live
bottom bar remains hidden or reduced and must not show `Quit Replay`; the live
quit/back action should use Back, Quit Live, or Esc according to the local UI
convention. Live diagnostics use generic `Diagnostics` wording instead of
`Replay Diagnostics`.

### W Labels

Stage 33c preserves the Stage 33b W-label rule. W labels remain small, muted
orientation markers and must not return to large `W SLICE n/N` banners or
header chips.

### Stage 33c Acceptance Checklist

- The live top status has no dangling or overlapping `Godot command/render
  shell` line.
- Live Plain 2D, Live Plain 3D, and Live Plain 4D do not show `Replay Cases` as
  a left-panel title.
- Live mode gives the recovered side-panel space to the board, and the board
  remains visually dominant.
- The central board area has no partial quick-control row.
- The right inspector remains the single full live control map.
- Diagnostics and quick settings are secondary in live mode.
- Live mode does not show `Quit Replay`.
- W labels remain subtle orientation markers.
- Replay mode still exposes the replay case browser and replay diagnostics as
  appropriate.
- No gameplay, topology, replay, trace, parity, fixture, native semantic, or
  authority-transfer behavior changes.
