# CURRENT_STATE (Restart Handoff)

Last updated: 2026-04-15  
Branch: `codex/endgame-flow-slider-layout`  
Worktree expectation: clean unless an active batch is in progress

## Purpose

This file is the restart handoff for the current architecture baseline. It is
not a historical ledger. Long historical migration detail belongs in
`docs/history/DONE_SUMMARIES.md`.

## Current Authority

- For topology-playground architecture and migration-state questions, consult
  `docs/plans/topology_playground_current_authority.md` first.
- The active plan set is intentionally small:
  `docs/plans/topology_playground_current_authority.md` and
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- `docs/plans/README.md` defines the active-plan versus reference-doc split for
  the rest of `docs/plans/`.
- Older topology-playground manifests, stage plans, and audits remain useful
  background, but they are historical unless a future task explicitly
  reactivates them.
- If archived topology-playground manifests conflict with the current-authority
  file, follow the current-authority file.
- If a newer task instruction severely conflicts with the current-authority
  file or with current code reality, ask first and then update the manifest
  layer in the same batch if the direction changes.

## Active Batch Note

- Release packaging hidden-import follow-up (2026-04-15): the canonical
  PyInstaller spec now explicitly includes the lazy `tet4d.ai.playbot.*`
  modules used by frozen launcher/setup flows, preventing packaged Windows
  builds from crashing on `ModuleNotFoundError:
  tet4d.ai.playbot.dry_run` when the ND setup path imports playbot dry-run
  helpers through package-level lazy exports.
