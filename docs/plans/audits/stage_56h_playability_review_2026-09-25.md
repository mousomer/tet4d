# Stage 56H Playability Pre-Review and Triage

Role: audit
Status: active
Source of truth: none
Supersedes: none
Review date: 2026-09-25
Recorded: 2026-09-26
Evidence source commit: `0a0196131c4f844696a03667418f35dee710fcba`
Stage authority: `docs/tasks/live_4d_cockpit_convergence.md`

## Purpose

This audit preserves the agent-driven Stage 56H pre-review and the product
triage derived from it. It is evidence for Stage 56H; it is not the human
acceptance and does not close the 190/200 A/B choice.

The tested build was Godot 4.7.2 on macOS / Apple M1 Pro at a
1440×900-point client with a fresh throwaway profile for each launch. The
tested product code remains representative of current master: intervening
changes before this audit was recorded were governance/documentation/tooling,
not `godot/` or `native/`.

"Played" means reproduced in the running game. "Code" means established from
source inspection only. Subjective visual judgments are identified as such.

## Executive conclusion

The pre-review found enough product defects that Stage 56H should not be run as
a pure human acceptance pass yet. A bounded repair slice, Stage 56H-R, should
precede the human long-play.

Stage 56G proved containment and reachability, not play quality. The new
evidence shows that a contained cockpit can still be poor to play: fixture
sessions leak into the game path, soft-drop repeat can prevent locking,
onboarding runs while gravity advances, NEXT/HOLD can be technically reachable
but effectively hidden, and several shell/platform states contradict what the
player sees.

The repair spec is
`docs/plans/stage_56h_playability_repair_plan.md`.

## Finding triage

| # | Finding | Evidence | Disposition |
| --- | --- | --- | --- |
| 1 | Quick-entry paths run fixture sessions at the wrong gameplay defaults | Played | **Repair before acceptance.** A game product must not silently enter deterministic trace-fixture gameplay. |
| 2 | NEXT and HOLD are below the fold at 1440×900 | Played | **Direct Stage 56H failure.** Reachability after heavy scrolling is not HOLD/NEXT emphasis. |
| 3 | Holding soft drop on the floor prevents locking | Played | **Repair before acceptance.** Repeated soft-drop commands reset the gravity accumulator and can indefinitely postpone the locking tick. |
| 4 | Grounded movement does not extend lock | Played | **Human gameplay decision.** Current behavior is deterministic but may be too harsh at higher speed. |
| 5 | Speed does not progress during a game | Code | **Product decision.** The review proves current behavior, not that progression is required. |
| 6 | Restart is immediate and uses different keys by mode | Played | **Evaluate in 56H.** Inconsistency is real; confirmation policy and final binding need human judgment. |
| 7 | Ctrl soft drop collides with macOS desktop switching when combined with arrow movement | Played | **Repair before macOS acceptance.** The authoritative binding must have a usable platform-safe path. |
| 8 | Live play continues after window focus is lost | Played | **Repair before sustained play.** Losing focus must not silently consume game time. |
| 9 | README from-source Godot command opens Designer; game menu shows an inert Designer card | Played/source | **Repair product-shell boundary.** Player and authoring surfaces are leaking into one another. |
| 10 | 4D onboarding teaches the camera while gravity keeps running | Played | **Stage 56H blocker.** First-use instruction must not kill the session it is teaching. |
| 11 | Default 2D board is 6×6 | Played | **Question, not defect.** Keep until human playtest establishes a problem. |
| 12 | Status badge says RUNNING while gameplay is paused | Played | **Correctness repair.** Player-visible state contradicts actual state. |
| 13 | Every default configured game starts from seed 1337 | Played/source | **Product decision.** Preserve until the intended default-randomness contract is decided. |
| 14 | Retina first launch opens below the supported apparent-size floor | Played | **Repair startup sizing.** Responsive behavior cannot compensate for an initially unsupported window. |

## Detailed assessment

### Game entry is not a real configured game

The game controller currently enters Live 2D directly for the game product.
The Tab mode cycle can then enter 3D/4D without Game Setup. Those sessions use
native defaults and trace-oriented piece catalogs rather than the tuned
configured-game path.

Observed consequences:

- unconfigured 2D fell at about 0.5 s per row while the HUD said Speed 1;
- configured 4D fell at the tuned ~1.7 s interval;
- Tab-path 4D used fixture pieces such as `TRACE_4D_NEXT`;
- unattended fresh launch reached GAME OVER in about 40 seconds.

This is a product-entry defect, not a label issue.

### NEXT/HOLD emphasis is not satisfied

At 1440×900 in configured 4D, NEXT and HOLD were below the fold. In 3D and the
Tab-path 4D session, NEXT could be visible while its thumbnail was cut off.

Stage 56G's scroll escape hatch proves reachability. Stage 56H owns a stronger
criterion: NEXT/HOLD must be useful during play without the player excavating
them from the deck.

First try to solve this within the current `PIECE | VIEW | PIECE STATE`
semantic order. If that cannot be done without destroying key/action
legibility, amend the contract explicitly rather than violating it silently.

### Soft drop can suppress locking

The app resets `_live_tick_accumulator` for both hard and soft drop. Held soft
drop repeats at its own rate, so a grounded piece can keep resetting the
gravity timer and remain active until release.

Soft drop may accelerate descent; it must not grant an indefinite
lock-prevention mechanism.

### Grounded movement has no lock-delay extension

