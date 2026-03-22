# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-03-22  
Scope: active open backlog, governance watchlist, and current change footprint.

Topology-playground note: current architecture authority lives in
`docs/plans/topology_playground_current_authority.md`. Older topology-playground
batch entries below are historical change footprint, not active architecture
instructions.

Current sub-batch (2026-03-22): frozen visible shell redesign for launcher + topology playground.
- Root cause: the settled topology-playground architecture was stable, but the visible shell still exposed the older stable-shell-cleanup framing: the launcher root stayed too crowded, the playground still led with oversized explanatory copy and always-visible diagnostics, and the default controls surface still mixed contextual controls with cross-workspace status/admin rows.
- Fix strategy: freeze a visible-shell spec first, update current-authority/current-state/RDS/backlog wording to make the visible-shell redesign the active phase, move the launcher root to `Play`, `Continue`, `Tutorials`, `Topology Playground`, `Settings`, `Quit`, demote diagnostics from the default-primary playground view, land the compact top-bar/sidebar/workspace/helper/bottom-strip shell, restore the Editor probe as a large dot with a distinct Editor-owned `Probe Neighbors` dot overlay while keeping Sandbox `Neighbors` separate, update focused tests and generated config docs, and explicitly defer deeper `controls_panel.py` / `scene_state.py` simplification until a later pass.
- Visible-shell wording freeze in the same sub-batch: replace the old stable-shell-cleanup phrasing in the live authority docs with explicit visible-shell redesign wording, freeze the short top-bar status-chip language to `Valid` / `Needs Fix` / `Unsafe`, and pin the bottom strip as chips/actions-only rather than prose hints.
- Current IA wording follow-up for the same sub-batch: keep `Tutorials` and `Help / FAQ` explicitly distinct inside one learning/support branch, split `Controls Reference` from `Settings -> Controls`, and keep the root launcher flat by routing short section labels into the existing shared settings/help/keybindings surfaces instead of adding new top-level entries.
- Placement correction in the same sub-batch: keep `Leaderboard` and `Bot` out of `Settings` as well as out of the root, and route them through the play-adjacent launcher flow instead of treating `Settings` as an overflow bucket.
- Regression correction in the same sub-batch: keep `Topology Playground` as the direct modern editor/playground entry, remove any legacy topology setup/menu split from that path, and isolate the backward-compatibility editor at `Settings -> Advanced -> Legacy Topology Editor Menu`.
- Archive cleanup in the same sub-batch: retire the older explorer-topology phase docs, menu/startup audits, playability-signaling pass, and unsafe-topology correctness plan set into `docs/history/topology_playground/`, leaving only redirect stubs under `docs/plans/` and keeping active authority in `topology_playground_current_authority.md` plus `topology_playground_shell_redesign_spec.md`.
- Probe-surface clarification in the same sub-batch: the simplified `3D` / `4D` probe surface is intentional. The current shell only needs a movable probe plus concise full translation-key guidance, so the older per-panel ND movement-preview legends remain removed while the shared 2D probe glyph language stays canonical.
- Direct-run ergonomics in the same sub-batch: keep direct Topology Playground launch available through the unified CLI wrapper via `cli/front.py --topology-playground [2|3|4]`, retain `python -m tet4d.ui.pygame.topology_lab [2|3|4]` only as a thin compatibility delegate, and pin clean unsupported-dimension handling in tracked launcher-route tests.

Current sub-batch (2026-03-22): Explorer profile/draft projection retirement + remaining shell-cache reassessment.
- Root cause: after probe-mirror retirement, the next concentrated shadow-state debt was the still-synchronized `explorer_profile` / `explorer_draft` shell projection family plus an unclear boundary around which remaining shell-owned fields were true caches versus compatibility leftovers.
- Fix strategy: stop re-synchronizing `explorer_profile` and `explorer_draft` from canonical runtime state, migrate the focused topology-lab tests onto canonical selectors/helpers instead of raw shell mirrors, document the raw profile/draft fields as fallback-only storage when canonical state is absent, and explicitly classify the remaining shell-owned fields so the next cleanup target is sharper (`play_settings` true launch-settings cache, `sandbox` true scene/render cache, `active_tool` / `editor_tool` true shell-owned routing caches; the later fallback probe-storage pass retires the old `probe_coord` / `probe_trace` / `probe_path` seam entirely).

Current sub-batch (2026-03-22): shell compatibility-mirror cleanup + legacy panel decision.
- Root cause: after the Probe-naming cleanup, the main remaining explorer-state debt was concentrated in `src/tet4d/ui/pygame/topology_lab/scene_state.py`, where retained shell fields could still be mistaken for runtime authority, and in the former vague legacy-panel bucket that still owned Normal Game rows plus resolved-profile export.
- Fix strategy: make canonical selectors the only input authority when `scene_state.py` rebuilds runtime state, stop re-synchronizing the probe shell mirror trio (`probe_coord`, `probe_trace`, `probe_path`) along with dirty/probe-visibility/probe-frame plus seam-selection/highlight compatibility fields that no longer serve live callers, migrate the remaining tests to selectors, and retire `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py` by rehoming the last legacy Normal Game row-adjustment helper directly into `controls_panel.py` while keeping row specs/value presentation and export orchestration outside any new legacy bucket.

Current sub-batch (2026-03-22): Explorer probe-naming finalization + inspect alias retirement.
- Root cause: after the first shell-helper extraction, the main remaining coupling sat between `src/tet4d/ui/pygame/topology_lab/workspace_shell.py` and private helper logic still living in `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, while `src/tet4d/ui/pygame/topology_lab/scene_state.py` and the runtime state layer still centered the retained `inspect_boundary` alias more than the desired Probe-facing internal model.
- Fix strategy: extract shell-facing row values/playability/context formatting into `src/tet4d/ui/pygame/topology_lab/controls_panel_values.py`, move probe-readiness plus pane-state selectors into `src/tet4d/ui/pygame/topology_lab/scene_state.py`, rewire `workspace_shell.py` and `topology_lab_menu.py` onto those stable seams, switch the canonical internal tool id to `probe`, retire `TOOL_INSPECT` / `tool_is_inspect(...)` from the active topology-lab surface, keep `inspect_boundary` only as compatibility-normalization input, and deliberately change the projection info-path wording to `Probe` with focused tests.

Current sub-batch (2026-03-21): Explorer internal cleanup and decomposition under the stabilized shell contract.
- Root cause: after the workspace/control-shell contract was stabilized, the main remaining risk shifted from architecture drift to concentrated UI complexity plus lingering internal `Inspect` / `Edit` residue, especially inside `src/tet4d/ui/pygame/launch/topology_lab_menu.py` and `src/tet4d/ui/pygame/topology_lab/controls_panel.py`.
- Fix strategy: extract workspace-shell copy/layout/helper logic into `src/tet4d/ui/pygame/topology_lab/workspace_shell.py`, extract contextual row ownership into `src/tet4d/ui/pygame/topology_lab/controls_panel_rows.py`, switch safe internal probe-facing action/tool routing from legacy inspect wording to probe/editor wording without changing visible behavior, and update the current-authority/docs layer in the same batch so later Codex runs treat the retained `inspect_boundary` alias as explicit compatibility debt rather than an active design direction.

Current sub-batch (2026-03-21): local branch integration after `0.6`.
- Root cause: after the verified `0.6` release was cut from a clean clone, the original local branch still contained additional gameplay/runtime/topology-lab work plus further demotion of older topology-playground plan files, leaving the shipped branch line and the local architecture/documentation state temporarily out of sync.
- Fix strategy: committed the remaining local branch changes, rebased them cleanly onto the released `true-animations` head, kept the settled topology-playground workspace/drop-policy contract intact, and re-verified the integrated branch before fast-forwarding both `true-animations` and `master`.

Current sub-batch (2026-03-21): `0.6.1` patch release.
- Root cause: retagging the published `0.6` release would have broken release reproducibility after the integrated post-release branch work landed.
- Fix strategy: bumped the package/release version to `0.6.1`, updated the changelog, reran the local release gate, published `v0.6.1`, and let the tag-triggered packaging workflow attach the new installer set to the new release instead of mutating `v0.6`.

Current sub-batch (2026-03-20): topology-playground manifest reconciliation and current-authority refresh.
- Root cause: current repo guidance was drifting across older migration manifests, newer Stage 1 / Stage 2 accepted direction, and batch-specific prompts, which left future Codex runs at risk of mixing historical `Inspect` / `Edit` or pre-generalized false-lock assumptions with the live `Editor` / `Sandbox` / `Play` and Play drop-policy contracts.
- Fix strategy: added `docs/plans/topology_playground_current_authority.md` as the single current authority for topology-playground architecture, aligned `CURRENT_STATE.md`, this backlog, and the relevant RDS files to that contract, and marked older topology-playground manifests/audits as historical or superseded background instead of active instructions.

Current sub-batch (2026-03-21): topology-playground manifest archive unification.
- Root cause: several old topology-playground manifests still read like active unfinished instructions, and other plan files still pointed at those older manifests or audits as migration-status authority.
- Fix strategy: moved the old topology-playground manifest set under `docs/history/topology_playground/`, left redirect stubs at the old paths, preserved still-live cleanup debt in `docs/plans/topology_playground_current_authority.md`, and made the precedence rule explicit: newer task instructions and the current-authority manifest override archived manifests, with ask-first escalation for severe mismatches.

Current sub-batch (2026-03-21): Explorer stabilization guidance clarification.
- Root cause: the active instruction layer already implied the intended Explorer behavior, but it did not state the current user-facing expectations bluntly enough around probe/dot consistency, trace control placement, dimension parity, sandbox default piece visibility, neighbor-dot gating, menu readability, and helper-panel placement.
- Fix strategy: updated the current-authority manifest, `RDS_TETRIS_GENERAL`, `RDS_MENU_STRUCTURE`, and current-state notes so those expectations are explicit: the legacy Inspect dot is the Editor probe/dot, probe and trace consistency are required in `2D` / `3D` / `4D`, `Trace` belongs to Editor-owned contextual controls, Sandbox must show a piece by default in `3D` / `4D` as well as `2D`, neighbor dots appear only when `Neighbors` is enabled from Sandbox-owned contextual controls, menu items must remain fully visible, and the translation/rotation helper panel must remain outside the main Explorer panel while staying minimal.

Current sub-batch (2026-03-21): Explorer stabilization implementation pass.
- Root cause: even after the guidance refresh, the live explorer still hid `3D` / `4D` sandbox cells and some projected trace state behind exact hidden-slice matching, sandbox neighbor-search still reused the Editor trace overlay path instead of explicit marker dots, and the current shell sizing still left some control rows tighter than intended.
- Fix strategy: projected Editor trace and sandbox-piece overlays directly in `3D` / `4D` projection panels so they stay visible across hidden-axis changes, split sandbox neighbor markers into explicit small-dot overlays gated only by the `neighbor search` control, stopped the Editor probe from reinterpreting later moves through a seam-rotated local frame, tightened the visual main-panel/helper split, widened the current control-row/layout budget, and added focused regressions covering canonical post-seam probe stepping, hidden-slice sandbox visibility, projected `4D` trace visibility, dot-only neighbor markers, and sandbox-overlay routing.

Current sub-batch (2026-03-21): Explorer helper/footer visibility and menu crowding follow-up.
- Root cause: the previous helper-panel toggle hit targets existed in tests but were still being painted underneath the helper body in the live shell, and the same trace/neighbor toggles still duplicated as long analysis-list rows that kept the menu column unnecessarily crowded.
- Fix strategy: reserved a real helper footer so the visible `Trace` / `Neighbor` toggle paints after the helper body, removed those duplicate analysis-list rows so the Explorer-panel toggle is the authoritative control surface, widened the analysis column/workspace split for the remaining long labels, and added tests that assert the helper toggle is actually painted in the footer rather than only existing as a hidden hit target.

Current sub-batch (2026-03-21): Explorer-panel toggle placement and real sandbox neighbor dots.
- Root cause: the user-facing control still belonged in the explorer panel rather than the external helper, and the sandbox neighbor overlay was still deriving from the sandbox focus path instead of actual reachable neighboring cells.
- Fix strategy: moved the `Trace` / `Neighbor` toggle into the explorer panel header while leaving the helper keys-only and external, changed sandbox neighbor mode to render real reachable neighbor cells as small dots in `2D` / `3D` / `4D`, aligned `3D` / `4D` sandbox cell fills with the same filled-cell display logic used in `2D`, and added focused regressions covering panel-local toggle placement, real neighbor-cell computation, and projected `3D` / `4D` neighbor-dot rendering.

Current sub-batch (2026-03-21): Explorer control-surface normalization + authority drift guard.
- Root cause: the settled `Editor` / `Sandbox` / `Play` architecture existed, but `Trace` and `Neighbor` still behaved like scene-shell exceptions, the helper still risked becoming a shadow menu, and the authority layer still described stale toggle placement that could pull future Codex passes back toward ad hoc controls.
- Fix strategy: move `Trace` into Editor-owned contextual controls, move `Neighbors` into Sandbox-owned contextual controls, keep the helper external and keys-first with at most one short context line, widen/regroup the visible controls where labels were cramped, and update the current-authority manifest, RDS files, `CURRENT_STATE.md`, and this backlog in the same batch so code and guidance stay aligned.

Current sub-batch (2026-03-21): Sandbox ND projection overlay cleanup.
- Root cause: even after the whole-piece neighbor fix, sandbox mode in `3D` / `4D` still painted the old whole-piece move-preview overlay for every legal sandbox move, which made the piece and surrounding cells look dotted and made `Neighbor` off remove only part of the clutter.
- Fix strategy: removed sandbox move-preview rendering from the ND projection scene entirely so sandbox mode now paints only filled piece cells plus optional whole-piece neighbor dots, and added a focused regression asserting that ND sandbox mode does not paint neighbor cells when `Neighbor` is off.

Current sub-batch (2026-03-21): Sandbox ND neighbor completion and box-footprint follow-up.
- Root cause: the ND projection renderer still truncated visible sandbox neighbor markers to the last `12` projected points, which dropped legitimate `3D` / `4D` directions, and the fixed `-4` inset on ND sandbox fills left those cells looking like dots instead of boxes at smaller projection-panel cell sizes.
- Fix strategy: removed the ND neighbor-marker truncation so every visible projected neighbor dot renders, deduplicated per-panel marker centers instead of silently dropping earlier directions, enlarged ND sandbox cell fills into outlined box footprints, removed the sandbox-mode center dot from the selected ND cell, and added focused regressions covering many-marker projection completeness plus ND box-footprint rendering.

Current sub-batch (2026-03-21): Sandbox ND box-shape tightening.
- Root cause: even after the first ND box-footprint pass, the projection-cell inset and corner rounding were still loose enough that some `3D` / `4D` sandbox cells read visually as rounded dots instead of boxes.
- Fix strategy: tightened the ND sandbox inset to near-full-cell fill on smaller projection cells, reduced the corner radius, preserved a visible outline, and strengthened the render regression so both side-edge and top-edge points of the projected sandbox cell must paint.

Current sub-batch (2026-03-21): Sandbox ND behavior lock pass.
- Root cause: the live fix existed in code and tests, but the active manifest/RDS wording still did not pin one critical visual rule tightly enough: in `3D` / `4D`, sandbox piece cells must read as full boxes and neighbor dots must remain a separate overlay.
- Fix strategy: tightened the current-authority manifest plus the durable RDS files so ND sandbox piece cells are explicitly required to render as box-shaped piece cells, while neighbor dots remain distinct and toggle-gated behavior.

Current sub-batch (2026-03-21): Explorer-entry contract and current-neighbor test lock.
- Root cause: the accepted live shell behavior had drifted away from several committed clean-branch tests, which still assumed Editor-first explorer entry, legacy editor-tool restoration on workspace switching, or older neighbor-marker assumptions that no longer match the current sandbox-first shell.
- Fix strategy: locked the authority file to the accepted behavior that direct explorer entry opens in `Sandbox`, switching to `Editor` preserves the current remembered topology/sandbox situation, and the current neighbor-marker behavior is canonical; then aligned the focused topology-lab launch/menu/projection tests and committed the ND scene-wrapper seam needed by those tests.

Current sub-batch (2026-03-21): clean-clone topology-explorer CI lock.
- Root cause: the dirty local worktree had accumulated enough unrelated changes that remote CI failures were no longer reliably reproducible from the main checkout. The remaining branch blockers were a mix of stale menu expectations and missing committed workspace-shell/render-wrapper seams that only showed up when the branch was installed and verified from a clean clone.
- Fix strategy: reproduced the branch in a clone-local editable install, aligned the committed topology-lab menu tests with the accepted sandbox-first/workspace-preserving shell labels, committed the missing workspace-shell helpers plus `2D`/`3D`/`4D` `neighbor_markers` scene-wrapper seam, regenerated maintenance docs from that clean branch state, and used the clean-clone `./scripts/ci_check.sh` run as the final pre-push proof that the current topology-explorer contract and CI path are locked together.

Current sub-batch (2026-03-20): topology playground Editor unification Stage 2.
- Root cause: the migrated playground already carried internal `editor` / `sandbox` / `play` ownership, but the visible shell still centered the old `Inspect` / `Edit` split, Editor movement remained effectively inspect-only, and Explorer entry still defaulted to a competing top-level Sandbox-first posture.
- Fix strategy: promoted the primary workspace ribbon to `Editor` / `Sandbox` / `Play`, added remembered Editor-tool state, routed Editor movement and projection selection through the safe probe contract even while the Edit tool is active, kept topology mutation behind explicit actions, and added focused regressions for workspace routing, helper copy, probe safety, explicit mutation, and workspace isolation.

Current sub-batch (2026-03-20): Explorer workspace regression stabilization after Editor unification.
- Root cause: after the Stage-2 workspace unification, several shell paths still treated Editor probe/trace as inspect-only, Sandbox projection focus and movement framing still depended too heavily on neighbor-overlay state, and the new workspace-first shell had regressed the explicit helper panel and some action/menu discoverability.
- Fix strategy: kept the Editor probe substrate active for both Probe and Edit, added explicit Editor trace on/off state plus action/control-row exposure, made Sandbox focus/anchor fall back to an actual visible piece cell so `3D`/`4D` rendering survives entry and movement even when neighbor overlay is off, narrowed the external helper to minimal movement/rotation guidance plus short context, widened the analysis column for current long labels, and added focused regressions for trace toggling, edit-mode probe continuity, sandbox visible-cell anchoring, helper-panel placement/content, scene rendering, and current menu readability.

Current sub-batch (2026-03-20): GitHub Actions Node 24 workflow migration.
- Root cause: hosted CI passed, but GitHub annotated the workflow because `actions/checkout@v4` and `actions/setup-python@v5` still ran on deprecated Node 20 JavaScript action runtimes.
- Fix strategy: bumped the repo workflows to `actions/checkout@v5` and `actions/setup-python@v6`, which are the Node 24-compatible action lines, then reran local verification before rechecking hosted CI.

Current sub-batch (2026-03-20): non-trivial `Y`-seam Play coverage hardening.
- Root cause: the core runtime split was already in place, but focused Play regressions still did not pin `twisted_y_3d`, `twisted_y_4d`, a custom cross-axis `Y` seam, rotation-near-seam behavior, or input/playbot parity around the explicit drop helpers.
- Fix strategy: extracted reusable launch-path invariant assertions for grounded/drop, hard-drop parity, and translation-vs-drop legality; added focused twisted/custom/rotation regressions; and added targeted input/playbot parity checks without changing runtime semantics.

Current sub-batch (2026-03-20): non-trivial `Y`-seam Play drop/lock semantics.
- Root cause: Stage 1 added useful workspace scaffolding and partial continuation tests, but Play still conflated generic explorer seam transport with drop legality. `ND` gravity/soft-drop/hard-drop could continue through gravity-axis seams just because deliberate transport existed, while `2D` soft drop diverged from gravity/hard drop on the same projective seam family.
- Fix strategy: corrected the status/design language, added live-path spherical and projective regressions from the real playground launch path, split deliberate translation from gravity/soft-drop/hard-drop intents in gameplay runtime, based grounded/lock on one legal Play drop step, preserved legal sideways bottom-layer entry, and aligned hard drop with repeated drop legality across `2D` and `ND`.

Current sub-batch (2026-03-20): topology playground restructure Stage 1.
- Root cause: the migrated playground still treated legacy `Inspect` / `Edit` tool labels as the architectural center, sandbox neighbor-search remained implicit shell behavior, and the reported `Play This Topology` bottom-boundary false-lock defect was not pinned by live-path runtime tests.
- Fix strategy: froze the internal workspace model around `editor` / `sandbox` / `play`, kept legacy tool names only as compatibility labels inside that model, made sandbox neighbor-search explicit state in runtime/menu/helper surfaces, added workspace-keyed helper scaffolding, and added live-path `3D` / `4D` play-launch regressions that assert traced continuation/lock behavior from canonical transported gameplay state. Those tests did not close the separate spherical false-lock repro, which remained open for a follow-up runtime fix.
- Focused Stage-1 coverage now lives in `tests/unit/engine/test_topology_playground_state.py`, `tests/unit/engine/test_topology_playground_launch.py`, `tests/unit/engine/test_topology_playground_sandbox.py`, `tests/unit/engine/test_topology_lab_menu.py`, and `tests/unit/engine/test_topology_lab_state_ownership.py`.

Current sub-batch (2026-03-19): shared rotation-mode menu exposure and ND wiring.
- Root cause: both rotation animation paths existed in runtime code, but the selector was hidden behind a fallback-only `2D` setting path and never modeled in persisted shared gameplay settings or threaded into `3D`/`4D` loop construction.
- Fix strategy: promoted `rotation_animation_mode` to a real shared gameplay setting in defaults/schema/sanitization, exposed it in `Advanced gameplay`, wired `3D`/`4D` loop creation through the same saved selector already used by `2D`, and updated generated configuration/user-settings references plus focused regression coverage.
- Follow-up correctness fix: flipped the rigid `2D` sprite rotation sign so positive gameplay turns animate in the same visible direction as the discrete piece transform, and tightened the rigid render regression to assert the positive-turn direction.
- Follow-up rendering fix: replaced the bounded-only rigid `2D` sprite overlay with topology-aware rotated cell boxes drawn from mapped overlay cell centers, so wrapped/custom-topology play now uses the same rigid render path instead of silently falling back to sliding upright cells.
- Drift-prevention follow-up: rigid rotation angle now derives from the canonical discrete `rotate_point_2d(...)` contract, and focused render coverage now checks visible positive/negative turn geometry in both bounded and wrapped topology modes instead of only comparing helper values to themselves.
- Seam-rendering follow-up: rigid rotating `2D` cell boxes now clip against seam windows in board-space and map each visible fragment through the topology policy, so boundary-crossing cells render partial geometry in the correct wrapped destination cells instead of as one unsplit quad.
- Translation seam follow-up: non-rigid `2D` active-piece overlays now reuse that same seam-clipped cell-box renderer with zero rotation, so deliberate translation tweens and cellwise sliding rotation tweens also show partial boundary fragments in the correct wrapped destination cells.

Current sub-batch (2026-03-17): piece translation tweening + split rotation-speed settings.
- Root cause: gameplay only rendered eased rotation overlays; deliberate piece translations still snapped instantly on some ND view-relative paths, and users could not tune 2D rotation separately from ND rotation in the shared settings hub.
- Fix strategy: extended the existing active-piece overlay tween path so it can animate pure deliberate translations without touching discrete gameplay state, fixed ND view-relative/override movement routing so deliberate 4D translations emit animation hints, split persisted rotation durations into separate `2D` and `ND` settings, and routed 2D/3D/4D loop construction through those saved settings instead of static animator defaults.
- Updated shared settings/config/docs contracts:
  - `config/menu/defaults.json`
  - `config/schema/menu_settings.schema.json`
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
  - `docs/rds/RDS_TETRIS_GENERAL.md`
  - `docs/rds/RDS_MENU_STRUCTURE.md`
- Added focused regression coverage for:
  - 2D/ND translation tween overlays and zero-duration disable behavior
  - translation-to-rotation continuity
  - shared gameplay settings round-trip/clamp coverage for separate `2D`/`ND` rotation durations plus shared translation duration
  - settings-hub summary/reset/advanced-row adjustments for the split motion controls
  - ND key-routing paths that use view-relative or override-based movement
  - rigid `2D` whole-piece rotation animation so midpoint frames preserve the piece shape instead of cell-morphing

Current sub-batch (2026-03-14): topology playground cleanup pass 2.
- Root cause: even after the ownership split and pass-1 ambiguity cleanup, the migrated explorer shell still exposed mixed tool/action concepts (`create`/`probe`/`play mode`), let non-edit surfaces reach seam-edit controls, and still carried compatibility behavior where retained shell snapshots could backstop probe-unavailable or stale play-launch paths.
- Fix strategy: collapsed the then-live explorer surface to four intermediate modes (`Edit`, `Inspect`, `Sandbox`, `Play`), restricted scene action bars and transform-editor interactivity to the owning mode, removed probe-unavailable shell-fallback dependence from `src/tet4d/ui/pygame/topology_lab/scene_state.py`, and stopped `Play This Topology` from rebuilding explorer launch state from drifted dirty shell fields.
- Historical note: this four-mode cleanup was an intermediate implementation step. It was superseded on 2026-03-20 by the accepted `Editor` / `Sandbox` / `Play` top-level workspace model recorded in `docs/plans/topology_playground_current_authority.md`.
- Updated `CURRENT_STATE.md` and `docs/history/topology_playground/topology_playground_ownership_audit.md` to mark pass-2 mode ownership as the live baseline and to narrow the remaining compatibility debt to isolated non-explorer mirrors plus explicit legacy normal-mode helpers.
- Added focused regressions in `tests/unit/engine/test_topology_lab_menu.py`, `tests/unit/engine/test_topology_lab_state_ownership.py`, `tests/unit/engine/test_topology_lab_app.py`, `tests/unit/engine/test_topology_playground_state.py`, and `tests/unit/engine/test_topology_playground_launch.py` covering mode-owned action bars, read-only inspect behavior, sandbox/play no-longer-editing paths, canonical-only play launch, and inspector/sandbox ownership continuity.

Current sub-batch (2026-03-14): explorer play-launch gameplay/runtime fix.
- Root cause: `Play This Topology` was launching gameplay with `exploration_mode=True`, so the runtime entered explorer free-movement controls/spawn/gravity semantics instead of actual play, which made launched games behave like probe/sandbox traversal and left only explorer vertical bindings visibly active.
- Fix strategy: changed `src/tet4d/engine/runtime/topology_playground_launch.py` so direct playground play launch enters standard gameplay mode, while `src/tet4d/engine/gameplay/game2d.py`, `src/tet4d/engine/gameplay/game_nd.py`, and `src/tet4d/ui/pygame/frontend_nd_input.py` now keep explorer seam transport active whenever an explorer topology profile is present instead of keying that transport solely off the free-exploration flag. Actual-play explorer pieces now remain spawn-valid above the gravity axis and use ordinary translation until they fully enter the board, preventing the no-piece/game-over-at-start regression.
- Updated `CURRENT_STATE.md` to record that explorer play launch now preserves ordinary gameplay controls/gravity/locking while still honoring the canonical explorer transport.
- Added focused regressions in `tests/unit/engine/test_topology_playground_launch.py`, `tests/unit/engine/test_game2d.py`, and `tests/unit/engine/test_game_nd.py` covering gameplay-key routing on launched playground configs, actual-play spawn validity, and live seam transport in actual play mode.

Current sub-batch (2026-03-14): topology playground dimension-cycle sandbox-state fix.
- Root cause: changing Explorer Playground dimensions while a sandbox piece/state from the old dimension was still retained could push a stale-origin sandbox payload into canonical-state reconstruction, crashing normalization with `ValueError: sandbox origin must match the active dimension`.
- Fix strategy: reset transient sandbox focus/state during dimension changes in `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, and sanitize old-dimension sandbox payloads in `src/tet4d/ui/pygame/topology_lab/scene_state.py` before rebuilding canonical runtime state.
- Updated focused menu regression coverage in `tests/unit/engine/test_topology_lab_menu.py` so stale sandbox state no longer crashes dimension switching and is replaced by a clean empty sandbox state for the new dimension.

