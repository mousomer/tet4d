# Topology Explorer Menu Cleanup Pass 1

Status date: 2026-03-12
Status source of truth: [`docs/history/topology_playground/topology_explorer_menu_audit.md`](docs/history/topology_playground/topology_explorer_menu_audit.md)
Current migration status authority: [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
Historical migration audit: `docs/history/topology_playground/topology_playground_reality_audit.md`
Historical design intent only: `docs/history/topology_playground/topology_playground_migration.md`

## Scope

This pass implements the audit's next ambiguity-reduction stage only. It does
not reopen completed migration stages, and it does not broaden into engine
changes, startup work, or a shell redesign.

## Canonical Visible Surfaces Chosen

- Preset selection: `Analysis View` `Explorer Preset` remains the canonical
  visible preset control for the migrated explorer/editor path.
- Save/export/experiments/back: `Analysis View` rows remain the canonical
  administrative command surface for the migrated explorer/editor path.
- Scene action bar: now reserved for seam/tool actions plus the real direct
  `Play This Topology` launch action.

## Controls Clarified, Removed, Or Demoted

- Removed the visible transform-editor preset `<` / `>` control surface from
  the migrated path.
- Replaced the transform-editor preset pill with a read-only
  `Preset (Analysis View)` display so it no longer reads like a dead button.
- Removed duplicated `Save`, `Export`, `Experiments`, and `Back` buttons from
  the workspace action bar while keeping those functions in `Analysis View`.
- Relabeled the tool-ribbon `Play This Topology` toggle as `Play Mode` so it
  reads as a mode instead of an immediate launch command.
- Made `Selected Boundary`, `Selected Seam`, and `Draft Transform` display-only
  status rows by styling them as read-only state and excluding them from row
  selection.
- Relabeled the modern/legacy branch chooser as `Workspace Path`, labeled
  `Normal Game` as `legacy compat`, and renamed retained legacy rows to
  `Legacy Preset` / `Legacy Topology`.
- Added explicit footer labels so the shared movement grid now reads
  `Probe moves` or `Sandbox piece moves` depending on the active tool.

## Ambiguity Still Remaining

- Internal `preset_step` handling still exists for compatibility, even though
  the migrated UI no longer renders that duplicate preset surface.
- The retained `Normal Game` compatibility rows and resolved-profile export are
  still present intentionally; this pass demotes them but does not delete them.
- `Play Mode` is still a mode/toggle that arms later launch behavior rather than
  a dedicated play-only workspace panel.
