# Godot Core-Port Plan

Role: migration architecture plan
Status: active plain 2D accepted; planning plain ND native parity
Last updated: 2026-05-23

## 1. Decision Summary

Godot is accepted as the primary product shell direction, conditional on
completed manual visual acceptance of the Stage 6/6b replay viewer. The
migration reason is UI and product-shell quality: menus, settings, diagnostics,
controls, replay readability, and future packaging surfaces. It is not a claim
that Godot owns stronger gameplay semantics or that rendering alone justifies
the migration.

The shell language remains GDScript. The recommended semantic-core language is
C++ through Godot GDExtension. C# remains an alternative only if implementation
speed clearly outweighs export, console, and long-term dependency concerns.

Python remains the oracle and reference implementation until the replacement
core passes trace parity against the Stage 2 topology/gameplay traces and the
Stage 3 endgame traces.

## 2. Why Godot

Godot is the preferred shell because the replay spike demonstrates a workable
product surface without requiring the engine to own gameplay semantics. The
current Godot project already provides a screen shell, case browser, replay
viewer, diagnostics, settings/help surfaces, keyboard hints, Fit View, Quit,
the Diagnostic/Tron theme split, and a container-owned layout that keeps the
game viewport and inspector in one managed hierarchy.

The engine choice is therefore driven by shell ergonomics:

- first-class scene/UI composition;
- fast iteration on menus and panels;
- portable desktop packaging path;
- a reasonable future path to Steam-oriented product surfaces;
- good separation between GDScript shell code and a native deterministic core;
- enough rendering capability for readable 2D/3D/4D board presentation.

Unity remains a useful Stage 5 comparison artifact, but Godot is the preferred
product shell direction after Stage 6/6b, subject to manual visual acceptance.

## 3. Why Not Python Runtime

The shipped Godot product must not call into the Python runtime. Runtime Python
would keep the migration coupled to the current development stack, complicate
packaging, increase startup and distribution risk, weaken console viability,
and blur ownership between the old implementation and the new product shell.

Python remains valuable as:

- the semantic oracle;
- the trace generator;
- the reference for topology, gameplay, and endgame behavior;
- the migration test authority until parity passes.

It must not become a hidden runtime dependency inside Godot.

## 4. Why Not GDScript Core

GDScript is appropriate for shell and presentation work, but it should not own
the deterministic core. The gameplay/topology/endgame core needs stricter
typing, explicit data ownership, portable performance, and clean testability
outside scene nodes.

Keeping semantics out of GDScript reduces these risks:

- gameplay behavior drifting into scene scripts;
- topology transport becoming presentation-coupled;
- replay-only scripts becoming accidental gameplay authority;
- performance surprises in 3D/4D topology checks and endgame simulation;
- weaker reuse for tests, tools, and future platform-specific builds.

GDScript should orchestrate views, menus, input, and rendering. It should call a
small deterministic core API once that core exists.

## 5. Core Language Recommendation: C++ GDExtension

C++ GDExtension is the recommended core-port path. It gives the project a native
deterministic core while keeping Godot itself as the product shell.

The expected benefits are:

- strong control over data layout and deterministic algorithms;
- portable performance for topology transport, legality checks, scoring, and
  endgame particle simulation;
- a runtime boundary that keeps semantics out of GDScript scene code;
- a better long-term fit for Steam and possible console work than a Python
  bridge or GDScript-only semantic core;
- a natural place to expose a compact Godot-facing API while preserving
  headless tests around the core.

The C++ core starts small. Stage 8 creates only a skeleton extension and
contract tests, not gameplay.

## 6. C# Alternative And Decision Criteria

C# is a viable alternative if port speed becomes the dominant concern. It may
be faster to write and easier to refactor for a small team already moving from
Python data models.

C# should be chosen only if these criteria outweigh the native-core concerns:

- faster validated parity against all golden traces;
- simpler development velocity for the team;
- acceptable export behavior for the target desktop platforms;
- no near-term console requirement that would punish the runtime choice;
- clear evidence that C++ GDExtension setup cost is slowing the migration more
  than it protects the product.

C# should not be chosen merely because it is convenient for shell code. If C#
is selected, it still must obey the same semantic boundary: no scene-owned
gameplay authority, no runtime Python calls, and trace parity before trust.

## 7. Final Architecture

The target architecture is:

```text
Python oracle
  -> golden traces and generated config bundle
  -> parity tests

Godot shell in GDScript
  -> menus, settings, rendering, replay, input, diagnostics
  -> calls deterministic native core through a narrow API

C++ GDExtension core
  -> gameplay state and rules
  -> topology transport
  -> scoring, lock, clear, spawn, and lifecycle rules
  -> endgame particle simulation
  -> replay/parity instrumentation
```

Config remains authored in the repo config files until an explicit migration
changes that authority. Generated bundles and copied Godot assets are inputs,
not sources of truth.

## 8. Godot/GDScript Responsibilities

GDScript owns product-shell behavior:

- main menu and screen navigation;
- setup/settings/help/controls surfaces;
- replay browser and replay viewer;
- rendering and display mode presentation;
- camera, viewport, and panel layout;
- user input routing at the shell boundary;
- diagnostics display;
- calling the native core through a narrow API once available;
- replay visual comparison surfaces during migration.

GDScript must not own gameplay rules, topology transport, scoring, locking,
line clears, endgame simulation, or deterministic replay semantics.

## 9. C++ Core Responsibilities

The C++ core should eventually own:

- deterministic game state for 2D, 3D, and 4D;
- board and active-piece data models;
- piece definitions and piece-local transforms;
- movement, rotation, kicks, drop, lock, spawn, and lifecycle rules;
- topology transport and topology profile validation;
- score, line/layer/full-plane clear behavior, and game-over detection;
- endgame locked-cell particle state and seam-aware movement;
- deterministic RNG behavior and seed handling;
- compact trace/parity hooks for comparison against Python-generated traces;
- a small Godot-facing API that exposes state snapshots without leaking scene
  nodes into the core.

The core should be testable without running a Godot scene.

## 10. Python Oracle Role

Python remains the source of semantic truth through the migration. Its role is
to generate and validate:

- topology movement and probe traces;
- gameplay traces for 2D/3D/4D;
- launch parity traces from Topology Lab;
- endgame particle traces;
- config bundle snapshots and schema metadata.

Python is not a long-term shipped runtime dependency for Godot. It remains the
reference until the new core passes trace parity and the project explicitly
updates the authority documents.

## 11. What Gets Ported

The port should eventually cover:

- plain 2D gameplay first;
- shared piece definitions and transform helpers;
- board model and sparse cell storage;
- input intent reducer and deterministic step lifecycle;
- lock, score, line clear, spawn, and game-over rules;
- 3D gameplay once 2D parity is stable;
- 4D gameplay once 3D parity is stable;
- topology transport and topology profile validation;
- Topology Lab launch semantics;
- locked-cell endgame particle simulation;
- trace export/parity instrumentation from the native core.

Porting order must follow trace coverage, not UI convenience.

## 12. What Must Not Be Ported

The first core-port stages must not port:

- Python runtime execution inside Godot;
- Pygame UI code;
- replay-only Godot snapshot extraction as gameplay logic;
- Unity spike code;
- development-only migration tooling as runtime code;
- scene/node layout state as semantic authority;
- trace JSON mutation;
- generated bundle files as authored config;
- topology/editor affordances before plain 2D gameplay parity.

Replay and shell code may be reused as presentation scaffolding only.

## 13. First Playable Milestone: Plain 2D

The first playable milestone is plain bounded 2D gameplay in Godot using the
native core. It should be intentionally narrow:

- one standard 2D board profile;
- standard 2D piece set;
- deterministic seed path;
- movement, rotation, soft drop, hard drop, gravity tick, lock, line clear,
  scoring, spawn, and game-over;
