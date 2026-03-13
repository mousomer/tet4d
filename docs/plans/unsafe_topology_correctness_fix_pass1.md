# Unsafe Topology Correctness Fix Pass 1

Status date: 2026-03-12
Status sources of truth:
- [`docs/plans/topology_playground_reality_audit.md`](topology_playground_reality_audit.md)
- [`docs/plans/unsafe_topology_correctness_audit.md`](unsafe_topology_correctness_audit.md)
- supporting context only: [`docs/plans/topology_explorer_functional_audit.md`](topology_explorer_functional_audit.md)

## Scope

This pass stays within the correctness-fix stage for unsafe / quotient topology behavior.
It does not reopen completed playground migration stages, and it does not broaden into general performance work or UI redesign.

## A. Fixed topology cases

### Sandbox rigid transport was stricter than gameplay

Wrong subsystem(s):
- `src/tet4d/engine/runtime/topology_playground_sandbox.py`
- gameplay parity reference: `src/tet4d/engine/gameplay/explorer_piece_transport.py`

What was wrong:
- Sandbox only accepted same-delta translation across seam crossings.
- Gameplay already accepted both `plain_translation` and `rigid_transform` and blocked only `cellwise_deformation`.
- Unsafe presets such as `Mobius`, `Projective`, `Sphere`, and `swap_xw_4d` therefore looked broken in sandbox even when gameplay would accept the move.

What changed:
- Sandbox now classifies transported sandbox cells with the same `classify_explorer_piece_move(...)` logic used by gameplay.
- Successful rigid seam moves now update both sandbox origin and local blocks through the transported frame transform instead of rejecting anything that is not a pure translation.
- True `cellwise_deformation` still fails explicitly.

### Invalid unsafe preset / dimension pairs now surface explicitly

Wrong subsystem(s):
- `src/tet4d/engine/topology_explorer/glue_validate.py`
- `src/tet4d/engine/runtime/topology_playground_launch.py`
- sandbox movement path in `src/tet4d/engine/runtime/topology_playground_sandbox.py`

What was wrong:
- Non-bijective sphere-like / cross-axis board sizes failed with a generic bijection error or downstream mismatch.
- Runtime launch did not validate the explorer profile against the current board dimensions before building gameplay config.

What changed:
- Validation now reports `unsupported for current board dimensions ...` and includes the offending glue id, boundary pair, extents, and permutation.
- Runtime play-launch config now validates the canonical explorer profile against the current board dimensions before handing gameplay config to the frontend.
- Sandbox move attempts now surface the same explicit invalid-dimension message instead of crashing or failing opaquely.

### Invalid explorer topology now stays canonical instead of being replaced or dropped

Wrong subsystem(s):
- `src/tet4d/ui/pygame/topology_lab/app.py`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`

What was wrong:
- Explorer / launcher entry could replace an invalid stored topology with a fallback preset.
- Manual seam apply rejected dimension-invalid glue up front, so the draft topology never entered an explicit invalid state.
- Those behaviors violated the one-topology contract by swapping or dropping topology state instead of surfacing the invalidity.

What changed:
- Explorer and launcher entry now keep the current stored explorer topology and report that it is invalid for the active board dimensions.
- Manual seam apply now validates only topology structure up front; board-bijection errors stay attached to the draft topology and surface through `scene_preview_error`.
- Explorer status text now reports the invalid topology directly instead of generic `updated` / play-settings messages, and invalid preview states block export/experiment actions explicitly.

### Explorer unsafe traversal and glue mapping are now pinned with regressions

What changed:
- Added focused regressions that prove `Projective` probe traversal remains available as a cellwise explorer path in `2D`, `3D`, and `4D`.
- Added safe baseline regressions for bounded and wrap-all / torus-like cases so the unsafe fixes do not regress already-working safe topology connectivity.
- Added cross-axis glue roundtrip regressions for `swap_xz_3d` and `swap_xw_4d` so seam axis-order/sign handling stays pinned.

## B. Explorer unsafe-topology policy

Explorer / probe is a cellwise topology surface.
Gameplay and sandbox are rigid-piece transport surfaces.

That means:
- unsafe topologies may be explorable even when some multi-cell piece orientations are not rigid-piece playable
- preview / probe saying a single-cell seam crossing exists is not a promise that every rigid piece can follow it
- the correctness rule is now explicit in tests: explorer keeps the cellwise graph, while sandbox/gameplay block only true `cellwise_deformation`

This pass does not try to make every unsafe topology rigid-piece playable.

## C. Sandbox alignment

Shared rigid transport rule now in force:
- allow `plain_translation`
- allow `rigid_transform`
- block `cellwise_deformation`

Implementation note:
- Sandbox now reuses the gameplay transport classifier rather than its old translation-only delta check.

What still differs:
- Explorer / probe remains intentionally cellwise.
- Gameplay still has piece collisions, lock/gravity rules, and ordinary runtime constraints that the sandbox does not model.
- Those differences now come from transport policy and gameplay rules, not from separate topology definitions.

## D. Invalid topology handling

Explicitly surfaced in this pass:
- non-bijective sphere-like preset / board-size pairings such as `(5, 4)`, `(4, 5, 6)`, and `(4, 5, 6, 7)`
- any other gluing whose tangent extents are not bijective under the configured permutation for the current board dimensions

Current behavior:
- preview compile fails explicitly with `unsupported for current board dimensions ...` while keeping the current canonical explorer topology intact
- probe remains unavailable for those dimensions rather than pretending partial connectivity exists
- sandbox move attempts surface the same invalid message
- runtime play launch rejects the state before gameplay starts
- explorer / launcher entry keep the same invalid draft topology instead of swapping in a fallback preset
- manual seam apply keeps structurally valid but dimension-invalid glue in the draft topology and marks the explorer invalid rather than discarding the seam

## E. Remaining issues

Still not fixed in this pass:
- The product still does not expose a first-class user-facing playability signal that distinguishes cellwise-valid unsafe traversal from rigid-piece-safe playability.
- This pass covers explicit regressions for safe baselines, `Projective`, cross-axis roundtrips, invalid `Sphere`, and rigid-transform parity cases, but it does not claim exhaustive coverage for every unsafe family / every piece orientation.
- Legacy compatibility-only playground paths were intentionally not reworked here.

## Focused regression coverage added

- `tests/unit/engine/test_topology_lab_app.py`
- `tests/unit/engine/test_topology_lab_menu.py`
- `tests/unit/engine/test_topology_explorer.py`
- `tests/unit/engine/test_topology_playground_sandbox.py`
- `tests/unit/engine/test_unsafe_topology_correctness.py`

Focused verification run:
- `python -m ruff check src/tet4d/engine/topology_explorer/glue_validate.py src/tet4d/engine/topology_explorer/__init__.py src/tet4d/ui/pygame/topology_lab/controls_panel.py src/tet4d/ui/pygame/topology_lab/app.py tests/unit/engine/test_topology_lab_app.py tests/unit/engine/test_topology_lab_menu.py tests/unit/engine/test_topology_explorer.py`
- `python -m pytest -q tests/unit/engine/test_topology_lab_app.py tests/unit/engine/test_topology_lab_menu.py tests/unit/engine/test_topology_explorer.py tests/unit/engine/test_topology_playground_sandbox.py tests/unit/engine/test_unsafe_topology_correctness.py tests/unit/engine/test_topology_explorer_preview.py tests/unit/engine/test_topology_playground_launch.py`