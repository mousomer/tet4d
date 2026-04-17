# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-04-17  
Scope: active open backlog, governance watchlist, and compact recent change footprint.

## Current Authority

- Topology-playground architecture authority:
  `docs/plans/topology_playground_current_authority.md`
- Topology-playground visible-shell contract:
  `docs/plans/topology_playground_shell_redesign_spec.md`
- Topology-playground active debt ledger:
  `docs/plans/topology_playground_debt_register.md`
- Documentation routing authority:
  `docs/DOCUMENTATION_MAP.md`
- Governance/runtime policy authority:
  `config/project/policy_pack.json`

Older topology-playground manifests and older batch notes are historical
background only unless reactivated by a future task.

## Active Work

Current sub-batch (2026-03-29): shell-preserving topology-playground cleanup.

Parallel governance/runtime follow-up (2026-03-30): keybinding authority
unification around `config/keybindings/catalog.json`, so help/editor/control
group structure and keybindings section-menu copy no longer drift away from
the live runtime binding map.

Parallel contract-hardening follow-up (2026-03-30): keybinding defaults and
saved profile payloads now need one catalog-backed validator so direct config
edits and persisted overrides fail fast on stale action/group/dimension
references instead of degrading silently at runtime.

Parallel runtime-ownership follow-up (2026-03-30): the remaining keybinding
mutable-state seam needs to live under engine/runtime rather than the pygame
adapter, while built-in defaults gain full required-action coverage checks,
saved payloads gain explicit schema versioning, and config-only keybinding
work gets a focused contract-check script.

Parallel runtime-accessor follow-up (2026-03-30): UI callers that only need
live grouped bindings or active-profile reads should consume narrow
engine/runtime accessors instead of importing the broader pygame keybinding
adapter.

Parallel frozen-keybinding-path follow-up (2026-04-15): startup/profile
cleanup must continue honoring the split-root contract where bundled defaults
stay under the read-only packaged `keybindings/` tree and writable profile
directories live under the per-user data root, without weakening the runtime
path-containment guard for files outside those canonical roots.

Parallel release-packaging smoke follow-up (2026-04-15): release packaging
must continue exercising packaged runtime initialization on each target OS
before emitting installers, and frozen writable-path regression coverage
should keep the `project_config` / keybinding-store seam under direct test
instead of only validating those contracts in isolation.

Parallel topology-playground keybinding follow-up (2026-03-30): playground
helper and shortcut surfaces should keep reading runtime binding groups rather
than reintroducing direct adapter-global ownership in topology UI modules.

Parallel topology-playground 4D binding cleanup follow-up (2026-03-30): the
playground should not retain local fallback movement bindings that contradict
the runtime 4D rotation contract, so keys like `N` must route only through
the canonical runtime-backed gameplay binding map.

Parallel help/menu-contract follow-up (2026-04-12): runtime settings help
should stay sourced from the canonical `settings_root` subtree in
`config/menu/structure.json` rather than older parallel section docs, and the
focused keybinding contract script should continue covering every runtime-seam
consumer moved off the pygame adapter.

Parallel menu-shell follow-up (2026-04-10): the shared launcher/setup/pause/
settings/keybindings shell now has one aligned title/back/panel style, and
future tweaks should stay incremental, keep subtitle-free headers, keep
bounded numeric rows on sliders, and avoid drifting translation labels or the
gameplay-owned transparency setting back toward the older split layout.
Parallel slider-row follow-up (2026-04-11): larger menu sliders now rely on a
shared config-backed label/value/track allocation contract, so future slider
size changes must keep launcher/setup/in-game compact-width text visibility
aligned instead of reintroducing per-screen row geometry drift.

Parallel policy-pack hardening follow-up (2026-04-17): repo governance now
keeps policy data in `config/project/policy_pack.json`, keeps
`docs/WORKFLOW_CODEX.md` as the human workflow explainer with explicit
context-switch profiles, keeps `CURRENT_STATE.md` handoff-only, and keeps
reusable generated ownership/source-of-truth/verification inventories in
`docs/PROJECT_STRUCTURE.md` instead of duplicating them across validator code
or restart docs.