Current sub-batch (2026-03-13): topology playground ownership and mode-boundary cleanup.
- Root cause: after the semantics pass, the live playground still mixed canonical runtime state with UI-local transients in one shell surface, and sandbox reused inspector probe selection/path/frame for projection clicks, overlays, and footer controls. That made mode ownership hard to audit and kept sandbox/inspector leakage alive even though movement semantics were already correct.
- Fix strategy: documented the live surface in `docs/history/topology_playground/topology_playground_ownership_audit.md`, exposed explicit canonical/editor/inspector/sandbox/derived ownership views from `src/tet4d/engine/runtime/topology_playground_state.py`, added `src/tet4d/ui/pygame/topology_lab/state_ownership.py` for UI-side transient buckets, and rewired `src/tet4d/ui/pygame/launch/topology_lab_menu.py` so sandbox uses sandbox-local projection focus/path/frame while inspector probe state remains isolated.
- Added focused regressions in `tests/unit/engine/test_topology_playground_state.py` and `tests/unit/engine/test_topology_lab_state_ownership.py`, plus the existing menu/sandbox suites, covering inspector/sandbox transient isolation, sandbox overlay routing, and canonical-state survival across tool switches.

Current sub-batch (2026-03-13): topology-lab explorer defaults + dimension round-trip reset semantics.
- Root cause: Explorer Playground still carried hard-coded compact board defaults in code, while topology-lab launch and dimension switching mixed those defaults with saved mode snapshots inconsistently. A saved 4D launch size could be discarded on a dimension round-trip, and there was no explicit way to restore explorer defaults other than toggling dimensions.
- Fix strategy: moved explorer compact board defaults into `config/menu/defaults.json`, added a shared `mode_settings_snapshot_for_dimension(...)` helper so launcher/topology-lab read one merged saved-mode snapshot path, cached per-dimension explorer play settings inside the topology-lab scene state, and restored target-dimension settings from that cache or the saved-mode snapshot instead of rebuilding from bare defaults.
- Added an explicit `F8` reset path in the topology lab that restores the current dimension's explorer play settings to the config-backed explorer defaults, updates the cached per-dimension snapshot, and advertises the shortcut in the shell hints.
- Added focused regressions in `tests/unit/engine/test_topology_lab_app.py`, `tests/unit/engine/test_topology_lab_menu.py`, and `tests/unit/engine/test_front_launcher_routes.py` covering config-backed explorer defaults, saved-mode snapshot merging, 4D dimension round-trip preservation, and explicit reset-to-defaults behavior.

Current sub-batch (2026-03-13): topology playground semantics-correctness stabilization.
- Root cause: explorer movement correctness still leaked flat-chart assumptions in two places: piece-step rigidity classification treated chart-split torus wraps as deformation, and ND legality-preview input still defaulted explorer moves to rigid handling even when the active topology was cellwise-only.
- Fix strategy: kept atomic whole-piece placement, added an explicit `CELLWISE_FREE` vs `RIGID` movement-policy helper for active explorer runtime paths, split seam point-mapping from piece-frame transport in the shared resolver, and treated chart-split seam results as rigidly coherent when the transported piece frame remains consistent even though one chart cannot express the move as one affine transform.
- Updated `src/tet4d/engine/topology_explorer/transport_resolver.py`, `src/tet4d/engine/gameplay/explorer_runtime_2d.py`, `src/tet4d/engine/gameplay/explorer_runtime_nd.py`, `src/tet4d/engine/gameplay/game2d.py`, `src/tet4d/engine/gameplay/game_nd.py`, `src/tet4d/engine/runtime/topology_playground_sandbox.py`, `src/tet4d/ui/pygame/frontend_nd_input.py`, and `src/tet4d/ui/pygame/topology_lab/projection_scene.py` so sandbox/gameplay/input previews all consume the same policy-aware whole-piece transport semantics.
- Added focused regressions in `tests/unit/engine/test_explorer_transport_resolver.py`, `tests/unit/engine/test_explorer_transport_parity.py`, `tests/unit/engine/test_game2d.py`, `tests/unit/engine/test_topology_playground_sandbox.py`, `tests/unit/engine/test_topology_playability_signal.py`, and `tests/unit/engine/test_nd_routing.py` covering torus chart-split rigid acceptance, explicit rigid-vs-cellwise projective behavior, ND legality-preview parity, and playability analysis that no longer mislabels coherent torus wraps as non-rigid.

Current sub-batch (2026-03-13): projection-first 3D/4D Explorer Playground views.
- Root cause: the retained 3D/4D Explorer Playground primary scenes still rendered boundary-shell abstractions, which made inspector and sandbox state hard to reason about even after seam/runtime correctness improved.
- Fix strategy: replaced the 3D/4D primary scene with synchronized 2D coordinate-plane projection panels driven by the same canonical probe/sandbox/seam state, while preserving boundary and seam picks through a compact ribbon instead of free-camera shell sketches.
- Added `src/tet4d/ui/pygame/topology_lab/projection_scene.py`, rewired `scene3d.py` / `scene4d.py` onto it, routed projection-cell clicks back through canonical probe selection in `scene_state.py` and `topology_lab_menu.py`, and restricted scene-camera mouse interception to wheel / middle-mouse debug input so left-click selection remains reliable.
- Added focused regressions in `tests/unit/engine/test_topology_lab_scenes.py` and `tests/unit/engine/test_topology_lab_menu.py` covering the exact `3D` (`xy/xz/yz`) and `4D` (`xy/xz/xw/yz/yw/zw`) panel families, hidden-coordinate labeling, projection-cell selection sync, and left-click precedence over the retained debug-camera path.
- Explorer Playground startup defaults now use compact under-`9` board sizes (`8` along each axis) when entering from untouched launcher defaults or direct lab startup, while explicitly user-sized launches still preserve the chosen board dimensions.

Current sub-batch (2026-03-12): explorer seam transport resolver unification.
- Root cause: preview/probe used canonical explorer seam traversal, while sandbox/gameplay/playability still mixed in duplicated or inferred piece-transport logic, letting runtime seam behavior drift by system and dimension.
- Fix strategy: added `src/tet4d/engine/topology_explorer/transport_resolver.py` as the shared explorer transport authority for cell steps, rigid piece steps, seam traversal metadata, and canonical frame transforms derived directly from explorer gluing definitions.
- Rewired active explorer paths to that resolver: movement-graph/preview/probe, sandbox, 2D gameplay, ND gameplay, playability analysis, direct playground launch, play-menu explorer launch config, and exploration-mode overlay mapping in the 2D/3D/4D renderers.
- Added focused regressions in `tests/unit/engine/test_explorer_transport_resolver.py`, `tests/unit/engine/test_explorer_transport_parity.py`, and strengthened preview/launch/sandbox/game/unsafe/setup suites to pin 2D/3D/4D seam parity and launch preservation.
- Follow-up seam-family completeness pass: the resolver now materializes the full directed seam table for every active explorer gluing, validates reverse/inverse coverage across whole boundaries, and the topology-lab app launch path now rebuilds explorer transport after applying the chosen board dimensions so multiple seam families do not silently degrade at runtime.
- Remaining limitation: steps that resolve to `cellwise_deformation` are still intentionally blocked for rigid gameplay/sandbox even when the topology remains valid for explorer/probe traversal.


