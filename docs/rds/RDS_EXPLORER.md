# Explorer Mode — Requirements and Design Specification

Status: Proposed v0.1 (owner-confirmed product identity; detailed policy pending acceptance)
Date: 2026-11-02
Target runtime: Godot 4.7.2 Live 4D; later dimension-compatible Live 3D
Canonical owner: this file for the **Godot Explorer delta** from ordinary Live gameplay
Source requirements: `docs/rds/RDS_4D_TETRIS.md`, `docs/rds/RDS_TETRIS_GENERAL.md`, and this file

## 1. Purpose and explicit product decision

Explorer lets the player understand 4D position, orientation, movement and
rotation through direct, low-pressure experimentation with **one active 4D game piece at a time**. It is not a separate game, geometry editor, Topology Laboratory,
rendering engine, input system, or application.

**Owner-confirmed design decision:** Explorer is first and foremost an
alternate rules mode of existing **Live 4D**. It reuses the game's styles,
geometry, camera, 4D slicing, controls, keybindings, input-resolution rules,
pieces, motion/rotation rendering and cockpit. The essential changes are
disabled automatic gravity, free deliberate movement, and a **small,
explicitly defined** set of translations/rotations otherwise disallowed in
ordinary Play.

Use the smallest viable set of rule-policy differences. A convenience added
specifically for Explorer must be an extension of the shared system, not a
parallel replacement for it.

This RDS owns the Godot practice-mode delta only. It does **not** supersede
the existing Python Topology Playground's Editor/Sandbox/Play contract or
silently transfer inherited Python topology semantics to Godot.

## 2. Precedence, shared ownership, and reuse requirement

Unless an Explorer exception is stated in this RDS, the corresponding Live 4D
requirement applies without change.

| Aspect | Requirement | Owner |
| --- | --- | --- |
| 4D piece shapes and rotations | Share standard Live 4D production geometry, piece definitions and native transformation rules | Native/established gameplay authority |
| Board topology and legal placement | Start with bounded/no-seam topology and use existing authoritative placement/movement facilities | Existing gameplay/topology contract |
| Rotation/translation frame | Same relative/absolute preference and effective view-to-command resolver | `ControlFrameMapping` and Live input contract |
| Camera / exact view basis / local orientation | Same `B + L + V/P` presentation model and reset/fit semantics | Existing Godot 4D presentation authorities |
| Slice decomposition and cell rendering | Same shared mapper, renderer, styles, themes, grid modes and geometry | Existing Godot render/presentation owners |
| Input actions and displayed keys | Same semantic action IDs, registered bindings, resolved labels and public control guides | `LiveInputContract` and current shell settings |
| UI structure | Reuse Live 4D cockpit, with conditional labels/disabled functions only where necessary | Existing Godot product shell |
| Restart/reset, lifecycle and navigation | Reuse the existing Live flow, with Explorer-specific semantics described below | Existing live session/shell owners |
| Explorer changes | A **bounded mode-policy delta** on shared movement/tick/rotation machinery | Existing authoritative gameplay implementation |

No forked Explorer renderer, copied `trace_replay_app.gd`, duplicate
input-binding dictionary, separate gameplay rules engine, or independent
Explorer projection/axis mapper. Extract reusable subcomponents from existing
owners if needed; do not solve the task by duplicating their algorithms.

Godot controls presentation and dispatch but cannot independently invent
inherited collision, piece transformation, topology, or gameplay truth.
Changes to deterministic behavior require the appropriate native authority
or a documented parity/conformance boundary.

## 3. Supported modes and scope

### 3.1 First delivery: Live 4D Explorer

- Explorer is selected as a **mode** of the existing Live 4D experience.
- Show one active 4D game piece using existing production shape data.
- The game board, 4D slices, styles, input-frame preferences, camera,
  renderer and cockpit are inherited.
- Initial topology is bounded. No wrapping, inversion, custom seams or
  selectable non-bounded topology in the first Godot Explorer.
