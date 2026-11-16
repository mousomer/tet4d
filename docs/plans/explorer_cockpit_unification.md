# Explorer cockpit unification — structure, keys and functionality

Role: spec
Status: active
Source of truth: this file for Explorer cockpit unification sequencing and its
behaviour lock
Supersedes: none
Authority: product contract `docs/architecture/bounded_practice_explorer.md`;
topology requirements `docs/rds/RDS_EXPLORER_TOPOLOGIES.md` §3, §4, §9, §11;
Explorer key contract `docs/rds/RDS_KEYBINDINGS.md` §4.4. The locked Live
2D/3D/4D cockpit and Main Menu (`test_locked_shell_layouts.gd`) are out of
scope and must not move.

## Goal

One Explorer cockpit for 2D, 3D and 4D: one structure, one key vocabulary,
one input dispatch path and one capability table. A dimension may *lack* a
capability (2D has no Z, W, orbit, basis or slice); it may not *spell* a shared
capability differently, place it elsewhere, or route it through a different
code path.

Today Explorer is three Live cockpits with practice patched in. The
unification makes the dimension a parameter of one Explorer descriptor that
the panel, the helper deck and the keyboard dispatcher all consume.

## Measured state (2026-11-11, `44bb2861`)

### Structure

| Element | 2D | 3D | 4D | Owner |
| --- | --- | --- | --- | --- |
| Deck placement | side rail | side rail | split | inherited from Live via `_uses_side_rail()` (`replay_hud.gd:924`) |
| Practice panel host | `_live_4d_state_module` | same | same | `replay_hud.gd:839` |
| Panel header | title, 2D/3D/4D/Play | same | same | `practice_explorer_panel.gd:22-31` |
| View page | topology selector + framing (Zoom, Fit, Reset) | orient, framing, pointer | exact 6 planes, orient, framing, slice, pointer | `practice_view_control_groups` (`live_input_contract.gd:123`) |
| Topology selector | on **View** page, visible | hidden | hidden | `practice_explorer_panel.gd:37-49, 85` |
| Piece page | selector, Replace, New target, move/rotate buttons (filtered by `minimum_dimension`), Retry | same | same | `practice_explorer_panel.gd:50-74` |
| Lower helper deck | practice piece groups (own 2D table) | Live 3D groups + Z/X row | Live 4D groups + Z/X row | `practice_piece_control_groups` (`live_input_contract.gd:255`) |
| Live VIEW module | hidden; strip reparented into View page | same | same | `replay_hud.gd:855-865` |
| Header buttons | Restart → "Retry Object", Play/Change Setup disabled | same | same | `replay_hud.gd:866-879` |

### Keys

| Command | 2D | 3D | 4D |
| --- | --- | --- | --- |
| Move X −/+ | A/D, ←/→ (`live_3d_move_x_*`) | A/D, ←/→ (camera-relative) | A/D, ←/→ (camera-relative) |
| Move Y −/+ (up/down) | **W/S, ↑/↓** (`live_3d_move_z_*`) | **Z/X, PgUp/PgDn** | **Z/X, PgUp/PgDn** |
| Move Z −/+ | — | W/S, ↑/↓ | W/S, ↑/↓ |
| Move W −/+ | — | — | Q/E |
| Rotate XY | R/T | R/T | R/T |
| Rotate XZ / YZ | — | F/G, V/B | F/G, V/B |
| Rotate XW / YW / ZW | — | — | Y/U, H/J, N/M |
| Replace piece | Space, P | Space, P | Space, P |
| Retry object | Backspace | Backspace | Backspace |
| Fit view | **F** | **double-click only** (F is rotate XZ−) | **double-click only** |
| Reset view | 0 | 0 | 0 |
| Zoom | −/= | −/= | −/= |
| Look yaw/pitch | — | O/L, I/K | O/L, I/K |
| View turns | — | **none** | 1–6 (XZ/XW/ZW), Shift+1–6 (XY/YZ/YW) |
| Slice inspect | — | — | [ / ] |
| Z and X keys | swallowed (Live 2D rotate) | move Y | move Y |