Current sub-batch (2026-03-12): play-launch topology propagation + unsafe launch fix.
- Updated `src/tet4d/ui/pygame/topology_lab/controls_panel.py` so `Play This Topology` now re-synchronizes dirty canonical playground state and refreshes launch-critical preview validity before deciding whether to block or launch.
- This restores launch-time topology propagation on the migrated path even when retained shell snapshots have drifted, and it clears stale invalid preview errors before a now-valid unsafe topology launches.
- Added focused regressions in `tests/unit/engine/test_topology_lab_menu.py` covering stale shell profile/dimension resync and stale-invalid-preview recovery for valid unsafe launch.

Current sub-batch (2026-03-12): topology playability signaling pass 1.
- Added `src/tet4d/engine/runtime/topology_playability_signal.py` and extended `src/tet4d/engine/runtime/topology_playground_state.py` so the canonical playground state now derives one runtime-owned playability analysis covering validity, explorer usability, rigid playability, summary text, and reason strings.
- Updated `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and `src/tet4d/ui/pygame/launch/topology_lab_menu.py` so Analysis View rows plus the workspace status/preview panel now expose explicit `Validity`, `Explorer`, `Rigid Play`, and `Why` messaging before `Play This Topology`.
- Added focused regressions in `tests/unit/engine/test_topology_playability_signal.py` and `tests/unit/engine/test_topology_lab_menu.py` covering valid rigid-playable, valid explorer-only/non-rigid, and invalid topology states.
- Added [`docs/history/topology_playground/topology_playability_signaling_pass1.md`](docs/history/topology_playground/topology_playability_signaling_pass1.md) as the implementation note for this signaling stage.

Current sub-batch (2026-03-12): unsafe topology correctness fix pass 1.
- Aligned sandbox seam acceptance in `src/tet4d/engine/runtime/topology_playground_sandbox.py` with gameplay transport semantics by reusing `classify_explorer_piece_move(...)`, so sandbox now accepts `plain_translation` and `rigid_transform` seam moves while continuing to block `cellwise_deformation`.
- Split explorer validation in `src/tet4d/engine/topology_explorer/glue_validate.py` into topology-structure and board-bijection checks, while `src/tet4d/engine/runtime/topology_playground_launch.py` now validates the canonical explorer profile against the active board dimensions before gameplay launch; non-bijective unsafe preset / board-size pairings now fail explicitly as `unsupported for current board dimensions ...`.
- Preserved invalid topology as the canonical draft state in `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and `src/tet4d/ui/pygame/topology_lab/app.py`: explorer/launcher entry and manual seam apply now keep the current topology definition, surface the invalid state explicitly, and no longer swap in fallback presets or silently drop the seam.
- Added focused regressions in `tests/unit/engine/test_topology_lab_app.py`, `tests/unit/engine/test_topology_lab_menu.py`, `tests/unit/engine/test_topology_explorer.py`, `tests/unit/engine/test_topology_playground_sandbox.py`, and `tests/unit/engine/test_unsafe_topology_correctness.py` covering canonical invalid-state preservation, cross-axis glue roundtrips, safe bounded/wrap baselines, Projective cellwise traversal, sandbox/gameplay rigid-transport parity, and invalid Sphere dimension handling.
- Added [`docs/history/topology_playground/unsafe_topology_correctness_fix_pass1.md`](docs/history/topology_playground/unsafe_topology_correctness_fix_pass1.md) as the implementation note for this narrow correctness stage.


Current sub-batch (2026-03-12): unsafe topology correctness audit.
- Added [`docs/history/topology_playground/unsafe_topology_correctness_audit.md`](docs/history/topology_playground/unsafe_topology_correctness_audit.md) as the diagnostic authority for unsafe / quotient topology behavior across preview, probe, sandbox, and play launch.
- Reproduced two separate blocker classes:
  - preview-valid point connectivity that is not always rigid-piece-safe in play
  - sandbox rejecting `rigid_transform` seam moves that gameplay already accepts
- Confirmed the migrated play-launch path still hands the live canonical explorer profile directly into gameplay; the main mismatch is transport semantics, not a stale-profile conversion on the audited path.
- Confirmed sphere-like unsafe presets still fail preview compilation on non-bijective board dimensions, which leaves probe/play unavailable until the board extents satisfy the gluing transform.

Current sub-batch (2026-03-12): topology explorer latency reduction pass 1.
- Removed the duplicated migrated-path dimension-change post-pass in src/tet4d/ui/pygame/topology_lab/controls_panel.py, so _cycle_dimension(...) now performs one real canonical sync and scene refresh instead of re-entering _mark_updated(...) for a cached second pass.
- Short-circuited launch-only Piece Set and Speed edits in src/tet4d/ui/pygame/topology_lab/controls_panel.py by comparing ExplorerPreviewCompileSignature before and after the setting change; unchanged signatures now skip scene refresh and keep the current preview/experiment batch alive.
- Reused the live preview payload for migrated-path Export Explorer Preview via src/tet4d/engine/runtime/topology_explorer_preview.py; representative 4D export timing dropped from the audit baseline 402.8 ms to 2.1 ms handler / 1.9 ms export-call time when the live preview already matches.
- Made experiment-pack export single-pass via src/tet4d/engine/runtime/topology_explorer_experiments.py and src/tet4d/engine/runtime/topology_explorer_runtime.py; representative 4D Build Experiment Pack timing dropped from the audit baseline 10.31 s to 5185.7 ms, with the remaining cost now concentrated in the one required compile (5183.3 ms) rather than a second export-time rebuild.

Current sub-batch (2026-03-12): topology playground legacy-consumer retirement pass.
- Migrated the live probe/highlight write path in `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and `src/tet4d/ui/pygame/topology_lab/boundary_picker.py` onto canonical `scene_state.py` helpers, so canonical runtime probe state now owns more of the remaining migrated explorer path instead of direct shell snapshot writes.
- Split normal-mode preset/topology-mode/edge-rule rows plus legacy resolved-profile export into the then-transitional helper now narrowed as `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py`, leaving `src/tet4d/ui/pygame/topology_lab/controls_panel.py` with thin legacy delegation rather than mixed old/new responsibility.
- Removed the unused `run_topology_lab_menu(...)` alias after caller audit found no remaining `src/` callers; focused launch coverage now stays on `run_explorer_playground(...)`.
Current sub-batch (2026-03-11): topology playground startup optimization pass 2.
- Added a state-local Explorer preview cache keyed by the effective `ExplorerTopologyProfile` plus normalized board dims in `src/tet4d/ui/pygame/topology_lab/scene_state.py` and `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, so repeated migrated-path refreshes now reuse compiled preview payloads instead of rebuilding the movement graph.
- Restricted invalidation to real preview-signature changes: board-size/profile changes replace the cached preview, leaving the migrated path or losing the explorer profile clears it, and unrelated UI churn such as tool/pane/speed/piece-set changes reuses the cached preview while preserving the current experiment batch.
- Extended `scripts/profile_topology_playground_startup.py` to trace repeated refreshes and measured the `4D` migrated path at `1718.9 ms` for the one startup preview compile versus `0.061 ms` and `0.030 ms` for repeated same-signature refreshes, with `0` movement-graph rebuilds in the repeated-refresh phase.
Current sub-batch (2026-03-11): topology playground startup optimization pass 1.
- Reduced the audited Explorer Playground startup path to one pre-first-frame movement-graph build by validating launch profiles cheaply in `src/tet4d/ui/pygame/topology_lab/app.py`, skipping the stored explorer-profile refresh when an explicit launch profile is already supplied in `src/tet4d/ui/pygame/launch/topology_lab_menu.py`, and defaulting the initial probe from validated center coordinates in `src/tet4d/engine/runtime/topology_explorer_preview.py`.
- Removed redundant per-cell `validate_explorer_topology_profile(...)` calls from `src/tet4d/engine/topology_explorer/movement_graph.py`, so the remaining startup graph build validates once per `(profile, dims)` instead of once per cell.
- Measured via `scripts/profile_topology_playground_startup.py`: first interactive frame dropped from `137.5/555.5/6890.3 ms` to `64.6/215.9/2326.1 ms` for representative `2D/3D/4D` explorer launches, and startup movement-graph builds dropped from `4` to `1`.
Current sub-batch (2026-03-10): topology playground canonical-state Stages 1-2.
- Added `src/tet4d/engine/runtime/topology_playground_state.py` as the canonical engine/runtime-owned topology playground state contract for dimension, axis sizes, topology config, selection, probe/sandbox state, transport/gravity, playability, presets, launch settings, and dirty tracking.
- Routed the migrated explorer scene cache, preview payload, and explorer-side selection/probe read path through that canonical state via additive bridge helpers in `src/tet4d/ui/pygame/topology_lab/scene_state.py`, `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`, and `src/tet4d/ui/pygame/launch/topology_lab_menu.py`.
- Kept retained UI-local shell paths in place for compatibility and non-migrated analysis/edit flows; this batch does not delete the old panels or claim full direct gluing-edit migration.
Current sub-batch (2026-03-10): Stage 3 direct explorer-side gluing edits.
- Explorer-scene seam picks, right-click existing-boundary edit picks, and linked glue-slot inspection now synchronize canonical boundary/seam selection plus the normalized gluing draft instead of only mutating shell-local state.
- Added focused explorer playground regressions in `tests/unit/engine/test_topology_lab_menu.py` covering seam picks, glue-slot seam inspection, and right-click edits of existing glued boundaries without leaving the explorer shell.
Current sub-batch (2026-03-11): Stage 5 sandbox migration is now live through engine/runtime-owned playground state: added `src/tet4d/engine/runtime/topology_playground_sandbox.py` as the canonical sandbox owner, rewired `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py` into a thin adapter, and moved spawn/move/rotate/seam-cross preview off the detached UI-local sandbox state path.
Current sub-batch (2026-03-11): explorer piece transport frame preservation + ND launcher return semantics.
- Added `src/tet4d/engine/gameplay/explorer_piece_transport.py` so explorer movement now classifies transported pieces as `plain_translation`, `rigid_transform`, or `cellwise_deformation` before mutating frame state.
- Updated `src/tet4d/engine/gameplay/explorer_runtime_2d.py` and `src/tet4d/engine/gameplay/explorer_runtime_nd.py` so interior translations preserve the existing local frame, coherent seam-safe rigid moves apply an explicit piece-frame transform, and unsafe seam deformation is blocked instead of silently min-corner-normalized.
- Updated `src/tet4d/ui/pygame/launch/launcher_nd_runner.py` so returning from Explorer Playground no longer exits the ND launcher just because the playground reported a recoverable status message.
Stage 6 demotion cleanup is now live: the launcher's ordinary custom-topology action now enters the unified Explorer Playground shell through `run_explorer_playground(...)`, so the detached lab route is no longer required for ordinary topology editing.
Stage 7 is now live: the graphical explorer is the primary editor, and the former row/list line+dots surface is now labeled `Analysis View` and treated as optional secondary analysis only.
- The `Analysis View` pane now keeps board/preset settings, save/export, experiment-pack launch, and read-only seam context only; row-based source/target/tangent/apply/remove seam editing no longer acts as a parallel editor on the migrated explorer path.
- Menu ambiguity cleanup pass 1 is now live on the migrated explorer path: `Explorer Preset` in `Analysis View` is the canonical visible preset control, the transform editor now shows that preset as read-only state instead of a second button surface, `Save`/`Export`/`Experiments`/`Back` no longer duplicate in the workspace action bar, `Play Mode` replaces the misleading play-toggle label, analysis seam-context rows are display-only, the `Normal Game` path is labeled as legacy compatibility, and the footer movement grid now spells out whether it moves the probe or the sandbox piece.
Remaining legacy-only blockers on this surface: retained shell fields in `src/tet4d/ui/pygame/topology_lab/scene_state.py` still survive as synchronized compatibility projections for legacy readers/diagnostics, while normal-mode legacy rows plus resolved-profile export still exist intentionally through `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py`.
Stage 8 is now live: the shell action is explicitly `Play This Topology`, and play launch uses the current in-memory playground draft directly without a secondary conversion menu on the migrated path.
- The migrated play-launch path now bypasses the older shell-snapshot `build_explorer_playground_config(...)` helper and instead routes through `src/tet4d/engine/runtime/topology_playground_launch.py` plus `src/tet4d/ui/pygame/topology_lab/play_launch.py`, which derive gameplay launch directly from the canonical `TopologyPlaygroundState`.
Stage 9 is now live: ordinary play menus and launcher settings surfaces are now preset-only for topology, keeping safe preset launches plus `Play Last Custom Topology` and `Topology Playground` while leaving topology complexity in the playground shell.
Explorer experiment packs now live in the Explorer Playground: the current draft and preset family export as a shared comparison batch with an in-shell recommendation for what to try next.

Stage 4 live playground settings on top of the Stage 3 explorer-side topology editing path.
- Kept the existing UI scene caches in `src/tet4d/ui/pygame/topology_lab/scene_state.py` as retained shell-local compatibility debt rather than the canonical source of truth.
- Confirmed the playground shell itself exposes the dimension selector, axis-size editors, and explorer preset selector for the migrated explorer-entry path.
- Added focused explorer-entry regressions in `tests/unit/engine/test_topology_lab_menu.py` proving dimension, board-size, and preset changes update canonical state directly and refresh the migrated explorer scene without leaving the shell.

Current sub-batch (2026-03-09): explorer topology Phase 5 live runtime migration + Phase 6 diagnostics + Phase 7 scene-first playground integration + Phase 8 runtime-owned bridge shrink + Phase 9 shared launch-contract unification + Phase 10 setup-side unification.
- Routed live explorer gameplay/runtime through the general gluing engine for ND and 2D via `src/tet4d/engine/gameplay/explorer_runtime_nd.py`, `src/tet4d/engine/gameplay/explorer_runtime_2d.py`, `GameConfigND.explorer_topology_profile`, and `GameConfig.explorer_topology_profile`.
- Updated ND and 2D setup/export flows so Explorer launch now resolves the stored gluing profile by default, while legacy edge-rule bridging remains only for explicit compatibility export/preview paths.
- Added focused regression coverage for mode-aware config loading, live explorer wrap movement, and explorer move prediction.
- Added engine-owned explorer diagnostics in preview payloads and surfaced them in the lab sidebar for orientation-reversing, cross-axis, and disconnected movement-graph warnings.
- Added engine-owned tangent-basis arrow previews to explorer preview payloads so the lab now shows actual signed basis mappings for each gluing instead of only counts and warnings.
- Replaced the explorer lab's text-only workspace with a scene-first graphical playground under `src/tet4d/ui/pygame/topology_lab/`, so boundary selection, seam editing, basis-arrow inspection, and probe traversal now happen inside one explorer shell with side panels acting as supporting editors.
- Completed the scene-first playground owners (`scene_state.py`, `explorer_tools.py`, `boundary_picker.py`, `scene2d.py`, `piece_sandbox.py`) and kept `topology_lab_menu.py` as the orchestration shell over those owners.
- Added clickable seam arrows, scene-visible probe path state with reset, explorer-only sandbox controls, and direct play-from-draft launch in the same explorer shell for 2D/3D/4D.
- Unified live Explorer launch with the same scene-first playground shell, so entering Explorer 2D/3D/4D now opens the graphical topology playground directly instead of a separate detached explorer frontend.
- Added `src/tet4d/ui/pygame/topology_lab/app.py` as the shared explorer-playground launch owner, so Explorer Mode and the Topology Lab menu action now build the same shell launch state and differ only by entry context.
- Removed topology-editor rows from the outer Explorer setup menus and made Explorer launch/export resolve the stored gluing profile by default, so topology design now lives in the unified playground shell rather than in detached pre-launch menu rows.
- Added focused regression coverage for sandbox transport/limitations, probe reset/path state, and 2D/3D/4D play-preview routing from the in-memory draft topology.
- Moved remaining explorer setup/export bridge usage behind `src/tet4d/engine/runtime/topology_explorer_runtime.py`, so UI setup owners and Topology Lab export no longer import the legacy edge-rule bridge directly.
- Extended the direct Explorer Topology Lab editor to 2D and 4D, so all explorer dimensions now edit engine-owned gluing profiles instead of legacy edge-rule rows.
- Added engine-owned 2D/4D explorer presets plus a live sidebar preview for boundary ownership, active gluings, and movement-graph diagnostics in all direct editor dimensions.
- Added unsafe `Projective` / `Sphere` preset families for 2D/3D/4D at the engine preset layer and exposed them in the lab with explicit unsafe labeling.
- Added `scripts/verify_focus.sh` as the documented staged local validation helper; full `verify.sh` remains the required final gate.
- Relaxed the newer thin-wrapper drift budgets for `cli/front.py`, `src/tet4d/engine/api.py`, and `src/tet4d/ui/pygame/front2d_game.py`, and documented a contributor rule preferring medium-sized localized patches over brittle ultra-narrow patch fragmentation.
- Clarified contributor edit-method selection so localized code edits use `apply_patch`, while broad drifting doc rewrites use one deterministic scripted rewrite instead of repeated failing patch retries.
- Added stricter write-safety policy for source files: no multiline PowerShell `-replace`, no BOM-producing source writes, mandatory touched-file hygiene after non-patch rewrites, and explicit prohibition on running `verify.sh` / `ci_check.sh` in parallel.
- Tightened edit-method escalation: dirty/generated maintenance files now skip patch-first behavior, and one rejected `apply_patch` attempt per file is the maximum before switching to a deterministic rewrite path.
- Added an explicit Explorer Playground unification contract: pane-aware helper text, mouse-adjustable +/- controls, scene-first Explorer entry parity, and 3D/4D in-shell camera controls are now treated as drift-protected behavior rather than implied UX.
- Moved the remaining legacy-profile preview export bridge out of `src/tet4d/engine/runtime/topology_explorer_runtime.py` and into the explicit compatibility bridge owner, so the runtime facade now only owns direct explorer launch/store/export paths.
- Tightened scene picking so overlapping targets prefer the most specific nearby hit, reducing false row picks when seam/step targets overlap in the Explorer Playground.
- Explorer Playground unification is now complete for the product contract; only optional structural cleanup remains.