- The initial learning emphasis is 4D manipulation. A later 3D Explorer
  shall consume the same mode-policy mechanism rather than a second engine.

### 3.2 Board and setup

- Reuse the existing validated Godot Live 4D setup, board extent authority,
  production piece selection and shared setup workflow.
- Explorer must not introduce independent dimensions, a separate
  configuration database or a second production piece catalog.
- **Compatibility distinction:** the legacy Python 4D exploration profile
  `8 × 9 × 7 × 6` is retained for its existing runtime. This does not
  mandate that the new Godot alternate Live mode replace the currently
  validated Live setup with those dimensions.
- The current selected/validated configuration is the default Godot
  Explorer configuration. A future named practice preset, if warranted,
  must use the same setup schema/validator.
- Explorer admission must not corrupt or silently replace a normal Play
  session or any saved setup.

### 3.3 Object population

There is one active game piece. Explorer does not implement multi-object
selection, cell painting, arbitrary object editing or custom topology
construction.

**Terminology and existing production data:** a strict 4D polycube
(polytesseract) is a face-connected union of unit 4D hypercubes.
The default native `standard_4d_5` catalog has seven five-cell game pieces.
`CROSS4`, `SKEW4_A`, `SKEW4_B` and `STAIR4` are face-connected.
`TEE4` and `CORK4` each comprise two disconnected components;
`FORK4` comprises three. These are existing production piece data.
Explorer inherits the same game pieces as Play. This catalog discrepancy
does not authorize changing piece definitions, gameplay traces or replay
compatibility. Any future connectedness requirement is separate.

If another production shape can be selected, that selection must reuse the
existing piece data and an established session/setup entry. It may never
introduce a second geometric authority. A multi-shape browser is not required
for the initial Explorer gate.

## 4. Mode-dependent gameplay policy

### 4.1 Compact rule delta

| Rule | Ordinary Live 4D | Explorer |
| --- | --- | --- |
| Automatic gravity tick | Active under gameplay timing | **Disabled** |
| Player movement on X/Z/current slice axis | Current legal commands and frame rules | **Same bindings/resolver**, permissive only where stated |
| Deliberate Y translation | Gravity/drop is asymmetric; ordinary Live has no Y-up command | **Permit deliberate Y− and Y+** |
| Piece rotation | Six existing plane families, normal legality | Same six actions; additional *named* relaxations only |
| Board bounds / piece integrity | Enforced by authoritative core | **Remain enforced** by default |
| Collision with occupied cells | Enforced | Remains enforced for any occupied scenario |
| Automatic landing, lock and next-piece progression | Normal gameplay lifecycle | **Must not occur due to elapsed time** |
| Score, clears, game-over | Normal gameplay | Must not advance merely due to Explorer frames |
| Styles / camera / input / cockpit | Existing Live implementation | **Inherited**, not duplicated |

The phrase **free movement** means deliberate access to both signs of all
four canonical axes without gravity or time pressure. It does **not** by
itself mean moving an object outside the bounded board, overlapping cells,
skipping collision validation, allowing arbitrary continuous angles, or
changing topology transport semantics.

### 4.2 Gravity and time

1. While Explorer is active, normal frame updates must not invoke the
   gravity-driven piece descent or its lock continuation.
2. Pausing, onboarding, resize, focus loss, camera motion and idle periods
   must not cause accumulated gravity to execute on resume.
3. There must be no hidden lock timer whose expiration advances the piece.
4. Explorer's simulation state remains stable for an unlimited number of
   frames without piece actions.
5. Normal Live gameplay gravity, scoring and lifecycle are bit-for-bit
   unaffected by this mode decision; the off-policy path is not applied to Play.

### 4.3 Deliberate translation

1. Maintain X/Z/active-slice movement semantics and relative/absolute frame
   behavior, including the existing 4D `B + Q(L.local_yaw)` resolution.
2. Add support for *deliberate* moves along canonical `−Y` and `+Y` while
   Explorer is active. Y is still visibly labeled Y and is not reclassified
   as a camera or slice axis.
