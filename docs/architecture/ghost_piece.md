# Authoritative Ghost Piece

Status: Stage 54D-2 implementation contract

## Purpose and authority boundary

The live 2D, 3D, and 4D ghost displays the exact canonical cells that the
current native hard drop will occupy immediately before lock effects. Existing
deterministic gameplay authority continues to own the active pose, collision,
gravity, topology, landing, lock, clear, score, and game-over behavior. Godot
owns only visibility, styling, caching, and projection of the returned cells.
This observational surface does not transfer or establish authority.

## Authoritative landing provider

`GameState2D::hard_drop_destination()` and
`GameStateND::hard_drop_destination()` are pure queries over the current active
piece. They step a copied pose along the state's gravity axis through the same
`can_exist` legality owner used by gameplay. `hard_drop()` calls that same
query, commits its returned pose, and then performs the unchanged lock/spawn
sequence. There is no ghost-specific landing algorithm.

The live session and GDExtension methods are:

```text
live_2d_hard_drop_destination()
live_3d_hard_drop_destination()
live_4d_hard_drop_destination()
```

A successful result contains `ok=true`, `status=destination`, the dimension,
piece name, existing production `color_id`, and exact canonical destination
cells. Terminal or missing-active-piece state returns a checked unavailable
result with no cells. Transport/model validation failure also yields no visual
ghost; gameplay continues and stale geometry is discarded.

Queries do not mutate active or locked cells, score, clears, RNG, bag, queue,
game over, snapshots, hashes, replay identity, or trace identity. Native tests
compare exact queried cells with the cells subsequently locked by hard drop.

## Godot presentation

`GhostPieceModel` validates, sorts, and caches canonical board-positioned
cells. It does not inspect occupancy or calculate distance. The app adds those
cells to a presentation-only snapshot field, and `BoardPresentationModel`
routes them through the same coordinate mapper used by active and locked
cells. The renderer gives them the dedicated `cell.ghost` palette role, a
reduced fill, smaller body, and explicit outline. The active piece is rendered
after the ghost and therefore retains visual priority. An exact zero-distance
destination is hidden when all canonical ghost cells equal the active cells.

In live 4D, every `(x,y,z,w)` destination cell flows through the Stage 54C
signed-basis mapper. Basis turns retain canonical ghost data and only remap its
layer and local coordinates. Replay stays identity-based and never infers a
ghost from replay snapshots.

## Setting and lifecycle

`ghost.enabled` is a persistent Godot-shell presentation preference, defaults
to `true`, and is excluded from gameplay setup and deterministic identity.
Turning it off clears presentation data and suppresses native queries. Turning
it on invalidates the cache and queries the current live state.

The semantic query key is `(live mode, native state_hash)`. Native landing is
queried after live snapshot revisions caused by movement, rotation, gravity,
soft/hard drop, reset, new game, or setup changes. Stable frames, pause, camera
motion, HUD refresh, theme/accessibility changes, and Stage 54C basis turns do
not re-query semantics. Returned geometry receives its own signature so an
unchanged landing does not advance its geometry revision.

Game over, no active piece, Replay, Setup, and the main menu clear or hide the
ghost. Pause retains it. Provider failure invalidates stale data immediately.

## Deterministic exclusions and next boundary

Ghost cells and the preference are absent from native snapshots, state hashes,
replays, traces, queue state, and persistence schemas for gameplay. Stage
54D-3 Hold is separate deterministic state: it may cause an ordinary active
state revision later, but this stage introduces no held piece, swap action, or
Hold special case.