## 1. Priority Verification Rules

1. `P1` = user-facing correctness, consistency, and discoverability gaps.
2. `P2` = maintainability and complexity risks that can cause regressions.
3. `P3` = optimization, tuning, and documentation hygiene.

## 2. Unified Change Set (Implemented Baseline)

Historical DONE summaries were deduplicated and moved to a single source:

- `docs/history/DONE_SUMMARIES.md`

Policy for updates:

1. New implementation detail belongs in `## 5. Change Footprint` for the active batch.
2. At batch close, summarize and append durable DONE history in `docs/history/DONE_SUMMARIES.md`.
3. Keep `docs/BACKLOG.md` focused on active open issues and near-term execution.

Historical anchor references:

- `[BKL-P3-001]` pre-push local CI gate checkpoint is closed and retained in historical DONE source.

## 3. Active Open Backlog / TODO (Unified RDS Gaps + Technical Debt)

1. Canonical machine-readable debt source:
   `config/project/backlog_debt.json` (`active_debt_items`).
2. Policy-pack and context-router manifests are contract-validated via:
   `tools/governance/validate_project_contracts.py`.

### Active Open Items (Canonical)

1. None currently.

### Historical ID Lineage Policy

1. Backlog IDs must be unique in this file for unambiguous audit/search.
2. Legacy rerolled IDs use `-R2` suffix (for example `BKL-P2-010-R2`) when an original ID already exists in historical DONE ledgers.
3. Legacy/base references are retained in historical files; active/open tracking stays in this file.

### Operational Watchlist (Non-debt; recurring controls)

Cadence: weekly and after workflow/config changes.  
Trigger: any governance, CI-workflow, runtime-validation, or release-process drift.  
Done criteria: controls run cleanly and docs/contracts remain synchronized.

1. `WATCH` `[BKL-P3-002]` Scheduled stability + policy workflow watch:
   cadence remains weekly and after workflow/config changes for
   `.github/workflows/ci.yml`, `.github/workflows/stability-watch.yml`,
   `tools/stability/check_playbot_stability.py`, and
   `tools/benchmarks/analyze_playbot_policies.py`.
2. `WATCH` `[BKL-P3-003]` Runtime-config validation split watch:
   triggered only when playbot policy-surface growth exceeds maintainable scope
   in `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`.
3. `WATCH` `[BKL-P3-006]` Desktop release hardening watch:
   cadence remains before each public release and is tracked through
   release-packaging workflow + release checklist/installers docs.
4. WATCH [BKL-P3-007] Module decomposition watch:
   large engine/runtime/ui module split pressure moved from active debt to watch
   after shared-settings and API dedup passes; monitor hotspot growth and
   continue staged LOC reduction.
5. WATCH [BKL-P3-009] Playbot learning-mode tuning watch:
   monitor threshold retuning and long-run stability behavior after adaptive
   learning-mode rollout.
6. WATCH [BKL-P3-013] Interactive tutorials rollout watch:
   track data-driven lesson packs, deterministic step progression, input gating,
   and tutorial regression harness coverage across 2D/3D/4D.

## 4. Gap Mapping to RDS

1. `docs/rds/RDS_TETRIS_GENERAL.md`: CI/stability workflows and setup-menu dedup follow-up are closed; maintain drift watch only.
2. `docs/rds/RDS_PLAYBOT.md`: learning-mode architecture is implemented; maintain tuning/stability watch only.
3. `docs/rds/RDS_MENU_STRUCTURE.md`: menu graph modularization and interactive topology-lab workflow are closed; maintain drift watch only.
4. `docs/rds/RDS_FILE_FETCH_LIBRARY.md`: lifecycle/adaptive-fetch design baseline exists; implementation remains future-scoped.

## 4.1 Interactive Tutorials Plan (BKL-P3-013)

### Objective

Ship an in-game, step-driven tutorial system that:

1. Teaches movement in nD, rotation, camera control, and layer completion.
2. Works consistently across 2D, 3D, and 4D modes.
3. Is scriptable/data-driven, testable, and resilient to UI/input refactors.

### Scope

In-scope:

1. A tutorial engine (state machine + triggers + gating).
2. A data schema to define tutorial lessons (JSON/YAML).
3. Overlay UI: instruction panel, key prompts, highlights, ghost targets,
   progress indicator.
4. Interactive lessons:
   2D: move/rotate/drop + complete a line.
   3D: move in 3 axes, rotate in 3D, camera orbit/pan, complete a layer/plane.
   4D: move in 4 axes (or slice + axis select), rotate in 4D planes, camera +
   slice navigation, complete a hyper-layer (per runtime clearing definition).

Out-of-scope (this pack):

1. Full campaign/story mode.
2. Full localization framework implementation (leave hooks only).
3. Analytics backend (local event logging hooks only).

### Non-negotiable design constraints

1. Deterministic progression: steps advance only on explicit conditions.
2. No hard-coded lesson logic beyond generic triggers/conditions; lessons are data.
3. Input gating per step: allowed actions constrained; disallowed actions ignored
   (optional user feedback).
4. Skippable and restartable at any time.
5. Mode-agnostic core: 2D/3D/4D are content packs, not separate implementations.
6. Deterministic tutorial start contract:
   first step starts with a curated asymmetric piece, full visibility at least
   two gravity layers below top, and deterministic 1-2 seeded bottom layers.

### Context requirements (Codex router)

1. Code context: input handling, game loop/update, UI rendering, camera controls,
   piece transforms, line/layer clear logic.
2. Docs context: control scheme documentation, gameplay definitions for layer in
   3D/4D, UX conventions.
3. Config context: keybind mappings, settings flags, UI theme tokens.
4. Runtime context: tutorial event logs, step transitions, replay traces.
5. Git context: diff scope + feature branch hygiene.
6. Planning context: acceptance criteria + stop conditions.

### Deliverables

D1. Tutorial engine (core):

1. Load lesson definitions (JSON/YAML).
2. Maintain `(lesson_id, step_id)` state.
3. Evaluate conditions and triggers.
4. Enforce input gating.
5. Emit events:
   `step_started`, `hint_shown`, `condition_met`, `step_completed`,
   `lesson_completed`, `lesson_skipped`.

Implementation shape:

1. `TutorialManager` service.
2. `Step` definition with:
   `instruction_text`, optional `hint_text`,
   `allowed_actions`/`blocked_actions`,
   `on_enter` hooks (spawn target, camera preset, fixed seed),
   `completion_conditions`,
   `timeout_hint_seconds` (optional).

Condition system:

1. Event predicates: action performed, rotation plane used, camera moved.
2. World predicates: piece position/orientation, layer cleared, target cell filled.
3. Composite predicates: AND/OR DSL.

D2. Tutorial content schema (data-driven):

Schema requirements:

1. Versioned (`schema_version`).
2. Validatable (unit tests + JSON schema where used).

Minimum fields:

1. `lesson_id`, `title`, `mode` (`2d|3d|4d`).
2. `steps[]` with:
   `id`,
   `ui: {text, hint, highlights[], key_prompts[]}`,
   `gating: {allow[], deny[]}`,
   `setup: {camera_preset?, spawn_piece?, board_preset?, rng_seed?}`,
   `complete_when: {events[], predicates[], logic}`,
   optional `fail_when`.

D3. Tutorial UI overlay:

UI elements:

1. Instruction panel (top/side).
2. Contextual key prompts (from keybind config).
3. Highlight system:
   piece/axes gizmo/target cells/camera widget.
4. Progress indicator (step X/Y).
5. Skip/restart controls (also accessible from pause menu).

Hard constraint:

1. UI depends on tutorial state + highlight descriptors only, not renderer internals.

### Tutorial curriculum (content packs)

Pack A: 2D tutorial (short, canonical)

Lesson A1 Movement:

1. Move left/right to marked columns.
2. Soft drop vs hard drop.
3. Hold (if supported) + next-preview explanation (non-blocking).

Lesson A2 Rotation:

1. Rotate with positive/negative quarter-turn inputs.
2. Wall-kick demonstration (if supported).

Lesson A3 Clear a line:

1. Place piece to complete a nearly-finished line.
2. Clear confirmation + brief scoring explanation.

Definition of done (Pack A):

1. New player can complete a line in under two minutes without external docs.

Pack B: 3D tutorial

Lesson B1 Camera control:

1. Orbit.
2. Pan.
3. Zoom + reset view.

Lesson B2 Movement in 3 axes:

1. X/Y move (screen plane).
2. Z move (depth).
3. Layer/slice explanation if applicable.

Lesson B3 3D rotations:

1. Rotate around X/Y/Z (or equivalent mapping).
2. Demonstrate supported reference frame (camera-relative or world-relative).

Lesson B4 Clear a layer:

1. Complete a plane with constrained placement.
2. Show clear animation + resulting board state.

Definition of done (Pack B):

1. Player demonstrates camera orbit, depth move, one rotation, one plane clear.

Pack C: 4D tutorial

Lesson C1 Understanding slices:

1. W-slice concept.
2. Slice navigation (`W-`/`W+` or equivalent).
3. Active-slice indicator behavior.

Lesson C2 Movement in 4 axes:

1. Move in visible plane.
2. Move along W (or equivalent abstraction).
3. Confirm cross-slice placement.

Lesson C3 4D rotations (plane-based):

1. Rotate in visible 3D subspace.
2. Rotate involving W planes (`XW`/`YW`/`ZW` or equivalent).
3. Teach rotation-plane selection UX.

Lesson C4 Clear a hyper-layer:

1. Start from near-complete deterministic preset.
2. Complete with constrained placement.
3. Show clear + scoring explanation.

Definition of done (Pack C):

1. Player demonstrates slice navigation, one W-plane rotation, one hyper-layer clear.

### Sequencing plan (milestones)

M0 Spec + interfaces (planning only):

1. Formalize layer completion definitions in 3D and 4D.
2. Formalize canonical action list (`MoveX+`, `RotatePlaneXY`, `SliceW+`, etc.).
3. Define tutorial schema v1.

Acceptance:

1. One source of truth for actions + clearing definitions.

Stop condition:

1. Schema + action list reviewed once; no feature creep.

M1 Tutorial core engine:

1. Implement `TutorialManager`.
2. Implement condition evaluation.
3. Implement input gating at dispatch layer.
4. Implement persistence (last completed lesson + resume flag).

Acceptance:

1. Dummy three-step lesson advances deterministically and gating works.

Stop condition:

1. No UI polish beyond minimal debug text.

M2 Overlay UI + highlight system:

1. Instruction panel + key prompts from keybind config.
2. Render highlight descriptors.
3. Implement skip/restart lesson controls.

Acceptance:

1. Any step can render text + highlight + prompts without game-logic changes.

Stop condition:

1. No animation polish beyond basic clarity.

M3 Content Pack A (2D):

1. Author lesson content files.
2. Add deterministic line-clear presets.
3. Add lesson-file validation tests.

Acceptance:

1. Pack A completes end-to-end with no dead steps.

M4 Content Pack B (3D):

1. Author measurable camera steps.
2. Author movement + rotation steps with gating.
3. Add 3D plane-clear preset.

Acceptance:

1. Pack B stable across different keybinds.

M5 Content Pack C (4D):

1. Author slice-navigation steps.
2. Author rotation-plane selection steps with explicit events.
3. Add hyper-layer clear preset.

Acceptance:

1. Pack C stable end-to-end without accidental-behavior dependency.

M6 QA + regression harness:

1. Add tutorial replay mode (scripted inputs -> assert transitions).
2. Add static validation (schema, key prompt coverage, highlight coverage).
3. Add runtime tutorial event log export (last 200 events).

Acceptance:

1. Tutorial packs pass automated replay for at least one canonical keymap.

### File/module layout (recommended)

1. `tutorial/`
   `manager.py`
   `schema.py`
   `conditions.py`
   `gating.py`
   `events.py`
2. `tutorial/content/`
   `2d_pack.yaml`
   `3d_pack.yaml`
   `4d_pack.yaml`
3. `ui/tutorial_overlay.*`
4. `tests/tutorial/`
   `test_schema_validation.py`
   `test_step_transitions.py`

### Global acceptance criteria (release gate)

1. Tutorials work in 2D/3D/4D without per-pack code changes.
2. Every step defines completion conditions, gating set, and visible instruction.
3. No softlocks: skip and restart always recover to known state.
4. Deterministic clear presets for line/plane/hyper-layer lessons.

### Global stop conditions (anti-scope-creep)

1. Do not expand into advanced strategy coaching.
2. Do not add new control schemes; reflect existing actions only.
3. Do not add cinematic tutorial sequences; keep interactive and fast.

## 5. Change Footprint (Current Batch)

Current sub-batch (2026-03-10): explorer playground experiment packs and recommendation loop.

- Added `src/tet4d/engine/runtime/topology_explorer_experiments.py` plus `state/topology/explorer_experiments.json` path support so the current draft and preset family can be compiled/exported as one comparison batch.
- Wired the Explorer Playground controls/action ribbon to build that experiment pack from the current draft, keep it scoped to the live board dimensions, and surface the recommended next topology directly in the preview panel.
- Added focused regression coverage in `tests/unit/engine/test_topology_explorer_experiments.py` and `tests/unit/engine/test_topology_lab_experiments.py`, alongside focused project-config and preview checks.

Current sub-batch (2026-03-07): drift prevention and generated hotspot enforcement.

- Added `config/project/policy/manifests/drift_protection.json` as the canonical drift-protection manifest for live hotspot scans, thin-wrapper LOC budgets, and tutorial copy taxonomy checks.
- Added `tools/governance/check_drift_protection.py` and wired it into `scripts/verify.sh` so wrapper growth and tutorial wording drift fail the local gate before docs drift silently.
- Extended `tools/governance/generate_maintenance_docs.py` so `CURRENT_STATE.md` now generates a `Live Drift Watch` section from live code metrics instead of hand-maintaining hotspot lists.
- Updated governance docs/contracts to treat the generated hotspot section and thin-wrapper budgets as enforced maintenance surfaces.
- Fixed the recurring GitHub-only CI failure mode where new shell entrypoints could be committed from Windows without `100755` mode by restoring the executable bit on `scripts/check_editable_install.sh` and teaching `scripts/check_git_sanitation_repo.sh` to enforce executable bits for all direct-run shell entrypoints in git metadata.

Current sub-batch (2026-03-08): explorer topology engine Phase 1 kernel.

- Added `src/tet4d/engine/topology_explorer/` as the canonical engine-owned explorer topology package for general boundary gluing descriptors, signed-permutation tangent transforms, boundary-crossing mapping, movement-graph compilation, and basic quotient-topology presets.
- Added focused kernel regression coverage in `tests/unit/engine/test_topology_explorer.py` for transform inversion, duplicate-boundary rejection, discrete bijection failure, torus-style wrapping, Mobius-style twisting, and graph compilation.
- Documented the staged rollout and explicit non-goals in `docs/history/topology_playground/explorer_topology_phase1.md` and updated `docs/plans/cleanup_master_plan.md` so the live runtime remains on the existing per-edge explorer topology path until a later integration batch proves parity.
- Validation:
  - focused `ruff check` passed
  - focused pytest (`test_topology_explorer.py`) passed

Current sub-batch (2026-03-08): mode-aware Topology Lab split for normal vs explorer rules.

- Split topology profile ownership for advanced 3D/4D play into `normal` and `explorer` stores in `src/tet4d/engine/runtime/topology_profile_store.py`, keyed by gameplay mode and dimension instead of one shared profile bucket per dimension.
- Extended `src/tet4d/engine/gameplay/topology_designer.py` with gameplay-mode normalization and hard validation rules so Normal Game rejects any seam touching gravity-axis `Y` boundaries while Explorer Mode allows them.
- Reworked `src/tet4d/ui/pygame/launch/topology_lab_menu.py` and `config/topology/lab_menu.json` so Topology Lab now edits a `(game type, dimension)` profile pair, locks `Y` edges in Normal Game, and clearly explains the rule difference in UI copy.
- Added explorer-only `move_up` / `move_down` bindings and routing across 2D/3D/4D exploration, updated help/control maps to those canonical action ids, and removed stale 3D/4D setup rows for `topology_profile_index` so advanced topology selection is isolated to the lab/store path.
- Added regression coverage for mode-aware topology validation, lab locking behavior, separate profile save/load, ND explorer routing, and mode-specific topology profile application in ND setup.
- Validation:
  - focused `ruff check` passed
  - focused pytest (`test_topology_profile_store.py`, `test_topology_designer.py`, `test_topology_lab_menu.py`, `test_keybindings.py`, `test_front3d_setup.py`, `test_gameplay_replay.py`, `test_nd_routing.py`, `test_menu_policy.py`) passed

Current sub-batch (2026-03-07): smaller 4D tutorial/exploration boards, clearer tutorial copy, and larger 4D piece sets.

- Reduced the fixed 4D tutorial board profile in `config/tutorial/lessons.json` to `8 x 20 x 7 x 6`, preserving explicit tutorial-only sizing independent from normal 4D setup settings.
- Reduced the fixed 4D exploration board profile in `src/tet4d/engine/gameplay/exploration_mode.py` to `8 x 9 x 7 x 6` so 4D exploration stays compact and readable.
- Simplified tutorial overlay instruction wording to one plain-language `Do this:` line, one optional `Tip:` line, and `USE:` prompts, and rewrote 4D lesson text for clearer layman guidance.
- Added larger dedicated 4D piece-set options (`True 4D (7-cell)`, `True 4D (8-cell)`) in `config/gameplay/piece_sets_nd.json` and `src/tet4d/engine/gameplay/pieces_nd.py`, with regression coverage in `tests/unit/engine/test_pieces_nd.py`.
- Validation:
  - focused `ruff check` passed
  - focused pytest slice covering tutorial overlay/content/schema/setup, 4D render/setup, and ND piece sets passed

