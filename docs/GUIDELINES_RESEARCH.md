# Researched Guidelines And Current Issues

Status: Active  
Last verified: 2026-02-19

## 1. Guidelines used (manuals and standards)

1. WAI-ARIA APG menu patterns:
2. [Menu Button Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menu-button/)
3. [Menu and Menubar Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/menubar/)
4. WCAG 2.2:
5. [Consistent Help](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html)
6. [Contrast Minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
7. [Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance)
8. Microsoft menu/flyout guidance:
9. [Menus and context flyouts](https://learn.microsoft.com/en-us/windows/apps/design/controls/menu-and-context-flyouts)
10. Material menu guidance:
11. [Material menus](https://m1.material.io/components/menus.html)
12. Nielsen heuristics:
13. [Ten usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
14. Content structuring reference:
15. [ONS structuring content](https://service-manual.ons.gov.uk/content/writing-for-users/structuring-content)

## 2. Core rules derived from those sources

1. Keep keyboard behavior predictable and consistent across menu contexts.
2. Preserve visible focus and contrast in all menu states and window sizes.
3. Keep help in predictable locations and retain direct in-game access.
4. Prefer short, scannable labels and shallow menu depth.
5. Show immediate status feedback after user actions (save/load/reset/apply).
6. Keep context menus context-specific and avoid overloading them as global navigation.
7. Prefer recognition over recall: place key/action hints near controls.

## 3. Current issues (open backlog)

1. `BKL-P2-006`: help/menu IA rework for overlap/readability/synchronization.
2. `BKL-P2-007`: setup-menu render/value dedup extraction.
3. Continuous watch items remain in `P3` (`BKL-P3-001`..`BKL-P3-005`).
4. Canonical source of active status is `docs/BACKLOG.md`.

## 4. Active plan artifacts

1. Help/menu restructuring report and execution plan:
2. `docs/plans/PLAN_HELP_AND_MENU_RESTRUCTURE_2026-02-19.md`
3. Unreferenced-helper and dedup follow-up plan:
4. `docs/plans/PLAN_UNREFERENCED_HELPERS_AND_CODE_REDUCTION_2026-02-19.md`