3. The native command/pose authority, rather than GDScript, validates and
   applies deliberate Y moves. Reuse the existing command pipeline or extend
   that same pipeline; do not manufacture a separate Explorer movement engine.
4. A blocked move returns a meaningful rejected result without altering
   pose, occupancy or session progression.
5. Translation repetition follows the existing Live input-repeat behavior
   unless a documented, user-tested policy requires a difference.
6. Relative translation remains relative to the current presented frame for
   X/Z/slice intents; gravity-axis moves remain along canonical ±Y.
7. A change to camera framing alone must not change which canonical command
   a given Live 4D movement intent resolves to.

### 4.4 Piece rotation

1. Reuse all existing Live 4D rotation plane actions: XY, XZ, YZ, XW, YW
   and ZW, each in positive/negative quarter turns.
2. Preserve native exact geometry, existing frame resolution and existing
   animation. Do not create an Explorer-only rotation algorithm.
3. Explorer may relax only *identified normal-Play restrictions*, through
   the shared authoritative policy. Any override must specify the predicate
   being bypassed and the invariant still enforced.
4. An invalid transformation must fail atomically and never lose, duplicate,
   overlap or unexpectedly deform piece cells.
5. Generic collision bypass, out-of-bounds rendering, free-angle geometric
   rotation and speculative wall kicks are **not authorized** by this RDS.
6. **Decision still required:** precisely which currently rejected
   rotations/placements should become legal in Explorer. The implementation
   must inventory reproducible examples from current Live 4D before activating
   a relaxation. The owner-approved list becomes an explicit policy table
   and test fixture; no agent may infer it from the word "free".

### 4.5 Soft drop, hard drop, Hold and game progression

These controls currently have game-progression meanings. The first Explorer
must prevent inadvertent progression or piece replacement during practice.

- The existing action identities and bindings must not be reassigned to an
  unrelated operation merely to avoid adding an action.
- Gravity-free practice cannot interpret a held Soft Drop as automatic lock.
- Hard Drop must not lock the active piece and spawn a new piece unless a
  separately accepted Explorer policy explicitly authorizes it.
- Hold, NEXT, score, ghost and terminal status remain shared UI components,
  but a component with no valid Explorer meaning must be marked unavailable
  or contextually hidden within the **same** cockpit structure. Do not
  introduce a redesigned cockpit to address their inapplicability.
- No implicit line-clear, score accumulation or automatic game-over during
  ordinary object manipulation.
- An explicit transition back to normal Play restores **normal Play rules**
  through its established validated session route; it must not import the
  Explorer pose into the Play state without a separate product decision.

## 5. Input, keys and control discoverability

1. Explorer uses the existing Live 4D key/action mapping for every shared
   operation. It has **no private keybinding profile or replacement keymap**.
2. The six rotation pairs, X/Z/W translations, exact XZ/XW/ZW basis turns,
   `O/L` yaw, `I/K` pitch, pointer gestures, Fit and Reset View must
   continue to work as in Live 4D.
3. New Y−/Y+ commands need an input path. Reuse an existing correctly
   scoped semantic action when available; otherwise extend the **shared**
   `LiveInputContract` action metadata and corresponding central resolver.
   That addition is mode-gated, not a second independent Explorer key system.
4. The inherited Python `explorer` keybinding group and `move_up/down`
   requirements remain authoritative for **Python**, not automatically for
   new Godot defaults.
5. The actual Y−/Y+ shortcut assignments are **unselected** here. They
   require owner-approved conflict analysis against existing Live 4D keys,
   macOS shortcuts and discoverability before implementation. Do not
   silently choose or overload keys.
6. Any new action must appear in the same generated control/help presentation
   path as current controls, only when applicable.
7. Effective labels must reflect currently resolved bindings; Explorer
   cannot display one command while dispatching another.
8. No key already used for Live 4D piece rotation, exact basis change or
   view/reset may change its meaning merely because Explorer is active,
   except a deliberate, documented future control decision.

## 6. Camera, basis, slices, rendering and styles