Current sub-batch (2026-03-07): cleanup ledger + remaining owner cleanup.

- Added `docs/plans/cleanup_master_plan.md` as the canonical ledger for the remaining cleanup program, with stage/domain ownership status taken from live code rather than older manifests.
- Narrowed `src/tet4d/engine/api.py` so it no longer re-exports raw piece-transform helpers; transform tests now import `src/tet4d/engine/core/piece_transform.py` directly.
- Extracted shared gameplay orchestration into `src/tet4d/engine/gameplay/lock_flow.py` (lock-analysis / score-bookkeeping) and `src/tet4d/engine/core/rules/lifecycle.py` (lock-and-respawn / hard-drop flow), then rewired `src/tet4d/engine/gameplay/game2d.py`, `src/tet4d/engine/gameplay/game_nd.py`, `src/tet4d/engine/core/rules/gravity_2d.py`, and `src/tet4d/engine/core/step/reducer.py` to use those shared owners.
- Moved keybinding path/profile/json ownership into `src/tet4d/engine/runtime/keybinding_store.py`, leaving `src/tet4d/ui/pygame/keybindings.py` with runtime binding maps, conflict handling, and presentation-facing helpers only.
- Removed the stale `requirements.txt` install authority, updated `README.md` to the editable-install-only contract, and added `scripts/check_editable_install.sh` to the local verification gate.
- Further reduced `src/tet4d/engine/runtime/menu_structure_schema.py` by moving menu graph parsing into `src/tet4d/engine/runtime/menu_structure/menu_parse.py` and settings/payload parsing into `src/tet4d/engine/runtime/menu_structure/settings_parse.py`, leaving `menu_structure_schema.py` as the stable validation facade consumed by `menu_config.py`.
- Validation:
  - focused `ruff check` passed
  - focused pytest (`test_piece_transform.py`, `test_keybindings.py`, `test_game2d.py`, `test_game_nd.py`, `test_lifecycle_rules.py`) passed
  - additional focused pytest (`test_menu_policy.py`, `test_menu_graph_linter.py`, `test_front_launcher_routes.py`, `test_help_text.py`) passed
  - full `CODEX_MODE=1 ./scripts/verify.sh` passed
  - full `CODEX_MODE=1 ./scripts/ci_check.sh` passed

Current sub-batch (2026-03-07): maintenance-doc generation for architecture handoff.

- Added `tools/governance/generate_maintenance_docs.py` to generate the marker-backed sections in `CURRENT_STATE.md` and `docs/PROJECT_STRUCTURE.md` from canonical architecture metrics and owner lists.
- Converted both maintenance docs to mixed manual/generated templates so ownership snapshots, metric snapshots, entry-point inventories, and verification-contract sections are checked mechanically instead of hand-maintained.
- Added a dedicated governance regression test for stale maintenance-doc detection and wired the new `--check` path into `scripts/verify.sh` and the canonical-maintenance contract.

Current sub-batch (2026-03-07): settings/analytics correctness hotfix.

- Fixed the shared settings hub to seed `analytics.score_logging_enabled` from persisted runtime settings instead of source-controlled defaults, so preview and unsaved restore reflect the actual saved value.
- Hardened `score_analysis_summary_snapshot()` to return detached copies instead of shallow top-level copies that leaked nested cached state.
- Deleted the unused `dispatch_nd_gameplay_key()` helper from `src/tet4d/ui/pygame/frontend_nd_input.py` to keep the ND input surface aligned with the post-split ownership model.
- Added focused regression coverage for persisted analytics initialization/reset-default behavior and score-summary snapshot isolation.

Current sub-batch (2026-03-07): verification/state isolation hardening.

- Added a canonical `TET4D_STATE_ROOT` override path in `src/tet4d/engine/runtime/project_config.py` so runtime state helpers can resolve menu settings, tutorial progress, analytics, and leaderboard outputs under an isolated project-local state root.
- Hardened `scripts/verify.sh` with a serialized full-gate lock, per-run isolated state root, repo-local step logs, and local policy/sanitation checks (`check_policy_compliance.sh`, `check_policy_compliance_repo.sh`, `check_git_sanitation_repo.sh`) so local verification matches CI formatting/path checks and avoids GNU/BSD `mktemp` drift.
- Repointed pytest temp handling and repo-local unittest helpers to the canonical state root instead of hardcoded `Path.cwd()/state/pytest_temp` paths.
- Ignored the recurring `.tmp_pytest_contracts/` local artifact to reduce git-status noise from inaccessible temp directories.

Current sub-batch (2026-03-07): Stage 0-5 architecture completion and lower-layer cleanup.

- Sealed the restructuring baseline in a dedicated checkpoint commit before the final deletion-heavy stages.
- Finished 2D runtime decomposition and deleted `src/tet4d/ui/pygame/front2d_runtime.py` by splitting ownership across:
  - `src/tet4d/ui/pygame/front2d_loop.py` (orchestration)
  - `src/tet4d/ui/pygame/front2d_session.py` (session/state)
  - `src/tet4d/ui/pygame/front2d_frame.py` (per-frame/update)
  - `src/tet4d/ui/pygame/front2d_results.py` (results/leaderboard)
- Finished ND frontend decomposition and deleted `src/tet4d/ui/pygame/frontend_nd.py` by splitting ownership across:
  - `src/tet4d/ui/pygame/frontend_nd_setup.py` (setup/menu/config)
  - `src/tet4d/ui/pygame/frontend_nd_state.py` (state creation)
  - `src/tet4d/ui/pygame/frontend_nd_input.py` (gameplay/input routing)
- Finished settings-hub decomposition and deleted `src/tet4d/ui/pygame/launch/settings_hub_state.py` by splitting ownership across:
  - `src/tet4d/ui/pygame/launch/settings_hub_model.py` (model/layout/defaults)
  - `src/tet4d/ui/pygame/launch/settings_hub_actions.py` (mutation/text-entry/save/reset)
  - `src/tet4d/ui/pygame/launch/launcher_settings.py` (orchestration/view)
- Split large engine-runtime helpers into stable facades plus smaller subpackage owners:
  - `src/tet4d/engine/runtime/menu_settings_state.py` over `runtime/menu_settings/`
  - `src/tet4d/engine/runtime/menu_structure_schema.py` over `runtime/menu_structure/`
  - `src/tet4d/engine/runtime/score_analyzer.py` over `runtime/score_analysis/`
- Updated policy/runtime manifests, architecture docs, RDS docs, generated config references, and package metadata to the deleted-facade-free owner graph.
- Kept the one-way contract intact throughout the batch:
  - `engine_to_ui_non_api = 0`
  - `engine_to_ai_non_api = 0`
  - `engine_core_purity.violation_count = 0`
  - `pygame_imports_non_test = 0`

Current sub-batch (2026-03-05): center-of-piece rotation semantic swap.

- Switched canonical block rotation semantics in `src/tet4d/engine/core/piece_transform.py` from origin-style pivot turns to active-bounding-box center rotation for occupied cells.
- Odd active-plane spans rotate around the center cell; even spans rotate around the between-cells axis/plane with deterministic local re-anchoring.
- Rewired remaining gameplay state holders to use block-rotation helpers instead of pointwise pivot-style math:
  - `src/tet4d/engine/gameplay/pieces2d.py`
  - `src/tet4d/engine/gameplay/pieces_nd.py`
- Updated transform, piece, and RDS coverage to describe the new local occupied-cell semantics and even-span rotation behavior.

Current sub-batch (2026-03-06): topology-aware kick-system implementation.

- Implemented canonical rotation-kick candidate generation and first-fit resolution in `src/tet4d/engine/core/rotation_kicks.py`.
- Rewired 2D/ND gameplay rotation to consume the shared resolver while keeping topology-aware legality checks authoritative for acceptance.
- Added shared `kick_level` runtime/config support:
  - persisted in shared advanced gameplay settings
  - exposed in launcher advanced gameplay menu
  - folded into assist score multiplier
  - serialized in replay and leaderboard metadata while leaving leaderboard ordering unchanged
- Added topology-aware regression coverage for bounded, wrap, and invert rotation acceptance paths in 2D/4D plus replay, leaderboard, settings, and assist-scoring coverage.
- Synced help/RDS/project-structure/current-state docs to the implemented kick system.
- Stabilized the playbot benchmark gate after the kick batch by:
  - applying deadline-safety margin during ND candidate enumeration
  - warming benchmark runs and disabling cyclic GC during timed samples
  - switching benchmark p95 to nearest-rank percentile for 40-sample stability
- Fixed GitHub scheduled stability-watch bootstrap drift by switching `.github/workflows/stability-watch.yml` to editable install (`pip install -e .[dev]`) for both the dry-run matrix and policy-analysis jobs so the `src/` layout imports resolve consistently with `ci.yml` and local `verify.sh`.

Current sub-batch (2026-03-06): release-installer hardening for `0.4`.

- Advanced the project version in `pyproject.toml` from `0.3` to `0.4`.
- Reworked local packaging outputs from archive bundles to installer artifacts:
  - Windows: `.msi`
  - macOS x64/arm64: `.dmg`
  - Linux AMD64: `.deb`
- Updated `.github/workflows/release-packaging.yml` to build the full installer matrix and publish tag-triggered assets to the matching GitHub release.
- Synced packaging/release docs and RDS for the installer-based release contract:
  - `README.md`
  - `docs/RELEASE_INSTALLERS.md`
  - `docs/RELEASE_CHECKLIST.md`
  - `docs/rds/RDS_PACKAGING.md`
  - `docs/CHANGELOG.md`

Current sub-batch (2026-03-05): canonical piece-transform extraction (no behavior change).

- Added pure canonical piece-local transform owner:
  - `src/tet4d/engine/core/piece_transform.py`
- Moved current local rotation, normalization, block-bounds, canonicalization,
  and ND orientation-enumeration math into engine core without changing
  current integer/floor-centered semantics.
- Rewired gameplay, AI, tutorial setup, rotation animation, and `engine.api`
  wrappers to consume the shared core owner instead of duplicating transform math:
  - `src/tet4d/engine/gameplay/pieces2d.py`
  - `src/tet4d/engine/gameplay/pieces_nd.py`
  - `src/tet4d/engine/gameplay/rotation_anim.py`
  - `src/tet4d/engine/tutorial/setup_apply.py`
  - `src/tet4d/ai/playbot/planner_2d.py`
  - `src/tet4d/ai/playbot/planner_nd_core.py`
  - `src/tet4d/ai/playbot/controller.py`
  - `src/tet4d/engine/api.py`
- Added transform-equivalence regression coverage:
  - `tests/unit/engine/test_piece_transform.py`
- Added retrospective extraction/inventory docs for the completed canonical transform migration:
  - `docs/plans/piece_transform_extraction.md`
  - `docs/plans/piece_transform_inventory.md`

Current sub-batch (2026-03-05): menu navigation key policy split (`Esc` vs `Q`).

- Menu navigation normalization no longer aliases `Q` to `Esc`; tiny-profile
  `I/K/J/L` aliases remain unchanged.
- Shared menu graph runner now treats:
  - `Esc/Backspace` as return/back within menu stack
  - `Q` as exit from the current menu flow
- Updated custom menu handlers (settings, bot options, keybindings, help,
  leaderboard, topology lab, setup controls) to enforce `Q` exit explicitly.
- Updated launcher/settings/menu copy strings from `Esc/Q` coupling to explicit
  `Esc back` + `Q quit` wording.
- Updated menu-navigation regression tests:
  - `tests/unit/engine/test_menu_navigation_keys.py`
- Fixed tutorial pause-menu regression where `Esc` stopped resuming and `Q`
  resumed instead; now:
  - `Esc` resumes/returns from pause (including tutorial `menu_back` callback)
  - `Q` exits pause flow (`quit`)
- Added runner-level regression guard so `Q` dispatches quit-handler semantics
  (not root-escape fallback):
  - `tests/unit/engine/test_menu_runner.py`

Current sub-batch (2026-03-05): tutorial overlay readability/placement polish.

- Tutorial key prompts now render staged keys as blue keycap chips while
  keeping action text separate for scanability:
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Removed tutorial overlay `ACTION:` label and removed `System (not staged)`
  helper line from tutorial panel output.
- Added tutorial-overlay short labels for system actions in key prompts:
  - `help -> HELP`
  - `menu -> pause MENU`
  - `restart -> restart`
  - `quit/menu_back -> main menu`
- Moved default 3D/4D tutorial overlay placement into the right-side panel lane, outside the active board/layers area, and clamp tutorial-panel dragging to that safe lane.
- Added/updated overlay tests for:
  - key prompt parsing and short-label behavior
  - 2D/3D/4D render-bounds/layout stability after keychip rendering
  - files:
    - `tests/unit/engine/test_tutorial_overlay.py`
    - `tests/unit/engine/test_tutorial_overlay_layout.py`

Current sub-batch (2026-03-05): tutorials launcher parity with shared main-menu renderer.

- Replaced launcher root `Tutorials` route with a real submenu in menu graph:
  - `launcher_tutorials` now contains `Play 2D Tutorial`, `Play 3D Tutorial`,
    `Play 4D Tutorial` actions.
  - file: `config/menu/structure.json`
- Removed launcher special-case tutorials route flow and moved tutorial launching
  to standard action handlers (`tutorial_2d/3d/4d`) in shared `MenuRunner` flow:
  - file: `cli/front.py`
- Relaxed menu structure parser contract so `launcher_route_actions` may be empty
  when no launcher routes exist:
  - file: `src/tet4d/engine/runtime/menu_structure_schema.py`
- Updated launcher route tests for direct tutorial action launch path:
  - file: `tests/unit/engine/test_front_launcher_routes.py`
- Removed obsolete standalone launcher tutorial screen (dead code after submenu unification):
  - file removed: `src/tet4d/ui/pygame/launch/tutorials_menu.py`
- Synced structure docs to remove stale standalone tutorial-menu references:
  - `docs/PROJECT_STRUCTURE.md`

Current sub-batch (2026-03-04): tiny keyboard profile (no-arrow defaults).

- Added built-in `tiny` keybinding profile for compact keyboards without arrow keys:
  - movement cluster on letter keys (`J/L`, `I/K`, `U/O`) with shift-based soft drop
  - 4D W-axis movement on `,`/`.`
  - no-keypad advanced 4D camera fallback (`-`, `=`, `P`, `Backspace`)
  - files:
    - `config/keybindings/defaults.json`
    - `src/tet4d/ui/pygame/keybindings.py`
    - `tests/unit/engine/test_keybindings.py`
- Updated keybinding RDS profile model docs:
  - `docs/rds/RDS_KEYBINDINGS.md`
Current sub-batch (2026-03-04): CI compliance hardening + governance preflight.

- Stabilized sanitation inputs for local/context artifacts:
  - `.gitignore` now ignores `context-*.instructions.md`
  - `scripts/check_git_sanitation_repo.sh` now excludes `context-*.instructions.md`
  - local `.claude/` worktree sandboxes and VCS metadata `.git` files are excluded from repo-content absolute-path scanning
- Added single-command CI preflight:
  - `scripts/ci_preflight.sh`
  - runs sanitation/policy checks + canonical `ci_check` pipeline.
- Added policy-manifest literal safety validation to catch string literals that
  can accidentally trigger absolute-path sanitation gates:
  - `tools/governance/validate_project_contracts.py`
  - `tests/unit/governance/test_governance_validate_project_contracts.py`
- Tuned wheel-reuse rule scopes to reduce low-signal noise while keeping
  high-risk runtime/UI/governance coverage:
  - `config/project/policy/manifests/wheel_reuse_rules.json`
- Added CI compliance runbook and wired it into canonical governance docs:
  - `docs/policies/CI_COMPLIANCE_RUNBOOK.md`
  - `docs/policies/INDEX.md`
  - `docs/RDS_AND_CODEX.md`
  - `CONTRIBUTING.md`
- Synced canonical maintenance contract for new script/doc tokens:
  - `config/project/policy/manifests/canonical_maintenance.json`

Tuned next-batch priorities:
1. CI compliance maintenance first (preflight + runbook triage discipline).
2. Tutorial stability closure for 4D/W-axis and step-transition edge-cases.
3. LOC-focused non-behavioral dedup in runtime/UI hotspots.

Current sub-batch (2026-03-04): directive-manifest normalization.

- Added canonical contributor directives manifest:
  - `config/project/policy/manifests/contributor_directives.json`
- Registered contributor directives in policy pack and policy contract map:
  - `config/project/policy/pack.json`
  - `config/project/policy/manifests/project_policy.json`
- Added contributor directives manifest to canonical maintenance required governance files:
  - `config/project/policy/manifests/canonical_maintenance.json`
- Added explicit validation for contributor directive manifest schema/IDs/content:
  - `tools/governance/validate_project_contracts.py`
- Synced instruction docs to reference the canonical contributor directives manifest:
  - `AGENTS.md`
  - `docs/RDS_AND_CODEX.md`