`RDS_KEYBINDINGS.md` §4.1 still lists 2D Explorer `move_up`/`move_down` as
Up/PageUp and Down/PageDown; the implementation and
`bounded_practice_explorer.md` say W/S or ↑/↓, and PageUp/PageDown do nothing
in 2D.

### Dispatch

Explorer input reaches `_practice_action` (`trace_replay_app.gd:1454`) through
four routes:

1. `_input`: VIEW descriptors and Space (`trace_replay_app.gd:249-264`).
2. `_unhandled_input` practice block: VIEW again, Replace, the 2D spec table
   `practice_2d_action_specs`, then Z/X (`trace_replay_app.gd:283-310`).
3. Ordinary Live dispatchers for 3D/4D piece keys, intercepted inside
   `_live_3d_command`/`_live_4d_command` (`trace_replay_app.gd:1948-1963`);
   `_live_2d_command` re-maps Live 2D names (`:1939`).
4. Live reset handlers intercepted to Retry (`trace_replay_app.gd:2152-2183`).

The panel buttons emit a third command vocabulary (`move_x_neg`,
`rotate_xy_pos`, `basis_xy_neg`…), which `_practice_action` shares with the
dispatchers. `cell` and `neighbors` commands remain in `_practice_action` with
no UI or key.

### Functionality

| Capability | 2D | 3D | 4D | Note |
| --- | --- | --- | --- | --- |
| Topology profiles | bounded, cylinder X/Y, torus | bounded only | bounded only | T2A native transport is 2D-only |
| Rotations on non-bounded topology | disabled | n/a | n/a | pending T2C |
| Exact view turns | — | — | 6 planes | 3D has orbit but no quarter-turn basis |
| New target | yes | yes | yes | |
| Slice inspection | — | — | yes | inherent |
| Canonical-axis buttons vs relative keys | equal (no camera) | differ | differ | documented, but unexplained in the UI |

## Divergences to remove

- **S1** Explorer placement follows Live (rail for 2D/3D, split for 4D), so the
  same panel reflows into two different cockpits.
- **S2** The topology selector sits on the View page and exists only in 2D,
  although topology is a property of the space, not the view.
- **S3** The practice panel lives in a node named for Live 4D state and is
  built lazily inside `set_practice_state`; its structure has no owner of its
  own.
- **K1** "Up/down" is W/S in 2D and Z/X in 3D/4D.
- **K2** Fit has a key only in 2D.
- **K3** 3D has no view turns although its orbit can leave the player
  disoriented; 4D has all six.
- **K4** The 2D Explorer borrows `live_3d_*` action IDs and a private spec
  table; 3D/4D borrow Live IDs through interception. Rebinding a Live 3D key
  silently rebinds 2D Explorer.
- **K5** `RDS_KEYBINDINGS.md` §4.1 contradicts the shipped 2D keys.
- **F1** Four dispatch routes, two of which live inside ordinary Play
  handlers. A Live change can break Explorer without touching Explorer code.
- **F2** Dead `cell`/`neighbors` commands and the unreachable `live_reset`
  branch in `practice_piece_control_groups` (`live_input_contract.gd:273`).

## Target model

### Explorer descriptor

A single static source, `ExplorerContract.profile(dimension)` (new
`scripts/input/explorer_contract.gd`, or a section of `LiveInputContract`),
returns per dimension:

- `axes`: translation axes and their action IDs and commands;
- `rotation_planes`: object planes with action IDs and commands;
- `view_groups`: exact turns, orient, framing, slice, pointer (today's
  `practice_view_control_groups`);
- `session`: Replace, Retry, New target, Play;
- `topologies`: available and visibly unavailable profiles;
- `capabilities`: `camera_orbit`, `basis_turns`, `slice`, `relative_frame`.

Every consumer reads it: the panel builds its buttons from it, the helper deck
renders its rows from it, the dispatcher matches its action IDs, and tests
assert against it. No consumer keeps its own list.

### Structure

```
Header: Explorer · ND   [2D][3D][4D]   [Play]
Tabs:   View | Piece | Space        (one tab set for every dimension)
  View   exact turns (if any) · orient (if any) · framing · slice (if any)
  Piece  selector · Replace · New target · canonical moves · rotations · Retry
  Space  topology selector + profile note (bounded-only in 3D/4D, labelled)
Feedback slot (fixed font-relative height)
Lower helper deck: one Explorer legend (translate / rotate / session)
```

