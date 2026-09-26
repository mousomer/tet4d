# Stage 56H-R Playability Repair Plan

Role: spec
Status: active
Source of truth: docs/tasks/live_4d_cockpit_convergence.md
Supersedes: none
Created: 2026-09-26
Input audit: `docs/plans/audits/stage_56h_playability_review_2026-09-25.md`

## Objective

Repair the bounded product defects that currently make a Stage 56H human
playability acceptance misleading or invalid.

Stage 56H-R is **not** a new redesign stage. It prepares the existing Godot
game for the Stage 56H human long-play by fixing entry-path correctness,
gameplay timing/input defects, onboarding/focus lifecycle, player-visible state,
startup sizing, and HOLD/NEXT visibility.

Sequence:

`56H-R -> focused/full verification -> human 56H -> governance post-mortem -> 56I`

Do not begin Stage 56I, broad visual redesign, audio/animation work, or the
190/200 A/B decision inside this repair.

## Governing constraints

1. Godot remains the product shell.
2. `LiveInputContract` remains the only public action/binding authority.
3. Native gameplay remains the deterministic gameplay owner; GDScript may fix
   shell timing/input dispatch defects but must not duplicate gameplay legality.
4. Existing deterministic snapshot/hash semantics stay unchanged unless a
   reproduced defect proves the gameplay rule itself must change.
5. `LiveCockpit` keeps `PIECE | VIEW | PIECE STATE` unless measured repair
   evidence proves that contract cannot satisfy Stage 56H. Any exception
   requires an explicit contract amendment in the same change.
6. Stage 56G real-window geometry remains a regression contract.
7. Human/product decisions are not to be pre-decided by implementation.

## Must repair before human Stage 56H

- unconfigured fixture sessions exposed through game quick entry / Tab;
- held soft drop preventing lock;
- macOS-hostile soft-drop input path;
- gameplay continuing on focus loss;
- onboarding competing with gravity;
- paused gameplay displaying RUNNING;
- Retina first launch below supported responsive floor;
- NEXT/HOLD effectively hidden at 1440×900;
- game/Designer shell leakage and ambiguous README launch instructions.

## Must remain human/product decisions

- grounded lock delay / move reset;
- speed progression;
- restart confirmation and final restart key;
- 6×6 default;
- seed 1337 versus normal randomness;
- final 190/200 A/B choice.

## Explicitly deferred

- audio;
- interpolation;
- broad effects suite;
- title/attract mode;
- broad menu redesign;
- comprehensive lighting/depth redesign;
- style-selection UX.

## 56H-R1 — Real game entry and product-shell separation

### Current defect

`trace_replay_app.gd::_deferred_ready()` enters Live 2D directly for the game
product. Tab can enter Live 3D/4D without setup. The game menu constructs a
Design Laboratory command although the game product does not connect it. The
README default Godot command starts the Designer profile.

### Required behavior

1. `godot_game` starts at a stable player entry point, preferably Main Menu,
   not an already-running native-default session.
2. Play 2D/3D/4D starts only through validated configuration.
3. Tab/mode-cycle in the game product cannot manufacture an unconfigured
   session.
4. Game UI contains no enabled/inert Design Laboratory action.
5. Designer retains its authoring actions.
6. README gives an explicit game-product launch and separately documents
   Designer launch if useful.

### Likely surfaces

- `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd`
- `godot/Tet4D.Godot/scripts/ui/replay_hud.gd`
- game/designer bootstrap scenes and product profile staging if needed
- `README.md`

### Regression evidence

A product-profile lifecycle test must prove:

- fresh game startup has no unconfigured active live session;
- Play + Start creates a configured session;
- normal player navigation cannot surface fixture piece catalogs;
- game menu has no actionable Design Laboratory entry;
- Designer still has one;
- mode-cycle cannot create an unconfigured session.

## 56H-R2 — Soft-drop and input safety

### Held soft drop

Current command wrappers reset `_live_tick_accumulator` for both
`hard_drop` and `soft_drop`. Held soft drop can therefore postpone the
normal locking tick indefinitely.

Required behavior:

- holding soft drop on a grounded piece still permits normal locking;
- hard drop remains unchanged;
- no parallel GDScript lock-delay model is introduced.

Preferred direction: do not reset the normal gravity accumulator on every soft
drop repeat. If first-engagement scheduling changes, it must be bounded and
must not repeat while held.

Required test for 2D/3D/4D:

1. deterministic configured session;
2. ground active piece;
3. keep soft drop logically held/repeated for longer than one normal gravity
   interval;
4. assert lock/new-piece occurs without releasing soft drop.

The regression must fail on pre-fix master.

### macOS soft-drop binding

3D/4D Ctrl soft drop collides with common macOS Ctrl+Arrow Spaces shortcuts.

Required behavior:

- provide a discoverable soft-drop path usable simultaneously with movement;
- keep the binding exclusively in `LiveInputContract`;
- cockpit/help update from that authority;
- choose the replacement/alternate only after checking the complete key
  inventory for collisions;
- validate it in a real macOS window.

Do not create an app-local binding override.

## 56H-R3 — Focus and onboarding lifecycle

### Focus loss

Required live-game behavior:

- automatic ticks stop immediately on focus loss;
- held-repeat state is cleared;
- focus regain emits no stale movement/drop;
- player must explicitly resume unless an existing product authority requires
  auto-resume.

Implement at the app/window notification boundary and reuse the existing live
pause/timing owner. Do not add another gameplay clock.

Required tests:

- state/hash remains frozen across simulated gravity intervals after focus loss;
- repeat state clears;
- focus regain does not synthesize input;
- replay/Designer lifecycle is unchanged.