- Follow-up LOC reduction pass:
  - reduced duplicate governance bullets in `AGENTS.md` by deferring to manifest/policy sources
  - reduced contributor-manifest overlap with policy docs (process-only directives retained)
  - collapsed contributor-directive validation helpers into compact validation flow
  - added risk-gates manifest + checker coverage for CI-enforced directives,
    dependency policy (`pip check` + blocked dependency list), and sensitive-file
    ownership thresholds:
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
    - `scripts/verify.sh`
  - added policy-index drift enforcement so `docs/policies/INDEX.md` must stay in
    sync with policy IDs and contract paths declared in
    `config/project/policy/manifests/project_policy.json`:
    - `tools/governance/validate_project_contracts.py`
    - `config/project/policy/manifests/canonical_maintenance.json`
    - `docs/policies/INDEX.md`
  - added menu-simplification manifest enforcement:
    - validates that shared gameplay controls (`game_seed`,
      `game_random_mode`, `game_topology_advanced`, `gameplay_advanced`) are
      present in `settings_hub_layout_rows` and not duplicated in
      per-dimension `setup_fields`.
    - `tools/governance/validate_project_contracts.py`
  - hardened risk-gates security/dependency posture:
    - blocked dependency denylist now includes `pycrypto` and `python-jose`
    - security ownership scope is no longer no-op; it now requires a minimum
      matched sensitive-file set (`min_sensitive_files`) before pass.
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
  - added runtime policy checker for two previously review-only policies:
    - string sanitation checks on text-entrypoint modules
    - no-magic-number checks for config-backed settings controls
    - `config/project/policy/manifests/policy_runtime_rules.json`
    - `tools/governance/check_policy_runtime_rules.py`
    - `scripts/verify.sh`
  - generalized no-reinventing-wheel enforcement:
    - new manifest-driven reuse rules that detect ad-hoc replacement code for
      stdlib/repo helpers and require explicit `Wheel Exception:` markers when
      deviations are intentional.
    - rules are now category-based (parsing/validation, normalization, path/config,
      algorithm utilities) rather than a bool-parser-specific example.
    - `config/project/policy/manifests/wheel_reuse_rules.json`
    - `tools/governance/check_wheel_reuse_rules.py`
  - converted LOC reduction into soft non-blocking guidance:
    - warning-only per-bucket LOC pressure report (batch-type aware), wired into
    verify for visibility without blocking important work.
    - `config/project/policy/manifests/loc_guidance.json`
    - `tools/governance/check_loc_guidance.py`
  - added dedup/dead-code contract gate:
    - legacy path reintroduction checks
    - TODO/FIXME backlog-ID linkage checks
    - duplicate governance helper-body detection in scoped paths
    - `config/project/policy/manifests/dedup_dead_code_rules.json`
    - `tools/governance/check_dedup_dead_code_rules.py`
  - upgraded security ownership to phased strictness:
    - keep blocking threshold at `min_distinct_authors_per_file`
    - add non-blocking warning target (`target_min_distinct_authors_per_file`)
      for gradual bus-factor improvement without CI breakage.
    - `config/project/policy/manifests/risk_gates.json`
    - `tools/governance/check_risk_gates.py`
  - extended wheel-reuse checker with AST-assisted detectors (not regex-only)
    for common reinvention patterns (`custom_bool_parser`,
    `custom_numeric_text_parser`, `custom_clamp_helper`).

Current sub-batch (2026-03-04): governance-doc cleanup and directive dedup.

- Replaced oversized duplicated instruction content in `docs/RDS_AND_CODEX.md`
  with a compact canonical workflow that references policy manifests, policy docs,
  RDS specs, and checkpoint docs (`CURRENT_STATE.md`, `docs/BACKLOG.md`).
- Removed historical stage-by-stage migration directives from `docs/RDS_AND_CODEX.md`
  and set explicit scope boundary: stage history belongs in this backlog + current-state handoff.
- Preserved required contract anchors (`RDS index`, `Testing instructions`,
  `docs/BACKLOG.md`, `docs/rds/RDS_PACKAGING.md`) while reducing duplicate policy text.

Current sub-batch (2026-03-04): tutorial timing regression coverage + runtime dedup.

- Added tutorial runtime regression coverage for two active risks:
  - configured stage-delay gating enforcement before transition
  - ordered 4D W-axis stage progression (`move_w_neg` -> `move_w_pos`)
  - `tests/unit/engine/test_tutorial_runtime.py`
- Reduced duplicated runtime settings persistence/update plumbing by introducing
  a shared section saver in:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
- Reduced API/keybindings wrapper duplication with proxy/alias consolidation in:
  - `src/tet4d/engine/api.py`
  - `src/tet4d/ui/pygame/keybindings.py`
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_content.py` passed.
  - `.venv/bin/pytest -q tests/unit/engine/test_keybindings.py tests/unit/engine/test_engine_api_determinism.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): ND control-stage continuity sequence lock.

- Reordered 3D/4D tutorial lesson packs so the control stage sequence is:
  translations -> piece rotations -> camera rotations -> grid/zoom/reset ->
  transparency.
- Extended runtime setup suppression to treat camera rotations/controls and
  transparency as continuous control steps, preserving board/piece state across
  those transitions and preventing redraw between control stages.
- Added regression coverage for 3D/4D sequence continuity through `toggle_grid`
  with no board-reset setup payloads injected between adjacent stages:
  - `tests/unit/engine/test_tutorial_runtime.py`
- Hardened runtime test helper behavior to derive overlay targets and required
  action repeat counts from lesson step definitions (no stale hardcoded values).
- Fixed opening 3D/4D translation-stage anchor drift that could trigger
  early safety-redo redraws after stages 1-2:
  - opening setup now repositions to a deterministic near-corner candidate that
    satisfies the full translation chain before rotations/camera stages
    (`x-/x+`, `z away/closer`, plus `w-/w+` in 4D).
  - regression assertions now match canonical viewer-relative semantics for the
    translation order and axis direction.
  - `src/tet4d/engine/tutorial/setup_apply.py`
  - `tests/unit/engine/test_tutorial_setup_apply.py`
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_nd_routing.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): tutorial control sequencing hardening.

- Added deterministic tutorial sequencing coverage for restart/redo/previous/next
  controls across all lesson modes (2D/3D/4D):
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added repeated 4D W-axis progression smoke across lesson restarts to guard
  against recurrence of W-stage stalls:
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added nonzero stage-delay regression coverage (`1500ms`) to ensure no
  premature transitions:
  - `tests/unit/engine/test_tutorial_runtime.py`
- Added live system-control keybinding prompt sync coverage in tutorial overlay:
  - `tests/unit/engine/test_tutorial_overlay.py`
- Reduced duplicate profile and per-mode update plumbing in:
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/runtime/menu_settings_state.py`
- Fixed tutorial soft-drop responsiveness by splitting drop pacing into
  separate config-backed delays (fast soft-drop, slower hard-drop):
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_overlay.py` passed.
  - `.venv/bin/pytest -q tests/unit/engine/test_keybindings.py tests/unit/engine/test_menu_policy.py tests/unit/engine/test_runtime_config.py` passed.
  - `.venv/bin/pytest -q tests/unit/engine/test_project_config.py` passed.
  - `.venv/bin/ruff check cli/front2d.py src/tet4d/ui/pygame/front3d_game.py src/tet4d/ui/pygame/front4d_game.py src/tet4d/engine/runtime/project_config.py tests/unit/engine/test_project_config.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.
  - `./scripts/ci_preflight.sh` passed (known non-blocking local warnings unchanged).

Current sub-batch (2026-03-04): tutorial stage solvability + grid/transparency alignment.

- Aligned grid tutorial steps to explicitly cover all display modes with required
  full cycle progression:
  - `OFF -> EDGE -> FULL -> HELPER -> OFF`
  - `event_count_required = 4` on `toggle_grid` steps (2D/3D/4D).
- Hardened step transition setup rules in tutorial runtime:
  - board/piece setup is preserved between translation/rotation/drop stages
    (no redraw/reset between those stages),
  - leaving transparency stages now resets overlay transparency to `50%`.
- Improved deterministic tutorial piece placement for movement-stage completion:
  - translation starts one cell off boundary and validates repeated legal moves
    for required event counts,
  - ND spawn bias updated so sequential axis movement can reach edge targets
    reliably.
- Tightened goal-stage setup for line/layer/full-clear tasks:
  - goal piece now starts laterally away from target holes and at configured
    gravity distance so move/rotate is required before hard drop.
- Verification:
  - `.venv/bin/python -m ruff check src/tet4d/engine/tutorial/setup_apply.py` passed.
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_content.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): ND translation feasibility near-corner enforcement.

- Tutorial ND translation spawn now prefers one-cell-off-boundary for non-active
  lateral axes too (near corner, not hard-boundary corner) so stage starts are
  spatially consistent.
- Increased tutorial minimum board clamps for ND lessons to preserve feasibility
  of four-step translation stages with asymmetric pieces:
  - 3D min dims: `x=8`, `y=18`, `z=8`
  - 4D min dims: `x=10`, `y=20`, `z=8`, `w=8`
- Added regression assertions for sequential translation feasibility under real
  lesson setup values and continuity to rotation stages:
  - `tests/unit/engine/test_tutorial_setup_apply.py`
  - `tests/unit/engine/test_tutorial_runtime.py`
- Verification:
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_project_config.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): ND tutorial translation continuity redraw fix.

- Fixed mid-stage tutorial redraw/regression trigger in 3D/4D loops:
  tutorial safety checks now skip auto-redo when a stage is already complete and
  waiting for configured transition delay.
- Added explicit runtime API/session support for transition-pending checks:
  - `transition_pending()` on tutorial runtime session
  - `tutorial_runtime_transition_pending_runtime(...)` API wrapper.
- Aligned 3D/4D tutorial required-action feasibility checks with actual
  viewer-relative input routing and view-axis override logic:
  - added `can_apply_nd_gameplay_action_with_view(...)` in
    `src/tet4d/engine/frontend_nd.py`
  - tutorial safety in `front3d_game.py` / `front4d_game.py` now uses this
    canonical legality path.
- Synced ND tutorial min-board fallback defaults in gameplay loops with updated
  constants for translation feasibility:
  - 3D default clamp fallback `x/z`: `8`
  - 4D default clamp fallback `z/w`: `8`
- Verification:
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_nd_routing.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): ND tutorial Step-3 feasibility alignment.

- Fixed setup-positioning drift for ND translation steps by aligning tutorial
  required move deltas with default viewer-relative control semantics:
  - `move_z_neg` => away (`+z`)
  - `move_z_pos` => closer (`-z`)
  - implemented in `src/tet4d/engine/tutorial/setup_apply.py`.
- Hardened tutorial safety skip condition to avoid pre-sync stage redo:
  - skip safety redo while current step is already completion-ready
    (`completion_ready`) or transition-pending.
- Added regression coverage:
  - runtime completion-ready signal behavior during stage-delay windows
  - ND `move_z_neg` setup feasibility for 3D/4D (four away moves possible)
  - `tests/unit/engine/test_tutorial_runtime.py`
  - `tests/unit/engine/test_tutorial_setup_apply.py`
- Verification:
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_nd_routing.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-03): scoring clear-size weighting (square-root).

- Added config-backed clear-size weighting so larger cleared layers award higher
  clear points with square-root scaling (`sqrt(layer_size/reference)`, floor `1.0`):
  - `config/gameplay/tuning.json` (`clear_scoring.layer_size_weighting`)
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
  - `src/tet4d/engine/runtime/runtime_config.py`
  - `src/tet4d/engine/gameplay/scoring_bonus.py`
  - `src/tet4d/engine/gameplay/game2d.py`
  - `src/tet4d/engine/gameplay/game_nd.py`
- Added regression coverage and runtime-config assertions:
  - `tests/unit/engine/test_scoring_bonus.py`
  - `tests/unit/engine/test_runtime_config.py`
- Updated scoring help text to reflect clear-size weighting:
  - `config/help/content/runtime_help_content.json`
  - `docs/rds/RDS_TETRIS_GENERAL.md`

Current sub-batch (2026-03-02): interactive tutorial runtime integration (M2-M6 baseline).

- Added tutorial runtime state layer with deterministic progression hooks and
  persistence of started/completed lessons:
  - `src/tet4d/engine/tutorial/runtime.py`
  - `src/tet4d/engine/tutorial/persistence.py`
  - `config/project/io_paths.json` (`tutorial_progress_file_default`)
  - `src/tet4d/engine/runtime/project_config.py`
- Extended API surface to expose tutorial runtime session helpers to UI loops:
  - `src/tet4d/engine/api.py`
- Added launcher tutorial selector and wired Play -> Tutorials route to launch
  guided runs for 2D/3D/4D:
  - `src/tet4d/ui/pygame/launch/tutorials_menu.py` (historical; removed in 2026-03-05 after launcher submenu unification)
  - `cli/front.py`
  - `src/tet4d/ui/pygame/launch/launcher_play.py`
- Integrated tutorial gating/event observation/step progression into gameplay loops:
  - `cli/front2d.py`
  - `src/tet4d/engine/frontend_nd.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Added tutorial in-game overlay renderer (instruction + key prompts + progress):
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Added canonical non-Python tutorial plan config:
  - `config/tutorial/plan.json`
  - `config/schema/tutorial_plan.schema.json`
  - `src/tet4d/engine/tutorial/content.py` loader/validator + cache
  - `src/tet4d/engine/api.py` runtime accessor (`tutorial_plan_payload_runtime`)
- Tightened runtime tutorial behavior contract:
  - step-pause enforcement now freezes gravity/bot tick while tutorial is running
  - tutorial stages now auto-redo if no currently legal stage action exists
    (prevents dead-end game-over states during gated steps)
  - active tutorial piece visibility is re-enforced at runtime; if visibility
    cannot be restored deterministically, tutorial session restarts
  - tutorial mode uses exact board profiles from `config/tutorial/lessons.json` (2D/3D/4D)
    before session start so tutorial geometry is independent of normal mode settings
  - full-clear bonus stages now use deterministic one-piece board-clear presets:
    - `2d_almost_full_clear_o` + starter `O`
    - `3d_almost_full_clear_o3` + starter `O3`
    - `4d_almost_full_clear_cross4` + starter `CROSS4`
  - gameplay Esc now routes to menu/pause flow instead of instant quit
  - gameplay restart action no longer resets tutorial lesson to step 1
  - leaderboard registration is disabled during tutorial sessions
  - clear-step board presets (`2d_almost_line`, `3d_almost_layer`, `4d_almost_hyper_layer`)
    are applied deterministically
  - tutorial camera presets (`tutorial_3d_default`, `tutorial_4d_default`) are now
    applied by loop adapters
  - pause menu tutorial control is now hotkey-driven (no dedicated
    `tutorial_restart` row in pause menu)
  - tutorial pause/menu copy now exposes explicit tutorial exit wording
    (`Exit Tutorial`)
  - tutorial restart stability hardened:
    - pause-menu restart now emits tutorial `restart` action
    - tutorial `F9` now restarts the tutorial lesson session deterministically
      and reapplies step setup
    - visibility recovery now redoes the current step (instead of restarting the
      full lesson), reducing cross-step instability
  - 3D/4D move+rotate stages now force asymmetric starters (`SCREW3`/`SKEW4_A`)
  - 3D/4D layer-clear presets now use deterministic solvable hole patterns:
    - `3d_almost_layer_screw3`
    - `4d_almost_hyper_layer_skew4`
  - tutorial stage pacing increased (movement/rotation/drop delays) via
    config-backed constants
  - lesson packs now require full movement/rotation/camera action completion per mode
  - tutorial lesson segmentation and ordering were clarified and canonicalized:
    - translations
    - piece rotations
    - camera rotations (3D/4D)
    - camera controls (`toggle_grid`, transparency)
    - goals (target clear, line/layer clear, full board clear)
  - interactive system-control tutorial stages (`menu_button`, `help_button`,
    `restart_button`) were removed; controls are now guidance-only in overlay copy
  - movement and rotation stages now require 4 successful actions per direction
  - full-board clean stages now require `board_cleared` predicate in addition to
    clear-event predicates
  - tutorial overlay panel moved to enlarged ND side-panel docking with clearer
    Segment + Task + KEY/ACTION formatting
  - files:
    - `config/tutorial/lessons.json`
    - `config/project/constants.json`
    - `config/menu/structure.json`
    - `src/tet4d/engine/tutorial/setup_apply.py`
    - `src/tet4d/engine/tutorial/runtime.py`
    - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
    - `src/tet4d/ui/pygame/front3d_game.py`
    - `src/tet4d/ui/pygame/front4d_game.py`
    - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
    - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
    - `cli/front2d.py`
- Added regression coverage for tutorial runtime and new routing callbacks:
  - `tests/unit/engine/test_tutorial_runtime.py`
  - `tests/unit/engine/test_nd_routing.py`
  - `tests/unit/engine/test_front_launcher_routes.py`

Current sub-batch (2026-03-02): interactive tutorial core scaffolding (M0/M1 seed).

- Added canonical tutorial lesson-pack data source:
  - `config/tutorial/lessons.json`
- Added tutorial data schema contract:
  - `config/schema/tutorial_lessons.schema.json`
- Added tutorial core package with deterministic schema parsing, gating, condition
  evaluation, and step-state manager:
  - `src/tet4d/engine/tutorial/schema.py`
  - `src/tet4d/engine/tutorial/content.py`
  - `src/tet4d/engine/tutorial/gating.py`
  - `src/tet4d/engine/tutorial/conditions.py`
  - `src/tet4d/engine/tutorial/events.py`
  - `src/tet4d/engine/tutorial/manager.py`
  - `src/tet4d/engine/tutorial/__init__.py`
- Exposed tutorial content runtime accessors via engine API:
  - `src/tet4d/engine/api.py`
- Added unit coverage for schema validation, manager progression/gating, and
  runtime content loading/API exposure:
  - `tests/unit/engine/test_tutorial_schema.py`
  - `tests/unit/engine/test_tutorial_manager.py`
  - `tests/unit/engine/test_tutorial_content.py`
- Canonical maintenance sync:
  - `config/project/policy/manifests/canonical_maintenance.json`
- RDS/project-structure sync:
  - `docs/rds/RDS_TETRIS_GENERAL.md`
  - `docs/PROJECT_STRUCTURE.md`

Current sub-batch (2026-03-02): runtime parser/validation decomposition continuation.

- Reduced duplicate menu-structure parsing logic by extracting shared helpers to:
  - `src/tet4d/engine/runtime/menu_structure_parse_helpers.py`
- Extracted shared menu-graph traversal/collection helpers to:
  - `src/tet4d/engine/runtime/menu_structure_graph.py`