Batch 3 progress (2026-04-17): topology-playground explorer row mutation and
seam-edit helpers now live in
`src/tet4d/ui/pygame/topology_lab/controls_panel_actions.py`, keeping
`controls_panel.py` focused on shell/input/launch orchestration while
preserving deferred rigid playability analysis and same-signature cache reuse.

Batch 4 progress (2026-04-17): topology-playground state ownership is now
split so `scene_state.py` keeps the state model plus pane/tool/workspace
routing, `scene_state_canonical.py` owns canonical runtime sync/write and
fallback storage handling, and `scene_state_probe.py` owns probe selectors,
probe mutations, and probe-state synchronization without moving deferred
preview/playability work out of `scene_preview_state.py`.

- Open work:
  1. continue structural simplification of remaining
     `src/tet4d/ui/pygame/topology_lab/controls_panel.py` shortcut/export/
     launch orchestration without moving visible-shell ownership
  2. continue structural simplification of remaining
     `src/tet4d/ui/pygame/topology_lab/scene_state.py` routing/facade code and
     any still-thick compatibility seams without collapsing the new
     `scene_state_canonical.py` / `scene_state_probe.py` ownership split
  3. continue startup/refresh latency cleanup around deferred rigid
     playability analysis and signature-based cache reuse without reopening the
     shell contract
  4. keep the shell-layout/text-visibility contract intact across Topology
     Playground, pause/settings/help, tutorial overlays, and gameplay side
     panels
  5. keep diagnostics explicitly secondary rather than default-primary in any
     future topology-playground shell follow-up
  6. continue compatibility-debt reduction without reopening runtime authority,
     launcher IA, or the frozen visible shell

- Acceptance bar:
  1. `Topology Playground` remains the direct modern launcher entry
  2. visible workspaces remain `Editor` / `Sandbox` / `Play`
  3. top bar remains limited to title, workspace tabs, validity chip, and the
     current dimension chip
  4. left sidebar remains limited to the accepted `Editor` / `Sandbox` /
     `Play` inventories, with diagnostics collapsed or secondary
  5. helper stays minimal and external, diagnostics stay secondary
  6. required UI text remains visible and unobscured at supported compact sizes
  7. first-frame explorer startup no longer waits for the full rigid
     playability scan, and same-signature refreshes reuse cached playability
     results
  8. `CODEX_MODE=1 ./scripts/verify.sh` stays green

## 3. Active Open Backlog / TODO

Compatibility mirror for legacy backlog validators. The active execution view
remains the compact sections above.

Cadence: update this mirror whenever the active sub-batch or validation
contracts change.
Trigger: topology-playground runtime work, governance/contract work, or any
batch that changes active acceptance criteria.
Done criteria: the compact backlog stays accurate, this compatibility mirror
stays synchronized, and the contract validator accepts the backlog shape.

1. `WATCH` `[BKL-P3-001]` Backlog contract compatibility:
   keep the compact backlog structure aligned with the still-enforced legacy
   backlog validator until the maintenance contract is updated to the newer
   compact format.
2. `ACTIVE` `[BKL-P3-009]` Topology-playground startup/runtime latency:
   preserve deferred rigid playability analysis, signature-based cache reuse,
   and launch-time forced completion without reopening the frozen shell
   contract.

## Governance Watchlist

- Keep docs/manifests/current-state/backlog synchronized in the same batch as
  code changes.
- Keep generated maintenance docs current after status-layer edits.
- Keep policy inventories in `config/project/policy_pack.json`, not in
  `tools/governance/validate_project_contracts.py`.
- Keep `CURRENT_STATE.md` limited to restart handoff material; do not
  reintroduce batch ledgers or validation transcripts there.
- Keep `docs/WORKFLOW_CODEX.md` context-switch profiles explicit and aligned
  with the current authority stack.
- Do not let historical topology-playground manifests drift back into active
  authority.
- Keep canonical runtime selectors as the only explorer-path input authority.
- Keep the `controls_panel_rows.py` / `controls_panel_values.py` /
  `controls_panel_actions.py` split intact; do not drift non-shell explorer
  mutations back into `controls_panel.py`.
