# Stage 54F Integrated Visual Acceptance Record

Role: verification record
Status: implemented; agent-driven real-window review green; independent human product review pending
Source of truth: Stage 54F task contract and the established Godot presentation authorities
Supersedes: none
Last updated: 2026-08-22

## Purpose

This record makes the Stage 54F baseline, bounded corrections, and
human-visible evidence reviewable. It is not a new visual authority and it is
not independent human sign-off. Durable behavior remains owned by the relevant
RDS, cockpit, 4D presentation, display/accessibility, NEXT, and Ghost
contracts.

## Environment

| Item | Value |
| --- | --- |
| Baseline commit | `6793cd0fb53c68d4a3b9644cb86ab95a6b3fe53c` |
| Candidate branch | `codex/54f-integrated-playability-visual-acceptance` |
| Godot | `4.7.1.stable.official.a13da4feb` |
| Binary | `/Applications/Godot.app/Contents/MacOS/Godot` |
| Renderer | Metal 4.0 Forward+, Apple M1 Pro; real DisplayServer windows |
| User state | isolated project copies with unique custom user-data directories |
| Window requests | 960x640, 1180x760, 1600x960, 1920x1080 |
| Supported minimum observed | the 960x640 request is clamped by product authority to 960x660 |

The application scene was instantiated through
`res://scenes/trace_replay.tscn`, configured through the production setup/live
entry paths, driven through real native sessions, and captured from the real
viewport. Headless tests were used only for structural regression evidence.

## Verifier and Acceptance Boundary

This was an agent-driven session: real windows, rendered frames, focus changes,
camera orbit, native hard drops, occupied boards, HUD density changes, and
accessibility modes were exercised and visually inspected. It is human-visible
evidence but not a human sign-off. Therefore the truthful terminal state is
`IMPLEMENTED / READY FOR INTEGRATED HUMAN REVIEW`.

## Baseline Findings

The accepted E5 baseline preserved cockpit, View Actions, NEXT, Ghost, and
relative-control semantics, but the integrated review confirmed these Stage
54F blockers:

1. Four-dimensional slice gutters were fixed and too tight for labels, spawn
   pieces, and perceptual separation (#69).
2. Internal-grid alpha values were ineffective because grid materials did not
   enable alpha transparency; the active-frame emphasis was also too heavy
   (#70).
3. W labels occupied slice geometry and could cross pieces, especially in
   occupied multi-row layouts.
4. The 2D active piece correctly spawned above the closed board but the visual
   grammar did not explain that space.
5. Runtime setup validation changed a theme variation without reapplying shell
   style; a collapsed error-owning disclosure had no redundant error signal.
6. Keyboard focus could move to a lower Settings reset action while the
   ScrollContainer remained at zero, leaving the focused action off-screen.
7. `display.show_w_labels`, `display.projection_strength`, and
   `display.board_detail` were exposed with inapplicable or misleading
   player-facing presentation.
8. `display.ui_scale` updated its stored/runtime factor but did not visibly
   resize an already-rendered live shell.

Live 3D depth, stateless View Actions, the E5 cockpit hierarchy, NEXT fidelity,
Ghost authority, and accepted movement/view semantics were not defective and
were not redesigned.

## Corrected Findings

### #69 and 4D label clearance

- `AdaptiveLayerLayout` now derives deterministic bounded horizontal and
  vertical gutters from visible board extents.
- Vertical gutters reserve the space between rows that is needed by W labels
  and above-board spawn pieces.
- W labels use a stable camera-facing side edge and sit below playable volume
  geometry. The fit envelope includes the label and active-spawn clearances.
- Stable membership, ordering, anchor-only composition, non-overlap, Fit, and
  lifecycle/persistence boundaries remain unchanged.

### #70 and volume readability

- Live grid materials now enable alpha transparency, making the governed grid
  alpha effective.
- Internal grid remains weakest, ordinary wireframe remains stronger, active
  frame remains distinct with reduced thickness, and pieces/Ghost remain the
  strongest content.
- High Contrast strengthens the same semantic roles without collapsing their
  ordering.
- Existing rear-face grids, floor lattice, cell faces/outlines, orthographic
  camera contract, and occlusion continue to make 3D and every W slice read as
  a volume. No projection redesign was introduced.

### Setup, Settings, and setting truthfulness

- Invalid setup refreshes shell styling at runtime and a collapsed invalid
  disclosure carries error styling plus literal `ERROR` text.
- Settings explicitly use automatic vertical scrolling and reveal every
  focused generated control or reset action with `ensure_control_visible()`.
- Settings declarations admit presentation UI contexts. Global Settings retain
  the complete taxonomy, while replay/live quick settings show only applicable
  rows.
- Player-facing labels now truthfully describe Cell Outline Strength, 4D Slice
  Labels, and Replay Object Scale. IDs, stored values, categories, reset
  ownership, and persistence schema are unchanged.
- Runtime UI scale now applies a responsive HUD-root transform with inverse
  logical bounds, so Large and Extra Large visibly reflow controls while the
  transformed shell still covers the viewport. ThemeDB receives the same
  fallback factor; Standard restores the identity transform.

### 2D spawn grammar

The gameplay spawn rule is unchanged. A subdued `SPAWN ENTRY` cue now sits
outside the upper-left board boundary and points toward the entry edge without
fabricating hidden cells or colliding with the active piece.

## Real-Window Matrix

| Surface | Evidence | Result |
| --- | --- | --- |
| 2D ordinary + large UI | active piece, Ghost, NEXT, minimal cockpit, explicit spawn entry | clear and intentionally flat |
| 3D canonical + rotated | active/Ghost depth, rear faces, floor lattice, NEXT, control guidance | volume readable; grid subordinate |
| 4D simple + occupied | four 3D volumes, multi-W active/Ghost, stable labels, NEXT | slices distinct and membership readable |
| 4D wide-W | eight slices in a deterministic multi-row arrangement | whole collection fits; labels and boards remain separate |
| 4D compact/standard/detailed HUD | density-specific inspector disclosure | board remains primary and NEXT remains prominent |
| 4D rotated | occupied board after outer camera orbit | volumes, labels, cells, and Ghost remain distinguishable |
| High Contrast | occupied 4D plus invalid setup | non-colour identity and hierarchy retained |
| Large/Extra Large UI | Live 2D at 1600x960; Settings at supported minimum | controls visibly enlarge; play remains coherent; Settings still scrolls |
| Settings minimum | OS-clamped 960x660 | all rows and both resets scroll into range |
| Settings focus reveal | focus moved directly to Reset Accessibility | scroll moved from 0 to 901 and focused control became visible |
| Setup invalid | Advanced Game collapsed with invalid seed | global summary, Show Problem, and `Advanced Game · ERROR` are unmistakable |
| Window matrix | 960x660, 1180x760, 1600x960, 1920x1080 | no essential overlap or unreachable action |

Reduced Motion changes no semantic visibility in this static presentation
work. The implementation adds no animation and no per-frame geometry rebuild;
the only dynamic label work reuses the existing camera-relative update over a
fixed label set.

## Explicit Acceptance Answers

### 2D

Yes for the candidate: it reads as an intentional finished 2D board, not a
flattened 3D volume. Piece, Ghost, grid, playable boundary, spawn entry, NEXT,
and minimal cockpit have distinct purposes.

### 3D

Yes for the candidate: canonical and rotated views preserve front/back,
floor, cell depth, and Ghost destination without wireframe noise dominating.

### 4D

Yes for the candidate: the screen presents multiple individually volumetric
3D boards indexed by W. Responsive gutters and stable labels preserve W
progression, and occupied/rotated evidence distinguishes active piece, Ghost,
locked cells, active frame, inactive wireframe, and internal grid.

### Overall

The candidate presents a coherent progression from simple 2D, through one 3D
volume, to multiple W-indexed 3D volumes. NEXT and recovery actions remain
prominent, View Actions remains visibly interactive and stateless, no
developer diagnostic copy returns to ordinary play, and no accepted semantic
system was reopened.

## Regression and Scope Result

- Cockpit: accepted E5 View/Display/Session grouping and dimensional
  disclosure preserved.
- Relative controls: no resolver/input/gizmo file changed; established
  cross-dimensional regression coverage remains green.
- NEXT: geometry/data construction untouched; representative embedded/native
  NEXT remains faithful in real windows and exhaustive tests remain green.
- Ghost: landing authority untouched; Ghost remains visible and subordinate to
  active cells in 2D, 3D, and 4D.
- Fit/Reset/Restart: lifecycle and semantics untouched; fit bounds changed only
  to include presentation clearance.
- Performance: no per-frame node churn, new line layers, shaders, timers, or
  gameplay queries were added.
- Native/gameplay/topology/persistence authority: unchanged.
- Hold: not implemented or absorbed; remains independently eligible.

## Automated Evidence

- Final isolated focused Godot suite: exit 0, `Godot replay tests passed.`
- `git diff --check`: passed.
- `./scripts/check_git_sanitation_repo.sh`: passed; 103 tests and 50 subtests.
- `./scripts/check_keybinding_contract.sh`: passed.
- `.venv/bin/python tools/governance/validate_project_contracts.py`: passed,
  114 required paths checked.
- `.venv/bin/python tools/governance/generate_configuration_reference.py
  --check`: passed.
- `GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot
  ./scripts/verify_godot_4_7.sh`: passed, including replay tests and 59 shared
  topology transport cases.
- `CODEX_MODE=1 ./scripts/verify.sh`: passed (`verify: OK`).

The deliberate settings replacement-failure cases and invalid native setup
inputs emit expected error logs while their suites pass. No native source was
changed, so additional native-only checks beyond the pinned/full gates were
not routed.

## Screenshots

Representative before/after evidence is stored in
`docs/design/screenshots/stage_54f_integrated_acceptance/`. These images are
review evidence, not pixel-diff golden tests. The directory README maps each
frame to the finding or matrix cell it demonstrates.

## Remaining Work

No Stage 54F blocker remains in automated or agent-driven real-window review.
Independent human integrated product review is still required. Stage 54G keeps
its existing release-hardening/final-manual-acceptance scope; this review found
no additional non-blocking cosmetic item that merits a new 54G entry.