The panel moves into its own `ExplorerCockpit` owner that the HUD places;
the HUD stops creating it inside `set_practice_state`. Placement stays
Live's per-dimension rail/split (Q1).

### Keys

One `explorer` action group with Explorer-owned IDs (`explorer_move_x_neg`…,
`explorer_rotate_xy_neg`…, `explorer_retry`, `explorer_fit_view`), whose
defaults copy today's bindings so Phases 1–3 change nothing visible. Live IDs
are no longer read in practice. The accepted key changes (Q2–Q4) land in
Phase 5.

| Command | 2D | 3D | 4D |
| --- | --- | --- | --- |
| Move Y up / down | Z / X, W / S, ↑ / ↓ | Z / X | Z / X |
| Fit view | 9, double-click | 9, double-click | 9, double-click |
| View turns | — | Shift+1/2 XY, 1/2 XZ, Shift+3/4 YZ | as 3D, plus 3/4 XW, 5/6 ZW, Shift+5/6 YW |

PageUp/PageDown are retired from Explorer in every dimension, including
legacy aliases. Z/X replace them as the common Y movement pair; 2D retains
W/S and arrow aliases. No helper may advertise the retired keys.

Godot persists no keybindings: `keyboard_rebinding` is a forbidden settings
category (`setting_spec.gd:26`), `project.godot` defines no input actions, and
every launch installs the `LiveInputContract` defaults
(`trace_replay_app.gd:2883`). The only override is runtime InputMap rebinding,
as used by tests and the manual rebind check; the retirement rule applies to
it. The saved profiles in `RDS_KEYBINDINGS.md` belong to the legacy Python
game and are not read by Godot. If Godot later persists bindings, loading
them must not resurrect retired aliases, must retain unrelated custom
bindings and must report retired assignments explicitly.

All other rows of the measured key table stay as they are.

### Dispatch

One `_handle_explorer_input(event)` in `_unhandled_input`, driven by the
descriptor and called before any Live handler. Movement bindings and Space
reserve early `_input` ownership so focused controls cannot take them. Movement
presses, releases and OS echo are consumed before GUI navigation; fresh presses
use the same dispatcher and held-repeat lifecycle. Modal input ownership wins. `_live_*_command` and
`_reset_live_*` lose their practice interceptions.

## Phases

Current execution status (2026-11-15, later): Phase 4 items 2–3 (Space tab in
every dimension, re-baselined lock) and Phase 5 items 1, 2 and 4 (Z/X Y keys,
PageUp/PageDown retired, Fit on 9, key docs) are implemented in the working
tree, together with one helper legend structure for 2D/3D/4D and a Space-tab
board size control. Phase 3 (structure owner extraction) and Phase 5 item 3
(3D view turns) remain open. Earlier status: Phases 0–2 are implemented and verified in this delivery. Phase 2 has independent Explorer action
IDs, unified dispatch and held-key lifecycle coverage. Phase 3 structure
ownership and Phases 4–6 visible changes/documentation/acceptance remain open.
The measured state above is the pre-refactor baseline, not a claim that the
accepted key and tab changes have landed. Human `EXPLORER_LEARNING_READY`
acceptance remains pending independently of these refactors.

Each phase lands as its own PR. Phases 0–3 are refactors: the key→command
matrix, tab/scroll state and every rectangle must stay identical. Node
identity is preserved during ordinary commands and dimension switches within
a running cockpit. Structural extraction may change construction-time paths
and IDs; migrate those assertions without weakening the lifecycle invariant.
Phases 4–5 change what the player sees, as the owner decided on
2026-11-11 (Q1–Q5 below).

### Phase 0 — Lock

Implementation: the lock uses a test-only app subclass to observe the production
`_practice_action` seam without executing commands. It records shifted/plain
keys (including unbound candidates), panel signals, helper rows/action IDs,
default InputMap bindings and visible relative node identities at 1280×800.
Factory setup and display inputs are pinned; the original InputMap and window
state are restored. Write mode always fails, and normal runs compare the
checked-in fixture with fresh observations and exercise negative mutations.
This test establishes the captured behavior; later-phase status is tracked above.