- Keep the `scene_state.py` / `scene_state_canonical.py` /
  `scene_state_probe.py` split intact; do not drift canonical sync/write or
  probe normalization back into one mixed state file.
- Keep the legacy topology editor isolated to
  `Settings -> Legacy Topology Editor Menu`.
- Keep the shared menu shell aligned across launcher, setup, pause, settings,
  keybindings, leaderboard, and bot options; do not reintroduce subtitle-only
  header variants or move `display_overlay_transparency` back out of gameplay
  settings, and keep the launcher/pause input-config surface consistently
  labeled `Keybindings`.
- Keep keyboard configuration inside the shared `Settings` flow, and do not
  reintroduce a parallel launcher-only keyboard-profiles submenu or revive the
  authored `Controls` wrapper as a visible one-item runtime page.

## Recent Completed Work

Completed on 2026-04-17:

- shell-preserving topology-playground state cleanup so `scene_state.py` now
  keeps the state model plus pane/tool/workspace routing, while
  `scene_state_canonical.py` owns canonical runtime sync/write and fallback
  storage handling and `scene_state_probe.py` owns probe selectors/mutations
  and probe-state synchronization without reopening the shell contract or the
  deferred preview/playability ownership in `scene_preview_state.py`
- shell-preserving topology-playground cleanup so explorer row-mutation and
  seam-edit helpers now live in
  `src/tet4d/ui/pygame/topology_lab/controls_panel_actions.py`, dropping
  `controls_panel.py` to a smaller shell/orchestration owner while preserving
  deferred rigid playability analysis, same-signature cache reuse, and the
  existing launcher/test compatibility seams
- post-policy-pack hardening so `CURRENT_STATE.md` is restart-only again,
  `docs/WORKFLOW_CODEX.md` now defines explicit `review` / `engine` /
  `menu_ui` / `topology_explorer` / `packaging` / `governance` / `handoff`
  context-switch profiles, and project-contract validation now reads menu and
  policy-index inventories from `config/project/policy_pack.json` instead of
  Python literals

Completed on 2026-04-15:

- frozen packaging follow-up so the canonical PyInstaller spec now includes
  hidden imports for the lazy `tet4d.ai.playbot.*` package surface, preventing
  Windows frozen launcher/setup imports from failing on missing
  `tet4d.ai.playbot.dry_run`

Completed on 2026-04-12:

- flattened the authored launcher/settings menu tree so `Play` keeps same-row
  `Play` / `Setup` actions, `Settings` removes the old single-child wrappers,
  and `Game` absorbs gameplay-adjacent micro-pages into one shared scrolling
  settings surface
- unified remaining menu-family stragglers such as leaderboard and bot options
  onto the shared shell treatment, while keybindings now uses the same menu
  typography family as the rest of the launcher/settings/pause shell
- upgraded the endgame relic field so persistent motion, topology behavior,
  speed controls, and optional collisions all operate on true ND relic state
  before projection instead of flattened post-process drift
- hardened Windows release packaging so stale MSI/CAB outputs are cleaned
  before each build, external CAB emission is a hard build failure, and the
  release workflow uploads only MSI artifacts from Windows jobs

Completed on 2026-04-10:

- dedicated post-terminal endgame animation phase so `2D`, projected `3D`,
  and projected `4D` gameplay now freeze a final board snapshot, drive locked
  cells and shell/frame fragments from deterministic seeded fragment state
  instead of live-board mutation, and keep leaderboard/session completion tied
  to the completed terminal transition rather than the first raw `game_over`
  tick
- leaderboard contract cleanup so leaderboard prompts now trigger only on
  completed standard-play `game_over` transitions, never from explorer mode or
  quit/menu/restart exits, and persisted score storage now keeps the top `10`
  entries per gameplay dimension instead of one mixed global cap
- projected `3D` / `4D` active-piece occlusion pass so board gridlines and
  board-box edges now resolve against the active piece per projected fragment
  from screen overlap plus projected depth instead of one global draw-order

Completed on 2026-04-11:

- post-terminal relic-field follow-up so the endgame now splits into finite
  `endgame_shatter` and persistent `endgame_relic_field` phases, shell/grid/
  box fragments die after the rupture, and locked-cell debris is captured into
  deterministic bounded orbit/drift families instead of continuing as one-shot
  ballistic spray
- endgame preset follow-up so the persistent relic field now freezes a shared
  preset id plus a separate interaction mode into the endgame snapshot,
  supports the required `wrap_all`, `invert_all`, and `sphere` topology-flavored
  motion fields, and exposes those controls together under
  the `Settings -> Game` endgame section instead of scattering them across new
  menus or multiplying preset ids for collision variants
- leaderboard registration now stays in the post-terminal gameplay flow as a
  compact modal overlay on top of the existing endgame surface instead of
  taking over the screen as a dedicated full-page prompt, while preserving the
  same form-state and persistence authority
- shared menu-slider layout correction so launcher, setup, and in-game slider
  rows now use one larger config-backed slider geometry contract with explicit
  label/value/track allocation, preventing clipping in supported compact menu
  shells instead of relying on per-screen width guesses

Completed on 2026-04-12:

- canonical menu-source-of-truth pass so `config/menu/structure.json` now
  defines the launcher tree, pause tree, settings hierarchy, the flattened
  scrolling `Game` page, keyboard bindings placement, retained legacy
  placement, and the typed row/component model
  without parallel Python-owned settings sections or launcher routes
- shared menu-overflow pass so settings, keybindings, and bot options now use
  one auto-scrolling viewport with reserved scrollbar width, selection
  visibility enforcement, and shared scrollbar geometry instead of clipping
  oversized menus off-screen
- settings IA flattening pass so `Settings -> Game` is now one scrolling page
  with `Gameplay`, `Board / Geometry`, `Movement / Rotation`,
  `Endgame Effects`, and `Difficulty / Pace` sections instead of a submenu
  forest
- menu normalization pass so runtime launcher/settings/keybindings consumers
  now read a compiled normalized graph rather than the raw authored menu tree,
  singleton wrappers are collapsed before render/input use, and the one-row
  `Visual / Animation` page no longer survives as a visible runtime submenu
- authored menu-flattening + direct-play pass so `config/menu/structure.json`
  now drops the settled `Controls`, `Legacy`, and one-row `Visual /
  Animation` wrappers entirely, `Play -> 2D/3D/4D` uses same-row
  `Play` / `Setup` action groups instead of another layer, direct `Play`
  launches from persisted settings, and `Setup` still routes through the
  existing setup screens before using the same gameplay launch path
- ND endgame-motion pass so persistent relic updates now advance and collide in
  ND state before projection, `wrap_all` / `invert_all` / `sphere` differ by
  ongoing ND boundary behavior rather than only start layout, 4D relics can
  traverse hidden axes and blend across frozen layer boards, and the `Game`
  page now includes separate `Relic field speed` and `Shatter speed` controls
  instead of baking speed into preset identity
- shared menu-shell completion pass so leaderboard and bot options now render
  on the same title/back-chip/framed-panel/footer shell as the other menu
  surfaces, and keybindings main rows now use the shared menu typography
  instead of a separate panel-font treatment
- post-terminal cleanup follow-up so the helper side panel no longer repeats a
  separate `GAME OVER` label and the frozen endgame fragments remain visible
  indefinitely instead of fading away after a fixed lifetime
  assumption, with shared primitive emission/resolution coverage and `2D`
  intentionally left on its simpler path


Completed on 2026-03-29:

- compact governance + planning layer consolidation around
  `docs/DOCUMENTATION_MAP.md`, the reduced active plan layer, and the unified
  governance/code-rules manifests
- topology-playground explorer board-size floor update so explorer height can
  now be reduced from `8` to `6` without reopening the frozen shell contract
- topology-playground preset naming alignment so the all-wrap `3D` and `4D`
  explorer presets now surface explicitly as torus presets while preserving
  stable compatibility ids