- Godot UI and rendering as shell only;
- no custom topology;
- no 3D/4D gameplay;
- no endgame simulation beyond whatever trace/parity scaffolding is needed;
- no AI/playbot.

This milestone proves the API boundary and the parity workflow before broader
feature porting starts.

## 14. Port Order: Stage 8 Onward

1. Stage 8: create the C++ GDExtension skeleton, build scripts, minimal Godot
   binding, and a headless smoke test. No gameplay port. The only exposed API
   is `get_core_version()`, `get_core_status()`, `echo_text(text)`,
   `stable_hash_text(text)`, and `add_integers(a, b)`.
2. Stage 9: port the smallest plain 2D data model and deterministic reducer
   surface needed to match `gameplay_plain_2d_short` on required trace fields.
3. Stage 10: complete canonical snapshot and `state_hash` parity for
   `gameplay_plain_2d_short` before broadening plain 2D coverage.
4. Stage 11: broaden plain bounded 2D trace parity with small Python golden
   traces for rotation, hard-drop lock, and line clear. Keep Godot APIs
   parity-only.
5. Stage 12: connect a narrow live plain bounded 2D Godot shell to the native
   core. Godot sends commands and renders C++ snapshots only.
6. Stage 13: polish the existing live plain bounded 2D slice into a minimally
   usable first playable loop. Keep Godot as input/HUD/render shell only.
7. Stage 14: plan the plain bounded 3D/4D native parity path. No 3D/4D code.
8. Stage 15: add native plain-ND trace contract scaffolding and a minimal ND
   data model beside the accepted 2D core, with parity exports for
   `gameplay_plain_3d_short` and `gameplay_plain_4d_short`.
9. Stage 16: document the next explicit ND trace coverage expansion in
   `docs/plans/plain_nd_coverage_expansion_plan.md`, including rotation,
   plane-clear/scoring, and spawn-blocked game-over cases.
10. Stage 17: add the explicit Python-oracle plain-ND golden traces selected
   by Stage 16 while keeping C++ parity scoped to implemented cases.
11. Stage 18: implement native ND rotation parity only for the explicit 3D/4D
   rotation golden traces.
12. Stage 19: implement native plane clear/scoring parity for the explicit
   plain-ND clear traces.
13. Stage 20: implement native spawn-blocked game-over parity and command
   rejection for the explicit plain-ND game-over traces.
14. Later: prototype live Godot 3D/4D shell only after native plain-ND trace
   parity is stable.
15. Later: plan topology transport and Topology Lab launch semantics.
16. Later: port locked-cell endgame particle simulation.
17. Later: retire Python as semantic oracle only after trace parity,
   product acceptance, and authority-doc updates explicitly allow it.

Stages may be split smaller if a parity gate is too broad.

## 15. Trace Parity Gates

Every semantic stage must pass deterministic trace parity before becoming
trusted:

- topology probe movement and transport traces;
- gameplay traces for 2D, 3D, and 4D;
- launch parity traces from Topology Lab;
- endgame particle traces;
- config snapshot compatibility where settings affect semantics.

Parity failures must stop the port stage. They should be diagnosed against the
Python oracle rather than accepted as new behavior.

## 16. Config Authority

Config authority remains in `config/` and the documented RDS/plans/governance
files. `migration/exported_bundle/` is generated and disposable.
`godot/Tet4D.Godot/assets/tet4d_bundle/` is a copied runtime input for the
Godot spike, not a source of truth.

The native core should consume a normalized config payload through a controlled
API. It must not make Godot scene defaults, inspector values, or extension
build constants the semantic config authority.

## 17. Console/Steam Implications

Steam-oriented desktop packaging is compatible with Godot plus a native core if
the extension build and export process are kept reproducible. Console viability
is one reason to prefer C++ GDExtension over a Python runtime bridge and to be
cautious about choosing C# as the core language.

Before committing to console work, the project should validate:

- Godot export templates and native extension packaging;
- platform-specific extension build requirements;
- save/config path behavior;
- input abstraction;
- crash/log handling for native code;
- any licensing or middleware implications.

The Stage 7 decision does not start console implementation.

## 18. Risks And Mitigations

- Risk: C++ setup cost slows migration. Mitigation: Stage 8 is skeleton-only
  and must prove build/test/export mechanics before gameplay porting.
- Risk: semantic drift from Python. Mitigation: trace parity gates block every
  port stage.
- Risk: GDScript scene code becomes gameplay authority. Mitigation: keep a
  narrow API and document GDScript as shell-only.
- Risk: config authority splits between Godot and repo config. Mitigation:
  consume generated/normalized payloads and keep config authority in `config/`.
- Risk: manual visual acceptance finds Stage 6b issues. Mitigation: Godot is
  accepted conditionally; implementation waits until manual replay acceptance
  is complete.
- Risk: C# appears faster but harms export goals. Mitigation: keep C# as an
  explicit alternative with decision criteria rather than an implicit default.
- Risk: port order chases impressive 4D/topology features too early.
  Mitigation: first playable milestone is plain bounded 2D only.

## 19. Acceptance Criteria Before Implementation

Implementation may start only when all of these are true:

- Stage 6/6b Godot replay has passed manual visual acceptance.
- This plan is checked in and referenced from the active handoff/backlog/RDS
  docs.
- No C++, C#, GDExtension, gameplay, topology, endgame, trace, or config
  implementation has been added as part of Stage 7.
- Python remains documented as oracle/reference.
- Godot remains documented as shell/UI/product surface.
- C++ GDExtension is documented as the recommended core path.
- C# is documented only as an alternative with explicit decision criteria.
- Stage 8 is limited to C++ GDExtension skeleton/build/test scaffolding.
- Governance and repo verification pass.

## 20. Stage 8 Skeleton

Stage 8 adds the minimum native integration proof:

- `native/tet4d_core/` owns the local extension source.
- `native/tet4d_core/src/core/` contains a plain C++ helper layer independent
  of Godot types.
- `native/tet4d_core/src/godot/` contains the `Tet4DCoreApi` GDExtension
  wrapper.
- `native/third_party/godot-cpp` is the official `godot-cpp` submodule. It is
  a dependency, not project-owned code.
- `godot/Tet4D.Godot/addons/tet4d_core/tet4d_core.gdextension` declares the
  extension for Godot.
- `godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd` is the GDScript
  bridge used by tests and future shell code.
- `godot/Tet4D.Godot/tests/test_tet4d_core_extension.gd` verifies Godot can
  instantiate and call the native wrapper.

Fresh-checkout build/test sequence:

```bash
git submodule update --init --recursive
./scripts/build_godot_tet4d_core.sh
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The native extension smoke test depends on the `godot-cpp` submodule and the
compiled local library under `godot/Tet4D.Godot/addons/tet4d_core/bin/`; it is
expected to fail on a fresh checkout until both are present.

Stage 8 still must not expose or implement gameplay stepping, piece movement,
rotation, drop, lock, topology transport, endgame simulation, trace parity
APIs, Python runtime calls, C#, Steam packaging, or console packaging.

## 21. Stage 9 Plain 2D Parity

Stage 9 introduces the first semantic native port, scoped to
`gameplay_plain_2d_short` only. The detailed contract lives in
`docs/plans/plain_2d_core_parity_contract.md`.

The C++ core now owns a minimal plain bounded 2D model under
`native/tet4d_core/src/core/`:

- `Board2D`;
- `PieceShape2D` / `ActivePiece2D`;
- `GameState2D`;
- `GameCommand2D`;
- `GameStepper2D`;
- deterministic JSON export for the built-in short trace.

The Godot-facing API remains parity/smoke-only:

- `run_builtin_plain_2d_smoke_case()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json()`.

Stage 9 does not expose live gameplay controls, does not make Godot playable,
does not call Python at runtime, and does not port topology, 3D, 4D, or
endgame behavior. Field parity against the Python golden trace is enforced by
`tools/migration/compare_cpp_gameplay_trace.py --case gameplay_plain_2d_short`.
Stage 10 completes the deferred `state_hash` work for this short trace.

## 22. Stage 10 Plain 2D Snapshot/Hash Parity

Stage 10 strengthens `gameplay_plain_2d_short` parity by adding
Python-compatible compact canonical JSON SHA-256 hashing in the native core and
by comparing per-frame and final `state_hash` values through
`tools/migration/compare_cpp_gameplay_trace.py`.

The Godot-facing API remains parity/smoke-only:

- `run_builtin_plain_2d_smoke_case()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json()`;
- `get_plain_2d_required_field_parity()`.

This stage still must not expose live `step_game`, move, rotate, drop, lock,
topology, endgame, C#, Python runtime, Steam, or console APIs. It also does not
add new golden traces; the sole C++ parity target remains
`gameplay_plain_2d_short`.

## 23. Stage 11 Broadened Plain 2D Parity

Stage 11 broadens the native plain bounded 2D parity foundation before any
live Godot gameplay controls are added. The Python oracle now exports these
small deterministic golden traces:

- `gameplay_plain_2d_short`;
- `gameplay_plain_2d_rotation_short`;
- `gameplay_plain_2d_hard_drop_lock`;
- `gameplay_plain_2d_line_clear_short`.

The native C++ core adds only the behavior needed to match those traces:
rotation in the existing 2D piece model, hard-drop lock/spawn parity, starting
locked cells for the line-clear case, and single-line clear scoring. The
comparison tool supports `--all-plain-2d` and checks required fields plus
per-frame/final `state_hash` values.

The Godot-facing API remains parity-only:

- `run_builtin_plain_2d_smoke_case()`;
- `list_plain_2d_parity_cases()`;
- `get_plain_2d_parity_status()`;
- `export_plain_2d_trace_json(case_id)`;
- `get_plain_2d_required_field_parity(case_id)`.

Stage 11 still must not expose live `step_game`, `move_left`, `move_right`,
`rotate`, `soft_drop`, `hard_drop`, topology, endgame, Python runtime, C#,
Steam, or console APIs.

## 24. Stage 12 Narrow Live Plain 2D Shell

Stage 12 adds the first live Godot milestone, scoped to plain bounded 2D only.
The native C++ core owns gameplay state transitions through `Plain2DSession`.
Godot owns only the shell: mode switching, input routing, HUD labels, and
rendering the snapshot JSON returned by the extension.

Allowed live commands:

- `move_left`;
- `move_right`;
- `rotate_cw`;
- `rotate_ccw`;
- `soft_drop`;
- `hard_drop`;
- `tick`;
- `reset`.

The Godot-facing live API is intentionally narrow:

- `live_2d_reset()`;
- `live_2d_apply_command(command)`;
- `live_2d_tick()`;
- `live_2d_snapshot_json()`;
- `live_2d_status()`;
- `live_2d_state_hash()`.

Godot must not perform collision checks, movement legality, rotation
resolution, lock, line clear, scoring, spawn, or state hashing. Replay mode
remains intact and continues to consume copied bundle traces.

Stage 12 still does not authorize 3D, 4D, topology, endgame, Python runtime
calls from Godot, C#, Steam, or console work. The live 2D shell is a proving
surface for the native API boundary, not a complete game product.

## 25. Stage 12b Live Plain 2D Playability Surface

Stage 12b keeps the Stage 12 boundary and improves only the plain bounded 2D
live surface. The native `Plain2DSession` owns a deterministic fixed sequence
using the Python classic tetromino definitions in classic order
`I, O, T, S, Z, J, L`. This is intentionally not the Python shuffled bag yet;
full seed/bag parity remains a later gameplay-parity task. The Stage 11 parity
fixtures keep their synthetic `TRACE_2D` initialization and must not consume
the live sequence path.

Godot still must not choose piece types or compute legality. It may display
the current C++ piece name, status, score, lines, state hash, last command,
mode-specific control hints, and render the returned live snapshot through the
existing replay visual/material role system.

The Stage 12 defect-closure acceptance bar also requires live game-over state
to stay native-owned. `Plain2DSession` snapshots expose `game_over`,
`game_over_reason`, `paused`, and `state_hash`; native gameplay commands after
`game_over` are rejected except reset/new game. Godot must stop automatic
gravity ticks once the native snapshot reports game-over, render `GAME OVER`
with the native reason, and continue to route reset back through C++.

The always-visible viewer hint strip is mode-specific. Live 2D shows:
`A/D or ←/→ Move · W/↑/X Rotate · Z Rotate CCW · S/↓ Soft Drop · Space Hard Drop · P Pause · R Reset · F Fit · Tab Replay · Q/Esc Quit`.
Replay shows:
`Space Play/Pause Replay · ←/→ Frame · ↑/↓ Case · 1/2/3 Family · F Fit · H Help · Tab Live 2D · Q/Esc Quit`.
Live cells must remain in the shared replay renderer/material system while
using Python-like colored tetromino cells, crisp borders, readable locked
cells, and a visible board grid/bounds rather than flat diagnostic blocks.

## 26. Stage 13 Plain 2D Gameplay Polish

Stage 13 keeps the Stage 12/12b semantic boundary and broadens only the
plain bounded 2D live shell quality. It does not port 3D, 4D, topology,
endgame, Python runtime, C#, Steam, or console behavior.

Godot may own live presentation timing and input repeat:

- gravity accumulator interval: `0.50s` by default;
- left/right hold repeat: shell detects held keys and sends repeated
  `move_left` / `move_right` command strings after a short initial delay;
- soft-drop hold repeat: shell detects held keys and sends repeated
  `soft_drop` command strings at a faster presentation cadence;
- rotation and hard drop remain press-triggered commands;
- paused live mode blocks gameplay command dispatch in Godot except
  pause/resume, reset/new game, mode switch, fit view, help, and quit.

C++ still owns every result of those commands: movement legality, rotation
legality, gravity tick outcome, lock, line clear, scoring, piece sequence,
game-over, and state hash. The live snapshot/status may expose additional
display-only fields such as `next_piece` and `last_command_status`, but Godot
must only display them.

Live/replay mode switching must preserve authority separation. Switching to
Replay pauses live ticking without destroying the live session. Switching back
to Live 2D shows the current native live session, or creates one if no live
session exists yet. Reset/New Game is the explicit action that creates a fresh
deterministic live session.

Ghost/drop preview remains deferred unless C++ computes and exposes it in a
future snapshot field. Godot must not compute hard-drop landing cells.

## 27. Stage 14 Plain ND Core Parity Plan

Stage 14 is documentation/governance only. The detailed plan lives in
`docs/plans/plain_nd_core_parity_plan.md`.

The first native parity targets are:

- `gameplay_plain_3d_short`;
- `gameplay_plain_4d_short`.

The plan chooses a conservative sidecar strategy: preserve the accepted plain
2D core and live `Plain2DSession`, then add a minimal runtime-dimensional
plain-ND parity path beside it. The first ND implementation stage should use
fixture-driven trace parity, lexicographically sorted coordinate arrays, and
the existing compact canonical JSON/SHA-256 parity machinery. It should not
template-refactor the accepted 2D live path.

The initial target traces cover only `move_axis`, `soft_drop`, and
`hard_drop` in plain bounded 3D/4D. Stage 18 adds rotation-only native parity
for the explicit 3D/4D rotation traces. Stage 19 adds clear/scoring parity
only for the explicit 3D/4D plane-clear traces. Spawn-blocked game-over,
topology, RNG/bag parity, and live Godot 3D/4D controls remain deferred until
their explicit parity stages.

Stage 14 forbids 3D/4D implementation, topology transport, endgame simulation,
live Godot 3D/4D gameplay, C#, Python runtime calls from Godot, and
Godot-side gameplay legality.

## 28. Stage 15 Native Plain ND Trace Scaffolding

Stage 15 implements the Stage 14 sidecar strategy without touching the
accepted live plain 2D session. The detailed contract lives in
`docs/plans/plain_nd_core_parity_contract.md`.

The native C++ core adds a separate runtime-dimensional plain-ND model:

- `CoordND`;
- `BoardShapeND`;
- `BoardND`;
- `PieceShapeND`;
- `ActivePieceND`;
- `GameStateND`;
- `GameCommandND`;
- `GameStepperND`.

The scaffold implements only the commands present in the target traces:
`move_axis`, `soft_drop`, and `hard_drop`. It exports Python-compatible trace
JSON and compact canonical SHA-256 hashes for:

- `gameplay_plain_3d_short`;
- `gameplay_plain_4d_short`.

The comparison tool supports `--all-plain-nd` beside the existing
`--all-plain-2d` gate. Godot receives parity/smoke methods only:

- `run_builtin_plain_nd_smoke_case()`;
- `list_plain_nd_parity_cases()`;
- `get_plain_nd_parity_status()`;
- `export_plain_nd_trace_json(case_id)`;
- `get_plain_nd_required_field_parity(case_id)`.

Stage 15 still forbids live Godot 3D/4D sessions or controls, topology
transport, ND rotation beyond explicit trace coverage, plane-clear
generalization beyond explicit trace coverage, endgame simulation, C#,
Python runtime calls from Godot, and Godot-side gameplay legality. Stage 18
uses that explicit-trace exception only for the 3D/4D rotation traces, and
Stage 19 uses it only for the 3D/4D plane-clear traces.

## 29. Stage 17 Plain ND Oracle Traces

Stage 17 adds Python-authoritative plain bounded ND traces for rotation,
plane-clear/scoring, and spawn-blocked game-over:

- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`
- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`
- `gameplay_plain_3d_spawn_blocked_game_over`
- `gameplay_plain_4d_spawn_blocked_game_over`

The rotation traces become native C++ parity targets in Stage 18. The
plane-clear/scoring traces become native C++ parity targets in Stage 19.
Spawn-blocked game-over traces remain oracle-only. Stage 17 does not add live
Godot 3D/4D, topology, endgame, C#, Python runtime calls from Godot, or
Godot-side gameplay legality.

## 30. Stage 18 Native Plain ND Rotation Parity

Stage 18 implements native C++ parity only for:

- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`

