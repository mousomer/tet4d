# Plan Report: Help And Menu Restructuring (2026-02-19)

Status: Proposed (not implemented in this document)  
Related backlog items: `BKL-P2-006`, `BKL-P2-007`

## 1. Objective

Produce a concrete restructuring plan for launcher/pause/help flows that:
1. eliminates panel overlap and readability collisions,
2. improves discoverability and information hierarchy,
3. keeps controls/help synchronized with active keybindings,
4. preserves parity between launcher and pause menus,
5. stays maintainable with config-driven structure.

## 2. External Best-Practice Sources Consulted

1. WAI-ARIA APG Menu Button Pattern  
   [https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/)
2. WAI-ARIA APG Menu and Menubar Pattern  
   [https://www.w3.org/WAI/ARIA/apg/patterns/menubar/](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
3. WCAG 2.2: Consistent Help  
   [https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)
4. WCAG 2.2: Contrast (Minimum)  
   [https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
5. WCAG 2.2: Focus Appearance  
   [https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance)
6. Microsoft Windows App Design: Menus and context flyouts  
   [https://learn.microsoft.com/en-us/windows/apps/design/controls/menu-and-context-flyouts](https://learn.microsoft.com/en-us/windows/apps/design/controls/menu-and-context-flyouts)
7. Material Design Menus guidance  
   [https://m1.material.io/components/menus.html](https://m1.material.io/components/menus.html)
8. Nielsen Norman Group heuristics  
   [https://www.nngroup.com/articles/ten-usability-heuristics/](https://www.nngroup.com/articles/ten-usability-heuristics/)
9. ONS Service Manual content structuring guidance  
   [https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)

## 3. Best-Practice Rules Extracted

1. Keyboard behavior must be explicit and predictable (`Enter` activate, `Esc` close/back, arrow navigation for menu movement) and match ARIA menu patterns.
2. Focus order must follow visual order, and visible focus must remain strong under all themes/sizes.
3. Help entry points should be consistently located across contexts.
4. Menus should contain concise, descriptive labels; avoid vague bucket labels.
5. Limit nesting depth and reduce hidden complexity; deep cascading structures raise navigation cost.
6. Keep most frequent actions near top and destructive actions separated.
7. Context menus should only contain actions relevant to current state/selection.
8. Use recognition-over-recall: show key/action mapping near the action, not only in separate docs.
9. Keep text scannable: short sections, front-loaded headings, avoid dense paragraphs.
10. Show immediate system-status feedback after save/load/reset/apply.

## 4. Current Project Gaps (From Repo Audit)

1. Help page layout is largely fixed-coordinate rendering (`x/y` hardcoded), which is fragile for small windows and can still cause overlap.
2. Help content is partly static text and partly live-binding driven; synchronization exists but is incomplete for all settings/action surfaces.
3. Key-reference help page truncates overflow with `...` instead of offering paging/filtering, so discoverability drops on dense profiles.
4. Menu/help information architecture exists in RDS but execution remains partially distributed across multiple render paths.
5. Setup menus still carry duplicated render/value-format logic (`BKL-P2-007`), increasing drift risk.
6. Help index exists (`docs/help/HELP_INDEX.md`) but does not yet enforce full per-action completeness from runtime key catalogs.

## 5. Recommendations

### 5.1 Information architecture
1. Keep top-level launcher IA stable: `Play`, `Settings`, `Keybindings`, `Bot Options`, `Help`, `Quit`.
2. In `Help`, switch from fixed page count to topic registry model (`topic_id`, `title`, `sections`, `priority`, `dimension_scope`).
3. Split help into two lanes:
4. `Quick Help` (contextual, 1-screen actionable),
5. `Full Help` (complete reference, scroll/paged).

### 5.2 Layout model
1. Replace hardcoded coordinates with a layout grid contract:
2. header zone,
3. primary content zone,
4. secondary visual zone,
5. status/footer zone.
6. Add auto-wrap and overflow policy per zone: clip is forbidden for required controls.
7. Add small-window fallback profile (`compact`): hide non-critical blocks first, never hide focus row or key hints.

### 5.3 Key/help synchronization
1. Help keys must be generated from runtime binding catalogs for all groups (`system`,`game`,`camera`,`slice`) and all scopes (`general`,`2d`,`3d`,`4d`).
2. Add a completeness check: every bindable action must appear in either quick or full help.
3. Add source-of-truth mapping file (config-level) between action id and help topic.

### 5.4 Navigation and interaction
1. Keep navigation semantics identical in launcher, setup, pause, and help.
2. Add breadcrumb/context line in help (`Launcher > Help > Controls`).
3. Add per-topic pagination where line count exceeds viewport; remove silent truncation.
4. Keep `F1` help shortcut active in gameplay and in menu contexts.

### 5.5 Content quality
1. Rewrite help sections into short scan blocks: `What`, `When to use`, `Keys`, `Pitfalls`.
2. Prefer task phrasing over conceptual-only text for top pages.
3. Keep diagrams action-local (row-level icon + short legend), not one overloaded combined panel.

### 5.6 Maintainability
1. Move help topic definitions to config-backed structure (JSON canonical, loaded at runtime).
2. Keep rendering logic in one reusable help renderer module.
3. Keep dimension-specific deltas as data, not additional draw branches.

## 6. Proposed Execution Plan

## Phase 0: Contract and schema
1. Add help-topic schema and action-topic mapping schema.
2. Add validation in `tools/validate_project_contracts.py`.
3. Define layout tokens (spacing, min-row-height, section paddings) in config constants.

## Phase 1: IA and renderer refactor
1. Implement topic registry loader for help.
2. Build shared menu/help layout engine with zone allocation.
3. Replace fixed help page dispatcher with data-driven page model.

## Phase 2: Synchronization and coverage
1. Wire action-to-help generation from runtime binding groups.
2. Implement per-topic paging/filter in long key lists.
3. Add completeness test that fails when new bindable actions lack help entries.

## Phase 3: UX hardening and parity
1. Run overlap/readability passes on launcher, pause, and in-game help surfaces.
2. Ensure menu parity matrix (launcher vs pause) is test-covered.
3. Finalize compact mode behavior for small windows.

## 7. Acceptance Criteria

1. No panel/text overlap in supported window sizes.
2. No required help content is truncated without explicit paging.
3. All bindable actions are documented and displayed with current profile keys.
4. Launcher and pause expose the same settings/keybinding/help entry points (parity).
5. `ruff`, `pytest`, and contract validation pass after restructure.

## 8. Suggested Tests

1. Snapshot/layout tests for help pages in normal and compact window sizes.
2. Property test: every runtime action id appears in help coverage mapping.
3. Keyboard navigation tests for menu/help transitions (`Esc`, arrows, `Enter`, `F1`).
4. Regression tests for focus visibility and status-message emission after save/load/reset.

## 9. Scope Boundaries

In scope:
1. menu/help IA,
2. layout/readability,
3. key-help synchronization,
4. parity and maintainability improvements.

Out of scope for this batch:
1. gameplay mechanics changes,
2. bot/planner algorithm redesign,
3. new graphics engine.
