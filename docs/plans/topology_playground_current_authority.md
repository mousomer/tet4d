# Topology Playground Current Authority

Status: active current-authority manifest  
Last updated: 2026-03-22

Use this file first for topology-playground architecture and migration-state
questions. Older topology-playground manifests, stage plans, audits, and
historical summaries are background only unless a future task explicitly
reactivates them.

## Instruction precedence

- This manifest and any newer user or developer instruction for the current
  task take precedence over archived topology-playground manifests.
- If an archived manifest conflicts with this file, follow this file.
- If a newer instruction severely conflicts with this file or with current code
  reality, stop and reconcile first.
- Once that mismatch is clarified, update this manifest and any affected
  archive-note stubs in the same batch so the repo stays coherent.

## Accepted architecture now

- Visible and canonical top-level workspaces are `Editor`, `Sandbox`, and
  `Play`.
- `Topology Playground` is the modern current editing flow.
- The old menu-only topology setup/editor is legacy compatibility only.
- The legacy topology editor is not part of `Topology Playground`, `Explorer`,
  or `Path`.
- The legacy topology editor is reachable only through
  `Settings -> Advanced -> Legacy Topology Editor Menu`.
- Direct explorer entry opens in `Sandbox` by default. This is the accepted
  startup contract unless a future task explicitly changes it.
- `Inspect` is not a top-level workspace. It survives only as an
  Editor-internal non-mutating probe/selection flow.
- `Edit` is not a top-level workspace. It survives only as an Editor-internal
  explicit mutation flow.
- `Probe` is the canonical internal concept for the non-mutating Editor tool
  flow.
- Legacy `inspect_boundary` is accepted only at narrow compatibility
  boundaries, where it must normalize to canonical `probe`.
- Editor movement is always non-mutating, even when an edit-capable Editor tool
  is active.
- Probe movement, trace, and edit targeting must derive from the same canonical
  seam-aware Editor probe state.
- `Trace` is an Editor-owned contextual control.
- `Probe Neighbors` is a distinct Editor-owned contextual visualization option
  derived from canonical probe state.
- `Neighbors` is a Sandbox-owned contextual control.
- Explorer behavior-changing controls must not be ad hoc. They belong to
  workspace selection, workspace tool selection, workspace-owned contextual
  controls, helper display options, or status-only display.
- Sandbox is a separate piece-experimentation workspace. It does not
  implicitly mean neighbor-search.
- Play is a separate gameplay workspace. Translation legality and drop legality
  are distinct on non-trivial `Y`-seam topologies.
- Play move classes remain explicit: deliberate translation, rotation, gravity
  tick, soft drop, and hard drop must not collapse back into one generic
  seam-transport rule.
- Play groundedness and lock are based on whether one legal drop continuation
  exists under the Play drop policy, not on generic seam adjacency or generic
  transport reachability.
- Hard drop must match repeated legal drop continuation.
- Canonical runtime selectors are the only accepted explorer-path input
  authority.
- `explorer_profile` and `explorer_draft` are no longer synchronized shell
  projections on the migrated path. Canonical runtime state owns both; the raw
  shell fields survive only as fallback storage when canonical state is absent.
- Retained shell fields, where still present, are synchronized compatibility
  projections or true shell-owned caches only. They are not truth sources.

## Accepted invariants

### Editor / Probe invariants

- The legacy Inspect "dot" is the Editor probe/dot. Its movement must stay
  consistent before and after seam traversal.
- The Editor probe/dot and its trace must work consistently in `2D`, `3D`, and
  `4D`.
- Probe movement, trace, edit targeting, and probe-neighbor overlay derivation
  must stay aligned to the same canonical seam-aware Editor probe state in
  every supported dimension.
- The reduced default probe guidance in `3D` / `4D` is intentional for this
  phase: the shell only needs to make probe movement possible and show the full
  translation keys. The older per-panel movement-preview legends are not
  required by the current visible-shell contract.
- Toggling `Trace` must not disable probe movement or hide the probe/dot
  itself.
- The Editor probe must render as a dot, not as a sandbox-style box, in `2D`,
  `3D`, and `4D`.
- The probe trace visual language is now the connecting trace line itself; the
  old intermediate path dots are intentionally removed across dimensions.
