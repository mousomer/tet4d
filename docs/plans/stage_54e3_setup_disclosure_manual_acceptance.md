# Stage 54E-3 Setup Disclosure Manual Acceptance

Role: checklist
Status: passed with advisories; external technical review pending
Source of truth: docs/rds/RDS_MENU_STRUCTURE.md sections 4.4 and 4.5
Supersedes: none
Stage: 54E-3 human-visible verification gate
Last updated: 2026-08-17

## Purpose

This record is the human-visible verification evidence for Stage 54E-3
setup/menu information architecture. It exists because the programme and task
contract claim real-window verification, and that claim must be reviewable
without re-running the work.

It is not Stage 54F integrated playability acceptance.

## Environment

| Item | Value |
| --- | --- |
| Godot | `4.7.1.stable.official.a13da4feb` |
| Binary | `/Applications/Godot.app/Contents/MacOS/Godot` |
| Platform | macOS (Darwin 25.6.0), arm64 |
| Renderer | real window, not headless |
| Window size | 1600 x 960 |
| Scene | `res://scenes/trace_replay.tscn` via `ReplayHud.open_game_setup()` |
| User state | throwaway `HOME`/`XDG_*`, fresh per run |
| Commit | Stage 54E-3b implementation plus review corrections |

The shell was driven through `open_game_setup()` so the panel receives the
normal `_apply_shell_style()` pass. Frames captured through `configure()`
directly bypass that pass and are not representative; an earlier capture round
was discarded for that reason.

## Verifier

Agent-driven session: the setup surface was exercised in a real window and the
rendered frames were inspected. This is **not** a human sign-off. External
technical review and any human acceptance remain outstanding, which is why the
stage is recorded as COMPLETE / REVIEW PENDING rather than reviewed green.

## Screenshots

`docs/design/screenshots/stage_54e3_setup_disclosure/`

| Frame | Shows |
| --- | --- |
| `live_2d_01_ordinary.png` | 2D ordinary path, no one-choice piece selector, no Controls |
| `live_3d_01_ordinary.png` | 3D ordinary path with piece-set choice |
| `live_4d_01_ordinary.png` | 4D Standard 5x10x4x4 fitting one screen |
| `live_4d_02_expanded_board.png` | Customize Board exposing X/Y/Z/W and Reset Sizes |
| `live_4d_02_expanded_controls.png` | Controls exposing Translation and Rotation |
| `live_4d_04_custom_reentered.png` | Custom 6x10x5x4 still obvious after leaving and re-entering |
| `live_4d_05_invalid_w1.png` | W=1 with True 4D pieces blocked and explained |
| `live_4d_06_advanced_fixed_seed.png` | Fixed Seed exposing Seed |
| `live_4d_07_advanced_true_random.png` | True Random hiding Seed |
| `live_4d_09_blocked_collapsed.png` | Blocked launch with the failure explained and `Show Problem` offered |
| `live_4d_10_blocked_revealed.png` | `Show Problem` opening Advanced Game and focusing Seed |

## Checklist

### 2D

- [x] Ordinary setup is concise: preset shortcut, Customize Board, Starting
      Speed, Advanced Game, Start Game, Reset Setup, Back.
- [x] No single-choice piece-set selector is presented.
- [x] No Controls disclosure is presented.
- [x] X/Y remain discoverable behind Customize Board.
- [x] Start Game is the obvious primary action.

### 3D

- [x] Piece-set choice is present and understandable in the ordinary path.
- [x] Exact dimensions remain discoverable behind Customize Board.
- [x] Controls is present, secondary, and collapsed by default.

### 4D Standard

- [x] The opening screen no longer reads as one long engineering form and fits
      the window without scrolling.
- [x] Standard 5x10x4x4 is immediately readable in the preset shortcut.
- [x] True 4D (5-cell) piece identity is clear, with its description.
- [x] Starting Speed is visible without entering a disclosure.
- [x] Exact X/Y/Z/W editing is discoverable but not permanently dominant.

### 4D custom

- [x] Dimensions can be customized to a non-preset valid shape (6x10x5x4).
- [x] The preset shortcut reads `Custom` for that shape.
- [x] After leaving to 2D setup and re-entering 4D, the board section is
      expanded and the custom dimensions are immediately visible.
- [x] Selecting the `Custom` entry exposes the editors without mutating the
      shape.

### 4D invalid W=1

- [x] With True 4D pieces and W=1, Start Game is disabled.
- [x] The summary states `Not launchable: spawn_not_viable @ $.piece_set_id`.
- [x] The failure remains actionable through `Show Problem`.

### Blocked launch recovery

- [x] An invalid seed with Advanced Game collapsed keeps the summary visible.
- [x] `Show Problem` is presented, enabled, and keyboard focusable.
- [x] Clicking it expands Advanced Game and focuses the Seed field.
- [x] Repairing the value withdraws the action and restores Start Game.

### Randomness

- [x] Advanced Game exposes Randomness.
- [x] Fixed Seed shows Seed; True Random hides it.
- [x] True Random keeps the generated effective-seed explanation.

### Keyboard

- [x] The complete setup surface is traversable with the keyboard only.
- [x] A 40-step Down traversal, toggling each disclosure it lands on, never
      loses the focus owner.
- [x] Undisclosed controls are skipped by the focus ring.

### Pointer

- [x] Every disclosure control toggles on click, in both directions, in all
      three modes.
- [x] Press does not toggle; release does, exactly once per click.
- [x] Principal actions are mouse-operable.

## Findings Corrected During Verification

1. The all-clear validation banner dominated the ordinary path with
   engineer-facing copy. It is now presented only alongside a failure or while
   board customization is open.
2. Start Game carried no primary emphasis. It now uses the shell's established
   `action_button` semantic role.

## Advisories Not Corrected Here

1. The validation summary can render in the accent colour instead of the error
   colour. `_refresh_validation_state()` switches `theme_type_variation` at
   runtime, but `replay_hud.gd::_apply_shell_style()` runs once per screen
   open, so the colour is not re-resolved. This is pre-existing and unchanged
   from commit `aafa19b1`; it is left out of Stage 54E-3 because folding visual
   polish into an information-architecture stage is out of scope. The failure
   remains legible and actionable in both colours.

## Reproduction

Copy `godot/Tet4D.Godot` to a scratch directory, point `HOME`, `XDG_CONFIG_HOME`,
`XDG_CACHE_HOME`, and `XDG_DATA_HOME` at fresh throwaway directories, and run
the project in a real window. Persisted `user://` state changes which sections
start expanded, so a stale home directory will not reproduce these frames.

The behaviour recorded above is additionally enforced by
`tests/test_setup_progressive_disclosure.gd` and
`tests/test_setup_field_taxonomy.gd`, which drive real pointer and key events
through the live scene tree rather than calling panel handlers.
