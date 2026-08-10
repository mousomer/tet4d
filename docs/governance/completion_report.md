# Completion Report — Stage 54E-2d

Last updated: 2026-08-10

## Summary

Stage 54E-2d is COMPLETE / REVIEWED GREEN. Live 4D now has explicit, tested
presentation lifecycle boundaries: entry and restart restore the exact basis,
local orientation, framing, fit, and reflection defaults; Reset View is
presentation-only; the internal basis-only reset remains separately testable;
and setup, menu, replay, and mode transitions synchronously clear presentation
children and interpolation state. Public gameplay roll bindings are removed
without removing the reusable generic camera-rig roll capability. Persistence,
snapshot, replay, and deterministic identity remain presentation-state free.

All implementation acceptance criteria and external technical review criteria
are satisfied. Merge remains the publication step; integrated Stage 54F human
playability/visual acceptance is deliberately not claimed here.

## Files Changed

- `godot/Tet4D.Godot/scripts/`: lifecycle cleanup, camera reset, input-contract,
  InputMap, and HUD help reconciliation.
- `godot/Tet4D.Godot/tests/`: entry, reset, restart, teardown, re-entry,
  roll-removal, fit, preference-preservation, and persistence-exclusion tests.
- `docs/architecture/`, `docs/design/`, and `docs/rds/`: lifecycle ownership,
  presentation contracts, current controls, and authority boundaries.
- `docs/plans/`, `docs/BACKLOG.md`, `CURRENT_STATE.md`, and governance reports:
  Stage 54E-2d status, evidence, review boundary, and explicit deferrals.
- `godot/Tet4D.Godot/README.md`: current Live-4D control and persistence scope.

## Semantic Impact

Changed behavior:

- Every Live-4D entry begins with exact identity basis `B`, identity shared
  local orientation `L`, default framing, current-bounds fit, and the canonical
  renderer-only reflection convention.
- Restart resets native gameplay and all presentation state. Reset View resets
  presentation only. The internal basis-only seam changes `B` only.
- Leaving Live 4D for setup, menu, replay, or another live mode synchronously
  clears presentation roots, bounds, fit envelopes, and interpolation targets.
- Normal gameplay no longer registers or exposes roll actions.

Deliberately unchanged behavior:

- Native gameplay authority, movement legality, deterministic identity,
  snapshots, replay/trace formats, and persistence schemas are unchanged.
- Camera preferences such as sensitivity, inverted drag, and reduced motion
  survive presentation reset.
- Generic camera-rig roll remains available for future Explorer/free-inspection
  use; it is not a normal-gameplay action.
- GitHub Issues #69 and #70 remain deferred to Stage 54F.

## Authority Changes

None. Godot remains presentation/input authority and C++/native remains live
gameplay authority. No authority transfer or new authority establishment is
performed.

## Tests and Verification

Passed:

```bash
GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot ./scripts/verify_godot_4_7.sh
.venv/bin/python tools/governance/validate_project_contracts.py
.venv/bin/python tools/governance/generate_maintenance_docs.py --check
.venv/bin/python tools/governance/generate_config_reference.py --check
./scripts/check_keybinding_contract.sh
git diff --check
```

The pinned Godot gate passed all Godot tests and 59 shared topology transport
parity cases. Governance validation covered 114 routed paths. The keybinding
contract passed 103 tests and 50 subtests.

The repository-wide gate also passed:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Result: `verify: OK`.

[GitHub CI run 31343615624](https://github.com/mousomer/tet4d/actions/runs/31343615624)
passed the baseline contracts, documentation/governance, pinned Godot
4.7.1/native-parity lane, and required gate after implementation publication.
Packaging, general Python checks, deterministic/parity, standalone native,
platform-package, cross-layer, and release lanes were skipped by the resolver.

External technical review of final implementation HEAD
`d0640439c1ab73160a959698ebb2804d2dd56792` found no runtime, lifecycle,
persistence, RDS, authority, or test blocker and accepted Stage 54E-2d and the
aggregate Stage 54E-2 implementation series as reviewed green. A subsequent
status-only reconciliation commit series updates durable records before merge.

## Manual Checks

Real, non-headless Godot 4.7.1 window on macOS, using the pinned executable at
`/Applications/Godot.app/Contents/MacOS/Godot`, Metal 4.0 Forward+ on an Apple
M1 Pro:

- Standard 5×10×4×4 Live-4D launch rendered four coherent slices, active
  piece, Ghost, NEXT, exact-basis controls, and framing controls.
- Exact-basis input plus orbit/zoom changed the view; Reset View restored exact
  identity basis and fitted framing without restarting gameplay.
- After another basis/framing change, Restart restored gameplay and all
  presentation defaults.
- Live 4D → Live 3D → Live 4D cleared the prior 4D presentation and re-entered
  with fresh identity basis/local orientation/framing.
- W=1 with Embedded 3D launched as one coherent slice with active piece,
  Ghost, NEXT, and stable fit.
- Wide 8×16×5×8 launched with eight coherent fitted slices.
- With a non-identity exact basis active, the Top presentation camera preset
  changed `L`/framing coherently, retained `B`, and kept all slices fitted.
- Visible help exposed piece rotation, exact 4D basis, framing, Reset View, and
  Restart semantics without public gameplay-roll controls.

## Known Warnings

No new warnings were introduced. The pinned Godot run emitted the existing
macOS certificate and ObjectDB shutdown advisories plus intentional negative-
path settings/native-input messages; the gate completed successfully.

## Unresolved Limitations

- Merge/publication of reviewed-green PR #72 remains pending at this report
  revision.
- Board spacing/wireframe visual polish tracked by GitHub Issues #69 and #70
  remains explicitly deferred to Stage 54F.
- No Stage 54E-3/4/5 work is included. Stage 54E-3 is the next eligible Stage
  54E implementation slice after merge.

## Diffstat

Implementation handoff diffstat before reviewed-green status reconciliation:
26 files changed, 681 insertions, 256 deletions.

## Commit SHA

Implementation commit tested and published:
`a7c811b9f910d92ced5d5aa73c41544126f10d37`. Final implementation-review HEAD:
`d0640439c1ab73160a959698ebb2804d2dd56792`. The reviewed-green status
reconciliation adds documentation-only commits before merge.

## PR URL

[PR #72](https://github.com/mousomer/tet4d/pull/72), targeting `master`.
State at this report revision: reviewed green; merge pending.

## Worktree State

Branch: `codex/54e-2d-lifecycle-authority-reconciliation`.
Base agreement: started from required `master` commit
`021db14664e118e649a2171296ded7bf6abeb0d4`. The implementation handoff reported
a clean local/remote worktree before the connector-applied status-only
reconciliation commits.