- `Probe Neighbors`, when enabled, must render as smaller subordinate dots
  around the main probe and must not hide the probe/dot itself.
- Visible tool wording should prefer `Probe` for the non-mutating Editor probe
  flow.

### Sandbox invariants

- Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and
  `4D`.
- Switching from `Sandbox` to `Editor` must not discard or silently rebuild the
  current sandbox/topology situation. The same remembered topology state must
  remain available after the workspace switch.
- In `3D` and `4D`, projected sandbox piece cells must render as full piece
  boxes, not as neighbor-style dots.
- Neighbor markers must appear as small dots in `2D`, `3D`, and `4D` only when
  the Explorer `neighbor search` control is explicitly enabled.
- Neighbor markers must not appear by default, must not replace or hide the
  sandbox piece, and must remain visually distinct from sandbox piece cells.
- Sandbox `Neighbors` and Editor `Probe Neighbors` are distinct overlays with
  distinct ownership and must stay documented and implemented separately.

### Shell invariants

- Menu items and critical controls must remain fully visible; clipped, hidden,
  or unreadable items are regressions.
- The helper panel must stay visible outside the main Explorer panel / viewport
  and remain minimal: translation keys, rotation keys, and at most one short
  current workspace/tool context line.
- Helper content is not a second menu and must not become a shadow control
  surface.

## Current phase focus

The current topology-playground phase is the frozen visible-shell redesign
phase.

This phase is intentionally limited to:

- launcher first-layer menu cleanup,
- topology-playground visible-shell redesign around a compact global top bar,
  contextual left sidebar, materially larger center workspace, small external
  key helper, and compact bottom strip,
- visible-shell wording cleanup including the `Valid` / `Needs Fix` /
  `Unsafe` status-chip contract,
- diagnostics demotion behind secondary surfaces,
- and manifest/doc/test drift prevention while the visible shell contract is
  being frozen.

This phase must preserve the settled architecture rules above.
It must not reopen the accepted `Editor` / `Sandbox` / `Play` workspace model,
the accepted sandbox-first entry path, the canonical runtime-selector authority,
or the settled Play drop-policy contract.

Structural module simplification remains deferred until the visible shell
contract is stable.

## Still transitional

- Some dimension-specific Editor probe/camera behavior still rides on older
  helper layers while the migrated shell consumes canonical runtime state.
- Remaining synchronized shell projections in
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` are compatibility-only.
  They may still back explicit compatibility readers/tests, diagnostics, or
  retained shell consumers, but they must not regain explorer-path input
  authority. `explorer_profile` and `explorer_draft` are retired as
  canonical-to-shell sync outputs; boundary/seam selection, highlighted-glue
  mirrors, and the former probe shell mirror trio (`probe_coord`,
  `probe_trace`, `probe_path`) are also retired as canonical-to-shell sync
  outputs. Canonical selectors own those seams now, while the raw
  profile/draft fields survive only as fallback compatibility storage when
  canonical state is absent; the probe trio no longer exists as retained shell
  storage on the migrated path.
- Remaining shell-owned cache/projection classification after this pass:
  `play_settings` remains a true shell-owned per-dimension launch-settings
  cache mirrored into canonical launch settings; `sandbox` remains a live
  shell-owned scene/render cache over canonical sandbox piece state;
  `active_tool` and `editor_tool` remain live shell-owned workspace/tool caches
  that synchronize immediately into canonical state for menu/input/render
  routing. No retained probe fallback-storage seam remains after this pass; any
  later cache retirement work would need a separate routing/cache reassessment
  rather than another probe-shadow-state cleanup.
- The former transitional seam
  `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py` is retired.
  Legacy Normal Game row adjustment now lives as a narrow private helper path
  inside `controls_panel.py`; it must not expand back into a generic legacy
  bucket or reclaim authority over Explorer flow, row layout, row value
  presentation, or export orchestration.
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` still carry follow-up
  decomposition and compatibility debt, but that work is explicitly deferred
  until after the visible shell redesign is stable.
- Unsafe-topology cross-surface drift still exists in some paths, especially
  where sandbox behavior is stricter than gameplay or preview-invalid
  dimension-pairing behavior remains confusing.
- Some topology families still need focused Play drop-policy regression
  coverage beyond the currently pinned live-path cases.
- Historical docs may still mention removed legacy paths. Those references are
  documentation debt, not active authority.

