# Live 3D/4D relative translation regression evidence

Session: 2026-10-20 to 2026-10-21. Routes: `godot_product_shell`, `governance_and_tooling`.
Execution mode: FEATURE. Layers: Godot input/presentation consumer, existing
native-session provider, test/CI infrastructure and product documentation.
Native movement, gravity, trace and replay implementations are unchanged.

## Diagnosis and scope

The initial shared-scene probe passed 290 independent command/displacement
cases with explicit Relative setup. Final review identified that the shared scene
defaults to Designer. The corrected regression launches the shipped
`game_bootstrap.tscn`, asserts `product_id == godot_game`, and re-enters
through the app's main-menu return and configured-launch handlers. That game
fixture passed all 322 cases and all four mutation proofs were repeated against
it. The inspected machine setup also selected Relative for both modes. A
current production mapping defect was not reproduced; no mapping change is justified by these observations. Explicit Absolute setup
reproduces canonical movement intentionally and is tested separately. This does
not establish the cause of an earlier unrecorded gameplay observation.

The actual path is setup model `selected_control_frames` -> app
`_sync_control_frames_from_setup` -> `_unhandled_input` -> mode-specific
translation intent -> `_control_frame_mapping` -> canonical command -> native
session -> snapshot. 3D consumes `CameraRig.control_frame_yaw()` (presented,
not target yaw). 4D consumes exact B and quantized local L, excluding outer V/P.
Existing legend probes bypass `_unhandled_input` and derive direction from the
legend; mapping units do not prove actual dispatch or successful displacement.

A confirmed CI coverage defect allowed `config/keybindings/**` changes to select
only Python evidence. That configuration now also requires the Godot lane.
Tests assert lane selection for input, app, camera, basis, L, mapping, setup,
regression, keybinding configuration, GDExtension bindings and ND command/session
providers. The adapter initially selected only `baseline, native`: the new
routing assertion failed with `assert godot in (baseline, native)`. The correction
selects `baseline, godot, native, integration` without changing native source. The required gate checks
that every selected lane passed. The canonical Godot runner requires the new
regression's explicit success marker, and CI uploads `godot-verification-log`.

## Oracle and deterministic fixture

`RDS_3D_TETRIS.md` §5 and `RDS_4D_TETRIS.md` §6 supply fixed signed-axis
command/displacement data. Neither ControlFrameMapping nor HUD output supplies
expected results. Each action requires native `last_command`, `accepted` status,
a stable active-cell count and the exact delta of every cell on every axis.
Opposite pairs must return every cell. No blocked move counts as success.

The shipped game bootstrap uses fixed seed 1337, Embedded 2D pieces and empty
6x10x6 / 6x10x6x6 bounded boards. The app's automatic process is disabled before
frames advance gameplay. Camera interpolation and held polling receive explicit
deltas. Mouse orbit/pan/zoom/Fit, exact basis actions, keyboard local yaw,
restart, Reset View and movement use the production input/view paths.
The restart button uses its connected production handler. Re-entry calls
`_return_to_main_menu` and `_start_configured_live_game` directly; it does not
drive the menu UI and checks mapping without advancing frames after relaunch.
On completion, held Input is released and the scene and viewport dimensions are
restored; a script error that aborts the test skips that cleanup. Isolated
HOME/XDG directories prevent machine settings or test persistence from
supplying accidental success.

## Commands and observed results

Use `GODOT_BIN` pointing at pinned `4.7.2.stable.official.ed1daf0bf`.

- `GODOT_BIN=/path/to/Godot ./scripts/test_live_relative_translation.sh`:
  initial 290-case baseline passed; expanded 322-case baseline passed with zero failures.
- `./scripts/verify_focus.sh tests/unit/governance/test_classify_codex_ci_paths.py --pytest tests/unit/governance/test_classify_codex_ci_paths.py`:
  55 tests passed, including provider routes, completion-marker and artifact assertions.
- Godot semantic-boundary validation: passed, 182 scripts scanned.
- Final `GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh`: exited 0, all
  85 registered scripts passed, the new regression ran at slot 34/85 with its
  explicit success marker, 59 topology transport parity cases passed, and
  the final headless boot passed without script errors or teardown leaks.
  This complete gate passed again with the final shipped-game fixture.
- Mutation proof: all four runs failed on independent assertions as listed below;
  the restored 322-case focused run passed.
- Working-checkout `CODEX_MODE=1 ./scripts/verify.sh` stopped at the secret
  scanner's 120-second wrapper timeout. The scanner enumerates directories before
  filtering excluded state; this checkout contains substantial ignored outputs.
  A fresh shared Git clone with the exact tracked and new source changes passed
  `gov doctor` and the same secret-scanner policy/timeout without exclusions or
  scanner changes. `TET4D_PYTHON=<governed interpreter> CODEX_MODE=1 ./scripts/verify.sh`
  in that isolated source checkout exited 0 with `verify: OK`. Existing sanitation
  advisories remained warnings. The source-file byte comparison matched every
  changed/new file before execution. After the shipped-game fixture correction,
  the full repository gate passed again with the pinned Godot C++ submodule
  initialized at `5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731`. The same scanner
  policy and 120-second bound passed with those dependency sources present.
  Runtime gameplay and regression code remain unchanged by the subsequent
  reporting and CI-routing updates.

Mutation commands target disposable copies only; the checked-out production
source is never mutated and needs no restoration:

| Mutation command suffix | Deliberate break | Observed assertion/result |
| --- | --- | --- |
| `--mutation A` | 3D factory ignores camera yaw | Exit 1, 319 assertions: `3D yaw 90 move_x_pos command expected move_z_neg got move_x_pos` |
| `--mutation B-basis` | 4D factory ignores exact B | Exit 1, 990 assertions: `4D view_zx_pos L=0 move_x_pos command expected move_z_neg got move_x_pos` |
| `--mutation B-local` | 4D factory ignores local L yaw | Exit 1, 906 assertions: `4D L=90 move_x_pos command expected move_z_pos got move_x_pos` |
| `--mutation C` | Relative resolves through canonical Absolute dispatch | Exit 1, 1706 assertions: the 3D yaw-90 failure above and `4D L=0 move_z_neg command expected move_z_pos got move_z_neg` |

Prefix every suffix with
`GODOT_BIN=/path/to/Godot ./scripts/test_live_relative_translation.sh`.
All four negative runs checked all 322 cases, exited 1 and contained no
`SCRIPT ERROR`. Each also failed independent displacement assertions, e.g.
`cell 0 axis 0 delta expected 0 got 1` for the Right cases above. The fresh
unmodified focused run after discarding these copies exited 0: all 322 cases
passed, with `LIVE_RELATIVE_TRANSLATION_PASS: 3D + 4D` and no script errors.
`git diff --quiet -- godot/Tet4D.Godot/scripts native src` exited 0: production
source remains unchanged.

## Acceptance boundary

Hosted execution is recorded by [PR #155 checks](https://github.com/mousomer/tet4d/pull/155/checks)
and the `godot-verification-log` artifact of its required Godot job. The PR's
Verification section records the observed successful job URL and source head.
Acceptance requires the actual log to contain `test_live_relative_translation.gd`
and `LIVE_RELATIVE_TRANSLATION_PASS: 3D + 4D`, a successful canonical Godot job,
and the required CI gate. Registration, selection, queued or cancelled runs,
and unit/legend agreement do not establish hosted execution.

Merge status belongs to the PR. No visual quality, manual gameplay,
other-device acceptance or merge claim is made here.
