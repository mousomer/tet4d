# Stage 56H-R — bounded playability repair plan

Status: approved planning input for Stage 56H. R1.1 is complete (PR #141,
merge `fe108857`), R1.2 is complete locally and awaiting its narrow PR, and
R1.3 is complete (PR #137, merge `30548ca3`). R2 has not started. The Stage 56
task contract (`docs/tasks/live_4d_cockpit_convergence.md`, Stage 56H-R)
authorizes this tranche as its only bounded cross-layer exception.

Source evidence:
- `docs/plans/stage_56h_playability_review.md`
- six real-window captures under
  `docs/design/screenshots/stage_56h_playability_review/`
- Stage 56 contract:
  `docs/tasks/live_4d_cockpit_convergence.md`

## Purpose

Stage 56H was intended to be the human sustained-playability, key/action
legibility, and HOLD/NEXT-emphasis checkpoint. The agent pre-review found
reproducible defects that would contaminate that acceptance if the human test
were run immediately.

Stage 56H therefore gains one bounded repair tranche, **56H-R**, before human
acceptance. This is product work, not governance work and not Stage 56I polish.

The execution order is:

1. 56H-R1 — ordinary-session correctness;
2. 56H-R2 — lifecycle, onboarding, and platform-safe interaction;
3. 56H-R3 — cockpit/player-facing legibility;
4. canonical verification and real-window evidence;
5. human Stage 56H acceptance;
6. task-scoped governance post-mortem from the retained telemetry/transcripts;
7. only then decide whether P1b or Stage 56I proceeds.

## Governing constraints

- Godot is the shipped product surface.
- Native gameplay semantics stay native unless a reproduced defect requires a
  native correction.
- `LiveInputContract` remains the binding/action authority.
- Presentation changes must not alter deterministic gameplay identity.
- The Stage 56 semantic hierarchy remains `PIECE | VIEW | PIECE STATE`.
  56H-R may change sizing, density, visibility treatment, and player-facing
  chrome to satisfy playability, but it must not silently invent a second input
  map or piece-state model.
- The 190/200 A/B choice remains open.
- No release/distribution work belongs here.
- No P1b implementation belongs here. Existing P1a may be enabled locally and
  raw Claude/Codex transcripts must be retained for the post-mortem.

## Evidence triage

### Repair now

The following findings are reproduced defects or direct failures of the Stage
56H acceptance purpose:

1. ordinary quick-entry paths can run deterministic trace-fixture sessions
   instead of normal configured gameplay;
2. NEXT/HOLD are below the fold or clipped at the 1440×900 standard window;
3. repeated soft drop against the floor prevents normal locking;
7. the Ctrl soft-drop interaction collides with macOS desktop switching when
   combined with arrow movement;
8. live gameplay continues while the window has lost focus;
9. game/Designer product boundaries leak into ordinary player entry surfaces;
10. onboarding teaches controls while gravity continues underneath it;
12. the paused game can display `[ RUNNING ]`;
14. the default Retina window can open below the supported live-shell floor.

These define 56H-R.

### Human/product decisions after the repair

Do not silently change these during 56H-R:

4. whether grounded movement should extend lock time;
5. whether speed should progress during a game and what progression curve to
   use;
6. final restart-key semantics/confirmation policy, except where a current
   collision makes normal play unsafe;
11. whether 6×6 remains the default 2D board;
13. whether ordinary games should default to a fixed seed or a generated seed.

The human 56H session should evaluate these with a functioning build.

### Defer to Stage 56I or later unless needed to pass human 56H

- audio;
- title/attract-mode redesign;
- broad animation/effects work;
- global style-selection UX;
- motion interpolation;
- comprehensive depth-cue redesign.

A small presentation correction is allowed if the human playtest cannot read
the active piece or board state without it.

---

# 56H-R1 — ordinary-session correctness

## R1.1 Remove fixture gameplay from ordinary entry

### Problem

The game bootstrap and Tab quick paths can start a native default/trace
session. In 4D this exposes fixture pieces such as `TRACE_4D` and
`TRACE_4D_NEXT`, uses fixed ordering, and does not reproduce the configured
game timing.

### Required behavior

- The packaged/game bootstrap starts a normal configured game session.
- 2D/3D/4D quick switching starts the normal product session for the target
  dimension using the current/default game setup.
- Trace fixtures remain available only through explicit replay/diagnostic
  surfaces.
- Ordinary live gameplay must not expose `TRACE_*` fixture piece names.
- Switching dimension must not silently select a diagnostic/native fixture
  session.

### Likely implementation surface

- `godot/Tet4D.Godot/scenes/game_bootstrap.tscn`
- `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd`
- existing game setup/session launch path
- product-profile/bootstrap tests

Do not duplicate session construction. Route quick entry through the same
configured-game launch path already used by Main Menu → Play → Start.

### Regression evidence

Add/extend Godot tests proving:

- fresh game bootstrap creates ordinary gameplay, not a trace fixture;
- Tab 2D→3D→4D uses ordinary catalogs/session settings;
- no ordinary-session snapshot/presentation contains `TRACE_*`;
- replay/diagnostic fixture entry still works when explicitly selected.

### Completion

Complete: ordinary Game bootstrap, player-facing Live navigation, and Tab mode
switches now request the HUD's validated mode-specific setup and route through
`_start_configured_live_game(setup)`. The direct live-entry helpers remain the
explicit internal fixture/replay seam.

Regression: `godot/Tet4D.Godot/tests/test_ordinary_live_entry.gd` exercises
Game bootstrap, Tab 2D→3D→4D, the menu Start signal, and explicit replay entry.
It asserts that every ordinary live snapshot and player summary omit `TRACE_*`.

## R1.2 Fix blocked soft-drop lock starvation

### Problem

A held soft-drop repeat resets the gravity accumulator even when the piece
cannot move down. At the floor, holding soft drop can therefore keep the active
piece alive indefinitely until the key is released.

### Required behavior

- A successful soft-drop move may update timing according to the existing
  gameplay contract.
- A blocked repeated soft-drop must not postpone the lock/gravity decision.
- Holding soft drop continuously against the floor must still lock the piece
  within the normal lock/gravity cadence.
- Hard drop behavior and deterministic state remain unchanged except for the
  corrected blocked-soft-drop case.

### Likely implementation surface

- `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd`
  around live repeat processing/gravity accumulation;
- native session only if investigation proves the defect is native rather than
  app timing.

Prefer the smallest fix: only reset the relevant accumulator when a downward
movement actually succeeds, rather than on every repeat attempt.

### Regression evidence

A Godot test must hold the real soft-drop action against a grounded piece for
longer than one lock interval and prove that the piece locks without key
release.

Also prove:

- successful soft drop still moves repeatedly;
- hard drop still locks immediately;
- deterministic state/hash expectations change only where the corrected timing
  semantics require it.

### Completion

Complete: merged in PR #142 as `9a3ee5fa`.

- Finding and owner: native `Plain2DSession::tick()` and `PlainNDSession::tick()`
  already lock a piece when their next gravity/drop attempt is blocked. The
  starvation was Godot-owned timing orchestration: each live command helper
  cleared `_live_tick_accumulator` before it knew whether a held soft drop had
  moved. No native lock rule, lock delay, DAS/ARR, kick timing, speed curve, or
  deterministic state was changed.
- Fix: the three Godot live-command paths now consume the existing bridge command
  result and reset the accumulator only for hard drop or an authoritative
  `last_command_status=accepted` soft drop. The 2D session now propagates its
  already-computed `GameStepper2D` soft-drop result as `accepted`/`rejected`,
  matching the existing 3D/4D result contract; this is status fidelity needed
  by the Godot owner, not a gameplay-locking change.
- Regression: `test_blocked_soft_drop_locking.gd` starts ordinary 2D/3D/4D
  sessions, drives the real held soft-drop action past each mode's normal
  gravity interval, proves grounded pieces lock without release, verifies two
  successful repeated drops still advance authoritative state and preserve the
  accumulator cadence, and confirms hard drop still locks immediately with the
  native next-piece spawn order.
- Determinism: existing fixed command-stream hashes remain covered by
  `test_live_loop_parity_acceptance.gd`; only the formerly-starved held-input
  timing sequence gains its missing native tick/lock.

## R1.3 Pause status must be truthful

### Problem

The live state can be paused while the primary status badge still shows
`[ RUNNING ]`.

### Required behavior

- pause/unpause updates the displayed status in the same frame, from the app's
  authoritative pause flags;
- `[ PAUSED ]` is shown while paused;
- `[ RUNNING ]` is shown only while gameplay is advancing;
- game-over status remains distinct.

### Likely implementation surface

- pause command path in `trace_replay_app.gd`;
- snapshot/HUD refresh path;
- `replay_hud.gd` only if it is rendering stale state incorrectly.

### Repair and owner decision

This plan first required repairing the snapshot refresh path and ruled out an
independent pause boolean in the HUD. The first commit did exactly that
(`4dec403b`). The owner then chose to remove the redundant copy instead
(`212157ba`):

- The app no longer writes `_current_snapshot["paused"]`.
- The HUD derives the status from the pause flags that `set_live_*_mode()`
  already delivers on every refresh, and passes them explicitly to the summary
  and feedback text helpers. The HUD holds no pause state of its own; it renders
  the app's flags.

Known consequence: the native snapshot still carries a constant
`"paused": false` (`plain_2d_session.cpp`, `plain_nd_session.cpp`). No HUD
surface reads it, but the Design Laboratory fingerprint copies the snapshot and
so records that constant. Removing the native field is a separate native change.

### Completion

Complete: merged in PR #137 as `30548ca3`.

- Regression: `godot/Tet4D.Godot/tests/test_live_pause_status.gd` presses P in
  Live 2D, 3D, and 4D. It checks the badge, the `PAUSED` status word, and that
  pausing leaves the native state hash unchanged. Against the previous HUD it
  fails 6 checks.
- The Godot 4.7.2 suite passes (68 scripts), and so does
  `CODEX_MODE=1 ./scripts/verify.sh`.

---

# 56H-R2 — lifecycle, onboarding, and platform-safe interaction

## R2.1 Focus loss pauses ordinary live play

### Problem

The game continues advancing while its window is not focused. On macOS this
combines badly with desktop-Space switching.

### Required behavior

- Losing focus during a live game automatically pauses gameplay.
- Regaining focus does **not** silently resume; the user explicitly resumes.
- If the game was already paused, focus transitions preserve that state.
- Replay/Designer behavior must not be changed accidentally.

### Likely implementation surface

Use Godot window/application focus notifications at the app/shell boundary.
Do not poll platform-specific APIs.

### Regression evidence

Simulate/drive the focus-loss notification and prove:

- active-piece/gravity state stops advancing;
- UI reports paused;
- focus return leaves the game paused;
- explicit resume restores play.

### Completion

Complete: `NOTIFICATION_WM_WINDOW_FOCUS_OUT` at the `TraceReplayApp` shell
boundary ensures that a running Live 2D/3D/4D session is paused without
toggling an already-paused session. This is the Godot cross-platform
interactive-window focus-loss notification; it is preferred over polling or a
platform adapter because the app owns the live pause flags at that boundary.
Focus-in intentionally has no handler, so the player must explicitly resume.
The existing pause gate freezes gravity accumulation, and the handler resets
the existing held/repeat state so a key released while unfocused cannot produce
a phantom repeated command.

- Regression: `godot/Tet4D.Godot/tests/test_live_focus_loss_pause.gd` drives
  the actual Node focus notifications across configured Live 2D, 3D, and 4D
  sessions. It checks authoritative flags, HUD status, native state hashes,
  gravity freeze/resume, manual-pause idempotence, held-input cleanup, game-over
  preservation, replay, and Main Menu isolation.
- Native-state invariant: focus transitions do not invoke the native bridge;
  state hashes are equal immediately before and after focus pause and remain
  equal while paused.

R2.2–R2.4 remain unstarted.

## R2.2 Onboarding must not run a lethal background game

### Problem

The first-run tutorial teaches controls while gravity continues. A player can
reach GAME OVER while still reading/performing onboarding steps.

### Required behavior

For interactive onboarding shown over a live session:

- gameplay gravity/locking is suspended while the onboarding step is awaiting
  explanation/input;
- tutorial-required control actions may still be observed for progression;
- dismissing/completing the tutorial restores the prior running/paused state;
- opening onboarding must not mutate deterministic gameplay state merely
  because time passes;
- first-run onboarding cannot cause unattended GAME OVER.

Reuse the existing pause/lifecycle authority rather than inventing a second
simulation clock.

### Regression evidence

A first-run 2D and 4D onboarding test must run for longer than the previous
unattended game-over interval and prove no gravity/game-over progression occurs
while the guide owns the interaction.

## R2.3 Provide an OS-safe soft-drop interaction on macOS

### Problem

Ctrl is the live 3D/4D soft-drop action. Combining it with arrow movement can
trigger macOS Mission Control/Space switching before the game receives the
input.

### Required behavior

- There must be at least one canonical soft-drop binding for 3D/4D that can be
  held while performing ordinary lateral movement without invoking default
  macOS desktop switching.
- `LiveInputContract` remains the sole authority.
- Any retained Ctrl binding is compatibility/secondary input, not the only
  practical path on macOS.
- The displayed PIECE controls must show the authoritative usable binding.

### Implementation procedure

Before choosing the replacement/alternate key, audit the current canonical
3D/4D bindings for collisions. Do **not** guess a key in code and then update
the documentation to fit it.

The chosen binding must have automated collision coverage against the existing
piece, camera, Hold, restart, menu, and tutorial actions.

### Binding decision (authority reconciliation, owner-approved)

The collision audit covered every live 3D/4D binding in `LiveInputContract` and
the live input handlers, plus default operating-system shortcuts.

Keys already taken in 3D/4D:
- WASD and the arrow keys (move); `Q/E` (W move);
- `R/T`, `F/G`, `V/B`, `Y/U`, `H/J`, `N/M` (rotate); `I/K`, `O/L` (look);
- `1`–`6` and `0` (exact camera and reset view); `-`/`=`/`+` (zoom);
- `Space` (hard drop), `C` (Hold), `P` (pause), `Backspace` (restart);
- `Tab` (mode switch), `Esc` (menu).

In 2D only, `Z/X` rotate and `R`, `F`, and `H` are restart, fit, and help.

| Candidate | In-game conflict | macOS | Windows / Linux |
| --- | --- | --- | --- |
| Ctrl (current) | None | Ctrl+←/→ switches Space, Ctrl+↑/↓ opens Mission Control and App Exposé, Ctrl+Space switches input source | None |
| Shift | None; tests already assert Shift has no live camera role | Shift+arrows and Shift+Space have no system action | Windows shows its Sticky Keys prompt after five rapid Shift taps (default on, can be disabled) |
| Z | None in 3D/4D, but Z rotates in 2D | None | None |
| Alt/Option | None | None | Alt+Space opens the Windows window menu, and Space is hard drop |

Ctrl+Space matters in practice: holding soft drop and then pressing hard drop
switches the keyboard layout on any Mac with more than one input source.

Decision:
- **Shift** (either side) is the canonical 3D/4D soft-drop key, and every helper
  and PIECE row displays it. It sits beside WASD and beside the arrows, and it
  matches the Python runtime's LShift/RShift.
- **Ctrl** remains an undisplayed compatibility binding. It is never the only
  advertised path, because of the macOS collisions above.
- Z was rejected as less ergonomic with WASD and inconsistent with 2D. Alt was
  rejected because of the Windows window menu.

This deliberately reverses the earlier "Ctrl only; Shift does not trigger soft
drop" rule. The RDS documents and the Godot visual-system authority now state
the new contract. The runtime binding changes in the R2.3 implementation, which
must also:
- update `LiveInputContract.ACTION_SPECS` (display key Shift, keys Shift and
  Ctrl, no forbidden keys);
- replace the Ctrl-only assertions in `tests/test_live_input_contract.gd` and
  `tests/test_live_2d_shell.gd`;
- add the collision coverage required above.

No persisted-user migration is required, because Godot live bindings are a
fixed code contract and are not stored as user state.

## R2.4 Open the initial window inside the supported responsive envelope

### Problem

On a 2× Retina display the requested 1600×960 viewport can appear as an
800×480-point window, below the established 680×520 live-shell floor and with
visible clipping.

### Required behavior

- first launch on a high-DPI display opens at or above the supported live-shell
  minimum in logical/root-window coordinates;
- the Stage 56G real-root-window responsive policy remains the authority;
- no double-scaling assumption may derive the size from child
  `SubViewport` coordinates;
- restored user window sizes remain respected when valid.

### Regression/evidence

Add a deterministic sizing test where possible and record a real Retina
first-launch capture with a fresh profile.

---

# 56H-R3 — cockpit and player-facing legibility

## R3.1 NEXT/HOLD must be visible at the standard play window

### Problem

At 1440×900, 3D/4D can place NEXT/HOLD below the fold or clip the preview.
Stage 56H explicitly owns HOLD/NEXT emphasis.

### Required behavior

At the Stage 56G standard 1440×900 root window:

- PIECE, VIEW, and PIECE STATE remain in semantic order;
- NEXT and HOLD headings and useful state/previews are visible without
  scrolling;
- the primary board remains fully visible;
- the deck does not overlap the board;
- constrained smaller profiles may scroll as the established escape hatch,
  but standard play must not require scrolling to see NEXT/HOLD.

Do not move NEXT/HOLD beside the board as an unreviewed redesign. First make
the existing semantic cockpit work.

### Implementation direction

Re-evaluate the measured module minimums/density thresholds that currently
force PIECE and VIEW onto the first deck row and PIECE STATE onto the second.

Prefer, in order:

1. remove avoidable explanatory chrome;
2. tighten passive key/reference spacing;
3. use the existing compact density treatment at the correct threshold;
4. adjust module minima so the three semantic modules can coexist at the
   standard width.

Do not solve this by shrinking NEXT thumbnails into irrelevance.

### Acceptance evidence

Real-window captures and layout snapshots at least at:

- 1440×900;
- 1200×800;
- 1000×720;
- 860×640;
- 720×600;

for Live 2D/3D/4D, with occupied and empty Hold states represented.

1440×900 is a hard no-scroll acceptance for NEXT/HOLD.

## R3.2 Reduce player-visible developer vocabulary

### Problem

The primary live header/status currently exposes developer-state vocabulary and
fixture/engine concepts, e.g. command-state words and internal active-piece
names.

### Required behavior

The primary player surface should emphasize:

- mode;
- score;
- clears/level or speed where product-relevant;
- pause/game-over state;
- actionable recovery.

Internal command outcomes, diagnostic fields, and fixture identifiers belong
behind diagnostics/advanced surfaces, not in the primary player status.

This is presentation-only. Do not change scoring or gameplay semantics here.

## R3.3 Enforce game/Designer product boundaries

### Problem

The from-source command can launch Designer, and game surfaces can display
Designer/Design Laboratory affordances that are disconnected or inappropriate
for the game product.

### Required behavior

- the documented game-from-source command launches the game product entry;
- game product menus contain only connected game/player actions;
- Designer/Design Laboratory/authoring actions are hidden from the game product
  unless deliberately exposed through an explicitly player-appropriate route;
- Designer behavior remains intact in the Designer product.

Update README/documentation only after the executable entry points are correct.

---

# Human Stage 56H acceptance after 56H-R

The repair tranche does not itself accept Stage 56H.

After R1–R3 are green, perform a human play session from a fresh profile.

## Required session

At minimum:

1. fresh launch and onboarding in 2D;
2. sustained 2D play through several locks and at least one line clear;
3. 3D play using move, rotate, soft drop, hard drop, Hold, NEXT, pause,
   focus-loss/re-entry, restart, and setup change;
4. 4D play using W movement, piece rotations, exact camera rotations,
   yaw/pitch, pointer orientation/translation/zoom, Hold/NEXT, pause, and
   restart;
5. resize through standard and constrained Stage 56G sizes during active play;
6. macOS-specific simultaneous movement + soft drop without Space switching.

## Human questions to decide

Record explicit answers rather than letting implementation choose them:

- Is grounded adjustment time sufficient, or should movement reset/extend lock?
- Should level/speed progress during one game?
- Is restart confirmation needed and should restart have one cross-mode
  binding?
- Is 6×6 the desired default 2D board?
- Should ordinary games default to random/generated seed while still allowing
  an explicit fixed seed?
- Does the board read as the primary object despite the permanent cockpit?
- Is depth in 3D/4D sufficient for play, or does Stage 56I need stronger depth
  cues?
- Which of the 190/200 presentation alternatives is preferred, if both still
  comply?

## 56H acceptance gate

Stage 56H may be accepted only if:

- no ordinary product entry leaks trace-fixture gameplay;
- held soft drop cannot suppress locking;
- onboarding cannot kill the unattended first game;
- focus loss cannot silently advance live gameplay;
- the displayed pause/running state is truthful;
- macOS has a practical non-conflicting soft-drop path;
- fresh Retina launch starts inside the supported layout envelope;
- NEXT/HOLD are visible and legible without scroll at 1440×900;
- the player-facing game product does not expose dead/disconnected Designer
  controls;
- the human tester can sustain play in 2D/3D/4D and can identify the important
  actions without consulting source/developer diagnostics.

---

# Verification

Each R slice requires focused tests before the canonical gate.

Before declaring 56H-R complete:

1. run the full Godot 4.7.2 suite;
2. run the canonical local full repository gate,
   `CODEX_MODE=1 ./scripts/verify.sh`. CI workflows may run additional checks,
   but they do not substitute for this gate;
3. run the Stage 56G real-window responsive acceptance matrix;
4. capture fresh 1440×900 2D/3D/4D play images with NEXT/HOLD visible;
5. capture fresh first-launch Retina evidence;
6. preserve raw agent transcripts and P1a telemetry for the subsequent
   task-scoped post-mortem.

No test may be weakened to fit the repair.

# Explicit non-goals

56H-R does not authorize:

- generalized cockpit redesign;
- moving NEXT/HOLD outside the Stage 56 semantic hierarchy without a separate
  contract decision;
- audio;
- attract mode/title-screen production;
- broad animation polish;
- style-system redesign;
- topology work;
- release packaging/distribution;
- governance P1b/P1c/P2–P6;
- unrelated repository hygiene.

If a repair requires one of these, stop that subtask and record the dependency
rather than silently expanding scope.
