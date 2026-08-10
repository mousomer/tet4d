# Completion Report — Stage 54E-2d

Last updated: 2026-08-10

## Summary

Stage 54E-2d is implemented and review pending. Live 4D now has explicit,
tested presentation lifecycle boundaries: entry and restart restore the exact
basis, local orientation, framing, fit, and reflection defaults; Reset View is
presentation-only; the internal basis-only reset remains separately testable;
and setup, menu, replay, and mode transitions synchronously clear presentation
children and interpolation state. Public gameplay roll bindings are removed
without removing the reusable generic camera-rig roll capability. Persistence,
snapshot, replay, and deterministic identity remain presentation-state free.

All implementation acceptance criteria are satisfied. Human review and merge
are deliberately not claimed.

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

## Manual Checks

Real, non-headless Godot 4.7.1 window on macOS, using the pinned executable at
`/Applications/Godot.app/Contents/MacOS/Godot`:

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
- Visible help exposed piece rotation, exact 4D basis, framing, Reset View, and
  Restart semantics without public gameplay-roll controls.

## Known Warnings

No new warnings were introduced. The pinned Godot run emitted the existing
macOS certificate and ObjectDB shutdown advisories plus intentional negative-
path settings/native-input messages; the gate completed successfully.

## Unresolved Limitations

- Human review and visual acceptance are pending on the draft PR.
- Stage 54E-2 remains aggregate-open until Stage 54E-2d is reviewed.
- Board spacing/wireframe visual polish tracked by GitHub Issues #69 and #70
  remains explicitly deferred to Stage 54F.
- No Stage 54E-3/4/5 work is included.

## Diffstat

Pre-publication diffstat: 26 files changed, 664 insertions, 256 deletions.

## Commit SHA

Pending intentional commit after the full repository gate.

## PR URL

Pending draft PR publication against `master`.

## Worktree State

Branch: `codex/54e-2d-lifecycle-authority-reconciliation`.
Base agreement: started from required `master` commit
`021db14664e118e649a2171296ded7bf6abeb0d4`. The worktree is intentionally
dirty until the implementation is committed and published.
