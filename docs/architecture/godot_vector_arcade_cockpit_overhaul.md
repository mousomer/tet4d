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

## Stage 33d Compact Live Control Map

Manual review found Stage 33c substantially cleaner, with the remaining issue
that the complete right-panel Live Plain 4D control map was still too
vertically verbose. Stage 33d keeps the right inspector as the single full
control map, but compacts inverse controls into paired rows and adds one
rotation-direction hint.

Stage 33d remains Godot product-shell visual UX only. It changes only
control-map presentation and does not change input bindings, gameplay,
topology, movement, drop, collision, lock behavior, trace semantics,
replay-frame semantics, fixtures, parity logic, native C++ semantics, or
authority transfer.

### Inverse-Pair Grouping

Movement controls that form inverse pairs should render as one row per axis:

- `A / D`: `X- / X+`
- `W / S`: `Z+ / Z-`
- `Q / E`: `W- / W+`

Camera controls should follow the same compact pairing:

- `I / K`: pitch up / down
- `O / L`: yaw left / right
- `- / = / +`: zoom out / in

The display may include `+` with `=` for zoom-in discoverability, but the
underlying camera bindings remain unchanged.

### Rotation Plane Rows

Live Plain 4D rotation controls remain six visible plane-pair rows:

- `R / T`: `XY- / XY+`
- `F / G`: `XZ- / XZ+`
- `V / B`: `YZ- / YZ+`
- `Y / U`: `XW- / XW+`
- `H / J`: `YW- / YW+`
- `N / M`: `ZW- / ZW+`

The rotation section must include one section-level direction note:
`Left key: CCW · Right key: CW on plane`. Individual rows should not repeat
`Rotate`, `clockwise`, or `counter-clockwise`.

### System Rows

System controls are not inverse pairs and remain one-per-row: `P` pause,
`Backspace` reset, `Esc` back / quit, and `Fit View` fit view. System labels
should stay short enough to avoid making the control map tall again.

### Density And Non-Regression Rules

The full Live Plain 4D control map should be noticeably shorter than the Stage
33c version and should mostly fit in the first visible right-panel view before
diagnostics, inspector metadata, events, and settings. The pass must preserve
the Stage 33b/33c rules: subtle W labels, no central quick-control row, no
Replay Cases panel in live mode, no live `Quit Replay` wording, no live bottom
replay bar, and no dangling top-status `Godot command/render shell` detail.

### Stage 33d Acceptance Checklist

- Movement controls appear as paired rows, not six separate rows.
- Rotation controls appear as six compact plane-pair rows.
- The rotation section explains left key as CCW and right key as CW on the
  named plane.
- Rotation rows do not repeat `Rotate` wording.
- Camera controls appear as paired pitch, yaw, and zoom rows.
- System controls remain readable and complete.
- The full Live Plain 4D control map is shorter than Stage 33c.
- The right panel remains the single complete live control map.
- Stage 33b/33c layout decisions remain intact.
- No gameplay, topology, replay, trace, parity, fixture, native semantic, or
  authority-transfer behavior changes.

## Stage 33e Live Control Wording, Mouse Camera, And Palette Polish

Manual review found Stage 33d cleaner but still accepted with issues:
rotation wording remained awkward, game-over status exposed internal reason
strings, camera roll and mouse-camera controls were missing from the Live Plain
4D cockpit, and the Vector Arcade palette read too much like neon terminal
signage. Stage 33e is a focused presentation polish pass for those issues.

Stage 33e remains Godot product-shell, HUD, camera-presentation, and palette
work only. It does not change gameplay input command semantics, native C++
gameplay rules, topology, movement, drop, collision, lock behavior, trace
semantics, replay-frame semantics, fixtures, parity logic, Python oracle
authority, or authority transfer.

### Rotation Wording

The Live Plain 4D rotation section should read as `Plane Rotation`, with one
section-level direction hint: `Left: CCW · Right: CW`. Rows name the plane only:

- `R / T`: `XY`
- `F / G`: `XZ`
- `V / B`: `YZ`
- `Y / U`: `XW`
- `H / J`: `YW`
- `N / M`: `ZW`

Rows must not repeat `Rotate`, `clockwise`, or `counter-clockwise`, and the
underlying rotation input bindings remain unchanged.

### Game-Over Reason Labels

Live top/status/inspector text must use user-facing reason labels. Internal
snapshot values remain unchanged and may appear only in lower-level diagnostics
if needed. Required presentation mappings are:

- `out_of_bounds`: `Piece out of bounds`
- `spawn_blocked`: `Spawn blocked`
- `locked_above_top`: `Locked above board`
- `stopped`, empty, or missing: `Stopped`
- unknown values: prettified fallback text

Accepted top-strip wording includes `GAME OVER · Piece out of bounds`; raw
strings such as `out_of_bounds` should not appear in user-facing live status
or inspector rows.

### Camera Roll And Mouse Camera

Live Plain 4D camera controls are presentation-only and must not dispatch
gameplay commands. Keyboard camera controls include:

- `I / K`: pitch up / down
- `O / L`: yaw left / right
- `, / .`: roll left / right
- `- / = / +`: zoom out / in