- Simplified `menu_structure_schema` by removing duplicate local parsers and
  consuming shared helpers for:
  - mode string-list parsing
  - copy-field parsing
  - `ui_copy` section parsing
  - menu reachability/action/route collection
- Reduced `runtime_config.py` validator concentration by extracting gameplay/audio
  payload validation to:
  - `src/tet4d/engine/runtime/runtime_config_validation_gameplay.py`
- Updated `runtime_config.py` to delegate to extracted gameplay/audio validators.
- Verification:
  - `.venv/bin/pytest -q tests/unit/engine/test_menu_policy.py tests/unit/engine/test_runtime_config.py tests/unit/engine/test_project_config.py`
  - `CODEX_MODE=1 ./scripts/verify.sh`

Current sub-batch (2026-03-02): helper-panel runtime stability + cross-mode structure unification.

- Expanded release-packaging CI matrix to publish separate artifacts for:
  Linux, Windows, macOS x64, and macOS ARM64:
  - `.github/workflows/release-packaging.yml`
- Synced packaging docs with the explicit CI target list:
  - `docs/RELEASE_INSTALLERS.md`
- Unified default side-panel width across gameplay dimensions by aligning
  2D `rendering.2d.side_panel` with 3D/4D (`360`) via config-backed constants:
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
  - `src/tet4d/ui/pygame/render/gfx_game.py`
- Fixed side-panel structure drift after gameplay state changes by keeping control
  panel sizing stable and clipping low-priority data separately in:
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Unified helper control-group skeleton for 2D/3D/4D side panels (same panel set
  and order with mode placeholders where controls are unavailable) in:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Enforced canonical runtime panel priority order:
  - `Main` > `Translation` > `Rotation` > `Camera` > `Data`
- Merged former `View/Overlay` actions into `Camera` so control tiers are explicit.
- Kept low-priority runtime lines inside the dedicated titled `Data` panel only.
- Reserved minimum layout space for `Data` so runtime/bot/analysis lines render in
  a boxed panel instead of collapsing under control-area pressure.
- Enforced full rotation helper visibility before lower-priority camera trimming:
  - 3D keeps all 3 rotation pairs.
  - 4D keeps all 6 rotation pairs.
- Canonical helper layout source updated:
  - `config/help/layout/runtime_help_action_layout.json`
- Added regression coverage for unified-structure guarantees:
  - `tests/unit/engine/test_control_ui_helpers.py`

Current sub-batch (2026-03-01): helper-panel unification and priority rendering fix.

- Unified 2D side-panel rendering with the shared panel pipeline used by 3D/4D:
  - `src/tet4d/ui/pygame/render/gfx_panel_2d.py`
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Unified summary/data composition via shared helper used by 2D/3D/4D:
  - `draw_unified_game_side_panel(...)` in `src/tet4d/ui/pygame/render/panel_utils.py`
  - `src/tet4d/engine/front3d_render.py`
  - `src/tet4d/engine/front4d_render.py`
- Simplified helper-panel utility internals by collapsing redundant text-row builders
  and summary-row merge helpers in:
  - `src/tet4d/ui/pygame/render/panel_utils.py`
- Further simplified helper-panel rendering flow to one compact unified path
  (`draw_unified_game_side_panel`) with reduced internal branch/adapter count.
- Merged top summary rows into `Main` as a single panel (title/score/lines/speed + main controls).
- Kept strict priority ordering under constrained height:
  - `Main` > `Translation`/`Rotation` > `Camera` > `View/Overlay` > `Data`.
- Added dedicated titled `Data` panel for tier-5 runtime/bot/analysis lines.
- Updated helper layout tiers and group minima:
  - `config/help/layout/runtime_help_action_layout.json`
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added regression coverage for summary-to-main merge behavior:
  - `tests/unit/engine/test_panel_utils.py`

Current sub-batch (2026-03-01): helper-panel tiering update for gameplay side panels.

- Reordered helper tiers across modes so top panel is consistent:
  - Tier 1: game title + score/lines/speed + `Main`
  - Tier 2: `Translation` + `Rotation`
  - Tier 3: `Camera`
  - Tier 4: `View/Overlay` (`locked-cells alpha`, `projection` where supported)
  - Tier 5: remaining runtime/bot/analysis data lines
- Canonicalized helper section membership/order in:
  - `config/help/layout/runtime_help_action_layout.json`
- Updated side-panel summary labels to use `Lines` in all modes:
  - `src/tet4d/engine/front3d_render.py`
  - `src/tet4d/engine/front4d_render.py`
- Updated helper-group coverage expectations:
  - `tests/unit/engine/test_control_ui_helpers.py`

Current sub-batch (2026-03-01): helper-panel contract unification (config intent + engine feasibility).

- Replaced hardcoded helper-group membership logic with data-driven panels/lines from:
  - `config/help/layout/runtime_help_action_layout.json`
- Added engine contract validation + runtime panel filtering:
  - `src/tet4d/engine/help_text.py`
  - `src/tet4d/engine/api.py`
- Rewired helper rendering to consume engine-provided panel specs while keeping shared rendering style:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added coverage for helper-action layout constraints and capability-based line filtering:
  - `tests/unit/engine/test_help_text.py`
- Design sync:
  - `docs/rds/RDS_MENU_STRUCTURE.md`

Current sub-batch (2026-03-01): leaderboard runtime + scoring-help documentation + helper-panel camera visibility.

- Added persistent cross-mode leaderboard runtime storage and API adapters:
  - `src/tet4d/engine/runtime/leaderboard.py`
  - `src/tet4d/engine/runtime/project_config.py`
  - `src/tet4d/engine/api.py`
  - `config/project/io_paths.json`
  - `config/project/constants.json`
- Added leaderboard UI + launcher/pause routing:
  - `src/tet4d/ui/pygame/launch/leaderboard_menu.py`
  - `cli/front.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
- Added runtime session submission hooks in gameplay loops:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- Added scoring-rule explanations to non-Python help assets:
  - `config/help/topics.json`
  - `config/help/content/runtime_help_content.json`
- Improved 3D/4D in-game helper panel prioritization so camera actions appear before lower-priority groups:
  - `src/tet4d/ui/pygame/render/control_helper.py`
- Added/updated regression coverage:
  - `tests/unit/engine/test_leaderboard.py`
  - `tests/unit/engine/test_menu_policy.py`
  - `tests/unit/engine/test_pause_menu.py`
  - `tests/unit/engine/test_front_launcher_routes.py`
  - `tests/unit/engine/test_control_ui_helpers.py`
  - `tests/unit/engine/test_project_config.py`
- Verification:
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Hotfix (2026-03-01, same batch):
- Leaderboard session capture now records restart outcomes (keyboard restart and pause-menu restart) for 2D/3D/4D loops.
- 3D/4D helper panel ordering aligned to priority:
  - score summary first, then Translation, Rotation, Camera/View, System(menu), then low-priority data.
- Leaderboard entries now capture player names, and qualifying sessions prompt for player-name entry before commit.
- 4D viewer-relative input mapping now preserves translation/rotation intent across camera yaw and hyper-view (XW/ZW) rotations via basis-aware axis routing; added regression coverage in `tests/unit/engine/test_nd_routing.py`.
- Helper panel cleanup:
  - removed duplicated locked-cell-transparency line from 3D/4D side-panel headers (meter remains canonical display).
  - retained Camera/View ahead of System in grouped helper ordering while adding constrained-height row planning so System (`menu`, `help`, `restart`) remains visible.
- Leaderboard visual refresh:
  - switched to a structured table layout with explicit column headers and cell demarcations.
  - removed outcome/exit-type from displayed leaderboard columns.
- Helper panel visibility/layout follow-up:
  - improved narrow-panel key/action text fit by rebalancing key/value columns.
  - split 3D/4D side-panel priority tiers so score + dimensions stay in the top section.
  - moved camera and extended runtime state details to the low-priority section below controls.
  - prioritized camera control group visibility while retaining system controls (`menu`, `help`, `restart`) in grouped helper rendering.
- Code-review hardening follow-up:
  - fixed leaderboard table width scaling to prevent narrow-screen column overflow.
  - removed dead `_overlay_alpha_label` helpers no longer referenced by 3D/4D panel rendering.
  - added regression coverage for helper-group constrained-height planning and leaderboard column scaling:
    - `tests/unit/engine/test_control_ui_helpers.py`
    - `tests/unit/engine/test_leaderboard_menu.py`
- Helper-panel policy follow-up:
  - folded system controls into the top `Main` helper group (removed separate `System` group block).
  - removed the overflow footer copy (`open Help for full key guide`).
  - emphasized key-name rendering in helper rows.
  - moved `Dims`, `Score mod`, and locked-cell transparency into low-priority data lines; kept `Speed level` in top panel.

Current sub-batch (2026-03-01): stage 836+ governance contract tightening (context-router manifest).

- Added strict context-router manifest validation in project contracts:
  - `tools/governance/validate_project_contracts.py`
- Added regression coverage:
  - `tests/unit/engine/test_validate_project_contracts.py`
- Backlog TODO cleanup:
  - converted context-router and policy-pack consolidation TODO entries into enforced contract checks.

Current sub-batch (2026-03-01): stage 835+ playbot learning-mode baseline and debt closure.

- Added deterministic adaptive learning mode (`LEARN`) for playbot profile tuning:
  - `src/tet4d/ai/playbot/types.py`
  - `src/tet4d/ai/playbot/controller.py`
- Added runtime policy keys for learning thresholds/window and validation wiring:
  - `config/playbot/policy.json`
  - `src/tet4d/engine/runtime/runtime_config_validation_playbot.py`
  - `src/tet4d/engine/runtime/runtime_config.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
  - `config/gameplay/tuning.json` (`assist_scoring.bot_factors.learn`)
- Added regression coverage:
  - `tests/unit/engine/test_playbot.py`
  - `tests/unit/engine/test_runtime_config.py`
- Debt source reprioritization:
  - closed `BKL-P2-024` in `config/project/backlog_debt.json`
  - added operational tuning watch `BKL-P3-009`.

Current sub-batch (2026-03-01): stage 827-834 topology-lab workflow completion + launcher/runtime wiring.

- Added Topology Lab non-Python content/layout asset:
  - `config/topology/lab_menu.json`
- Added launcher-play Topology Lab interactive flow:
  - `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
  - `cli/front.py`
- Simplified launcher routing by making `Topology Lab` a direct `Play` action:
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
  - `tests/unit/engine/test_menu_policy.py`
- Added runtime API adapters used by topology-lab workflow:
  - `src/tet4d/engine/api.py`
- Added shared numeric text-input helper and reused it in settings/lab menus:
  - `src/tet4d/ui/pygame/menu/numeric_text_input.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Added regression coverage:
  - `tests/unit/engine/test_topology_lab_menu.py`
  - `tests/unit/engine/test_front_launcher_routes.py`
  - `tests/unit/engine/test_numeric_text_input.py`
- Canonical maintenance sync:
  - `config/project/policy/manifests/canonical_maintenance.json`
- Debt source sync:
  - closed `BKL-P2-023` in `config/project/backlog_debt.json`
- Verification:
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - targeted menu/front/topology suites passed.

Current sub-batch (2026-03-01): stage 814+ shared gameplay-settings dedup + API dispatch cleanup.

- Consolidated shared gameplay settings load/save/clamp logic into runtime state layer:
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/settings_schema.py`
- Added engine API runtime adapters for shared gameplay settings access:
  - `src/tet4d/engine/api.py`
- Rewired runtime consumers to use shared helpers (removed duplicate speedup parsing/clamps):
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Added regression coverage for shared gameplay settings persistence/clamp behavior:
  - `tests/unit/engine/test_keybindings.py`
- Backlog reprioritization:
  - moved decomposition pressure from active debt (`BKL-P2-027`) to operational
    watch (`BKL-P3-007`) in `config/project/backlog_debt.json` after this dedup
    tranche.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front3d_setup.py`, `test_pause_menu.py`,
    `test_display_resize_persistence.py`, `tests/test_leveling.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): pause hotkey parity + deterministic auto speed-up controls.

- Added dedicated pause hotkey default (`F10`) alongside `m`:
  - `config/keybindings/defaults.json`
  - `keybindings/2d.json`
  - `keybindings/3d.json`
  - `keybindings/4d.json`
- Added shared advanced gameplay defaults and settings row:
  - `config/menu/defaults.json` (`auto_speedup_enabled`, `lines_per_level`)
  - `config/menu/structure.json` (`gameplay_advanced` entry + category metrics update)
- Implemented settings hub advanced gameplay submenu and persistence wiring:
  - `src/tet4d/ui/pygame/launch/launcher_settings.py`
- Implemented deterministic speed-level helper:
  - `src/tet4d/engine/gameplay/leveling.py`
  - `tests/test_leveling.py`
- Applied speed-level progression in runtime loops (2D/3D/4D), with restart reset
  to session base speed and runtime gravity reconfiguration:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
- Added engine API adapter for leveling helper to keep architecture boundary clean:
  - `src/tet4d/engine/api.py`
- Verification:
  - targeted pytest suites passed (76 tests)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-01): stage 801-812 API/runtime dedup + debt-signal cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=812`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=812`)
- Reduced repetitive wrapper/import boilerplate in `src/tet4d/engine/api.py`
  across:
  - runtime menu/settings/config/schema helpers
  - keybinding menu helper dispatch
  - frontend/render adapter dispatch
- Reduced duplicated helper logic in `src/tet4d/ui/pygame/keybindings.py`
  (key-list parsing, key tuple filtering, conflict-apply branch flow, profile
  creation delegation).
- Consolidated duplicated action/route collection loops in
  `src/tet4d/engine/runtime/menu_structure_schema.py`.
- Reworded canonical `BKL-P2-027` title in `config/project/backlog_debt.json`
  to classify it as structural maintenance debt (not bug backlog semantics),
  aligning tech-debt bug-pressure input with actual bug-class issues.
- Verification:
  - targeted suites passed (`test_keybindings.py`, `test_menu_policy.py`,
    `test_front4d_render.py`, `test_front3d_setup.py`,
    `test_validate_project_contracts.py`)
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed with debt score decrease:
    `9.81 -> 7.04`.

Current sub-batch (2026-03-01): stage 791-800 governance + LOC cleanup.

- Advanced stage metadata:
  - `scripts/arch_metrics.py` (`ARCH_STAGE=800`)
  - `config/project/policy/manifests/architecture_metrics.json` (`arch_stage=800`)
- Closed traceability debt in active backlog source:
  - removed `BKL-P2-029` from `config/project/backlog_debt.json`
  - disambiguated duplicated backlog IDs in historical summaries using `-R2` rollover IDs.
- Added project-contract enforcement for backlog-ID uniqueness:
  - `tools/governance/validate_project_contracts.py`
  - `tests/unit/engine/test_validate_project_contracts.py`
- Reduced runtime/UI wrapper/parser duplication (no behavior change):
  - `src/tet4d/engine/runtime/menu_settings_state.py`
  - `src/tet4d/engine/runtime/menu_structure_schema.py`
  - `src/tet4d/ui/pygame/keybindings.py`
  - `src/tet4d/engine/api.py`
- Documentation dedup/cleanup:
  - moved legacy DONE summaries from this file to `docs/history/DONE_SUMMARIES.md`
  - converted this file to active/open + current-batch scope only.
- Verification:
  - targeted policy/menu/keybinding/front4d/project-contract test suites passed
  - `CODEX_MODE=1 ./scripts/verify.sh` passed
  - `python scripts/arch_metrics.py` passed.

Current sub-batch (2026-03-03): tutorial control-flow hardening (Esc-back, stage redo, paced input).

- Added stage-local redo control (`F7`) without full lesson reset:
  - `src/tet4d/engine/tutorial/manager.py`
  - `src/tet4d/engine/tutorial/runtime.py`
  - `src/tet4d/engine/api.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Enforced menu/help back semantics via Esc-only return event (`menu_back`) for tutorial progression:
  - `src/tet4d/ui/pygame/runtime_ui/help_menu.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`
  - `cli/front2d.py`
  - `config/tutorial/lessons.json`
- Tightened stage success criteria for board-goal steps:
  - `config/tutorial/lessons.json` (`target_drop` now requires clear predicates)
- Enforced visible active-piece placement at every tutorial step setup apply:
  - `src/tet4d/engine/tutorial/setup_apply.py`
- Added config-backed tutorial action pacing (movement/rotation/drop delays):
  - `config/project/constants.json`
  - `src/tet4d/engine/runtime/project_config.py`
- Verification:
  - targeted tutorial suites passed
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-03): tutorial/menu flow consolidation (root Tutorials route, stage navigation, free-play handoff).

- Moved tutorial entrypoint to launcher root and removed pause-menu tutorial exit action:
  - `config/menu/structure.json`
  - `tests/unit/engine/test_menu_policy.py`
  - `tests/unit/engine/test_pause_menu.py`
- Tutorial launch now bypasses per-mode setup menus and starts from deterministic lesson presets:
  - `src/tet4d/ui/pygame/launch/launcher_play.py`
- Added tutorial stage navigation controls (`F5` previous, `F6` next) and
  preserved existing `F7` redo, `F8` main-menu exit, `F9` lesson restart:
  - `src/tet4d/engine/api.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
- Tutorial end now transitions cleanly into free play by dropping completed
  tutorial session state in active loops:
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- Hardened 4D W-move tutorial setup solvability and added regression coverage:
  - `src/tet4d/engine/tutorial/setup_apply.py`
  - `tests/unit/engine/test_tutorial_setup_apply.py`
- Clarified 2D drop-phase instruction wording (precision drop vs line clear):
  - `config/tutorial/lessons.json`
- Enforced menu back parity for `Backspace` with `Esc`:
  - `src/tet4d/ui/pygame/menu/menu_runner.py`
  - `src/tet4d/ui/pygame/menu/menu_controls.py`
  - `src/tet4d/ui/pygame/menu/keybindings_menu.py`
- Verification:
  - `PYTHONPATH=src .venv/bin/pytest -q tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_menu_policy.py tests/unit/engine/test_pause_menu.py tests/unit/engine/test_front_launcher_routes.py tests/unit/engine/test_nd_routing.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-03): tutorial camera/transparency UX alignment + stage-stability hardening.

