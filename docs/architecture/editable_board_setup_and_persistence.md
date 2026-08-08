# Editable Board Setup and Persistence

Status: Stage 54B-2 complete and verified

## Purpose and authority

Stage 54B-2 makes the established `AE-0054` bounded-board admission contract
usable in the Godot product shell. It adds no new gameplay, topology, piece,
spawn, or construction authority. The generated board-extent binding provides
the displayed axis ranges and defaults; the native `validate_live_board_setup`
boundary remains the sole authority for board-shape, topology-profile,
piece-set, canonical-spawn, volume, and structured admissibility decisions.

Godot owns only the setup draft, control presentation, code/path error display,
persistence source adapter, focus order, and launch gating. It must not infer
an extent minimum from a piece set or repair an invalid tuple.

## Setup state

`GameSetupModel` owns a separate draft and last-valid entry for each of
`live_2d`, `live_3d`, and `live_4d`.

- A draft retains what the person typed, including malformed axis text.
- Every material axis, preset, or piece-set edit sends a complete setup request
  to native validation. Final Start revalidates that exact draft.
- Only a successful result replaces that mode's last-valid entry.
- Invalid drafts remain visible, make Start unavailable, and never become the
  next session or persisted state.
- Errors are shown as stable `code @ path` identities. Native prose messages
  remain diagnostic metadata, not product-shell behavior.

The active axes are X/Y in 2D, X/Y/Z in 3D, and X/Y/Z/W in 4D. Each axis has
direct integer entry, decrement/increment controls, and a generated inclusive
minimum/maximum label. Controls do not clamp typed values. A malformed typed
value is deliberately passed through the strict validation representation so
that `invalid_field_type` remains observable.

Presets are shortcuts: selecting one fills the concrete axis values. Preset
identity is derived from exact equality with a curated preset shape; a changed
shape is shown as Custom/no-preset and serializes with an empty preset ID, not
as a semantic `custom` preset. No preset selection changes a piece set, and no
piece-set selection repairs a board shape. This preserves tuple-level
admission, including W=1: `embedded_3d` and `embedded_2d` may validate at
W=1 while `standard_4d_5` rejects through `spawn_not_viable`.

## Reset, launch, and lifecycle

`Reset Sizes` resets only the current mode's shape to the generated canonical
default. `Reset Setup` resets the complete current mode entry (shape, piece
set, random mode, seed, and speed). Both actions are explicit and revalidate
their result.

Start emits only the currently validated setup. The existing app freezes that
dictionary after checked native configuration; active boards are never resized
by later setup editing. Restart reconstructs that frozen setup, while Change
Setup leaves the session and starts a future setup flow.

## Persistence schema 3

`user://game_setup.json` is separate from shell preferences. Schema 3 writes
only model-produced last-valid entries, one per mode:

```json
{
  "schema_version": 3,
  "last_selected": {
    "live_4d": {
      "board_preset_id": "",
      "board_shape": [5, 10, 4, 1],
      "piece_set_id": "embedded_3d",
      "random_mode": "fixed_seed",
      "seed": 1337,
      "initial_speed_level": 1
    }
  }
}
```

Schemas 1 and 2 remain readable source formats. Their preset IDs migrate to
the corresponding concrete shape before the candidate is given to the model.
Schema 3 reads its stored shape directly. Missing, malformed, future, or
native-invalid entries recover per mode to the generated canonical default;
recovery is performed before any session construction and never mutates an
active session. Persistence does not store an invalid draft, an effective
true-random seed, bag/RNG progress, cells, score, pause, or game-over state.

## Scope boundary

| Owned here | Explicitly not owned here |
| --- | --- |
| Godot editable controls, drafts, last-valid persistence, native error presentation, and launch gating | Topology seam rules, Strip/Möbius behavior, piece catalogues, spawn rules, movement, rotation, collision, gravity, scoring, replay/trace/hash semantics, or camera/renderer redesign |

Stage 55A may add topology-specific extent rules through `AE-0054`; it must
not reintroduce Godot-owned minima or bypass tuple-level validation.

## Completion evidence

Focused model and panel tests cover 2D/3D/4D active-axis counts, preset-to-
shape population, Custom derivation, strict malformed entry, W=1 piece-set
discrimination, reset separation, frozen restart state, schema 1/2 migration,
schema 3 round trips, and stale-invalid recovery. Godot-rendered visual review
covered 2D, 3D, and 4D setup surfaces plus the disabled 4D W=1 True-4D error
state. The completion gate includes generated-contract freshness, native build
and tests, Godot 4.7 verification, governance/documentation checks, sanitation,
and the full repository verification command.