The C++ sidecar ND model now supports the trace `rotate` command with
`axis_a`, `axis_b`, and signed `delta` step fields. Rotation applies the
Python `rotate_blocks_nd` local-block semantics, preserves active-piece `pos`
for these fixtures, serializes `last_rotation_plane` and
`last_rotation_steps`, and compares frame/final `state_hash` through
`compare_cpp_gameplay_trace.py --all-plain-nd`.

Stage 18 does not add plane-clear/scoring parity, spawn-blocked game-over
parity, live Godot ND commands, topology transport, endgame simulation, C#,
Python runtime calls from Godot, or Godot-side gameplay legality. Accepted
live plain 2D remains preserved.

## 31. Stage 19 Native Plain ND Clear/Scoring Parity

Stage 19 implements native C++ parity only for:

- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`

The C++ sidecar ND model now supports the trace-only `lock_current_piece`
command and the Python-compatible clear subset exercised by those fixtures:
full gravity-axis levels clear, surviving locked cells compact toward larger
gravity-axis values, generic `lines` and `score` fields update after clear
resolution, and frame/final `state_hash` values match the Python goldens.

Stage 19 does not add spawn-blocked game-over parity, live Godot ND commands,
topology transport, endgame simulation, C#, Python runtime calls from Godot,
or Godot-side gameplay legality. Accepted live plain 2D remains preserved.