- topology-playground local preview cache pass so identical explorer preview
  signatures can reuse a versioned repo-local on-disk cache under `state/`
  instead of rebuilding movement graphs every run
- dead-seam cleanup pass so unused gameplay/runtime wrapper helpers,
  test-only help/menu validation seams, and the test-only menu-graph linter
  no longer stay alive through isolated unit-test coverage; `launcher_play`
  remains a live launcher dependency and is not part of that removal set
- dead-test cleanup pass so cache-debug tests no longer pin projection/control
  icon internals, camera/view key smoke now exercises live routing helpers
  instead of dead wrapper entrypoints, and topology-lab sandbox tests no
  longer depend on a dead private rotation helper
- topology-explorer movement-graph fast path so preview compilation now builds
  graph edges through direct interior-step arithmetic, precomputed boundary
  seam lookups, and same-signature in-process graph-row memoization instead of
  routing every cell-step through the fully general transport resolver path
- topology-playground persistent cache completion so the same versioned
  topology cache now retains preview payloads, movement-graph rows, and rigid
  playability analysis on disk, and Advanced gameplay exposes cache measure
  plus cache clear actions for that persistent cache set
- topology-playground cache-miss warning fix so absent repo-local explorer
  preview cache files now behave as ordinary silent misses while corrupt
  existing cache files still use the existing warning-and-rebuild path
- topology-playground/layout visibility pass so compact sidebar rows and
  Advanced gameplay rows now wrap label/value text instead of obscuring it,
  shared action buttons/workspace tabs now wrap instead of hard truncating,
  and the external helper lane keeps a wider readable budget on supported
  compact shells
- topology-playground helper-panel redesign so the right helper now renders as
  a minimal structured controls card with one short workspace/tool context
  line plus movement and rotation keys pulled from the current active
  keybindings for the active dimension
- topology-playground text-layout dedup so shared wrapped-text primitives now
  handle row sizing plus centered compact-label rendering for launcher
  settings rows, Topology Playground rows, workspace tabs, and transform /
  action buttons instead of keeping near-duplicate wrapping logic in each
  caller
- topology-playground row-render dedup so launcher settings and Topology
  Playground control rows now share the same selection-highlight and wrapped
  label/value text renderer instead of maintaining parallel drawing loops
- topology-playground panel/text dedup so helper/preview cards and centered
  launcher title/status/hint lines now reuse shared framed-panel and fitted
  centered-text helpers instead of repeating local drawing boilerplate
- topology-playground compact-chip dedup so top-bar validity/dimension chips
  and footer helper chips now reuse one shared centered chip renderer instead
  of repeating local fit-center-border badge drawing logic
- topology-playground fitted-text cleanup so remaining shell title/header and
  compact control-label callers now route through the shared fitted-text
  helpers instead of keeping local fit-text render boilerplate
- topology-playground duplicate-panel cleanup so local framed-panel and
  fitted-text helpers in projection/transform surfaces now use the existing
  shared pygame UI primitives instead of keeping separate caller-local
  drawing helpers
- topology-playground dead-code cleanup so the shared side-panel and modern
  explorer-workspace paths no longer carry unused parameters, and the current
  `vulture` sweep is back to clean high-confidence results
- launcher settings split fix so top-level `Game`, `Display`, and `Audio`
  entries now open category-specific settings screens instead of reopening the
  bundled hub behind separate labels
- launcher settings IA cleanup so the `Advanced` submenu is retired, `Legacy
  Topology Editor Menu` moves up to the main settings level, and the old
  `Game -> Advanced gameplay...` sub-flow is retired in favor of an inline
  `Advanced gameplay` section inside the game settings screen
- launcher settings config-authority cleanup so settings section
  titles/subtitles/header membership/row ownership and launcher category
  routes now live in `config/menu/structure.json`, top-level settings policy
  now derives from that same section contract, bad section header/row
  references now fail validation instead of degrading filtered settings
  screens, and launcher/settings Python is reduced to validated
  config-driven rendering and dispatch
- repo documentation follow-up so menu graph and filtered settings edits now
  have a dedicated contributor guide in `docs/MENU_STRUCTURE_EDITING.md`,
  with docs routing and menu-structure RDS copy updated to match the current
  config-first contract