Mouse camera hints and behavior are:

- drag: orbit
- Shift-drag: roll
- wheel: zoom
- double-click: Fit View

Fit View restores the canonical fitted W-slice camera and clears accumulated
manual roll as part of the existing fitted-view reset convention.

### Blueprint Arcade Palette

The default `tron` / `Vector Arcade` product theme shifts to a calmer
Blueprint Arcade palette. The intent is:

- cyan/teal board geometry without screaming wireframes;
- off-white and pale blue text;
- muted amber warning/status accents;
- restrained purple locked cells;
- red/orange only for error and bounds roles;
- reduced bright green and magenta in control hints.

Control-hint panels use distinct role mapping rather than the generic
`label.hint` fallback. Stage 33f owns the final config-first hint role
split.

### Stage 33e Follow-Up: Restart And Endgame Camera

Live game-over presentation keeps the keyboard reset bindings and also exposes
a visible `Restart Game` button in the top live status area. The button routes
to the existing reset signal and does not introduce gameplay ownership in
Godot.

Camera controls are presentation-only and should remain available after game
over. Live mouse camera gestures over the game viewport continue to orbit,
roll, zoom, and fit the camera while gameplay commands remain blocked once the
native live snapshot reports game over.

### Stage 33e Acceptance Checklist

- Rotation section reads naturally as `Plane Rotation`.
- The CCW/CW plane rule appears once at section level.
- Rotation rows are compact plane rows and not cryptic.
- Game-over reasons are user-facing, for example `Piece out of bounds`.
- Raw internal reason strings do not appear in user-facing live status.
- Camera roll appears in controls and is presentation-only.
- Mouse camera hints appear and route to camera-only presentation controls,
  including after live game over.
- Live game-over status exposes a visible `Restart Game` button.
- Palette is calmer and less green/magenta-heavy.
- Board readability and subtle W-label orientation markers are preserved.
- Stage 33b/33c/33d layout and compactness decisions remain intact.
- No gameplay, topology, replay, trace, parity, fixture, native semantic, or
  authority-transfer behavior changes.

## Stage 33f Config-First Calm Blueprint Cockpit Polish

Stage 33f repairs the Stage 33e follow-up hint-colour regression without
reverting the good endgame behavior from `3d4909a1`. `Restart Game` remains
visible after live game over, mouse camera controls remain usable after game
over, gameplay commands remain blocked after game over, and camera movement
remains presentation-only.

The stage is product-shell visual presentation only. It does not transfer
authority and does not change gameplay, topology, replay-frame, trace, parity,
fixture, or native C++ semantics.

### Config-First Design Rule

Palette and visual hierarchy values should live in style config/resources
where practical. GDScript may construct layout and map semantic UI states to
named roles, but should consume named palette roles instead of hard-coding
colours or derived visual constants in UI logic.

Stage 33f extends `shell_theme_palettes.json` and `ShellStyleRoles` with
config-owned cockpit roles:

- `accent.soft`
- `cell.secondary`
- `hint.section`
- `hint.keycap.border`
- `hint.keycap.text`
- `hint.action`
- `hint.note`
- `hint.error`

All required roles are present in `diagnostic`, `plain`, and `tron` themes.
Unknown role fallback remains deterministic through `ShellThemePalette`.

### Calm Blueprint Cockpit Palette

The default `tron` / `Vector Arcade` theme uses a calmer Blueprint Cockpit
palette:

- dark blue-black backgrounds;
- cyan/teal board geometry and section headers;
- off-white and pale-blue keycap/action text;
- muted grey-blue locked cells and W labels;
- amber reserved for warnings/notes;
- restrained red for error/game-over text;
- no bright-green keycap borders or magenta-dominant action labels.

`ReplayVisuals` consumes the config-owned `accent.soft` role rather than
deriving a soft accent in code.

### Hint Panel Hierarchy

The right controls panel must not collapse into one `label.hint` colour.
Control labels map to distinct roles:

- section headers: `hint.section`
- keycap border: `hint.keycap.border`
- keycap text: `hint.keycap.text`
- action labels: `hint.action`
- notes: `hint.note`
- game-over/error hint text: `hint.error`

These are visual roles only. Control group content, key bindings, and live
gameplay command routing remain unchanged.

### Stage 33f Acceptance Checklist

- `Restart Game` remains visible after live game over.
- Mouse camera controls remain usable after live game over.
- Gameplay commands remain blocked after live game over.
- Right controls panel has clear but calm section/key/action/note/error
  hierarchy.
- Ordinary controls are not dominated by bright green, magenta, or one
  lavender/pink text colour.
- Product/default palette values are config-owned.
- Board readability and subtle W-label orientation markers are preserved.
- Main board area still has no partial quick-control row.
- Right inspector remains the single full live control map.
- Live mode does not show `Replay Cases` or `Quit Replay` wording.
- Plane Rotation wording and the single CCW/CW rule remain intact.
- Game-over reason labels remain user-facing, for example
  `Piece out of bounds`.
- No gameplay, topology, replay, trace, parity, fixture, native semantic, or
  authority-transfer behavior changes.
