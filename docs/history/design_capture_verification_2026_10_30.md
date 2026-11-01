# Design capture and final orchestration review — 2026-10-30

Base: `2049ff26`, plan `cf8a9517`, separate helper completion repair `cc9aeed1` and inactive-owner repair
`5f139ef2`.
Route: Godot product shell; FEATURE exploration with explicit structural owner
review. `./gov check`, task explanation and `./gov doctor` resolved the existing
manifest authorities, source binding and Python 3.14.8 interpreter. No manifest,
native semantics, visual scale, grid, profile schema or capture-schema changes.

## Implementation

DesignCaptureOperation owns one request's lifetime, frozen comparison identity,
settling/draw wait, validation, pair restoration and result. The panel owns UI
busy state and cancels on close, teardown, scenario reset, assignment, shown-arm
change and external profile/candidate actions. Revision checks prevent an old
completion from clearing a new request's controls or restoring its old arm.

The app supplies readiness from an all-mode profile-application revision, its
profile guard, pending fit, camera snapshot
and the HUD's public cockpit/viewport observation. A 3D equal-profile round trip
regression verifies that each application invalidates the previous draw token. It includes the actual applied
complete-profile hash; each requested frozen arm must match that hash before
storage. The frame budget is the project.godot key documented in the owning
laboratory contract. Two equal ready observations must be followed by a later
drawn frame retaining the same token. A headless/no-draw timeout is diagnostic.
The operation stores frozen validated provenance, reports partial pair failures
and restores only while it still owns the unchanged comparison and profile.
Storage remains the existing replacement-safe schema-1 capture owner.

## Relevant evidence

- Pinned Godot 4.7.2; isolated project/user data. Fresh native extension build
  completed using the pinned godot-cpp submodule and governed interpreter.
- Focused operation, laboratory storage and runtime suites passed: 3/3, with
  no script/parse errors. The production runtime readiness case now uses live
  4D with enlarged UI and checks non-style fingerprint preservation.
- Expanded helper/cockpit/coordinator/resize/capture/runtime run: 6/6 passed.
- Additional operation-only run passed restoration failure, zero budget and
  actual panel teardown cases, alongside cancellation, close/reopen, duplicate
  rejection, timeouts, profile drift, store failure and pair partial failure.
- Replacing only the panel with the preceding one-draw implementation fails
  production capture settling and close/reopen regressions. The separate helper
  repeated-observation case fails on the previous owner and passes on repair.
- Real macOS/Metal window: fixed-seed live 3D and 4D A/B pairs, with B using
  enlarged UI and a different theme, pass. Each PNG's metadata hash matches its
  frozen arm, both arms are recorded, and A is restored. Final provider includes
  the actual applied-profile hash. No capture timeout was accepted as success.
- Evidence ID: `tet4d-window-capture-pp_xdorx`; initial successful helper-repair
  captures: `tet4d-window-capture-yy8tp_p2`. Artifacts are retained in local
  temporary evidence directories, not a durable shared screenshot bundle.
  Root images are 2560×1440 for a 1280×720 point canvas on Apple M1 Pro.
  Agent inspected both earlier successful 3D/4D cockpit images: boards were
  contained, with rail/split placement and reachable controls. This is limited
  inspection, not owner sign-off or comparison to the missing historical bundle.

The existing real-window panel runner also passed at `size=1280x720`,
`scale=standard`, with `fullscreen`: macOS DisplayServer, 82 observations,
61 screenshots, zero findings. Evidence ID `tet4d-window-responsive-5kbupoa9`.
This exercises production navigation/setup/panels, height-only transitions and
actual window modes; it does not supply owner interaction or other-device proof.

Additional real-window replay plus live 3D/4D pairs passed after inactive live
fitting was cancelled at its owner (evidence `tet4d-window-capture-pp_xdorx`).
The replay board was contained. Its replay toolbar extends beyond the selected
1280×720 root image; toolbar construction is unchanged by these repairs and
broad replay UI acceptance is not claimed. A separate responsive follow-up
needs origin/baseline assessment rather than scale changes in this refactor.
The new inactive-owner regression failed before the owner repair. Four of five
expanded scripts passed immediately; the live-cockpit packing fixture required
explicit activation in two cases, preserving all five original assertions.
The corrected full live-cockpit script then passed separately.

## Dependency review

Traced app input/profile/viewport paths, HUD navigation and Designer/laboratory
routing, cockpit scheduling and measurement, helper transitions and detached
session restoration. HUD laboratory activation/end calls now use public APIs;
no private comparison/session/search access remains in the reviewed HUD/app/
cockpit dependency paths. Existing pure policy, sole scheduler and session
owners are retained. Source audit found no need for a broad extra HUD split.
Main-menu overflow/content invalidation remains an unconfirmed concern rather
than a fabricated resolved defect. Stale Designer A/B preview, 58C depth/contrast
and Stage 59 labels remain deferred. No accepted scale/framing retuning occurred.

## Broad gates and remaining acceptance

Canonical repository gate initially stopped at generated-reference checking;
regeneration and the direct declared check then passed. Preliminary full Godot runs were stopped when copied source was superseded
by the helper/profile validation, all-mode revision and inactive-owner repairs; no pass is
claimed for those incomplete runs.
Final `CODEX_MODE=1 ./scripts/verify.sh` passed (`verify: OK`). The final pinned
`GODOT_BIN=/path/to/Godot CODEX_MODE=1 ./scripts/verify_godot_4_7.sh` passed:
94 scripts executed, no script/parse errors or unexpected teardown leaks,
59 shared topology transport parity cases, extension API identity and boot.
Normal pre-push and exact publication-head CI results are reported on PR #162;
this source record does not assert a future publication result. Aggregate governance and
semantic-boundary validation passed, with existing non-blocking advisories.
Remote CI for preceding `2049ff26` completed successfully (run `41103770668`);
that result does not certify this diff. Exact new-head CI remains required.

The supplied historical screenshot bundle is not available here. Full historical
pixel comparison, owner playability approval, physical mouse/HiDPI behavior and
other devices remain separate acceptance boundaries. The draft PR must retain
those limits; source completion and automated/rendered checks do not establish
owner acceptance or authorize recording a new baseline as accepted.

## Local rendered artifact inventory

Evidence ID `tet4d-window-capture-pp_xdorx`; hashes identify the observed PNGs,
not a promoted visual baseline or durable artifact storage.

| Arm | Render pixels | PNG SHA-256 |
| --- | --- | --- |
| Live 3D A | 1504×812 | `7d33aa4bdc961da861a48229088d1e4fcfc8b5e5a5eedc984115fe4ee333275a` |
| Live 3D B | 1311×617 | `5740f9d53db3f978430f002b8d60a3d0072092c825b7f2143f14f446d5495fc6` |
| Live 4D A | 1940×516 | `63bf71ab9a554dcd6d7b610ba54dfc2f3bd2366c98e7b74dd6d939556ad8760d` |
| Live 4D B | 2434×302 | `e333c7bd9a981b142ebc1bc279cb22c900a8a3f1138e5a5ed16f97256fd8dbae` |
| Replay 2D A | 1372×510 | `316540f7866b403f841d85e0e85250be064d82d6cba18a5914c685f880f1a75c` |
| Replay 2D B | 1196×226 | `3c3eedc530515a3fc98b6642c57566d735c402c306071864c9258bd50231bade` |
