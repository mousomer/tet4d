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
