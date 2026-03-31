# Consolidated Backlog

Generated: 2026-02-18  
Updated: 2026-03-30  
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
  `config/project/policy/governance.json`
  and `config/project/policy/code_rules.json`

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

Parallel topology-playground keybinding follow-up (2026-03-30): playground
helper and shortcut surfaces should keep reading runtime binding groups rather
than reintroducing direct adapter-global ownership in topology UI modules.

Parallel topology-playground 4D binding cleanup follow-up (2026-03-30): the
playground should not retain local fallback movement bindings that contradict
the runtime 4D rotation contract, so keys like `N` must route only through
the canonical runtime-backed gameplay binding map.

Parallel help/menu-contract follow-up (2026-03-30): runtime settings help
should stay sourced from `settings_sections` rather than the older parallel
`settings_category_docs` list, and the focused keybinding contract script
should continue covering every runtime-seam consumer moved off the pygame
adapter.

- Open work:
  1. continue structural simplification of
     `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
  2. continue structural simplification of
     `src/tet4d/ui/pygame/topology_lab/scene_state.py`
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
- Do not let historical topology-playground manifests drift back into active
  authority.
- Keep canonical runtime selectors as the only explorer-path input authority.
- Keep the legacy topology editor isolated to
  `Settings -> Advanced -> Legacy Topology Editor Menu`.

## Recent Completed Work

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
- topology-explorer movement-graph fast path so preview compilation now builds
  graph edges through direct interior-step arithmetic, precomputed boundary
  seam lookups, and same-signature in-process graph-row memoization instead of
  routing every cell-step through the fully general transport resolver path
- topology-playground persistent cache completion so the same versioned
  topology cache now retains preview payloads, movement-graph rows, and rigid
  playability analysis on disk, and Advanced gameplay exposes cache measure
  plus cache clear actions for that persistent cache set
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
- windows packaging MSI embedding fix so the published Windows installer no
  longer depends on an external `cab1.cab` sidecar file at install time
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
