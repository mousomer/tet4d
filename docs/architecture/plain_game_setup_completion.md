# Plain Game Setup Completion

Status: Stage 50 complete; implementation, parity, persistence, and manual GUI
acceptance verified on `codex/configurable-plain-boards`.

This document extends the Stage 49 board-configuration boundary documented in
`configurable_plain_boards_and_4d_layout.md`. Python remains the gameplay and
replay semantic oracle. Native C++ remains the owner of the accepted bounded
live-session transitions. Godot remains the product shell and owns setup
presentation, validation feedback, persistence, input routing, and timing.

## Product boundary

Stage 50 completes only ordinary bounded 2D, 3D, and 4D game setup. The
canonical setup fields are:

| Field | Canonical representation | Semantic role |
| --- | --- | --- |
| mode | `live_2d`, `live_3d`, or `live_4d` | Selects dimension/session family |
| board preset | stable preset ID | Shell selection identity |
| board shape | integer axis-size array | Native board geometry |
| piece set | stable piece-set ID | Native bag/catalog identity |
| random mode | `fixed_seed` or `true_random` | Session seed policy |
| seed | decimal integer `0..999999999` | Configured fixed seed |
| initial speed | integer `1..10` | Initial Godot gravity cadence |

Shell theme, fullscreen/window behavior, onboarding, and other presentation
preferences are not game setup. Topology, bots, kicks, challenge layers,
progression controls, random-cell generator controls, endgame/explosion,
audio, keybindings, analytics, and packaging remain excluded.

## Audit answers

1. **Python ordinary setup fields.** `GameConfig`/`GameConfigND` contain board
   dimensions, `piece_set`/`piece_set_id`, `rng_mode`, `rng_seed`, and
   `speed_level`. The pygame setup layer also carries legacy selection indices.
2. **Canonical IDs.** Piece-set IDs from `pieces2d.py`/`pieces_nd.py`,
   `fixed_seed`/`true_random`, bounded topology identity, and the Stage 49 board
   preset IDs are canonical strings.
3. **Legacy mirrors.** `piece_set_index`, `random_mode_index`,
   `topology_mode`, `topology_advanced`, topology-profile indices, bot indices,
   and kick indices are pygame/menu compatibility fields. Stage 50 neither
   emits nor semantically depends on them.
4. **Semantic gameplay identity.** Mode/dimension, board shape, piece-set ID,
   effective seed and RNG progress, and current gameplay state affect future
   transitions. Initial speed selects shell-driven gravity cadence but does not
   alter an individual native command transition.
5. **Presentation-only settings.** Theme, viewport/window choices,
   onboarding, camera, HUD layout, and display preferences are shell-owned.
6. **Deterministic replay inputs.** Board shape, piece-set ID, effective seed,
   action stream, and (where time is modeled) initial gravity cadence are
   required. Random-mode provenance is diagnostic identity; true-random replay
   becomes deterministic once its effective seed is captured.
7. **Already native.** Stage 49 board-shape configuration and plain
   move/rotate/drop/lock/clear/game-over transitions are native. Live snapshots
   already expose board shape and current/next piece names.
8. **Python-only before Stage 50.** Canonical RNG policy, shuffled bags,
   explicit seed, initial speed, embedded piece-set selection, random-cell
   generation, debug rectangles, and the additional 4D 6/7/8-cell catalogs.
9. **Native piece sets before Stage 50.** Classic 2D and True 3D are complete.
   The live 4D sequence uses five trace-oriented shapes and is not the complete
   Python `standard_4d_5` catalog.
10. **Python-only piece sets.** Random Cells and debug rectangles in every
    dimension; Embedded 2D/3D; complete True 4D 5/6/7/8-cell catalogs.
11. **Safe Stage 50 exposure.** Stage 50 will implement and expose Classic
    (`classic`) in 2D; True 3D (`native_3d`) and Embedded 2D (`embedded_2d`) in
    3D; True 4D 5-cell (`standard_4d_5`), Embedded 3D (`embedded_3d`), and
    Embedded 2D (`embedded_2d`) in 4D. All use finite production catalogs,
    fit every Stage 49 preset, and can be parity-backed. Random-cell, debug,
    and 4D 6/7/8-cell sets remain deferred.
12. **Bag identity.** Python trace settings already include `piece_set`; live
    snapshots expose current/next piece. Stage 50 adds canonical piece-set and
    RNG identity plus remaining-bag/RNG progress to complete native hashing.
13. **RNG mode.** Python canonical IDs are `fixed_seed` and `true_random`.
14. **Seed.** Python validates a non-boolean integer in `0..999999999`.
15. **Current restart.** Native reset restores a fixed cyclic sequence at
    index zero; it has no seed or RNG state. Python UI reconstruction seeds
    fixed runs and asks `random.Random()` for true-random runs.
16. **Stage 50 restart.** Native reset reconstructs the immutable initial
    setup with the same effective seed, resets bag/RNG progress, and therefore
    reproduces the initial sequence. Only New Random Game requests new entropy.
17. **Initial speed.** Python stores numeric `speed_level` in the validated
    config, range `1..10`.
18. **Speed semantics.** Native transitions are command-driven. Godot owns
    elapsed-time scheduling and uses the Python-authoritative dimension speed
    curve. Speed is nevertheless setup identity and is exposed in snapshots.
    Stage 50 does not change scoring or progression rules.
19. **Replay fields.** Replay config serialization already carries board
    dimensions, piece set, `rng_mode`, `rng_seed`, and `speed_level`; replay
    scripts also have a top-level seed. Gameplay migration traces carry
    `axis_sizes`, `piece_set`, and top-level `seed`, but need the narrow Stage
    50 settings extension for random mode and speed.