- keybinding contract-hardening follow-up so `config/keybindings/defaults.json`
  and saved profile payloads are now validated against the same
  catalog-backed action/group/dimension contract, and direct config edits now
  have a dedicated contributor guide in `docs/KEYBINDINGS_EDITING.md`
- keybinding runtime-ownership completion so mutable live keybinding maps now
  sit in `src/tet4d/engine/runtime/keybinding_runtime_state.py`, built-in
  defaults enforce complete required-action coverage, payloads now carry an
  explicit schema version, partial custom profile overrides remain allowed by
  contract, and `./scripts/check_keybinding_contract.sh` now provides the
  focused validation path for direct keybinding config work
- keybinding runtime-accessor cleanup so engine/runtime now exports narrow
  keybinding read accessors and the help/tutorial/control/setup callers that
  only need runtime grouped bindings or active-profile reads no longer depend
  on the wider pygame keybinding adapter
- keybinding docs follow-up so contributors now have both the full
  `docs/KEYBINDINGS_EDITING.md` contract guide and a shorter
  `docs/SHORT_KEYBINDINGS_GUIDE.md` checklist for common direct config edits
- keybinding config-format follow-up so defaults and saved payloads now accept
  readable key-name strings in addition to integer keycodes, with the store
  normalizing them before runtime use and docs explaining the allowed forms
- keybinding stale-source cleanup so dead legacy defaults code is removed and
  the obsolete `keybindings/profiles/small/` built-in directory is purged at
  startup instead of silently coexisting with the canonical root `keybindings/*.json`
- keybinding round-trip repair so every serialized keypad token written by the
  runtime is accepted again at load/validation time, and invalid custom
  profiles now surface a hard load failure instead of broad silent overwrite
- dead-code pruning follow-up so another small set of unreferenced helpers and
  stale compatibility leftovers now drops out of playbot, core, gameplay,
  help, settings, and topology-lab code without changing live behavior
- `vulture` bucket-1 pruning follow-up so the obvious non-test UI/tooling
  leftovers identified by the current high-confidence sweep are removed before
  any deeper verify-first or public-bridge pruning pass
- dead-wrapper retirement follow-up so test-only topology-lab sidebar/preview/
  probe-control seams and their wrapper-pinning tests are removed instead of
  preserved as fake compatibility surfaces
- config-reference/theme follow-up so `config/ui/theme.json` now participates
  in the generated configuration reference, project-config tests now pin theme
  color fallback/validation behavior, and topology-playground color reads stay
  lazy at the UI seam instead of freezing once at import time
- topology-playground sandbox-neighbor row click fix so the modern shell now
  toggles Sandbox `Neighbors` directly on mouse click in `3D` / `4D` instead
  of requiring keyboard row adjustment to disable the overlay
- topology-playground sandbox auto-move latency fix so Sandbox moves no longer
  force a full rigid-playability rescan while the canonical analysis is still
  pending in `AUTO` mode
- topology-playground compact footer action-lane sizing fix so the six-button
  Sandbox footer keeps labels like `Next Piece` and `Show Path` visible under
  the compact shell layout tested in CI
- topology-playground authority/spec/status/menu alignment around the settled
  modern `Topology Playground` contract and legacy-editor placement
- shared menu-shell rework so launcher/setup/pause/settings/keybindings now
  share title-cased subtitle-free headers, visible `Back` affordances,
  bounded numeric sliders, flash-on-change row feedback, bulkier title-font
  selection, and slightly more Tron-1982-inspired panel/background treatment
- topology-playground shell-layout extraction plus deterministic cross-surface
  text-visibility coverage
- topology-playground preview/cache extraction and shared canonical-state
  write-path cleanup
- topology-playground deferred rigid-playability caching pass, including
  same-signature reuse and profiler-script repair
- topology-playground compact-shell readability pass for sidebar/helper width
  allocation and wrapped helper copy
- topology-playground seam-edit help pass so the current Editor seam workflow
  is now documented both in `docs/help/TOPOLOGY_PLAYGROUND_SEAM_EDITING.md`
  and in the shared launcher/pause help topic registry