- Governance/planning layer consolidation (2026-03-29): documentation routing is now being compacted around `docs/DOCUMENTATION_MAP.md` as the only docs routing authority, `docs/README.md` is being reduced to a landing page, recent planning-adjacent audits are moving under `docs/plans/audits/`, and the older security/config policy plan is being retired to history while `config/project/policy/governance.json` plus `config/project/policy/code_rules.json` remain the compact top-level governance surface.
- Topology-playground doc authority alignment (2026-03-29): the accepted visible shell is now documented consistently across the active authority/spec/status/menu files. `Topology Playground` is the direct modern shell entry, the legacy topology editor remains reachable only through `Settings -> Legacy Topology Editor Menu`, the visible workspace model remains `Editor` / `Sandbox` / `Play`, the top bar stays limited to title/tabs/validity/dimension, the left sidebar stays limited to the accepted per-workspace inventories with diagnostics secondary, the right helper remains keys-first and diagnostics-free, and the next phase is shell-preserving implementation simplification centered on `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and `src/tet4d/ui/pygame/topology_lab/scene_state.py`.
- Topology-playground shell-layout + text-visibility guard pass (2026-03-29): the shell now computes top-bar, footer, and control-row text budgets through explicit internal layout helpers rather than only inline geometry, and focused visibility coverage now checks compact-window required text for the Topology Playground shell, pause/settings/help surfaces, tutorial overlays, and gameplay side-panel bounds without introducing screenshot-based tests or changing the frozen shell contract.
- Topology-playground state/write seam cleanup follow-up (2026-03-29): preview compile/cache refresh now lives in a dedicated `scene_preview_state.py` helper instead of remaining mixed into `controls_panel.py`, and `scene_state.py` now routes canonical-state writes through a narrower shared runtime-state acquisition path so play-settings/profile/draft/selection/probe toggles keep one explicit fallback-versus-canonical mutation contract.
- Topology-playground runtime latency follow-up (2026-03-29): the scene refresh path now splits cheap immediate preview/validity sync from deferred rigid playability analysis, same-signature rigid-analysis results are cached alongside preview signatures, explicit play launch forces any still-pending rigid analysis once at launch time, and the visible `Play Transport` wording tolerates a temporary analyzing state without reopening the frozen shell contract.
- Topology-playground readability follow-up (2026-03-29): compact-shell sizing now gives the left sidebar and right helper less brittle width budgets, helper copy wraps instead of collapsing into early ellipses, and focused visibility tests now pin 960px-class top-bar fit, compact control-row text budgets, and a minimum readable helper lane.
- Topology-playground explorer board-size floor follow-up (2026-03-29): explorer-mode board height can now be lowered to `6` instead of stopping at `8`, and focused menu coverage now pins the new minimum without changing the settled workspace or shell layout contract.
- Topology-playground torus preset follow-up (2026-03-29): the all-wrap explorer presets now surface as explicit torus presets in every supported dimension, with `2D` keeping `Torus` and the existing `3D` / `4D` full-wrap compatibility ids now labeling the user-facing presets as `3-Torus` and `4-Torus`.
- Topology-playground local preview cache follow-up (2026-03-29): explorer preview compilation now uses a versioned repo-local on-disk cache keyed by effective `(profile, dims)` signature under `state/topology/cache/explorer_preview`, so repeated identical preview/signaling work can reuse cached movement-graph payloads across runs while corrupt or version-stale cache entries safely fall back to recompute.
- Topology-explorer movement-graph speedup follow-up (2026-03-29): the graph builder now uses a graph-specific fast path instead of calling the fully general cell-step resolver for every cell edge. Interior moves now use direct coordinate arithmetic, boundary exits reuse precomputed seam lookups, and identical `(profile, dims)` graph builds now reuse an in-process memoized row set before preview payload assembly.
- Topology-playground persistent cache completion follow-up (2026-03-29): the same versioned topology cache file now persists preview payloads, serialized movement-graph rows, and rigid-playability analysis together by effective topology signature, so repeat runs can reuse the full preview/signaling artifact stack rather than only the summary preview payload. Advanced gameplay now also exposes `Measure topology cache` and `Clear topology cache` actions for the persistent topology cache set, while clear also flushes the current process movement-graph and resolver memos.
- Topology-playground cache-miss warning fix follow-up (2026-03-31): missing repo-local explorer preview cache files now return a silent cache miss during lookup instead of surfacing config-read warnings, while corrupt or unreadable existing cache files still follow the existing warning-and-rebuild path.
- Shared menu-shell rework follow-up (2026-04-10): launcher, setup, pause,
  settings, and keybindings screens now share the same title-cased
  subtitle-free shell with a visible `Back` chip, framed Tron-leaning panel
  treatment, flash-on-change feedback, and inline numeric sliders where the
  ranges are bounded. Runtime movement/keybinding copy now prefers
  `Left` / `Right` / `Forward` / `Backward` / `Down`, and the default overlay
  transparency control now lives directly under
  `Settings -> Game` instead of
  `Settings -> Display`.
- Shared menu-slider layout follow-up (2026-04-11): slider-bearing launcher,
  setup, and in-game settings rows now share one config-backed row contract
  for label/value/track allocation, the slider track/thumb geometry is larger,
  and compact supported menu widths now grow row/panel allocation instead of
  clipping slider labels or values.
- Leaderboard recording contract follow-up (2026-04-10): leaderboard writes now
  happen only on completed standard-play `game_over` transitions, never from
  explorer-mode runs or quit/menu/restart exits, and persisted score trimming
  now keeps the top `10` entries per gameplay dimension instead of one mixed
  global cap.
- Post-terminal endgame animation follow-up (2026-04-10): gameplay now enters a
  dedicated `playing` -> `endgame_shatter` -> `endgame_relic_field` runtime
  path on terminal loss, freezes the final board into a seeded endgame
  snapshot instead of mutating live gameplay state, lets shell/grid/box
  fragments die in a finite rupture, and keeps locked-cell relics alive
  forever through deterministic bounded path families in the simple 2D path
  and the shared projected 3D/4D renderers.
- Endgame preset-system follow-up (2026-04-11): the persistent relic phase now
  freezes a shared preset id plus a separate interaction mode into the endgame
  snapshot, supports the required `wrap_all`, `invert_all`, and `sphere`
  topology-flavored motion fields with deterministic optional collision
  handling, and exposes those controls together under the
  `Settings -> Game` endgame section.
- Canonical menu-structure follow-up (2026-04-12): `config/menu/structure.json`
  is now the sole structural source of truth for launcher, pause, settings,
  the flattened scrolling `Game` page, keyboard bindings, and retained legacy
  entries. The old split settings row/section/route authorities are removed
  from live config, and launcher/settings/keybindings rendering now consumes
  one compiled runtime graph rather than re-authoring page structure in
  Python.
- Menu normalization follow-up (2026-04-12): runtime menu consumers now read a
  normalized graph compiled from `config/menu/structure.json` instead of the
  raw authored tree directly. Hidden rows are stripped first, singleton
  wrappers are collapsed, direct-forward shims are rewritten away, authored
  `Settings -> Controls -> Keyboard Bindings` and `Settings -> Legacy ->
  Legacy Topology Editor Menu` originally collapsed into direct runtime
  entries on `Settings`, and the single-setting `Visual / Animation` wrapper
  originally inlined into `Game` instead of surviving as a one-row submenu.
- Authored menu-flattening + direct-play follow-up (2026-04-12): the settled
  `Controls`, `Legacy`, and one-row `Visual / Animation` wrappers are now
  removed from authored config instead of only collapsing at runtime,
  `config/menu/structure.json` now carries generic `action_group` rows for
  `Play -> 2D/3D/4D`, `Play` launches gameplay directly from persisted mode
  settings, `Setup` stays reachable on the same `Choose Mode` screen, and
  `config/topology/lab_menu.json` is reduced to Topology Playground shell copy
  rather than looking like a second visible menu-structure authority.
- Shared menu-overflow follow-up (2026-04-12): settings and keybindings pages
  now share one overflow viewport contract with auto-scroll, scrollbar
  geometry reserved in layout, and selection visibility kept in sync while
  navigating long pages instead of clipping rows off-screen; the same shared
  overflow path now also covers the compact bot-options surface.
- ND endgame-motion follow-up (2026-04-12): persistent relic motion now
  evolves in ND board space before projection instead of only in render-space
  path surrogates. `wrap_all`, `invert_all`, and `sphere` now govern ongoing
  ND boundary/field behavior, 4D relics can traverse hidden axes and blend
  between rendered layer boards from the frozen basis map, and the scrolling
  `Settings -> Game` page now carries separate `Relic field speed` and
  `Shatter speed` controls so long-run motion speed is independent from preset
  identity.
- Leaderboard modal follow-up (2026-04-11): qualifying leaderboard registration
  now opens as a compact modal overlay over the existing post-terminal gameplay
  surface instead of repainting a dedicated full-screen registration page, and
  the live registration form/persistence authority remains centralized in the
  leaderboard runtime while background gameplay input stays suppressed.
- Projected active-piece occlusion follow-up (2026-04-10): projected `3D` /
  `4D` board gridlines and board-box edges now resolve against the active piece
  per projected fragment rather than by one global draw-order pass, the shared
  projection layer now emits explicit projected board-line and piece-face
  primitives for that resolver, and `2D` intentionally stays on its simpler
  non-projected layering path.
- Topology-playground/menu visibility follow-up (2026-03-30): compact control rows in both `Topology Playground` and `Advanced gameplay` now use wrap-aware label/value rendering instead of single-line truncation-only rendering, shared action buttons plus workspace tabs now wrap instead of hard truncating long labels, and the external helper lane now reserves a wider minimum width on supported compact shells so wrapped helper lines stay readable instead of collapsing into an overly narrow sidebar.
- Topology-playground helper-panel redesign follow-up (2026-03-30): the right helper no longer renders as a generic wrapped hint stack. It now presents a minimal `Controls` card with one short workspace/tool context line plus dedicated `Move` and `Rotate` sections populated from the live current keybinding maps for the active dimension, keeping the helper easy to scan without reintroducing diagnostics or duplicate menu controls.
- Topology-playground 4D keybinding drift follow-up (2026-03-30): the last local sandbox fallback that still treated `N` as `w-` translation is removed, so `N` now consistently follows the runtime-backed `rotate_zw_neg` binding in the playground instead of bypassing the canonical keybinding contract.
- Keybinding authority unification follow-up (2026-03-30): keybinding action/group/editor/helper structure now lives in `config/keybindings/catalog.json` instead of being split across Python constants, menu structure docs, and a separate help-action layout file. Built-in preset defaults remain in `config/keybindings/defaults.json`, user profile files remain the mutable override layer, the keybindings menu scope-section copy is now catalog-backed instead of UI-local, and runtime help/editor/control surfaces now read the same catalog-backed metadata plus the same resolved live binding map.
- Keybinding contract-hardening follow-up (2026-03-30): shipped defaults and persisted profile payloads are now validated against the same catalog-backed action/group/dimension contract before runtime use, invalid saved profile payloads now fail cleanly instead of being silently filtered through partial group application, and contributor docs now include a dedicated config-first keybinding editing guide.
- Keybinding runtime-ownership completion follow-up (2026-03-30): mutable live keybinding maps now live under `src/tet4d/engine/runtime/keybinding_runtime_state.py` instead of being constructed and mutated directly in the pygame adapter, built-in defaults now enforce full required-action coverage, saved payloads now carry an explicit schema version, custom saved profiles remain allowed as partial overrides, and the repo now includes a dedicated `./scripts/check_keybinding_contract.sh` focused validation path for keybinding config work.
- Keybinding runtime accessor cleanup follow-up (2026-03-30): engine/runtime now exposes narrow keybinding accessors through `src/tet4d/engine/runtime/api.py`, and UI callers that only needed active-profile or grouped runtime binding reads now consume those runtime accessors directly instead of depending on the wider `src/tet4d/ui/pygame/keybindings.py` adapter surface.
- Keybinding short-guide follow-up (2026-03-30): repo docs now include `docs/SHORT_KEYBINDINGS_GUIDE.md`, a shorter task-oriented guide for direct keybinding config edits with concrete catalog/defaults examples, while the longer `docs/KEYBINDINGS_EDITING.md` remains the full contract reference.
- Keybinding key-name config follow-up (2026-03-30): shipped defaults and saved keybinding payloads may now use readable key-name strings such as `"g"` and `"space"` in addition to integer keycodes, with store-level validation normalizing them to canonical `pygame` keycodes before runtime use.
- Keybinding stale-source cleanup follow-up (2026-03-30): the dead legacy `src/tet4d/ui/pygame/input/keybindings_defaults.py` fallback source is removed, startup now deletes the obsolete `keybindings/profiles/small/` built-in directory if it exists, and the canonical shipped keybinding truth remains only the catalog/defaults-plus-runtime-store path.
- Keybinding round-trip contract repair follow-up (2026-03-30): the runtime/store key-token parser now accepts the keypad operator token names that the serializer writes into built-in profile files, built-in `full` 4D bindings round-trip cleanly again, and invalid custom profile files now fail load instead of being silently overwritten during normal active-profile initialization.
- Topology-playground keybinding seam follow-up (2026-03-30): helper-panel movement/rotation labels plus movement/camera shortcut matching in the playground now read the canonical runtime binding groups instead of direct `KEYS_*` / `EXPLORER_KEYS_*` / `CAMERA_KEYS_*` adapter globals, so the playground stays aligned with the active runtime keybinding state.
- Settings-help contract follow-up (2026-04-12): the runtime help screen’s
  settings summary now derives from the live `settings_root` subtree in the
  compiled menu graph sourced from `config/menu/structure.json`, so the
  current runtime `Game`, `Display`, and `Audio` categories stay in sync with
  the shared menu graph instead of drifting through older parallel section
  docs.
- Keybinding contract-check follow-up (2026-03-30): the focused `./scripts/check_keybinding_contract.sh` gate now also covers the runtime-seam consumers in menu navigation and tutorial overlays, and `src/tet4d.egg-info/SOURCES.txt` has been regenerated so the deleted legacy keybinding defaults file no longer appears in the packaged source manifest.
- Topology-playground text-layout dedup follow-up (2026-03-30): shared wrapped-text primitives now centralize multi-line row sizing and centered compact-label rendering in `src/tet4d/ui/pygame/ui_utils.py`, so Topology Playground control rows, launcher settings rows, workspace tabs, and transform/action buttons now reuse the same layout math instead of maintaining near-duplicate wrapping code at each callsite.
- Topology-playground row-render dedup follow-up (2026-03-30): the shared pygame UI helpers now also centralize selection-highlight drawing plus wrapped label/value row text rendering, so launcher settings and Topology Playground control rows no longer keep parallel per-surface loops for the same highlighted multi-line row presentation.
- Config-reference/theme follow-up (2026-03-30): `config/ui/theme.json` now participates in the generated configuration-reference contract, focused project-config coverage now pins theme color fallback and validation behavior, and topology-playground color reads now stay lazy at the `pygame` UI seam instead of binding the theme once at `ui_utils.py` import time.
- Topology-playground panel/text dedup follow-up (2026-03-30): shared pygame UI helpers now centralize common framed-card drawing and centered fitted single-line text rendering, so the helper card, preview panel, and launcher status/title/hint lines reuse the same compact panel/text primitives instead of repeating local fit-and-center boilerplate.
- Topology-playground compact-chip dedup follow-up (2026-03-30): the shared pygame UI helpers now also centralize centered chip/badge rendering, so the Topology Playground top-bar validity/dimension chips and footer helper chips reuse one compact chip primitive instead of maintaining duplicate fit-center-border drawing logic.
- Topology-playground fitted-text cleanup follow-up (2026-03-30): the remaining Topology Playground shell callers now route more title/header/button text through the shared fitted-text helpers, so the top-bar title, controls header, helper-card internals, and probe-control labels no longer carry separate local fit-text render boilerplate.
- Topology-playground duplicate-panel cleanup follow-up (2026-03-30): local framed-panel and fitted-text helpers in `projection_scene.py` and `transform_editor.py` are now removed in favor of the shared pygame UI primitives, so more of the projection/info/transform surfaces now spend down caller-local duplication instead of growing new abstraction layers.
- Topology-playground dead-code cleanup follow-up (2026-03-30): the shared side-panel path no longer exposes an unused `min_controls_h` parameter, the modern explorer workspace shell no longer accepts stale unused title/color arguments, and `vulture src tests scripts tools --min-confidence 80` is clean again after removing those defunct callsite parameters.
- Launcher settings split fix follow-up (2026-03-30): the launcher `Settings` menu no longer reopens the full bundled settings hub for `Game`, `Display`, and `Audio`. Those entries now open filtered category-specific settings screens, while `Advanced gameplay` continues to use the broader gameplay/advanced path and focused coverage now pins both the row filtering and launcher dispatch contract.
- Launcher settings IA follow-up (2026-03-30): the top-level launcher settings menu no longer has an `Advanced` submenu. `Legacy Topology Editor Menu` now sits directly on the main settings list, and the old `Game -> Advanced gameplay...` sub-flow is retired so its shared gameplay tuning rows now render directly as an inline `Advanced gameplay` section inside the game settings screen itself.
- Launcher settings config-authority follow-up (2026-03-30): menu structure now owns settings section titles/subtitles/header membership/row ownership plus launcher `Game`/`Display`/`Audio` route targets in `config/menu/structure.json`, top-level settings category policy now derives from that same section contract instead of the older category-metrics path, invalid section header/row references now fail config validation instead of silently degrading filtered settings screens, launcher/settings Python no longer keeps private section or route maps for that IA, and governance now fails if those hardcoded maps are reintroduced.
- Menu-structure editing guide follow-up (2026-03-30): repo docs now include a dedicated `docs/MENU_STRUCTURE_EDITING.md` guide covering config-first menu graph/settings-section edits, current validation rules, and the expected verification flow, and the docs routing plus menu-structure RDS references now point contributors to that guide instead of leaving menu editing knowledge implicit.
- Dead-code pruning follow-up (2026-03-30): another small set of unreferenced helpers and stale compatibility leftovers is now removed, including the unused topology-lab `_COMPAT_EXPORTS` tuple, the unused `tool_is_play(...)` export seam, dead internal core/gameplay helpers, and a few unused playbot/help/settings helpers, reducing non-runtime surface area without changing live behavior.
- Vulture bucket-1 pruning follow-up (2026-03-30): the current high-confidence UI/tooling sweep no longer carries stale topology-lab imports, unused workspace/helper card functions, unused camera-hint fields, orphaned projection/control-icon cache debug helpers, or dead pause/governance helpers, and the non-test `vulture src cli scripts tools --min-confidence 80` pass is again limited to the remaining verify-first surfaces rather than obvious internal leftovers.
- Dead-wrapper retirement follow-up (2026-03-30): the old topology-lab preview/sidebar/probe-control compatibility helpers and a small set of row-adjustment wrapper functions are now retired entirely instead of being kept alive through test-only seams, and the matching defunct tests were removed or rewritten to assert real owner modules rather than reconstructed dead wrapper behavior.
- Topology-playground sandbox-neighbor mouse-toggle follow-up (2026-03-29): the Sandbox `Neighbors` control row now toggles directly on mouse click in the modern shell instead of only selecting the row, and focused `3D` / `4D` workspace coverage now pins that click path so neighbor markers can be disabled without relying on keyboard row adjustment.
- Topology-playground sandbox-move latency fix follow-up (2026-03-30): Sandbox movement in `AUTO` rigid-play mode no longer forces a fresh full rigid-playability scan while the canonical analysis is still in the deferred `analyzing` state, so `4D` Sandbox moves now reuse the pending analysis state instead of stalling for seconds per move.
- Topology-playground compact-footer action fit follow-up (2026-03-30): the compact shell footer now reserves enough action-lane width for the six-button Sandbox action set so labels such as `Next Piece` and `Show Path` stay visible under the current compact-width layout contract and CI text-fit checks.
- Topology-playground seam-edit help follow-up (2026-03-30): the current `Editor` seam workflow is now documented both as a dedicated `docs/help/TOPOLOGY_PLAYGROUND_SEAM_EDITING.md` guide and as a runtime help topic available through the existing launcher/pause help flow, with wording aligned to the live source-boundary -> target-boundary -> transform -> `Apply` implementation.
- Keybinding defaults redesign follow-up (2026-03-30): the canonical built-in keybinding defaults now use a compact standard-first gameplay movement cluster, a fixed negative-left / positive-right rotation ladder (`RT FG VB YU HJ NM`), shared 3D/4D number-row camera core positions for yaw/pitch/zoom/cycle/reset, an explicit 4D reset on `0`, and deconflicted system defaults (`P` / `F10` menu, `X` restart) so the shipped layouts remain conflict-safe without changing saved user profiles.
- Dead-seam cleanup follow-up (2026-03-31): another dead-code sweep removed uncalled gameplay/runtime wrapper helpers, test-only help-topic/help-text validator seams, the unused pygame key-profile alias, and the test-only menu-graph linter module; focused tests now target the live help-text/help-topic owners directly instead of preserving those dead wrappers, while `launcher_play` remains an active launcher seam used by `cli/front.py`.
- Dead-test cleanup follow-up (2026-03-31): cache-debug tests tied only to projection/control-icon internals are now removed, direct test-only calls to unused camera/view keydown wrappers now assert the live key-routing helpers instead, and topology-lab sandbox rotation setup now probes rotatable pieces through real sandbox key dispatch instead of a dead private rotation helper seam.
- Topology-playground exploration return-menu follow-up (2026-03-30): topology-playground-launched `Explore This Topology` now treats the gameplay `menu` action as a direct return to the main playground shell instead of opening the generic independent pause menu first, while ordinary launcher gameplay keeps the existing pause flow.
- Windows packaging hardening follow-up (2026-04-12): the WiX-generated
  Windows installer still embeds its cabinet payload into the published
  `.msi`, but the packaging script now also clears stale `*.msi` / `*.cab`
  outputs before each run, builds into `build/packaging/windows/out`, fails if
  the expected MSI is missing, and fails if any external `*.cab` appears
  anywhere under `build/packaging/windows`; the release workflow correspondingly
  uploads only `*.msi` from the Windows job so stale or stray CAB files cannot
  leak into published artifacts.
- Dead-code cleanup follow-up (2026-03-31): one zero-reference test-only
  topology-lab export tuple plus unused board/menu/tutorial helper shims were
  removed, and focused regression coverage was refreshed so the current
  topology preset-value text contract continues to include the explicit
  `[unsafe]` suffix when applicable.
- Governance policy consolidation prune follow-up (2026-03-29): `config/project/policy/governance.json` and `config/project/policy/code_rules.json` are now the sole runtime policy sources for governance checks, `tools/governance/validate_governance.py` remains the unified policy gate used by `scripts/verify.sh`, and the older manifest pack is retained only as contract and inventory compatibility rather than as an execution fallback.
- Shared rotation animation mode is now a first-class shared gameplay setting rather than a hidden fallback.
- Advanced gameplay now exposes the mode selector directly, and `2D`/`3D`/`4D` runtime loop construction all load the persisted mode through `menu_settings_state.mode_rotation_animation_mode(...)`.
- Active `2D` animation overlays now clip seam-straddling cell boxes into topology-aware fragments, so rigid rotation and deliberate/cellwise tween paths both show partial geometry in each affected wrapped destination cell instead of one unsplit quad.
- Topology Playground Editor unification Stage 2 is now live for the migrated shell: the visible top-level workspace model is `Editor` / `Sandbox` / `Play`, Editor keeps its own remembered tool state, movement in Editor always updates the safe probe/selection target, and topology mutation stays behind explicit Editor-tool actions.
- Explorer Playground workspace stabilization follow-up (2026-03-20): Editor probe/dot and trace now stay live even while the Edit tool is active, Editor trace is an explicit on/off control, Sandbox focus/anchor now tracks a visible piece cell so `3D`/`4D` piece rendering survives entry and movement even when neighbor overlay is off, and the migrated shell now shows an explicit external right-side helper keyed to minimal movement/rotation guidance plus short workspace context.
- Visible shell redesign landing note (2026-03-22, reaffirmed 2026-03-29): the visible-shell redesign is now the accepted settled shell contract rather than an in-progress shell-freeze phase. The launcher first layer is `Play`, `Continue`, `Tutorials`, `Topology Playground`, `Settings`, and `Quit`; the playground shell is frozen around a compact top bar, contextual left sidebar, larger center workspace, readable minimal right helper, and compact bottom strip; and follow-up work now targets shell-preserving simplification rather than further shell redesign.
- Visible shell contract freeze follow-up (2026-03-22, reaffirmed 2026-03-29): the shell wording stays explicitly on the visible-shell redesign contract rather than the older stable-shell-cleanup wording. The compact top bar keeps `Topology Playground`, `Editor` / `Sandbox` / `Play`, and the short validity-chip contract `Valid` / `Needs Fix` / `Unsafe`; the right helper stays keys-only plus at most one short workspace/tool line and no diagnostics; and the bottom strip is constrained to compact status chips plus compact action buttons instead of prose hints.
- Launcher IA clarification pass (2026-03-22, refreshed 2026-04-12):
  `Tutorials` stays a first-class learning/support destination with explicit
  `Interactive Tutorials`, `How to Play`, `Controls Reference`, and
  `Help / FAQ` siblings, while `Settings` now routes into the shared
  `Game`, `Display`, and `Audio` categories plus direct `Keyboard Bindings`
  and `Legacy Topology Editor Menu` entries without reviving a separate
  launcher-only settings layout.
- Menu-shell unification follow-up (2026-04-12): launcher/play, settings,
  keybindings, pause, leaderboard, and bot-options now use the same shared
  title/back-chip/framed-panel/footer shell treatment, and keybindings main
  rows now render with the shared `menu_font` instead of the denser
  `panel_font`.
- Keyboard profile-management follow-up (2026-04-12): direct launcher
  `Keyboard Profiles` submenu placement is retired. Profile creation/rename/
  save/load and conflict handling remain inside the dedicated `Keyboard
  Bindings` editor, and the canonical menu tree keeps keyboard configuration
  under the shared `Settings` flow even though the normalized runtime graph
  flattens the authored `Controls` wrapper away.
- Topology Playground legacy-placement regression correction (2026-03-22, refreshed 2026-03-31): the root `Topology Playground` launcher action is again the direct modern playground entry only, while the old menu-only topology setup/editor is explicitly legacy-only and now lives only at `Settings -> Legacy Topology Editor Menu`.
- Launcher play-adjacent placement correction (2026-03-22): `Leaderboard` and `Bot` are no longer launcher-root or `Settings` entries in the visible-shell contract; they now live in the play-adjacent launcher flow while `Settings` stays focused on persistent preferences.
- Visible-shell probe contract amendment (2026-03-22): Editor `Probe` now explicitly owns a large dot render in `2D` / `3D` / `4D` plus an optional `Probe Neighbors` dot overlay derived from canonical probe state, while Sandbox keeps its separate `Neighbors` control and box-shaped piece rendering. This amendment is part of the same frozen visible-shell phase and does not reopen deeper module simplification.
- Projection probe-glyph reuse follow-up (2026-03-22): the shared `3D` / `4D` projection renderer now reuses the existing `2D` probe, trace, and probe-neighbor glyph helpers instead of maintaining a second copy of that circle/dot drawing logic, keeping the canonical probe visual language aligned across dimensions without a deeper scene-module rewrite.
- Probe guidance simplification follow-up (2026-03-22): the reduced `3D` / `4D` projection surface is intentional for the visible-shell phase. The shell now relies on the movable probe plus concise full translation-key guidance rather than the older per-panel movement-preview legends, and the shared probe trace visual language is now the connecting line without intermediate path dots.
- Direct topology-lab CLI follow-up (2026-03-22): direct Topology Playground launch is now available through the unified launcher wrapper via `cli/front.py --topology-playground [2|3|4]`, while `src/tet4d/ui/pygame/topology_lab/__main__.py` remains as a thin compatibility delegate for `python -m tet4d.ui.pygame.topology_lab [2|3|4]` with the same dimension validation.
- Explorer internal cleanup and decomposition pass (2026-03-21): workspace-shell copy/layout/helper routing now lives in `src/tet4d/ui/pygame/topology_lab/workspace_shell.py`, contextual row ownership now lives in `src/tet4d/ui/pygame/topology_lab/controls_panel_rows.py`, probe-facing action ids now use explicit Probe naming internally, and the then-remaining `inspect_boundary` / `TOOL_INSPECT` seam was demoted to explicit compatibility debt rather than preferred terminology.
- Explorer compatibility-seam retirement pass (2026-03-22): shell-facing row values/playability/context formatting now live in `src/tet4d/ui/pygame/topology_lab/controls_panel_values.py`, `workspace_shell.py` now consumes stable scene/value helpers instead of private helpers from `controls_panel.py`, probe-readiness plus pane-state selectors now live in `scene_state.py`, and that intermediate pass narrowed legacy inspect naming to a smaller compatibility surface before the final Probe-naming cleanup.
- Explorer probe-naming finalization pass (2026-03-22): canonical runtime/UI tool normalization now uses the internal tool id `probe`, the legacy serialized/input token `inspect_boundary` is accepted only at compatibility-normalization boundaries, the `TOOL_INSPECT` / `tool_is_inspect(...)` export surface is retired from the active topology-lab flow, and projection info-panel wording now deliberately says `Probe`.
- Explorer probe-storage retirement pass (2026-03-22): `src/tet4d/ui/pygame/topology_lab/scene_state.py` no longer retains the raw shell probe trio (`probe_coord`, `probe_trace`, `probe_path`) at all, so canonical probe selectors and canonical probe-state writes are now the only explorer-path probe authority on the migrated shell; the remaining shell-owned caches are `play_settings`, `sandbox`, `active_tool`, and `editor_tool`, all retained explicitly for launch-settings, scene/render, or tool-routing roles rather than as runtime-truth mirrors.
- Explorer profile/draft projection retirement pass (2026-03-22): `src/tet4d/ui/pygame/topology_lab/scene_state.py` no longer re-synchronizes `explorer_profile` or `explorer_draft` from canonical runtime state, so canonical selectors now own those seams outright on the migrated path while the raw shell fields survive only as fallback storage when canonical state is absent. With the later probe-storage removal, the remaining shell-owned fields are now explicitly classified as: `play_settings` true per-dimension launch-settings cache, `sandbox` true scene/render cache over canonical sandbox piece state, and `active_tool` / `editor_tool` true shell-owned workspace/tool caches synchronized immediately into canonical state.
- Manifest reconciliation and current-authority refresh (2026-03-20): `docs/plans/topology_playground_current_authority.md` is now the single current topology-playground architecture authority, while older topology-playground manifests/plans/audits are explicitly marked historical or supporting background.
- Topology-playground plan retirement follow-up (2026-03-22): the old explorer-topology phase plans, menu/startup audits, playability-signaling pass, and unsafe-topology correctness plans now live under `docs/history/topology_playground/`; the active plan layer is reduced to `docs/plans/topology_playground_current_authority.md` plus `docs/plans/topology_playground_shell_redesign_spec.md`.
- Topology-explorer clean-CI lock follow-up (2026-03-21): the committed shell/runtime contract now matches the accepted sandbox-first explorer entry and current neighbor-marker model in a clean clone as well as the dirty worktree. Workspace switching back to `Editor` preserves the remembered sandbox/topology situation, scene wrappers expose the current neighbor-marker render seam directly, and the focused topology-lab menu/projection tests now pin the current shell labels and workspace behavior instead of older Editor-first assumptions.
- Local branch integration follow-up (2026-03-21): the later local topology-explorer/gameplay work is now integrated on top of the released branch line. Historical topology-playground plan material was further demoted toward archive status, play move intents are now owned explicitly in `src/tet4d/engine/gameplay/play_move_intents.py`, and matching gameplay/input/playbot/launch coverage now rides on that explicit translation-vs-drop intent split without reopening the settled topology-playground architecture contract.
- Release follow-up (2026-04-12): the current integrated batch is being
  promoted as `0.7`, carrying the flattened shared-shell menu flow, the
  full-ND endgame relic-field update, and the hardened single-file Windows MSI
  packaging contract.

Sections with `BEGIN/END GENERATED:*` markers are maintained by
`tools/governance/generate_maintenance_docs.py`.

<!-- BEGIN GENERATED:current_state_architecture_snapshot -->
## Current Architecture Snapshot

- `arch_stage`: `900`
- Canonical local gate: `CODEX_MODE=1 ./scripts/verify.sh`
- CI wrapper: `./scripts/ci_check.sh`
- Full local gate runs are serialized by `scripts/verify.sh`, use an isolated per-run state root via `TET4D_STATE_ROOT` when no explicit override is provided, and include the CI sanitation/policy checks (`scripts/check_policy_compliance.sh`, `scripts/check_policy_compliance_repo.sh`, `scripts/check_git_sanitation_repo.sh`) so local verification matches GitHub policy enforcement.
- Dependency direction:
  - `ui`, `ai`, `replay`, and `tools` may import engine modules directly
  - `engine` must not import `ui`, `ai`, `replay`, or `tools`
  - `engine/core` remains strict-pure
<!-- END GENERATED:current_state_architecture_snapshot -->

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
## Current Metric Snapshot

From `python scripts/arch_metrics.py`:

- `deep_imports.engine_to_ui_non_api.count = 0`
- `deep_imports.engine_to_ai_non_api.count = 0`
- `deep_imports.ui_to_engine_non_api.count = 208` (allowed under current rule)
- `deep_imports.ai_to_engine_non_api.count = 27` (allowed under current rule)
- `engine_core_purity.violation_count = 0`
- `migration_debt_signals.pygame_imports_non_test.count = 0`
- `tech_debt.score = 4.72` (`low`)

Dominant remaining pressure:

1. `delivery_size_pressure = 2.17`
2. `code_balance = 1.31`
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_canonical_ownership -->
## Canonical Ownership After This Batch

### Engine

- `src/tet4d/engine/core/piece_transform.py`
- `src/tet4d/engine/core/rotation_kicks.py`
- `src/tet4d/engine/core/rules/lifecycle.py`
- `src/tet4d/engine/topology_explorer/*`
- `src/tet4d/engine/gameplay/*`
- `src/tet4d/engine/gameplay/api.py`
- `src/tet4d/engine/runtime/*`
- `src/tet4d/engine/runtime/api.py`
- `src/tet4d/engine/tutorial/*`
- `src/tet4d/engine/tutorial/api.py`
- `src/tet4d/engine/api.py (small compatibility facade for replay/tests/tutorial payload exports)`

### UI

- `src/tet4d/ui/pygame/front2d_game.py`
- `src/tet4d/ui/pygame/front2d_setup.py`
- `src/tet4d/ui/pygame/front2d_loop.py`
- `src/tet4d/ui/pygame/front2d_session.py`
- `src/tet4d/ui/pygame/front2d_frame.py`
- `src/tet4d/ui/pygame/front2d_results.py`
- `src/tet4d/ui/pygame/frontend_nd_setup.py`
- `src/tet4d/ui/pygame/frontend_nd_state.py`
- `src/tet4d/ui/pygame/frontend_nd_input.py`
- `src/tet4d/ui/pygame/front3d_game.py`
- `src/tet4d/ui/pygame/front4d_game.py`
- `src/tet4d/ui/pygame/front3d_render.py`
- `src/tet4d/ui/pygame/front4d_render.py`
- `src/tet4d/ui/pygame/topology_lab/*`
- `src/tet4d/ui/pygame/runtime_ui/*`
- `src/tet4d/ui/pygame/menu/*`
- `src/tet4d/ui/pygame/launch/* (with settings_hub_model.py owning settings model/layout, settings_hub_actions.py owning settings mutations/text-entry, and launcher_settings.py owning orchestration/view)`
- `src/tet4d/ui/pygame/render/*`

### AI

- `src/tet4d/ai/playbot/*`
<!-- END GENERATED:current_state_canonical_ownership -->

## Transform Ownership Note

- The requested piece-transform extraction plan is already complete in code.
- Canonical owner: `src/tet4d/engine/core/piece_transform.py`.
- Retrospective plan/inventory docs now exist at:
  - `docs/plans/piece_transform_extraction.md`
  - `docs/plans/piece_transform_inventory.md`
- Current `HEAD` has already progressed beyond the original extraction-stage
  non-goal and now uses center-of-piece block rotation semantics.

## Topology Playground History

- Historical topology-playground rollout details and completed stage notes now
  live under
  `docs/history/topology_playground/current_state_archive_2026-03-31.md`.
- Use `docs/plans/topology_playground_current_authority.md` for the active
  contract and `docs/BACKLOG.md` for active work only.

## What This Batch Changed

1. Folded 2D into the shared `src/tet4d/ui/pygame/` frontend structure and split
   ownership into `front2d_game.py` (orchestration), `front2d_setup.py`
   (setup/menu), `front2d_loop.py` (runtime orchestration), `front2d_session.py`
   (session/state), `front2d_frame.py` (per-frame/update), and
   `front2d_results.py` (results/leaderboard flow).
2. Moved engine-owned render/frontend adapters out of `src/tet4d/engine/` into
   UI ownership.
3. Removed all remaining reverse imports from `engine` into `ui` and `ai`.
4. Decomposed engine-owned convenience exports into
   `src/tet4d/engine/gameplay/api.py`, `src/tet4d/engine/runtime/api.py`, and
   `src/tet4d/engine/tutorial/api.py`, while keeping `src/tet4d/engine/api.py`
   as a thin compatibility facade.
5. Cut `menu_settings_state` -> UI keybinding side effects; live keybinding sync
   now happens in UI runtime/menu code.
6. Repointed AI planners/controllers/dry-run tooling to direct engine imports,
   eliminating `engine -> ai` wrapper pressure in `engine/api.py`.
7. Centralized shared rotation-with-kicks application through
   `resolve_rotated_piece(...)`, deleting duplicated first-fit application logic
   from 2D and ND gameplay states.
8. Zeroed the reverse-import metric budgets and aligned the boundary script with
   the current one-way rule.
9. Rewrote stale architecture docs so they describe the current architecture,
   not the old migration-only `engine.api` seam.
10. Moved remaining governance and render-benchmark callers off `engine.api` onto
    direct engine/UI owners, then reduced `src/tet4d/engine/api.py` to a small
    compatibility facade used mainly by replay and explicit compatibility tests.
11. Finished the 2D runtime decomposition by splitting `front2d_loop.py` into
    orchestration, session/state, frame/update, and results owners, then
    deleted `front2d_runtime.py` after migrating affected callers/tests.
12. Extracted the duplicated setup-menu event/save loop into
    `src/tet4d/ui/pygame/menu/setup_menu_runner.py` and rewired both 2D and ND
    setup flows to use it.
13. Removed duplicated settings/default wrappers from
    `src/tet4d/ui/pygame/launch/launcher_settings.py` by extending
    `src/tet4d/engine/runtime/menu_settings_state.py` and reusing
    `src/tet4d/engine/runtime/settings_schema.py` window-size helpers.
14. Finished ND frontend decomposition by splitting shared ND ownership into
    `frontend_nd_setup.py` (setup/menu/config), `frontend_nd_state.py`
    (state creation), and `frontend_nd_input.py` (gameplay/input routing), then
    deleted `frontend_nd.py`.
15. Finished settings-hub decomposition by splitting shared settings ownership
    into `settings_hub_model.py` (model/layout/defaults),
    `settings_hub_actions.py` (mutation/text-entry/save/reset), and
    `launcher_settings.py` (orchestration/view), then deleted
    `settings_hub_state.py`.
16. Split oversized engine-runtime helpers into stable facades plus smaller
    internal owners:
    - `menu_settings_state.py` over `runtime/menu_settings/`
    - `menu_structure_schema.py` over `runtime/menu_structure/`
    - `score_analyzer.py` over `runtime/score_analysis/`
17. Applied a correctness hotfix batch after the restructure: the settings hub
    now seeds analytics from persisted runtime state,
    `score_analysis_summary_snapshot()` returns detached copies, and the unused
    `dispatch_nd_gameplay_key()` helper was deleted from
    `frontend_nd_input.py`.
18. Hardened local verification against recurring Windows state collisions by
    adding a serialized `verify.sh` lock, a per-run `TET4D_STATE_ROOT` sandbox
    for full-gate runs, and env-aware pytest temp roots for Codex/local test
    helpers.
19. Converted `CURRENT_STATE.md` and `docs/PROJECT_STRUCTURE.md` to mixed
    manual/generated maintenance docs and added
    `tools/governance/generate_maintenance_docs.py` plus verify-time drift
    checks for the generated sections.
20. Added `docs/plans/cleanup_master_plan.md` as the canonical cleanup ledger and used code, not manifests, as the stage-status authority for the remaining dedup program.
21. Narrowed `src/tet4d/engine/api.py` by deleting raw piece-transform re-exports; replay/tests now consume stable engine contracts there while transform tests import the canonical kernel directly.
22. Extracted shared gameplay orchestration into `src/tet4d/engine/gameplay/lock_flow.py` (lock-analysis / score-bookkeeping) and `src/tet4d/engine/core/rules/lifecycle.py` (lock-and-respawn / hard-drop flow), then rewired `game2d.py`, `game_nd.py`, `core/rules/gravity_2d.py`, and `core/step/reducer.py` to consume those shared owners.
23. Moved keybinding path/profile/json ownership into `src/tet4d/engine/runtime/keybinding_store.py`; `src/tet4d/ui/pygame/keybindings.py` now owns runtime maps and rebinding behavior only.
24. Unified the install contract on editable install from `pyproject.toml`, removed `requirements.txt`, added `scripts/check_editable_install.sh`, and wired that smoke check into `scripts/verify.sh`.
25. Further thinned `src/tet4d/engine/runtime/menu_structure_schema.py` by moving menu graph parsing into `runtime/menu_structure/menu_parse.py` and settings/payload parsing into `runtime/menu_structure/settings_parse.py`, keeping `menu_structure_schema.py` as the stable validation facade only.
26. Reduced the fixed 4D tutorial board profile to `8 x 20 x 7 x 6` and the fixed 4D exploration board profile to `8 x 9 x 7 x 6`.
27. Unified tutorial instruction copy around one plain-language `Do this:` line, one optional `Tip:` line, and simpler `USE:` input prompts, with clearer layman wording across the 4D lesson pack.
28. Added larger dedicated 4D piece-set options (`True 4D (7-cell)` and `True 4D (8-cell)`) plus regression coverage for the new 4D bag families.
29. Added machine-checked drift protection via the `drift_protection` section in `config/project/policy/governance.json`, `tools/governance/check_drift_protection.py`, a generated `Live Drift Watch` section in `CURRENT_STATE.md`, and verify-time enforcement of thin-wrapper LOC budgets plus tutorial copy taxonomy.
30. Fixed recurring GitHub CI parity drift by restoring the executable bit on `scripts/check_editable_install.sh` and teaching `scripts/check_git_sanitation_repo.sh` to fail if any direct-run shell entrypoint in the repo loses `100755` mode in git metadata.
31. Split Topology Lab topology ownership by gameplay mode (`normal` vs `explorer`) for 3D/4D, with engine-owned validation rejecting wrapped `Y` boundaries in Normal Game while Explorer Mode persists separate topology profiles and allows bidirectional vertical traversal.
32. Added explorer-only `move_up` / `move_down` keybinding groups and routing for 2D/3D/4D exploration, removed stale `move_y_*` gameplay naming from live help/control mappings, and hid 3D/4D topology-profile setup rows so advanced topology now flows through the mode-aware Topology Lab store.
33. Added a new engine-only explorer topology kernel under `src/tet4d/engine/topology_explorer/` covering general boundary gluing descriptors, signed-permutation transform validation, move-through-boundary mapping, movement-graph compilation, and basic quotient-topology presets without switching the live runtime/UI to the new model yet.
34. Added Stage 2 runtime-owned explorer topology integration: `topology_explorer_store.py` now owns JSON save/load for general explorer gluing profiles, `topology_explorer_bridge.py` converts the representable subset of legacy explorer edge-rule profiles into the new gluing model for preview/export, `topology_explorer_preview.py` compiles and exports movement-graph previews, and Topology Lab export now emits that explorer preview when the current explorer profile is representable as a true paired-boundary gluing.
35. Added `scripts/verify_focus.sh` as the documented fast-path staged local validation helper for focused lint/tests and maintenance-doc checks while keeping `./scripts/verify.sh` as the required pre-commit/pre-push gate.
36. Replaced the legacy edge-rule editor path for Explorer 2D, Explorer 3D, and Explorer 4D inside Topology Lab with direct general-gluing editors backed by `src/tet4d/engine/runtime/topology_explorer_store.py`, engine-owned explorer presets, and live sidebar previews compiled from the explorer movement graph; Normal Game remains on the legacy lab path in this phase.
37. Added engine-owned unsafe `Projective` / `Sphere` explorer preset families for 2D/3D/4D and surfaced them in Topology Lab with explicit `[unsafe]` labeling while keeping validation canonical in `src/tet4d/engine/topology_explorer/glue_validate.py`.
38. Routed live Explorer 2D gameplay/runtime through the general gluing engine by adding `src/tet4d/engine/gameplay/explorer_runtime_2d.py`, teaching `src/tet4d/engine/gameplay/game2d.py` to use `explorer_topology_profile` for explorer movement/collision/hard-drop behavior, and updating `src/tet4d/ui/pygame/front2d_setup.py` so explorer setup resolves the stored gluing profile through the runtime-owned explorer profile model.
39. Expanded explorer preview diagnostics so `src/tet4d/engine/runtime/topology_explorer_preview.py` now exports engine-owned tangent-basis arrow mappings for each gluing, and `src/tet4d/ui/pygame/launch/topology_lab_menu.py` renders those signed basis transforms in the live lab sidebar directly from the preview payload.
40. Relaxed the newer thin-wrapper drift budgets for `cli/front.py`, `src/tet4d/engine/api.py`, and `src/tet4d/ui/pygame/front2d_game.py`, and documented a contributor-process rule preferring medium-sized localized patches over ultra-narrow patch fragmentation while keeping the core architecture/purity gates unchanged.
40a. Clarified contributor edit-method selection so `apply_patch` is reserved for localized code edits with fresh context, while broad drifting maintenance-doc rewrites use one deterministic scripted rewrite instead of repeated patch retries.
40b. Hardened contributor write-safety and verification process rules: source-file rewrites now forbid multiline PowerShell `-replace` and BOM-producing writes, require a touched-file hygiene pass after non-patch rewrites, and explicitly ban parallel `verify.sh` / `ci_check.sh` runs.
40c. Tightened edit-method escalation so dirty/generated maintenance files skip patch-first behavior, and one rejected `apply_patch` attempt on a file is now the maximum before switching to a deterministic rewrite path.
41. Replaced the explorer Topology Lab's text-only right-hand sidebar with a scene-first graphical playground built from `src/tet4d/ui/pygame/topology_lab/scene3d.py`, `scene4d.py`, `transform_editor.py`, `preview.py`, and `arrow_overlay.py`, so explorer 2D/3D/4D topology editing now starts from the graphical explorer shell rather than from a detached editor panel.
42. Added engine-backed probe traversal support to the explorer lab via `advance_explorer_probe(...)` and `explorer_probe_options(...)` in `src/tet4d/engine/runtime/topology_explorer_preview.py`, and surfaced those controls in the same graphical explorer shell so seam edits, arrows, diagnostics, and movement feedback update in one coherent scene-first playground.
43. Completed the missing scene-first topology-lab owners under `src/tet4d/ui/pygame/topology_lab/` (`scene_state.py`, `explorer_tools.py`, `boundary_picker.py`, `scene2d.py`, `piece_sandbox.py`) and reduced `src/tet4d/ui/pygame/launch/topology_lab_menu.py` to orchestration over those owners.
44. Made seam arrows directly clickable in the explorer scene, added explicit probe path state plus reset behavior, and rendered scene-visible probe trace/sandbox status for Explorer 2D/3D/4D.
45. Added explorer-only sandbox and play-preview regression coverage, including direct Explorer 2D/3D/4D launch-from-draft checks and a sandbox guard that reports non-rigid seam-crossing failures explicitly instead of silently corrupting piece motion.
46. Added `src/tet4d/engine/runtime/topology_explorer_runtime.py` as the runtime-owned resolver/export facade for explorer setup and legacy-profile preview export, and migrated `front2d_setup.py`, `frontend_nd_setup.py`, and Topology Lab export to that runtime owner so the UI no longer imports the legacy edge-rule bridge directly.
47. Unified live Explorer launch with the same scene-first topology playground shell, so Explorer 2D/3D/4D now enter `run_explorer_playground(...)` directly and use bound explorer movement inside the probe/sandbox tools instead of a separate detached explorer frontend.
48. Added `src/tet4d/ui/pygame/topology_lab/app.py` as the canonical explorer-playground launch owner, so Explorer Mode, Topology Lab, and play-preview now share one launch/config assembly path and differ only by entry context instead of by separate shell setup logic.
49. Removed topology-editor rows from the outer Explorer setup menus and made Explorer launch/export resolve the stored explorer gluing profile by default, so topology editing now lives in the unified scene-first playground shell rather than in detached setup-menu toggles.
50. Added runtime-owned Explorer experiment packs under `src/tet4d/engine/runtime/topology_explorer_experiments.py` plus a new `state/topology/explorer_experiments.json` export path, then wired the playground controls/action ribbon to build that pack from the current draft, compare it against the dimension's preset family, and show an in-shell recommended next topology.
51. Added shared atomic candidate-placement validation in `src/tet4d/engine/core/rules/piece_placement.py` and rewired `game2d.py`, `game_nd.py`, explorer runtime collision helpers, and topology-playground sandbox rotation so full-piece moves/rotations are validated and committed atomically across seam-aware runtime paths.

## Validation Status

Validation completed during this batch:

- focused cleanup slices covering `engine.api`, keybinding storage migration, and shared gameplay lifecycle/lock-flow helpers: passed
- focused `ruff check`: passed
- focused pytest batches covering the 2D split, compatibility facade, and shared kick-resolution paths: passed
- focused explorer-topology kernel tests (`test_topology_explorer.py`): passed
- focused 2D explorer runtime/setup tests (`test_game2d.py`, `test_front2d_setup.py`): passed
- focused atomic piece-placement and explorer seam parity regressions (`test_piece_placement.py`, `test_game2d.py`, `test_game_nd.py`, `test_explorer_transport_parity.py`, `test_topology_playground_sandbox.py`): passed
- focused topology-playground ownership regressions (`test_topology_playground_state.py`, `test_topology_lab_state_ownership.py`, `test_topology_lab_menu.py`, `test_topology_lab_sandbox.py`): passed
- focused explorer experiment pack checks (`test_project_config.py`, `test_topology_explorer_experiments.py`, `test_topology_lab_experiments.py`, `test_topology_explorer_preview.py`): passed
- `python scripts/arch_metrics.py`: passed with zero reverse imports
- `CODEX_MODE=1 ./scripts/verify.sh`: passed
- `CODEX_MODE=1 ./scripts/ci_check.sh`: passed

<!-- BEGIN GENERATED:current_state_drift_watch -->
## Live Drift Watch

Generated from `tools/governance/check_drift_protection.py` and `config/project/policy/governance.json`.

Top 8 live Python hotspots by real LOC:

1. `tests/unit/engine/test_topology_lab_menu.py`: `3665` real LOC
2. `src/tet4d/ui/pygame/endgame_animation.py`: `2145` real LOC
3. `scripts/arch_metrics.py`: `1887` real LOC
4. `src/tet4d/ui/pygame/topology_lab/controls_panel.py`: `1540` real LOC
5. `src/tet4d/engine/tutorial/setup_apply.py`: `1496` real LOC
6. `src/tet4d/ui/pygame/front4d_render.py`: `1313` real LOC
7. `src/tet4d/ui/pygame/render/gfx_game.py`: `1243` real LOC
8. `tools/governance/validate_project_contracts.py`: `1105` real LOC

Thin-wrapper budgets:

1. `cli/front.py: 807/840 real LOC (compatibility launcher wrapper)`
2. `cli/front2d.py: 15/24 real LOC (thin 2D launcher shim)`
3. `cli/front3d.py: 15/24 real LOC (thin 3D launcher shim)`
4. `cli/front4d.py: 15/24 real LOC (thin 4D launcher shim)`
5. `src/tet4d/engine/api.py: 91/160 real LOC (small engine compatibility facade)`
6. `src/tet4d/ui/pygame/front2d_game.py: 116/180 real LOC (2D orchestration entrypoint)`

Tutorial wording drift guard:

1. Lesson copy must not start with `Goal:` or `Action:`.
2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.
<!-- END GENERATED:current_state_drift_watch -->

## Next High-Value Follow-Ups

1. Keep trimming the runtime-engine facades (`menu_structure_schema.py`,
   `score_analyzer.py`, `menu_settings_state.py`) only if hotspot growth returns.
2. Watch `settings_hub_model.py` and `settings_hub_actions.py` for another split
   only if new feature work pushes them back into mixed responsibility.
3. Keep docs, budgets, generated references, and package manifests synchronized
   whenever ownership changes.
4. If more 2D/ND gameplay orchestration duplication remains after `lock_flow.py` and `core/rules/lifecycle.py`, extract only the next shared owner that produces net deletion.
5. Keep `engine.api` narrow and do not reintroduce raw transform or upper-layer
   convenience exports there.
6. Continue explorer topology by polishing the scene-first graphical explorer shell (especially richer 3D/4D picking/visualization), then delete the remaining legacy bridge once non-advanced explorer setup/export no longer depend on edge-rule conversion.

## Restart Checklist

1. `git branch --show-current`
2. `git status --short`
3. Read:
   - `AGENTS.md`
   - `docs/RDS_AND_CODEX.md`
   - `docs/ARCHITECTURE_CONTRACT.md`
   - `CURRENT_STATE.md`
4. Capture fresh metrics:

```bash
python scripts/arch_metrics.py
```

5. Re-run the local gate before commit:

```bash
CODEX_MODE=1 ./scripts/verify.sh
./scripts/ci_check.sh
```