- Unified helper-panel control taxonomy with camera/transparency parity:
  - moved `grid mode` into camera panel and exposed camera panel in 2D
  - added transparency meter bar (`Locked-cell transparency`) to 2D/3D/4D side panels
  - files:
    - `config/help/layout/runtime_help_action_layout.json`
    - `src/tet4d/ui/pygame/render/control_helper.py`
    - `src/tet4d/ui/pygame/render/gfx_panel_2d.py`
    - `src/tet4d/ui/pygame/render/gfx_game.py`
    - `src/tet4d/engine/front3d_render.py`
    - `src/tet4d/engine/front4d_render.py`
    - `tests/unit/engine/test_control_ui_helpers.py`
- Tutorial runtime pacing/stability updates:
  - added config-backed `>=1s` step transition hold
  - added transparency target-range progression predicate with per-step randomized target in `20%-80%`
  - enabled `soft_drop` as always-allowed tutorial action
  - passed overlay/grid runtime predicates into tutorial progression for 2D/3D/4D loops
  - files:
    - `config/project/constants.json`
    - `src/tet4d/engine/runtime/project_config.py`
    - `src/tet4d/engine/tutorial/manager.py`
    - `src/tet4d/engine/tutorial/runtime.py`
    - `src/tet4d/engine/api.py`
    - `cli/front2d.py`
    - `src/tet4d/ui/pygame/front3d_game.py`
    - `src/tet4d/ui/pygame/front4d_game.py`
- Tutorial content updates:
  - 4D movement stages now require double action count (`event_count_required=2`)
  - layer-fill and full-clear goal steps now accept `toggle_grid` and require `grid_enabled`
  - transparency stages now require target-range predicate completion
  - file:
    - `config/tutorial/lessons.json`
- Removed `Restart Tutorial` from pause menu action graph:
  - `config/menu/structure.json`
  - `src/tet4d/engine/ui_logic/menu_action_contracts.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `tests/unit/engine/test_pause_menu.py`
- Verification:
  - `PYTHONPATH=src pytest -q tests/unit/engine/test_control_ui_helpers.py tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_pause_menu.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-04): transparency-goal clamp binding + tutorial stage solvability hardening.

- Transparency tutorial goals are now derived from global overlay transparency
  clamps (schema/runtime), not hardcoded lesson percentages:
  - `overlay_alpha_dec` resolves to clamp-min
  - `overlay_alpha_inc` resolves to clamp-max
  - files:
    - `src/tet4d/engine/tutorial/runtime.py`
    - `config/tutorial/lessons.json`
- Raised global locked-cell transparency max clamp from `85%` to `90%` and
  synchronized schema/help copy:
  - `src/tet4d/engine/runtime/settings_schema.py`
  - `config/schema/menu_settings.schema.json`
  - `config/help/content/runtime_help_content.json`
  - `tests/unit/engine/test_keybindings.py`
- Goal-stage spawn behavior tightened for line/layer/full-clear lessons:
  piece spawn now targets approximately 3 gravity layers above prepared goal
  regions; helper grid is forced for fill/full-clear stages:
  - `src/tet4d/engine/tutorial/setup_apply.py`
  - `cli/front2d.py`
  - `src/tet4d/ui/pygame/front3d_game.py`
  - `src/tet4d/ui/pygame/front4d_game.py`
- ND (3D/4D) movement-stage setup continuity fixed by restoring per-step setup
  application across translation/rotation steps to prevent unsolvable 4-action
  movement stages:
  - `src/tet4d/engine/tutorial/runtime.py`
  - `tests/unit/engine/test_tutorial_runtime.py`
  - `tests/unit/engine/test_tutorial_setup_apply.py`
- Verification:
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_runtime.py tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_overlay.py` passed.
  - `.venv/bin/python -m pytest -q tests/unit/engine/test_tutorial_setup_apply.py tests/unit/engine/test_keybindings.py` passed.
  - `CODEX_MODE=1 ./scripts/verify.sh` passed.

Current sub-batch (2026-03-05): tutorial step-set realignment (2D/3D/4D) + plan parity updates.

- Tutorial lesson order updated to canonical sets:
  - 2D: move X, rotate XY, drop controls, grid/transparency, then goals (`line_fill`, `full_clear_bonus`, `target_drop`)
  - 3D: adds `move_z_*`, `rotate_xz_*`, `rotate_yz_*`, keeps camera yaw/pitch then mouse orbit/zoom, then zoom/camera reset and goals
  - 4D: adds `move_w_*`, `rotate_xw/yw/zw_*`, keeps keyboard `view_xw/zw_*` before mouse camera steps, then goals
- Tutorial plan updates in `config/tutorial/plan.json`:
  - moved shared drop stages (`soft_drop`, `hard_drop`) after piece-rotation stages
  - scoped `cycle_projection` to `4d` only
  - split target-placement plan stage into:
    - `target_placement_nd` (`3d`, `4d`)
    - `target_placement_2d` (`2d`, final goal stage)
- Tests updated to enforce new ordering and prevent drift:
  - `tests/unit/engine/test_tutorial_content.py`
  - `tests/unit/engine/test_tutorial_runtime.py`
- Verification:
  - `pytest -q tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_runtime.py` passed.

Current sub-batch (2026-03-05): tutorial pause-key routing fix (`Esc`/`Q`).

- Fixed tutorial pause-menu key handling so both keys now close the pause loop correctly:
  - root `Esc` now routes via `MenuRunner.on_root_escape`
  - `Q` routes via `on_quit_event`
- Removed pause-menu local keydown interception that consumed keys without
  terminating the shared menu runner.
- Added regression tests:
  - integration tests for `run_pause_menu(...): Esc -> resume`, `Q -> quit`
  - `MenuRunner` root-escape test to prevent `Esc`-at-root drift
- Files:
  - `src/tet4d/ui/pygame/menu/menu_runner.py`
  - `src/tet4d/ui/pygame/runtime_ui/pause_menu.py`
  - `tests/unit/engine/test_pause_menu.py`
  - `tests/unit/engine/test_menu_runner.py`
- Verification:
  - `pytest -q tests/unit/engine/test_pause_menu.py tests/unit/engine/test_menu_runner.py tests/unit/engine/test_menu_navigation_keys.py` passed.
  - `ruff check src/tet4d/ui/pygame/menu/menu_runner.py src/tet4d/ui/pygame/runtime_ui/pause_menu.py tests/unit/engine/test_pause_menu.py tests/unit/engine/test_menu_runner.py` passed.

Current sub-batch (2026-03-05): tutorial mouse stages are mouse-only (no keyboard completion mapping).

- Removed keyboard fallback completion from tutorial mouse stages in 3D/4D:
  - `mouse_orbit` now completes only on `mouse_orbit` event.
  - `mouse_zoom` now completes only on `mouse_zoom` event.
- Removed `event_count_required` from mouse stages (default single successful mouse action).
- Tightened mouse-stage input gating to remove keyboard camera actions from allowed lists.
- Strengthened tutorial pointer gating in 3D/4D loops so blocked RMB drags cannot arm stale orbit state and mouse-wheel completion requires a real zoom delta.
- Extended 3D/4D mouse tutorial stages so the overlay uses explicit mouse KEY labels and completion now requires sustained orbit/zoom input across at least 2 seconds instead of a single mouse event.
- Updated content/runtime tests to enforce:
  - no keyboard fallback completion
  - mouse-stage progression requires mouse events
- Files:
  - `config/tutorial/lessons.json`
  - `tests/unit/engine/test_tutorial_content.py`
  - `tests/unit/engine/test_tutorial_runtime.py`
- Verification:
  - `pytest -q tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_runtime.py` passed.
  - `ruff check config/tutorial/lessons.json tests/unit/engine/test_tutorial_content.py tests/unit/engine/test_tutorial_runtime.py` passed.

Current sub-batch (2026-03-06): tutorial action-delay reduction + generated configuration reference governance.

- Halved tutorial intra-step action delays in canonical project constants and runtime fallback values:
  - `movement`: `140 ms`
  - `rotation`: `170 ms`
  - `drop`: `500 ms`
  - `soft_drop`: `90 ms`
  - `hard_drop`: `450 ms`
  - files:
    - `config/project/constants.json`
    - `src/tet4d/engine/runtime/project_config.py`
- Added generated configuration references:
  - full config inventory: `docs/CONFIGURATION_REFERENCE.md`
  - compact user-facing settings view: `docs/USER_SETTINGS_REFERENCE.md`
  - generator/check: `tools/governance/generate_configuration_reference.py`
  - tests: `tests/unit/governance/test_generate_configuration_reference.py`
- Refined the compact user settings reference to:
  - group settings into stable buckets (`Profiles`, `Display`, `Audio`, `Analytics`, per-mode `Gameplay Setup` / `Gameplay` / `Bot Options`)
  - resolve dynamic option labels for piece-set and topology-profile indices
  - fail generation when a persisted setting is not assigned to a bucket
- Extended the compact keybinding profile summary to use canonical category docs and scope ordering (`General / System`, `Gameplay`, `Camera / View`) with hard failures for unknown profile groups/scopes.
- Added policy/contract enforcement so config changes must keep the reference synchronized:
  - `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`
  - `config/project/policy/manifests/policy_registry.json`
  - `config/project/policy/manifests/project_policy.json`
  - `config/project/policy/manifests/canonical_maintenance.json`
  - `scripts/verify.sh`
- Docs updated to link the generated reference and document the governance rule:
  - `README.md`
  - `docs/README.md`
  - `docs/RDS_AND_CODEX.md`
  - `docs/FEATURE_MAP.md`
  - `docs/PROJECT_STRUCTURE.md`
  - `docs/SECURITY_AND_CONFIG_PLAN.md`
  - `docs/rds/RDS_TETRIS_GENERAL.md`
- Verification:
  - `tools/governance/generate_configuration_reference.py --check` will now fail on drift.
  - Full verification pending after this batch.

Current sub-batch (2026-03-07): tutorial overlay safe-lane closure for ND tutorials.

- Closed active debt item `BKL-P1-010` after moving the default 3D/4D tutorial overlay dock into the side-panel lane and clamping tutorial-panel dragging to stay outside the active board/layers area.
- Added layout regression coverage that asserts the default 3D/4D tutorial overlay rect does not intersect the gameplay area and stays inside the safe lane even under extreme drag offsets:
  - `tests/unit/engine/test_tutorial_overlay_layout.py`
- Files:
  - `src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py`
  - `config/project/backlog_debt.json`
  - `docs/rds/RDS_TETRIS_GENERAL.md`
  - `CURRENT_STATE.md`
- Verification:
  - `pytest -q tests/unit/engine/test_tutorial_overlay_layout.py tests/unit/engine/test_tutorial_overlay.py` passed.
  - `ruff check src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py tests/unit/engine/test_tutorial_overlay_layout.py` passed.
Current sub-batch (2026-03-07): tutorial zoom-stage debt closure.

- Closed stale active debt item `BKL-P1-011`; zoom tutorial stages are already config-defined in `config/tutorial/lessons.json` and enforced by tutorial content/runtime tests.
- Canonical debt source now has no active open debt items.
- Files:
  - `config/project/backlog_debt.json`
  - `docs/BACKLOG.md`
  - `CURRENT_STATE.md`
  - `docs/CONFIGURATION_REFERENCE.md`
- Verification:
  - `python scripts/arch_metrics.py` passed after debt-source update.
Current sub-batch (2026-03-07): Windows packaging host-tooling guard.

- Hardened `packaging/scripts/build_windows.ps1` so local MSI builds:
  - fail fast with a clear message when only `.NET SDK < 6` is available,
  - avoid user-profile global WiX installation by using a repo-local `--tool-path`,
  - default `DOTNET_CLI_HOME` into the packaging build directory for cleaner local execution.
- Updated `docs/RELEASE_INSTALLERS.md` to document the Windows local-build prerequisite and local tool-path behavior.
Current sub-batch (2026-03-10): numeric setup-menu entry and explorer translation regression hardening.

- Added shared numeric text parsing/editing for setup menus so numeric rows can be entered directly from typed digits, committed with `Enter`, canceled with `Esc`, and edited with `Backspace`.
- Extended setup state owners and shared menu controls to support numeric text mode:
  - `src/tet4d/ui/pygame/menu/menu_controls.py`
  - `src/tet4d/ui/pygame/front2d_setup.py`
  - `src/tet4d/ui/pygame/frontend_nd_setup.py`
- Added focused regression coverage:
  - `tests/unit/engine/test_setup_menu_numeric_input.py`
  - strengthened live explorer/playground translation coverage in `tests/unit/engine/test_gameplay_replay.py`
- Verified the current explorer playground launch path does not reproduce the reported `3D/4D` translation-to-menu regression on this branch; the new tests pin that behavior directly through the live handlers.

Current sub-batch (2026-03-10): staged migration control-contract hardening.

- Contributor directives now encode staged-migration honesty, additive migration before deletion, and required delta reporting for migration work.
- `docs/RDS_AND_CODEX.md` now states that partial progress is not completion, large migrations must add new modules and route one flow before deleting old code, and staged batches must end with a delta report.
- Governance tests now pin those directives and the corresponding `docs/RDS_AND_CODEX.md` contract tokens.

Current sub-batch (2026-03-13): atomic full-piece topology movement validation.

- Added shared candidate-placement validation in `src/tet4d/engine/core/rules/piece_placement.py` so piece motion now validates the full target footprint before any commit, with explicit support for ignoring the active piece's vacated source cells during move/rotation checks.
- Rewired active gameplay and sandbox paths to use that atomic contract:
  - `src/tet4d/engine/gameplay/game2d.py`
  - `src/tet4d/engine/gameplay/game_nd.py`
  - `src/tet4d/engine/gameplay/explorer_runtime_2d.py`
  - `src/tet4d/engine/gameplay/explorer_runtime_nd.py`
  - `src/tet4d/engine/runtime/topology_playground_sandbox.py`
  - `src/tet4d/engine/core/rules/state_queries.py`
- Added focused regressions covering self-vacated moves, rotation atomicity, genuine-collision rejection, seam-crossing parity, and sandbox no-mutate-on-failed-rotation behavior:
  - `tests/unit/engine/test_piece_placement.py`
  - `tests/unit/engine/test_game2d.py`
  - `tests/unit/engine/test_game_nd.py`
  - `tests/unit/engine/test_explorer_transport_parity.py`
  - `tests/unit/engine/test_topology_playground_sandbox.py`
- RDS contract unchanged; no RDS doc update required for this batch.


Current sub-batch (2026-03-13): explorer rigid-play mode and unsafe seam movement parity.

- Root cause: topology playability analysis already detected unsafe explorer topologies, but sandbox/gameplay still treated local rigid-looking seam moves as legal because runtime movement hard-blocked only `CELLWISE_DEFORMATION` and had no canonical rigid-play mode setting.
- Added canonical playground `rigid_play_mode` (`auto` / `on` / `off`) and threaded it through explorer launch snapshots, gameplay launch config, sandbox movement, and both 2D/ND explorer gameplay runtimes.
- `auto` now resolves unsafe explorer topologies to cellwise seam transport by default, while still allowing the user to force rigid or cellwise play explicitly from the topology lab controls.
- Cellwise mode now rebuilds exact moved-cell placements for seam crossings/deformation cases, so flat and non-flat pieces follow the same unsafe-topology rules instead of splitting on incidental local rigidity.
- Files:
  - `src/tet4d/engine/runtime/topology_playground_state.py`
  - `src/tet4d/engine/runtime/topology_playability_signal.py`
  - `src/tet4d/engine/runtime/topology_playground_launch.py`
  - `src/tet4d/engine/runtime/topology_playground_sandbox.py`
  - `src/tet4d/engine/gameplay/explorer_runtime_2d.py`
  - `src/tet4d/engine/gameplay/explorer_runtime_nd.py`
  - `src/tet4d/engine/gameplay/game2d.py`
  - `src/tet4d/engine/gameplay/game_nd.py`
  - `src/tet4d/ui/pygame/topology_lab/scene_state.py`
  - `src/tet4d/ui/pygame/topology_lab/app.py`
  - `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
  - `tests/unit/engine/test_topology_playground_launch.py`
  - `tests/unit/engine/test_topology_playground_sandbox.py`
  - `tests/unit/engine/test_unsafe_topology_correctness.py`
  - `tests/unit/engine/test_explorer_transport_parity.py`
  - `tests/unit/engine/test_game2d.py`
  - `tests/unit/engine/test_game_nd.py`
  - `tests/unit/engine/test_topology_lab_menu.py`
  - `tests/unit/engine/test_topology_lab_app.py`
- Verification:
  - `python -m pytest tests/unit/engine/test_topology_playground_launch.py tests/unit/engine/test_topology_playground_sandbox.py tests/unit/engine/test_unsafe_topology_correctness.py tests/unit/engine/test_explorer_transport_parity.py tests/unit/engine/test_game2d.py tests/unit/engine/test_game_nd.py tests/unit/engine/test_topology_lab_menu.py tests/unit/engine/test_topology_lab_app.py` passed.
  - `python -m ruff check ...` passed on the touched runtime/UI/test files.

## 6. Source Inputs

1. `config/project/backlog_debt.json`
2. `scripts/arch_metrics.py`
3. `config/project/policy/manifests/tech_debt_budgets.json`
4. `docs/rds/*.md`
5. `docs/ARCHITECTURE_CONTRACT.md`
6. `CURRENT_STATE.md`
7. `docs/history/DONE_SUMMARIES.md`