### Onboarding

While first-run onboarding is visible:

- automatic gravity is suspended;
- commands needed by the current tutorial step still work;
- camera/view instructions remain presentation-only;
- dismiss/completion resumes the configured gravity interval cleanly;
- merely displaying onboarding does not mutate deterministic gameplay state.

Use an explicit shell "gravity suspended by onboarding" condition if ordinary
pause would block required tutorial commands.

Required tests:

- visible onboarding prevents automatic ticks;
- tutorial commands still dispatch;
- completion/dismiss resumes gravity;
- no unattended first-run game can reach game over while the guide remains
  active.

## 56H-R4 — Truthful player-visible state

### Pause badge

The HUD must never say RUNNING while `_live_mode_paused()` is true.

Preferred repair: update/refresh the live snapshot's `paused` value through
the existing snapshot/HUD path before drawing status. Do not create a second
HUD pause owner.

Regression:

- pause via keyboard/action;
- native state stops;
- HUD reports PAUSED;
- resume restores RUNNING.

### Player-facing status

Keep this bounded. Remove only developer vocabulary that obstructs normal play:

- fixture names must not appear in configured player sessions;
- score, clears, speed/level, pause and game-over must be distinguishable
  without parsing internal command state;
- diagnostics may retain engine vocabulary behind diagnostics surfaces.

Do not turn this into a complete copywriting pass.

## 56H-R5 — Supported first-launch window size

Keep the logical 1600×960 design resolution and Stage 56G stretch semantics.

After display scale is known, ensure the initial **physical/apparent** client
starts inside the existing supported domain:

- hard floor: at least the Stage 56G smallest tested 720×600 apparent client;
- prefer the standard profile on desktop where usable display area permits;
- never resize beyond available usable display bounds.

Evidence:

- fresh macOS Retina launch measurement/capture;
- one 1× environment if available;
- rerun the Stage 56G real-window resize matrix.

## 56H-R6 — NEXT/HOLD visible emphasis

At 1440×900, normal play must expose:

- NEXT heading;
- at least one useful NEXT preview;
- HOLD state;
- without deck scrolling.

First attempt must remain inside the current semantic contract:

1. reduce unnecessary helper padding and repeated explanatory labels;
2. make key/action rows denser without becoming ambiguous;
3. reduce header/status chrome before shrinking the board;
4. give PieceState a measurable visible allocation at standard desktop size;
5. keep the board the primary visual object.

Do **not** encode an arbitrary board-area percentage.

### Contract escape hatch

If measured evidence shows the permanent
`PIECE | VIEW | PIECE STATE` arrangement cannot simultaneously provide:

- immediate NEXT/HOLD usefulness;
- key/action legibility;
- primary-board visual dominance;
- Stage 56G containment;

stop and record the contradiction. Only then amend the Stage 56 contract, for
example by moving the full key reference to an on-demand overlay while keeping
the same semantic/action authority.

### Responsive evidence

Test 2D/3D/4D at:

- 1440×900;
- 1200×800;
- 1000×720;
- 860×640;
- 720×600.

At 1440×900 assert no-scroll NEXT/HOLD visibility. Smaller profiles may use
the Stage 56G scroll escape hatch, but initial scroll position must remain
useful and bounded.

## Human decision queue after repair

The human Stage 56H record must explicitly cover:

### Grounded lock behavior

Test late lateral/rotational adjustment at several speeds and decide whether
next-gravity-tick lock is acceptable or a bounded lock delay/reset rule is
needed.

### Speed progression

Play long enough to clear multiple layers and decide whether fixed setup speed
is intentional or normal play needs progression.

### Restart

Test accidental restart risk in all dimensions. Decide consistent key policy
and whether mid-game restart needs confirmation or hold-to-confirm.

### 2D default size

Compare 6×6 against at least one larger board as a new-player experience.

### Randomness

Compare deterministic seed behavior with random-session behavior and decide
which belongs to normal player startup versus testing/replay.

## Verification

After each tranche, run focused Godot regressions that demonstrate
failing-before/passing-after evidence.

Before human Stage 56H:

1. `./gov explain --task "Stage 56H-R: repair playability blockers before human acceptance"`
   must route to `godot_product_shell`.
2. Run the complete Godot 4.7.2 suite.
3. Run Stage 56G real-window responsive acceptance.
4. Run product-profile/packaging boundary tests affected by game-vs-Designer
   separation.
5. Run the canonical repository verification gate.
6. Fresh-profile real-window smoke 2D/3D/4D at 1440×900.
7. Preserve raw agent transcript and P1a telemetry for the later governance
   post-mortem.

## Human Stage 56H acceptance

The acceptance itself remains a separate human step.

Minimum run:

1. fresh launch into game product;
2. configured 2D/3D/4D starts through player path;
3. sustained play with many locks and, where practical, layer clears;
4. exercise move/rotate/drop/hold, pause/resume, focus loss/return, restart,
   onboarding, NEXT/HOLD, 4D camera/exact view, and resizing;
5. record whether:
   - board is the primary visual object;
   - controls are discoverable without dominating play;
   - NEXT/HOLD are glanceable;
   - depth is readable enough for decisions;
   - unresolved gameplay choices above are acceptable.

Stage 56H passes only after that human record exists.

## Completion condition

56H-R is complete only when:

- every must-repair item has a regression or real-window proof;
- full Godot/repository gates pass;
- Stage 56G matrix stays green;
- fresh Retina launch is in supported range;
- configured game navigation cannot expose fixture sessions;
- no known defect invalidates the subsequent human Stage 56H run.