20. **Hashes.** Python gameplay trace `settings_digest` includes axis sizes and
    piece set, while final trace hashes include frames/final state. Existing
    native live hashes include board shape, visible state, and a sequence
    index, but not piece-set/seed/speed identity. Stage 50 extends native hashes
    without changing Python gameplay rules or existing golden-trace hashes.
21. **Godot persistence.** Per mode: board preset ID, piece-set ID, random-mode
    ID, stored fixed seed, and initial speed. Active/effective seed and mutable
    session state are not persisted.
22. **Malformed values.** Reject unknown mode/preset/piece-set/random-mode IDs,
    invalid preset/piece-set combinations, non-integer/bool/out-of-range seeds,
    non-integer/bool/out-of-range speed, malformed board shapes, missing fixed
    seeds, and dimension mismatches. Persistence falls back independently per
    mode; explicit native construction remains strict.
23. **Explicit exclusions.** Topology and explorer settings, bots, kicks,
    challenge layers, auto-speedup/lines-per-level editors, random-cell
    parameters, debug controls, endgame/explosion, analytics, keybindings,
    audio, unrestricted dimensions, replay-viewer redesign, and packaging.
24. **Readable aliases.** Stage 49 schema version 1 (`last_selected` values as
    preset-ID strings), and the canonical Python random-mode IDs are readable.
    Legacy UI indices may be normalized by the existing Python settings
    sanitizer, but the Godot Stage 50 store never emits indices or labels.
25. **Parity matrix.** Preserve all existing plain trace cases and add:
    standard 2D Classic/seed 1337/speed 1; alternate 2D/different seed;
    alternate 3D Embedded 2D; standard 4D Embedded 3D; standard 4D Embedded
    2D; fixed-seed repeat/restart and different-seed divergence checks;
    true-random effective-seed checks; invalid ID/mode/seed/speed checks; and
    movement/rotation/drop/lock coverage through representative configured
    cases. The matrix is bounded rather than a Cartesian product.

## Compatibility matrix

Every production piece set below is valid for every Stage 49 preset in its
mode. The setup model still validates the combined mode/preset/piece-set tuple
so future catalogs can narrow compatibility without changing the API.

| Mode | Presets | Exposed piece sets | Default |
| --- | --- | --- | --- |
| Live 2D | Compact, Standard, Large | `classic` | `classic` |
| Live 3D | Compact, Standard, Large | `native_3d`, `embedded_2d` | `native_3d` |
| Live 4D | Compact, Standard, Wide W | `standard_4d_5`, `embedded_3d`, `embedded_2d` | `standard_4d_5` |

## Canonical construction and lifecycle

Godot validates and freezes one setup dictionary before construction:

```json
{
  "schema_version": 2,
  "mode": "live_4d",
  "board_preset_id": "wide_w",
  "board_shape": [8, 16, 5, 8],
  "piece_set_id": "standard_4d_5",
  "random_mode": "fixed_seed",
  "seed": 1337,
  "initial_speed_level": 1
}
```

Native construction validates the semantic fields strictly and captures an
effective seed. Fixed-seed sessions use the configured seed. True-random
construction generates exactly one effective seed. Restart reuses that seed;
New Random Game constructs a new session and requests a new effective seed.
Godot never selects or repairs pieces.

The narrow semantic-boundary suppressions on the Godot setup model, store,
panel, and gravity scheduler are adapter-routing declarations only. They route
through the canonical setup spec or the bundled Python-authoritative tuning
curve; they do not grant Godot gameplay-rule authority.

The persistence document advances to schema version 2 and stores a validated
entry per mode. Schema version 1 preset strings migrate independently to
version 2 defaults. Malformed/future documents fail safely without touching
`user://shell_settings.json`.

## Completion evidence

Stage 50 manual GUI acceptance covered readable and unclipped 2D, 3D, and 4D
setup screens; keyboard and mouse launch paths; fixed-seed restart; alternate
boards, pieces, seeds, and speeds; 2D/3D movement, rotation, and hard drop; and
the Wide W 4D matrix with eight cards, active-layer emphasis, Q/E movement,
fourth-axis rotation, hard drop, restart, and correct HUD identity.

The 3D true-random acceptance run persisted Standard `6 × 10 × 6`, Embedded 2D,
true-random, and speed 4 across application restart. Its first effective seed
was `70273464`; the visible `New Random Game` mouse action produced
`892089889` while retaining every non-seed setup field. Backspace restart was
also verified to retain the current effective seed and initial sequence.

Manual inspection found the live Restart/New Random/Change Setup row clipped by
the original 80-pixel summary height. The completion pass raises the summary
contract to 132 pixels, keeps the status badge elastic, and protects all
visible live actions with supported-viewport layout assertions. The Plain
theme keeps the status and action choices readable. Existing Godot RID/ObjectDB
exit warnings remain non-blocking because the suite exits successfully.

## Authority and deferrals

No new authority transfer is introduced. Python piece catalogs, bag semantics,
RNG behavior, speed curves, and gameplay rules remain the oracle. Native
authority stays limited to the already accepted bounded live-session owner,
now constructed from canonical setup identity. Godot gains no legality,
topology, piece-generation, or scoring logic.

Random-shape generation, debug bags, True 4D 6/7/8-cell production exposure,
topology setup, bots, kicks, challenge/progression editors, and all later Stage
51/52 work remain deferred.