These systems are inherited **without a new mode-specific owner**.

1. Use the current exact `SliceBasis4D` signed-axis state, shared
   `SliceLocalOrientation`, existing slice anchors/layout, `CameraRig`,
   `ControlFrameMapping`, shared world-coordinate mapper and renderer.
2. Canonical piece rotations alter piece geometry; exact view-basis turns
   do not. Camera pan/orbit/zoom and Fit do not change piece geometry,
   placement or deterministic piece identity.
3. Normal Live 4D retains the fixed visible +Y basis slot and the
   existing XZ/XW/ZW exact view turns. Explorer additionally permits
   **XY/YZ/YW exact view-plane quarter turns**. These can move canonical
   Y into a horizontal, depth or slicing slot. This needs an extension
   of the **same** `SliceBasis4D`, coordinate mapper, signed dimension
   derivation, `ControlFrameMapping` and UI indicators, not a new camera
   or a UI-only shortcut. Explorer must not apply its expanded basis
   admissibility to ordinary Play.
4. Explorer inherits shipped styles, Designer-origin presentation profiles,
   palette roles, opacity hierarchy, grid modes and user settings. No
   Explorer style selector, theme catalog, material system or independent
   configuration storage is added.
5. Preserve rotation tweens, projection guides and snapshot-stable 4D
   slice geometry already specified in the 4D RDS.
6. Reset View retains the Live 4D presentation-only reset semantics.
   A piece reset or Explorer restart must use the existing reset/lifecycle
   ownership while respecting the no-gravity policy.
7. Do not change accepted Stage 58B geometry or locked Live cockpit
   arrangements just to accommodate Explorer.

### 6.1 Exact view axis-turn inventory

A quarter-turn in a coordinate plane exchanges two **signed** axes.
A literal unsigned swap may instead be a reflection; it is not a
proper quarter-turn rotation.

| View plane (both ±90°) | Normal Live 4D | Explorer |
| --- | --- | --- |
| XZ | Available: 1 / 2 | Reuse |
| XW | Available: 3 / 4 | Reuse |
| ZW | Available: 5 / 6 | Reuse |
| XY | **Not exposed / not supported by fixed-Y basis** | Enable via shared basis extension |
| YZ | **Not exposed / not supported by fixed-Y basis** | Enable via shared basis extension |
| YW | **Not exposed / not supported by fixed-Y basis** | Enable via shared basis extension |

Normal 4D's three exact view generators can reach 24 orientation-
preserving signed bases with visible +Y fixed. All six generators
can reach 192 proper signed orientations (4! permutations times
2^4 sign choices, divided by two for positive determinant). The
full signed-permutation set including reflections has 384 members.
These are mathematical counts, **not** claims of current runtime
capability. The new three view planes are unavailable until the
existing mapper, slice layout, labels and command resolver can
consume them safely.

Continuous slice yaw/pitch, mouse orientation, camera framing,
pan, zoom and Fit are already present in normal Live 4D. An
independent general camera roll is not exposed in normal play
and is not implicitly introduced by these exact view turns.

### 6.2 Object-rotation and translation inventory

| Object plane, ±90° | Normal Live 4D | Explorer |
| --- | --- | --- |
| XY | R / T | Reuse |
| XZ | F / G | Reuse |
| YZ | V / B | Reuse |
| XW | Y / U | Reuse |
| YW | H / J | Reuse |
| ZW | N / M | Reuse |

**All six object-rotation planes already exist in normal Play.**
Any particular turn can be rejected by the authoritative
placement/bounds/collision test. Explorer-only acceptance of
such a rejected attempt requires the named EX-D1 exception.
Do not mistake an unavailable view-plane rotation for an
unavailable object-rotation plane.

| Canonical translation | Normal Live 4D | Explorer |
| --- | --- | --- |
| −X, +X | Available | Same shared actions |
| −Y | No deliberate upward command | Add centrally |
| +Y | Gravity/Soft Drop/Hard Drop, not independent free-step command | Add deliberate step |
| −Z, +Z | Available | Same shared actions |
| −W, +W | Available | Same shared actions |

