# Designer panel-session verification — 2026-10-30

Base: `aa0b11d7`, plus the separate semantic-boundary clarification `54e0dcb1`.
Scope: phase 4 inside the existing Godot shell/Designer authority. No manifest,
profile schema/storage, gameplay, grid or accepted visual parameter changes.

## Implementation and review boundary

DesignerPanelSession owns detached host/frames, origin records, rectangles,
ordering and opening/closing. It captures all original indices before removing
siblings. Closing restores control modes, parents, visibility, sizing flags and
sibling order synchronously before queued frame destruction. Session revisions
reject old frame geometry edits and deferred constraints; HUD opening-geometry
capture checks the same revision. Public surface/constraint adapters replace
HUD access to the cockpit's private detached-host field and constraint method.
The session does not apply profiles, persist values or call Fit.

DesignerPanelFrame releases detached controls synchronously and clears its weak
references. An old queued frame's tree-exit handler cannot reset controls that
have already entered a new session. Existing layout constraints, panel minimums,
default placement and profile restoration semantics remain with their contracts.

## Relevant verification

- Pinned Godot `4.7.2.stable.official.ed1daf0bf`; isolated project/user data and
  reused debug native extension, as in prior focused records. No native changes.
- Final focused run: 8/8 scripts executed, zero failures and no script/parse
  errors: camera rig, cockpit coordinator, Designer panel session, helper state,
  live cockpit, locked shell layouts, presentation Designer and profile library.
- Separate six-style 3D/4D readability matrix: 1/1 passed. Nine relevant suites
  passed across those runs; the aggregate Godot runner was not executed.
- New public-API regression: out-of-order sibling detachment, synchronous order,
  sizing and visibility restoration, close/reopen before old frame destruction,
  old frame geometry callback rejection and detached mode survival after cleanup.
  An additional session-only run covers owner teardown while a session is active.
- Existing production Designer/profile integration and locked-layout cases pass.
  New session suite is registered in the normal runner.
- `./gov check`, semantic-boundary checker and aggregate governance validation
  passed. Existing non-blocking configuration/sanitation/utility advisories
  remain. Native tooling is advisory locally; this is not clang/device proof.

## Remote and remaining acceptance

Run `41065963311` passed baseline planning but blocked on the coordinator's
`invalidate` name. Commit `54e0dcb1` uses the guard's declared `display-only`
annotation on that UI scheduling method, without changing scanner rules. The
owning checker and aggregate governance pass locally. Remote CI for the new head
still needs completion. Full repository gate, complete Godot runner, fresh native
build, device/manual acceptance and new visual baseline equivalence are not
claimed. Shell conversion/F1 and laboratory capture/F4 remain future work.

Generated maintenance-document and handoff checks passed. Canonical text
formatting, pinned Ruff lint/format on the publication regression, scoped
secrets/string sanitation and diff whitespace passed. CURRENT_STATE remains
150 lines. This focused set does not replace the complete pre-push gate.