1. `tests/test_explorer_cockpit_lock.gd`: for 2D, 3D and 4D, record every
   default key (with and without Shift) → `_practice_action` command, every
   panel button → command, every helper row → action ID, and the visible
   nodes per tab, each identified by node name and role relative to the
   Explorer panel — never by absolute scene path or instance ID, which
   Phase 3 may change. Check in the matrix as
   `tests/fixtures/explorer_cockpit_baseline.json`.
2. Register it in `tests/run_tests.gd`; a write mode behind
   `TET4D_WRITE_EXPLORER_BASELINE=1` that always reports failure, as the
   typography lock does.
3. Capture the current behavior before refactoring. Keep the ordinary Live
   lock (`test_locked_shell_layouts.gd`) unchanged throughout every phase.
   Migrate Explorer integration assertions in the phase that changes their
   entry point or intentional UI expectation; preserve behavioral coverage.
   Baseline fixtures record expected behavior independently of the descriptor,
   so deriving implementation and expectations from it cannot mask errors.

### Phase 1 — Descriptor (pure refactor)

Implementation: `LiveInputContract.explorer_profile` supplies the detached
inventory to panel construction/visibility, helpers and the existing 2D
dispatch/repeat path. Legacy keys and allocation are preserved. Unexposed
inspection commands are removed from player dispatch; native/model query
coverage is retained. Phase 0 fixtures are not regenerated.

1. Add the Explorer descriptor; derive `practice_view_control_groups`,
   `practice_piece_control_groups` and `practice_2d_action_specs` from it,
   then delete the latter two.
2. Build the panel's Piece page from the descriptor instead of the
   `"xyzw"`/plane loops and `minimum_dimension` metadata.
3. Remove player dispatch for unexposed `cell`/`neighbors` commands and the
   unreachable `live_reset` branch (F2). Existing tests call these commands:
   migrate their panel-stability coverage to supported player actions and
   retain native/model inspection-query coverage. Do not delete inspection
   APIs merely because they have no player-facing binding.

Exit: Phase 0 matrix unchanged.

### Phase 2 — Dispatch (pure refactor)

Implemented contract: Explorer owns separate move/rotate/retry/view action IDs,
one `_handle_explorer_input` path in `_unhandled_input`, and its own held-movement
timers. `_input` reserves only Explorer Replace's early capture, alongside the
existing pointer/shell handling. Relative keyboard intents use the same
control-frame mapping; canonical panel buttons keep their direct commands.
For this refactor, 2D's W/S/arrow Y pair has temporary `explorer_2d_move_y_*`
IDs; 3D/4D Y retains Z/X/PageUp/PageDown and its existing one-shot behavior.
Phase 5 owns changing those defaults and repeat capabilities. Legacy action
registrations may remain unread for the frozen lock's compatibility projection.
An explicit test-only ID projection preserves the Phase 0 fixture; separate
tests prove new defaults and Live/Explorer rebinding isolation. Focus loss,
navigation and modal input ownership disarm held Explorer movement until a fresh
press, preventing a stale held key from moving an object on return.

1. Introduce Explorer action IDs with defaults equal to today's keys (K4).
   No saved-profile migration exists or is needed: Godot persists no
   bindings, so Explorer IDs start from the contract defaults at every launch.
2. Replace the four routes with `_handle_explorer_input` (F1); remove the
   practice branches from `_live_*_command` and `_reset_live_*`.
3. Add a test that rebinding a Live 3D key leaves Explorer unchanged, and the
   reverse. Migrate Explorer tests that directly call Live command/reset
   interceptors to the unified Explorer input path. Keep ordinary Play
   assertions against the original Live handlers and prove practice input
   cannot advance the native gameplay session. Cover held-key repeat,
   opposite-direction cancellation, modifiers, focus and early Space capture.

Exit: Phase 0 matrix unchanged; ordinary Live tests unchanged.

### Phase 3 — Structure owner (pure refactor)

1. Extract `ExplorerCockpit` (panel + its helper deck rows) from
   `replay_hud.gd`; the HUD creates it once and places it.
