# Godot Core-Port Plan

Role: migration architecture plan
Status: active plain 2D snapshot/hash parity integration
Last updated: 2026-05-20

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
4. Stage 11: connect Godot playable 2D shell to the native core behind a narrow
   API.
5. Stage 12: port 3D gameplay and parity tests.
6. Stage 13: port 4D gameplay and parity tests.
7. Stage 14: port topology transport and Topology Lab launch semantics.
8. Stage 15: port locked-cell endgame particle simulation.
9. Stage 16: retire Python as semantic oracle only after trace parity,
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