## Superseded assumptions

- `Inspect` / `Edit` are not the primary visible top-level workspaces anymore.
- Sandbox is not implicitly neighbor mode and must not be documented or treated
  as such.
- Older Explorer-entry assumptions that the shell should open directly into
  `Editor` / `Edit` are superseded.
- Older Sandbox assumptions that workspace switching should restore a legacy
  editor-tool posture instead of preserving the current remembered situation are
  superseded.
- Generic explorer seam transport must not determine Play drop legality.
- Earlier Stage-1 continuation coverage did not fully fix the old spherical
  false-lock family; any wording that implies that is superseded.
- Older intermediate cleanup states, including the temporary four-mode
  `Edit` / `Inspect` / `Sandbox` / `Play` shell, are historical implementation
  steps rather than the current architecture.
- Retained shell fields are not active runtime truth, even when they are still
  synchronized for compatibility.

## Current active priorities

- Freeze the visible launcher first layer to `Play`, `Continue`, `Tutorials`,
- `Topology Playground`, `Settings`, and `Quit`.
- Keep `Tutorials` as the learning/support umbrella without collapsing
  tutorials, help, and controls reference into one ambiguous surface.
- Keep `Settings -> Controls` for persistent input configuration only, and keep
  controls reference/help reachable through the `Tutorials` learning/support
  surface rather than burying help inside `Settings`.
- Keep `Leaderboard` and `Bot` out of the launcher root and out of
  `Settings`; they belong to play-adjacent launch/setup flow instead.
- Freeze the topology-playground visible shell around the compact top bar,
  contextual left sidebar, larger center workspace, small right helper, and
  compact bottom strip.
- Freeze the visible-shell render contract so Editor probe rendering stays a
  large circle in `2D`, `3D`, and `4D`, probe neighbors stay subordinate dots,
  and sandbox cells remain box-shaped.
- Remove or demote old default-primary verbose status and diagnostic wording.
- Keep canonical runtime state as the only explorer-path input authority.
- Keep launcher/setup surfaces minimal for topology and keep custom-topology
  editing/play flowing through the Explorer Playground shell.
- Keep `Topology Playground` as a direct modern launcher entry with no
  modern-vs-legacy submenu split.
- Keep the legacy topology editor/menu out of `Topology Playground`,
  `Explorer`, and `Path`; expose it only through
  `Settings -> Advanced -> Legacy Topology Editor Menu`.
- Keep the direct playground entrypoint available via
  `python -m tet4d.ui.pygame.topology_lab` in addition to the launcher path.
- Update manifests/docs in the same pass as code changes, prevent drift, and
  keep local CI-equivalent checks green.

## Explicit non-goals for the next implementation phases

- Do not silently reopen the settled `Editor` / `Sandbox` / `Play` workspace
  split.
- Do not silently reopen the settled Play drop-policy distinction between
  deliberate translation and drop continuation unless a regression proves it
  wrong.
- Do not start deeper `controls_panel.py` or `scene_state.py` simplification as
  the goal of the visible-shell pass.
- Do not redesign Sandbox beyond focused visibility/framing, neighbor-toggle,
  or coupling fixes required by current regressions.
- Do not treat historical manifests as active execution authority.
- Do not let retained shell projections or transitional legacy helpers drift
  back into truth ownership.
- Do not silently leave the authority file stale after a task changes accepted
  topology-playground direction.

## Mandatory execution rules for future passes

- Update documentation and manifests in the same pass as code changes.
- Prevent drift between code, tests, manifests, generated docs, and status
  files.
- Run the repo’s governance/drift/document checks required by the project.
- Run local CI-style verification before declaring completion.
- If a full local CI command cannot run, state exactly why and run the nearest
  equivalent checks.

## Historical references

These files remain useful for background, but they are not the current
authority:

- `docs/history/topology_playground/tet4d_topology_playground_restructure_plan_codex.md`
- `docs/history/topology_playground/tet4d_spherical_false_lock_fix_manifest.md`
- `docs/history/topology_playground/topology_playground_migration.md`
- `docs/history/topology_playground/explorer_playground_unification.md`
- `docs/history/topology_playground/topology_playground_reality_audit.md`
- `docs/history/topology_playground/topology_playground_ownership_audit.md`