A grounded piece locks on the next gravity tick even while lateral input is
being applied. At 4D speed 5 the remaining adjustment window was about 340 ms.

This is not automatically wrong. It is a gameplay-rule decision for the human
playtest after basic input/timing defects are removed.

### Speed is fixed for the session

The gravity interval is derived from setup at game start and does not progress
during play. The pre-review does not establish that level progression is
required.

### Restart semantics differ by dimension

2D uses R for immediate restart. In 4D, R is an XY piece rotation and
Backspace restarts immediately. Neither path asks for confirmation. Evaluate
this in the human Stage 56H run.

### Ctrl soft drop conflicts with macOS Spaces

3D/4D use arrow keys for movement and Ctrl for soft drop. On macOS,
Ctrl+Right can be consumed by Spaces.

`LiveInputContract` remains the sole binding authority. Any repair must use
that authority rather than an app-local alternate map.

### Focus loss does not suspend play

While the game window was on another macOS Space for about 14 seconds, the
active piece continued falling. A live game must not silently consume gameplay
time while the application is unfocused.

### Game/Designer shell separation leaks

The README's from-source command launches the default Godot project, whose
main scene/product identity is the Designer path. Conversely, the game build's
main menu constructs Design Laboratory UI even though the game controller does
not connect that action.

The player-facing game must not expose dead authoring actions, and the README
must give an unambiguous game-product launch command.

### Onboarding competes with gravity

The 4D onboarding sequence is primarily camera/view instruction while the
piece continues falling. A first-run game can end while the player is still
learning the view.

The repair should suspend automatic gravity while onboarding owns first-run
attention without blocking the input required to complete onboarding.

### 6×6 default is unresolved

Nothing in this review proves the 2D default is wrong. Treat it as a human
playability question.

### Pause badge is stale

A paused 2D session remained frozen while the prominent badge continued to
say `[ RUNNING ]`. Player-visible state must come from the current pause owner.

### Fixed default seed is unresolved

Configured games default to seed 1337, so restart reproduces the opening
sequence. This may be useful deterministic behavior or may be wrong for normal
play. Do not change it without a product decision.

### Retina startup size violates the tested floor

The logical viewport is 1600×960. On a 2× Retina display the initial client
appeared near 800×480 points, below the Stage 56G real-window range and visibly
clipping the shell.

Keep the logical design resolution. Fix the initial physical/apparent size.

## Visual/product review

### What works

- controlled, readable cube rendering;
- useful landing ghost and active-slice frames;
- coherent near-black / muted-gold shell palette;
- Tron Grid Flow remains a credible stronger-atmosphere style candidate.

### What does not yet work

The dominant visual problem is hierarchy: the board is not the primary object.
At 1440×900 the permanent helper/deck chrome can carry more perceptual weight
than the game itself. 3D is especially small relative to its available primary
surface. 4D uses width better, but permanent PIECE/VIEW reference material
still competes strongly with the playfield.

The shell also reads as an engineering instrument rather than a finished game:
pipe-separated status, engine-state vocabulary, fixture names, authoring
actions in player navigation, and diagnostic/settings vocabulary all compete
with Play.

Depth in 3D/4D is weak. Transparent locked cells muddy stacks, and cross-slice
fragments of a 4D piece lack a shared presentation cue.

### Constraint on the response

Do **not** turn the review's illustrative "40% board" suggestion into a numeric
contract. The evidence supports "board must be the primary visual object," not
a universal percentage.

Do not move NEXT/HOLD beside the board merely because the review suggested it.
The current Stage 56 contract owns `PIECE | VIEW | PIECE STATE`. First reduce
permanent helper footprint and improve PieceState visibility. If that fails,
change the contract explicitly.

## Deferred beyond 56H-R

The following may be valuable but are not prerequisites for a valid Stage 56H
human acceptance pass:

- audio;
- title/attract mode;
- broad front-door redesign;
- move/rotation interpolation;
- line-clear/hard-drop/game-over effects;
- score popups/level-up effects;
- comprehensive depth/lighting redesign;
- style-selection UX;
- final 190/200 visual A/B decision.

## Required sequence

1. Execute bounded Stage 56H-R from
   `docs/plans/stage_56h_playability_repair_plan.md`.
2. Run the actual human Stage 56H long-play / key-legibility / HOLD-NEXT
   acceptance.
3. Run the task-scoped governance post-mortem using retained raw session
   evidence.
4. Only then proceed to Stage 56I or decide on further governance work.

## Evidence captures

1. [First launch / unattended game over](../../design/screenshots/stage_56h_playability_review/01_first_launch_game_over.png)
2. [Paused gameplay with RUNNING badge](../../design/screenshots/stage_56h_playability_review/02_paused_badge_says_running.png)
3. [Main menu](../../design/screenshots/stage_56h_playability_review/03_main_menu.png)
4. [Live 3D mid-game](../../design/screenshots/stage_56h_playability_review/04_live_3d_midgame.png)
5. [Live 4D mid-game with NEXT cut off](../../design/screenshots/stage_56h_playability_review/05_live_4d_midgame_next_cut.png)
6. [Tab-path 4D fixture session](../../design/screenshots/stage_56h_playability_review/06_tab_path_trace_fixture_pieces.png)

## Limits

The play session was short and agent-driven. No high-speed line-clear session
was completed. Esc from 4D was not verified under clean conditions. Aesthetic
judgments are evidence for owner review, not authority. Human feel remains the
Stage 56H gate.
