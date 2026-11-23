# RP199 R0 — static cockpit baseline and duplication inventory

Role: review evidence
Status: partial R0; static inspection complete, runtime capture and verification pending
Recorded: 2026-11-23
Source revision: `master` at `391ca2ae7fe960db4f598e139fadf4e1a7a724b7` (PR #198 merged)
Design authority: PR #199, `docs/plans/unified_cockpit_visual_redesign.md` (still proposed on its design branch)
Scope: source inventory only; no gameplay, shell, input, layout, rendering, profile or fixture change

## 1. Provenance and execution boundary

The source was read from the authenticated remote GitHub repository at the pinned revision above. This environment has no Tet4D checkout and cannot resolve github.com for direct Git operations; a local `git pull`, `./gov check`, Godot run and `CODEX_MODE=1 ./scripts/verify.sh` were **not** executed. The branch containing this report was created directly from that remote master revision. No remote checks are claimed as passing on this audit branch.

Historical captures and fixtures cited below are **not** new measurements of current master. This document must not be used to declare R0 finished or to authorize an R4B layout baseline replacement.

## 2. Cockpit architecture actually present on master

| Responsibility | Owning source | Measured finding |
| --- | --- | --- |
| Shared stage, modules, scroll/fit and deck placement | `scripts/ui/live_cockpit.gd` | 872 lines; **zero** literal `live_2d`, `live_3d` or `live_4d` references; one Control implementation, not three |
| Layout decisions | `scripts/ui/cockpit_layout_policy.gd` | 91 lines; no dimension/mode references |
| Layout scheduling | `scripts/ui/cockpit_layout_coordinator.gd` | 103 lines; no dimension/mode references |
| Shared piece controls | `scripts/ui/live_piece_control_strip.gd` | One presenter, configured by mode and practice flag; localized 2D/3D rendering exceptions remain |
| Shared view controls | `scripts/ui/live_view_control_strip.gd` | One presenter, configured by mode and practice flag; regular and practice presentation branches |
| Live group descriptors and binding labels | `scripts/input/live_input_contract.gd` | One binding authority; three Live group-producing functions; separate parameterized Explorer profile |
| Shell composition and Main Menu | `scripts/ui/replay_hud.gd` | One HUD with explicit dimension-dependent placement and controls |
| Explorer panel | `scripts/ui/practice_explorer_panel.gd` | One panel configured by dimension; creates UI from `explorer_profile` |
| Explorer behavior, dispatch and held-key lifecycle | Existing Explorer-owned dispatch and profile contracts | Preserve, not a candidate for cockpit presentation deduplication |

The meaningful remaining dimensional branches are in HUD composition, not copies of the entire Control tree:

- `replay_hud.gd:779-815`: mode-specific camera menu visibility, basis panel and view-strip selection.
- `replay_hud.gd:827-882`: one Explorer panel, lazily constructed; allowed to rebuild controls when changing dimensions. The panel currently attaches below `_live_4d_state_module`.
- `replay_hud.gd:927-960`: 2D/3D side rail vs 4D split; one `LiveCockpit.set_deck_placement` call.
- `replay_hud.gd:978-996`: omit camera guidance in 2D.
- `replay_hud.gd:3730-3747`: responsive sizing routes to the same `LiveCockpit.set_available_size`.

Do **not** replace these with three new 2D/3D/4D cockpit builders, a `CockpitContext` framework, or an Explorer-only styling/layout stack. Also do not pretend that semantic 2D/3D/4D movement differences are duplicate UI implementations.

## 3. LiveInputContract duplication count

Counted directly from the return dictionaries in `live_input_contract.gd:429-505`; a group is one role block, not an individual binding row.

| Group role | 2D | 3D | 4D | Classification | Evidence and minimum change |
| --- | --- | --- | --- | --- | --- |
| Piece movement / `translate` | 1 | 1 | 1 | Semantically distinct | 2D dual legacy pair; 3D X/Z; 4D X/Z/W including slice. Preserve the current frame/axis labeling. |
| Piece rotation / `rotate` | 1 | 1 | 1 | Shared with capability parameters, distinct command inventory | 2D CW/CCW; 3D XY/XZ/YZ; 4D six planes. Reuse existing rotation specs, not a new engine. |
| Drop / `drop` | 1 | 1 | 1 | Shared with parameter | Same two roles (Soft/Hard); 2D has legacy generic soft-drop binding, 3D/4D use Shift, action IDs differ. Optional small descriptor builder. |
| Hold / `hold` | 1 | 1 | 1 | **Shared identical** | All three emit the same Piece management group, `live_hold`, and display C. A single zero-argument group factory is sufficient if extraction is approved. |
| Session / `session` | 1 | 1 | 1 | Shared with parameter | Pause + Restart Game labels repeat; 2D uses generic actions, 3D/4D dimension-specific pause/reset actions. Optional factory taking action IDs. |
| Navigation (no cockpit role) | 1 | 1 | 1 | Shared with parameter | Esc → Main Menu identical; Tab target differs (Play 3D, Play 4D, Replay Demos). Do not change menu routing. |
| Framing / `view_framing` | 1 | 1 | 1 | Semantically distinct in this slice | 2D Fit uses F, 3D/4D double-click; 4D also has zoom and broader Reset View scope. Do not blindly unify prose/actions. |
| Pointer / `view_pointer` | 0 | 1 | 1 | Shared with parameter | Reuses `CAMERA_CONTROL_SPECS`; 4D has slice-specific display text via `live_4d_pointer_helper_items`. |
| Exact camera rotation / `view_exact` | 0 | 0 | 1 | Capability only | 4D-only exact basis controls; do not fabricate missing 2D/3D capabilities. |
| Slice orientation / `view_orient` | 0 | 0 | 1 | Capability only | 4D pitch/yaw rows; preserve action IDs and projection semantics. |
| **Total groups** | **7** | **8** | **10** | **25 blocks** | **Three exact Hold copies; three parameterized Drop, Session, Navigation blocks; no duplicate cockpit tree.** |

These are static **definition occurrences**, not counts of duplicate runtime presenters. The existing `piece_control_groups` and `view_control_groups` already filter common descriptor data by `cockpit_role`, and `explorer_profile(dimension)` already provides per-dimension axes, rotation planes, session, topology, view groups and action commands.

**R4A provisional minimum:** evaluate replacing only the identical Hold definitions and, if it meaningfully reduces source repetition without changing order/labels, the parameterized Drop/Session/Navigation group constructors. This is a change inside the existing input contract, not a new abstraction layer. Keep framing, movement, rotation and 4D-specific groups where they are unless subsequent tests reveal actual maintenance bugs. No R4A edit may touch Explorer composition until its Phase 3 owner extraction is reviewed and merged.

## 4. Input-to-command surfaces that must be frozen

| Activity | Dimension | Existing descriptor and control path | Regression-sensitive distinctions |
| --- | --- | --- | --- |
| Play | 2D | `control_hint_groups("live_2d")` → `piece_control_groups` → shared piece strip | Dual movement hints; 2D CW/CCW; generic soft drop; F framing |
| Play | 3D | `control_hint_groups("live_3d")` → shared piece/view strips | X/Z, three rotation planes; Shift soft drop; 3D reset |
| Play | 4D | `control_hint_groups("live_4d", basis, frame)` → shared strips | W slice movement, six piece rotation planes, exact three camera pairs; signed-axis/basis labels |
| Explorer | 2D | `explorer_profile(2)` → Explorer panel and common helper strips | X/Y, one rotation plane; topology profile availability; Explorer-owned keys |
| Explorer | 3D | `explorer_profile(3)` → same panel and strips | X/Y/Z, three planes; orbit/framing; held-key lifecycle |
| Explorer | 4D | `explorer_profile(4)` → same panel and strips | X/Y/Z/W, six planes; exact view turns and slice inspection |

For every role, tests must assert descriptor action IDs and current binding labels, one active presenter, no double-triggered signal handlers, and refreshed controls after switching dimension and Play/Explorer. Existing Explorer controls may be reconstructed: do **not** assert persistent node instance identity.

## 5. Existing evidence (not freshly regenerated)

- `tests/test_locked_shell_layouts.gd`: historical menu and Live 2D/3D/4D layout lock, unchanged.
- `tests/test_live_input_contract.gd`: binding uniqueness, group inventories, Explorer descriptor cardinality and detached state.
- `tests/test_explorer_cockpit_lock.gd` with `tests/fixtures/explorer_cockpit_baseline.json`: event→command and visible-control fixture; must be exercised during Phase 3 and R4A.
- `docs/design/baselines/cockpit_windowed_2026_10_26/manifest.json`: historical macOS/Godot 4.7.2 capture; 410 observations per listed run, three source records and 358 listed PNG hashes. Historical provenance expressly says executions were not repeated when the bundle was recorded.
- `docs/design/ui_cockpit_result_lock_2026_10_27.json`: older source SHA inventory (source commit `e37441bb...`), **not current-master checksums**.
- `docs/design/screenshots/stage_56g_responsive_cockpit/` and `docs/design/screenshots/stage_56h_r3_cockpit/`: archived image evidence, not new R0 snapshots.

All relative `scripts/` and `tests/` paths above are under `godot/Tet4D.Godot/`.

## 6. R0 completion gates still open

1. Run `./gov check` and the resolved local verifier from a real checkout at the recorded revision; capture exact commands, environment and results.
2. Record current-master Play 2D/3D/4D and Explorer 2D/3D/4D, Main Menu, Replay and Designer with real engine screenshots at supported 700×480, 680×520, 960×640, 1280×720, 1440×900, 1600×960 and 1920×1080 viewports (where platform constraints permit). Record theme, density, focus, viewport safety and provenance.
3. Record current native/replay deterministic hashes and presentation/Designer profile fingerprints from existing accepted tools. Do not substitute obsolete lock hashes or fabricate a clean result.
4. Execute locked layout, live-input contract, Explorer cockpit, responsiveness and full verification gates. Use one completion observation rather than polling remote CI.
5. Confirm the independent Explorer Phase 3 structure-owner extraction branch is merged before any R4A modifications to `live_cockpit.gd`, `replay_hud.gd` or `practice_explorer_panel.gd`.

**Outcome of static inspection:** architecture is already substantially shared; the smallest justified future code change is descriptor deduplication. R2/R3 styling can be developed independently under the rendering visual authority. No production source or lock fixtures changed in this R0 slice.