- topology-playground exploration return-menu fix so `Explore This Topology`
  now exits directly back to the main playground shell on `menu` instead of
  opening the generic independent gameplay pause menu first
- windows packaging hardening pass so the published Windows installer is
  enforced as one self-contained `.msi`, stale `*.msi` / `*.cab` outputs are
  cleaned before each run, external CAB emission now fails the Windows build,
  and the release workflow uploads only Windows `*.msi` artifacts
- dead-code cleanup pass removing zero-reference board/menu/tutorial helper
  shims plus the unused topology-lab `_TEST_COMPAT_EXPORTS` tuple
- built-in keybinding defaults redesign so shipped movement uses a compact
  standard-first cluster, rotation uses the fixed `RT FG VB YU HJ NM` ladder,
  and 3D/4D camera defaults now share the same core number-row layout with an
  explicit 4D reset on `0`
- built-in keybinding materialization fix so startup now refreshes stale
  built-in profile JSON files from the current shipped defaults payload
  instead of silently consuming older on-disk movement/rotation/camera
  layouts
- final governance-pack prune after unified manifest cutover, including
  maintenance-doc regeneration and local gate re-verification

## 5. Change Footprint

Current batch:

- runtime/UI split of immediate preview sync versus deferred rigid playability
  analysis
- signature-based playability cache reuse plus launch-time forced completion
- movement-graph resolver reuse inside preview compilation
- movement-graph interior/boundary fast path plus same-signature in-process
  graph-row memoization
- persistent topology cache coverage for preview payloads, movement-graph
  rows, and rigid-playability analysis plus Advanced-menu cache
  measure/clear actions
- wrap-aware compact row rendering for Topology Playground controls and
  Advanced gameplay settings plus a wider helper-lane budget
- minimal structured helper-panel rendering sourced from live current
  movement/rotation keybindings instead of a generic wrapped hint stack
- shared wrapped-text primitives for compact rows and centered button labels
  reused across launcher settings and Topology Playground surfaces
- shared highlighted row renderer for launcher settings and Topology
  Playground wrapped label/value rows
- shared framed-card and centered fitted-text helpers reused by helper/preview
  cards and launcher title/status/hint lines
- shared centered chip helper reused by Topology Playground top-bar and footer
  badge rendering
- further adoption of shared fitted-text helpers across Topology Playground
  shell title/header and compact control labels
- replacement of remaining caller-local projection/transform panel helpers
  with the existing shared pygame UI primitives
- removal of dead shared-panel and explorer-workspace parameters confirmed by
  `vulture`
- launcher settings-hub category filtering plus launcher action routing for
  separate `Game` / `Display` / `Audio` entry screens
- retirement of the launcher `Advanced` submenu plus inlined advanced
  gameplay rows directly inside the game settings screen
- compact-shell layout rebalance for control rows and helper lane readability
- profiler-script repair for the current topology-playground startup path
- focused playability/menu tests plus authority/status doc synchronization

## Historical Milestones

March 2026 milestones retained here as compact orientation only:

- 2026-03-22:
  visible-shell redesign locked for launcher + Topology Playground, with
  direct `Topology Playground` entry and legacy editor isolation
- 2026-03-20 to 2026-03-21:
  `Editor` / `Sandbox` / `Play` workspace model stabilized, sandbox-first
  entry locked, helper/neighbor/probe contracts clarified, and focused menu /
  projection / gameplay tests aligned
- 2026-03-17 to 2026-03-19:
  shared gameplay animation settings expanded and threaded through 2D/3D/4D
  runtime setup
- 2026-03-12 to 2026-03-14:
  canonical-state migration deepened across launch, probe, sandbox, unsafe
  topology handling, playability signaling, and play launch semantics
- 2026-03-10 to 2026-03-11:
  early topology-playground staged migration and sandbox/runtime ownership
  movement landed

For detailed historical implementation notes, use:

- `CURRENT_STATE.md`
- `docs/history/DONE_SUMMARIES.md`
- `docs/history/topology_playground/`