2. Rename the host so Explorer no longer lives in `_live_4d_state_module`
   (S3). Placement stays exactly as today.

Exit: Phase 0 matrix and all rectangles unchanged at 1280×800, 1280×720,
1440×900 and a narrow window.

### Phase 4 — Unified structure (visible; Q1, Q5)

1. Placement stays per-dimension (Q1); S1 is closed by unifying the panel
   contents, not the allocation. No rectangle in the Live lock may move.
2. Move the topology selector off View to a Space tab present in every
   dimension: 2D as today, 3D/4D Bounded only with later profiles disabled
   and labelled (S2, Q5). Tabs become View | Piece | Space everywhere.
3. Re-baseline Phase 0 (new tab and its controls only); update Explorer
   tests that assert two tabs or selector parentage to View/Piece/Space,
   retaining node/layout/scroll preservation through ordinary actions. Add
   the tab to the Explorer manual checklist, not to the Live lock test.

### Phase 5 — Unified keys and functionality (visible; Q2–Q4)

1. Up/down (K1, Q2): Z/X move Y in every dimension; 2D also keeps W/S
   and ↑/↓. Remove PageUp/PageDown aliases from all Explorer dimensions.
   Test presses, held keys and runtime InputMap rebinding: retired keys do
   not move the piece or appear in help, and rebinding cannot restore them.
   Z/X must bypass the Live 2D rotation swallow
   list in Explorer, while ordinary Live 2D Z/X still rotate.
2. Fit (K2, Q3): `explorer_fit_view` on `9` in every dimension, with the
   keycap in each VIEW helper; double-click stays; 2D F→Fit is removed.
3. 3D view turns (K3, Q4): XY/XZ/YZ quarter turns on Shift+1/2, 1/2 and
   Shift+3/4, through the 4D exact-turn path with a 3D basis. Test identity,
   inverse and four-turn return, object coordinates unchanged, Reset View
   restoring identity, and that ordinary Live 3D gains no view turns.
   Before implementation, extend the owning architecture contract,
   `docs/architecture/bounded_practice_explorer.md`, with the signed 3D
   presentation basis and its composition with camera orbit. The basis is
   Explorer-only: Live 3D camera/view rules in
   `docs/plans/gameboard_visual_language_design.md` are unchanged and remain
   that document's authority. Define
   relative translation and object-rotation plane mapping after XY/XZ/YZ
   turns (including when canonical Y is no longer screen vertical), while
   canonical-axis buttons continue to address the labelled canonical axes.
   Define basis-aware projection/inverse mapping and extent permutation for
   non-cubic boards. Rendering, helpers and input must consume the same basis
   without changing native geometry, legality, topology or object coordinates.
   Gate this capability on every reachable signed 3D basis: expected native
   displacement for relative keys and canonical buttons; signed rotation-plane
   mapping; projection/inverse round trips; non-cubic board bounds; orbit/basis
   composition; Retry preserving view; Reset restoring identity; and fresh
   ordinary Play restoring its existing Y-fixed behavior. Inverse/four-turn
   tests alone do not satisfy this gate.
4. Correct `RDS_KEYBINDINGS.md` §4.1/§4.4 and the 2D lines in
   `bounded_practice_explorer.md` (both copies) to the new keys (K5). Remove
   every Explorer `move_up`/`move_down` alias other than Z/X (and 2D's W/S and
   ↑/↓): PageUp/PageDown and the Numpad1/Numpad3 aliases listed in §4.1
   profiles. Godot binds no Numpad alias, so this is a documentation fix.
5. Re-baseline Phase 0; the diff must contain only the Q2–Q4 rows.

### Phase 6 — Documents and acceptance

1. Update `docs/architecture/bounded_practice_explorer.md` to describe one
   cockpit with dimension capabilities instead of per-dimension prose.
2. Fold the Explorer manual checks in `docs/plans/bounded_practice_explorer.md`
   into one dimension-parameterised checklist.
3. `EXPLORER_LEARNING_READY` stays pending; this plan does not promote it.

## Owner decisions (accepted 2026-11-11)

This plan records Q1–Q5. The owner correction in this review explicitly
requires retiring PageUp/PageDown and accepts the expanded 3D basis contract
and phase-specific test migrations. It supersedes the former Q2 alias text.