Existing X/Z/W **intents** are remapped through signed view basis
and relative yaw; this table names canonical axes, not fixed keys.
The native session currently dispatches X/Z/W moves and all six
rotation planes, but it does not dispatch \`move_y_neg/pos\`.
Its current placement rule permits a spawning piece to be
above the board's Y=0 top boundary. That existing spawn
exception does not justify unbounded Explorer translations.

### 6.3 Additional Y-involving view turns: acceptance contract

1. Keep one \`SliceBasis4D\`, shared projection pipeline and
   shared orientation state. Add Explorer-scoped admissible planes;
   normal Play still restricts exact view turns to XZ/XW/ZW.
2. The new Y-bearing view turns alter **presentation only**,
   never piece geometry, canonical cells, native identity,
   replay, collision or topology.
3. Generalize canonical-to-visible coordinate mapping, its inverse
   and visible board extents for all four signed basis slots. A
   basis that slices on Y may not treat the second visible slot
   as canonical Y or blindly use \`dims[Y]\`.
4. Explorer's gravity is Off. Display canonical Y and the
   current **screen-vertical axis** distinctly. A tilted/
   Y-sliced view must never claim that canonical +Y remains
   visibly downward when it is not.
5. Extend \`ControlFrameMapping\` consistently for relative
   movement, the added deliberate Y± actions, and all six
   object rotations after Y-changing view turns. Keep the
   absolute control frame a stable canonical escape path.
6. Verify the mapper's bijection/inverse for asymmetric
   dimensions and every new signed orientation. No disappearing,
   duplicated or mislabeled cells, stale layers or unwanted
   state changes are permitted.
7. Verify six signed view-action pairs, inverse and four-turn
   identity, compositions that place Y in the slice slot,
   reset, Fit, normal Play refusal of the extra view turns,
   and zero change to piece hash/replay identity on view-only
   actions.
8. Publish new view actions/keys only through the existing
   \`LiveInputContract\` and help system. The actual bindings
   for XY/YZ/YW are **EX-D7** (not yet selected); no private
   Explorer keymap may be created.

## 7. Entry, session isolation and navigation

1. Expose Explorer through an explicit action on the existing game navigation
   surface (the LEARN grouping is the initial product location). Do not
   create a separate product or executable.
2. Explorer launches the same Live 4D presentation/gameplay shell with the
   Explorer mode flag/policy selected at the session authority.
3. Switching to Explorer must not overwrite a suspended normal-game
   session, silently mix its score or seed with practice state, or reuse
   incompatible mode-policy state.
4. Exiting to the Main Menu follows existing shell navigation and clears
   transient Explorer mode state in the same lifecycle path as an ordinary
   session transition.
5. Restart in Explorer rebuilds/reinitializes the current chosen practice
   object and scenario under the **same Explorer policy**, not a normal
   gravity-running game.
6. Reset View stays presentation-only. The default Explorer restart behavior
   should follow the existing Live Restart view-reset contract; any alternate
   reset UX is a later explicit decision, not grounds for another state manager.
7. Starting Play from Explorer starts a validated ordinary bounded Live
   session and restores its gravity, drops and legality. No silent state
   conversion from the current practice pose.
8. Existing persistent setup and presentation preferences remain under
   current owners. Explorer introduces no independent accounts or server state.

## 8. Observability and learning aids

The first Explorer must be understandable without a new teaching application.

1. The inherited cockpit shall display that **Explorer** and **Gravity Off**
   are active; it must not falsely show a running gravity game.
2. Show the effective movement and rotation controls already supported by
   the shared control-guidance mechanism. Add the two Y directions when their
   shared actions are accepted.
3. On an attempted rejected movement/rotation, provide a concise reason when
   the authoritative result supplies one. Do not fabricate legality reasons
   in Godot from a picture.
4. The player must be able to tell whether they transformed the piece or
   changed only its view. Reuse existing view-basis/orientation indicators.
5. A later additive **Neighbors** overlay may identify face-adjacent cells
   in 3D/4D, especially across W layers. It must consume canonical adjacency
   truth and cannot equate projected proximity with 4D adjacency.
6. Neighbors, coordinate inspection and optional guided tasks must build on
   the same Live renderer/control plumbing; they do not justify a new
   Explorer viewport.
7. Research participant IDs, telemetry, server persistence, task grading,
   tutorial campaigns and a full topology editor are **outside this RDS's
   first implementation gate**.

## 9. Versioned policy and compatibility

The mode difference must be encoded as an explicit, reviewable
**gameplay/exploration policy**, not scattered conditions across Godot,
native code and UI. The same session code paths must be used wherever
their semantics coincide.

Minimum conceptual policy dimensions:

- `automatic_gravity`: normal Play enabled; Explorer disabled.
- `manual_y_translation`: normal Play unavailable; Explorer enabled.
- `rotation_exception_set`: normal Play unchanged; Explorer contains only
  specifically reviewed exception IDs; initially empty until documented.
- `automatic_lock_or_spawn`: no time-triggered continuation in Explorer.
- `topology_profile`: bounded for the first Godot Explorer.

This table specifies required **behavior**, not a mandatory public JSON
schema, GDScript class or separate storage format. The actual authority
and serialization boundary must be reviewed against current native
`PlainNDSession` and existing setup validation before implementation.

Do not add Explorer-only replay identity, serialization or snapshot fields
without a scoped compatibility contract. Normal Play's existing hashes,
replays, saved settings and deterministic traces must remain unchanged.

## 10. Required test and acceptance evidence

### 10.1 Normal-mode non-regression

- Identical existing 4D seed/setup and command stream with Explorer
  disabled produce the same canonical state, hash and replay behavior.
- No new Explorer action is accidentally reachable in normal Live Play.
- All existing Live input, camera-relative translation, exact basis,
  soft/hard-drop, lock, scoring, Hold, NEXT and restart tests remain green.
- Switching Explorer → Play restores normal gravity and navigation.

### 10.2 Explorer deterministic behavior

- After a long idle simulation with gravity disabled, the active piece,
  score, occupied cells and progress are unchanged.
- Both signs of X/Y/Z/W deliberate movement are accepted when the
  resulting legal placement is valid; invalid attempts preserve state.
- Every one of the six rotation planes and each sign is callable using
  the original action mapping and respects exact native geometry.
- For moves/rotations accepted in both modes, the same command yields
  the same canonical transformation. Policy differences are isolated to
  declared exceptions.
- Four quarter turns and turn/inverse cycles preserve geometry where
  intermediate placements are valid; no false acceptance is asserted
  for out-of-bounds intermediate states.
- All owner-approved exceptions have positive/negative fixtures and
  invariant checks. No exception means no untested bypass.
- A basis/camera-only operation changes no canonical piece coordinates or
  gameplay identity.
- Normal Play session data survives or is discarded on transition
  **only according to its existing documented lifecycle**; no state leakage.

### 10.3 UI and integration

- Explorer uses precisely the same style, grid, cell, 4D slice, camera and
  rotation-tween implementations as ordinary Live 4D.
- Shared key labels match the dispatched action after any supported
  configuration/presentation change.
- Existing 3D/4D camera-relative regressions from PR #158 are run on the
  shared path; Explorer test variants cover Y and W operations.
- Extended Explorer-only exact view mapping tests cover XY/YZ/YW,
  all 192 reachable proper signed 4D orientations, Y as slice axis,
  basis-relative commands, inverse mapping and canonical hash isolation.
  Normal Live 4D remains fixed +Y and unchanged.
- At 1280×720 and 1440×900 logical points, the active piece and applicable
  controls are visible; no newly inserted overlay clips the board.
- Real-user review demonstrates movement without gravitational pressure,
  Y-up recovery, piece/view differentiation and a safe return to normal
  Play. Record failures, not only successful runs.

### 10.4 Governance

- Review the owning `docs/rds/RDS_4D_TETRIS.md`,
  `docs/rds/RDS_KEYBINDINGS.md`,
  `docs/architecture/game_safe_4d_slice_basis.md`,
  `docs/architecture/authority_map.md` and
  `docs/architecture/topology_playground_current_authority.md`.
- Gameplay policy changes must be tested in the authoritative core and at
  the Godot consumer. Inherited Python semantics require oracle parity
  if touched; otherwise do not add artificial Python duplicates.
- Any actual authority transfer follows the repository authority-transfer
  protocol; **this RDS does not itself transfer runtime authority**.
- Select all applicable governed routes and run the focused tests,
  documentation/governance validators, and canonical repository gate
  prescribed by the resulting scope.

## 11. Explicit exclusions and boundaries

Not part of the initial Godot Explorer:

- a second game/application or rewritten 4D shell;
- independent controls, style settings, geometry, renderer or camera system;
- general object sculpting, multi-object placement or arbitrary 4D meshes;
- unbounded movement, wrap/invert/sphere/custom-gluing controls;
- independent topology editor or complete Python Topology Lab port;
- active gameplay gravity, automatic locking and puzzle progression during
  free manipulation;
- a challenge curriculum, scoring study, login, remote telemetry or
  physics/explosion mode;
- wholesale correction of unrelated Stage 59, Designer/replay or
  cockpit issues as an Explorer prerequisite.

## 12. Unresolved decisions — mandatory before affected code

The RDS intentionally does **not** invent missing owner decisions.

| ID | Unresolved decision | Conservative implementation rule |
| --- | --- | --- |
| EX-D1 | Exact existing Live 4D restrictions to relax for translations and rotations, beyond Y± and disabled gravity | Inventory current rejections and bring named cases for approval; initially no other bypass |
| EX-D2 | The shared conflict-free shortcut(s) for deliberate Y−/Y+ in Godot | Add no private keymap or overloaded shortcut; wire the approved centrally declared action(s) |
| EX-D3 | Whether an explicit Hard Drop may perform a non-locking reposition, or is simply disabled in Explorer | Disable its gameplay effect; do not lock/spawn |
| EX-D4 | Whether Hold or changing to another single piece is required in MVP | No new shape browser; preserve one active game piece and disable irrelevant progression |
| EX-D5 | Whether the first Godot Explorer needs a fixed named compact board preset | Use validated current Live setup, retain Python `8×9×7×6` profile in its runtime |
| EX-D6 | When neighbor/coordinate inspection becomes a mandatory acceptance gate | Keep as later additive work after working shared-mode manipulation |
| EX-D7 | Conflict-free shared input bindings for Explorer-only XY/YZ/YW exact view turns | Do not reuse existing rotation/movement/view keys; use shared input authority after approval |

A code agent must not resolve an unresolved product choice by inventing a
new semantic owner, keymap, topology policy, graphical shell or gameplay
exception. A bounded follow-up RDS revision records each selected decision
before enabling that behavior.

## 13. First implementation boundary

Deliver the **smallest vertical slice inside the existing Live 4D path**:

1. Identify the existing authoritative gravity, lock and move dispatch
   boundaries and the exact Live 4D input actions to preserve.
2. Add a session-scoped mode/policy that suppresses automatic gravity and
   consequent timed locking while preserving unchanged Play behavior.
3. Extend the same authoritative transformation path to support deliberate
   Y−/Y+; expose them only through centrally approved shared actions.
4. Render the same Live 4D board/piece and present Explorer/Gravity Off in the
   same cockpit; provide ordinary restart and return to Play.
5. Gate with deterministic native tests, Godot shared-path tests, camera-
   relative regression tests and real visible acceptance.

The additional Y-bearing exact view turns require their own **shared-
presentation-owner** extension and conformance gate; they cannot
be implemented by new shortcuts alone. Only then enumerate and
implement limited extra blocked-rotation or translation exceptions
after EX-D1 is explicitly resolved. Adjacency comprehension and
`EXPLORER_LEARNING_READY` follow as bounded additive slices.