- **Q1 Placement — keep Live's per-dimension placement.** 2D/3D keep the side
  rail and 4D the split; only the panel contents are unified. No measured
  board allocation changes. Revisit after novice acceptance.
- **Q2 Up/down keys — Z/X everywhere, W/S also in 2D.** Z = up (Y−) and
  X = down (Y+) in 2D, 3D and 4D. PageUp/PageDown are retired in every
  Explorer dimension. 2D additionally keeps W/S and ↑/↓, because 2D's Y is the screen
  vertical. In 2D Explorer, Z/X stop being swallowed as Live 2D rotations.
- **Q3 Fit key — `9` in every dimension, double-click kept.** `9` sits next
  to Reset on `0` and is unbound today. 2D Explorer's F→Fit is retired so F
  means nothing in 2D and rotate XZ− in 3D/4D.
- **Q4 3D view turns — added.** 3D Explorer gains XY/XZ/YZ quarter turns on the
  4D keys for the same planes: Shift+1/2 XY, plain 1/2 XZ, Shift+3/4 YZ.
  Plain 3–6 and Shift+5/6 stay W-only and do nothing in 3D. The turns are
  presentation-only, with the 4D inverse/four-turn identity rules.
- **Q5 Topology tab — shown in every dimension.** A Space tab holds the
  topology selector in 2D, 3D and 4D. 3D/4D list Bounded as selectable and
  later profiles as visibly unavailable; nothing implies 3D/4D transport
  exists.

## Surface implementation interaction (2026-11-14)

The separately authorized `docs/architecture/explorer_surface_runtime.md` slice
adds selectable 2D surfaces, profile notes and surface-only Undo. Its intentional
lock delta is limited to topology options, hidden surface-control identities
and their typography inventory. Default key→command routes, Live rectangles
and the remaining unification Phases 3–6 remain open.
The Phase 0 fixture was re-baselined on 2026-11-15 for this delta only: the
four 2D topology-selector entries. RDS §2.5 additionally replaces only the
normal Sphere label and command with `Sphere` /
`topology_sphere_adjacent_positive`; keys, helpers and nodes retain the lock.

## Non-goals

- Live 2D/3D/4D cockpit allocation, Main Menu and their lock test.
- Ordinary Play keys, the Y-fixed Play basis and Live dispatch behaviour.
- Topology transport (T2C twisted seams, 3D/4D topologies) and the builder.
- New diagnostics in the rail; rejected-action feedback stays the only prose.

## Verification

```sh
"$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_practice_explorer.gd
"$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_explorer_cockpit_lock.gd
./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
git diff --check origin/master...HEAD
```

Run Godot tests with an isolated HOME. A test runner "passed" line is not
enough on its own; check for script errors in the log.

## Phase 2 owner review (pending)

Use the existing local game launch, enter Explorer and repeat in 2D/3D/4D:
move, hold/release opposite movement keys, rotate, Retry, replace with Space/P,
change view and return from Main Menu. Focus another app while holding a move;
return and confirm the object waits for a fresh press. Check that Space does
not also activate a focused GUI button. Runtime rebinding remains a test seam;
this phase adds no user-facing binding editor or saved profiles. Phase 5 key
changes, the Space tab, 3D view turns and novice learning acceptance stay open.


## Arrow-focus correction (2026-11-15)

Movement was reaching only `_unhandled_input`, allowing the internal TabBar
and focused controls to consume arrow navigation first. Pre-GUI ownership now
reserves descriptor movement bindings, including releases and echo; fresh presses
reuse `_handle_explorer_input`. Other commands retain their dispatch path and
modal/window-focus guards retain precedence. This supersedes Phase 2's
Space-only early-capture description. Real `Input.parse_input_event` regressions
focus the actual Explorer TabBar in every dimension and assert exactly one
piece move, unchanged tab selection, no echo command and modal suspension.

Arrow-focus verification: isolated-HOME `tests/run_practice_explorer.gd`, focused
cockpit-lock/Live-menu/navigation regressions, and
`CODEX_MODE=1 ./scripts/verify.sh` passed. No binding or lock baseline changed.
